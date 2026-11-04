from pathlib import Path
import subprocess,time,json,hashlib,tarfile
R=Path(__file__).resolve().parent
remote='/home/zhixin/Documents/Cooperation_Ali/model_revisions/20261102_cylinder_thermal_v13'
def status(stage,**kw):(R/'final_delivery_status.json').write_text(json.dumps(dict(stage=stage,**kw),indent=2))
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(2**20),b''):h.update(b)
 return h.hexdigest()
try:
 status('waiting_remote_archive')
 for i in range(240):
  q=subprocess.run(['ssh','-o','LogLevel=ERROR','-o','BatchMode=yes','liqin',f'test -f {remote}/final_174h_delivery.sha256'],capture_output=True)
  if q.returncode==0:break
  time.sleep(15)
 else:raise RuntimeError('Remote archive not ready in one hour')
 for name in ['final_174h_delivery.sha256','final_174h_manifest.json','final_174h_delivery.tar']:
  status('downloading',file=name)
  subprocess.run(['scp','-q','-o','BatchMode=yes',f'liqin:{remote}/{name}',str(R/name)],check=True)
 expected=(R/'final_174h_delivery.sha256').read_text().split()[0]
 status('verifying_archive');assert sha(R/'final_174h_delivery.tar')==expected
 manifest=json.loads((R/'final_174h_manifest.json').read_text());seen=[]
 with tarfile.open(R/'final_174h_delivery.tar') as tar:
  for member in tar:
   if member.name not in manifest['files']:continue
   h=hashlib.sha256()
   with tar.extractfile(member) as f:
    for b in iter(lambda:f.read(2**20),b''):h.update(b)
   assert h.hexdigest()==manifest['files'][member.name]['sha256'],member.name
   seen.append(member.name)
 assert set(seen)==set(manifest['files'])
 status('verified',archive_sha256=expected,verified_file_count=len(seen),remote_verification=manifest['verification'])
except Exception as exc:status('failed',error=repr(exc));raise
