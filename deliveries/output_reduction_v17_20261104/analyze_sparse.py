"""Depth-wide enrichment diagnostics from saved native fields and native face ledgers.
No experimental onset inference, interpolation of missing profiles, or refit.
"""
from pathlib import Path
import sys,json,hashlib,xml.etree.ElementTree as ET
import numpy as np,pandas as pd
R=Path(sys.argv[sys.argv.index('--root')+1]).resolve() if '--root' in sys.argv else Path(__file__).resolve().parent
sys.path.insert(0,str(Path(__file__).resolve().parent))
from field_series import entries as pvd_entries, read_field
case=sys.argv[1];raw=R/'raw/runs'/case;O=R/'results'/case;O.mkdir(parents=True,exist_ok=True)
g=pd.read_csv(raw/'cell_geometry.csv').set_index('dof');rows=[];profiles=[];src=[]
pvd=Path(sys.argv[sys.argv.index('--pvd')+1]).resolve() if '--pvd' in sys.argv else raw/(case+'.pvd')
for e in pvd_entries(pvd):
 t=float(e.get('timestep'));h=t/3600-2
 if h<0:continue
 if '--checkpoints' in sys.argv and not any(abs(h-k)<1e-7 for k in [0,24,60,84,96,108,120,144,174]):continue
 p,data=read_field(pvd.parent,e.get('file'));root=ET.fromstring(data);a={x.get('Name'):np.fromstring(x.text or '',sep=' ').reshape(-1,int(x.get('NumberOfComponents','1'))) for x in root.findall('.//CellData/DataArray')};a={k:v[:,0] if v.shape[1]==1 else v for k,v in a.items()}
 geom=g.loc[a['dof_id'].astype(int)];v=geom.volume_m3.to_numpy();x=geom.x_m.to_numpy();y=geom.y_m.to_numpy();lo=(.04-geom.ymax_m.to_numpy())*1000;hi=(.04-geom.ymin_m.to_numpy())*1000
 C=a['x^NaCl_liq']*a['rhoMolar_liq']/1000;phi=a['porosity'];Sw=a['S_liq'];vy=a['velocity_liq_interior_LS (m/s)'][:,1];rho=a['rho_liq']
 for label,mask in [('F36',(x<.025)&(y>0)),('W3',(x>.025)&(y>0)),('filter',y<0)]:
  if not mask.any():continue
  av=lambda z,w:float(np.average(z,weights=w))
  profile=[]
  if label!='filter':
   for d in range(40):
    w=v*mask*np.maximum(0,np.minimum(hi,d+1)-np.maximum(lo,d))/(hi-lo);profile.append(av(C,w));profiles.append(dict(case=case,time_h=h,material=label,depth_mm=d+.5,C_M=profile[-1]))
  bands=[('all',-10,45)] if label=='filter' else [('all',0,40),('3_37',3,37),('upper',3,12),('middle',12,28),('lower',28,37)]
  for band,d0,d1 in bands:
   w=v*mask*np.maximum(0,np.minimum(hi,d1)-np.maximum(lo,d0))/(hi-lo)
   if w.sum()==0:continue
   # Total NaCl includes gas salt, even though the registered fluid law makes it negligible.
   dissolved=sum(a['x^NaCl_'+ph]*a['rhoMolar_'+ph]*a['S_'+ph]*phi for ph in ['liq','gas'])
   row=dict(case=case,time_h=h,material=label,band=band,C_volume_mean_M=av(C,w),C_liquid_weighted_M=av(C,w*phi*Sw),liquid_volume_m3=float(np.sum(w*phi*Sw)),mean_Sliq=av(Sw,w),min_Sliq=float(Sw[w>0].min()),salt_dissolved_mol=float(np.sum(w*dissolved)),equivalent_solid_volume_m3=float(np.sum(w*a['precipitateVolumeFraction^NaCl'])),mean_vy_m_s=av(vy,w),max_down_m_s=max(0.,float(-vy[w>0].min())),max_up_m_s=max(0.,float(vy[w>0].max())),down_volume_fraction=float(w[vy<-1e-8].sum()/w.sum()))
   if band=='3_37':row.update(depth_profile_std_M=float(np.std(profile[3:37])),depth_gradient_M_mm=float(np.polyfit(np.arange(3.5,37),profile[3:37],1)[0]))
   # Horizontal anomaly relative to each material's mean on its own depth level.
   ca=C.copy();ra=rho.copy()
   for yy in np.unique(y[mask]):
    m=mask&(y==yy);ca[m]-=av(C[m],v[m]);ra[m]-=av(rho[m],v[m])
   row.update(horizontal_C_RMS_M=np.sqrt(av(ca**2,w)),horizontal_density_RMS_kg_m3=np.sqrt(av(ra**2,w)));rows.append(row)
 src.append(dict(file=p.name,sha256=hashlib.sha256(data).hexdigest(),time_h=h))
df=pd.DataFrame(rows);pf=pd.DataFrame(profiles)
# Solid molar density is pinned from parent component source; ledger cross-check below
# independently catches unit/density errors, including filter-inclusive budget confusion.
solid_rhomolar=2165/0.0584428
df['salt_solid_mol']=df.equivalent_solid_volume_m3*solid_rhomolar;df['salt_total_mol']=df.salt_dissolved_mol+df.salt_solid_mol
separate=(raw/'material_budgets.csv').exists();ledger=pd.read_csv(raw/('material_budgets.csv' if separate else 'budget.csv'));checks=[]
for (h,mat),part in df[df.band=='all'].groupby(['time_h','material']):
 m={'F36':0,'W3':1,'filter':2}[mat]
 if separate:expected=ledger[(abs(ledger.evaporation_h-h)<1e-7)&(ledger.material==m)].iloc[-1].salt_mol
 else:
  if abs(h)<1e-7:continue # Legacy ledger records preseed0h; do not compare to postseed output.
  expected=ledger[abs(ledger.evaporation_time_h-h)<1e-7].iloc[-1]['coarse_salt_mol' if mat=='F36' else 'fine_salt_mol']
 pred=part.salt_total_mol.iloc[0];err=abs(pred-expected)/max(abs(expected),1e-12);checks.append(err)
assert max(checks)<1e-8,('Native field/ledger salt mismatch',max(checks))
df.to_csv(O/'depth_enrichment_history.csv',index=False);pf.to_csv(O/'profiles_history.csv',index=False)
# Report mean-profile MRI discrepancies only at actual archived nominal times.
obs_path=R.parent/'baseline_reference/MRI_profile_pairs_unchanged.csv';errors=[]
if obs_path.exists():
 obs=pd.read_csv(obs_path)
 for (h,mat),part in pf.groupby(['time_h','material']):
  o=obs[(obs.time_h==h)&(obs.side==mat)].sort_values('depth_mm')
  if len(o)!=40:continue
  c=part.sort_values('depth_mm').C_M.to_numpy()[3:37];d=c-o.MRI_archived_M.to_numpy()[3:37];errors.append(dict(time_h=h,material=mat,bias_M=d.mean(),RMSE_M=np.sqrt(np.mean(d*d)),mean_M=c.mean()))
pd.DataFrame(errors).to_csv(O/'MRI_nominal_comparison.csv',index=False)
f=pd.read_csv(raw/'native_fluxes.csv') if (raw/'native_fluxes.csv').exists() else pd.DataFrame(columns=['kind','material']);integrated=[]
for (kind,mat),z in f.groupby(['kind','material']):
 q=dict(kind=int(kind),material=int(mat));q.update({c:float(np.sum(z[c]*z.dt_s)) for c in z if c not in ['time_s','dt_s','kind','material','area_m2','unused']});integrated.append(q)
pd.DataFrame(integrated).to_csv(O/'native_throughputs.csv',index=False)
film=pd.read_csv(raw/'film_budget.csv');enrich=[]
for (mat,band),z in df[df.material!='filter'].groupby(['material','band']):
 z=z.sort_values('time_h');late=z[z.time_h>=120];enrich.append(dict(material=mat,band=band,final_C_M=float(z.C_volume_mean_M.iloc[-1]),change_C_M=float(z.C_volume_mean_M.iloc[-1]-z.C_volume_mean_M.iloc[0]),change_total_salt_mol=float(z.salt_total_mol.iloc[-1]-z.salt_total_mol.iloc[0]),liquid_volume_ratio=float(z.liquid_volume_m3.iloc[-1]/z.liquid_volume_m3.iloc[0]),late_slope_M_h=float(np.polyfit(late.time_h,late.C_volume_mean_M,1)[0]) if len(late)>2 else None))
pd.DataFrame(enrich).to_csv(O/'enrichment_summary.csv',index=False)
(O/'verification.json').write_text(json.dumps(dict(state='passed',through_evaporation_h=float(df.time_h.max()),frames=len(src),max_salt_field_ledger_relative_error=max(checks),source_hashes=src,interpretation='native depth-wide diagnostic; geometry must be read from case metadata; no absolute 2D–3D or morphology/onset validation'),indent=2))
print(case,df.time_h.max(),max(checks),flush=True)
