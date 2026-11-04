from __future__ import annotations

import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def table_difference(left: Path, right: Path) -> dict:
    a, b = pd.read_csv(left), pd.read_csv(right)
    if list(a.columns) != list(b.columns) or len(a) != len(b):
        raise RuntimeError(f"Table structure differs: {left.name}")
    numeric = [name for name in a.columns if np.issubdtype(a[name].dtype, np.number)]
    absolute = max(float(np.nanmax(np.abs(a[name].to_numpy() - b[name].to_numpy()))) for name in numeric)
    relative = 0.0
    for name in numeric:
        x, y = a[name].to_numpy(), b[name].to_numpy()
        scale = np.maximum(np.maximum(np.abs(x), np.abs(y)), 1e-300)
        relative = max(relative, float(np.nanmax(np.abs(x - y) / scale)))
    return {"rows": len(a), "max_absolute_difference": absolute, "max_relative_difference": relative}


def arrays(path: Path) -> dict[str, np.ndarray]:
    root = ET.parse(path).getroot()
    result = {}
    for node in root.findall(".//CellData/DataArray"):
        value = np.fromstring(node.text or "", sep=" ")
        components = int(node.attrib.get("NumberOfComponents", "1"))
        result[node.attrib["Name"]] = value.reshape(-1, components)
    return result


def final_vtu(run: Path, name: str) -> Path:
    entries = ET.parse(run / f"{name}.pvd").findall(".//DataSet")
    return run / max(entries, key=lambda item: float(item.attrib["timestep"])).attrib["file"]


def compact_profile_check(run: Path, fields: dict[str, np.ndarray]) -> dict:
    compact = pd.read_csv(run / "depth_profiles_compact.csv")
    final_time = compact.time_s.max()
    compact = compact.loc[compact.time_s == final_time].copy()
    geometry = pd.read_csv(run / "cell_geometry.csv").set_index("dof")
    ids = fields["dof_id"][:, 0].astype(int)
    cell = geometry.loc[ids]
    volume = cell.volume_m3.to_numpy()
    x = cell.x_m.to_numpy()
    low = (0.04 - cell.ymax_m.to_numpy()) * 1000
    high = (0.04 - cell.ymin_m.to_numpy()) * 1000
    concentration = fields["x^NaCl_liq"][:, 0] * fields["rhoMolar_liq"][:, 0] / 1000
    saturation = fields["S_liq"][:, 0]
    porosity = fields["porosity"][:, 0]

    expected = []
    for material, side in [(0, x < 0.025), (1, x > 0.025)]:
        for depth in range(40):
            overlap = np.maximum(0, np.minimum(high, depth + 1) - np.maximum(low, depth)) / (high - low)
            geometric_weight = volume * side * overlap
            liquid_weight = geometric_weight * porosity * saturation
            expected.append(
                {
                    "material": material,
                    "depth_mm": depth + 0.5,
                    "C_volume_mean_M": float(np.average(concentration, weights=geometric_weight)),
                    "liquid_volume_m3": float(liquid_weight.sum()),
                }
            )
    expected = pd.DataFrame(expected)
    merged = compact.merge(expected, on=["material", "depth_mm"], suffixes=("_compact", "_vtu"), validate="one_to_one")
    return {
        "final_time_s": float(final_time),
        "rows": len(merged),
        "max_concentration_absolute_difference_M": float(
            np.max(np.abs(merged.C_volume_mean_M_compact - merged.C_volume_mean_M_vtu))
        ),
        "max_liquid_volume_absolute_difference_m3": float(
            np.max(np.abs(merged.liquid_volume_m3_compact - merged.liquid_volume_m3_vtu))
        ),
    }


def main() -> None:
    reference = ROOT / "remote_results/reduced"
    overlay = ROOT / "profile_overlay_result"
    report = {
        "reference_binary_sha256": sha(reference / "solver_elf"),
        "overlay_binary_sha256": "e36ca36d532b5a42b56e27c6a50e0c3c379d5de706072a3743e91cec57166908",
        "binary_difference_reason": "diagnostic-only accepted-step depth_profiles_compact.csv writer",
        "tables": {},
    }
    for name in ["budget.csv", "film_budget.csv", "thermal_budget.csv", "mineral_budget.csv"]:
        report["tables"][name] = table_difference(reference / name, overlay / name)

    left = arrays(final_vtu(reference, "OutputReduced"))
    right = arrays(final_vtu(overlay, "OutputProfile"))
    fields = {}
    for name in sorted(set(left) & set(right)):
        delta = np.abs(left[name] - right[name])
        fields[name] = {"max_absolute_difference": float(delta.max()), "shape": list(delta.shape)}
    report["final_fields"] = fields
    report["compact_profile_against_final_vtu"] = compact_profile_check(overlay, right)
    report["compact_profile_rows_total"] = len(pd.read_csv(overlay / "depth_profiles_compact.csv"))
    report["accepted_step_rows_reference"] = len(pd.read_csv(reference / "budget.csv"))
    report["accepted_step_rows_overlay"] = len(pd.read_csv(overlay / "budget.csv"))

    core_exact = max(value["max_absolute_difference"] for value in fields.values()) == 0
    tables_exact = max(value["max_absolute_difference"] for value in report["tables"].values()) == 0
    profile = report["compact_profile_against_final_vtu"]
    profile_ok = (
        profile["rows"] == 80
        and profile["max_concentration_absolute_difference_M"] < 1e-12
        and profile["max_liquid_volume_absolute_difference_m3"] < 1e-18
    )
    report["state"] = "passed" if core_exact and tables_exact and profile_ok else "failed"
    target = ROOT / "profile_overlay_equivalence.json"
    target.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if report["state"] != "passed":
        sys.exit(1)


if __name__ == "__main__":
    main()
