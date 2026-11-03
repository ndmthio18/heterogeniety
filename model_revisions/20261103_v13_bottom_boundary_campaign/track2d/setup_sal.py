from pathlib import Path
import json,hashlib,shutil,subprocess
R=Path(__file__).resolve().parent;P=R.parent;B=R/'build_sal';B.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
hashes={};sources={}
for name,dest in [('solver','heterogeneity_revised'),('test_boundary','test_boundary')]:
 m=json.loads((R/'build'/f'{name}_manifest.json').read_text())
 assert sha(R/'build'/name)==m['binary_sha256']
 for path,h in m['source_sha256'].items():assert sha(R/path)==h,path
 sources.update(m['source_sha256']);exe=B/(dest+'_elf');shutil.copy2(R/'build'/name,exe);exe.chmod(0o755)
 for lib in subprocess.check_output(['patchelf','--print-needed',str(exe)],text=True).splitlines():
  if lib.startswith('/'):
   assert (P/'runtime/lib'/Path(lib).name).exists();subprocess.run(['patchelf','--replace-needed',lib,Path(lib).name,str(exe)],check=True)
 subprocess.run(['patchelf','--set-interpreter',str(P/'runtime/lib/ld-linux-x86-64.so.2'),'--set-rpath',str(P/'runtime/lib'),str(exe)],check=True)
 wrapper=B/dest;wrapper.write_text((P/'build_ni1/heterogeneity_revised').read_text().replace(str(P/'build_ni1/solver_elf'),str(exe)));wrapper.chmod(0o755)
 hashes[dest]=dict(original_sha256=m['binary_sha256'],elf_sha256=sha(exe),wrapper_sha256=sha(wrapper))
(B/'build_manifest.json').write_text(json.dumps(dict(binary_sha256=sha(B/'heterogeneity_revised'),binaries=hashes,source_sha256=sources,runtime_dependency=str(P/'runtime'),runtime_sha256={p.relative_to(P).as_posix():sha(p) for p in (P/'runtime').rglob('*') if p.is_file()}),indent=2))
print(json.dumps(hashes))
