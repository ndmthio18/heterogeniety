from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parent
if '--remote' in sys.argv:
 rows=[]
 for remote,local in [('native_replay','native_replay'),('native_vertical','vertical_replay')]:
  d=R/remote
  files=[d/n for n in ['build_manifest.json','compile_command.json','diagnostic.patch','build.log']]
  files+=list((d/'pilot').glob('*'))
  if remote=='native_replay':files+=list((d/'full').glob('*'))+[d/'full_run.log']
  for p in files:
   if p.is_file():rows.append({'path':local+'/'+p.relative_to(d).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 print(json.dumps({'remote_files':rows},indent=2))
else:
 m=json.loads((R/'REMOTE_TRANSFER_MANIFEST.json').read_text())
 for f in m['remote_files']:
  p=R/f['path'];assert p.stat().st_size==f['bytes'];assert hashlib.sha256(p.read_bytes()).hexdigest()==f['sha256'],str(p)
 print('SHA256 transfer verified:',len(m['remote_files']),'files')
