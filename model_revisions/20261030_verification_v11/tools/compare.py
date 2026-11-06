"""Paired-effect and convergence tables for v11 (Opus B).

Input: a JSON registry {pair_id: {"C1": summary_dir, "C0": summary_dir, "label": ...}}
Output: analysis/compare/{effects.csv, gates.csv, effect_envelope.csv, compare.json}
Only reads summary.json produced by tools/metrics.py (same code for every case).
"""
import csv, json, sys
from pathlib import Path
import numpy as np

T = ['0', '2', '4', '8', '12', '24']
SIDES = ['F36', 'W3']
INV = ['0_2mm', '0_3mm', '3_10mm', '10_20mm', '20_40mm', '0_40mm']


def load(d):
    return json.loads((Path(d) / 'summary.json').read_text())


def frame(s, t):
    return s['at'][t]


def inv(s, side, band, t):
    return frame(s, t)[f'{side}_salt_g_{band}']


def deep_change(s, side, t):
    f, f0 = frame(s, t), frame(s, '0')
    return sum(f[f'{side}_salt_g_{b}'] - f0[f'{side}_salt_g_{b}'] for b in ['10_20mm', '20_40mm'])


def case_metrics(s):
    """Per-case scalar metrics used by the gates (registered in DESIGN.md amendment 1)."""
    m = {}
    for t in T:
        f, f0, L = frame(s, t), frame(s, '0'), s['ledger_at'][t]
        for side in SIDES:
            for b in INV:
                m[f'{side}_inv_{b}@{t}'] = f[f'{side}_salt_g_{b}']
                m[f'{side}_dinv_{b}@{t}'] = f[f'{side}_salt_g_{b}'] - f0[f'{side}_salt_g_{b}']
            m[f'{side}_ddeep_10_40mm@{t}'] = deep_change(s, side, t)
            m[f'{side}_bottom_salt_in_g@{t}'] = L[f'{side}_bottom_salt_in_mol'] * 58.443
            m[f'{side}_evap_water_g@{t}'] = L[f'{side}_evap_water_g']
            m[f'{side}_core_desc_vf_1e-8@{t}'] = f[f'{side}_core_desc_vf_1.0e-08']
            m[f'{side}_core_rms_anom@{t}'] = f[f'{side}_core_rms_anomaly_mol_L']
            m[f'{side}_enriched_dC0.1@{t}'] = f[f'{side}_enriched_depth_mm_dC0.1']
        m[f'iface_net_c2f_g@{t}'] = (L['interface_adv_c2f_mol'] + L['interface_diff_c2f_mol']) * 58.443
        m[f'iface_adv_c2f_g@{t}'] = L['interface_adv_c2f_mol'] * 58.443
        m[f'iface_diff_c2f_g@{t}'] = L['interface_diff_c2f_mol'] * 58.443
        m[f'total_salt_g@{t}'] = f['total_salt_g']
        # assembled A-snapshot diagnostics (present for every production case)
        if 'A_if_salt_total_cum_net_mol' in L:
            for q in ('net', 'pos', 'neg'):
                m[f'iface_salt_{q}_g@{t}'] = L[f'A_if_salt_total_cum_{q}_mol'] * 58.443
                m[f'iface_liquid_{q}_mL@{t}'] = L[f'A_if_liquid_volume_total_cum_{q}_m3'] * 1e6
            for b in ('0_2', '2_10', '10_20', '20_40'):
                m[f'iface_salt_net_{b}mm_g@{t}'] = sum(L[f'A_if_{md}_salt_{b}mm_cum_net_mol'] for md in ('adv', 'diff')) * 58.443
            for side in SIDES:
                m[f'{side}_bottom_water_in_g@{t}'] = L[f'A_{side}_cum_bottom_water_in_mol'] * 18.015
                m[f'{side}_bottom_salt_gross_in_g@{t}'] = L[f'A_{side}_cum_bottom_salt_gross_in_mol'] * 58.443
                m[f'{side}_bottom_salt_gross_out_g@{t}'] = L[f'A_{side}_cum_bottom_salt_gross_out_mol'] * 58.443
                for d in ('3', '10', '20'):
                    m[f'{side}_down_salt_net_{d}mm_g@{t}'] = L[f'A_{side}_down_salt_net_cum_mol_at{d}mm'] * 58.443
    for k, v in s['onset_h'].items():
        m[f'onset_{k}'] = v
    m['max_budget_residual'] = max(s['max_relative_budget_residual'].values())
    m['field_ledger_err'] = s['max_field_to_ledger_salt_relative_error']
    return m


def effect(m1, m0):
    return {k: (m1[k] - m0[k]) if isinstance(m1.get(k), float) and isinstance(m0.get(k), float) else None for k in m1 if not k.startswith('onset')}


def rel(a, b):
    if a is None or b is None:
        return None
    return abs(a - b) / abs(b) if b != 0 else (0.0 if a == b else float('inf'))


def main(reg_path, out):
    reg = json.loads(Path(reg_path).read_text())
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    cases, effects = {}, {}
    for pid, p in reg.items():
        c = {}
        for arm in ('C1', 'C0'):
            if p.get(arm) and (Path(p[arm]) / 'summary.json').exists():
                c[arm] = case_metrics(load(p[arm]))
        cases[pid] = c
        if 'C1' in c and 'C0' in c:
            effects[pid] = effect(c['C1'], c['C0'])
    keys = sorted({k for e in effects.values() for k in e})
    with open(out / 'effects.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['metric'] + list(effects))
        for k in keys:
            w.writerow([k] + [effects[p].get(k) for p in effects])
    with open(out / 'cases.csv', 'w', newline='') as f:
        w = csv.writer(f)
        cols = [(p, a) for p in cases for a in cases[p]]
        w.writerow(['metric'] + [f'{p}:{a}' for p, a in cols])
        allk = sorted({k for p, a in cols for k in cases[p][a]})
        for k in allk:
            w.writerow([k] + [cases[p][a].get(k) for p, a in cols])
    # envelope of E over all available pairs
    env = {}
    for k in keys:
        vals = [effects[p][k] for p in effects if effects[p].get(k) is not None]
        if vals:
            env[k] = {'min': min(vals), 'max': max(vals), 'n': len(vals), 'sign_change': bool(min(vals) < 0 < max(vals)),
                      'pairs': {p: effects[p][k] for p in effects if effects[p].get(k) is not None}}
    (out / 'compare.json').write_text(json.dumps({'cases': cases, 'effects': effects, 'envelope': env}, indent=1, default=str))
    return cases, effects, env


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
