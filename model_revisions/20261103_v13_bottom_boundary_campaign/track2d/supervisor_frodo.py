"""Bounded local queue on an authorized compute workstation without a scheduler.
One core gate precedes independent B cases plus G gates; six physical CPUs maximum.
"""
from pathlib import Path
import os,sys,json,subprocess,time,datetime,shutil,socket
R=Path(__file__).resolve().parent;assert socket.gethostname()=='frodo'
lock=R/'supervisor.lock';fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.write(fd,str(os.getpid()).encode());os.close(fd)
CPUS=list(range(4,10));running={};finished={};queue=[('core','core')];stage=0
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(state,**kw):
 d=dict(state=state,utc=utc(),supervisor_pid=os.getpid(),host='frodo',max_parallel=6,cpu_pool=CPUS,running={k:dict(pid=v['p'].pid,cpu=v['cpu'],mode=v['mode'],case=v['case']) for k,v in running.items()},finished=finished,queued=queue,**kw);p=R/'supervisor_status.json';q=p.with_suffix('.tmp');q.write_text(json.dumps(d,indent=2));q.replace(p)
def launch(mode,case,cpu):
 ident=mode+'_'+case;env=os.environ.copy();env.update(LOCAL_CAMPAIGN_APPROVED='1',CAMPAIGN_JOB_ID='frodo_'+ident,DUMUX_NUM_THREADS='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
 log=(R/(ident+'.log')).open('w');p=subprocess.Popen(['taskset','-c',str(cpu),'nice','-n','10',sys.executable,str(R/'controller.py'),mode,case],cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 running[ident]=dict(p=p,cpu=cpu,mode=mode,case=case,log=log)
try:
 while queue or running:
  free=[c for c in CPUS if all(v['cpu']!=c for v in running.values())]
  mem=int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:')))/1024**2
  if mem<8 or shutil.disk_usage(R).free<20*1024**3:
   save('admission_paused',reason='memory<8GiB or disk<20GiB; current children keep their own guards')
  else:
   while queue and free:
    mode,case=queue.pop(0);launch(mode,case,free.pop(0))
  for k,v in list(running.items()):
   rc=v['p'].poll()
   if rc is None:continue
   v['log'].close();statefile=R/'status'/f'{v["case"]}_{v["mode"]}.json';s=json.loads(statefile.read_text()) if statefile.exists() else {}
   success=rc==0 and s.get('state') in ['passed','completed'];finished[k]=dict(returncode=rc,state=s.get('state','missing'),utc=utc(),cpu=v['cpu']);del running[k]
   if v['mode']=='core':
    if not success:queue=[];save('failed_core');raise RuntimeError('Core acceptance failed; no production launched')
    queue += [('case',n) for n in ['B0','B1','B2','B3']]+[('gatesG','core')];stage=1
   elif v['mode']=='gatesG' and success:queue += [('caseG',n) for n in ['G1','G2','G3']]
  save('running' if running or queue else ('completed' if all(v['returncode']==0 for v in finished.values()) else 'completed_with_failures'))
  if running or queue:time.sleep(20)
except Exception as e:save('failed',error=repr(e));raise
