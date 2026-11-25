#!/usr/bin/env python3
"""DRA repair: are the figshare ECGData signals the same signals as the
ecg-arrhythmia part-1 .mat files, and are the 399 SI records complete?

Pairing rule (established by src/figshare_check.py): JS id k <-> Diagnostics.xlsx
data row k <-> figshare ECGData/<FileName>.csv.

For every paired record this script loads both signals and records:
  * the least-squares scale s in csv ~= s * mat (all 12 leads pooled),
  * the max |csv - s0 * mat| for the modal scale s0,
  * whether the lead order agrees (per-lead correlation),
  * whether mat == round(csv) exactly, and whether csv values are integer
    multiples of 4.88 (the documented "volts per A/D bit", D8).
For the 399 SI rows (no part-1 file) it records shape, missing values and range.
It computes no features and fits no model.

Usage (from the repository root):
    python -I src/figshare_signal_check.py [--data-root ~/bme4191_ecg]
Expects <data-root>/figshare_chapman/ECGData/*.csv and the part-1 WFDB files.
Writes results/figshare_check/signal_match.csv and signal_summary.json.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.io as sio

ALIGN = Path("results/figshare_check/id_alignment.csv")
MANIFEST = Path("results/source_data/ecg_arrhythmia_parts.csv")
OUT = Path("results/figshare_check")
LEADS = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", default=str(Path.home() / "bme4191_ecg"))
    a = ap.parse_args()
    root = Path(a.data_root).expanduser()
    csv_dir = root / "figshare_chapman" / "ECGData"
    wfdb = root / "ecg-arrhythmia" / "1.0.0" / "WFDBRecords"
    folder = {r["record"]: r["folder"] for r in csv.DictReader(MANIFEST.open()) if r["part"] == "1"}
    align = list(csv.DictReader(ALIGN.open()))

    rows, header_seen = [], Counter()
    for i, r in enumerate(align):
        p = csv_dir / f"{r['FileName']}.csv"
        out = {"js_id": r["js_id"], "FileName": r["FileName"], "fs_rhythm": r["fs_rhythm"],
               "in_part1": r["in_part1"], "csv_exists": p.exists()}
        if p.exists():
            df = pd.read_csv(p)
            header_seen[tuple(df.columns)] += 1
            x = df.to_numpy(dtype=float)  # 5000 x 12
            k = x / 4.88
            out.update(csv_shape=f"{x.shape[0]}x{x.shape[1]}", csv_nan=int(np.isnan(x).sum()),
                       csv_min=float(np.nanmin(x)), csv_max=float(np.nanmax(x)),
                       csv_on_4p88_grid=bool(np.all(np.abs(k - np.round(k)) < 1e-6)))
            if r["in_part1"] == "True":
                m = sio.loadmat(wfdb / folder[r["js_id"]] / f"{r['js_id']}.mat")["val"].T.astype(float)
                mm = m.ravel()
                denom = float(mm @ mm)
                s = float(mm @ x.ravel() / denom) if denom else float("nan")
                out["scale_ls"] = s
                # 4.88*k never ends in .5 (88k mod 100 != 50), so rounding has no ties
                out["mat_equals_round_csv"] = bool(np.array_equal(m, np.round(x)))
                out["maxabs_resid_ls"] = float(np.max(np.abs(x - s * m))) if denom else float("nan")
                # per-lead correlation, same lead index
                cors = []
                for j in range(12):
                    sx, sm = x[:, j].std(), m[:, j].std()
                    cors.append(float(np.corrcoef(x[:, j], m[:, j])[0, 1]) if sx > 0 and sm > 0 else float("nan"))
                out["min_lead_corr"] = float(np.nanmin(cors)) if not all(np.isnan(cors)) else float("nan")
        rows.append(out)
        if i % 1000 == 0:
            print(f"{i}/{len(align)}", file=sys.stderr)

    keys = sorted({k for r in rows for k in r}, key=lambda k: list(rows[0]).index(k) if k in rows[0] else 99)
    with (OUT / "signal_match.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)

    paired = [r for r in rows if r["in_part1"] == "True" and r["csv_exists"]]
    scales = np.array([r["scale_ls"] for r in paired])
    s0 = float(np.median(scales))
    si = [r for r in rows if r["fs_rhythm"] == "SA"]
    summ = {
        "csv_files_found": sum(r["csv_exists"] for r in rows),
        "csv_headers": {",".join(k): n for k, n in header_seen.items()},
        "paired_records": len(paired),
        "scale_median": s0,
        "scale_min": float(scales.min()), "scale_max": float(scales.max()),
        "records_scale_within_1e-3_of_median": int(np.sum(np.abs(scales - s0) < 1e-3)),
        "maxabs_resid_ls_max": float(np.nanmax([r["maxabs_resid_ls"] for r in paired])),
        "records_maxabs_resid_ls_gt_1": sum(r["maxabs_resid_ls"] > 1 for r in paired),
        "records_min_lead_corr_lt_0.999": sum(not (r["min_lead_corr"] >= 0.999) for r in paired),
        "paired_mat_equals_round_csv": sum(r["mat_equals_round_csv"] for r in paired),
        "csv_on_4p88_grid_all": sum(r.get("csv_on_4p88_grid", False) for r in rows),
        "SI_rows": len(si),
        "SI_csv_on_4p88_grid": sum(r.get("csv_on_4p88_grid", False) for r in si),
        "SI_csv_found": sum(r["csv_exists"] for r in si),
        "SI_shapes": dict(Counter(r.get("csv_shape") for r in si)),
        "SI_with_nan": sum(r.get("csv_nan", 0) > 0 for r in si),
        "SI_range": [min(r["csv_min"] for r in si if r["csv_exists"]), max(r["csv_max"] for r in si if r["csv_exists"])],
        "all_shapes": dict(Counter(r.get("csv_shape") for r in rows)),
        "versions": {"python": sys.version.split()[0], "numpy": np.__version__, "pandas": pd.__version__},
    }
    (OUT / "signal_summary.json").write_text(json.dumps(summ, indent=2) + "\n")
    print(json.dumps(summ, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
