from pathlib import Path
import json,hashlib,subprocess,shutil
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for name,h in json.loads((R/'staging_manifest.json').read_text()).items():assert sha(R/name)==h,name
b=R/'build_ni1';b.mkdir(exist_ok=False)
exe=b/'solver_elf';shutil.copy2(R/'parent_build/heterogeneity_revised',exe)
original=sha(exe)
for needed in subprocess.check_output(['patchelf','--print-needed',str(exe)],text=True).splitlines():
 if needed.startswith('/'):
  assert (R/'runtime/lib'/Path(needed).name).exists()
  subprocess.run(['patchelf','--replace-needed',needed,Path(needed).name,str(exe)],check=True)
subprocess.run(['patchelf','--set-interpreter',str(R/'runtime/lib/ld-linux-x86-64.so.2'),'--set-rpath',str(R/'runtime/lib'),str(exe)],check=True)
wrapper=b/'heterogeneity_revised'
wrapper.write_text('#!/bin/bash\nexport LD_LIBRARY_PATH="'+str(R/'runtime/lib')+'"\nexport OMPI_MCA_mca_base_component_path="'+str(R/'runtime/plugins')+'"\nexport OPAL_PREFIX="'+str(R/'runtime')+'"\nexec "'+str(exe)+'" "$@"\n');wrapper.chmod(0o755)
(b/'build_manifest.json').write_text(json.dumps(dict(binary_sha256=sha(wrapper),original_elf_sha256=original,relocated_elf_sha256=sha(exe),source_sha256={p.relative_to(R).as_posix():sha(p) for p in (R/'source').rglob('*') if p.is_file()},runtime_sha256={p.relative_to(R).as_posix():sha(p) for p in (R/'runtime').rglob('*') if p.is_file()},host='sal',change='ELF interpreter and library paths only; compiled code frozen'),indent=2))
print('runtime staged',sha(exe))
