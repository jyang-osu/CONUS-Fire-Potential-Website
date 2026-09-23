"""Local read-only CONUS results dashboard."""
from pathlib import Path
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from urllib.parse import urlparse,parse_qs
import json,re,hashlib,io,os
from datetime import datetime,timezone,timedelta
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
ROOT=Path(__file__).resolve().parent
os.environ['GDAL_DATA']=str(ROOT/'runtime/Lib/site-packages/rasterio/gdal_data')
import numpy as np
import rasterio
CONFIG=json.loads((ROOT/'config.json').read_text())
SOURCE=(ROOT/CONFIG['simulation_root']).resolve()
META={
'dmc_1_hr':['1-hour dead fuel moisture','% dry mass',2,30],
'dmc_10_hr':['10-hour dead fuel moisture','% dry mass',2,30],
'dmc_100_hr':['100-hour dead fuel moisture','% dry mass',2,30],
'dmc_1000_hr':['1000-hour dead fuel moisture','% dry mass',2,30],
'lmc_herb':['Herbaceous live moisture','% dry mass',20,200],
'lmc_woody':['Woody live moisture','% dry mass',50,200],
'BI':['Burning index','index',0,120],'ERC':['Energy release component','index',0,60],
'SC':['Spread component','index',0,60],'IC':['Ignition component','index',0,100],
'rate_of_spread':['Rate of spread','m/min',0,30],'flame_length':['Flame length','m',0,4],
'fireline_intensity':['Fireline intensity','kW/m',0,4000],
'fire_type':['Fire type','category',0,3]}
META.update({
'TAIR_mean':['Air temperature','°C',-20,40],
'RELH_mean':['Relative humidity','%',0,100],
'WSPD_mean':['Wind speed','m/s',0,25],
'RAIN_total_mm':['Hourly precipitation','mm',0,25],
'SRAD_mean':['Solar radiation','W/m²',0,800]})
GROUPS={k:('Fuel moisture' if k.startswith(('dmc_','lmc_')) else
    'Fire danger indices' if k in ('BI','ERC','SC','IC') else
    'Weather conditions' if k in ('TAIR_mean','RELH_mean','WSPD_mean','RAIN_total_mm','SRAD_mean') else
    'Fire behavior') for k in META}
PAT=re.compile(r'CONUS_(\d{8})_(\d{4})_UTC_(.+)\.tif$')
def inventory():
    entries={}
    receipts=list((SOURCE/'reports/nfdrs_hours').glob('*.json'))
    receipts+=list((SOURCE/'Output/Check_Point/NFDRS/generations').glob('*/complete.json'))
    receipts+=list((SOURCE/'Output/Behavior').glob('*/*/*/*/*run.json'))
    receipts+=list((SOURCE/'Output/Weather/data').glob('**/geotiff_complete.json'))
    for receipt in receipts:
        try:
            m=json.loads(receipt.read_text())
            behavior='Behavior' in receipt.parts
            weather=receipt.name=='geotiff_complete.json'
            base=receipt.parent if behavior or weather else SOURCE/'Output/NFDRS'
            for item in m.get('outputs',[]):
                p=(base/item['file' if weather else 'path']).resolve()
                if not p.is_relative_to(SOURCE/'Output') or not p.is_file():continue
                match=PAT.fullmatch(p.name)
                if not match or match[3] not in META:continue
                stamp=datetime.fromisoformat(m['interval_end_utc'].replace('Z','+00:00')).astimezone(timezone.utc).strftime('%Y%m%d_%H%M') if weather else match[1]+'_'+match[2];key=stamp+'_'+match[3]
                entries[key]={'key':key,'time':stamp,'variable':match[3],'group':GROUPS[match[3]],'path':p,'sha':item['sha256']}
        except (OSError,ValueError,KeyError):continue
    return entries
