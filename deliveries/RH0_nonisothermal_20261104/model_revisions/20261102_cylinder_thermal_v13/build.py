from pathlib import Path
import subprocess,json,hashlib,datetime,os
r=Path(__file__).resolve().parent;old=r.parent/'20261030_cylinder_film_v08'
b=r/'build_ni1';b.mkdir(exist_ok=True)
cmd=json.loads((old/'build_ni0/compile_command.json').read_text())
cmd=[x.replace(str(old/'source'),str(r/'source')).replace(str(old/'build_ni0/heterogeneity_revised'),str(b/'heterogeneity_revised')).replace('-DNONISOTHERMAL=0','-DNONISOTHERMAL=1') for x in cmd]
env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
(b/'compile_command.json').write_text(json.dumps(cmd,indent=2))
with (b/'build.log').open('w') as f:p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,env=env)
if p.returncode:print((b/'build.log').read_text()[-12000:]);raise SystemExit(p.returncode)
tc=[x.replace(str(r/'source/appl/main.cc'),str(r/'tests/test_unified_equilibrium.cc')).replace(str(b/'heterogeneity_revised'),str(b/'test_unified_equilibrium')).replace('-DNDEBUG=1','-UNDEBUG') for x in cmd]
with (b/'test_build.log').open('w') as f:p=subprocess.run(tc,stdout=f,stderr=subprocess.STDOUT,env=env)
if p.returncode:print((b/'test_build.log').read_text()[-10000:]);raise SystemExit(p.returncode)
p=subprocess.run([str(b/'test_unified_equilibrium'),'-Revision.UnifiedWaterActivity','true'],capture_output=True,text=True,env=env)
(b/'thermodynamic_test.log').write_text(p.stdout+p.stderr)
if p.returncode:raise RuntimeError(p.stdout+p.stderr)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
data={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'binary_sha256':sha(b/'heterogeneity_revised'),'source_sha256':{p.relative_to(r).as_posix():sha(p) for p in (r/'source').rglob('*') if p.is_file()},'thermodynamic_test':p.stdout,'compile_command':cmd}
(b/'build_manifest.json').write_text(json.dumps(data,indent=2));print(json.dumps({'status':'built','binary_sha256':data['binary_sha256']}))
