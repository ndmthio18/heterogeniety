from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SKIP_PARTS = {"__pycache__", "sparse_working_sets", "remote_results", "profile_overlay_result"}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


files = {}
for path in sorted(item for item in ROOT.rglob("*") if item.is_file()):
    relative = path.relative_to(ROOT)
    if path.name == "EVIDENCE_MANIFEST.json" or any(part in SKIP_PARTS for part in relative.parts):
        continue
    files[relative.as_posix()] = {"bytes": path.stat().st_size, "sha256": sha(path)}
result = {
    "utc": datetime.now(timezone.utc).isoformat(),
    "scope": "reports, implementations and compact evidence; bulk sparse VTUs and downloaded regression raw have their own manifests/results",
    "files": files,
}
(ROOT / "EVIDENCE_MANIFEST.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(len(files))
