from pathlib import Path
import shutil, subprocess, json, hashlib
root=Path('/WORK/hulm_work/zhixin/Greal_coupled_external_crust_20261105')
old=Path('/WORK/hulm_work/zhixin/Greal_experimental_bottom_hpcc_20261104')
record=root/'c0_jobs.json'
if record.exists(): raise RuntimeError('Already submitted: inspect job record')
if shutil.disk_usage(root).free < 30*1024**3: raise RuntimeError('Storage reserve')
if not (root/'runtime').exists(): (root/'runtime').symlink_to(old/'runtime',target_is_directory=True)
for name in ('solver_wrapper.sh','run_case.slurm'): shutil.copy2(old/name,root/name)
(root/'solver').chmod(0o755)
jobs={}
for label,binary_root in [('C0_original',old),('C0_patched',root)]:
    out=root/'gates'/label
    out.mkdir(parents=True,exist_ok=False)
    content=(old/'Greal-81.input').read_text().replace('TEnd = 633600','TEnd = 7800')
    content+='\n[ExternalCrust]\nEnable = false\nThermalResistance = false\n'
    (out/'case.input').write_text(content)
    for name in ('filter_6layers.msh','Greal04_port.txt','water_flux_zero_storage.txt'):
        (out/name).symlink_to(old/name)
    job=subprocess.check_output(['/rmprog/slurm/v22.05.7/bin/sbatch','--parsable','--partition=cnmix','--nodes=1','--ntasks=1','--cpus-per-task=8','--time=01:00:00',f'--job-name={label}',f'--chdir={out}','--output=slurm-%j.out',f'--export=ALL,GREAL_ROOT={binary_root},GREAL_WORKDIR={out},GREAL_INPUT=case.input',str(root/'run_case.slurm')],text=True).strip()
    jobs[label]={'job_id':job,'input_sha256':hashlib.sha256((out/'case.input').read_bytes()).hexdigest()}
    record.write_text(json.dumps(jobs,indent=2))
print(json.dumps(jobs))
