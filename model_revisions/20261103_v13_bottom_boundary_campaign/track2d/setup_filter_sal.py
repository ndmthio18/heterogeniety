from pathlib import Path
import json,hashlib,subprocess,shutil
R=Path(__file__).resolve().parent;b=R/'build_filter_sal';b.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((R/'build_filter/build_manifest.json').read_text())
for k,h in m['source_sha256'].items():assert sha(R/k)==h,k
hashes={}
for original,name in [('solver','heterogeneity_revised'),('test_boundary','test_boundary'),('native_replay','native_replay')]:
 p=R/'build_filter'/original
 parent=m if original=='solver' else json.loads((R/'build_filter'/('test_manifest.json' if original=='test_boundary' else 'replay_manifest.json')).read_text())
 assert sha(p)==parent['binary_sha256']
 exe=b/(name+'_elf');shutil.copy2(p,exe);exe.chmod(0o755)
 for lib in subprocess.check_output(['patchelf','--print-needed',str(exe)],text=True).splitlines():
  if lib.startswith('/'):
   assert (R/'runtime/lib'/Path(lib).name).exists(),lib;subprocess.run(['patchelf','--replace-needed',lib,Path(lib).name,str(exe)],check=True)
 subprocess.run(['patchelf','--set-interpreter',str(R/'runtime/lib/ld-linux-x86-64.so.2'),'--set-rpath',str(R/'runtime/lib'),str(exe)],check=True)
 template=(R/'build_ni1/heterogeneity_revised').read_text().replace(str(R/'build_ni1/solver_elf'),str(exe));wrapper=b/name;wrapper.write_text(template);wrapper.chmod(0o755)
 hashes[name]={'original_elf_sha256':sha(p),'relocated_elf_sha256':sha(exe),'wrapper_sha256':sha(wrapper)}
(b/'build_manifest.json').write_text(json.dumps(dict(binary_sha256=sha(b/'heterogeneity_revised'),source_sha256={k:sha(R/k) for k in m['source_sha256']},binaries=hashes,parent_build=m),indent=2))
print(json.dumps({'state':'staged','binaries':hashes},indent=2))
