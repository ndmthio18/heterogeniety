"""Registered numerical gates (DESIGN.md amendment 1) and three-level grid analysis.

Input: analysis/compare/compare.json (tools/compare.py). Output: gates.json, gates.csv,
grid3.csv, envelope.csv in the same directory.
"""
import csv, json, math, sys
from pathlib import Path

SIDES = ['F36', 'W3']
T = ['4', '8', '12', '24']


def rel(test, ref):
    if test is None or ref is None:
        return None
    if ref == 0:
        return 0.0 if test == 0 else math.inf
    return abs(test - ref) / abs(ref)


def gate_rows(ref, test, eff_ref, eff_test, label):
    """ref/test: {'C1': metrics, 'C0': metrics}; eff_*: effect dicts."""
    rows = []

    def add(kind, arm, metric, t, tol, a=None, b=None, abs_only=False):
        k = f'{metric}@{t}'
        if a is None:
            a, b = test[arm].get(k), ref[arm].get(k)
        r = None if abs_only else rel(a, b)
        rows.append({'check': label, 'kind': kind, 'arm': arm, 'metric': metric, 't_h': t, 'test': a, 'ref': b,
                     'abs_diff': None if a is None or b is None else a - b, 'rel_diff': r, 'tol': tol,
                     'pass': None if (r is None or tol is None) else bool(r <= tol)})

    for t in T:
        for arm in ('C1', 'C0'):
            if arm not in ref or arm not in test:
                continue
            for s in SIDES:
                add('surface_change', arm, f'{s}_dinv_0_3mm', t, .02)
                add('surface_inventory', arm, f'{s}_inv_0_3mm', t, .02)
                add('surface_change_0_2', arm, f'{s}_dinv_0_2mm', t, None)
                add('deep_change', arm, f'{s}_ddeep_10_40mm', t, .05)
                add('bottom_salt', arm, f'{s}_bottom_salt_in_g', t, .05)
                for d in ('3', '10', '20'):
                    add('vertical_transport', arm, f'{s}_down_salt_net_{d}mm_g', t, .05)
                a, b = test[arm].get(f'{s}_core_desc_vf_1e-8@{t}'), ref[arm].get(f'{s}_core_desc_vf_1e-8@{t}')
                big = a is not None and b is not None and min(a, b) > .01
                add('core_descending_vf', arm, f'{s}_core_desc_vf_1e-8', t, .05 if big else None, a, b, abs_only=not big)
            if arm == 'C1':
                add('interface_net', arm, 'iface_salt_net_g', t, .05)
                add('interface_pos', arm, 'iface_salt_pos_g', t, .05)
                add('interface_liquid_net', arm, 'iface_liquid_net_mL', t, .05)
        # paired effect
        if eff_ref and eff_test:
            for s in SIDES:
                for metric in (f'{s}_inv_0_3mm', f'{s}_inv_0_2mm', f'{s}_ddeep_10_40mm', f'{s}_bottom_salt_in_g'):
                    k = f'{metric}@{t}'
                    a, b = eff_test.get(k), eff_ref.get(k)
                    small = b is None or abs(b) <= 1e-4
                    rows.append({'check': label, 'kind': 'effect', 'arm': 'E=C1-C0', 'metric': metric, 't_h': t, 'test': a, 'ref': b,
                                 'abs_diff': None if a is None or b is None else a - b,
                                 'rel_diff': None if small else rel(a, b), 'tol': None if small else (.02 if '0_3' in metric or '0_2' in metric else .05),
                                 'pass': None if (small or a is None) else bool(rel(a, b) <= (.02 if '0_3' in metric or '0_2' in metric else .05))})
    # onsets
    for arm in ('C1', 'C0'):
        if arm not in ref or arm not in test:
            continue
        for k in ref[arm]:
            if k.startswith('onset_') and 'thr1.0e-08' in k:
                a, b = test[arm].get(k), ref[arm].get(k)
                ok = (a is None and b is None) or (a is not None and b is not None and abs(a - b) <= 1 / 6 + 1e-9)
                rows.append({'check': label, 'kind': 'onset', 'arm': arm, 'metric': k, 't_h': '-', 'test': a, 'ref': b,
                             'abs_diff': None if a is None or b is None else a - b, 'rel_diff': None, 'tol': '10 min', 'pass': bool(ok)})
    return rows


def grid3(c, m, f, key):
    """Three-level behaviour for a scalar: monotone?, observed order with r=1.5 (indicative)."""
    if None in (c, m, f):
        return None
    d21, d32 = m - c, f - m
    out = {'coarse': c, 'medium': m, 'fine': f, 'd_medium_coarse': d21, 'd_fine_medium': d32,
           'monotone': bool(d21 * d32 > 0 and abs(d32) < abs(d21))}
    if out['monotone']:
        p = math.log(abs(d21) / abs(d32)) / math.log(1.5)
        out['observed_order_r1.5'] = p
        if 0.5 <= p <= 4:
            ext = f + d32 / (1.5 ** p - 1)
            out['richardson_estimate'] = ext
            out['gci_fine_rel'] = 1.25 * abs(d32 / f) / (1.5 ** p - 1) if f else None
    return out


def main(cmp_path):
    cmp = json.loads(Path(cmp_path).read_text())
    out = Path(cmp_path).parent
    cases, eff = cmp['cases'], cmp['effects']
    rows = []
    full = lambda k: len(cases.get(k, {})) == 2
    if full('G_fine') and full('MEDIUM'):
        rows += gate_rows(cases['G_fine'], cases['MEDIUM'], eff.get('G_fine'), eff.get('MEDIUM'), 'medium->fine')
    if full('T150') and full('MEDIUM'):
        rows += gate_rows(cases['T150'], cases['MEDIUM'], eff.get('T150'), eff.get('MEDIUM'), 'dt300->150')
    if full('G_coarse') and full('MEDIUM'):
        rows += gate_rows(cases['MEDIUM'], cases['G_coarse'], eff.get('MEDIUM'), eff.get('G_coarse'), 'coarse->medium (info)')
    with open(out / 'gates.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ['check'])
        w.writeheader()
        w.writerows(rows)
    g3 = {}
    if all(len(cases.get(k, {})) == 2 for k in ('G_coarse', 'MEDIUM', 'G_fine')):
        for arm in ('C1', 'C0'):
            for k in cases['MEDIUM'].get(arm, {}):
                if k.endswith('@24') and not k.startswith('onset'):
                    r = grid3(cases['G_coarse'][arm].get(k), cases['MEDIUM'][arm].get(k), cases['G_fine'][arm].get(k), k)
                    if r:
                        g3[f'{arm}:{k}'] = r
        for k in eff.get('MEDIUM', {}):
            if k.endswith('@24'):
                r = grid3(eff['G_coarse'].get(k), eff['MEDIUM'].get(k), eff['G_fine'].get(k), k)
                if r:
                    g3[f'E:{k}'] = r
    summary = {}
    for r in rows:
        key = (r['check'], r['kind'])
        s = summary.setdefault(f'{key[0]}|{key[1]}', {'n': 0, 'pass': 0, 'fail': 0, 'na': 0, 'worst_rel': 0})
        s['n'] += 1
        if r['pass'] is True:
            s['pass'] += 1
        elif r['pass'] is False:
            s['fail'] += 1
        else:
            s['na'] += 1
        if isinstance(r['rel_diff'], float) and r['tol'] not in (None, '10 min'):
            s['worst_rel'] = max(s['worst_rel'], r['rel_diff'])
    (out / 'gates.json').write_text(json.dumps({'summary': summary, 'grid3': g3}, indent=1, default=str))
    return summary, g3


if __name__ == '__main__':
    s, g = main(sys.argv[1])
    print(json.dumps(s, indent=1))
