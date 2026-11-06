#!/usr/bin/env python3
"""Submit the immutable original/patched 24 h C1B1 recovery pair."""
import json
import os
import pathlib
import subprocess
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
SBATCH = "/rmprog/slurm/v22.05.7/bin/sbatch"
CASES = (("M0_regression_original", "solver_original"),
         ("M0_regression_patched", "solver_patched_r03"))


def stage_case(name):
    work = ROOT / "runs" / name
    if work.exists():
        raise RuntimeError(f"immutable case directory already exists: {work}")
    work.mkdir(parents=True)
    for item in ("filter_6layers.msh", "Greal04_port.txt",
                 "water_flux_zero_storage.txt"):
        os.symlink(ROOT / "inputs" / item, work / item)
    os.symlink(ROOT / "inputs" / "campaign" / "M0_regression_C1B1.input",
               work / "M0_regression_C1B1.input")
    return work


def main():
    jobs = []
    for name, target in CASES:
        work = stage_case(name)
        export = ",".join([
            "ALL", f"GREAL_ROOT={ROOT}", f"GREAL_WORKDIR={work}",
            f"GREAL_INPUT={work / 'M0_regression_C1B1.input'}",
            f"GREAL_TARGET={target}",
        ])
        command = [
            SBATCH, "--parsable", "--partition=cnall", "--nodes=1",
            "--ntasks=1", "--cpus-per-task=8", "--time=08:00:00",
            f"--job-name=g81_{name[14:]}",
            f"--output={work / 'slurm-%j.out'}", f"--export={export}",
            str(ROOT / "slurm" / "run_case.slurm"),
        ]
        job_id = subprocess.check_output(command, text=True).strip().split(";")[0]
        jobs.append({"case": name, "binary": target, "job_id": job_id,
                     "workdir": str(work)})
    record = {"submitted_epoch": time.time(), "stage": "M0_regression_24h",
              "jobs": jobs}
    (ROOT / "m0_regression_jobs.json").write_text(
        json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
