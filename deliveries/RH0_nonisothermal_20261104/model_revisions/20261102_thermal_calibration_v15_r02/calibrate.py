from pathlib import Path
import json,subprocess,os,hashlib,configparser,datetime,shutil
import numpy as np
import pandas as pd
import runner as r
R=Path(__file__).resolve().parent
P=Path('/temp/zhixin/heterogeneity_performance_v14_20261102')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def status(state,**kw):r.write(R/'calibration_status.json',dict(state=state,utc=r.utc(),controller_pid=os.getpid(),**kw))
def prepare(name,delta,base='RH0_174h'):
 c=configparser.ConfigParser();c.optionxform=str;c.read(R/'inputs'/f'{base}.input')
 c['Problem']['Name']=name;c['Revision']['FilmThickness']=str(delta)
 with (R/'inputs'/f'{name}.input').open('w') as f:c.write(f)
def main():
 status('building')
 b=R/'build_ni1';b.mkdir(exist_ok=False)
 parent=P/'build_cached_ni1'
 manifest=json.loads((parent/'build_manifest.json').read_text())
 assert sha(parent/'heterogeneity_revised')==manifest['binary_sha256']
 for p in (R/'source').rglob('*'):
  if p.is_file():assert sha(p)==sha(P/'source_cached'/p.relative_to(R/'source'))
 shutil.copy2(parent/'heterogeneity_revised',b/'heterogeneity_revised')
 shutil.copy2(parent/'build_manifest.json',b/'parent_build_manifest.json')
 shutil.copy2(parent/'compile_command.json',b/'parent_compile_command.json')
 r.write(b/'build_manifest.json',dict(binary_sha256=sha(b/'heterogeneity_revised'),source_sha256={p.relative_to(R).as_posix():sha(p) for p in (R/'source').rglob('*') if p.is_file()},parent_build=str(parent),parent_manifest_sha256=sha(parent/'build_manifest.json'),host='frodo',threads=4,cpu_set='8-11'))
 r.ROOT=R;r.SCRATCH=R/'raw';r.SCRATCH.mkdir(exist_ok=False)
 status('gates_running')
 gates=[]
 for name in ['Precipitate_dt30','Precipitate_dt15','Dissolve_dt30','Dissolve_dt15','RemainSolid_dt30','RemainSolid_dt15','Regression_equilibrium','Recovery_injected']:
  z=r.run(name,"8-11");gates.append(z);assert z['state']=='completed',z
 for a,b in [(0,1),(2,3),(4,5)]:
  for k in ['final_solid_mol','final_dissolved_mol']:
   x,y=gates[a]['acceptance'][k],gates[b]['acceptance'][k]
   assert abs(x-y)<max(1e-9,.005*max(abs(x),abs(y)))
 log=(r.SCRATCH/'runs/Recovery_injected/simulation.log').read_text()
 assert 'Retrying with time step' in log and 'Nonpositive liquid water fraction' in log
 reference=Path('/temp/zhixin/heterogeneity_thermal_calibration_v15_20261102/raw/runs/Regression_equilibrium')
 assert json.loads((reference/'run_status.json').read_text())['status']=='completed'
 a=r.csvread(r.SCRATCH/'runs/Regression_equilibrium/budget.csv');b=r.csvread(reference/'budget.csv')
 columns=['water_mol','salt_total_mol','coarse_salt_mol','fine_salt_mol','C_max_mol_L','S_min']
 assert abs(a.time_s.iloc[-1]-b.time_s.iloc[-1])<1e-8
 errors={k:float(abs(a[k].iloc[-1]-b[k].iloc[-1])/max(abs(b[k]).max(),1e-12)) for k in columns}
 ta=r.csvread(r.SCRATCH/'runs/Regression_equilibrium/thermal_budget.csv');tb=r.csvread(reference/'thermal_budget.csv')
 for k in ['T_min_K','T_max_K','energy_J']:
  errors[k]=float(abs(ta[k].iloc[-1]-tb[k].iloc[-1])/max(abs(tb[k]).max(),1e-12))
 assert max(errors.values())<1e-7,errors
 r.write(R/'gate_summary.json',dict(status='passed',gates=gates,reference=str(reference),reference_budget_sha256=sha(reference/'budget.csv'),endpoint_relative_errors=errors,tolerance=1e-7))
 e=pd.read_csv(R/'experiment.csv');e=e[(e.time_h>=1)&(e.time_h<=174)]
 target=float(e.mass_g.iloc[0]-e.mass_g.iloc[-1]);assert abs(target-51.52)<1e-8
 delta=.008100162249880822;history=[]
 for i in range(1,5):
  name=f'Trial{i:02d}';prepare(name,delta)
  status('trial_running',trial=name,delta_m=delta,history=history)
  z=r.run(name,"8-11",production=True);assert z['state']=='completed',z
  f=pd.read_csv(r.SCRATCH/'runs'/name/'film_budget.csv')
  y=np.interp(e.time_h,f.evaporation_time_h,f.cumulative_reservoir_loss_g);loss=float(y[-1]-y[0])
  rates=np.diff(y)/np.diff(e.time_h);observed=-np.diff(e.mass_g)/np.diff(e.time_h)
  err=loss/target-1
  history.append(dict(case=name,delta_m=delta,loss_g=loss,error_fraction=err,interval_rate_RMSE_g_h=float(np.sqrt(np.average((rates-observed)**2,weights=np.diff(e.time_h))))))
  r.write(R/'calibration_history.json',history)
  if abs(err)<=.01:
   status('completed',selected=history[-1],history=history);return
  proposal=delta*loss/target
  low=[h for h in history if h['error_fraction']>0];high=[h for h in history if h['error_fraction']<0]
  if low and high:proposal=(max(h['delta_m'] for h in low)+min(h['delta_m'] for h in high))/2
  assert .004<=proposal<=.012,('thickness_range_exceeded',proposal)
  delta=proposal
 status('trial_limit_reached',history=history)
if __name__=='__main__':
 try:main()
 except Exception as exc:status('failed',error=repr(exc));raise
