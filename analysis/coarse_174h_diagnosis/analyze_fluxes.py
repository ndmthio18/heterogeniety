"""Face-resolved signed/gross flux reduction; distinguish quadrature from accepted budgets."""
from pathlib import Path
import json
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import SymLogNorm
from matplotlib.ticker import FuncFormatter
R=Path(__file__).resolve().parent;P=R.parents[1];O=R/'results';D=R/'native_replay/full';V=P/'model_revisions/20261102_cylinder_fixed_hydraulics_v12'
check=json.loads((D/'verification.json').read_text());assert check['state']=='passed' and check['frames']==1044
h=pd.read_csv(D/'flux_history.csv');assert h.time_h.iloc[-1]==174
# The zero-time net ledger is hydrostatic; the 0h saved state follows an infinitesimal seed.
# Zero boundary flux used for quadrature only; first ten-minute unresolved evolution is not exact.
zero=h.iloc[0].copy()*0;h=pd.concat([pd.DataFrame([zero]),h],ignore_index=True)
b=pd.read_csv(V/'results/comparison/model_budget_derived.csv')
raw_budget=pd.read_csv(V/'remote_backup/runs/RH0_174h/budget.csv')
replayed=pd.read_csv(D/'replay_checks.csv');replayed['time_s']=np.rint((replayed.time_h+2)*3600)
joined=replayed.merge(raw_budget,on='time_s',suffixes=('_replay','_accepted'));assert len(joined)==1044
absolute=[]
for col in [x for x in replayed if x not in ['time_h','time_s','max_scaled_error']]:
 delta=abs(joined[col+'_replay']-joined[col+'_accepted']);i=delta.idxmax();absolute.append(dict(quantity=col,max_absolute_error=delta.max(),time_h=joined.loc[i,'time_h']))
pd.DataFrame(absolute).to_csv(O/'replay_absolute_errors.csv',index=False)
episodes=[]
for side,col in [('F36','coarse_bottom_salt_out_mol_s'),('W3','fine_bottom_salt_out_mol_s')]:
 d=raw_budget[raw_budget.evaporation_time_h>=0];mask=d[col]>1e-12;groups=(mask!=mask.shift()).cumsum()
 for _,segment in d[mask].groupby(groups[mask]):episodes.append(dict(side=side,first_accepted_positive_out_h=segment.evaporation_time_h.iloc[0],last_accepted_positive_out_h=segment.evaporation_time_h.iloc[-1],integrated_positive_net_out_mol=(segment[col]*segment.dt_s).sum(),peak_net_out_g_h=segment[col].max()*58.44*3600))
pd.DataFrame(episodes).to_csv(O/'instantaneous_net_export_episodes.csv',index=False)
seed=json.loads((V/'remote_backup/runs/RH0_174h/seed_event.json').read_text())['partition_impulses_mol']
def val(frame,col,t):return np.interp(t,frame.time_h if 'time_h' in frame else frame.evaporation_time_h,frame[col])
def integ(col,a,z,stride=1):
 d=h.iloc[::stride];tt=np.unique(np.r_[a,d.time_h[(d.time_h>a)&(d.time_h<z)],z]);yy=np.interp(tt,h.time_h,h[col]);return np.trapezoid(yy,tt*3600)
intervals=list(zip([0,24,60,84,96,120,144],[24,60,84,96,120,144,174]))+[(0,174),(120,174)]
rows=[];errors=[]
for a,z in intervals:
 adv=val(b,'cumulative_interface_adv_mol',z)-val(b,'cumulative_interface_adv_mol',a);dif=val(b,'cumulative_interface_diff_mol',z)-val(b,'cumulative_interface_diff_mol',a);inter=adv+dif
 for side,mat in [('F36',0),('W3',1)]:
  inc=val(b,'coarse_salt_mol' if mat==0 else 'fine_salt_mol',z)-val(b,'coarse_salt_mol' if mat==0 else 'fine_salt_mol',a)
  net=val(b,f'{side}_bottom_supply_mol',z)-val(b,f'{side}_bottom_supply_mol',a);ix=inter if mat==0 else -inter;imp=seed[mat] if a==0 else 0
  row=dict(start_h=a,end_h=z,side=side,accepted_salt_increase_mol=inc,accepted_bottom_net_supply_mol=net,accepted_interface_net_out_mol=ix,seed_mol=imp,accepted_closure_residual_mol=inc-net+ix-imp)
  for quantity,name in [('salt_adv_mol_s','salt_mol'),('water_adv_mol_s','water_mol'),('liquid_volume_m3_s','liquid_m3')]:
   for sgn,direction in [('neg','in'),('pos','out')]:row[f'bottom_gross_{direction}_{name}']=integ(f'bottom_{mat}_{quantity}_{sgn}',a,z)
  incoming=row['bottom_gross_in_salt_mol'];outgoing=row['bottom_gross_out_salt_mol'];row['quadrature_bottom_net_mol']=incoming-outgoing
  row['quadrature_net_error_mol']=incoming-outgoing-net
  row['gross_in_fraction_bottom_export']=outgoing/incoming if incoming>1e-14 else np.nan;row['gross_in_fraction_net_interface_export']=ix/incoming if incoming>1e-14 else np.nan;row['gross_in_fraction_retained']=inc/incoming if incoming>1e-14 else np.nan
  row['net_supply_fraction_interface_export']=ix/net if abs(net)>1e-12 else np.nan
  row['outflow_weighted_C_mol_L']=outgoing/max(row['bottom_gross_out_liquid_m3'],1e-30)/1000
  row['simultaneous_in_out_fraction_saved_frames']=float(((h.time_h>a)&(h.time_h<=z)&(h[f'bottom_{mat}_liquid_volume_m3_s_pos']>1e-16)&(h[f'bottom_{mat}_liquid_volume_m3_s_neg']>1e-16)).sum()/((h.time_h>a)&(h.time_h<=z)).sum())
  rows.append(row)
 for comp,ref in [('salt_adv_mol_s',adv),('salt_diff_mol_s',dif)]:
  c=f'interface_all_{comp}_net';q=integ(c,a,z);errors.append(dict(start_h=a,end_h=z,component=comp,accepted_net_mol=ref,replay_10min_trapezoid_mol=q,absolute_error_mol=q-ref,relative_error=abs(q-ref)/max(abs(ref),1e-15),replay_20min_mol=integ(c,a,z,2),replay_60min_mol=integ(c,a,z,6)))
pd.DataFrame(rows).to_csv(O/'bottom_interval_budgets.csv',index=False);pd.DataFrame(errors).to_csv(O/'interface_quadrature_checks.csv',index=False)
ixrows=[]
for a,z in intervals:
 r=dict(start_h=a,end_h=z)
 for q in ['salt_adv_mol_s','salt_diff_mol_s','water_adv_mol_s','water_diff_mol_s','liquid_volume_m3_s']:
  for sg,direction in [('pos','coarse_to_fine'),('neg','fine_to_coarse')]:r[q+'_'+direction]=integ('interface_all_'+q+'_'+sg,a,z)
 ixrows.append(r)
pd.DataFrame(ixrows).to_csv(O/'interface_gross_intervals.csv',index=False)
vertical=[];geometry=[]
for p in (R/'vertical_replay/pilot').glob('faces_*.csv.gz'):
 f=pd.read_csv(p);t=f.time_s.iloc[0]/3600-2
 for (y,m),d in f[f.kind==2].groupby(['y_m','material']):
  r=dict(time_h=t,height_m=y,depth_mm=(.04-y)*1000,side=['F36','W3'][m],faces=len(d),area_m2=d.area_m2.sum())
  for q in ['salt_adv_mol_s','water_adv_mol_s','liquid_volume_m3_s']:
   r[q+'_up']=d[q].clip(lower=0).sum();r[q+'_down']=-d[q].clip(upper=0).sum();r[q+'_net_up']=d[q].sum()
  vertical.append(r)
 for k in [0,1]:
  d=f[f.kind==k];area=d.area_m2.sum();expected=np.pi*.025**2/1.0016081890839748 if k==0 else .05*.04
  assert len(d)==(768 if k==0 else 960);assert abs(area/expected-1)<1e-8
  geometry.append(dict(time_h=t,kind=k,count=len(d),area_m2=area,expected_mesh_area_m2=expected))
 assert len(f[f.kind==2])==2304
pd.DataFrame(vertical).to_csv(O/'vertical_native_transport.csv',index=False);pd.DataFrame(geometry).to_csv(O/'face_geometry_checks.csv',index=False)
# Verify gross versus net implementation on a sign-changing fixture.
z=np.array([-3.,2.,-1.,4.]);assert z.clip(min=0).sum()==6 and -z.clip(max=0).sum()==4 and z.sum()==2
assert 6!=abs(z.sum())
maxclosure=max(abs(r['accepted_closure_residual_mol']) for r in rows);assert maxclosure<1e-10
(O/'flux_analysis_checks.json').write_text(json.dumps({'passed':True,'native_replay_scaled_max_error':check['max_scaled_error'],'accepted_interval_max_closure_mol':maxclosure,'gross_sign_test':'passed','face_geometry_tests':'passed: 768 bottom, 960 interface, 2304 selected horizontal faces','quadrature_note':'10-minute trapezoid is approximate. Native accepted net budgets remain authoritative. No grid/full-time-step convergence claim.'},indent=2))
# Histories: outward bottom is positive, interface positive F36->W3.
fig,ax=plt.subplots(2,2,figsize=(11,7),layout='constrained')
for mat,side in [(0,'F36'),(1,'W3')]:
 for sg,label in [('neg','in'),('pos','out')]:ax[0,mat].plot(h.time_h,h[f'bottom_{mat}_salt_adv_mol_s_{sg}']*58.44*3600,label='Gross '+label)
 ax[0,mat].plot(h.time_h,-h[f'bottom_{mat}_salt_adv_mol_s_net']*58.44*3600,'k--',label='Net supply');ax[0,mat].set(title=side+' bottom salt exchange',ylabel='NaCl (g/h)',xlabel='Time (h)');ax[0,mat].legend(fontsize=8)
for q,label in [('salt_adv_mol_s','Advection'),('salt_diff_mol_s','Diffusion')]:ax[1,0].plot(h.time_h,h[f'interface_all_{q}_net']*58.44*3600,label=label)
ax[1,0].axhline(0,color='.7',lw=.7);ax[1,0].set(ylabel='Signed salt F36 → W3 (g/h)',xlabel='Time (h)');ax[1,0].legend()
ax[1,1].plot(b.evaporation_time_h,b.coarse_salt_mol*58.44,label='F36 total');ax[1,1].plot(b.evaporation_time_h,b.fine_salt_mol*58.44,label='W3 total');ax[1,1].set(ylabel='Salt inventory (g)',xlabel='Time (h)');ax[1,1].legend()
fig.savefig(O/'05_native_flux_histories.png',dpi=180);fig.savefig(O/'05_native_flux_histories.pdf');plt.close(fig)
fig,ax=plt.subplots(3,4,figsize=(13,9),layout='constrained')
for j,t in enumerate([24,84,120,174]):
 f=pd.read_csv(D/f'faces_{t:06.1f}h.csv.gz');d=f[f.kind==0];q=d.salt_adv_mol_s/d.area_m2*58.44*3600
 im=ax[0,j].scatter(d.x_m*1000,d.z_m*1000,c=q,cmap='RdBu_r',norm=SymLogNorm(linthresh=3,vmin=-300,vmax=300),s=12);ax[0,j].axvline(25,color='k',lw=.5);ax[0,j].set(title=f'{t} h: bottom, + out',xlabel='x (mm); F36 left / W3 right',ylabel='z (mm)',aspect='equal')
 d=f[f.kind==1]
 for i,qname in [(1,'salt_adv_mol_s'),(2,'salt_diff_mol_s')]:
  limit=30 if i==1 else 30;q=d[qname]/d.area_m2*58.44*3600
  im2=ax[i,j].scatter(d.z_m*1000,(.04-d.y_m)*1000,c=q,cmap='RdBu_r',norm=SymLogNorm(linthresh=1,vmin=-110,vmax=110),s=10);ax[i,j].set(xlabel='z (mm)',ylabel=('Advection' if i==1 else 'Diffusion')+'\nDepth (mm)');ax[i,j].invert_yaxis()
fmt=FuncFormatter(lambda x,pos:f'{x:g}')
fig.colorbar(im,ax=ax[0,:],label='Bottom (g m⁻² h⁻¹)\nSymLog threshold 3',shrink=.7,ticks=[-300,-30,-3,0,3,30,300],format=fmt);fig.colorbar(im2,ax=ax[1:,:],label='Interface, + F36→W3 (g m⁻² h⁻¹)\nSymLog threshold 1',shrink=.7,ticks=[-100,-10,-1,0,1,10,100],format=fmt)
fig.savefig(O/'06_native_flux_maps.png',dpi=180,bbox_inches='tight');fig.savefig(O/'06_native_flux_maps.pdf',bbox_inches='tight');plt.close(fig)
print('Flux analysis accepted; max interval closure',maxclosure)
