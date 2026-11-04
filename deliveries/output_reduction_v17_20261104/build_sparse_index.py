from __future__ import annotations

import json
from pathlib import Path


root = Path(__file__).resolve().parent
datasets = []
for path in sorted((root / "sparse_working_sets").rglob("manifest.json")):
    record = json.loads(path.read_text(encoding="utf-8"))
    record["dataset"] = path.parent.relative_to(root / "sparse_working_sets").as_posix()
    datasets.append(record)
result = {
    "state": "passed" if len(datasets) == 13 and all(row["state"] == "passed" and len(row["frames"]) == 9 for row in datasets) else "failed",
    "datasets": datasets,
    "total_frames": sum(len(row["frames"]) for row in datasets),
    "total_working_bytes": sum(row["working_bytes"] for row in datasets),
    "storage_note": "Bulk VTU working files are local/external and are intentionally excluded from Git; this index fixes all source and working hashes.",
}
(root / "SPARSE_WORKING_SET_INDEX.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps({key: result[key] for key in ["state", "total_frames", "total_working_bytes"]}))
