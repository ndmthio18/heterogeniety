"""Shared measured CPU admission: retain 3D work, prioritize eligible 2D jobs.
Only registered own held jobs are released. No other job is modified.
"""
from pathlib import Path
import json,subprocess,datetime,math
R=Path(__file__).resolve().parent
def cmd(*args):return subprocess.check_output(args,text=True)
rows=[]
for line in cmd('squeue','-h','-o','%i|%j|%T|%C|%u').splitlines():
 i,n,s,c,u=line.split('|');rows.append(dict(id=i,name=n,state=s,cpus=int(c),user=u))
ours=lambda x:x['user']=='zhixin' and x['name'].startswith(('bottom_','bottom2d_'))
unrelated=sum(x['cpus'] for x in rows if x['state'] in ['RUNNING','CONFIGURING','COMPLETING'] and not ours(x))
budget=min(8,math.floor(.7*max(0,128-unrelated)))
# Existing B arrays have throttle2 after2D moved toFrodo; already-running tasks are never stopped.
three=[x for x in rows if x['user']=='zhixin' and x['name'] in ['bottom_baseline','bottom_short','bottom_174h']]
reserve=max(4 if three else 0,sum(x['cpus'] for x in three if x['state'] in ['RUNNING','CONFIGURING','COMPLETING']))
registered=[]
def passed(path):return path.exists() and json.loads(path.read_text())['state']=='passed'
if (R/'track2d/jobs.json').exists():
 j=json.loads((R/'track2d/jobs.json').read_text())['jobs']
 for key,id in j.items():
  eligible=key=='core' or (passed(R/'track2d/status/core_core.json') if key in ['B_array','G_gates'] else passed(R/'track2d/status/core_gatesG.json'))
  registered.append((key,id,eligible,2))
for key,item in json.loads((R/'g_jobs.json').read_text()).items():registered.append(('3D_'+key,item['job_id'],key=='gates' or passed(R/'status/Gates_gates.json'),2))
items=[]
for key,id,eligible,cost in registered:
 p=subprocess.run(['scontrol','show','job',id],capture_output=True,text=True)
 if p.returncode:continue
 info=p.stdout
 if 'JobState=PENDING' not in info and 'JobState=RUNNING' not in info:continue
 held='Reason=JobHeldUser' in info or 'Priority=0 ' in info
 if not held:reserve+=cost
 items.append((key,id,eligible,cost,held))
released=[]
blocked=(R/'BLOCK_PRODUCTION.json').exists() or (R/'track2d/BLOCK_PRODUCTION.json').exists()
if not blocked:
 for key,id,eligible,cost,held in items:
  if held and eligible and reserve+cost<=budget:
   subprocess.run(['scontrol','release',id],check=True);reserve+=cost;released.append(id)
state=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),unrelated_logical_cpus=unrelated,admission_budget=budget,campaign_peak_reserved_logical_cpus=reserve,released=released,blocked=blocked,squeue=rows)
(R/'track_resource_admission.json').write_text(json.dumps(state,indent=2));print(json.dumps(state,indent=2))
