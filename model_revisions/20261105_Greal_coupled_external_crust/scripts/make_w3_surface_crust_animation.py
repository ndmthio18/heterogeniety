"""Render a truthful native-face animation of W3 external salt inventory."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import imageio_ffmpeg
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.animation import FFMpegWriter, FuncAnimation, PillowWriter
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "w3_surface_animation_174h"
GEOMETRY = OUT / "w3_top_geometry.json"
SURFACE = OUT / "w3_surface_crust_hourly.csv"
SUMMARY = OUT / "w3_surface_summary_hourly.csv"
SOLVER_BUDGET = OUT / "crust_budget_solver.csv"
EXTRACT_MANIFEST = OUT / "extraction_manifest.json"

DETECTION_VF = 1.0e-12
HEIGHT_MAX_MM = 0.42
FPS = 8


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_inputs() -> dict:
    manifest = json.loads(EXTRACT_MANIFEST.read_text(encoding="utf-8"))
    for name, expected in manifest["files"].items():
        actual = sha256(OUT / name)
        if actual != expected:
            raise RuntimeError(f"SHA256 mismatch for {name}: {actual} != {expected}")
    if manifest["surface_cells"] != 384 or manifest["frames"] != 177:
        raise RuntimeError("Unexpected extraction dimensions")
    return manifest


def load_data():
    geometry = json.loads(GEOMETRY.read_text(encoding="utf-8"))
    surface = pd.read_csv(SURFACE)
    summary = pd.read_csv(SUMMARY)
    solver = pd.read_csv(SOLVER_BUDGET)
    surface = surface[surface.evaporation_h >= 0].copy()
    summary = summary[summary.evaporation_h >= 0].copy()
    solver = solver[(solver.evaporation_time_h >= 0) & (solver.part == 1)].copy()
    if len(geometry) != 384 or surface.cell_id.nunique() != 384:
        raise RuntimeError("W3 native-face mapping is incomplete")
    return geometry, surface, summary, solver


def qa_reconstruction(summary: pd.DataFrame, solver: pd.DataFrame) -> dict:
    paired = summary.merge(
        solver[["evaporation_time_h", "external_mass_kg", "max_height_m"]],
        left_on="evaporation_h",
        right_on="evaporation_time_h",
        suffixes=("_reconstructed", "_solver"),
    )
    paired["mass_abs_error_kg"] = (
        paired.external_mass_kg_reconstructed - paired.external_mass_kg_solver
    ).abs()
    paired["height_abs_error_m"] = (
        paired.max_height_m_reconstructed - paired.max_height_m_solver
    ).abs()
    first = solver.loc[solver.external_mass_kg > 2165.0e-18].iloc[0]
    qa = {
        "paired_hourly_frames": int(len(paired)),
        "max_mass_abs_error_kg": float(paired.mass_abs_error_kg.max()),
        "max_height_abs_error_m": float(paired.height_abs_error_m.max()),
        "first_detectable_solver_evaporation_h": float(first.evaporation_time_h),
        "final_mass_mg": float(summary.iloc[-1].external_mass_kg * 1.0e6),
        "final_max_height_mm": float(summary.iloc[-1].max_height_m * 1.0e3),
        "final_detected_area_mm2": float(summary.iloc[-1].detected_area_m2 * 1.0e6),
    }
    if qa["max_mass_abs_error_kg"] > 1.0e-15 or qa["max_height_abs_error_m"] > 1.0e-15:
        raise RuntimeError(f"Surface reconstruction does not match solver budget: {qa}")
    paired.to_csv(OUT / "reconstruction_qa.csv", index=False)
    return qa


def prepare_frames(surface: pd.DataFrame):
    available = sorted(surface.evaporation_h.unique())
    selected = [time for time in available if abs(time % 2.0) < 1.0e-9]
    return selected


def polygons_for_frame(geometry, frame: pd.DataFrame):
    values = frame.set_index("cell_id")
    polygons = []
    heights = []
    detected = []
    for cell in geometry:
        row = values.loc[cell["cell_id"]]
        # Accepted-state negatives are only round-off (~1e-38); the raw values
        # remain in the source CSV while display height is bounded at zero.
        height_mm = max(0.0, float(row.equivalent_external_height_m) * 1000.0)
        polygons.append(
            [(x * 1000.0, z * 1000.0, height_mm) for x, z in cell["vertices_xz_m"]]
        )
        heights.append(height_mm)
        detected.append(float(row.solid_vf) > DETECTION_VF)
    return polygons, np.asarray(heights), np.asarray(detected)


def style_surface_axis(ax, show_display_note=True):
    ax.set_xlim(25, 50)
    ax.set_ylim(-25, 25)
    ax.set_zlim(0, HEIGHT_MAX_MM)
    ax.set_xlabel("Cylinder x (mm)", labelpad=7)
    ax.set_ylabel("Cylinder z (mm)", labelpad=7)
    ax.set_zlabel("Equivalent crust height (mm)", labelpad=7)
    ax.view_init(elev=32, azim=-56)
    ax.set_box_aspect((25, 50, 17))
    theta = np.linspace(-np.pi / 2, np.pi / 2, 200)
    ax.plot(25 + 25 * np.cos(theta), 25 * np.sin(theta), 0, color="#3b3b3b", lw=1.1)
    ax.plot([25, 25], [-25, 25], [0, 0], color="#3b3b3b", lw=1.1)
    ax.grid(False)
    if show_display_note:
        ax.text2D(
            0.01,
            0.01,
            "Native top faces; vertical display scale exaggerated",
            transform=ax.transAxes,
            fontsize=8,
            color="#4b4b4b",
        )


def add_surface(ax, polygons, heights, detected, norm, cmap):
    colors = cmap(norm(np.clip(heights, 0, HEIGHT_MAX_MM)))
    colors[~detected] = mpl.colors.to_rgba("#e8e8e8")
    side_polygons = []
    side_colors = []
    light_direction = np.asarray([-0.45, -0.89])
    light_direction /= np.linalg.norm(light_direction)
    for polygon, height, is_detected, color in zip(polygons, heights, detected, colors):
        if not is_detected or height <= 0.0:
            continue
        for index, upper_a in enumerate(polygon):
            upper_b = polygon[(index + 1) % len(polygon)]
            lower_a = (upper_a[0], upper_a[1], 0.0)
            lower_b = (upper_b[0], upper_b[1], 0.0)
            side_polygons.append([lower_a, lower_b, upper_b, upper_a])
            edge = np.asarray([upper_b[0] - upper_a[0], upper_b[1] - upper_a[1]])
            edge_norm = np.linalg.norm(edge)
            if edge_norm > 0:
                normal = np.asarray([edge[1], -edge[0]]) / edge_norm
                illumination = abs(float(np.dot(normal, light_direction)))
            else:
                illumination = 0.0
            shade = 0.40 + 0.42 * illumination
            side_color = np.asarray(color).copy()
            side_color[:3] *= shade
            side_colors.append(side_color)
    side_collection = Poly3DCollection(
        side_polygons,
        facecolors=side_colors,
        edgecolors="#515151",
        linewidths=0.18,
        antialiased=True,
    )
    ax.add_collection3d(side_collection)
    top_collection = Poly3DCollection(
        polygons,
        facecolors=colors,
        edgecolors="#727272",
        linewidths=0.18,
        antialiased=True,
    )
    ax.add_collection3d(top_collection)
    return [side_collection, top_collection]


def make_figure(geometry, surface, summary, qa):
    mpl.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.titlesize": 11,
            "axes.labelsize": 9,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "pdf.fonttype": 42,
        }
    )
    fig = plt.figure(figsize=(12.8, 7.2), layout="constrained")
    grid = fig.add_gridspec(2, 3, width_ratios=(1.0, 1.0, 0.86), height_ratios=(1, 1))
    ax3d = fig.add_subplot(grid[:, :2], projection="3d")
    ax_mass = fig.add_subplot(grid[0, 2])
    ax_height = fig.add_subplot(grid[1, 2], sharex=ax_mass)
    style_surface_axis(ax3d)

    cmap = mpl.colormaps["viridis"]
    norm = mpl.colors.Normalize(0, HEIGHT_MAX_MM)
    scalar = mpl.cm.ScalarMappable(norm=norm, cmap=cmap)
    colorbar = fig.colorbar(scalar, ax=ax3d, location="left", shrink=0.68, pad=0.03)
    colorbar.set_label("Equivalent external crust height (mm)")

    times = summary.evaporation_h.to_numpy()
    masses = summary.external_mass_kg.to_numpy() * 1.0e6
    maxima = summary.max_height_m.to_numpy() * 1.0e3
    ax_mass.plot(times, masses, color="#b4b4b4", lw=1.4, label="Complete trajectory")
    ax_height.plot(times, maxima, color="#b4b4b4", lw=1.4)
    onset = qa["first_detectable_solver_evaporation_h"]
    for axis in (ax_mass, ax_height):
        axis.axvline(onset, color="#d55e00", ls="--", lw=1.0)
        axis.grid(axis="y", color="#dddddd", lw=0.6)
        axis.spines[["top", "right"]].set_visible(False)
        axis.set_xlim(0, 174)
    ax_mass.set_ylabel("External NaCl mass (mg)")
    ax_mass.set_title("W3 surface inventory")
    ax_mass.text(onset + 3, masses.max() * 0.18, "first accepted solid\n71.92 h", color="#b34e00", fontsize=8)
    ax_height.set_ylabel("Maximum height (mm)")
    ax_height.set_xlabel("Evaporation time (h)")
    ax_height.set_title("Maximum equivalent height")

    current_mass, = ax_mass.plot([], [], color="#0072b2", lw=2.2)
    current_height, = ax_height.plot([], [], color="#0072b2", lw=2.2)
    mass_marker, = ax_mass.plot([], [], "o", color="#0072b2", ms=5)
    height_marker, = ax_height.plot([], [], "o", color="#0072b2", ms=5)
    readout = ax3d.text2D(
        0.02, 0.91, "", transform=ax3d.transAxes, ha="left", va="top", fontsize=9
    )

    frames = prepare_frames(surface)
    artists = {"surface": []}

    def update(frame_number):
        time_h = frames[frame_number]
        frame = surface[np.isclose(surface.evaporation_h, time_h)]
        polygons, heights, detected = polygons_for_frame(geometry, frame)
        for collection in artists["surface"]:
            collection.remove()
        artists["surface"] = add_surface(ax3d, polygons, heights, detected, norm, cmap)
        current = summary[np.isclose(summary.evaporation_h, time_h)].iloc[0]
        mask = times <= time_h
        current_mass.set_data(times[mask], masses[mask])
        current_height.set_data(times[mask], maxima[mask])
        current_mass_value = current.external_mass_kg * 1.0e6
        current_height_value = current.max_height_m * 1.0e3
        mass_marker.set_data([time_h], [current_mass_value])
        height_marker.set_data([time_h], [current_height_value])
        ax3d.set_title(f"Modeled W3 external salt inventory — {time_h:.0f} h", pad=12, weight="bold")
        readout.set_text(
            f"t = {time_h:.0f} h   |   external NaCl = {current_mass_value:.2f} mg   |   "
            f"max h = {current_height_value:.3f} mm"
        )
        return (*artists["surface"], current_mass, current_height, mass_marker, height_marker, readout)

    animation = FuncAnimation(fig, update, frames=len(frames), interval=1000 / FPS, blit=False)
    return fig, animation, update, frames


def save_contact_sheet(geometry, surface, qa):
    times = [0, 72, 96, 120, 144, 174]
    cmap = mpl.colormaps["viridis"]
    norm = mpl.colors.Normalize(0, HEIGHT_MAX_MM)
    fig = plt.figure(figsize=(12, 8), layout="constrained")
    axes = [fig.add_subplot(2, 3, index + 1, projection="3d") for index in range(6)]
    for ax, time_h in zip(axes, times):
        style_surface_axis(ax, show_display_note=False)
        frame = surface[np.isclose(surface.evaporation_h, time_h)]
        polygons, heights, detected = polygons_for_frame(geometry, frame)
        add_surface(ax, polygons, heights, detected, norm, cmap)
        ax.set_title(f"{time_h} h")
        ax.set_xlabel("")
        ax.set_ylabel("")
        ax.set_zlabel("")
    scalar = mpl.cm.ScalarMappable(norm=norm, cmap=cmap)
    colorbar = fig.colorbar(scalar, ax=axes, location="bottom", shrink=0.72, pad=0.04)
    colorbar.set_label("Equivalent external crust height (mm)")
    fig.suptitle("Modeled W3 external salt inventory: native-face snapshots", weight="bold")
    fig.savefig(OUT / "w3_surface_crust_contact_sheet.png", dpi=180, facecolor="white")
    plt.close(fig)


def main() -> None:
    extraction = verify_inputs()
    geometry, surface, summary, solver = load_data()
    qa = qa_reconstruction(summary, solver)
    (OUT / "animation_qa.json").write_text(json.dumps(qa, indent=2), encoding="utf-8")

    save_contact_sheet(geometry, surface, qa)
    fig, animation, update, frames = make_figure(geometry, surface, summary, qa)
    update(len(frames) - 1)
    fig.savefig(OUT / "w3_surface_crust_final_frame.png", dpi=180, facecolor="white")

    mpl.rcParams["animation.ffmpeg_path"] = imageio_ffmpeg.get_ffmpeg_exe()
    mp4 = OUT / "w3_surface_crust_0_174h.mp4"
    animation.save(
        mp4,
        writer=FFMpegWriter(fps=FPS, codec="libx264", bitrate=2400, extra_args=["-pix_fmt", "yuv420p"]),
        dpi=120,
    )
    gif = OUT / "w3_surface_crust_0_174h.gif"
    animation.save(gif, writer=PillowWriter(fps=FPS), dpi=85)
    plt.close(fig)

    readme = f"""# W3 surface salt-deposition animation

This animation shows the model-derived equivalent external NaCl-crust height on the 384 native W3 atmospheric top faces from 0 to 174 h. It does not show an experimentally observed crystal morphology.

- Source: completed Frodo 174 h coupled external-crust run.
- Variable: accepted equilibrium solid NaCl inventory, reinterpreted as external inventory.
- Height: `solid_vf * cell_volume / top_face_area / (1 - 0.43)`.
- Time sampling: every 2 h from the hourly VTU series.
- Spatial rendering: piecewise constant native top faces; no interpolation or smoothing.
- Geometry rendering: salt-bearing faces are extruded from the sand surface; side faces use directional darkening only to reveal shape, while the quantitative color scale applies to the top-face height.
- Display: fixed 0–{HEIGHT_MAX_MM:.2f} mm color scale; 3D vertical display scale is exaggerated for visibility.
- Detection threshold: solid volume fraction > {DETECTION_VF:g}.
- First accepted solver solid: {qa['first_detectable_solver_evaporation_h']:.5g} h.
- Final W3 external mass: {qa['final_mass_mg']:.6f} mg.
- Final maximum equivalent height: {qa['final_max_height_mm']:.6f} mm.
- Final crust-bearing area: {qa['final_detected_area_mm2']:.6f} mm2.

The raw extracted values, native face geometry, reconstruction QA, and hashes accompany the media files.
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")

    products = [
        mp4,
        gif,
        OUT / "w3_surface_crust_contact_sheet.png",
        OUT / "w3_surface_crust_final_frame.png",
        OUT / "animation_qa.json",
        OUT / "reconstruction_qa.csv",
        OUT / "README.md",
    ]
    manifest = {
        "source_extraction_manifest_sha256": sha256(EXTRACT_MANIFEST),
        "source_pvd_sha256": extraction["source_pvd_sha256"],
        "frames_rendered": len(frames),
        "frame_times_h": [float(time) for time in frames],
        "fps": FPS,
        "color_scale_mm": [0.0, HEIGHT_MAX_MM],
        "spatial_interpolation": "none",
        "geometry_rendering": "native polygon prisms; top color encodes height and side colors are directionally darkened for shape perception",
        "display_clipping": "negative round-off heights shown as zero; raw CSV preserved",
        "products": {path.name: sha256(path) for path in products},
    }
    (OUT / "animation_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"qa": qa, "products": manifest["products"]}, indent=2))


if __name__ == "__main__":
    main()
