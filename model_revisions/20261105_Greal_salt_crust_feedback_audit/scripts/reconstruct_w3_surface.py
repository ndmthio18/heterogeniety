"""Read-only reconstruction of W3 top-cell solid NaCl and hypothetical crust maps."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.colors import LogNorm
import numpy as np
from scipy.spatial import ConvexHull
from PIL import Image

TIMES = (60, 72, 84, 96, 108, 120, 144, 174)
MAP_TIMES = (72, 84, 96, 108, 120, 144, 174)
CASES = ("Greal-81", "Greal-75")
VF_THRESHOLDS = (1e-15, 1e-12, 1e-9, 1e-6)
PRIMARY_THRESHOLD = 1e-12
RHO_NACL = 2165.0
M_NACL = 0.0584428  # kg/mol, accepted DuMuX Components::NaCl convention
RHO_MOLAR = RHO_NACL / M_NACL
CRUST_POROSITY = 0.43
ALPHAS = (0.25, 0.5, 1.0)
ABS_TOL_MOL = 5e-13
REL_TOL = 5e-10


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--expected-hashes", type=Path, required=True)
    p.add_argument("--inventory-summary", type=Path, required=True)
    return p.parse_args()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def vtk_arrays(path: Path):
    root = ET.parse(path).getroot()
    return {e.attrib["Name"]: np.fromstring(e.text or "", sep=" ")
            for e in root.iter("DataArray") if "Name" in e.attrib}


def polygon_area_xz(poly: np.ndarray) -> float:
    center = poly.mean(axis=0)
    order = np.argsort(np.arctan2(poly[:, 1] - center[1], poly[:, 0] - center[0]))
    q = poly[order]
    return abs(np.dot(q[:, 0], np.roll(q[:, 1], -1))
               - np.dot(q[:, 1], np.roll(q[:, 0], -1))) / 2


def ordered_polygon(poly: np.ndarray) -> np.ndarray:
    center = poly.mean(axis=0)
    return poly[np.argsort(np.arctan2(poly[:, 1] - center[1], poly[:, 0] - center[0]))]


def build_top_geometry(arr):
    pts = arr["Coordinates"].reshape(-1, 3)
    conn, offsets = arr["connectivity"].astype(int), arr["offsets"].astype(int)
    types = arr["types"].astype(int)
    starts = np.r_[0, offsets[:-1]]
    rows, keys = [], []
    for cell_id, (lo, hi) in enumerate(zip(starts, offsets)):
        ids = conn[lo:hi]
        xyz = pts[ids]
        if not np.isclose(xyz[:, 1].max(), 0.04, atol=1e-11, rtol=0):
            continue
        face_ids = ids[np.isclose(xyz[:, 1], 0.04, atol=1e-11, rtol=0)]
        if len(face_ids) not in (3, 4):
            raise AssertionError((cell_id, "top face vertex count", len(face_ids)))
        xz = ordered_polygon(pts[face_ids][:, [0, 2]])
        area = polygon_area_xz(xz)
        center = xyz.mean(axis=0)
        key = tuple(sorted(map(int, face_ids)))
        if key in keys:
            raise AssertionError((cell_id, "duplicate top boundary face"))
        keys.append(key)
        rows.append(dict(cell_id=cell_id, cell_type=int(types[cell_id]),
                         cell_center_x_m=float(center[0]), cell_center_y_m=float(center[1]),
                         cell_center_z_m=float(center[2]), cell_volume_m3=float(ConvexHull(xyz).volume),
                         face_center_x_m=float(xz[:, 0].mean()), face_center_z_m=float(xz[:, 1].mean()),
                         face_area_m2=float(area), top_face_vertex_count=len(face_ids),
                         top_face_vertices_xz=json.dumps(xz.tolist(), separators=(",", ":")),
                         _poly=xz))
    if len(rows) != 768:
        raise AssertionError(("top cell count", len(rows), 768))
    w3 = [r for r in rows if r["cell_center_x_m"] > 0.025]
    f36 = [r for r in rows if r["cell_center_x_m"] <= 0.025]
    if len(w3) != 384 or len(f36) != 384:
        raise AssertionError(("material top counts", len(w3), len(f36)))
    return w3, f36


def read_pvd(case_root: Path, case: str):
    root = ET.parse(case_root / f"{case}.pvd").getroot()
    items = [(float(d.attrib["timestep"]), d.attrib["file"])
             for d in root.findall(".//DataSet")]
    result = {}
    for hour in TIMES:
        hits = [name for t, name in items if abs(t - (hour * 3600 + 7200)) < 1e-6]
        if len(hits) != 1:
            raise AssertionError((case, hour, "PVD match", hits))
        result[hour] = case_root / hits[0]
    return result


def read_csv_rows(path: Path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def nearest_time_rows(rows, time_key, target, extra=None):
    candidates = [r for r in rows if extra is None or extra(r)]
    delta = np.array([abs(float(r[time_key]) - target) for r in candidates])
    best = delta.min()
    if best > 1e-8:
        raise AssertionError((time_key, target, best))
    return [r for r, d in zip(candidates, delta) if d == best]


def weighted_quantile(values, weights, q):
    order = np.argsort(values)
    v, w = np.asarray(values)[order], np.asarray(weights)[order]
    c = np.cumsum(w) / np.sum(w)
    return float(np.interp(q, c, v))


def mass_fraction_within_area(loadings, areas, fraction):
    order = np.argsort(loadings)[::-1]
    a, density = np.asarray(areas)[order], np.asarray(loadings)[order]
    target, used, mass = fraction * a.sum(), 0.0, 0.0
    for ai, di in zip(a, density):
        take = min(ai, target - used)
        if take <= 0:
            break
        mass += take * di
        used += take
    total = float(np.sum(a * density))
    return 0.0 if total == 0 else float(np.clip(mass / total, 0.0, 1.0))


def concentration_curve(loadings, areas):
    order = np.argsort(loadings)[::-1]
    a, density = np.asarray(areas)[order], np.asarray(loadings)[order]
    mass = a * density
    return np.r_[0, np.cumsum(a) / a.sum()], np.r_[0, np.cumsum(mass) / mass.sum()]


def face_polys(rows):
    return [json.loads(r["top_face_vertices_xz"]) for r in rows]


def maps_figure(rows, case, variable, label, output, times, norm, cmap):
    fig, axes = plt.subplots(2, 4, figsize=(178 / 25.4, 86 / 25.4),
                             layout="constrained", sharex=True, sharey=True)
    for ax, hour in zip(axes.flat, times):
        part = [r for r in rows if r["case"] == case and r["time_h"] == hour]
        vals = np.array([r[variable] if r["solid_detected_primary"] else np.nan for r in part])
        coll = PolyCollection(face_polys(part), array=vals, cmap=cmap, norm=norm,
                              edgecolors="none")
        ax.add_collection(coll); ax.autoscale_view(); ax.set_aspect("equal")
        ax.set_title(f"{hour} h")
        ax.axvline(0.025, color="black", lw=.5)
    axes.flat[-1].axis("off")
    for ax in axes[-1, :3]: ax.set_xlabel("x (m)")
    for ax in axes[:, 0]: ax.set_ylabel("z (m)")
    sm = mpl.cm.ScalarMappable(norm=norm, cmap=cmap)
    fig.colorbar(sm, ax=axes[:, :], label=label, shrink=.82)
    fig.suptitle(f"{case} W3; gray = below VF threshold {PRIMARY_THRESHOLD:g}")
    fig.savefig(output.with_suffix(".png"), dpi=300, facecolor="white")
    fig.savefig(output.with_suffix(".pdf"), facecolor="white")
    plt.close(fig)


def diagnostics_figures(map_rows, coverage, stats, figdir):
    colors = plt.cm.viridis(np.linspace(.1, .9, len(MAP_TIMES)))
    fig, ax = plt.subplots(figsize=(120 / 25.4, 75 / 25.4), layout="constrained")
    for color, hour in zip(colors, MAP_TIMES):
        part = [r for r in map_rows if r["case"] == "Greal-81" and r["time_h"] == hour]
        x, y = concentration_curve([r["solid_mass_kg_m2"] if r["solid_detected_primary"] else 0.0 for r in part],
                                   [r["face_area_m2"] for r in part])
        ax.plot(x * 100, y * 100, color=color, label=f"{hour} h")
    ax.plot([0, 100], [0, 100], "k:", lw=.8, label="uniform")
    ax.set(xlabel="Cumulative W3 area, highest loading first (%)",
           ylabel="Cumulative solid mass (%)", xlim=(0, 100), ylim=(0, 100))
    ax.legend(ncol=2, fontsize=7)
    fig.savefig(figdir / "Figure_T2_mass_concentration.png", dpi=300, facecolor="white")
    fig.savefig(figdir / "Figure_T2_mass_concentration.pdf", facecolor="white"); plt.close(fig)

    fig, ax = plt.subplots(figsize=(120 / 25.4, 75 / 25.4), layout="constrained")
    for color, hour in zip(colors, MAP_TIMES):
        part = [r for r in map_rows if r["case"] == "Greal-81" and r["time_h"] == hour]
        h = np.array([r["height_alpha1_mm"] for r in part]); a = np.array([r["face_area_m2"] for r in part])
        order = np.argsort(h); x, w = h[order], a[order]
        ax.step(x, np.cumsum(w) / w.sum(), where="post", color=color, label=f"{hour} h")
    ax.set_xscale("symlog", linthresh=1e-3, linscale=.5)
    ax.set_xticks([0, 1e-3, 1e-2, 1e-1, 1])
    ax.set_xticklabels(["0", "$10^{-3}$", "$10^{-2}$", "$10^{-1}$", "$10^{0}$"])
    ax.set(xlabel="Hypothetical local crust height, alpha=1 (mm)", ylabel="Area-weighted CDF", ylim=(0, 1))
    ax.legend(ncol=2, fontsize=7)
    fig.savefig(figdir / "Figure_T3_thickness_distributions.png", dpi=300, facecolor="white")
    fig.savefig(figdir / "Figure_T3_thickness_distributions.pdf", facecolor="white"); plt.close(fig)

    fig, ax = plt.subplots(figsize=(120 / 25.4, 75 / 25.4), layout="constrained")
    for threshold, style in zip(VF_THRESHOLDS, [":", "-", "--", "-."]):
        part = [r for r in coverage if r["case"] == "Greal-81" and r["vf_threshold"] == threshold]
        ax.plot([r["time_h"] for r in part], [100*r["bearing_area_fraction"] for r in part],
                style, marker="o", ms=3, label=f"VF > {threshold:g}")
    ax.set(xlabel="Evaporation time (h)", ylabel="Numerical salt-bearing W3 area (%)", ylim=(0, 100))
    ax.legend(fontsize=7)
    fig.savefig(figdir / "Figure_T4_coverage_thresholds.png", dpi=300, facecolor="white")
    fig.savefig(figdir / "Figure_T4_coverage_thresholds.pdf", facecolor="white"); plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(178 / 25.4, 67 / 25.4), layout="constrained")
    for ax, variable, label in [(axes[0], "solid_mass_kg_m2", "Solid loading (kg m$^{-2}$)"),
                                (axes[1], "height_alpha1_mm", "Hypothetical height (mm)")]:
        combined = [r for r in map_rows if r["time_h"] == 174]
        positive = [r[variable] for r in combined if r["solid_detected_primary"]]
        norm = LogNorm(vmin=min(positive), vmax=max(positive))
        for case, hatch in [("Greal-81", None), ("Greal-75", "//")]:
            part = [r for r in combined if r["case"] == case]
            vals = np.array([r[variable] if r["solid_detected_primary"] else np.nan for r in part])
            coll = PolyCollection(face_polys(part), array=vals, cmap=mpl.colormaps["viridis"].with_extremes(bad="#d9d9d9"),
                                  norm=norm, edgecolors="none")
            # Plot side-by-side by shifting Greal-75 in x; coordinates remain metrically scaled.
            offset = 0 if case == "Greal-81" else .028
            shifted = [np.asarray(p) + [offset, 0] for p in face_polys(part)]
            coll.set_verts(shifted); ax.add_collection(coll)
            ax.text(.037 + offset, -.027, case, ha="center", fontsize=7)
        ax.autoscale_view(); ax.set_aspect("equal"); ax.set_title(label)
        fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap="viridis"), ax=ax, shrink=.75)
        ax.set_xlabel("x (m; Greal-75 offset for comparison)"); ax.set_ylabel("z (m)")
    fig.savefig(figdir / "Figure_T5_Greal75_vs_81_174h.png", dpi=300, facecolor="white")
    fig.savefig(figdir / "Figure_T5_Greal75_vs_81_174h.pdf", facecolor="white"); plt.close(fig)


def main():
    a = parse_args(); a.out.mkdir(parents=True, exist_ok=True)
    figdir = a.out.parent / "figures"; figdir.mkdir(exist_ok=True)
    mpl.rcParams.update({"font.size": 8, "axes.titlesize": 9, "axes.labelsize": 8,
                         "xtick.labelsize": 7, "ytick.labelsize": 7,
                         "legend.fontsize": 7, "pdf.fonttype": 42})
    expected = json.loads(a.expected_hashes.read_text(encoding="utf-8"))
    previous = json.loads(a.inventory_summary.read_text(encoding="utf-8"))
    all_rows, coverage_rows, stat_rows = [], [], []
    checks = {"constants": {"rho_NaCl_kg_m3": RHO_NACL, "molar_mass_kg_mol": M_NACL,
                            "solid_molar_density_mol_m3": RHO_MOLAR, "crust_porosity": CRUST_POROSITY,
                            "primary_vf_threshold": PRIMARY_THRESHOLD,
                            "absolute_tolerance_mol": ABS_TOL_MOL, "relative_tolerance": REL_TOL},
              "source_files_read_only": True, "cases": {}, "hashes": {}}
    reference_geometry = None
    for case in CASES:
        root = a.source / case; paths = read_pvd(root, case)
        profiles = read_csv_rows(root / "depth_profiles_compact.csv")
        mineral = read_csv_rows(root / "mineral_budget.csv")
        case_checks = {"times": {}, "face_mapping": {}}
        for hour, path in paths.items():
            actual_hash = sha256(path)
            expected_key = str(path)
            if expected.get(expected_key) != actual_hash:
                raise AssertionError((path, "SHA mismatch", expected.get(expected_key), actual_hash))
            checks["hashes"][expected_key] = actual_hash
            arr = vtk_arrays(path)
            geometry, other = build_top_geometry(arr)
            geometry_signature = [(r["cell_id"], r["face_area_m2"], r["cell_volume_m3"], r["top_face_vertices_xz"])
                                  for r in geometry]
            if reference_geometry is None: reference_geometry = geometry_signature
            elif geometry_signature != reference_geometry: raise AssertionError((case, hour, "mesh changed"))
            solid = arr["precipitateVolumeFraction^NaCl"]
            rows = []
            for g in geometry:
                vf = float(solid[g["cell_id"]]); moles = g["cell_volume_m3"] * vf * RHO_MOLAR
                mass = moles * M_NACL
                loading = mass / g["face_area_m2"]
                height = mass / (RHO_NACL * (1 - CRUST_POROSITY) * g["face_area_m2"])
                row = {k: v for k, v in g.items() if k != "_poly"}
                row.update(case=case, time_h=hour, solid_volume_fraction=vf,
                           solid_molar_density_mol_m3=RHO_MOLAR, solid_moles=moles,
                           solid_mass_kg=mass, solid_mass_kg_m2=loading,
                           solid_detected_primary=bool(vf > PRIMARY_THRESHOLD),
                           height_alpha025_mm=height * .25 * 1000,
                           height_alpha05_mm=height * .5 * 1000,
                           height_alpha1_mm=height * 1000)
                rows.append(row); all_rows.append(row)
            areas = np.array([r["face_area_m2"] for r in rows])
            moles = np.array([r["solid_moles"] for r in rows])
            masses = np.array([r["solid_mass_kg"] for r in rows])
            loadings = np.array([r["solid_mass_kg_m2"] for r in rows])
            vf = np.array([r["solid_volume_fraction"] for r in rows])
            heights = np.array([r["height_alpha1_mm"] for r in rows])
            profile_hits = nearest_time_rows(profiles, "evaporation_h", hour,
                                             lambda r: int(r["material"]) == 1 and float(r["depth_mm"]) < 1)
            profile_mol = sum(float(r["salt_solid_mol"]) for r in profile_hits)
            mineral_hits = nearest_time_rows(mineral, "evaporation_time_h", hour)
            mineral_mol = float(mineral_hits[-1]["fine_solid_mol"])
            surface_mol = float(moles.sum())
            def comparison(reference):
                absolute = surface_mol - reference
                relative = absolute / max(abs(reference), ABS_TOL_MOL)
                return {"reference_mol": reference, "absolute_difference_mol": absolute,
                        "relative_difference": relative,
                        "passed": abs(absolute) <= max(ABS_TOL_MOL, REL_TOL * abs(reference))}
            tcheck = {"surface_cell_mol": surface_mol,
                      "profile_top1": comparison(profile_mol), "mineral_fine": comparison(mineral_mol)}
            if hour == 174:
                prev = float(previous[case]["terminal_mol"]["W3_top1"])
                tcheck["previous_inventory_summary_top1"] = comparison(prev)
            case_checks["times"][str(hour)] = tcheck
            for threshold in VF_THRESHOLDS:
                bearing = vf > threshold
                coverage_rows.append(dict(case=case, time_h=hour, vf_threshold=threshold,
                                          bearing_cell_count=int(bearing.sum()),
                                          bearing_area_m2=float(areas[bearing].sum()),
                                          bearing_area_fraction=float(areas[bearing].sum() / areas.sum()),
                                          total_surface_area_m2=float(areas.sum()),
                                          total_solid_mol=surface_mol, total_solid_mass_g=float(masses.sum()*1000)))
            for alpha in ALPHAS:
                primary = vf > PRIMARY_THRESHOLD
                # Values below the declared detection threshold are numerical dust:
                # retain their raw mass in conservation totals but encode local
                # detectable-crust height as zero in distribution statistics.
                h = np.where(primary, heights * alpha, 0.0)
                detected_loadings = np.where(primary, loadings, 0.0)
                stat_rows.append(dict(case=case, time_h=hour, alpha=alpha,
                    total_surface_area_m2=float(areas.sum()), total_solid_mol=surface_mol,
                    total_solid_mass_g=float(masses.sum()*1000), solid_bearing_cell_count=int(primary.sum()),
                    solid_bearing_area_fraction=float(areas[primary].sum()/areas.sum()),
                    area_weighted_mean_height_mm=float(np.sum(h*areas)/areas.sum()),
                    area_weighted_median_height_mm=weighted_quantile(h,areas,.5),
                    area_weighted_p90_height_mm=weighted_quantile(h,areas,.9),
                    area_weighted_p95_height_mm=weighted_quantile(h,areas,.95),
                    max_height_mm=float(h.max()),
                    mass_from_height_g=float(np.sum(h/1000*RHO_NACL*(1-CRUST_POROSITY)*areas)*1000),
                    mass_fraction_top10pct_area=mass_fraction_within_area(detected_loadings,areas,.1),
                    mass_fraction_top25pct_area=mass_fraction_within_area(detected_loadings,areas,.25),
                    mass_fraction_top50pct_area=mass_fraction_within_area(detected_loadings,areas,.5)))
        total_area = sum(r["face_area_m2"] for r in geometry)
        expected_half = math.pi * .025**2 / 2
        case_checks["face_mapping"] = {"top_cell_count": len(geometry), "unique_top_face_count": len(geometry),
            "actual_discrete_W3_area_m2": total_area, "analytical_half_circle_area_m2": expected_half,
            "relative_discrete_area_difference": (total_area-expected_half)/expected_half,
            "every_top_cell_has_one_face": True}
        checks["cases"][case] = case_checks
    for case in CASES:
        for t in TIMES:
            for name, comp in checks["cases"][case]["times"][str(t)].items():
                if isinstance(comp, dict) and "passed" in comp and not comp["passed"]:
                    raise AssertionError((case, t, name, comp))

    fields = list(all_rows[0])
    with (a.out / "W3_surface_solid_maps.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fields); w.writeheader(); w.writerows(all_rows)
    with (a.out / "W3_surface_coverage_history.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, list(coverage_rows[0])); w.writeheader(); w.writerows(coverage_rows)
    with (a.out / "W3_local_thickness_statistics.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, list(stat_rows[0])); w.writeheader(); w.writerows(stat_rows)
    checks["all_mass_checks_passed"] = True
    (a.out / "W3_spatial_mass_balance.json").write_text(json.dumps(checks, indent=2), encoding="utf-8")

    primary = [r for r in all_rows if r["case"] == "Greal-81" and r["time_h"] in MAP_TIMES and r["solid_detected_primary"]]
    mass_values = [r["solid_mass_kg_m2"] for r in primary]
    height_values = [r["height_alpha1_mm"] for r in primary]
    cmap = mpl.colormaps["viridis"].with_extremes(bad="#d9d9d9")
    maps_figure(all_rows, "Greal-81", "solid_mass_kg_m2", "Numerical solid loading (kg m$^{-2}$)",
                figdir / "Figure_T1a_Greal81_solid_loading_maps", MAP_TIMES,
                LogNorm(vmin=min(mass_values), vmax=max(mass_values)), cmap)
    maps_figure(all_rows, "Greal-81", "height_alpha1_mm", "Hypothetical local height, alpha=1 (mm)",
                figdir / "Figure_T1b_Greal81_hypothetical_height_maps", MAP_TIMES,
                LogNorm(vmin=min(height_values), vmax=max(height_values)), cmap)
    diagnostics_figures(all_rows, coverage_rows, stat_rows, figdir)
    # Matplotlib writes an alpha channel even with a white facecolor. Deliver
    # explicit opaque RGB rasters so downstream backgrounds cannot alter them.
    for png in figdir.glob("Figure_T*.png"):
        with Image.open(png) as source:
            source.convert("RGB").save(png, dpi=(300, 300))
    manifest = {"audience":"scientific review; general 178/120 mm layouts, no journal compliance claimed",
                "sources":[str(a.source/c) for c in CASES],
                "transformations":["actual VTK convex-cell volume", "actual top polygon area", "VF threshold sensitivity",
                                   "solid moles=cell volume*VF*2165/0.0584428",
                                   "hypothetical height=mass/[2165*(1-0.43)*area]*alpha"],
                "missing_data":"below primary VF threshold shown gray, not zero-colored",
                "normalization":"common LogNorm across all Greal-81 time-map panels; no smoothing/interpolation",
                "figures":{p.name:sha256(p) for p in sorted(figdir.glob("Figure_T*"))}}
    (a.out / "W3_figure_manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print(json.dumps({"rows":len(all_rows),"coverage_rows":len(coverage_rows),"statistics_rows":len(stat_rows),
                      "Greal81_174":next(r for r in stat_rows if r["case"]=="Greal-81" and r["time_h"]==174 and r["alpha"]==1),
                      "Greal75_174":next(r for r in stat_rows if r["case"]=="Greal-75" and r["time_h"]==174 and r["alpha"]==1)},indent=2))


if __name__ == "__main__":
    main()
