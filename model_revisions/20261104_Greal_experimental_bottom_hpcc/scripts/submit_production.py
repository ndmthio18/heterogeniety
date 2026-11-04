"""Prepare and submit the two admitted G-real production cases exactly once."""
from pathlib import Path
import json
import os
import shutil
import subprocess


ROOT = Path(os.environ["GREAL_ROOT"])
RUNS = ROOT / "runs"
STATUS = ROOT / "production_jobs.json"
SBATCH = "/rmprog/slurm/v22.05.7/bin/sbatch"

if STATUS.exists():
    raise RuntimeError(f"production submission already recorded: {STATUS}")
benchmark = json.loads((ROOT / "gates" / "multicore" / "benchmark_status.json").read_text())
if benchmark.get("state") != "passed":
    raise RuntimeError("multicore gate has not passed")
capacity = json.loads((ROOT / "gates" / "capacity_gate.json").read_text())
if capacity.get("state") != "pass":
    raise RuntimeError("storage-capacity gate has not passed")
threads = int(benchmark["selected_threads"])
RUNS.mkdir(exist_ok=True)
record = {"state": "submitting", "selected_threads": threads, "jobs": {}}
STATUS.write_text(json.dumps(record, indent=2) + "\n")

try:
    for case, source_input in (("Greal-75", "Greal-75.input"), ("Greal-81", "Greal-81.input")):
        out = RUNS / case
        if out.exists():
            raise RuntimeError(f"refusing to overwrite {out}")
        out.mkdir()
        shutil.copy2(ROOT / source_input, out / "case.input")
        for asset in ("filter_6layers.msh", "Greal04_port.txt", "water_flux_zero_storage.txt"):
            shutil.copy2(ROOT / asset, out / asset)
        command = [
            SBATCH, "--parsable", "--partition=cnmix", "--nodes=1", "--ntasks=1",
            f"--cpus-per-task={threads}", "--time=48:00:00", f"--job-name={case}",
            f"--chdir={out}", "--output=slurm-%j.out",
            f"--export=ALL,GREAL_ROOT={ROOT},GREAL_WORKDIR={out},GREAL_INPUT=case.input",
            str(ROOT / "run_case.slurm"),
        ]
        job_id = subprocess.check_output(command, text=True).strip().split(";")[0]
        record["jobs"][case] = {"job_id": job_id, "directory": str(out)}
        STATUS.write_text(json.dumps(record, indent=2) + "\n")
except Exception:
    record["state"] = "partial_submission_requires_audit"
    STATUS.write_text(json.dumps(record, indent=2) + "\n")
    raise

record["state"] = "submitted"
STATUS.write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps(record, indent=2))
