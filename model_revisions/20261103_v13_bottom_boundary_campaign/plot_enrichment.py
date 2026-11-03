"""Plot existing evidence and available 2D/3D runs without filling missing cases."""
from pathlib import Path
import json
import numpy as np,pandas as pd,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent;O=R/'results/enrichment_figures';O.mkdir(exist_ok=True)
ref=pd.read_csv(R/'results/reference_v13/depth_enrichment_history.csv');prof=pd.read_csv(R/'results/reference_v13/profiles_history.csv');obs=pd.read_csv(R/'baseline_reference/MRI_profile_pairs_unchanged.csv')
plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'savefig.dpi':180})
fig,axs=plt.subplots(2,2,figsize=(11,7.5),constrained_layout=True)
for mat,color in [('F36','#176b9b'),('W3','#b24b29')]:
 z=ref[(ref.material==mat)&(ref.band=='3_37')];axs[0,0].plot(z.time_h,z.C_volume_mean_M,color=color,marker='.',label='accepted 3D v13 '+mat)
 o=obs[(obs.side==mat)&(obs.depth_mm>=3)&(obs.depth_mm<37)].groupby('time_h').MRI_archived_M.mean();axs[0,0].plot(o.index,o,'o',ms=4,color=color,mfc='none',label='MRI '+mat)
 z=prof[(prof.material==mat)&(prof.time_h==174)];axs[1,1].plot(z.C_M,z.depth_mm,color=color,label='v13 '+mat)
 o=obs[(obs.side==mat)&(obs.time_h==174)];axs[1,1].plot(o.MRI_archived_M,o.depth_mm,'--',color=color,label='MRI '+mat)
for band,limits,color in [('upper',(3,12),'#ac4a37'),('middle',(12,28),'#368464'),('lower',(28,37),'#6e5aa5')]:
 z=ref[(ref.material=='F36')&(ref.band==band)];axs[0,1].plot(z.time_h,z.C_volume_mean_M,color=color,marker='.',label=f'v13 {band} {limits[0]}–{limits[1]} mm')
 o=obs[(obs.side=='F36')&(obs.depth_mm>=limits[0])&(obs.depth_mm<limits[1])].groupby('time_h').MRI_archived_M.mean();axs[0,1].plot(o.index,o,'o',ms=3,mfc='none',color=color)
z=ref[(ref.material=='F36')&(ref.band=='all')].sort_values('time_h');axs[1,0].plot(z.time_h,z.salt_total_mol/z.salt_total_mol.iloc[0],label='total NaCl / initial',color='#176b9b');axs[1,0].plot(z.time_h,z.liquid_volume_m3/z.liquid_volume_m3.iloc[0],label='liquid volume / initial',color='#777777',ls='--')
axs[0,1].plot([],[],'o',mfc='none',color='#555555',ms=3,label='MRI (matching band colours)')
for ax,title in zip(axs.flat,['(a) Mean concentration, 3–37 mm','(b) F36 upper, middle and lower bands','(c) F36 retained salt and liquid storage','(d) Depth profiles at 174 h']):ax.set_title(title,loc='left');ax.grid(alpha=.15);ax.legend(fontsize=7)
for ax in [axs[0,0],axs[0,1],axs[1,0]]:ax.set(xlabel='Nominal evaporation time (h)',xlim=(0,180))
axs[0,0].set_ylabel('NaCl concentration (mol/L)');axs[0,1].set_ylabel('NaCl concentration (mol/L)');axs[1,0].set_ylabel('Ratio to initial inventory');axs[1,1].set(xlabel='NaCl concentration (mol/L)',ylabel='Depth below sand surface (mm)',ylim=(40,0))
fig.suptitle('Existing evidence: accepted 3D v13 and unchanged archived MRI\nv13 lines join saved checkpoints; new bottom-boundary cases remain pending',fontsize=11)
fig.savefig(O/'baseline_depth_wide.png');fig.savefig(O/'baseline_depth_wide.pdf');plt.close(fig)
available=[]
for dim,root in [('2D',R/'track2d/results'),('3D',R/'results')]:
 for case in ['B0','B1','B2','B3','G1','G2','G3']:
  p=root/case/'depth_enrichment_history.csv'
  if p.exists():available.append((dim,case,pd.read_csv(p)))
if available:
 fig,axs=plt.subplots(2,2,figsize=(11,7),constrained_layout=True)
 for dim,case,df in available:
  for ax,band in zip(axs.flat,['3_37','upper','middle','lower']):
   z=df[(df.material=='F36')&(df.band==band)];ax.plot(z.time_h,z.C_volume_mean_M,label=dim+' '+case);ax.set(title=band,xlabel='Evaporation time (h)',ylabel='F36 concentration (mol/L)',xlim=(0,180));ax.grid(alpha=.15)
 for ax in axs.flat:ax.legend(fontsize=7)
 fig.savefig(O/'available_case_enrichment.png');fig.savefig(O/'available_case_enrichment.pdf');plt.close(fig)
(O/'plot_sources.json').write_text(json.dumps(dict(baseline='accepted v13, eight saved checkpoints; field/ledger verified',MRI='archived nominal-clock profiles, unchanged',available_cases=[(a,b) for a,b,_ in available],interpretation='No missing case is extrapolated; MRI is comparison, not a fit target'),indent=2))
