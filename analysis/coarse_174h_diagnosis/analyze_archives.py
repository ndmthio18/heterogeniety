"""Offline audit. Originals are read-only; all outputs stay beside this script."""
from pathlib import Path
import json,re,hashlib,importlib.util,datetime
import numpy as np
import pandas as pd
import openpyxl
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent;P=R.parents[1];V=P/'model_revisions/20261102_cylinder_fixed_hydraulics_v12'
O=R/'results';O.mkdir(exist_ok=True)
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':180})
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
sources=[]
def source(p):sources.append({'path':str(p.relative_to(P)),'sha256':sha(p)});return p
def csv(name,rows):
 d=rows if isinstance(rows,pd.DataFrame) else pd.DataFrame(rows);d.to_csv(O/(name+'.csv'),index=False);return d
def fig(name):
 plt.savefig(O/(name+'.png'),bbox_inches='tight');plt.savefig(O/(name+'.pdf'),bbox_inches='tight');plt.close()
E=P/'analysis/model_experiment_comparison_20261028'
exp=pd.read_csv(source(E/'experimental_profiles.csv')).rename(columns={'raw_signal':'workbook_reconstruction_corrected_GV'})
npz=np.load(source(V/'results/comparison/fixed/profiles.npz'))
times=[0,24,48,60,84,96,108,120,144,162,174];bands=[(3,37),(3,12),(12,28),(28,37)]
stats=[];pairs=[];metrics=[]
for side,j in [('F36',0),('W3',1)]:
 for t in times:
  ex=exp[(exp.side==side)&(exp.time_h==t)].sort_values('depth_center_mm');assert len(ex)==40
  k=np.argmin(abs(npz['time']-t));assert abs(npz['time'][k]-t)<1e-8
  z=ex.depth_center_mm.to_numpy();m=npz['concentration'][k,j]
  variants={'MRI_archived':ex.archived_concentration.to_numpy(),'MRI_recalibration':ex.signal_recalibration.to_numpy(),'corrected_GV':ex.workbook_reconstruction_corrected_GV.to_numpy(),'model_liquid_M':m}
  for label,c in variants.items():
   for lo,hi in bands:
    mask=(z>=lo)&(z<hi);slope=np.polyfit(z[mask],c[mask],1)[0]
    stats.append(dict(side=side,time_h=t,quantity=label,band=f'{lo}-{hi}',mean=np.mean(c[mask]),depth_sd=np.std(c[mask]),slope_per_mm=slope))
  mask=(z>=3)&(z<37);err=m[mask]-variants['MRI_archived'][mask];bias=err.mean();shape=np.sqrt(np.mean((err-bias)**2));rmse=np.sqrt(np.mean(err**2));assert abs(rmse**2-bias**2-shape**2)<1e-12
  metrics.append(dict(side=side,time_h=t,mean_bias_mol_L=bias,profile_RMSE_mol_L=rmse,shape_RMSE_mol_L=shape,gradient_error_mol_L_mm=np.polyfit(z[mask],err,1)[0],mean_bias_fraction_MSE=bias**2/max(rmse**2,1e-30)))
  for i,zz in enumerate(z):pairs.append(dict(side=side,time_h=t,depth_mm=zz,model_liquid_M=m[i],MRI_archived_M=variants['MRI_archived'][i],MRI_recalibration_M=variants['MRI_recalibration'][i],corrected_GV=variants['corrected_GV'][i]))
stats=pd.DataFrame(stats)
for col in ['mean','depth_sd','slope_per_mm']:
 for base in [0,60]:
  lookup=stats[stats.time_h==base].set_index(['side','quantity','band'])[col]
  stats[f'{col}_change_from_{base}h']=[r[col]-lookup.loc[(r.side,r.quantity,r.band)] for _,r in stats.iterrows()]
csv('profile_statistics',stats);csv('profile_pairs',pairs);metrics=csv('profile_error_decomposition',metrics)
growth=[]
for (side,q,b),d in stats.groupby(['side','quantity','band']):
 d=d.sort_values('time_h')
 for a,c in zip(d.iloc[:-1].itertuples(),d.iloc[1:].itertuples()):growth.append(dict(side=side,quantity=q,band=b,start_h=a.time_h,end_h=c.time_h,growth_per_h=(c.mean-a.mean)/(c.time_h-a.time_h)))
csv('profile_growth_rates',growth)
f,ax=plt.subplots(2,2,figsize=(11,7),layout='constrained')
for j,s in enumerate(['F36','W3']):
 for q,label,style in [('MRI_archived','MRI archived','o-'),('MRI_recalibration','Before manual edits','s:'),('model_liquid_M','v12 liquid molarity','-')]:
  d=stats[(stats.side==s)&(stats.quantity==q)&(stats.band=='3-37')];ax[0,j].plot(d.time_h,d['mean'],style,label=label)
 ax[0,j].set(title=s+' mean, 3–37 mm',ylabel='Concentration (mol/L)',xlabel='Nominal evaporation time (h)');ax[0,j].legend(fontsize=8)
 d=metrics[metrics.side==s];ax[1,j].plot(d.time_h,d.mean_bias_mol_L,'o-',label='Mean bias');ax[1,j].plot(d.time_h,d.shape_RMSE_mol_L,'s-',label='Shape RMSE');ax[1,j].axhline(0,color='.6',lw=.8);ax[1,j].set(ylabel='Model − MRI / error (mol/L)',xlabel='Nominal evaporation time (h)');ax[1,j].legend()
fig('01_concentration_and_error')
# Workbooks and acquisition metadata, including explicit reconstruction scaling.
book=source(next((P/'experimental_data/DARUS-6478/extracted').rglob('F36+W3_Hetero_Data_Analysis.xlsx')))
w=openpyxl.load_workbook(book,data_only=False);wv=openpyxl.load_workbook(book,data_only=True)
cells=[]
for sheet in w:
 for row in sheet:
  for c in row:
   if c.value is not None:cells.append(dict(sheet=sheet.title,cell=c.coordinate,formula_or_literal=str(c.value),cached_value=wv[sheet.title][c.coordinate].value))
csv('workbook_cell_provenance',cells)
timing=pd.read_csv(source(E/'scan_timing.csv'));scandir=next((P/'experimental_data/DARUS-6478/extracted').rglob('F36+W3_Hetero_Evap_MRI_Scans'))
def param(txt,key):
 m=re.search(r'^##\$'+re.escape(key)+r'=(.*?)(?=^##|\Z)',txt,re.M|re.S)
 return ' '.join(x.strip() for x in m.group(1).splitlines() if not x.startswith('$$')) if m else None
meta=[]
for scan in sorted(set(timing.scan_id.astype(int))|{31,39,41}):
 row={'scan_id':scan};p=scandir/str(scan)
 for file,keys in [('acqp',['ACQ_time','RG','ACQ_nucleus']),('method',['PVM_RefPowCh1','PVM_ScanTime','PVM_SpatResol','PVM_Matrix','PVM_RepetitionTime','PVM_EchoTime']),('pdata/1/reco',['RECO_map_slope','RECO_map_offset','RECO_wordtype','RECO_byte_order']),('pdata/1/visu_pars',['VisuCoreSize','VisuCoreDataSlope','VisuCoreDataOffs','VisuCoreWordType'])]:
  if (p/file).exists():
   txt=source(p/file).read_text(errors='replace')
   for key in keys:row[key]=param(txt,key)
 row['native_2dseq_exists']=(p/'pdata/1/2dseq').exists()
 if row['native_2dseq_exists']:row['native_2dseq_sha256']=sha(p/'pdata/1/2dseq')
 meta.append(row)
csv('scan_metadata',pd.DataFrame(meta).merge(timing.rename(columns={'ACQ_time':'ACQ_time_archived_mapping'}),how='left',on='scan_id'))
manual=exp[abs(exp.archived_concentration-exp.signal_recalibration)>1e-9];csv('manual_and_alignment_changes',manual)
jump=[]
for side in ['F36','W3']:
 for q in ['MRI_archived','MRI_recalibration','corrected_GV']:
  d=stats[(stats.side==side)&(stats.quantity==q)&(stats.band=='3-37')].set_index('time_h')['mean']
  jump.append(dict(side=side,quantity=q,at84=d[84],at96=d[96],increase=d[96]-d[84],relative_increase=(d[96]/d[84]-1)))
csv('jump_84_96',jump)
# Bulk signal inversion is already divided by initial phi: do not multiply Sw a second time.
area=np.pi*.025**2;phis={'F36':.39,'W3':.35};inventory=[]
for (side,t),d in exp.groupby(['side','time_h']):
 if t not in times:continue
 for lo,hi in [(0,40),(3,37)]:
  mask=(d.depth_center_mm>=lo)&(d.depth_center_mm<hi)
  for label,c in [('archived',d.archived_concentration),('recalibrated',d.signal_recalibration)]:
   n=float(c[mask].sum()*phis[side]*area/2*.001*1000)
   inventory.append(dict(side=side,time_h=t,band=f'{lo}-{hi}',route=label,apparent_inventory_mol=n,initial_pore_volume_L=phis[side]*area/2*(hi-lo)*.001*1000))
inv=csv('MRI_apparent_inventory',inventory)
mass=pd.read_csv(source(P/'analysis/rh0_evaporation_65h_20261102/full_experiment/full_experimental_mass.csv'));mass=mass[mass.time_h<=174]
loss=float(np.interp(96,mass.time_h,mass.solution_loss_since_1h_g)-np.interp(84,mass.time_h,mass.solution_loss_since_1h_g))
plaus=[]
for band in ['0-40','3-37']:
 for route in ['archived','recalibrated']:
  d=inv[(inv.band==band)&(inv.route==route)].groupby('time_h').apparent_inventory_mol.sum();delta=d[96]-d[84]
  for rho in [1.002,1.04]: # Source workbook density vs approximate solution density; scenario, not confidence interval.
   supply=loss/rho/1000
   plaus.append(dict(band=band,route=route,solution_loss_84_96_g=loss,reservoir_density_g_mL=rho,inflow_only_supply_mol=supply,apparent_increase_mol=delta,ratio=delta/supply,unexplained_under_inflow_only_mol=delta-supply,alternative_trueC_uniformS96_if_S84_1=(d[84]+supply)/d[96]))
csv('inventory_supply_scenarios',plaus)
# H scans provide limited, differently normalized endpoint evidence, not a saturation field at 84/96h.
s=wv['2W_5W_Corr.'];hchecks={k:s[k].value for k in ['E70','N215','Q54','Q55']}
hchecks['filter_normalized_H_sample_endpoint_ratio']=s['Q55'].value/s['Q54'].value
(O/'normalization_checks.json').write_text(json.dumps(hchecks,indent=2))
f,ax=plt.subplots(1,2,figsize=(11,4),layout='constrained')
for s in ['F36','W3']:
 d=stats[(stats.side==s)&(stats.quantity=='corrected_GV')&(stats.band=='3-37')];ax[0].plot(d.time_h,d['mean'],'o-',label=s)
ax[0].axvspan(84,96,alpha=.15,color='grey');ax[0].set(xlabel='Nominal time (h)',ylabel='Workbook reconstruction-corrected GV',title='Processed signal; not native raw MRI');ax[0].legend()
for route in ['archived','recalibrated']:
 d=inv[(inv.band=='0-40')&(inv.route==route)].groupby('time_h').apparent_inventory_mol.sum();ax[1].plot(d.index,d*58.44,'o-',label='MRI apparent: '+route)
initial=inv[(inv.band=='0-40')&(inv.route=='archived')&(inv.time_h==0)].apparent_inventory_mol.sum()
ax[1].plot(mass.time_h,initial*58.44+mass.solution_loss_since_1h_g/1.04/1000*58.44,'--',label='1h-anchored inflow-only supply scenario')
ax[1].set(xlabel='Nominal time (h)',ylabel='NaCl-equivalent inventory (g)',title='Observation and supply are conditional');ax[1].legend(fontsize=8);fig('02_signal_and_apparent_inventory')
# Native fields: layer anomalies, true storage, observed bulk-signal approximation, and LS velocity correlations.
spec=importlib.util.spec_from_file_location('extract',V/'finalize_extract.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
raw=V/'remote_backup/runs/RH0_174h';import xml.etree.ElementTree as ET
entries={round(float(e.get('timestep'))/3600-2,8):e.get('file')+'.gz' for e in ET.parse(raw/'RH0_174h.pvd').findall('.//DataSet')}
g=pd.read_csv(source(raw/'cell_geometry.csv')).set_index('dof');conv=[];obs=[];snap={}
for t in [24,60,84,96,120,144,174]:
 p=source(raw/entries[t]);a=mod.read(p);ids=np.rint(a['dof_id']).astype(int);geom=g.loc[ids];pos=geom[['x_m','y_m','z_m']].to_numpy();vol=geom.volume_m3.to_numpy();depth=(.04-pos[:,1])*1000
 C=a['x^NaCl_liq']*a['rhoMolar_liq']/1000;vy=a['velocity_liq_interior_LS (m/s)'][:,1];rho=a['rho_liq'];theta=a['porosity']*a['S_liq'];layers=np.round(pos[:,1],10)
 for side,mask in [('F36',pos[:,0]<.025),('W3',pos[:,0]>.025)]:
  ca=C.copy();ra=rho.copy()
  for l in np.unique(layers):
   mm=mask&(layers==l);ca[mm]-=np.average(C[mm],weights=vol[mm]);ra[mm]-=np.average(rho[mm],weights=vol[mm])
  for region,mm in [('all',mask),('core',mask&(np.hypot(pos[:,0]-.025,pos[:,2])<.02)&(abs(pos[:,0]-.025)>.003)&(depth>5)&(depth<35))]:
   def avg(x):return np.average(x[mm],weights=vol[mm])
   cov=avg((ca-avg(ca))*(vy-avg(vy)));den=np.sqrt(avg((ca-avg(ca))**2)*avg((vy-avg(vy))**2))
   conv.append(dict(time_h=t,side=side,region=region,mean_C=avg(C),sd_horizontal_C=np.sqrt(avg(ca**2)),rms_density_anomaly_kg_m3=np.sqrt(avg(ra**2)),mean_vy_m_s=avg(vy),min_vy_m_s=vy[mm].min(),max_vy_m_s=vy[mm].max(),down_volume_fraction_1e8=vol[mm&(vy<-1e-8)].sum()/vol[mm].sum(),up_volume_fraction_1e8=vol[mm&(vy>1e-8)].sum()/vol[mm].sum(),C_anomaly_vy_correlation=cov/den if den else np.nan,liquid_saturation_min=a['S_liq'][mm].min(),mean_liquid_saturation=avg(a['S_liq'])))
  # Same whole-half 1mm slabs, approximate calibration applied before averaging. No voxel PSF claimed.
  low=(.04-geom.ymax_m.to_numpy())*1000;high=(.04-geom.ymin_m.to_numpy())*1000
  bulk=C*theta;signal=.96+2.62*bulk if side=='F36' else .6991+(7.1241-(2.6693-.4516*bulk)**2)/.9032
  for d in range(40):
   weights=np.maximum(0,np.minimum(high,d+1)-np.maximum(low,d))/(high-low)*vol*mask;sig=np.average(signal,weights=weights)
   cb=(sig-.96)/2.62 if side=='F36' else (2.6693-np.sqrt(7.1241-.9032*(sig-.6991)))/.4516
   obs.append(dict(time_h=t,side=side,depth_mm=d+.5,model_observation_approx_M=cb/phis[side]))
 if t in [24,84,120,174]:snap[t]=(pos.copy(),C.copy(),vy.copy(),ca.copy())
csv('convection_diagnostics',conv);csv('model_observation_approximation',obs)
f,ax=plt.subplots(2,4,figsize=(14,7),layout='constrained')
for j,(t,(pos,c,v,ca)) in enumerate(snap.items()):
 sel=(abs(pos[:,2])<.0015)&(pos[:,0]<.025)
 q=ax[0,j].scatter(pos[sel,0]*1000,(.04-pos[sel,1])*1000,c=c[sel],s=8,vmin=1,vmax=2.2,cmap='viridis');ax[0,j].set(title=f'F36, {t} h',xlabel='x (mm)',ylabel='Depth (mm)');ax[0,j].invert_yaxis()
 q2=ax[1,j].scatter(pos[sel,0]*1000,(.04-pos[sel,1])*1000,c=v[sel]*1e6,s=8,vmin=-1,vmax=1,cmap='RdBu_r');ax[1,j].set(xlabel='x (mm)',ylabel='Depth (mm)');ax[1,j].invert_yaxis()
f.colorbar(q,ax=ax[0,:],label='Liquid concentration (mol/L)',shrink=.8,extend='max');f.colorbar(q2,ax=ax[1,:],label='Upward LS velocity (µm/s)',shrink=.8,extend='both');fig('03_coarse_internal_fields')
(O/'source_manifest.json').write_text(json.dumps(sources,indent=2));print('Offline audit written',len(sources),'source records')
