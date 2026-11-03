"""Verify every B field's compressed and original-byte SHA in the local archives."""
from pathlib import Path
import json,hashlib,tarfile,gzip,datetime
R=Path(__file__).resolve().parent;B=R/'track2d';O=B/'remote_backup'
index=json.loads((O/'verified_index.json').read_text());expected={};seen={};pvd={}
for case in ['B0','B1','B2','B3']:
 for line in (B/'raw/runs'/case/'compressed_fields.jsonl').read_text().splitlines():
  d=json.loads(line);name=f'track2d/raw/runs/{case}/'+d['file'];expected[name]=d
  assert index[name]==d['gzip_sha256'],name
for archive in sorted(O.glob('snapshot_*.tar')):
 with tarfile.open(archive) as t:
  for m in t:
   if m.name in expected and m.name not in seen:
    d=expected[m.name];data=t.extractfile(m).read()
    if hashlib.sha256(data).hexdigest()!=d['gzip_sha256']:continue
    raw=gzip.decompress(data);assert len(raw)==d['raw_bytes'];assert hashlib.sha256(raw).hexdigest()==d['raw_sha256'],m.name
    seen[m.name]=dict(archive=archive.name,gzip_sha256=d['gzip_sha256'],raw_sha256=d['raw_sha256'])
   if m.name in [f'track2d/raw/runs/{c}/{c}.pvd' for c in ['B0','B1','B2','B3']]:
    data=t.extractfile(m).read()
    if hashlib.sha256(data).hexdigest()==index.get(m.name):pvd[m.name]=data
assert len(seen)==len(expected),(len(seen),len(expected))
import xml.etree.ElementTree as ET
checks=[]
for case in ['B0','B1','B2','B3']:
 name=f'track2d/raw/runs/{case}/{case}.pvd';data=pvd[name];datasets=ET.fromstring(data).findall('.//DataSet')
 assert max(float(x.get('timestep')) for x in datasets)==176*3600
 for x in datasets:assert f'track2d/raw/runs/{case}/'+x.get('file')+'.gz' in seen
 checks.append(dict(case=case,fields=len(datasets),last_simulation_s=176*3600,last_evaporation_h=174,pvd_sha256=hashlib.sha256(data).hexdigest()))
out=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),state='passed',fields_with_both_gzip_and_raw_SHA_verified=len(seen),cases=checks)
(R/'provenance/B2D_final_backup_verification.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
