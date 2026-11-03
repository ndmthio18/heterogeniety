"""Plot accepted 2D B profiles using page 3 of the user's v12 PDF as layout reference."""
from pathlib import Path
import json,hashlib,datetime
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import fitz
R=Path(__file__).resolve().parent;P=R.parents[1]
O=R/'results/vertical_profiles_2d';O.mkdir(exist_ok=True)
reference=R.parent/'20261102_cylinder_fixed_hydraulics_v12/results/comparison/RH0_FIXED_174H_COMPARISON.pdf'
exp_path=R/'baseline_reference/MRI_profile_pairs_unchanged.csv'
original_exp=P/'analysis/model_experiment_comparison_20261028/experimental_profiles.csv'
obs=pd.read_csv(exp_path);original=pd.read_csv(original_exp)
times=[24,60,108,174];sides=['F36','W3'];cases=['B0','B1','B2','B3']
colors={'B0':'#0072B2','B1':'#009E73','B2':'#E69F00','B3':'#CC3377'}
styles={'B0':'-','B1':'--','B2':'-.','B3':'-'}
ratios={'B0':'0','B1':'0.1','B2':'1','B3':'10'}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
profiles={};source_paths=[Path(__file__),reference,exp_path,original_exp,R/'provenance/B2D_174h_acceptance.json',R/'provenance/B2D_final_backup_verification.json']
accepted=json.loads(source_paths[-2].read_text());backup=json.loads(source_paths[-1].read_text());assert backup['state']=='passed'
for case in cases:
 assert accepted[case]['status']['acceptance']['completed_evaporation_h']==174
 p=R/'track2d/results'/case/'profiles_history.csv';source_paths.append(p);profiles[case]=pd.read_csv(p)
pairs=[];metrics=[]
for side in sides:
 for t in times:
  e=obs[(obs.side==side)&(obs.time_h==t)].sort_values('depth_mm')
  old=original[(original.side==side)&(original.time_h==t)].sort_values('depth_center_mm')
  assert len(e)==len(old)==40
  assert np.allclose(e.depth_mm,old.depth_center_mm,rtol=0,atol=1e-12)
  assert np.allclose(e.MRI_archived_M,old.archived_concentration,rtol=0,atol=1e-12)
  for case,d in profiles.items():
   z=d[(d.material==side)&np.isclose(d.time_h,t,rtol=0,atol=1e-9)].sort_values('depth_mm')
   assert len(z)==40 and np.allclose(z.depth_mm,e.depth_mm,rtol=0,atol=1e-12)
   for dep,c,m in zip(z.depth_mm,z.C_M,e.MRI_archived_M):pairs.append(dict(case=case,side=side,time_h=t,depth_mm=dep,model_liquid_M=c,MRI_archived_M=m))
   for band,mask in [('whole_0_40',np.ones(40,dtype=bool)),('interior_3_37',(z.depth_mm.to_numpy()>=3)&(z.depth_mm.to_numpy()<37))]:
    diff=z.C_M.to_numpy()[mask]-e.MRI_archived_M.to_numpy()[mask];metrics.append(dict(case=case,side=side,time_h=t,band=band,RMSE_M=float(np.sqrt(np.mean(diff**2))),bias_M=float(np.mean(diff))))
pd.DataFrame(pairs).to_csv(O/'profile_pairs.csv',index=False);pd.DataFrame(metrics).to_csv(O/'profile_metrics.csv',index=False)
pages=[]
with PdfPages(O/'RH0_2D_VERTICAL_PROFILES_COMPARISON.pdf') as pdf:
 for selection,name in [(cases,'00_all_B_cases')]+[([c],c+'_profiles') for c in cases]:
  fig,axs=plt.subplots(2,4,figsize=(12,7),sharex=True,sharey=True)
  for j,side in enumerate(sides):
   for i,t in enumerate(times):
    ax=axs[j,i];e=obs[(obs.side==side)&(obs.time_h==t)].sort_values('depth_mm')
    ax.plot(e.MRI_archived_M,e.depth_mm,'o',ms=3,mfc='white',c='k',label='Archived MRI',zorder=5)
    for case in selection:
     z=profiles[case];z=z[(z.material==side)&np.isclose(z.time_h,t,rtol=0,atol=1e-9)].sort_values('depth_mm')
     ax.plot(z.C_M,z.depth_mm,c=colors[case],ls=styles[case],lw=1.45,label=f'2D {case} ($R_f/R_{{ref}}$={ratios[case]})')
    ax.set(title=f'{side} | {t} h',xlim=(0,5.5),ylim=(40,0),xlabel='Solution C (mol/L)');ax.grid(alpha=.15)
    if i==0:ax.set_ylabel('Depth below surface (mm)')
  title='2D whole-half concentration profiles: '+('B0–B3' if len(selection)>1 else selection[0])
  fig.suptitle(title,fontsize=13,y=.984)
  handles,labels=axs[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.5,.951),ncol=len(labels),fontsize=8,frameon=False)
  fig.text(.5,.014,'Archived MRI: dissolved salt; nominal clock. Exact voxel processing / 32 min scan window not reproduced. No crystallization-time inference.',ha='center',fontsize=7.5)
  fig.tight_layout(rect=(0,.045,1,.90))
  for ext in ['png','pdf','svg']:fig.savefig(O/(name+'.'+ext),dpi=180)
  pdf.savefig(fig);plt.close(fig);pages.append(name)
# Render the actual PDF, rather than relying only on PNG exports.
doc=fitz.open(O/'RH0_2D_VERTICAL_PROFILES_COMPARISON.pdf');assert len(doc)==5
for i in [0,4]:doc[i].get_pixmap(matrix=fitz.Matrix(1.5,1.5)).save(O/f'QA_pdf_page_{i+1:02}.png')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(O/'SOURCE_PINS.json').write_text(json.dumps(dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),reference_page=3,layout='12x7 inches;2rows F36/W3;24,60,108,174h columns;0–5.5M and0–40mm axes',source_sha256={str(p.relative_to(P)):sha(p) for p in source_paths},MRI_versus_original_reference_data='all320 plotted experimental values and depths matched to1e-12',model_sampling='actual saved times; no time interpolation, fitting or smoothing',pages=pages,limitations='conventional2D compared to same archived whole-half MRI; no3D geometry equivalence; G unavailable'),indent=2),encoding='utf-8')
print(O/'RH0_2D_VERTICAL_PROFILES_COMPARISON.pdf')
