"""Headless ParaView validation for sparse PVD working datasets."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from paraview.simple import PVDReader, UpdatePipeline


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    records = []
    for pvd in sorted(args.root.rglob("*_sparse.pvd")):
        reader = PVDReader(registrationName=pvd.stem, FileName=str(pvd))
        times = list(reader.TimestepValues)
        frames = []
        for time in times:
            UpdatePipeline(time=time, proxy=reader)
            info = reader.GetDataInformation()
            frames.append({"time_s": float(time), "points": int(info.GetNumberOfPoints()), "cells": int(info.GetNumberOfCells())})
        passed = len(times) == 9 and all(frame["points"] > 0 and frame["cells"] > 0 for frame in frames)
        records.append({"pvd": str(pvd), "state": "passed" if passed else "failed", "frames": frames})
        # ParaView 5.11 on Frodo can segfault when Delete() is called while
        # Python still owns data-information wrappers.  Let process teardown
        # release proxies after the validation report has been written.
    result = {"state": "passed" if records and all(row["state"] == "passed" for row in records) else "failed", "datasets": records}
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"state": result["state"], "datasets": len(records), "frames": sum(len(row["frames"]) for row in records)}))
    if result["state"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
