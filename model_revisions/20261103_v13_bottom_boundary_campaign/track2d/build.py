from pathlib import Path
import json,hashlib,subprocess,datetime,concurrent.futures
R=Path(__file__).resolve().parent;OLD=Path('/temp/zhixin/heterogeneity_performance_v14_20261102');B=R/'build';B.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(OLD/'build_cached_ni1/heterogeneity_revised')=='9b1422e33fb76423322b081e414206e22777548fca0b703d6e285186a4fe63e5'
base=json.loads((OLD/'build_cached_ni1/compile_command.json').read_text())
def compile_one(name,source,cpu):
 cmd=[s.replace(str(OLD/'source_cached'),str(R/'source')).replace(str(OLD/'build_cached_ni1/heterogeneity_revised'),str(B/name)) for s in base]
 cmd=[str(source) if s==str(R/'source/appl/main.cc') else s for s in cmd]
 with (B/(name+'.log')).open('w') as log:p=subprocess.run(['taskset','-c',str(cpu),'nice','-n','15',*cmd],stdout=log,stderr=subprocess.STDOUT)
 assert p.returncode==0,name+' compile failed; log preserved'
 m=dict(binary_sha256=sha(B/name),compile_command=cmd,source_sha256={p.relative_to(R).as_posix():sha(p) for p in (R/'source').rglob('*') if p.is_file()},test_source_sha256=sha(source),utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),build_host='frodo; build only, no simulation')
 (B/(name+'_manifest.json')).write_text(json.dumps(m,indent=2));return name,m['binary_sha256']
with concurrent.futures.ThreadPoolExecutor(2) as pool:
 for x in [pool.submit(compile_one,'solver',R/'source/appl/main.cc',0),pool.submit(compile_one,'test_boundary',R/'test_boundary.cc',1)]:print(x.result(),flush=True)
