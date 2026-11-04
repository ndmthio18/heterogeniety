from pathlib import Path
import json,hashlib,tarfile,gzip
R=Path(__file__).resolve().parent
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(2**20),b''):h.update(b)
 return h.hexdigest()
files=[];verification={}
for name in ['RH0_174h']:
 p=Path('/tmp/zhixin_cylinder_thermal_v13_20261102/runs')/name
 assert json.loads((p/'acceptance.json').read_text())['completed_evaporation_h']==174
 assert json.loads((p/'run_status.json').read_text())['status']=='completed'
 assert json.loads((p/'run_manifest.json').read_text())['returncode']==0
 entries=[json.loads(s) for s in (p/'compressed_fields.jsonl').read_text().splitlines()]
 for e in entries:assert sha(p/e['file'])==e['gzip_sha256']
 assert not list(p.glob('*.vtu')),'Uncompressed final field remains'
 verification[name]=dict(compressed_fields_verified=len(entries),completed_h=174)
 files+=list(f for f in p.iterdir() if f.is_file())
files += [p for d in ['source','inputs','build_ni1','tests'] for p in (R/d).rglob('*') if p.is_file()]
files += [p for p in R.iterdir() if p.is_file() and p.suffix in ['.md','.json','.jsonl','.py']]
def arc(p):
 return ('raw/runs/RH0_174h/'+p.name) if str(p).startswith('/tmp/') else p.relative_to(R).as_posix()
manifest={arc(p):dict(sha256=sha(p),bytes=p.stat().st_size) for p in files}
(R/'final_174h_manifest.json').write_text(json.dumps(dict(files=manifest,verification=verification),indent=2))
with tarfile.open(R/'final_174h_delivery.tar','w',dereference=True) as tar:
 for p in files+[R/'final_174h_manifest.json']:tar.add(p,arcname=arc(p))
(R/'final_174h_delivery.sha256').write_text(sha(R/'final_174h_delivery.tar')+'  final_174h_delivery.tar\n')
print(json.dumps(verification),flush=True)
