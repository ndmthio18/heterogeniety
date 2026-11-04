import subprocess
script = r"""
from pathlib import Path
import json,shutil,subprocess,csv
r=Path('/tmp/zhixin_sal_film_v16_20261103')
for name in ['gates_status.json','Film075mm_status.json','Film080mm_status.json']:
 p=r/name
 if p.exists():
  d=json.loads(p.read_text());d.pop('results',None);print(name,json.dumps(d))
for case in ['Film075mm','Film080mm']:
 d=r/'raw/runs'/case
 for n in ['budget.csv','thermal_budget.csv','film_budget.csv']:
  p=d/n
  if p.exists():
   with p.open() as f:
    rows=list(csv.DictReader(f))
   if rows:print(case,n,json.dumps(rows[-1]))
print('free_GiB',shutil.disk_usage(r).free/1024**3)
print(subprocess.run(['squeue','-u','zhixin'],capture_output=True,text=True).stdout)
print(subprocess.run(['pgrep','-af',str(r)],capture_output=True,text=True).stdout)
"""
subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=20','sal','python3 -'],input=script,text=True,check=True)
