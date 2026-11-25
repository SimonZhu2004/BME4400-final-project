#!/usr/bin/env python3
"""Build results/source_data/ecg_arrhythmia_parts.csv: which hospital (and so which project
part) every ecg-arrhythmia 1.0.0 record belongs to.

The ecg-arrhythmia page does not say which records come from which hospital.
The PhysioNet/CinC Challenge 2021 v1.0.3 release ships the same recordings in
two folders, training/chapman_shaoxing/ and training/ningbo/. This script
joins the two releases by record ID using ONLY their published SHA256SUMS.txt
files (file names and checksums; no recording is opened or downloaded):

    part 1 (downloaded)  = Chapman-Shaoxing (Shaoxing People's Hospital)
    part 2 (protected)   = Ningbo First Hospital

It refuses to write the manifest unless the join is exact: every record is in
exactly one hospital folder, the counts match the Challenge page (10,247 and
34,905), and every .mat signal file is byte-identical across the releases.

Usage (from the repository root; standard library only):
    python src/build_ecg_parts_manifest.py
"""
from __future__ import annotations

import csv
import hashlib
import re
import sys
import tempfile
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT = REPO_ROOT / "results" / "source_data" / "ecg_arrhythmia_parts.csv"
SOURCES = {
    "ecg": ("https://physionet.org/files/ecg-arrhythmia/1.0.0/SHA256SUMS.txt",
            "dfad0c26a276ce7e450e5002051f4c749304552d9add4d592928bbdcb6e4f31c"),
    "challenge": ("https://physionet.org/files/challenge-2021/1.0.3/SHA256SUMS.txt",
                  "f29c2609343c38734f3a3d62be4a9052ca56a9e560e7ad2efc2118563fca2473"),
}
PART = {"chapman_shaoxing": 1, "ningbo": 2}
EXPECTED_COUNTS = {"chapman_shaoxing": 10247, "ningbo": 34905}  # Challenge 2021 page, Data Access items 7-8


def fetch_pinned(url: str, want: str, tmp: Path) -> list[list[str]]:
    dest = tmp / hashlib.sha1(url.encode()).hexdigest()
    with urllib.request.urlopen(url, timeout=300) as r:
        dest.write_bytes(r.read())
    got = hashlib.sha256(dest.read_bytes()).hexdigest()
    if got != want:
        sys.exit(f"{url} changed: sha256 {got[:12]} != pinned {want[:12]}; stop and investigate")
    return [p for p in (line.split(maxsplit=1) for line in dest.read_text().splitlines()) if len(p) == 2]


def main() -> int:
    with tempfile.TemporaryDirectory() as t:
        ecg = fetch_pinned(*SOURCES["ecg"], Path(t))
        chal = fetch_pinned(*SOURCES["challenge"], Path(t))

    ecg_mat, ecg_dir = {}, {}
    for h, path in ecg:
        m = re.fullmatch(r"WFDBRecords/(\d+/\d+)/(JS\d+)\.(hea|mat)", path.strip())
        if m:
            ecg_dir[m.group(2)] = m.group(1)
            if m.group(3) == "mat":
                ecg_mat[m.group(2)] = h

    src, chal_mat = {}, {}
    for h, path in chal:
        m = re.fullmatch(r"training/(chapman_shaoxing|ningbo)/(g\d+)/(JS\d+)\.(hea|mat)", path.strip())
        if not m:
            continue
        hosp, rec = m.group(1), m.group(3)
        if src.setdefault(rec, hosp) != hosp:
            sys.exit(f"{rec} appears under both hospital folders")
        if m.group(4) == "mat":
            chal_mat[rec] = h

    problems = []
    if set(src) != set(ecg_dir):
        problems.append(f"record sets differ: {len(set(ecg_dir) - set(src))} only in ecg-arrhythmia, "
                        f"{len(set(src) - set(ecg_dir))} only in challenge")
    for hosp, n in EXPECTED_COUNTS.items():
        got = sum(v == hosp for v in src.values())
        if got != n:
            problems.append(f"{hosp}: {got} records, Challenge page states {n}")
    diff = [r for r in ecg_mat if chal_mat.get(r) != ecg_mat[r]]
    if diff:
        problems.append(f"{len(diff)} .mat files differ between releases (e.g. {diff[:3]})")
    if problems:
        sys.exit("refusing to write manifest:\n  " + "\n  ".join(problems))

    rows = sorted(ecg_dir, key=lambda r: int(r[2:]))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["record", "folder", "hospital", "part"])
        for r in rows:
            w.writerow([r, ecg_dir[r], src[r], PART[src[r]]])
    for hosp, part in PART.items():
        ids = [int(r[2:]) for r in rows if src[r] == hosp]
        print(f"part {part} = {hosp}: {len(ids)} records, JS{min(ids):05d}-JS{max(ids):05d}")
    print(f"wrote {OUT.relative_to(REPO_ROOT)} ({len(rows)} rows); all .mat files identical across releases")
    return 0


if __name__ == "__main__":
    sys.exit(main())
