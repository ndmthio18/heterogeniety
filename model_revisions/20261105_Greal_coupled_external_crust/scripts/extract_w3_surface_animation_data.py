"""Extract lightweight W3 top-cell crust geometry and hourly inventory from VTU.

Run this script next to the completed Frodo ``run`` directory.  It preserves
the native top-face polygons and the cellwise solid inventory; no spatial
interpolation is performed.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import vtk


SOLID_ARRAY = "precipitateVolumeFraction^NaCl"
TOP_Y_TOLERANCE_M = 1.0e-10
W3_SPLIT_X_M = 0.025
CRUST_POROSITY = 0.43
DETECTION_VF = 1.0e-12


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_vtu(path: Path):
    reader = vtk.vtkXMLUnstructuredGridReader()
    reader.SetFileName(str(path))
    reader.Update()
    grid = reader.GetOutput()
    if grid.GetNumberOfCells() == 0:
        raise RuntimeError(f"No cells read from {path}")
    return grid


def cell_centres(grid):
    centres = vtk.vtkCellCenters()
    centres.SetInputData(grid)
    centres.Update()
    return centres.GetOutput().GetPoints()


def cell_volumes(grid):
    sizes = vtk.vtkCellSizeFilter()
    sizes.SetInputData(grid)
    sizes.ComputeVolumeOn()
    sizes.Update()
    result = sizes.GetOutput().GetCellData().GetArray("Volume")
    if result is None:
        raise RuntimeError("VTK did not produce a Volume cell array")
    return result


def top_face(grid, cell_id: int, ymax: float):
    cell = grid.GetCell(cell_id)
    for face_id in range(cell.GetNumberOfFaces()):
        face = cell.GetFace(face_id)
        points = [face.GetPoints().GetPoint(i) for i in range(face.GetNumberOfPoints())]
        if min(point[1] for point in points) >= ymax - TOP_Y_TOLERANCE_M:
            return face, points
    raise RuntimeError(f"No atmospheric face found for cell {cell_id}")


def horizontal_polygon_area(points) -> float:
    """Return native x-z polygon area; top-face vertices retain VTK order."""
    twice_area = 0.0
    for index, point in enumerate(points):
        following = points[(index + 1) % len(points)]
        twice_area += point[0] * following[2] - following[0] * point[2]
    area = abs(twice_area) / 2.0
    if area <= 0.0:
        raise RuntimeError(f"Non-positive top-face area for vertices {points}")
    return area


def datasets(pvd: Path):
    root = ET.parse(pvd).getroot()
    rows = []
    for node in root.findall(".//DataSet"):
        time_s = float(node.attrib["timestep"])
        rows.append((time_s, pvd.parent / node.attrib["file"]))
    if not rows:
        raise RuntimeError(f"No DataSet entries in {pvd}")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--pvd", default="Greal81_external_crust.pvd")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=False)
    series = datasets(args.run_dir / args.pvd)
    first = read_vtu(series[0][1])
    bounds = first.GetBounds()
    ymax = bounds[3]
    centres = cell_centres(first)
    volumes = cell_volumes(first)

    surface = []
    for cell_id in range(first.GetNumberOfCells()):
        x, y, z = centres.GetPoint(cell_id)
        if x < W3_SPLIT_X_M - 1.0e-12:
            continue
        cell = first.GetCell(cell_id)
        ys = [first.GetPoint(cell.GetPointId(i))[1] for i in range(cell.GetNumberOfPoints())]
        if max(ys) < ymax - TOP_Y_TOLERANCE_M:
            continue
        face, points = top_face(first, cell_id, ymax)
        area = horizontal_polygon_area(points)
        volume = float(volumes.GetTuple1(cell_id))
        surface.append(
            {
                "cell_id": cell_id,
                "dof_id": int(first.GetCellData().GetArray("dof_id").GetTuple1(cell_id)),
                "x_m": x,
                "z_m": z,
                "area_m2": area,
                "volume_m3": volume,
                "vertices_xz_m": [[point[0], point[2]] for point in points],
            }
        )
    if len(surface) != 384:
        raise RuntimeError(f"Expected 384 W3 top cells; found {len(surface)}")

    geometry_path = args.output_dir / "w3_top_geometry.json"
    geometry_path.write_text(json.dumps(surface, indent=2), encoding="utf-8")

    data_path = args.output_dir / "w3_surface_crust_hourly.csv"
    summaries = []
    with data_path.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "time_s",
            "evaporation_h",
            "cell_id",
            "dof_id",
            "solid_vf",
            "equivalent_external_height_m",
            "detected",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for time_s, path in series:
            grid = read_vtu(path)
            array = grid.GetCellData().GetArray(SOLID_ARRAY)
            if array is None:
                raise RuntimeError(f"Missing {SOLID_ARRAY} in {path}")
            mass_volume = 0.0
            maximum = 0.0
            detected_area = 0.0
            for item in surface:
                solid_vf = float(array.GetTuple1(item["cell_id"]))
                height = solid_vf * item["volume_m3"] / item["area_m2"] / (1.0 - CRUST_POROSITY)
                detected = solid_vf > DETECTION_VF
                writer.writerow(
                    {
                        "time_s": f"{time_s:.17g}",
                        "evaporation_h": f"{(time_s - 7200.0) / 3600.0:.17g}",
                        "cell_id": item["cell_id"],
                        "dof_id": item["dof_id"],
                        "solid_vf": f"{solid_vf:.17g}",
                        "equivalent_external_height_m": f"{height:.17g}",
                        "detected": int(detected),
                    }
                )
                mass_volume += solid_vf * item["volume_m3"]
                maximum = max(maximum, height)
                if detected:
                    detected_area += item["area_m2"]
            summaries.append(
                {
                    "time_s": time_s,
                    "evaporation_h": (time_s - 7200.0) / 3600.0,
                    "solid_crystal_volume_m3": mass_volume,
                    "external_mass_kg": mass_volume * 2165.0,
                    "max_height_m": maximum,
                    "detected_area_m2": detected_area,
                }
            )

    summary_path = args.output_dir / "w3_surface_summary_hourly.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summaries[0]))
        writer.writeheader()
        writer.writerows(summaries)

    manifest = {
        "source_run": str(args.run_dir),
        "source_pvd": args.pvd,
        "source_pvd_sha256": sha256(args.run_dir / args.pvd),
        "frames": len(series),
        "surface_cells": len(surface),
        "evaporation_time_range_h": [summaries[0]["evaporation_h"], summaries[-1]["evaporation_h"]],
        "solid_array": SOLID_ARRAY,
        "mapping": "native W3 atmospheric top faces; no spatial interpolation",
        "height_equation": "solid_vf*cell_volume/top_face_area/(1-crust_porosity)",
        "crust_porosity": CRUST_POROSITY,
        "crystal_density_kg_m3": 2165.0,
        "external_fraction": 1.0,
        "detection_solid_vf": DETECTION_VF,
        "files": {
            geometry_path.name: sha256(geometry_path),
            data_path.name: sha256(data_path),
            summary_path.name: sha256(summary_path),
        },
    }
    manifest_path = args.output_dir / "extraction_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
