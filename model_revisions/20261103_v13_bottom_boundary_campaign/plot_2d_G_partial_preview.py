"""Create a truthful partial 2D G salt-profile preview through 102 h.

The G cases are conditional sensitivity runs because the refined-grid gate failed.
No missing 108/174 h G profile is interpolated or extrapolated.
"""
from pathlib import Path
import datetime
import hashlib
import json

import fitz
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import pandas as pd

R = Path(__file__).resolve().parent
P = R.parents[1]
SNAP = R / "track2d_g_partial_preview_20261103_2029"
O = R / "results/vertical_profiles_2d_G_partial_102h"
O.mkdir(parents=True, exist_ok=True)
OBS_PATH = R / "baseline_reference/MRI_profile_pairs_unchanged.csv"
REF_PDF = R / "results/vertical_profiles_2d/RH0_2D_VERTICAL_PROFILES_COMPARISON.pdf"
PROVENANCE = SNAP / "SNAPSHOT_PROVENANCE.json"

obs = pd.read_csv(OBS_PATH)
B = ["B0", "B1", "B2", "B3"]
G = ["G1", "G2", "G3"]
sides = ["F36", "W3"]
standard_times = [24, 60, 108, 174]
partial_times = [24, 60, 96, 102]
inventory_times = [0, 24, 60, 96, 102]

colors = {
    "B0": "#555555", "B1": "#888888", "B2": "#AAAAAA", "B3": "#CCCCCC",
    "G1": "#0072B2", "G2": "#D55E00", "G3": "#009E73",
}
styles = {"B0": "-", "B1": "--", "B2": "-.", "B3": ":", "G1": "--", "G2": "-.", "G3": ":"}
markers = {"B0": "o", "G1": "s", "G2": "^", "G3": "D"}
labels = {
    "B0": "B0 baseline", "B1": "B1", "B2": "B2", "B3": "B3",
    "G1": "G1: 2 mm port-equivalent", "G2": "G2: 5 mm port-equivalent",
    "G3": "G3: 10 mm port-equivalent",
}
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "pdf.fonttype": 42,
    "svg.fonttype": "none", "axes.spines.top": False, "axes.spines.right": False,
    "figure.facecolor": "white", "axes.facecolor": "white",
})

profiles = {}
depth = {}
source_paths = [Path(__file__), OBS_PATH, REF_PDF, PROVENANCE]
for case in B:
    p = R / "track2d/results" / case / "profiles_history.csv"
    profiles[case] = pd.read_csv(p); source_paths.append(p)
    q = R / "track2d/results" / case / "depth_enrichment_history.csv"
    depth[case] = pd.read_csv(q); source_paths.append(q)
for case in G:
    p = SNAP / "results" / case / "profiles_history.csv"
    q = SNAP / "results" / case / "depth_enrichment_history.csv"
    profiles[case] = pd.read_csv(p); depth[case] = pd.read_csv(q)
    source_paths.extend([p, q, SNAP / "results" / case / "verification.json"])
    v = json.loads((SNAP / "results" / case / "verification.json").read_text())
    assert v["state"] == "passed" and abs(v["through_evaporation_h"] - 102) < 1e-9
    assert v["max_salt_field_ledger_relative_error"] < 1e-8

def profile(case, side, time_h):
    d = profiles[case]
    return d[(d.material == side) & np.isclose(d.time_h, time_h, rtol=0, atol=1e-9)].sort_values("depth_mm")

def row(case, side, band, time_h):
    d = depth[case]
    z = d[(d.material == side) & (d.band == band) & np.isclose(d.time_h, time_h, rtol=0, atol=1e-9)]
    assert len(z) == 1, (case, side, band, time_h, len(z))
    return z.iloc[0]

summary_rows = []
for case in ["B0"] + G:
    for side in sides:
        interior = row(case, side, "3_37", 102)
        whole = row(case, side, "all", 102)
        b_int = row("B0", side, "3_37", 102)
        b_all = row("B0", side, "all", 102)
        summary_rows.append({
            "case": case, "side": side, "time_h": 102,
            "C_3_37_M": interior.C_volume_mean_M,
            "delta_C_3_37_vs_B0_M": interior.C_volume_mean_M - b_int.C_volume_mean_M,
            "total_salt_g": whole.salt_total_mol * 58.4428,
            "delta_total_salt_vs_B0_g": (whole.salt_total_mol - b_all.salt_total_mol) * 58.4428,
            "solid_salt_g": whole.salt_solid_mol * 58.4428,
            "liquid_volume_ratio_vs_0h": whole.liquid_volume_m3 / row(case, side, "all", 0).liquid_volume_m3,
        })
summary = pd.DataFrame(summary_rows)
summary.to_csv(O / "partial_summary_102h.csv", index=False)

pair_rows = []
rmse_rows = []
for case in ["B0"] + G:
    for side in sides:
        for time_h in [24, 60, 96]:
            z = profile(case, side, time_h)
            e = obs[(obs.side == side) & (obs.time_h == time_h)].sort_values("depth_mm")
            assert len(z) == len(e) == 40 and np.allclose(z.depth_mm, e.depth_mm, atol=1e-12, rtol=0)
            diff = z.C_M.to_numpy()[3:37] - e.MRI_archived_M.to_numpy()[3:37]
            rmse_rows.append({"case": case, "side": side, "time_h": time_h,
                              "RMSE_3_37_M": np.sqrt(np.mean(diff**2)), "bias_3_37_M": np.mean(diff)})
            for dep, model, measured in zip(z.depth_mm, z.C_M, e.MRI_archived_M):
                pair_rows.append({"case": case, "side": side, "time_h": time_h,
                                  "depth_mm": dep, "model_liquid_M": model, "MRI_archived_M": measured})
pd.DataFrame(pair_rows).to_csv(O / "profile_pairs_common_times.csv", index=False)
pd.DataFrame(rmse_rows).to_csv(O / "MRI_RMSE_common_times.csv", index=False)

def setup_profile_page(times, selection, title, partial=False):
    fig, axes = plt.subplots(2, 4, figsize=(12, 7), sharex=True, sharey=True)
    for j, side in enumerate(sides):
        for i, time_h in enumerate(times):
            ax = axes[j, i]
            e = obs[(obs.side == side) & (obs.time_h == time_h)].sort_values("depth_mm")
            if len(e):
                ax.plot(e.MRI_archived_M, e.depth_mm, "o", ms=3, mfc="white", mec="black",
                        label="Archived MRI", zorder=8)
            else:
                ax.text(.5, .96, "No archived MRI at 102 h", transform=ax.transAxes,
                        ha="center", va="top", fontsize=7.5, color="#555555")
            missing_g = []
            for case in selection:
                z = profile(case, side, time_h)
                if z.empty:
                    if case in G: missing_g.append(case)
                    continue
                ax.plot(z.C_M, z.depth_mm, color=colors[case], ls=styles[case], lw=1.45,
                        label=labels[case], zorder=5 if case in G else 3)
            if missing_g:
                ax.text(.5, .87, "G not yet available", transform=ax.transAxes, ha="center",
                        va="top", fontsize=7.5, color="#A33A2B")
            ax.set(title=f"{side} | {time_h} h", xlim=(0, 5.5), ylim=(40, 0), xlabel="Solution C (mol/L)")
            ax.grid(alpha=.15)
            if i == 0: ax.set_ylabel("Depth below surface (mm)")
    fig.suptitle(title, fontsize=13, y=.985)
    handles, legend_labels = axes[0, 0].get_legend_handles_labels()
    # Keep one legend entry per series while preserving plot order.
    unique = dict(zip(legend_labels, handles))
    fig.legend(unique.values(), unique.keys(), loc="upper center", bbox_to_anchor=(.5, .942),
               ncol=4, fontsize=7.2, frameon=False)
    footer = ("G1–G3 are conditional sensitivity runs; the refined-grid gate failed. "
              "Missing G times are gaps, not interpolation. MRI uses nominal clock.")
    fig.text(.5, .012, footer, ha="center", fontsize=7.2)
    fig.tight_layout(rect=(0, .045, 1, .84))
    return fig

pages = []
pdf_path = O / "RH0_2D_G_PARTIAL_102H_COMPARISON.pdf"
with PdfPages(pdf_path) as pdf:
    fig = setup_profile_page(standard_times, B + G,
                             "2D B0–B3 plus conditional G1–G3: established comparison times")
    fig.savefig(O / "page01_established_times.png", dpi=220)
    fig.savefig(O / "page01_established_times.svg")
    pdf.savefig(fig); plt.close(fig); pages.append("established_times")

    fig = setup_profile_page(partial_times, ["B0"] + G,
                             "Current conditional G snapshot through 102 h (B0 reference)")
    fig.savefig(O / "page02_current_G_snapshot.png", dpi=220)
    fig.savefig(O / "page02_current_G_snapshot.svg")
    pdf.savefig(fig); plt.close(fig); pages.append("current_G_snapshot")

    fig, axes = plt.subplots(2, 2, figsize=(12, 7), sharex=True)
    for j, side in enumerate(sides):
        ax_c = axes[0, j]; ax_s = axes[1, j]
        for case in ["B0"] + G:
            cvals=[]; svals=[]
            for time_h in inventory_times:
                cvals.append(row(case, side, "3_37", time_h).C_volume_mean_M)
                svals.append(row(case, side, "all", time_h).salt_total_mol * 58.4428)
            ax_c.plot(inventory_times, cvals, color=colors[case], ls=styles[case], marker=markers[case],
                      ms=4, lw=1.45, label=labels[case])
            ax_s.plot(inventory_times, svals, color=colors[case], ls=styles[case], marker=markers[case],
                      ms=4, lw=1.45, label=labels[case])
        ax_c.set(title=f"{side}: interior mean concentration", ylabel="C, 3–37 mm (mol/L)")
        ax_s.set(title=f"{side}: total salt inventory", xlabel="Evaporation time (h)", ylabel="NaCl-equivalent mass (g)")
        for ax in [ax_c, ax_s]: ax.grid(alpha=.18)
    handles, legend_labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, legend_labels, loc="upper center", bbox_to_anchor=(.5, .952), ncol=4, fontsize=8, frameon=False)
    fig.suptitle("Current 2D conditional G salt redistribution through 102 h", fontsize=13, y=.985)
    fig.text(.5, .012, "Saved-state values only (0/24/60/96/102 h); lines guide the eye. Conditional G, not grid-accepted evidence.",
             ha="center", fontsize=7.2)
    fig.tight_layout(rect=(0, .045, 1, .89))
    fig.savefig(O / "page03_salt_summary.png", dpi=220)
    fig.savefig(O / "page03_salt_summary.svg")
    pdf.savefig(fig); plt.close(fig); pages.append("salt_summary")

    fig, axes = plt.subplots(2, 4, figsize=(12, 7), sharex=True, sharey=True)
    for j, side in enumerate(sides):
        for i, time_h in enumerate(partial_times):
            ax = axes[j, i]
            b = profile("B0", side, time_h)
            for case in G:
                z = profile(case, side, time_h)
                ax.plot(z.C_M.to_numpy() - b.C_M.to_numpy(), z.depth_mm,
                        color=colors[case], ls=styles[case], lw=1.55, label=labels[case])
            ax.axvline(0, color="#555555", lw=.8, alpha=.7)
            ax.set(title=f"{side} | {time_h} h", xlim=(-.16, .36), ylim=(40, 0), xlabel="$C_G-C_{B0}$ (mol/L)")
            ax.grid(alpha=.16)
            if i == 0: ax.set_ylabel("Depth below surface (mm)")
    handles, legend_labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, legend_labels, loc="upper center", bbox_to_anchor=(.5, .942), ncol=3, fontsize=8, frameon=False)
    fig.suptitle("Conditional G concentration change relative to 2D B0", fontsize=13, y=.985)
    fig.text(.5, .012, "Common x scale across panels; actual saved states only. Overlap among G curves indicates weak port-size sensitivity at this scale.",
             ha="center", fontsize=7.2)
    fig.tight_layout(rect=(0, .045, 1, .84))
    fig.savefig(O / "page04_G_minus_B0.png", dpi=220)
    fig.savefig(O / "page04_G_minus_B0.svg")
    pdf.savefig(fig); plt.close(fig); pages.append("G_minus_B0")

doc = fitz.open(pdf_path)
assert len(doc) == 4
for i in range(4):
    doc[i].get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False).save(O / f"QA_pdf_page_{i+1:02}.png")

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

pins = {
    "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "snapshot_through_evaporation_h": 102,
    "source_sha256": {str(p.relative_to(P)): sha256(p) for p in source_paths},
    "standard_page": "G is shown only at 24 and 60 h; 108 and 174 h are explicit missing gaps",
    "partial_page": "actual saved 24,60,96,102 h profiles; no interpolation or smoothing",
    "salt_page": "actual saved 0,24,60,96,102 h points; connecting lines are visual guides",
    "scientific_status": "conditional sensitivity; original refined-grid gate failed",
    "pages": pages,
}
(O / "SOURCE_PINS.json").write_text(json.dumps(pins, indent=2), encoding="utf-8")

rmse = pd.DataFrame(rmse_rows)
g102 = summary[summary.case.isin(G)].copy()
spread_rows = []
for side in sides:
    z = g102[g102.side == side]
    stacks = np.vstack([profile(case, side, 102).C_M.to_numpy() for case in G])
    spread_rows.append({
        "side": side,
        "G_range_C_3_37_M": z.C_3_37_M.max() - z.C_3_37_M.min(),
        "G_max_pointwise_profile_range_M": np.max(np.ptp(stacks, axis=0)),
        "G_range_total_salt_g": z.total_salt_g.max() - z.total_salt_g.min(),
    })
spread = pd.DataFrame(spread_rows)
spread.to_csv(O / "G_spread_102h.csv", index=False)

def markdown_table(frame):
    columns = list(frame.columns)
    def fmt(value):
        return f"{value:.6g}" if isinstance(value, (float, np.floating)) else str(value)
    rows = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    rows.extend("| " + " | ".join(fmt(value) for value in record) + " |" for record in frame.itertuples(index=False, name=None))
    return "\n".join(rows)

lines = [
    "# Conditional 2D G partial salt analysis through 102 h", "",
    "This is a read-only intermediate snapshot. G1–G3 remain conditional because the original refined-grid gate failed.",
    "No 108 h or 174 h G values were interpolated or extrapolated.", "",
    "## 102 h comparison to B0", "",
    markdown_table(summary), "",
    "## MRI RMSE at common archived times", "",
    markdown_table(rmse), "",
    "## Spread among G1–G3 at 102 h", "",
    markdown_table(spread), "",
    "The MRI comparison uses archived whole-half profiles and nominal time. It is not a crystallization-onset inference.",
]
(O / "PARTIAL_ANALYSIS.md").write_text("\n".join(lines), encoding="utf-8")
print(pdf_path)
