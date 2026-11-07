from pathlib import Path
import subprocess, shutil, hashlib, json
root=Path(__file__).resolve().parents[1]
tool=root/'build_tools/bin/patchelf'
src=root/'build/solver'; dst=root/'build/solver_hpcc'
if dst.exists(): raise RuntimeError('Refusing overwrite')
shutil.copy2(src,dst)
needed=subprocess.check_output([str(tool),'--print-needed',str(dst)],text=True).splitlines()
changes=[]
for dep in needed:
    if '/' in dep:
        subprocess.run([str(tool),'--replace-needed',dep,Path(dep).name,str(dst)],check=True)
        changes.append([dep,Path(dep).name])
(root/'build/portable_manifest.json').write_text(json.dumps({'changes':changes,'original_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'portable_sha256':hashlib.sha256(dst.read_bytes()).hexdigest()},indent=2))
