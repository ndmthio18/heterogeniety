"""Separate 2D gates and case predictions; all launches require Slurm and frozen input hashes."""
from pathlib import Path
import os,sys,json,subprocess,configparser,shutil,gzip,socket,xml.etree.ElementTree as ET
import numpy as np,pandas as pd
import runner as r
R=Path(__file__).resolve().parent;r.ROOT=R;r.SCRATCH=R/'raw';r.BUILD_DIRECTORY='build_sal';r.SHORT_WALL_S=6*3600
r.SCRATCH.mkdir(exist_ok=True);(R/'status').mkdir(exist_ok=True)
local=os.environ.get('LOCAL_CAMPAIGN_APPROVED')=='1' and socket.gethostname()=='frodo'
assert (os.environ.get('SLURM_JOB_ID') or local) and os.environ.get('DUMUX_NUM_THREADS')=='1'
cpu=','.join(map(str,sorted(os.sched_getaffinity(0))));mode=sys.argv[1];case=sys.argv[2] if len(sys.argv)>2 else 'core'
if case=='array':case='B'+os.environ['SLURM_ARRAY_TASK_ID']
def status(state,**kw):r.write(R/'status'/f'{case}_{mode}.json',dict(state=state,case=case,mode=mode,job=os.environ.get('SLURM_JOB_ID',os.environ.get('CAMPAIGN_JOB_ID')),host=socket.gethostname(),pid=os.getpid(),cpu=cpu,utc=r.utc(),**kw))
def run(name,prod=False):
 z=r.run(name,cpu,production=prod);assert z['state']=='completed',z;return z
def fields(name,t):
 d=R/'raw/runs'/name;es=ET.parse(d/(name+'.pvd')).findall('.//DataSet');f=next(e.get('file') for e in es if abs(float(e.get('timestep'))-t)<1e-7);p=d/(f+'.gz');root=ET.fromstring(gzip.decompress(p.read_bytes()));a={e.get('Name'):np.fromstring(e.text or '',sep=' ') for e in root.findall('.//CellData/DataArray') if e.get('NumberOfComponents','1')=='1'};idx=np.argsort(a['dof_id']);return {k:v[idx] for k,v in a.items()}
def hydro(name):
 a=fields(name,0);b=fields(name,7200);err={k:float(abs(a[k]-b[k]).max()) for k in ['p_liq','S_liq','T','x^NaCl_liq']}
 assert err['p_liq']<5e-5 and err['S_liq']<1e-9 and err['T']<1e-6 and err['x^NaCl_liq']<1e-10,err
 q=r.csvread(R/'raw/runs'/name/'budget.csv');assert abs(q.salt_boundary_out_mol_s.iloc[-1])<1e-12
 for k in ['water_mol','salt_total_mol']:assert abs(q[k]-q[k].iloc[0]).max()/abs(q[k].iloc[0])<1e-8
 r.write(R/'raw/runs'/name/'hydro_check.json',dict(passed=True,errors=err));return err
def probe(name):
 d=R/'raw/probes'/name;d.mkdir(parents=True,exist_ok=False);c=configparser.ConfigParser();c.read(R/'inputs'/f'{name}.input')
 for f in [name+'.input',c['Grid']['File']]:shutil.copy2(R/'inputs'/f,d/f)
 with (d/'probe.log').open('w') as log:p=subprocess.run([str(R/'build_sal/test_boundary'),str(d/(name+'.input'))],cwd=d,stdout=log,stderr=subprocess.STDOUT,timeout=600)
 assert p.returncode==0,(d/'probe.log').read_text()[-3000:]
 a=json.loads((d/'boundary_selftest.json').read_text());assert a['passed']
 expected=np.pi*.025**2 if name.startswith('B') else np.pi*{'G1':.001,'G2':.0025,'G3':.005}[name]**2
 assert abs(a['port_area_m2']/expected-1)<1e-10,a
 return a
def reduce(name):subprocess.run([sys.executable,str(R/'analyze.py'),name],check=True)
def screen(base,others):
 a=pd.read_csv(R/'results'/base/'profiles_history.csv');a=a[abs(a.time_h-2)<1e-7].sort_values(['material','depth_mm']);rows=[]
 for name in others:
  b=pd.read_csv(R/'results'/name/'profiles_history.csv');b=b[abs(b.time_h-2)<1e-7].sort_values(['material','depth_mm'])
  for mat in ['F36','W3']:
   x=a[a.material==mat].C_M.to_numpy();y=b[b.material==mat].C_M.to_numpy();err=float(np.sqrt(np.mean((x-y)**2))/max(np.mean(abs(x)),1.))
   rows.append(dict(reference=base,comparison=name,material=mat,normalized_profile_RMSE=err));assert err<.05,rows[-1]
 pd.DataFrame(rows).to_csv(R/'results'/f'{base}_numerical_screen.csv',index=False)
 return rows
try:
 status('running')
 assert not (R.parent/'BLOCK_PRODUCTION.json').exists(),'3D baseline mismatch blocks shared-physics launch'
 if mode=='probe':status('passed',results={k:probe(k) for k in ['B0','G1','G2','G3']})
 elif mode=='core':
  assert json.loads((R.parent/'status/baseline_baseline.json').read_text())['state']=='passed'
  results=[r.selftest(k,cpu) for k in ['Selftest_fixed','Selftest_coupled']]
  pairs=[('Precipitate_dt30','Precipitate_dt15'),('Dissolve_dt30','Dissolve_dt15'),('RemainSolid_dt30','RemainSolid_dt15')]
  for pair in pairs:
   z=[run(k) for k in pair];results+=z
   for key in ['final_solid_mol','final_dissolved_mol']:
    a,b=[v['acceptance'][key] for v in z];assert abs(a-b)<max(1e-9,.005*max(abs(a),abs(b)))
  results.append(run('Recovery_injected'));log=(R/'raw/runs/Recovery_injected/simulation.log').read_text();assert 'Retrying with time step' in log and 'Nonpositive liquid water fraction' in log
  # Actual native boundary donor tests precede any time-dependent evaporation case.
  probes={k:probe(k) for k in ['B0','G1','G2','G3']}
  run('B0_hydro');hydro('B0_hydro')
  for name in ['B0_short','B0_width2','B0_dt150','B0_refined']:run(name);reduce(name)
  screen('B0_short',['B0_dt150','B0_refined'])
  a=fields('B0_short',14400);b=fields('B0_width2',14400)
  errors={k:float(abs(a[k]-b[k]).max()/max(float(abs(a[k]).max()),1e-3)) for k in ['p_liq','T','x^NaCl_liq','S_liq']};assert max(errors.values())<1e-7,errors
  for f,col in [('budget.csv','salt_total_mol'),('thermal_budget.csv','energy_J'),('film_budget.csv','cumulative_reservoir_loss_g')]:
   x=r.csvread(R/'raw/runs/B0_short'/f)[col].iloc[-1];y=r.csvread(R/'raw/runs/B0_width2'/f)[col].iloc[-1];assert abs(y/2-x)/max(abs(x),1e-10)<1e-7
  status('passed',results=results,donor_tests=probes,extrusion_scaling_errors=errors,numerical_screens='B0 dt150 and refined4000→16000 cells; compare before physical claims')
 elif mode=='case':
  assert json.loads((R/'status/core_core.json').read_text())['state']=='passed'
  if case!='B0':run(case+'_hydro');hydro(case+'_hydro');run(case+'_short');reduce(case+'_short')
  z=run(case,True);reduce(case);status('completed',acceptance=z['acceptance'])
 elif mode=='gatesG':
  assert json.loads((R/'status/core_core.json').read_text())['state']=='passed'
  for name in ['G1','G2','G3']:run(name+'_hydro');hydro(name+'_hydro');run(name+'_short');reduce(name+'_short')
  for name in ['G1_dt150','G1_refined','G2_dt150','G2_refined']:run(name);reduce(name)
  for name in ['G1','G2']:screen(name+'_short',[name+'_dt150',name+'_refined'])
  status('passed',screens='short targeted dt/spatial screens; not full convergence')
 elif mode=='caseG':
  assert json.loads((R/'status/core_gatesG.json').read_text())['state']=='passed'
  z=run(case,True);reduce(case);status('completed',acceptance=z['acceptance'])
 else:raise ValueError(mode)
except Exception as e:status('failed',error=repr(e));raise
