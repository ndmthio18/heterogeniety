"""Assemble VERIFICATION_REPORT.md from computed outputs (re-runnable; Opus B v11).

The report states its own completion status from remote_status/*.json; it only
says "final" when every queued case is terminal.
"""
import csv, datetime, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUEUE = ['G_coarse', 'T150', 'G_fine', 'S2', 'S3', 'A3e-6', 'A3e-5', 'P1', 'P2']
B0Q = ['G_fine', 'T150']


def J(p):
    p = ROOT / p
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else None


def st(name):
    return J(f'remote_status/{name}.json') or {}


def f(x, n=5, sign=True):
    if x is None:
        return '–'
    return (f'{x:+.{n}f}' if sign else f'{x:.{n}f}')


def pct(a, b):
    return '–' if a is None or b in (None, 0) else f'{abs(a - b) / abs(b) * 100:.2f} %'


def main():
    now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    cmp1, cmp0 = J('analysis/compare/compare.json'), J('analysis/compare_B0/compare.json')
    g1, g0 = J('analysis/compare/gates.json'), J('analysis/compare_B0/gates.json')
    E, C = cmp1['effects'], cmp1['cases']
    E0 = cmp0['effects'] if cmp0 else {}
    inter = J('analysis/interaction.json') or {}
    pert = J('analysis/perturbation_and_acceptance.json') or {}
    runs = {}
    for cid, b in [(q, 'B1') for q in QUEUE] + [(q, 'B0') for q in B0Q]:
        for arm in ('C1', 'C0'):
            n = f'v11_{cid}_{arm}{b}'
            s = st(n)
            runs[n] = s.get('state', 'queued')
    terminal = all(v in ('completed', 'failed', 'interrupted') for v in runs.values())
    done = [k for k, v in runs.items() if v == 'completed']
    failed = [k for k, v in runs.items() if v in ('failed', 'interrupted')]
    L = []
    A = L.append
    A('# VERIFICATION_REPORT — v11 grid / time-step / perturbation / parameter checks of the connection effect (Opus B)')
    A('')
    A(f'Generated {now} by `tools/build_report.py` (model claude-opus-5-5). Protocol: `model_revision_plan/20261030_opus_campaign/PLAN.md`; pre-registration `DESIGN.md` (hash log `DESIGN.registered.sha256`).')
    A('')
    A(f"**Report status: {'FINAL — all queued cases terminal' if terminal else 'IN PROGRESS — not a final report; queued cases still running'}.** Completed new production runs: {len(done)}/{len(runs)}; failed/interrupted: {len(failed)} {failed if failed else ''}.")
    A('')
    A('| run | state | wall (h) | accepted steps | max rel. residual |')
    A('|---|---|---:|---:|---:|')
    for n, v in runs.items():
        s = st(n)
        a = s.get('acceptance') or {}
        A(f"| {n} | {v} | {f(s.get('wall_h'), 2, False) if s.get('wall_h') else '–'} | {a.get('accepted_steps', '–')} | {('%.1e' % max(a['max_relative_residuals'].values())) if a.get('max_relative_residuals') else '–'} |")
    A('')
    A('Reused medium baselines (A, handoff `causal_v10c`, identity verified: binary cb57a841…, inputs per snapshot manifest, mesh fc30b952…): C1B1_24h, C0B1_24h, C1B0_24h, C0B0_24h; extracted with the same B extractor. C1B1_24h equals v08 Dry_trial02_r02 in every B frame metric (difference 0.0).')
    A('')
    # ---- 1 summary
    A('## 1. Summary (numbers from this batch; inference limits in §8)')
    A('')
    m = E['MEDIUM']
    A(f"- Primary effect E_1 = S_W3,0–3mm(C1,B1) − S_W3,0–3mm(C0,B1), medium/dt300/seed1/σ1e-5: {f(m['W3_inv_0_3mm@2'])}, {f(m['W3_inv_0_3mm@4'])}, {f(m['W3_inv_0_3mm@8'])}, {f(m['W3_inv_0_3mm@12'])}, {f(m['W3_inv_0_3mm@24'])} g at 2/4/8/12/24 h (NaCl 58.443 g/mol; A uses 58.4428, ratio 1+3.422e-6).")
    for p, lab in [('T150', 'dt 300→150 s'), ('G_fine', 'medium→fine grid'), ('G_coarse', 'coarse (info)')]:
        if p in E:
            A(f"- {lab}: E_1(24 h) {f(E[p]['W3_inv_0_3mm@24'])} g vs medium {f(m['W3_inv_0_3mm@24'])} g ({pct(m['W3_inv_0_3mm@24'], E[p]['W3_inv_0_3mm@24']) if p != 'G_coarse' else pct(E[p]['W3_inv_0_3mm@24'], m['W3_inv_0_3mm@24'])} relative to the {'finer' if p != 'G_coarse' else 'medium'} reference).")
    pp = [p for p in ('S2', 'S3', 'A3e-6', 'A3e-5') if p in E]
    if pp:
        A('- Perturbation phase/amplitude pairs available: ' + ', '.join(f"{p}: E_1(24 h) {f(E[p]['W3_inv_0_3mm@24'])} g" for p in pp) + '.')
    pq = [p for p in ('P1', 'P2') if p in E]
    if pq:
        A('- Measured-Ks endpoint pairs: ' + ', '.join(f"{p}: E_1(24 h) {f(E[p]['W3_inv_0_3mm@24'])} g" for p in pq) + '.')
    if inter:
        A('- Interaction E_1−E_0 (W3 0–3 mm, 24 h): ' + ', '.join(f"{p}: {f(v.get('W3_inv_0_3mm@24'))} g" for p, v in inter.items()) + '.')
    env = cmp1['envelope'].get('W3_inv_0_3mm@24')
    if env:
        A(f"- Finite scenario envelope of E_1(24 h) over the {env['n']} available B1 pairs: {f(env['min'])} … {f(env['max'])} g; sign change: {'yes' if env['sign_change'] else 'no'}. This is a range over registered numerical/parameter variants, not a confidence interval.")
    A('- Working tolerances not met medium→fine (kept as failures, no tolerance/physics change): see §4.1 table (F36 surface-change 2.28 %/2.37 %, F36 surface effect, F36 deep effect, connected F36 core descending volume fraction 47.8 %, W3 net vertical transport at 3 mm in C1).')
    A('')
    for part in ['01_methods.md']:
        p = ROOT / 'report_parts' / part
        if p.exists():
            L.extend(p.read_text(encoding='utf-8').splitlines())
            A('')
    # ---- grid
    A('## 4. Results')
    A('')
    A('### 4.1 Grid (B=1, connected/disconnected pairs; coarse 10368, medium 30720, fine 103680 cells)')
    A('')
    if 'G_fine' in E:
        g3 = g1['grid3']
        A('| quantity (24 h, g) | coarse | medium | fine | medium→fine rel | three-level |')
        A('|---|---:|---:|---:|---:|---|')
        for k, l in [('W3_inv_0_3mm', 'E W3 0–3 mm'), ('W3_inv_0_2mm', 'E W3 0–2 mm'), ('F36_inv_0_3mm', 'E F36 0–3 mm'), ('W3_inv_3_10mm', 'E W3 3–10 mm'),
                     ('W3_ddeep_10_40mm', 'E W3 Δ10–40 mm'), ('F36_ddeep_10_40mm', 'E F36 Δ10–40 mm'), ('W3_bottom_salt_in_g', 'E W3 bottom salt supply'), ('total_salt_g', 'E total salt')]:
            v = [E[p].get(f'{k}@24') for p in ('G_coarse', 'MEDIUM', 'G_fine')]
            gg = g3.get(f'E:{k}@24', {})
            mono = 'monotone' if gg.get('monotone') else 'non-monotone'
            if gg.get('observed_order_r1.5') is not None:
                mono += f", apparent order {gg['observed_order_r1.5']:.2f}"
            if gg.get('gci_fine_rel') is not None:
                mono += f", GCI_fine {100 * gg['gci_fine_rel']:.2f} % (indicative; non-uniform refinement)"
            A(f'| {l} | {f(v[0])} | {f(v[1])} | {f(v[2])} | {pct(v[1], v[2])} | {mono} |')
        A('')
        A('| per-arm quantity (24 h) | arm | coarse | medium | fine | medium→fine rel |')
        A('|---|---|---:|---:|---:|---:|')
        for k, l in [('W3_dinv_0_3mm', 'W3 Δ0–3 mm (g)'), ('F36_dinv_0_3mm', 'F36 Δ0–3 mm (g)'), ('F36_ddeep_10_40mm', 'F36 Δ10–40 mm (g)'), ('iface_salt_net_g', 'interface net salt c→f (g)'),
                     ('W3_down_salt_net_3mm_g', 'W3 net downward salt @3 mm (g)'), ('F36_down_salt_net_10mm_g', 'F36 net downward salt @10 mm (g)'), ('F36_core_desc_vf_1e-8', 'F36 core descending volume fraction (–)')]:
            for arm in ('C1', 'C0'):
                v = [C[p][arm].get(f'{k}@24') for p in ('G_coarse', 'MEDIUM', 'G_fine')]
                if None in v:
                    continue
                A(f'| {l} | {arm} | {v[0]:.5f} | {v[1]:.5f} | {v[2]:.5f} | {pct(v[1], v[2])} |')
        A('')
        A('Persistent-downflow onset (1e-8 m/s, 3 frames), F36 [all, core] h: ' + '; '.join(
            f"{p} {arm} [{C[p][arm].get('onset_F36_all_thr1.0e-08')}, {C[p][arm].get('onset_F36_core_thr1.0e-08')}]" for p in ('G_coarse', 'MEDIUM', 'G_fine') for arm in ('C1', 'C0')) + '. W3: none in any case.')
        A('')
        s = g1['summary']
        A('Registered gate counts medium→fine (pass/fail/n.a.): ' + '; '.join(f"{k.split('|')[1]} {v['pass']}/{v['fail']}/{v['na']}" for k, v in s.items() if k.startswith('medium->fine')) + '. Full rows: `analysis/compare/gates.csv`.')
        A('')
    p = ROOT / 'report_parts' / '04_dt.md'
    if p.exists():
        L.extend(p.read_text(encoding='utf-8').splitlines())
        A('')
    # ---- perturbation
    A('### 4.3 Perturbation phase (seed 2, 3) and amplitude (σ 3e-6, 3e-5), medium, dt 300')
    A('')
    A('| pair | E W3 0–3 mm 4 h | 12 h | 24 h | E W3 0–2 mm 24 h | E F36 0–3 mm 24 h | onset F36 core C1/C0 (h) |')
    A('|---|---:|---:|---:|---:|---:|---|')
    for p in ['MEDIUM', 'S2', 'S3', 'A3e-6', 'A3e-5']:
        if p in E:
            A(f"| {p} | {f(E[p]['W3_inv_0_3mm@4'])} | {f(E[p]['W3_inv_0_3mm@12'])} | {f(E[p]['W3_inv_0_3mm@24'])} | {f(E[p]['W3_inv_0_2mm@24'])} | {f(E[p]['F36_inv_0_3mm@24'])} | {fmt(C[p]['C1'].get('onset_F36_core_thr1.0e-08'),2,False)}/{fmt(C[p]['C0'].get('onset_F36_core_thr1.0e-08'),2,False)} |")
        else:
            A(f'| {p} | pending | | | | | |')
    A('')
    A('### 4.4 Parameter endpoints (measured Ks replicate range; §6)')
    A('')
    for p in ['P1', 'P2']:
        A(f"- {p}: " + (f"E_1(W3 0–3 mm) {f(E[p]['W3_inv_0_3mm@12'])} g at 12 h, {f(E[p]['W3_inv_0_3mm@24'])} g at 24 h; E F36 0–3 mm 24 h {f(E[p]['F36_inv_0_3mm@24'])} g." if p in E else 'pending'))
    A('')
    A('### 4.5 B=0 extension (interaction), fine grid and dt 150 s')
    A('')
    if E0:
        for p in ['MEDIUM', 'G_fine', 'T150']:
            if p in E0:
                A(f"- {p}: E_0(W3 0–3 mm, 24 h) {f(E0[p]['W3_inv_0_3mm@24'])} g; E_1−E_0 {f(inter.get(p, {}).get('W3_inv_0_3mm@24'))} g.")
            else:
                A(f'- {p}: pending')
    A('')
    for part in ['03_parameters.md']:
        p = ROOT / 'report_parts' / part
        if p.exists():
            L.extend(p.read_text(encoding='utf-8').splitlines())
            A('')
    A('## 7. Archive, hashes, resources')
    A('')
    arch = sorted((ROOT / 'runs_archive').glob('*/ARCHIVE_MANIFEST.json'))
    A(f'- {len(arch)} run directories archived to `runs_archive/` with per-file SHA256 verified on both ends; large verified files then released individually on liqin (`RELEASED_INDEX.json` kept remotely and locally).')
    A('- Perturbation bookkeeping and acceptance per extracted case: `analysis/perturbation_and_acceptance.json`.')
    A('')
    A('## 8. Inference limits')
    A('')
    A('- Grid/time-step/perturbation results are a finite scenario envelope of registered variants; they are not confidence intervals and do not cover unknown errors. Passing them is not parameter robustness and not experimental validation.')
    A('- Parameter coverage: only the measured Ks replicate range (separate lab packings, a lower bound on column uncertainty). No interval exists for D0/tortuosity/D_eff, dispersion or retention parameters; porosity corners were registered as not run. Hence no claim that the effect exceeds parameter uncertainty in general can be made.')
    A('- Plume-structure metrics (core descending fraction) are grid-sensitive and non-monotone; plume structure is not grid-converged even where inventories are.')
    (ROOT / 'VERIFICATION_REPORT.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
    print(json.dumps({'terminal': terminal, 'completed': len(done), 'total': len(runs)}))


if __name__ == '__main__':
    main()
