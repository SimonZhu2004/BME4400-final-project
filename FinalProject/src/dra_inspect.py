#!/usr/bin/env python3
"""Data Reality Audit inspection of ecg-arrhythmia 1.0.0, PART 1 ONLY
(Chapman-Shaoxing, the records with part == 1 in results/source_data/ecg_arrhythmia_parts.csv).

Describes what the released files contain; it fits nothing and computes no
features. Every number quoted as [O] in dra/DRA.md comes from the files this
script writes to results/dra/.

Refuses to run if any part-2 (Ningbo, protected) record is present under the
data root, and never opens a record that is not in part 1.

Usage (from the repository root):
    python -I src/dra_inspect.py [--data-root ~/bme4191_ecg] [--no-rehash]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import scipy
import scipy.io as sio

REPO = Path(__file__).resolve().parents[1]
MANIFEST = REPO / "results" / "source_data" / "ecg_arrhythmia_parts.csv"
OUT = REPO / "results" / "dra"

# Rhythm codes: the rows of ConditionNames_SNOMED-CT.csv whose names describe a rhythm
# (my grouping [I]; the CSV itself does not mark which codes are rhythms).
RHYTHM = {
    "426783006": "SR", "426177001": "SB", "427084000": "ST", "427393009": "SI(SA)",
    "164889003": "AFIB", "164890007": "AFL(AF)", "426761007": "SVT", "713422000": "AT",
    "233896004": "AVNRT", "233897008": "AVRT", "195101003": "SAAWR/WAVN",
}
SIX = ["SR", "SB", "ST", "SI(SA)", "AFIB", "AFL(AF)"]
INT16_MIN, INT16_MAX = -32768, 32767


def sha256_of(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_header(p: Path) -> dict:
    lines = p.read_text().splitlines()
    rec = lines[0].split()
    h = {"record_line": rec, "signals": [], "comments": {}, "other": []}
    for ln in lines[1:]:
        if ln.startswith("#"):
            m = re.match(r"#\s*([^:]+):\s*(.*)$", ln)
            if m:
                h["comments"][m.group(1).strip()] = m.group(2).strip()
            else:
                h["other"].append(ln)
        elif ln.strip():
            f = ln.split()
            h["signals"].append({"file": f[0], "fmt": f[1], "gain": f[2], "adc_res": f[3], "adc_zero": f[4],
                                 "init": int(f[5]), "checksum": int(f[6]), "block": f[7],
                                 "lead": f[8] if len(f) > 8 else ""})
    return h


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default=str(Path.home() / "bme4191_ecg"))
    ap.add_argument("--no-rehash", action="store_true", help="skip re-verifying file checksums")
    a = ap.parse_args()
    root = Path(a.data_root).expanduser().resolve() / "ecg-arrhythmia" / "1.0.0"

    part = {}
    with MANIFEST.open(newline="") as f:
        for r in csv.DictReader(f):
            part[r["record"]] = (int(r["part"]), r["folder"])
    present = {p.stem for p in (root / "WFDBRecords").rglob("JS*.*")}
    leaked = sorted(r for r in present if part.get(r, (0,))[0] != 1)
    if leaked:
        sys.exit(f"STOP: {len(leaked)} non-part-1 records present under {root} (e.g. {leaked[:3]})")
    recs = sorted((r for r, (pt, _) in part.items() if pt == 1), key=lambda r: int(r[2:]))

    sums = dict((p[1].strip(), p[0]) for p in (ln.split(maxsplit=1) for ln in
                (root / "SHA256SUMS.txt").read_text().splitlines()) if len(p) == 2)
    S: dict = {"data_root": str(root), "n_part1_records_in_manifest": len(recs),
               "versions": {"python": sys.version.split()[0], "numpy": np.__version__, "scipy": scipy.__version__}}

    # --- files present / integrity
    missing, bad_hash = [], []
    for r in recs:
        for ext in ("hea", "mat"):
            rel = f"WFDBRecords/{part[r][1]}/{r}.{ext}"
            p = root / rel
            if not p.exists():
                missing.append(rel)
            elif not a.no_rehash and sha256_of(p) != sums[rel]:
                bad_hash.append(rel)
    S["files_missing"] = missing
    S["files_checksum_mismatch"] = bad_hash if not a.no_rehash else "not checked"
    ids = [int(r[2:]) for r in recs]
    S["id_range"] = [f"JS{min(ids):05d}", f"JS{max(ids):05d}"]
    S["ids_absent_in_range"] = max(ids) - min(ids) + 1 - len(ids)

    # --- RECORDS files
    folder_recs = defaultdict(list)
    for r in recs:
        folder_recs[part[r][1]].append(r)
    rec_mismatch = []
    for folder, rs in folder_recs.items():
        rf = root / "WFDBRecords" / folder / "RECORDS"
        if rf.exists():
            listed = [x.strip() for x in rf.read_text().splitlines() if x.strip()]
            if sorted(listed) != sorted(rs):
                rec_mismatch.append(folder)
    S["folder_RECORDS_not_matching_files"] = rec_mismatch
    S["folders_without_RECORDS_downloaded"] = sorted(f for f in folder_recs
                                                    if not (root / "WFDBRecords" / f / "RECORDS").exists())

    # --- condition table
    cond_rows = list(csv.DictReader((root / "ConditionNames_SNOMED-CT.csv").open(encoding="utf-8-sig")))
    code_to_acr = defaultdict(list)
    for row in cond_rows:
        code_to_acr[row["Snomed_CT"].strip()].append(row["Acronym Name"].strip())
    S["condition_table_rows"] = len(cond_rows)
    S["condition_table_distinct_codes"] = len(code_to_acr)
    S["condition_codes_shared_by_several_acronyms"] = {c: v for c, v in code_to_acr.items() if len(v) > 1}

    # --- per-record headers and signals
    table, hdr_issues, sig_issues = [], Counter(), Counter()
    rec_lines, gains, fmts, units_res, lead_orders, extra_comment_keys = Counter(), Counter(), Counter(), Counter(), Counter(), Counter()
    rx = Counter(); hx = Counter(); sx = Counter()
    mat_hash_to_recs = defaultdict(list)
    gmin, gmax = INT16_MAX, INT16_MIN
    flat_leads_per_rec, zero_leads_per_rec, sat_recs = Counter(), Counter(), 0
    flat_lead_names = Counter()
    malformed, base_time_recs = [], []
    for r in recs:
        folder = part[r][1]
        h = parse_header(root / "WFDBRecords" / folder / f"{r}.hea")
        rl = h["record_line"]
        rec_ok = len(rl) >= 4 and all(x.isdigit() for x in rl[1:4])
        if not rec_ok:
            hdr_issues["malformed_record_line"] += 1
            malformed.append({"record": r, "record_line": " ".join(rl), "n_signal_lines": len(h["signals"])})
            rec_lines["<malformed>"] += 1
        else:
            rec_lines[" ".join(rl[1:4])] += 1
            if len(rl) > 4:
                base_time_recs.append(r)
        if rl[0] != r:
            hdr_issues["record_name_mismatch"] += 1
        sigs = h["signals"]
        lead_orders[",".join(s["lead"] for s in sigs)] += 1
        for s in sigs:
            gains[s["gain"]] += 1; fmts[s["fmt"]] += 1; units_res[(s["adc_res"], s["adc_zero"], s["block"])] += 1
            if s["file"] != f"{r}.mat":
                hdr_issues["signal_file_name_mismatch"] += 1
        c = h["comments"]
        for k in c:
            if k not in {"Age", "Sex", "Dx", "Rx", "Hx", "Sx"}:
                extra_comment_keys[k] += 1
        if h["other"]:
            hdr_issues["unparsed_comment_lines"] += 1
        rx[c.get("Rx", "<absent>")] += 1; hx[c.get("Hx", "<absent>")] += 1; sx[c.get("Sx", "<absent>")] += 1
        dx = [d.strip() for d in c.get("Dx", "").split(",") if d.strip()]

        m = sio.loadmat(root / "WFDBRecords" / folder / f"{r}.mat")
        keys = [k for k in m if not k.startswith("__")]
        v = m.get("val")
        flags = []
        if keys != ["val"] or v is None:
            sig_issues["unexpected_mat_variables"] += 1; flags.append("mat_vars")
            v = np.zeros((0, 0), dtype=np.int16)
        shape = list(v.shape)
        if v.size:
            if v.dtype != np.int16:
                sig_issues["dtype_not_int16"] += 1
            n_sig, n_samp = (int(rl[1]), int(rl[3])) if rec_ok else (12, 5000)
            if v.shape != (n_sig, n_samp):
                sig_issues["shape_differs_from_header"] += 1; flags.append("shape")
            vi = v.astype(np.int64)
            if not rec_ok:
                flags.append("malformed_header")
            elif any(int(vi[i, 0]) != s["init"] for i, s in enumerate(sigs[:v.shape[0]])):
                sig_issues["first_sample_differs_from_header_init"] += 1; flags.append("init")
            cks = [((int(vi[i].sum()) + 32768) % 65536) - 32768 for i in range(v.shape[0])]
            if rec_ok and any((cks[i] - s["checksum"]) % 65536 for i, s in enumerate(sigs[:v.shape[0]])):
                sig_issues["checksum_differs_from_header"] += 1; flags.append("checksum")
            if rec_ok and any(cks[i] != s["checksum"] and (cks[i] - s["checksum"]) % 65536 == 0
                              for i, s in enumerate(sigs[:v.shape[0]])):
                hdr_issues["checksum_written_unsigned(+32768_for_-32768)"] += 1; flags.append("checksum_unsigned_notation")
            if False:
                sig_issues["checksum_differs_from_header"] += 1; flags.append("checksum")
            gmin, gmax = min(gmin, int(v.min())), max(gmax, int(v.max()))
            flat = [i for i in range(v.shape[0]) if v[i].min() == v[i].max()]
            zero = [i for i in range(v.shape[0]) if not v[i].any()]
            flat_leads_per_rec[len(flat)] += 1; zero_leads_per_rec[len(zero)] += 1
            names = [s["lead"] for s in sigs] if rec_ok else ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]
            for i in flat:
                flat_lead_names[names[i]] += 1
            if flat:
                flags.append(f"flat:{len(flat)}")
            if (v == INT16_MIN).any() or (v == INT16_MAX).any():
                sat_recs += 1; flags.append("int16_extreme")
        mat_hash_to_recs[sums[f"WFDBRecords/{folder}/{r}.mat"]].append(r)

        rhythms = [RHYTHM[d] for d in dx if d in RHYTHM]
        table.append({"record": r, "folder": folder, "age": c.get("Age", ""), "sex": c.get("Sex", ""),
                      "dx": ";".join(dx), "n_dx": len(dx), "rhythm_labels": ";".join(rhythms),
                      "n_rhythm": len(rhythms), "n_sig": rl[1] if rec_ok else "", "fs": rl[2] if rec_ok else "",
                      "n_samp": rl[3] if rec_ok else "", "base_time_date": " ".join(rl[4:]) if rec_ok else "",
                      "mat_shape": "x".join(map(str, shape)), "flags": ";".join(flags)})

    S["header_record_line_variants(n_sig fs n_samp)"] = dict(rec_lines)
    S["header_issues"] = dict(hdr_issues)
    S["malformed_headers"] = malformed
    S["records_with_base_time_date"] = len(base_time_recs)
    S["base_time_date_records_folders"] = dict(Counter(part[r][1] for r in base_time_recs))
    S["base_time_date_values_min_max"] = (lambda v: [min(v), max(v)] if v else [])(
        sorted(t["base_time_date"] for t in table if t["base_time_date"]))
    S["lead_orders"] = dict(lead_orders)
    S["gain_field_values"] = dict(gains)
    S["fmt_field_values"] = dict(fmts)
    S["adc_res_zero_block_values"] = {" ".join(k): n for k, n in units_res.items()}
    S["extra_comment_keys"] = dict(extra_comment_keys)
    S["Rx_values"], S["Hx_values"], S["Sx_values"] = dict(rx.most_common(10)), dict(hx.most_common(10)), dict(sx.most_common(10))
    S["signal_issues"] = dict(sig_issues)
    S["signal_global_min_max_adu"] = [gmin, gmax]
    S["records_by_n_flat_leads"] = {str(k): n for k, n in sorted(flat_leads_per_rec.items())}
    S["records_by_n_all_zero_leads"] = {str(k): n for k, n in sorted(zero_leads_per_rec.items())}
    S["flat_lead_counts_by_lead"] = dict(flat_lead_names)
    S["records_with_int16_extreme_values"] = sat_recs
    dups = [v for v in mat_hash_to_recs.values() if len(v) > 1]
    S["groups_of_byte_identical_mat_files"] = len(dups)
    S["records_in_byte_identical_groups"] = sum(len(v) for v in dups)
    S["byte_identical_mat_examples"] = dups[:10]

    # --- demographics
    ages_raw = Counter(t["age"] for t in table)
    ages = [int(t["age"]) for t in table if re.fullmatch(r"\d+", t["age"])]
    S["age_non_integer_values"] = {k: n for k, n in ages_raw.items() if not re.fullmatch(r"\d+", k)}
    S["age_n_integer"] = len(ages)
    S["age_min_median_max"] = [min(ages), statistics.median(ages), max(ages)]
    S["age_quartiles"] = [float(q) for q in np.percentile(ages, [25, 50, 75])]
    S["age_lt_18"] = sum(x < 18 for x in ages)
    S["age_ge_90"] = sum(x >= 90 for x in ages)
    S["sex_values"] = dict(Counter(t["sex"] for t in table))

    # --- labels
    code_recs = Counter(d for t in table for d in set(t["dx"].split(";")) if d)
    S["records_with_empty_Dx"] = sum(1 for t in table if not t["dx"])
    S["records_with_repeated_code_in_Dx"] = sum(1 for t in table if t["dx"] and len(t["dx"].split(";")) != len(set(t["dx"].split(";"))))
    S["distinct_Dx_codes"] = len(code_recs)
    S["Dx_codes_not_in_condition_table"] = {c: n for c, n in code_recs.items() if c not in code_to_acr}
    S["n_dx_per_record"] = {str(k): n for k, n in sorted(Counter(t["n_dx"] for t in table).items())}
    S["n_rhythm_labels_per_record"] = {str(k): n for k, n in sorted(Counter(t["n_rhythm"] for t in table).items())}
    single = Counter(t["rhythm_labels"] for t in table if t["n_rhythm"] == 1)
    S["records_with_exactly_one_rhythm_label_by_label"] = dict(single.most_common())
    S["six_class_single_label_total"] = sum(single[c] for c in SIX)
    S["records_without_rhythm_code_by_dx"] = dict(Counter(t["dx"] for t in table if t["n_rhythm"] == 0).most_common())
    combos = Counter(t["rhythm_labels"] for t in table if t["n_rhythm"] > 1)
    S["multi_rhythm_label_combinations"] = dict(combos.most_common())

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "dra_summary.json").write_text(json.dumps(S, indent=2, default=str))
    with (OUT / "dx_code_counts.csv").open("w", newline="") as f:
        w = csv.writer(f); w.writerow(["snomed_ct", "acronyms", "is_rhythm_code", "n_records", "pct_records"])
        for code, n in code_recs.most_common():
            w.writerow([code, "|".join(code_to_acr.get(code, ["<not in table>"])), code in RHYTHM, n, round(100 * n / len(table), 2)])
    rh = list(RHYTHM.values())
    co = {a_: Counter() for a_ in rh}
    for t in table:
        labs = [x for x in t["rhythm_labels"].split(";") if x]
        for a_ in labs:
            for b in labs:
                co[a_][b] += 1
    with (OUT / "rhythm_cooccurrence.csv").open("w", newline="") as f:
        w = csv.writer(f); w.writerow(["label"] + rh)
        for a_ in rh:
            w.writerow([a_] + [co[a_][b] for b in rh])
    with (OUT / "record_table_part1.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(table[0])); w.writeheader(); w.writerows(table)
    print(json.dumps({k: S[k] for k in ["files_missing", "files_checksum_mismatch", "signal_issues", "header_issues",
                                        "n_rhythm_labels_per_record", "six_class_single_label_total"]}, default=str))
    print(f"wrote {OUT.relative_to(REPO)}/: dra_summary.json, dx_code_counts.csv, rhythm_cooccurrence.csv, record_table_part1.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
