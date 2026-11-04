"""Replay native fluxes on saved states; gate every frame against original ledger."""
from pathlib import Path
import os,sys,json,gzip,hashlib,subprocess,xml.etree.ElementTree as ET
os.environ.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',DUMUX_NUM_THREADS='1')
import numpy as np
import pandas as pd
R=Path(__file__).resolve().parent
case=sys.argv[1];RAW=R/'raw/runs'/case
pilot='--pilot' in sys.argv
O=RAW/('native_pilot' if pilot else 'native_replay');O.mkdir(exist_ok=False)
inp=RAW/(case+'.input')
import configparser
cfg=configparser.ConfigParser();cfg.read(inp);mesh=RAW/cfg['Grid']['File'];assert mesh.exists()
err=(O/'stderr.log').open('w');log=(O/'stdout.log').open('w')
p=subprocess.Popen(['nice','-n','10',str(R/'build_filter_sal/native_replay'),str(inp),'-Grid.File',str(mesh)],cwd=O,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,text=True,bufsize=1,env=os.environ.copy())
bud=pd.read_csv(RAW/'budget.csv').set_index('time_s').join(pd.read_csv(RAW/'thermal_budget.csv').set_index('time_s')[['energy_J','energy_boundary_out_W']])
cols=['water_mol','salt_total_mol','coarse_salt_mol','fine_salt_mol','coarse_bottom_salt_out_mol_s','fine_bottom_salt_out_mol_s','interface_adv_mol_s','interface_diff_mol_s','energy_J','energy_boundary_out_W']
entries=ET.parse(RAW/(case+'.pvd')).findall('.//DataSet');checks=[];hist=[];sources=[]
wanted=[24,60,84,96,120,144,174]
try:
 for e in entries:
  ts=float(e.get('timestep'));t=ts/3600-2
  if t<=0:continue # 0h saved field follows seeding; accepted ledger is before seeding.
  if pilot and not any(abs(t-v)<1e-7 for v in [1/6,24,60,120,174]):continue
  f=RAW/(e.get('file')+'.gz');b=f.read_bytes();root=ET.fromstring(gzip.decompress(b));a={el.get('Name'):np.fromstring(el.text or '',sep=' ') for el in root.findall('.//CellData/DataArray') if el.get('NumberOfComponents','1')=='1'}
  state=a['phase presence'].astype(int);assert set(state)<={1,3}
  data=np.column_stack([a['dof_id'],state,a['p_liq'],np.where(state==1,a['x^Air_liq'],a['S_gas']),a['x^NaCl_liq'],a['precipitateVolumeFraction^NaCl'],a['T']])
  import io
  buf=io.StringIO();np.savetxt(buf,data,fmt=['%d','%d','%.17g','%.17g','%.17g','%.17g','%.17g'])
  p.stdin.write(f'{ts:.17g} {len(data)}\n'+buf.getvalue());p.stdin.flush()
  while True:
   line=p.stdout.readline();log.write(line);log.flush()
   if not line:raise RuntimeError('Native replay ended; inspect stderr')
   if line.startswith('REPLAY_OK '):break
  vals=np.array([float(v) for v in line.split()[2:]]);ref=bud.loc[ts,cols].to_numpy(float)
  # Primary-field precision gate; absolute floors prevent cancellation from masking a failure.
  scales=np.r_[np.maximum(abs(ref[:4]),1e-10),np.maximum(abs(ref[4:]),1e-10)]
  delta=abs(vals-ref);rel=delta/scales
  # The final quantity is a signed net energy flux assembled from many face
  # contributions.  Near a zero crossing, VTU text roundoff can leave an
  # O(1e-11 W) reconstruction difference while the material/storage fields
  # still agree to machine precision.  Require the original relative gate OR
  # a strict absolute 1e-10 W gate for this cancellation-prone diagnostic.
  # This is a replay-verification rule only; it does not change solver
  # tolerances, states, physics, timesteps, or the accepted energy budget.
  energy_boundary_ok=(rel[-1]<=1e-5 or delta[-1]<=1e-10)
  if rel[:-1].max()>1e-5 or not energy_boundary_ok:
   raise RuntimeError(f'Replay mismatch {t}: relative={dict(zip(cols,rel))}, energy_boundary_abs_W={delta[-1]}')
  row={'time_h':t,'max_scaled_error':rel[:-1].max(),
       'energy_boundary_relative_error':rel[-1],
       'energy_boundary_absolute_error_W':delta[-1]}
  row.update({c:float(v) for c,v in zip(cols,vals)});checks.append(row)
  faces=pd.read_csv(O/f'native_faces_{ts:.0f}.csv').rename(columns={'q_liq_m3_s':'liquid_volume_m3_s','donor_C_M':'donor_C_mol_L'});record={'time_h':t}
  for kind,label in [(0,'bottom'),(1,'interface'),(2,'vertical')]:
   groups=[(str(m),faces[(faces.kind==kind)&(faces.material==m)]) for m in [0,1]] if kind!=1 else [('all',faces[faces.kind==1])]
   for mat,df in groups:
    if df.empty:continue
    assert (df.area_m2>0).all()
    for c in ['liquid_volume_m3_s','water_adv_mol_s','water_diff_mol_s','salt_adv_mol_s','salt_diff_mol_s']:
     z=df[c].to_numpy();prefix=f'{label}_{mat}_{c}'
     record[prefix+'_pos']=np.maximum(z,0).sum();record[prefix+'_neg']=-np.minimum(z,0).sum();record[prefix+'_net']=z.sum()
    record[f'{label}_{mat}_in_area_m2']=df.loc[df.liquid_volume_m3_s<0,'area_m2'].sum()
    record[f'{label}_{mat}_out_area_m2']=df.loc[df.liquid_volume_m3_s>0,'area_m2'].sum()
    if kind==0:
     assert np.max(abs(df.salt_adv_mol_s-df.liquid_volume_m3_s*df.donor_C_mol_L*1000))<1e-16
     record[f'{label}_{mat}_out_C_mol_L']=df.loc[df.liquid_volume_m3_s>0,'salt_adv_mol_s'].sum()/max(df.loc[df.liquid_volume_m3_s>0,'liquid_volume_m3_s'].sum(),1e-30)/1000
  # Independent aggregation tests, using actual native integrated face fluxes (no area twice).
  assert abs(faces.loc[(faces.kind==0)&(faces.material==0),'salt_adv_mol_s'].sum()-vals[4])<1e-15
  assert abs(faces.loc[(faces.kind==0)&(faces.material==1),'salt_adv_mol_s'].sum()-vals[5])<1e-15
  assert abs(faces.loc[faces.kind==1,'salt_adv_mol_s'].sum()-vals[6])<1e-15
  assert abs(faces.loc[faces.kind==1,'salt_diff_mol_s'].sum()-vals[7])<1e-15
  if any(abs(t-v)<1e-7 for v in wanted):faces.to_csv(O/f'faces_{t:06.1f}h.csv.gz',index=False)
  # Large unsaved face maps are regenerable from hash-preserved states; retain only selected maps.
  if not any(abs(t-v)<1e-7 for v in wanted):(O/f'native_faces_{ts:.0f}.csv').unlink()
  hist.append(record);sources.append({'time_h':t,'file':f.name,'gzip_sha256':hashlib.sha256(b).hexdigest()})
  pd.DataFrame(hist).to_csv(O/'flux_history.csv',index=False);pd.DataFrame(checks).to_csv(O/'replay_checks.csv',index=False)
  if len(hist)%30==0 or pilot:print(f'Replayed {t:.4f} h, max scaled error {rel.max():.3g}',flush=True)
 p.stdin.close();assert p.wait()==0
 (O/'verification.json').write_text(json.dumps({'state':'passed','frames':len(hist),
  'max_scaled_error':max(x['max_scaled_error'] for x in checks),
  'max_energy_boundary_relative_error':max(x['energy_boundary_relative_error'] for x in checks),
  'max_energy_boundary_absolute_error_W':max(x['energy_boundary_absolute_error_W'] for x in checks),
  'energy_boundary_gate':'relative <= 1e-5 OR absolute <= 1e-10 W; signed net-flux cancellation safeguard',
  'native_face_sum_tests':'passed','donor_concentration_test':'passed','saved_interval_s':600,
  'zero_hour':'Preseed ledger flux approximately zero; 0h is supplied separately in quadrature.','sources':sources},indent=2))
finally:
 if p.poll() is None:p.terminate()
 err.close();log.close()
