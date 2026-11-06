"""Reduce one completed v10 run on liqin (vasca311, numpy only).
Independent raw-field band integration checked against the solver ledger,
evaporation-clock ledger time series, interface/bottom/vertical transport,
plume diagnostics and selected snapshots. Usage: extract.py <run_dir> <out_dir>"""
from pathlib import Path
import configparser,gzip,hashlib,json,sys
import xml.etree.ElementTree as ET
import numpy as np
M_NACL=58.4428e-3;M_H2O=18.01518e-3;RHO_NACL_SOLID=2165.0
PRE=7200.0;TOP=0.04;SPLIT=0.025
SIDES=['F36','W3'];INV=['0_2','2_3','3_10','10_20','20_40'];INV_EDGES=np.array([0,2,3,10,20,40.])
IFB=['0_2','2_10','10_20','20_40'];THRESHOLDS=[0.5e-8,1e-8,2e-8];SNAP_H=[0,2,4,8,12,24]
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for c in iter(lambda:f.read(1<<20),b''):h.update(c)
 return h.hexdigest()
def opener(p):
 p=Path(p);return open(p,'rb') if p.exists() else gzip.open(str(p)+'.gz','rb')
def read_vtu(p,geometry=False):
 with opener(p) as f:tree=ET.parse(f)
 out={}
 for e in tree.findall('.//CellData/DataArray'):
  a=np.array((e.text or '').split(),dtype=float);n=int(e.get('NumberOfComponents','1'));out[e.get('Name')]=a if n==1 else a.reshape(-1,n)
 if not geometry:return out
 pts=np.array(tree.find('.//Points/DataArray').text.split(),dtype=float).reshape(-1,3)
 conn=np.array(tree.find('.//Cells/DataArray[@Name="connectivity"]').text.split(),dtype=int)
 off=np.array(tree.find('.//Cells/DataArray[@Name="offsets"]').text.split(),dtype=int)
 verts=np.full((len(off),8,3),np.nan)
 for i,(lo,hi) in enumerate(zip(np.r_[0,off[:-1]],off)):verts[i,:hi-lo]=pts[conn[lo:hi]]
 return out,verts
def table(p):
 lines=Path(p).read_text().splitlines();head=lines[0].split(',');rows=[l.split(',') for l in lines[1:] if len(l.split(','))==len(head)]
 a=np.array(rows,dtype=float);return {h:a[:,i] for i,h in enumerate(head)}
def overlap(lo,hi,edges):
 return np.maximum(0,np.minimum(hi[:,None],edges[None,1:])-np.maximum(lo[:,None],edges[None,:-1]))/(hi-lo)[:,None]
def first_persistent(times,values,thr):
 ok=[i for i in range(len(values)-2) if times[i]>=.5-1e-9 and all(v>thr for v in values[i:i+3])]
 return float(times[ok[0]]) if ok else None
def main(run,out,partial=False):
 run=Path(run);out=Path(out);out.mkdir(parents=True,exist_ok=True)
 cfg=configparser.ConfigParser();cfg.optionxform=str;cfg.read(next(run.glob('*.input')));name=cfg['Problem']['Name']
 frames=[(float(d.get('timestep')),run/d.get('file')) for d in ET.parse(run/(name+'.pvd')).findall('.//DataSet')]
 frames=[(t,p) for t,p in frames if t>=PRE-1e-9]
 led=table(run/'causal_budget.csv');sw=json.loads((run/'causal_switches.json').read_text())
 seeded=(run/'seed_event.json').exists();seed=json.loads((run/'seed_event.json').read_text()) if seeded else {}
 band_imp=np.array(seed.get('band_salt_impulses_mol',np.zeros((2,5))));side_imp=np.array(seed.get('side_component_impulses_mol',np.zeros((2,3))))
 # Geometry in VTU cell order.
 f0,verts=read_vtu(frames[0][1],True);ids=np.rint(f0['dof_id']).astype(int);assert len(np.unique(ids))==len(ids)
 cg=np.loadtxt(run/'cell_geometry.csv',delimiter=',',skiprows=1);cg=cg[np.argsort(cg[:,0])][ids]
 pos,vol,ymin,ymax=cg[:,1:4],cg[:,4],cg[:,5],cg[:,6]
 assert np.max(np.abs(np.nanmin(verts[:,:,1],axis=1)-ymin))<1e-12 and np.max(np.abs(np.nanmax(verts[:,:,1],axis=1)-ymax))<1e-12
 lo=(TOP-ymax)*1000;hi=(TOP-ymin)*1000;depth=(TOP-pos[:,1])*1000
 side=np.where(pos[:,0]<=SPLIT,0,1);band=overlap(lo,hi,INV_EDGES);mm=overlap(lo,hi,np.arange(41.))
 radial=np.hypot(pos[:,0]-SPLIT,pos[:,2]);core=(radial<.020)&(np.abs(pos[:,0]-SPLIT)>.003)&(depth>5)&(depth<35)
 uy,layer=np.unique(np.round(pos[:,1],12),return_inverse=True)
 ledger_time={round(t,6):i for i,t in enumerate(led['time_s'])}
 rows=[];snaps={};errors=[];sources=[]
 for t,path in frames:
  a=read_vtu(path);assert np.array_equal(np.rint(a['dof_id']).astype(int),ids)
  th=(t-PRE)/3600;C=a['x^NaCl_liq']*a['rhoMolar_liq']/1000;theta=a['porosity']*a['S_liq'];down=-a['velocity_liq_interior_LS (m/s)'][:,1]
  pvf=a['precipitateVolumeFraction^NaCl'];assert np.max(pvf)==0,'solid salt present'
  dissolved=vol*theta*C*1000;liquid=vol*theta;water=liquid*a['rhoMolar_liq']*a['x^H2O_liq']
  i=ledger_time[round(t,6)];row={'time_s':t,'t_h':th}
  for s in range(2):
   m=side==s
   for b in range(5):
    fld=float(np.sum(band[m,b]*dissolved[m]));ref=led[f'{SIDES[s]}_salt_mol_{INV[b]}mm'][i]+(band_imp[s,b] if abs(t-PRE)<1e-6 else 0)
    errors.append(abs(fld-ref)/abs(ref));row[f'{SIDES[s]}_field_salt_g_{INV[b]}mm']=fld*M_NACL*1000
   # Plume diagnostics, same masks as v08 (core: r<20 mm, >3 mm from interface, depth 5..35 mm).
   anomaly=np.zeros_like(C)
   for l in np.unique(layer[m]):
    k=m&(layer==l);anomaly[k]=C[k]-np.average(C[k],weights=vol[k])
   for region,mask in [('all',m),('core',m&core)]:
    j=np.flatnonzero(mask);pk=j[np.argmax(down[j])]
    row[f'{SIDES[s]}_{region}_max_down_m_s']=float(down[pk]);row[f'{SIDES[s]}_{region}_max_down_depth_mm']=float(depth[pk])
    for thr in THRESHOLDS:row[f'{SIDES[s]}_{region}_descending_volume_fraction_{thr:g}']=float(np.sum(vol[mask&(down>thr)])/np.sum(vol[mask]))
    row[f'{SIDES[s]}_{region}_rms_anomaly_mol_L']=float(np.sqrt(np.average(anomaly[mask]**2,weights=vol[mask])))
    row[f'{SIDES[s]}_{region}_C_std_mol_L']=float(np.sqrt(np.cov(C[mask],aweights=vol[mask])))
   w=mm*(m*vol)[:,None];prof=(w.T@(theta*C))/(w.T@theta)
   row[f'{SIDES[s]}_profile']=prof
   ex=np.maximum(0,liquid[m]*(C[m]-1.0)*1000)
   row[f'{SIDES[s]}_excess_salt_g_over_1M']=float(np.sum(ex)*M_NACL*1000)
   row[f'{SIDES[s]}_excess_centroid_depth_mm']=float(np.sum(depth[m]*ex)/np.sum(ex)) if np.sum(ex)>0 else np.nan
   for thr in [1.05,1.1,1.5]:
    below=np.flatnonzero(prof<thr);d=0.0
    if len(below)==0:d=40.0
    elif below[0]>0:
     k=below[0];z=np.arange(40)+.5;d=float(z[k-1]+(prof[k-1]-thr)/(prof[k-1]-prof[k])*(z[k]-z[k-1]))
    row[f'{SIDES[s]}_enriched_depth_mm_{thr:g}M']=d
  rows.append(row);sources.append({'file':path.name,'time_s':t,'sha256':sha(path) if path.exists() else sha(str(path)+'.gz'),'compressed':not path.exists()})
  if any(abs(th-q)<1e-9 for q in SNAP_H):snaps[f'{th:g}h']=dict(C=C,down=down,theta=theta,S=a['S_liq'])
 # Frame table (profiles separated).
 prof=np.array([[r.pop('F36_profile'),r.pop('W3_profile')] for r in rows])
 keys=list(rows[0]);np.savetxt(out/'frames.csv',np.array([[r[k] for k in keys] for r in rows]),delimiter=',',header=','.join(keys),comments='',fmt='%.17g')
 np.savez_compressed(out/'profiles.npz',t_h=np.array([r['t_h'] for r in rows]),depth_mm=np.arange(40)+.5,pore_weighted_C_mol_L=prof,sides=np.array(SIDES))
 arrays=dict(positions=pos,volumes=vol,vertices=verts,core_mask=core,depth_mm=depth,side=side,dof_ids=ids)
 for k,v in snaps.items():
  for q,x in v.items():arrays[f'{k}_{q}']=x
 np.savez_compressed(out/'snapshots.npz',**arrays)
 th=np.array([r['t_h'] for r in rows]);persist={}
 for s in SIDES:
  for region in ['all','core']:
   for thr in THRESHOLDS:persist[f'{s}_{region}_{thr:g}']=first_persistent(th,np.array([r[f'{s}_{region}_max_down_m_s'] for r in rows]),thr)
 (out/'persistent_downflow.json').write_text(json.dumps({'rule':'first output frame (t>=0.5 h) starting 3 consecutive 10-min frames with max downward interior LS Darcy speed above threshold','first_time_h':persist},indent=2))
 # Ledger time series on the evaporation clock (every accepted step from t=0).
 i0=ledger_time[round(PRE,6)];sel=np.arange(i0,len(led['time_s']));ts={'time_s':led['time_s'][sel],'t_h':(led['time_s'][sel]-PRE)/3600}
 def since(col):return led[col][sel]-led[col][i0]
 g=lambda mol:mol*M_NACL*1000
 for s,S in enumerate(SIDES):
  for b,B in enumerate(INV):
   v=led[f'{S}_salt_mol_{B}mm'][sel].copy();v[0]+=band_imp[s,b];ts[f'{S}_salt_g_{B}mm']=g(v)
   ts[f'{S}_C_mean_mol_L_{B}mm']=led[f'{S}_dissolved_salt_mol_{B}mm'][sel]/led[f'{S}_liquid_volume_m3_{B}mm'][sel]/1000
  ts[f'{S}_salt_g_0_3mm']=ts[f'{S}_salt_g_0_2mm']+ts[f'{S}_salt_g_2_3mm']
  ts[f'{S}_C_mean_mol_L_0_3mm']=(led[f'{S}_dissolved_salt_mol_0_2mm'][sel]+led[f'{S}_dissolved_salt_mol_2_3mm'][sel])/(led[f'{S}_liquid_volume_m3_0_2mm'][sel]+led[f'{S}_liquid_volume_m3_2_3mm'][sel])/1000
  tot=led[f'{S}_salt_mol'][sel].copy();tot[0]+=side_imp[s,2];ts[f'{S}_salt_g_total']=g(tot)
  wat=led[f'{S}_water_mol'][sel].copy();wat[0]+=side_imp[s,0];ts[f'{S}_water_storage_g']=wat*M_H2O*1000
  for comp,M in [('salt',M_NACL),('water',M_H2O)]:
   ts[f'{S}_cum_bottom_{comp}_in_g']=since(f'{S}_cum_bottom_{comp}_in_mol')*M*1000
   ts[f'{S}_cum_bottom_{comp}_gross_in_g']=since(f'{S}_cum_bottom_{comp}_gross_in_mol')*M*1000
   ts[f'{S}_cum_bottom_{comp}_gross_out_g']=since(f'{S}_cum_bottom_{comp}_gross_out_mol')*M*1000
   ts[f'{S}_bottom_{comp}_in_rate_g_h']=led[f'{S}_bottom_{comp}_in_mol_s'][sel]*M*1000*3600
  ts[f'{S}_cum_evaporation_g']=since(f'{S}_cum_top_water_out_mol')*M_H2O*1000
  ts[f'{S}_evaporation_rate_g_h']=led[f'{S}_top_water_out_mol_s'][sel]*M_H2O*1000*3600
 for comp,M in [('salt',M_NACL),('water',M_H2O),('air',28.96e-3)]:
  for mode in ['adv','diff']:
   for B in IFB:
    base=f'if_{mode}_{comp}_{B}mm'
    for q in ['net','pos','neg']:ts[f'{base}_cum_{q}_g']=since(f'{base}_cum_{q}_mol')*M*1000
    ts[f'{base}_rate_g_h']=led[f'{base}_mol_s'][sel]*M*1000*3600
 for B in IFB:
  for q in ['net','pos','neg']:ts[f'if_liquid_volume_{B}mm_cum_{q}_mL']=since(f'if_liquid_volume_{B}mm_cum_{q}_m3')*1e6
 for comp in ['salt','water']:
  I=sum(ts[f'if_{m}_{comp}_{B}mm_cum_net_g'] for m in ['adv','diff'] for B in IFB);ts[f'interface_{comp}_coarse_to_fine_cum_g']=I
  for s,S in enumerate(SIDES):
   key=f'{S}_salt_g_total' if comp=='salt' else f'{S}_water_storage_g'
   dS=ts[key]-ts[key][0];Bn=ts[f'{S}_cum_bottom_{comp}_in_g'];E=ts[f'{S}_cum_evaporation_g'] if comp=='water' else 0
   ts[f'{S}_{comp}_budget_closure_g']=dS-(Bn+(I if s==1 else -I)-E)
 ts['domain_salt_g_total']=ts['F36_salt_g_total']+ts['W3_salt_g_total'];ts['domain_cum_evaporation_g']=ts['F36_cum_evaporation_g']+ts['W3_cum_evaporation_g']
 with np.errstate(invalid='ignore',divide='ignore'):ts['W3_evaporation_share']=np.where(ts['domain_cum_evaporation_g']>0,ts['W3_cum_evaporation_g']/ts['domain_cum_evaporation_g'],np.nan)
 keys=list(ts);np.savetxt(out/'timeseries.csv',np.column_stack([ts[k] for k in keys]),delimiter=',',header=','.join(keys),comments='',fmt='%.17g')
 # Conservative vertical salt transport through horizontal mesh planes, cumulative since t=0.
 vf=table(run/'vertical_salt_flux.csv');vsel=np.arange(int(np.flatnonzero(np.abs(vf['time_s']-PRE)<1e-6)[0])+1,len(vf['time_s']))
 dt=vf['dt_s'][vsel];vt={'time_s':vf['time_s'][vsel],'t_h':(vf['time_s'][vsel]-PRE)/3600}
 depths=np.array(sw['horizontal_plane_depths_m'])*1000;picks={}
 for target in [2,3,10,20]:
  k=int(np.argmin(np.abs(depths-target)));picks[target]=float(depths[k]);d=str(int(round(depths[k]*1e4)))
  for S in SIDES:
   for q,col in [('adv_net','adv_down_net'),('adv_gross_down','adv_down_gross'),('diff_net','diff_down_net')]:
    vt[f'{S}_d{target}mm_{q}_cum_g']=np.cumsum(vf[f'{S}_{col}_mol_s_d{d}'][vsel]*dt)*M_NACL*1000
 keys=list(vt);np.savetxt(out/'vertical_transport.csv',np.column_stack([vt[k] for k in keys]),delimiter=',',header=','.join(keys),comments='',fmt='%.17g')
 closure=max(float(np.max(np.abs(ts[f'{S}_{c}_budget_closure_g']))) for S in SIDES for c in ['salt','water'])
 info={'case':name,'status':'completed','seed_event_present':seeded,'frames':len(rows),'evaporation_end_h':float(th[-1]),'snapshots':list(snaps),
  'max_field_vs_ledger_band_salt_relative_error':float(max(errors)),'max_side_budget_closure_g':closure,
  'vertical_planes_used_mm':picks,'interface_enabled':sw['InterfaceExchangeEnabled'],'salinity_buoyancy_scale':sw['SalinityBuoyancyScale'],
  'script_sha256':sha(Path(__file__)),'inputs_sha256':{p:sha(run/p) for p in ['causal_budget.csv','budget.csv','vertical_salt_flux.csv','seed_event.json',name+'.pvd'] if (run/p).exists()},
  'field_sources':sources,'method':'actual cell/depth-band overlap (extruded prisms); dissolved+solid salt; solid asserted zero; evaporation clock t=time-7200 s; t=0 inventories include the seed impulse; cumulative fluxes since the accepted step at 7200 s'}
 assert info['max_field_vs_ledger_band_salt_relative_error']<1e-9,info['max_field_vs_ledger_band_salt_relative_error']
 if not partial:assert abs(th[-1]-24)<1e-9
 (out/'extraction.json').write_text(json.dumps(info,indent=2))
 print(json.dumps({k:info[k] for k in ['case','frames','max_field_vs_ledger_band_salt_relative_error','max_side_budget_closure_g']}))
if __name__=='__main__':main(sys.argv[1],sys.argv[2],len(sys.argv)>3 and sys.argv[3]=='partial')
