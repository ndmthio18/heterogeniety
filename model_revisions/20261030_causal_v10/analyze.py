"""2x2 connection/buoyancy effects from the reduced v10 runs (local).
E_B(t)=S_surface,W3(C1,B,t)-S_surface,W3(C0,B,t); interaction E_1-E_0.
Absolute g differences are primary; relative values only where the reference
change is not near zero. Usage: analyze.py <tag>"""
from pathlib import Path
import hashlib,json,sys
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
L=Path(__file__).resolve().parent
CASES=['C1B1','C0B1','C1B0','C0B0']
TIMES=[0,2,4,8,12,24]
COL={'C1B1':'#1f4e9c','C0B1':'#7fa7e0','C1B0':'#b03a2e','C0B0':'#e8a29a'}
STY={'C1B1':'-','C0B1':'--','C1B0':'-','C0B0':'--'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(tag):
 d={}
 for c in CASES:
  r=L/'results'/tag/f'{c}_24h'
  if not (r/'extraction.json').exists():continue
  ts=pd.read_csv(r/'timeseries.csv');fr=pd.read_csv(r/'frames.csv');vt=pd.read_csv(r/'vertical_transport.csv')
  grid=np.round(ts.t_h*6)/6;ts=ts[np.abs(ts.t_h-grid)<1e-9].copy();ts['t_h']=np.round(ts.t_h*6)/6;ts=ts.drop_duplicates('t_h',keep='last').set_index('t_h')
  fr['t_h']=np.round(fr.t_h*6)/6;fr=fr.set_index('t_h')
  vgrid=np.round(vt.t_h*6)/6;vt=vt[np.abs(vt.t_h-vgrid)<1e-9].copy();vt['t_h']=np.round(vt.t_h*6)/6;vt=vt.drop_duplicates('t_h',keep='last').set_index('t_h')
  d[c]=dict(ts=ts,fr=fr,vt=vt,info=json.loads((r/'extraction.json').read_text()),persist=json.loads((r/'persistent_downflow.json').read_text())['first_time_h'])
 return d
def pick(df,col,t):return float(df.loc[t,col]) if t in df.index else np.nan
def main(tag):
 d=load(tag);out=L/'analysis'/tag;out.mkdir(parents=True,exist_ok=True)
 have=[c for c in CASES if c in d];print('cases',have)
 metrics=[]
 for side in ['W3','F36']:
  for b in ['0_3mm','0_2mm','3_10mm','10_20mm','20_40mm','total']:metrics.append((f'{side}_salt_g_{b}','ts','g'))
  metrics+= [(f'{side}_C_mean_mol_L_0_3mm','ts','mol/L'),(f'{side}_cum_bottom_salt_in_g','ts','g'),(f'{side}_cum_bottom_water_in_g','ts','g'),(f'{side}_cum_evaporation_g','ts','g'),(f'{side}_water_storage_g','ts','g'),
   (f'{side}_excess_centroid_depth_mm','fr','mm'),(f'{side}_enriched_depth_mm_1.1M','fr','mm'),(f'{side}_core_descending_volume_fraction_1e-08','fr','-'),(f'{side}_core_rms_anomaly_mol_L','fr','mol/L'),(f'{side}_core_max_down_m_s','fr','m/s')]
 metrics+=[('domain_salt_g_total','ts','g'),('domain_cum_evaporation_g','ts','g'),('W3_evaporation_share','ts','-'),('interface_salt_coarse_to_fine_cum_g','ts','g')]
 rows=[]
 for m,src,unit in metrics:
  for t in TIMES:
   v={c:pick(d[c][src],m,t) for c in have};r={'metric':m,'unit':unit,'t_h':t,**{c:v[c] for c in have}}
   for B in ['1','0']:
    a,b=f'C1B{B}',f'C0B{B}'
    if a in v and b in v:
     r[f'E_B{B}']=v[a]-v[b]
     if unit=='g' and src=='ts':
      dref=v[b]-pick(d[b][src],m,0)
      r[f'E_B{B}_rel_to_C0_change']=r[f'E_B{B}']/dref if abs(dref)>1e-3 else np.nan
   if 'E_B1' in r and 'E_B0' in r:r['interaction_E1_minus_E0']=r['E_B1']-r['E_B0']
   for C in ['1','0']:
    a,b=f'C{C}B1',f'C{C}B0'
    if a in v and b in v:r[f'buoyancy_effect_C{C}']=v[a]-v[b]
   rows.append(r)
 eff=pd.DataFrame(rows);eff.to_csv(out/'effects_table.csv',index=False)
 # Full-resolution effect time series on the 10-min grid.
 ts={c:d[c]['ts'] for c in have};series=pd.DataFrame(index=ts[have[0]].index)
 for m in ['W3_salt_g_0_3mm','W3_salt_g_0_2mm','F36_salt_g_0_3mm','F36_salt_g_0_2mm','W3_salt_g_total','F36_salt_g_total','domain_salt_g_total','W3_salt_g_3_10mm','W3_salt_g_10_20mm','W3_salt_g_20_40mm']:
  for B in ['1','0']:
   if f'C1B{B}' in ts and f'C0B{B}' in ts:series[f'E_B{B}_{m}']=ts[f'C1B{B}'][m]-ts[f'C0B{B}'][m]
  if f'E_B1_{m}' in series and f'E_B0_{m}' in series:series[f'interaction_{m}']=series[f'E_B1_{m}']-series[f'E_B0_{m}']
 series.to_csv(out/'effects_timeseries.csv')
 # Exact side-level decomposition of the connection effect: dS=B+I (salt).
 dec=[]
 for B in ['1','0']:
  a,b=f'C1B{B}',f'C0B{B}'
  if a not in ts or b not in ts:continue
  for t in TIMES:
   for side,sgn in [('W3',1),('F36',-1)]:
    dS1=pick(ts[a],f'{side}_salt_g_total',t)-pick(ts[a],f'{side}_salt_g_total',0);dS0=pick(ts[b],f'{side}_salt_g_total',t)-pick(ts[b],f'{side}_salt_g_total',0)
    B1=pick(ts[a],f'{side}_cum_bottom_salt_in_g',t);B0=pick(ts[b],f'{side}_cum_bottom_salt_in_g',t);I1=sgn*pick(ts[a],'interface_salt_coarse_to_fine_cum_g',t);I0=sgn*pick(ts[b],'interface_salt_coarse_to_fine_cum_g',t)
    dec.append({'B':B,'t_h':t,'side':side,'dS_connected_g':dS1,'dS_partitioned_g':dS0,'effect_on_side_inventory_g':dS1-dS0,'bottom_supply_difference_g':B1-B0,'interface_input_connected_g':I1,'interface_input_partitioned_g':I0,'closure_g':(dS1-dS0)-((B1-B0)+(I1-I0))})
 pd.DataFrame(dec).to_csv(out/'side_decomposition.csv',index=False)
 # Interface exchange by band (connected cases).
 ib=[]
 for c in have:
  if c.startswith('C0'):continue
  for t in TIMES:
   for comp in ['salt','water']:
    for mode in ['adv','diff']:
     for band in ['0_2','2_10','10_20','20_40']:
      base=f'if_{mode}_{comp}_{band}mm'
      ib.append({'case':c,'t_h':t,'component':comp,'mode':mode,'band_mm':band,'net_g':pick(ts[c],base+'_cum_net_g',t),'coarse_to_fine_g':pick(ts[c],base+'_cum_pos_g',t),'fine_to_coarse_g':pick(ts[c],base+'_cum_neg_g',t)})
 pd.DataFrame(ib).to_csv(out/'interface_exchange.csv',index=False)
 # Vertical transport and plume onset.
 vt=[]
 for c in have:
  for t in TIMES:
   r={'case':c,'t_h':t}
   for k in d[c]['vt'].columns:r[k]=pick(d[c]['vt'],k,t)
   vt.append(r)
 pd.DataFrame(vt).to_csv(out/'vertical_transport_selected.csv',index=False)
 (out/'persistent_downflow.json').write_text(json.dumps({c:d[c]['persist'] for c in have},indent=2))
 # Figures.
 fig,ax=plt.subplots(2,3,figsize=(15,8.5))
 for c in have:
  t=ts[c].index
  for j,(side,b) in enumerate([('W3','0_3mm'),('F36','0_3mm'),('W3','total')]):ax[0,j].plot(t,ts[c][f'{side}_salt_g_{b}'],STY[c],c=COL[c],label=c)
 for j,(side,b) in enumerate([('W3','0_3mm'),('F36','0_3mm'),('W3','total')]):ax[0,j].set(title=f'{side} salt {b.replace("_","-")} (NaCl g)',xlabel='Evaporation time (h)');ax[0,j].legend(fontsize=8)
 for j,m in enumerate(['W3_salt_g_0_3mm','F36_salt_g_0_3mm','domain_salt_g_total']):
  for B,c in [('1','#1f4e9c'),('0','#b03a2e')]:
   if f'E_B{B}_{m}' in series:ax[1,j].plot(series.index,series[f'E_B{B}_{m}'],c=c,label=f'E_B{B}=C1B{B}-C0B{B}')
  if f'interaction_{m}' in series:ax[1,j].plot(series.index,series[f'interaction_{m}'],'k:',label='E_1-E_0')
  ax[1,j].axhline(0,c='.6',lw=.6);ax[1,j].set(title=f'Connection effect: {m}',xlabel='Evaporation time (h)',ylabel='g');ax[1,j].legend(fontsize=8)
 fig.suptitle('v10 2x2: material contact (C) x salinity buoyancy (B); same external forcing, solved fluxes');fig.tight_layout();fig.savefig(out/'fig1_inventories_effects.png',dpi=150);plt.close(fig)
 fig,ax=plt.subplots(2,3,figsize=(15,8.5))
 for c in have:
  t=ts[c].index
  for j,side in enumerate(['W3','F36']):ax[0,j].plot(t,ts[c][f'{side}_cum_bottom_salt_in_g'],STY[c],c=COL[c],label=c);ax[1,j].plot(t,ts[c][f'{side}_cum_evaporation_g'],STY[c],c=COL[c],label=c)
  ax[0,2].plot(t,ts[c]['interface_salt_coarse_to_fine_cum_g'],STY[c],c=COL[c],label=c);ax[1,2].plot(t,ts[c]['W3_evaporation_share'],STY[c],c=COL[c],label=c)
 for a,ttl in zip(ax.ravel(),['W3 cumulative bottom salt supply (g)','F36 cumulative bottom salt supply (g)','Interface salt coarse->fine, cumulative net (g)','W3 cumulative evaporation (g)','F36 cumulative evaporation (g)','W3 share of evaporation (-)']):a.set(title=ttl,xlabel='Evaporation time (h)');a.legend(fontsize=8)
 fig.tight_layout();fig.savefig(out/'fig2_supply_interface_evaporation.png',dpi=150);plt.close(fig)
 fig,ax=plt.subplots(2,3,figsize=(15,8.5))
 for c in have:
  f=d[c]['fr']
  for i,side in enumerate(['F36','W3']):
   ax[i,0].plot(f.index,f[f'{side}_core_max_down_m_s']*1e8,STY[c],c=COL[c],label=c)
   ax[i,1].plot(f.index,f[f'{side}_core_descending_volume_fraction_1e-08']*100,STY[c],c=COL[c],label=c)
   ax[i,2].plot(f.index,f[f'{side}_core_rms_anomaly_mol_L'],STY[c],c=COL[c],label=c)
 for i,side in enumerate(['F36','W3']):
  ax[i,0].axhline(1,c='.5',ls=':');ax[i,0].set(title=f'{side} core max downward Darcy (1e-8 m/s)',xlabel='h',yscale='symlog');ax[i,1].set(title=f'{side} core volume with q_down>1e-8 m/s (%)',xlabel='h');ax[i,2].set(title=f'{side} core same-depth anomaly RMS (mol/L)',xlabel='h')
  for a in ax[i]:a.legend(fontsize=8)
 fig.text(.5,.01,'Threshold diagnostics are not linear-instability or MRI-visible onset. Core: r<20 mm, >3 mm from interface, depth 5-35 mm.',ha='center',fontsize=8)
 fig.tight_layout(rect=(0,.03,1,1));fig.savefig(out/'fig3_plume_diagnostics.png',dpi=150);plt.close(fig)
 fig,ax=plt.subplots(1,2,figsize=(11,5.5))
 for c in have:
  r=L/'results'/tag/f'{c}_24h';p=np.load(r/'profiles.npz');k=int(np.argmin(np.abs(p['t_h']-24)))
  for i,side in enumerate(['F36','W3']):ax[i].plot(p['pore_weighted_C_mol_L'][k,i],p['depth_mm'],STY[c],c=COL[c],label=c)
 for i,side in enumerate(['F36','W3']):ax[i].set(title=f'{side} pore-weighted solution C at 24 h',xlabel='mol/L',ylabel='Depth (mm)',ylim=(40,0));ax[i].legend(fontsize=8)
 fig.tight_layout();fig.savefig(out/'fig4_profiles_24h.png',dpi=150);plt.close(fig)
 fig,ax=plt.subplots(1,len(have),figsize=(4.2*len(have),4.6),squeeze=False)
 for j,c in enumerate(have):
  s=np.load(L/'results'/tag/f'{c}_24h'/'snapshots.npz');pos=s['positions'];m=np.abs(pos[:,2])<.0011
  im=ax[0,j].scatter(pos[m,0]*1000,s['depth_mm'][m],c=s['24h_C'][m],s=5,cmap='viridis',vmin=1,vmax=3.5);ax[0,j].set(title=f'{c} 24 h, |z|<1.1 mm',xlim=(0,50),ylim=(40,0),xlabel='x (mm)',ylabel='Depth (mm)');ax[0,j].axvline(25,c='w',lw=.6)
 fig.colorbar(im,ax=ax.ravel().tolist(),label='C (mol/L)');fig.savefig(out/'fig5_sections_24h.png',dpi=150);plt.close(fig)
 summary={'tag':tag,'cases':have,'extraction':{c:{k:d[c]['info'][k] for k in ['frames','max_field_vs_ledger_band_salt_relative_error','max_side_budget_closure_g','script_sha256']} for c in have},
  'analysis_script_sha256':sha(Path(__file__)),'outputs':sorted(p.name for p in out.iterdir())}
 (out/'analysis_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=1))
if __name__=='__main__':main(sys.argv[1] if len(sys.argv)>1 else 'v10c')
