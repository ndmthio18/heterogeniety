"""Background waiter: polls liqin every 50 s; exits when any v11 case state changes,
A's remote stage/completed list changes, or the time budget is spent.
Usage: python wait_event.py [max_hours]
"""
import json, subprocess, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sync

A_STATUS = '/home/zhixin/Documents/Cooperation_Ali/model_revisions/20261030_causal_v10/STATUS_remote.json'


def a_state():
    p = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', 'liqin', f'cat {A_STATUS}'], capture_output=True, text=True, timeout=60)
    try:
        d = json.loads(p.stdout)
        return (d.get('stage'), d.get('state'), tuple(d.get('completed', [])), tuple(d.get('failed', [])))
    except Exception:
        return None


def mine():
    d = sync.remote()
    try:
        import write_status
        c = d['controller'] or {}
        cur = (c.get('current') or {}).get('case')
        cs = d['cases'].get(cur, {}) if cur else {}
        write_status.update(case=cur, solver_pid=cs.get('solver_pid'), reached_hours=cs.get('reached_evaporation_h'),
                            controller_pid=c.get('controller_pid'), controller_alive=d['controller_alive'])
    except Exception:
        pass
    return tuple(sorted((k, v.get('state')) for k, v in d['cases'].items())), d['controller_alive']


end = time.time() + float(sys.argv[1] if len(sys.argv) > 1 else 1.9) * 3600
m0, a0 = mine(), a_state()
reason = 'timeout'
while time.time() < end:
    time.sleep(50)
    try:
        m, a = mine(), a_state()
    except Exception as e:
        continue
    if m != m0:
        reason = 'v11_change'
        break
    if a and a0 and a != a0:
        reason = 'A_change'
        break
print(json.dumps({'reason': reason, 'v11': dict(m[0]) if m else None, 'controller_alive': m[1] if m else None, 'A': a[:2] if a else None,
                  'A_completed_tail': list(a[2])[-3:] if a else None, 'A_failed': list(a[3]) if a else None}))
