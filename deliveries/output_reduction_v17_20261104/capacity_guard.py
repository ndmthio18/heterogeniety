"""Pre-launch disk admission check for field output and concurrent cases."""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("--duration-h", type=float, required=True)
    parser.add_argument("--checkpoint-s", type=float, default=600.0)
    parser.add_argument("--vtk-every", type=int, default=6)
    parser.add_argument("--mean-frame-mib", type=float, required=True)
    parser.add_argument("--jobs", type=int, required=True)
    parser.add_argument("--compact-history-mib-per-job", type=float, default=150.0)
    parser.add_argument("--reserve-gib", type=float, default=30.0)
    parser.add_argument("--warning-gib", type=float, default=50.0)
    args = parser.parse_args()
    if args.vtk_every < 1 or args.checkpoint_s <= 0 or args.jobs < 1:
        raise SystemExit("Invalid output or job configuration")
    frames = int(args.duration_h * 3600 // (args.checkpoint_s * args.vtk_every)) + 2
    projected_gib = args.jobs * (frames * args.mean_frame_mib + args.compact_history_mib_per_job) / 1024
    free_gib = shutil.disk_usage(args.path).free / 2**30
    remaining_gib = free_gib - projected_gib
    state = "pass"
    if remaining_gib < args.reserve_gib:
        state = "reject"
    elif remaining_gib < args.warning_gib:
        state = "warn"
    result = {
        "state": state,
        "path": str(args.path.resolve()),
        "frames_per_job": frames,
        "jobs": args.jobs,
        "projected_output_GiB": projected_gib,
        "free_before_GiB": free_gib,
        "projected_free_after_GiB": remaining_gib,
        "reserve_GiB": args.reserve_gib,
        "warning_GiB": args.warning_gib,
    }
    print(json.dumps(result, indent=2))
    raise SystemExit(2 if state == "reject" else 0)


if __name__ == "__main__":
    main()
