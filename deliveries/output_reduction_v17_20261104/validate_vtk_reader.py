"""Validate PVD references and every VTU with ParaView's underlying VTK reader."""
from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import vtk


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pattern", default="*_sparse.pvd")
    args = parser.parse_args()
    datasets = []
    for pvd in sorted(args.root.rglob(args.pattern)):
        frames = []
        for entry in ET.parse(pvd).findall(".//DataSet"):
            path = pvd.parent / entry.attrib["file"]
            reader = vtk.vtkXMLUnstructuredGridReader()
            reader.SetFileName(str(path))
            reader.Update()
            output = reader.GetOutput()
            frames.append(
                {
                    "time_s": float(entry.attrib["timestep"]),
                    "file": path.name,
                    "points": output.GetNumberOfPoints(),
                    "cells": output.GetNumberOfCells(),
                    "cell_arrays": output.GetCellData().GetNumberOfArrays(),
                }
            )
        passed = bool(frames) and all(row["points"] > 0 and row["cells"] > 0 and row["cell_arrays"] > 0 for row in frames)
        datasets.append({"pvd": str(pvd), "state": "passed" if passed else "failed", "frames": frames})
    result = {
        "state": "passed" if datasets and all(row["state"] == "passed" for row in datasets) else "failed",
        "vtk_version": vtk.vtkVersion.GetVTKVersion(),
        "scope": "PVD XML references plus vtkXMLUnstructuredGridReader used by ParaView; Frodo pvpython 5.11.2 itself segfaults during proxy creation and is recorded separately.",
        "datasets": datasets,
    }
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"state": result["state"], "vtk_version": result["vtk_version"], "datasets": len(datasets), "frames": sum(len(row["frames"]) for row in datasets)}))
    if result["state"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
