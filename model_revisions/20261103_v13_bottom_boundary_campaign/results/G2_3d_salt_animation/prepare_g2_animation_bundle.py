#!/usr/bin/env python3
"""Select the accepted G2 3D fields at 2 h spacing and build a hashed tar bundle.

Run this script inside the remote G2 run directory. The source VTU files are
already gzip-compressed by the campaign monitor, so the delivery tar is left
uncompressed to avoid redundant compression.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import tarfile
import xml.etree.ElementTree as ET


PRE_EQUILIBRATION_S = 7200.0
FRAME_STEP_S = 7200.0
FINAL_TIME_S = 633600.0
CASE = "G2"


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    run_dir = pathlib.Path.cwd()
    pvd = run_dir / f"{CASE}.pvd"
    datasets = ET.parse(pvd).getroot().findall(".//DataSet")

    frames: list[dict[str, object]] = []
    for dataset in datasets:
        time_s = float(dataset.attrib["timestep"])
        frame_index = round((time_s - PRE_EQUILIBRATION_S) / FRAME_STEP_S)
        if time_s < PRE_EQUILIBRATION_S - 1e-9 or time_s > FINAL_TIME_S + 1e-9:
            continue
        if abs(time_s - (PRE_EQUILIBRATION_S + frame_index * FRAME_STEP_S)) > 1e-6:
            continue
        raw_name = dataset.attrib["file"]
        gz_path = run_dir / f"{raw_name}.gz"
        if not gz_path.is_file():
            raise FileNotFoundError(gz_path)
        frames.append(
            {
                "frame_index": int(frame_index),
                "simulation_time_s": time_s,
                "evaporation_time_h": (time_s - PRE_EQUILIBRATION_S) / 3600.0,
                "source_name": raw_name,
                "gzip_name": gz_path.name,
                "bytes": gz_path.stat().st_size,
                "sha256": sha256(gz_path),
            }
        )

    expected = list(range(88))
    actual = [int(frame["frame_index"]) for frame in frames]
    if actual != expected:
        raise RuntimeError(f"Expected frame indices {expected}, received {actual}")

    # run_dir is <track3d_r02>/raw/runs/G2.
    export_dir = run_dir.parents[2] / "animation_exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = export_dir / "G2_2h_frame_manifest.json"
    manifest = {
        "case": CASE,
        "selection": "accepted saved fields at 2 h evaporation-time spacing",
        "pre_equilibration_s": PRE_EQUILIBRATION_S,
        "frame_step_s": FRAME_STEP_S,
        "final_time_s": FINAL_TIME_S,
        "frame_count": len(frames),
        "frames": frames,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    bundle_path = export_dir / "G2_2h_animation_fields.tar"
    with tarfile.open(bundle_path, "w") as archive:
        archive.add(manifest_path, arcname=manifest_path.name)
        archive.add(pvd, arcname=pvd.name)
        archive.add(run_dir / "cell_geometry.csv", arcname="cell_geometry.csv")
        for frame in frames:
            gzip_name = str(frame["gzip_name"])
            archive.add(run_dir / gzip_name, arcname=f"frames/{gzip_name}")

    receipt = {
        "bundle": bundle_path.name,
        "bytes": bundle_path.stat().st_size,
        "sha256": sha256(bundle_path),
        "manifest_sha256": sha256(manifest_path),
        "frame_count": len(frames),
    }
    receipt_path = export_dir / "G2_2h_animation_bundle_receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
