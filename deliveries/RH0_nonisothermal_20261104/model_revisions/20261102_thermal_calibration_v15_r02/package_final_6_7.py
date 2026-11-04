from pathlib import Path
import json,hashlib,tarfile,gzip
R=Path(__file__).resolve().parent
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(2**20),b''):h.update(b)
 return h.hexdigest()
files=[];verification={}
for name in ['Film06mm','Film07mm']:
 p=R/'raw/runs'/name
 assert json.loads((p/'acceptance.json').read_text())['completed_evaporation_h']==174
 assert json.loads((p/'run_status.json').read_text())['status']=='completed'
 assert json.loads((p/'run_manifest.json').read_text())['returncode']==0
 entries=[json.loads(s) for s in (p/'compressed_fields.jsonl').read_text().splitlines()]
 for e in entries:assert sha(p/e['file'])==e['gzip_sha256']
 assert not list(p.glob('*.vtu')),'Uncompressed final field remains'
 verification[name]=dict(compressed_fields_verified=len(entries),completed_h=174)
 files+=list(f for f in p.iterdir() if f.is_file())
for name in ['Trial01','Bracket04mm','Bracket12mm']:
 p=R/'raw/runs'/name
 files += [p/f for f in ['film_budget.csv','budget.csv','thermal_budget.csv','mineral_budget.csv','user_stop_manifest.json']]
files += [p for d in ['source','inputs','build_ni1'] for p in (R/d).rglob('*') if p.is_file()]
files += [R/n for n in ['METHOD.md','REPAIR_LOG.md','experiment.csv','comparison_6_7mm.json','calibration_status.json','gate_summary.json','replacement_6_7mm_deployment.json','run_6_7mm.py','runner.py','calibrate.py','parallel_calibrate.py']]
manifest={p.relative_to(R).as_posix():dict(sha256=sha(p),bytes=p.stat().st_size) for p in files}
(R/'final_6_7_manifest.json').write_text(json.dumps(dict(files=manifest,verification=verification),indent=2))
with tarfile.open(R/'final_6_7_delivery.tar','w') as tar:
 for p in files+[R/'final_6_7_manifest.json']:tar.add(p,arcname=p.relative_to(R))
(R/'final_6_7_delivery.sha256').write_text(sha(R/'final_6_7_delivery.tar')+'  final_6_7_delivery.tar\n')
print(json.dumps(verification),flush=True)
