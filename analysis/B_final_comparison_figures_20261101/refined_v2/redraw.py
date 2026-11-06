"""Visual revision of the frozen four-figure comparison package; no solver work."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
from matplotlib.lines import Line2D
from matplotlib.colors import ListedColormap

HERE=Path(__file__).resolve().parent;PARENT=HERE.parent
SD=PARENT/'SOURCE_DATA'; OUT=HERE/'SOURCE_DATA';OUT.mkdir(exist_ok=True)
SKILL=Path.home()/'.agents/skills/nature-figure/scripts'
sys.path.insert(0,str(SKILL))
from audit_panel_alignment import require_matplotlib_panel_alignment
oldmanifest=json.loads((PARENT/'MANIFEST.json').read_text())
sources={};exports=[]
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(2**20),b''):h.update(block)
    return h.hexdigest()
def load(name):
    p=SD/(name+'.csv');key='SOURCE_DATA/'+p.name
    # The parent manifest was serialized with native Windows path separators.
    expected=oldmanifest['output_sha256'].get(key,oldmanifest['output_sha256'].get(key.replace('/','\\')))
    assert expected and sha(p)==expected, name
    sources[key]=expected
    (OUT/p.name).write_bytes(p.read_bytes())
    return pd.read_csv(p)

effects=load('effects_all_145_frames');primary=load('primary_effects_24h')
supply=load('whole_side_supply_and_interface_24h');depth=load('depth_effect_finite_ranges')
gates=load('selected_gate_ratios');plume=load('plume_endpoints_onsets')
local=load('local_connection_differences_24h');localts=load('local_connection_differences_145_frames')
interaction=load('local_interaction_contributions_24h');load('all_registered_numeric_checks')
SC=['medium','coarse','fine','dt150','seed2','seed3','amplitude3e-6','amplitude3e-5','P1','P2']
LABEL=['Reference','Coarse mesh','Fine mesh','Time step /2','Phase 2','Phase 3','Amplitude ×0.3','Amplitude ×3','Ks P1','Ks P2']
NUM=SC[:8];PAR=['medium','P1','P2'];FULL=['medium','fine','dt150'];PERT=['medium','seed2','seed3','amplitude3e-6','amplitude3e-5']
INK='#233746';BLUE='#2477A6';TEAL='#168B80';RUST='#C07A32';PURPLE='#9B718E';GREY='#93A3AD'
scenario_color={'medium':INK,'fine':BLUE,'dt150':RUST,'P1':TEAL,'P2':PURPLE}
plt.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','DejaVu Sans'],
    'font.size':8.5,'axes.labelsize':9,'axes.titlesize':9,'xtick.labelsize':8,'ytick.labelsize':8,
    'legend.fontsize':7.5,'axes.linewidth':.65,'axes.spines.top':False,'axes.spines.right':False,
    'xtick.major.size':3,'ytick.major.size':3,'xtick.major.width':.6,'ytick.major.width':.6,
    'text.color':INK,'axes.labelcolor':INK,'axes.edgecolor':'#5B6870','xtick.color':'#5B6870','ytick.color':'#5B6870',
    'legend.frameon':False,'legend.handlelength':1.8,'legend.labelspacing':.35,
    'lines.linewidth':1.35,'lines.markersize':4,'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none',
    'svg.hashsalt':'wrr-comparison-v2','figure.facecolor':'white','axes.facecolor':'white','savefig.facecolor':'white',
    'axes.unicode_minus':True,'path.simplify':False})

def figgrid(height=6.15):
    f,axs=plt.subplots(2,2,figsize=(183/25.4,height))
    f.subplots_adjust(left=.165,right=.98,bottom=.145,top=.92,wspace=.55,hspace=.50)
    for a,letter in zip(axs.flat,'abcd'):
        a.set_label(letter)
        a.text(-.10,1.075,letter,transform=a.transAxes,fontsize=11,fontweight='bold',ha='left',va='bottom')
    return f,axs
def title(a,t):a.set_title(t,loc='left',pad=13,fontweight='normal')
def note(f,t):f.text(.165,.035,t,fontsize=7.2,va='bottom',linespacing=1.4,color='#52616B')
def zero(a,axis='y'):
    (a.axhline if axis=='y' else a.axvline)(0,color='#A9B1B7',lw=.7,zorder=0)
def timex(a):a.set(xlim=(0,24),xticks=[0,6,12,18,24],xlabel='Evaporation time (h)');zero(a)
def rows(a,labels,extra=0):
    a.set_yticks(range(len(labels)),labels)
    a.set_ylim(len(labels)-.5,-.5-extra)
    a.tick_params(axis='y',length=0,pad=6)
def curve(s,b=1):return effects[(effects.scenario==s)&(effects.B==b)&(effects.side=='W3')&(effects.band=='0_3')].sort_values('time_h')
T=curve('medium').time_h.to_numpy()
def vals(s,b=1):return curve(s,b).connection_mg.to_numpy()
def endpoint(s,b=1):return vals(s,b)[-1]

def save(f,name):
    f.canvas.draw()
    require_matplotlib_panel_alignment(f,json_out=HERE/(name+'.alignment.json'),
        overlay_svg=HERE/(name+'.alignment.svg'),tolerance_pt=1.5,gutter_tolerance_pt=1.5,strict=True)
    f.savefig(HERE/(name+'.pdf'))
    f.savefig(HERE/(name+'.svg'))
    f.savefig(HERE/(name+'.png'),dpi=600)
    f.savefig(HERE/(name+'.tiff'),dpi=600,pil_kwargs={'compression':'tiff_lzw'})
    # Derive a screen thumbnail from the actual 600-dpi deliverable.
    with Image.open(HERE/(name+'.png')) as im:
        im.resize((round(im.width*.3),round(im.height*.3)),Image.Resampling.LANCZOS).save(HERE/(name+'_preview.png'))
    exports.append(name);plt.close(f)

# 1 — Resolved surface response; point-axis zoom explicitly disclosed.
f,ax=figgrid()
a=ax[0,0];v=np.array([vals(s) for s in NUM])
a.fill_between(T,v.min(axis=0),v.max(axis=0),color='#C9E2F0',label='Numerics / perturb.',zorder=1)
a.plot(T,vals('medium'),color=INK,lw=1.6,label='Reference',zorder=3)
for s,ls in [('P1','--'),('P2',':')]:a.plot(T,vals(s),color=scenario_color[s],ls=ls,label=f'Ks {s}')
timex(a);a.set_ylim(-.25,6.2);a.set_ylabel('Δconn(B1) (mg)');title(a,'Surface connection effect')
a.legend(loc='upper left',fontsize=7.2,borderaxespad=.2)
a=ax[0,1]
for lo,hi in [(3.5,7.5)]:a.axhspan(lo,hi,color='#F2F5F7',zorder=0)
for i,s in enumerate(SC):
    a.plot(endpoint(s),i,marker='D' if s in PAR[1:] else 'o',ls='none',ms=4.5,
        color=scenario_color.get(s,GREY),mec='white',mew=.4,zorder=3)
    if s in ['medium','P1','P2']:a.annotate(f'{endpoint(s):.3f}',(endpoint(s),i),xytext=(5,0),textcoords='offset points',va='center',fontsize=7.6)
a.axvline(endpoint('medium'),color='#BCC4CA',ls=':',lw=.8)
rows(a,LABEL);a.set_xlim(3.70,5.12);a.set_xticks([3.8,4.2,4.6,5.0]);a.set_xlabel('24 h effect (mg; zoomed scale)');title(a,'All tested pairs remain positive')
a=ax[1,0]
for s,ls,m in [('medium','-','o'),('fine','--','s'),('dt150',':','^')]:
    a.plot(T,vals(s,1)-vals(s,0),color=scenario_color[s],ls=ls,marker=m,ms=3.5,markevery=24,
        label={'medium':'Reference','fine':'Fine mesh','dt150':'Time step /2'}[s])
timex(a);a.set_ylim(-4.7,1.3);a.set_ylabel('Δint (mg)');title(a,'Buoyancy interaction over time');a.legend(loc='lower left')
a=ax[1,1]
for j,s in enumerate(FULL):
    values=[endpoint(s,1),endpoint(s,0),endpoint(s,1)-endpoint(s,0)]
    a.plot(values,np.arange(3)+(j-1)*.14,marker=['o','s','^'][j],ls='none',color=scenario_color[s],ms=4.5)
rows(a,['Δconn(B1)','Δconn(B0)','Δint']);zero(a,'x');a.set_xlim(-5.2,10);a.set_xticks([-4,0,4,8]);a.set_xlabel('24 h effect (mg)');title(a,'Endpoint contrasts')
note(f,'W3 upper 3 mm · RH = 0 · 24 h. Ranges span tested scenarios, not confidence intervals.\nΔconn = connected − blocked; Δint = Δconn(B1) − Δconn(B0). B1/B0: buoyancy on/off.')
save(f,'Fig05_surface_response_v2')

# 2 — Horizontal paired comparisons and compact contribution ranges.
f,ax=figgrid(6.4);sp=supply.set_index('scenario').loc[SC];y=np.arange(10)
a=ax[0,0]
for i,s in enumerate(SC):
    r=sp.loc[s];a.plot([r.W3_bottom_salt_C1_g*1000,r.W3_bottom_salt_C0_g*1000],[i,i],color='#DDE3E7',lw=.9,zorder=1)
a.plot(sp.W3_bottom_salt_C1_g*1000,y,'o',color=BLUE,ms=4,label='Connected')
a.plot(sp.W3_bottom_salt_C0_g*1000,y,'s',color=RUST,mfc='white',ms=4,label='Blocked')
rows(a,LABEL,extra=1.15);a.set_xlim(0,270);a.set_xticks([0,100,200]);a.set_xlabel('Bottom salt input (mg)');title(a,'W3 bottom supply is rerouted');a.legend(loc='upper center',ncol=2,fontsize=7)
a=ax[0,1]
for v,c,m,label in [(sp.interface_adv_C1_g*1000,TEAL,'o','Adv.'),(sp.interface_diff_C1_g*1000,PURPLE,'s','Diff.'),((sp.interface_adv_C1_g+sp.interface_diff_C1_g)*1000,INK,'D','Net')]:a.plot(v,y,marker=m,ls='none',color=c,ms=3.7,label=label)
rows(a,LABEL,extra=1.15);zero(a,'x');a.set_xlim(-65,330);a.set_xticks([-50,0,150,300]);a.set_xlabel('F36 → W3 salt (mg)');title(a,'Opposing lateral contributions');a.legend(loc='upper center',ncol=3,fontsize=7,columnspacing=.7,handletextpad=.3)
sp['bottom_diff']=(sp.W3_bottom_salt_C1_g-sp.W3_bottom_salt_C0_g)*1000
sp['lateral_net']=(sp.interface_adv_C1_g+sp.interface_diff_C1_g)*1000
sp['whole_change']=sp.W3_whole_side_connection_effect_g*1000
sp['surface_change']=[endpoint(s) for s in SC]
a=ax[1,0];terms=['bottom_diff','lateral_net','whole_change','surface_change'];contrib=[]
for i,key in enumerate(terms):
    for ss,dy,c,m,label in [(NUM,-.11,BLUE,'o','Numerics*'),(PAR,.11,TEAL,'s','Ks corners')]:
        vv=sp.loc[ss,key];base=sp.loc['medium',key]
        a.errorbar(base,i+dy,xerr=[[base-vv.min()],[vv.max()-base]],fmt=m,ms=3.8,color=c,capsize=3,elinewidth=1.3,label=label if i==0 else None)
        contrib.append({'term':key,'group':label,'baseline_mg':base,'min_mg':vv.min(),'max_mg':vv.max(),'members':';'.join(ss)})
rows(a,['Bottom input\ndifference','Lateral net\ninput','Whole-W3\nresponse','Upper-3-mm\nresponse'],extra=.65)
zero(a,'x');a.axhline(2.5,color='#DAE0E4',ls=':',lw=.7);a.set_xlim(-260,310);a.set_xticks([-200,0,200]);a.set_xlabel('Connected − blocked (mg)');title(a,'Whole-side budget compensation');a.legend(loc='upper center',ncol=2,fontsize=7)
a=ax[1,1]
for i,band in enumerate(['0_3','3_10','10_20','20_40']):
    for g,dy,c,m,lab in [('Numerical / perturbation',-.11,BLUE,'o','Numerics*'),('Ks corners + baseline',.11,TEAL,'s','Ks corners')]:
        r=depth[(depth.band_mm==band)&(depth.group==g)].iloc[0]
        a.errorbar(r.baseline_mg,i+dy,xerr=[[r.baseline_mg-r.min_mg],[r.max_mg-r.baseline_mg]],fmt=m,ms=3.8,color=c,capsize=3,elinewidth=1.3,label=lab if i==0 else None)
rows(a,['0–3 mm','3–10 mm','10–20 mm','20–40 mm'],extra=.65);a.set_xlim(0,22);a.set_xticks([0,5,10,15,20]);a.set_xlabel('W3 connection effect (mg)');title(a,'Added storage lies mainly deeper');a.legend(loc='upper center',ncol=2,fontsize=7)
pd.DataFrame(contrib).to_csv(OUT/'supply_range_encoding.csv',index=False)
note(f,'B1 · 24 h. All ten pairs (a,b); reference and finite ranges (c,d). *Includes mesh, time step and perturbations.\nThe upper-3-mm response is part of the whole-W3 response, not an additional budget term.')
save(f,'Fig04_supply_partition_v2')

# 3 — Directly readable local balance components, all variants retained.
f,ax=figgrid(6.3)
k2=['vertical_adv_mg','vertical_diff_mg','lateral_adv_direct_mg','lateral_diff_direct_mg','storage_change_mg']
k3=['vertical_adv_mg','vertical_diff_mg','lateral_net_inferred_mg','storage_change_mg']
labs2=['Vertical\nadvection','Vertical\ndiffusion','Lateral\nadvection','Lateral\ndiffusion','Storage\nchange']
labs3=['Vertical\nadvection','Vertical\ndiffusion','Lateral net*','Storage\nchange']
mode={k2[0]:BLUE,k2[1]:PURPLE,k2[2]:TEAL,k2[3]:RUST,k2[4]:INK,k3[2]:TEAL}
range_rows=[]
for a,d,ks,labs in [(ax[0,0],2,k2,labs2),(ax[0,1],3,k3,labs3)]:
    r=local[(local.depth_mm==d)&(local.B==1)].set_index('scenario').loc[SC]
    for i,k in enumerate(ks):
        vv=r[k];base=r.loc['medium',k]
        a.plot([vv.min(),vv.max()],[i,i],color='#89969E',lw=2,zorder=1)
        a.plot(vv,np.full(len(vv),i),ls='none',marker='o',color=mode[k],ms=2.5,alpha=.45,zorder=2)
        a.plot(base,i,'D',color=mode[k],ms=5,zorder=3)
        if k=='storage_change_mg':a.annotate(f'{base:+.2f}',(base,i),xytext=(7,0),textcoords='offset points',va='center',fontsize=8)
        range_rows.append({'depth_mm':d,'term':k,'baseline_mg':base,'min_mg':vv.min(),'max_mg':vv.max(),'n':len(vv)})
    rows(a,labs);zero(a,'x');a.set_xlim(-125,125);a.set_xticks([-100,0,100]);a.set_xlabel('24 h connection contribution (mg)')
    title(a,'0–2 mm: direct flux budget' if d==2 else '0–3 mm: local compensation')
a=ax[1,0]
for j,s in enumerate(FULL):
    rr=interaction[interaction.scenario==s].set_index('term')
    a.plot(rr.loc[k3,'interaction_contribution_mg'],np.arange(4)+(j-1)*.13,ls='none',marker=['o','s','^'][j],color=scenario_color[s],ms=4,
        label={'medium':'Reference','fine':'Fine','dt150':'dt /2'}[s])
rows(a,labs3,extra=1);zero(a,'x');a.set_xlim(-11,11);a.set_xticks([-10,-5,0,5,10]);a.set_xlabel('Interaction contribution (mg)');title(a,'Buoyancy changes several terms');a.legend(loc='upper center',ncol=3,fontsize=7,handletextpad=.3,columnspacing=.7)
a=ax[1,1]
for s,ls in [('medium','-'),('fine','--')]:
    r=localts[(localts.scenario==s)&(localts.B==1)&(localts.depth_mm==3)]
    for v,col in [(r.lateral_net_inferred_mg,TEAL),(r.vertical_adv_mg+r.vertical_diff_mg,BLUE),(r.storage_change_mg,INK)]:a.plot(r.time_h,v,color=col,ls=ls,lw=1.5)
timex(a);a.set_ylim(-115,115);a.set_ylabel('Connection contribution (mg)');title(a,'Compensation persists in time')
lg=a.legend(handles=[Line2D([],[],color=TEAL,label='Lateral net*'),Line2D([],[],color=BLUE,label='Vertical net'),Line2D([],[],color=INK,label='Storage')],loc='upper left',fontsize=7)
a.add_artist(lg)
a.legend(handles=[Line2D([],[],color='#6A7881',label='Reference'),Line2D([],[],color='#6A7881',ls='--',label='Fine mesh')],loc='lower left',fontsize=7)
pd.DataFrame(range_rows).to_csv(OUT/'local_range_encoding.csv',index=False)
note(f,'a,b: ten B1 pairs; diamonds mark the reference, grey spans mark the tested range.\n*0–3 mm lateral net is inferred from storage minus vertical input; it is not an independent flux check.')
save(f,'FigS_local_compensation_v2')

# 4 — Exact tolerance ratios and equally sized panels replace a narrow scatter.
f,ax=figgrid(6.4)
a=ax[0,0];labels=['W3 surface\nC1B1','W3 surface\nC0B1','F36 surface\nC1B1','F36 surface\nC0B1','Interface net\nC1B1','F36 descent\nC1B1','W3 vertical\nC1B1','W3 vertical\nC1B0']
unique=gates[['arm','metric']].drop_duplicates();matrix=[]
for rr in unique.itertuples():
    matrix.append([gates[(gates.arm==rr.arm)&(gates.metric==rr.metric)&(gates.comparison==c)].difference_over_tolerance.iloc[0] for c in ['fine','dt150']])
matrix=np.array(matrix);assert matrix.shape==(8,2)
a.pcolormesh(np.arange(3)-.5,np.arange(9)-.5,(matrix>1).astype(int),cmap=ListedColormap(['#EAF1F5','#F4DDCA']),vmin=0,vmax=1,edgecolors='white',linewidth=3)
for i in range(8):
    for j in range(2):
        label='<0.01' if 0<matrix[i,j]<.005 else f'{matrix[i,j]:.2f}'
        a.text(j,i,label,ha='center',va='center',fontsize=8.3,color='#995C28' if matrix[i,j]>1 else '#416176',fontweight='bold' if matrix[i,j]>1 else 'normal')
a.set_yticks(range(8),labels,fontsize=7.3);a.set_xticks([0,1],['Medium → fine','300 → 150 s'],fontsize=7.4)
a.set_ylim(7.5,-.5);a.tick_params(length=0);a.spines[['left','bottom']].set_visible(False)
a.set_xlabel('Change / tolerance (>1 fails)');title(a,'Metric-specific verification')
a=ax[0,1]
for c,col,m,ls in [(1,BLUE,'o','-'),(0,RUST,'s','--')]:
    vv=[100*plume[(plume.scenario==s)&(plume.C==c)].F36_core_down_volume_fraction.iloc[0] for s in ['coarse','medium','fine']]
    a.plot(range(3),vv,color=col,marker=m,ls=ls,ms=4.5,label='Connected' if c else 'Blocked')
a.set_xticks(range(3),['Coarse','Medium','Fine']);a.set_ylim(0,27);a.set_yticks([0,10,20]);a.set_ylabel('Descending core volume (%)');title(a,'Plume geometry is non-monotone');a.legend(loc='lower left',fontsize=7.4)
for a,colkey,tit,xlab,factor,xlim in [(ax[1,0],'F36_core_down_volume_fraction','Perturbation changes plume geometry','Descending core volume (%)',100,(0,45)),(ax[1,1],'core_onset_h','Diagnostic onset is sensitive','Persistent core onset (h)',1,(8,18))]:
    for i,s in enumerate(PERT):
        q=plume[plume.scenario==s].set_index('C');v1=q.loc[1,colkey]*factor;v0=q.loc[0,colkey]*factor
        a.plot([v1,v0],[i,i],color='#DDE3E7',lw=1)
        a.plot(v1,i,'o',color=BLUE,ms=4.5);a.plot(v0,i,'s',color=RUST,mfc='white',ms=4.5)
    rows(a,[LABEL[SC.index(s)] for s in PERT]);a.set_xlim(xlim);a.set_xlabel(xlab);title(a,tit)
note(f,'a: tolerance ratios, rounded; amber cells fail. b–d: B1, core-descent criterion (Darcy speed >1e-8 m/s).\nSurface tolerance 2%; flux/volume tolerance 5%. Onset is a diagnostic, not an instability threshold.')
save(f,'FigS_numerical_limits_v2')

(HERE/'MANIFEST.json').write_text(json.dumps({'sources_sha256':sources,'parent_manifest_sha256':sha(PARENT/'MANIFEST.json'),
    'script_sha256':sha(Path(__file__)),'figures':exports,'data_revision':'unchanged frozen final A+B evidence',
    'design':'183 mm compact 2x2 quantitative grids; explicit zoom in primary endpoint dotplot; finite ranges with members preserved',
    'output_sha256':{str(p.relative_to(HERE)):sha(p) for p in HERE.rglob('*') if p.is_file() and p.name!='MANIFEST.json' and '__pycache__' not in str(p)}},indent=2),encoding='utf-8')
print('Rebuilt four figures from verified frozen tables:',exports)
