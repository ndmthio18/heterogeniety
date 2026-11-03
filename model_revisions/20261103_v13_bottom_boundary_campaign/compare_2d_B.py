"""Accepted B-only comparison; failed G gates and unavailable 3D results are censored."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent
O=R/'results/B2D_174h';O.mkdir(exist_ok=True)
obs=pd.read_csv(R/'baseline_reference/MRI_profile_pairs_unchanged.csv')
mass=pd.read_csv(R/'baseline_reference/experiment_mass.csv');mass=mass[(mass.time_h>=1)&(mass.time_h<=174)].sort_values('time_h')
accept=json.loads((R/'provenance/B2D_174h_acceptance.json').read_text())
colors=['#343434','#237eb0','#df8b22','#ad3e52'];cases=['B0','B1','B2','B3']
plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':180})
fig,ax=plt.subplots(2,3,figsize=(13,7.7),constrained_layout=True)
fig2,bx=plt.subplots(2,2,figsize=(11,7),constrained_layout=True)
rows=[];fluxrows=[];late=[]
for case,color in zip(cases,colors):
 p=R/'track2d/results'/case;raw=R/'track2d/raw/runs'/case
 assert accept[case]['status']['acceptance']['completed_evaporation_h']==174
 d=pd.read_csv(p/'depth_enrichment_history.csv');pr=pd.read_csv(p/'profiles_history.csv');s=pd.read_csv(p/'enrichment_summary.csv');err=pd.read_csv(p/'MRI_nominal_comparison.csv');f=pd.read_csv(raw/'film_budget.csv')
 select=lambda mat,band:d[(d.material==mat)&(d.band==band)].sort_values('time_h')
 row={'case':case}
 for mat in ['F36','W3']:
  z=select(mat,'3_37');e=err[(err.material==mat)&(err.time_h==174)].iloc[0]
  row[mat+'_mean_M']=z.C_volume_mean_M.iloc[-1];row[mat+'_MRI_RMSE_M']=e.RMSE_M
 for a,band in zip(ax[0],['upper','middle','lower']):
  z=select('F36',band);a.plot(z.time_h,z.C_volume_mean_M,color=color,label=case)
  row[band+'_M']=z.C_volume_mean_M.iloc[-1]
  q=s[(s.material=='F36')&(s.band==band)].iloc[0]
  row[band+'_late_slope_M_h']=q.late_slope_M_h
  # All saved intervals, not just a single fitted slope.
  z=z[z.time_h>=120];inc=np.diff(z.C_volume_mean_M.to_numpy())
  late.append(dict(case=case,band=band,positive_interval_fraction=float(np.mean(inc>0)),minimum_increment_M=float(inc.min()),maximum_increment_M=float(inc.max()),interval_h=1/6))
 z=select('F36','3_37');ax[1,0].plot(z.time_h,z.C_volume_mean_M,color=color,label=case)
 row['F36_3_37_salt_gain_g']=(z.salt_total_mol.iloc[-1]-z.salt_total_mol.iloc[0])*58.4428
 row['F36_liquid_volume_ratio']=z.liquid_volume_m3.iloc[-1]/z.liquid_volume_m3.iloc[0]
 a=select('F36','all');ax[1,1].plot(a.time_h,(a.salt_total_mol-a.salt_total_mol.iloc[0])*58.4428,color=color,label=case)
 ax[1,2].plot(a.time_h,(a.liquid_volume_m3/a.liquid_volume_m3.iloc[0]-1)*1e6,color=color,label=case)
 for b,mat in zip(bx[0],['F36','W3']):
  z=pr[(pr.material==mat)&(pr.time_h==174)];b.plot(z.C_M,z.depth_mm,color=color,label=case)
 f=f[f.evaporation_time_h>=0];t=f.evaporation_time_h.to_numpy();loss=f.cumulative_reservoir_loss_g.to_numpy();water=f.cumulative_top_water_g.to_numpy()
 loss=loss-np.interp(1,t,loss);water=water-np.interp(1,t,water)
 bx[1,0].plot(t[t>=1],loss[t>=1],color=color,label=case)
 row['reservoir_solution_loss_1_174_g']=float(loss[-1]);row['top_water_loss_1_174_g']=float(water[-1])
 row['reservoir_loss_error_percent']=float((loss[-1]/mass.solution_loss_since_1h_g.iloc[-1]-1)*100)
 row['interval_rate_RMSE_g_h']=float(np.sqrt(np.mean(((np.diff(np.interp(mass.time_h,t,loss))-np.diff(mass.solution_loss_since_1h_g))/np.diff(mass.time_h))**2)))
 row['F36_max_down_174_m_s']=a.max_down_m_s.iloc[-1];row['F36_down_volume_fraction_174']=a.down_volume_fraction.iloc[-1]
 fl=pd.read_csv(p/'native_throughputs.csv');bottom=fl[(fl.kind==0)&(fl.material==0)].iloc[0];side=fl[(fl.kind==1)&(fl.material==0)].iloc[0]
 fr=dict(case=case,bottom_salt_in_g=(bottom.salt_adv_in+bottom.salt_diff_in)*58.4428,bottom_salt_out_g=(bottom.salt_adv_out+bottom.salt_diff_out)*58.4428,interface_adv_net_F36_to_W3_g=(side.salt_adv_out-side.salt_adv_in)*58.4428,interface_diff_net_F36_to_W3_g=(side.salt_diff_out-side.salt_diff_in)*58.4428)
 fr['bottom_net_salt_in_g']=fr['bottom_salt_in_g']-fr['bottom_salt_out_g'];fr['interface_net_F36_to_W3_g']=fr['interface_adv_net_F36_to_W3_g']+fr['interface_diff_net_F36_to_W3_g'];fr['net_retained_from_flux_g']=fr['bottom_net_salt_in_g']-fr['interface_net_F36_to_W3_g']
 fluxrows.append(fr);rows.append(row)
 for j,key in enumerate(['bottom_net_salt_in_g','interface_net_F36_to_W3_g','net_retained_from_flux_g']):bx[1,1].bar(j+(cases.index(case)-1.5)*.18,fr[key],.18,color=color,label=case if j==0 else None)
for a,band,limits in zip(ax[0],['Upper 3–12 mm','Middle 12–28 mm','Lower 28–37 mm'],[(3,12),(12,28),(28,37)]):
 o=obs[(obs.side=='F36')&(obs.depth_mm>=limits[0])&(obs.depth_mm<limits[1])].groupby('time_h').MRI_archived_M.mean();a.plot(o.index,o,'o',mfc='none',color='#777777',ms=3,label='Archived MRI');a.set_title(band)
o=obs[(obs.side=='F36')&(obs.depth_mm>=3)&(obs.depth_mm<37)].groupby('time_h').MRI_archived_M.mean();ax[1,0].plot(o.index,o,'o',mfc='none',color='#777777',ms=3,label='Archived MRI')
for a in ax.flat:a.set(xlabel='Evaporation time (h)',xlim=(0,180));a.grid(alpha=.2);a.legend(fontsize=7)
for a in [*ax[0],ax[1,0]]:a.set_ylabel('F36 NaCl (mol/L)')
ax[1,0].set_title('Mean, 3–37 mm');ax[1,1].set(title='Whole F36 retained salt',ylabel='NaCl gain from evaporation start (g)');ax[1,2].set(title='Whole F36 liquid storage',ylabel='Relative liquid-volume change (ppm)',ylim=(-20,10))
fig.suptitle('Accepted 2D B cases: stronger bottom resistance increases depth-wide salt retention')
for b,mat in zip(bx[0],['F36','W3']):
 o=obs[(obs.side==mat)&(obs.time_h==174)];b.plot(o.MRI_archived_M,o.depth_mm,'--',color='#777777',label='Archived MRI');b.set(title=mat+' at 174 h',xlabel='NaCl (mol/L)',ylabel='Depth (mm)',ylim=(40,0))
bx[1,0].set(title='Predicted reservoir solution loss',xlabel='Evaporation time (h)',ylabel='Loss relative to 1 h (g)',xlim=(0,180))
bx[1,0].plot(mass.time_h,mass.solution_loss_since_1h_g,'o',color='#777777',mfc='none',ms=3,label='Direct weighing')
bx[1,1].set(title='Native F36 pathways (2 h equilibration + 174 h)',ylabel='NaCl (g)',xticks=[0,1,2],xticklabels=['Bottom net in','Net to W3','Retained'])
for b in bx.flat:b.legend(fontsize=7);b.grid(alpha=.2)
fig2.suptitle('B-only mechanism comparison; G and new 3D production remain unavailable')
for figure,name in [(fig,'depth_wide_enrichment'),(fig2,'profiles_and_fluxes')]:
 for ext in ['png','pdf']:figure.savefig(O/(name+'.'+ext))
 plt.close(figure)
pd.DataFrame(rows).to_csv(O/'summary.csv',index=False);pd.DataFrame(fluxrows).to_csv(O/'native_salt_pathways.csv',index=False);pd.DataFrame(late).to_csv(O/'late_interval_changes.csv',index=False)
(O/'definitions.json').write_text(json.dumps(dict(scope='2D B0-B3 only, accepted 174h; final raw backup is independently verified',MRI='unchanged nominal-clock, whole-half profiles; no crystallization inference',flux_window='2h equilibration plus174h evaporation, native per-face gross signs before aggregation; outward interface positive F36 to W3',loss='reservoir solution loss is distinct from top pure-water evaporation; shown relative to1h',velocity='interior LS Darcy velocity, all F36; down fraction vy<-1e-8m/s; no core-only metric',limitation='short2h numerical screens are not full174h convergence; no2D-3D morphology equivalence'),indent=2))
print(pd.DataFrame(rows).to_string(index=False))
