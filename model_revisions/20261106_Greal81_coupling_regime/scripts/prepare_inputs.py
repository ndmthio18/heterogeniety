#!/usr/bin/env python3
"""Generate immutable M0/M1/M3/M4 inputs from Greal-81."""
from __future__ import annotations

import configparser
import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
BASE = ROOT / "inputs" / "Greal-81.input"
OUT = ROOT / "inputs" / "campaign"
K0 = 7.819185772155931e-12
D0 = 0.008100162249880822


def digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_case(name: str, hours: float, connected: bool, buoyancy: float,
               kc: float = K0, film: float = D0, kfilter: float = 5.30e-12,
               selftest: bool = False) -> dict:
    cfg = configparser.ConfigParser(interpolation=None)
    cfg.optionxform = str
    cfg.read(BASE, encoding="utf-8")
    cfg["TimeLoop"]["TEnd"] = f"{7200 + hours*3600:.17g}"
    cfg["TimeLoop"]["CheckpointOutputInterval"] = "3600"
    cfg["Problem"]["Name"] = name
    cfg["Revision"]["InterfaceExchangeEnabled"] = str(connected).lower()
    cfg["Revision"]["SalinityBuoyancyScale"] = f"{buoyancy:.17g}"
    cfg["Revision"]["CausalSelfTest"] = str(selftest).lower()
    cfg["SpatialParams"]["CoarsePermeability"] = f"{kc:.17g}"
    cfg["SpatialParams"]["FilterPermeability"] = f"{kfilter:.17g}"
    cfg["Revision"]["FilmThickness"] = f"{film:.17g}"
    path = OUT / f"{name}.input"
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        cfg.write(stream, space_around_delimiters=True)
    return {
        "case": name, "path": str(path.relative_to(ROOT)), "hours": hours,
        "connected": connected, "salinity_buoyancy_scale": buoyancy,
        "coarse_permeability_m2": kc, "film_thickness_m": film,
        "filter_permeability_m2": kfilter, "selftest": selftest,
        "sha256": digest(path),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cases = []
    for c, b in ((True, 1.0), (False, 1.0), (True, 0.0), (False, 0.0)):
        tag = f"C{int(c)}B{int(b)}"
        cases.append(write_case(f"M0_selftest_{tag}", 0.01, c, b, selftest=True))
    cases.append(write_case("M0_regression_C1B1", 24, True, 1.0))
    for c, b in ((True, 1.0), (False, 1.0), (True, 0.0), (False, 0.0)):
        tag = f"C{int(c)}B{int(b)}"
        cases.append(write_case(f"M1_{tag}_K100_D100", 60, c, b))
    for kfac in (0.5, 1.0, 2.0):
        for dfac in (0.75, 1.0, 1.33):
            for c in (True, False):
                # Center C1B1/C0B1 is reused from M1, not resubmitted.
                if kfac == 1.0 and dfac == 1.0:
                    continue
                cases.append(write_case(
                    f"M3_C{int(c)}B1_K{int(kfac*100):03d}_D{int(dfac*100):03d}",
                    60, c, 1.0, kc=K0*kfac, film=D0*dfac))
    # Prespecified buoyancy-off extensions at two opposite screen corners.
    for kfac, dfac in ((0.5, 0.75), (2.0, 1.33)):
        for c in (True, False):
            cases.append(write_case(
                f"M3B0_C{int(c)}B0_K{int(kfac*100):03d}_D{int(dfac*100):03d}",
                60, c, 0.0, kc=K0*kfac, film=D0*dfac))
    for kfilter, label in ((3.39e-12, "LOW"), (7.64e-12, "HIGH")):
        for c in (True, False):
            cases.append(write_case(
                f"M4_C{int(c)}B1_KF_{label}", 60, c, 1.0, kfilter=kfilter))
    manifest = {
        "baseline_input": str(BASE.relative_to(ROOT)),
        "baseline_sha256": digest(BASE),
        "cases": cases,
        "counts": {
            "M0": sum(x["case"].startswith("M0") for x in cases),
            "M1": sum(x["case"].startswith("M1") for x in cases),
            "M3": sum(x["case"].startswith("M3_") for x in cases),
            "M3B0": sum(x["case"].startswith("M3B0") for x in cases),
            "M4": sum(x["case"].startswith("M4") for x in cases),
        },
    }
    (ROOT / "CASE_REGISTRY.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
