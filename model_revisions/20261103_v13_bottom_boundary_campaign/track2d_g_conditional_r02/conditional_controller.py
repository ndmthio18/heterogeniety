"""Run one full 2D G case as a conditional sensitivity calculation.

The original refined-grid gate failure is deliberately not reclassified as a
pass.  This controller uses the unchanged production mesh, executable, input,
physics, tolerances, and time stepping, and records that the result is
conditional until the spatial screen is repaired and accepted.
"""
from pathlib import Path
import json
import os
import socket
import subprocess
import sys

import runner as r

R = Path(__file__).resolve().parent
r.ROOT = R
r.SCRATCH = R / "raw"
r.BUILD_DIRECTORY = "build_sal"
r.SCRATCH.mkdir(exist_ok=True)
(R / "status").mkdir(exist_ok=True)

assert socket.gethostname() == "frodo"
assert os.environ.get("CONDITIONAL_G_PRODUCTION_APPROVED") == "1"
assert os.environ.get("DUMUX_NUM_THREADS") == "1"

case = sys.argv[1]
assert case in {"G1", "G2", "G3"}
cpu = ",".join(map(str, sorted(os.sched_getaffinity(0))))
status_path = R / "status" / f"{case}_production.json"


def write(state, **extra):
    r.write(
        status_path,
        dict(
            state=state,
            case=case,
            stage="conditional_production",
            validation_status="conditional_unaccepted_refined_grid_gate",
            original_gate_failure="2D G1_refined residual floor 1.04–1.09e-10 above fixed 1e-10 criterion",
            scientific_use="sensitivity evidence only; exclude from validated claims until numerical screen is resolved",
            host=socket.gethostname(),
            controller_pid=os.getpid(),
            affinity=cpu,
            utc=r.utc(),
            **extra,
        ),
    )


try:
    write("running")
    result = r.run(case, cpu, production=True)
    assert result["state"] == "completed", result
    subprocess.run(
        [sys.executable, str(R / "analyze.py"), case, "--root", str(R)],
        check=True,
    )
    write("completed_conditional", acceptance=result["acceptance"], raw=result["raw_path"])
except Exception as exc:
    write("failed", error=repr(exc))
    raise

