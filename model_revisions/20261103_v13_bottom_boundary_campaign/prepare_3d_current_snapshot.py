"""Create a hash-pinned, read-only sparse snapshot for 3D plotting."""
from pathlib import Path
import copy, gzip, hashlib, json, shutil, sys
import xml.etree.ElementTree as ET

SOURCE = Path(sys.argv[1]).resolve()
DEST = Path(sys.argv[2]).resolve()
if DEST.exists():
    raise SystemExit(f"Refusing to overwrite {DEST}")

requested = {
    "B0": [0, 24, 60, 108, 174],
    "B1": [0, 24, 60, 108, 174],
    "B2": [0, 24, 60, 108, 174],
    "B3": [0, 24, 60, 108, 174],
    "G1": [0, 24, 60, 108, 174],
    "G2": [0, 24, 60, 108, 174],
    "G3": [0, 24, 60, 108, 174],
}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

manifest = {"source": str(SOURCE), "cases": {},
            "selection": "exact accepted saved times only; no interpolation or extrapolation"}
for case, times in requested.items():
    src = SOURCE / "raw" / "runs" / case
    dst = DEST / "raw" / "runs" / case
    dst.mkdir(parents=True)
    pvd = src / f"{case}.pvd"
    tree = ET.parse(pvd)
    collection = tree.find(".//Collection")
    entries = list(collection.findall("DataSet"))
    chosen = []
    for wanted in times:
        matches = [e for e in entries if abs(float(e.get("timestep")) / 3600 - 2 - wanted) < 1e-8]
        if len(matches) != 1:
            raise RuntimeError(f"{case}: expected one saved field at {wanted} h, found {len(matches)}")
        chosen.append(matches[0])
    for e in entries:
        collection.remove(e)
    records = []
    for e in chosen:
        collection.append(copy.deepcopy(e))
        rel = Path(e.get("file"))
        raw = src / rel
        zipped = raw.with_suffix(raw.suffix + ".gz")
        out = dst / (str(rel) + ".gz")
        out.parent.mkdir(parents=True, exist_ok=True)
        if zipped.exists():
            shutil.copy2(zipped, out)
        elif raw.exists():
            with raw.open("rb") as fi, gzip.GzipFile(filename="", mode="wb", fileobj=out.open("wb"), mtime=0) as fo:
                shutil.copyfileobj(fi, fo)
        else:
            raise FileNotFoundError(zipped)
        records.append({"time_h": float(e.get("timestep")) / 3600 - 2,
                        "file": out.name, "sha256": sha(out), "bytes": out.stat().st_size})
    tree.write(dst / f"{case}.pvd", encoding="utf-8", xml_declaration=True)
    for name in ["cell_geometry.csv", "budget.csv", "thermal_budget.csv", "film_budget.csv",
                 "mineral_budget.csv", "material_budgets.csv"]:
        if (src / name).exists():
            shutil.copy2(src / name, dst / name)
    manifest["cases"][case] = records

(DEST / "SNAPSHOT_PROVENANCE.json").write_text(json.dumps(manifest, indent=2))
print(json.dumps({"state": "prepared", "destination": str(DEST),
                  "fields": sum(len(v) for v in manifest["cases"].values())}, indent=2))
