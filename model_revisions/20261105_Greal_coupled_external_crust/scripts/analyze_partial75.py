"""Read-only comparison of accepted partial histories; no time extrapolation."""
from pathlib import Path
import hashlib,json,subprocess
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

rev=Path(__file__).resolve().parents[1]; root=rev.parents[1]
out=rev/'results/partial75'; inp=out/'inputs'
expected=json.loads((out/'remote_sha256.json').read_text())
for name,sha in expected.items():
 assert hashlib.sha256((inp/name).read_bytes()).hexdigest()==sha, name+' transfer SHA mismatch'
base=root/'model_revisions/20261104_Greal_experimental_bottom_hpcc'
paths={'Greal-81':base/'results/full174_verified/Greal-81','Coupled crust':inp}
names=['film_budget','budget','thermal_budget','mineral_budget','depth_profiles_compact','material_budgets']
data={k:{n:pd.read_csv(p/(n+'.csv')) for n in names} for k,p in paths.items()}
# Recover the solver's own molar-mass convention from its independently recorded
# mass and molar inventory, rather than rounding NaCl to 58.44 g/mol.
c=pd.read_csv(inp/'crust_budget.csv')
mass_per_mol=c[c.evaporation_time_h.eq(75)].external_mass_kg.sum()/data['Coupled crust']['mineral_budget'].iloc[-1].salt_solid_mol
assert .0584 < mass_per_mol < .0585
exp=pd.read_csv(base/'inputs/experiment.csv'); exp=exp[exp.time_h.between(1,75)].copy()
obs=pd.read_csv(base/'inputs/MRI_profile_pairs_unchanged.csv');obs=obs[obs.time_h.between(0,75)]
plt.rcParams.update({'font.size':10,'pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
def save(fig,name):
 for ext in ['png','pdf']:fig.savefig(out/(name+'.'+ext),dpi=240,facecolor='white')
 plt.close(fig)
def at(d,c,t=75):return float(np.interp(t,d.evaporation_time_h,d[c]))
metrics=[]; pairs=[]; errors=[]; endpoints={}
fig,ax=plt.subplots(2,2,figsize=(11,8),layout='constrained')
ax[0,0].plot(exp.time_h,exp.solution_loss_since_1h_g,'ko',ms=4,label='Experiment')
dt=np.diff(exp.time_h); mid=(exp.time_h.to_numpy()[1:]+exp.time_h.to_numpy()[:-1])/2
er=np.diff(exp.solution_loss_since_1h_g)/dt
ax[0,1].plot(mid,er,'ko',label='Experiment')
for j,(label,d) in enumerate(data.items()):
 f=d['film_budget']; f=f[f.evaporation_time_h.between(0,75)].drop_duplicates('time_s',keep='last')
 shift=at(f,'cumulative_reservoir_loss_g',1)
 loss=np.interp(exp.time_h,f.evaporation_time_h,f.cumulative_reservoir_loss_g)-shift
 rate=np.diff(loss)/dt
 metrics.append({'case':label,'last_measured_h':float(exp.time_h.iloc[-1]),'model_loss_g':float(loss[-1]),'measured_loss_g':float(exp.solution_loss_since_1h_g.iloc[-1]),'error_g':float(loss[-1]-exp.solution_loss_since_1h_g.iloc[-1]),'interval_rate_RMSE_g_h':float(np.sqrt(np.average((rate-er)**2,weights=dt)))})
 exp[label+'_g']=loss
 style='-' if j==0 else '--'
 q=f[f.evaporation_time_h>=1]
 ax[0,0].plot(q.evaporation_time_h,q.cumulative_reservoir_loss_g-shift,style,label=label)
 ax[0,1].plot(mid,rate,style+'o',ms=3,label=label)
 b=d['budget']; b=b[b.evaporation_time_h.between(0,75)].drop_duplicates('time_s',keep='last')
 for col,side in [('coarse_top_water_out_mol_s','F36'),('fine_top_water_out_mol_s','W3')]:
  ax[1,0].plot(b.evaporation_time_h,b[col]*18.01528*3600,style,label=label+' '+side)
 ref=data['Greal-81']['film_budget']
 delta=q.cumulative_reservoir_loss_g-shift-(np.interp(q.evaporation_time_h,ref.evaporation_time_h,ref.cumulative_reservoir_loss_g)-at(ref,'cumulative_reservoir_loss_g',1))
 ax[1,1].plot(q.evaporation_time_h,delta*1000,style,label=label)
 endpoints[label]={'loss_1_75_g':at(f,'cumulative_reservoir_loss_g')-shift,'solid_mg':at(d['mineral_budget'],'salt_solid_mol')*mass_per_mol*1e6,'T_min_C':at(d['thermal_budget'],'T_min_K')-273.15,'T_max_C':at(d['thermal_budget'],'T_max_K')-273.15}
 for c in ['water_residual_mol','salt_residual_mol']:
  endpoints[label]['max_abs_'+c]=float(b[c].abs().max())
 th=d['thermal_budget']; th=th[th.evaporation_time_h.between(0,75)]
 endpoints[label]['max_abs_energy_residual_J']=float(th.energy_residual_J.abs().max())
 for col in ['coarse_salt_mol','fine_salt_mol','cumulative_interface_adv_mol','cumulative_interface_diff_mol']:
  endpoints[label][col+'_change_0_75']=at(b,col,75)-at(b,col,0)
 p=d['depth_profiles_compact'].drop_duplicates(['material','evaporation_h','depth_mm'],keep='last')
 for side,mat in [('F36',0),('W3',1)]:
  v=obs[obs.side.eq(side)].merge(p[p.material.eq(mat)],left_on=['time_h','depth_mm'],right_on=['evaporation_h','depth_mm'],how='left',validate='one_to_one')
  v['case']=label;pairs.append(v)
  for lo,hi in [(0,3),(3,37)]:
   for dataset in ['MRI_archived_M','MRI_recalibration_M']:
    z=v[v.depth_mm.ge(lo)&v.depth_mm.lt(hi)&v.C_volume_mean_M.notna()];r=z.C_volume_mean_M-z[dataset]
    errors.append({'case':label,'side':side,'band':f'{lo}-{hi}','dataset':dataset,'n':len(z),'last_MRI_h':float(z.time_h.max()),'RMSE_M':float(np.sqrt(np.mean(r*r))),'bias_M':float(r.mean())})
for a,title,y in zip(ax.flat,['Cumulative reservoir solution loss','Complete weighing intervals only','Top water flux by sand','Difference from baseline'],['Loss since 1 h (g)','Solution-loss rate (g/h)','Top water rate (g/h)','Coupled minus baseline (mg)']):
 a.set(title=title,xlabel='Evaporation time (h)',ylabel=y,xlim=(0,75));a.grid(alpha=.2);a.legend(fontsize=8)
save(fig,'01_evaporation')
pd.DataFrame(metrics).to_csv(out/'evaporation_metrics.csv',index=False);exp.to_csv(out/'weighing_comparison.csv',index=False)
pairs=pd.concat(pairs);pairs.to_csv(out/'MRI_pairs.csv',index=False);pd.DataFrame(errors).to_csv(out/'MRI_metrics.csv',index=False)
fig,ax=plt.subplots(2,2,figsize=(10,8),layout='constrained')
for row,(side,mat) in enumerate([('F36',0),('W3',1)]):
 latest=float(pairs.loc[pairs.side.eq(side)&pairs.C_volume_mean_M.notna(),'time_h'].max())
 for j,(label,d) in enumerate(data.items()):
  v=pairs[pairs.side.eq(side)&pairs.case.eq(label)&pairs.time_h.eq(latest)].sort_values('depth_mm')
  ax[row,0].plot(v.C_volume_mean_M,v.depth_mm,'-' if j==0 else '--',label=label)
  if j==0:ax[row,0].plot(v.MRI_recalibration_M,v.depth_mm,'ko',ms=3,label='MRI recalibrated')
  p=d['depth_profiles_compact']; ts=p.loc[p.evaporation_h.le(75),'evaporation_h'].max();p=p[p.material.eq(mat)&p.evaporation_h.eq(ts)].drop_duplicates('depth_mm',keep='last').sort_values('depth_mm')
  ax[row,1].plot(p.C_volume_mean_M,p.depth_mm,'-' if j==0 else '--',label=f'{label}, {ts:g} h')
 for col in range(2):
  ax[row,col].set(title=f'{side}: '+(f'latest matched MRI, {latest:g} h' if col==0 else 'latest compact profile'),xlabel='Concentration (mol/L)',ylabel='Depth (mm)',ylim=(40,0));ax[row,col].legend(fontsize=8);ax[row,col].grid(alpha=.2)
save(fig,'02_concentration')
c=pd.read_csv(inp/'crust_budget.csv'); w=c[c.part.eq(1)].drop_duplicates('time_s',keep='last');last=w.iloc[-1]
crust={'last_time_h':float(last.evaporation_time_h),'external_salt_mg':float(last.external_mass_kg*1e6),'max_height_um':float(last.max_height_m*1e6),'bearing_area_mm2':float(last.bearing_area_m2*1e6),'instantaneous_W3_suppression_percent':float(100*(1-last.corrected_evaporation_kg_s/last.baseline_evaporation_kg_s)),'first_detectable_h':float(w.loc[w.bearing_area_m2.gt(0),'evaporation_time_h'].min()),'max_deeper_solid_mol':float(c.deeper_solid_mol.max())}
fig,ax=plt.subplots(2,2,figsize=(10,8),layout='constrained')
for j,(label,d) in enumerate(data.items()):
 m=d['mineral_budget'];m=m[m.evaporation_time_h.between(0,75)]
 ax[0,0].plot(m.evaporation_time_h,m.salt_solid_mol*mass_per_mol*1e6,'-' if j==0 else '--',label=label)
 t=d['thermal_budget'];t=t[t.evaporation_time_h.between(0,75)]
 for col in ['T_min_K','T_max_K']:ax[1,1].plot(t.evaporation_time_h,t[col]-273.15,'-' if j==0 else '--',label=label+' '+col[:5])
ax[0,1].plot(w.evaporation_time_h,w.max_height_m*1e6)
ax[1,0].plot(w.evaporation_time_h,100*(1-w.corrected_evaporation_kg_s/w.baseline_evaporation_kg_s.replace(0,np.nan)))
for a,title,y in zip(ax.flat,['Total equilibrium solid','Maximum external thickness','W3 resistance effect (same driving state)','Domain temperature extrema'],['Solid NaCl (mg)','Thickness (um)','Vapor flux suppression (%)','Temperature (C)']):
 a.set(title=title,xlabel='Evaporation time (h)',ylabel=y,xlim=(0,75));a.grid(alpha=.2)
 a.title.set_fontsize(10)
ax[0,0].legend();ax[1,1].legend(fontsize=7);save(fig,'03_crust_temperature')
sources=list(inp.glob('*.csv'))+[base/'inputs/experiment.csv',base/'inputs/MRI_profile_pairs_unchanged.csv']+[p/(n+'.csv') for p in [paths['Greal-81']] for n in names]
manifest={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
(out/'source_sha256.json').write_text(json.dumps(manifest,indent=2))
summary={'evaporation':metrics,'endpoints':endpoints,'crust':crust,'MRI':errors,'limitations':['Exploratory user-released run; full gates not passed.','HPCC stopped by output file quota; 75 h budgets but no 75 h full VTK.','No extrapolation; MRI matched exact nominal time/depth, no voxel/32min averaging.','No added crust thermal resistance.','Current-state suppression is not coupled versus baseline reservoir-loss reduction.']}
(out/'summary.json').write_text(json.dumps(summary,indent=2))
lines=['# 外部盐壳耦合：截至75 h的部分结果分析','',
 '## 数据与比较口径',
 'HPCC作业16309385因用户文件数配额导致VTK写入失败，最后接受的收支为75 h蒸发时间。75 h完整VTK缺失；此处空间浓度比较采用实际保存的compact深度剖面，不声称获得75 h三维场。Frodo重算未被改动。',
 '本案为用户放行的探索性计算，完整数值门槛尚未通过。固定气膜8.100162 mm，扩散率比0.08，外壳孔隙率0.43，面内覆盖率1；不增加盐壳导热阻力，保留原非等温边界。',
 '储液器溶液失重均以1 h为零点；不等同于纯水蒸发。误差只计算1–72 h完整实测称重窗口，75 h不插造试验值。速率RMSE按区间时长加权。MRI保持原始时间/深度配对，保留归档与再标定两套值，无时钟平移或外推。',
 '', '## 蒸发比较', '|方案|1–72 h模拟失重(g)|试验(g)|误差(g)|区间速率RMSE(g/h)|','|---|---:|---:|---:|---:|']
for m in metrics:lines.append(f"|{m['case']}|{m['model_loss_g']:.8f}|{m['measured_loss_g']:.5f}|{m['error_g']:+.8f}|{m['interval_rate_RMSE_g_h']:.8f}|")
delta=endpoints['Coupled crust']['loss_1_75_g']-endpoints['Greal-81']['loss_1_75_g']
lines += ['',f"1–75 h原模型失重{endpoints['Greal-81']['loss_1_75_g']:.8f} g，新模型{endpoints['Coupled crust']['loss_1_75_g']:.8f} g，差值{delta:.8f} g（{delta*1000:.5f} mg）。曲线几乎重合；这段数据不支持蒸发预测已有实质改善。",'', '## 盐壳与热响应',f"首次可检测承盐面{crust['first_detectable_h']:.6f} h，至75 h仅经历约{75-crust['first_detectable_h']:.2f} h反馈。W3外部固盐{crust['external_salt_mg']:.6f} mg，最大等效厚度{crust['max_height_um']:.5f} µm，承盐面积{crust['bearing_area_mm2']:.5f} mm²。当前状态下W3总通量被局地阻力降低{crust['instantaneous_W3_suppression_percent']:.6f}%；这是同一驱动状态下有/无阻力的诊断，不是新旧耦合解差异。",f"75 h新案温度范围{endpoints['Coupled crust']['T_min_C']:.6f}–{endpoints['Coupled crust']['T_max_C']:.6f} °C。最大深层正固盐库存{crust['max_deeper_solid_mol']:.4e} mol，未见显著向深层扩展。首次平衡固盐不是试验成核时刻。",'', '## 浓度与MRI', '75 h以内MRI只有0、24、48、60 h；下一次为84 h。因而没有析盐后MRI配对，不能评价析盐后的浓度改善，也不能据此认为MRI低估。已有析盐前偏差不由刚开始形成的盐壳解释。下表采用再标定MRI、3–37 mm、各时间深度点等权；0–3 mm及原始MRI结果见CSV。', '|方案|砂|RMSE(M)|偏差(M)|配对数|','|---|---|---:|---:|---:|']
for m in errors:
 if m['band']=='3-37' and m['dataset']=='MRI_recalibration_M':lines.append(f"|{m['case']}|{m['side']}|{m['RMSE_M']:.6f}|{m['bias_M']:+.6f}|{m['n']}|")
lines+=['','深度剖面是各砂整半域、重叠体积加权浓度，不是中心MRI ROI，也未实施精确体素或32 min采集平均。不能将未用于拟合浓度称为盲验证。','', '## 守恒与盐输运', '|方案|最大水残差(mol)|最大盐残差(mol)|最大能量残差(J)|','|---|---:|---:|---:|']
for k,e in endpoints.items():lines.append(f"|{k}|{e['max_abs_water_residual_mol']:.4e}|{e['max_abs_salt_residual_mol']:.4e}|{e['max_abs_energy_residual_J']:.4e}|")
lines+=['','各砂总盐增量及累计界面对流/扩散变化（0–75 h）保存在summary.json；这些是模型内部收支，不能代替试验盐量闭合。数值闭合不构成物理模型验证。','', '## 科学判断','目前最稳妥结论是：耦合反馈已进入析盐后的早期阶段，但75 h时盐量和等效厚度仍很小，整体蒸发变化极弱。尚无证据说明它改善了浓度或蒸发的时间演化。需等待更长的实际接受结果，尤其84 h之后的MRI配对；不以本窗口外推174 h效果。干盐壳与全部顶层固盐外生均为假设，非试验确认。','', '## 文件','- 01_evaporation.png/pdf：失重、区间速率、两砂通量与新旧差值。','- 02_concentration.png/pdf：最近MRI配对及最新实际compact剖面。','- 03_crust_temperature.png/pdf：固盐、厚度、局地抑制与温度。','- summary.json、MRI_metrics.csv、MRI_pairs.csv、weighing_comparison.csv、source_sha256.json：可复核结果与输入哈希。']
(out/'PARTIAL75_REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps(summary,indent=2))
