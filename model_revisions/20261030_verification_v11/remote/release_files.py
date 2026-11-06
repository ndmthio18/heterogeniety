"""Remote half of tools/release_remote.py: delete individually re-verified files of one v11 run."""
import hashlib,json,os,sys
case,keep=sys.argv[1],json.loads(sys.stdin.read())
d=os.path.join("/tmp/zhixin_verification_v11_20261030/runs",case)
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
