#!/usr/bin/env bash
# Refresh STATUS.json every 30 s until stage $1 is in the remote completed list,
# any stage fails, the controller dies, or $2 seconds elapse.
cd "$(dirname "$0")"
target=$1; limit=${2:-3000}; start=$(date +%s)
while true; do
  line=$(python sync_local.py v10c 2>&1 | tail -1)
  verdict=$(echo "$line" | python -c "
import json,sys
try:d=json.loads(sys.stdin.read())
except Exception:print('sync_error');raise SystemExit
if d['remote_failed']:print('failed',d['remote_failed'])
elif not d['controller_alive']:print('dead',d['stage'])
elif '$target' in d['remote_completed']:print('reached',d['stage'])
else:print('wait',d['stage'],d.get('reached_hours'))")
  echo "$(date +%T) $verdict"
  case "$verdict" in failed*|dead*|reached*) exit 0;; esac
  if [ $(( $(date +%s) - start )) -gt $limit ]; then echo "timeout"; exit 0; fi
  sleep 30
done
