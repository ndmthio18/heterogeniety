from pathlib import Path
import shutil,json,hashlib,subprocess
R=Path(__file__).resolve().parent;OLD=Path('/tmp/zhixin_sal_film_v16_20261103')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
parent=json.loads((R/'provenance/accelerated_sal_manifest.json').read_text())
assert sha(OLD/'build_ni1/solver_elf')==parent['relocated_elf_sha256']
for k,v in parent['runtime_sha256'].items():assert sha(OLD/k)==v,k
shutil.copytree(OLD/'runtime',R/'runtime');shutil.copytree(OLD/'venv',R/'venv',symlinks=True)
# venv scripts have old shebangs; invoke this venv/bin/python explicitly only.
b=R/'build_ni1';b.mkdir();shutil.copy2(OLD/'build_ni1/solver_elf',b/'solver_elf')
subprocess.run(['patchelf','--set-interpreter',str(R/'runtime/lib/ld-linux-x86-64.so.2'),'--set-rpath',str(R/'runtime/lib'),str(b/'solver_elf')],check=True)
wrapper=(OLD/'build_ni1/heterogeneity_revised').read_text().replace(str(OLD),str(R))
(b/'heterogeneity_revised').write_text(wrapper);(b/'heterogeneity_revised').chmod(0o755)
# The singleton MPI helper also has a relocated interpreter. Keep all runtime local.
orted=R/'runtime/bin/orted'
if orted.exists():subprocess.run(['patchelf','--set-interpreter',str(R/'runtime/lib/ld-linux-x86-64.so.2'),'--set-rpath',str(R/'runtime/lib'),str(orted)],check=True)
source={str(p.relative_to(R)):sha(p) for p in (R/'source_baseline').rglob('*') if p.is_file()}
manifest={'binary_sha256':sha(b/'heterogeneity_revised'),'relocated_elf_sha256':sha(b/'solver_elf'),'original_frodo_elf_sha256':parent['original_elf_sha256'],'source_sha256':source,'parent_manifest':parent,'change':'isolated loader/runtime relocation only; exact compiled code'}
(b/'build_manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps({'setup':'passed','elf':manifest['relocated_elf_sha256']}))
