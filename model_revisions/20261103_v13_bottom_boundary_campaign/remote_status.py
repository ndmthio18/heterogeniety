from pathlib import Path
import subprocess,json,datetime,csv,io
R=Path(__file__).resolve().parent;remote='/tmp/zhixin_v13_bottom_boundary_20261103'
code='''from pathlib import Path
import json,subprocess,shutil
r=Path("/tmp/zhixin_v13_bottom_boundary_20261103")
states={p.name:json.loads(p.read_text()) for p in (r/"status").glob("*.json")}
latest={}
for p in r.glob("*_status.json"):
 try:latest[p.name]=json.loads(p.read_text())
 except Exception:pass
print(json.dumps(dict(states=states,solver_states=latest,scratch_free_GiB=shutil.disk_usage(r).free/1024**3,squeue=subprocess.check_output(["squeue","-u","zhixin","-h","-o","%i|%j|%T|%M|%C|%R"],text=True))))
'''
p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','sal','python3 -'],input=code,capture_output=True,text=True,check=True);d=json.loads(p.stdout);d['queried_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();(R/'remote_status_latest.json').write_text(json.dumps(d,indent=2))
deployment=json.loads((R/'deployment.json').read_text())
rows=[]
for name in ['B0','B1','B2','B3','G1','G2','G3']:
 terminal=d['states'].get(name+'_production.json',{});live=d['solver_states'].get(name+'_status.json',{});rows.append(dict(case=name,state=terminal.get('state',live.get('state','pending_gates')),evaporation_h=live.get('evaporation_time_h',0),job=terminal.get('job',deployment['B_production_array']+'_'+name[1:] if name.startswith('B') else deployment['G_jobs'][name]['job_id']),error=terminal.get('error','')))
with (R/'RUN_STATUS.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
print(json.dumps(dict(cases=rows,gate_states={k:v['state'] for k,v in d['states'].items() if not k.endswith('_production.json')},scratch_free_GiB=d['scratch_free_GiB'],squeue=d['squeue']),indent=2))
