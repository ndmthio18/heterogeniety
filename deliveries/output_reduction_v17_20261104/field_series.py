"""PVD-driven field access supporting raw VTU and verified VTU.GZ files."""
from __future__ import annotations

import gzip
import xml.etree.ElementTree as ET
from pathlib import Path


def entries(pvd: Path):
    return ET.parse(pvd).findall(".//DataSet")


def read_field(directory: Path, file_attribute: str) -> tuple[Path, bytes]:
    raw = directory / file_attribute
    compressed = Path(str(raw) + ".gz")
    if raw.is_file():
        return raw, raw.read_bytes()
    if compressed.is_file():
        return compressed, gzip.decompress(compressed.read_bytes())
    raise FileNotFoundError(f"Neither {raw} nor {compressed} exists")


def exact_entry(pvd: Path, simulation_time_s: float, tolerance_s: float = 1e-7):
    candidates = entries(pvd)
    item = min(candidates, key=lambda row: abs(float(row.attrib["timestep"]) - simulation_time_s))
    if abs(float(item.attrib["timestep"]) - simulation_time_s) > tolerance_s:
        raise KeyError(f"No exact field at {simulation_time_s:g} s")
    return item
