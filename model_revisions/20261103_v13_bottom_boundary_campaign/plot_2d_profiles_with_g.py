"""Build the established MRI/model profile comparison with B and conditional G cases."""
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
O = R / "results/vertical_profiles_2d_with_G"
O.mkdir(parents=True, exist_ok=True)
reference = R / "results/vertical_profiles_2d/RH0_2D_VERTICAL_PROFILES_COMPARISON.pdf"
exp_path = R / "baseline_reference/MRI_profile_pairs_unchanged.csv"
original_exp = P / "analysis/model_experiment_comparison_20261028/experimental_profiles.csv"
obs = pd.read_csv(exp_path)
original = pd.read_csv(original_exp)
times = [24, 60, 108, 174]
sides = ["F36", "W3"]
B = ["B0", "B1", "B2", "B3"]
G = ["G1", "G2", "G3"]
cases = B + G
colors = {
    "B0": "#0072B2", "B1": "#009E73", "B2": "#E69F00", "B3": "#CC3377",
    "G1": "#56B4E9", "G2": "#D55E00", "G3": "#7B3294",
}
styles = {"B0": "-", "B1": "--", "B2": "-.", "B3": ":", "G1": "--", "G2": "-.", "G3": ":"}
labels = {
    "B0": "2D B0 (baseline)", "B1": "2D B1 ($R_f/R_{ref}=0.1$)",
    "B2": "2D B2 ($R_f/R_{ref}=1$)", "B3": "2D B3 ($R_f/R_{ref}=10$)",
    "G1": "2D G1 conditional", "G2": "2D G2 conditional", "G3": "2D G3 conditional",
}
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "pdf.fonttype": 42,
    "axes.spines.top": False, "axes.spines.right": False,
})

profiles = {}
source_paths = [Path(__file__), reference, exp_path, original_exp]
for case in B:
    path = R / "track2d/results" / case / "profiles_history.csv"
    profiles[case] = pd.read_csv(path); source_paths.append(path)
for case in G:
    status_path = R / "track2d_g_conditional_r02/status" / f"{case}_production.json"
    status = json.loads(status_path.read_text())
    assert status["state"] == "completed_conditional", (case, status)
    assert float(status.get("completed_evaporation_h", status.get("evaporation_time_h", 0))) >= 174
    path = R / "track2d_g_conditional_r02/results" / case / "profiles_history.csv"
    profiles[case] = pd.read_csv(path); source_paths.extend([status_path, path])

pairs = []
metrics = []
for side in sides:
    for time_h in times:
        e = obs[(obs.side == side) & (obs.time_h == time_h)].sort_values("depth_mm")
        old = original[(original.side == side) & (original.time_h == time_h)].sort_values("depth_center_mm")
        assert len(e) == len(old) == 40
        assert np.allclose(e.depth_mm, old.depth_center_mm, rtol=0, atol=1e-12)
        assert np.allclose(e.MRI_archived_M, old.archived_concentration, rtol=0, atol=1e-12)
        for case, data in profiles.items():
            z = data[(data.material == side) & np.isclose(data.time_h, time_h, rtol=0, atol=1e-9)].sort_values("depth_mm")
            assert len(z) == 40 and np.allclose(z.depth_mm, e.depth_mm, rtol=0, atol=1e-12)
            status = "accepted_B" if case in B else "conditional_G_refined_gate_failed"
            for depth, model, measured in zip(z.depth_mm, z.C_M, e.MRI_archived_M):
                pairs.append(dict(case=case,case_status=status,side=side,time_h=time_h,depth_mm=depth,
                                  model_liquid_M=model,MRI_archived_M=measured))
            for band, mask in [
                ("whole_0_40", np.ones(40, dtype=bool)),
                ("interior_3_37", (z.depth_mm.to_numpy() >= 3) & (z.depth_mm.to_numpy() < 37)),
            ]:
                diff = z.C_M.to_numpy()[mask] - e.MRI_archived_M.to_numpy()[mask]
                metrics.append(dict(case=case,case_status=status,side=side,time_h=time_h,band=band,
                                    RMSE_M=float(np.sqrt(np.mean(diff**2))),bias_M=float(np.mean(diff))))
pd.DataFrame(pairs).to_csv(O / "profile_pairs.csv", index=False)
pd.DataFrame(metrics).to_csv(O / "profile_metrics.csv", index=False)

page_specs = [
    (cases, "00_all_B_and_conditional_G"),
    (B, "01_B_only"),
    (["B0"] + G, "02_B0_and_conditional_G"),
] + [([case], f"{case}_profiles") for case in cases]
pages = []
pdf_path = O / "RH0_2D_B_G_VERTICAL_PROFILES_COMPARISON.pdf"
with PdfPages(pdf_path) as pdf:
    for selection, name in page_specs:
        fig, axes = plt.subplots(2, 4, figsize=(12, 7), sharex=True, sharey=True)
        for j, side in enumerate(sides):
            for i, time_h in enumerate(times):
                ax = axes[j, i]
                e = obs[(obs.side == side) & (obs.time_h == time_h)].sort_values("depth_mm")
                ax.plot(e.MRI_archived_M, e.depth_mm, "o", ms=3, mfc="white", c="k", label="Archived MRI", zorder=6)
                for case in selection:
                    data = profiles[case]
                    z = data[(data.material == side) & np.isclose(data.time_h, time_h, rtol=0, atol=1e-9)].sort_values("depth_mm")
                    ax.plot(z.C_M, z.depth_mm, color=colors[case], ls=styles[case], lw=1.45, label=labels[case])
                ax.set(title=f"{side} | {time_h} h", xlim=(0, 5.5), ylim=(40, 0), xlabel="Solution C (mol/L)")
                ax.grid(alpha=.15)
                if i == 0:
                    ax.set_ylabel("Depth below surface (mm)")
        fig.suptitle("2D whole-half concentration profiles: " + name.replace("_", " "), fontsize=13, y=.984)
        handles, legend_labels = axes[0, 0].get_legend_handles_labels()
        fig.legend(handles, legend_labels, loc="upper center", bbox_to_anchor=(.5, .951),
                   ncol=min(4, len(legend_labels)), fontsize=7.5, frameon=False)
        fig.text(.5, .012,
                 "G1–G3 are conditional sensitivity runs: the original refined-grid gate remains failed. "
                 "Archived MRI uses nominal clock; no crystallization-time inference.",
                 ha="center", fontsize=7.2)
        fig.tight_layout(rect=(0, .045, 1, .89))
        for ext in ["png", "pdf", "svg"]:
            fig.savefig(O / f"{name}.{ext}", dpi=180)
        pdf.savefig(fig)
        plt.close(fig)
        pages.append(name)

doc = fitz.open(pdf_path)
assert len(doc) == len(page_specs) == 10
for page_index in [0, 2, 9]:
    doc[page_index].get_pixmap(matrix=fitz.Matrix(1.5, 1.5)).save(O / f"QA_pdf_page_{page_index+1:02}.png")

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

(O / "SOURCE_PINS.json").write_text(json.dumps({
    "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "reference": str(reference.relative_to(P)),
    "layout": "12x7 inches; 2 rows F36/W3; 24,60,108,174 h columns; 0–5.5 M and 0–40 mm axes",
    "source_sha256": {str(path.relative_to(P)): sha256(path) for path in source_paths},
    "MRI_versus_original_reference_data": "all 320 plotted values and depths matched to 1e-12",
    "model_sampling": "actual saved 2 h outputs at requested times; no interpolation, fitting, or smoothing",
    "pages": pages,
    "limitations": "B cases accepted. G cases are conditional sensitivities because the original refined-grid gate failed; conventional 2D is not 3D geometry equivalence.",
}, indent=2), encoding="utf-8")
print(pdf_path)
