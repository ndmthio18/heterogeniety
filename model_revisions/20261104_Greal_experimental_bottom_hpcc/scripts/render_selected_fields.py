"""Render selected 3-D concentration and velocity fields with PyVista."""
from pathlib import Path
import argparse
import pyvista as pv


parser = argparse.ArgumentParser()
parser.add_argument("files", nargs="+")
parser.add_argument("--out", required=True)
args = parser.parse_args()
out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
for name in args.files:
    path = Path(name); grid = pv.read(path)
    concentration = grid["x^NaCl_liq"] * grid["rhoMolar_liq"] / 1000.0
    grid["C_liq_mol_L"] = concentration
    plotter = pv.Plotter(off_screen=True, shape=(1, 2), window_size=(1800, 800))
    plotter.subplot(0, 0); plotter.add_mesh(grid.slice(normal="z"), scalars="C_liq_mol_L", cmap="viridis")
    plotter.subplot(0, 1); plotter.add_mesh(grid.slice(normal="z"), scalars="velocity_liq_interior_LS (m/s)", cmap="coolwarm")
    plotter.link_views(); plotter.view_isometric(); plotter.screenshot(out / f"{path.stem}.png"); plotter.close()
