"""User-requested replacement: stop three partial cases, run only 6/7 mm."""
from pathlib import Path
import os,signal,time,json,shutil
from concurrent.futures import ThreadPoolExecutor,as_completed
import parallel_calibrate as p
r=p.r;R=p.R

def alive(pid):
 q=Path(f'/proc/{pid}/stat')
 return q.exists() and q.read_text().split()[2]!='Z'

def main():
 old=2395057
 cases={'Trial01':2364718,'Bracket04mm':2395120,'Bracket12mm':2395121}
 assert Path(f'/proc/{old}/cwd').resolve()==R
 assert b'parallel_calibrate.py' in Path(f'/proc/{old}/cmdline').read_bytes()
 for name,pid in cases.items():
  assert str(R/'raw/runs'/name) in Path(f'/proc/{pid}/cmdline').read_text()
 v=R/'provenance/user_stop_three_cases';v.mkdir(parents=True,exist_ok=False)
 for f in ['calibration_status.json','parallel_deployment.json','parallel_controller.log']:
  shutil.copy2(R/f,v/f)
 for name in cases:
  shutil.copy2(R/(name+'_status.json'),v/(name+'_status.json'))
 os.kill(old,signal.SIGTERM)
 for pid in cases.values():os.kill(pid,signal.SIGTERM)
 deadline=time.monotonic()+30
 while any(alive(pid) for pid in cases.values()) and time.monotonic()<deadline:time.sleep(.5)
 assert not any(alive(pid) for pid in cases.values()),'Solver did not stop; inspect before further action'
 stopped=[]
 for name,pid in cases.items():
  out=R/'raw/runs'/name
  meta=json.loads((R/(name+'_status.json')).read_text())
  b=r.csvread(out/'budget.csv')
  meta.update(state='stopped_by_user',stop_utc=r.utc(),stop_reason='User replaced 4/8.10/12mm with 6/7mm cases',evaporation_time_h=float(b.evaporation_time_h.iloc[-1]),solver_pid=pid)
  # Preserve every last raw field; compression verifies reversible raw SHA256.
  r.compress_closed(out,final=True)
  meta['preserved_files_sha256']={f.name:r.sha(f) for f in out.iterdir() if f.is_file()}
  r.write(out/'user_stop_manifest.json',meta);r.write(R/(name+'_status.json'),meta)
  stopped.append({k:meta[k] for k in ['case','state','evaporation_time_h','solver_pid']})
 r.write(R/'replacement_6_7mm_deployment.json',dict(utc=r.utc(),controller_pid=os.getpid(),stopped_cases=stopped,new_cases={'Film06mm':{'delta_mm':6,'cpus':'0-3'},'Film07mm':{'delta_mm':7,'cpus':'4-7'}},automatic_additional_cases=False))
 history=[];failures=[]
 with ThreadPoolExecutor(max_workers=2) as pool:
  tasks={pool.submit(p.fresh,'Film06mm',.006,'0-3'):'Film06mm',pool.submit(p.fresh,'Film07mm',.007,'4-7'):'Film07mm'}
  while tasks:
   for f in list(tasks):
    if not f.done():continue
    name=tasks.pop(f)
    try:history.append(f.result())
    except Exception as exc:failures.append(dict(case=name,error=repr(exc)))
   p.c.status('replacement_running' if not failures else 'replacement_partial_failure',active=list(tasks.values()),stopped_cases=stopped,history=history,failures=failures)
   if tasks:time.sleep(15)
 r.write(R/'comparison_6_7mm.json',dict(history=history,failures=failures))
 p.c.status('replacement_completed' if not failures else 'failed',history=history,failures=failures,stopped_cases=stopped,automatic_additional_cases=False)

if __name__=='__main__':
 try:main()
 except Exception as exc:p.c.status('failed',error=repr(exc));raise
