from pathlib import Path
import os,json,sys,configparser
import numpy as np
import runner as r
R=Path(__file__).resolve().parent;r.ROOT=R;r.SCRATCH=R/'raw';r.SCRATCH.mkdir(exist_ok=True)
cpus=','.join(map(str,sorted(os.sched_getaffinity(0))))
assert len(os.sched_getaffinity(0))>=4
assert os.environ.get('SLURM_JOB_ID'),'Only run in Slurm allocation'
mode=sys.argv[1]
def status(**kw):r.write(R/(mode+'_status.json'),dict(utc=r.utc(),job_id=os.environ['SLURM_JOB_ID'],cpus=cpus,**kw))
try:
 if mode=='gates':
  status(state='running');results=[]
  for name in ['Precipitate_dt30','Precipitate_dt15','Dissolve_dt30','Dissolve_dt15','RemainSolid_dt30','RemainSolid_dt15','Recovery_injected','Regression_equilibrium']:
   z=r.run(name,cpus);assert z['state']=='completed',z;results.append(z)
  for a,b in [(0,1),(2,3),(4,5)]:
   for k in ['final_solid_mol','final_dissolved_mol']:
    x,y=results[a]['acceptance'][k],results[b]['acceptance'][k];assert abs(x-y)<max(1e-9,.005*max(abs(x),abs(y)))
  log=(r.SCRATCH/'runs/Recovery_injected/simulation.log').read_text();assert 'Retrying with time step' in log and 'Nonpositive liquid water fraction' in log
  errors={}
  for filename,ref,columns in [('budget.csv','reference_budget.csv',['water_mol','salt_total_mol','coarse_salt_mol','fine_salt_mol','C_max_mol_L','S_min']),('thermal_budget.csv','reference_thermal.csv',['T_min_K','T_max_K','energy_J'])]:
   a=r.csvread(r.SCRATCH/'runs/Regression_equilibrium'/filename);b=r.csvread(R/ref)
   assert abs(a.time_s.iloc[-1]-b.time_s.iloc[-1])<1e-8
   for k in columns:errors[k]=float(abs(a[k].iloc[-1]-b[k].iloc[-1])/max(abs(b[k]).max(),1e-12))
  assert max(errors.values())<1e-7,errors
  status(state='passed',errors=errors,results=results)
 else:
  assert json.loads((R/'gates_status.json').read_text())['state']=='passed'
  delta=float(sys.argv[2]);assert .007<=delta<=.008
  cfg=configparser.ConfigParser();cfg.optionxform=str;cfg.read(R/'inputs/RH0_174h.input')
  cfg['Problem']['Name']=mode;cfg['Revision']['FilmThickness']=str(delta)
  with (R/'inputs'/f'{mode}.input').open('w') as f:cfg.write(f)
  status(state='running',delta_m=delta)
  z=r.run(mode,cpus,production=True);assert z['state']=='completed',z
  import pandas as pd
  e=pd.read_csv(R/'experiment.csv');e=e[(e.time_h>=1)&(e.time_h<=174)]
  f=r.csvread(r.SCRATCH/'runs'/mode/'film_budget.csv');assert f.evaporation_time_h.max()>=174-1e-8
  y=np.interp(e.time_h,f.evaporation_time_h,f.cumulative_reservoir_loss_g);loss=float(y[-1]-y[0]);target=float(e.mass_g.iloc[0]-e.mass_g.iloc[-1]);assert abs(target-51.52)<1e-8
  dt=np.diff(e.time_h);rmse=float(np.sqrt(np.average((np.diff(y)/dt+np.diff(e.mass_g)/dt)**2,weights=dt)))
  status(state='completed',delta_m=delta,loss_g=loss,error_fraction=loss/target-1,rate_RMSE_g_h=rmse,acceptance=z['acceptance'])
except Exception as exc:status(state='failed',error=repr(exc));raise
