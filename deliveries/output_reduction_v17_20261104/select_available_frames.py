"""Select exact or nearest available PVD frames; never infer 600 s numbering."""
from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pvd", type=Path)
    parser.add_argument("--evaporation-h", type=float, nargs="+", required=True)
    parser.add_argument("--pre-equilibration-s", type=float, default=7200.0)
    parser.add_argument("--tolerance-s", type=float, default=1e-7)
    args = parser.parse_args()
    entries = ET.parse(args.pvd).findall(".//DataSet")
    rows = []
    for hour in args.evaporation_h:
        target = args.pre_equilibration_s + hour * 3600
        item = min(entries, key=lambda e: abs(float(e.attrib["timestep"]) - target))
        actual = float(item.attrib["timestep"])
        rows.append(
            {
                "requested_evaporation_h": hour,
                "exact": abs(actual - target) <= args.tolerance_s,
                "actual_simulation_time_s": actual,
                "actual_evaporation_h": (actual - args.pre_equilibration_s) / 3600,
                "file": item.attrib["file"],
            }
        )
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
