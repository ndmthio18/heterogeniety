#!/usr/bin/env python3
"""Submit immutable M0 causal and short conservation gates after a verified build."""
from __future__ import annotations
import json
import os
import pathlib
import subprocess
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
SBATCH = "/rmprog/slurm/v22.05.7/bin/sbatch"
GATES = [
    *(f"M0_{config}_C{connection}B{buoyancy}"
      for config in ("A", "B") for connection in (1, 0) for buoyancy in (1, 0)),
    "M0_A_conservation_4h", "M0_B_conservation_4h",
]


def stage(case: str) -> pathlib.Path:
    work = ROOT / "runs" / case
    if work.exists():
        raise RuntimeError(f"immutable run already exists: {work}")
    work.mkdir(parents=True)
    input_path = ROOT / "inputs" / "gates" / f"{case}.input"
    text = input_path.read_text(encoding="utf-8")
    mesh = next(line.split("=", 1)[1].strip() for line in text.splitlines()
                if line.startswith("File ="))
    os.symlink(input_path, work / input_path.name)
    os.symlink(ROOT / "inputs" / "meshes" / mesh, work / mesh)
    os.symlink(ROOT / "inputs" / "water_flux_zero_storage.txt",
               work / "water_flux_zero_storage.txt")
    return work


jobs = []
selftest_ids: list[str] = []
for case in GATES:
    work = stage(case)
    selftest = "_C" in case
    command = [
        SBATCH, "--parsable", "--partition=cnmix", "--nodes=1", "--ntasks=1",
        "--cpus-per-task=1", "--time=" + ("00:30:00" if selftest else "06:00:00"),
        f"--job-name=g2d_{case[3:]}", f"--output={work / 'slurm-%j.out'}",
        "--export=" + ",".join(("ALL", f"GREAL_ROOT={ROOT}",
                                 f"GREAL_WORKDIR={work}",
                                 f"GREAL_INPUT={work / (case + '.input')}")),
    ]
    if not selftest:
        command.append("--dependency=afterok:" + ":".join(selftest_ids))
    command.append(str(ROOT / "slurm" / "run_case.slurm"))
    job_id = subprocess.check_output(command, text=True).strip().split(";")[0]
    if selftest:
        selftest_ids.append(job_id)
    jobs.append({"case": case, "job_id": job_id, "workdir": str(work)})
record = {"stage": "M0_gates", "submitted_epoch": time.time(), "jobs": jobs}
(ROOT / "m0_gate_jobs.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
print(json.dumps(record, indent=2))
