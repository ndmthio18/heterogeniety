"""Compare a hash-verified fixed Frodo snapshot with Greal-81 and experiment."""
from pathlib import Path
import json,hashlib,tarfile
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
rev=Path(__file__).resolve().parents[1];out=rev/'results/partial133';inp=out/'inputs'
archive=out/'snapshot.tar.gz'
assert hashlib.sha256(archive.read_bytes()).hexdigest()=='8b2eebe02e7562e7175f93effac6a7ba1a05daeede436effad0ba4963da5312c'
with tarfile.open(archive) as t:
 for m in t.getmembers():
  assert m.isfile() and Path(m.name).name==m.name
 t.extractall(inp,filter='data')
manifest=json.loads((inp/'manifest.json').read_text());end=manifest['evaporation_h']
for n,h in manifest['sha256'].items():assert hashlib.sha256((inp/n).read_bytes()).hexdigest()==h
base=rev.parent/'20261104_Greal_experimental_bottom_hpcc'
names=['film_budget','budget','mineral_budget','thermal_budget','depth_profiles_compact']
data={label:{n:pd.read_csv(path/(n+'.csv')) for n in names} for label,path in [('Greal-81',base/'results/full174_verified/Greal-81'),('Coupled crust',inp)]}
exp=pd.read_csv(base/'inputs/experiment.csv');exp=exp[exp.time_h.between(1,end)].copy()
obs=pd.read_csv(base/'inputs/MRI_profile_pairs_unchanged.csv');obs=obs[obs.time_h.between(0,end)].copy();obs['time_h']=obs.time_h.astype(float)
c=pd.read_csv(inp/'crust_budget.csv');w=c[c.part.eq(1)].drop_duplicates('time_s',keep='last');last=w.iloc[-1]
mm=c[c.time_s.eq(manifest['accepted_time_s'])].external_mass_kg.sum()/data['Coupled crust']['mineral_budget'].iloc[-1].salt_solid_mol
assert .0584<mm<.0585
plt.rcParams.update({'font.size':9,'axes.titlesize':10,'pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
colors=['#0072B2','#D55E00'];styles=['-','--'];pdf=PdfPages(out/'PARTIAL_COMPARISON.pdf')
def save(fig,name):
 fig.suptitle(f'Exploratory coupled crust: accepted snapshot through {end:.2f} h',fontsize=12)
 fig.savefig(out/(name+'.png'),dpi=240,facecolor='white');fig.savefig(out/(name+'.pdf'));pdf.savefig(fig);plt.close(fig)
def trim(d):return d[d.evaporation_time_h.between(0,end)].drop_duplicates('time_s',keep='last')
def value(d,col,t):return float(np.interp(t,d.evaporation_time_h,d[col]))
def finish(ax,y,title):ax.set(xlabel='Evaporation time (h)',ylabel=y,title=title,xlim=(0,end));ax.grid(alpha=.2);ax.legend(fontsize=7)
metrics=[];ends={};fig,axes=plt.subplots(2,2,figsize=(11,8),layout='constrained')
tx=exp.time_h.to_numpy();dt=np.diff(tx);mid=(tx[1:]+tx[:-1])/2;er=np.diff(exp.solution_loss_since_1h_g)/dt
axes[0,0].plot(tx,exp.solution_loss_since_1h_g,'ko',ms=3,label='Experiment')
axes[0,1].plot(mid,er,'ko',ms=3,label='Experiment')
for j,(label,d) in enumerate(data.items()):
 f=trim(d['film_budget']);b=trim(d['budget']);t=trim(d['thermal_budget']);m=trim(d['mineral_budget'])
 offset=value(f,'cumulative_reservoir_loss_g',1);loss=np.interp(tx,f.evaporation_time_h,f.cumulative_reservoir_loss_g)-offset
 rate=np.diff(loss)/dt;exp[label+'_loss_g']=loss
 metrics.append({'case':label,'window_end_h':float(tx[-1]),'loss_g':float(loss[-1]),'observed_g':float(exp.solution_loss_since_1h_g.iloc[-1]),'error_g':float(loss[-1]-exp.solution_loss_since_1h_g.iloc[-1]),'rate_RMSE_g_h':float(np.sqrt(np.average((rate-er)**2,weights=dt)))})
 q=f[f.evaporation_time_h.ge(1)];axes[0,0].plot(q.evaporation_time_h,q.cumulative_reservoir_loss_g-offset,styles[j],color=colors[j],label=label)
 axes[0,1].plot(mid,rate,styles[j],color=colors[j],label=label)
 for col,side,color in [('coarse_top_water_out_mol_s','F36','#0072B2'),('fine_top_water_out_mol_s','W3','#D55E00')]:axes[1,0].plot(b.evaporation_time_h,b[col]*18.01528*3600,styles[j],color=color,label=label+' '+side)
 ref=data['Greal-81']['film_budget'];delta=q.cumulative_reservoir_loss_g-offset-(np.interp(q.evaporation_time_h,ref.evaporation_time_h,ref.cumulative_reservoir_loss_g)-value(ref,'cumulative_reservoir_loss_g',1))
 axes[1,1].plot(q.evaporation_time_h,delta,styles[j],color=colors[j],label=label)
 ends[label]={'loss_1_end_g':value(f,'cumulative_reservoir_loss_g',end)-offset,'solid_mg':value(m,'salt_solid_mol',end)*mm*1e6,'Tmin_C':value(t,'T_min_K',end)-273.15,'Tmax_C':value(t,'T_max_K',end)-273.15,'max_water_residual_mol':float(b.water_residual_mol.abs().max()),'max_salt_residual_mol':float(b.salt_residual_mol.abs().max()),'max_energy_residual_J':float(t.energy_residual_J.abs().max())}
for ax,y,title in zip(axes.flat,['Loss since 1 h (g)','Interval solution-loss rate (g/h)','Top water rate (g/h)','Loss difference from baseline (g)'],['Reservoir solution loss','Complete weighing intervals','Separate sand evaporation','Coupled response relative to baseline']):finish(ax,y,title)
save(fig,'01_evaporation')
pairs=[];err=[]
for label,d in data.items():
 p=d['depth_profiles_compact'].drop_duplicates(['material','evaporation_h','depth_mm'],keep='last')
 for mat,side in [(0,'F36'),(1,'W3')]:
  q=obs[obs.side.eq(side)].merge(p[p.material.eq(mat)],left_on=['time_h','depth_mm'],right_on=['evaporation_h','depth_mm'],how='left',validate='one_to_one');q['case']=label;pairs.append(q)
  assert q.C_volume_mean_M.notna().all()
  for dataset in ['MRI_archived_M','MRI_recalibration_M']:
   for lo,hi in [(0,3),(3,37)]:
    for win,mask in [('pre',q.time_h.le(60)),('post',q.time_h.ge(84)),('all',q.time_h.ge(0))]:
     v=q[mask&q.depth_mm.ge(lo)&q.depth_mm.lt(hi)];r=v.C_volume_mean_M-v[dataset]
     err.append({'case':label,'side':side,'dataset':dataset,'band':f'{lo}-{hi}','window':win,'n':len(v),'RMSE_M':float(np.sqrt(np.mean(r*r))),'bias_M':float(r.mean())})
pairs=pd.concat(pairs);pairs.to_csv(out/'MRI_pairs.csv',index=False);pd.DataFrame(err).to_csv(out/'MRI_metrics.csv',index=False)
fig,axes=plt.subplots(2,4,figsize=(13,8),layout='constrained')
for row,side in enumerate(['F36','W3']):
 for col,time in enumerate([60,84,108,120]):
  ax=axes[row,col]
  for j,label in enumerate(data):
   q=pairs[pairs.side.eq(side)&pairs.case.eq(label)&pairs.time_h.eq(time)].sort_values('depth_mm')
   ax.plot(q.C_volume_mean_M,q.depth_mm,styles[j],color=colors[j],label=label)
   if j==0:ax.plot(q.MRI_recalibration_M,q.depth_mm,'ko',ms=2.5,label='MRI recalibrated')
  ax.set(title=f'{side}, {time} h',xlabel='Concentration (M)',ylabel='Depth (mm)',ylim=(40,0));ax.grid(alpha=.2)
axes[0,0].legend(fontsize=7);save(fig,'02_MRI_profiles')
fig,axes=plt.subplots(2,2,figsize=(11,8),layout='constrained')
for row,side in enumerate(['F36','W3']):
 for j,label in enumerate(data):
  q=pairs[pairs.side.eq(side)&pairs.case.eq(label)&pairs.depth_mm.between(3,36.999)]
  for t,v in q.groupby('time_h'):
   r=v.C_volume_mean_M-v.MRI_recalibration_M
   axes[row,0].plot(t,np.sqrt(np.mean(r*r)),'o' if j==0 else 'x',color=colors[j],label=label if t==0 else None)
  p=data[label]['depth_profiles_compact'];p=p[p.material.eq(row)&p.evaporation_h.le(end)].drop_duplicates(['evaporation_h','depth_mm'],keep='last')
  ref=data['Greal-81']['depth_profiles_compact'];ref=ref[ref.material.eq(row)].drop_duplicates(['evaporation_h','depth_mm'],keep='last')
  z=p.merge(ref,on=['evaporation_h','depth_mm'],suffixes=('_new','_old'));z['absdiff']=(z.C_volume_mean_M_new-z.C_volume_mean_M_old).abs();curve=z.groupby('evaporation_h').absdiff.max()
  axes[row,1].plot(curve.index,curve.values,styles[j],color=colors[j],label=label)
 finish(axes[row,0],'MRI RMSE (M)',side+' 3–37 mm, each observed time')
 finish(axes[row,1],'Max absolute profile difference (M)',side+' depth-bin difference from baseline')
save(fig,'03_concentration_differences')
fig,axes=plt.subplots(2,2,figsize=(11,8),layout='constrained')
for j,(label,d) in enumerate(data.items()):
 m=trim(d['mineral_budget']);t=trim(d['thermal_budget'])
 axes[0,0].plot(m.evaporation_time_h,m.salt_solid_mol*mm*1e6,styles[j],color=colors[j],label=label)
 for col,color in [('T_min_K','#0072B2'),('T_max_K','#D55E00')]:axes[1,1].plot(t.evaporation_time_h,t[col]-273.15,styles[j],color=color,label=label+' '+col[:5])
axes[0,1].plot(w.evaporation_time_h,w.max_height_m*1000,label='Maximum')
axes[1,0].plot(w.evaporation_time_h,100*(1-w.corrected_evaporation_kg_s/w.baseline_evaporation_kg_s.replace(0,np.nan)),label='W3 integrated resistance effect')
for ax,y,title in zip(axes.flat,['Solid NaCl (mg)','Equivalent external height (mm)','Flux suppression (%)','Temperature (°C)'],['Equilibrium solid inventory','Maximum crust thickness','W3 vapor resistance at current state','Domain temperature extrema']):finish(ax,y,title)
save(fig,'04_crust_temperature');pdf.close()
pd.DataFrame(metrics).to_csv(out/'evaporation_metrics.csv',index=False);exp.to_csv(out/'weighing_comparison.csv',index=False)
summary={'end_h':end,'evaporation':metrics,'endpoints':ends,'crust':{'mass_mg':float(last.external_mass_kg*1e6),'max_height_mm':float(last.max_height_m*1000),'suppression_percent':float(100*(1-last.corrected_evaporation_kg_s/last.baseline_evaporation_kg_s))},'MRI':err}
(out/'summary.json').write_text(json.dumps(summary,indent=2))
sources=[base/'inputs/experiment.csv',base/'inputs/MRI_profile_pairs_unchanged.csv']+list((base/'results/full174_verified/Greal-81').glob('*.csv'))
(out/'baseline_source_hashes.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},indent=2))
lines=['# Frodo部分结果对比',f'固定快照截止：{end:.5f} h；非174 h完整验收结果。源文件、归档SHA及成员SHA全部核验。','', '图1：储液器溶液失重从1 h归零；误差仅用已覆盖完整称重区间；图内不外推。两砂顶面通量为水，不能与储液器溶液失重直接等同。','图2：整半域、原始时间和深度的再标定MRI配对；未采用时钟平移、中心ROI或32 min平均。','图3：分别展示MRI误差和新旧深度平均剖面差异；不能据此证明三维局部场相同。','图4：等效外部盐壳与原能量边界响应；未添加盐壳导热阻力。同状态阻力抑制不等于新旧解累计失重差。','', '## 完整称重窗口误差','|方案|截止(h)|模拟(g)|实测(g)|误差(g)|速率RMSE(g/h)|','|---|---:|---:|---:|---:|---:|']
for m in metrics:lines.append(f"|{m['case']}|{m['window_end_h']:g}|{m['loss_g']:.6f}|{m['observed_g']:.4f}|{m['error_g']:+.6f}|{m['rate_RMSE_g_h']:.6f}|")
lines+=['','## 析盐后MRI：84–120 h、3–37 mm、所有配对等权','|方案|砂|RMSE(M)|偏差(M)|','|---|---|---:|---:|']
for e in err:
 if e['window']=='post' and e['band']=='3-37' and e['dataset']=='MRI_recalibration_M':lines.append(f"|{e['case']}|{e['side']}|{e['RMSE_M']:.6f}|{e['bias_M']:+.6f}|")
lines+=['','数值闭合见summary.json；模型尚未完成全部数值门槛，为用户放行的探索性结果。盐壳为假设干扩散层，不代表试验验证的形态。MRI已曾查看，不是盲验证；未进行新的网格/时间步收敛验收。','', '复现：运行 scripts/plot_partial_snapshot.py。原75 h分析保留，Frodo求解未被修改。']
(out/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'end':end,'evaporation':metrics,'endpoints':ends,'crust':summary['crust'],'MRI_post':[e for e in err if e['window']=='post' and e['band']=='3-37' and e['dataset']=='MRI_recalibration_M']},indent=2))
