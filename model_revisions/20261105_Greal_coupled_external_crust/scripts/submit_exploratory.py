from pathlib import Path
import json,hashlib,shutil,subprocess,re
root=Path('/WORK/hulm_work/zhixin/Greal_external_crust_release_20261106_r02')
old=Path('/WORK/hulm_work/zhixin/Greal_experimental_bottom_hpcc_20261104')
if (root/'job.json').exists(): raise RuntimeError('Already submitted')
if shutil.disk_usage(root).free<30*1024**3: raise RuntimeError('Insufficient storage reserve')
if not (root/'runtime').exists(): (root/'runtime').symlink_to(old/'runtime',target_is_directory=True)
shutil.copy2(old/'solver_wrapper.sh',root/'solver_wrapper.sh')
(root/'solver').chmod(0o755)
run=root/'run';run.mkdir(exist_ok=False)
content=(old/'Greal-81.input').read_text().replace('Name = Greal-81','Name = Greal81_external_crust')
if re.search(r'^FaceOutputInterval\s*=',content,re.M):
    content=re.sub(r'^FaceOutputInterval\s*=.*$', 'FaceOutputInterval = 3600',content,flags=re.M)
else:
    content=content.replace('[Benchmark]','[Benchmark]\nFaceOutputInterval = 3600')
content+='\n[ExternalCrust]\nEnable = true\nAllowUnqualifiedProduction = true\nThermalResistance = false\nExternalFraction = 1\nDiffusivityRatio = 0.08\nPorosity = 0.43\nCrystalDensity = 2165\nWithinFaceCoverage = 1\n'
(run/'case.input').write_text(content)
for asset in ('filter_6layers.msh','Greal04_port.txt','water_flux_zero_storage.txt'): (run/asset).symlink_to(old/asset)
batch='#!/bin/bash\nset -euo pipefail\n/rmprog/slurm/v22.05.7/bin/srun --ntasks=1 --cpus-per-task=8 --cpu-bind=cores python3 '+str(root/'run_exploratory.py')+'\n'
(root/'run.slurm').write_text(batch)
job=subprocess.check_output(['/rmprog/slurm/v22.05.7/bin/sbatch','--parsable','--partition=cnmix','--nodes=1','--ntasks=1','--cpus-per-task=8','--time=48:00:00','--job-name=Greal_crust_174h',f'--chdir={run}','--output=slurm-%j.out',str(root/'run.slurm')],text=True).strip()
record={'job_id':job,'status':'submitted','qualification':'exploratory_user_release_not_gate_qualified','target_s':633600,'evaporation_h':174,'binary_sha256':hashlib.sha256((root/'solver').read_bytes()).hexdigest(),'input_sha256':hashlib.sha256((run/'case.input').read_bytes()).hexdigest()}
(root/'job.json').write_text(json.dumps(record,indent=2));print(json.dumps(record,indent=2))
