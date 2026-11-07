#!/usr/bin/env python3
"""Submit identical short Configuration-B runs at 1/2/4 DuMuX threads."""
from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
SBATCH = "/rmprog/slurm/v22.05.7/bin/sbatch"
source_input = ROOT / "inputs" / "gates" / "M0_B_conservation_4h.input"
mesh = "primary_filter.msh"
jobs = []
for threads in (1, 2, 4):
    case = f"benchmark_B_4h_t{threads}"
    work = ROOT / "runs" / case
    if work.exists():
        raise RuntimeError(f"immutable run exists: {work}")
    work.mkdir(parents=True)
    os.symlink(source_input, work / f"{case}.input")
    os.symlink(ROOT / "inputs" / "meshes" / mesh, work / mesh)
    os.symlink(ROOT / "inputs" / "water_flux_zero_storage.txt", work / "water_flux_zero_storage.txt")
    export = ",".join(("ALL", f"GREAL_ROOT={ROOT}", f"GREAL_WORKDIR={work}",
                       f"GREAL_INPUT={work / (case + '.input')}"))
    cmd = [SBATCH, "--parsable", "--partition=cnmix", "--nodes=1", "--ntasks=1",
           f"--cpus-per-task={threads}", "--time=06:00:00", f"--job-name=g2d_bench_t{threads}",
           f"--output={work / 'slurm-%j.out'}", f"--export={export}",
           str(ROOT / "slurm" / "run_case.slurm")]
    job_id = subprocess.check_output(cmd, text=True).strip().split(";")[0]
    jobs.append({"case": case, "threads": threads, "job_id": job_id})
record = {"stage": "performance_benchmark", "submitted_epoch": time.time(), "jobs": jobs}
(ROOT / "benchmark_jobs.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
print(json.dumps(record, indent=2))
