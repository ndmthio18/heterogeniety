from pathlib import Path
import json,hashlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import fitz
R=Path(__file__).resolve().parent
iv=pd.read_csv(R/'experimental_rates_only.csv');d=pd.read_csv(R/'model_comparison.csv');fits=json.loads((R/'fits.json').read_text())
primary=[f for f in fits if f['start_h']==24 and f['end_h']==174]
def rate(t,f):
 c=f['coeff'];x=(t-f['start_h'])/100;k=f['kind'];tau=f['tau_h']
 if k=='slope_change':return (c[1]+c[2]*x+c[3]*np.maximum(t-tau,0)/100)/100
 if k=='rate_jump':return (c[1]+c[2]*(t>tau))/100
 if k=='smooth_quartic':return (c[1]+c[2]*x+c[3]*x*x+c[4]*x**3)/100
 if k=='smooth_exp':return c[1]/100+c[2]/tau*np.exp(-(t-f['start_h'])/tau)
rc={'font.family':FontProperties(fname='C:/Windows/Fonts/msyh.ttc').get_name(),'font.size':10,'axes.unicode_minus':False,'pdf.fonttype':42,'svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False}
colors={'slope_change':'#0072B2','rate_jump':'#B65B00','smooth_quartic':'#009E73','smooth_exp':'#777777'}
names={'slope_change':'连续速率：下降斜率改变','rate_jump':'速率突然跳变','smooth_quartic':'光滑三次速率','smooth_exp':'光滑指数缓降'}
with plt.rc_context(rc):
 fig,axs=plt.subplots(2,2,figsize=(12.6,8.5),layout='constrained')
 ax=axs[0,0]
 ax.errorbar(iv.mid_h,iv.rate_g_h,xerr=iv.duration_h/2,fmt='o-',mfc='white',c='black',ms=3.2,lw=.8,label='原始称重：实际区间平均率')
 ax.axvspan(1,24,color='.93',zorder=0);ax.set(xlim=(0,190),ylim=(0,.55),xlabel='时间 / h',ylabel='储液器溶液失重率 / (g/h)',title='a  完整速率序列：没有使用浓度或模拟数据')
 ax.text(.37,.8,'横线为测量区间，非统计误差条\n灰区：早期过程，另做起始窗敏感性',transform=ax.transAxes,fontsize=9);ax.legend(fontsize=8,loc='lower left')
 ax=axs[0,1];q=iv[(iv.start_h>=24)&(iv.end_h<=174)];tt=np.linspace(24,174,601)
 ax.errorbar(q.mid_h,q.rate_g_h,xerr=q.duration_h/2,fmt='o',mfc='white',c='black',ms=3.5,lw=.6,label='实测区间平均')
 for k,ls in [('slope_change','-'),('smooth_quartic','--'),('rate_jump',':')]:
  f=next(x for x in primary if x['kind']==k);ax.plot(tt,rate(tt,f),c=colors[k],ls=ls,lw=1.7,label=names[k])
 ax.set(xlim=(20,178),ylim=(.24,.35),xlabel='时间 / h',ylabel='储液器溶液失重率 / (g/h)',title='b  24–174 h比较（纵轴放大）');ax.legend(fontsize=8,loc='upper right')
 ax=axs[1,0];kinds=['slope_change','smooth_quartic','smooth_exp','rate_jump'];q=d[d.start_h.eq(24)&d.end_h.eq(174)].set_index('kind')
 vals=[q.loc[k,'delta_aicc'] for k in kinds]
 ax.barh(range(4),vals,color=[colors[k] for k in kinds],height=.55);ax.set_yticks(range(4),['斜率改变','光滑三次速率','光滑指数缓降','速率突然跳变']);ax.invert_yaxis()
 for i,v in enumerate(vals):ax.text(v+1,i,f'{v:.1f}',va='center',fontsize=9)
 ax.set(xlim=(0,125),xlabel='相对最佳模型的 ΔAICc（越小越优）',title='c  同一数据、计入复杂度的条件比较')
 ax.text(.98,.90,'假定称重误差独立且同方差\n不是结晶发生概率或物理验证',transform=ax.transAxes,fontsize=8.5,ha='right')
 ax=axs[1,1]
 for end,col,mark in [(174,'#0072B2','o'),(186,'#B65B00','s')]:
  q=d[d.kind.eq('slope_change')&d.end_h.eq(end)]
  ax.plot(q.start_h,q.tau_h,marker=mark,c=col,lw=1,label=f'终点{end} h')
 ax.set(xlabel='拟合起始时间 / h',ylabel='单个候选斜率转折 / h',xticks=[12,18,24,30,36],ylim=(0,186),title='d  时窗敏感性：并非唯一、稳定的起点');ax.legend(fontsize=8.5)
 for ax in axs.flat:ax.grid(alpha=.14,axis='x' if ax is axs[1,0] else 'both')
 fig.suptitle('仅依据称重速率的阶段变化分析\n不使用MRI浓度、模拟析盐时间或预设结晶窗口',fontsize=13)
 for ext in ['pdf','png','svg']:fig.savefig(R/f'EVAPORATION_ONLY_CHANGEPOINT.{ext}',dpi=260,facecolor='white')
 plt.close(fig)
doc=fitz.open(R/'EVAPORATION_ONLY_CHANGEPOINT.pdf');doc[0].get_pixmap(matrix=fitz.Matrix(1.2,1.2)).save(R/'render.png')
report='''# 只依据蒸发速率推断阶段变化

## 数据与判据

只读取真实称重时间和质量两列。相邻质量差除以实际间隔，得到储液器溶液失重率；与此前称为“蒸发率”的量一致，但不是独立测得的样品纯水通量。不使用MRI浓度、模拟结果、章稿成核窗口作输入或先验。全部1–186h原始数据展示，不平移、不平滑、不剔除早期波动。

差分后的相邻速率共享同一次称重误差，因此不把各区间速率误差当独立样本。候选速率规律先积分，再以自由截距拟合原始称重水平。主窗口24–174h（26个称重点）；为检验早期过程和后期尾段的影响，另检查起点12/18/24/30/36h、终点174/186h。每个断点两侧至少保留4个称重点，0.5h搜索步长仅为数值拟合网格，不代表时间分辨率。

比较恒速、线性缓降、光滑多项式/指数/对数形式，以及一次速率跳变、一次连续速率斜率变化。AICc计入拟合系数、搜索的断点/时间尺度和未知误差方差；独立同方差高斯称重误差只是条件假设，没有实测重复性/漂移资料，不能把排名当作严格显著性或结晶概率。误差诊断与物理识别不足以给出成核置信区间。

## 结果

1. 24–174h最佳的已测候选形式是连续速率斜率变化，候选转折42h，称重拟合RMSE0.01126g；它落在该时窗允许的最早断点边界，因此不能解释为精确起点。转折前后速率斜率约-0.001343与-0.0003525 g/h²：表现为下降明显减缓，而不是速率突然下跳。
2. 将起点在12–36h间改变，终点保持174h，单转折拟合给出约42–54h；起点36h时光滑指数规律与斜率转折的ΔAICc小于2，不能明显区分。因而可把约40–60h视为一个值得检验的速率阶段变化候选区，但不是已测得的结晶时间窗。
3. 强行用“一次速率跳变”解释主窗口，会得到约93.5h，然而ΔAICc约109、称重RMSE0.09776g，明显逊于斜率变化形式。不能仅因为拟合能给出某时刻，就认为该时刻有可靠依据。
4. 把终点扩到186h且起点取30/36h，单个最优斜率转折会移至167–168h，反映末段速率回升。一个断点无法同时刻画所有阶段，起点识别对分析窗口敏感。未继续添加断点追求拟合，因为那仍不能提供结晶独特性。

## 如何解释结晶

若预先假设：外部传质和温度基本稳定、供液与储量响应没有独立转折，且析盐使表面溶液浓缩受限、从而减弱活度造成的速率下降，则约40–60h的斜率减缓可以成为“结晶可能开始影响总体蒸发”的候选信号。上述条件尚未由这条总失重曲线独立验证。

同一种减缓也可来自不发生结晶的传质/浓缩演化。这里没有用无析盐物理模型证明必须引入结晶，也没有实际称重误差模型。因此当前可报告的是速率阶段变化候选，不宜报告确定的首次晶体时刻。曲线本身没有为约96h的突然结晶提供优势解释。

这项分析纠正此前偏重MRI浓度的依据选择：后续关于本次推断的讨论应以本目录称重速率证据为准，不把章稿浓度推测当成先验或校验答案。
'''
(R/'EVAPORATION_ONLY_INFERENCE.md').write_text(report,encoding='utf-8')
(R/'checks.json').write_text(json.dumps({'used_only_weighing':True,'MRI_or_model_inputs':False,'visual_review':'pending','fit_error_assumption':'iid equal-variance weighing errors; conditional only','no_claim_of_identified_crystallization_onset':True},indent=2))
