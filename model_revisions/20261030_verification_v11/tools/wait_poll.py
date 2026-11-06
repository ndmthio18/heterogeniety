"""Bounded wait (<=55 s) that returns early when a watched condition changes.

Watches: local A HANDOFF_READY.json existence, the remote state of every v11 case
and the controller current case. Prints a compact status line, updates STATUS.json.
Usage: python wait_poll.py [seconds<=55]
"""
import json, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sync

ROOT = Path(__file__).resolve().parent.parent
A = ROOT.parent / '20261030_causal_v10'


def snap():
    d = sync.remote()
    c = d['controller'] or {}
    return d, ((c.get('current') or {}).get('case'), tuple(sorted((k, v.get('state')) for k, v in d['cases'].items())),
               (A / 'HANDOFF_READY.json').exists(), d.get('A_handoff_remote'))


limit = min(float(sys.argv[1]) if len(sys.argv) > 1 else 55, 55)
t0 = time.monotonic()
d, s0 = snap()
while time.monotonic() - t0 < limit - 12:
    time.sleep(10)
    d, s = snap()
    if s != s0:
        break
c = d['controller'] or {}
cur = (c.get('current') or {}).get('case')
cs = d['cases'].get(cur, {}) if cur else {}
a_stage = json.loads((A / 'STATUS.json').read_text()).get('stage') if (A / 'STATUS.json').exists() else None
print(json.dumps({'current': cur, 'reached_h': cs.get('reached_evaporation_h'), 'wall_h': round(cs.get('wall_h') or 0, 3),
                  'states': {k: v.get('state') for k, v in d['cases'].items()}, 'A_stage': a_stage,
                  'A_handoff': (A / 'HANDOFF_READY.json').exists(), 'A_handoff_remote': d.get('A_handoff_remote'), 'mem': round(d['mem_available_GiB'], 1),
                  'scratch': round(d['scratch_free_GiB'], 1), 'home': round(d['home_free_GiB'], 2)}))
