"""Verify analysis inputs against accepted archive manifest and salt accounting."""
from pathlib import Path
import argparse,json,hashlib
import pandas as pd
p=argparse.ArgumentParser();p.add_argument('--audit',type=Path,required=True);p.add_argument('--accepted',type=Path,required=True);a=p.parse_args()
manifest={}
for line in (a.accepted/'results/archive_verification/full_files.sha256').read_text().splitlines():
 h,name=line.split(maxsplit=1);manifest[name.strip()]=h
r=a.audit/'results';checks={};verified=[]
for file in ['analysis_source_hashes.json','selected_native_hashes.json']:
 for name,h in json.loads((r/file).read_text()).items():
  key='runs/'+name.split('/runs/')[-1] if '/runs/' in name else name
  assert key in manifest,(file,key,'not in accepted manifest')
  assert manifest[key]==h,(key,'source hash mismatch')
  verified.append(key)
checks['accepted_source_files_verified']=len(set(verified));checks['accepted_source_paths']=sorted(set(verified))
checks['W3_salt_closure_mol']={}
for case in ['Greal-81','Greal-75']:
 d=pd.read_csv(a.accepted/f'results/full174_verified/{case}/depth_profiles_compact.csv').drop_duplicates(['time_s','material','depth_mm'],keep='last')
 z=d[d.material==1].groupby('time_s').salt_total_mol.sum();delta=z.loc[633600]-z.loc[7200]
 t=pd.read_csv(r/f'{case}_transport_windows.csv');t=t[(t.start_h==0)&(t.end_h==174)].iloc[0]
 incoming=sum(t[c] for c in ['lateral_adv_net_mol','lateral_diff_net_mol','upward_adv_net_mol','upward_diff_net_mol'])
 error=float(delta-incoming);assert abs(error)<1e-10,(case,error)
 checks['W3_salt_closure_mol'][case]={'storage_increase':float(delta),'integrated_supply':float(incoming),'residual':error}
coverage=json.loads((r/'MRI_match_coverage.json').read_text());assert all(x['observations']==x['matched'] for x in coverage['coverage'])
checks['MRI_pairs_matched']=sum(x['matched'] for x in coverage['coverage'])
checks['MRI_input_sha_verified']=hashlib.sha256((a.accepted/'inputs/MRI_profile_pairs_unchanged.csv').read_bytes()).hexdigest()==coverage['MRI_sha256'];assert checks['MRI_input_sha_verified']
checks['visual_review']='pending';checks['literature_dimensional_band']='unverified; no invented band'
(r/'QA_checks.json').write_text(json.dumps(checks,indent=2));print(json.dumps(checks,indent=2))
