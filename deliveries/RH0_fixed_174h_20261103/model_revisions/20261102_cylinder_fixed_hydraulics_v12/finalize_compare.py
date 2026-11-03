"""Accepted 174h comparison; no fitting, clock shifts, MRI-based onset or extrapolation."""
from pathlib import Path
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
import json,hashlib,datetime,importlib.util
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize,TwoSlopeNorm
from matplotlib.backends.backend_pdf import PdfPages
from PIL import Image,ImageOps,ImageDraw
R=Path(__file__).resolve().parent;P=R.parents[1];O=R/'results/comparison';D=R/'remote_backup/runs/RH0_174h';OD=R.parent/'20261030_cylinder_precip_v09_r02/remote_backup/runs/RH0_174h'
oldanalysis=P/'analysis/rh0_evaporation_65h_20261102'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
spec=importlib.util.spec_from_file_location('native',R.parent/'20261029_cylinder_v06/plot_comparison.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
blue='#0072B2';orange='#D55E00';grey='#777777';colors={'fixed':blue,'coupled':grey};labels={'fixed':'Fixed porosity / K','coupled':'Coupled porosity / K (to 65.28h)'}
b=pd.read_csv(D/'budget.csv');f=pd.read_csv(D/'film_budget.csv');mi=pd.read_csv(D/'mineral_budget.csv');ob=pd.read_csv(OD/'budget.csv');of=pd.read_csv(OD/'film_budget.csv')
assert b.evaporation_time_h.iloc[-1]==174
mass=pd.read_csv(oldanalysis/'full_experiment/full_experimental_mass.csv');arch=pd.read_csv(oldanalysis/'report_rate_formula_audit.csv')
at=lambda t,col='cumulative_reservoir_loss_g':np.interp(t,f.evaporation_time_h,f[col])
oldat=lambda t:np.interp(t,of.evaporation_time_h,of.cumulative_reservoir_loss_g)
rows=[]
for a,z in zip(mass.iloc[:-1].itertuples(),mass.iloc[1:].itertuples()):
 dt=z.time_h-a.time_h;ex=a.mass_g-z.mass_g
 row={'start_h':a.time_h,'end_h':z.time_h,'mid_h':(a.time_h+z.time_h)/2,'duration_h':dt,'experiment_loss_g':ex,'experiment_rate_g_h':ex/dt}
 for k,fn,end in [('fixed',at,174),('coupled',oldat,float(of.evaporation_time_h.iloc[-1]))]:
  v=fn(z.time_h)-fn(a.time_h) if z.time_h<=end else np.nan;row[k+'_loss_g']=v;row[k+'_rate_g_h']=v/dt
 rows.append(row)
iv=pd.DataFrame(rows);iv.to_csv(O/'interval_rates.csv',index=False);metrics=[]
for k in colors:
 for lo,hi in [(1,24),(24,60),(1,60),(60,174),(24,174),(1,174)]:
  q=iv[(iv.start_h>=lo)&(iv.end_h<=hi)]
  if q[k+'_loss_g'].isna().any():continue
  ex=q.experiment_loss_g.sum();mo=q[k+'_loss_g'].sum()
  metrics.append(dict(model=k,start_h=lo,end_h=hi,experiment_g=ex,model_g=mo,error_percent=(mo/ex-1)*100,rate_RMSE_g_h=np.sqrt(np.average((q[k+'_rate_g_h']-q.experiment_rate_g_h)**2,weights=q.duration_h))))
metrics=pd.DataFrame(metrics);metrics.to_csv(O/'evaporation_metrics.csv',index=False)
g=b[b.evaporation_time_h>=0].copy();mg=mi[mi.evaporation_time_h>=0];MW=18.01518;MS=58.4428;A=np.pi*.025**2
for side,col in [('F36','coarse_top_water_out_mol_s'),('W3','fine_top_water_out_mol_s')]:g[side+'_water_mm_day']=g[col]*MW/1000/(A/2)*86400
g['whole_water_mm_day']=(g.F36_water_mm_day+g.W3_water_mm_day)/2
g['F36_bottom_supply_mol']=-np.cumsum(np.where(g.evaporation_time_h>0,g.coarse_bottom_salt_out_mol_s*g.dt_s,0))
g['W3_bottom_supply_mol']=-np.cumsum(np.where(g.evaporation_time_h>0,g.fine_bottom_salt_out_mol_s*g.dt_s,0))
g['interface_net_coarse_to_fine_mol']=g.cumulative_interface_adv_mol+g.cumulative_interface_diff_mol-g.cumulative_interface_adv_mol.iloc[0]-g.cumulative_interface_diff_mol.iloc[0]
seed=json.loads((D/'seed_event.json').read_text());saltrows=[]
for j,(side,key) in enumerate([('F36','coarse_salt_mol'),('W3','fine_salt_mol')]):
 change=g[key]-g[key].iloc[0];exchange=g.interface_net_coarse_to_fine_mol*(-1 if j==0 else 1)
 residual=change-g[side+'_bottom_supply_mol']-exchange-np.where(g.evaporation_time_h>0,seed['partition_impulses_mol'][j],0)
 assert max(abs(residual))<1e-10
 saltrows.append(dict(side=side,inventory_increase_mol=change.iloc[-1],bottom_supply_mol=g[side+'_bottom_supply_mol'].iloc[-1],interface_in_mol=exchange.iloc[-1],seed_mol=seed['partition_impulses_mol'][j],max_residual_mol=max(abs(residual))))
pd.DataFrame(saltrows).to_csv(O/'salt_partition_closure.csv',index=False);g.to_csv(O/'model_budget_derived.csv',index=False)
assert max(abs(np.cumsum(f.top_water_mol_s*f.dt_s*MW)-f.cumulative_top_water_g))<1e-9
assert max(abs((b.cumulative_coarse_top_water_mol+b.cumulative_fine_top_water_mol)*MW-f.cumulative_top_water_g))<1e-9
data={k:np.load(O/k/'profiles.npz') for k in colors};sn={k:np.load(O/k/'snapshots.npz') for k in colors};hs={k:pd.read_csv(O/k/'spatial_history.csv') for k in colors}
assert np.array_equal(sn['fixed']['positions'],sn['coupled']['positions'])
def profile(k,t,j):
 d=data[k];assert t<=max(d['time']);return np.array([np.interp(t,d['time'],d['concentration'][:,j,z]) for z in range(40)])
exp=pd.read_csv(P/'analysis/model_experiment_comparison_20261028/experimental_profiles.csv');ep={(s,float(t)):q.sort_values('depth_center_mm').archived_concentration.to_numpy() for (s,t),q in exp.groupby(['side','time_h'])}
Z=np.arange(40)+.5;pr=[];pairs=[]
for k in colors:
 for (side,t),e in ep.items():
  if t>max(data[k]['time']):continue
  j=['F36','W3'].index(side);c=profile(k,t,j)
  for band,mask in [('whole_0_40',np.ones(40,dtype=bool)),('interior_3_37',(Z>=3)&(Z<37))]:pr.append(dict(model=k,side=side,time_h=t,band=band,RMSE_mol_L=np.sqrt(np.mean((c[mask]-e[mask])**2)),bias_mol_L=np.mean(c[mask]-e[mask])))
  for z,x,y in zip(Z,c,e):pairs.append(dict(model=k,side=side,time_h=t,depth_mm=z,model_mol_L=x,experiment_mol_L=y))
uniform=np.load(R.parent/'20261029_cylinder_v06/results/production24/profiles.npz')
for j,side in enumerate(['F36','W3']):
 c=np.array([np.interp(24,uniform['time'],uniform['concentration'][:,j,z]) for z in range(40)]);e=ep[side,24.]
 for band,mask in [('whole_0_40',np.ones(40,dtype=bool)),('interior_3_37',(Z>=3)&(Z<37))]:pr.append(dict(model='uniform_v06',side=side,time_h=24,band=band,RMSE_mol_L=np.sqrt(np.mean((c[mask]-e[mask])**2)),bias_mol_L=np.mean(c[mask]-e[mask])))
pr=pd.DataFrame(pr);pr.to_csv(O/'profile_metrics.csv',index=False);pd.DataFrame(pairs).to_csv(O/'profile_pairs.csv',index=False)
prefix=[]
for t in [0,2,4,24,57.5,60,65+1/6]:
 prefix.append({'time_h':t,**{key:float(max(abs(sn['fixed'][f'{t:.6f}_{key}']-sn['coupled'][f'{t:.6f}_{key}']))) for key in ['C','down','anomaly']}})
pd.DataFrame(prefix).to_csv(O/'native_field_differences.csv',index=False)
figures=[];pdf=PdfPages(O/'RH0_FIXED_174H_COMPARISON.pdf')
def save(fig,name,title,foot):
 fig.suptitle(title,fontsize=13);fig.text(.5,.012,foot,ha='center',fontsize=8);fig.tight_layout(rect=(0,.045,1,.95))
 if name in ['05_early','06_common']:fig.subplots_adjust(hspace=.42)
 fig.savefig(O/(name+'.png'),dpi=180);fig.savefig(O/(name+'.pdf'));pdf.savefig(fig);plt.close(fig);figures.append(name)
def timeax(ax):ax.set(xlabel='Nominal evaporation time (h)',xlim=(0,186));ax.grid(alpha=.15)
fig,axs=plt.subplots(2,2,figsize=(12,8))
ax=axs[0,0];ax.plot(mass.time_h,mass.solution_loss_since_1h_g,'o',mfc='white',c='k',ms=3,label='Measured reservoir solution loss')
for k,df in [('fixed',f),('coupled',of)]:
 q=df[df.evaporation_time_h>=1];ax.plot(q.evaporation_time_h,q.cumulative_reservoir_loss_g-np.interp(1,df.evaporation_time_h,df.cumulative_reservoir_loss_g),c=colors[k],ls='-' if k=='fixed' else '--',label=labels[k])
ax.set(title='a  Cumulative reservoir solution loss',ylabel='Loss since 1 h (g)');ax.legend(fontsize=7)
ax=axs[0,1];ax.errorbar(iv.mid_h,iv.experiment_rate_g_h,xerr=iv.duration_h/2,fmt='o',ms=3,mfc='white',c='k',lw=.6,label='Measured interval average')
for k in colors:ax.plot(iv.mid_h,iv[k+'_rate_g_h'],c=colors[k],ls='-' if k=='fixed' else '--',label=k)
ax.set(title='b  Identical weighing intervals',ylabel='Solution loss rate (g/h)');ax.legend(fontsize=8)
ax=axs[1,0];fac=240/(1.002*19.64);ax.plot(arch.display_time_h,arch.report_proxy_mm_day,':',c=grey,label='Report-derived column, original timestamps');ax.plot(iv.mid_h,iv.experiment_rate_g_h*fac,'o-',ms=3,c='k',label='Recomputed from actual intervals');ax.plot(iv.mid_h,iv.fixed_rate_g_h*fac,c=blue,label='Fixed model, same conversion');ax.set(title='c  Report-proxy rate (separate convention)',ylabel='Apparent rate (mm/day)');ax.legend(fontsize=7)
ax=axs[1,1]
for col,c,ls,label in [('F36_water_mm_day',orange,'-','Coarse F36'),('W3_water_mm_day',blue,'--','Fine W3'),('whole_water_mm_day',grey,':','Whole surface')]:ax.plot(g.evaporation_time_h,g[col],c=c,ls=ls,label=label)
ax.axvline(57+7/12,c='.4',ls=':',lw=1);ax.set(title='d  Model top-water flux by sand',ylabel='Water-equivalent rate (mm/day)');ax.legend(fontsize=8)
for ax in axs.flat:timeax(ax)
save(fig,'01_evaporation','RH=0: fixed porosity and K, accepted 174 h','No extrapolation of the failed coupled run. Horizontal bars are measurement intervals, not uncertainty; no measured t=0 mass.')
fig,axs=plt.subplots(2,2,figsize=(12,8))
ax=axs[0,0]
for col,lab,ls in [('salt_total_mol','Total salt','-'),('salt_dissolved_mol','Dissolved','--'),('salt_solid_mol','Solid',':')]:ax.plot(g.evaporation_time_h,g[col]*MS,label=lab,ls=ls)
ax.set(title='a  Fixed-model salt inventories',ylabel='NaCl mass (g)');ax.legend()
ax=axs[0,1];ax.plot(g.evaporation_time_h,mg.fine_solid_mol.to_numpy()*MS,c=blue,label='Fine solid');ax.plot(g.evaporation_time_h,mg.coarse_solid_mol.to_numpy()*MS,c=orange,label='Coarse solid');ax.plot(ob.evaporation_time_h,ob.salt_solid_mol*MS,'--',c=grey,label='Coupled total (accepted prefix)');ax.set(title='b  Equilibrium solid inventory',ylabel='Solid NaCl (g)');ax.legend()
for j,(side,key) in enumerate([('F36','coarse_salt_mol'),('W3','fine_salt_mol')]):
 ax=axs[1,j];ax.plot(g.evaporation_time_h,(g[key]-g[key].iloc[0])*MS,label='Total-salt increase',c='k');ax.plot(g.evaporation_time_h,g[side+'_bottom_supply_mol']*MS,label='Net bottom supply',c=blue);ax.plot(g.evaporation_time_h,g.interface_net_coarse_to_fine_mol*(-1 if j==0 else 1)*MS,label='Net interface inflow',c=orange);ax.set(title=f'{chr(99+j)}  {side}: supply / exchange / storage',ylabel='NaCl mass since 0 h (g)');ax.legend(fontsize=8)
for ax in axs.flat:timeax(ax)
save(fig,'02_salt','Salt conservation and spatial partition','Solid is retained in total-salt storage. Equivalent solid volume is an inventory diagnostic, not geometric pore occupancy or salt-crust shape.')
fig,axs=plt.subplots(2,4,figsize=(12,7),sharex=True,sharey=True)
for j,side in enumerate(['F36','W3']):
 for i,t in enumerate([24,60,108,174]):
  ax=axs[j,i];ax.plot(ep[side,float(t)],Z,'o',ms=3,mfc='white',c='k',label='Archived MRI');ax.plot(profile('fixed',t,j),Z,c=blue,label='Fixed')
  if t<=max(data['coupled']['time']):ax.plot(profile('coupled',t,j),Z,'--',c=grey,label='Coupled')
  ax.set(title=f'{side} | {t} h',xlim=(0,5.5),ylim=(40,0),xlabel='Solution C (mol/L)');ax.grid(alpha=.15)
  if i==0:ax.set_ylabel('Depth below surface (mm)')
axs[0,0].legend(fontsize=8)
save(fig,'03_profiles','Unfitted whole-half concentration profiles','MRI is dissolved-salt evidence, not total salt or crystallization timing. Exact voxel processing / 32 min scan window are not reproduced; nominal clock.')
fig,axs=plt.subplots(2,2,figsize=(12,7))
for k,h in hs.items():
 for ax,key,mult in [(axs[0,0],'F36_all_max_down_m_s',1e8),(axs[0,1],'F36_core_max_down_m_s',1e8),(axs[1,0],'F36_core_descending_volume_fraction',100),(axs[1,1],'F36_core_rms_anomaly_mol_L',1)]:ax.plot(h.time_h,h[key]*mult,c=colors[k],ls='-' if k=='fixed' else '--',label=k)
for ax,title,y in zip(axs.flat,['a  All coarse-sand cells','b  Coarse interior core','c  Core volume with downward velocity >1e-8 m/s','d  Core same-depth concentration anomaly'],['Max downward speed (1e-8 m/s)','Max downward speed (1e-8 m/s)','Volume fraction (%)','RMS anomaly (mol/L)']):ax.set(title=title,ylabel=y);timeax(ax);ax.legend()
save(fig,'04_downflow','Coarse-sand downward-flow diagnostics','Core excludes wall/top/bottom 5 mm and interface 3 mm. Interior-LS velocity; hourly after 4 h; threshold is not MRI-visible or linear-instability onset.')
def field(k,t,key='C'):return sn[k][f'{t:.6f}_{key}']
polys,ix=helper.section(sn['fixed']['vertices'],0)
for name,times,title in [('05_early',[2,4],'Early central sections: unchanged pre-precipitation prefix'),('06_common',[60,65+1/6],'Last common native-field comparison after equilibrium precipitation')]:
 fig,axs=plt.subplots(2,2,figsize=(9,7));vmax=max(field(k,t)[ix].max() for k in colors for t in times);norm=Normalize(1,vmax)
 for j,k in enumerate(['coupled','fixed']):
  for i,t in enumerate(times):
   ax=axs[j,i];im=helper.panel(ax,polys,field(k,t)[ix],norm,'viridis');ax.set(title=f'{k} | {t:.3f} h',xlim=(0,50),ylim=(40,0),xlabel='x (mm)',ylabel='Depth (mm)');ax.axvline(25,c='.4',lw=.5);ax.set_aspect('equal');fig.colorbar(im,ax=ax,label='mol/L',shrink=.8)
 save(fig,name,title,'Shared color scale; native finite-volume cells at z=0. Coarse sand left, fine sand right. No coupled-model fields beyond its saved prefix.')
fig,axs=plt.subplots(2,3,figsize=(12,8));anmax=max(abs(field('fixed',t,'anomaly')[ix]).max() for t in [96,108,174])
for j,key in enumerate(['C','anomaly']):
 norm=Normalize(1,5.4) if j==0 else TwoSlopeNorm(vmin=-anmax,vcenter=0,vmax=anmax)
 for i,t in enumerate([96,108,174]):
  ax=axs[j,i];im=helper.panel(ax,polys,field('fixed',t,key)[ix],norm,'viridis' if j==0 else 'RdBu_r');ax.set(title=f'{key} | fixed {t} h',xlim=(0,50),ylim=(40,0),xlabel='x (mm)',ylabel='Depth (mm)');ax.set_aspect('equal');fig.colorbar(im,ax=ax,label='mol/L',shrink=.8)
save(fig,'07_late_fields','Late fixed-hydraulics native central sections','Same-depth anomaly removes each material layer mean. Late fields have no completed coupled counterpart and do not establish experimental plume agreement.')
verts=sn['fixed']['vertices'];pos=sn['fixed']['positions'];fig,axs=plt.subplots(2,4,figsize=(13,7.5));anmax=max(abs(field('fixed',t,'anomaly')).max() for t in [24,174]);norm=TwoSlopeNorm(vmin=-anmax,vcenter=0,vmax=anmax)
for j,t in enumerate([24,174]):
 for i,z in enumerate([-.01,.01]):
  ps,ii=helper.section(verts,z);ax=axs[j,i];im=helper.panel(ax,ps,field('fixed',t,'anomaly')[ii],norm,'RdBu_r');ax.set(title=f'{t} h | z={z*1000:g} mm',xlim=(0,50),ylim=(40,0),xlabel='x (mm)',ylabel='Depth (mm)');ax.set_aspect('equal')
 for i,depth in enumerate([10,25]):
  y=.04-depth/1000;ii=np.flatnonzero((np.nanmin(verts[:,:,1],axis=1)<=y)&(np.nanmax(verts[:,:,1],axis=1)>y));ps=[]
  for v in verts[ii]:
   vv=v[np.isfinite(v[:,0])];p=vv[np.isclose(vv[:,1],vv[:,1].min(),atol=1e-12)][:,[0,2]]*1000;centre=p.mean(0);ps.append(p[np.argsort(np.arctan2(p[:,1]-centre[1],p[:,0]-centre[0]))])
  ax=axs[j,i+2];im=helper.panel(ax,ps,field('fixed',t,'anomaly')[ii],norm,'RdBu_r');ax.set(title=f'{t} h | depth={depth} mm',xlim=(0,50),ylim=(-25,25),xlabel='x (mm)',ylabel='z (mm)');ax.set_aspect('equal')
 for ax in axs[j]:fig.colorbar(im,ax=ax,label='Anomaly (mol/L)',shrink=.7)
save(fig,'08_sections','Off-centre and horizontal fixed-model concentration structure','Common anomaly scale at 24 and 174 h; whole-half MRI profiles cannot validate these individual cross-sections.')
pdf.close()
thumbs=[]
for n in figures:
 im=Image.open(O/(n+'.png')).convert('RGB');im.thumbnail((800,540));tile=Image.new('RGB',(820,570),'white');tile.paste(im,((820-im.width)//2,15));ImageDraw.Draw(tile).text((12,550),n,fill='black');thumbs.append(tile)
sheet=Image.new('RGB',(1640,570*4),'white')
for i,im in enumerate(thumbs):sheet.paste(im,((i%2)*820,(i//2)*570))
sheet.save(O/'contact_sheet.png')
summary={'completion_h':174,'first_accepted_solid_h':float(g[g.salt_solid_mol>1e-12].evaporation_time_h.iloc[0]),'first_saved_solid_h':None,'solid_g':float(g.salt_solid_mol.iloc[-1]*MS),'max_solid_equivalent_volume':float(g.precip_vf_max.max()),'dissolved_g':float(g.salt_dissolved_mol.iloc[-1]*MS),'coarse_cumulative_water_share':float(g.cumulative_coarse_top_water_mol.iloc[-1]/(g.cumulative_coarse_top_water_mol.iloc[-1]+g.cumulative_fine_top_water_mol.iloc[-1])),'coarse_final_mm_day':float(g.F36_water_mm_day.iloc[-1]),'fine_final_mm_day':float(g.W3_water_mm_day.iloc[-1]),'old_new_loss_difference_at_old_end_g':float(at(of.evaporation_time_h.iloc[-1])-at(1)-oldat(of.evaporation_time_h.iloc[-1])+oldat(1)),'downflow_final':hs['fixed'].iloc[-1].to_dict(),'figures':figures,'salt_partition':saltrows}
# Saved-field times are 10-minute output times, distinct from accepted solver steps.
import xml.etree.ElementTree as ET
saved=np.array([float(e.get('timestep'))/3600-2 for e in ET.parse(D/'RH0_174h.pvd').findall('.//DataSet')]);solid=np.interp(saved,b.evaporation_time_h,b.salt_solid_mol);summary['first_saved_solid_h']=float(saved[solid>1e-12][0])
(O/'summary.json').write_text(json.dumps(summary,indent=2));(O/'artifact_checks.json').write_text(json.dumps({'numerical_checks':'passed','visual_review':'pending','pages':8,'full_window_convergence':False},indent=2))
sources=[Path(__file__),R/'finalize_extract.py',D/'budget.csv',D/'mineral_budget.csv',D/'film_budget.csv',OD/'budget.csv',OD/'film_budget.csv',P/'analysis/model_experiment_comparison_20261028/experimental_profiles.csv',oldanalysis/'full_experiment/full_experimental_mass.csv',oldanalysis/'report_rate_formula_audit.csv',R/'backup_manifest.json']
(O/'SOURCE_PINS.json').write_text(json.dumps({str(p.relative_to(P)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},indent=2))
print(metrics.to_string(index=False));print(json.dumps(summary,indent=2))
