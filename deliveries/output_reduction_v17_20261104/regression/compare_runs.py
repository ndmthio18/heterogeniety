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


def main() -> None:
    original, reduced = ROOT / "remote_results/original", ROOT / "remote_results/reduced"
    report = {
        "binary_sha256_original": sha(original / "solver_elf"),
        "binary_sha256_reduced": sha(reduced / "solver_elf"),
        "input_difference_allowed": "Problem.Name and Benchmark.VtkEvery only",
        "tables": {},
    }
    physical_tables = ["budget.csv", "film_budget.csv", "thermal_budget.csv", "mineral_budget.csv"]
    for name in physical_tables:
        report["tables"][name] = table_difference(original / name, reduced / name)
    left, right = arrays(final_vtu(original, "OutputOriginal")), arrays(final_vtu(reduced, "OutputReduced"))
    common = sorted(set(left) & set(right))
    fields = {}
    for name in common:
        delta = np.abs(left[name] - right[name])
        fields[name] = {"max_absolute_difference": float(delta.max()), "shape": list(left[name].shape)}
    report["final_fields"] = fields
    geometry = pd.read_csv(original / "cell_geometry.csv").set_index("dof")
    ids = left["dof_id"][:, 0].astype(int)
    cell = geometry.loc[ids]
    volume = cell.volume_m3.to_numpy()
    x = cell.x_m.to_numpy()
    low = (0.04 - cell.ymax_m.to_numpy()) * 1000
    high = (0.04 - cell.ymin_m.to_numpy()) * 1000
    concentration_left = left["x^NaCl_liq"][:, 0] * left["rhoMolar_liq"][:, 0] / 1000
    concentration_right = right["x^NaCl_liq"][:, 0] * right["rhoMolar_liq"][:, 0] / 1000
    profile_differences = {}
    for side, mask in {"F36": x < 0.025, "W3": x > 0.025}.items():
        delta = []
        for depth in range(40):
            weight = volume * mask * np.maximum(0, np.minimum(high, depth + 1) - np.maximum(low, depth)) / (high - low)
            delta.append(abs(np.average(concentration_left, weights=weight) - np.average(concentration_right, weights=weight)))
        profile_differences[side] = {"max_absolute_difference_M": float(max(delta)), "bins": 40}
    report["final_F36_W3_profiles"] = profile_differences
    perf = {}
    for label, directory in [("original", original), ("reduced", reduced)]:
        steps = pd.read_csv(directory / "performance_steps.csv")
        perf[label] = {
            "accepted_steps": len(steps),
            "sum_output_s": float(steps.output_s.sum()),
            "sum_step_s": float(steps.step_s.sum()),
            "sum_newton_s": float(steps.newton_s.sum()),
            "sum_audit_record_s": float(steps.audit_record_s.sum()),
        }
    report["performance"] = perf
    report["original_vtu_count"] = len(list(original.glob("*.vtu")))
    report["reduced_vtu_count"] = len(list(reduced.glob("*.vtu")))
    report["original_output_bytes"] = sum(path.stat().st_size for path in original.rglob("*") if path.is_file())
    report["reduced_output_bytes"] = sum(path.stat().st_size for path in reduced.rglob("*") if path.is_file())
    report["measured_reduction_fraction"] = 1 - report["reduced_output_bytes"] / report["original_output_bytes"]
    report["original_field_bytes"] = sum(path.stat().st_size for path in original.glob("*.vtu")) + (original / "OutputOriginal.pvd").stat().st_size
    report["reduced_field_bytes"] = sum(path.stat().st_size for path in reduced.glob("*.vtu")) + (reduced / "OutputReduced.pvd").stat().st_size
    report["measured_field_reduction_fraction"] = 1 - report["reduced_field_bytes"] / report["original_field_bytes"]
    report["state"] = "passed" if (
        report["binary_sha256_original"] == report["binary_sha256_reduced"]
        and max(v["max_absolute_difference"] for v in fields.values()) == 0
        and max(v["max_absolute_difference"] for v in report["tables"].values()) == 0
        and max(v["max_absolute_difference_M"] for v in profile_differences.values()) == 0
    ) else "failed"
    (ROOT / "equivalence_results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if report["state"] != "passed":
        sys.exit(1)


if __name__ == "__main__":
    main()
