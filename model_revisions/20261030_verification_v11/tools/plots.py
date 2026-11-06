"""Figures for VERIFICATION_REPORT.md from frame_series.csv of each case (numpy/matplotlib only).

Usage: python plots.py REGISTRY.json OUTDIR
"""
import csv, json, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def series(d):
    rows = list(csv.DictReader(open(Path(d) / 'frame_series.csv')))
    return {k: np.array([float(r[k]) for r in rows]) for k in rows[0]}


def main(reg_path, out):
    reg = json.loads(Path(reg_path).read_text())
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    data = {}
    for pid, p in reg.items():
        try:
            data[pid] = {a: series(p[a]) for a in ('C1', 'C0') if p.get(a) and (Path(p[a]) / 'frame_series.csv').exists()}
        except Exception as e:
            print('skip', pid, e)
    for key, title, fn in [('W3_salt_g_0_3mm', 'E_1: W3 0-3 mm salt, connected - disconnected (g NaCl)', 'E_W3_surface.png'),
                           ('F36_salt_g_0_3mm', 'F36 0-3 mm salt, connected - disconnected (g NaCl)', 'E_F36_surface.png'),
                           ('W3_salt_g_0_2mm', 'W3 0-2 mm salt, connected - disconnected (g NaCl)', 'E_W3_surface_0_2.png')]:
        fig, ax = plt.subplots(figsize=(7, 4.2))
        for pid, d in data.items():
            if 'C1' in d and 'C0' in d:
                n = min(len(d['C1']['time_h']), len(d['C0']['time_h']))
                assert np.allclose(d['C1']['time_h'][:n], d['C0']['time_h'][:n])
                ax.plot(d['C1']['time_h'][:n], d['C1'][key][:n] - d['C0'][key][:n], label=reg[pid].get('label', pid), lw=1.3)
        ax.axhline(0, color='k', lw=.6)
        ax.set_xlabel('evaporation time (h)')
        ax.set_ylabel('effect (g)')
        ax.set_title(title, fontsize=9)
        ax.legend(fontsize=7)
        fig.tight_layout()
        fig.savefig(out / fn, dpi=150)
        plt.close(fig)
    fig, axs = plt.subplots(1, 2, figsize=(10, 4.2), sharey=True)
    for ax, side in zip(axs, ['F36', 'W3']):
        for pid, d in data.items():
            for arm, ls in [('C1', '-'), ('C0', '--')]:
                if arm in d:
                    s = d[arm]
                    ax.plot(s['time_h'], s[f'{side}_salt_g_0_3mm'] - s[f'{side}_salt_g_0_3mm'][0], ls, lw=1, label=f"{reg[pid].get('label', pid)} {arm}")
        ax.set_title(f'{side} 0-3 mm inventory change (g)', fontsize=9)
        ax.set_xlabel('evaporation time (h)')
    axs[0].legend(fontsize=6)
    fig.tight_layout()
    fig.savefig(out / 'surface_inventory_change.png', dpi=150)
    plt.close(fig)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
