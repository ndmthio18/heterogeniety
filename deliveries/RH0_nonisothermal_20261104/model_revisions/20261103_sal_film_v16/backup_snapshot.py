from pathlib import Path
import subprocess,json,hashlib,tarfile,datetime
R=Path(__file__).resolve().parent
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')
remote='/tmp/zhixin_sal_film_v16_20261103'
out=R/'remote_backup';out.mkdir(exist_ok=True)
script=r'''from pathlib import Path
import json,hashlib,tarfile,io,csv
r=Path(ROOT); manifest={};files=list(r.glob('*_status.json'))+[r/'build_ni1/build_manifest.json',r/'build_ni1/heterogeneity_revised',r/'REPAIR_LOG.md']
for case in ['Film075mm','Film080mm']:
 d=r/'raw/runs'/case
 records=[json.loads(x) for x in (d/'compressed_fields.jsonl').read_text().splitlines() if x.strip()]
 for v in records:
  p=d/v['file'];assert hashlib.sha256(p.read_bytes()).hexdigest()==v['gzip_sha256'];files.append(p)
 files += [p for p in d.iterdir() if p.suffix in ['.csv','.json','.jsonl','.input']]
a=r/('backup_'+STAMP+'.tar')
with tarfile.open(a,'w') as tar:
 for p in files:
  data=p.read_bytes();name=p.relative_to(r).as_posix();manifest[name]=hashlib.sha256(data).hexdigest();info=tarfile.TarInfo(name);info.size=len(data);tar.addfile(info,io.BytesIO(data))
 data=json.dumps(manifest).encode();info=tarfile.TarInfo('snapshot_manifest.json');info.size=len(data);tar.addfile(info,io.BytesIO(data))
print(json.dumps(dict(archive=str(a),sha256=hashlib.sha256(a.read_bytes()).hexdigest(),files=len(manifest))))
'''.replace('ROOT',repr(remote)).replace('STAMP',repr(stamp))
p=subprocess.run(['ssh','-o','BatchMode=yes','sal','python3 -'],input=script,text=True,capture_output=True,check=True);meta=json.loads(p.stdout)
archive=out/Path(meta['archive']).name
subprocess.run(['scp','-o','BatchMode=yes','sal:'+meta['archive'],str(archive)],check=True)
assert hashlib.sha256(archive.read_bytes()).hexdigest()==meta['sha256']
with tarfile.open(archive) as tar:
 m=json.load(tar.extractfile('snapshot_manifest.json'))
 for n,h in m.items():assert hashlib.sha256(tar.extractfile(n).read()).hexdigest()==h,n
meta.update(state='verified',local_archive=str(archive.resolve()),snapshot=stamp)
(out/(stamp+'_verified.json')).write_text(json.dumps(meta,indent=2));print(json.dumps(meta))
