"""QC of the development feature tables (PRD §4 item 5, §12). Development data only.

    python src/feature_qc.py        # after: python src/features.py --split dev

Writes results/features/qc_dev.json:
  * hr_check: share of units with |hr - VentricularRate| <= 5 bpm at T = 10 s, overall and per class
    (PRD §4 item 5 requires >= 0.95), plus the same with 60 / median RR for comparison;
  * r_peaks: units with < 2 and < 3 R peaks per window;
  * nan_share: share of NaN per feature and window;
  * class_medians: median of every feature per class and window.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ecg_io  # noqa: E402
import features as F  # noqa: E402


def main() -> int:
    root = ecg_io.DEFAULT_DATA_ROOT
    d = root / "derived" / "features"
    tables = {T: pd.read_csv(d / f"features_dev_T{T}.csv") for T in F.WINDOWS}
    manifest = json.loads((ecg_io.REPO / "results" / "features" / "manifest_dev.json").read_text())
    for T, t in tables.items():
        if ecg_io.sha256_file(d / f"features_dev_T{T}.csv") != manifest["files"][f"T{T}"]["sha256"]:
            raise SystemExit(f"features_dev_T{T}.csv does not match manifest_dev.json; rerun src/features.py")

    diag = ecg_io.read_diagnostics(root)
    vr = {f"JS{k:05d}": float(r["VentricularRate"]) for k, r in enumerate(diag, 1)}
    t10 = tables[10]
    ok = (t10["hr"] - t10["record"].map(vr)).abs() <= 5
    qc = {
        "hr_check": {
            "definition": "hr = 60000 / mean RR (lead II, neurokit detector), T = 10 s; pass if share >= 0.95",
            "overall": round(float(ok.mean()), 4),
            "passes_0.95": bool(ok.mean() >= 0.95),
            "by_class": {k: round(float(v), 4) for k, v in ok.groupby(t10["label"]).mean().items()},
            "n_units": int(len(ok)), "n_hr_nan": int(t10["hr"].isna().sum()),
        },
        "r_peaks": {f"T{T}": {"lt2": int((t.meta_n_rpeaks < 2).sum()), "lt3": int((t.meta_n_rpeaks < 3).sum())}
                    for T, t in tables.items()},
        "nan_share": {f"T{T}": {k: round(float(t[k].isna().mean()), 4) for k in F.FEATURES} for T, t in tables.items()},
        "class_medians": {f"T{T}": {lab: {k: (None if np.isnan(v) else round(float(v), 4)) for k, v in g.items()}
                                    for lab, g in t.groupby("label")[F.FEATURES].median().iterrows()}
                          for T, t in tables.items()},
    }
    out = ecg_io.REPO / "results" / "features" / "qc_dev.json"
    out.write_text(json.dumps(qc, indent=2) + "\n")
    print(json.dumps(qc["hr_check"], indent=2))
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
