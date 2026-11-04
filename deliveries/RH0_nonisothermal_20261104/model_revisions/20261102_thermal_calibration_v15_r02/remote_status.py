import subprocess
root='/temp/zhixin/heterogeneity_thermal_calibration_v15_r02_20261102'
script="""from pathlib import Path
import json,shutil,subprocess
r=Path(ROOT)
for name in ['calibration_status.json','deployment.json','gate_summary.json','build_ni1/build_manifest.json']:
 p=r/name
 if p.exists():
  d=json.loads(p.read_text())
  if name.endswith('build_manifest.json'):d={k:d[k] for k in ['binary_sha256','threads','cpu_set']}
  if name=='gate_summary.json':d={k:v for k,v in d.items() if k!='gates'}
  print(name,json.dumps(d))
states=sorted(r.glob('*_status.json'),key=lambda p:p.stat().st_mtime)
for p in states[-3:]:print(p.name,p.read_text())
print('free_GiB',shutil.disk_usage(r).free/1024**3)
print(subprocess.run(['pgrep','-af',str(r)],capture_output=True,text=True).stdout)
""".replace('ROOT',repr(root))
subprocess.run(['ssh','-o','LogLevel=ERROR','-o','BatchMode=yes','iws_zhixin','python3 -'],input=script,text=True,check=True)
