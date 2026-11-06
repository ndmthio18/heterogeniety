"""One bounded poll (<=45 s), compact output; updates STATUS via sync."""
import json, subprocess, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import sync, write_status
t0 = time.monotonic(); d0 = None
while True:
    d = sync.remote(); c = d['controller'] or {}
    states = {k: v.get('state') for k, v in d['cases'].items()}
    if d0 is not None and states != d0: break
    d0 = states
    if time.monotonic() - t0 > 30: break
    time.sleep(12)
cur = (c.get('current') or {}).get('case'); cs = d['cases'].get(cur, {}) if cur else {}
write_status.update(case=cur, solver_pid=cs.get('solver_pid'), reached_hours=cs.get('reached_evaporation_h'),
                    controller_pid=c.get('controller_pid'), controller_alive=d['controller_alive'],
                    remote_resources={k: round(d[k], 2) for k in ['mem_available_GiB', 'scratch_free_GiB', 'home_free_GiB']})
n = sum(1 for v in states.values() if v == 'completed')
print(json.dumps({'utc': time.strftime('%H:%M:%S', time.gmtime()), 'cur': cur, 'h': cs.get('reached_evaporation_h'), 'solver': cs.get('solver_pid'),
                  'ctl_alive': d['controller_alive'], 'completed_total': n, 'failed': [k for k, v in states.items() if v in ('failed', 'interrupted')],
                  'scratch': round(d['scratch_free_GiB'], 1)}))
