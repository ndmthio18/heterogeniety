"""Create a ParaView-ready sparse working set without modifying source data."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path


DEFAULT_HOURS = (0, 24, 60, 84, 96, 108, 120, 144, 174)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--name", required=True)
    parser.add_argument("--pre-equilibration-s", type=float, default=7200.0)
    parser.add_argument("--hours", type=float, nargs="*", default=DEFAULT_HOURS)
    args = parser.parse_args()

    if args.destination.exists():
        raise SystemExit(f"Refusing to overwrite {args.destination}")
    args.destination.mkdir(parents=True)
    source_pvd = args.source / f"{args.name}.pvd"
    root = ET.parse(source_pvd).getroot()
    entries = root.findall(".//DataSet")
    chosen = []
    for hour in args.hours:
        target = args.pre_equilibration_s + hour * 3600.0
        entry = min(entries, key=lambda item: abs(float(item.attrib["timestep"]) - target))
        actual = float(entry.attrib["timestep"])
        if abs(actual - target) > 1e-7:
            raise RuntimeError(f"No exact frame for {hour:g} h; nearest simulation time is {actual:g} s")
        relative = Path(entry.attrib["file"])
        raw = args.source / relative
        compressed = Path(str(raw) + ".gz")
        output = args.destination / relative.name
        if raw.exists():
            shutil.copyfile(raw, output)
            source_used = raw
        elif compressed.exists():
            with gzip.open(compressed, "rb") as src, output.open("wb") as dst:
                shutil.copyfileobj(src, dst, length=8 * 1024 * 1024)
            source_used = compressed
        else:
            raise FileNotFoundError(f"Missing {raw} and {compressed}")
        chosen.append(
            {
                "evaporation_h": hour,
                "simulation_time_s": actual,
                "source": str(source_used),
                "source_sha256": sha256(source_used),
                "file": output.name,
                "working_sha256": sha256(output),
                "bytes": output.stat().st_size,
            }
        )

    vtk_file = ET.Element("VTKFile", type="Collection", version="0.1", byte_order="LittleEndian")
    collection = ET.SubElement(vtk_file, "Collection")
    for item in chosen:
        ET.SubElement(
            collection,
            "DataSet",
            timestep=f"{item['simulation_time_s']:.17g}",
            group="",
            part="0",
            file=item["file"],
        )
    pvd = args.destination / f"{args.name}_sparse.pvd"
    ET.ElementTree(vtk_file).write(pvd, encoding="utf-8", xml_declaration=True)
    parsed = ET.parse(pvd)
    references = [args.destination / element.attrib["file"] for element in parsed.findall(".//DataSet")]
    if len(references) != len(args.hours) or not all(path.is_file() for path in references):
        raise RuntimeError("PVD validation failed")
    manifest = {
        "state": "passed",
        "source_pvd": str(source_pvd),
        "source_pvd_sha256": sha256(source_pvd),
        "sparse_pvd": pvd.name,
        "sparse_pvd_sha256": sha256(pvd),
        "frames": chosen,
        "working_bytes": sum(path.stat().st_size for path in references) + pvd.stat().st_size,
        "note": "A working copy only. The verified full-resolution archive remains authoritative.",
    }
    (args.destination / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
