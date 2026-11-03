"""Slurm-only isolated gates and predictions; no automatic numerical retries."""
from pathlib import Path
import os,sys,json,subprocess,gzip,xml.etree.ElementTree as ET,configparser,hashlib
import numpy as np,pandas as pd
import runner as r
R=Path(__file__).resolve().parent;r.ROOT=R;r.SCRATCH=R/'raw';r.SCRATCH.mkdir(exist_ok=True)
assert os.environ.get('SLURM_JOB_ID'),'Must run inside Slurm'
assert os.environ.get('DUMUX_NUM_THREADS')=='1'
cpus=','.join(map(str,sorted(os.sched_getaffinity(0))))
mode=sys.argv[1];case=sys.argv[2] if len(sys.argv)>2 else 'baseline'
if case=='array':case='B'+os.environ['SLURM_ARRAY_TASK_ID']
status_path=R/'status'/f'{case}_{mode}.json';status_path.parent.mkdir(exist_ok=True)
def status(state,**kw):r.write(status_path,dict(state=state,case=case,stage=mode,utc=r.utc(),job=os.environ['SLURM_JOB_ID'],affinity=cpus,**kw))
def fields(out,seconds):
 pvd=ET.parse(next(out.glob('*.pvd')))
 file=next(e.get('file') for e in pvd.findall('.//DataSet') if abs(float(e.get('timestep'))-seconds)<1e-7)
 p=out/file
 raw=p.read_bytes() if p.exists() else gzip.decompress(p.with_suffix('.vtu.gz').read_bytes())
 root=ET.fromstring(raw);a={e.get('Name'):np.fromstring(e.text or '',sep=' ') for e in root.findall('.//CellData/DataArray') if e.get('NumberOfComponents','1')=='1'}
 order=np.argsort(a['dof_id']);return {k:v[order] for k,v in a.items()}
def compare(out,seconds,strict=True):
 a=fields(out,seconds);ref=np.load(R/'baseline_reference'/f'fields_{seconds}.npz');err={}
 for k in ['p_liq','p_gas','T','S_liq','S_gas','x^NaCl_liq','x^Air_liq','rhoMolar_liq','precipitateVolumeFraction^NaCl']:
  floor=1. if k.startswith(('p_','T','rho')) else 1e-3
  err[k]=float(np.max(abs(a[k]-ref[k]))/max(floor,float(abs(ref[k]).max())))
 err['phase_mismatch_cells']=int(np.sum(a['phase presence']!=ref['phase presence']))
 budget={}
 for f,cols in [('budget.csv',['water_mol','salt_total_mol','coarse_salt_mol','fine_salt_mol','cumulative_interface_adv_mol','cumulative_interface_diff_mol']),('thermal_budget.csv',['energy_J']),('film_budget.csv',['cumulative_reservoir_loss_g'])]:
  x=r.csvread(out/f);y=pd.read_csv(R/'baseline_reference'/f)
  ix=x[np.abs(x.time_s-seconds)<1e-7].iloc[-1];iy=y[np.abs(y.time_s-seconds)<1e-7].iloc[-1]
  for k in cols:budget[k]=float(abs(ix[k]-iy[k])/max(1e-9,float(abs(y[y.time_s<=seconds][k]).max())))
 passed=max(v for k,v in err.items() if k!='phase_mismatch_cells')<1e-7 and err['phase_mismatch_cells']==0 and max(budget.values())<1e-6
 result=dict(time_s=seconds,field_errors=err,budget_errors=budget,passed=passed,interpretation='zero-change numerical regression, not experimental validation')
 r.write(out/f'baseline_comparison_{seconds}.json',result)
 if strict and not passed:
  r.write(R/'BLOCK_PRODUCTION.json',dict(reason='accelerated v13 zero-change regression failed',result=result,utc=r.utc()))
  raise AssertionError(result)
 return result
def hydro_check(out):
 b=r.csvread(out/'budget.csv');t=r.csvread(out/'thermal_budget.csv');a=fields(out,7200);ref=np.load(R/'baseline_reference/fields_0.npz')
 err={k:float(np.max(abs(a[k]-ref[k]))) for k in ['p_liq','S_liq','T','x^NaCl_liq']}
 assert err['p_liq']<5e-5 and err['S_liq']<1e-9 and err['T']<1e-6 and err['x^NaCl_liq']<1e-10,err
 assert abs(float(b.salt_boundary_out_mol_s.iloc[-1]))<1e-12
 for col in ['water_mol','salt_total_mol']:assert float(abs(b[col]-b[col].iloc[0]).max())/abs(b[col].iloc[0])<1e-8
 r.write(out/'hydrostatic_check.json',dict(passed=True,absolute_field_errors=err))
def checkpoint_hook(out,b):
 for h in [24,60,84,96,120,144,174]:
  if b.evaporation_time_h.iloc[-1]<h+1/6:continue
  dest=out/f'checkpoint_{h}.json'
  if dest.exists():continue
  z=b[b.evaporation_time_h<=h].iloc[-1]
  # The model itself checks every accepted step. Checkpoint collection never restarts.
  result={'evaporation_h':h,'last_accepted_h':float(z.evaporation_time_h),'salt_total_mol':float(z.salt_total_mol),'coarse_salt_mol':float(z.coarse_salt_mol),'fine_salt_mol':float(z.fine_salt_mol),'state':'accepted_budget_checkpoint'}
  if case=='B0':result['baseline_comparison']=compare(out,7200+3600*h)
  r.write(dest,result)
r.checkpoint_hook=checkpoint_hook
try:
 status('running')
 if mode=='baseline':
  results=[]
  for name in ['Precipitate_dt30','Precipitate_dt15','Dissolve_dt30','Dissolve_dt15','RemainSolid_dt30','RemainSolid_dt15','Recovery_injected','Baseline_short']:
   z=r.run(name,cpus);assert z['state']=='completed',z;results.append(z)
  for i,j in [(0,1),(2,3),(4,5)]:
   for k in ['final_solid_mol','final_dissolved_mol']:
    x,y=results[i]['acceptance'][k],results[j]['acceptance'][k];assert abs(x-y)<max(1e-9,.005*max(abs(x),abs(y)))
  log=(r.SCRATCH/'runs/Recovery_injected/simulation.log').read_text();assert 'Retrying with time step' in log and 'Nonpositive liquid water fraction' in log
  comparisons=[compare(r.SCRATCH/'runs/Baseline_short',s) for s in [7200,7800]]
  status('passed',results=results,zero_change=comparisons)
 elif mode=='short':
  assert json.loads((R/'status/baseline_baseline.json').read_text())['state']=='passed'
  for suffix in ['_hydro','_short']:
   z=r.run(case+suffix,cpus);assert z['state']=='completed',z
   if suffix=='_hydro':hydro_check(r.SCRATCH/'runs'/(case+suffix))
  subprocess.run([sys.executable,str(R/'native_replay.py'),case+'_short','--pilot'],check=True)
  status('passed',short_acceptance=z['acceptance'],native_pilot='passed')
 elif mode=='production':
  assert json.loads((R/'status/baseline_baseline.json').read_text())['state']=='passed'
  for name in ['B0','B1','B2','B3']:assert json.loads((R/'status'/f'{name}_short.json').read_text())['state']=='passed'
  z=r.run(case,cpus,production=True);assert z['state']=='completed',z
  if case=='B0':compare(r.SCRATCH/'runs'/case,633600)
  subprocess.run([sys.executable,str(R/'native_replay.py'),case],check=True)
  subprocess.run([sys.executable,str(R/'collect_case.py'),case],check=True)
  status('completed',acceptance=z['acceptance'],raw=str(r.SCRATCH/'runs'/case))
 else:raise ValueError(mode)
except Exception as e:status('failed',error=repr(e));raise
