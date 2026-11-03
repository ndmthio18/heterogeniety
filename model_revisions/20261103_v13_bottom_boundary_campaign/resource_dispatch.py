"""Lightweight Slurm admission check. Never changes other users' jobs.
Release only this campaign's explicitly registered held G jobs when capacity permits.
"""
from pathlib import Path
import subprocess,json,datetime,math
R=Path(__file__).resolve().parent
def cmd(*args):return subprocess.check_output(args,text=True)
rows=[]
for line in cmd('squeue','-h','-o','%i|%j|%T|%C|%u').splitlines():
 ident,name,state,cpus,user=line.split('|');rows.append(dict(id=ident,name=name,state=state,cpus=int(cpus),user=user))
node=cmd('scontrol','show','node','localhost');total=int(next(x.split('=')[1] for x in node.split() if x.startswith('CPUTot=')))
unrelated=sum(x['cpus'] for x in rows if x['state'] in ['RUNNING','COMPLETING','CONFIGURING'] and not(x['user']=='zhixin' and x['name'].startswith('bottom_')))
budget=min(8,math.floor(.7*max(0,total-unrelated)))
# B array can use two physical cores, each allocated two SMT CPUs. Reserve its peak while it remains active/pending.
reserve=4 if any(x['name'] in ['bottom_short','bottom_174h','bottom_baseline'] for x in rows) else 0
released=[];registry=R/'g_jobs.json'
if registry.exists() and not (R/'BLOCK_PRODUCTION.json').exists():
 jobs=json.loads(registry.read_text())
 for key,item in jobs.items():
  info=cmd('scontrol','show','job',item['job_id'])
  if 'JobState=PENDING' not in info and 'JobState=RUNNING' not in info:continue
  held='Reason=JobHeldUser' in info or 'Priority=0 ' in info
  if not held:reserve+=2;continue
  # G production stays held until G gates have actually passed (not merely queued).
  gate=R/'status/Gates_gates.json'
  if key!='gates' and (not gate.exists() or json.loads(gate.read_text())['state']!='passed'):continue
  if reserve+2<=budget:
   subprocess.run(['scontrol','release',item['job_id']],check=True);reserve+=2;released.append(item['job_id'])
state=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),total_logical_cpus=total,unrelated_allocated_cpus=unrelated,initial_70percent_admission_budget=budget,campaign_peak_reserved_cpus=reserve,released_jobs=released,jobs=rows,note='Single-thread processes; SMT allocation counts twice. Scheduler controls placement; no unrelated jobs modified.')
(R/'resource_admission.json').write_text(json.dumps(state,indent=2));print(json.dumps(state,indent=2))
