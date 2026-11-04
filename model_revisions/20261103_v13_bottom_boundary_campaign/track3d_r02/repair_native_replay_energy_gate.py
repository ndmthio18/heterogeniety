"""Repair only the cancellation-prone native replay energy-flux gate.

The B solvers already reached accepted 174 h endpoints.  This controller
preserves the failed replay attempt, reruns replay/collection on free campaign
CPUs, and rebuilds the terminal status without rerunning any solver.
"""
from pathlib import Path
import datetime, json, os, shutil, subprocess, sys

R = Path(__file__).resolve().parent
CASES = {"B0": 4, "B1": 6, "B2": 7}
STAMP = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
PROV = R / "provenance" / f"native_replay_energy_gate_attempt01_{STAMP}"
PROV.mkdir(parents=True, exist_ok=False)

receipt = {
    "state": "running",
    "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "scope": "postprocess replay only; no solver rerun or physics/numerical change",
    "cases": {},
    "energy_boundary_gate": "relative <= 1e-5 OR absolute <= 1e-10 W",
}
(PROV / "receipt.json").write_text(json.dumps(receipt, indent=2))

jobs = {}
for case, cpu in CASES.items():
    run = R / "raw" / "runs" / case
    old = run / "native_replay"
    preserved = run / f"native_replay_attempt01_energy_net_roundoff_{STAMP}"
    if not old.is_dir():
        raise RuntimeError(f"Missing failed replay directory for {case}")
    shutil.move(old, preserved)
    for src in [R / "status" / f"{case}_production.json", R / f"production_{case}.log"]:
        if src.exists():
            shutil.copy2(src, PROV / src.name)
    log = (PROV / f"{case}_repair.log").open("x")
    cmd = ["taskset", "-c", str(cpu), "nice", "-n", "10", sys.executable,
           str(R / "native_replay.py"), case]
    env = os.environ.copy()
    env.update(OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", DUMUX_NUM_THREADS="1")
    jobs[case] = (subprocess.Popen(cmd, cwd=R, env=env, stdout=log,
                                   stderr=subprocess.STDOUT), log, preserved)
    receipt["cases"][case] = {"cpu": cpu, "pid": jobs[case][0].pid,
                              "preserved_attempt": str(preserved)}
(PROV / "receipt.json").write_text(json.dumps(receipt, indent=2))

failed = {}
for case, (proc, log, preserved) in jobs.items():
    rc = proc.wait()
    log.close()
    if rc:
        failed[case] = rc
        continue
    with (PROV / f"{case}_collect.log").open("x") as out:
        q = subprocess.run([sys.executable, str(R / "collect_case.py"), case],
                           cwd=R, stdout=out, stderr=subprocess.STDOUT)
    if q.returncode:
        failed[case] = q.returncode
        continue
    acceptance = json.loads((R / "raw" / "runs" / case / "acceptance.json").read_text())
    verification = json.loads((R / "raw" / "runs" / case / "native_replay" / "verification.json").read_text())
    status = {
        "state": "completed",
        "case": case,
        "stage": "production",
        "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "job": f"frodo3d_r02_production_{case}",
        "host": "frodo",
        "acceptance": acceptance,
        "raw": str(R / "raw" / "runs" / case),
        "postprocess_repair": {
            "kind": "native replay signed-net energy cancellation gate",
            "solver_rerun": False,
            "original_failure_preserved": str(PROV),
            "verification": verification,
        },
    }
    (R / "status" / f"{case}_production.json").write_text(json.dumps(status, indent=2))

receipt["state"] = "failed" if failed else "completed"
receipt["failed"] = failed
receipt["completed_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
(PROV / "receipt.json").write_text(json.dumps(receipt, indent=2))
if failed:
    raise SystemExit(f"Replay repair failed: {failed}")
