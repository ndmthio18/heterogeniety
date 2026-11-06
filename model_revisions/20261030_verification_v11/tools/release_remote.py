"""Release remote scratch space of archived v11 runs (PLAN: only own, double-end
hash-verified files; keep an index; no recursive deletion).

For CASE: requires runs_archive/CASE/ARCHIVE_MANIFEST.json status=verified; local
files are re-hashed; on liqin each candidate file (> MIN_BYTES, inside
/tmp/zhixin_verification_v11_20261030/runs/CASE, regular file) is re-hashed and
removed individually only if remote hash == manifest hash == local hash. Small files
(manifests, logs, budgets) stay. Writes RELEASED_INDEX.json remotely and locally.
Usage: python release_remote.py CASE [CASE ...]
"""
import hashlib, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCR = '/tmp/zhixin_verification_v11_20261030/runs'
MIN_BYTES = 512 * 1024
RSCRIPT = '/home/zhixin/Documents/Cooperation_Ali/model_revisions/20261030_verification_v11/remote/release_files.py'

REMOTE = r'''
import hashlib,json,os,sys
case,keep=sys.argv[1],json.loads(sys.stdin.read())
d=os.path.join("%s",case)
assert os.path.realpath(d).startswith("/tmp/zhixin_verification_v11_20261030/runs/") and os.path.isdir(d)
out={"case":case,"released":[],"skipped":[]}
idx=os.path.join(d,"RELEASED_INDEX.json")
if os.path.exists(idx):out=json.load(open(idx))
for name,h in keep.items():
    p=os.path.join(d,name)
    if os.path.dirname(os.path.realpath(p))!=os.path.realpath(d) or not os.path.isfile(p) or os.path.islink(p):
        out["skipped"].append([name,"not a regular file in run dir"]);continue
    s=hashlib.sha256()
    with open(p,"rb") as f:
        for c in iter(lambda:f.read(1<<20),b""):s.update(c)
    if s.hexdigest()!=h:out["skipped"].append([name,"hash mismatch"]);continue
    size=os.path.getsize(p);os.remove(p);out["released"].append([name,h,size])
json.dump(out,open(idx+".tmp","w"),indent=1);os.replace(idx+".tmp",idx)
print(json.dumps({"case":case,"released":len(out["released"]),"bytes":sum(x[2] for x in out["released"]),"skipped":out["skipped"]}))
''' % SCR


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()


def release(case):
    a = ROOT / 'runs_archive' / case
    man = json.loads((a / 'ARCHIVE_MANIFEST.json').read_text())
    assert man['status'] == 'verified', case
    cand = {}
    for name, h in man['sha256'].items():
        p = a / name
        if p.stat().st_size > MIN_BYTES:
            assert sha(p) == h, f'local archive changed: {case}/{name}'
            cand[name] = h
    p = subprocess.run(['ssh', '-o', 'BatchMode=yes', 'liqin', f'python3 {RSCRIPT} {case}'], input=json.dumps(cand),
                       capture_output=True, text=True, timeout=1800)
    if p.returncode:
        raise RuntimeError(p.stderr)
    res = json.loads(p.stdout.strip().splitlines()[-1])
    subprocess.run(['scp', '-q', '-o', 'BatchMode=yes', f'liqin:{SCR}/{case}/RELEASED_INDEX.json', str(a / 'RELEASED_INDEX.json')], check=True)
    return res


if __name__ == '__main__':
    for c in sys.argv[1:]:
        print(json.dumps(release(c)))
