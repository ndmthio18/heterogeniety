"""Plot a read-only partial 3D B/MRI comparison and early G preview.

B0–B3 use actual saved 0/24/48 h states and archived MRI at the same nominal
times. G1/G2 use actual 0/12/16 h states; MRI is shown only at 0 h because no
archived 12/16 h profile exists. G3 is pending resources and is not invented.
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
SNAP = R / "track3d_partial_preview_20261103_2140"
O = R / "results/vertical_profiles_3d_partial_48h"
O.mkdir(parents=True, exist_ok=True)
OBS_PATH = R / "baseline_reference/MRI_profile_pairs_unchanged.csv"
REF_PDF = R / "results/vertical_profiles_2d_G_partial_102h/RH0_2D_G_PARTIAL_102H_COMPARISON.pdf"
PROVENANCE = SNAP / "SNAPSHOT_PROVENANCE.json"

obs = pd.read_csv(OBS_PATH)
B = ["B0", "B1", "B2", "B3"]
G = ["G1", "G2"]
sides = ["F36", "W3"]
b_times = [0, 24, 48]
g_times = [0, 12, 16]
colors = {"B0": "#555555", "B1": "#0072B2", "B2": "#E69F00", "B3": "#009E73",
          "G1": "#0072B2", "G2": "#D55E00"}
styles = {"B0": "-", "B1": "--", "B2": "-.", "B3": ":", "G1": "--", "G2": "-."}
markers = {"B0": "o", "B1": "s", "B2": "^", "B3": "D"}
labels = {"B0": "3D B0 baseline", "B1": "3D B1 ($R_f/R_{ref}=0.1$)",
          "B2": "3D B2 ($R_f/R_{ref}=1$)", "B3": "3D B3 ($R_f/R_{ref}=10$)",
          "G1": "3D G1: 2 mm port", "G2": "3D G2: 5 mm port"}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "pdf.fonttype": 42,
                     "svg.fonttype": "none", "axes.spines.top": False,
                     "axes.spines.right": False, "figure.facecolor": "white"})

profiles = {}
source_paths = [Path(__file__), OBS_PATH, REF_PDF, PROVENANCE]
for case in B + G:
    p = SNAP / "results" / case / "profiles_history.csv"
    v = SNAP / "results" / case / "verification.json"
    profiles[case] = pd.read_csv(p); source_paths.extend([p, v])
    check = json.loads(v.read_text())
    expected = 48 if case in B else 16
    assert check["state"] == "passed" and abs(check["through_evaporation_h"] - expected) < 1e-9
    assert check["max_salt_field_ledger_relative_error"] < 1e-8

def profile(case, side, time_h):
    d = profiles[case]
    return d[(d.material == side) & np.isclose(d.time_h, time_h, rtol=0, atol=1e-9)].sort_values("depth_mm")

pairs = []
metrics = []
for case in B:
    for side in sides:
        for time_h in b_times:
            z = profile(case, side, time_h)
            e = obs[(obs.side == side) & (obs.time_h == time_h)].sort_values("depth_mm")
            assert len(z) == len(e) == 40 and np.allclose(z.depth_mm, e.depth_mm, atol=1e-12, rtol=0)
            diff = z.C_M.to_numpy()[3:37] - e.MRI_archived_M.to_numpy()[3:37]
            metrics.append({"case": case, "side": side, "time_h": time_h,
                            "RMSE_3_37_M": float(np.sqrt(np.mean(diff**2))),
                            "bias_3_37_M": float(np.mean(diff))})
            for dep, model, measured in zip(z.depth_mm, z.C_M, e.MRI_archived_M):
                pairs.append({"case": case, "side": side, "time_h": time_h, "depth_mm": dep,
                              "model_liquid_M": model, "MRI_archived_M": measured})
metrics = pd.DataFrame(metrics)
metrics.to_csv(O / "MRI_RMSE_B_common_times.csv", index=False)
pd.DataFrame(pairs).to_csv(O / "profile_pairs_B_common_times.csv", index=False)

pages = []
pdf_path = O / "RH0_3D_PARTIAL_48H_COMPARISON.pdf"
with PdfPages(pdf_path) as pdf:
    fig, axes = plt.subplots(2, 3, figsize=(11, 7), sharex=True, sharey=True)
    for j, side in enumerate(sides):
        for i, time_h in enumerate(b_times):
            ax = axes[j, i]
            e = obs[(obs.side == side) & (obs.time_h == time_h)].sort_values("depth_mm")
            ax.plot(e.MRI_archived_M, e.depth_mm, "o", ms=3, mfc="white", mec="black",
                    label="Archived MRI", zorder=8)
            for case in B:
                z = profile(case, side, time_h)
                ax.plot(z.C_M, z.depth_mm, color=colors[case], ls=styles[case], lw=1.45,
                        label=labels[case])
            ax.set(title=f"{side} | {time_h} h", xlim=(0, 5.5), ylim=(40, 0), xlabel="Solution C (mol/L)")
            ax.grid(alpha=.15)
            if i == 0: ax.set_ylabel("Depth below surface (mm)")
    handles, legend_labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, legend_labels, loc="upper center", bbox_to_anchor=(.5, .94), ncol=3,
               fontsize=7.5, frameon=False)
    fig.suptitle("Current 3D B0–B3 versus archived MRI: common saved times", fontsize=13, y=.985)
    fig.text(.5, .012, "Whole-half profiles; actual saved 0/24/48 h states; nominal MRI clock; no interpolation or onset inference.",
             ha="center", fontsize=7.2)
    fig.tight_layout(rect=(0, .045, 1, .83))
    fig.savefig(O / "page01_B_vs_MRI.png", dpi=220); fig.savefig(O / "page01_B_vs_MRI.svg")
    pdf.savefig(fig); plt.close(fig); pages.append("B_vs_MRI")

    fig, axes = plt.subplots(2, 2, figsize=(11, 7), sharex=True)
    for j, side in enumerate(sides):
        ax_rmse = axes[0, j]; ax_bias = axes[1, j]
        for case in B:
            z = metrics[(metrics.case == case) & (metrics.side == side)].sort_values("time_h")
            ax_rmse.plot(z.time_h, z.RMSE_3_37_M, color=colors[case], ls=styles[case],
                         marker=markers[case], ms=4, lw=1.4, label=labels[case])
            ax_bias.plot(z.time_h, z.bias_3_37_M, color=colors[case], ls=styles[case],
                         marker=markers[case], ms=4, lw=1.4, label=labels[case])
        ax_rmse.set(title=f"{side}: profile RMSE", ylabel="RMSE, 3–37 mm (mol/L)")
        ax_bias.axhline(0, color="#555555", lw=.8)
        ax_bias.set(title=f"{side}: profile bias", xlabel="Evaporation time (h)", ylabel="Bias, 3–37 mm (mol/L)")
        for ax in [ax_rmse, ax_bias]: ax.grid(alpha=.18)
    handles, legend_labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, legend_labels, loc="upper center", bbox_to_anchor=(.5, .94), ncol=4,
               fontsize=8, frameon=False)
    fig.suptitle("Current 3D B profile errors at common MRI times", fontsize=13, y=.985)
    fig.text(.5, .012, "Three nominal-time comparisons only; no uncertainty model or full-window validation.",
             ha="center", fontsize=7.2)
    fig.tight_layout(rect=(0, .045, 1, .84))
    fig.savefig(O / "page02_B_error_summary.png", dpi=220); fig.savefig(O / "page02_B_error_summary.svg")
    pdf.savefig(fig); plt.close(fig); pages.append("B_error_summary")

    fig, axes = plt.subplots(2, 3, figsize=(11, 7), sharex=True, sharey=True)
    for j, side in enumerate(sides):
        for i, time_h in enumerate(g_times):
            ax = axes[j, i]
            e = obs[(obs.side == side) & (obs.time_h == time_h)].sort_values("depth_mm")
            if len(e):
                ax.plot(e.MRI_archived_M, e.depth_mm, "o", ms=3, mfc="white", mec="black",
                        label="Archived MRI", zorder=8)
            else:
                ax.text(.5, .96, f"No archived MRI at {time_h} h", transform=ax.transAxes,
                        ha="center", va="top", fontsize=7.5, color="#555555")
            for case in G:
                z = profile(case, side, time_h)
                ax.plot(z.C_M, z.depth_mm, color=colors[case], ls=styles[case], lw=1.55,
                        label=labels[case])
            ax.set(title=f"{side} | {time_h} h", xlim=(0, 5.5), ylim=(40, 0), xlabel="Solution C (mol/L)")
            ax.grid(alpha=.15)
            if i == 0: ax.set_ylabel("Depth below surface (mm)")
    handles, legend_labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, legend_labels, loc="upper center", bbox_to_anchor=(.5, .94), ncol=3,
               fontsize=8, frameon=False)
    fig.suptitle("Early 3D G1/G2 numerical preview (G3 pending resources)", fontsize=13, y=.985)
    fig.text(.5, .012, "Actual saved 0/12/16 h states; 12/16 h have no MRI counterpart and are not validation panels.",
             ha="center", fontsize=7.2)
    fig.tight_layout(rect=(0, .045, 1, .83))
    fig.savefig(O / "page03_G_early_preview.png", dpi=220); fig.savefig(O / "page03_G_early_preview.svg")
    pdf.savefig(fig); plt.close(fig); pages.append("G_early_preview")

doc = fitz.open(pdf_path)
assert len(doc) == 3
for i in range(3):
    doc[i].get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False).save(O / f"QA_pdf_page_{i+1:02}.png")

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

(O / "SOURCE_PINS.json").write_text(json.dumps({
    "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "source_sha256": {str(p.relative_to(P)): sha256(p) for p in source_paths},
    "B_times_h": b_times, "G_times_h": g_times,
    "missing_data": "G3 pending; no MRI at12/16h; no values interpolated or extrapolated",
    "model_sampling": "actual closed compressed saved states only",
    "pages": pages,
    "scientific_status": "partial production preview; not final acceptance or validation",
}, indent=2), encoding="utf-8")

def md_table(frame):
    cols=list(frame.columns)
    fmt=lambda x: f"{x:.6g}" if isinstance(x,(float,np.floating)) else str(x)
    rows=["| "+" | ".join(cols)+" |","| "+" | ".join(["---"]*len(cols))+" |"]
    rows += ["| "+" | ".join(fmt(x) for x in row)+" |" for row in frame.itertuples(index=False,name=None)]
    return "\n".join(rows)

report = [
    "# Partial 3D profile comparison through 48 h", "",
    "B0–B3 are compared with archived MRI only at common saved nominal times 0, 24 and 48 h.",
    "G1/G2 are shown at 0, 12 and 16 h as numerical previews; only 0 h has an archived MRI counterpart. G3 is pending resources.",
    "No missing state was interpolated or extrapolated. Production continues, so these are not final accepted results.", "",
    "## B versus MRI metrics", "", md_table(metrics), "",
]
(O / "PARTIAL_3D_ANALYSIS.md").write_text("\n".join(report), encoding="utf-8")
print(pdf_path)
