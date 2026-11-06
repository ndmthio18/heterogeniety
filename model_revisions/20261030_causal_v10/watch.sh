#!/usr/bin/env bash
# Refresh local STATUS.json every 30 s; exit when the remote stage changes,
# a stage fails, the controller stops, or after $1 seconds (default 3000).
cd "$(dirname "$0")"
limit=${1:-3000}; start=$(date +%s)
first=$(python sync_local.py v10c 2>&1 | tail -1)
stage0=$(echo "$first" | python -c "import json,sys;d=json.loads(sys.stdin.read());print(d['stage'],len(d['remote_completed']),len(d['remote_failed']))")
echo "start: $stage0"
while true; do
  sleep 30
  line=$(python sync_local.py v10c 2>&1 | tail -1)
  now=$(echo "$line" | python -c "import json,sys;d=json.loads(sys.stdin.read());print(d['stage'],len(d['remote_completed']),len(d['remote_failed']),d['controller_alive'])" 2>/dev/null || echo "sync_error")
  echo "$(date +%T) $now"
  case "$now" in *False*|sync_error) echo "controller not alive or sync error: $line"; exit 0;; esac
  set -- $now
  if [ "$1 $2 $3" != "$stage0" ]; then echo "changed: $line"; exit 0; fi
  if [ $(( $(date +%s) - start )) -gt $limit ]; then echo "timeout: $line"; exit 0; fi
done
