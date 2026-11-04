from pathlib import Path
import subprocess,re,shutil,hashlib,json,tarfile
parent=Path('/temp/zhixin/heterogeneity_thermal_calibration_v15_r02_20261102')
r=Path('/temp/zhixin/heterogeneity_sal_v16_stage_20261103');r.mkdir(exist_ok=False)
for name in ['source','inputs']:shutil.copytree(parent/name,r/name)
for name in ['runner.py','experiment.csv']:shutil.copy2(parent/name,r/name)
shutil.copytree(parent/'build_ni1',r/'parent_build')
shutil.copy2(parent/'raw/runs/Regression_equilibrium/budget.csv',r/'reference_budget.csv')
shutil.copy2(parent/'raw/runs/Regression_equilibrium/thermal_budget.csv',r/'reference_thermal.csv')
lib=r/'runtime/lib';lib.mkdir(parents=True)
plugins=Path('/usr/lib/x86_64-linux-gnu/openmpi/lib/openmpi3')
shutil.copytree(plugins,r/'runtime/plugins',symlinks=False)
shutil.copytree('/usr/share/openmpi',r/'runtime/share/openmpi',symlinks=False)
paths=[parent/'build_ni1/heterogeneity_revised']+list(plugins.glob('*.so'))
deps={}
for p in paths:
 out=subprocess.run(['ldd',str(p)],capture_output=True,text=True).stdout
 for path in re.findall(r'(\/[^\s()]+)',out):
  a=Path(path)
  if a.is_file():
   if a.name in deps:assert deps[a.name].read_bytes()==a.read_bytes()
   deps[a.name]=a
for name,p in deps.items():shutil.copy2(p,lib/name)
manifest={p.relative_to(r).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in r.rglob('*') if p.is_file()}
(r/'staging_manifest.json').write_text(json.dumps(manifest,indent=2))
with tarfile.open(str(r)+'.tar.gz','w:gz') as t:t.add(r,arcname='.')
print(hashlib.sha256(Path(str(r)+'.tar.gz').read_bytes()).hexdigest())
