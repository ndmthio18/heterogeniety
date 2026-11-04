"""Build the future compact-profile overlay in isolation on Frodo."""
from __future__ import annotations

import datetime
import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OLD = Path("/temp/zhixin/heterogeneity_performance_v14_20261102")
BUILD = ROOT / "build_profile"
SOURCE = ROOT / "source_profile"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if BUILD.exists():
    raise SystemExit(f"Refusing to overwrite {BUILD}")
BUILD.mkdir()
frozen = OLD / "build_cached_ni1/heterogeneity_revised"
assert sha(frozen) == "9b1422e33fb76423322b081e414206e22777548fca0b703d6e285186a4fe63e5"
command = json.loads((OLD / "build_cached_ni1/compile_command.json").read_text())
command = [
    item.replace(str(OLD / "source_cached"), str(SOURCE)).replace(str(frozen), str(BUILD / "solver"))
    for item in command
]
(BUILD / "compile_command.json").write_text(json.dumps(command, indent=2))
with (BUILD / "build.log").open("w") as log:
    result = subprocess.run(["taskset", "-c", "9", "nice", "-n", "15", *command], stdout=log, stderr=subprocess.STDOUT)
if result.returncode:
    raise SystemExit("Compile failed; build.log retained")
manifest = {
    "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "host": "frodo",
    "purpose": "future-output overlay only; frozen accepted v13 remains unchanged",
    "binary_sha256": sha(BUILD / "solver"),
    "frozen_reference_sha256": sha(frozen),
    "source_sha256": {str(path.relative_to(ROOT)): sha(path) for path in SOURCE.rglob("*") if path.is_file()},
    "compile_command": command,
}
(BUILD / "build_manifest.json").write_text(json.dumps(manifest, indent=2))
print(json.dumps({"state": "passed", "binary_sha256": manifest["binary_sha256"]}))
