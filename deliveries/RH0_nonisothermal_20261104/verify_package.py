from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "PACKAGE_MANIFEST.sha256"


def digest(path: Path) -> str:
    hasher = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def write_manifest() -> None:
    files = sorted(
        path
        for path in ROOT.rglob("*")
        if path.is_file() and path != MANIFEST and "__pycache__" not in path.parts
    )
    lines = [f"{digest(path)}  {path.relative_to(ROOT).as_posix()}" for path in files]
    MANIFEST.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {len(lines)} records")


def main() -> int:
    if len(sys.argv) == 2 and sys.argv[1] == "--write":
        write_manifest()
        return 0
    failures: list[str] = []
    records = [line for line in MANIFEST.read_text(encoding="utf-8").splitlines() if line]
    for record in records:
        expected, relative = record.split("  ", 1)
        path = ROOT / relative
        if not path.is_file():
            failures.append(f"missing: {relative}")
        elif digest(path) != expected:
            failures.append(f"hash mismatch: {relative}")
    if failures:
        print("\n".join(failures))
        return 1
    print(f"verified {len(records)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
