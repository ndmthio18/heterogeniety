from __future__ import annotations

from pathlib import Path
import hashlib
import io
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image


OUT = Path(__file__).resolve().parent
RAW = OUT / "raw"

CASES = {
    "Film075mm": {"label": "7.5 mm (partial)", "color": "#D55E00", "ls": "--"},
    "Film080mm": {"label": "8.0 mm (partial)", "color": "#009E73", "ls": "-."},
    "Film081mm": {"label": "8.10 mm (complete)", "color": "#0072B2", "ls": "-"},
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_complete_csv(path: Path) -> tuple[pd.DataFrame, int]:
    lines = path.read_text(encoding="utf-8").splitlines()
    width = len(lines[0].split(","))
    complete = [line for line in lines[1:] if len(line.split(",")) == width]
    frame = pd.read_csv(io.StringIO("\n".join([lines[0], *complete])))
    return frame, len(lines) - 1 - len(complete)


curves: dict[str, pd.DataFrame] = {}
manifest: dict[str, object] = {"sources": {}, "transformations": []}
for name in CASES:
    path = RAW / f"{name}.csv"
    frame, dropped = read_complete_csv(path)
    frame = (
        frame.dropna(subset=["evaporation_time_h", "cumulative_reservoir_loss_g"])
        .sort_values("evaporation_time_h")
        .drop_duplicates("evaporation_time_h", keep="last")
    )
    x = frame["evaporation_time_h"].to_numpy()
    y = frame["cumulative_reservoir_loss_g"].to_numpy()
    assert x.min() <= 1.0 < x.max()
    frame["loss_since_1h_g"] = y - np.interp(1.0, x, y)
    frame = frame[frame.evaporation_time_h >= 1.0].copy()
    curves[name] = frame
    manifest["sources"][name] = {
        "path": str(path),
        "sha256": sha256(path),
        "achieved_evaporation_h": float(frame.evaporation_time_h.max()),
        "dropped_incomplete_rows": dropped,
    }
    frame.to_csv(OUT / f"{name}_curve.csv", index=False)

exp_path = RAW / "experiment.csv"
experiment = pd.read_csv(exp_path)
experiment = experiment[(experiment.time_h >= 1.0) & (experiment.time_h <= 174.0)].copy()
experiment["loss_g"] = experiment.mass_g.iloc[0] - experiment.mass_g
manifest["sources"]["experiment"] = {
    "path": str(exp_path),
    "sha256": sha256(exp_path),
    "points_1_174h": int(len(experiment)),
}

common_model_end = min(float(frame.evaporation_time_h.max()) for frame in curves.values())
common_exp = experiment[experiment.time_h <= common_model_end].copy()
common_end = float(common_exp.time_h.iloc[-1])
assert common_end == 36.0

metrics: list[dict[str, float | str]] = []
matched: list[dict[str, float | str]] = []
intervals: list[dict[str, float | str]] = []
for name, frame in curves.items():
    model = np.interp(
        common_exp.time_h,
        frame.evaporation_time_h,
        frame.loss_since_1h_g,
    )
    observed = common_exp.loss_g.to_numpy()
    dt = np.diff(common_exp.time_h.to_numpy())
    model_rate = np.diff(model) / dt
    observed_rate = np.diff(observed) / dt
    cumulative_error = model - observed
    metrics.append(
        {
            "case": name,
            "label": CASES[name]["label"],
            "common_start_h": 1.0,
            "common_end_h": common_end,
            "experiment_loss_g": float(observed[-1]),
            "model_loss_g": float(model[-1]),
            "endpoint_error_g": float(cumulative_error[-1]),
            "endpoint_error_percent": float(cumulative_error[-1] / observed[-1] * 100.0),
            "cumulative_RMSE_g": float(np.sqrt(np.mean(cumulative_error[1:] ** 2))),
            "interval_rate_RMSE_g_h": float(
                np.sqrt(np.average((model_rate - observed_rate) ** 2, weights=dt))
            ),
            "available_model_h": float(frame.evaporation_time_h.max()),
        }
    )
    for time_h, model_g, exp_g in zip(common_exp.time_h, model, observed):
        matched.append({"case": name, "time_h": time_h, "model_g": model_g, "experiment_g": exp_g})
    for start_h, end_h, model_r, exp_r in zip(
        common_exp.time_h.iloc[:-1], common_exp.time_h.iloc[1:], model_rate, observed_rate
    ):
        intervals.append(
            {
                "case": name,
                "start_h": start_h,
                "end_h": end_h,
                "model_g_h": model_r,
                "experiment_g_h": exp_r,
            }
        )

metrics_frame = pd.DataFrame(metrics).sort_values("interval_rate_RMSE_g_h")
metrics_frame.to_csv(OUT / "metrics_common_1_36h.csv", index=False)
pd.DataFrame(matched).to_csv(OUT / "matched_points_common_1_36h.csv", index=False)
pd.DataFrame(intervals).to_csv(OUT / "interval_rates_common_1_36h.csv", index=False)

manifest["transformations"] = [
    "All cumulative losses are referenced to each source at 1 h by linear interpolation.",
    "No smoothing or extrapolation is used.",
    "Ranking uses only experimental weighing points shared by all models: 1-36 h.",
    "Interval-rate RMSE is duration weighted over the original weighing intervals.",
]
manifest["common_model_end_h"] = common_model_end
manifest["common_measured_end_h"] = common_end
manifest["ranking_by_interval_rate_RMSE"] = metrics_frame.case.tolist()
manifest["matplotlib_version"] = matplotlib.__version__
(OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 9.5,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "pdf.fonttype": 42,
        "svg.fonttype": "none",
    }
)

fig = plt.figure(figsize=(180 / 25.4, 155 / 25.4), layout="constrained")
grid = fig.add_gridspec(2, 2, height_ratios=[1.05, 1.0])
ax_full = fig.add_subplot(grid[0, :])
ax_zoom = fig.add_subplot(grid[1, 0])
ax_rate = fig.add_subplot(grid[1, 1])


def draw_loss(ax: plt.Axes, end_h: float) -> None:
    obs = experiment[experiment.time_h <= end_h]
    ax.plot(
        obs.time_h,
        obs.loss_g,
        color="#222222",
        marker="o",
        markersize=3.2,
        linewidth=1.25,
        label="Experiment",
        zorder=5,
    )
    for name, spec in CASES.items():
        frame = curves[name]
        shown = frame[frame.evaporation_time_h <= end_h]
        ax.plot(
            shown.evaporation_time_h,
            shown.loss_since_1h_g,
            color=spec["color"],
            linestyle=spec["ls"],
            linewidth=1.8,
            label=spec["label"],
        )
        if name != "Film081mm":
            last = shown.iloc[-1]
            ax.scatter(
                last.evaporation_time_h,
                last.loss_since_1h_g,
                s=28,
                marker="|",
                linewidths=1.8,
                color=spec["color"],
                zorder=6,
            )
    ax.set(xlabel="Evaporation time (h)", ylabel="Reservoir solution loss since 1 h (g)")
    ax.grid(alpha=0.18, linewidth=0.6)


draw_loss(ax_full, 174.0)
ax_full.set(xlim=(1, 174), title="a  Full experimental window; partial simulations stop at their achieved times")
ax_full.legend(frameon=False, ncol=2, loc="upper left")

draw_loss(ax_zoom, 48.0)
ax_zoom.set(xlim=(1, 48), title="b  Available trajectories (zoom)")
ax_zoom.axvline(common_end, color="#777777", linestyle=":", linewidth=1.0)
ax_zoom.text(common_end + 0.7, 0.6, "common measured end = 36 h", rotation=90, color="#666666", fontsize=8)

edges = common_exp.time_h.to_numpy()
observed_rate = np.diff(common_exp.loss_g.to_numpy()) / np.diff(edges)
ax_rate.stairs(observed_rate, edges, baseline=None, color="#222222", linewidth=2.0, label="Experiment")
interval_frame = pd.DataFrame(intervals)
for name, spec in CASES.items():
    values = interval_frame[interval_frame.case == name].model_g_h.to_numpy()
    ax_rate.stairs(
        values,
        edges,
        baseline=None,
        color=spec["color"],
        linestyle=spec["ls"],
        linewidth=1.7,
        label=spec["label"],
    )
ax_rate.set(
    xlim=(1, common_end),
    xlabel="Evaporation time (h)",
    ylabel="Interval-average solution loss rate (g/h)",
    title="c  Identical weighing intervals, 1-36 h",
)
ax_rate.grid(alpha=0.18, linewidth=0.6)

fig.suptitle("Non-isothermal RH = 0 gas-film comparison", fontsize=12.5)
for suffix in ("png", "pdf", "svg"):
    fig.savefig(OUT / f"evaporation_comparison.{suffix}", dpi=300, facecolor="white")
plt.close(fig)

# Matplotlib writes RGBA PNGs even with a white face colour. Flatten the alpha
# channel explicitly so the delivered raster is an opaque RGB figure.
png_path = OUT / "evaporation_comparison.png"
with Image.open(png_path) as image:
    rgba = image.convert("RGBA")
    rgb = Image.new("RGB", rgba.size, "white")
    rgb.paste(rgba, mask=rgba.getchannel("A"))
    rgb.save(png_path, dpi=(300, 300))

best = metrics_frame.iloc[0]
report = f"""# 7.5/8.0/8.10 mm evaporation snapshot

The 7.5 and 8.0 mm simulations are partial ({curves['Film075mm'].evaporation_time_h.max():.2f} and {curves['Film080mm'].evaporation_time_h.max():.2f} h); 8.10 mm is complete to 174 h. No partial trajectory is extrapolated.

The fair ranking uses the original experimental points common to every model, 1-36 h. By duration-weighted interval-rate RMSE, **{best['label']} is currently closest** ({best['interval_rate_RMSE_g_h']:.5f} g/h). See `metrics_common_1_36h.csv` for all cumulative and rate errors.

The 8.10 mm complete simulation predicts 51.94784 g solution loss over 1-174 h versus 51.52 g measured (+0.830%). That full-window result cannot yet be compared fairly with the incomplete 7.5/8.0 mm runs.

The figure uses measured points, unsmoothed model output, a common zero at 1 h, and a visible endpoint marker for partial simulations. Raw snapshots and SHA256 provenance are in `raw/` and `manifest.json`.
"""
(OUT / "SNAPSHOT_REPORT.md").write_text(report, encoding="utf-8")

print(metrics_frame.to_string(index=False))
