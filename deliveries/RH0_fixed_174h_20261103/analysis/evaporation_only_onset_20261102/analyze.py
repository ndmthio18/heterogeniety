from pathlib import Path
import json,hashlib
import numpy as np
import pandas as pd
R=Path(__file__).resolve().parent;P=R.parents[1]
src=P/'analysis/rh0_fixed_80h_comparison_20261102/matched_mass.csv'
m=pd.read_csv(src)[['time_h','mass_g']]
iv=pd.DataFrame({'start_h':m.time_h.values[:-1],'end_h':m.time_h.values[1:],'loss_g':-np.diff(m.mass_g)})
iv['mid_h']=(iv.start_h+iv.end_h)/2;iv['duration_h']=iv.end_h-iv.start_h;iv['rate_g_h']=iv.loss_g/iv.duration_h
iv.to_csv(R/'experimental_rates_only.csv',index=False)
def design(t,start,kind,tau=0):
 x=(t-start)/100
 if kind=='constant':return np.array([np.ones(len(t)),x]).T
 if kind=='linear_rate':return np.array([np.ones(len(t)),x,x*x/2]).T
 if kind=='smooth_cubic':return np.array([np.ones(len(t)),x,x*x/2,x**3/3]).T
 if kind=='smooth_quartic':return np.array([np.ones(len(t)),x,x*x/2,x**3/3,x**4/4]).T
 if kind=='smooth_log':return np.array([np.ones(len(t)),x,np.log(t/start)]).T
 if kind=='smooth_exp':return np.array([np.ones(len(t)),x,1-np.exp(-(t-start)/tau)]).T
 if kind=='rate_jump':return np.array([np.ones(len(t)),x,np.maximum(t-tau,0)/100]).T
 if kind=='slope_change':return np.array([np.ones(len(t)),x,x*x/2,(np.maximum(t-tau,0)/100)**2/2]).T
def fit(t,y,start,kind,tau=0):
 X=design(t,start,kind,tau);c=np.linalg.lstsq(X,y,rcond=None)[0];res=y-X@c;sse=float(res@res)
 # All fitted mean coefficients, estimated break/timescale, and unknown variance count.
 k=len(c)+1+int(kind in ['smooth_exp','rate_jump','slope_change']);n=len(y)
 aic=n*np.log(sse/n)+2*k+2*k*(k+1)/(n-k-1)
 return dict(kind=kind,start_h=start,end_h=float(t[-1]),n=n,k=k,tau_h=float(tau),sse_g2=sse,aicc=aic,coeff=c.tolist(),mass_RMSE_g=float(np.sqrt(sse/n)))
def candidates(t,y,start,kind):
 if kind in ['rate_jump','slope_change']:grid=np.arange(t[3],t[-4]+.1,.5)
 elif kind=='smooth_exp':grid=np.geomspace(2,500,400)
 else:grid=[0]
 return [fit(t,y,start,kind,tau) for tau in grid]
results=[];profiles=[]
for start in [12,18,24,30,36]:
 for end in [174,186]:
  q=m[(m.time_h>=start)&(m.time_h<=end)];t=q.time_h.to_numpy();y=(q.mass_g.iloc[0]-q.mass_g).to_numpy()
  for kind in ['constant','linear_rate','smooth_cubic','smooth_quartic','smooth_log','smooth_exp','rate_jump','slope_change']:
   fits=candidates(t,y,start,kind);best=min(fits,key=lambda x:x['aicc']);results.append(best)
   if kind in ['rate_jump','slope_change']:
    support=[f['tau_h'] for f in fits if f['aicc']-best['aicc']<=2]
    best.update(conditional_profile_low_h=min(support),conditional_profile_high_h=max(support))
    if start==24 and end==174:
     profiles += [{**{k:v for k,v in f.items() if k!='coeff'},'delta_aicc_within_model':f['aicc']-best['aicc']} for f in fits]
d=pd.DataFrame(results);d['delta_aicc']=d.aicc-d.groupby(['start_h','end_h']).aicc.transform('min')
d.to_csv(R/'model_comparison.csv',index=False);pd.DataFrame(profiles).to_csv(R/'break_profiles.csv',index=False)
(R/'fits.json').write_text(json.dumps(results,indent=2))
(R/'source.json').write_text(json.dumps({'file':str(src),'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'used_columns':['time_h','mass_g'],'MRI_or_simulation_inputs':False,'primary_window':[24,174],'sensitivity_starts':[12,18,24,30,36],'sensitivity_ends':[174,186],'fit_basis':'integrated rate laws fitted to original weighing levels with free intercept, avoiding independent-error assumption on differenced intervals','AICc_assumption':'iid equal-variance Gaussian weighing errors; unknown repeatability/drift; rankings are conditional, not proof of physical onset','profile_interval':'delta AICc <=2 within selected break model; not a confidence interval for crystallization time'},indent=2))
print(d[d.start_h.eq(24)&d.end_h.eq(174)][['kind','tau_h','mass_RMSE_g','delta_aicc','conditional_profile_low_h','conditional_profile_high_h']].to_string(index=False))
print(d[d.kind.eq('slope_change')][['start_h','end_h','tau_h','delta_aicc']].to_string(index=False))
