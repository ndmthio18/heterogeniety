"""Verify the local copy of the four production runs: every compressed field
against compressed_fields.jsonl (gzip SHA and decompressed raw SHA), the
pvd frame list against the field files, and remote vs local SHA of the
small ledger/manifest files."""
from pathlib import Path
import gzip,hashlib,json,subprocess,datetime
import xml.etree.ElementTree as ET
L=Path(__file__).resolve().parent;A=L/'archive/v10c'
REMOTE='/tmp/zhixin_causal_v10_20261030/runs/v10c'
SMALL=['budget.csv','causal_budget.csv','vertical_salt_flux.csv','film_budget.csv','seed_event.json','run_status.json','run_manifest.json','causal_switches.json','compressed_fields.jsonl']
def sha_file(p,gz=False):
 h=hashlib.sha256()
 with (gzip.open(p,'rb') if gz else open(p,'rb')) as f:
  for c in iter(lambda:f.read(1<<20),b''):h.update(c)
 return h.hexdigest()
def main():
 out={'verified_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'cases':{}}
 for case in ['C1B1_24h','C0B1_24h','C1B0_24h','C0B0_24h']:
  d=A/case;r={'files':0,'bytes':sum(p.stat().st_size for p in d.rglob('*') if p.is_file()),'gzip_mismatch':[],'raw_mismatch':[],'missing':[]}
  idx=[json.loads(l) for l in (d/'compressed_fields.jsonl').read_text().splitlines() if l.strip()]
  for e in idx:
   p=d/e['file']
   if not p.exists():r['missing'].append(e['file']);continue
   r['files']+=1
   if sha_file(p)!=e['gzip_sha256']:r['gzip_mismatch'].append(e['file'])
   if sha_file(p,gz=True)!=e['raw_sha256']:r['raw_mismatch'].append(e['file'])
  frames=[x.get('file') for x in ET.parse(d/f'{case}.pvd').findall('.//DataSet')]
  r['pvd_frames']=len(frames);r['frames_without_field']=[f for f in frames if not (d/(f+'.gz')).exists() and not (d/f).exists()]
  remote=dict(reversed(l.split()) for l in subprocess.run(['ssh','-o','BatchMode=yes','liqin',f'cd {REMOTE}/{case} && sha256sum '+' '.join(SMALL)],capture_output=True,text=True).stdout.splitlines())
  r['small_file_mismatch']=[f for f in SMALL if remote.get(f)!=sha_file(d/f)]
  r['status']='verified' if not (r['gzip_mismatch'] or r['raw_mismatch'] or r['missing'] or r['frames_without_field'] or r['small_file_mismatch']) else 'mismatch'
  out['cases'][case]=r;print(case,r['status'],r['files'],r['bytes'])
 out['status']='verified' if all(v['status']=='verified' for v in out['cases'].values()) else 'mismatch'
 (A/'archive_verification.json').write_text(json.dumps(out,indent=2));print(out['status'])
if __name__=='__main__':main()
