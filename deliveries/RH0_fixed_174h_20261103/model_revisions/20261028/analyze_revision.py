"""Reproducible, read-only analysis of isolated revision runs and Ali profiles."""
from pathlib import Path
import csv,hashlib,json,sys,xml.etree.ElementTree as ET
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[1]
sys.path.insert(0,str(PROJECT/'analysis'))
from redraw_molarity_comparison import vtu
OUT=ROOT/'results'
OUT.mkdir(exist_ok=True)
Z=np.arange(40)+.5
SIDES=['F36','W3']
BANDS={'upper_3_10':(3,10),'middle_10_20':(10,20),'deep_20_37':(20,37),'core_3_37':(3,37)}
COLORS={'legacy':'#777777','revised_isothermal':'#0072B2','revised_nonisothermal':'#D55E00'}

def read(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def write(name,rows):
    with (OUT/name).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def load_profiles(folder,pre,label,targets=None):
    pvd=next(folder.glob('*.pvd'))
    datasets=ET.parse(pvd).findall('.//DataSet')
    times=[];profiles=[];sources=[];frames=[]
    for entry in datasets:
        t=float(entry.get('timestep'))/3600-pre
        if t < -1e-8:continue
        if targets is not None and not any(abs(t-q)<1e-7 for q in targets):continue
        path=folder/entry.get('file');f,c,lo,hi,dx,_=vtu(path)
        conc=f['x^NaCl_liq']*f['rhoMolar_liq']/1000
        assert np.isfinite(conc).all() and np.all((conc>=0)&(f['x^H2O_liq']>=0))
        overlap=np.maximum(0,np.minimum(hi[None,:],(Z[:,None]+.5)/1000)-np.maximum(lo[None,:],(Z[:,None]-.5)/1000))
        pp=[]
        for side in SIDES:
            mask=c[:,0]<.025 if side=='F36' else c[:,0]>=.025
            w=overlap*dx[None,:]*mask[None,:]
            pp.append((w@conc)/w.sum(1))
        times.append(t);profiles.append(pp)
        sources.append({'file':str(path.relative_to(PROJECT)),'sha256':digest(path),'evaporation_time_h':t})
        vel=f.get('velocity_liq (m/s)',np.zeros((len(c),3)))
        frames.append({'model':label,'time_h':t,'S_min':float(f['S_liq'].min()),'C_max_mol_L':float(conc.max()),
                       'T_min_K':float(f['T'].min()) if 'T' in f else None,'T_max_K':float(f['T'].max()) if 'T' in f else None,
                       'coarse_min_vz_core_m_s':float(vel[(c[:,0]>.005)&(c[:,0]<.022)&(c[:,1]>.005)&(c[:,1]<.035),1].min()),
                       'fine_min_vz_core_m_s':float(vel[(c[:,0]>.028)&(c[:,0]<.045)&(c[:,1]>.005)&(c[:,1]<.035),1].min())})
    times=np.array(times);profiles=np.array(profiles)
    assert len(times)>0 and np.all(np.diff(times)>0)
    return times,profiles,sources,frames

def at(data,t,j):
    times,profiles=data[:2]
    assert times[0]-1e-8<=t<=times[-1]+1e-8
    return np.array([np.interp(t,times,profiles[:,j,k]) for k in range(40)])

def main():
    exfile=PROJECT/'analysis/model_experiment_comparison_20261028/experimental_profiles.csv'
    exrows=read(exfile)
    exp={}
    for side in SIDES:
        for t in [0.,8.,24.]:
            rr=sorted((r for r in exrows if r['side']==side and float(r['time_h'])==t),key=lambda r:float(r['depth_center_mm']))
            assert len(rr)==40
            exp[side,t]=np.array([float(r['archived_concentration']) for r in rr])
    models={'legacy':load_profiles(PROJECT/'liqin_snapshot/Simulation_Data/REV_scale/hete_experiment/hete_test',0,'legacy',[0,8,24])}
    for label,run in [('revised_isothermal','B0_24h_v03'),('revised_nonisothermal','B0_24h_NI_abs1e8_v03')]:
        folder=ROOT/'runs'/run
        if folder.exists() and (folder/'run_status.json').exists():models[label]=load_profiles(folder,2,label)
    metrics=[];pairs=[]
    for label,data in models.items():
        for j,side in enumerate(SIDES):
            for t in [0.,8.,24.]:
                if t>data[0][-1]+1e-8:continue
                m=at(data,t,j);e=exp[side,t];dm=m-at(data,0,j);de=e-exp[side,0.]
                for k,z in enumerate(Z):pairs.append({'model':label,'side':side,'time_h':t,'depth_mm':z,'model_mol_L':m[k],'experiment_mol_L':e[k],'bias_mol_L':m[k]-e[k]})
                for band,(a,b) in BANDS.items():
                    k=(Z>=a)&(Z<b)
                    metrics.append({'model':label,'side':side,'time_h':t,'band':band,'model_mean_mol_L':float(m[k].mean()),
                                    'experiment_mean_mol_L':float(e[k].mean()),'mean_bias_mol_L':float((m-e)[k].mean()),
                                    'relative_mean_bias':float((m-e)[k].mean()/e[k].mean()),'rmse_mol_L':float(np.sqrt(np.mean((m-e)[k]**2))),
                                    'model_change_mol_L':float(dm[k].mean()),'experiment_change_mol_L':float(de[k].mean()),
                                    'change_rmse_mol_L':float(np.sqrt(np.mean((dm-de)[k]**2)))})
    write('profile_metrics.csv',metrics);write('profile_comparison.csv',pairs)
    write('frame_diagnostics.csv',[r for d in models.values() for r in d[3]])
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
    fig,axes=plt.subplots(2,3,figsize=(11,7.6),sharey=True)
    for j,side in enumerate(SIDES):
        for k,t in enumerate([0.,8.,24.]):
            ax=axes[j,k];ax.plot(exp[side,t],Z,'o',ms=3,color='black',label='Ali: archived profile')
            for label,data in models.items():
                if t<=data[0][-1]+1e-8:ax.plot(at(data,t,j),Z,color=COLORS[label],ls='--' if label=='legacy' else '-',lw=1.6,label=label.replace('_',' '))
            ax.axhspan(0,3,color='.92');ax.axhspan(37,40,color='.92');ax.set_title(f'{side}, {t:g} h');ax.set_xlabel('Solution concentration (mol/L)');ax.grid(alpha=.15)
            if k==0:ax.set_ylabel('Depth below sand surface (mm)')
    axes[0,0].set_ylim(40,0)
    handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='lower center',bbox_to_anchor=(.5,.035),ncol=len(labels),fontsize=9)
    fig.suptitle('Diagnostic revision: nominal-time snapshots, identical depth registration',fontsize=12)
    fig.text(.5,.015,'Uniform per-area water forcing; idealized distributed supply. Shading: excluded outer depth bands.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.085,1,.96));fig.savefig(OUT/'01_profiles.png',dpi=220);fig.savefig(OUT/'01_profiles.pdf');plt.close(fig)
    budgets={};summary={}
    for folder in sorted((ROOT/'runs').glob('*v03')):
        if not (folder/'budget.csv').exists():continue
        rows=read(folder/'budget.csv');arr={k:np.array([float(r[k]) for r in rows]) for k in rows[0]}
        budgets[folder.name]=arr
        manifest=json.loads((folder/'run_manifest.json').read_text());state=json.loads((folder/'run_status.json').read_text())
        if len(rows)<2:
            summary[folder.name]={'run_status':state,'returncode':manifest.get('returncode'),'accepted_steps':0};continue
        summary[folder.name]={'run_status':state,'returncode':manifest.get('returncode'),'binary_sha256':manifest['binary_sha256'],
                              'accepted_steps':len(rows)-1,'time_strictly_increasing':bool(np.all(np.diff(arr['time_s'])>0)),
                              'min_accepted_dt_s':float(arr['dt_s'][1:].min()),'max_accepted_dt_s':float(arr['dt_s'][1:].max()),
                              'max_abs_water_residual_mol':float(np.max(np.abs(arr['water_residual_mol']))),
                              'max_abs_salt_residual_mol':float(np.max(np.abs(arr['salt_residual_mol']))),
                              'max_abs_coarse_salt_residual_mol':float(np.max(np.abs(arr['coarse_residual_mol']))),
                              'max_abs_fine_salt_residual_mol':float(np.max(np.abs(arr['fine_residual_mol']))),
                              'water_relative_residual':float(np.max(np.abs(arr['water_residual_mol']))/arr['water_mol'][0]),
                              'salt_relative_residual':float(np.max(np.abs(arr['salt_residual_mol']))/arr['salt_total_mol'][0]),
                              'S_min':float(arr['S_min'].min()),'C_max_mol_L':float(arr['C_max_mol_L'].max()),
                              'precip_vf_max':float(arr['precip_vf_max'].max()),
                              'cumulative_interface_adv_mol':float(arr['cumulative_interface_adv_mol'][-1]),
                              'cumulative_interface_diff_mol':float(arr['cumulative_interface_diff_mol'][-1])}
    (OUT/'verification.json').write_text(json.dumps(summary,indent=2))
    sensitivity={}
    dtfolder=ROOT/'runs/B0_8h_dt150_v03'
    if (dtfolder/'run_status.json').exists():
        fine=load_profiles(dtfolder,2,'dt150')
        sensitivity['window_h']=[0,8]
        sensitivity['limitation']='Time-step sensitivity only; same mesh and seed. This does not establish grid convergence or 24h time convergence.'
        changes=[]
        for j,side in enumerate(SIDES):
            a=at(models['revised_isothermal'],8,j);b=at(fine,8,j)
            for band,(z0,z1) in BANDS.items():
                k=(Z>=z0)&(Z<z1)
                changes.append({'side':side,'band':band,'dt300_mean_mol_L':float(a[k].mean()),'dt150_mean_mol_L':float(b[k].mean()),
                                'relative_mean_change':float((b[k].mean()-a[k].mean())/a[k].mean()),'max_abs_profile_change_mol_L':float(np.abs(b[k]-a[k]).max())})
        sensitivity['profiles']=changes
        a=budgets['B0_24h_v03'];i=np.argmin(np.abs(a['evaporation_time_h']-8));b=budgets['B0_8h_dt150_v03']
        for key in ['salt_total_mol','coarse_salt_mol','fine_salt_mol','cumulative_interface_adv_mol','cumulative_interface_diff_mol']:
            av,bv=float(a[key][i]),float(b[key][-1]);sensitivity[key]={'dt300':av,'dt150':bv,'relative_change':(bv-av)/av if av else None}
        (OUT/'time_step_sensitivity.json').write_text(json.dumps(sensitivity,indent=2))
    fig,axes=plt.subplots(2,2,figsize=(10,6.8))
    for label,run in [('revised_isothermal','B0_24h_v03'),('revised_nonisothermal','B0_24h_NI_abs1e8_v03')]:
        if run not in budgets:continue
        a=budgets[run];k=a['evaporation_time_h']>=0;t=a['evaporation_time_h'][k];color=COLORS[label]
        axes[0,0].plot(t,a['S_min'][k],color=color,label=label.replace('_',' '))
        axes[0,1].plot(t,a['C_max_mol_L'][k],color=color)
        axes[1,0].plot(t,a['cumulative_interface_adv_mol'][k],color=color,label=label.replace('_',' ')+' adv.')
        axes[1,0].plot(t,a['cumulative_interface_diff_mol'][k],color=color,ls='--',label=label.replace('_',' ')+' diff.')
        axes[1,1].semilogy(t,np.maximum(1e-17,np.abs(a['salt_residual_mol'][k]))/a['salt_total_mol'][0],color=color)
    for ax,title,y in zip(axes.flat,['Minimum liquid saturation','Maximum concentration','Net interface transfer: positive F36 to W3','Global total-salt budget'],['Liquid saturation','mol/L','mol per metre of planar depth','Absolute residual / initial salt']):
        ax.set_title(title,fontsize=10);ax.set_xlabel('Evaporation time (h)');ax.set_ylabel(y);ax.grid(alpha=.2)
    axes[1,1].set_ylim(1e-15,1e-2);axes[1,1].axhline(.001,color='.4',ls=':',label='Registered budget gate (0.1%)');axes[1,1].legend(fontsize=8)
    axes[0,0].legend(fontsize=8);axes[1,0].legend(fontsize=7);fig.tight_layout();fig.savefig(OUT/'02_diagnostics.png',dpi=220);fig.savefig(OUT/'02_diagnostics.pdf');plt.close(fig)
    provenance={'experiment':{'file':str(exfile.relative_to(PROJECT)),'sha256':digest(exfile)},
                'comparison':'solution molarity x_NaCl*rho_molar/1000; 1-mm bins, exact planar cell/bin overlap; instantaneous nominal snapshots, no MRI temporal averaging; 3-37mm core',
                'sources':[s for d in models.values() for s in d[2]],'analysis_sha256':digest(Path(__file__))}
    (OUT/'analysis_provenance.json').write_text(json.dumps(provenance,indent=2))
    comparisons={}
    for name,folder,label in [('supply','B0_24h_central_v03','central aperture'),('temperature','B0_24h_NI_abs1e8_v03','nonisothermal')]:
        path=ROOT/'runs'/folder
        if not (path/'run_status.json').exists():continue
        candidate=load_profiles(path,2,label)
        if candidate[0][-1]<24-1e-8:continue
        table=[]
        for j,side in enumerate(SIDES):
            a=at(models['revised_isothermal'],24,j);b=at(candidate,24,j)
            for band,(z0,z1) in BANDS.items():
                k=(Z>=z0)&(Z<z1);e=exp[side,24.][k]
                table.append({'side':side,'band':band,'reference_mean_mol_L':float(a[k].mean()),'candidate_mean_mol_L':float(b[k].mean()),
                              'relative_change_from_reference':float((b[k].mean()-a[k].mean())/a[k].mean()),
                              'reference_experiment_bias':float((a[k].mean()-e.mean())/e.mean()),'candidate_experiment_bias':float((b[k].mean()-e.mean())/e.mean())})
        compare={'reference':'B0_24h_v03','candidate':folder,'time_h':24,'profiles':table,
                 'limitation':'idealized sensitivity, not measured device reconstruction' if name=='supply' else 'same assumed heat boundaries; NI nonlinear absolute tolerance differs, energy budget not independently closed'}
        for key in ['cumulative_interface_adv_mol','cumulative_interface_diff_mol','salt_total_mol','fine_salt_mol']:
            compare[key]={'reference':float(budgets['B0_24h_v03'][key][-1]),'candidate':float(budgets[folder][key][-1])}
        if name=='temperature':
            compare['final_T_min_K']=candidate[3][-1]['T_min_K'];compare['final_T_max_K']=candidate[3][-1]['T_max_K']
        comparisons[name]=compare
        (OUT/(name+'_sensitivity.json')).write_text(json.dumps(compare,indent=2))
        if name=='supply':
            fig,axes=plt.subplots(1,2,figsize=(8,5),sharey=True)
            for j,side in enumerate(SIDES):
                ax=axes[j];ax.plot(exp[side,24.],Z,'o',ms=3,color='black',label='Ali: archived profile')
                ax.plot(at(models['revised_isothermal'],24,j),Z,color=COLORS['revised_isothermal'],label='Distributed supply')
                ax.plot(at(candidate,24,j),Z,color='#CC79A7',label='Central 2-mm aperture')
                ax.set_title(side+', 24 h');ax.set_xlabel('Solution concentration (mol/L)');ax.grid(alpha=.2)
            axes[0].set_ylim(40,0);axes[0].set_ylabel('Depth below sand surface (mm)')
            handles,labels=axes[0].get_legend_handles_labels();fig.legend(handles,labels,loc='lower center',ncol=3,fontsize=8)
            fig.suptitle('Supply-boundary sensitivity: two idealized limits')
            fig.tight_layout(rect=(0,.06,1,.94));fig.savefig(OUT/'03_supply_sensitivity.png',dpi=220);fig.savefig(OUT/'03_supply_sensitivity.pdf');plt.close(fig)
    make_report(summary,metrics,sensitivity,models,comparisons)
    print(json.dumps({'runs':summary,'24h_upper_and_core':[r for r in metrics if r['time_h']==24 and r['band'] in ['upper_3_10','core_3_37']]},indent=2))

def make_report(summary,metrics,sensitivity,models,comparisons):
    lines=['# 模型修改与首轮重算报告','',
           '2026-10-28。按已批准方案实施首阶段：计算实现修复、液压初态与供液修正、0–24 h 沉淀前诊断及热处理配对。**状态：已建立可追溯诊断基准，尚未完成实验验证或机制识别。**','',
           '## 已实施的修改','',
           '- 保留原 DuMuˣ 2pncmin 框架；采用液相压力主变量 p0s1，初始状态为仅液相、S_l=1。没有改成专门的 1p 模型，也没有强制饱和度永远等于 1。',
           '- 储液面相对砂体底部 20 mm；两种砂从同一液相静水压场初始化，关闭蒸发预平衡 7200 s。初始/供液盐度由 EOS 反求为溶液 1 mol/L，溶解空气按储液状态平衡。',
           '- 问题类直接共享求解器时钟，Newton 缩步时自动使用当前尝试的步长；强迫按当前区间精确积分。接受步单独记录，检查点排序去重并防止零时间步。',
           '- 底部采用压力驱动、分布式理想储液边界；水、盐、空气按流向采用供体组成。以液压势而非裸压力判定供体，重力只计一次。实现了等效阻力和精确入口交叠选项，但本轮未把未知滤板阻力设成测量值。',
           '- 顶部给定水组分的质量通量，转换为水的摩尔通量；补回空气出口，避免将空气封闭造成的人为储留混入物理解读。相同单位面积水通量是本轮假设。',
           '- K 更新为独立属性表值；保留 phi=0.40/0.36、D0=1.54e-9 m²/s 和现有扩散本构，未用盐剖面拟合材料参数。',
           '- 每个接受步检查组分、相态、密度、孔隙率和有限值；记录全域水/总盐、粗细侧总盐和求解器实际界面平流/扩散通量。固体盐纳入总盐预算；出现沉淀即停止当前沉淀前任务。',
           '- 固定随机种子 1，在预平衡结束后施加小扰动；通过全域组成偏移保持总盐量，微小水/空气及分区盐量冲量另行记账。','',
           '## 本轮条件与不能省略的假设','',
           '计算仍为 50×40 mm 二维平面域、32×40 分级网格。二维库存和通量以每米出平面厚度计；不能直接与圆柱实验的克数比较。',
           '强迫来自 Ali 本次异质实验的原始称重质量差，按直径 50 mm 面积及供液盐质量分数扣除盐，采用零样品水储量变化近似。0–1 h 缺测，沿用第一个 1–2 h 区间。24 h 水量代理积分为 4.0423 kg/m²，约 4.0423 mm 水当量；它是给定的诊断输入，不是模型独立预测的蒸发。',
           '按用户最新意见，本轮不追求滤板和管路逐个零件还原，也不把缺少型号或实测渗透率作为推进前提。滤板未显式加入；分布式储液边界是理想参照。另用名义 2 mm 中央窄口作简化敏感性，并非声称真实装置入口已知。',
           '主比较按 x_NaCl × rho_molar / 1000 转为溶液 mol/L；用单元与 1 mm 深度带的精确面积交叠平均。实验使用 Ali 归档浓度剖面。本轮图按名义 0/8/24 h 瞬时快照比较，**没有应用 MRI 32 分钟扫描平均**，因此不与前轮扫描平均指标混称。图中 0–3、37–40 mm 单独遮示，主要指标用 3–37 mm。','',
           '## 数值验收记录','',
           '| 运行 | 接受步数 | 最低 S_l | 最大水相对残差 | 最大盐相对残差 | 状态 |',
           '|---|---:|---:|---:|---:|---|']
    for name,a in summary.items():
        if a.get('accepted_steps',0)==0:
            lines.append(f'| {name} | 0 | — | — | — | 保留的中止记录，不用于物理比较 |');continue
        lines.append(f"| {name} | {a['accepted_steps']} | {a['S_min']:.7f} | {a['water_relative_residual']:.3g} | {a['salt_relative_residual']:.3g} | {a['run_status']['status']} |")
    lines+=['','相对残差以各自初始库存为分母。全域与粗/细侧的绝对残差、逐步原始预算见 [verification.json](results/verification.json) 与各运行 budget.csv；未单独输出所有外边界的累计绝对通量，不能把净通量当总吞吐量。',
            '区间积分、跨区间积分加性、覆盖越界拒绝和正/反向组分供体测试通过。T0_retry 实际触发 300→150→75→37.5 s 缩步，随后完成；失败尝试未写成接受步。',
            '非等温原 1e-10 绝对残差阈值测试在首步残差约 1.3e-9、相对位移约 1e-15 处停滞，已中止并保留。单独命名的 NI_abs1e8 输入采用 1e-8 绝对阈值、仍要求 1e-9 位移阈值；不把它与原配置混为同一运行。能量守恒的独立预算尚未加入。']
    if sensitivity:
        maxchange=max(abs(r['relative_mean_change']) for r in sensitivity['profiles'])
        lines+=['',f'0–8 h 最大时间步 300→150 s 的配对中，各侧四个深度带均值的最大相对变化为 {maxchange:.3%}。完整指标见 [time_step_sensitivity.json](results/time_step_sensitivity.json)。这只是同网格、同种子的早期时间步敏感性；没有证明网格独立，也没有证明 24 h 全窗时间收敛。']
    lines+=['','## 24 h 与实验的比较','',
            '| 模型 | 砂 | 3–10 mm 均值偏差 | 20–37 mm 均值偏差 | 3–37 mm RMSE (mol/L) |',
            '|---|---|---:|---:|---:|']
    for label in models:
        for side in SIDES:
            rr={r['band']:r for r in metrics if r['model']==label and r['side']==side and r['time_h']==24}
            if not rr:continue
            lines.append(f"| {label} | {side} | {rr['upper_3_10']['relative_mean_bias']:+.1%} | {rr['deep_20_37']['relative_mean_bias']:+.1%} | {rr['core_3_37']['rmse_mol_L']:.4f} |")
    lines+=['','[新旧模型与实验的剖面对比](results/01_profiles.png)；[饱和度、浓度、界面通量与守恒检查](results/02_diagnostics.png)。CSV 同时保留绝对值偏差和相对 0 h 的浓度增量。',
            '等温修订使 W3 上部偏高从约 43% 降至约 34%；F36 上部仍偏高约 34%。内部均值接近不能抵消上部过高、深部偏低和初始剖面不匹配。改动涉及初态、供液、强迫、物性小更新及温度，旧新比较不能识别其中某一项的独立因果贡献。','',
            '## 目前可以怎样解释界面交换','',
            '等温 24 h 界面累计平流盐量为 +0.113106 mol/m，累计扩散为 −0.013006 mol/m，合计约 +0.100100 mol/m；正号定义为 F36→W3。两侧盐预算对该接口通量闭合，因此这次是直接面通量诊断。',
            '这支持本理想化条件下“平流净向细侧供盐、扩散有反向净贡献”的描述。它不证明各个深度通量都同向，不证明实验存在完整闭合循环，也不能把该数值量当作实验测得的交换。尚未输出按深度分解的界面通量，且真实滤板可能改变路径。','',
            '## 结果的使用边界与下一阶段','',
            '1. 原始 hete_test、同步快照和原远程研究模块均保留；本轮所有计算在独立 model_revisions/20261028 目录。编译、输入、强迫、二进制、源文件哈希和依赖审计均有记录。开发失败和容差不同的运行不混入主比较。',
            '2. 目前数值有效性与守恒检查通过；物理匹配仍未通过。不能据此声称模型已验证，也不能据此生产论文 regime map。',
            '3. 下一门槛是网格、扰动场及 24 h 时间步收敛，并逐项比较强迫历史、水头、供液路径和扩散。网格加密时需保留物理加密位置；随机场应在不同网格间映射，不能只复用随机种子就宣称同一扰动。',
            '4. 优先用等效供液和少量边界敏感性检验主结论；仅当结论对合理简化敏感时再细化滤板/入口。识别砂体接触与底部旁路仍要明确边界含义，不要求还原每个装置零件。当前浓度偏差和离散检验尚不足以启动大规模机制扫描或 174 h 盐壳预测。',
            '5. MRI 原始 ROI、扫描起止时间、归档剖面人工处理与初始场不均匀性需要进一步核实；不能为消除上部偏差任意调参。','',
            '## 文件与复现入口','',
            '- [源文件](source/appl/main.cc)、[边界与诊断](source/appl/problem.hh)、[区间积分辅助](source/appl/revision_support.hh)。',
            '- build_remote.py 使用原已固定依赖栈直接编译，分别传参数 0/1；run_case.py 按独立运行名创建目录并保存元数据，已有运行名拒绝覆盖。',
            '- analyze_revision.py 从本地归档 VTU、budget.csv 和原始实验派生表重新生成本报告、PNG/PDF、CSV 与验证 JSON。',
            '- [执行与失败记录](EXECUTION_NOTES.md)、[依赖审计](dependency_manifest.json)、每次运行的 build_manifest.json / run_manifest.json / effective_parameters.txt。','']
    if comparisons:
        lines+=['## 简化供液边界与温度配对结果','']
        for name,compare in comparisons.items():
            maximum=max(abs(r['relative_change_from_reference']) for r in compare['profiles'])
            lines.append(f"- {name}: 24 h 各侧四个深度带均值的最大相对变化为 {maximum:.2%}，见 [配对指标](results/{name}_sensitivity.json)。")
            if name=='supply':
                lines.append('  该对照检验分布供液与中央窄口两个理想化条件，不能给未知滤板反演出唯一参数。见 [供液方式对照图](results/03_supply_sensitivity.png)。')
                adv=compare['cumulative_interface_adv_mol'];diff=compare['cumulative_interface_diff_mol']
                relative_net=(adv['candidate']+diff['candidate'])/(adv['reference']+diff['reference'])-1
                lines.append(f'  中央窄口使 F36 上部均值降低约 7.4%，W3 上部仅变化约 0.13%；但累计净界面交换量变化 {relative_net:+.1%}。所以供液简化对主要 W3 上部偏差影响小，却不能视为对机制通量完全无影响。')
            else:
                lines.append(f"  非等温 24 h 温度范围为 {compare['final_T_min_K']:.2f}–{compare['final_T_max_K']:.2f} K；热边界未由样品测温约束，结论只对当前假设成立。")
        lines.append('')
    lines+=['## 对下一轮物理修改的判断','',
            '当前热处理与简化供液变化都未消除 W3 上部约三成的偏高。下一轮优先在固定整体水量下检验粗/细侧局部蒸发分配，并检查上部富集向深部的输运及 MRI 观测对应；这些是待检验解释，不能直接把偏差归因为某一项。',
            '无需为此先追究滤板型号。继续保留等效边界、明确敏感性即可；涉及界面通量幅值的机制结论则必须带上供液方式的不确定度。','']
    (ROOT/'IMPLEMENTATION_REPORT.md').write_text('\n'.join(lines),encoding='utf-8')

if __name__=='__main__':main()
