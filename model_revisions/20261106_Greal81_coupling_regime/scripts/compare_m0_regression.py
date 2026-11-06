#!/usr/bin/env python3
"""Numerically compare original and patched C1B1 final state files."""
import json
import math
import pathlib
import sys


def read_state(path):
    words = pathlib.Path(path).read_text(encoding="utf-8").split()
    if words[0] != "PERF_SEGMENT_V1":
        raise RuntimeError(f"unexpected state format: {path}")
    nonisothermal, time, seeded, rows, cols = words[1:6]
    rows, cols = int(rows), int(cols)
    values = [float(x) for x in words[6:]]
    if len(values) != rows * cols:
        raise RuntimeError(f"incomplete state: {path}")
    return {"nonisothermal": int(nonisothermal), "time_s": float(time),
            "seeded": seeded, "rows": rows, "cols": cols,
            "values": values}


def main():
    if len(sys.argv) != 4:
        raise SystemExit("usage: compare_m0_regression.py ORIGINAL PATCHED OUT")
    a, b = read_state(sys.argv[1]), read_state(sys.argv[2])
    compatible = all(a[k] == b[k] for k in
                     ("nonisothermal", "time_s", "rows", "cols"))
    component_scales = []
    component_max_abs = []
    component_max_norm = []
    if compatible:
        for j in range(a["cols"]):
            av = a["values"][j::a["cols"]]
            bv = b["values"][j::b["cols"]]
            scale = max(1.0, max(abs(x) for x in av))
            diffs = [abs(x-y) for x, y in zip(av, bv)]
            component_scales.append(scale)
            component_max_abs.append(max(diffs))
            component_max_norm.append(max(diffs) / scale)
    max_norm = max(component_max_norm, default=math.inf)
    result = {
        "status": "passed" if compatible and max_norm <= 1e-7 else "failed",
        "criterion": "max_j(max_i(abs(patched-original))/max(1,max_i(abs(original)))) <= 1e-7",
        "compatible_headers": compatible,
        "max_normalized_state_difference": max_norm,
        "component_scales": component_scales,
        "component_max_abs_difference": component_max_abs,
        "component_max_normalized_difference": component_max_norm,
        "original": {k: a[k] for k in ("time_s", "rows", "cols")},
        "patched": {k: b[k] for k in ("time_s", "rows", "cols")},
    }
    pathlib.Path(sys.argv[3]).write_text(json.dumps(result, indent=2) + "\n",
                                         encoding="utf-8")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["status"] == "passed" else 3)


if __name__ == "__main__":
    main()
