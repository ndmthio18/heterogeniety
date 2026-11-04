"""Validate a completed G-real short case using only the Python standard library."""
from pathlib import Path
import csv
import json
import math
import sys


run = Path(sys.argv[1])


def rows(name):
    with (run / name).open(newline="") as handle:
        data = list(csv.DictReader(handle))
    for row in data:
        for value in row.values():
            if value not in (None, "") and not math.isfinite(float(value)):
                raise RuntimeError(f"nonfinite value in {name}")
    return data


status = json.loads((run / "run_status.json").read_text())
if status["status"] != "completed" or abs(status["time_s"] - 7800) > 1e-8:
    raise RuntimeError(status)
budget = rows("budget.csv")
thermal = rows("thermal_budget.csv")
mineral = rows("mineral_budget.csv")
metrics = {
    "water_relative": max(abs(float(r["water_residual_mol"])) for r in budget) / max(abs(float(budget[0]["water_mol"])), 1e-12),
    "salt_relative": max(abs(float(r["salt_residual_mol"])) for r in budget) / max(abs(float(budget[0]["salt_total_mol"])), 1e-12),
    "coarse_relative": max(abs(float(r["coarse_residual_mol"])) for r in budget) / max(abs(float(budget[0]["coarse_salt_mol"])), 1e-12),
    "fine_relative": max(abs(float(r["fine_residual_mol"])) for r in budget) / max(abs(float(budget[0]["fine_salt_mol"])), 1e-12),
    "energy_relative": max(abs(float(r["energy_residual_J"])) for r in thermal) / max(abs(float(thermal[0]["energy_J"])), 1.0),
    "temperature_min_K": min(float(r["T_min_K"]) for r in thermal),
    "temperature_max_K": max(float(r["T_max_K"]) for r in thermal),
    "max_complementarity_relative": max(float(r["max_relative_complementarity_residual"]) for r in mineral[1:]),
    "min_solid_vf": min(float(r["min_solid_vf"]) for r in mineral[1:]),
    "vtu_count": len(list(run.glob("*.vtu"))),
    "total_bytes": sum(p.stat().st_size for p in run.iterdir() if p.is_file()),
    "film_faces_bytes": (run / "film_faces.csv").stat().st_size,
}
metrics["state"] = "passed" if (
    max(metrics[key] for key in ("water_relative", "salt_relative", "coarse_relative", "fine_relative", "energy_relative")) <= 1e-6
    and metrics["max_complementarity_relative"] < 1e-6
    and metrics["min_solid_vf"] > -1e-10
) else "failed"
(run / "short_validation.json").write_text(json.dumps(metrics, indent=2) + "\n")
print(json.dumps(metrics, indent=2))
if metrics["state"] != "passed":
    raise SystemExit(1)
