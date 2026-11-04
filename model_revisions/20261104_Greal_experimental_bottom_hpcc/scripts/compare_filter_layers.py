"""Compare six- and twelve-layer short G-real filter discretizations."""
from pathlib import Path
import csv
import json
import math
import sys


base, refined = map(Path, sys.argv[1:3])


def table(run, name):
    with (run / name).open(newline="") as handle:
        return list(csv.DictReader(handle))


def final(run, name):
    return table(run, name)[-1]


metrics = {}
for file_name, columns in {
    "film_budget.csv": ["cumulative_reservoir_loss_g", "cumulative_top_water_g", "sample_water_g"],
    "budget.csv": ["water_mol", "salt_total_mol", "coarse_salt_mol", "fine_salt_mol", "C_max_mol_L", "S_min"],
    "thermal_budget.csv": ["energy_J", "T_min_K", "T_max_K"],
}.items():
    a, b = final(base, file_name), final(refined, file_name)
    metrics[file_name] = {}
    for column in columns:
        av, bv = float(a[column]), float(b[column])
        metrics[file_name][column] = {"six_layers": av, "twelve_layers": bv,
                                     "absolute_difference": bv-av,
                                     "relative_difference": abs(bv-av)/max(abs(av), 1e-12)}


def profile(run):
    data = table(run, "depth_profiles_compact.csv")
    t = max(float(row["time_s"]) for row in data)
    return {(int(row["material"]), float(row["depth_mm"])): float(row["C_volume_mean_M"])
            for row in data if abs(float(row["time_s"])-t) < 1e-8}


pa, pb = profile(base), profile(refined)
if set(pa) != set(pb):
    raise RuntimeError("profile bins differ")
profile_max = max(abs(pa[key]-pb[key]) for key in pa)
relative_values = [entry["relative_difference"] for group in metrics.values() for entry in group.values()
                   if math.isfinite(entry["relative_difference"])]
result = {
    "state": "passed",
    "interpretation": "completed finite vertical-resolution screen; not a radial refinement",
    "metrics": metrics,
    "profile_max_absolute_difference_M": profile_max,
    "max_reported_relative_difference": max(relative_values),
    "vertical_convergence_screen": bool(max(relative_values) < 0.01 and profile_max < 0.01),
    "radial_convergence_demonstrated": False,
}
(refined / "spatial_comparison.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
