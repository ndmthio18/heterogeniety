"""Read selected ASCII native VTK arrays on HPCC without extra raw copies."""
from pathlib import Path
import argparse,xml.etree.ElementTree as ET,hashlib,json
import numpy as np
import pandas as pd
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();rows=[];hashes={}
for case in ['Greal-81','Greal-75']:
 datasets=ET.parse(a.source/case/f'{case}.pvd').findall('.//DataSet')
 for th in [0,1,2,4,12,24,60,72,84,96,108,120,144,174]:
  matches=[d for d in datasets if abs(float(d.attrib['timestep'])-(th*3600+7200))<1e-6]
  assert len(matches)==1, (case,th,'missing or ambiguous PVD time')
  path=a.source/case/matches[0].attrib['file'];raw=path.read_bytes();hashes[str(path)]=hashlib.sha256(raw).hexdigest();tree=ET.fromstring(raw)
  arr={e.attrib['Name']:np.fromstring(e.text,sep=' ') for e in tree.iter('DataArray')}
  pts=arr['Coordinates'].reshape(-1,3);conn=arr['connectivity'].astype(int);off=arr['offsets'].astype(int)
  starts=np.r_[0,off[:-1]];centers=np.array([pts[conn[l:r]].mean(axis=0) for l,r in zip(starts,off)])
  ymin=np.array([pts[conn[l:r],1].min() for l,r in zip(starts,off)]);ymax=np.array([pts[conn[l:r],1].max() for l,r in zip(starts,off)])
  solid=arr['precipitateVolumeFraction^NaCl'];top=np.isclose(ymax,.04,atol=1e-10,rtol=0)
  for side,mask in [('F36',centers[:,0]<=.025),('W3',centers[:,0]>.025)]:
   mask=mask&(centers[:,1]>=0);z=mask&top;pos=mask&(solid>1e-12)
   rows.append({'case':case,'time_h':th,'side':side,'top_cell_count':int(z.sum()),'top_T_min_K':float(arr['T'][z].min()),'top_T_max_K':float(arr['T'][z].max()),'positive_solid_cell_count':int(pos.sum()),'positive_solid_max_depth_mm':float((.04-ymin[pos]).max()*1000) if pos.any() else None,'positive_solid_min_depth_mm':float((.04-ymax[pos]).min()*1000) if pos.any() else None,'max_equivalent_solid_VF':float(solid[mask].max())})
pd.DataFrame(rows).to_csv(a.out/'selected_native_fields.csv',index=False)
(a.out/'selected_native_hashes.json').write_text(json.dumps(hashes,indent=2));print(pd.DataFrame(rows).tail(4).to_string(index=False))
