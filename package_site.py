from pathlib import Path
import zipfile,json
root=Path(__file__).resolve().parent
with zipfile.ZipFile(root/'site.zip.tmp','w',compression=zipfile.ZIP_STORED) as z:
    for p in (root/'site').rglob('*'):
        if p.is_file():z.write(p,p.relative_to(root/'site').as_posix())
(root/'site.zip.tmp').replace(root/'site.zip')
print('Prepared site.zip: upload as a GitHub release asset, not a Git commit.')

