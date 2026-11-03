from pathlib import Path
import os,sys,json,subprocess,configparser,shutil,math,socket
import numpy as np,pandas as pd
import runner as r
from checks import compare,fields,hydro_check
R=Path(__file__).resolve().parent;r.ROOT=R;r.SCRATCH=R/'raw';r.BUILD_DIRECTORY='build_filter_sal';r.SHORT_WALL_S=6*3600
assert (os.environ.get('SLURM_JOB_ID') or (os.environ.get('LOCAL_CAMPAIGN_APPROVED')=='1' and socket.gethostname()=='frodo')) and os.environ.get('DUMUX_NUM_THREADS')=='1'
cpus=','.join(map(str,sorted(os.sched_getaffinity(0))));mode=sys.argv[1];case=sys.argv[2] if len(sys.argv)>2 else 'Gates'
def status(state,**kw):r.write(R/'status'/f'{case}_{mode}.json',dict(case=case,stage=mode,state=state,utc=r.utc(),job=os.environ.get('SLURM_JOB_ID',os.environ.get('CAMPAIGN_JOB_ID')),host=socket.gethostname(),controller_pid=os.getpid(),affinity=cpus,**kw))
def run(name,production=False):
 z=r.run(name,cpus,production=production);assert z['state']=='completed',z;return z
def probe(name):
 out=R/'raw/probes'/(mode+'_'+name);out.mkdir(parents=True,exist_ok=False);cfg=configparser.ConfigParser();cfg.read(R/'inputs'/f'{name}.input')
 for f in [f'{name}.input',cfg['Grid']['File'],cfg['Revision'].get('PortAreaFile','')]:
  if f:shutil.copy2(R/'inputs'/f,out/f)
 with (out/'probe.log').open('w') as log:p=subprocess.run([str(R/'build_filter_sal/test_boundary'),str(out/f'{name}.input')],cwd=out,stdout=log,stderr=subprocess.STDOUT,timeout=600)
 assert p.returncode==0,(out/'probe.log').read_text()[-3000:]
 z=json.loads((out/'boundary_selftest.json').read_text());assert z['passed']
 if name.startswith('G'):
  diam={'G1':.002,'G2':.005,'G3':.01}[name];assert abs(z['port_area_m2']/(math.pi*(diam/2)**2)-1)<1e-10
 return z
try:
 status('running')
 if not mode.startswith('probe'):assert json.loads((R/'status/baseline_baseline.json').read_text())['state']=='passed'
 if mode.startswith('probe'):
  results={name:probe(name) for name in ['B0','G1','G2','G3']}
  status('passed',results=results)
 elif mode=='gates':
  result={};result['zero_probe']=probe('B0');run('Filter_code_zero');result['zero_regression']=compare(R/'raw/runs/Filter_code_zero',7800)
  for name in ['G1','G2','G3']:
   result[name]={'probe':probe(name)};run(name+'_hydro');hydro_check(R/'raw/runs'/(name+'_hydro'));result[name]['short']=run(name+'_short')['acceptance'];status('running',gates_so_far=result)
  # Numerical screens use the same initial state and fixed parameters, no restart.
  for name in ['G2_dt150','G2_z12']:result[name]=run(name)['acceptance']
  rows=[]
  for name in ['G2_short','G2_dt150','G2_z12']:
   b=r.csvread(R/'raw/runs'/name/'material_budgets.csv');f=r.csvread(R/'raw/runs'/name/'film_budget.csv')
   for mat in range(3):
    z=b[b.material==mat].iloc[-1];rows.append(dict(case=name,material=mat,salt_mol=z.salt_mol,water_mol=z.water_mol,energy_J=z.energy_J,reservoir_loss_g=f.cumulative_reservoir_loss_g.iloc[-1]))
  pd.DataFrame(rows).to_csv(R/'results/G2_resolution_screen.csv',index=False)
  status('passed',results=result,resolution='short dt150 and doubled filter vertical layers; no full-window or radial convergence claim')
 elif mode=='production':
  assert json.loads((R/'status/Gates_gates.json').read_text())['state']=='passed'
  z=run(case,production=True)
  subprocess.run([sys.executable,str(R/'collect_case.py'),case],check=True)
  status('completed',acceptance=z['acceptance'])
 else:raise ValueError(mode)
except Exception as e:status('failed',error=repr(e));raise
