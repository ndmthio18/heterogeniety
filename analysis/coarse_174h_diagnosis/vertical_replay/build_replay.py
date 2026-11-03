"""Remote-only isolated diagnostic build; never edits accepted source/binary."""
from pathlib import Path
import shutil,json,subprocess,hashlib,difflib
R=Path(__file__).resolve().parent
V=Path('/home/zhixin/Documents/Cooperation_Ali/model_revisions/20261102_cylinder_fixed_hydraulics_v12')
assert not (R/'source').exists(), 'Preserve prior diagnostic attempts'
shutil.copytree(V/'source',R/'source')
p=R/'source/appl/problem.hh';old=p.read_text();new=old.replace('\nprivate:\n','\n'+(R/'replay_member.hh').read_text()+'\nprivate:\n');assert new!=old;p.write_text(new)
(R/'diagnostic.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='accepted/problem.hh',tofile='replay/problem.hh')))
shutil.copyfile(R/'replay_main.cc',R/'source/appl/main.cc')
cmd=json.loads((V/'build_ni0/compile_command.json').read_text())
cmd=[v.replace(str(V/'source'),str(R/'source')).replace(str(V/'build_ni0/heterogeneity_revised'),str(R/'native_replay')) for v in cmd]
(R/'compile_command.json').write_text(json.dumps(cmd,indent=2))
with (R/'build.log').open('w') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
assert r.returncode==0, 'Read build.log'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(R/'build_manifest.json').write_text(json.dumps({'binary_sha256':sha(R/'native_replay'),'accepted_binary_sha256':sha(V/'build_ni0/heterogeneity_revised'),'original_problem_sha256':sha(V/'source/appl/problem.hh'),'diagnostic_problem_sha256':sha(p),'purpose':'Read-only accepted-state finite-volume flux replay. No Newton/time stepping.'},indent=2))
print('BUILD_OK',flush=True)
