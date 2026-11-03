"""Local, reproducible paired comparison. No fitting or temporal registration shift."""
from pathlib import Path
import hashlib,importlib.util,json,sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.colors import Normalize,TwoSlopeNorm
from pypdf import PdfReader,PdfWriter
root=Path(__file__).resolve().parent;project=root.parents[1];out=root/'results/comparison'
spec=importlib.util.spec_from_file_location('rev',root.parent/'20261028/analyze_revision.py')
rev=importlib.util.module_from_spec(spec);spec.loader.exec_module(rev)
out.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
figures=[]
def save(fig,name):
 fig.savefig(out/(name+'.png'),dpi=190);fig.savefig(out/(name+'.pdf'));plt.close(fig);figures.append(name)
def at(t,p,time,side):return np.array([np.interp(time,t,p[:,side,k]) for k in range(40)])
def section(vertices,z):
 polys=[];ids=[]
 for i,v in enumerate(vertices):
  v=v[np.isfinite(v[:,0])];lo=v[:,2].min();hi=v[:,2].max()
  if not lo-1e-12<=z<hi-1e-12:continue
  y0=v[:,1].min();y1=v[:,1].max();poly=v[np.isclose(v[:,1],y0,atol=1e-12)][:,[0,2]]
  centre=poly.mean(0);poly=poly[np.argsort(np.arctan2(poly[:,1]-centre[1],poly[:,0]-centre[0]))]
  xs=[]
  for a,b in zip(poly,np.roll(poly,-1,axis=0)):
   if abs(a[1]-z)<1e-12:xs.append(a[0])
   if (a[1]-z)*(b[1]-z)<0:xs.append(a[0]+(b[0]-a[0])*(z-a[1])/(b[1]-a[1]))
  if len(xs)>=2 and max(xs)-min(xs)>1e-10:
   left,right=np.array([min(xs),max(xs)])*1000;top,bottom=(.04-np.array([y1,y0]))*1000
   polys.append([[left,top],[right,top],[right,bottom],[left,bottom]]);ids.append(i)
 return polys,np.array(ids)
def panel(ax,polys,values,norm,cmap):
 c=PolyCollection(polys,array=values,cmap=cmap,norm=norm,edgecolors='none',rasterized=True);ax.add_collection(c);return c
def main():
 case='production24';folder=root/'results'/case
 assert json.loads((root/'runs'/case/'acceptance_gate.json').read_text())['status']=='passed'
 data=np.load(folder/'profiles.npz');s=np.load(folder/'snapshots.npz');t=data['time'];p=data['concentration'];Z=data['depth']
 reference=rev.load_profiles(root.parent/'20261028/runs/B0_24h_v03',2,'2D distributed')
 central=rev.load_profiles(root.parent/'20261029_evap_activity_v05/runs/R0_uniform',2,'2D central (previous boundary)')
 spatial2d=rev.load_profiles(root/'control2d/runs/Fourier2D',2,'2D Fourier control')
 ex=pd.read_csv(project/'analysis/model_experiment_comparison_20261028/experimental_profiles.csv')
 exp={(side,float(time)):g.sort_values('depth_center_mm').archived_concentration.to_numpy() for (side,time),g in ex.groupby(['side','time_h'])}
 models={'3D cylinder':(t,p),'2D distributed':reference[:2],'2D Fourier control':spatial2d[:2],'2D central (previous boundary)':central[:2]};metrics=[];pairs=[]
 bands={'full_0_40':(0,40),'interior_3_37':(3,37),'upper_3_10':(3,10),'deep_20_37':(20,37)}
 for model,(tt,pp) in models.items():
  for j,side in enumerate(['F36','W3']):
   for (es,time),e in exp.items():
    if es!=side or time>24:continue
    m=at(tt,pp,time,j);dm=m-at(tt,pp,0,j);de=e-exp[side,0.]
    for z,a,b in zip(Z,m,e):pairs.append(dict(model=model,side=side,time_h=time,depth_mm=z,model_mol_L=a,experiment_mol_L=b))
    for band,(lo,hi) in bands.items():
     k=(Z>=lo)&(Z<hi)
     metrics.append(dict(model=model,side=side,time_h=time,band=band,rmse_mol_L=float(np.sqrt(np.mean((m[k]-e[k])**2))),bias_mol_L=float(np.mean(m[k]-e[k])),relative_mean_bias=float(np.mean(m[k]-e[k])/np.mean(e[k])),model_change_mol_L=float(np.mean(dm[k])),experiment_change_mol_L=float(np.mean(de[k])),change_rmse_mol_L=float(np.sqrt(np.mean((dm[k]-de[k])**2)))))
 pd.DataFrame(metrics).to_csv(out/'profile_metrics.csv',index=False);pd.DataFrame(pairs).to_csv(out/'profile_pairs.csv',index=False)
 fig,axes=plt.subplots(2,4,figsize=(12,7),sharex=True,sharey=True)
 for j,side in enumerate(['F36','W3']):
  for k,time in enumerate([0,2,8,24]):
   ax=axes[j,k];ax.plot(exp[side,float(time)],Z,'o',color='.15',ms=2.8,label='Ali archived MRI profile')
   ax.plot(at(reference[0],reference[1],time,j),Z,'--',color='.45',label='2D distributed supply')
   ax.plot(at(spatial2d[0],spatial2d[1],time,j),Z,':',color='#009E73',label='2D spatial-seed control')
   ax.plot(at(t,p,time,j),Z,color='#0072B2',lw=1.8,label='3D cylinder')
   ax.axhspan(0,3,color='.94');ax.axhspan(37,40,color='.94');ax.set_title(f'{side} | {time} h');ax.grid(alpha=.15)
   ax.set_xlim(0,3.0);ax.set_xticks(np.arange(0,3.01,.5));ax.tick_params(axis='x',labelbottom=True)
   ax.set_xlabel('Solution concentration (mol/L)')
   if k==0:ax.set_ylabel('Depth below surface (mm)')
 axes[0,0].set_ylim(40,0);fig.legend(*axes[0,0].get_legend_handles_labels(),loc='lower center',ncol=4,bbox_to_anchor=(.5,.025),fontsize=8)
 fig.suptitle('Frozen materials, distributed supply: paired profile comparison')
 fig.text(.5,.008,'Whole-half profiles; nominal times; common concentration axes. MRI voxel-edge and acquisition-window effects are not reproduced.',ha='center',fontsize=8)
 fig.tight_layout(rect=(0,.07,1,.95));save(fig,'01_profiles')
 times=[4.,8.,12.,24.];verts=s['vertices'];pos=s['positions'];polys,ids=section(verts,0.)
 fullmax=max(float(s[str(tt)+'_C'].max()) for tt in times)
 anmax=max(float(np.max(abs(s[str(tt)+'_anomaly']))) for tt in times)
 cn=Normalize(1,fullmax);an=TwoSlopeNorm(vcenter=0,vmin=-anmax,vmax=anmax)
 fig,axes=plt.subplots(2,4,figsize=(12,6.4),sharex=True,sharey=True)
 for k,time in enumerate(times):
  for j,(key,norm,cmap) in enumerate([('C',cn,'viridis'),('anomaly',an,'RdBu_r')]):
   ax=axes[j,k];im=panel(ax,polys,s[str(time)+'_'+key][ids],norm,cmap);ax.axvline(25,c='.3',lw=.7)
   ax.set_xlim(0,50);ax.set_ylim(40,0);ax.set_aspect('equal');ax.set_title(f'{time:g} h');ax.set_xlabel('x (mm)')
   if k==0:ax.set_ylabel(('Concentration' if j==0 else 'Same-depth anomaly')+'\nDepth (mm)')
   if k==3:fig.colorbar(im,ax=axes[j,:],fraction=.018,pad=.02,label='mol/L')
 fig.suptitle('3D cylinder: central vertical plane (z = 0 mm)')
 fig.text(.5,.025,'Anomaly subtracts each material half’s mean at the same depth. It includes deterministic interface/wall structure.',ha='center',fontsize=8)
 fig.subplots_adjust(left=.07,right=.86,bottom=.12,top=.91,hspace=.25,wspace=.22);save(fig,'02_central_sections')
 fig,axes=plt.subplots(3,4,figsize=(12,9),sharex=True,sharey=True)
 coarse_limit=max(float(np.max(abs(s[str(tt)+'_anomaly'][pos[:,0]<.025]))) for tt in times)
 coarse_norm=TwoSlopeNorm(vcenter=0,vmin=-coarse_limit,vmax=coarse_limit)
 for j,z in enumerate([-.01,0,.01]):
  polygons,ix=section(verts,z)
  for k,time in enumerate(times):
   ax=axes[j,k];im=panel(ax,polygons,s[str(time)+'_anomaly'][ix],coarse_norm,'RdBu_r');descending=s[str(time)+'_down'][ix]>1e-8
   centres=np.array(polygons).mean(1);coarse=pos[ix,0]<.025
   mark=descending&coarse
   ax.scatter(centres[mark,0],centres[mark,1],s=2,c='k',alpha=.6,linewidths=0)
   ax.axvline(25,c='.35',lw=.6);ax.set_xlim(0,25);ax.set_ylim(40,0);ax.set_aspect('equal');ax.set_title(f'{time:g} h | z={z*1000:g} mm')
   if k==0:ax.set_ylabel('Depth (mm)')
   if j==2:ax.set_xlabel('x (mm)')
 fig.colorbar(im,ax=axes.ravel().tolist(),fraction=.018,pad=.025,label='Same-depth anomaly (mol/L)')
 fig.suptitle('Across-plane structure: coarse-sand descending cells and concentration anomalies')
 fig.text(.5,.02,'Black dots: reconstructed downward speed > 1e-8 m/s in F36. Boundary velocities are one-sided; dots are not MRI observations.',ha='center',fontsize=8)
 fig.subplots_adjust(left=.06,right=.86,bottom=.08,top=.93,hspace=.28,wspace=.18);save(fig,'03_cross_plane_instability')
 fig,axes=plt.subplots(3,3,figsize=(10,9),sharex=True,sharey=True)
 for j,targetdepth in enumerate([2,10,20]):
  ys=np.unique(pos[:,1]);y=ys[np.argmin(abs((.04-ys)*1000-targetdepth))];ix=np.where(abs(pos[:,1]-y)<1e-10)[0];polygons=[]
  for i in ix:
   v=verts[i];v=v[np.isfinite(v[:,0])];poly=v[np.isclose(v[:,1],v[:,1].min(),atol=1e-12)][:,[0,2]]*1000
   centre=poly.mean(0);polygons.append(poly[np.argsort(np.arctan2(poly[:,1]-centre[1],poly[:,0]-centre[0]))])
  for k,time in enumerate([4.,8.,24.]):
   ax=axes[j,k];im=panel(ax,polygons,s[str(time)+'_anomaly'][ix],an,'RdBu_r');ax.axvline(25,c='.3',lw=.6)
   ax.set_xlim(0,50);ax.set_ylim(-25,25);ax.set_aspect('equal');ax.set_title(f'{time:g} h | depth {(.04-y)*1000:.1f} mm')
   if k==0:ax.set_ylabel('z (mm)')
   if j==2:ax.set_xlabel('x (mm)')
 fig.colorbar(im,ax=axes.ravel().tolist(),fraction=.02,pad=.025,label='Same-depth anomaly (mol/L)')
 fig.suptitle('Horizontal sections of the full cylinder')
 fig.subplots_adjust(left=.07,right=.85,bottom=.07,top=.93,hspace=.22,wspace=.2);save(fig,'04_horizontal_sections')
 hist=pd.read_csv(folder/'spatial_history.csv');fig,axes=plt.subplots(2,2,figsize=(11,7))
 for side,color in [('F36','#0072B2'),('W3','#D55E00')]:
  axes[0,0].plot(hist.time_h,hist[side+'_core_max_down_m_s']*1e8,label=side,color=color)
  axes[0,1].plot(hist.time_h,hist[side+'_core_descending_volume_fraction']*100,label=side,color=color)
  axes[1,0].plot(hist.time_h,hist[side+'_core_rms_anomaly_mol_L'],label=side,color=color)
  axes[1,1].plot(hist.time_h,hist[side+'_salt_mol']*1000,label=side,color=color)
 axes[0,0].axhline(1,c='.3',ls=':',label='diagnostic threshold');axes[0,0].set_ylabel('Maximum downward speed (1e-8 m/s)')
 axes[0,1].set_ylabel('Core volume above threshold (%)');axes[1,0].set_ylabel('Core RMS same-depth anomaly (mol/L)');axes[1,1].set_ylabel('Dissolved salt inventory (mmol)')
 for ax in axes.ravel():ax.set_xlabel('Nominal evaporation time (h)');ax.legend();ax.grid(alpha=.2)
 fig.suptitle('Both sands: spatial diagnostics and inventories')
 fig.text(.5,.015,'Core: >5 mm from wall/top/bottom and >3 mm from interface. Threshold crossing is not a validated instability onset.',ha='center',fontsize=8)
 fig.tight_layout(rect=(0,.045,1,.95));save(fig,'05_spatial_history')
 m=pd.DataFrame(metrics);summary={'profile_24h':m[(m.time_h==24)&(m.band.isin(['interior_3_37','upper_3_10','deep_20_37']))].to_dict('records'),
 'persistent_downflow':json.loads((folder/'persistent_downflow.json').read_text()),'max_pore_vs_volume_profile_difference_mol_L':float(np.max(abs(p-data['pore_weighted']))),
 '2d_sources':reference[2],'experiment_sha256':hashlib.sha256((project/'analysis/model_experiment_comparison_20261028/experimental_profiles.csv').read_bytes()).hexdigest(),'figures':figures}
 reference_onsets={}
 for side,key in [('F36','coarse_min_vz_core_m_s'),('W3','fine_min_vz_core_m_s')]:
  frames=[f for f in reference[3] if f['time_h']>=.5]
  ii=[i for i in range(len(frames)-2) if all(f[key]<-1e-8 for f in frames[i:i+3])]
  reference_onsets[side]=frames[ii[0]]['time_h'] if ii else None
 summary['2d_core_persistent_downflow_h']=reference_onsets
 summary['previous_central_supply_sources']=central[2]
 summary['2d_fourier_sources']=spatial2d[2]
 control_onsets={}
 for side,key in [('F36','coarse_min_vz_core_m_s'),('W3','fine_min_vz_core_m_s')]:
  frames=[f for f in spatial2d[3] if f['time_h']>=.5]
  ii=[i for i in range(len(frames)-2) if all(f[key]<-1e-8 for f in frames[i:i+3])]
  control_onsets[side]=frames[ii[0]]['time_h'] if ii else None
 summary['2d_fourier_core_persistent_downflow_h']=control_onsets
 (out/'summary.json').write_text(json.dumps(summary,indent=2))
 writer=PdfWriter()
 for name in figures:writer.append(PdfReader(out/(name+'.pdf')))
 with (out/'Cylinder_3D_vs_experiment.pdf').open('wb') as f:writer.write(f)
 print(json.dumps({k:v for k,v in summary.items() if k!='2d_sources'}))
if __name__=='__main__':main()
