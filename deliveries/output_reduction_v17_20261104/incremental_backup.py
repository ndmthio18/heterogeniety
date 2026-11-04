"""Hash-indexed backup: copy only files absent or changed at destination."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    args.destination.mkdir(parents=True, exist_ok=True)
    index_path = args.destination / "verified_index.json"
    previous = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() else {}
    current, copied, unchanged = {}, [], []
    for source in sorted(path for path in args.source.rglob("*") if path.is_file()):
        relative = source.relative_to(args.source).as_posix()
        sha = digest(source)
        current[relative] = {"sha256": sha, "bytes": source.stat().st_size}
        target = args.destination / relative
        if previous.get(relative, {}).get("sha256") == sha and target.exists():
            unchanged.append(relative)
            continue
        copied.append(relative)
        if not args.dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            if digest(target) != sha:
                raise RuntimeError(f"Post-copy SHA256 mismatch: {relative}")
    receipt = {
        "utc": datetime.now(timezone.utc).isoformat(),
        "source": str(args.source.resolve()),
        "destination": str(args.destination.resolve()),
        "dry_run": args.dry_run,
        "copied_files": len(copied),
        "unchanged_files": len(unchanged),
        "copied_bytes": sum(current[name]["bytes"] for name in copied),
        "copied": copied,
    }
    if not args.dry_run:
        index_path.write_text(json.dumps(current, indent=2), encoding="utf-8")
        (args.destination / "last_backup_receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
