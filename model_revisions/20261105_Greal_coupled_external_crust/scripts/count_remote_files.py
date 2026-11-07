"""Read-only metadata scan; never follows directory symlinks."""
import os,json,time
from collections import defaultdict
root='/WORK/hulm_work'
counts=defaultdict(lambda:[0,0,0])  # files, directories, symlinks/other
errors=[];started=time.time()
for first in sorted(os.scandir(root),key=lambda x:x.name):
    if not first.is_dir(follow_symlinks=False): continue
    stack=[first.path]
    while stack:
        directory=stack.pop()
        try:
            with os.scandir(directory) as it:
                for e in it:
                    rel=os.path.relpath(e.path,root).split(os.sep)
                    keys=[os.path.join(root,*rel[:n]) for n in (1,2,3) if len(rel)>=n]
                    if e.is_dir(follow_symlinks=False): kind=1;stack.append(e.path)
                    elif e.is_file(follow_symlinks=False): kind=0
                    else: kind=2
                    for key in keys: counts[key][kind]+=1
        except OSError as exc: errors.append({'path':directory,'error':str(exc)})
    print(json.dumps({'completed_top':first.path,'counts':counts[first.path],'elapsed_s':round(time.time()-started)}),flush=True)
for depth in (1,2,3):
    rows=[{'path':p,'files':v[0],'directories':v[1],'other':v[2],'entries':sum(v)} for p,v in counts.items() if len(os.path.relpath(p,root).split(os.sep))==depth]
    print(json.dumps({'depth':depth,'largest':sorted(rows,key=lambda r:r['entries'],reverse=True)[:20]}),flush=True)
print(json.dumps({'errors':errors,'elapsed_s':round(time.time()-started)}),flush=True)
