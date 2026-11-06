#!/usr/bin/env python3
"""Rebuild the isolated solver with the accepted portable Frodo toolchain."""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=pathlib.Path)
    parser.add_argument("source", type=pathlib.Path)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--old-source", default="/temp/zhixin/Greal_experimental_bottom_hpcc_20261104/source")
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    source = args.source.resolve()
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    command = []
    old_output = "/temp/zhixin/Greal_experimental_bottom_hpcc_20261104/build/solver"
    for item in manifest["compile_command"]:
        item = item.replace(args.old_source, str(source))
        item = item.replace(old_output, str(output))
        command.append(item)
    subprocess.run(command, check=True)
    result = {
        "status": "passed",
        "source": str(source),
        "output": str(output),
        "binary_sha256": sha256(output),
        "compile_command": command,
    }
    (output.parent / "build_manifest.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
