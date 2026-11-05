"""Match original MRI bins/times without shifting, smoothing or extrapolation."""
from pathlib import Path
import argparse,json,hashlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--mri',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
a.out.mkdir(parents=True,exist_ok=True); figdir=a.out.parent/'figures';figdir.mkdir(exist_ok=True)
obs=pd.read_csv(a.mri);rows=[];pairs=[];hist=[];coverage=[]
bands=[(0,3),(3,12),(12,28),(28,37),(3,37)]
windows=[(0,60),(60,84),(84,96),(96,108),(108,144),(144,174)]
for case,onset in [('Greal-81',71.9166666667),('Greal-75',61.0833333333)]:
 d=pd.read_csv(a.source/case/'depth_profiles_compact.csv').drop_duplicates(['time_s','material','depth_mm'],keep='last')
 for side,mat in [('F36',0),('W3',1)]:
  q=obs[obs.side.eq(side)].merge(d[d.material.eq(mat)],left_on=['time_h','depth_mm'],right_on=['evaporation_h','depth_mm'],how='left',validate='one_to_one')
  coverage.append({'case':case,'side':side,'observations':len(q),'matched':int(q.C_volume_mean_M.notna().sum()),'missing_times':q.loc[q.C_volume_mean_M.isna(),'time_h'].unique().tolist()})
  q['case']=case
  for dataset in ['MRI_archived_M','MRI_recalibration_M']:
   q['residual_'+dataset]=q.C_volume_mean_M-q[dataset]
   for lo,hi in bands:
    z=q[q.depth_mm.ge(lo)&q.depth_mm.lt(hi)&q.C_volume_mean_M.notna()].copy()
    for label,mask in [(f'{l}-{h}h',z.time_h.ge(l)&(z.time_h.le(h) if l==0 else z.time_h.gt(l))&z.time_h.le(h)) for l,h in windows]+[('pre_model_solid',z.time_h.lt(onset)),('post_model_solid',z.time_h.ge(onset))]:
     v=z[mask];r=v['residual_'+dataset]
     rows.append({'case':case,'side':side,'dataset':dataset,'band_mm':f'{lo}-{hi}','window':label,'n':len(v),'times_h':','.join(map(str,sorted(v.time_h.unique()))),'rmse_M':float(np.sqrt(np.mean(r*r))) if len(v) else None,'bias_M':float(r.mean()) if len(v) else None})
    for t,v in z.groupby('time_h'):
     r=v['residual_'+dataset];hist.append({'case':case,'side':side,'dataset':dataset,'band_mm':f'{lo}-{hi}','time_h':t,'model_mean_M':v.C_volume_mean_M.mean(),'MRI_mean_M':v[dataset].mean(),'bias_M':r.mean(),'rmse_M':np.sqrt(np.mean(r*r))})
  pairs.append(q)
pd.DataFrame(rows).to_csv(a.out/'MRI_window_errors.csv',index=False)
h=pd.DataFrame(hist).sort_values(['case','side','dataset','band_mm','time_h'])
groups=h.groupby(['case','side','dataset','band_mm'])
for c in ['model_mean_M','MRI_mean_M','bias_M']:
 h[c+'_interval_slope_per_h']=groups[c].diff()/groups.time_h.diff()
h.to_csv(a.out/'MRI_error_histories.csv',index=False)
q=pd.concat(pairs);q.to_csv(a.out/'MRI_matched_pairs.csv',index=False)
(a.out/'MRI_match_coverage.json').write_text(json.dumps({'coverage':coverage,'MRI_sha256':hashlib.sha256(a.mri.read_bytes()).hexdigest(),'window_rule':'[0,60], then (lower,upper]; exact time and depth joins; no interpolation','estimator':'equal weight per observed 1mm depth-bin pair; C_volume_mean_M uses overlap-weighted bulk cell volume (campaign_diagnostics.hh), not liquid-volume weighting; slopes are finite differences between observed times'},indent=2))
fig,axes=plt.subplots(2,4,figsize=(12,7),layout='constrained')
for ax,t in zip(axes.flat,[60,84,96,108,120,144,174]):
 for case,style in [('Greal-81','-'),('Greal-75','--')]:
  z=q[q.side.eq('W3')&q.case.eq(case)&q.time_h.eq(t)].sort_values('depth_mm')
  ax.plot(z.C_volume_mean_M,z.depth_mm,style,label=case)
 z=q[q.side.eq('W3')&q.case.eq('Greal-81')&q.time_h.eq(t)].sort_values('depth_mm')
 for col,mark in [('MRI_archived_M','o'),('MRI_recalibration_M','x')]: ax.plot(z[col],z.depth_mm,mark,ms=3,label=col.replace('MRI_',''))
 ax.set(title=f'{t} h',xlabel='Liquid concentration (M)',ylabel='Depth (mm)',ylim=(40,0),xlim=(0,8))
axes.flat[-1].axis('off');axes.flat[-1].legend(*axes.flat[0].get_legend_handles_labels(),loc='center')
for ext in ['png','pdf']:fig.savefig(figdir/f'Figure4_W3_profiles.{ext}',dpi=300)
plt.close(fig)
fig,axes=plt.subplots(2,2,figsize=(10,7),layout='constrained')
for row,side in zip(axes,['W3','F36']):
 for ax,band in zip(row,['0-3','3-37']):
  for case,style in [('Greal-81','-'),('Greal-75','--')]:
   z=h[h.side.eq(side)&h.band_mm.eq(band)&h.case.eq(case)&h.dataset.eq('MRI_recalibration_M')]
   ax.plot(z.time_h,z.bias_M,style+'o',ms=3,label=case)
  ax.axvline(71.9167,color='C0',ls=':');ax.axvline(61.0833,color='C1',ls=':');ax.axvspan(96,108,color='gray',alpha=.15,label='Ali hypothesis');ax.axhline(0,color='black',lw=.5)
  ax.set(title=f'{side}, {band} mm',xlabel='Evaporation time (h)',ylabel='Model minus recalibrated MRI (M)');ax.legend(fontsize=7)
for ext in ['png','pdf']:fig.savefig(figdir/f'Figure5_residuals.{ext}',dpi=300)
print(pd.DataFrame(rows).query("case=='Greal-81' and side=='W3' and dataset=='MRI_recalibration_M' and band_mm=='3-37'").to_string(index=False))
