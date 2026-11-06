"""Deterministic post-processing of everything completed so far (Opus B, v11).

Re-runnable at any time: pulls reduced remote analysis, rebuilds B1 and B0
comparisons, gates, tables, figures and the perturbation/parameter summaries.
Does not touch running solvers. Usage: python finalize.py [--no-pull]
"""
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
T = ROOT / 'tools'
sys.path.insert(0, str(T))


def run(*a):
    subprocess.run([sys.executable, *map(str, a)], check=True, cwd=ROOT)


def main(pull=True):
    if pull:
        import sync
        (ROOT / 'remote_status').mkdir(exist_ok=True)
        sync.pull_analysis()
    reg0 = {'MEDIUM': {'label': 'medium dt300 B0 (A C1B0/C0B0)', 'C1': 'remote_analysis/A_C1B0_24h', 'C0': 'remote_analysis/A_C0B0_24h'},
            'G_fine': {'label': 'fine B0', 'C1': 'remote_analysis/v11_G_fine_C1B0', 'C0': 'remote_analysis/v11_G_fine_C0B0'},
            'T150': {'label': 'medium dt150 B0', 'C1': 'remote_analysis/v11_T150_C1B0', 'C0': 'remote_analysis/v11_T150_C0B0'}}
    (ROOT / 'analysis' / 'registry_B0.json').write_text(json.dumps(reg0, indent=1))
    for tag, reg in [('compare', 'analysis/registry_B1.json'), ('compare_B0', 'analysis/registry_B0.json')]:
        run(T / 'compare.py', reg, f'analysis/{tag}')
        run(T / 'gates.py', f'analysis/{tag}/compare.json')
        run(T / 'report_tables.py', f'analysis/{tag}', f'report_parts/tables_{tag}.md', reg)
    run(T / 'plots.py', 'analysis/registry_B1.json', 'analysis/figures')
    run(T / 'plots.py', 'analysis/registry_B0.json', 'analysis/figures_B0')
    # interaction E1-E0 across the numerical variants present in both registries
    c1 = json.loads((ROOT / 'analysis/compare/compare.json').read_text())['effects']
    c0 = json.loads((ROOT / 'analysis/compare_B0/compare.json').read_text())['effects']
    inter = {}
    for p in ('MEDIUM', 'G_fine', 'T150'):
        if p in c1 and p in c0:
            inter[p] = {k: c1[p][k] - c0[p][k] for k in c1[p] if k in c0[p] and c1[p][k] is not None and c0[p][k] is not None
                        and any(s in k for s in ('W3_inv_0_3mm', 'F36_inv_0_3mm', 'W3_inv_0_2mm', 'total_salt_g'))}
    (ROOT / 'analysis/interaction.json').write_text(json.dumps(inter, indent=1))
    # perturbation bookkeeping per case (seed partition impulses, t=0 layer-anomaly RMS)
    pert = {}
    for d in sorted((ROOT / 'remote_analysis').glob('*')):
        s = d / 'summary.json'
        if s.exists():
            j = json.loads(s.read_text())
            if 'at' in j and j['at'].get('0'):
                f0 = j['at']['0']
                pert[d.name] = {'F36_t0_rms_layer_anomaly_mol_L': f0.get('F36_all_rms_anomaly_mol_L'),
                                'W3_t0_rms_layer_anomaly_mol_L': f0.get('W3_all_rms_anomaly_mol_L'),
                                'seed_impulse_mol_F36_W3': [j['ledger_at']['24'].get('F36_seed_impulse_mol'), j['ledger_at']['24'].get('W3_seed_impulse_mol')],
                                'cells': j.get('cells'), 'max_rel_budget_residual': max(j['max_relative_budget_residual'].values()),
                                'field_ledger': j.get('max_field_to_ledger_salt_relative_error'), 'final_h': j.get('final_evaporation_h')}
    (ROOT / 'analysis/perturbation_and_acceptance.json').write_text(json.dumps(pert, indent=1))
    print(json.dumps({'interaction_pairs': list(inter), 'cases_summarised': len(pert)}))


if __name__ == '__main__':
    main('--no-pull' not in sys.argv)
