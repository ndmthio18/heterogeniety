"""Read-only precipitation inventory and equivalent external-crust screening."""
from pathlib import Path
import argparse, json, hashlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

p=argparse.ArgumentParser()
p.add_argument('--source',type=Path,required=True)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args(); a.out.mkdir(parents=True,exist_ok=True)
figdir=a.out.parent/'figures'; figdir.mkdir(exist_ok=True)
summary={}; provenance={}
for case in ['Greal-81','Greal-75']:
    root=a.source/case
    for name in ['depth_profiles_compact.csv','mineral_budget.csv']:
        provenance[f'{case}/{name}']=hashlib.sha256((root/name).read_bytes()).hexdigest()
    d=pd.read_csv(root/'depth_profiles_compact.csv').drop_duplicates(['time_s','material','depth_mm'],keep='last')
    m=pd.read_csv(root/'mineral_budget.csv').drop_duplicates('time_s',keep='last').set_index('time_s')
    s=pd.DataFrame(index=m.index); s['time_h']=m.evaporation_time_h
    for label,mask in {
        'W3_all':d.material.eq(1), 'W3_top1':d.material.eq(1)&d.depth_mm.lt(1),
        'W3_top2':d.material.eq(1)&d.depth_mm.lt(2),
        'W3_deeper2':d.material.eq(1)&d.depth_mm.ge(2), 'F36':d.material.eq(0)
    }.items():
        s[label]=d[mask].groupby('time_s').salt_solid_mol.sum().reindex(s.index)
    assert s.notna().all().all(), 'Missing profile/ledger matches'
    # Filter is a ledger remainder, not an independent spatial observation.
    s['filter_remainder']=m.salt_solid_mol-m.fine_solid_mol-m.coarse_solid_mol
    s['total']=m.salt_solid_mol
    err=(s.W3_all-m.fine_solid_mol).abs().max()
    err2=(s.F36-m.coarse_solid_mol).abs().max()
    onset={}
    for col in ['total','W3_all','W3_top1','W3_top2','W3_deeper2','F36','filter_remainder']:
        onset[col]={}
        for threshold in [1e-12,1e-9,1e-6]:
            q=s[(s[col]>threshold)&(s.time_h>=0)]
            onset[col][str(threshold)]=None if q.empty else float(q.time_h.iloc[0])
    summary[case]={'onset_threshold_mol':onset,'profile_vs_ledger_max_abs_mol':{'W3':float(err),'F36':float(err2)},'terminal_mol':s.iloc[-1].to_dict()}
    s.to_csv(a.out/f'{case}_solid_inventory_mol.csv',index_label='time_s')
    heights=[]
    for region in ['W3_top1','W3_top2','W3_all']:
        for rho in [2165.,2650.]:
            for porosity in [.3,.43,.6]:
                for cover in [1.,.75,.5,.25]:
                    h=s[region]*.05844/(rho*(1-porosity)*(np.pi*.025**2/2)*cover)
                    heights.append(pd.DataFrame({'time_h':s.time_h,'region':region,'rho_kg_m3':rho,'porosity':porosity,'coverage':cover,'height_mm':h*1000,'growth_mm_h':np.gradient(h*1000,s.index/3600)}))
    pd.concat(heights).to_csv(a.out/f'{case}_thickness_sensitivity.csv',index=False)
    fig,ax=plt.subplots(figsize=(7,4),layout='constrained')
    for col,style in [('W3_all','-'),('W3_top1','--'),('W3_top2',':'),('W3_deeper2','-.')]:
        ax.plot(s.time_h,s[col]*58.44,style,label=col)
    ax.set(xlim=(0,174),xlabel='Evaporation time (h)',ylabel='Solid NaCl equivalent (g)',title=case)
    ax.legend(); fig.savefig(figdir/f'Figure1_{case}.png',dpi=300); fig.savefig(figdir/f'Figure1_{case}.pdf'); plt.close(fig)
    fig,ax=plt.subplots(figsize=(7,4),layout='constrained')
    for cover,style in zip([1,.75,.5,.25],['-','--',':','-.']):
        h=s.W3_top1*.05844/(2165*.57*(np.pi*.025**2/2)*cover)*1000
        ax.plot(s.time_h,h,style,label=f'Coverage {cover:g}')
    ax.set(xlim=(0,174),xlabel='Evaporation time (h)',ylabel='Hypothetical external crust height (mm)',title=case+'; top 1 mm inventory; porosity 0.43')
    ax.legend(); fig.savefig(figdir/f'Figure2_{case}.png',dpi=300); fig.savefig(figdir/f'Figure2_{case}.pdf'); plt.close(fig)
(a.out/'inventory_summary.json').write_text(json.dumps(summary,indent=2))
(a.out/'source_hashes.json').write_text(json.dumps(provenance,indent=2))
print(json.dumps(summary,indent=2))
