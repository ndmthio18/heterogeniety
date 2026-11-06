"""Local periodic sync: every PERIOD s update STATUS.json from liqin and pull reduced
analysis/status when the set of completed cases changes. Read-only on remote.
Usage: python monitor_loop.py [hours] [period_s]
"""
import json, sys, time, traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sync, write_status

ROOT = Path(__file__).resolve().parent.parent
hours = float(sys.argv[1]) if len(sys.argv) > 1 else 1.9
period = float(sys.argv[2]) if len(sys.argv) > 2 else 300
end = time.time() + hours * 3600
seen = None
while time.time() < end:
    try:
        d = sync.remote()
        c = d['controller'] or {}
        cur = (c.get('current') or {}).get('case')
        cs = d['cases'].get(cur, {}) if cur else {}
        done = sorted(k for k, v in d['cases'].items() if v.get('state') == 'completed')
        failed = sorted(k for k, v in d['cases'].items() if v.get('state') in ('failed', 'interrupted'))
        write_status.update(controller_pid=c.get('controller_pid'), controller_alive=d['controller_alive'], controller_state=c.get('state'),
                            case=cur, solver_pid=cs.get('solver_pid'), reached_hours=cs.get('reached_evaporation_h'),
                            remote_completed_runs=done, remote_failed_runs=failed,
                            remote_resources={k: round(d[k], 2) for k in ['mem_available_GiB', 'scratch_free_GiB', 'home_free_GiB']})
        if done != seen:
            (ROOT / 'remote_status').mkdir(exist_ok=True)
            sync.pull_analysis()
            seen = done
        with open(ROOT / 'logs' / 'monitor_loop.log', 'a') as f:
            f.write(json.dumps({'t': time.strftime('%Y-%m-%dT%H:%M:%S'), 'case': cur, 'h': cs.get('reached_evaporation_h'), 'done': len(done), 'failed': failed}) + '\n')
    except Exception:
        with open(ROOT / 'logs' / 'monitor_loop.log', 'a') as f:
            f.write(traceback.format_exc() + '\n')
    time.sleep(period)
