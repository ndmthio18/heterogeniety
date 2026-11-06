#!/usr/bin/env python3
"""Submit the four 60 h M1 cases only after an explicit passed M0 record."""
import json
import os
import pathlib
import subprocess
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
SBATCH = "/rmprog/slurm/v22.05.7/bin/sbatch"
CASES = ["M1_C1B1_K100_D100", "M1_C0B1_K100_D100",
         "M1_C1B0_K100_D100", "M1_C0B0_K100_D100"]


def main():
    gate_path = ROOT / "m0_acceptance.json"
    gate = json.loads(gate_path.read_text(encoding="utf-8"))
    if gate.get("status") != "passed":
        raise RuntimeError("M0 acceptance is absent or not passed")
    jobs = []
    for case in CASES:
        work = ROOT / "runs" / case
        if work.exists():
            raise RuntimeError(f"immutable case directory already exists: {work}")
        work.mkdir(parents=True)
        for item in ("filter_6layers.msh", "Greal04_port.txt",
                     "water_flux_zero_storage.txt"):
            os.symlink(ROOT / "inputs" / item, work / item)
        input_path = ROOT / "inputs" / "campaign" / f"{case}.input"
        os.symlink(input_path, work / input_path.name)
        export = ",".join([
            "ALL", f"GREAL_ROOT={ROOT}", f"GREAL_WORKDIR={work}",
            f"GREAL_INPUT={work / input_path.name}",
            "GREAL_TARGET=solver_patched_r03",
        ])
        command = [
            SBATCH, "--parsable", "--partition=cnall", "--nodes=1",
            "--ntasks=1", "--cpus-per-task=8", "--time=12:00:00",
            f"--job-name=g81_{case[3:11]}",
            f"--output={work / 'slurm-%j.out'}", f"--export={export}",
            str(ROOT / "slurm" / "run_case.slurm"),
        ]
        job_id = subprocess.check_output(command, text=True).strip().split(";")[0]
        jobs.append({"case": case, "job_id": job_id, "workdir": str(work)})
    record = {"submitted_epoch": time.time(), "stage": "M1_60h",
              "m0_gate": gate, "jobs": jobs}
    (ROOT / "m1_jobs.json").write_text(json.dumps(record, indent=2) + "\n",
                                        encoding="utf-8")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
