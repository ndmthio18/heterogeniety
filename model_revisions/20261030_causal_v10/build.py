"""Isolated v10 build on liqin: the v08 compile command with only this source tree
and output path substituted. Single compile process, serialized through the shared
flock, pinned to CPU4, nice 10, MemAvailable gate. Never reuses a build directory."""
from pathlib import Path
import datetime,fcntl,hashlib,json,os,subprocess,sys,time
R=Path(__file__).resolve().parent
OLD=R.parent/'20261030_cylinder_film_v08'
LOCK='/tmp/zhixin_hete_20261030_compile.lock'
CPU='4'
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for c in iter(lambda:f.read(1<<20),b''):h.update(c)
 return h.hexdigest()
def mem_available_gib():
 for line in open('/proc/meminfo'):
  if line.startswith('MemAvailable:'):return int(line.split()[1])/1024**2
def run(cmd,log,env):
 with open(log,'w') as f:return subprocess.run(['taskset','-c',CPU,'nice','-n','10']+cmd,stdout=f,stderr=subprocess.STDOUT,env=env).returncode
def main(tag):
 B=R/f'build_{tag}';B.mkdir(exist_ok=False)
 cmd=json.loads((OLD/'build_ni0/compile_command.json').read_text())
 cmd=[x.replace(str(OLD/'source'),str(R/'source')).replace(str(OLD/'build_ni0/heterogeneity_revised'),str(B/'heterogeneity_causal')) for x in cmd]
 assert not any(str(OLD) in x for x in cmd),'v08 path left in compile command'
 env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
 (B/'compile_command.json').write_text(json.dumps(cmd,indent=2))
 status={'tag':tag,'state':'waiting_for_lock','requested_utc':utc()};(B/'build_status.json').write_text(json.dumps(status,indent=2))
 with open(LOCK,'a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  status.update(lock_acquired_utc=utc())
  while mem_available_gib()<6:
   status.update(state='waiting_for_memory',mem_available_gib=mem_available_gib());(B/'build_status.json').write_text(json.dumps(status,indent=2));time.sleep(30)
  status.update(state='compiling',mem_available_gib_at_start=mem_available_gib());(B/'build_status.json').write_text(json.dumps(status,indent=2))
  t0=time.time();rc=run(cmd,B/'build.log',env);status['compile_seconds']=time.time()-t0
  if rc:
   status.update(state='compile_failed',returncode=rc);(B/'build_status.json').write_text(json.dumps(status,indent=2))
   print((B/'build.log').read_text()[-15000:]);sys.exit(rc)
  tc=[x.replace(str(R/'source/appl/main.cc'),str(R/'tests/test_unified_equilibrium.cc')).replace(str(B/'heterogeneity_causal'),str(B/'test_unified_equilibrium')).replace('-DNDEBUG=1','-UNDEBUG') for x in cmd]
  rc=run(tc,B/'test_build.log',env)
  if rc:
   status.update(state='test_compile_failed',returncode=rc);(B/'build_status.json').write_text(json.dumps(status,indent=2));print((B/'test_build.log').read_text()[-8000:]);sys.exit(rc)
  rc=run(['/usr/bin/g++','-std=c++17','-O0',str(R/'tests/test_revision_support.cc'),'-o',str(B/'test_revision_support')],B/'support_build.log',env)
  if rc:
   status.update(state='support_test_compile_failed',returncode=rc);(B/'build_status.json').write_text(json.dumps(status,indent=2));sys.exit(rc)
 thermo=subprocess.run(['taskset','-c',CPU,str(B/'test_unified_equilibrium'),'-Revision.UnifiedWaterActivity','true'],capture_output=True,text=True,env=env,cwd=B)
 (B/'thermodynamic_test.log').write_text(thermo.stdout+thermo.stderr)
 support=subprocess.run(['taskset','-c',CPU,str(B/'test_revision_support')],capture_output=True,text=True,env=env,cwd=B)
 (B/'support_test.log').write_text(support.stdout+support.stderr)
 files=lambda d:{p.relative_to(R).as_posix():sha(p) for p in sorted((R/d).rglob('*')) if p.is_file()}
 deps=[x for x in cmd if x.endswith(('.a','.so')) and '/model_revisions/' in x]
 manifest={'tag':tag,'utc':utc(),'binary':str(B/'heterogeneity_causal'),'binary_sha256':sha(B/'heterogeneity_causal'),
  'test_binaries_sha256':{n:sha(B/n) for n in ['test_unified_equilibrium','test_revision_support']},
  'source_sha256':files('source'),'tests_sha256':files('tests'),'build_script_sha256':sha(Path(__file__)),
  'static_dependency_sha256':{d:sha(d) for d in deps},
  'compiler':subprocess.check_output(['/usr/bin/c++','--version'],text=True).splitlines()[0],
  'thermodynamic_test_returncode':thermo.returncode,'thermodynamic_test':thermo.stdout[-3000:],
  'support_test_returncode':support.returncode,'support_test':support.stdout[-2000:],
  'compile_command':cmd,'compile_seconds':status['compile_seconds'],'cpu':int(CPU),'lock':LOCK}
 (B/'build_manifest.json').write_text(json.dumps(manifest,indent=2))
 status.update(state='built' if thermo.returncode==0 and support.returncode==0 else 'tests_failed',finished_utc=utc());(B/'build_status.json').write_text(json.dumps(status,indent=2))
 print(json.dumps({k:manifest[k] for k in ['tag','binary_sha256','thermodynamic_test_returncode','support_test_returncode','compile_seconds']}))
 if status['state']!='built':sys.exit(4)
if __name__=='__main__':main(sys.argv[1])
