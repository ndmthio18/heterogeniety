"""Validate formal Slurm benchmark endpoints and select the fastest equivalent case."""
from pathlib import Path
import csv
import hashlib
import json
import os
import re
import subprocess


ROOT = Path(os.environ["GREAL_ROOT"])
RUNS = ROOT / "gates" / "multicore"
SACCT = "/rmprog/slurm/v22.05.7/bin/sacct"
job_map = json.loads((RUNS / "slurm_jobs.json").read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def state(path):
    rows = []
    with Path(path).open() as handle:
        next(handle)
        for line in handle:
            if line.strip():
                rows.append([float(value) for value in line.split()])
    return rows


def compare(reference, candidate):
    a, b = state(reference), state(candidate)
    if len(a) != len(b) or any(len(x) != len(y) for x, y in zip(a, b)):
        raise RuntimeError("state shape mismatch")
    phase_identical = all(x[0] == y[0] for x, y in zip(a, b))
    scales = [max(max(abs(row[j]) for row in a), 1e-12) for j in range(1, len(a[0]))]
    errors = [max(abs(x[j] - y[j]) for x, y in zip(a, b)) / scales[j - 1]
              for j in range(1, len(a[0]))]
    return {"phase_identical": phase_identical, "max_relative": max(errors),
            "passed": phase_identical and max(errors) < 1e-7}


def timings(path):
    with Path(path).open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {key: sum(float(row[key]) for row in rows)
            for key in ("newton_s", "audit_record_s", "output_s", "step_s")}


records = []
reference = RUNS / "t1" / "final_state.txt"
for threads in (1, 2, 4, 8):
    job_id = str(job_map[str(threads)])
    raw = subprocess.check_output(
        [SACCT, "-j", job_id, "-X", "--format=State,ExitCode,ElapsedRaw,NodeList", "-n", "-P"],
        text=True,
    ).strip().splitlines()[0].split("|")
    state_name, exit_code, elapsed, node_list = raw
    out = RUNS / f"t{threads}"
    status = json.loads((out / "run_status.json").read_text())
    if state_name != "COMPLETED" or exit_code != "0:0" or status["status"] != "completed":
        raise RuntimeError(f"t{threads} not accepted: {raw}, {status}")
    if abs(float(status["time_s"]) - 9600.0) > 1e-8:
        raise RuntimeError(f"t{threads} endpoint mismatch")
    log_text = (out / "simulation.log").read_text(errors="replace")
    def time_value(label):
        match = re.search(rf"{re.escape(label)}:\s*([0-9.]+)", log_text)
        if not match:
            raise RuntimeError(f"missing /usr/bin/time field: {label}")
        return float(match.group(1))
    cpu_match = re.search(r"Percent of CPU this job got:\s*([0-9.]+)%", log_text)
    if not cpu_match:
        raise RuntimeError("missing CPU utilization field")
    record = {
        "threads": threads,
        "job_id": job_id,
        "elapsed_s": float(elapsed),
        "user_cpu_s": time_value("User time (seconds)"),
        "system_cpu_s": time_value("System time (seconds)"),
        "cpu_percent": float(cpu_match.group(1)),
        "max_rss_kb": int(time_value("Maximum resident set size (kbytes)")),
        "node_list": node_list,
        "binary_sha256": sha(ROOT / "solver"),
        "timing": timings(out / "performance_steps.csv"),
        "state_comparison": {"phase_identical": True, "max_relative": 0.0, "passed": True}
            if threads == 1 else compare(reference, out / "final_state.txt"),
    }
    if not record["state_comparison"]["passed"]:
        raise RuntimeError(f"t{threads} numerical equivalence failed")
    records.append(record)

baseline = records[0]["elapsed_s"]
for row in records:
    row["speedup"] = baseline / row["elapsed_s"]
    row["parallel_efficiency"] = row["speedup"] / row["threads"]
selected = min(records, key=lambda row: row["elapsed_s"])
report = {
    "state": "passed",
    "results": records,
    "selected_threads": selected["threads"],
    "selection_rule": "lowest Slurm elapsed time among state-equivalent one-task cases",
}
(RUNS / "benchmark_status.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
