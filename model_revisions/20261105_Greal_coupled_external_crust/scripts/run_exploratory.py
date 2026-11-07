"""Run inside Slurm; supervise only this solver process group."""
from pathlib import Path
import os,subprocess,shutil,time,json,signal,datetime,hashlib
root=Path(__file__).resolve().parent
run=root/'run'
if not os.environ.get('SLURM_JOB_ID'): raise RuntimeError('Slurm allocation required')
os.chdir(run)
env=os.environ.copy()
env.update(DUMUX_NUM_THREADS=env.get('SLURM_CPUS_PER_TASK','8'),OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
with open('simulation.log','w') as log:
    process=subprocess.Popen([str(root/'solver_wrapper.sh'),'case.input'],env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    reason=None
    while process.poll() is None:
        free=shutil.disk_usage(run).free
        if free<4*1024**3:
            reason='4 GiB storage reserve reached'
            os.killpg(process.pid,signal.SIGTERM)
            try: process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL);process.wait()
        status={'state':'running' if process.poll() is None else 'exited','pid':process.pid,'job_id':os.environ['SLURM_JOB_ID'],'free_bytes':free,'reason':reason,'updated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'qualification':'exploratory_user_release'}
        (run/'controller_status.json').write_text(json.dumps(status,indent=2))
        if process.poll() is None: time.sleep(30)
    status.update(state='completed_process' if process.returncode==0 else 'failed',returncode=process.returncode)
    (run/'controller_status.json').write_text(json.dumps(status,indent=2))
raise SystemExit(process.returncode)
