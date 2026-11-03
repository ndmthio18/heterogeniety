"""Back up the isolated conditional 2D G track from Frodo with SHA-256 verification."""
from pathlib import Path
import datetime
import hashlib
import json
import subprocess
import tarfile

R = Path(__file__).resolve().parent
TRACK = "track2d_g_conditional_r02"
REMOTE_ROOT = Path("/temp/zhixin/v13_bottom_boundary_campaign_20261103")
O = R / TRACK / "remote_backup"
O.mkdir(parents=True, exist_ok=True)
index = O / "verified_index.json"
known = json.loads(index.read_text()) if index.exists() else {}
stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")

code = r'''
from pathlib import Path
import hashlib, io, json, tarfile
r=Path('/temp/zhixin/v13_bottom_boundary_campaign_20261103')
t=r/'track2d_g_conditional_r02'; known=KNOWN; files=[]
for name in ['launch_receipt.json','supervisor_status.json','input_manifest.json','METHOD.md']:
 p=t/name
 if p.exists(): files.append(p)
for folder in ['status','build_sal','inputs','results','provenance']:
 for p in (t/folder).rglob('*'):
  if p.is_file() and p.suffix.lower() in ['.json','.csv','.input','.txt','.log','.md','.py']:
   files.append(p)
for d in (t/'raw').glob('runs/*'):
 registry=d/'compressed_fields.jsonl'
 if registry.exists():
  for line in registry.read_text().splitlines():
   x=json.loads(line); p=d/x['file']; rel=p.relative_to(r).as_posix()
   if known.get(rel)!=x['gzip_sha256']:
    assert hashlib.sha256(p.read_bytes()).hexdigest()==x['gzip_sha256']; files.append(p)
 for p in d.rglob('*'):
  if p.is_file() and p.suffix.lower() in ['.json','.csv','.input','.txt','.log','.jsonl','.pvd']:
   files.append(p)
folder=r/'transport_archives'; folder.mkdir(exist_ok=True)
a=folder/('snapshot_2d_g_'+STAMP+'.tar'); manifest={}
with tarfile.open(a,'w') as archive:
 for p in sorted(set(files)):
  data=p.read_bytes(); name=p.relative_to(r).as_posix(); h=hashlib.sha256(data).hexdigest()
  if known.get(name)==h: continue
  info=tarfile.TarInfo(name); info.size=len(data); archive.addfile(info,io.BytesIO(data)); manifest[name]=h
 data=json.dumps(manifest).encode(); info=tarfile.TarInfo('snapshot_manifest.json'); info.size=len(data)
 archive.addfile(info,io.BytesIO(data))
h=hashlib.sha256()
with a.open('rb') as f:
 for b in iter(lambda:f.read(2**20),b''): h.update(b)
print(json.dumps({'archive':str(a),'sha256':h.hexdigest(),'files':len(manifest)}))
'''.replace("KNOWN", repr(known)).replace("STAMP", repr(stamp))

p = subprocess.run(
    ["ssh", "-o", "BatchMode=yes", "-o", "LogLevel=ERROR", "iws_zhixin", "python3", "-"],
    input=code, capture_output=True, text=True, check=True,
)
meta = json.loads(p.stdout)
archive = O / Path(meta["archive"]).name
subprocess.run([
    "scp", "-q", "-o", "BatchMode=yes", "-o", "LogLevel=ERROR",
    "iws_zhixin:" + meta["archive"], str(archive),
], check=True)

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(2**20), b""):
            h.update(block)
    return h.hexdigest()

assert sha256(archive) == meta["sha256"]
with tarfile.open(archive) as tf:
    manifest = json.load(tf.extractfile("snapshot_manifest.json"))
    for name, expected in manifest.items():
        assert hashlib.sha256(tf.extractfile(name).read()).hexdigest() == expected, name
    # Materialize only light status/result evidence. Raw gzip fields stay in the verified archive.
    prefix = TRACK + "/"
    for member in tf.getmembers():
        if not member.isfile() or member.name == "snapshot_manifest.json" or not member.name.startswith(prefix):
            continue
        rel = Path(member.name[len(prefix):])
        if rel.parts and (rel.parts[0] in {"status", "results", "provenance"} or len(rel.parts) == 1):
            target = R / TRACK / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(tf.extractfile(member).read())

known.update(manifest)
index.write_text(json.dumps(known, indent=2))
meta.update(state="verified", utc=stamp, total_verified_paths=len(known), local=str(archive.resolve()))
(O / (stamp + "_verified.json")).write_text(json.dumps(meta, indent=2))
cleanup = (
    f"from pathlib import Path; p=Path({meta['archive']!r}); "
    f"root=Path({REMOTE_ROOT.as_posix() + '/transport_archives'!r}); "
    f"assert p.resolve().parent==root.resolve() and p.name=={archive.name!r}; p.unlink()"
)
subprocess.run([
    "ssh", "-o", "BatchMode=yes", "-o", "LogLevel=ERROR", "iws_zhixin", "python3", "-"
], input=cleanup, text=True, check=True)
print(json.dumps(meta, indent=2))
