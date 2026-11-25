"""Build the Shaoxing unit list, the 80/20 split and the 5 development folds (PRD §5 A1-A2).

Run from the repository root, in the bme4400-final environment:
    python src/make_split.py [--data-root ~/bme4191_ecg]

Reads only Diagnostics.xlsx, the figshare ECGData CSVs of the SI records, the
part-1 .mat files and the parts manifest. Computes no features.

Writes results/splits/:
    shaoxing_units.csv       record, label, code, source, signal_sha256  (9,887 rows)
    shaoxing_test_ids.csv    record, label, code                          (20%)
    shaoxing_dev_folds.csv   record, label, code, fold                    (80%)
    split_summary.json       counts per class for every step, split and fold
    SHA256SUMS               hashes of the three CSV files

Every count in VCM v2 §8.1 is asserted; the script stops if one differs.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
from sklearn.model_selection import StratifiedKFold, train_test_split

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ecg_io  # noqa: E402

SEED = 4400
OUT = ecg_io.REPO / "results" / "splits"

# VCM v2 §8.1
EXPECT_SIX_CLASS = 9907
EXPECT_AFTER_DUP = 9901  # 13 part-1 pairs (DRA O10): 5 in the six classes; plus 1 SI pair, JS02561 = JS04771
EXPECT_UNITS = {"SB": 3888, "SR": 1825, "AFIB": 1778, "ST": 1562, "AFL": 438, "SI": 396}


def check(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(f"CHECK FAILED: {msg}")
    print(f"[ok] {msg}")


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default=str(ecg_io.DEFAULT_DATA_ROOT))
    root = Path(ap.parse_args().data_root).expanduser()

    manifest = ecg_io.read_parts_manifest()
    diag = ecg_io.read_diagnostics(root)
    check(len(diag) == 10646, f"Diagnostics.xlsx has 10,646 rows ({len(diag)})")

    # Step 1-2: row k = JSk; keep the six rhythms
    units = []
    for k, row in enumerate(diag, start=1):
        rhythm = row["Rhythm"]
        if rhythm in ecg_io.FIGSHARE_RHYTHM:
            units.append({"record": f"JS{k:05d}", "label": ecg_io.FIGSHARE_RHYTHM[rhythm],
                          "file_name": row["FileName"]})
    check(len(units) == EXPECT_SIX_CLASS, f"six-class rows = {EXPECT_SIX_CLASS} ({len(units)})")

    # Load every signal: part 1 from .mat, SI (not in part 1) from figshare CSV
    for i, u in enumerate(units):
        m = manifest.get(u["record"])
        if m is not None and m["part"] == "1":
            sig, u["source"] = ecg_io.load_part1_signal(root, u["record"], m["folder"]), "physionet_part1"
        else:
            sig, u["source"] = ecg_io.load_figshare_signal(root, u["file_name"]), "figshare_csv"
        if sig.shape != (12, 5000):
            raise SystemExit(f"{u['record']}: signal shape {sig.shape}, expected (12, 5000)")
        u["signal_sha256"] = ecg_io.signal_sha256(sig)
        u["zero_lead"] = bool((~sig.any(axis=1)).any())
        if i % 1000 == 0:
            print(f"  loaded {i}/{len(units)}", file=sys.stderr)
    src = Counter((u["label"], u["source"]) for u in units)
    check(all(s == "figshare_csv" for (lab, s) in src if lab == "SI")
          and all(s == "physionet_part1" for (lab, s) in src if lab != "SI"),
          "SI records come from figshare, all others from PhysioNet part 1")

    # Step 3: identical signals -> keep the lower JS id (units are in JS order)
    seen, kept = set(), []
    for u in units:
        if u["signal_sha256"] in seen:
            continue
        seen.add(u["signal_sha256"])
        kept.append(u)
    check(len(kept) == EXPECT_AFTER_DUP, f"after duplicate removal = {EXPECT_AFTER_DUP} ({len(kept)})")

    # Step 4: drop records with any all-zero lead
    final = [u for u in kept if not u["zero_lead"]]
    counts = Counter(u["label"] for u in final)
    check(dict(counts) == EXPECT_UNITS, f"final class counts = {EXPECT_UNITS} ({dict(counts)})")

    # Split: sorted by JS id, stratified by label (PRD §3)
    final.sort(key=lambda u: u["record"])
    for u in final:
        u["code"] = ecg_io.CLASS_CODE[u["label"]]
    idx = np.arange(len(final))
    y = np.array([u["code"] for u in final])
    dev_idx, test_idx = train_test_split(idx, test_size=0.2, stratify=y, random_state=SEED)
    dev = sorted((final[i] for i in dev_idx), key=lambda u: u["record"])
    test = sorted((final[i] for i in test_idx), key=lambda u: u["record"])

    # Folds on the development set, sorted by JS id (PRD §5 A2)
    y_dev = np.array([u["code"] for u in dev])
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    for fold, (_, va) in enumerate(skf.split(np.zeros(len(dev)), y_dev)):
        for i in va:
            dev[i]["fold"] = fold

    # Label proportions must match across splits and folds (within one record per class)
    def by_class(rows):
        c = Counter(u["label"] for u in rows)
        return {k: c.get(k, 0) for k in ecg_io.CLASSES}

    total = by_class(final)
    for name, rows, frac in [("test", test, 0.2), ("dev", dev, 0.8)]:
        got = by_class(rows)
        check(all(abs(got[k] - total[k] * frac) <= 1 for k in ecg_io.CLASSES),
              f"{name} class counts within 1 of {frac:.0%} of each class {got}")
    fold_counts = {f: by_class([u for u in dev if u["fold"] == f]) for f in range(5)}
    dev_total = by_class(dev)
    check(all(abs(fold_counts[f][k] - dev_total[k] / 5) <= 1 for f in range(5) for k in ecg_io.CLASSES),
          "every fold within 1 record of 1/5 of each development class")
    check(not ({u["record"] for u in dev} & {u["record"] for u in test}), "no record in both dev and test")
    check(len({u["signal_sha256"] for u in final}) == len(final), "all unit signals distinct")

    OUT.mkdir(parents=True, exist_ok=True)
    write_csv(OUT / "shaoxing_units.csv", final, ["record", "label", "code", "source", "signal_sha256"])
    write_csv(OUT / "shaoxing_test_ids.csv", test, ["record", "label", "code"])
    write_csv(OUT / "shaoxing_dev_folds.csv", dev, ["record", "label", "code", "fold"])

    dropped_dup = sorted({u["record"] for u in units} - {u["record"] for u in kept})
    dropped_zero = sorted(u["record"] for u in kept if u["zero_lead"])
    summary = {
        "seed": SEED,
        "steps": {"six_class_rows": len(units), "after_duplicates": len(kept), "units": len(final)},
        "dropped_duplicates": dropped_dup,
        "dropped_zero_lead": dropped_zero,
        "class_counts": {"all": total, "dev": dev_total, "test": by_class(test)},
        "fold_counts": {str(f): c for f, c in fold_counts.items()},
        "versions": {"python": sys.version.split()[0], "numpy": np.__version__,
                     "scikit-learn": __import__("sklearn").__version__},
    }
    (OUT / "split_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    sums = "".join(f"{ecg_io.sha256_file(OUT / n)}  {n}\n"
                   for n in ["shaoxing_units.csv", "shaoxing_test_ids.csv", "shaoxing_dev_folds.csv"])
    (OUT / "SHA256SUMS").write_text(sums)
    print(sums, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
