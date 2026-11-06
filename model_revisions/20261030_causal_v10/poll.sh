#!/usr/bin/env bash
# One monitoring tick (<60 s): refresh STATUS.json, print one compact line, pad to ~55 s.
cd "$(dirname "$0")"; t0=$(date +%s)
python sync_local.py v10c 2>&1 | tail -1 | python -c "
import json,sys
try:d=json.loads(sys.stdin.read());print(d['stage'],d.get('reached_hours'),'alive' if d['controller_alive'] else 'DEAD','failed:',d['remote_failed'])
except Exception as e:print('sync_error',e)"
while [ $(( $(date +%s) - t0 )) -lt 50 ]; do sleep 5; done
