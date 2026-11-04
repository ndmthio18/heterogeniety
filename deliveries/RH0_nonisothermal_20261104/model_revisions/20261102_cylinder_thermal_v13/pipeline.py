from pathlib import Path
import subprocess,json,datetime,sys
r=Path(__file__).resolve().parent
def status(state,**extra):
 (r/'campaign_status.json').write_text(json.dumps({'state':state,'updated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),**extra},indent=2))
try:
 status('building')
 subprocess.run([sys.executable,str(r/'build.py')],cwd=r,check=True,timeout=3600)
 subprocess.run([sys.executable,str(r/'campaign.py')],cwd=r,check=True)
except Exception as e:
 current=json.loads((r/'campaign_status.json').read_text())
 if current.get('state')!='failed':status('failed',pipeline_error=repr(e))
 raise
