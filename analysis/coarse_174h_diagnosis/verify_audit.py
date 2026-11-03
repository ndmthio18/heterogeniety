"""Portable numerical and file-integrity audit; no solver or original MRI required."""
from pathlib import Path
import json,hashlib,sys
import numpy as np,pandas as pd
R=Path(__file__).resolve().parent;O=R/'results';checks={}
if (R/'AUDIT_MANIFEST.json').exists():
 manifest=json.loads((R/'AUDIT_MANIFEST.json').read_text())
 for x in manifest['files']:assert hashlib.sha256((R/x['path']).read_bytes()).hexdigest()==x['sha256'],x['path']
 checks['manifest_files']=len(manifest['files'])
p=pd.read_csv(O/'profile_pairs.csv');m=pd.read_csv(O/'profile_error_decomposition.csv').set_index(['side','time_h'])
for key,d in p.groupby(['side','time_h']):
 d=d[(d.depth_mm>=3)&(d.depth_mm<37)];z=d.model_liquid_M-d.MRI_archived_M;r=m.loc[key]
 assert abs(r.mean_bias_mol_L-z.mean())<1e-12
 assert abs(r.profile_RMSE_mol_L**2-z.pow(2).mean())<1e-12
 assert abs(r.profile_RMSE_mol_L**2-r.mean_bias_mol_L**2-r.shape_RMSE_mol_L**2)<1e-12
checks['profile_mean_shape_identity']='passed, 22 comparisons'
b=pd.read_csv(O/'bottom_interval_budgets.csv')
assert np.max(abs(b.accepted_salt_increase_mol-b.accepted_bottom_net_supply_mol+b.accepted_interface_net_out_mol-b.seed_mol))<1e-10
assert np.max(abs(b.quadrature_bottom_net_mol-b.bottom_gross_in_salt_mol+b.bottom_gross_out_salt_mol))<1e-12
checks['material_interval_closure']='passed'
h=pd.read_csv(R/'native_replay/full/flux_history.csv')
for c in h:
 if c.endswith('_net'):
  assert np.max(abs(h[c]-h[c[:-4]+'_pos']+h[c[:-4]+'_neg']))<1e-15,c
assert h.time_h.iloc[-1]==174 and len(h)==1044
checks['face_gross_sign_and_net']='passed, 1044 frames'
for d in [R/'native_replay/full',R/'vertical_replay/pilot']:
 v=json.loads((d/'verification.json').read_text());assert v['state']=='passed' and v['max_scaled_error']<1e-5
checks['native_replay_gates']='passed'
v=pd.read_csv(O/'vertical_native_transport.csv');assert len(v)==42 and (v.faces==384).all()
checks['horizontal_plane_counts']='passed, 7 times x3 planes x2 materials'
tm=pd.read_csv(O/'thermal_profile_metrics.csv').set_index(['side','time_h']);tp=pd.read_csv(O/'thermal_profiles.csv')
for key,d in tp.groupby(['side','time_h']):
 e=p[(p.side==key[0])&(p.time_h==key[1])];d=d.merge(e,on=['side','time_h','depth_mm']);d=d[(d.depth_mm>=3)&(d.depth_mm<37)]
 assert abs(np.sqrt(np.mean((d.v13_C_mol_L-d.MRI_archived_M)**2))-tm.loc[key,'RMSE_mol_L'])<1e-12
checks['thermal_profile_reduction']='passed'
intervals=pd.read_csv(O/'thermal_evaporation_intervals.csv');assert intervals.end_h.max()==174
checks['no_post_endpoint_model_extrapolation']='passed'
print(json.dumps(checks,indent=2))
