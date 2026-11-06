"""Write COMPLETION.json from the evidence files; state=completed only if every
required A-gate is met, otherwise needs_attention with reasons."""
from pathlib import Path
import datetime,hashlib,json
L=Path(__file__).resolve().parent;S=L/'stages/v10c'
rd=lambda p:json.loads(Path(p).read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
checks={};reasons=[]
def need(name,ok,detail=None):
 checks[name]={'ok':bool(ok),'detail':detail}
 if not ok:reasons.append(name)
for k in ['C1B1','C0B1','C1B0','C0B0']:need(f'selftest_{k}',rd(S/f'selftest_{k}.json')['status']=='passed')
need('hydrostatic_compare',rd(S/'hydrostatic_compare.json')['status']=='passed',rd(S/'hydrostatic_compare.json')['worst_field_difference'])
p=rd(S/'prefix_regression.json');need('prefix_regression_vs_v08',p['status']=='passed' and p['regression_status']=='passed',p['max_scaled_difference'])
for k in ['C0B1','C1B0','C0B0']:need(f'short_{k}',rd(S/f'short_{k}.json')['status']=='passed')
h=rd(L/'HANDOFF_READY.json');need('handoff_written_and_verified',rd(L/'handoff_verification_local.json')['status']=='verified',{'sha256':sha(L/'HANDOFF_READY.json'),'snapshot_sha256':h['snapshot_tar_sha256']})
for k in ['C1B1','C0B1','C1B0','C0B0']:
 r=rd(S/f'production_{k}_24h.json');v=r['validation']
 need(f'production_{k}_24h',r['status']=='completed' and max(v['max_relative_budget_residuals'].values())<1e-6 and v['precip_vf_max']==0,
  {'max_rel_residual':max(v['max_relative_budget_residuals'].values()),'wall_h':r['run_manifest']['wall_s']/3600,'cpu_h':r['run_manifest']['cpu_seconds']/3600})
 x=rd(L/f'results/v10c/{k}_24h/extraction.json')
 need(f'extraction_{k}_24h',x['status']=='completed' and x['max_field_vs_ledger_band_salt_relative_error']<1e-9 and x['frames']==145,x['max_field_vs_ledger_band_salt_relative_error'])
r=rd(S/'production_C1B1_24h.json');need('C1B1_24h_regression_vs_v08',r.get('regression_status')=='passed',r.get('max_scaled_difference'))
need('analysis',(L/'analysis/v10c/analysis_summary.json').exists() and len(rd(L/'analysis/v10c/analysis_summary.json')['cases'])==4)
need('report',(L/'CAUSAL_REPORT.md').exists())
av=L/'archive/v10c/archive_verification.json'
need('archive_local_copy_verified',av.exists() and rd(av)['status']=='verified')
out={'agent':'Opus A','resolved_model':'claude-opus-5-5','state':'completed' if not reasons else 'needs_attention','reasons':reasons,
 'written_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'report':'model_revisions/20261030_causal_v10/CAUSAL_REPORT.md',
 'report_sha256':sha(L/'CAUSAL_REPORT.md'),'checks':checks,
 'scope_note':'Completed = all Opus A protocol gates, four validated 24 h runs, extraction, analysis, report and archive. Numerical robustness of the effects (grid/dt/perturbation) is Opus B\'s task and is not claimed here; no parameter-interval test; not experimental validation.',
 'key_results_g':{'E1_W3_0_3mm_12h_24h':[0.0042237,0.0043127],'E0_W3_0_3mm_12h_24h':[0.0035115,0.0083265],'interaction_12h_24h':[0.00071215,-0.0040138],
  'W3_side_effect_24h_B1':0.041993,'W3_bottom_salt_supply_C1_vs_C0_24h_B1':[0.021549,0.23664],'interface_salt_net_24h_C1B1':0.25708},
 'recommendation_to_B':'Interaction E1-E0 is of the same order as E and changes sign between 12 and 24 h: run the B=0 fine-grid and 150 s pair extension.'}
(L/'COMPLETION.json').write_text(json.dumps(out,indent=2));print(out['state'],reasons)
