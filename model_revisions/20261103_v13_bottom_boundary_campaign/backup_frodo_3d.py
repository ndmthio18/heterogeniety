"""Transfer closed raw gzip fields and metadata; verify hashes before retiring transport tar."""
from pathlib import Path
import subprocess,json,hashlib,tarfile,datetime
R=Path(__file__).resolve().parent;O=R/'track3d_r02/remote_backup';O.mkdir(exist_ok=True);index=O/'verified_index.json'
known=json.loads(index.read_text()) if index.exists() else {};stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')
code=r'''from pathlib import Path
import json,hashlib,tarfile,io
r=Path('/temp/zhixin/v13_bottom_boundary_campaign_20261103');known=KNOWN;files=[]
for base in [r,r/'track3d_r02']:
 for p in base.glob('*_status.json'):files.append(p)
 for name in ['jobs.json','track_resource_admission.json','resource_admission.json','input_manifest.json']:
  if (base/name).exists():files.append(base/name)
 for folder in ['status','build_ni1','build_filter_sal','build_sal','inputs','results']:
  for p in (base/folder).rglob('*'):
   if p.is_file() and p.suffix in ['.json','.csv','.input','.txt','.log','.md']:files.append(p)
 for d in (base/'raw').glob('runs/*'):
  registry=d/'compressed_fields.jsonl'
  if registry.exists():
   for line in registry.read_text().splitlines():
    x=json.loads(line);p=d/x['file'];rel=p.relative_to(r).as_posix()
    if known.get(rel)!=x['gzip_sha256']:
     assert hashlib.sha256(p.read_bytes()).hexdigest()==x['gzip_sha256'];files.append(p)
  for p in d.rglob('*'):
   if p.is_file() and p.suffix in ['.json','.csv','.input','.txt','.log','.jsonl','.pvd']:files.append(p)
 for p in (base/'raw/probes').rglob('*'):
  if p.is_file() and p.suffix in ['.json','.log']:files.append(p)
folder=r/'transport_archives';folder.mkdir(exist_ok=True);a=folder/('snapshot_3d_r02_'+STAMP+'.tar');manifest={}
with tarfile.open(a,'w') as t:
 for p in sorted(set(files)):
  data=p.read_bytes();name=p.relative_to(r).as_posix();h=hashlib.sha256(data).hexdigest()
  if known.get(name)==h:continue
  info=tarfile.TarInfo(name);info.size=len(data);t.addfile(info,io.BytesIO(data));manifest[name]=h
 data=json.dumps(manifest).encode();info=tarfile.TarInfo('snapshot_manifest.json');info.size=len(data);t.addfile(info,io.BytesIO(data))
h=hashlib.sha256()
with a.open('rb') as f:
 for b in iter(lambda:f.read(2**20),b''):h.update(b)
print(json.dumps({'archive':str(a),'sha256':h.hexdigest(),'files':len(manifest)}))
'''.replace('KNOWN',repr(known)).replace('STAMP',repr(stamp))
p=subprocess.run(['ssh','-o','BatchMode=yes','-o','LogLevel=ERROR','iws_zhixin','python3 -'],input=code,capture_output=True,text=True,check=True);meta=json.loads(p.stdout);archive=O/Path(meta['archive']).name
subprocess.run(['scp','-q','-o','BatchMode=yes','-o','LogLevel=ERROR','iws_zhixin:'+meta['archive'],str(archive)],check=True)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(2**20),b''):h.update(b)
 return h.hexdigest()
assert sha(archive)==meta['sha256']
with tarfile.open(archive) as t:
 m=json.load(t.extractfile('snapshot_manifest.json'))
 for name,h in m.items():assert hashlib.sha256(t.extractfile(name).read()).hexdigest()==h,name
known.update(m);index.write_text(json.dumps(known,indent=2));meta.update(state='verified',utc=stamp,total_verified_paths=len(known),local=str(archive.resolve()));(O/(stamp+'_verified.json')).write_text(json.dumps(meta,indent=2))
# Only the newly created transfer tar is removed. Raw fields/metadata remain on Frodo.
cleanup=f"from pathlib import Path; p=Path({meta['archive']!r}); root=Path('/temp/zhixin/v13_bottom_boundary_campaign_20261103/transport_archives'); assert p.resolve().parent==root.resolve() and p.name=={archive.name!r}; p.unlink()"
subprocess.run(['ssh','-o','BatchMode=yes','-o','LogLevel=ERROR','iws_zhixin','python3 -'],input=cleanup,text=True,check=True)
print(json.dumps(meta,indent=2))
