#!/usr/bin/env python3
"""Low-resource login-node controller: accept M0, then release M1 once."""
import json
import pathlib
import subprocess
import time
import traceback

ROOT = pathlib.Path(__file__).resolve().parents[1]
RUNS = ROOT / "runs"
STATUS = ROOT / "m0_controller_status.json"
LOG = ROOT / "m0_controller.log"


def record(state, **extra):
    data = {"state": state, "updated_epoch": time.time(), **extra}
    STATUS.write_text(json.dumps(data, indent=2)+"\n", encoding="utf-8")
    with LOG.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(data, sort_keys=True)+"\n")


def load_run(name):
    path = RUNS/name/"run_status.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    deadline = time.time() + 10*3600
    record("waiting_for_m0")
    while time.time() < deadline:
        original = load_run("M0_regression_original")
        patched = load_run("M0_regression_patched")
        states = {"original": original, "patched": patched}
        if any(x and x.get("status") == "failed" for x in states.values()):
            record("m0_run_failed", run_status=states)
            return 2
        if all(x and x.get("status") == "completed" for x in states.values()):
            record("evaluating_m0", run_status=states)
            accepted = subprocess.run(["python3", str(ROOT/"scripts"/"accept_m0.py")],
                                      cwd=ROOT, text=True, capture_output=True)
            if accepted.returncode != 0:
                record("m0_gate_failed", run_status=states,
                       stdout=accepted.stdout[-8000:], stderr=accepted.stderr[-8000:])
                return 3
            gate = json.loads((ROOT/"m0_acceptance.json").read_text(encoding="utf-8"))
            if (ROOT/"m1_jobs.json").exists():
                record("m1_already_registered", gate=gate)
                return 4
            submitted = subprocess.run(["python3", str(ROOT/"scripts"/"submit_m1.py")],
                                       cwd=ROOT, text=True, capture_output=True)
            if submitted.returncode != 0:
                record("m1_submission_failed", gate=gate,
                       stdout=submitted.stdout[-8000:], stderr=submitted.stderr[-8000:])
                return 5
            jobs = json.loads((ROOT/"m1_jobs.json").read_text(encoding="utf-8"))
            record("m1_submitted", gate=gate, jobs=jobs)
            return 0
        record("waiting_for_m0", run_status=states)
        time.sleep(60)
    record("m0_timeout")
    return 6


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        record("controller_exception", traceback=traceback.format_exc())
        raise
