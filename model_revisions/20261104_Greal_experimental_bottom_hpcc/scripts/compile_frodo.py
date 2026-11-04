"""Rebuild the isolated G-real executable on the verified Frodo toolchain."""
from pathlib import Path
import hashlib
import json
import os
import platform
import subprocess


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "compile_command_reference.json"
SOURCE = ROOT / "source"
BUILD = ROOT / "build"
BUILD.mkdir(exist_ok=True)

old_source = "/temp/zhixin/v17_output_reduction_20261104/source_profile"
old_binary = "/temp/zhixin/v17_output_reduction_20261104/build_profile/solver"
command = json.loads(REFERENCE.read_text())
command = [
    token.replace(old_source, str(SOURCE)).replace(old_binary, str(BUILD / "solver"))
    for token in command
]
# Frodo is AMD and HPCC is Intel.  The accepted model formerly used
# -march=native, which is not a defensible cross-host deployment target.
command = ["-march=x86-64-v3" if token == "-march=native" else token for token in command]
(ROOT / "compile_command.json").write_text(json.dumps(command, indent=2) + "\n")

with (BUILD / "compile.log").open("w") as log:
    result = subprocess.run(
        ["taskset", "-c", os.environ.get("GREAL_BUILD_CPU", "10"), "nice", "-n", "10"] + command,
        stdout=log,
        stderr=subprocess.STDOUT,
    )
if result.returncode:
    raise SystemExit(result.returncode)


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


ldd = subprocess.run(["ldd", str(BUILD / "solver")], text=True, capture_output=True, check=True)
(BUILD / "ldd.txt").write_text(ldd.stdout)
if "not found" in ldd.stdout:
    raise RuntimeError(ldd.stdout)

sources = {
    str(path.relative_to(ROOT)): sha256(path)
    for path in sorted(SOURCE.rglob("*"))
    if path.is_file()
}
manifest = {
    "status": "passed",
    "host": platform.node(),
    "binary_sha256": sha256(BUILD / "solver"),
    "compile_command": command,
    "source_sha256": sources,
    "build_cpu": os.environ.get("GREAL_BUILD_CPU", "10"),
    "purpose": "isolated G-real executable; no accepted binary replaced",
    "portable_isa": "x86-64-v3 (common Frodo/HPCC subset; replaces host-native ISA only)",
}
(BUILD / "build_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(json.dumps({"binary_sha256": manifest["binary_sha256"], "host": manifest["host"]}, indent=2))
