"""Launch G1–G3 simultaneously on three distinct physical Frodo cores."""
from pathlib import Path
import datetime
import json
import os
import shutil
import socket
import subprocess
import sys

R = Path(__file__).resolve().parent
assert socket.gethostname() == "frodo"

lock = R / "parallel_supervisor.lock"
fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
os.write(fd, str(os.getpid()).encode())
os.close(fd)

assignments = {"G1": 3, "G2": 10, "G3": 11}
children = {}
logs = {}


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def save(state, **extra):
    data = dict(
        state=state,
        utc=utc(),
        supervisor_pid=os.getpid(),
        host="frodo",
        simultaneous=True,
        assignments=assignments,
        production_wall_s=48 * 3600,
        running={case: process.pid for case, process in children.items() if process.poll() is None},
        returncodes={case: process.poll() for case, process in children.items() if process.poll() is not None},
        **extra,
    )
    path = R / "supervisor_status.json"
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(data, indent=2))
    temp.replace(path)


try:
    assert shutil.disk_usage(R).free >= 80 * 1024**3
    available_kib = int(
        next(line.split()[1] for line in Path("/proc/meminfo").read_text().splitlines() if line.startswith("MemAvailable:"))
    )
    assert available_kib >= 12 * 1024**2
    for case, cpu in assignments.items():
        env = os.environ.copy()
        env.update(
            CONDITIONAL_G_PRODUCTION_APPROVED="1",
            DUMUX_NUM_THREADS="1",
            OMP_NUM_THREADS="1",
            OPENBLAS_NUM_THREADS="1",
            MKL_NUM_THREADS="1",
        )
        log = (R / f"{case}_production.log").open("x")
        logs[case] = log
        children[case] = subprocess.Popen(
            [
                "taskset",
                "-c",
                str(cpu),
                "nice",
                "-n",
                "10",
                sys.executable,
                str(R / "conditional_controller.py"),
                case,
            ],
            cwd=R,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    save("running", launch_utc=utc())
    while any(process.poll() is None for process in children.values()):
        save("running")
        import time

        time.sleep(20)
    for log in logs.values():
        log.close()
    states = {}
    for case in assignments:
        path = R / "status" / f"{case}_production.json"
        states[case] = json.loads(path.read_text()).get("state") if path.exists() else "missing"
    success = all(state == "completed_conditional" for state in states.values())
    save("completed_conditional" if success else "completed_with_failures", case_states=states)
except Exception as exc:
    save("failed", error=repr(exc))
    raise

