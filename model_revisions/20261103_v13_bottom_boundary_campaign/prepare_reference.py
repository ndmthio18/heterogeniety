"""Rebuild regression NPZs from the separately preserved accepted-v13 archive."""
from pathlib import Path
import sys,tarfile,json,hashlib,gzip,xml.etree.ElementTree as ET
import numpy as np
R=Path(__file__).resolve().parent;out=R/'baseline_reference'
archive=Path(sys.argv[1]);manifest={x['member']:x['sha256'] for x in json.loads((out/'member_hashes.json').read_text())}
with tarfile.open(archive) as t:
 def read(name):
  data=t.extractfile(name).read();assert hashlib.sha256(data).hexdigest()==manifest[name],name;return data
 prefix='raw/runs/RH0_174h/'
 pvd=ET.fromstring(read(prefix+'RH0_174h.pvd'))
 for seconds in [0,7200,7800,93600,223200,309600,352800,439200,525600,633600]:
  file=next(e.get('file') for e in pvd.findall('.//DataSet') if abs(float(e.get('timestep'))-seconds)<1e-7)
  root=ET.fromstring(gzip.decompress(read(prefix+file+'.gz')))
  a={e.get('Name'):np.fromstring(e.text or '',sep=' ') for e in root.findall('.//CellData/DataArray') if e.get('NumberOfComponents','1')=='1'}
  order=np.argsort(a['dof_id']);np.savez_compressed(out/f'fields_{seconds}.npz',**{k:v[order] for k,v in a.items()})
 for name in ['budget.csv','thermal_budget.csv','film_budget.csv','mineral_budget.csv','cell_geometry.csv']:(out/name).write_bytes(read(prefix+name))
print('Verified archive members and rebuilt ten scalar-field references; no simulation restarted.')
