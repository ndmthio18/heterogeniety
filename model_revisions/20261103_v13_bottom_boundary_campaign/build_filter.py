from pathlib import Path
import json,hashlib,subprocess,os,datetime
R=Path(__file__).resolve().parent;OLD=Path('/temp/zhixin/heterogeneity_performance_v14_20261102');b=R/'build_filter';b.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(OLD/'build_cached_ni1/heterogeneity_revised')=='9b1422e33fb76423322b081e414206e22777548fca0b703d6e285186a4fe63e5'
cmd=json.loads((OLD/'build_cached_ni1/compile_command.json').read_text())
cmd=[s.replace(str(OLD/'source_cached'),str(R/'source_filter')).replace(str(OLD/'build_cached_ni1/heterogeneity_revised'),str(b/'solver')) for s in cmd]
(b/'compile_command.json').write_text(json.dumps(cmd,indent=2))
with (b/'build.log').open('w') as log:p=subprocess.run(['taskset','-c','0','nice','-n','15',*cmd],stdout=log,stderr=subprocess.STDOUT)
assert p.returncode==0,'compile failure retained in build_filter/build.log'
(b/'build_manifest.json').write_text(json.dumps(dict(binary_sha256=sha(b/'solver'),compile_command=cmd,source_sha256={str(p.relative_to(R)):sha(p) for p in (R/'source_filter').rglob('*') if p.is_file()},utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),host='frodo',purpose='isolated build only; production and regression run on sal'),indent=2))
print('build passed',sha(b/'solver'),flush=True)
