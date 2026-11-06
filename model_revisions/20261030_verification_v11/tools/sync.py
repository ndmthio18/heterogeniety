"""Pull remote v11 controller/case status and small analysis outputs; update STATUS.json.

Usage: python sync.py [--analysis]   (never deletes anything locally or remotely)
"""
import json, subprocess, sys, os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
R = '/home/zhixin/Documents/Cooperation_Ali/model_revisions/20261030_verification_v11'
sys.path.insert(0, str(ROOT / 'tools'))
import write_status

SCRIPT = r'''
import json,glob,os,shutil
R="%s"
out={"controller":None,"cases":{}}
p=R+"/controller_status.json"
if os.path.exists(p):out["controller"]=json.load(open(p))
for f in sorted(glob.glob(R+"/status/*.json")):
    d=json.load(open(f));d.pop("spec",None);d.pop("log_tail",None) if d.get("state")=="completed" else None
    out["cases"][os.path.basename(f)[:-5]]=d
pid=(out["controller"] or {}).get("controller_pid")
out["controller_alive"]=bool(pid and os.path.exists("/proc/%%d"%%pid))
for l in open("/proc/meminfo"):
    if l.startswith("MemAvailable"):out["mem_available_GiB"]=int(l.split()[1])/2**20
out["scratch_free_GiB"]=shutil.disk_usage("/tmp").free/2**30
out["home_free_GiB"]=shutil.disk_usage("/home/zhixin").free/2**30
out["A_handoff_remote"]=os.path.exists("/home/zhixin/Documents/Cooperation_Ali/model_revisions/20261030_causal_v10/HANDOFF_READY.json")
print(json.dumps(out))
''' % R


def remote():
    p = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', 'liqin', 'python3 -'], input=SCRIPT,
                       capture_output=True, text=True, timeout=60)
    if p.returncode:
        raise RuntimeError(p.stderr)
    return json.loads(p.stdout)


def pull_analysis():
    (ROOT / 'remote_analysis').mkdir(exist_ok=True)
    subprocess.run(['scp', '-r', '-q', '-o', 'BatchMode=yes', f'liqin:{R}/analysis/.', str(ROOT / 'remote_analysis')], timeout=600, check=True)
    subprocess.run(['scp', '-r', '-q', '-o', 'BatchMode=yes', f'liqin:{R}/status/.', str(ROOT / 'remote_status')], timeout=120, check=True)


if __name__ == '__main__':
    d = remote()
    (ROOT / 'logs').mkdir(exist_ok=True)
    (ROOT / 'logs' / 'last_remote_status.json').write_text(json.dumps(d, indent=1))
    if '--analysis' in sys.argv:
        (ROOT / 'remote_status').mkdir(exist_ok=True)
        pull_analysis()
    c = d['controller'] or {}
    cur = (c.get('current') or {}).get('case')
    cs = d['cases'].get(cur, {}) if cur else {}
    upd = dict(controller_pid=c.get('controller_pid'), controller_alive=d['controller_alive'], controller_state=c.get('state'),
               case=cur, solver_pid=cs.get('solver_pid'), reached_hours=cs.get('reached_evaporation_h'),
               remote_resources={k: round(d[k], 2) for k in ['mem_available_GiB', 'scratch_free_GiB', 'home_free_GiB']},
               remote_cases={k: {q: v.get(q) for q in ['state', 'reached_evaporation_h', 'wall_h', 'peak_rss_GiB', 'failure_reason']} for k, v in d['cases'].items()})
    if '--no-status' not in sys.argv:
        write_status.update(**upd)
    print(json.dumps(upd, indent=1))
