#!/usr/bin/env python3
"""DRA repair checks U1 and U9 against the original Chapman-Shaoxing release on figshare.

U1: are the 399 record IDs absent from ecg-arrhythmia part 1 the 399 sinus
    irregularity (SI, "SA" in Diagnostics.xlsx) records?
U9: how do the SB / SR / ST labels relate to the MUSE-measured ventricular rate?

Reads only metadata: figshare Diagnostics.xlsx (collection ChapmanECG, 4560497,
file 15653771, MD5 f9795256cd8590f8b22f2f8f6762d89e) and the part-1 record
table written by src/dra_inspect.py. No signal is opened, nothing is fitted.
Standard library only (no openpyxl): an .xlsx file is a zip of XML sheets.

Usage (from the repository root):
    python -I src/figshare_check.py [--data-root ~/bme4191_ecg]
Expects <data-root>/figshare_chapman/Diagnostics.xlsx. Writes results/figshare_check/.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import statistics
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from pathlib import Path

DIAG_MD5 = "f9795256cd8590f8b22f2f8f6762d89e"
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
RECORD_TABLE = Path("results/dra/record_table_part1.csv")
OUT = Path("results/figshare_check")
# record_table_part1.csv rhythm names -> Diagnostics.xlsx rhythm names
PN_TO_FS = {"AFL(AF)": "AF"}
SINUS = ("SB", "SR", "ST")


def read_xlsx_first_sheet(path: Path) -> list[dict[str, str]]:
    """Return the first sheet as a list of dicts keyed by the header row."""
    z = zipfile.ZipFile(path)
    shared = [
        "".join(t.text or "" for t in si.iter(f"{{{NS['m']}}}t"))
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS)
    ]
    rows = []
    for r in ET.fromstring(z.read("xl/worksheets/sheet1.xml")).iter(f"{{{NS['m']}}}row"):
        row = {}
        for c in r.findall("m:c", NS):
            col = re.match(r"[A-Z]+", c.get("r")).group()
            v = c.find("m:v", NS)
            val = None if v is None else v.text
            if c.get("t") == "s":
                val = shared[int(val)]
            row[col] = val
        rows.append(row)
    header = rows[0]
    return [{header[k]: v for k, v in r.items()} for r in rows[1:]]


def rate_rule(bpm: int) -> str:
    return "SB" if bpm < 60 else ("ST" if bpm > 100 else "SR")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default=str(Path.home() / "bme4191_ecg"))
    a = ap.parse_args()
    diag_path = Path(a.data_root).expanduser() / "figshare_chapman" / "Diagnostics.xlsx"
    md5 = hashlib.md5(diag_path.read_bytes()).hexdigest()
    if md5 != DIAG_MD5:
        raise SystemExit(f"Diagnostics.xlsx MD5 {md5} != figshare's {DIAG_MD5}")

    diag = read_xlsx_first_sheet(diag_path)
    pn = {int(r["record"][2:]): r for r in csv.DictReader(RECORD_TABLE.open())}
    OUT.mkdir(parents=True, exist_ok=True)

    # ---- U1: align JS ids with Diagnostics row order (row k <-> JS{k:05d}) ----
    align, mism = [], Counter()
    for k, d in enumerate(diag, start=1):
        p = pn.get(k)
        row = {"js_id": f"JS{k:05d}", "diag_row": k, "FileName": d["FileName"],
               "fs_rhythm": d["Rhythm"], "fs_age": d["PatientAge"], "fs_sex": d["Gender"],
               "in_part1": p is not None, "pn_rhythm": "", "pn_age": "", "pn_sex": "",
               "mismatch": ""}
        if p is not None:
            row.update(pn_rhythm=p["rhythm_labels"], pn_age=p["age"], pn_sex=p["sex"])
            f = []
            if p["age"] != d["PatientAge"]:
                f.append("age")
            if p["sex"].lower() != d["Gender"].lower():
                f.append("sex")
            if PN_TO_FS.get(p["rhythm_labels"], p["rhythm_labels"]) != d["Rhythm"]:
                f.append("rhythm")
            row["mismatch"] = "+".join(f)
            for x in f:
                mism[x] += 1
        align.append(row)
    with (OUT / "id_alignment.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(align[0]))
        w.writeheader()
        w.writerows(align)

    absent = [r for r in align if not r["in_part1"]]
    age_mm = [r for r in align if "age" in r["mismatch"]]
    rhy_mm = [r for r in align if "rhythm" in r["mismatch"]]

    # ---- U9: ventricular rate by rhythm label ----
    rate_rows = []
    for cls in ("SB", "SR", "ST", "SA", "AFIB", "AF"):
        v = [int(d["VentricularRate"]) for d in diag if d["Rhythm"] == cls]
        q = statistics.quantiles(v, n=20)
        rate_rows.append({"rhythm": cls, "n": len(v), "min": min(v), "p5": round(q[0], 1),
                          "median": statistics.median(v), "p95": round(q[-1], 1), "max": max(v),
                          "lt60": sum(x < 60 for x in v), "60to100": sum(60 <= x <= 100 for x in v),
                          "gt100": sum(x > 100 for x in v)})
    with (OUT / "rate_by_rhythm.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rate_rows[0]))
        w.writeheader()
        w.writerows(rate_rows)

    sinus = [d for d in diag if d["Rhythm"] in SINUS]
    disagree = Counter((d["Rhythm"], rate_rule(int(d["VentricularRate"])))
                       for d in sinus if rate_rule(int(d["VentricularRate"])) != d["Rhythm"])
    # same check restricted to the part-1 records (JS ids present)
    sinus_p1 = [d for k, d in enumerate(diag, 1) if k in pn and d["Rhythm"] in SINUS]

    summary = {
        "diagnostics_md5": md5,
        "diagnostics_rows": len(diag),
        "fs_rhythm_counts": dict(Counter(d["Rhythm"] for d in diag).most_common()),
        "SA_sex": dict(Counter(d["Gender"] for d in diag if d["Rhythm"] == "SA")),
        "part1_records": len(pn),
        "U1": {
            "rule": "JS id k is compared with Diagnostics.xlsx data row k (file order)",
            "part1_rows_with_age_sex_rhythm_all_equal": sum(1 for r in align if r["in_part1"] and not r["mismatch"]),
            "mismatch_counts_by_field": dict(mism),
            "age_mismatches_all_pn89_fs90plus": all(r["pn_age"] == "89" and int(r["fs_age"]) >= 90 for r in age_mm),
            "fs_ages_ge90_total": sum(int(d["PatientAge"]) >= 90 for d in diag),
            "rhythm_mismatch_pairs": {f"{a}->{b}": n for (a, b), n in Counter((r["pn_rhythm"], r["fs_rhythm"]) for r in rhy_mm).items()},
            "absent_ids": len(absent),
            "absent_ids_fs_rhythm": dict(Counter(r["fs_rhythm"] for r in absent)),
            "absent_ids_fs_sex": dict(Counter(r["fs_sex"] for r in absent)),
            "same_check_with_rows_sorted_by_FileName_all_equal": None,
        },
        "U9": {
            "rule": "rate_rule: VentricularRate < 60 -> SB, 60..100 -> SR, > 100 -> ST",
            "sinus_records_all_10646": len(sinus),
            "rule_agrees_all_10646": len(sinus) - sum(disagree.values()),
            "disagreements_label_to_rule": {f"{a}->{b}": n for (a, b), n in disagree.items()},
            "sinus_records_part1": len(sinus_p1),
            "rule_agrees_part1": sum(rate_rule(int(d["VentricularRate"])) == d["Rhythm"] for d in sinus_p1),
        },
    }
    # control: a different row order should NOT align
    srt = sorted(diag, key=lambda d: d["FileName"])
    summary["U1"]["same_check_with_rows_sorted_by_FileName_all_equal"] = sum(
        1 for k, d in enumerate(srt, 1) if k in pn
        and pn[k]["age"] == d["PatientAge"] and pn[k]["sex"].lower() == d["Gender"].lower()
        and PN_TO_FS.get(pn[k]["rhythm_labels"], pn[k]["rhythm_labels"]) == d["Rhythm"])
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
