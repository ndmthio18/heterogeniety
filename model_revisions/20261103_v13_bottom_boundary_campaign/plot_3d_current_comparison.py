"""Plot complete 3D B results and explicitly incomplete current G snapshots."""
from pathlib import Path
import datetime, hashlib, json

import fitz
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import pandas as pd

R = Path(__file__).resolve().parent
P = R.parents[1]
SNAP = R / "track3d_current_snapshot_20261104"
O = R / "results" / "vertical_profiles_3d_B174_Gcurrent"
O.mkdir(parents=True, exist_ok=True)
OBS_PATH = R / "baseline_reference" / "MRI_profile_pairs_unchanged.csv"
PROV = SNAP / "SNAPSHOT_PROVENANCE.json"

obs = pd.read_csv(OBS_PATH)
B = ["B0", "B1", "B2", "B3"]
G = ["G1", "G2", "G3"]
cases = B + G
sides = ["F36", "W3"]
times = [24, 60, 108, 174]
colors = {"B0":"#4D4D4D", "B1":"#0072B2", "B2":"#E69F00", "B3":"#009E73",
          "G1":"#56B4E9", "G2":"#D55E00", "G3":"#CC79A7"}
styles = {"B0":"-", "B1":"--", "B2":"-.", "B3":":", "G1":"--", "G2":"-.", "G3":":"}
labels = {"B0":"3D B0 baseline", "B1":"3D B1 ($R_f/R_{ref}=0.1$)",
          "B2":"3D B2 ($R_f/R_{ref}=1$)", "B3":"3D B3 ($R_f/R_{ref}=10$)",
          "G1":"3D G1: 2 mm port", "G2":"3D G2: 5 mm port", "G3":"3D G3: 10 mm port"}
plt.rcParams.update({"font.family":"DejaVu Sans", "font.size":9, "pdf.fonttype":42,
                     "svg.fonttype":"none", "axes.spines.top":False,
                     "axes.spines.right":False, "figure.facecolor":"white"})

profiles = {}
depth = {}
source_paths = [Path(__file__), OBS_PATH, PROV]
for case in cases:
    p = SNAP / "results" / case / "profiles_history.csv"
    d = SNAP / "results" / case / "depth_enrichment_history.csv"
    v = SNAP / "results" / case / "verification.json"
    profiles[case] = pd.read_csv(p)
    depth[case] = pd.read_csv(d)
    check = json.loads(v.read_text())
    assert check["state"] == "passed" and check["max_salt_field_ledger_relative_error"] < 1e-8
    source_paths += [p, d, v]

def get_profile(case, side, time_h):
    d = profiles[case]
    return d[(d.material == side) & np.isclose(d.time_h, time_h, atol=1e-8, rtol=0)].sort_values("depth_mm")

pairs, metrics = [], []
for case in cases:
    for side in sides:
        for time_h in times:
            z = get_profile(case, side, time_h)
            if z.empty:
                continue
            e = obs[(obs.side == side) & (obs.time_h == time_h)].sort_values("depth_mm")
            assert len(z) == len(e) == 40 and np.allclose(z.depth_mm, e.depth_mm, atol=1e-12, rtol=0)
            diff = z.C_M.to_numpy()[3:37] - e.MRI_archived_M.to_numpy()[3:37]
            metrics.append({"case":case, "side":side, "time_h":time_h,
                            "RMSE_3_37_M":float(np.sqrt(np.mean(diff**2))),
                            "bias_3_37_M":float(np.mean(diff))})
            for dep, model, measured in zip(z.depth_mm, z.C_M, e.MRI_archived_M):
                pairs.append({"case":case, "side":side, "time_h":time_h, "depth_mm":dep,
                              "model_liquid_M":model, "MRI_archived_M":measured})
metrics = pd.DataFrame(metrics)
metrics.to_csv(O / "profile_metrics.csv", index=False)
pd.DataFrame(pairs).to_csv(O / "profile_pairs.csv", index=False)

def profile_page(pdf, selected, title, filename, incomplete=False):
    fig, axes = plt.subplots(2, 4, figsize=(12, 7), sharex=True, sharey=True)
    for j, side in enumerate(sides):
        for i, time_h in enumerate(times):
            ax = axes[j, i]
            e = obs[(obs.side == side) & (obs.time_h == time_h)].sort_values("depth_mm")
            ax.plot(e.MRI_archived_M, e.depth_mm, "o", ms=3, mfc="white", mec="black",
                    label="Archived MRI", zorder=8)
            for case in selected:
                z = get_profile(case, side, time_h)
                if not z.empty:
                    ax.plot(z.C_M, z.depth_mm, color=colors[case], ls=styles[case], lw=1.5,
                            label=labels[case])
            if incomplete and not any(not get_profile(c, side, time_h).empty for c in selected):
                ax.text(.5, .92, "No accepted snapshot", transform=ax.transAxes, ha="center",
                        va="top", fontsize=7.5, color="#666666")
            ax.set(title=f"{side} | {time_h} h", xlim=(0,5.5), ylim=(40,0),
                   xlabel="Solution C (mol/L)")
            ax.grid(alpha=.15)
            if i == 0: ax.set_ylabel("Depth below surface (mm)")
    handles, names = axes[0,0].get_legend_handles_labels()
    by_label = dict(zip(names, handles))
    fig.legend(by_label.values(), by_label.keys(), loc="upper center", bbox_to_anchor=(.5,.94),
               ncol=min(4,len(by_label)), fontsize=7.5, frameon=False)
    fig.suptitle(title, fontsize=13, y=.985)
    footer = ("Whole-half profiles; actual saved states and nominal MRI clock; no interpolation or onset inference."
              if not incomplete else
              "Running G snapshot: absent curves are explicit missing states; no interpolation, extrapolation or terminal claim.")
    fig.text(.5,.012,footer,ha="center",fontsize=7.2)
    fig.tight_layout(rect=(0,.045,1,.84))
    fig.savefig(O / f"{filename}.png", dpi=220)
    fig.savefig(O / f"{filename}.svg")
    pdf.savefig(fig); plt.close(fig)

pdf_path = O / "RH0_3D_B174_GCURRENT_MRI_COMPARISON.pdf"
with PdfPages(pdf_path) as pdf:
    profile_page(pdf, B, "3D B0–B3 complete 174 h results versus archived MRI", "page01_B_complete")
    profile_page(pdf, G, "Current 3D G1–G3 snapshots versus archived MRI", "page02_G_current", incomplete=True)

    fig, axes = plt.subplots(2,2,figsize=(11,7),sharex=True)
    for j, side in enumerate(sides):
        for case in cases:
            z=metrics[(metrics.case==case)&(metrics.side==side)].sort_values("time_h")
            if z.empty: continue
            axes[0,j].plot(z.time_h,z.RMSE_3_37_M,color=colors[case],ls=styles[case],marker="o",ms=3,lw=1.35,label=labels[case])
            axes[1,j].plot(z.time_h,z.bias_3_37_M,color=colors[case],ls=styles[case],marker="o",ms=3,lw=1.35,label=labels[case])
        axes[0,j].set(title=f"{side}: RMSE",ylabel="RMSE, 3–37 mm (mol/L)")
        axes[1,j].axhline(0,color="#666666",lw=.8)
        axes[1,j].set(title=f"{side}: bias",xlabel="Evaporation time (h)",ylabel="Bias, 3–37 mm (mol/L)")
        for ax in axes[:,j]: ax.grid(alpha=.18); ax.set_xticks(times)
    handles,names=axes[0,0].get_legend_handles_labels();fig.legend(handles,names,loc="upper center",bbox_to_anchor=(.5,.94),ncol=4,fontsize=7.3,frameon=False)
    fig.suptitle("Profile-error evolution at available common MRI times",fontsize=13,y=.985)
    fig.text(.5,.012,"Lines stop at the last available actual case time; missing G endpoints are not connected.",ha="center",fontsize=7.2)
    fig.tight_layout(rect=(0,.045,1,.83));fig.savefig(O/"page03_error_evolution.png",dpi=220);fig.savefig(O/"page03_error_evolution.svg");pdf.savefig(fig);plt.close(fig)

    rows=[]
    for case in B:
        for side in sides:
            z=depth[case]
            q=z[(z.material==side)&(z.band=="3_37")&np.isclose(z.time_h,174,atol=1e-8)]
            assert len(q)==1
            rows.append({"case":case,"side":side,"C_M":float(q.C_volume_mean_M.iloc[0]),"salt_mol":float(q.salt_total_mol.iloc[0])})
    summary=pd.DataFrame(rows)
    base=summary[summary.case=="B0"].set_index("side")
    summary["delta_C_vs_B0_M"]=[r.C_M-base.loc[r.side,"C_M"] for r in summary.itertuples()]
    summary["delta_salt_vs_B0_g"]=[(r.salt_mol-base.loc[r.side,"salt_mol"])*58.4428 for r in summary.itertuples()]
    summary.to_csv(O/"B_174h_effect_vs_B0.csv",index=False)
    fig,axes=plt.subplots(1,2,figsize=(10,4.8));x=np.arange(len(B));w=.34
    for ax,col,ylabel in [(axes[0],"delta_C_vs_B0_M","Δ mean C vs B0, 3–37 mm (mol/L)"),(axes[1],"delta_salt_vs_B0_g","Δ total NaCl vs B0, 3–37 mm (g)")]:
        for k,side in enumerate(sides):
            z=summary[summary.side==side].set_index("case").loc[B]
            ax.bar(x+(k-.5)*w,z[col],w,label=side,color=["#0072B2","#D55E00"][k],alpha=.85)
        ax.axhline(0,color="#555555",lw=.8);ax.set_xticks(x,B);ax.set_ylabel(ylabel);ax.grid(axis="y",alpha=.18)
    axes[0].legend(frameon=False);fig.suptitle("Complete 3D B boundary effect at 174 h relative to B0",fontsize=13)
    fig.text(.5,.012,"Numerical redistribution relative to the same-dimension baseline; not independent physical validation.",ha="center",fontsize=7.2)
    fig.tight_layout(rect=(0,.05,1,.93));fig.savefig(O/"page04_B174_effect.png",dpi=220);fig.savefig(O/"page04_B174_effect.svg");pdf.savefig(fig);plt.close(fig)

doc=fitz.open(pdf_path);assert len(doc)==4
for i in range(4):doc[i].get_pixmap(matrix=fitz.Matrix(1.5,1.5),alpha=False).save(O/f"QA_pdf_page_{i+1:02}.png")

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
(O/"SOURCE_PINS.json").write_text(json.dumps({"created_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "source_sha256":{str(p.relative_to(P)):sha(p) for p in source_paths},
 "B_status":"complete 174 h","G_status":"G1/G2 through 144 h snapshots; G3 through 24 h snapshot",
 "missing_data":"explicit gaps; no interpolation or extrapolation","pages":4,
 "scientific_status":"complete B comparison plus running G snapshot; final G assessment pending"},indent=2))

pivot=metrics.pivot_table(index=["case","side"],columns="time_h",values="RMSE_3_37_M")
table_frame=pivot.reset_index()
table_cols=[str(c) for c in table_frame.columns]
table_lines=["| "+" | ".join(table_cols)+" |","| "+" | ".join(["---"]*len(table_cols))+" |"]
for row in table_frame.itertuples(index=False,name=None):
    table_lines.append("| "+" | ".join("" if pd.isna(x) else (f"{x:.6g}" if isinstance(x,(float,np.floating)) else str(x)) for x in row)+" |")
report=["# Current 3D B-complete/G-running profile analysis","",
 "B0–B3 are complete 174 h cases. G1/G2 are represented only through the latest selected accepted 144 h state; G3 only through 24 h. Missing curves remain gaps.","",
 "## RMSE table (mol/L, 3–37 mm)","","\n".join(table_lines),"",
 "## Interpretation boundary","",
 "B cases support a full-window within-3D boundary comparison. G cases do not yet support a terminal ranking. MRI uses the archived nominal clock and is not used to infer crystallization onset."]
(O/"CURRENT_3D_ANALYSIS.md").write_text("\n".join(report))
print(pdf_path)
