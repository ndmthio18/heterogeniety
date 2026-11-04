"""Preserve completed compressed fields on home, retaining transparent scratch links."""
from pathlib import Path
import hashlib,shutil,json,os,datetime
src=Path('/tmp/zhixin_cylinder_thermal_v13_20261102/runs/RH0_174h')
root=Path('/home/zhixin/Documents/Cooperation_Ali/model_revisions/20261102_cylinder_thermal_v13')
dst=root/'preserved_fields_20261103';dst.mkdir(exist_ok=True)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(2**20),b''):h.update(b)
 return h.hexdigest()
assert src.resolve()==src and dst.resolve().is_relative_to(root.resolve())
assert shutil.disk_usage(dst).free>5*1024**3
known={z['file']:z for z in map(json.loads,(src/'compressed_fields.jsonl').read_text().splitlines())}
total=0
for p in sorted(src.glob('*.vtu.gz')):
 if p.is_symlink():continue
 assert p.resolve().parent==src and p.name in known
 expected=known[p.name]['gzip_sha256'];assert sha(p)==expected
 target=dst/p.name;assert not target.exists()
 shutil.copy2(p,target)
 assert sha(target)==expected
 size=p.stat().st_size
 # Atomic replacement only after matching SHA: original pathname still reads identical bytes.
 link=src/(p.name+'.relocated_link');assert not link.exists()
 link.symlink_to(target);assert sha(link)==expected
 os.replace(link,p)
 record=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),original_path=str(p),preserved_path=str(target),bytes=size,gzip_sha256=expected,raw_sha256=known[p.name]['raw_sha256'])
 with (root/'scratch_relocation_20261103.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
 total+=size
 if total>=1536*1024**2:break
print(json.dumps(dict(relocated_bytes=total,scratch_free_GiB=shutil.disk_usage(src).free/1024**3,home_free_GiB=shutil.disk_usage(dst).free/1024**3)))
