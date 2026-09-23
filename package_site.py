"""Package only catalog-listed assets in the latest shared 240-hour window."""
from pathlib import Path
from datetime import datetime, timedelta
import zipfile, json
root=Path(__file__).resolve().parent
site=root/'site'
catalog=json.loads((site/'catalog.json').read_text())
items=catalog['items']
if not items: raise ValueError('No exported products to package')
latest=max(e['time'] for e in items)
cutoff=(datetime.strptime(latest,'%Y%m%d_%H%M')-timedelta(hours=239)).strftime('%Y%m%d_%H%M')
catalog['items']=[e for e in items if cutoff<=e['time']<=latest]
assets={'index.html','.nojekyll'}
for item in catalog['items']:
    assets.update((item['binary'],item['png']))
with zipfile.ZipFile(root/'site.zip.tmp','w',compression=zipfile.ZIP_STORED) as z:
    z.writestr('catalog.json',json.dumps(catalog,separators=(',',':'),allow_nan=False))
    for name in sorted(assets):
        p=(site/name).resolve()
        if not p.is_relative_to(site.resolve()): raise ValueError('Unsafe asset path')
        z.write(p,name)
with zipfile.ZipFile(root/'site.zip.tmp') as z:
    saved=json.loads(z.read('catalog.json'))
    if not all(cutoff<=e['time']<=latest for e in saved['items']): raise ValueError('Out-of-window asset')
    if set(z.namelist()) != assets|{'catalog.json'}: raise ValueError('Unexpected ZIP contents')
(root/'site.zip.tmp').replace(root/'site.zip')
print(f'Prepared site.zip: {cutoff} to {latest} UTC (240 hourly slots); {len(catalog["items"])} products. No older assets included.')
