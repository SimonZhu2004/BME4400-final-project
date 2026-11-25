"""Feature table for the BME4400 final project (PRD §5 step A3).

For every unit and every window T in {2, 4, 6, 8, 10} s, the crop is the first
T s of the 12-lead record (samples [0, 500*T)). Every step below uses only the
crop. One row per unit and window, 16 features (FEATURES, fixed order).

Run from the repository root, in the bme4400-final environment:
    python src/features.py --split dev             # 7,909 development units (Stage A)
    python src/features.py --split test            # 1,978 test units (Stage B only; PRD §5 B3)
Options: --windows 2 4 6 8 10, --workers N, --limit N (first N units, for timing),
--data-root ~/bme4191_ecg, --out DIR (default results/features/tables/ in the repository).

Writes, in the repository (PRD amendment 6):
    results/features/tables/features_<split>_T<T>.csv   record, label, code, [fold], meta_n_rpeaks, 16 features
    results/features/feature_list.json
    results/features/manifest_<split>.json   file hashes, row counts, NaN counts per feature, versions
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import platform
import subprocess
import sys
import time
import warnings
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from scipy.signal import welch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ecg_io  # noqa: E402

FS = 500                      # Hz, every record (DRA O11)
WINDOWS = [2, 4, 6, 8, 10]    # s, PRD §3
LEAD = {"II": 1, "V1": 6}     # row index in the 12 x 5000 array (order I, II, III, aVR, aVL, aVF, V1-V6)
P_REGION_MS = (250, 60)       # P-wave region: from 250 ms to 60 ms before each R peak
MASK_MS = 120                 # QRS mask for the atrial spectrum, centred on each R peak
NPERSEG_MAX = 1000            # Welch segment length cap (2 s)

FEATURES = (
    ["hr", "rr_sdnn", "rr_rmssd", "rr_pnn50", "rr_range", "rr_cv"]
    + [f"p_consistency_{l}" for l in LEAD]
    + [f"{f}_{l}" for l in LEAD for f in ("af_power_ratio", "af_dom_freq", "af_peak_ratio")]
    + [f"r_amp_{l}" for l in LEAD]
)
assert len(FEATURES) == 16

FEATURE_DOC = {
    "hr": "60000 / mean RR (ms), lead II R peaks; NaN if < 2 R peaks",
    "rr_sdnn": "SD of RR intervals (ms, ddof=1); NaN if < 3 R peaks",
    "rr_rmssd": "root mean square of successive RR differences (ms); NaN if < 3 R peaks",
    "rr_pnn50": "fraction of successive RR differences > 50 ms; NaN if < 3 R peaks",
    "rr_range": "max RR - min RR (ms); NaN if < 3 R peaks",
    "rr_cv": "rr_sdnn / mean RR; NaN if < 3 R peaks",
    "p_consistency": "median Pearson correlation, over all pairs of beats, of the cleaned signal from 250 ms to "
                     "60 ms before each lead-II R peak (beats whose region starts before the crop are skipped); "
                     "NaN if < 2 such beats",
    "af_power_ratio": "Welch power 4-9 Hz / power 1-40 Hz after masking 120 ms around each R peak",
    "af_dom_freq": "frequency of maximum Welch power in 3-12 Hz (Hz), same masked signal",
    "af_peak_ratio": "max Welch power in 4-6 Hz / median Welch power in 3-12 Hz, same masked signal",
    "r_amp": "median cleaned amplitude at the lead-II R peak times (µV); NaN if no R peak",
}


def _quiet() -> None:
    warnings.filterwarnings("ignore")


def r_peaks(clean_ii: np.ndarray) -> np.ndarray:
    import neurokit2 as nk
    try:
        r = nk.ecg_peaks(clean_ii, sampling_rate=FS, method="neurokit")[1]["ECG_R_Peaks"]
    except Exception:
        return np.array([], dtype=int)
    return np.asarray(r, dtype=int)


def rr_features(r: np.ndarray) -> dict[str, float]:
    f = dict.fromkeys(FEATURES[:6], np.nan)
    rr = np.diff(r) / FS * 1000.0  # ms
    if len(r) >= 2:
        f["hr"] = 60000.0 / float(np.mean(rr))
    if len(r) >= 3:
        d = np.diff(rr)
        f.update(rr_sdnn=float(np.std(rr, ddof=1)), rr_rmssd=float(np.sqrt(np.mean(d ** 2))),
                 rr_pnn50=float(np.mean(np.abs(d) > 50)), rr_range=float(rr.max() - rr.min()),
                 rr_cv=float(np.std(rr, ddof=1) / np.mean(rr)))
    return f


def p_consistency(x: np.ndarray, r: np.ndarray) -> float:
    """Median pairwise correlation of the P-wave region across beats (high in sinus rhythm, ~0 in AFIB)."""
    a, b = (int(round(ms / 1000 * FS)) for ms in P_REGION_MS)
    segs = np.array([x[ri - a: ri - b] for ri in r if ri - a >= 0])
    if len(segs) < 2:
        return np.nan
    segs = segs[segs.std(axis=1) > 0]
    if len(segs) < 2:
        return np.nan
    c = np.corrcoef(segs)
    return float(np.median(c[np.triu_indices(len(segs), 1)]))


def spectrum_features(x: np.ndarray, r: np.ndarray, lead: str) -> dict[str, float]:
    f = {f"{k}_{lead}": np.nan for k in ("af_power_ratio", "af_dom_freq", "af_peak_ratio")}
    y = x.astype(float).copy()
    half = int(round(MASK_MS / 2 / 1000 * FS))
    for ri in r:
        a, b = max(ri - half, 0), min(ri + half, len(y) - 1)
        left = y[a - 1] if a > 0 else y[b]
        right = y[b] if b < len(y) - 1 else left
        y[a:b + 1] = np.linspace(left, right, b - a + 1)
    freq, p = welch(y, fs=FS, nperseg=min(NPERSEG_MAX, len(y)))
    band = lambda lo, hi: (freq >= lo) & (freq <= hi)
    total = p[band(1, 40)].sum()
    if total <= 0:
        return f
    f[f"af_power_ratio_{lead}"] = float(p[band(4, 9)].sum() / total)
    m = band(3, 12)
    f[f"af_dom_freq_{lead}"] = float(freq[m][np.argmax(p[m])])
    med = float(np.median(p[m]))
    f[f"af_peak_ratio_{lead}"] = float(p[band(4, 6)].max() / med) if med > 0 else np.nan
    return f


def crop(sig: np.ndarray, T: int) -> np.ndarray:
    """First T seconds: samples [0, 500*T) of every lead (PRD §3)."""
    n = FS * T
    if sig.shape[1] < n:
        raise ValueError(f"record has {sig.shape[1]} samples, crop needs {n}")
    return sig[:, :n]


def crop_features(sig12: np.ndarray, T: int) -> dict[str, float]:
    """All 16 features of one crop. Uses only crop(sig12, T)."""
    import neurokit2 as nk
    c = crop(sig12, T).astype(float)
    clean = {l: nk.ecg_clean(c[i], sampling_rate=FS, method="neurokit") for l, i in LEAD.items()}
    r = r_peaks(clean["II"])  # one set of R peaks, lead II, used for both leads
    out = {"meta_n_rpeaks": len(r)}
    out.update(rr_features(r))
    for l in LEAD:
        out[f"p_consistency_{l}"] = p_consistency(clean[l], r)
        out.update(spectrum_features(clean[l], r, l))
        out[f"r_amp_{l}"] = float(np.median(clean[l][r])) if len(r) else np.nan
    return {k: out[k] for k in ["meta_n_rpeaks"] + FEATURES}


# ---------------------------------------------------------------- driver

def _work(task):
    unit, root, windows = task
    if unit["source"] == "physionet_part1":
        sig = ecg_io.load_part1_signal(root, unit["record"], unit["folder"])
    else:
        sig = ecg_io.load_figshare_signal(root, unit["file_name"])
    if ecg_io.signal_sha256(sig) != unit["signal_sha256"]:
        raise RuntimeError(f"{unit['record']}: signal hash differs from results/splits/shaoxing_units.csv")
    return unit["record"], {T: crop_features(sig, T) for T in windows}


def _git_commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True,
                              cwd=ecg_io.REPO).stdout.strip()
    except Exception:
        return "unknown"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["dev", "test"], required=True)
    ap.add_argument("--windows", type=int, nargs="+", default=WINDOWS)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--limit", type=int, default=None, help="first N units only (timing runs; no manifest)")
    ap.add_argument("--data-root", default=str(ecg_io.DEFAULT_DATA_ROOT))
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    root = Path(a.data_root).expanduser()
    out = Path(a.out).expanduser() if a.out else ecg_io.REPO / "results" / "features" / "tables"
    out.mkdir(parents=True, exist_ok=True)
    if not set(a.windows) <= set(WINDOWS):
        raise SystemExit(f"windows must be among {WINDOWS}")

    # Units of this split, with what is needed to load each signal
    splits = ecg_io.REPO / "results" / "splits"
    units = {u["record"]: u for u in csv.DictReader((splits / "shaoxing_units.csv").open())}
    fname = "shaoxing_dev_folds.csv" if a.split == "dev" else "shaoxing_test_ids.csv"
    rows = list(csv.DictReader((splits / fname).open()))
    manifest = ecg_io.read_parts_manifest()
    diag = ecg_io.read_diagnostics(root)
    for r in rows:
        u = units[r["record"]]
        r["source"], r["signal_sha256"] = u["source"], u["signal_sha256"]
        r["folder"] = manifest[r["record"]]["folder"] if u["source"] == "physionet_part1" else ""
        r["file_name"] = diag[int(r["record"][2:]) - 1]["FileName"]
    if a.limit:
        rows = rows[: a.limit]

    t0 = time.time()
    tasks = [(r, root, a.windows) for r in rows]
    results = {}
    with Pool(a.workers, initializer=_quiet) as pool:
        for i, (rec, feats) in enumerate(pool.imap_unordered(_work, tasks, chunksize=8), 1):
            results[rec] = feats
            if i % 500 == 0 or i == len(tasks):
                print(f"  {i}/{len(tasks)} units, {time.time() - t0:.0f} s", file=sys.stderr)
    elapsed = time.time() - t0

    key_cols = ["record", "label", "code"] + (["fold"] if a.split == "dev" else [])
    files = {}
    for T in a.windows:
        path = out / f"features_{a.split}_T{T}.csv"
        with path.open("w", newline="") as fh:
            w = csv.writer(fh, lineterminator="\n")
            w.writerow(key_cols + ["meta_n_rpeaks"] + FEATURES)
            for r in sorted(rows, key=lambda r: r["record"]):
                f = results[r["record"]][T]
                w.writerow([r[k] for k in key_cols] + [f["meta_n_rpeaks"]]
                           + ["" if np.isnan(f[k]) else repr(float(f[k])) for k in FEATURES])
        nan_counts = {k: int(sum(np.isnan(results[r["record"]][T][k]) for r in rows)) for k in FEATURES}
        shown = path.resolve().relative_to(ecg_io.REPO.resolve()) if path.resolve().is_relative_to(ecg_io.REPO.resolve()) else path
        files[f"T{T}"] = {"path": str(shown), "sha256": ecg_io.sha256_file(path), "rows": len(rows),
                          "nan_counts": nan_counts,
                          "rpeaks_lt2": sum(results[r["record"]][T]["meta_n_rpeaks"] < 2 for r in rows),
                          "rpeaks_lt3": sum(results[r["record"]][T]["meta_n_rpeaks"] < 3 for r in rows)}
    print(f"done: {len(rows)} units x {len(a.windows)} windows in {elapsed:.0f} s with {a.workers} workers")

    feat_dir = ecg_io.REPO / "results" / "features"
    feat_dir.mkdir(parents=True, exist_ok=True)
    (feat_dir / "feature_list.json").write_text(json.dumps(
        {"features": FEATURES, "definitions": FEATURE_DOC, "leads": list(LEAD), "fs": FS,
         "crop": "first T s, samples [0, 500*T)", "windows": WINDOWS,
         "cleaning": "neurokit2.ecg_clean(method='neurokit') per lead; R peaks: "
                     "neurokit2.ecg_peaks(method='neurokit') on cleaned lead II"},
        indent=2, ensure_ascii=False) + "\n")
    if a.limit:
        print("--limit given: no manifest written (timing run)")
        return 0
    import neurokit2, scipy, sklearn
    (feat_dir / f"manifest_{a.split}.json").write_text(json.dumps({
        "split": a.split, "units": len(rows), "windows": a.windows, "files": files,
        "elapsed_s": round(elapsed), "workers": a.workers, "git_commit": _git_commit(),
        "versions": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__,
                     "neurokit2": neurokit2.__version__, "scikit-learn": sklearn.__version__},
        "platform": platform.platform(),
    }, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
