"""Generate the experiment-constrained 4 mm inlet map on the frozen 3D mesh.

The line/circle-sector integration is copied from the accepted v13 geometry
preparation.  It integrates the circular aperture over each native polygonal
bottom face; it does not change the mesh or approximate the port by face
centres.
"""
from pathlib import Path
import hashlib
import json
import math
import os

import numpy as np


ROOT = Path(__file__).resolve().parent
MESH = ROOT / "inputs" / os.environ.get("GREAL_MESH", "filter_6layers.msh")
OUT = ROOT / "inputs" / os.environ.get("GREAL_PORT_MAP", "Greal04_port.txt")
EVIDENCE = ROOT / "results" / os.environ.get("GREAL_GEOMETRY_EVIDENCE", "geometry_preparation.json")
FILTER_LAYERS = int(os.environ.get("GREAL_FILTER_LAYERS", "6"))
DIAMETER_M = 0.004
CENTER_XZ_M = np.array([0.025, 0.0])


def cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def polygon_area(poly):
    return abs(sum(cross(a, b) for a, b in zip(poly, poly[1:] + poly[:1])) / 2)


def circle_overlap(poly, radius):
    total = 0.0
    for a, b in zip(poly, poly[1:] + poly[:1]):
        d = b - a
        aa = d @ d
        bb = 2 * (a @ d)
        cc = a @ a - radius * radius
        disc = bb * bb - 4 * aa * cc
        cuts = [0.0, 1.0]
        if disc > 0:
            cuts += [
                v
                for v in (
                    (-bb - math.sqrt(disc)) / (2 * aa),
                    (-bb + math.sqrt(disc)) / (2 * aa),
                )
                if 0 < v < 1
            ]
        cuts = sorted(cuts)
        for t, u in zip(cuts, cuts[1:]):
            p = a + t * d
            q = a + u * d
            mid = (p + q) / 2
            total += (
                cross(p, q) / 2
                if mid @ mid < radius * radius
                else radius * radius * math.atan2(cross(p, q), p @ q) / 2
            )
    return abs(total)


def circumcentre(poly):
    a = poly[0]
    b = poly[1] - a
    c = poly[2] - a
    return a + np.linalg.solve(np.array([b, c]) * 2, np.array([b @ b, c @ c]))


lines = MESH.read_text().splitlines()
i = lines.index("$Nodes")
nn = int(lines[i + 1])
nodes = {
    int(parts[0]): np.array(list(map(float, parts[1:])))
    for parts in (line.split() for line in lines[i + 2 : i + 2 + nn])
}
i = lines.index("$Elements")
ne = int(lines[i + 1])
elements = [list(map(int, line.split())) for line in lines[i + 2 : i + 2 + ne]]
bottom = []
filter_cells = 0
filter_y = []
for element in elements:
    node_ids = element[3 + element[2] :]
    half = len(node_ids) // 2
    ys = [nodes[k][1] for k in node_ids]
    if min(ys) < -1e-12:
        filter_cells += 1
        filter_y.extend(ys)
    if all(abs(nodes[k][1] + 0.0045) < 1e-12 for k in node_ids[:half]):
        bottom.append((element[1], node_ids[:half]))

assert len(bottom) == 768, len(bottom)
assert abs(min(filter_y) + 0.0045) < 1e-12
assert abs(max(filter_y)) < 1e-12

rows = []
radius = DIAMETER_M / 2
for _, node_ids in bottom:
    poly = [nodes[k][[0, 2]] - CENTER_XZ_M for k in node_ids]
    face_area = polygon_area(poly)
    cut = circle_overlap(poly, radius)
    cut = 0.0 if cut < face_area * 1e-12 else (face_area if cut > face_area * (1 - 1e-12) else cut)
    centre = circumcentre(poly) + CENTER_XZ_M
    rows.append((centre[0], centre[1], min(1.0, max(0.0, cut / face_area)), face_area))

analytic = math.pi * radius * radius
integrated = sum(fraction * area for _, _, fraction, area in rows)
relative_error = abs(integrated / analytic - 1)
assert relative_error < 1e-10, (integrated, analytic, relative_error)
np.savetxt(OUT, np.array(rows)[:, :3], fmt="%.17g")

face_areas = np.array([row[3] for row in rows])
active = [row for row in rows if row[2] > 0]
cut = [row for row in rows if 0 < row[2] < 1]
evidence = {
    "status": "passed",
    "mesh": MESH.name,
    "mesh_sha256": hashlib.sha256(MESH.read_bytes()).hexdigest(),
    "mesh_elements": ne,
    "filter_cells": filter_cells,
    "filter_thickness_m": 0.0045,
    "filter_layers": FILTER_LAYERS,
    "filter_layer_thickness_m": 0.0045 / FILTER_LAYERS,
    "bottom_faces": len(bottom),
    "port_map": OUT.name,
    "port_map_sha256": hashlib.sha256(OUT.read_bytes()).hexdigest(),
    "nominal_diameter_m": DIAMETER_M,
    "centre_xz_m": CENTER_XZ_M.tolist(),
    "analytic_area_m2": analytic,
    "integrated_active_area_m2": integrated,
    "relative_area_error": relative_error,
    "active_faces": len(active),
    "cut_faces": len(cut),
    "bottom_face_area_min_m2": float(face_areas.min()),
    "bottom_face_area_max_m2": float(face_areas.max()),
    "bottom_face_equivalent_diameter_max_m": float(2 * math.sqrt(face_areas.max() / math.pi)),
    "interpretation": (
        "Exact integrated area on the frozen mesh; this does not establish local radial-pressure "
        "or through-filter spatial convergence. The layer count is recorded for controlled comparison."
    ),
}
EVIDENCE.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
print(json.dumps(evidence, indent=2))
