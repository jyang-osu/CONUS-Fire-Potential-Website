"""Verify the prepared static delivery and numeric precision."""
from pathlib import Path
import json,gzip,numpy as np,rasterio
import source_reader as src
ROOT=Path(__file__).resolve().parent
catalog=json.loads((ROOT/'site/catalog.json').read_text())
items=catalog['items'];assert set(catalog['variables'])==set(src.META) and len(src.META)==19
assert not {'WDIR_vector_mean','spread_direction','SNOWC','SNOW_FLAG'} & set(catalog['variables'])
source=src.inventory();checks=[]
for var in catalog['variables']:
    group=[e for e in items if e['variable']==var]
    assert 0<len(group)<=240
    e=max(group,key=lambda e:e['time'])
    values=np.frombuffer(gzip.decompress((ROOT/'site'/e['binary']).read_bytes()),dtype='<i4')
    assert values.size==e['width']*e['height']
    valid=values!=-2147483648
    with rasterio.open(source[e['key']]['path']) as ds:
        a=ds.read(1,masked=True);mask=~np.ma.getmaskarray(a).ravel()&np.isfinite(a.data.ravel())
        assert np.array_equal(mask,valid)
        error=float(np.max(np.abs(values[valid]/100-a.data.ravel()[valid]), initial=0))
        if error>.006: raise ValueError(f'{var} at {e["time"]}: numeric precision error {error:.9f} exceeds 0.006')
    with rasterio.open(ROOT/'site'/e['png']) as ds:
        assert (ds.width,ds.height)==(e['width'],e['height'])
    checks.append(dict(variable=var,hours=len(group)))
for e in items:
    for k in ('binary','png'):
        p=(ROOT/'site'/e[k]).resolve()
        assert p.is_relative_to((ROOT/'site').resolve()) and p.is_file()
size=sum(p.stat().st_size for p in (ROOT/'site').rglob('*') if p.is_file())
assert size<1_000_000_000
report=dict(status='PASS',site_bytes=size,products=len(items),variables=checks,
            web_precision='0.01 units; source GeoTIFF unchanged',checks=['All referenced assets exist','19 variable numeric grids and masks agree with source','PNG dimensions','Ten-day maximum per variable','Published site under 1 GB'])
(ROOT/'verification.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'status':'PASS','products':len(items),'site_MB':round(size/1e6,1)}))

