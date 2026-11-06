#!/usr/bin/env python3
"""Submit only the four short M0 production-mesh switch gates."""
import json
import os
import pathlib
import subprocess
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
SBATCH = "/rmprog/slurm/v22.05.7/bin/sbatch"
CASES = ["M0_selftest_C1B1", "M0_selftest_C0B1",
         "M0_selftest_C1B0", "M0_selftest_C0B0"]


def stage_case(case):
    work = ROOT / "runs" / case
    if work.exists():
        raise RuntimeError(f"immutable case directory already exists: {work}")
    work.mkdir(parents=True)
    for name in ("filter_6layers.msh", "Greal04_port.txt",
                 "water_flux_zero_storage.txt"):
        os.symlink(ROOT / "inputs" / name, work / name)
    os.symlink(ROOT / "inputs" / "campaign" / f"{case}.input",
               work / f"{case}.input")
    return work


def main():
    jobs = []
    for case in CASES:
        work = stage_case(case)
        export = ",".join([
            "ALL", f"GREAL_ROOT={ROOT}", f"GREAL_WORKDIR={work}",
            f"GREAL_INPUT={work / (case + '.input')}",
            "GREAL_TARGET=solver_patched_r03",
        ])
        command = [
            SBATCH, "--parsable", "--partition=cnall", "--nodes=1",
            # cnall advertises RealMemory=1 MB despite normal physical RAM;
            # accepted Greal jobs therefore omit --mem and audit RSS instead.
            "--ntasks=1", "--cpus-per-task=8",
            "--time=02:00:00", f"--job-name=g81_{case[3:]}",
            f"--output={work / 'slurm-%j.out'}", f"--export={export}",
            str(ROOT / "slurm" / "run_case.slurm"),
        ]
        job_id = subprocess.check_output(command, universal_newlines=True).strip().split(";")[0]
        jobs.append({"case": case, "job_id": job_id, "workdir": str(work)})
    record = {"submitted_epoch": time.time(), "stage": "M0_selftests", "jobs": jobs}
    (ROOT / "m0_selftest_jobs.json").write_text(
        json.dumps(record, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
