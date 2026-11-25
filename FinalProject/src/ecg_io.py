"""Shared loaders for the BME4400 final project (PRD §2).

Every script that reads labels or signals goes through these functions, so all
teammates read the same files the same way.
"""
from __future__ import annotations

import csv
import hashlib
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import numpy as np
import scipy.io as sio

REPO = Path(__file__).resolve().parent.parent
DEFAULT_DATA_ROOT = Path.home() / "bme4191_ecg"
PARTS_MANIFEST = REPO / "results" / "source_data" / "ecg_arrhythmia_parts.csv"
PARTS_MANIFEST_SHA256 = "6720d3b3177bfce0eefa93e92275cd7f0b7b9fa7216ee3fa6c72181b75cc0d1a"
DIAG_MD5 = "f9795256cd8590f8b22f2f8f6762d89e"  # figshare file 15653771

# PRD §3 target coding
CLASSES = ["SR", "SB", "ST", "SI", "AFIB", "AFL"]
CLASS_CODE = {c: i for i, c in enumerate(CLASSES)}
# Diagnostics.xlsx Rhythm value -> class name
FIGSHARE_RHYTHM = {"SR": "SR", "SB": "SB", "ST": "ST", "SA": "SI", "AFIB": "AFIB", "AF": "AFL"}

_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def md5_file(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_parts_manifest() -> dict[str, dict[str, str]]:
    """record -> {folder, hospital, part}. Checks the pinned hash first."""
    got = sha256_file(PARTS_MANIFEST)
    if got != PARTS_MANIFEST_SHA256:
        raise SystemExit(f"parts manifest sha256 {got} != pinned {PARTS_MANIFEST_SHA256}")
    with PARTS_MANIFEST.open() as fh:
        return {r["record"]: r for r in csv.DictReader(fh)}


def read_diagnostics(data_root: Path) -> list[dict[str, str]]:
    """Rows of figshare Diagnostics.xlsx in file order (row k = record JSk). Standard library only."""
    path = Path(data_root).expanduser() / "figshare_chapman" / "Diagnostics.xlsx"
    got = md5_file(path)
    if got != DIAG_MD5:
        raise SystemExit(f"Diagnostics.xlsx MD5 {got} != figshare's {DIAG_MD5}")
    z = zipfile.ZipFile(path)
    shared = [
        "".join(t.text or "" for t in si.iter(f"{{{_NS['m']}}}t"))
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", _NS)
    ]
    rows = []
    for r in ET.fromstring(z.read("xl/worksheets/sheet1.xml")).iter(f"{{{_NS['m']}}}row"):
        row = {}
        for c in r.findall("m:c", _NS):
            col = re.match(r"[A-Z]+", c.get("r")).group()
            v = c.find("m:v", _NS)
            val = None if v is None else v.text
            if c.get("t") == "s":
                val = shared[int(val)]
            row[col] = val
        rows.append(row)
    header = rows[0]
    return [{header[k]: v for k, v in r.items()} for r in rows[1:]]


def load_part1_signal(data_root: Path, record: str, folder: str) -> np.ndarray:
    """12 x 5000 int16, µV, from the PhysioNet part-1 .mat file."""
    p = Path(data_root).expanduser() / "ecg-arrhythmia" / "1.0.0" / "WFDBRecords" / folder / f"{record}.mat"
    return sio.loadmat(p)["val"].astype(np.int16)


def load_figshare_signal(data_root: Path, file_name: str) -> np.ndarray:
    """12 x 5000 int16, µV: round(figshare CSV), which is how part-1 signals relate to figshare (DRA O30)."""
    import pandas as pd

    p = Path(data_root).expanduser() / "figshare_chapman" / "ECGData" / f"{file_name}.csv"
    x = pd.read_csv(p).to_numpy(dtype=float)  # 5000 x 12
    if x.shape != (5000, 12) or np.isnan(x).any():
        raise SystemExit(f"{p}: shape {x.shape} or NaN values; expected 5000 x 12 with no NaN")
    return np.round(x).T.astype(np.int16)


def signal_sha256(sig: np.ndarray) -> str:
    """Hash of the 12 x 5000 int16 array (C order), used for duplicate and leakage checks."""
    return hashlib.sha256(np.ascontiguousarray(sig, dtype=np.int16).tobytes()).hexdigest()
