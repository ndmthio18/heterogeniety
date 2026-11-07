#!/usr/bin/env python3
"""Evaluate Task-10 geometry, causal and short conservation gates."""
from __future__ import annotations
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "runs"
failures: list[str] = []
evidence: dict[str, object] = {"causal": {}, "conservation": {}}


def load_json(path: Path) -> dict:
    if not path.exists():
        failures.append(f"missing {path.relative_to(ROOT)}")
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


for config in ("A", "B"):
    for connection in (1, 0):
        for buoyancy in (1, 0):
            case = f"M0_{config}_C{connection}B{buoyancy}"
            data = load_json(RUNS / case / "causal_selftest.json")
            evidence["causal"][case] = data
            if data.get("status") != "passed":
                failures.append(f"{case}: causal selftest not passed")
            if abs(float(data.get("interface_area_m2", math.nan)) - 0.002) > 1e-12:
                failures.append(f"{case}: wrong physical interface area")
            if connection == 0 and (
                float(data.get("max_abs_interface_advective_flux", math.nan)) != 0
                or float(data.get("max_abs_interface_diffusive_flux", math.nan)) != 0
                or float(data.get("max_abs_jacobian_interface_mass_rows", math.nan)) != 0
            ):
                failures.append(f"{case}: C0 mass coupling is not exact zero")
            if buoyancy == 0 and float(data.get("max_abs_salinity_response_lambda0", math.nan)) != 0:
                failures.append(f"{case}: B0 retains salinity-only Darcy response")
            if config == "B" and int(data.get("filter_cross_faces", 0)) <= 0:
                failures.append(f"{case}: shared-filter cross connection absent")

for config in ("A", "B"):
    case = f"M0_{config}_conservation_4h"
    work = RUNS / case
    status = load_json(work / "run_status.json")
    record: dict[str, object] = {"run_status": status}
    if status.get("status") != "completed" or abs(float(status.get("evaporation_time_h", -1)) - 4) > 1e-8:
        failures.append(f"{case}: did not reach 4 h evaporation")
    for filename, storage, residual in (
        ("budget.csv", "water_mol", "water_residual_mol"),
        ("budget.csv", "salt_total_mol", "salt_residual_mol"),
        ("thermal_budget.csv", "energy_J", "energy_residual_J"),
    ):
        rows = list(csv.DictReader((work / filename).open(encoding="utf-8")))
        scale = max(abs(float(rows[0][storage])), 1.0 if storage == "energy_J" else 1e-12)
        maximum = max(abs(float(row[residual])) / scale for row in rows)
        record[f"max_relative_{residual}"] = maximum
        if maximum > 1e-6:
            failures.append(f"{case}: {residual} {maximum:.3g} > 1e-6")
    mineral = list(csv.DictReader((work / "mineral_budget.csv").open(encoding="utf-8")))
    ncp = max(abs(float(row["max_relative_complementarity_residual"])) for row in mineral)
    record["max_ncp_residual"] = ncp
    if ncp > 1e-6:
        failures.append(f"{case}: complementarity residual {ncp:.3g}")
    evidence["conservation"][case] = record

result = {"status": "passed" if not failures else "failed",
          "failures": failures, "evidence": evidence}
(ROOT / "m0_acceptance.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2))
raise SystemExit(0 if not failures else 2)
