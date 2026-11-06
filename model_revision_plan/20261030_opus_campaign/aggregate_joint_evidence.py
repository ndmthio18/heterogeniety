"""Coordinator aggregation of frozen executor outputs; no simulation mutations."""
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
B = ROOT / 'model_revisions/20261030_verification_v11'
OUT = ROOT / 'analysis/opus_campaign_joint_20261101'
SCENARIOS = {
    'medium': ('A_C1B1_24h', 'A_C0B1_24h', 'A_C1B0_24h', 'A_C0B0_24h'),
    'coarse': ('v11_G_coarse_C1B1', 'v11_G_coarse_C0B1'),
    'fine': ('v11_G_fine_C1B1', 'v11_G_fine_C0B1', 'v11_G_fine_C1B0', 'v11_G_fine_C0B0'),
    'dt150': ('v11_T150_C1B1', 'v11_T150_C0B1', 'v11_T150_C1B0', 'v11_T150_C0B0'),
    'seed2': ('v11_S2_C1B1', 'v11_S2_C0B1'),
    'seed3': ('v11_S3_C1B1', 'v11_S3_C0B1'),
    'amplitude3e-6': ('v11_A3e-6_C1B1', 'v11_A3e-6_C0B1'),
    'amplitude3e-5': ('v11_A3e-5_C1B1', 'v11_A3e-5_C0B1'),
    'P1': ('v11_P1_C1B1', 'v11_P1_C0B1'),
    'P2': ('v11_P2_C1B1', 'v11_P2_C0B1'),
}


def read(p):
    return json.loads(p.read_text(encoding='utf-8'))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write_csv(name, rows):
    if not rows:
        return
    with (OUT / name).open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main():
    OUT.mkdir(exist_ok=True, parents=True)
    names = list(dict.fromkeys(n for names in SCENARIOS.values() for n in names))
    summaries = {n: read(B / 'remote_analysis' / n / 'summary.json') for n in names}
    assert len([n for n in names if n.startswith('v11_')]) == 22
    assert all(s['final_evaporation_h'] == 24 for s in summaries.values())
    assert all(s['frames'] == 145 for s in summaries.values())
    sources = []
    acceptance = []
    a_archive = read(ROOT / 'model_revision_plan/20261030_opus_campaign/COORDINATOR_A_FINAL_REVIEW.json')
    assert a_archive['all_checks_pass']
    for n in names:
        sp = B / 'remote_analysis' / n / 'summary.json'
        s = summaries[n]
        sources.append({'path': str(sp.resolve()), 'sha256': sha(sp)})
        row = {'case': n, 'final_h': s['final_evaporation_h'], 'frames': s['frames'],
               'max_native_relative_budget_error': max(s['max_relative_budget_residual'].values()),
               'max_executor_raw_field_salt_error': s['max_field_to_ledger_salt_relative_error'],
               'archive_verified': None, 'zero_interface_max_abs': None, 'wall_h': None}
        assert row['max_native_relative_budget_error'] < 1e-6
        assert row['max_executor_raw_field_salt_error'] < 1e-6
        if n.startswith('A_'):
            row['archive_verified'] = a_archive['archive_executor_verification']['cases'][n[2:]]['status'] == 'verified'
            assert row['archive_verified']
        if n.startswith('v11_'):
            status = read(B / 'remote_status' / f'{n}.json')
            assert status['state'] == 'completed' and status['acceptance']['status'] == 'passed'
            assert status['acceptance']['max_precip_vf'] == 0
            ap = B / 'runs_archive' / n / 'ARCHIVE_MANIFEST.json'
            archive = read(ap)
            assert archive['status'] == 'verified' and not archive['mismatches'] and not archive['gzip_record_mismatches']
            row['archive_verified'] = True
            row['wall_h'] = status['wall_h']
            sources.extend({'path': str(p.resolve()), 'sha256': sha(p)} for p in [ap, B / 'remote_status' / f'{n}.json'])
            if '_C0B' in n:
                cp = B / 'runs_archive' / n / 'causal_budget.csv'
                with cp.open() as f:
                    rows = list(csv.DictReader(f))
                cols = [k for k in rows[0] if k.startswith('if_') and 'salt' in k]
                row['zero_interface_max_abs'] = max(abs(float(r[k])) for r in rows for k in cols)
                assert len(cols) == 32 and row['zero_interface_max_abs'] == 0
        acceptance.append(row)

    effects = []
    for label, cases in SCENARIOS.items():
        for t in ['0', '2', '4', '8', '12', '24']:
            for side in ['F36', 'W3']:
                for band in ['0_2', '0_3', '3_10', '10_20', '20_40', '0_40']:
                    key = f'{side}_salt_g_{band}mm'
                    stocks = [summaries[n]['at'][t][key] for n in cases]
                    e1 = stocks[0] - stocks[1]
                    e0 = stocks[2] - stocks[3] if len(stocks) == 4 else None
                    effects.append({'scenario': label, 'time_h': int(t), 'side': side, 'band_mm': band,
                                    'E1_g': e1, 'E0_g': e0, 'interaction_g': e1-e0 if e0 is not None else None})

    comparisons = []
    def compare(label, arm, metric, a, b, tolerance, family):
        rel = abs(a-b)/abs(b) if abs(b) > 1e-12 else None
        comparisons.append({'comparison': label, 'arm': arm, 'family': family, 'metric': metric,
                            'medium_value': a, 'refined_value': b, 'absolute_difference': abs(a-b),
                            'relative_difference': rel, 'working_tolerance': tolerance,
                            'within_working_tolerance': rel <= tolerance if rel is not None and tolerance is not None else None})

    for label in ['fine', 'dt150']:
        for i, n in enumerate(SCENARIOS[label]):
            arm = ['C1B1', 'C0B1', 'C1B0', 'C0B0'][i]
            a = summaries[SCENARIOS['medium'][i]]
            b = summaries[n]
            for side in ['F36', 'W3']:
                for band in ['0_2', '0_3']:
                    k = f'{side}_salt_g_{band}mm'
                    compare(label, arm, k+'_increase', a['at']['24'][k]-a['at']['0'][k], b['at']['24'][k]-b['at']['0'][k], .02, 'surface_inventory')
                for region in ['all', 'core']:
                    for threshold in ['5.0e-09', '1.0e-08', '2.0e-08']:
                        k = f'{side}_{region}_desc_vf_{threshold}'
                        av,bv = a['at']['24'][k], b['at']['24'][k]
                        compare(label, arm, k, av, bv, .05 if bv > .01 else None, 'plume_volume_fraction')
                        onset = f'{side}_{region}_thr{threshold}'
                        av,bv = a['onset_h'][onset], b['onset_h'][onset]
                        delta = abs(av-bv)*60 if av is not None and bv is not None else None
                        comparisons.append({'comparison': label, 'arm': arm, 'family': 'diagnostic_onset', 'metric': onset,
                                            'medium_value': av, 'refined_value': bv, 'absolute_difference': delta,
                                            'relative_difference': None, 'working_tolerance': 10,
                                            'within_working_tolerance': delta <= 10+1e-7 if delta is not None else (True if av is None and bv is None else False)})
                for depth in ['3', '10', '20']:
                    for mode in ['net', 'advgross']:
                        k=f'A_{side}_down_salt_{mode}_cum_mol_at{depth}mm'
                        compare(label, arm, k, a['ledger_at']['24'][k], b['ledger_at']['24'][k], .05, 'vertical_conservative_flux')
            for key in ['A_if_salt_total_cum_net_mol', 'A_if_salt_total_cum_pos_mol', 'A_if_salt_total_cum_neg_mol',
                        'interface_adv_c2f_mol', 'interface_diff_c2f_mol']:
                compare(label, arm, key, a['ledger_at']['24'][key], b['ledger_at']['24'][key], .05, 'interface_conservative_flux')
    write_csv('acceptance.csv', acceptance)
    write_csv('effects_timeseries.csv', effects)
    write_csv('numeric_comparisons.csv', comparisons)
    final_effects = [e for e in effects if e['time_h']==24 and e['side']=='W3' and e['band_mm']=='0_3']
    result = {'generated_utc': datetime.now(timezone.utc).isoformat(), 'sources': sources,
              'acceptance': acceptance, 'W3_24h_primary_effects': final_effects,
              'working_criterion_failures': [r for r in comparisons if r['within_working_tolerance'] is False],
              'comparison_count': len(comparisons),
              'status': 'Coordinator evidence aggregation; original Opus B final report remains blocked by organization access 403.'}
    (OUT / 'joint_evidence.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'cases':len(acceptance),'comparisons':len(comparisons),'failures':len(result['working_criterion_failures']),
                      'effects':final_effects}, indent=2))


if __name__ == '__main__':
    main()
