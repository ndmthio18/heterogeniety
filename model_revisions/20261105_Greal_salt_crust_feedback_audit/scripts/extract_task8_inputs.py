"""Extract only the accepted face/budget rows needed by Task 8.

The accepted files remain read-only.  This helper records their full-file SHA256
before writing a compact, auditable subset for the seven requested snapshots.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np


CASES = ("Greal-81", "Greal-75")
TIMES = (72.0, 84.0, 96.0, 108.0, 120.0, 144.0, 174.0)
FILES = ("film_faces.csv", "film_budget.csv", "budget.csv",
         "mineral_budget.csv", "material_budgets.csv")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def selected(time_h: str) -> bool:
    value = float(time_h)
    return any(abs(value - target) <= 1e-8 for target in TIMES)


def arrays(path: Path):
    root = ET.parse(path).getroot()
    return {e.attrib["Name"]: np.fromstring(e.text or "", sep=" ")
            for e in root.iter("DataArray") if "Name" in e.attrib}


def pvd_files(root: Path, case: str):
    tree = ET.parse(root / f"{case}.pvd").getroot()
    datasets = [(float(e.attrib["timestep"]), e.attrib["file"])
                for e in tree.findall(".//DataSet")]
    result = {}
    for hour in TIMES:
        hits = [name for time, name in datasets
                if abs(time - (hour * 3600 + 7200)) <= 1e-6]
        if len(hits) != 1:
            raise AssertionError((case, hour, hits))
        result[hour] = root / hits[0]
    return result


def top_temperatures(path: Path):
    data = arrays(path)
    points = data["Coordinates"].reshape(-1, 3)
    conn = data["connectivity"].astype(int)
    offsets = data["offsets"].astype(int)
    starts = np.r_[0, offsets[:-1]]
    values = data["T"]
    rows = []
    for cell_id, (lo, hi) in enumerate(zip(starts, offsets)):
        xyz = points[conn[lo:hi]]
        if not np.isclose(xyz[:, 1].max(), 0.04, atol=1e-11, rtol=0):
            continue
        center = xyz.mean(axis=0)
        if center[0] > 0.025:
            rows.append((cell_id, center[0], center[2], values[cell_id]))
    if len(rows) != 384:
        raise AssertionError((path, len(rows)))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    manifest = {"source_root": str(args.source), "times_h": TIMES,
                "files": {}, "outputs": {}}
    for case in CASES:
        root = args.source / case
        manifest["files"][case] = {}
        for name in FILES:
            path = root / name
            manifest["files"][case][name] = {
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }

        source = root / "film_faces.csv"
        target = args.out / f"{case}_film_faces_selected.csv"
        counts = {f"{time:g}": 0 for time in TIMES}
        with source.open(encoding="utf-8", newline="") as inp, \
                target.open("w", encoding="utf-8", newline="") as out:
            reader = csv.DictReader(inp)
            writer = csv.DictWriter(out, fieldnames=reader.fieldnames)
            writer.writeheader()
            for row in reader:
                if selected(row["evaporation_time_h"]):
                    writer.writerow(row)
                    counts[f"{float(row['evaporation_time_h']):g}"] += 1
        if set(counts.values()) != {768}:
            raise AssertionError((case, counts))
        manifest["outputs"][target.name] = {
            "rows": sum(counts.values()), "rows_by_time": counts,
            "bytes": target.stat().st_size, "sha256": sha256(target),
        }

        temperature_target = args.out / f"{case}_top_temperature_selected.csv"
        vtk_manifest = {}
        with temperature_target.open("w", encoding="utf-8", newline="") as out:
            writer = csv.writer(out)
            writer.writerow(["case", "time_h", "cell_id", "cell_center_x_m",
                             "cell_center_z_m", "T_K"])
            for hour, vtk in pvd_files(root, case).items():
                vtk_manifest[f"{hour:g}"] = {
                    "path": str(vtk.relative_to(args.source)),
                    "bytes": vtk.stat().st_size,
                    "sha256": sha256(vtk),
                }
                for cell_id, x, z, temperature in top_temperatures(vtk):
                    writer.writerow([case, f"{hour:g}", cell_id,
                                     f"{x:.17g}", f"{z:.17g}",
                                     f"{temperature:.17g}"])
        manifest["files"][case]["selected_vtk"] = vtk_manifest
        manifest["outputs"][temperature_target.name] = {
            "rows": len(TIMES) * 384,
            "bytes": temperature_target.stat().st_size,
            "sha256": sha256(temperature_target),
        }

        for name in FILES[1:]:
            source = root / name
            target = args.out / f"{case}_{name}"
            target.write_bytes(source.read_bytes())
            manifest["outputs"][target.name] = {
                "bytes": target.stat().st_size, "sha256": sha256(target),
            }

    path = args.out / "task8_input_manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
