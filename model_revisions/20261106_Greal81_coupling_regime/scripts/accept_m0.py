#!/usr/bin/env python3
"""Create the machine-readable M0 gate from completed immutable runs."""
import csv
import hashlib
import json
import math
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
RUNS = ROOT / "runs"
ORIGINAL = RUNS / "M0_regression_original"
PATCHED = RUNS / "M0_regression_patched"
CSV_FILES = ["budget.csv", "material_budgets.csv", "thermal_budget.csv",
             "film_budget.csv", "mineral_budget.csv", "native_fluxes.csv",
             "depth_profiles_compact.csv"]


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_state(path):
    words = path.read_text(encoding="utf-8").split()
    if words[0] != "PERF_SEGMENT_V1":
        raise RuntimeError(f"unexpected state header: {path}")
    rows, cols = int(words[4]), int(words[5])
    values = [float(x) for x in words[6:]]
    if len(values) != rows * cols:
        raise RuntimeError(f"incomplete state: {path}")
    return float(words[2]), rows, cols, values


def compare_state():
    a = read_state(ORIGINAL / "final_state.txt")
    b = read_state(PATCHED / "final_state.txt")
    compatible = a[:3] == b[:3]
    per_component = []
    if compatible:
        for j in range(a[2]):
            av, bv = a[3][j::a[2]], b[3][j::b[2]]
            scale = max(1.0, max(abs(x) for x in av))
            per_component.append(max(abs(x-y) for x, y in zip(av, bv))/scale)
    return {"compatible": compatible,
            "max_normalized_difference": max(per_component, default=math.inf),
            "component_max_normalized_difference": per_component,
            "time_s": a[0], "rows": a[1], "cols": a[2]}


def compare_csv(name):
    with (ORIGINAL/name).open(newline="", encoding="utf-8") as fa, \
         (PATCHED/name).open(newline="", encoding="utf-8") as fb:
        ar, br = list(csv.reader(fa)), list(csv.reader(fb))
    if not ar or not br or ar[0] != br[0] or len(ar) != len(br):
        return {"compatible": False, "max_normalized_difference": math.inf,
                "rows_original": len(ar), "rows_patched": len(br)}
    max_norm, max_abs = 0.0, 0.0
    for ra, rb in zip(ar[1:], br[1:]):
        if len(ra) != len(rb):
            return {"compatible": False, "max_normalized_difference": math.inf}
        for xa, xb in zip(ra, rb):
            try:
                a, b = float(xa), float(xb)
            except ValueError:
                if xa != xb:
                    return {"compatible": False, "max_normalized_difference": math.inf,
                            "string_mismatch": [xa, xb]}
                continue
            d = abs(a-b)
            max_abs = max(max_abs, d)
            max_norm = max(max_norm, d/max(1.0, abs(a)))
    return {"compatible": True, "max_normalized_difference": max_norm,
            "max_absolute_difference": max_abs, "data_rows": len(ar)-1,
            "sha256_original": sha256(ORIGINAL/name),
            "sha256_patched": sha256(PATCHED/name)}


def main():
    statuses = {}
    for label, path in (("original", ORIGINAL), ("patched", PATCHED)):
        statuses[label] = json.loads((path/"run_status.json").read_text())
    selftests = {}
    for case in ("C1B1", "C0B1", "C1B0", "C0B0"):
        selftests[case] = json.loads(
            (RUNS/f"M0_selftest_{case}"/"causal_selftest.json").read_text())
    state = compare_state()
    csv_results = {name: compare_csv(name) for name in CSV_FILES}
    all_complete = all(x.get("status") == "completed" and
                       abs(x.get("time_s", 0)-93600) < 1e-8
                       for x in statuses.values())
    all_selftests = all(x.get("status") == "passed" for x in selftests.values())
    tolerance = 1e-7
    all_equivalent = (state["compatible"] and
                      state["max_normalized_difference"] <= tolerance and
                      all(v["compatible"] and v["max_normalized_difference"] <= tolerance
                          for v in csv_results.values()))
    result = {
        "status": "passed" if all_complete and all_selftests and all_equivalent else "failed",
        "criterion": "normalized state and matched compact outputs <= 1e-7",
        "all_runs_complete_93600s": all_complete,
        "all_causal_selftests_passed": all_selftests,
        "all_regression_outputs_equivalent": all_equivalent,
        "run_status": statuses, "state": state, "csv": csv_results,
        "binary_sha256": {
            "original": sha256(ROOT/"solver_original"),
            "patched_r03": sha256(ROOT/"solver_patched_r03")},
        "selftests": selftests,
    }
    (ROOT/"m0_acceptance.json").write_text(json.dumps(result, indent=2)+"\n",
                                             encoding="utf-8")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["status"] == "passed" else 3)


if __name__ == "__main__":
    main()
