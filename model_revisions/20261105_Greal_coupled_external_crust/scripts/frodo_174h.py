"""Isolated user-authorized Frodo run; no changes to HPCC outputs."""
from pathlib import Path
import os,sys,json,subprocess,time,signal,hashlib,shutil,datetime
ROOT=Path('/temp/zhixin/Greal_external_crust_174h_frodo_20261106')
BUILD=Path('/temp/zhixin/Greal_external_crust_release_20261106/build/solver')
EXPECTED={'solver':'99775343b964856a5a3820cf5ed32e5603273783c8e269ffdd628ad5412028ee','case.input':'331bf2c4848e105faa9e2e12369390e709b3b9cce1bdbb55f3f96d0067cdf4c2','filter_6layers.msh':'4a47ac0b67c6bca83b7d1241558346a66d7eb830642b923ee9005f554de86395','Greal04_port.txt':'d30db051344d4d900820a9834c71425a2910a1111f1b7f6aa0c9a32648bd4d15','water_flux_zero_storage.txt':'4758eb4bf0356f16d1d10376709fecebb9570c6e211b901a124430af9f2bddbe'}
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def save(data):
    p=ROOT/'status.tmp';p.write_text(json.dumps(data,indent=2));p.replace(ROOT/'status.json')
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
if '--run' not in sys.argv:
    if (ROOT/'launch.json').exists(): raise RuntimeError('Already launched; inspect status')
    if shutil.disk_usage(ROOT).free<30*1024**3: raise RuntimeError('Admission space reserve')
    if sha(BUILD)!=EXPECTED['solver']: raise RuntimeError('Source binary hash mismatch')
    shutil.copy2(BUILD,ROOT/'solver')
    for name,digest in EXPECTED.items():
        if sha(ROOT/name)!=digest: raise RuntimeError('Hash mismatch: '+name)
    ldd=subprocess.check_output(['ldd',str(ROOT/'solver')],text=True)
    (ROOT/'ldd.txt').write_text(ldd)
    if 'not found' in ldd: raise RuntimeError('Missing runtime')
    run=ROOT/'run';run.mkdir(exist_ok=False)
    for name in EXPECTED:
        if name!='solver':shutil.copy2(ROOT/name,run/name)
    with (ROOT/'controller.log').open('w') as out:
        p=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--run'],stdin=subprocess.DEVNULL,stdout=out,stderr=subprocess.STDOUT,start_new_session=True,cwd=ROOT)
    record={'controller_pid':p.pid,'started_utc':utc(),'hashes':EXPECTED,'threads':8,'cpu_affinity':'0-7','target_evaporation_h':174,'pre_h':2,'qualification':'exploratory_user_release','restart':'original_initial_conditions'}
    (ROOT/'launch.json').write_text(json.dumps(record,indent=2));print(json.dumps(record));raise SystemExit(0)
env=os.environ.copy();env.update(DUMUX_NUM_THREADS='8',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
start=time.monotonic();reason=None
with (ROOT/'run/simulation.log').open('w') as log:
    p=subprocess.Popen(['taskset','-c','0-7','nice','-n','10',str(ROOT/'solver'),'case.input'],cwd=ROOT/'run',env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    while p.poll() is None:
        free=shutil.disk_usage(ROOT).free;inodes=os.statvfs(ROOT).f_favail
        if free<4*1024**3 or inodes<10000 or time.monotonic()-start>48*3600:
            reason='disk/inode reserve or 48h wall limit reached'
            os.killpg(p.pid,signal.SIGTERM)
            try:p.wait(timeout=30)
            except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
        data={'state':'running' if p.poll() is None else 'exited','solver_pid':p.pid,'controller_pid':os.getpid(),'updated_utc':utc(),'elapsed_s':time.monotonic()-start,'free_bytes':free,'free_inodes':inodes,'reason':reason,'qualified':False}
        save(data)
        if p.poll() is None:time.sleep(30)
    data.update(state='completed_process' if p.returncode==0 else 'failed',returncode=p.returncode);save(data)
raise SystemExit(p.returncode)
