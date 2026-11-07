"""Run on Frodo: capture complete CSV lines, trim to a shared accepted time."""
from pathlib import Path
import csv,io,json,hashlib,tarfile,datetime
root=Path('/temp/zhixin/Greal_external_crust_174h_frodo_20261106')
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
out=root/('analysis_snapshot_'+stamp);out.mkdir()
names=['film_budget','budget','thermal_budget','mineral_budget','material_budgets','depth_profiles_compact','crust_budget']
tables={}
for name in names:
 raw=(root/'run'/(name+'.csv')).read_bytes();raw=raw[:raw.rfind(b'\n')+1]
 reader=csv.DictReader(io.StringIO(raw.decode())); rows=list(reader)
 tables[name]=(reader.fieldnames,rows)
cutoff=min(max(float(r['time_s']) for r in rows) for _,rows in tables.values())
for name,(fields,rows) in tables.items():
 with (out/(name+'.csv')).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(r for r in rows if float(r['time_s'])<=cutoff)
manifest={'snapshot_utc':stamp,'source':str(root/'run'),'accepted_time_s':cutoff,'evaporation_h':(cutoff-7200)/3600,'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.csv')}}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2))
archive=out.with_suffix('.tar.gz')
with tarfile.open(archive,'w:gz') as t:
 for p in out.iterdir():t.add(p,arcname=p.name)
print(json.dumps({'archive':str(archive),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'manifest':manifest}),flush=True)
