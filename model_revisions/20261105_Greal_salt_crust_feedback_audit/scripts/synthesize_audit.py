"""Compact synchronized audit, using accepted-step dt weighting; no solver changes."""
from pathlib import Path
import argparse,json,hashlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
figdir=a.out.parent/'figures'; summaries={}; hashes={}
for case in ['Greal-81','Greal-75']:
 root=a.source/case
 for name in ['budget.csv','mineral_budget.csv','film_budget.csv','film_faces.csv','native_fluxes.csv','material_budgets.csv','depth_profiles_compact.csv',f'{case}.pvd']:
  h=hashlib.sha256()
  with (root/name).open('rb') as f:
   for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
  hashes[f'runs/{case}/{name}']=h.hexdigest()
 s=pd.read_csv(a.out/f'{case}_solid_inventory_mol.csv'); surf=pd.read_csv(a.out/f'{case}_surface_history.csv')
 f=pd.read_csv(root/'native_fluxes.csv');f['time_h']=(f.time_s-7200)/3600
 # Right-end accepted flux is constant over its backward-Euler step.
 lateral=f[(f.kind==1)&(f.material==0)].copy();up=f[(f.kind==3)&(f.material==1)].copy()
 windows=[]
 for lo,hi in [(0,60),(60,84),(84,96),(96,108),(108,144),(144,174),(0,174)]:
  rec={'start_h':lo,'end_h':hi}
  for label,z,sign in [('lateral',lateral,1),('upward',up,-1)]:
   duration=np.maximum(0,np.minimum(z.time_s,hi*3600+7200)-np.maximum(z.time_s-z.dt_s,lo*3600+7200))
   for mech in ['adv','diff']:
    rec[f'{label}_{mech}_net_mol']=float(np.sum(sign*(z[f'salt_{mech}_out']-z[f'salt_{mech}_in'])*duration))
    rec[f'{label}_{mech}_gross_mol']=float(np.sum((z[f'salt_{mech}_out']+z[f'salt_{mech}_in'])*duration))
  windows.append(rec)
 pd.DataFrame(windows).to_csv(a.out/f'{case}_transport_windows.csv',index=False)
 d=pd.read_csv(root/'depth_profiles_compact.csv').drop_duplicates(['time_s','material','depth_mm'],keep='last');w=d[d.material==1]
 inv=w.groupby('time_s')[['salt_dissolved_mol','salt_solid_mol']].sum()
 sync=surf[surf.side=='W3'][['time_s','time_h','aw_mean','C_mean_M','evap_g_h']].set_index('time_s')
 sync=sync.rename(columns={'evap_g_h':'W3_evap_g_h'})
 sync['F36_evap_g_h']=surf[surf.side=='F36'].set_index('time_s').evap_g_h
 sync['total_evap_g_h']=sync.W3_evap_g_h+sync.F36_evap_g_h
 for col in inv:sync[col]=np.interp(sync.index,inv.index,inv[col])
 sync['equivalent_height_mm']=sync.salt_solid_mol*.05844/(2165*.57*np.pi*.025**2/2)*1000
 for label,z,sign in [('F36_to_W3',lateral,1),('filter_to_W3',up,-1)]:
  for mech in ['adv','diff']:
   sync[f'{label}_{mech}_net_mol_s']=np.interp(sync.index,z.time_s,sign*(z[f'salt_{mech}_out']-z[f'salt_{mech}_in']))
   sync[f'{label}_{mech}_gross_mol_s']=np.interp(sync.index,z.time_s,z[f'salt_{mech}_out']+z[f'salt_{mech}_in'])
 sync.to_csv(a.out/f'{case}_synchronized_hourly.csv')
 thickness=pd.read_csv(a.out/f'{case}_thickness_sensitivity.csv')
 thickness[thickness.time_h==174].to_csv(a.out/f'{case}_thickness_terminal.csv',index=False)
 # Preserve hourly sensitivity plus all terminal values; full accepted-step result reproducible remotely.
 thickness[np.isclose(thickness.time_h,np.round(thickness.time_h),atol=1e-8)].to_csv(a.out/f'{case}_thickness_hourly.csv',index=False)
 summaries[case]={'transport_0_174':windows[-1],'terminal_surface':sync.iloc[-1].to_dict(),'height_growth_max_mm_h':float(thickness[(thickness.region=='W3_top1')&(thickness.rho_kg_m3==2165)&(thickness.porosity==.43)&(thickness.coverage==1)].growth_mm_h.max())}
 fig,axs=plt.subplots(2,2,figsize=(10,7),layout='constrained',sharex=True)
 axs[0,0].plot(sync.time_h,sync.salt_dissolved_mol*58.44,label='Dissolved');axs[0,0].plot(sync.time_h,sync.salt_solid_mol*58.44,label='Solid');axs[0,0].set(ylabel='W3 NaCl equivalent (g)');axs[0,0].legend()
 axs[0,1].plot(sync.time_h,sync.C_mean_M);axs[0,1].set(ylabel='Top-face mean C (mol/L)')
 axs[1,0].plot(sync.time_h,sync.aw_mean);axs[1,0].set(ylabel='Top-face mean water activity')
 native=pd.read_csv(a.out/'selected_native_fields.csv');z=native[(native.case==case)&(native.side=='W3')]
 axs[1,1].errorbar(z.time_h,(z.top_T_min_K+z.top_T_max_K)/2-273.15,yerr=(z.top_T_max_K-z.top_T_min_K)/2,fmt='o',ms=3,capsize=3);axs[1,1].set(ylabel='Saved top-cell temperature range (°C)')
 for ax in axs.flat:ax.set(xlim=(0,174),xlabel='Evaporation time (h)')
 fig.suptitle(case+'; accepted state, without crust feedback')
 for ext in ['png','pdf']:fig.savefig(figdir/f'FigureS1_{case}_state.{ext}',dpi=300)
 plt.close(fig)
(a.out/'synthesis_summary.json').write_text(json.dumps(summaries,indent=2));(a.out/'analysis_source_hashes.json').write_text(json.dumps(hashes,indent=2))
fig,axs=plt.subplots(1,2,figsize=(11,5),layout='constrained')
for ax,title,wet in zip(axs,['A  Dry / disconnected crust','B  Wet / connected crust'],[False,True]):
 ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off');ax.set_title(title,fontsize=13)
 ax.add_patch(Rectangle((.08,.12),.84,.23,color='#d9c69d'));ax.text(.5,.23,'Sand: liquid + dissolved salt',ha='center',fontsize=10)
 ax.add_patch(Rectangle((.08,.35 if wet else .40),.84,.20 if wet else .15,facecolor='#9bd0da' if wet else '#dddddd',edgecolor='gray',hatch='..'));ax.text(.5,.475,'Wet porous crust' if wet else 'Vapor-resistive crust',ha='center',fontsize=10)
 ax.annotate('',xy=(.5,.85),xytext=(.5,.56 if wet else .35),arrowprops={'arrowstyle':'->','lw':2,'color':'#3a6d9c'});ax.text(.6,.72,'Vapor',color='#3a6d9c')
 if wet:ax.annotate('',xy=(.28,.55),xytext=(.28,.27),arrowprops={'arrowstyle':'->','lw':2,'color':'#168f86'})
 ax.text(.5,.94,'Air film: fixed thickness',ha='center',fontsize=10)
 ax.text(.5,.025,'Interface below crust; extra vapor + heat resistance' if not wet else 'Outer wet interface; hydraulic + heat supply required',ha='center',fontsize=9)
fig.suptitle('Alternative limiting mechanisms — not an implemented model')
for ext in ['png','pdf']:fig.savefig(figdir/f'Figure7_regimes.{ext}',dpi=300)
print(json.dumps(summaries,indent=2))
