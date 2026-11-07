"""Submit only integration gates, never the 174h production calculation."""
from pathlib import Path
import json,hashlib,subprocess,shutil
base=Path('/WORK/hulm_work/zhixin/Greal_coupled_external_crust_20261105')
root=base/'enabled_r01'
old=Path('/WORK/hulm_work/zhixin/Greal_experimental_bottom_hpcc_20261104')
if (root/'jobs.json').exists(): raise RuntimeError('Submission already recorded')
if not json.loads((base/'c0_comparison.json').read_text())['passed']: raise RuntimeError('C0 missing')
if shutil.disk_usage(root).free<30*1024**3: raise RuntimeError('Capacity reserve')
if not (root/'runtime').exists(): (root/'runtime').symlink_to(old/'runtime',target_is_directory=True)
for name in ('solver_wrapper.sh','run_case.slurm'): shutil.copy2(old/name,root/name)
(root/'solver').chmod(0o755)
jobs={}
for name,enabled,end,extra in [('Disabled_r01',False,7800,''),('Enabled_zero',True,7800,''),('Enabled_solid_closed',True,15,'\nRevision.ClosedReactionTest = true\n')]:
    out=root/'gates'/name; out.mkdir(parents=True,exist_ok=False)
    content=(old/'Greal-81.input').read_text().replace('TEnd = 633600',f'TEnd = {end}')
    if end==15:
        content=content.replace('PerturbationStd = 1e-05','PerturbationStd = 0').replace('[Revision]','[Revision]\nClosedReactionTest = true')
    content+='\n[ExternalCrust]\nEnable = '+str(enabled).lower()+'\nThermalResistance = false\nExternalFraction = 1\nDiffusivityRatio = 0.08\nPorosity = 0.43\nCrystalDensity = 2165\nWithinFaceCoverage = 1\n'
    if end==15: content+='TestInitialTopSolidVF = 0.1\n'
    (out/'case.input').write_text(content)
    for asset in ('filter_6layers.msh','Greal04_port.txt','water_flux_zero_storage.txt'): (out/asset).symlink_to(old/asset)
    cmd=['/rmprog/slurm/v22.05.7/bin/sbatch','--parsable','--partition=cnmix','--nodes=1','--ntasks=1','--cpus-per-task=8','--time=01:00:00',f'--job-name=crust_{name}',f'--chdir={out}','--output=slurm-%j.out',f'--export=ALL,GREAL_ROOT={root},GREAL_WORKDIR={out},GREAL_INPUT=case.input',str(root/'run_case.slurm')]
    jobs[name]={'job_id':subprocess.check_output(cmd,text=True).strip(),'target_s':end,'input_sha256':hashlib.sha256(content.encode()).hexdigest()}
    (root/'jobs.json').write_text(json.dumps(jobs,indent=2))
print(json.dumps(jobs,indent=2))
