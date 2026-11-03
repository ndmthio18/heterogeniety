from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parent
d=json.loads((r/'PACKAGE_MANIFEST.json').read_text(encoding='utf-8'))
for x in d['files']:
 p=r/x['path'];assert p.is_file(),x['path']
 assert p.stat().st_size==x['bytes'],x['path']
 assert hashlib.sha256(p.read_bytes()).hexdigest()==x['sha256'],x['path']
print('Verified',len(d['files']),'packaged files')
