"""Markdown tables for VERIFICATION_REPORT.md from analysis/compare*/ outputs.

Usage: python report_tables.py COMPARE_DIR OUT_MD [registry.json]
"""
import csv, json, sys
from pathlib import Path

T = ['2', '4', '8', '12', '24']


def fmt(x, n=5):
    if x is None or x == '':
        return '–'
    try:
        x = float(x)
    except (TypeError, ValueError):
        return str(x)
    return f'{x:+.{n}f}' if abs(x) < 10 else f'{x:.3g}'


def pct(x):
    if x in (None, ''):
        return '–'
    return f'{100 * float(x):.2f} %'


def main(cdir, out, reg_path=None):
    cdir = Path(cdir)
    c = json.loads((cdir / 'compare.json').read_text())
    reg = json.loads(Path(reg_path).read_text()) if reg_path else {}
    eff = c['effects']
    L = []
    L.append('| case | ' + ' | '.join(f'E_W3 0–3 mm {t} h' for t in T) + ' | E_W3 0–2 mm 24 h | E_F36 0–3 mm 24 h | E_W3 3–10 mm 24 h | E_total 24 h |')
    L.append('|---|' + '---:|' * (len(T) + 4))
    for p, e in eff.items():
        lab = reg.get(p, {}).get('label', p)
        L.append(f'| {lab} | ' + ' | '.join(fmt(e.get(f'W3_inv_0_3mm@{t}')) for t in T) +
                 f" | {fmt(e.get('W3_inv_0_2mm@24'))} | {fmt(e.get('F36_inv_0_3mm@24'))} | {fmt(e.get('W3_inv_3_10mm@24'))} | {fmt(e.get('total_salt_g@24'))} |")
    L.append('')
    env = c['envelope']
    L.append('| metric (24 h, g) | min over cases | max over cases | n | sign change |')
    L.append('|---|---:|---:|---:|---|')
    for k in ['W3_inv_0_3mm@24', 'W3_inv_0_2mm@24', 'W3_inv_0_3mm@12', 'F36_inv_0_3mm@24', 'W3_inv_3_10mm@24', 'W3_ddeep_10_40mm@24', 'F36_ddeep_10_40mm@24',
              'W3_bottom_salt_in_g@24', 'F36_bottom_salt_in_g@24', 'iface_salt_net_g@24', 'total_salt_g@24']:
        if k in env:
            v = env[k]
            L.append(f"| {k} | {fmt(v['min'])} | {fmt(v['max'])} | {v['n']} | {'yes' if v['sign_change'] else 'no'} |")
    L.append('')
    if (cdir / 'gates.csv').exists():
        rows = list(csv.DictReader(open(cdir / 'gates.csv')))
        L.append('| check | kind | arm | metric | t (h) | test | reference | abs diff | rel diff | tol | pass |')
        L.append('|---|---|---|---|---|---:|---:|---:|---:|---|---|')
        for r in rows:
            if r['t_h'] in ('24', '-') and r['kind'] not in ('surface_change_0_2',):
                L.append(f"| {r['check']} | {r['kind']} | {r['arm']} | {r['metric']} | {r['t_h']} | {fmt(r['test'])} | {fmt(r['ref'])} | {fmt(r['abs_diff'], 6)} | {pct(r['rel_diff'])} | {r['tol'] or '–'} | {r['pass']} |")
    Path(out).write_text('\n'.join(L) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main(*sys.argv[1:4])
