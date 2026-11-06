"""Pull the immutable v10 snapshot named in HANDOFF_READY.json to this directory
and verify its SHA256 and the source/binary/mesh hashes inside it."""
from pathlib import Path
import hashlib,json,subprocess,tarfile,datetime
L=Path(__file__).resolve().parent
def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def main():
 h=json.loads((L/'HANDOFF_READY.json').read_text());remote=h['snapshot_tar'];local=L/Path(remote).name
 if not local.exists():
  p=subprocess.run(['scp','-q','-o','BatchMode=yes',f'liqin:{remote}',str(local)]);assert p.returncode==0
 assert sha_bytes(local.read_bytes())==h['snapshot_tar_sha256'],'snapshot sha mismatch'
 bad=[];seen=0
 with tarfile.open(local) as t:
  members={m.name:m for m in t.getmembers() if m.isfile()}
  for k,v in h['source_sha256'].items():
   seen+=1
   if sha_bytes(t.extractfile(members[k]).read())!=v:bad.append(k)
  tag=h['version'].split('_')[-1]
  if sha_bytes(t.extractfile(members[f'build_{tag}/heterogeneity_causal']).read())!=h['binary_sha256']:bad.append('binary')
  if sha_bytes(t.extractfile(members['inputs/cylinder.msh']).read())!=h['mesh_sha256']:bad.append('mesh')
 r={'verified_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'snapshot':str(local),'snapshot_sha256':h['snapshot_tar_sha256'],'source_files_checked':seen,'mismatches':bad,'status':'verified' if not bad else 'mismatch'}
 (L/'handoff_verification_local.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
if __name__=='__main__':main()
