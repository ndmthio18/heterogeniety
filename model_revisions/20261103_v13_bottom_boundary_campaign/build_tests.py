from pathlib import Path
import subprocess,json,hashlib
R=Path(__file__).resolve().parent;b=R/'build_filter'
cmd=json.loads((b/'compile_command.json').read_text());cmd=[x.replace(str(R/'source_filter/appl/main.cc'),str(R/'test_boundary.cc')).replace(str(b/'solver'),str(b/'test_boundary')) for x in cmd]
with (b/'test_build.log').open('w') as f:r=subprocess.run(['taskset','-c','0','nice','-n','15',*cmd],stdout=f,stderr=subprocess.STDOUT)
assert r.returncode==0
(b/'test_manifest.json').write_text(json.dumps(dict(binary_sha256=hashlib.sha256((b/'test_boundary').read_bytes()).hexdigest(),source_sha256=hashlib.sha256((R/'test_boundary.cc').read_bytes()).hexdigest(),compile_command=cmd),indent=2))
print('boundary test compiled',flush=True)

cmd=[x.replace(str(R/"test_boundary.cc"),str(R/"native_replay.cc")).replace(str(b/"test_boundary"),str(b/"native_replay")) for x in cmd]
with (b/"replay_build.log").open("w") as f:r=subprocess.run(["taskset","-c","0","nice","-n","15",*cmd],stdout=f,stderr=subprocess.STDOUT)
assert r.returncode==0
(b/"replay_manifest.json").write_text(json.dumps(dict(binary_sha256=hashlib.sha256((b/"native_replay").read_bytes()).hexdigest(),source_sha256=hashlib.sha256((R/"native_replay.cc").read_bytes()).hexdigest(),compile_command=cmd),indent=2))
print("native replay compiled",flush=True)
