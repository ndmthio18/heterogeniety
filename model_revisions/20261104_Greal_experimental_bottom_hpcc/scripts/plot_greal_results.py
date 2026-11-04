"""Create reproducible scalar/profile G-real figures after both cases complete."""
from pathlib import Path
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def load_case(path):
    path = Path(path)
    return {name: pd.read_csv(path / name) for name in (
        "film_budget.csv", "budget.csv", "material_budgets.csv",
        "native_fluxes.csv", "depth_profiles_compact.csv")}


def experimental_rate(exp):
    dt = np.diff(exp.time_h.to_numpy())
    dm = np.diff(exp.solution_loss_since_1h_g.to_numpy())
    return (exp.time_h.to_numpy()[1:] + exp.time_h.to_numpy()[:-1]) / 2, dm / dt


def model_loss_at_measurements(film, times):
    time = film.evaporation_time_h.to_numpy()
    loss = film.cumulative_reservoir_loss_g.to_numpy()
    baseline = np.interp(1.0, time, loss)
    return np.interp(times, time, loss) - baseline


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--greal75", required=True)
    parser.add_argument("--greal81", required=True)
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    exp = pd.read_csv(args.experiment)
    cases = {"Greal-75": load_case(args.greal75), "Greal-81": load_case(args.greal81)}

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), constrained_layout=True)
    axes[0].plot(exp.time_h, exp.solution_loss_since_1h_g, "ko", label="experiment")
    tx, erate = experimental_rate(exp); axes[1].plot(tx, erate, "ko", label="experiment")
    metrics = []
    for label, data in cases.items():
        film = data["film_budget"]
        loss = model_loss_at_measurements(film, exp.time_h.to_numpy())
        axes[0].plot(exp.time_h, loss, label=label)
        rate = np.diff(loss) / np.diff(exp.time_h)
        axes[1].plot(tx, rate, label=label)
        residual = loss - exp.solution_loss_since_1h_g.to_numpy()
        metrics.append({"case": label, "cumulative_RMSE_g": np.sqrt(np.mean(residual**2)),
                        "interval_rate_RMSE_g_h": np.sqrt(np.average((rate-erate)**2, weights=np.diff(exp.time_h))),
                        "final_error_g": residual[-1], "final_error_percent": 100*residual[-1]/exp.solution_loss_since_1h_g.iloc[-1]})
    axes[0].set(xlabel="Evaporation time (h)", ylabel="Reservoir solution loss since 1 h (g)")
    axes[1].set(xlabel="Interval midpoint (h)", ylabel="Interval loss rate (g h$^{-1}$)")
    for ax in axes: ax.legend(frameon=False); ax.grid(alpha=.2)
    fig.savefig(out / "evaporation_comparison.png", dpi=300); plt.close(fig)
    pd.DataFrame(metrics).to_csv(out / "evaporation_metrics.csv", index=False)

    fig, axes = plt.subplots(2, 2, figsize=(10, 8), constrained_layout=True)
    bands = [(3, 12, "upper"), (12, 28, "middle"), (28, 37, "lower"), (3, 37, "whole")]
    for label, data in cases.items():
        p = data["depth_profiles_compact"]
        for material, row in enumerate(axes):
            q = p[p.material == material]
            for lo, hi, band in bands:
                z = q[(q.depth_mm >= lo) & (q.depth_mm < hi)]
                curve = z.groupby("evaporation_h").apply(lambda x: np.average(x.C_volume_mean_M, weights=x.liquid_volume_m3))
                row[0].plot(curve.index, curve.values, label=f"{label} {band}")
            inventory = q.groupby("evaporation_h")[["salt_dissolved_mol", "salt_solid_mol", "salt_total_mol"]].sum()
            row[1].plot(inventory.index, inventory.salt_dissolved_mol, label=f"{label} dissolved")
            row[1].plot(inventory.index, inventory.salt_total_mol, "--", label=f"{label} total")
    axes[0,0].set_title("F36 depth-resolved concentration"); axes[1,0].set_title("W3 depth-resolved concentration")
    axes[0,1].set_title("F36 salt inventory"); axes[1,1].set_title("W3 salt inventory")
    for row in axes:
        row[0].set(xlabel="Evaporation time (h)", ylabel="Liquid concentration (mol L$^{-1}$)")
        row[1].set(xlabel="Evaporation time (h)", ylabel="Salt inventory (mol)")
    for ax in axes.flat: ax.legend(fontsize=6, frameon=False); ax.grid(alpha=.2)
    fig.savefig(out / "concentration_and_inventory.png", dpi=300); plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), constrained_layout=True)
    for label, data in cases.items():
        flux = data["native_fluxes"]
        for kind, ax, title in [(0, axes[0], "Reservoir/filter"), (1, axes[1], "F36/W3")]:
            q = flux[flux.kind == kind].groupby("time_s")[["salt_adv_out", "salt_adv_in", "salt_diff_out", "salt_diff_in"]].sum()
            ax.plot((q.index-7200)/3600, q.salt_adv_out-q.salt_adv_in+q.salt_diff_out-q.salt_diff_in, label=label)
            ax.set_title(title)
    for ax in axes: ax.set(xlabel="Evaporation time (h)", ylabel="Net salt flux (mol s$^{-1}$)"); ax.legend(frameon=False); ax.grid(alpha=.2)
    fig.savefig(out / "interface_salt_fluxes.png", dpi=300); plt.close(fig)


if __name__ == "__main__":
    main()
