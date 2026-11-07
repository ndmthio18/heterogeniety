#!/usr/bin/env python3
"""Release only the four 60 h baseline C/B cases after M0 acceptance."""
from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
gate = json.loads((ROOT / "m0_acceptance.json").read_text(encoding="utf-8"))
if gate.get("status") != "passed":
    raise RuntimeError("M0 acceptance has not passed")
SBATCH = "/rmprog/slurm/v22.05.7/bin/sbatch"
cases = ["S_Kc1_Kf1_D1_C1B1", "S_Kc1_Kf1_D1_C0B1",
         "B0_reference_C1B0", "B0_reference_C0B0",
         "M1_A_C1B1_24h", "M1_A_C0B1_24h"]
jobs = []
for case in cases:
    work = ROOT / "runs" / case
    if work.exists():
        raise RuntimeError(f"immutable run exists: {work}")
    work.mkdir(parents=True)
    source_input = ((ROOT / "inputs" / "validation" / f"{case}.input")
                    if case.startswith("M1_A_") else
                    (ROOT / "inputs" / "cases" / f"{case}.input"))
    os.symlink(source_input, work / source_input.name)
    text = source_input.read_text(encoding="utf-8")
    mesh = next(line.split("=", 1)[1].strip() for line in text.splitlines()
                if line.startswith("File ="))
    os.symlink(ROOT / "inputs" / "meshes" / mesh, work / mesh)
    os.symlink(ROOT / "inputs" / "water_flux_zero_storage.txt", work / "water_flux_zero_storage.txt")
    export = ",".join(("ALL", f"GREAL_ROOT={ROOT}", f"GREAL_WORKDIR={work}",
                       f"GREAL_INPUT={work / source_input.name}"))
    cmd = [SBATCH, "--parsable", "--partition=cnmix", "--nodes=1", "--ntasks=1",
           "--cpus-per-task=1", "--time=24:00:00", f"--job-name=g2d_{case}",
           f"--output={work / 'slurm-%j.out'}", f"--export={export}",
           str(ROOT / "slurm" / "run_case.slurm")]
    job_id = subprocess.check_output(cmd, text=True).strip().split(";")[0]
    jobs.append({"case": case, "job_id": job_id})
record = {"stage": "M1_reference_only", "submitted_epoch": time.time(), "jobs": jobs}
(ROOT / "m1_reference_jobs.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
print(json.dumps(record, indent=2))
