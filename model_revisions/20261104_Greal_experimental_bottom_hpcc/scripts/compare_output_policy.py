"""Check sparse face output against the completed dense-face reference."""
from pathlib import Path
import hashlib
import json
import sys


dense, sparse = map(Path, sys.argv[1:3])
physics_files = (
    "final_state.txt", "budget.csv", "film_budget.csv", "thermal_budget.csv",
    "mineral_budget.csv", "material_budgets.csv", "native_fluxes.csv",
    "depth_profiles_compact.csv",
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


checks = {}
for name in physics_files:
    a, b = dense / name, sparse / name
    checks[name] = {"dense_sha256": sha(a), "sparse_sha256": sha(b), "identical": sha(a) == sha(b)}

result = {
    "state": "passed" if all(row["identical"] for row in checks.values()) else "failed",
    "physics_tables": checks,
    "dense_film_faces_bytes": (dense / "film_faces.csv").stat().st_size,
    "sparse_film_faces_bytes": (sparse / "film_faces.csv").stat().st_size,
    "dense_vtu_count": len(list(dense.glob("*.vtu"))),
    "sparse_vtu_count": len(list(sparse.glob("*.vtu"))),
    "interpretation": "output-frequency equivalence only; not a time-step or grid convergence test",
}
(sparse / "output_equivalence_sparse.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
if result["state"] != "passed":
    raise SystemExit(1)
