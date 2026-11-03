"""Read independently accepted v13 archive. No recalibration or trajectory mixing."""
from pathlib import Path
import json,tarfile,hashlib,gzip,xml.etree.ElementTree as ET
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parent;P=R.parents[1];O=R/'results'
V=P/'model_revisions/20261102_cylinder_thermal_v13';B=P/'model_revisions/20261102_cylinder_fixed_hydraulics_v12'
manifest=json.loads((V/'final_174h_manifest.json').read_text())['files'];status=json.loads((V/'final_delivery_status.json').read_text());assert status['stage']=='verified'
tar=tarfile.open(V/'final_174h_delivery.tar');members={x.name:x for x in tar.getmembers()};base='raw/runs/RH0_174h/'
verified=[]
def read(name):
 b=tar.extractfile(members[name]).read();h=hashlib.sha256(b).hexdigest();assert h==manifest[name]['sha256'];verified.append({'member':name,'sha256':h});return b
pvd=ET.fromstring(read(base+'RH0_174h.pvd'));entries={round(float(e.get('timestep'))/3600-2,8):e.get('file')+'.gz' for e in pvd.findall('.//DataSet')}
import io
g=pd.read_csv(io.BytesIO(read(base+'cell_geometry.csv'))).set_index('dof')
exp=pd.read_csv(R/'results/profile_pairs.csv');rows=[];profiles=[]
for t in [24,60,84,96,120,144,174]:
 root=ET.fromstring(gzip.decompress(read(base+entries[t])));a={el.get('Name'):np.fromstring(el.text or '',sep=' ') for el in root.findall('.//CellData/DataArray') if el.get('NumberOfComponents','1')=='1'}
 ids=np.rint(a['dof_id']).astype(int);geom=g.loc[ids];low=(.04-geom.ymax_m.to_numpy())*1000;high=(.04-geom.ymin_m.to_numpy())*1000;vol=geom.volume_m3.to_numpy();C=a['x^NaCl_liq']*a['rhoMolar_liq']/1000
 for side,mask in [('F36',geom.x_m.to_numpy()<.025),('W3',geom.x_m.to_numpy()>.025)]:
  c=[]
  for d in range(40):
   weights=np.maximum(0,np.minimum(high,d+1)-np.maximum(low,d))/(high-low)*vol*mask;c.append(np.average(C,weights=weights));profiles.append(dict(time_h=t,side=side,depth_mm=d+.5,v13_C_mol_L=c[-1]))
  c=np.array(c);ex=exp[(exp.side==side)&(exp.time_h==t)].sort_values('depth_mm').MRI_archived_M.to_numpy();err=c[3:37]-ex[3:37]
  rows.append(dict(time_h=t,side=side,mean_C_mol_L=c[3:37].mean(),bias_mol_L=err.mean(),RMSE_mol_L=np.sqrt(np.mean(err**2))))
pd.DataFrame(rows).to_csv(O/'thermal_profile_metrics.csv',index=False);pd.DataFrame(profiles).to_csv(O/'thermal_profiles.csv',index=False)
(O/'thermal_member_verification.json').write_text(json.dumps({'parent_archive_verification':status,'read_members_verified_now':verified,'revision':'v13, independent nonisothermal trajectory; not v12 replay'},indent=2))
mass=pd.read_csv(P/'analysis/rh0_evaporation_65h_20261102/full_experiment/full_experimental_mass.csv');mass=mass[mass.time_h<=174];intervals=[];hist=[]
fig,ax=plt.subplots(2,2,figsize=(11,7),layout='constrained')
ax[0,0].plot(mass.time_h,mass.solution_loss_since_1h_g,'ko',ms=3,label='Weighing: solution loss')
for label,rev,folder in [('v12 isothermal',B,B/'remote_backup/runs/RH0_174h'),('v13 nonisothermal',V,V/'results')]:
 f=pd.read_csv(folder/'film_budget.csv');b=pd.read_csv(folder/'budget.csv');mi=pd.read_csv(folder/'mineral_budget.csv');f=f[f.evaporation_time_h>=0];b=b[b.evaporation_time_h>=0];mi=mi[mi.evaporation_time_h>=0]
 t=f.evaporation_time_h.to_numpy();loss=f.cumulative_reservoir_loss_g.to_numpy();loss-=np.interp(1,t,loss)
 ax[0,0].plot(t,loss,label=label)
 for left,right,m0,m1 in zip(mass.time_h.iloc[:-1],mass.time_h.iloc[1:],mass.solution_loss_since_1h_g.iloc[:-1],mass.solution_loss_since_1h_g.iloc[1:]):
  rate=(np.interp(right,t,loss)-np.interp(left,t,loss))/(right-left);er=(m1-m0)/(right-left);intervals.append(dict(model=label,start_h=left,end_h=right,experimental_rate_g_h=er,model_rate_g_h=rate));ax[0,1].plot([left,right],[rate,rate],color='C0' if label.startswith('v12') else 'C1',lw=1.4)
 if label.startswith('v12'):
  for left,right,m0,m1 in zip(mass.time_h.iloc[:-1],mass.time_h.iloc[1:],mass.solution_loss_since_1h_g.iloc[:-1],mass.solution_loss_since_1h_g.iloc[1:]):ax[0,1].plot([left,right],[(m1-m0)/(right-left)]*2,color='k',lw=1)
 ax[1,0].plot(mi.evaporation_time_h,mi.salt_solid_mol*58.44,label=label)
 share=b.coarse_top_water_out_mol_s/(b.coarse_top_water_out_mol_s+b.fine_top_water_out_mol_s)
 ax[1,1].plot(b.evaporation_time_h,share,label=label)
 for t0 in [24,60,84,96,120,144,174]:
  br=b.iloc[np.argmin(abs(b.evaporation_time_h-t0))];hist.append(dict(model=label,time_h=t0,coarse_top_water_share=float(share.loc[br.name]),coarse_salt_mol=br.coarse_salt_mol,fine_salt_mol=br.fine_salt_mol,net_interface_coarse_to_fine_mol=br.cumulative_interface_adv_mol+br.cumulative_interface_diff_mol))
ax[0,0].set(title='Independent trajectories; same 8.100162 mm film',ylabel='1h-anchored solution loss (g)',xlabel='Nominal evaporation time (h)');ax[0,0].legend(fontsize=8)
ax[0,1].set(title='Black: experiment; blue: v12; orange: v13',ylabel='Interval solution-loss rate (g/h)',xlabel='Nominal evaporation time (h)')
ax[1,0].set(ylabel='Solid NaCl-equivalent inventory (g)',xlabel='Evaporation time (h)');ax[1,0].legend(fontsize=8)
ax[1,1].set(ylabel='F36 fraction of top water evaporation',xlabel='Evaporation time (h)',ylim=(.45,.65));ax[1,1].legend(fontsize=8)
fig.savefig(O/'04_thermal_and_evaporation.png',dpi=180);fig.savefig(O/'04_thermal_and_evaporation.pdf');plt.close(fig)
pd.DataFrame(intervals).to_csv(O/'thermal_evaporation_intervals.csv',index=False);pd.DataFrame(hist).to_csv(O/'thermal_inventory_partition.csv',index=False)
print('Verified',len(verified),'v13 archive members; comparison complete')
