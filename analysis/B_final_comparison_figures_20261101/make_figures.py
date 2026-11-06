"""Final A+B comparison figures. Offline postprocessing; no solver invocation.

Uses 26 accepted 24-h cases, separates finite sensitivity ranges from CIs,
and preserves failed numerical checks. Local 0-3-mm lateral flux is inferred.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import sys
import zipfile
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
B=ROOT/'model_revisions/20261030_verification_v11'
A=ROOT/'model_revisions/20261030_causal_v10'
JOINT=ROOT/'analysis/opus_campaign_joint_20261101'
OLD=ROOT/'analysis/opus_comparison_figures_20261031'
SD=HERE/'SOURCE_DATA'; SD.mkdir(exist_ok=True)
PIN=SD/'source_pins.json'
parser=argparse.ArgumentParser(); parser.add_argument('--pin',action='store_true'); args=parser.parse_args()
pins=json.loads(PIN.read_text()) if PIN.exists() else {}
sources={}; checks={}; outputs=[]

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for x in iter(lambda:f.read(2**20),b''):h.update(x)
    return h.hexdigest()

def source(p):
    p=Path(p); key=str(p.relative_to(ROOT)); digest=sha(p)
    if not args.pin:
        assert pins.get(key)==digest, f'Input changed or not pinned: {key}'
    sources[key]=digest
    return p

def readj(p): return json.loads(source(p).read_text(encoding='utf-8'))
def readcsv(p): return pd.read_csv(source(p))
def table(df,name): df.to_csv(SD/f'{name}.csv',index=False,float_format='%.15g')

# Verify the final coordinator evidence chain; old B STATUS/report are not final.
manifest=readj(JOINT/'evidence_manifest.json')
for record in manifest['sources']:
    assert sha(source(Path(record['path'])))==record['sha256'],record['path']
checks['verified_coordinator_source_count']=len(manifest['sources'])
assert sha(source(JOINT/'JOINT_ASSESSMENT_ZH.md'))==manifest['report_sha256']
accept=readcsv(JOINT/'acceptance.csv')
assert len(accept)==26 and (accept.final_h==24).all() and (accept.frames==145).all()
assert (accept.max_native_relative_budget_error<1e-6).all() and accept.archive_verified.all()
table(accept,'accepted_cases')
numeric=readcsv(JOINT/'numeric_comparisons.csv')
table(numeric,'all_registered_numeric_checks')
joint_effects=readcsv(JOINT/'effects_timeseries.csv')
supply=readcsv(JOINT/'supply_redistribution.csv')
readj(JOINT/'independent_accepted_flux_audit.json')
source(B/'DESIGN.md')
source(B/'report_parts/03_parameters.md')
with zipfile.ZipFile(source(ROOT/'WRR_Outline.docx')) as z:
    tree=ET.fromstring(z.read('word/document.xml'))
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
outline=[''.join(p.itertext()) for p in tree.findall('.//w:p',ns)]
(SD/'outline_text.txt').write_text('\n'.join(outline),encoding='utf-8')

spec=importlib.util.spec_from_file_location('oldfig',source(OLD/'make_figures.py'))
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old);old.Style.apply()
plt.rcParams.update({'font.size':7.5,'axes.titlesize':8,'axes.labelsize':7.5,'xtick.labelsize':6.5,'ytick.labelsize':6.5,'legend.fontsize':6.2})
SC=['medium','coarse','fine','dt150','seed2','seed3','amplitude3e-6','amplitude3e-5','P1','P2']
LAB=['Baseline','Coarse','Fine','dt 150 s','Phase 2','Phase 3','Amp ×0.3','Amp ×3','Ks P1','Ks P2']
SHORT=['Ref.','Coarse','Fine','dt150','S2','S3','A0.3','A3','P1','P2']
PREFIX={'coarse':'G_coarse','fine':'G_fine','dt150':'T150','seed2':'S2','seed3':'S3','amplitude3e-6':'A3e-6','amplitude3e-5':'A3e-5','P1':'P1','P2':'P2'}
ALLB=['medium','fine','dt150'];NUM=SC[:8];PAR=['medium','P1','P2'];PERT=['medium','seed2','seed3','amplitude3e-6','amplitude3e-5']
M=58443.0
colors={'medium':'#222222','fine':'#0072B2','dt150':'#D55E00','P1':'#009E73','P2':'#CC79A7'}
modecolors=['#0072B2','#CC79A7','#009E73','#D55E00','#222222']
frames={};summaries={};budgets=[];effects=[];ends=[];plumes=[]

def case_name(s,c,b): return f'A_C{c}B{b}_24h' if s=='medium' else f'v11_{PREFIX[s]}_C{c}B{b}'

def load_local_budget(s,c,b,name):
    run=A/'archive/v10c'/f'C{c}B{b}_24h' if s=='medium' else B/'runs_archive'/name
    if s=='medium':
        provenance=readj(A/'results/v10c'/f'C{c}B{b}_24h'/'extraction.json')['inputs_sha256']
    else:
        provenance=readj(run/'ARCHIVE_MANIFEST.json')['sha256']
    for fname in ['causal_budget.csv','vertical_salt_flux.csv','seed_event.json']:
        assert sha(source(run/fname))==provenance[fname],(name,fname)
    led=pd.read_csv(run/'causal_budget.csv');vf=pd.read_csv(run/'vertical_salt_flux.csv')
    sw=readj(run/'causal_switches.json');seed=json.loads((run/'seed_event.json').read_text())
    led=led[led.time_s>=7200].reset_index(drop=True);vf=vf[vf.time_s>=7200].reset_index(drop=True)
    assert np.array_equal(led.time_s,vf.time_s) and led.time_s.iloc[-1]==93600
    assert np.allclose(np.diff(led.time_s),vf.dt_s.iloc[1:])
    assert np.max(np.abs(led.W3_top_salt_out_mol_s))==0
    step=vf.dt_s.to_numpy().copy();step[0]=0
    dep=np.sort(np.array(sw['horizontal_plane_depths_m'])*1000)
    out=[]
    for d in [2,3]:
        inv=led.W3_salt_mol_0_2mm.to_numpy().copy()
        if d==3: inv+=led.W3_salt_mol_2_3mm.to_numpy()
        inv[0]+=sum(seed['band_salt_impulses_mol'][1][:1 if d==2 else 2])
        inv*=M;dm=inv-inv[0]
        f=frames[s,c,b]
        matched=np.interp(f.time_h,(led.time_s-7200)/3600,inv)
        err=float(np.max(np.abs(matched-f[f'W3_salt_g_0_{d}mm']*1000)))
        assert err<1e-7,(name,d,err)
        k=np.searchsorted(dep,d);du,dl=dep[k-1:k+1];w=(d-du)/(dl-du)
        vertical={}
        for mode in ['adv','diff']:
            q=(1-w)*vf[f'W3_{mode}_down_net_mol_s_d{round(du*1e4)}']+w*vf[f'W3_{mode}_down_net_mol_s_d{round(dl*1e4)}']
            vertical[mode]=-np.cumsum(q.to_numpy()*step)*M
        lat={}
        for mode in ['adv','diff']:
            col=led[f'if_{mode}_salt_0_2mm_cum_net_mol'].to_numpy()
            lat[mode]=(col-col[0])*M if d==2 else np.full(len(led),np.nan)
        inferred=dm-vertical['adv']-vertical['diff']
        residual=inferred-lat['adv']-lat['diff']
        if d==2:
            checks[name+'_0_2_closure_max_mg']=float(np.max(np.abs(residual)))
            assert np.max(np.abs(residual))<1e-6
        if c==0: assert np.max(np.abs(inferred))<1e-6
        out.append(pd.DataFrame({'scenario':s,'C':c,'B':b,'depth_mm':d,'time_h':(led.time_s-7200)/3600,
            'inventory_mg':inv,'storage_change_mg':dm,'vertical_adv_mg':vertical['adv'],'vertical_diff_mg':vertical['diff'],
            'lateral_adv_direct_mg':lat['adv'],'lateral_diff_direct_mg':lat['diff'],
            'lateral_net_inferred_mg':inferred,'independent_residual_mg':residual,'upper_face_mm':du,'lower_face_mm':dl,'lower_face_weight':w}))
    return pd.concat(out,ignore_index=True)

for s in SC:
    for b in ([1,0] if s in ALLB else [1]):
        for c in [1,0]:
            name=case_name(s,c,b);p=B/'remote_analysis'/name
            f=readcsv(p/'frame_series.csv');summ=readj(p/'summary.json')
            assert len(f)==145 and f.time_h.iloc[0]==0 and f.time_h.iloc[-1]==24
            for t in [0,2,4,8,12,24]:
                row=f[np.isclose(f.time_h,t)].iloc[0]
                for col in ['W3_salt_g_0_3mm','F36_salt_g_0_3mm','W3_C_mol_L_0_3mm']:
                    assert abs(row[col]-summ['at'][str(t)][col])<1e-12
            frames[s,c,b]=f;summaries[s,c,b]=summ
            r=f.iloc[-1];r0=f.iloc[0]
            ends.append({'scenario':s,'C':c,'B':b,'name':name,'W3_inventory_mg':r.W3_salt_g_0_3mm*1000,
                'W3_increase_mg':(r.W3_salt_g_0_3mm-r0.W3_salt_g_0_3mm)*1000,'W3_mean_C_M':r.W3_C_mol_L_0_3mm,
                'F36_increase_mg':(r.F36_salt_g_0_3mm-r0.F36_salt_g_0_3mm)*1000})
            if b==1:
                plumes.append({'scenario':s,'C':c,'F36_core_down_volume_fraction':r['F36_core_desc_vf_1.0e-08'],
                    'core_onset_h':summ['onset_h']['F36_core_thr1.0e-08'],'all_onset_h':summ['onset_h']['F36_all_thr1.0e-08']})
            budgets.append(load_local_budget(s,c,b,name))
        c1=frames[s,1,b];c0=frames[s,0,b]
        assert np.allclose(c1.time_h,c0.time_h)
        for side in ['F36','W3']:
            for band in ['0_2','0_3','3_10','10_20','20_40','0_40']:
                col=f'{side}_salt_g_{band}mm'
                effects.append(pd.DataFrame({'scenario':s,'B':b,'side':side,'band':band,'time_h':c1.time_h,
                    'connection_mg':(c1[col]-c0[col])*1000}))

eff=pd.concat(effects,ignore_index=True);end=pd.DataFrame(ends);plume=pd.DataFrame(plumes);local=pd.concat(budgets,ignore_index=True)
table(eff,'effects_all_145_frames');table(end,'case_endpoints');table(plume,'plume_endpoints_onsets');table(local,'local_budgets_accepted_steps')
for row in joint_effects.itertuples():
    for b,k in [(1,'E1_g'),(0,'E0_g')]:
        val=getattr(row,k)
        if pd.isna(val):continue
        ours=eff[(eff.scenario==row.scenario)&(eff.B==b)&(eff.side==row.side)&(eff.band==row.band_mm)&np.isclose(eff.time_h,row.time_h)].connection_mg
        assert len(ours)==1 and abs(ours.iloc[0]-val*1000)<1e-8
checks['joint_effects_match_all_available_rows']=True

def response(s,b=1,side='W3',band='0_3'):
    return eff[(eff.scenario==s)&(eff.B==b)&(eff.side==side)&(eff.band==band)].sort_values('time_h')
def endpoint(s,b=1,side='W3',band='0_3'):return response(s,b,side,band).connection_mg.iloc[-1]
def curve(s,b=1):return response(s,b).connection_mg.to_numpy()
time=response('medium').time_h.to_numpy()
primary=pd.DataFrame({'scenario':SC,'label':LAB,'B1_connection_mg':[endpoint(s) for s in SC]})
primary['B0_connection_mg']=[endpoint(s,0) if s in ALLB else np.nan for s in SC]
primary['interaction_mg']=primary.B1_connection_mg-primary.B0_connection_mg
primary['B1_change_from_baseline_mg']=primary.B1_connection_mg-endpoint('medium')
primary['B1_effect_pct_blocked_gain']=[100*endpoint(s)/end[(end.scenario==s)&(end.C==0)&(end.B==1)].W3_increase_mg.iloc[0] for s in SC]
primary['B1_mean_concentration_difference_M']=[end[(end.scenario==s)&(end.C==1)&(end.B==1)].W3_mean_C_M.iloc[0]-end[(end.scenario==s)&(end.C==0)&(end.B==1)].W3_mean_C_M.iloc[0] for s in SC]
table(primary,'primary_effects_24h')

# Local paired differences on a common frame clock; no temporal extrapolation.
localdiff=[]
for s in SC:
    for b in ([1,0] if s in ALLB else [1]):
        for d in [2,3]:
            pair=[]
            for c in [1,0]:
                r=local[(local.scenario==s)&(local.B==b)&(local.C==c)&(local.depth_mm==d)]
                pair.append({k:np.interp(time,r.time_h,r[k]) for k in ['storage_change_mg','vertical_adv_mg','vertical_diff_mg','lateral_adv_direct_mg','lateral_diff_direct_mg','lateral_net_inferred_mg']})
            localdiff.append(pd.DataFrame({'scenario':s,'B':b,'depth_mm':d,'time_h':time,**{k:pair[0][k]-pair[1][k] for k in pair[0]}}))
ld=pd.concat(localdiff,ignore_index=True);le=ld[ld.time_h==24].copy()
table(ld,'local_connection_differences_145_frames');table(le,'local_connection_differences_24h')
for s in SC:
    r=supply[supply.scenario==s].iloc[0]
    closure=r.W3_bottom_salt_C1_g-r.W3_bottom_salt_C0_g+r.interface_adv_C1_g+r.interface_diff_C1_g-r.W3_whole_side_connection_effect_g
    assert abs(closure)<1e-8
    assert abs(r.W3_whole_side_connection_effect_g*1000-endpoint(s,1,'W3','0_40'))<1e-6
table(supply,'whole_side_supply_and_interface_24h')

def newfig(height=6.8):
    fig,ax=plt.subplots(2,2,figsize=(7.6,height))
    fig.subplots_adjust(left=.11,right=.97,top=.93,bottom=.16,wspace=.38,hspace=.53)
    for a,l in zip(ax.flat,'abcd'):old.panel_label(a,l)
    return fig,ax

def foot(fig,lines):fig.text(.11,.025,lines,fontsize=6.2,va='bottom')
def timeaxis(ax):ax.set_xlim(0,24);ax.set_xticks([0,6,12,18,24]);ax.set_xlabel('Evaporation time (h)');ax.axhline(0,color='.5',lw=.6)
def scenarioaxis(ax,subset=SC):
    ax.set_xticks(range(len(subset)),[SHORT[SC.index(s)] for s in subset],rotation=45,ha='right',fontsize=6)
    ax.axhline(0,color='.5',lw=.6)

def save(fig,name):
    fig.canvas.draw();ren=fig.canvas.get_renderer();bad=[]
    unused_ticks=set()
    for a in fig.axes:
        for axis,limits in [(a.xaxis,a.get_xlim()),(a.yaxis,a.get_ylim())]:
            lo,hi=sorted(limits)
            for tick in axis.get_major_ticks()+axis.get_minor_ticks():
                if not lo-1e-9<=tick.get_loc()<=hi+1e-9:
                    unused_ticks.update([tick.label1,tick.label2])
    for t in fig.findobj(matplotlib.text.Text):
        if t.get_visible() and t.get_text() and t not in unused_ticks:
            bb=t.get_window_extent(ren)
            if bb.x0 < -1 or bb.y0 < -1 or bb.x1 > fig.bbox.width+1 or bb.y1 > fig.bbox.height+1:bad.append(t.get_text())
    assert not bad,(name,bad)
    for ax in fig.axes:
        for patch in ax.patches:
            if isinstance(patch,matplotlib.patches.Rectangle) and patch is not ax.patch:
                lo,hi=sorted([patch.get_y(),patch.get_y()+patch.get_height()])
                assert lo>=ax.get_ylim()[0]-1e-8 and hi<=ax.get_ylim()[1]+1e-8,(name,'clipped bar')
    for ext in ['pdf','svg','png','tiff']:
        kw={'pil_kwargs':{'compression':'tiff_lzw'}} if ext=='tiff' else {}
        fig.savefig(HERE/f'{name}.{ext}',dpi=600,**kw)
    fig.savefig(HERE/f'{name}_preview.png',dpi=150)
    outputs.append(name);plt.close(fig)

# Fig05: numerical/sensitivity ranges are shown separately, never as a CI.
fig,ax=newfig(7.1)
a=ax[0,0];v=np.array([curve(s) for s in NUM])
a.fill_between(time,v.min(axis=0),v.max(axis=0),color='#56B4E9',alpha=.5,label='8 numerical / perturbation scenarios')
a.plot(time,curve('medium'),color='#222222',label='Baseline',lw=1.3)
for s,ls in [('P1','--'),('P2',':')]:a.plot(time,curve(s),color=colors[s],ls=ls,label=f'Ks {s}')
timeaxis(a);a.set_ylim(-.25,6);a.set_ylabel('W3 0–3 mm Δconn(B1) (mg)');a.set_title('Connection effect across tested scenarios',loc='left');a.legend(loc='upper left',fontsize=5.8)
a=ax[0,1]
for i,(s,label) in enumerate(zip(SC,LAB)):
    val=endpoint(s);a.plot(val,i,'D' if s in ['P1','P2'] else 'o',color=colors.get(s,'#777777'),ms=4)
    a.text(5.15,i,f'{val:.3f}',ha='left',va='center',fontsize=6)
a.axvline(0,color='.5',lw=.6);a.axvline(endpoint('medium'),color='.5',lw=.6,ls=':')
a.set_yticks(range(10),LAB);a.invert_yaxis();a.set_xlim(-.15,6.25)
a.set_xlabel('24 h W3 connection effect (mg)');a.set_title('All 10 B1 pairs remain positive',loc='left')
a=ax[1,0]
for s,ls,m in [('medium','-','o'),('fine','--','s'),('dt150',':','^')]:
    a.plot(time,curve(s,1)-curve(s,0),color=colors[s],ls=ls,marker=m,markevery=24,ms=3,label=LAB[SC.index(s)])
timeaxis(a);a.set_ylabel('W3 interaction Δint (mg)');a.set_ylim(-4.7,1.3);a.set_title('Buoyancy interaction changes sign in time',loc='left');a.legend(loc='lower left')
a=ax[1,1]
for j,(s,m) in enumerate([('medium','o'),('fine','s'),('dt150','^')]):
    vals=[endpoint(s,1),endpoint(s,0),endpoint(s,1)-endpoint(s,0)]
    a.plot(np.arange(3)+(j-1)*.16,vals,ls='none',marker=m,color=colors[s],label=LAB[SC.index(s)])
a.axhline(0,color='.5',lw=.6);a.set_xticks(range(3),['Δconn(B1)','Δconn(B0)','Δint']);a.set_ylim(-5.5,10.5)
a.set_ylabel('24 h W3 effect (mg)');a.set_title('Full 2×2 contrasts: grid and time step',loc='left');a.legend(loc='upper right',fontsize=5.8)
foot(fig,'C1/C0: connected/blocked; B1/B0: salinity buoyancy retained/suppressed. Δconn(B) = C1B − C0B; Δint = Δconn(B1) − Δconn(B0).\n'
     'Ranges are finite scenario ranges, not confidence intervals or a bound on all parameter uncertainty. P1/P2 are measured-Ks corners.\n'
     'RH = 0; 24 h; 26 accepted cases. No new experimental validation. Numerical and perturbation envelope includes the coarse grid.')
save(fig,'Fig05_B_final_response_robustness')

# Fig04 extension: bottom supply, opposing fluxes, whole-side budget, depth allocation.
fig,ax=newfig(7.2);ss=supply.set_index('scenario').loc[SC];x=np.arange(10)
a=ax[0,0]
a.plot(x,ss.W3_bottom_salt_C1_g*1000,'o-',color='#0072B2',label='Connected C1B1')
a.plot(x,ss.W3_bottom_salt_C0_g*1000,'s--',color='#D55E00',mfc='white',label='Blocked C0B1')
scenarioaxis(a);a.set_ylim(-10,285);a.set_ylabel('W3 bottom salt input (mg)');a.set_title('Bottom-supply reduction persists',loc='left');a.legend(loc='center left')
a=ax[0,1]
for col,colr,ls,m,label in [('interface_adv_C1_g','#009E73','-','o','Lateral advection'),('interface_diff_C1_g','#CC79A7','--','s','Lateral diffusion')]:a.plot(x,ss[col]*1000,color=colr,ls=ls,marker=m,ms=3,label=label)
a.plot(x,(ss.interface_adv_C1_g+ss.interface_diff_C1_g)*1000,'k:',label='Lateral net')
scenarioaxis(a);a.set_ylim(-60,345);a.set_ylabel('F36 → W3 cumulative salt (mg)');a.set_title('Opposing advective and diffusive exchange',loc='left');a.legend(loc='center left',fontsize=5.8)
a=ax[1,0]
terms=[((ss.W3_bottom_salt_C1_g-ss.W3_bottom_salt_C0_g)*1000,'#D55E00','--','Bottom-supply difference'),((ss.interface_adv_C1_g+ss.interface_diff_C1_g)*1000,'#009E73','-','Lateral input'),(ss.W3_whole_side_connection_effect_g*1000,'#222222','-.','Whole-W3 storage difference')]
for vals,col,ls,label in terms:a.plot(x,vals,color=col,ls=ls,marker='o',ms=2.5,label=label)
a.plot(x,[endpoint(s) for s in SC],color='#0072B2',marker='D',ms=2.5,label='W3 surface 0–3 mm')
scenarioaxis(a);a.set_ylim(-260,320);a.set_ylabel('24 h C1 − C0 contribution (mg)');a.set_title('Supply compensation, whole W3',loc='left');a.legend(loc='center left',bbox_to_anchor=(0,.26),fontsize=5.4)
a=ax[1,1];bands=['0_3','3_10','10_20','20_40']
dep_rows=[]
for i,band in enumerate(bands):
    for group,scenarios,dx,col in [('Numerical / perturbation',NUM,-.1,'#0072B2'),('Ks corners + baseline',PAR,.1,'#009E73')]:
        vals=[endpoint(s,band=band) for s in scenarios];base=endpoint('medium',band=band)
        a.errorbar(i+dx,base,yerr=[[base-min(vals)],[max(vals)-base]],fmt='o' if dx<0 else 's',color=col,capsize=3,ms=3,label=group if i==0 else None)
        dep_rows.append({'band_mm':band,'group':group,'baseline_mg':base,'min_mg':min(vals),'max_mg':max(vals)})
a.set_xticks(range(4),['0–3','3–10','10–20','20–40']);a.set_ylim(0,23);a.set_xlabel('Depth below surface (mm)');a.set_ylabel('24 h W3 Δconn(B1) (mg)');a.set_title('Most added storage lies below 3 mm',loc='left');a.legend(loc='upper right',fontsize=5.6)
table(pd.DataFrame(dep_rows),'depth_effect_finite_ranges')
foot(fig,'B1 only; all panels use the same 10 scenarios. S2/S3: phases 2/3; A0.3/A3: amplitude ×0.3/×3; P1/P2: conductivity corners.\n'
    'Lines across scenario categories guide comparison; categories are not a continuous parameter sweep. Depth whiskers show min–max ranges, not CIs.\n'
    'Whole-side budgets do not substitute for a surface-layer budget. Surface budgets are shown separately in Fig. S local transport.')
save(fig,'Fig04_B_final_supply_and_partitioning')

# FigS: pre-registered tests, including failures, plus non-monotone plumes.
fig,ax=newfig(7.5)
selected=[('C1B1','W3_salt_g_0_3mm_increase','W3 surface gain, C1B1'),('C0B1','W3_salt_g_0_3mm_increase','W3 surface gain, C0B1'),
    ('C1B1','F36_salt_g_0_3mm_increase','F36 surface gain, C1B1'),('C0B1','F36_salt_g_0_3mm_increase','F36 surface gain, C0B1'),
    ('C1B1','A_if_salt_total_cum_net_mol','Interface net, C1B1'),('C1B1','F36_core_desc_vf_1.0e-08','F36 core down-volume, C1B1'),('C1B1','A_W3_down_salt_net_cum_mol_at3mm','W3 vertical net, C1B1'),('C1B0','A_W3_down_salt_net_cum_mol_at3mm','W3 vertical net, C1B0')]
a=ax[0,0];gate_rows=[]
for i,(arm,metric,label) in enumerate(selected):
    for comp,dy,m,col in [('fine',-.12,'o','#0072B2'),('dt150',.12,'s','#D55E00')]:
        r=numeric[(numeric.comparison==comp)&(numeric.arm==arm)&(numeric.metric==metric)].iloc[0]
        ratio=r.relative_difference/r.working_tolerance
        a.plot(ratio,i+dy,marker=m,color=col,mfc=col if ratio<=1 else 'white',ms=4,ls='none')
        gate_rows.append(dict(r,display_label=label,difference_over_tolerance=ratio))
a.axvline(1,color='.3',ls='--',lw=.7);a.set_xlim(-.25,10.5);a.set_yticks(range(len(selected)),[s[2] for s in selected],fontsize=5.5);a.invert_yaxis()
a.set_xlabel('Relative difference / working tolerance');a.set_title('Selected 24 h verification checks',loc='left')
a.legend(handles=[Line2D([],[],marker='o',color='#0072B2',ls='none',label='Medium → fine'),Line2D([],[],marker='s',color='#D55E00',ls='none',label='300 → 150 s')],loc='lower right',fontsize=5.8)
a.text(.97,.72,'>1: outside tolerance\nOpen marker: failed',ha='right',transform=a.transAxes,fontsize=6)
table(pd.DataFrame(gate_rows),'selected_gate_ratios')
# Long labels need a dedicated wider left margin for panel a.
a.set_position([.30,.61,.25,.30]);ax[0,1].set_position([.65,.61,.30,.30])
a=ax[0,1]
for c,m,ls,col in [(1,'o','-','#0072B2'),(0,'s','--','#D55E00')]:
    vals=[plume[(plume.scenario==s)&(plume.C==c)].F36_core_down_volume_fraction.iloc[0] for s in ['coarse','medium','fine']]
    a.plot(range(3),vals,marker=m,ls=ls,color=col,label=f'C{c}B1')
a.set_xticks(range(3),['Coarse','Medium','Fine']);a.set_ylim(0,.27);a.set_ylabel('F36 core descending volume fraction');a.set_title('Plume fraction is not monotone',loc='left');a.legend(loc='upper left',fontsize=5.8)
for a,colkey,title,xlab in [(ax[1,0],'F36_core_down_volume_fraction','Phase / amplitude change plume geometry','24 h F36 core descending fraction'),(ax[1,1],'core_onset_h','Diagnostic onset depends on perturbation','Persistent core downflow onset (h)')]:
    for c,m,col in [(1,'o','#0072B2'),(0,'s','#D55E00')]:
        vals=[plume[(plume.scenario==s)&(plume.C==c)][colkey].iloc[0] for s in PERT]
        a.plot(vals,np.arange(5)+(c-.5)*.13,ls='none',marker=m,color=col,label=f'C{c}B1')
    a.set_yticks(range(5),[LAB[SC.index(s)] for s in PERT]);a.invert_yaxis();a.set_xlabel(xlab);a.set_title(title,loc='left');a.legend(loc='lower right',fontsize=6)
    a.set_xlim((0,.45) if colkey.endswith('fraction') else (8,18))
foot(fig,'A stable W3 integral does not imply converged F36 fields. All registered checks, including unplotted rows, are supplied in SOURCE_DATA.\n'
    'Surface-gain tolerance: 2%; plotted flux/volume tolerance: 5%. Vertical diagnostics retain the original registered depth interpolation.\n'
    'Core descent: Darcy speed >1e-8 m/s; onset requires three consecutive 10-min frames. It is not a linear-instability or MRI-detection onset.\n'
    'Filled/open markers in a indicate within/outside the working tolerance; phase/amplitude sensitivity is not solver failure.')
save(fig,'FigS_B_final_numerical_and_plume_limits')

# Extend the newly added local-budget mechanism with all final B data.
fig,ax=newfig(7.4)
keys2=['vertical_adv_mg','vertical_diff_mg','lateral_adv_direct_mg','lateral_diff_direct_mg','storage_change_mg']
keys3=['vertical_adv_mg','vertical_diff_mg','lateral_net_inferred_mg','storage_change_mg']
labels2=['Vertical advection','Vertical diffusion','Lateral advection','Lateral diffusion','Storage change']
labels3=['Vertical advection','Vertical diffusion','Lateral net* (inferred)','Storage change']
for a,d,keys,labels in [(ax[0,0],2,keys2,labels2),(ax[0,1],3,keys3,labels3)]:
    r=le[(le.depth_mm==d)&(le.B==1)].set_index('scenario').loc[SC]
    for i,(key,label) in enumerate(zip(keys,labels)):
        a.plot(x,r[key],color=modecolors[i],ls=['-','--','-.',':','-'][i],marker=['o','s','^','D','x'][i],ms=2.8,label=label)
    scenarioaxis(a);a.set_ylim(-130,150);a.set_ylabel('24 h W3 C1 − C0 transport (mg)');a.set_title(f'0–{d} mm: compensation across all B1 pairs',loc='left');a.legend(loc='upper left',bbox_to_anchor=(0,-.24),fontsize=5.5,ncol=2)
a=ax[1,0]
inter_rows=[]
for j,s in enumerate(ALLB):
    p=le[(le.scenario==s)&(le.depth_mm==3)].set_index('B');vals=[]
    for key in keys3:
        v=p.loc[1,key]-p.loc[0,key];vals.append(v);inter_rows.append({'scenario':s,'term':key,'interaction_contribution_mg':v})
    a.plot(np.arange(4)+(j-1)*.16,vals,ls='none',marker=['o','s','^'][j],color=colors[s],label=LAB[SC.index(s)])
a.axhline(0,color='.5',lw=.6);a.set_xticks(range(4),['Vertical\nadvection','Vertical\ndiffusion','Lateral net*','Storage\nchange'],fontsize=6)
a.set_ylabel('24 h interaction contribution (mg)');a.set_ylim(-11,12);a.set_title('Buoyancy changes several transport terms',loc='left');a.legend(loc='upper left',fontsize=5.8)
table(pd.DataFrame(inter_rows),'local_interaction_contributions_24h')
a=ax[1,1]
for s,ls in [('medium','-'),('fine','--')]:
    r=ld[(ld.scenario==s)&(ld.B==1)&(ld.depth_mm==3)]
    for key,col,label in [('lateral_net_inferred_mg','#009E73','Lateral net*'),('storage_change_mg','#222222','Storage change')]:
        a.plot(r.time_h,r[key],color=col,ls=ls,label=f'{label}, {LAB[SC.index(s)]}')
    a.plot(r.time_h,r.vertical_adv_mg+r.vertical_diff_mg,color='#0072B2',ls=ls,label=f'Vertical net, {LAB[SC.index(s)]}')
timeaxis(a);a.set_ylabel('W3 0–3 mm C1 − C0 transport (mg)');a.set_ylim(-115,115);a.set_title('Compensation persists on the finer grid',loc='left');a.legend(loc='lower left',fontsize=5.1,ncol=2)
foot(fig,'Upper 2 mm: independent lateral + vertical conservative flux balance. Upper 3 mm: *lateral NET is inferred from storage minus vertical input.\n'
    'Vertical terms use face weights consistent with fractional-cell storage, rather than the nearest mesh plane. No lateral 0–3 mm mode split is fabricated.\n'
    'Small storage differences can coexist with large opposing transport changes. This discrete-budget result does not establish all fluxes are grid independent.\n'
    'S2/S3: phases 2/3; A0.3/A3: amplitude ×0.3/×3; P1/P2: conductivity corners. NaCl-equivalent mass at 58.443 g/mol; true 24 h endpoints.')
save(fig,'FigS_B_final_local_transport_compensation')

if args.pin:PIN.write_text(json.dumps(sources,indent=2),encoding='utf-8')
checks.update({'accepted_cases':26,'B_production_cases':22,'summary':'Final coordinator evidence verified; all available paired effects reproduced; local 0–2 mm independently closes for all 26 cases.',
    'limitations':['Finite scenarios, not confidence intervals','0–3 mm lateral net inferred','No regime map from these verification variants','Original B narrative report remains incomplete; coordinator final evidence used']})
(HERE/'NUMERIC_QA.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
(HERE/'MANIFEST.json').write_text(json.dumps({'source_sha256':sources,'script_sha256':sha(Path(__file__)),'figures':outputs,'source_cutoff_utc':manifest['generated_utc'],
    'software':{'python':sys.version,'numpy':np.__version__,'pandas':pd.__version__,'matplotlib':matplotlib.__version__},
    'output_sha256':{str(p.relative_to(HERE)):sha(p) for p in HERE.rglob('*') if p.is_file() and p.name!='MANIFEST.json' and '__pycache__' not in str(p)}},indent=2),encoding='utf-8')
print(primary.to_string(index=False));print('Figures:',outputs)
