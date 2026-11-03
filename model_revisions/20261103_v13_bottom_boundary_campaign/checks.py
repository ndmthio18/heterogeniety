from pathlib import Path
import json,gzip,xml.etree.ElementTree as ET
import numpy as np,pandas as pd
import runner as r
R=Path(__file__).resolve().parent
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
  r.write(R/'BLOCK_PRODUCTION.json',dict(reason='filter-code zero-change regression failed',result=result,utc=r.utc()))
  raise AssertionError(result)
 return result

def hydro_check(out):
 b=r.csvread(out/'budget.csv');t=r.csvread(out/'thermal_budget.csv');a=fields(out,7200);ref=fields(out,0)
 err={k:float(np.max(abs(a[k]-ref[k]))) for k in ['p_liq','S_liq','T','x^NaCl_liq']}
 assert err['p_liq']<5e-5 and err['S_liq']<1e-9 and err['T']<1e-6 and err['x^NaCl_liq']<1e-10,err
 assert abs(float(b.salt_boundary_out_mol_s.iloc[-1]))<1e-12
 for col in ['water_mol','salt_total_mol']:assert float(abs(b[col]-b[col].iloc[0]).max())/abs(b[col].iloc[0])<1e-8
 r.write(out/'hydrostatic_check.json',dict(passed=True,absolute_field_errors=err))
