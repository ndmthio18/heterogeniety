from pathlib import Path
import argparse,json
import numpy as np
import pandas as pd
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();checks={}
for case in ['Greal-81','Greal-75']:
 root=a.source/case;s=pd.read_csv(a.out/f'{case}_surface_history.csv');b=pd.read_csv(root/'budget.csv').drop_duplicates('time_s',keep='last');f=pd.read_csv(root/'film_budget.csv').drop_duplicates('time_s',keep='last')
 c={}
 for side,col in [('F36','coarse_top_water_out_mol_s'),('W3','fine_top_water_out_mol_s')]:
  z=s[s.side.eq(side)].merge(b[['time_s',col]],on='time_s',validate='one_to_one')
  expected=z[col]*.01801528*3.6e6
  # DuMuX water molar mass may use 0.018 kg/mol; infer documented conversion.
  ratios=z.loc[z[col].abs()>1e-14,'evap_g_h']/(z.loc[z[col].abs()>1e-14,col]*3.6e6)
  mw=float(ratios.median());expected=z[col]*mw*3.6e6
  err=float(np.max(np.abs(z.evap_g_h-expected)));c[side]={'matched':len(z),'water_molar_mass_inferred_kg_mol':mw,'max_abs_difference_g_h':err,'area_range_m2':[float(z.area_m2.min()),float(z.area_m2.max())]}
  assert err<1e-10 and len(z)==len(s[s.side.eq(side)])
 total=s.groupby('time_s').evap_g_h.sum().reset_index().merge(f[['time_s','top_water_mol_s']],on='time_s',validate='one_to_one')
 c['total_max_abs_difference_g_h']=float(np.max(np.abs(total.evap_g_h-total.top_water_mol_s*mw*3.6e6)))
 assert c['total_max_abs_difference_g_h']<1e-10
 # Read only selected native face maps, no VTK archive extraction.
 temp=[]
 for th in [0,60,72,84,96,108,120,144,174]:
  path=root/f'native_faces_{7200+3600*th}.csv'
  if not path.exists():continue
  v=pd.read_csv(path);v=v[np.isclose(v.y_m,.04)]
  for mat in [0,1]:
   z=v[v.material.eq(mat)]
   if len(z):temp.append({'time_h':th,'material':mat,'T_area_mean_K':np.average(z.T_K,weights=z.area_m2),'T_min_K':z.T_K.min(),'T_max_K':z.T_K.max(),'n_faces':len(z)})
 pd.DataFrame(temp).to_csv(a.out/f'{case}_native_surface_temperature.csv',index=False)
 c['temperature_rows']=len(temp);checks[case]=c
(a.out/'surface_checks.json').write_text(json.dumps(checks,indent=2));print(json.dumps(checks,indent=2))
