"""Verify the completed archive and reduce native fields without modifying any run."""
from pathlib import Path
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
import json,hashlib,gzip,xml.etree.ElementTree as ET,datetime
import numpy as np
import pandas as pd
R=Path(__file__).resolve().parent; P=R.parents[1]; O=R/'results/comparison'; O.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(p,geometry=False):
 raw=gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes()
 tree=ET.fromstring(raw);a={}
 for e in tree.findall('.//CellData/DataArray'):
  x=np.fromstring(e.text or '',sep=' ');n=int(e.get('NumberOfComponents','1'));a[e.get('Name')]=x if n==1 else x.reshape(-1,n)
 if not geometry:return a
 pts=np.fromstring(tree.find('.//Points/DataArray').text,sep=' ').reshape(-1,3)
 c=np.fromstring(tree.find('.//Cells/DataArray[@Name="connectivity"]').text,sep=' ',dtype=int)
 ends=np.fromstring(tree.find('.//Cells/DataArray[@Name="offsets"]').text,sep=' ',dtype=int)
 verts=np.full((len(ends),8,3),np.nan)
 for i,(lo,hi) in enumerate(zip(np.r_[0,ends[:-1]],ends)):verts[i,:hi-lo]=pts[c[lo:hi]]
 return a,verts
def verify():
 manifest=json.loads((R/'backup_manifest.json').read_text()); rows=manifest['verified_files']
 assert len(rows)==manifest['listed_files']
 for f in rows:assert sha(R/'remote_backup'/f['local'])==f['sha256'],f['local']
 folder=R/'remote_backup/runs/RH0_174h';fields=[json.loads(x) for x in (folder/'compressed_fields.jsonl').read_text().splitlines()]
 for f in fields:
  raw=gzip.decompress((folder/f['file']).read_bytes());assert hashlib.sha256(raw).hexdigest()==f['raw_sha256'];assert len(raw)==f['raw_bytes']
 datasets=ET.parse(folder/'RH0_174h.pvd').findall('.//DataSet')
 assert {e.get('file')+'.gz' for e in datasets}=={f['file'] for f in fields}
 assert float(datasets[-1].get('timestep'))==633600
 status=json.loads((R/'remote_backup/remote_metadata/RH0_174h_status.json').read_text())
 assert status['state']=='completed' and status['acceptance']['status']=='passed' and status['evaporation_time_h']==174
 result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'verified_files':len(rows),'verified_raw_fields':len(fields),'last_raw_field':datasets[-1].attrib,'status':status,'backup_manifest_sha256':sha(R/'backup_manifest.json')}
 (O/'terminal_verification.json').write_text(json.dumps(result,indent=2));print('Terminal archive verified',len(rows),len(fields),flush=True)
def extract(label,folder):
 dest=O/label;dest.mkdir(exist_ok=True)
 entries=ET.parse(folder/'RH0_174h.pvd').findall('.//DataSet')
 wanted=[0,2,4,24,57.5,60,65+1/6,96,108,174]
 entries=[e for e in entries if (float(e.get('timestep'))/3600-2)>=0 and ((float(e.get('timestep'))/3600-2)<=4 or abs((float(e.get('timestep'))/3600-2)%1)<1e-9 or any(abs(float(e.get('timestep'))/3600-2-t)<1e-8 for t in wanted))]
 def path(e):
  p=folder/e.get('file');return p if p.exists() else Path(str(p)+'.gz')
 a,verts=read(path(entries[0]),True);ids=np.rint(a['dof_id']).astype(int)
 g=pd.read_csv(folder/'cell_geometry.csv').set_index('dof').loc[ids];pos=g[['x_m','y_m','z_m']].to_numpy();vol=g.volume_m3.to_numpy();depth=(.04-pos[:,1])*1000
 lo=(.04-g.ymax_m.to_numpy())*1000;hi=(.04-g.ymin_m.to_numpy())*1000
 overlap=np.maximum(0,np.minimum(hi[None,:],np.arange(1,41)[:,None])-np.maximum(lo[None,:],np.arange(40)[:,None]))
 masks=[pos[:,0]<.025,pos[:,0]>.025];weights=[overlap/(hi-lo)[None,:]*vol*m for m in masks];weights=[w/w.sum(axis=1)[:,None] for w in weights]
 core=(np.hypot(pos[:,0]-.025,pos[:,2])<.020)&(np.abs(pos[:,0]-.025)>.003)&(depth>5)&(depth<35)
 _,layers=np.unique(np.round(pos[:,1],12),return_inverse=True)
 budgets=pd.read_csv(folder/'budget.csv').set_index('time_s');mineral=pd.read_csv(folder/'mineral_budget.csv').set_index('time_s');seed=json.loads((folder/'seed_event.json').read_text())
 times=[];profiles=[];hist=[];sources=[];errors=[];snap={'positions':pos,'volumes':vol,'vertices':verts,'depth':depth,'dof_ids':ids,'core_mask':core}
 for e in entries:
  ts=float(e.get('timestep'));t=ts/3600-2;p=path(e);a=read(p);assert np.array_equal(np.rint(a['dof_id']).astype(int),ids)
  C=a['x^NaCl_liq']*a['rhoMolar_liq']/1000;down=-a['velocity_liq_interior_LS (m/s)'][:,1];theta=a['porosity']*a['S_liq'];anomaly=C.copy()
  if label=='fixed':
   assert np.max(abs(a['porosity']-np.where(masks[0],.40,.36)))<1e-12
   assert np.max(abs(a['Permeability']/np.where(masks[0],7.819185772155931e-12,3.2034098778596945e-14)-1))<1e-12
  row={'time_h':t};br=budgets.loc[ts];mr=mineral.loc[ts]
  for j,(side,mask) in enumerate(zip(['F36','W3'],masks)):
   for l in np.unique(layers):
    mm=mask&(layers==l);anomaly[mm]-=np.average(C[mm],weights=vol[mm])
   for region,mm in [('all',mask),('core',mask&core)]:
    row[f'{side}_{region}_max_down_m_s']=float(down[mm].max())
    row[f'{side}_{region}_descending_volume_fraction']=float(vol[mm&(down>1e-8)].sum()/vol[mm].sum())
    row[f'{side}_{region}_rms_anomaly_mol_L']=float(np.sqrt(np.average(anomaly[mm]**2,weights=vol[mm])))
   dissolved=float(np.sum(vol[mask]*theta[mask]*C[mask])*1000);solid=float(mr['coarse_solid_mol' if j==0 else 'fine_solid_mol']);target=float(br['coarse_salt_mol' if j==0 else 'fine_salt_mol'])
   if abs(t)<1e-8:target+=seed['partition_impulses_mol'][j]
   errors.append(abs(dissolved+solid-target)/max(abs(target),1e-12));row[f'{side}_dissolved_mol']=dissolved
  times.append(t);profiles.append(np.array([w@C for w in weights]));hist.append(row)
  if any(abs(t-w)<1e-8 for w in wanted):
   for k,v in {'C':C,'down':down,'anomaly':anomaly,'theta':theta,'S':a['S_liq'],'solid_equiv':a['precipitateVolumeFraction^NaCl']}.items():snap[f'{t:.6f}_{k}']=v
  sources.append({'file':p.name,'time_h':t,'sha256':sha(p)})
 assert max(errors)<1e-9,max(errors)
 np.savez_compressed(dest/'profiles.npz',time=times,depth=np.arange(40)+.5,concentration=profiles)
 np.savez_compressed(dest/'snapshots.npz',**snap);pd.DataFrame(hist).to_csv(dest/'spatial_history.csv',index=False)
 (dest/'extraction.json').write_text(json.dumps({'frames':len(times),'max_field_budget_salt_relative_error':max(errors),'sampling':'all saved frames 0-4h; hourly thereafter plus exact comparison snapshots; no persistent-onset estimation','sources':sources},indent=2))
 print(label,'extracted',len(times),'fields; salt error',max(errors),flush=True)
if __name__=='__main__':
 verify()
 extract('fixed',R/'remote_backup/runs/RH0_174h')
 extract('coupled',R.parent/'20261030_cylinder_precip_v09_r02/remote_backup/runs/RH0_174h')
