"""Explicit dependency DAG, bounded physical-core placement, no automatic retries."""
from pathlib import Path
import os,sys,json,subprocess,time,datetime,shutil,socket
R=Path(__file__).resolve().parent;assert socket.gethostname()=='frodo'
fd=os.open(R/'supervisor.lock',os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.write(fd,str(os.getpid()).encode());os.close(fd)
CPUS=list(range(4,10));running={};finished={}
tasks={'baseline':('campaign.py','baseline','baseline',[]),'probeG':('campaign_g.py','probe_r02','Gates',[])}
for c in ['B0','B1','B2','B3']:tasks['short_'+c]=('campaign.py','short',c,['baseline'])
tasks['gatesG']=('campaign_g.py','gates','Gates',['baseline','probeG'])
for c in ['B0','B1','B2','B3']:tasks['production_'+c]=('campaign.py','production',c,['short_'+k for k in ['B0','B1','B2','B3']])
for c in ['G1','G2','G3']:tasks['production_'+c]=('campaign_g.py','production',c,['gatesG'])
pending=list(tasks)
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save():
 state='running' if pending or running else ('completed' if all(v['state']=='passed' for v in finished.values()) else 'completed_with_failures')
 d=dict(state=state,utc=utc(),supervisor_pid=os.getpid(),host='frodo',cpu_pool=CPUS,max_parallel=6,short_wall_s=21600,production_wall_s=172800,running={k:dict(pid=v['p'].pid,cpu=v['cpu']) for k,v in running.items()},finished=finished,pending=pending)
 p=R/'supervisor_status.json';tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(d,indent=2));tmp.replace(p)
def launch(key,cpu):
 script,mode,case,_=tasks[key];env=os.environ.copy();env.update(LOCAL_CAMPAIGN_APPROVED='1',CAMPAIGN_JOB_ID='frodo3d_r02_'+key,DUMUX_NUM_THREADS='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
 log=(R/(key+'.log')).open('x');p=subprocess.Popen(['taskset','-c',str(cpu),'nice','-n','10',sys.executable,str(R/script),mode,case],cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 running[key]=dict(p=p,cpu=cpu,log=log)
try:
 while pending or running:
  for key,v in list(running.items()):
   rc=v['p'].poll()
   if rc is None:continue
   v['log'].close();_,mode,case,_=tasks[key];s=R/'status'/f'{case}_{mode}.json';d=json.loads(s.read_text()) if s.exists() else {}
   ok=rc==0 and d.get('state') in ['passed','completed'];finished[key]=dict(state='passed' if ok else 'failed',returncode=rc,status=d.get('state'),utc=utc());del running[key]
  for key in list(pending):
   deps=tasks[key][3]
   if any(dep in finished and finished[dep]['state']!='passed' for dep in deps):finished[key]=dict(state='blocked_dependency',dependencies=deps,utc=utc());pending.remove(key)
  free=[c for c in CPUS if all(v['cpu']!=c for v in running.values())]
  mem=int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:')))/1024**2
  if mem>=8 and shutil.disk_usage(R).free>=30*1024**3:
   for key in list(pending):
    if not free:break
    if all(dep in finished and finished[dep]['state']=='passed' for dep in tasks[key][3]):launch(key,free.pop(0));pending.remove(key)
  save()
  if pending or running:time.sleep(15)
except Exception as e:
 (R/'supervisor_failure.json').write_text(json.dumps(dict(error=repr(e),utc=utc(),children={k:v['p'].pid for k,v in running.items()}),indent=2));raise
