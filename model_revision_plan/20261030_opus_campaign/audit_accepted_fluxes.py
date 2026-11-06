"""Independent accepted-step boundary/interface integration for all B cases."""
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
B = ROOT / 'model_revisions/20261030_verification_v11'
OUT = ROOT / 'analysis/opus_campaign_joint_20261101'
records = []
for sp in sorted((B / 'remote_status').glob('v11_*.json')):
    status = json.loads(sp.read_text())
    case = status['case']
    assert status['state'] == 'completed'
    run = B / 'runs_archive' / case
    seed = json.loads((run / 'seed_event.json').read_text())
    with (run / 'causal_budget.csv').open() as f:
        rows = [{k: float(v) for k,v in r.items()} for r in csv.DictReader(f)]
    start = next(i for i,r in enumerate(rows) if abs(r['time_s']-7200)<1e-6)
    assert rows[-1]['time_s'] == 93600
    cum = [[0.,0.],[0.,0.]]
    maxerr = [[0.,0.],[0.,0.]]
    maxblocked = 0.
    for r in rows[start+1:]:
        dt = r['dt_s']
        for ci,comp in enumerate(['water','salt']):
            cols = [k for k in r if k.startswith('if_') and f'_{comp}_' in k and k.endswith('_mol_s')]
            assert len(cols) == 8
            irate = sum(r[k] for k in cols)
            if '_C0B' in case:
                maxblocked = max(maxblocked,max(abs(r[k]) for k in cols))
            for si,side in enumerate(['F36','W3']):
                cum[si][ci] += dt*(-r[f'{side}_boundary_{comp}_out_mol_s'] + (-1 if si==0 else 1)*irate)
                impulse = seed['side_component_impulses_mol'][si][0 if comp=='water' else 2]
                delta = r[f'{side}_{comp}_mol']-rows[start][f'{side}_{comp}_mol']-impulse
                err = abs(delta-cum[si][ci])/abs(rows[start][f'{side}_{comp}_mol'])
                maxerr[si][ci] = max(maxerr[si][ci],err)
    assert max(max(v) for v in maxerr)<1e-6, (case,maxerr)
    if '_C0B' in case:
        assert maxblocked == 0
    records.append({'case':case,'accepted_rows':len(rows),'end_s':rows[-1]['time_s'],
                    'max_relative_error_rows_F36_W3_columns_water_salt':maxerr,
                    'max_blocked_instantaneous_water_or_salt_interface_rate':maxblocked if '_C0B' in case else None,
                    'causal_budget_sha256':hashlib.sha256((run/'causal_budget.csv').read_bytes()).hexdigest(),
                    'method':'Reintegrate instantaneous accepted-step external boundary and eight advective/diffusive interface-band rates; subtract recorded side component seed impulses exactly once.'})
assert len(records)==22
result={'utc':datetime.now(timezone.utc).isoformat(),'cases':records,'all_passed':True,
        'maximum_relative_error':max(max(max(v) for v in r['max_relative_error_rows_F36_W3_columns_water_salt']) for r in records),
        'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(OUT/'independent_accepted_flux_audit.json').write_text(json.dumps(result,indent=2))
print(json.dumps({'cases':len(records),'all_passed':True,'max_relative_error':result['maximum_relative_error']}))
