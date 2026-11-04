from pathlib import Path
import subprocess,json
ROOT=Path(__file__).resolve().parent
SCRIPT=r'''from pathlib import Path
import json,shutil,os
r=Path('/home/zhixin/Documents/Cooperation_Ali/model_revisions/20261102_cylinder_thermal_v13')
s=Path('/tmp/zhixin_cylinder_thermal_v13_20261102')
d={'remote_root':str(r),'scratch_root':str(s),'scratch_free_GiB':shutil.disk_usage('/tmp').free/1024**3,'home_free_GiB':shutil.disk_usage(r).free/1024**3,'cases':{}}
for name in ['campaign_status.json','gate_summary.json','build_ni1/build_manifest.json']:
 p=r/name
 if p.exists():
  q=json.loads(p.read_text())
  d[name]=q if name!='build_ni1/build_manifest.json' else {'binary_sha256':q['binary_sha256'],'thermodynamic_test':q['thermodynamic_test']}
for p in r.glob('*_status.json'):
 if p.name=='campaign_status.json':continue
 d['cases'][p.stem]=json.loads(p.read_text())
print(json.dumps(d))
'''
def snapshot():
 p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','liqin','python3 -'],input=SCRIPT,capture_output=True,text=True,encoding='utf-8',timeout=60,check=True)
 return json.loads(p.stdout)
if __name__=='__main__':print(json.dumps(snapshot(),ensure_ascii=False,indent=2))
