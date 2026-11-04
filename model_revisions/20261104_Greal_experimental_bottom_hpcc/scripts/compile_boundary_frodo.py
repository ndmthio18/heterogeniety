"""Build the G-real boundary self-test with the same frozen toolchain."""
from pathlib import Path
import hashlib
import json
import os
import subprocess


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"
BUILD.mkdir(exist_ok=True)
solver_command = json.loads((ROOT / "compile_command.json").read_text())
command = []
for token in solver_command:
    if token == str(ROOT / "source" / "appl" / "main.cc"):
        token = str(ROOT / "test_boundary.cc")
    elif token == str(BUILD / "solver"):
        token = str(BUILD / "test_boundary")
    command.append(token)
(ROOT / "boundary_compile_command.json").write_text(json.dumps(command, indent=2) + "\n")

with (BUILD / "boundary_compile.log").open("w") as log:
    result = subprocess.run(
        ["taskset", "-c", os.environ.get("GREAL_BUILD_CPU", "10"), "nice", "-n", "10"] + command,
        stdout=log,
        stderr=subprocess.STDOUT,
    )
if result.returncode:
    raise SystemExit(result.returncode)

digest = hashlib.sha256((BUILD / "test_boundary").read_bytes()).hexdigest()
print(json.dumps({"boundary_binary_sha256": digest}, indent=2))
