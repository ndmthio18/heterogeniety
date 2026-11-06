"""Mirror the remote v10 controller state (status, stage results, handoff,
reduced results) into this directory and refresh STATUS.json atomically.
Large raw fields stay on liqin unless --fields is given."""
from pathlib import Path
import datetime,io,json,subprocess,sys,tarfile
L=Path(__file__).resolve().parent
REMOTE='/home/zhixin/Documents/Cooperation_Ali/model_revisions/20261030_causal_v10'
def ssh(cmd,binary=False):
 p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=20','liqin',cmd],capture_output=True)
 if p.returncode:raise RuntimeError(p.stderr.decode(errors='replace'))
 return p.stdout if binary else p.stdout.decode()
def pull(paths):
 data=ssh(f'cd {REMOTE} && tar cf - --ignore-failed-read {" ".join(paths)} 2>/dev/null; true',binary=True)
 if data:
  with tarfile.open(fileobj=io.BytesIO(data)) as t:t.extractall(L,filter='data')
def main():
 tag=sys.argv[1] if len(sys.argv)>1 else 'v10c'
 remote=json.loads(ssh(f'cat {REMOTE}/STATUS_remote.json'))
 alive=ssh(f'ps -eo args | grep "[c]ampaign.py {tag}" || true').split()
 hand=L/'HANDOFF_READY.json'
 pull(['STATUS_remote.json',f'stages/{tag}',f'results/{tag}',f'build_{tag}/build_manifest.json',f'build_{tag}/build_status.json','campaign_*.out','STATUS_remote_crash.json']+([] if hand.exists() else ['HANDOFF_READY.json']))
 handoff_check=None
 if hand.exists():
  import hashlib
  r=ssh(f'sha256sum {REMOTE}/HANDOFF_READY.json').split()[0];handoff_check=r==hashlib.sha256(hand.read_bytes()).hexdigest()
 st=json.loads((L/'STATUS.json').read_text())
 st.update(stage=remote.get('stage'),case=remote.get('case'),reached_hours=remote.get('reached_hours'),solver_pid=remote.get('solver_pid'),
  controller_pid=remote.get('controller_pid'),controller_alive=bool(alive),remote_state=remote.get('state'),
  remote_completed=sorted(set(remote.get('completed',[]))),remote_failed=sorted(set(remote.get('failed',[]))),
  updated_utc=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
  remote_resources={k:remote.get(k) for k in ['mem_available_gib','scratch_free_gib','peak_rss_MiB','wall_min']},handoff_remote_equals_local=handoff_check)
 tmp=L/'STATUS.json.tmp';tmp.write_text(json.dumps(st,indent=2));tmp.replace(L/'STATUS.json')
 print(json.dumps({k:st[k] for k in ['stage','case','reached_hours','remote_state','controller_alive','remote_completed','remote_failed']}))
if __name__=='__main__':main()
