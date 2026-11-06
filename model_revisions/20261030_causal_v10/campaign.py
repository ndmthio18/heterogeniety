"""v10 causal campaign controller (liqin). Deterministic and resumable:
gates (self-tests, hydrostatic, prefix regression, short switch checks) ->
immutable HANDOFF_READY.json -> four serial 24 h runs on CPU4 -> validation,
24 h regression of C1B1 against v08, field compression and extraction.
A stage is skipped on restart only if its result file says passed/completed.
Failed or interrupted runs are kept under their own identity; never retried
silently. Usage: python campaign.py <build_tag>"""
from pathlib import Path
import configparser,csv,datetime,gzip,hashlib,json,os,resource,shutil,subprocess,sys,tarfile,time,traceback
import xml.etree.ElementTree as ET
import numpy as np
R=Path(__file__).resolve().parent
SCRATCH=Path('/tmp/zhixin_causal_v10_20261030')
V08=R.parent/'20261030_cylinder_film_v08'
V08RUN=V08/'runs/Dry_trial02_r02'
PY='/home/zhixin/micromamba/envs/vasca311/bin/python3'
CPU='4'
SCRATCH_RESERVE=8.0;HOME_RESERVE=2.0;MEM_SOLVER=8.0
PRODUCTION=['C1B1_24h','C0B1_24h','C1B0_24h','C0B0_24h']
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for c in iter(lambda:f.read(1<<20),b''):h.update(c)
 return h.hexdigest()
def write(p,d):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+'.tmp');t.write_text(json.dumps(d,indent=2));t.replace(p)
def read(p):return json.loads(Path(p).read_text())
def free_gib(p):return shutil.disk_usage(p).free/1024**3
def mem_gib():
 for line in open('/proc/meminfo'):
  if line.startswith('MemAvailable:'):return int(line.split()[1])/1024**2
def csvread(p):
 """Numeric CSV, ignoring a possibly incomplete last line of a running solver."""
 lines=Path(p).read_text().splitlines();head=lines[0].split(',');rows=[l.split(',') for l in lines[1:]];rows=[r for r in rows if len(r)==len(head)]
 a=np.array(rows,dtype=float) if rows else np.zeros((0,len(head)))
 return {h:a[:,i] for i,h in enumerate(head)}
def last_line(p):
 with open(p,'rb') as f:
  f.seek(0,2);n=f.tell();f.seek(max(0,n-65536));lines=f.read().decode(errors='replace').splitlines()
 return lines[-2] if len(lines)>1 else None
class Status:
 def __init__(s,tag):s.tag=tag;s.path=R/'STATUS_remote.json';s.d={'tag':tag,'controller_pid':os.getpid(),'started_utc':utc(),'completed':[],'failed':[],'stage':None,'state':'running'}
 def set(s,**k):s.d.update(k);s.d['updated_utc']=utc();write(s.path,s.d)
def wait_resources(status,solver=True,need_scratch=0.):
 while True:
  m,fs,fh=mem_gib(),free_gib(SCRATCH),free_gib('/home/zhixin')
  ok=(m>=MEM_SOLVER or not solver) and fs>=SCRATCH_RESERVE+need_scratch and fh>=HOME_RESERVE
  if ok:return {'mem_available_gib':m,'scratch_free_gib':fs,'home_free_gib':fh}
  status.set(state='queued_for_resources',resources={'mem_available_gib':m,'scratch_free_gib':fs,'home_free_gib':fh});time.sleep(60)
def compress(out,final=False):
 """Lossless gzip of closed fields with raw/decompressed hash check; the raw
 file of this batch is unlinked only after verification and indexing."""
 paths=sorted(out.glob('*.vtu'))
 if not final:paths=paths[:-2]
 for p in paths:
  assert p.resolve().parent==out.resolve() and str(p.resolve()).startswith(str(SCRATCH.resolve()))
  gz=p.with_name(p.name+'.gz');assert not gz.exists(),gz
  raw=sha(p);tmp=gz.with_name(gz.name+'.tmp')
  with open(p,'rb') as a,gzip.open(tmp,'wb',compresslevel=1) as b:shutil.copyfileobj(a,b,1<<20)
  h=hashlib.sha256()
  with gzip.open(tmp,'rb') as b:
   for c in iter(lambda:b.read(1<<20),b''):h.update(c)
  assert h.hexdigest()==raw,'compression changed raw field'
  tmp.replace(gz)
  with open(out/'compressed_fields.jsonl','a') as f:f.write(json.dumps({'file':gz.name,'raw_sha256':raw,'gzip_sha256':sha(gz),'raw_bytes':p.stat().st_size,'gzip_bytes':gz.stat().st_size})+'\n')
  p.unlink()
def open_field(p):
 p=Path(p)
 if p.exists():return open(p,'rb')
 return gzip.open(str(p)+'.gz','rb')
def vtu_fields(p):
 with open_field(p) as f:tree=ET.parse(f)
 out={}
 for e in tree.findall('.//CellData/DataArray'):
  a=np.array((e.text or '').split(),dtype=float);n=int(e.get('NumberOfComponents','1'));out[e.get('Name')]=a if n==1 else a.reshape(-1,n)
 return out
def pvd_frames(out,name):
 return [(float(d.get('timestep')),out/d.get('file')) for d in ET.parse(out/(name+'.pvd')).findall('.//DataSet')]
class Runner:
 def __init__(s,tag,status):
  s.tag=tag;s.status=status;s.B=R/f'build_{tag}';s.manifest=read(s.B/'build_manifest.json');s.exe=s.B/'heterogeneity_causal'
  assert sha(s.exe)==s.manifest['binary_sha256'],'binary hash differs from build manifest'
  for k,v in s.manifest['source_sha256'].items():assert sha(R/k)==v,f'source changed since build: {k}'
  s.runs=SCRATCH/'runs'/tag;s.stages=R/'stages'/tag;s.runs.mkdir(parents=True,exist_ok=True);s.stages.mkdir(parents=True,exist_ok=True)
 def stage_done(s,name):
  p=s.stages/f'{name}.json';return p.exists() and read(p).get('status') in ('passed','completed')
 def run(s,name,wall,production=False):
  out=s.runs/name
  if out.exists():
   # Interrupted earlier attempt: keep it under its own identity.
   dest=s.runs/'_interrupted'/f'{name}_{datetime.datetime.now().strftime("%Y%m%dT%H%M%S")}';dest.parent.mkdir(exist_ok=True);out.rename(dest)
   s.status.set(note=f'previous attempt of {name} moved to {dest}')
  res=wait_resources(s.status,need_scratch=2.5 if production else .3)
  out.mkdir(parents=True)
  cfg=configparser.ConfigParser();cfg.optionxform=str;cfg.read(R/'inputs'/f'{name}.input')
  for f in [R/'inputs'/f'{name}.input',R/'inputs/cylinder.msh',R/'inputs/water_flux_zero_storage.txt',R/'inputs/forcing_provenance.json',s.B/'build_manifest.json']:shutil.copy2(f,out/f.name)
  env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
  meta={'case':name,'tag':s.tag,'start_utc':utc(),'binary_sha256':s.manifest['binary_sha256'],'input_sha256':sha(out/f'{name}.input'),'mesh_sha256':sha(out/'cylinder.msh'),
   'cpu':int(CPU),'nice':10,'threads':1,'wall_limit_s':wall,'raw_path':str(out),'resources_at_start':res,'controller_pid':os.getpid(),'state':'running',
   'TEnd':float(cfg['TimeLoop']['TEnd'])}
  t0=time.monotonic();r0=resource.getrusage(resource.RUSAGE_CHILDREN)
  with open(out/'simulation.log','w') as log:
   proc=subprocess.Popen(['taskset','-c',CPU,'nice','-n','10',str(s.exe),str(out/f'{name}.input')],cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT)
   meta['solver_pid']=proc.pid;write(out/'run_manifest.json',meta);s.status.set(case=name,solver_pid=proc.pid,state='running')
   peak=0
   try:
    while proc.poll() is None:
     time.sleep(20)
     try:peak=max(peak,int([l for l in open(f'/proc/{proc.pid}/status') if l.startswith('VmHWM')][0].split()[1]))
     except Exception:pass
     if time.monotonic()-t0>wall:raise RuntimeError('wall-time limit reached')
     if free_gib(SCRATCH)<SCRATCH_RESERVE:raise RuntimeError('scratch free space below reserve')
     reached=None
     if (out/'budget.csv').exists():
      l=last_line(out/'budget.csv')
      if l and l[0].isdigit():reached=float(l.split(',')[1])
     s.status.set(case=name,solver_pid=proc.pid,reached_hours=reached,wall_min=round((time.monotonic()-t0)/60,1),peak_rss_MiB=round(peak/1024,1),scratch_free_gib=round(free_gib(SCRATCH),2),mem_available_gib=round(mem_gib(),2))
     if production:compress(out)
   except Exception as exc:
    proc.terminate()
    try:proc.wait(timeout=30)
    except subprocess.TimeoutExpired:proc.kill();proc.wait()
    meta['failure_reason']=repr(exc)
   proc.wait()
  meta.update(returncode=proc.returncode,end_utc=utc(),wall_s=time.monotonic()-t0,peak_rss_MiB=peak/1024)
  r1=resource.getrusage(resource.RUSAGE_CHILDREN);meta['cpu_seconds']=(r1.ru_utime+r1.ru_stime)-(r0.ru_utime+r0.ru_stime)
  meta['scratch_bytes']=sum(p.stat().st_size for p in out.rglob('*') if p.is_file())
  write(out/'run_manifest.json',meta);return out,meta
 def validate(s,out,meta):
  name=meta['case'];checks={}
  st=read(out/'run_status.json');checks['run_status']=st
  assert meta['returncode']==0 and 'failure_reason' not in meta,meta.get('failure_reason',meta['returncode'])
  assert st['status']=='completed' and abs(st['time_s']-meta['TEnd'])<1e-6,st
  b=csvread(out/'budget.csv');c=csvread(out/'causal_budget.csv');sw=read(out/'causal_switches.json')
  assert abs(b['time_s'][-1]-meta['TEnd'])<1e-6 and abs(c['time_s'][-1]-meta['TEnd'])<1e-6
  assert all(np.isfinite(v).all() for v in b.values()) and all(np.isfinite(v).all() for v in c.values())
  rel={k:float(np.max(np.abs(b[k]))/abs(b[base][0])) for k,base in [('water_residual_mol','water_mol'),('salt_residual_mol','salt_total_mol'),('coarse_residual_mol','coarse_salt_mol'),('fine_residual_mol','fine_salt_mol')]}
  for sd in ['F36','W3']:
   for k in ['water','salt']:rel[f'{sd}_side_{k}']=float(np.max(np.abs(c[f'{sd}_residual_{k}_mol']))/abs(c[f'{sd}_{k}_mol'][0]))
  checks['max_relative_budget_residuals']=rel;assert max(rel.values())<1e-6,rel
  checks['precip_vf_max']=float(np.max(b['precip_vf_max']));checks['S_min']=float(np.min(b['S_min']));checks['C_max_mol_L']=float(np.max(b['C_max_mol_L']))
  assert checks['precip_vf_max']==0.0,'precipitation occurred in the 24 h window'
  assert checks['S_min']>0
  faces=c['interface_faces_evaluated'][1:] if len(c['time_s'])>1 else c['interface_faces_evaluated']
  checks['interface_faces_evaluated']=[float(faces.min()),float(faces.max())];assert faces.min()==faces.max()==sw['interface_faces'],'interface face count changed'
  ifcols=[k for k in c if k.startswith('if_')]
  checks['max_abs_interface_columns']=float(max(np.max(np.abs(c[k])) for k in ifcols))
  if not sw['InterfaceExchangeEnabled']:assert checks['max_abs_interface_columns']==0.0,'blocked interface carries flux'
  # Cross-check: legacy salt interface columns equal the new salt bands.
  adv=sum(c[f'if_adv_salt_{b}mm_mol_s'] for b in ['0_2','2_10','10_20','20_40']);dif=sum(c[f'if_diff_salt_{b}mm_mol_s'] for b in ['0_2','2_10','10_20','20_40'])
  scale=max(1e-30,float(np.max(np.abs(b['interface_adv_mol_s'])+np.abs(b['interface_diff_mol_s']))))
  checks['legacy_vs_band_interface_salt_max_rel']=float(max(np.max(np.abs(adv-b['interface_adv_mol_s'])),np.max(np.abs(dif-b['interface_diff_mol_s']))))/scale
  assert checks['legacy_vs_band_interface_salt_max_rel']<1e-9
  checks['hashes']={'input':meta['input_sha256'],'mesh':meta['mesh_sha256'],'binary':meta['binary_sha256']}
  return checks
 def finish(s,stage,out,meta,extra=None,production=False):
  res={'stage':stage,'case':meta['case'],'raw_path':str(out),'run_manifest':meta}
  try:
   res['validation']=s.validate(out,meta)
   if extra:res.update(extra(out))
   if production:compress(out,final=True)
   res['status']='passed' if not production else 'completed'
  except Exception as exc:
   res.update(status='failed',error=repr(exc),traceback=traceback.format_exc()[-3000:],log_tail=(out/'simulation.log').read_text(errors='replace')[-4000:])
  write(s.stages/f'{stage}.json',res);return res
def compare_budget(a,b,cols,tmax):
 bm=b['time_s']<=tmax+1e-9;errs={}
 for k in cols:
  ref=b[k][bm];val=np.interp(b['time_s'][bm],a['time_s'],a[k]);errs[k]=float(np.max(np.abs(val-ref))/max(1e-30,float(np.max(np.abs(ref)))))
 return errs
REG_COLS=['water_mol','air_mol','salt_total_mol','coarse_salt_mol','fine_salt_mol','cumulative_water_out_mol','cumulative_salt_out_mol','cumulative_interface_adv_mol','cumulative_interface_diff_mol','cumulative_coarse_top_water_mol','cumulative_fine_top_water_mol','C_max_mol_L','S_min']
FIELD_SKIP={'dof_id','phase presence'}
def compare_fields(pa,pb,skip=()):
 a=vtu_fields(pa);b=vtu_fields(pb);ia=np.argsort(np.rint(a['dof_id']));ib=np.argsort(np.rint(b['dof_id']));errs={}
 for k in b:
  if k in FIELD_SKIP or k in skip or k not in a:continue
  ref=b[k][ib];val=a[k][ia];errs[k]=float(np.max(np.abs(val-ref))/max(1e-30,float(np.max(np.abs(ref)))))
 return errs
def regression(out,name,tmax,frames):
 a=csvread(out/'budget.csv');b=csvread(V08RUN/'budget.csv')
 same_steps=bool(len(a['time_s'][a['time_s']<=tmax+1e-9])==len(b['time_s'][b['time_s']<=tmax+1e-9]) and np.allclose(a['time_s'][a['time_s']<=tmax+1e-9],b['time_s'][b['time_s']<=tmax+1e-9],rtol=0,atol=1e-9))
 berr=compare_budget(a,b,REG_COLS,tmax)
 fa=dict(pvd_frames(out,name));fb=dict(pvd_frames(V08RUN,'Dry_trial02_r02'));ferr={}
 for t in frames:ferr[str(t)]=compare_fields(fa[t],fb[t])
 seed=read(out/'seed_event.json') if (out/'seed_event.json').exists() else None;seed8=read(V08RUN/'seed_event.json')
 worst=max(list(berr.values())+[max(v.values()) for v in ferr.values()])
 r={'regression_status':'passed' if worst<=1e-6 else 'failed','through_time_s':tmax,'tolerance':1e-6,'max_scaled_difference':worst,'identical_accepted_step_times':same_steps,
  'budget_max_relative_to_peak':berr,'field_max_relative_to_peak':ferr,'v08_binary_sha256':read(V08RUN/'run_manifest.json')['binary_sha256'],'v08_budget_sha256':sha(V08RUN/'budget.csv')}
 if seed:r['seed_partition_impulses']={'v10':seed['partition_impulses_mol'],'v08':seed8['partition_impulses_mol']}
 return r
def hydro_compare(runs):
 a=runs/'Hydrostatic_C1B1';out={}
 fa=pvd_frames(a,'Hydrostatic_C1B1')[-1][1];A=vtu_fields(fa)
 out['C1B1_max_abs_liquid_velocity_m_s']=float(np.max(np.linalg.norm(A['velocity_liq_interior_LS (m/s)'],axis=1)))
 for n in ['Hydrostatic_C1B0','Hydrostatic_C0B0']:
  # Velocities are ~0 at rest; compared in absolute terms below, not relative to their own peak.
  f=pvd_frames(runs/n,n)[-1][1];out[n+'_vs_C1B1_field_max_relative']=compare_fields(f,fa,skip={'velocity_liq_interior_LS (m/s)','velocity_liq (m/s)','velocity_gas (m/s)'})
  B=vtu_fields(f);out[n+'_vs_C1B1_max_abs_velocity_difference_m_s']=float(np.max(np.abs(B['velocity_liq_interior_LS (m/s)'][np.argsort(np.rint(B['dof_id']))]-A['velocity_liq_interior_LS (m/s)'][np.argsort(np.rint(A['dof_id']))])))
  out[n+'_max_abs_liquid_velocity_m_s']=float(np.max(np.linalg.norm(vtu_fields(f)['velocity_liq_interior_LS (m/s)'],axis=1)))
 worst=max(max(v.values()) for k,v in out.items() if k.endswith('field_max_relative'))
 out['worst_field_difference']=worst;out['hydrostatic_status']='passed' if worst<=1e-6 else 'failed'
 return out
def snapshot(tag,status):
 """Immutable handoff snapshot: source/tests/inputs/scripts + build directory."""
 tar=R/f'snapshot_{tag}.tar.gz'
 if not tar.exists():
  tmp=tar.with_name(tar.name+'.tmp')
  with tarfile.open(tmp,'w:gz') as t:
   for p in ['source','tests','inputs','build.py','prepare_inputs.py','campaign.py',f'build_{tag}']:t.add(R/p,arcname=p)
  tmp.replace(tar)
 return tar
def main(tag):
 SCRATCH.mkdir(exist_ok=True);status=Status(tag);status.set(stage='init',scratch_root=str(SCRATCH))
 run=Runner(tag,status);stages=[]
 def gate(stage,name,wall=3600,extra=None,production=False):
  if run.stage_done(stage):status.d['completed'].append(stage);return read(run.stages/f'{stage}.json')
  status.set(stage=stage,state='running');out,meta=run.run(name,wall,production);res=run.finish(stage,out,meta,extra,production)
  (status.d['completed'] if res['status'] in ('passed','completed') else status.d['failed']).append(stage);status.set()
  return res
 # 1. Self-tests (no time loop; validation is the self-test file).
 for k in ['C1B1','C0B1','C1B0','C0B0']:
  stage=f'selftest_{k}'
  if run.stage_done(stage):status.d['completed'].append(stage);continue
  status.set(stage=stage);out,meta=run.run(f'SelfTest_{k}',1800)
  r={'stage':stage,'run_manifest':meta,'raw_path':str(out)}
  try:
   st=read(out/'causal_selftest.json');r['selftest']=st;r['causal_switches']=read(out/'causal_switches.json');r['status']='passed' if meta['returncode']==0 and st['status']=='passed' else 'failed'
  except Exception as exc:r.update(status='failed',error=repr(exc),log_tail=(out/'simulation.log').read_text(errors='replace')[-4000:])
  write(run.stages/f'{stage}.json',r);(status.d['completed'] if r['status']=='passed' else status.d['failed']).append(stage);status.set()
  if r['status']!='passed':status.set(state='failed',reason=f'{stage} failed');return
 # 2. Hydrostatic (zero evaporation, 1 M, no perturbation) for lambda=1/0.
 for k in ['C1B1','C1B0','C0B0']:
  r=gate(f'hydrostatic_{k}',f'Hydrostatic_{k}')
  if r['status']!='passed':status.set(state='failed',reason=f'hydrostatic_{k} failed');return
 if not run.stage_done('hydrostatic_compare'):
  h=hydro_compare(run.runs);h['status']=h['hydrostatic_status'];write(run.stages/'hydrostatic_compare.json',h)
  if h['status']!='passed':status.d['failed'].append('hydrostatic_compare');status.set(state='failed',reason='lambda=0 1 M hydrostatic differs from lambda=1');return
 status.d['completed'].append('hydrostatic_compare')
 # 3. Prefix regression with default (absent) switches against v08.
 r=gate('prefix_regression','PrefixRegression',extra=lambda out:regression(out,'PrefixRegression',7800,[0.,7200.,7800.]))
 if r['status']!='passed' or r.get('regression_status')!='passed':
  if r['status']=='passed':r['status']='failed';write(run.stages/'prefix_regression.json',r)
  status.d['failed'].append('prefix_regression');status.set(state='failed',reason='prefix regression failed');return
 # 4. Short switch checks (2 h + 1 h evaporation).
 for k in ['C0B1','C1B0','C0B0']:
  r=gate(f'short_{k}',f'Short_{k}')
  if r['status']!='passed':status.set(state='failed',reason=f'short_{k} failed');return
 # 5. Immutable handoff.
 hand=R/'HANDOFF_READY.json'
 if not hand.exists():
  tar=snapshot(tag,status);m=run.manifest
  evidence={p.stem:read(p) for p in sorted(run.stages.glob('*.json'))}
  h={'version':f'causal_{tag}','created_utc':utc(),'producer':'Opus A (claude-opus-5-5)','immutable':True,
   'snapshot_tar':str(tar),'snapshot_tar_sha256':sha(tar),'binary':str(run.exe),'binary_sha256':m['binary_sha256'],
   'source_sha256':m['source_sha256'],'tests_sha256':m['tests_sha256'],'mesh':str(R/'inputs/cylinder.msh'),'mesh_sha256':sha(R/'inputs/cylinder.msh'),
   'inputs_sha256':{p.name:sha(p) for p in sorted((R/'inputs').glob('*.input'))},'static_dependency_sha256':m['static_dependency_sha256'],
   'build_command':f'{PY} build.py {tag}  (single process, flock {m["lock"]}, taskset -c 4, nice 10)','compile_command':m['compile_command'],
   'switches':{'Revision.InterfaceExchangeEnabled':'bool, default true. false: every interior face between cells of different materials (spatial-parameter rule x<=0.025 m coarse) has zero Darcy flux (both phases, hence zero advection of all components) and zero Fickian flux (all components, both phases) inside the assembled flux laws; zero-thickness impermeable partition; no cells removed; bottom reservoir boundary unchanged.',
    'Revision.SalinityBuoyancyScale':'lambda in [0,1], default 1. Liquid density in the Darcy gravity term of interior faces and of the bottom reservoir face: rho_g=rho_ref(p_liq,T,x_ref)+lambda*(rho-rho_ref). lambda=1 calls the unmodified upstream law (exactly the v08 path). Gas-phase gravity uses its actual density. Storage, molar densities, viscosity, diffusion, water activity, film and reservoir head keep actual composition.'},
   'lambda0_reference_convention':evidence.get('selftest_C1B0',{}).get('causal_switches',{}),
   'regression_and_gate_evidence':evidence,'raw_runs_root':str(run.runs),
   'note':'Shared baseline pairs for B: C1B1_24h and C0B1_24h under '+str(run.runs)+' when completed; their stage files under '+str(run.stages)+'.'}
  t=hand.with_name(hand.name+'.tmp');t.write_text(json.dumps(h,indent=2));t.replace(hand)
 status.d['completed'].append('handoff');status.set(stage='handoff_written',handoff=str(hand))
 # 6. Production, strictly serial.
 for name in PRODUCTION:
  stage=f'production_{name}'
  extra=(lambda out:regression(out,'C1B1_24h',93600,[0.,7200.,14400.,21600.,36000.,50400.,93600.])) if name=='C1B1_24h' else None
  r=gate(stage,name,wall=6*3600,extra=extra,production=True)
  if r['status']=='completed':
   ex=run.stages/f'extract_{name}.json'
   if not (ex.exists() and read(ex).get('status')=='completed'):
    status.set(stage=f'extract_{name}',state='running')
    p=subprocess.run(['taskset','-c',CPU,'nice','-n','10',PY,str(R/'extract.py'),str(run.runs/name),str(R/'results'/tag/name)],capture_output=True,text=True)
    write(ex,{'status':'completed' if p.returncode==0 else 'failed','stdout':p.stdout[-4000:],'stderr':p.stderr[-4000:],'utc':utc()})
 done=[n for n in PRODUCTION if run.stage_done(f'production_{n}')]
 status.set(stage='finished',state='completed' if len(done)==4 else 'needs_attention',production_completed=done,solver_pid=None,case=None)
if __name__=='__main__':
 try:main(sys.argv[1])
 except Exception as exc:
  write(R/'STATUS_remote_crash.json',{'utc':utc(),'error':repr(exc),'traceback':traceback.format_exc()});raise
