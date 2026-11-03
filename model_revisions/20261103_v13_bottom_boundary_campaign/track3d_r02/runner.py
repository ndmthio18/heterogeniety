"""Bounded gates followed by one 174-h prediction; never silently retry failures."""
from pathlib import Path
import os,sys,json,csv,time,hashlib,datetime,subprocess,shutil,configparser,gzip
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parent
SCRATCH=Path('/tmp/zhixin_cylinder_thermal_v13_20261102')
PARENT=ROOT.parent/'20261030_cylinder_film_v08'
RESUME_VALIDATION_REPAIR='--resume-validation-repair' in sys.argv
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for chunk in iter(lambda:f.read(2**20),b''):h.update(chunk)
 return h.hexdigest()
def write(p,d):
 p=Path(p);tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(d,indent=2));tmp.replace(p)
def csvread(p):
 lines=Path(p).read_text().splitlines();width=len(lines[0].split(','))
 return pd.DataFrame(list(csv.DictReader([lines[0]]+[x for x in lines[1:] if len(x.split(','))==width]))).apply(pd.to_numeric)
def compress_closed(out,final=False):
 paths=sorted(out.glob('*.vtu'))
 if not final:paths=paths[:-2]
 for p in paths:
  assert p.resolve().is_relative_to(SCRATCH.resolve()) and p.parent==out
  gz=p.with_suffix(p.suffix+'.gz')
  assert not gz.exists(),str(gz)
  before=sha(p)
  with p.open('rb') as src,gzip.open(str(gz)+'.tmp','wb',compresslevel=1) as dst:shutil.copyfileobj(src,dst,2**20)
  h=hashlib.sha256()
  with gzip.open(str(gz)+'.tmp','rb') as src:
   for chunk in iter(lambda:src.read(2**20),b''):h.update(chunk)
  assert before==h.hexdigest(),'Compression changed raw field'
  Path(str(gz)+'.tmp').replace(gz)
  entry={'file':gz.name,'gzip_sha256':sha(gz),'raw_sha256':before,'raw_bytes':p.stat().st_size,'gzip_bytes':gz.stat().st_size}
  with (out/'compressed_fields.jsonl').open('a') as f:f.write(json.dumps(entry)+'\n')
  # Only this newly produced field, after a complete reversible hash-verified archive.
  p.unlink()
def prefix_check(out,end=24,reference=None):
 a=csvread(out/'budget.csv');b=pd.read_csv(reference or PARENT/'runs/Dry_trial02_r02/budget.csv');b=b[b.evaporation_time_h<=end]
 assert a.evaporation_time_h.max()>=end-1e-9
 cols=['water_mol','salt_total_mol','coarse_salt_mol','fine_salt_mol','cumulative_interface_adv_mol','cumulative_interface_diff_mol','cumulative_coarse_top_water_mol','cumulative_fine_top_water_mol','C_max_mol_L']
 errors={c:float(np.max(abs(np.interp(b.time_s,a.time_s,a[c])-b[c]))/max(1e-9,float(abs(b[c]).max()))) for c in cols}
 assert max(errors.values())<1e-6,errors
 result={'status':'passed','through_evaporation_h':end,'max_relative_to_peak_errors':errors,'parent_binary_sha256':'c9145e427a63e9d4b9c3a6e2dca459d8df0e4c54133f7ec698e076941a2eb1f3'}
 result['reference']=str(reference or PARENT/'runs/Dry_trial02_r02/budget.csv')
 if reference:result['parent_binary_sha256']='1ab6cfb632f7bf0a603ba83e8e00f810c0096af80ec534e3f776e0618e1efb10'
 write(out/('prefix_check_preprecip_v09r02.json' if reference else 'prefix_check.json'),result);return result
def validate(out,reaction=False):
 b=csvread(out/'budget.csv');m=csvread(out/'mineral_budget.csv')
 t=csvread(out/'thermal_budget.csv')
 status=json.loads((out/'run_status.json').read_text())
 cfg=configparser.ConfigParser();cfg.read(next(out.glob('*.input')))
 target=float(cfg['TimeLoop']['TEnd']);assert status['status']=='completed' and abs(b.time_s.iloc[-1]-target)<1e-6
 assert np.isfinite(b.to_numpy()).all() and np.isfinite(m.to_numpy()).all()
 assert np.isfinite(t.to_numpy()).all()
 errors={c:float(abs(b[c]).max()/max(abs(b[base].iloc[0]),1e-12)) for c,base in [('water_residual_mol','water_mol'),('salt_residual_mol','salt_total_mol'),('coarse_residual_mol','coarse_salt_mol'),('fine_residual_mol','fine_salt_mol')]}
 assert max(errors.values())<1e-6,errors
 eq=cfg['Revision'].getboolean('EquilibriumPrecipitation')
 if cfg['Revision'].getboolean('FixedHydraulics',fallback=False):
  # The executable independently checks phi and K against both material inputs at every audit.
  assert 'FIXED_HYDRAULICS enabled=true ' in (out/'simulation.log').read_text()
 if eq:
  assert m.max_relative_complementarity_residual.iloc[1:].max()<1e-6
  assert m.min_solid_vf.iloc[1:].min()>-1e-10
  assert m.max_molality.iloc[1:].max()<6.011884292870146*(1+1e-5)
 if reaction:
  assert abs(b.salt_boundary_out_mol_s).max()==0 and abs(b.water_boundary_out_mol_s).max()==0
 energy_error=float(abs(t.energy_residual_J).max()/max(abs(t.energy_J.iloc[0]),1.0))
 assert energy_error<1e-6,energy_error
 assert t.T_min_K.min()>273.15 and t.T_max_K.max()<323.15,(t.T_min_K.min(),t.T_max_K.max())
 result={'status':'passed','relative_budget_residuals':errors,'relative_energy_budget_residual':energy_error,'T_min_K':float(t.T_min_K.min()),'T_max_K':float(t.T_max_K.max()),'first_solid_mol':float(m.salt_solid_mol.iloc[0]),'final_solid_mol':float(m.salt_solid_mol.iloc[-1]),'final_dissolved_mol':float(m.salt_dissolved_mol.iloc[-1]),'max_molality_after_initial':float(m.max_molality.iloc[1:].max()),'max_complementarity_after_initial':float(m.max_relative_complementarity_residual.iloc[1:].max()),'completed_evaporation_h':float(b.evaporation_time_h.iloc[-1])}
 write(out/'acceptance.json',result);return result
def run(name,cpu,production=False):
 out=SCRATCH/'runs'/name
 if out.exists() and RESUME_VALIDATION_REPAIR:
  # Revalidate only existing successful solver exits; never retry a numerical failure.
  meta=json.loads((out/'run_manifest.json').read_text())
  assert meta['returncode']==0 and meta.get('failure_reason') in [None,'AssertionError()'],meta
  build=json.loads((ROOT/globals().get('BUILD_DIRECTORY','build_ni1')/'build_manifest.json').read_text())
  assert meta['binary_sha256']==build['binary_sha256'] and meta['input_sha256']==sha(ROOT/'inputs'/f'{name}.input')==sha(out/f'{name}.input')
  result=validate(out,reaction=name.startswith(('Precipitate','Dissolve','RemainSolid')))
  meta.update(state='completed',acceptance=result,revalidated_utc=utc(),validation_repair='boolalpha log parser; original failure retained in provenance/validation_attempt01')
  meta.pop('failure_reason',None);meta.pop('log_tail',None)
  write(out/'run_manifest.json',meta);write(ROOT/(name+'_status.json'),meta);return meta
 assert not (ROOT/'BLOCK_PRODUCTION.json').exists(), 'Campaign frozen by zero-change regression failure'
 frozen=json.loads((ROOT/'input_manifest.json').read_text())
 assert all(sha(ROOT/'inputs'/k)==v for k,v in frozen.items()), 'Frozen input hash mismatch'
 out.mkdir(parents=True,exist_ok=False)
 cfg=configparser.ConfigParser();cfg.read(ROOT/'inputs'/f'{name}.input')
 for p in [ROOT/'inputs'/f'{name}.input',ROOT/'inputs'/cfg['Grid']['File'],ROOT/'inputs/water_flux_zero_storage.txt',ROOT/'inputs/forcing_provenance.json']:shutil.copy2(p,out/p.name)
 if cfg['Revision'].get('PortAreaFile'):shutil.copy2(ROOT/'inputs'/cfg['Revision']['PortAreaFile'],out/cfg['Revision']['PortAreaFile'])
 build=json.loads((ROOT/globals().get('BUILD_DIRECTORY','build_ni1')/'build_manifest.json').read_text());exe=ROOT/globals().get('BUILD_DIRECTORY','build_ni1')/'heterogeneity_revised'
 assert sha(exe)==build['binary_sha256']
 assert all(sha(ROOT/k)==v for k,v in build['source_sha256'].items())
 shutil.copy2(ROOT/globals().get('BUILD_DIRECTORY','build_ni1')/'build_manifest.json',out/'build_manifest.json')
 env=os.environ.copy();env.update(DUMUX_NUM_THREADS='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
 wall=48*3600 if production else globals().get('SHORT_WALL_S',3600)
 meta={'case':name,'start_utc':utc(),'binary_sha256':build['binary_sha256'],'input_sha256':sha(out/f'{name}.input'),'cpu':cpu,'requested_threads':1,'wall_limit_s':wall,'raw_path':str(out),'state':'running','controller_pid':os.getpid()}
 with (out/'simulation.log').open('w') as log:
  proc=subprocess.Popen(['/usr/bin/time','-v','-o',str(out/'resource_usage.txt'),'taskset','-c',str(cpu),'nice','-n','10',str(exe),str(out/f'{name}.input')],cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  meta['solver_pid']=proc.pid;write(out/'run_manifest.json',meta);write(ROOT/(name+'_status.json'),meta)
  begin=time.monotonic();prefix=False;failure_prefix=False
  try:
   while proc.poll() is None:
    time.sleep(15)
    if time.monotonic()-begin>wall:raise RuntimeError('Wall-time limit reached')
    if shutil.disk_usage(SCRATCH).free<4*1024**3:raise RuntimeError('Scratch reserve below 4 GiB')
    if (out/'budget.csv').exists():
     b=csvread(out/'budget.csv');last=b.iloc[-1]
     meta.update(evaporation_time_h=float(last.evaporation_time_h),salt_solid_mol=float(last.salt_solid_mol),C_max_mol_L=float(last.C_max_mol_L),S_min=float(last.S_min),updated_utc=utc(),scratch_free_GiB=shutil.disk_usage(SCRATCH).free/1024**3)
     write(ROOT/(name+'_status.json'),meta)
    if production:
     compress_closed(out)
     hook=globals().get("checkpoint_hook")
     if hook:hook(out,b)
  except Exception as exc:
   os.killpg(proc.pid,15)
   try:proc.wait(timeout=30)
   except subprocess.TimeoutExpired:os.killpg(proc.pid,9);proc.wait()
   meta['failure_reason']=str(exc)
  proc.wait()
 meta.update(returncode=proc.returncode,end_utc=utc())
 write(out/'run_manifest.json',meta)
 try:
  assert proc.returncode==0 and 'failure_reason' not in meta
  result=validate(out,reaction=name.startswith(('Precipitate','Dissolve','RemainSolid')))
  if production:compress_closed(out,final=True)
  meta.update(state='completed',acceptance=result)
 except Exception as exc:meta.update(state='failed',failure_reason=meta.get('failure_reason',repr(exc)),log_tail=(out/'simulation.log').read_text(errors='replace')[-5000:])
 # Include the last fields even on failure; do not leave unbacked terminal VTUs.
 try:compress_closed(out,final=True)
 except Exception as exc:meta.update(state='failed',archive_error=repr(exc))
 write(out/'run_manifest.json',meta);write(ROOT/(name+'_status.json'),meta)
 return meta

def selftest(name,cpu):
 out=SCRATCH/'runs'/name
 if out.exists() and RESUME_VALIDATION_REPAIR:
  meta=json.loads((out/'run_manifest.json').read_text())
  assert meta['state']=='completed' and meta['input_sha256']==sha(ROOT/'inputs'/f'{name}.input')
  assert meta['binary_sha256']==json.loads((ROOT/globals().get('BUILD_DIRECTORY','build_ni1')/'build_manifest.json').read_text())['binary_sha256']
  return meta
 assert not (ROOT/'BLOCK_PRODUCTION.json').exists(), 'Campaign frozen by zero-change regression failure'
 frozen=json.loads((ROOT/'input_manifest.json').read_text())
 assert all(sha(ROOT/'inputs'/k)==v for k,v in frozen.items()), 'Frozen input hash mismatch'
 out.mkdir(parents=True,exist_ok=False)
 cfg=configparser.ConfigParser();cfg.read(ROOT/'inputs'/f'{name}.input')
 for p in [ROOT/'inputs'/f'{name}.input',ROOT/'inputs'/cfg['Grid']['File'],ROOT/'inputs/water_flux_zero_storage.txt']:shutil.copy2(p,out/p.name)
 if cfg['Revision'].get('PortAreaFile'):shutil.copy2(ROOT/'inputs'/cfg['Revision']['PortAreaFile'],out/cfg['Revision']['PortAreaFile'])
 build=json.loads((ROOT/globals().get('BUILD_DIRECTORY','build_ni1')/'build_manifest.json').read_text());exe=ROOT/globals().get('BUILD_DIRECTORY','build_ni1')/'heterogeneity_revised'
 assert sha(exe)==build['binary_sha256']
 env=os.environ.copy();env.update(DUMUX_NUM_THREADS='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
 with (out/'simulation.log').open('w') as log:
  p=subprocess.run(['taskset','-c',str(cpu),'nice','-n','10',str(exe),str(out/f'{name}.input')],cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=600)
 assert p.returncode==0,(name,(out/'simulation.log').read_text()[-3000:])
 result=json.loads((out/'hydraulic_selftest.json').read_text());assert result['status']=='passed'
 meta={'case':name,'state':'completed','binary_sha256':build['binary_sha256'],'input_sha256':sha(out/f'{name}.input'),'acceptance':result,'end_utc':utc()}
 write(out/'run_manifest.json',meta);write(ROOT/(name+'_status.json'),meta);return meta

def legacy_check():
 a=csvread(SCRATCH/'runs/Legacy_precipitate/budget.csv')
 ref=Path('/tmp/zhixin_cylinder_precip_v09_r02_20261030/runs/Precipitate_dt15/budget.csv')
 b=csvread(ref);assert list(a.columns)==list(b.columns) and len(a)==len(b)
 # Enabling the energy equation is expected to perturb the short evaporation
 # response. Compare conserved inventories and primary state diagnostics, not
 # near-zero residual/rate columns whose relative errors are meaningless.
 cols=['water_mol','salt_total_mol','salt_dissolved_mol','salt_solid_mol','coarse_salt_mol','fine_salt_mol','S_min','porosity_min','precip_vf_max','C_max_mol_L']
 errors={c:float(abs(a[c]-b[c]).max()/max(1e-12,float(abs(b[c]).max()))) for c in cols}
 assert max(errors.values())<2e-4,errors
 result={'status':'passed','interpretation':'bounded non-isothermal perturbation of the isothermal short gate','reference':str(ref),'reference_sha256':sha(ref),'selected_max_relative_to_peak_errors':errors,'tolerance':2e-4}
 write(ROOT/'legacy_regression.json',result);return result
def main():
 SCRATCH.mkdir(exist_ok=RESUME_VALIDATION_REPAIR)
 assert shutil.disk_usage(SCRATCH).free>12*1024**3
 write(ROOT/'campaign_status.json',{'state':'gates_running','updated_utc':utc(),'scratch_root':str(SCRATCH)})
 hydraulic=[selftest('Selftest_fixed',7),selftest('Selftest_coupled',7)]
 legacy=run('Legacy_precipitate',7)
 assert legacy['state']=='completed',legacy
 legacy_check()
 pairs=[('Precipitate_dt30','Precipitate_dt15'),('Dissolve_dt30','Dissolve_dt15'),('RemainSolid_dt30','RemainSolid_dt15'),('Regression_disabled','Regression_equilibrium')]
 gate_results=hydraulic+[legacy]
 for pair in pairs:
  res=[run(pair[0],7),run(pair[1],7)]
  gate_results+=res
  assert all(x['state']=='completed' for x in res),[(x['case'],x.get('failure_reason')) for x in res]
  if not pair[0].startswith('Regression'):
   x,y=[v['acceptance'] for v in res]
   for k in ['final_solid_mol','final_dissolved_mol']:assert abs(x[k]-y[k])<max(1e-9,.005*max(abs(x[k]),abs(y[k])))
   if pair[0].startswith('Precipitate'):assert x['final_solid_mol']>1e-8
   if pair[0].startswith('Dissolve'):assert abs(x['final_solid_mol'])<1e-10
   if pair[0].startswith('RemainSolid'):assert 1e-8<x['final_solid_mol']<x['first_solid_mol']
 recovery=run('Recovery_injected',7)
 assert recovery['state']=='completed',recovery
 log=(SCRATCH/'runs/Recovery_injected/simulation.log').read_text()
 assert 'Nonpositive liquid water fraction in trial state' in log and 'Retrying with time step' in log
 reference=next(x for x in gate_results if x['case']=='Precipitate_dt15')['acceptance']
 for k in ['final_solid_mol','final_dissolved_mol']:
  assert abs(recovery['acceptance'][k]-reference[k])<max(1e-9,.005*abs(reference[k]))
 gate_results.append(recovery)
 write(ROOT/'gate_summary.json',{'status':'passed','gates':gate_results,'reaction_dt_relative_tolerance':.005,'updated_utc':utc()})
 write(ROOT/'campaign_status.json',{'state':'production_running','updated_utc':utc(),'scratch_root':str(SCRATCH),'gates_passed':True})
 result=run('RH0_174h',7,production=True)
 write(ROOT/'campaign_status.json',{'state':'completed' if result['state']=='completed' else 'failed','updated_utc':utc(),'scratch_root':str(SCRATCH),'gates_passed':True,'production':result})
if __name__=='__main__':
 try:main()
 except Exception as exc:
  write(ROOT/'campaign_status.json',{'state':'failed','updated_utc':utc(),'error':repr(exc),'scratch_root':str(SCRATCH)})
  raise
