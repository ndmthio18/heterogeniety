"""Prepare four restart-equivalent benchmark segments without running a solver."""
from pathlib import Path
import configparser
import json
import os
import shutil


ROOT = Path(os.environ["GREAL_ROOT"])
RUNS = ROOT / "gates" / "multicore"
REFERENCE = ROOT / "gates" / "short_sparse_faces" / "final_state.txt"

if not REFERENCE.exists():
    raise RuntimeError("formal short-run restart state is missing")
if RUNS.exists():
    raise RuntimeError(f"refusing to overwrite existing benchmark directory: {RUNS}")
RUNS.mkdir(parents=True)

for threads in (1, 2, 4, 8):
    out = RUNS / f"t{threads}"
    out.mkdir()
    cfg = configparser.ConfigParser()
    cfg.optionxform = str
    cfg.read(ROOT / "Greal-75.input")
    cfg["Problem"]["Name"] = f"GrealBenchT{threads}"
    cfg["TimeLoop"]["TEnd"] = "9600"
    cfg["TimeLoop"]["DtInitial"] = "300"
    cfg["Benchmark"]["VtkEvery"] = "6"
    cfg["Benchmark"]["FaceOutputInterval"] = "3600"
    cfg["Benchmark"]["StateIn"] = "initial_state.txt"
    cfg["Benchmark"]["AllowSegmentReset"] = "true"
    with (out / "case.input").open("w", newline="\n") as handle:
        cfg.write(handle)
    for asset in ("filter_6layers.msh", "Greal04_port.txt", "water_flux_zero_storage.txt"):
        shutil.copy2(ROOT / asset, out / asset)
    shutil.copy2(REFERENCE, out / "initial_state.txt")

(RUNS / "benchmark_status.json").write_text(
    json.dumps({"state": "prepared", "threads": [1, 2, 4, 8]}, indent=2) + "\n"
)
print(RUNS)
