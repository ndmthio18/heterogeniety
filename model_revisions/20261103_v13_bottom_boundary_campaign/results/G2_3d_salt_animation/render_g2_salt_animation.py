#!/usr/bin/env python3
"""Render the accepted G2 3D dissolved-salt evolution at 2 h spacing.

The quantitative layer is cell-based and uses the same fixed colour scale,
camera, clipping plane, and opacity bands in every frame. The optional solid
overlay marks cells with non-zero equilibrium solid inventory; it never scales
geometry by the inventory variable.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import pathlib
import shutil
import tempfile
from dataclasses import dataclass

import imageio.v2 as imageio
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import numpy as np
from PIL import Image
import pyvista as pv


mpl.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "font.size": 7,
    }
)

CASE = "G2"
CONC_NAME = "NaCl_liq_M"
SOLID_NAME = "precipitateVolumeFraction^NaCl"
F36_ANOMALY_NAME = "F36_ring_mean_anomaly_M"
CLIM = (1.0, 5.5)
F36_ANOMALY_CLIM = (-0.15, 0.15)
F36_SLICE_Y_M = 0.0125
KEY_TIMES_H = (0, 24, 60, 108, 174)
WINDOW_SIZE = (3840, 2160)
FPS = 8
SALT_CMAP = ListedColormap(mpl.colormaps["viridis"](np.linspace(0.30, 1.0, 256)))
ANOMALY_CMAP = ListedColormap(mpl.colormaps["RdBu_r"](np.linspace(0.0, 1.0, 256)))


@dataclass(frozen=True)
class FrameSpec:
    frame_index: int
    simulation_time_s: float
    evaporation_time_h: float
    gzip_name: str
    sha256: str


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(source_dir: pathlib.Path) -> list[FrameSpec]:
    payload = json.loads((source_dir / "G2_2h_frame_manifest.json").read_text(encoding="utf-8"))
    frames = [
        FrameSpec(
            frame_index=int(row["frame_index"]),
            simulation_time_s=float(row["simulation_time_s"]),
            evaporation_time_h=float(row["evaporation_time_h"]),
            gzip_name=str(row["gzip_name"]),
            sha256=str(row["sha256"]),
        )
        for row in payload["frames"]
    ]
    if len(frames) != 88 or [f.frame_index for f in frames] != list(range(88)):
        raise RuntimeError("The source manifest does not contain the expected 88 ordered frames")
    return frames


def validate_sources(source_dir: pathlib.Path, frames: list[FrameSpec]) -> None:
    for frame in frames:
        path = source_dir / "frames" / frame.gzip_name
        if not path.is_file():
            raise FileNotFoundError(path)
        actual = sha256(path)
        if actual != frame.sha256:
            raise RuntimeError(f"SHA256 mismatch for {path.name}: {actual} != {frame.sha256}")


def read_frame(source_dir: pathlib.Path, frame: FrameSpec, temp_dir: pathlib.Path) -> pv.UnstructuredGrid:
    gz_path = source_dir / "frames" / frame.gzip_name
    vtu_path = temp_dir / frame.gzip_name.removesuffix(".gz")
    with gzip.open(gz_path, "rb") as source, vtu_path.open("wb") as target:
        shutil.copyfileobj(source, target, length=1024 * 1024)
    mesh = pv.read(vtu_path)
    vtu_path.unlink()
    return mesh


def derive_fields(mesh: pv.UnstructuredGrid) -> tuple[np.ndarray, np.ndarray]:
    x_nacl = np.asarray(mesh.cell_data["x^NaCl_liq"], dtype=float)
    rho_molar = np.asarray(mesh.cell_data["rhoMolar_liq"], dtype=float)
    concentration = x_nacl * rho_molar / 1000.0
    solid = np.maximum(np.asarray(mesh.cell_data[SOLID_NAME], dtype=float), 0.0)
    mesh.cell_data[CONC_NAME] = concentration
    return concentration, solid


def opacity_for_level(level: float) -> float:
    return {1.0: 0.10, 1.5: 0.15, 2.5: 0.22, 3.5: 0.31, 4.5: 0.44}[level]


def add_geometry(plotter: pv.Plotter) -> None:
    # Transparent specimen outline; y is vertical in the model.
    specimen = pv.Cylinder(
        center=(0.025, 0.020, 0.0), direction=(0.0, 1.0, 0.0), radius=0.025,
        height=0.040, resolution=144, capping=False,
    )
    plotter.add_mesh(specimen, color="#CBD5E1", style="wireframe", opacity=0.22, line_width=1.0)

    # Explicit 4.5 mm porous filter plate.
    filter_plate = pv.Cylinder(
        center=(0.025, -0.00225, 0.0), direction=(0.0, 1.0, 0.0), radius=0.025,
        height=0.0045, resolution=144, capping=True,
    )
    plotter.add_mesh(filter_plate, color="#94A3B8", opacity=0.22, smooth_shading=True)

    # G2 is the 5 mm-diameter bottom supply port. The short cylinder is a
    # contextual glyph beneath the model boundary, not an added flow domain.
    inlet = pv.Cylinder(
        center=(0.025, -0.0060, 0.0), direction=(0.0, 1.0, 0.0), radius=0.0025,
        height=0.0030, resolution=96, capping=True,
    )
    plotter.add_mesh(inlet, color="#38BDF8", opacity=0.92, smooth_shading=True)
    arrow = pv.Arrow(start=(0.025, -0.0080, 0.0), direction=(0.0, 1.0, 0.0), scale=0.0060)
    plotter.add_mesh(arrow, color="#7DD3FC", opacity=0.95)

    # The material split is x=25 mm. A quiet translucent plane makes the
    # coarse/fine arrangement legible without hiding the scalar field.
    interface = pv.Plane(
        center=(0.025, 0.020, -0.0125), direction=(1.0, 0.0, 0.0),
        i_size=0.040, j_size=0.025, i_resolution=1, j_resolution=1,
    )
    plotter.add_mesh(interface, color="#E2E8F0", opacity=0.07)


def add_direct_labels(plotter: pv.Plotter, time_h: float, detail: bool = False) -> None:
    if detail:
        plotter.add_text(
            f"F36 lateral instability · {time_h:03.0f} h",
            position=(0.025, 0.940), viewport=True, font_size=34, color="white",
            font="arial", shadow=False,
        )
        plotter.add_text(
            "Horizontal slice y ≈ 12.5 mm · Δc from same-radius mean",
            position=(0.025, 0.895), viewport=True, font_size=20, color="#E2E8F0",
            font="arial", shadow=False,
        )
        plotter.add_text(
            "Blue: below ring mean · red: above ring mean · fixed ±0.15 mol L⁻¹",
            position=(0.025, 0.035), viewport=True, font_size=18, color="#CBD5E1",
            font="arial", shadow=False,
        )
        return

    plotter.add_text(
        f"G2 full domain · dissolved NaCl · {time_h:03.0f} h",
        position=(0.025, 0.940), viewport=True, font_size=34, color="white",
        font="arial", shadow=False,
    )
    plotter.add_text(
        "F36 coarse (x < 25 mm)     |     W3 fine (x ≥ 25 mm)",
        position=(0.025, 0.895), viewport=True, font_size=20, color="#E2E8F0",
        font="arial", shadow=False,
    )
    plotter.add_text(
        "Ø50 × 40 mm specimen · 4.5 mm filter · Ø5 mm supply port · front half clipped",
        position=(0.025, 0.035), viewport=True, font_size=18, color="#CBD5E1",
        font="arial", shadow=False,
    )
    plotter.add_text(
        "Cyan wireframe: cells containing equilibrium solid inventory (location only)",
        position=(0.025, 0.070), viewport=True, font_size=16, color="#5EEAD4",
        font="arial", shadow=False,
    )


def add_concentration_panel(
    plotter: pv.Plotter,
    mesh: pv.UnstructuredGrid,
    cell_mask: np.ndarray,
    clim: tuple[float, float],
    scalar_title: str,
    levels: tuple[float, ...],
) -> pv.UnstructuredGrid:
    """Add transparent 3D thresholds plus an exact, opaque z=0 mesh section."""
    region = mesh.extract_cells(np.flatnonzero(cell_mask))
    scalar_bar_args = {
        "title": scalar_title,
        "color": "white",
        "title_font_size": 24,
        "label_font_size": 20,
        "font_family": "arial",
        "vertical": True,
        "position_x": 0.925,
        "position_y": 0.20,
        "width": 0.030,
        "height": 0.58,
        "n_labels": 6,
        "fmt": "%.1f",
        "outline": False,
    }
    for level in levels:
        layer = region if level == levels[0] else region.threshold(
            [level, clim[1] + 1.0], scalars=CONC_NAME, preference="cell"
        )
        if layer.n_cells == 0:
            continue
        opacity = 0.10 + 0.34 * (level - levels[0]) / max(levels[-1] - levels[0], 1e-12)
        plotter.add_mesh(
            layer,
            scalars=CONC_NAME,
            preference="cell",
            cmap=SALT_CMAP,
            clim=clim,
            opacity=opacity,
            show_edges=False,
            smooth_shading=False,
            show_scalar_bar=False,
            render=False,
        )

    surface = region.extract_surface()
    surface_centers = surface.cell_centers().points
    section_ids = np.flatnonzero(
        (np.abs(surface_centers[:, 2]) < 1e-8) & (surface_centers[:, 1] >= -1e-10)
    )
    if section_ids.size:
        section = surface.extract_cells(section_ids)
        plotter.add_mesh(
            section,
            scalars=CONC_NAME,
            preference="cell",
            cmap=SALT_CMAP,
            clim=clim,
            opacity=0.96,
            show_edges=False,
            scalar_bar_args=scalar_bar_args,
            show_scalar_bar=True,
            render=False,
        )
    return region


def add_f36_horizontal_slice(
    plotter: pv.Plotter,
    mesh: pv.UnstructuredGrid,
    centers: np.ndarray,
) -> tuple[pv.UnstructuredGrid, float]:
    f36 = (centers[:, 0] < 0.025) & (centers[:, 1] >= -1e-10)
    levels_y = np.unique(centers[f36, 1])
    selected_y = float(levels_y[np.argmin(np.abs(levels_y - F36_SLICE_Y_M))])
    layer_mask = f36 & np.isclose(centers[:, 1], selected_y, atol=1e-10)
    layer_ids = np.flatnonzero(layer_mask)
    layer = mesh.extract_cells(layer_ids)

    # Remove the axisymmetric radial background without spatial resampling.
    # Every rendered cell retains its native value; the derived scalar is the
    # deviation from the mean of cells on the same native radial ring. This
    # exposes lateral symmetry breaking while keeping one fixed scale in time.
    layer_centers = centers[layer_ids]
    radius = np.hypot(layer_centers[:, 0] - 0.025, layer_centers[:, 2])
    radius_key = np.round(radius, decimals=10)
    concentration = np.asarray(layer.cell_data[CONC_NAME], dtype=float)
    anomaly = np.empty_like(concentration)
    for ring in np.unique(radius_key):
        ring_mask = radius_key == ring
        anomaly[ring_mask] = concentration[ring_mask] - np.mean(concentration[ring_mask])
    layer.cell_data[F36_ANOMALY_NAME] = anomaly
    plotter.add_mesh(
        layer,
        scalars=F36_ANOMALY_NAME,
        preference="cell",
        cmap=ANOMALY_CMAP,
        clim=F36_ANOMALY_CLIM,
        opacity=1.0,
        show_edges=False,
        scalar_bar_args={
            "title": "Δc (mol L⁻¹)",
            "color": "white",
            "title_font_size": 24,
            "label_font_size": 20,
            "font_family": "arial",
            "vertical": True,
            "position_x": 0.925,
            "position_y": 0.20,
            "width": 0.030,
            "height": 0.58,
            "n_labels": 6,
            "fmt": "%.2f",
            "outline": False,
        },
        show_scalar_bar=True,
        render=False,
    )
    return layer, selected_y


def render_frame(
    mesh: pv.UnstructuredGrid,
    time_h: float,
    output_path: pathlib.Path,
    show_solid: bool = True,
) -> dict[str, float | int]:
    concentration, solid = derive_fields(mesh)
    centers = mesh.cell_centers().points
    sand_mask = (centers[:, 1] >= -1e-10) & (centers[:, 2] <= 1e-10)

    panel_size = (WINDOW_SIZE[0] // 2, WINDOW_SIZE[1])
    plotter = pv.Plotter(off_screen=True, window_size=panel_size, border=False)
    plotter.enable_anti_aliasing("ssaa")

    plotter.set_background("#0F172A", top="#475569")
    add_geometry(plotter)
    slice_ring = pv.Cylinder(
        center=(0.025, F36_SLICE_Y_M, 0.0), direction=(0.0, 1.0, 0.0),
        radius=0.025, height=0.00015, resolution=144, capping=False,
    )
    plotter.add_mesh(
        slice_ring, color="#67E8F9", style="wireframe", opacity=0.70,
        line_width=1.5, render=False,
    )
    add_concentration_panel(
        plotter, mesh, sand_mask, CLIM, "Full domain (mol L⁻¹)",
        (1.0, 1.5, 2.5, 3.5, 4.5),
    )

    solid_cells = int(np.count_nonzero(solid > 1e-12))
    if show_solid and solid_cells:
        solid_mask = sand_mask & (solid > 1e-12)
        solid_region = mesh.extract_cells(np.flatnonzero(solid_mask)).extract_surface()
        plotter.add_mesh(
            solid_region, color="#5EEAD4", opacity=0.82, style="wireframe",
            show_edges=True, line_width=0.75, render=False,
        )

    add_direct_labels(plotter, time_h, detail=False)
    plotter.camera_position = [
        (0.095, 0.075, 0.105),
        (0.025, 0.0175, -0.003),
        (0.0, 1.0, 0.0),
    ]
    # Leave a dedicated right-hand legend gutter; the scalar bar no longer
    # overlays the specimen.
    plotter.camera.zoom(0.88)
    plotter.render()
    main_image = plotter.screenshot(transparent_background=False, return_img=True)
    plotter.close()

    plotter = pv.Plotter(off_screen=True, window_size=panel_size, border=False)
    plotter.enable_anti_aliasing("ssaa")
    plotter.set_background("#0F172A", top="#475569")
    f36_layer, selected_y = add_f36_horizontal_slice(plotter, mesh, centers)
    if show_solid and np.any(np.asarray(f36_layer.cell_data[SOLID_NAME]) > 1e-12):
        f36_solid = f36_layer.threshold(
            [1e-12, float("inf")], scalars=SOLID_NAME, preference="cell"
        ).extract_surface()
        plotter.add_mesh(
            f36_solid, color="#5EEAD4", opacity=0.82, style="wireframe",
            show_edges=True, line_width=0.75, render=False,
        )
    add_direct_labels(plotter, time_h, detail=True)
    plotter.camera_position = [
        (0.0125, 0.1000, 0.000),
        (0.0125, selected_y, 0.000),
        (0.0, 0.0, 1.0),
    ]
    plotter.enable_parallel_projection()
    # Leave the same independent legend gutter in the F36 detail panel.
    plotter.camera.zoom(1.08)
    plotter.render()
    detail_image = plotter.screenshot(transparent_background=False, return_img=True)
    plotter.close()
    Image.fromarray(np.concatenate((main_image, detail_image), axis=1)).save(output_path)

    sand_conc = concentration[centers[:, 1] >= -1e-10]
    return {
        "time_h": time_h,
        "concentration_min_M": float(np.min(sand_conc)),
        "concentration_median_M": float(np.median(sand_conc)),
        "concentration_p95_M": float(np.percentile(sand_conc, 95)),
        "concentration_max_M": float(np.max(sand_conc)),
        "solid_cell_count": solid_cells,
        "solid_inventory_max_equivalent_vf": float(np.max(solid)),
    }


def encode_movies(frame_paths: list[pathlib.Path], output_dir: pathlib.Path) -> None:
    mp4_path = output_dir / "G2_3D_DISSOLVED_NACL_0_174H.mp4"
    writer = imageio.get_writer(
        mp4_path,
        fps=FPS,
        codec="libx264",
        quality=8,
        pixelformat="yuv420p",
        macro_block_size=2,
        ffmpeg_log_level="warning",
    )
    try:
        # Brief holds at the endpoints improve readability without inventing
        # intermediate physical states.
        for _ in range(FPS):
            writer.append_data(imageio.imread(frame_paths[0]))
        for path in frame_paths:
            writer.append_data(imageio.imread(path))
        for _ in range(FPS * 2):
            writer.append_data(imageio.imread(frame_paths[-1]))
    finally:
        writer.close()

    gif_path = output_dir / "G2_3D_DISSOLVED_NACL_0_174H_preview.gif"
    gif_writer = imageio.get_writer(gif_path, mode="I", fps=6, loop=0)
    try:
        for path in frame_paths:
            with Image.open(path) as image:
                preview = image.resize((1600, 900), Image.Resampling.LANCZOS).convert("RGB")
                gif_writer.append_data(np.asarray(preview))
    finally:
        gif_writer.close()


def make_contact_sheet(frame_paths: dict[int, pathlib.Path], output_dir: pathlib.Path) -> None:
    fig, axes = plt.subplots(1, len(KEY_TIMES_H), figsize=(12.0, 2.35), constrained_layout=True)
    for ax, time_h in zip(axes, KEY_TIMES_H, strict=True):
        image = plt.imread(frame_paths[time_h])
        ax.imshow(image)
        ax.set_title(f"{time_h} h", fontsize=8, color="black", pad=3)
        ax.axis("off")
    fig.suptitle("G2: full-domain concentration and fixed-scale F36 instability detail", fontsize=9)
    fig.savefig(output_dir / "G2_3D_DISSOLVED_NACL_KEYFRAMES.png", dpi=300, bbox_inches="tight")
    fig.savefig(output_dir / "G2_3D_DISSOLVED_NACL_KEYFRAMES.pdf", bbox_inches="tight")
    fig.savefig(output_dir / "G2_3D_DISSOLVED_NACL_KEYFRAMES.svg", bbox_inches="tight")
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=pathlib.Path, default=pathlib.Path("source_frames"))
    parser.add_argument("--output-dir", type=pathlib.Path, default=pathlib.Path("rendered"))
    parser.add_argument("--keyframes-only", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--no-solid-overlay", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source_dir = args.source_dir.resolve()
    output_dir = args.output_dir.resolve()
    frame_dir = output_dir / "frames_png"
    key_dir = output_dir / "keyframes"
    frame_dir.mkdir(parents=True, exist_ok=True)
    key_dir.mkdir(parents=True, exist_ok=True)

    frames = load_manifest(source_dir)
    validate_sources(source_dir, frames)
    if args.keyframes_only:
        frames = [frame for frame in frames if int(round(frame.evaporation_time_h)) in KEY_TIMES_H]

    metrics: list[dict[str, float | int]] = []
    rendered_paths: list[pathlib.Path] = []
    keyframe_paths: dict[int, pathlib.Path] = {}
    with tempfile.TemporaryDirectory(prefix="g2_animation_") as temporary:
        temp_dir = pathlib.Path(temporary)
        for frame in frames:
            output_path = frame_dir / f"G2_salt_{frame.frame_index:03d}.png"
            time_integer = int(round(frame.evaporation_time_h))
            if args.force or not output_path.is_file():
                mesh = read_frame(source_dir, frame, temp_dir)
                metric = render_frame(
                    mesh,
                    frame.evaporation_time_h,
                    output_path,
                    show_solid=not args.no_solid_overlay,
                )
            else:
                metric = {"time_h": frame.evaporation_time_h}
            metric.update(
                {
                    "frame_index": frame.frame_index,
                    "simulation_time_s": frame.simulation_time_s,
                    "source_gzip": frame.gzip_name,
                    "source_sha256": frame.sha256,
                    "render_png": output_path.name,
                    "render_sha256": sha256(output_path),
                }
            )
            metrics.append(metric)
            rendered_paths.append(output_path)
            if time_integer in KEY_TIMES_H:
                key_path = key_dir / f"G2_dissolved_NaCl_{time_integer:03d}h.png"
                shutil.copy2(output_path, key_path)
                keyframe_paths[time_integer] = key_path
            print(f"rendered {frame.evaporation_time_h:6.1f} h -> {output_path.name}", flush=True)

    fieldnames = sorted({key for row in metrics for key in row})
    with (output_dir / "G2_3D_DISSOLVED_NACL_FRAME_METRICS.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(metrics)

    if not args.keyframes_only:
        encode_movies(rendered_paths, output_dir)
    if set(keyframe_paths) == set(KEY_TIMES_H):
        make_contact_sheet(keyframe_paths, output_dir)

    receipt = {
        "case": CASE,
        "frame_count": len(rendered_paths),
        "frame_times_h": [float(frame.evaporation_time_h) for frame in frames],
        "fixed_clim_M": list(CLIM),
        "f36_anomaly_definition": "native-cell concentration minus same-native-radius ring mean",
        "f36_anomaly_fixed_clim_M": list(F36_ANOMALY_CLIM),
        "window_size_px": list(WINDOW_SIZE),
        "fps": FPS,
        "solid_overlay": not args.no_solid_overlay,
        "quantitative_transform": "x^NaCl_liq * rhoMolar_liq / 1000 [mol/L]",
        "temporal_interpolation": False,
        "spatial_resampling": False,
        "front_half_clipped": True,
    }
    for artifact in output_dir.glob("G2_3D_DISSOLVED_NACL_*"):
        if artifact.is_file():
            receipt.setdefault("artifacts", []).append(
                {"name": artifact.name, "bytes": artifact.stat().st_size, "sha256": sha256(artifact)}
            )
    (output_dir / "ANIMATION_RECEIPT.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
