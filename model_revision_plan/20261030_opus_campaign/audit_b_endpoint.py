"""Coordinator-only, read-only remote raw-field endpoint audit (stdlib)."""
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REMOTE = r'''
import csv,gzip,hashlib,json,math,pathlib,xml.etree.ElementTree as E
case=CASE_LITERAL
assert case.startswith('v11_') and '/' not in case
base=pathlib.Path('/home/zhixin/Documents/Cooperation_Ali/model_revisions/20261030_verification_v11')
run=pathlib.Path('/tmp/zhixin_verification_v11_20261030/runs')/case
status=json.loads((base/'status'/f'{case}.json').read_text())
assert status['state']=='completed'
entry=max(E.parse(run/f'{case}.pvd').findall('.//DataSet'),key=lambda e:float(e.get('timestep')))
t=float(entry.get('timestep'));assert abs(t-93600)<1e-6
p=run/entry.get('file')
if not p.exists():p=pathlib.Path(str(p)+'.gz')
raw=gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes()
fields={e.get('Name'):[float(v) for v in (e.text or '').split()] for e in E.fromstring(raw).findall('.//CellData/DataArray')}
geom={int(float(r['dof'])):r for r in csv.DictReader((run/'cell_geometry.csv').open())}
height=max(float(g['ymax_m']) for g in geom.values())
total=[[],[]];surface=[[],[]];core_volume=[[],[]];core_down_volume=[[],[]]
for i,dof in enumerate(fields['dof_id']):
 g=geom[int(round(dof))];side=int(float(g['x_m'])>=.025);vol=float(g['volume_m3'])
 mol=vol*fields['porosity'][i]*fields['S_liq'][i]*fields['rhoMolar_liq'][i]*fields['x^NaCl_liq'][i]
 assert math.isfinite(mol) and mol>=0
 assert fields['precipitateVolumeFraction^NaCl'][i]==0
 total[side].append(mol)
 low=height-float(g['ymax_m']);high=height-float(g['ymin_m'])
 overlap=max(0,min(high,.003)-max(low,0))/(high-low)
 surface[side].append(mol*overlap*58.443)
 x=float(g['x_m']);y=float(g['y_m']);z=float(g['z_m']);depth=height-y
 if math.hypot(x-.025,z)<.020 and abs(x-.025)>.003 and .005<depth<.035:
  core_volume[side].append(vol)
  if -fields['velocity_liq_interior_LS (m/s)'][3*i+1]>1e-8:core_down_volume[side].append(vol)
budget=list(csv.DictReader((run/'budget.csv').open()));last=budget[-1]
assert abs(float(last['time_s'])-t)<1e-6
mol=[math.fsum(v) for v in total];stock=[math.fsum(v) for v in surface]
err=[abs(mol[i]-float(last[k]))/abs(float(last[k])) for i,k in enumerate(['coarse_salt_mol','fine_salt_mol'])]
assert max(err)<1e-6
cb=list(csv.DictReader((run/'causal_budget.csv').open()))
cols=[k for k in cb[0] if k.startswith('if_') and 'salt' in k]
max_if=max(abs(float(r[k])) for r in cb for k in cols)
if '_C0B' in case:assert max_if==0
summary=json.loads((base/'analysis'/case/'summary.json').read_text())
print(json.dumps(dict(case=case,final_time_s=t,salt_mol_F36_W3=mol,surface_0_3mm_g_F36_W3=stock,relative_error_vs_ledger=err,core_downflow_vf_F36_W3=[math.fsum(core_down_volume[i])/math.fsum(core_volume[i]) for i in range(2)],max_abs_interface_salt_entry=max_if,interface_columns=len(cols),raw_file=p.name,raw_sha256=hashlib.sha256(raw).hexdigest(),status=status,executor_summary=summary)))
'''

case = sys.argv[1]
code = REMOTE.replace('CASE_LITERAL', repr(case))
p = subprocess.run(['ssh', '-o', 'ConnectTimeout=15', 'liqin',
                    '/home/zhixin/micromamba/envs/vasca311/bin/python3', '-'],
                   input=code, capture_output=True, text=True, timeout=55)
source = 'remote_raw'
if p.returncode and 'FileNotFoundError' in p.stderr:
    # Released remote fields remain in the hash-verified local archive.
    base = Path(__file__).resolve().parents[2] / 'model_revisions/20261030_verification_v11'
    archive = base / 'runs_archive' / case
    manifest = json.loads((archive / 'ARCHIVE_MANIFEST.json').read_text())
    assert manifest['status'] == 'verified' and not manifest['mismatches'] and not manifest['gzip_record_mismatches']
    metadata_code = "import pathlib,json\nb=pathlib.Path('/home/zhixin/Documents/Cooperation_Ali/model_revisions/20261030_verification_v11')\nc=" + repr(case) + "\nprint(json.dumps({'status':json.loads((b/'status'/f'{c}.json').read_text()),'summary':json.loads((b/'analysis'/c/'summary.json').read_text())}))"
    metadata_result = subprocess.run(['ssh', '-o', 'ConnectTimeout=15', 'liqin',
                                     '/home/zhixin/micromamba/envs/vasca311/bin/python3', '-'],
                                    input=metadata_code, capture_output=True, text=True, timeout=55)
    if metadata_result.returncode:
        raise RuntimeError(metadata_result.stderr)
    metadata = json.loads(metadata_result.stdout)
    local_code = code.replace("base=pathlib.Path('/home/zhixin/Documents/Cooperation_Ali/model_revisions/20261030_verification_v11')", "base=pathlib.Path(" + repr(str(base)) + ")")
    local_code = local_code.replace("run=pathlib.Path('/tmp/zhixin_verification_v11_20261030/runs')/case", "run=base/'runs_archive'/case")
    local_code = local_code.replace("status=json.loads((base/'status'/f'{case}.json').read_text())", 'status=' + repr(metadata['status']))
    local_code = local_code.replace("summary=json.loads((base/'analysis'/case/'summary.json').read_text())", 'summary=' + repr(metadata['summary']))
    local_code = local_code.replace("raw=gzip.decompress(p.read_bytes())", "manifest=json.loads((run/'ARCHIVE_MANIFEST.json').read_text());assert hashlib.sha256(p.read_bytes()).hexdigest()==manifest['sha256'][p.name]\nraw=gzip.decompress(p.read_bytes())")
    p = subprocess.run([sys.executable, '-'], input=local_code, capture_output=True, text=True, timeout=55)
    source = 'local_hash_verified_archive_after_remote_release'
if p.returncode:
    raise RuntimeError(p.stderr)
result = json.loads(p.stdout)
result['audit_source'] = source
result['checked_utc'] = datetime.now(timezone.utc).isoformat()
out = Path(__file__).parent / ('COORDINATOR_ENDPOINT_' + case + '_' +
      datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%SUTC') + '.json')
out.write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ['status','executor_summary']}, indent=2))
print(str(out))
