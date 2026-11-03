"""Reuse exact native ELFs behind the original sal relocations; no scientific rebuild."""
from pathlib import Path
import json,hashlib,shutil,subprocess,socket
R=Path(__file__).resolve().parent;assert socket.gethostname()=='frodo'
OLD=Path('/temp/zhixin/heterogeneity_performance_v14_20261102')
G=Path('/temp/zhixin/v13_bottom_boundary_build_20261103/build_filter')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
specs=[('build_ni1',OLD/'build_cached_ni1/heterogeneity_revised',OLD/'build_cached_ni1/build_manifest.json','source_cached/','source_baseline/','9b1422e33fb76423322b081e414206e22777548fca0b703d6e285186a4fe63e5'),('build_filter_sal',G/'solver',G/'build_manifest.json','source_filter/','source_filter/','f0205489a215670ac56650c5535f3544f8a4d1ef9365e2c630b6e973129f4868')]
for folder,exe,manifest,oldprefix,newprefix,want in specs:
 m=json.loads(manifest.read_text());assert sha(exe)==m['binary_sha256']==want
 sources={k.replace(oldprefix,newprefix,1):h for k,h in m['source_sha256'].items()}
 for k,h in sources.items():assert sha(R/k)==h,k
 b=R/folder;b.mkdir(exist_ok=False);shutil.copy2(exe,b/'solver_elf');(b/'solver_elf').chmod(0o755)
 wrapper=b/'heterogeneity_revised';wrapper.write_text('#!/bin/sh\nexec '+str(b/'solver_elf')+' "$@"\n');wrapper.chmod(0o755)
 (b/'build_manifest.json').write_text(json.dumps(dict(binary_sha256=sha(wrapper),native_elf_sha256=want,source_sha256=sources,original_build_manifest=m,host='frodo',change='same native ELF as original sal code before loader relocation; runner wrapper only'),indent=2))
for name,src,manifest in [('native_replay',G/'native_replay',G/'replay_manifest.json'),('test_boundary',G/'test_boundary_r04',G/'test_manifest_r04.json')]:
 m=json.loads(manifest.read_text());assert sha(src)==m['binary_sha256'];assert sha(R/('native_replay.cc' if name=='native_replay' else 'test_boundary.cc'))==m['source_sha256']
 p=R/'build_filter_sal'/name;shutil.copy2(src,p);p.chmod(0o755);shutil.copy2(manifest,R/'provenance'/(name+'_original_manifest.json'))
for b in ['build_ni1/solver_elf','build_filter_sal/solver_elf','build_filter_sal/native_replay','build_filter_sal/test_boundary']:
 d=subprocess.check_output(['ldd',str(R/b)],text=True);assert 'not found' not in d,d
 (R/'provenance'/(b.replace('/','_')+'_ldd.txt')).write_text(d)
print('Native binary/source/runtime verification passed',flush=True)
