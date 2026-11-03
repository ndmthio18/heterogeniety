from pathlib import Path
import json,hashlib,shutil,subprocess
R=Path(__file__).resolve().parent;B=R/'build_sal';B.mkdir(exist_ok=False)
# Kept build_sal directory name as runner adapter compatibility only; manifests label host.
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
hashes={};sources={}
for name,dest in [('solver','heterogeneity_revised'),('test_boundary','test_boundary')]:
 m=json.loads((R/'build'/f'{name}_manifest.json').read_text());p=R/'build'/name;assert sha(p)==m['binary_sha256']
 for k,h in m['source_sha256'].items():assert sha(R/k)==h,k
 sources.update(m['source_sha256']);p.chmod(0o755);wrapper=B/dest;wrapper.write_text('#!/bin/sh\nexec '+str(p)+' "$@"\n');wrapper.chmod(0o755)
 hashes[dest]=dict(original_elf_sha256=sha(p),wrapper_sha256=sha(wrapper),host='frodo native build, no relocation')
(B/'build_manifest.json').write_text(json.dumps(dict(binary_sha256=sha(B/'heterogeneity_revised'),binaries=hashes,source_sha256=sources,host='frodo',dependencies='same pinned build-time Frodo tree and libraries; see compile manifest'),indent=2))
print(json.dumps(hashes))
