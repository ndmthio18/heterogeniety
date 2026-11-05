"""Face-resolved screening; diffusivity ratios are hypothetical, not literature fits."""
from pathlib import Path
import argparse,json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
figdir=a.out.parent/'figures';summary={}
for case,delta in [('Greal-81',.008100162249880822),('Greal-75',.0075)]:
 root=a.source/case; records=[]
 for chunk in pd.read_csv(root/'film_faces.csv',chunksize=150000):
  chunk['side']=np.where(chunk.x_m<=.025,'F36','W3')
  chunk['evap_g_h']=chunk.water_flux_kg_m2_s*chunk.area_m2*3.6e6
  chunk['aw_area']=chunk.water_activity*chunk.area_m2
  chunk['C_area']=chunk.C_mol_L*chunk.area_m2
  records.append(chunk.groupby(['time_s','side'])[['evap_g_h','aw_area','C_area','area_m2']].sum())
 surface=pd.concat(records).groupby(level=[0,1]).sum().reset_index()
 surface['aw_mean']=surface.aw_area/surface.area_m2;surface['C_mean_M']=surface.C_area/surface.area_m2;surface['time_h']=(surface.time_s-7200)/3600
 surface.to_csv(a.out/f'{case}_surface_history.csv',index=False)
 w=surface[surface.side.eq('W3')&surface.time_h.ge(0)].sort_values('time_h')
 solid=pd.read_csv(a.out/f'{case}_solid_inventory_mol.csv')
 m=np.interp(w.time_h,solid.time_h,solid.W3_top1)*.05844
 scenarios=[]
 for cover in [1.,.75,.5,.25]:
  height=m/(2165*.57*(np.pi*.025**2/2)*cover)
  for ratio in [.01,.05,.1,.25,1.]:
   rr=height/delta/ratio;local=1/(1+rr);whole_w3=1-cover+cover*local
   # Patch screening assumes uniform baseline W3 flux, fixed temperature/activity,
   # and unchanged F36. No coupled redistribution or reservoir-loss prediction.
   lost=w.evap_g_h.to_numpy()*(1-whole_w3)
   scenarios.append(pd.DataFrame({'time_h':w.time_h,'coverage':cover,'Dcrust_over_Dair':ratio,'height_mm':height*1000,'resistance_ratio':rr,'covered_patch_flux_factor':local,'W3_flux_factor':whole_w3,'W3_evap_reduction_g_h':lost}))
 allsc=pd.concat(scenarios);allsc.to_csv(a.out/f'{case}_hypothetical_resistance.csv',index=False)
 summary[case]=[]
 fig,ax=plt.subplots(figsize=(7,4),layout='constrained')
 for ratio in [.01,.05,.1,.25,1.]:
  z=allsc[allsc.coverage.eq(1)&allsc.Dcrust_over_Dair.eq(ratio)]
  reduction=np.trapz(z.W3_evap_reduction_g_h,z.time_h)
  summary[case].append({'Dcrust_over_Dair':ratio,'full_coverage_terminal_reduction_fraction':float(1-z.W3_flux_factor.iloc[-1]),'estimated_evaporated_water_reduction_g':float(reduction)})
  ax.plot(z.time_h,100*(1-z.W3_flux_factor),label=f'Dc/Da={ratio:g}'+(' (2011 fitted comparator)' if ratio==.01 else ' (scenario)'))
 ax.set(xlabel='Evaporation time (h)',ylabel='W3 flux reduction (%)',title=case+'; hypothetical diffusivity ratios, fixed driving state');ax.legend(fontsize=8)
 for ext in ['png','pdf']:fig.savefig(figdir/f'Figure3_{case}_hypothetical.{ext}',dpi=300)
 plt.close(fig)
 flux=pd.read_csv(root/'native_fluxes.csv');flux['time_h']=(flux.time_s-7200)/3600
 selected=flux[(flux.kind.eq(1)&flux.material.eq(0))|(flux.kind.eq(3)&flux.material.eq(1))].copy()
 selected['salt_net_out_mol_s']=selected.salt_adv_out-selected.salt_adv_in+selected.salt_diff_out-selected.salt_diff_in
 selected['salt_net_out_increment_mol']=selected.salt_net_out_mol_s*selected.dt_s
 selected.to_csv(a.out/f'{case}_interface_history.csv',index=False)
 fig,axes=plt.subplots(3,1,figsize=(8,8),layout='constrained',sharex=True)
 for side,style in [('W3','-'),('F36','--')]:
  z=surface[surface.side.eq(side)];axes[0].plot(z.time_h,z.evap_g_h,style,label=side)
 axes[0].set(ylabel='Evaporated water (g/h)',title=case);axes[0].legend()
 z=selected[selected.kind.eq(1)];axes[1].plot(z.time_h,z.salt_net_out_mol_s,label='F36 to W3 net');axes[1].set(ylabel='Salt transfer (mol/s)');axes[1].legend()
 axes[2].plot(solid.time_h,solid.W3_all*58.44);axes[2].set(ylabel='W3 solid NaCl (g)',xlabel='Evaporation time (h)',xlim=(0,174))
 for ext in ['png','pdf']:fig.savefig(figdir/f'Figure6_{case}.{ext}',dpi=300)
 plt.close(fig)
(a.out/'hypothetical_screening_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
