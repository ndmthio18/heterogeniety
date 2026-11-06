"""Model-native metrics for one completed run directory (Opus B, verification_v11).

Works with plain or gzip-compressed VTU frames, any cylinder mesh of the v11
family, and both the v08 budget.csv and any extended budget columns supplied by
the A handoff (detected by name, never assumed). numpy + stdlib only.

Conventions (pre-registered in VERIFICATION_REPORT.md before variant results):
  * clock: evaporation time t = timestep/3600 - PreEquilibrationSeconds/3600; no shifting.
  * side: cell DOF position (circumcentre) x < SplitCoordinate is coarse (F36),
    otherwise fine (W3). Cells never straddle the material plane in this family.
  * depth bands by exact vertical overlap of each (vertically extruded) prism
    with the band; inventories are NaCl-equivalent grams (dissolved + solid).
  * band mean concentration = band salt mol / band liquid volume (mol/L).
  * plume: LS interior Darcy velocity, q_down = -v_y; thresholds 0.5/1/2 e-8 m/s,
    persistent if exceeded on 3 consecutive saved frames at t>=0.5 h;
    core mask r<20 mm, |x-25 mm|>3 mm, 5<depth<35 mm (as v08).
  * enriched depth: deepest 1-mm actual-overlap bin whose pore-weighted mean C
    exceeds the side's t=0 pore-weighted mean by +0.02 and +0.1 mol/L.
Usage: python metrics.py RUN_DIR OUT_DIR [--selected]
"""
import configparser, csv, gzip, hashlib, json, sys, xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np

M_NACL = 0.058443  # kg/mol, NaCl molar mass used for g-equivalent reporting
M_H2O = 0.018015
BANDS = [(0, 2), (0, 3), (3, 10), (10, 20), (20, 40), (0, 40)]
THRESH = [0.5e-8, 1e-8, 2e-8]
REPORT_T = [0, 2, 4, 8, 12, 24]
SIDES = ['F36', 'W3']


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()


def open_frame(path):
    path = Path(path)
    if path.exists():
        return open(path, 'rb'), path
    gz = Path(str(path) + '.gz')
    if gz.exists():
        return gzip.open(gz, 'rb'), gz
    raise FileNotFoundError(path)


def read_fields(path):
    f, real = open_frame(path)
    with f:
        tree = ET.parse(f)
    out = {}
    for e in tree.findall('.//CellData/DataArray'):
        a = np.fromstring(e.text or '', sep=' ')
        n = int(e.get('NumberOfComponents', '1'))
        out[e.get('Name')] = a if n == 1 else a.reshape(-1, n)
    return out, real


def read_csv(path):
    lines = Path(path).read_text().splitlines()
    head = lines[0].split(',')
    rows = [l.split(',') for l in lines[1:] if len(l.split(',')) == len(head)]
    arr = np.array(rows, dtype=float)
    return {h: arr[:, i] for i, h in enumerate(head)}


def overlap(lo, hi, a, b):
    return np.clip(np.minimum(hi, b) - np.maximum(lo, a), 0, None) / (hi - lo)


def main(run, out, selected=False):
    run, out = Path(run), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    cfg = configparser.ConfigParser()
    cfg.read(next(p for p in run.glob('*.input')))
    name = cfg['Problem']['Name']
    pre_h = float(cfg['Revision']['PreEquilibrationSeconds']) / 3600
    split = float(cfg['SpatialParams'].get('SplitCoordinate', '0.025'))
    pvd = run / (name + ('_selected.pvd' if selected else '.pvd'))
    entries = [(float(e.get('timestep')), e.get('file')) for e in ET.parse(pvd).findall('.//DataSet')]
    g = read_csv(run / 'cell_geometry.csv')
    order = np.argsort(g['dof_m' if 'dof_m' in g else 'dof'])
    G = {k: v[order] for k, v in g.items()}
    assert np.array_equal(G['dof'].astype(int), np.arange(len(order)))
    H = float(G['ymax_m'].max())
    f0, _ = read_fields(run / entries[0][1])
    ids = np.rint(f0['dof_id']).astype(int)
    assert len(np.unique(ids)) == len(ids)
    x, y, z, vol = G['x_m'][ids], G['y_m'][ids], G['z_m'][ids], G['volume_m3'][ids]
    dlo, dhi = (H - G['ymax_m'][ids]) * 1e3, (H - G['ymin_m'][ids]) * 1e3
    depth = (H - y) * 1e3
    side = [x < split, x >= split]
    radial = np.hypot(x - split, z)
    core = (radial < .020) & (np.abs(x - split) > .003) & (depth > 5) & (depth < 35)
    band_w = {b: overlap(dlo, dhi, *b) * vol for b in BANDS}
    bins = np.array([overlap(dlo, dhi, k, k + 1) * vol for k in range(int(round(H * 1e3)))])
    _, layer = np.unique(np.round(y, 12), return_inverse=True)
    nlayer = layer.max() + 1

    budget = read_csv(run / 'budget.csv')
    seed = json.loads((run / 'seed_event.json').read_text()) if (run / 'seed_event.json').exists() else None
    btime = budget['time_s']

    frames, sources, inv_err = [], [], []
    C0side = None
    for ts, fn in entries:
        t = ts / 3600 - pre_h
        if t < -1e-9:
            continue
        a, real = read_fields(run / fn)
        assert np.array_equal(np.rint(a['dof_id']).astype(int), ids)
        theta = a['porosity'] * a['S_liq']
        rmol = a['rhoMolar_liq']
        cmol = a['x^NaCl_liq'] * rmol  # mol/m3 solution
        solid_mol = a.get('precipitateVolumeFraction^NaCl', np.zeros_like(theta))
        if np.any(solid_mol > 0):
            raise RuntimeError('Solid salt present; this campaign window supports no precipitation')
        salt_cell = theta * cmol  # mol per m3 bulk
        liq_cell = theta  # m3 liquid per m3 bulk
        water_cell = (a['porosity'] * a['S_liq'] * rmol * a['x^H2O_liq']
                      + a['porosity'] * a['S_gas'] * a['rhoMolar_gas'] * a['x^H2O_gas'])
        C = cmol / 1000
        down = -a['velocity_liq_interior_LS (m/s)'][:, 1]
        assert np.isfinite(C).all() and np.isfinite(down).all() and np.isfinite(theta).all()
        row = {'time_h': t}
        anomaly = C.copy()
        for si, s in enumerate(SIDES):
            m = side[si]
            for b in BANDS:
                w = band_w[b] * m
                sm = float(w @ salt_cell)
                row[f'{s}_salt_g_{b[0]}_{b[1]}mm'] = sm * M_NACL * 1e3
                row[f'{s}_C_mol_L_{b[0]}_{b[1]}mm'] = sm / float(w @ liq_cell) / 1000
            row[f'{s}_water_g'] = float(vol[m] @ water_cell[m]) * M_H2O * 1e3
            row[f'{s}_salt_mol'] = float(vol[m] @ salt_cell[m])
            # layer anomaly on cell-centre layers (same as v08)
            lm = np.bincount(layer[m], weights=(vol * C)[m], minlength=nlayer)
            lv = np.bincount(layer[m], weights=vol[m], minlength=nlayer)
            anomaly[m] = C[m] - (lm / np.where(lv > 0, lv, 1))[layer[m]]
            prof = (bins * m) @ salt_cell / np.maximum((bins * m) @ liq_cell, 1e-30) / 1000
            if C0side is None or len(C0side) < 2:
                pass
            row[f'_{s}_profile'] = prof
            for region, rm in [('all', m), ('core', m & core)]:
                row[f'{s}_{region}_max_down_m_s'] = float(down[rm].max())
                for th in THRESH:
                    row[f'{s}_{region}_desc_vf_{th:.1e}'] = float(vol[rm & (down > th)].sum() / vol[rm].sum())
                row[f'{s}_{region}_rms_anomaly_mol_L'] = float(np.sqrt(np.average(anomaly[rm] ** 2, weights=vol[rm])))
            row[f'{s}_min_S'] = float(a['S_liq'][m].min())
            row[f'{s}_max_C_mol_L'] = float(C[m].max())
        row['total_salt_g'] = sum(row[f'{s}_salt_g_0_40mm'] for s in SIDES)
        row['total_water_g'] = sum(row[f'{s}_water_g'] for s in SIDES)
        # independent field integration vs solver ledger at the same accepted time
        k = int(np.argmin(abs(btime - ts)))
        assert abs(btime[k] - ts) < 1e-6, (ts, btime[k])
        for si, col in enumerate(['coarse_salt_mol', 'fine_salt_mol']):
            target = budget[col][k]
            if seed and abs(ts - seed['time_s']) < 1e-6:
                target += seed['partition_impulses_mol'][si]
            inv_err.append(abs(row[f'{SIDES[si]}_salt_mol'] - target) / abs(target))
        frames.append(row)
        sources.append({'file': real.name, 'time_h': t, 'sha256': sha(real)})

    # enriched depth relative to t=0 side mean
    for si, s in enumerate(SIDES):
        base = frames[0][f'{s}_C_mol_L_0_40mm']
        for r in frames:
            prof = r[f'_{s}_profile']
            for dc in (0.02, 0.1):
                idx = np.flatnonzero(prof > base + dc)
                r[f'{s}_enriched_depth_mm_dC{dc}'] = float(idx.max() + 1) if len(idx) else 0.0
    profiles = {s: np.array([r.pop(f'_{s}_profile') for r in frames]) for s in SIDES}

    # persistent downflow onset per threshold
    onset = {}
    valid = [r for r in frames if r['time_h'] >= .5 - 1e-9]
    for s in SIDES:
        for region in ['all', 'core']:
            key = f'{s}_{region}_max_down_m_s'
            for th in THRESH:
                hit = [i for i in range(len(valid) - 2) if all(v[key] > th for v in valid[i:i + 3])]
                onset[f'{s}_{region}_thr{th:.1e}'] = valid[hit[0]]['time_h'] if hit else None
    if selected:
        onset = {k: None for k in onset}  # gaps between selected frames: onset undefined

    # ledger time series (every accepted step)
    ev = budget['evaporation_time_h']
    dt = budget['dt_s']
    led = {'time_h': ev}
    i_adv, i_diff = budget['cumulative_interface_adv_mol'], budget['cumulative_interface_diff_mol']
    # coarse->fine positive for interface (audit integrates faces with coarse inside)
    pre = int(np.argmin(abs(btime - pre_h * 3600)))
    imp = seed['partition_impulses_mol'] if seed else [0, 0]
    for si, (s, sc, bc) in enumerate([('F36', 'coarse_salt_mol', 'coarse_bottom_salt_out_mol_s'), ('W3', 'fine_salt_mol', 'fine_bottom_salt_out_mol_s')]):
        bin_rate = -budget[bc]  # positive = supply into the sample
        cum = np.cumsum(bin_rate * dt)
        led[f'{s}_dS_salt_mol'] = budget[sc] - budget[sc][pre]
        led[f'{s}_seed_impulse_mol'] = np.where(btime > btime[pre], imp[si], 0.0)
        led[f'{s}_bottom_salt_in_mol'] = cum - cum[pre]
        pos = np.cumsum(np.clip(bin_rate, 0, None) * dt)
        neg = np.cumsum(np.clip(bin_rate, None, 0) * dt)
        led[f'{s}_bottom_salt_in_pos_stepwise_mol'] = pos - pos[pre]
        led[f'{s}_bottom_salt_in_neg_stepwise_mol'] = neg - neg[pre]
        sign = -1 if si == 0 else 1
        led[f'{s}_interface_salt_in_mol'] = sign * ((i_adv + i_diff) - (i_adv + i_diff)[pre])
        led[f'{s}_budget_residual_mol'] = led[f'{s}_dS_salt_mol'] - led[f'{s}_bottom_salt_in_mol'] - led[f'{s}_interface_salt_in_mol'] - led[f'{s}_seed_impulse_mol']
    led['interface_adv_c2f_mol'] = i_adv - i_adv[pre]
    led['interface_diff_c2f_mol'] = i_diff - i_diff[pre]
    for s, c in [('F36', 'cumulative_coarse_top_water_mol'), ('W3', 'cumulative_fine_top_water_mol')]:
        led[f'{s}_evap_water_g'] = (budget[c] - budget[c][pre]) * M_H2O * 1e3
    # assembled diagnostics of the A (v10) snapshot, if present: causal_budget.csv
    # (per-side ledgers, gross bottom flows, banded interface net/pos/neg) and
    # vertical_salt_flux.csv (every horizontal mesh plane, positive downward).
    extra, causal_info = [], {}
    if (run / 'causal_budget.csv').exists():
        cb = read_csv(run / 'causal_budget.csv')
        assert len(cb['time_s']) == len(btime) and np.allclose(cb['time_s'], btime, rtol=0, atol=1e-9), 'causal/budget rows differ'
        for s in SIDES:
            for k in ('water', 'salt'):
                for q in ('cum_bottom_%s_in_mol', 'cum_bottom_%s_gross_in_mol', 'cum_bottom_%s_gross_out_mol', 'cum_top_%s_out_mol'):
                    c = f'{s}_' + q % k
                    led['A_' + c] = cb[c] - cb[c][pre]
            for k in ('water', 'salt'):
                causal_info[f'{s}_max_rel_residual_{k}'] = float(np.max(np.abs(cb[f'{s}_residual_{k}_mol'])) / abs(cb[f'{s}_{k}_mol'][0]))
            # solver-side band inventories (independent of this script's overlap weights)
            for b in ('0_2', '2_3', '3_10', '10_20', '20_40'):
                led[f'A_{s}_salt_g_{b}mm'] = cb[f'{s}_salt_mol_{b}mm'] * M_NACL * 1e3
        bands = ('0_2', '2_10', '10_20', '20_40')
        for mode in ('adv', 'diff'):
            for b in bands:
                for q in ('net', 'pos', 'neg'):
                    c = f'if_{mode}_salt_{b}mm_cum_{q}_mol'
                    led['A_' + c] = cb[c] - cb[c][pre]
        for q in ('net', 'pos', 'neg'):
            led[f'A_if_salt_total_cum_{q}_mol'] = sum(led[f'A_if_{m}_salt_{b}mm_cum_{q}_mol'] for m in ('adv', 'diff') for b in bands)
            for b in bands:
                c = f'if_liquid_volume_{b}mm_cum_{q}_m3'
                led['A_' + c] = cb[c] - cb[c][pre]
            led[f'A_if_liquid_volume_total_cum_{q}_m3'] = sum(led[f'A_if_liquid_volume_{b}mm_cum_{q}_m3'] for b in bands)
        led['A_interface_faces_evaluated'] = cb['interface_faces_evaluated']
        extra.append('causal_budget.csv')
    if (run / 'vertical_salt_flux.csv').exists():
        vf = read_csv(run / 'vertical_salt_flux.csv')
        assert len(vf['time_s']) == len(btime)
        for s in SIDES:
            cols = sorted({int(c.rsplit('_d', 1)[1]) for c in vf if c.startswith(f'{s}_adv_down_net')})
            depth_mm = np.array(cols) * 1e-4  # column suffix is depth in 1e-7 m
            net = np.array([np.cumsum((vf[f'{s}_adv_down_net_mol_s_d{d}'] + vf[f'{s}_diff_down_net_mol_s_d{d}']) * vf['dt_s']) for d in cols])
            gross = np.array([np.cumsum(vf[f'{s}_adv_down_gross_mol_s_d{d}'] * vf['dt_s']) for d in cols])
            net -= net[:, [pre]]
            gross -= gross[:, [pre]]
            o = np.argsort(depth_mm)
            for target in (2.0, 3.0, 10.0, 20.0):
                led[f'A_{s}_down_salt_net_cum_mol_at{target:g}mm'] = np.array([np.interp(target, depth_mm[o], net[o, i]) for i in range(net.shape[1])])
                led[f'A_{s}_down_salt_advgross_cum_mol_at{target:g}mm'] = np.array([np.interp(target, depth_mm[o], gross[o, i]) for i in range(net.shape[1])])
                j = int(np.argmin(abs(depth_mm - target)))
                causal_info[f'{s}_nearest_plane_to_{target:g}mm'] = float(depth_mm[j])
        extra.append('vertical_salt_flux.csv')
    if causal_info:
        # cross-check: solver band inventories vs this script's overlap inventories at frames
        diffs = []
        for r in frames:
            k = int(np.argmin(abs(ev - r['time_h'])))
            for s in SIDES:
                a3 = led[f'A_{s}_salt_g_0_2mm'][k] + led[f'A_{s}_salt_g_2_3mm'][k]
                if abs(r['time_h']) > 1e-9:  # t=0 frame is written after the seed, ledger row before
                    diffs.append(abs(a3 - r[f'{s}_salt_g_0_3mm']) / r[f'{s}_salt_g_0_3mm'])
        causal_info['max_rel_diff_solver_vs_script_0_3mm_inventory'] = float(max(diffs)) if diffs else None
    if (run / 'causal_switches.json').exists():
        causal_info['switches'] = json.loads((run / 'causal_switches.json').read_text())
        causal_info['switches'].pop('horizontal_plane_depths_m', None)

    keep = ev >= -1e-9
    with open(out / 'ledger_series.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(list(led))
        for i in np.flatnonzero(keep):
            w.writerow([repr(float(led[k][i])) for k in led])
    keys = list(frames[0])
    with open(out / 'frame_series.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(frames)
    np.savez_compressed(out / 'profiles.npz', time_h=np.array([r['time_h'] for r in frames]),
                        depth_mm=np.arange(profiles['F36'].shape[1]) + .5, **profiles)

    def at(t):
        r = [q for q in frames if abs(q['time_h'] - t) < 1e-6]
        return r[0] if r else None

    rel = {}
    for col, base in [('water_residual_mol', 'water_mol'), ('salt_residual_mol', 'salt_total_mol'),
                      ('coarse_residual_mol', 'coarse_salt_mol'), ('fine_residual_mol', 'fine_salt_mol')]:
        rel[col] = float(np.max(np.abs(budget[col])) / abs(budget[base][0]))
    summary = {
        'run': str(run), 'name': name, 'frames': len(frames), 'selected_frames_only': selected,
        'final_evaporation_h': float(ev[-1]), 'max_relative_budget_residual': rel,
        'max_field_to_ledger_salt_relative_error': float(max(inv_err)),
        'onset_h': onset,
        'at': {str(t): at(t) for t in REPORT_T},
        'ledger_at': {str(t): {k: float(np.interp(t, ev, v)) for k, v in led.items()} for t in REPORT_T},
        'extended_diagnostics': extra,
        'causal_info': causal_info,
        'script_sha256': sha(__file__),
        'cells': int(len(ids)),
    }
    (out / 'summary.json').write_text(json.dumps(summary, indent=1))
    (out / 'field_sources.json').write_text(json.dumps(sources, indent=1))
    return summary


if __name__ == '__main__':
    s = main(sys.argv[1], sys.argv[2], '--selected' in sys.argv)
    print(json.dumps({k: s[k] for k in ['name', 'frames', 'final_evaporation_h', 'max_relative_budget_residual', 'max_field_to_ledger_salt_relative_error']}, indent=1))
