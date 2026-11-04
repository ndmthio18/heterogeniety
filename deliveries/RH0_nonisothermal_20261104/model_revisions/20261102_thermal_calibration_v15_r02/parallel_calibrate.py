"""Adopt live Trial01 without restart; evaluate two bracket endpoints concurrently."""
from pathlib import Path
import os,time,json,signal,shutil,subprocess,datetime
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import pandas as pd
import calibrate as c
r=c.r;R=c.R;r.ROOT=R;r.SCRATCH=R/'raw'
OLD_CONTROLLER=2361037
LIVE_SOLVER=2364718

def summary(name,delta):
 out=r.SCRATCH/'runs'/name
 acceptance=r.validate(out)
 e=pd.read_csv(R/'experiment.csv');e=e[(e.time_h>=1)&(e.time_h<=174)]
 f=r.csvread(out/'film_budget.csv')
 assert f.evaporation_time_h.max()>=174-1e-8
 y=np.interp(e.time_h,f.evaporation_time_h,f.cumulative_reservoir_loss_g)
 target=float(e.mass_g.iloc[0]-e.mass_g.iloc[-1]);assert abs(target-51.52)<1e-8
 loss=float(y[-1]-y[0]);rate=np.diff(y)/np.diff(e.time_h);obs=-np.diff(e.mass_g)/np.diff(e.time_h)
 return dict(case=name,delta_m=delta,loss_g=loss,error_fraction=loss/target-1,interval_rate_RMSE_g_h=float(np.sqrt(np.average((rate-obs)**2,weights=np.diff(e.time_h)))),acceptance=acceptance)

def adopt():
 name='Trial01';out=r.SCRATCH/'runs'/name
 meta=json.loads((R/(name+'_status.json')).read_text())
 meta.update(controller_pid=os.getpid(),adopted_without_restart=True)
 start=datetime.datetime.fromisoformat(meta['start_utc']).timestamp()
 while Path(f'/proc/{LIVE_SOLVER}').exists():
  if (out/'run_status.json').exists():break
  if time.time()-start>48*3600 or shutil.disk_usage(R).free<4*1024**3:
   assert str(out) in Path(f'/proc/{LIVE_SOLVER}/cmdline').read_text()
   os.kill(LIVE_SOLVER,signal.SIGTERM)
   raise RuntimeError('Adopted case resource/time limit')
  b=r.csvread(out/'budget.csv');last=b.iloc[-1]
  meta.update(evaporation_time_h=float(last.evaporation_time_h),salt_solid_mol=float(last.salt_solid_mol),updated_utc=r.utc(),scratch_free_GiB=shutil.disk_usage(R).free/1024**3)
  r.write(R/(name+'_status.json'),meta)
  r.compress_closed(out);time.sleep(15)
 result=summary(name,.008100162249880822)
 r.compress_closed(out,final=True)
 meta.update(state='completed',acceptance=result['acceptance'],end_utc=r.utc(),exit_code_unavailable_for_adopted_process=True)
 r.write(out/'run_manifest.json',meta);r.write(R/(name+'_status.json'),meta)
 return result

def fresh(name,delta,cpus):
 c.prepare(name,delta)
 z=r.run(name,cpus,production=True)
 assert z['state']=='completed',z
 return summary(name,delta)

def main():
 assert json.loads((R/'gate_summary.json').read_text())['status']=='passed'
 assert Path(f'/proc/{OLD_CONTROLLER}/cwd').resolve()==R
 assert b'calibrate.py' in Path(f'/proc/{OLD_CONTROLLER}/cmdline').read_bytes()
 assert str(R/'raw/runs/Trial01') in Path(f'/proc/{LIVE_SOLVER}/cmdline').read_text()
 v=R/'provenance/sequential_before_parallel';v.mkdir(parents=True,exist_ok=False)
 for name in ['calibration_status.json','Trial01_status.json','controller.log','calibrate.py']:
  shutil.copy2(R/name,v/name)
 os.kill(OLD_CONTROLLER,signal.SIGTERM)
 # Only the scheduler is replaced. Existing solver retains its PID, input and affinity.
 r.write(R/'parallel_deployment.json',dict(utc=r.utc(),controller_pid=os.getpid(),adopted_solver_pid=LIVE_SOLVER,stopped_scheduler_pid=OLD_CONTROLLER,profiles={'Trial01':dict(delta_mm=8.100162249880822,cpus='8-11'),'Bracket04mm':dict(delta_mm=4,cpus='0-3'),'Bracket12mm':dict(delta_mm=12,cpus='4-7')},max_full_trials=4))
 history=[];failures=[]
 with ThreadPoolExecutor(max_workers=3) as pool:
  pending={pool.submit(adopt):'Trial01',pool.submit(fresh,'Bracket04mm',.004,'0-3'):'Bracket04mm',pool.submit(fresh,'Bracket12mm',.012,'4-7'):'Bracket12mm'}
  while pending:
   for future in list(pending):
    if not future.done():continue
    name=pending.pop(future)
    try:history.append(future.result())
    except Exception as exc:failures.append(dict(case=name,error=repr(exc)))
    r.write(R/'calibration_history.json',history)
   c.status('parallel_running' if not failures else 'parallel_partial_failure',active=list(pending.values()),history=history,failures=failures)
   if pending:time.sleep(15)
 if failures:c.status('failed',history=history,failures=failures);return
 best=min(history,key=lambda z:abs(z['error_fraction']))
 if abs(best['error_fraction'])<=.01:c.status('completed',selected=best,history=history);return
 ordered=sorted(history,key=lambda z:z['delta_m'])
 brackets=[(a,b) for a,b in zip(ordered,ordered[1:]) if a['error_fraction']*b['error_fraction']<0]
 if not brackets:c.status('range_not_bracketed',history=history);return
 a,b=min(brackets,key=lambda ab:ab[1]['delta_m']-ab[0]['delta_m'])
 # One remaining trial within the original four-run cap; secant interpolation bounded by bracket.
 delta=a['delta_m']-a['error_fraction']*(b['delta_m']-a['delta_m'])/(b['error_fraction']-a['error_fraction'])
 assert a['delta_m']<delta<b['delta_m'] and .004<=delta<=.012
 c.status('refinement_running',trial='Refine04',delta_m=delta,bracket_mm=[a['delta_m']*1000,b['delta_m']*1000],history=history)
 history.append(fresh('Refine04',delta,'8-11'));r.write(R/'calibration_history.json',history)
 best=min(history,key=lambda z:abs(z['error_fraction']))
 c.status('completed' if abs(best['error_fraction'])<=.01 else 'trial_limit_reached',selected=best,history=history)

if __name__=='__main__':
 try:main()
 except Exception as exc:c.status('failed',error=repr(exc));raise
