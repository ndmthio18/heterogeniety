from pathlib import Path
import json,subprocess,datetime,csv
R=Path(__file__).resolve().parent
code='''from pathlib import Path
import json,subprocess,shutil
r=Path('/tmp/zhixin_v13_bottom_boundary_20261103');tracks={}
for label,p in [('3D',r),('2D',r/'track2d')]:
 tracks[label]=dict(states={q.name:json.loads(q.read_text()) for q in (p/'status').glob('*.json')},runs={q.stem:json.loads(q.read_text()) for q in p.glob('*_status.json')})
print(json.dumps(dict(tracks=tracks,squeue=subprocess.check_output(['squeue','-u','zhixin','-h','-o','%i|%j|%T|%M|%C|%R'],text=True),scratch_free_GiB=shutil.disk_usage(r).free/1024**3)))
'''
p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','sal','python3 -'],input=code,capture_output=True,text=True,check=True)
d=json.loads(p.stdout)
code2=code.replace('/tmp/zhixin_v13_bottom_boundary_20261103','/temp/zhixin/v13_bottom_boundary_campaign_20261103').replace("subprocess.check_output(['squeue','-u','zhixin','-h','-o','%i|%j|%T|%M|%C|%R'],text=True)","(r/'track2d/supervisor_status.json').read_text()")
p2=subprocess.run(['ssh','-o','LogLevel=ERROR','-o','BatchMode=yes','iws_zhixin','python3 -'],input=code2,capture_output=True,text=True,check=True)
frodo=json.loads(p2.stdout);d['tracks']['2D']=frodo['tracks']['2D'];d['frodo_supervisor']=json.loads(frodo['squeue']);d['frodo_scratch_GiB']=frodo['scratch_free_GiB']
d['queried_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();(R/'TRACK_STATUS.json').write_text(json.dumps(d,indent=2))
j2=json.loads((R/'track2d/provenance/jobs.json').read_text())['jobs'];j3=json.loads((R/'deployment.json').read_text());rows=[]
for dim in ['2D','3D']:
 for case in ['B0','B1','B2','B3','G1','G2','G3']:
  t=d['tracks'][dim];key=case+('_production.json' if dim=='3D' else ('_case.json' if case.startswith('B') else '_caseG.json'));terminal=t['states'].get(key,{});run=t['runs'].get(case+'_status',{})
  job=('frodo_case_'+case if case.startswith('B') else 'frodo_caseG_'+case) if dim=='2D' else (j3['B_production_array']+'_'+case[1] if case.startswith('B') else j3['G_jobs'][case]['job_id'])
  state=terminal.get('state',run.get('state','pending_gates_resources'));error=terminal.get('error','')
  if not terminal and not run:
   if dim=='2D' and case.startswith('G') and t['states'].get('core_gatesG.json',{}).get('state')=='failed':state='blocked_failed_G_gate';error='G1_refined did not pass; production not launched'
   if dim=='3D' and case.startswith('B') and any(t['states'].get(k+'_short.json',{}).get('state')=='failed' for k in ['B0','B1','B2','B3']):state='blocked_failed_short_array';error='Full B array requires all short jobs to pass'
  rows.append(dict(dimension=dim,case=case,host='frodo' if dim=='2D' else 'sal',state=state,accepted_evaporation_h=run.get('evaporation_time_h',0),job=job,error=error))
with (R/'TRACK_RUN_STATUS.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
print(json.dumps(dict(utc=d['queried_utc'],cases=rows,gate_states={dim:{k:v['state'] for k,v in z['states'].items()} for dim,z in d['tracks'].items()},squeue=d['squeue']),indent=2))
