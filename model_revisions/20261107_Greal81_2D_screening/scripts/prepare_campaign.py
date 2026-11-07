#!/usr/bin/env python3
"""Generate immutable 2D meshes, inputs and the deduplicated Task-10 matrix."""
from __future__ import annotations

import configparser
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT / "inputs"
MESHES = INPUTS / "meshes"
GATES = INPUTS / "gates"
CASES = INPUTS / "cases"
VALIDATION = INPUTS / "validation"
for directory in (MESHES, GATES, CASES, VALIDATION):
    directory.mkdir(parents=True, exist_ok=True)

R = 0.025
H = 0.04
FILTER_H = 0.0045
PRIMARY_WIDTH = math.pi * R / 2.0
PRIMARY_EXTRUSION = 2.0 * R
SENSITIVITY_WIDTH = 0.05
SENSITIVITY_EXTRUSION = math.pi * R * R / SENSITIVITY_WIDTH
INLET_DIAMETER = 0.004
INLET_AREA = math.pi * INLET_DIAMETER**2 / 4.0
PRIMARY_INLET_WIDTH = INLET_AREA / PRIMARY_EXTRUSION
KC0 = 7.819185772155931e-12
KF0 = 3.2034098778596945e-14
DELTA0 = 0.008100162249880822

# The accepted 3D Greal-81 sand layers, including the 0.0667 mm top layer.
Y_SAND = [
    0.0, 0.00406001, 0.00771402, 0.0110026, 0.0139624,
    0.0166261, 0.0190235, 0.0211812, 0.0231231, 0.0248708,
    0.0264437, 0.0278594, 0.0291334, 0.0302801, 0.0313121,
    0.0322409, 0.0330768, 0.0338292, 0.0345062, 0.0351156,
    0.0356641, 0.0361577, 0.0366019, 0.0370017, 0.0373616,
    0.0376854, 0.0379769, 0.0382392, 0.0384753, 0.0386878,
    0.038879, 0.0390511, 0.039206, 0.0393454, 0.0394709,
    0.0395838, 0.0396855, 0.0397769, 0.0398592, 0.0399333, 0.04,
]


def unique_sorted(values: list[float]) -> list[float]:
    return sorted({round(value, 15) for value in values})


def x_coordinates(width: float, nx: int, inlet_width: float) -> list[float]:
    split = width / 2.0
    values = [width * i / nx for i in range(nx + 1)]
    values += [split, split - inlet_width / 2.0, split + inlet_width / 2.0]
    result = unique_sorted(values)
    assert result[0] == 0.0 and abs(result[-1] - width) < 1e-14
    assert any(abs(value - split) < 1e-14 for value in result)
    return result


def y_coordinates(refined: bool, explicit_filter: bool) -> list[float]:
    values = list(Y_SAND)
    if refined:
        values += [(a + b) / 2.0 for a, b in zip(Y_SAND[:-1], Y_SAND[1:])]
    if explicit_filter:
        values += [-FILTER_H + FILTER_H * i / 6.0 for i in range(6)]
    return unique_sorted(values)


def write_mesh(path: Path, width: float, extrusion: float, nx: int,
               explicit_filter: bool, refined: bool = False) -> dict[str, float | int]:
    inlet_width = INLET_AREA / extrusion
    xs = x_coordinates(width, nx, inlet_width)
    ys = y_coordinates(refined, explicit_filter)
    nodes = [(x, y) for y in ys for x in xs]
    elements: list[tuple[int, int, int, int]] = []
    stride = len(xs)
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            lower_left = j * stride + i + 1
            elements.append((lower_left, lower_left + 1,
                             lower_left + stride + 1, lower_left + stride))
    lines = ["$MeshFormat", "2.2 0 8", "$EndMeshFormat", "$Nodes", str(len(nodes))]
    lines += [f"{i + 1} {x:.17g} {y:.17g} 0" for i, (x, y) in enumerate(nodes)]
    lines += ["$EndNodes", "$Elements", str(len(elements))]
    lines += [f"{i + 1} 3 2 1 1 {' '.join(map(str, element))}"
              for i, element in enumerate(elements)]
    lines += ["$EndElements"]
    path.write_text("\n".join(lines) + "\n", encoding="ascii", newline="\n")
    return {
        "nodes": len(nodes), "cells": len(elements), "x_cells": len(xs) - 1,
        "y_cells": len(ys) - 1, "width_m": width, "extrusion_m": extrusion,
        "inlet_width_m": inlet_width, "top_area_m2": width * extrusion,
        "sand_volume_m3": width * extrusion * H,
        "direct_interface_area_m2": extrusion * H,
    }


def clone_config() -> configparser.ConfigParser:
    source = configparser.ConfigParser()
    source.optionxform = str
    source.read(INPUTS / "Greal-81.input", encoding="utf-8")
    result = configparser.ConfigParser()
    result.optionxform = str
    result.read_dict({section: dict(source[section]) for section in source.sections()})
    return result


def write_input(path: Path, *, name: str, config: str, connection: int,
                buoyancy: int, kc_factor: float = 1.0, kf_factor: float = 1.0,
                delta_factor: float = 1.0, evaporation_h: float = 60.0,
                causal_selftest: bool = False, refined: bool = False,
                sensitivity: bool = False, vtk_every: int = 6) -> None:
    cfg = clone_config()
    width = SENSITIVITY_WIDTH if sensitivity else PRIMARY_WIDTH
    extrusion = SENSITIVITY_EXTRUSION if sensitivity else PRIMARY_EXTRUSION
    explicit_filter = config == "B"
    mesh_stem = "sensitivity50" if sensitivity else "primary"
    mesh_stem += "_filter" if explicit_filter else "_sand"
    if refined:
        mesh_stem += "_refined"
    cfg["Problem"]["Name"] = name
    cfg["Grid"]["File"] = f"{mesh_stem}.msh"
    cfg["TimeLoop"]["TEnd"] = f"{7200 + evaporation_h * 3600:.17g}"
    cfg["TimeLoop"]["CheckpointOutputInterval"] = "3600"
    cfg["Revision"]["ExplicitFilter"] = str(explicit_filter).lower()
    cfg["Revision"].pop("PortAreaFile", None)
    cfg["Revision"]["EquivalentInletWidth"] = f"{INLET_AREA / extrusion:.17g}"
    cfg["Revision"]["InterfaceExchangeEnabled"] = str(bool(connection)).lower()
    cfg["Revision"]["SalinityBuoyancyScale"] = str(float(buoyancy))
    cfg["Revision"]["CausalSelfTest"] = str(causal_selftest).lower()
    cfg["Revision"]["WaterFluxAreaCorrection"] = "1"
    cfg["Revision"]["FilmThickness"] = f"{DELTA0 * delta_factor:.17g}"
    cfg["SpatialParams"]["SplitCoordinate"] = f"{width / 2.0:.17g}"
    cfg["SpatialParams"]["CoarsePermeability"] = f"{KC0 * kc_factor:.17g}"
    cfg["SpatialParams"]["FinePermeability"] = f"{KF0 * kf_factor:.17g}"
    cfg["Benchmark"]["VtkEvery"] = str(vtk_every)
    cfg["Geometry"] = {
        "ExtrusionWidth": f"{extrusion:.17g}",
        "PrimaryEquivalent": str(not sensitivity).lower(),
    }
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        cfg.write(stream)


mesh_metadata: dict[str, dict[str, float | int]] = {}
for stem, width, extrusion in (
    ("primary", PRIMARY_WIDTH, PRIMARY_EXTRUSION),
    ("sensitivity50", SENSITIVITY_WIDTH, SENSITIVITY_EXTRUSION),
):
    for explicit_filter in (False, True):
        for refined in (False, True):
            suffix = "_filter" if explicit_filter else "_sand"
            if refined:
                suffix += "_refined"
            name = stem + suffix + ".msh"
            mesh_metadata[name] = write_mesh(
                MESHES / name, width, extrusion, 200 if refined else 100,
                explicit_filter, refined,
            )

# Production-mesh causal gates: both supply configurations and all C/B switches.
for config in ("A", "B"):
    for connection in (1, 0):
        for buoyancy in (1, 0):
            name = f"M0_{config}_C{connection}B{buoyancy}"
            write_input(GATES / f"{name}.input", name=name, config=config,
                        connection=connection, buoyancy=buoyancy,
                        evaporation_h=0.01, causal_selftest=True, vtk_every=1)
    name = f"M0_{config}_conservation_4h"
    write_input(GATES / f"{name}.input", name=name, config=config,
                connection=1, buoyancy=1, evaporation_h=4, vtk_every=2)

# Dynamic supply-representation and later numerical-sensitivity cases.  Only
# the A baseline pair is eligible for M1 release; M6 cases remain held.
for connection in (1, 0):
    name = f"M1_A_C{connection}B1_24h"
    write_input(VALIDATION / f"{name}.input", name=name, config="A",
                connection=connection, buoyancy=1, evaporation_h=24)
    name = f"M6_B_width50_C{connection}B1_24h"
    write_input(VALIDATION / f"{name}.input", name=name, config="B",
                connection=connection, buoyancy=1, evaporation_h=24,
                sensitivity=True)
write_input(VALIDATION / "M6_B_refined_C1B1_12h.input",
            name="M6_B_refined_C1B1_12h", config="B", connection=1,
            buoyancy=1, evaporation_h=12, refined=True)
write_input(VALIDATION / "M6_B_dt150_C1B1_12h.input",
            name="M6_B_dt150_C1B1_12h", config="B", connection=1,
            buoyancy=1, evaporation_h=12)
# Time-step refinement changes only this registered numerical control.
cfg_dt = configparser.ConfigParser(); cfg_dt.optionxform = str
cfg_dt.read(VALIDATION / "M6_B_dt150_C1B1_12h.input", encoding="utf-8")
cfg_dt["TimeLoop"]["MaxTimeStepSize"] = "150"
with (VALIDATION / "M6_B_dt150_C1B1_12h.input").open("w", encoding="utf-8", newline="\n") as stream:
    cfg_dt.write(stream)

physical: dict[tuple[float, float, float], set[str]] = {}
for kc in (0.5, 1.0, 2.0):
    for kf in (0.25, 1.0, 4.0):
        physical.setdefault((kc, kf, 1.0), set()).add("A")
for kc in (0.5, 1.0, 2.0):
    for delta in (0.75, 1.0, 1.33):
        physical.setdefault((kc, 1.0, delta), set()).add("B")

rows: list[dict[str, str | float | int]] = []
for kc, kf, delta in sorted(physical):
    physical_id = f"Kc{kc:g}_Kf{kf:g}_D{delta:g}".replace(".", "p")
    for connection in (1, 0):
        case_id = f"S_{physical_id}_C{connection}B1"
        write_input(CASES / f"{case_id}.input", name=case_id, config="B",
                    connection=connection, buoyancy=1, kc_factor=kc,
                    kf_factor=kf, delta_factor=delta)
        rows.append({
            "case_id": case_id, "physical_id": physical_id,
            "matrix_membership": "+".join(sorted(physical[(kc, kf, delta)])),
            "supply_config": "B", "connection": connection, "buoyancy": 1,
            "kc_factor": kc, "kf_factor": kf, "delta_factor": delta,
            "kc_m2": KC0 * kc, "kf_m2": KF0 * kf,
            "film_thickness_m": DELTA0 * delta, "evaporation_endpoint_h": 60,
            "status": "registered_not_submitted",
        })

# Required reference B0 pair; additional B0 points remain evidence-selected.
for connection in (1, 0):
    case_id = f"B0_reference_C{connection}B0"
    write_input(CASES / f"{case_id}.input", name=case_id, config="B",
                connection=connection, buoyancy=0)
    rows.append({
        "case_id": case_id, "physical_id": "Kc1_Kf1_D1",
        "matrix_membership": "B0_reference", "supply_config": "B",
        "connection": connection, "buoyancy": 0, "kc_factor": 1,
        "kf_factor": 1, "delta_factor": 1, "kc_m2": KC0, "kf_m2": KF0,
        "film_thickness_m": DELTA0, "evaporation_endpoint_h": 60,
        "status": "registered_not_submitted",
    })

fields = list(rows[0])
with (ROOT / "CASE_MATRIX.csv").open("w", encoding="utf-8", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)

geometry = {
    "primary": {
        "width_m": PRIMARY_WIDTH, "half_width_m": PRIMARY_WIDTH / 2,
        "extrusion_m": PRIMARY_EXTRUSION,
        "equivalent_inlet_width_m": PRIMARY_INLET_WIDTH,
        "sand_volume_m3": PRIMARY_WIDTH * H * PRIMARY_EXTRUSION,
        "top_area_m2": PRIMARY_WIDTH * PRIMARY_EXTRUSION,
        "direct_interface_area_m2": H * PRIMARY_EXTRUSION,
    },
    "sensitivity_50mm": {
        "width_m": SENSITIVITY_WIDTH, "extrusion_m": SENSITIVITY_EXTRUSION,
        "equivalent_inlet_width_m": INLET_AREA / SENSITIVITY_EXTRUSION,
        "direct_interface_area_m2": H * SENSITIVITY_EXTRUSION,
    },
    "meshes": mesh_metadata,
    "unique_physical_combinations": len(physical),
    "unique_B1_cases": 2 * len(physical),
    "registered_core_cases": len(rows),
}
(ROOT / "geometry_and_matrix.json").write_text(
    json.dumps(geometry, indent=2) + "\n", encoding="utf-8")

manifest: dict[str, str] = {}
for path in sorted(INPUTS.rglob("*")):
    if path.is_file():
        manifest[str(path.relative_to(ROOT)).replace("\\", "/")] = hashlib.sha256(path.read_bytes()).hexdigest()
(ROOT / "input_manifest.json").write_text(
    json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print(json.dumps(geometry, indent=2))
