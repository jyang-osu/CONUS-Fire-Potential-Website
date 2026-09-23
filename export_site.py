"""Export latest ten-day verified outputs as a static, GitHub Pages-ready site."""
from pathlib import Path
import gzip,json,hashlib,os,shutil,time,msvcrt
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timedelta,timezone
import source_reader as src
import numpy as np
import rasterio
ROOT=Path(__file__).resolve().parent
def atomic(p,data):
    p.parent.mkdir(parents=True,exist_ok=True)
    temp=p.with_suffix(p.suffix+'.tmp');temp.write_bytes(data);temp.replace(p)
def js(p,obj):atomic(p,json.dumps(obj,separators=(',',':'),allow_nan=False).encode())
def export_one(entry):
    raw=entry['path'].read_bytes()
    if hashlib.sha256(raw).hexdigest()!=entry['sha']:raise ValueError('Output is being rewritten: '+str(entry['path']))
    with rasterio.MemoryFile(raw) as mem:
        with mem.open() as ds:
            a=ds.read(1,masked=True);valid=~np.ma.getmaskarray(a)&np.isfinite(a.data)
            data=np.where(valid,a.data,np.nan).astype('<f4');vals=data[valid];tags=ds.tags()
            v=entry['variable'];base=entry['time']+'_'+entry['sha'][:16]+('_web6live' if v in ('lmc_herb','lmc_woody') else '_web5rain' if v=='RAIN_total_mm' else '_web4weather' if v in ('RELH_mean','RAIN_total_mm','SRAD_mean') else '_web3temp' if v=='TAIR_mean' else '_web2')
            rel=Path('data')/v/base
            numeric=rel.with_name(rel.name+'_precision2').with_suffix('.bin.gz');png=rel.with_suffix('.png')
            dest=ROOT/'site'
            if not (dest/numeric).exists():atomic(dest/numeric,gzip.compress(np.where(valid,np.rint(np.nan_to_num(data).astype(np.float64)*100),-2147483648).astype('<i4').tobytes(),compresslevel=6,mtime=0))
            if not (dest/png).exists():
                colors=([[215,25,28],[253,141,60],[255,230,65],[44,180,91],[33,102,222]] if src.GROUPS[v]=='Fuel moisture' or v=='RELH_mean' else
                        [[255,255,225],[151,218,130],[48,202,211],[38,121,218],[19,35,130]] if v=='RAIN_total_mm' else
                        [[0,145,55],[134,207,38],[255,230,0],[255,132,0],[220,20,35]] if src.GROUPS[v]=='Fire danger indices' else
                        [[30,80,230],[0,190,230],[60,200,75],[255,190,0],[225,20,35]] if v in ('rate_of_spread','flame_length','fireline_intensity','TAIR_mean') else
                        [[37,76,115],[50,139,158],[161,201,135],[241,204,102],[209,90,66]])
                lo,hi=src.META[v][2:]
                indices=np.where(valid,1+np.rint(np.clip((np.nan_to_num(data)-lo)/(hi-lo),0,1)*254),0).astype('uint8')
                pal=np.array(colors);cmap={0:(0,0,0,0)}
                for k in range(1,256):
                    f=(k-1)/254*4;j=min(int(f),3);t=f-j
                    rgb=np.rint(pal[j]*(1-t)+pal[j+1]*t).astype(int)
                    cmap[k]=tuple(map(int,rgb))+(255,)
                if v=='fire_type':
                    indices=np.where(valid,np.nan_to_num(data)+1,0).astype('uint8')
                    for k,c in enumerate([[209,220,215],[237,181,69],[224,100,48],[139,39,56]],1):cmap[k]=tuple(c)+(255,)
                with rasterio.MemoryFile() as image:
                    with image.open(driver='PNG',width=ds.width,height=ds.height,count=1,dtype='uint8') as out:
                        out.write(indices,1);out.write_colormap(1,cmap)
                    atomic(dest/png,image.read())
            return dict(key=entry['key'],time=entry['time'],variable=v,group=entry['group'],
                binary=numeric.as_posix(),png=png.as_posix(),source_sha256=entry['sha'],encoding='int32-le-scale100',
                width=ds.width,height=ds.height,transform=list(ds.transform)[:6],crs=str(ds.crs),
                min=float(vals.min()) if vals.size else None,max=float(vals.max()) if vals.size else None,
                mean=float(vals.mean()) if vals.size else None,cells=int(vals.size),
                warmup=any('warmup' in k.lower() and str(value).lower() in ('true','1','yes') for k,value in tags.items()))
def main():
    started=time.time();site=ROOT/'site';site.mkdir(exist_ok=True)
    with (ROOT/'export.lock').open('a+b') as lock:
        if lock.tell()==0:lock.write(b'0');lock.flush()
        lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
        all_items=src.inventory()
        if not all_items:raise ValueError('No completed outputs found')
        latest=max(e['time'] for e in all_items.values())
        cutoff=(datetime.strptime(latest,'%Y%m%d_%H%M')-timedelta(hours=239)).strftime('%Y%m%d_%H%M')
        selected=[e for e in all_items.values() if cutoff<=e['time']<=latest]
        if not selected:raise ValueError('No completed outputs found')
        results=[];skipped=[]
        def safe(e):
            try:return export_one(e),None
            except (OSError,ValueError) as exc:return None,str(exc)
        with ThreadPoolExecutor(max_workers=src.CONFIG.get('export_workers',4)) as pool:
            for i,(result,error) in enumerate(pool.map(safe,selected),1):
                if result:results.append(result)
                else:skipped.append(error)
                if i%100==0:print(f'Exported {i}/{len(selected)} products',flush=True)
        if not results:raise ValueError('No verified products could be exported')
        keep={item[k] for item in results for k in ('binary','png')}
        size=sum((site/p).stat().st_size for p in keep)+(ROOT/'web/index.html').stat().st_size
        if size>950_000_000:raise ValueError(f'Export exceeds the 950 MB safety budget: {size}; site catalog not replaced')
        js(site/'catalog.json',dict(variables=src.META,groups=src.GROUPS,items=results,exported_utc=datetime.now(timezone.utc).isoformat()))
        atomic(site/'index.html',(ROOT/'web/index.html').read_bytes());atomic(site/'.nojekyll',b'')
        # Remove only exporter-owned stale data, after publishing the new catalog.
        data_root=(site/'data').resolve()
        for path in data_root.rglob('*'):
            if path.is_file() and path.relative_to(site).as_posix() not in keep:
                if not path.resolve().is_relative_to(data_root):raise ValueError('Unsafe cleanup path')
                path.unlink()
        report=dict(status='PASS',products=len(results),variables=len(set(e['variable'] for e in results)),site_bytes=sum(p.stat().st_size for p in site.rglob('*') if p.is_file()),elapsed_seconds=round(time.time()-started,1),skipped=skipped)
        js(ROOT/'export_report.json',report);print(json.dumps(report,indent=2),flush=True)
if __name__=='__main__':main()


