"""Build final scalar/profile acceptance metrics for completed G-real cases."""
from pathlib import Path
import argparse
import json
import numpy as np
import pandas as pd


def weighted_band(p, material, lo, hi, time_h=174.0):
    q = p[(p.material == material) & (p.depth_mm >= lo) & (p.depth_mm < hi)
          & np.isclose(p.evaporation_h, time_h)]
    return float(np.average(q.C_volume_mean_M, weights=q.liquid_volume_m3))


def case_metrics(path, exp, mri):
    path = Path(path)
    film = pd.read_csv(path / "film_budget.csv")
    budget = pd.read_csv(path / "budget.csv")
    thermal = pd.read_csv(path / "thermal_budget.csv")
    mineral = pd.read_csv(path / "mineral_budget.csv")
    material = pd.read_csv(path / "material_budgets.csv")
    profiles = pd.read_csv(path / "depth_profiles_compact.csv")
    flux = pd.read_csv(path / "native_fluxes.csv")

    model_loss = np.interp(exp.time_h, film.evaporation_time_h,
                           film.cumulative_reservoir_loss_g)
    model_loss -= np.interp(1.0, film.evaporation_time_h,
                            film.cumulative_reservoir_loss_g)
    observed = exp.solution_loss_since_1h_g.to_numpy()
    model_rate = np.diff(model_loss) / np.diff(exp.time_h)
    observed_rate = np.diff(observed) / np.diff(exp.time_h)
    residual = model_loss - observed

    positive = mineral[mineral.salt_solid_mol > 1e-12]
    first_solid = None if positive.empty else float(positive.iloc[0].evaporation_time_h)

    profile_rows = []
    material_map = {"F36": 0, "W3": 1}
    for side, mat in material_map.items():
        obs = mri[mri.side == side][["time_h", "depth_mm", "MRI_recalibration_M"]]
        pred = (profiles[profiles.material == mat]
                [["evaporation_h", "depth_mm", "C_volume_mean_M"]]
                .drop_duplicates(["evaporation_h", "depth_mm"], keep="last"))
        joined = obs.merge(pred, left_on=["time_h", "depth_mm"],
                           right_on=["evaporation_h", "depth_mm"], how="inner")
        for window, q in (("all", joined), ("core_3_37", joined[(joined.depth_mm >= 3) & (joined.depth_mm < 37)]),
                          ("terminal_core_3_37", joined[(joined.time_h == 174) & (joined.depth_mm >= 3) & (joined.depth_mm < 37)])):
            profile_rows.append({"side": side, "window": window, "n": len(q),
                                 "rmse_M": float(np.sqrt(np.mean((q.C_volume_mean_M-q.MRI_recalibration_M)**2)))})

    material_terminal = {}
    for mat, name in ((0, "F36"), (1, "W3"), (2, "filter")):
        q = material[material.material == mat]
        material_terminal[name] = {
            "initial_salt_mol": float(q.iloc[0].salt_mol),
            "terminal_salt_mol": float(q.iloc[-1].salt_mol),
            "salt_increment_mol": float(q.iloc[-1].salt_mol-q.iloc[0].salt_mol),
        }

    flux_integrals = {}
    labels = {0: "reservoir_filter", 1: "F36_to_W3", 3: "sand_to_filter", 5: "filter_lateral"}
    for kind, label in labels.items():
        q = flux[flux.kind == kind].copy()
        if q.empty:
            continue
        q["net_salt_mol_s"] = (q.salt_adv_out-q.salt_adv_in+q.salt_diff_out-q.salt_diff_in)
        for mat in sorted(q.material.unique()):
            z = q[q.material == mat]
            flux_integrals[f"{label}_material{int(mat)}"] = {
                "net_salt_mol": float(np.sum(z.net_salt_mol_s*z.dt_s)),
                "gross_out_salt_mol": float(np.sum((z.salt_adv_out+z.salt_diff_out)*z.dt_s)),
                "gross_in_salt_mol": float(np.sum((z.salt_adv_in+z.salt_diff_in)*z.dt_s)),
            }

    b0, bf = budget.iloc[0], budget.iloc[-1]
    t0 = thermal.iloc[0]
    return {
        "endpoint_h": float(bf.evaporation_time_h),
        "evaporation": {
            "loss_1_174_g": float(model_loss[-1]),
            "final_error_g": float(residual[-1]),
            "final_error_percent": float(100*residual[-1]/observed[-1]),
            "cumulative_rmse_g": float(np.sqrt(np.mean(residual**2))),
            "duration_weighted_rate_rmse_g_h": float(np.sqrt(np.average((model_rate-observed_rate)**2, weights=np.diff(exp.time_h)))),
        },
        "first_solid_h": first_solid,
        "terminal_solid_mol": float(bf.salt_solid_mol),
        "terminal_solid_g_NaCl": float(bf.salt_solid_mol*58.44),
        "terminal_temperature_K": [float(thermal.iloc[-1].T_min_K), float(thermal.iloc[-1].T_max_K)],
        "max_relative_closure": {
            "water": float(np.max(np.abs(budget.water_residual_mol))/max(abs(b0.water_mol), 1e-12)),
            "salt": float(np.max(np.abs(budget.salt_residual_mol))/max(abs(b0.salt_total_mol), 1e-12)),
            "F36": float(np.max(np.abs(budget.coarse_residual_mol))/max(abs(b0.coarse_salt_mol), 1e-12)),
            "W3": float(np.max(np.abs(budget.fine_residual_mol))/max(abs(b0.fine_salt_mol), 1e-12)),
            "energy": float(np.max(np.abs(thermal.energy_residual_J))/max(abs(t0.energy_J), 1.0)),
        },
        "terminal_concentration_M": {
            "F36_upper_3_12": weighted_band(profiles, 0, 3, 12),
            "F36_middle_12_28": weighted_band(profiles, 0, 12, 28),
            "F36_lower_28_37": weighted_band(profiles, 0, 28, 37),
            "F36_core_3_37": weighted_band(profiles, 0, 3, 37),
            "W3_core_3_37": weighted_band(profiles, 1, 3, 37),
        },
        "MRI_profile_rmse": profile_rows,
        "material_salt": material_terminal,
        "flux_integrals": flux_integrals,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--greal75", required=True); p.add_argument("--greal81", required=True)
    p.add_argument("--experiment", required=True); p.add_argument("--mri", required=True)
    p.add_argument("--out", required=True)
    a = p.parse_args()
    exp = pd.read_csv(a.experiment)
    exp = exp[(exp.time_h >= 1) & (exp.time_h <= 174)].copy()
    mri = pd.read_csv(a.mri)
    result = {"Greal-75": case_metrics(a.greal75, exp, mri),
              "Greal-81": case_metrics(a.greal81, exp, mri)}
    Path(a.out).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
