"""Task 8: one-way, face-resolved dry-crust evaporation screening.

This script never edits accepted simulations.  It maps the accepted DuMuX
integration point on every W3 top face into the corresponding actual VTK top
polygon, verifies the accepted water-flux ledgers, and applies conditional
resistances only in post-processing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.colors import LogNorm, Normalize
import numpy as np
import pandas as pd
from PIL import Image
from scipy.stats import NearConstantInputWarning, pearsonr, rankdata, spearmanr

mpl.rcParams.update({"pdf.fonttype": 42, "ps.fonttype": 42})


CASES = ("Greal-81", "Greal-75")
TIMES = (72.0, 84.0, 96.0, 108.0, 120.0, 144.0, 174.0)
ALPHAS = (0.25, 0.5, 1.0)
RATIOS = (0.05, 0.08, 0.10, 0.23)
WITHIN_FACE_COVERAGES = (0.25, 0.50, 0.75, 1.0)
DELTAS = {"Greal-81": 0.008100162249880822, "Greal-75": 0.0075}
RHO_NACL = 2165.0
CRUST_POROSITY = 0.43
WATER_MOLAR_MASS = 0.01801518
PRIMARY_THRESHOLD = 1e-12
AREA_ABS_TOL = 1e-15
POLYGON_TOL = 2e-12
FLUX_ABS_TOL_G_H = 1e-12
FLUX_REL_TOL = 1e-10


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--maps", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--figures", type=Path, required=True)
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def polygon_contains(point, polygon, tol=POLYGON_TOL):
    q = np.roll(polygon, -1, axis=0)
    cross = ((q[:, 0] - polygon[:, 0]) * (point[1] - polygon[:, 1])
             - (q[:, 1] - polygon[:, 1]) * (point[0] - polygon[:, 0]))
    return bool(np.all(cross >= -tol) or np.all(cross <= tol))


def exact_time(frame, column, time):
    rows = frame[np.isclose(frame[column], time, atol=1e-8, rtol=0)]
    if len(rows) != 1:
        raise AssertionError((column, time, len(rows)))
    return rows.iloc[0]


def safe_corr(x, y, method):
    x, y = np.asarray(x, float), np.asarray(y, float)
    valid = np.isfinite(x) & np.isfinite(y)
    x, y = x[valid], y[valid]
    if len(x) < 3 or np.ptp(x) == 0 or np.ptp(y) == 0:
        return math.nan, math.nan
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", NearConstantInputWarning)
        result = spearmanr(x, y) if method == "spearman" else pearsonr(x, y)
    return float(result.statistic), float(result.pvalue)


def partial_spearman(x, y, controls):
    x, y, controls = np.asarray(x, float), np.asarray(y, float), np.asarray(controls, float)
    valid = np.isfinite(x) & np.isfinite(y) & np.all(np.isfinite(controls), axis=1)
    x, y, controls = x[valid], y[valid], controls[valid]
    if len(x) < 5 or np.ptp(x) == 0 or np.ptp(y) == 0:
        return math.nan
    xr, yr = rankdata(x), rankdata(y)
    design = np.column_stack([np.ones(len(x)), *(rankdata(controls[:, i])
                                                   for i in range(controls.shape[1]))])
    xres = xr - design @ np.linalg.lstsq(design, xr, rcond=None)[0]
    yres = yr - design @ np.linalg.lstsq(design, yr, rcond=None)[0]
    if np.ptp(xres) == 0 or np.ptp(yres) == 0:
        return math.nan
    return float(np.corrcoef(xres, yres)[0, 1])


def match_faces(salt, film):
    polygons = [np.asarray(json.loads(value), float)
                for value in salt.top_face_vertices_xz]
    matched = []
    used = set()
    for film_index, face in film.iterrows():
        point = np.array([face.x_m, face.z_m])
        candidates = []
        for local_index, (area, polygon) in enumerate(zip(salt.face_area_m2, polygons)):
            area_tol = max(AREA_ABS_TOL, abs(face.area_m2) * 1e-9)
            if abs(area - face.area_m2) <= area_tol and polygon_contains(point, polygon):
                candidates.append(local_index)
        if len(candidates) != 1:
            raise AssertionError(("face match", int(film_index), candidates))
        local_index = candidates[0]
        if local_index in used:
            raise AssertionError(("duplicate salt face", local_index))
        used.add(local_index)
        matched.append((film_index, salt.index[local_index]))
    if len(matched) != 384 or len(used) != 384:
        raise AssertionError(("mapping counts", len(matched), len(used)))
    return matched


def beta_dry(height_m, delta_m, ratio):
    return 1.0 / (1.0 + height_m / (delta_m * ratio))


def effective_partial_beta(height_full_face_m, delta_m, ratio, coverage):
    if coverage <= 0:
        return np.ones_like(height_full_face_m)
    covered_beta = beta_dry(height_full_face_m / coverage, delta_m, ratio)
    return (1.0 - coverage) + coverage * covered_beta


def save_opaque(fig, base):
    fig.savefig(base.with_suffix(".pdf"), facecolor="white")
    fig.savefig(base.with_suffix(".png"), dpi=300, facecolor="white")
    with Image.open(base.with_suffix(".png")) as image:
        image.convert("RGB").save(base.with_suffix(".png"), dpi=(300, 300))


def face_polygons(frame):
    return [np.asarray(json.loads(value), float) for value in frame.top_face_vertices_xz]


def plot_maps(mapped, figures):
    case = "Greal-81"
    alpha, ratio = 1.0, 0.08
    subset = mapped[(mapped.case == case) & (mapped.alpha == alpha)
                    & (mapped.Dcrust_over_Dair == ratio)].copy()
    fig, axes = plt.subplots(2, 4, figsize=(178 / 25.4, 86 / 25.4),
                             layout="constrained")
    norm = Normalize(0, 1)
    for ax, time in zip(axes.flat, TIMES):
        frame = subset[subset.time_h == time].sort_values("cell_id")
        collection = PolyCollection(face_polygons(frame), array=frame.beta_local_full.to_numpy(),
                                    cmap="viridis", norm=norm, edgecolors="none")
        ax.add_collection(collection)
        ax.set(xlim=(0.0245, 0.0505), ylim=(-0.0255, 0.0255), aspect="equal",
               title=f"{time:g} h", xticks=[], yticks=[])
    axes.flat[-1].axis("off")
    bar = fig.colorbar(mpl.cm.ScalarMappable(norm=norm, cmap="viridis"),
                       ax=axes, fraction=0.03, pad=0.02)
    bar.set_label(r"Local dry-screen factor $\beta_i$ (–)")
    fig.suptitle("Greal-81 local resistance; alpha=1, Dcrust/Dair=0.08\n"
                 "Yellow beta=1 regions include uncovered faces; actual top polygons")
    save_opaque(fig, figures / "Figure_T8_1_local_beta_maps")
    plt.close(fig)

    frame = subset[subset.time_h == 174].sort_values("cell_id")
    baseline = frame.water_flux_kg_m2_s.to_numpy() * 1e5
    corrected = frame.local_corrected_flux_kg_m2_s.to_numpy() * 1e5
    vmax = max(baseline.max(), corrected.max())
    fig, axes = plt.subplots(1, 3, figsize=(178 / 25.4, 58 / 25.4),
                             layout="constrained")
    for ax, values, title in zip(
            axes[:2], (baseline, corrected), ("Original G-real", "Local dry screening")):
        collection = PolyCollection(face_polygons(frame), array=values, cmap="magma",
                                    norm=Normalize(0, vmax), edgecolors="none")
        ax.add_collection(collection)
        ax.set(xlim=(0.0245, 0.0505), ylim=(-0.0255, 0.0255), aspect="equal",
               title=title, xticks=[], yticks=[])
    difference = baseline - corrected
    collection = PolyCollection(face_polygons(frame), array=difference, cmap="cividis",
                                norm=Normalize(0, difference.max()), edgecolors="none")
    axes[2].add_collection(collection)
    axes[2].set(xlim=(0.0245, 0.0505), ylim=(-0.0255, 0.0255), aspect="equal",
                title="Screened reduction", xticks=[], yticks=[])
    b1 = fig.colorbar(mpl.cm.ScalarMappable(norm=Normalize(0, vmax), cmap="magma"),
                      ax=axes[:2], fraction=0.04, pad=0.02)
    b1.set_label(r"Water flux ($10^{-5}$ kg m$^{-2}$ s$^{-1}$)")
    b2 = fig.colorbar(mpl.cm.ScalarMappable(norm=Normalize(0, difference.max()), cmap="cividis"),
                      ax=axes[2], fraction=0.08, pad=0.02)
    b2.set_label(r"Flux reduction ($10^{-5}$ kg m$^{-2}$ s$^{-1}$)")
    fig.suptitle("Greal-81 at 174 h; alpha=1, Dcrust/Dair=0.08; no state feedback")
    save_opaque(fig, figures / "Figure_T8_2_original_vs_corrected_flux")
    plt.close(fig)


def plot_totals(summary, figures):
    colors = dict(zip(RATIOS, ["#0072B2", "#009E73", "#E69F00", "#CC79A7"]))
    fig, axes = plt.subplots(2, 3, figsize=(178 / 25.4, 118 / 25.4),
                             sharex=True, layout="constrained")
    for row, case in enumerate(CASES):
        for col, alpha in enumerate(ALPHAS):
            ax = axes[row, col]
            base = summary[(summary.case == case) & (summary.alpha == alpha)
                           & (summary.within_face_coverage == 1.0)]
            baseline = base[base.Dcrust_over_Dair == RATIOS[0]]
            ax.plot(baseline.time_h, baseline.W3_baseline_g_h, color="black",
                    marker="o", label="A original")
            for ratio in RATIOS:
                frame = base[base.Dcrust_over_Dair == ratio]
                ax.plot(frame.time_h, frame.W3_uniform_g_h, color=colors[ratio],
                        linestyle="--", label=f"B uniform; {ratio:g}")
                ax.plot(frame.time_h, frame.W3_local_g_h, color=colors[ratio],
                        linestyle="-", label=f"C local; {ratio:g}")
            ax.set(title=f"{case}; alpha={alpha:g}", xlabel="Evaporation time (h)",
                   ylabel="W3 evaporation (g h$^{-1}$)", xlim=(70, 176))
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside lower center", ncol=3, fontsize=7)
    fig.suptitle("Snapshot one-way screening: same detectable salt mass in B and C\n"
                 "Dashed=uniform entire W3; solid=local bearing faces; F36 unchanged")
    save_opaque(fig, figures / "Figure_T8_3_uniform_vs_local_rates")
    plt.close(fig)


def plot_correlations(base_faces, correlation, figures):
    fig, axes = plt.subplots(1, 2, figsize=(190 / 25.4, 72 / 25.4),
                             layout="constrained")
    for ax, case in zip(axes, CASES):
        frame = base_faces[(base_faces.case == case) & (base_faces.time_h == 174)
                           & base_faces.solid_detected_primary].copy()
        points = ax.scatter(frame.water_flux_kg_m2_s * 1e5, frame.solid_mass_kg_m2,
                            c=frame.distance_to_outer_wall_mm, cmap="viridis_r",
                            s=np.clip(frame.face_area_m2 / frame.face_area_m2.median() * 15, 5, 40),
                            edgecolor="black", linewidth=0.2)
        row = correlation[(correlation.case == case) & (correlation.time_h == 174)
                          & (correlation.scope == "detected")
                          & (correlation.variable == "baseline_water_flux_kg_m2_s")
                          & (correlation.method == "spearman")].iloc[0]
        ax.set_xlabel(r"Original water flux ($10^{-5}$ kg m$^{-2}$ s$^{-1}$)", fontsize=8)
        ax.set_ylabel(r"Detected solid loading (kg m$^{-2}$)", fontsize=8)
        ax.set_title(f"{case}; detected faces; rho={row.coefficient:.3f}", fontsize=8, pad=3)
        ax.tick_params(labelsize=7)
        bar = fig.colorbar(points, ax=ax)
        bar.set_label("Wall distance (mm)", fontsize=8)
        bar.ax.tick_params(labelsize=7)
    fig.suptitle("Salt loading versus original local evaporation (marker area follows face area)\n"
                 "174 h descriptive association; geometric edge confounding remains", fontsize=9)
    save_opaque(fig, figures / "Figure_T8_4_salt_flux_correlation")
    plt.close(fig)


def plot_evolution(summary, coverage, figures):
    fig, axes = plt.subplots(2, 2, figsize=(178 / 25.4, 98 / 25.4),
                             layout="constrained", sharex="col")
    for case, color, marker in (("Greal-81", "#0072B2", "o"),
                                ("Greal-75", "#D55E00", "s")):
        c = coverage[coverage.case == case]
        axes[0, 0].plot(c.time_h, 100 * c.geometric_bearing_area_fraction,
                        color=color, marker=marker, label=case)
        axes[1, 0].plot(c.time_h, 100 * c.evaporation_weighted_bearing_fraction,
                        color=color, marker=marker, label=case)
        for ratio, style in ((0.05, "--"), (0.08, "-"), (0.10, "-."), (0.23, ":")):
            frame = summary[(summary.case == case) & (summary.alpha == 1)
                            & (summary.Dcrust_over_Dair == ratio)
                            & (summary.within_face_coverage == 1)]
            axes[0, 1].plot(frame.time_h, 100 * frame.uniform_reduction_fraction,
                            color=color, linestyle=style, alpha=0.8)
            axes[1, 1].plot(frame.time_h, 100 * frame.local_reduction_fraction,
                            color=color, linestyle=style, alpha=0.8,
                            label=f"{case}; {ratio:g}")
    axes[0, 0].set(ylabel="Bearing area (%)", title="Numerical support")
    axes[1, 0].set(ylabel="Bearing-flux share (%)",
                   xlabel="Evaporation time (h)", title="Evaporation-weighted support")
    axes[0, 1].set(ylabel="Uniform W3 reduction (%)", title="B: uniform")
    axes[1, 1].set(ylabel="Local W3 reduction (%)", xlabel="Evaporation time (h)",
                   title="C: local full-face")
    axes[0, 0].legend()
    axes[1, 1].legend(fontsize=6, ncol=2)
    fig.suptitle("72–174 h snapshot evolution; alpha=1; line style denotes Dcrust/Dair")
    save_opaque(fig, figures / "Figure_T8_5_snapshot_evolution")
    plt.close(fig)


def main():
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    args.figures.mkdir(parents=True, exist_ok=True)
    maps = pd.read_csv(args.maps)
    manifest = json.loads((args.inputs / "task8_input_manifest.json").read_text(encoding="utf-8"))
    input_hash_errors = []
    for name, metadata in manifest["outputs"].items():
        path = args.inputs / name
        if not path.exists() or sha256(path) != metadata["sha256"]:
            input_hash_errors.append(name)
    if input_hash_errors:
        raise AssertionError(("input hashes", input_hash_errors))

    base_rows = []
    mapping_qa = {}
    ledger_qa = {}
    for case in CASES:
        film_all = pd.read_csv(args.inputs / f"{case}_film_faces_selected.csv")
        budget = pd.read_csv(args.inputs / f"{case}_budget.csv")
        film_budget = pd.read_csv(args.inputs / f"{case}_film_budget.csv")
        temperatures = pd.read_csv(args.inputs / f"{case}_top_temperature_selected.csv")
        mapping_qa[case], ledger_qa[case] = {}, {}
        for time in TIMES:
            salt = maps[(maps.case == case) & np.isclose(maps.time_h, time)].copy().reset_index(drop=True)
            film_time = film_all[np.isclose(film_all.evaporation_time_h, time)].copy()
            film_w3 = film_time[film_time.x_m > 0.025].copy()
            film_f36 = film_time[film_time.x_m <= 0.025].copy()
            if len(salt) != 384 or len(film_w3) != 384 or len(film_f36) != 384:
                raise AssertionError((case, time, len(salt), len(film_w3), len(film_f36)))
            pairs = match_faces(salt, film_w3)
            salt_by_original = salt
            matched_rows = []
            for film_index, salt_original_index in pairs:
                s = salt_by_original.loc[salt_original_index]
                f = film_w3.loc[film_index]
                row = s.to_dict()
                for column, value in f.items():
                    row[f"film_{column}"] = value
                matched_rows.append(row)
            joined = pd.DataFrame(matched_rows)
            temp = temperatures[np.isclose(temperatures.time_h, time)][
                ["cell_id", "cell_center_x_m", "cell_center_z_m", "T_K"]].copy()
            temp = temp.rename(columns={"cell_center_x_m": "temperature_cell_center_x_m",
                                        "cell_center_z_m": "temperature_cell_center_z_m"})
            joined = joined.merge(temp, on="cell_id", how="left", validate="one_to_one")
            if joined.T_K.isna().any():
                raise AssertionError((case, time, "temperature mapping"))
            joined["baseline_face_evap_g_h"] = (joined.film_water_flux_kg_m2_s
                                                  * joined.face_area_m2 * 3.6e6)
            joined["distance_to_outer_wall_mm"] = (
                0.025 - np.hypot(joined.film_x_m - 0.025, joined.film_z_m)) * 1000
            joined["distance_to_interface_mm"] = (joined.film_x_m - 0.025) * 1000
            joined["solid_mass_for_resistance_kg"] = np.where(
                joined.solid_detected_primary.astype(bool), joined.solid_mass_kg, 0.0)
            joined["solid_loading_for_resistance_kg_m2"] = (
                joined.solid_mass_for_resistance_kg / joined.face_area_m2)
            joined["temperature_C"] = joined.T_K - 273.15
            base_rows.append(joined)

            area_error = float(abs(joined.face_area_m2.sum() - film_w3.area_m2.sum()))
            point_center_offset = np.hypot(joined.film_x_m - joined.face_center_x_m,
                                           joined.film_z_m - joined.face_center_z_m)
            mapping_qa[case][f"{time:g}"] = {
                "W3_faces": len(joined), "unique_cell_ids": int(joined.cell_id.nunique()),
                "unique_film_points": int(joined[["film_x_m", "film_z_m"]].drop_duplicates().shape[0]),
                "actual_W3_area_m2": float(joined.face_area_m2.sum()),
                "film_W3_area_m2": float(film_w3.area_m2.sum()),
                "area_abs_difference_m2": area_error,
                "integration_point_to_vertex_mean_center_max_m": float(point_center_offset.max()),
            }

            ledger = exact_time(budget, "evaporation_time_h", time)
            film_ledger = exact_time(film_budget, "evaporation_time_h", time)
            w3 = float((film_w3.water_flux_kg_m2_s * film_w3.area_m2).sum() * 3.6e6)
            f36 = float((film_f36.water_flux_kg_m2_s * film_f36.area_m2).sum() * 3.6e6)
            accepted_w3 = float(ledger.fine_top_water_out_mol_s * WATER_MOLAR_MASS * 3.6e6)
            accepted_f36 = float(ledger.coarse_top_water_out_mol_s * WATER_MOLAR_MASS * 3.6e6)
            accepted_total = float(film_ledger.top_water_mol_s * WATER_MOLAR_MASS * 3.6e6)
            differences = {"W3": w3 - accepted_w3, "F36": f36 - accepted_f36,
                           "total": w3 + f36 - accepted_total}
            for label, difference in differences.items():
                reference = {"W3": accepted_w3, "F36": accepted_f36,
                             "total": accepted_total}[label]
                if abs(difference) > max(FLUX_ABS_TOL_G_H, FLUX_REL_TOL * abs(reference)):
                    raise AssertionError((case, time, label, difference, reference))
            ledger_qa[case][f"{time:g}"] = {
                "reconstructed_W3_g_h": w3, "accepted_W3_g_h": accepted_w3,
                "reconstructed_F36_g_h": f36, "accepted_F36_g_h": accepted_f36,
                "reconstructed_total_g_h": w3 + f36, "accepted_total_g_h": accepted_total,
                "differences_g_h": differences,
            }

    base = pd.concat(base_rows, ignore_index=True)
    base = base.rename(columns={
        "film_water_flux_kg_m2_s": "water_flux_kg_m2_s",
        "film_C_mol_L": "near_surface_C_mol_L",
        "film_water_activity": "water_activity",
        "film_x_m": "integration_x_m", "film_z_m": "integration_z_m",
    })

    correction_rows, summary_rows, coverage_rows, correlation_rows = [], [], [], []
    partial_mass_rel_errors = []
    for (case, time), frame in base.groupby(["case", "time_h"], sort=False):
        frame = frame.sort_values("cell_id").copy()
        delta = DELTAS[case]
        area_total = frame.face_area_m2.sum()
        baseline_w3 = frame.baseline_face_evap_g_h.sum()
        ledger = ledger_qa[case][f"{time:g}"]
        baseline_f36 = ledger["reconstructed_F36_g_h"]
        detected = frame.solid_detected_primary.astype(bool)
        detected_mass = frame.solid_mass_for_resistance_kg.sum()
        bearing_flux = frame.loc[detected, "baseline_face_evap_g_h"].sum()
        coverage_rows.append({
            "case": case, "time_h": time, "threshold_solid_vf": PRIMARY_THRESHOLD,
            "bearing_faces": int(detected.sum()), "total_faces": len(frame),
            "bearing_area_m2": float(frame.loc[detected, "face_area_m2"].sum()),
            "total_W3_area_m2": float(area_total),
            "geometric_bearing_area_fraction": float(frame.loc[detected, "face_area_m2"].sum()/area_total),
            "baseline_W3_evap_g_h": float(baseline_w3),
            "baseline_evap_on_bearing_faces_g_h": float(bearing_flux),
            "evaporation_weighted_bearing_fraction": float(bearing_flux/baseline_w3),
            "mean_flux_bearing_kg_m2_s": float(frame.loc[detected, "water_flux_kg_m2_s"].mean()) if detected.any() else math.nan,
            "mean_flux_uncovered_kg_m2_s": float(frame.loc[~detected, "water_flux_kg_m2_s"].mean()) if (~detected).any() else math.nan,
            "detectable_solid_mass_kg": float(detected_mass),
            "raw_solid_mass_kg": float(frame.solid_mass_kg.sum()),
        })

        variables = {
            "baseline_water_flux_kg_m2_s": frame.water_flux_kg_m2_s,
            "near_surface_C_mol_L": frame.near_surface_C_mol_L,
            "water_activity": frame.water_activity,
            "temperature_C": frame.temperature_C,
            "distance_to_outer_wall_mm": frame.distance_to_outer_wall_mm,
            "distance_to_interface_mm": frame.distance_to_interface_mm,
        }
        for scope, mask in (("all", np.ones(len(frame), dtype=bool)),
                            ("detected", detected.to_numpy())):
            loading = frame.solid_loading_for_resistance_kg_m2.to_numpy()[mask]
            for variable, values in variables.items():
                for method in ("spearman", "pearson"):
                    coefficient, pvalue = safe_corr(loading, np.asarray(values)[mask], method)
                    correlation_rows.append({
                        "case": case, "time_h": time, "scope": scope,
                        "n_faces": int(mask.sum()), "variable": variable, "method": method,
                        "coefficient": coefficient, "p_value_descriptive_only": pvalue,
                    })
            partial = partial_spearman(
                loading, frame.water_flux_kg_m2_s.to_numpy()[mask],
                frame[["distance_to_outer_wall_mm", "distance_to_interface_mm"]].to_numpy()[mask])
            correlation_rows.append({
                "case": case, "time_h": time, "scope": scope, "n_faces": int(mask.sum()),
                "variable": "baseline_water_flux_kg_m2_s_control_wall_and_interface",
                "method": "partial_spearman_rank_residual", "coefficient": partial,
                "p_value_descriptive_only": math.nan,
            })

        for alpha in ALPHAS:
            face_height = (alpha * frame.solid_mass_for_resistance_kg /
                           (RHO_NACL * (1 - CRUST_POROSITY) * frame.face_area_m2))
            uniform_height = (alpha * detected_mass /
                              (RHO_NACL * (1 - CRUST_POROSITY) * area_total))
            for ratio in RATIOS:
                local_beta_full = np.where(detected, beta_dry(face_height, delta, ratio), 1.0)
                uniform_beta = float(beta_dry(uniform_height, delta, ratio))
                for index, source_row in frame.iterrows():
                    correction_rows.append({
                        "case": case, "time_h": time, "cell_id": int(source_row.cell_id),
                        "integration_x_m": source_row.integration_x_m,
                        "integration_z_m": source_row.integration_z_m,
                        "face_center_x_m": source_row.face_center_x_m,
                        "face_center_z_m": source_row.face_center_z_m,
                        "face_area_m2": source_row.face_area_m2,
                        "top_face_vertices_xz": source_row.top_face_vertices_xz,
                        "solid_detected_primary": bool(source_row.solid_detected_primary),
                        "solid_mass_kg": source_row.solid_mass_kg,
                        "solid_mass_for_resistance_kg": source_row.solid_mass_for_resistance_kg,
                        "solid_mass_kg_m2": source_row.solid_mass_kg_m2,
                        "alpha": alpha, "Dcrust_over_Dair": ratio,
                        "local_height_full_face_mm": face_height.loc[index] * 1000,
                        "beta_local_full": local_beta_full[frame.index.get_loc(index)],
                        "beta_uniform": uniform_beta,
                        "water_flux_kg_m2_s": source_row.water_flux_kg_m2_s,
                        "local_corrected_flux_kg_m2_s": source_row.water_flux_kg_m2_s * local_beta_full[frame.index.get_loc(index)],
                        "uniform_corrected_flux_kg_m2_s": source_row.water_flux_kg_m2_s * uniform_beta,
                        "baseline_face_evap_g_h": source_row.baseline_face_evap_g_h,
                        "local_corrected_face_evap_g_h": source_row.baseline_face_evap_g_h * local_beta_full[frame.index.get_loc(index)],
                        "uniform_corrected_face_evap_g_h": source_row.baseline_face_evap_g_h * uniform_beta,
                        "near_surface_C_mol_L": source_row.near_surface_C_mol_L,
                        "water_activity": source_row.water_activity,
                        "temperature_C": source_row.temperature_C,
                        "distance_to_outer_wall_mm": source_row.distance_to_outer_wall_mm,
                        "distance_to_interface_mm": source_row.distance_to_interface_mm,
                    })
                for coverage in WITHIN_FACE_COVERAGES:
                    local_beta = np.where(
                        detected,
                        effective_partial_beta(face_height.to_numpy(), delta, ratio, coverage),
                        1.0)
                    local_w3 = float(np.sum(frame.baseline_face_evap_g_h * local_beta))
                    uniform_w3 = float(baseline_w3 * uniform_beta)
                    covered_height = np.where(detected, face_height / coverage, 0.0)
                    reconstructed = float(np.sum(
                        RHO_NACL * (1 - CRUST_POROSITY) * frame.face_area_m2
                        * coverage * covered_height))
                    target_mass = float(alpha * detected_mass)
                    relative_error = abs(reconstructed - target_mass) / max(abs(target_mass), 1e-30)
                    partial_mass_rel_errors.append(relative_error)
                    summary_rows.append({
                        "case": case, "time_h": time, "alpha": alpha,
                        "Dcrust_over_Dair": ratio, "within_face_coverage": coverage,
                        "detectable_solid_mass_kg": detected_mass,
                        "resistance_solid_mass_kg": target_mass,
                        "uniform_height_mm": uniform_height * 1000,
                        "W3_baseline_g_h": baseline_w3, "F36_baseline_g_h": baseline_f36,
                        "total_baseline_g_h": baseline_w3 + baseline_f36,
                        "W3_uniform_g_h": uniform_w3,
                        "total_uniform_g_h": uniform_w3 + baseline_f36,
                        "W3_local_g_h": local_w3,
                        "total_local_g_h": local_w3 + baseline_f36,
                        "uniform_reduction_fraction": 1 - uniform_w3 / baseline_w3,
                        "local_reduction_fraction": 1 - local_w3 / baseline_w3,
                        "local_minus_uniform_W3_g_h": local_w3 - uniform_w3,
                        "F36_change_g_h": 0.0,
                        "partial_coverage_mass_relative_error": relative_error,
                    })

    corrections = pd.DataFrame(correction_rows)
    summary = pd.DataFrame(summary_rows)
    coverage = pd.DataFrame(coverage_rows)
    correlations = pd.DataFrame(correlation_rows)

    correction_export_columns = [
        "case", "time_h", "cell_id", "integration_x_m", "integration_z_m",
        "face_area_m2", "solid_detected_primary", "solid_mass_for_resistance_kg",
        "alpha", "Dcrust_over_Dair", "local_height_full_face_mm",
        "beta_local_full", "beta_uniform", "water_flux_kg_m2_s",
        "local_corrected_flux_kg_m2_s", "uniform_corrected_flux_kg_m2_s",
        "baseline_face_evap_g_h", "local_corrected_face_evap_g_h",
        "uniform_corrected_face_evap_g_h", "near_surface_C_mol_L",
        "water_activity", "temperature_C", "distance_to_outer_wall_mm",
        "distance_to_interface_mm",
    ]
    corrections[correction_export_columns].to_csv(
        args.out / "W3_face_evaporation_corrections.csv", index=False,
        float_format="%.12g")
    summary.to_csv(args.out / "W3_uniform_vs_local_resistance.csv", index=False,
                   float_format="%.12g")
    coverage.to_csv(args.out / "W3_evaporation_weighted_coverage.csv", index=False,
                    float_format="%.12g")
    correlations.to_csv(args.out / "W3_spatial_correlations.csv", index=False,
                        float_format="%.12g")

    highest_loading_checks = {}
    for case in CASES:
        initial = base[(base.case == case) & (base.time_h == 72)].set_index("cell_id")
        terminal = base[(base.case == case) & (base.time_h == 174)].set_index("cell_id")
        max_cell = int(terminal.solid_loading_for_resistance_kg_m2.idxmax())
        initial_flux = float(initial.loc[max_cell, "water_flux_kg_m2_s"])
        percentile = float(np.mean(initial.water_flux_kg_m2_s <= initial_flux) * 100)
        rho, pvalue = safe_corr(terminal.solid_loading_for_resistance_kg_m2,
                                initial.water_flux_kg_m2_s.reindex(terminal.index), "spearman")
        highest_loading_checks[case] = {
            "terminal_highest_loading_cell_id": max_cell,
            "terminal_highest_loading_kg_m2": float(terminal.loc[max_cell, "solid_loading_for_resistance_kg_m2"]),
            "same_face_72h_original_flux_kg_m2_s": initial_flux,
            "same_face_72h_flux_unweighted_percentile": percentile,
            "terminal_loading_vs_72h_flux_spearman": rho,
            "descriptive_p_value": pvalue,
            "is_same_face_initial_flux_maximum": bool(max_cell == int(initial.water_flux_kg_m2_s.idxmax())),
        }

    zero_alpha_beta = beta_dry(np.zeros(10), DELTAS["Greal-81"], 0.08)
    tiny_height_beta = beta_dry(np.full(10, 1e-18), DELTAS["Greal-81"], 0.08)
    beta_values = corrections.beta_local_full.to_numpy()
    ratio_monotonic_checks = []
    for _, frame in corrections.groupby(["case", "time_h", "cell_id", "alpha"]):
        ordered = frame.sort_values("Dcrust_over_Dair")
        ratio_monotonic_checks.append(bool(np.all(np.diff(ordered.beta_local_full) >= -1e-14)))
    thickness_monotonic_checks = []
    for _, frame in corrections.groupby(["case", "time_h", "cell_id", "Dcrust_over_Dair"]):
        ordered = frame.sort_values("alpha")
        thickness_monotonic_checks.append(bool(np.all(np.diff(ordered.beta_local_full) <= 1e-14)))
    max_ledger_difference = max(
        abs(value) for case in ledger_qa.values() for time in case.values()
        for value in time["differences_g_h"].values())
    qa = {
        "status": "passed",
        "scope": "read-only one-way dry/disconnected-crust screening; not coupled prediction",
        "source_input_manifest": manifest,
        "source_input_hashes_verified": not input_hash_errors,
        "mapping": mapping_qa,
        "baseline_flux_ledgers": ledger_qa,
        "gates": {
            "all_384_W3_faces_matched_once_each_snapshot": True,
            "no_unmatched_or_duplicate_faces": True,
            "maximum_area_abs_difference_m2": max(
                value["area_abs_difference_m2"] for case in mapping_qa.values() for value in case.values()),
            "maximum_baseline_flux_ledger_abs_difference_g_h": max_ledger_difference,
            "no_salt_exactly_original": bool(np.all(zero_alpha_beta == 1)),
            "vanishing_height_continuity_max_abs_beta_minus_one": float(np.max(abs(tiny_height_beta - 1))),
            "larger_diffusivity_ratio_never_reduces_beta": all(ratio_monotonic_checks),
            "increasing_thickness_never_increases_beta": all(thickness_monotonic_checks),
            "beta_min": float(beta_values.min()), "beta_max": float(beta_values.max()),
            "all_beta_within_0_1": bool(np.all((beta_values >= 0) & (beta_values <= 1))),
            "zero_external_fraction_has_zero_resistance": bool(np.all(zero_alpha_beta == 1)),
            "subthreshold_faces_beta_exactly_one": bool(np.all(
                corrections.loc[~corrections.solid_detected_primary, "beta_local_full"] == 1)),
            "F36_unchanged_max_abs_g_h": float(summary.F36_change_g_h.abs().max()),
            "partial_coverage_mass_max_relative_error": float(max(partial_mass_rel_errors)),
        },
        "highest_loading_vs_initial_flux": highest_loading_checks,
        "interpretive_limits": [
            "Numerical solid-bearing area is not measured physical crust coverage.",
            "Dry/disconnected resistance does not represent a wet hydraulically connected crust.",
            "Temperature, activity, concentration and pressure states are held at accepted baseline values.",
            "Correlations are descriptive and retain geometric and shared-state confounding.",
            "Snapshot rates cannot be integrated cumulatively without denser matched spatial fields or validation of a temporal interpolation rule.",
        ],
    }

    primary = corrections[(corrections.alpha == 1.0)
                          & (corrections.Dcrust_over_Dair == 0.08)].copy()
    plot_maps(primary, args.figures)
    plot_totals(summary, args.figures)
    plot_correlations(base, correlations, args.figures)
    plot_evolution(summary, coverage, args.figures)

    figure_hashes = {path.name: sha256(path) for path in sorted(args.figures.glob("Figure_T8_*"))}
    qa["figure_hashes"] = figure_hashes
    (args.out / "W3_local_resistance_QA.json").write_text(
        json.dumps(qa, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps({"status": qa["status"], "gates": qa["gates"],
                      "highest_loading": highest_loading_checks,
                      "rows": {"corrections": len(corrections), "summary": len(summary),
                               "coverage": len(coverage), "correlations": len(correlations)}},
                     indent=2))


if __name__ == "__main__":
    main()
