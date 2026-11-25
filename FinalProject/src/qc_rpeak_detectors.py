"""QC: compare NeuroKit R-peak detectors against figshare VentricularRate (PRD §4 item 5, amendment 1).

Stratified development sample: 300 units per class (seed 4400), full 10 s, cleaned lead II.
For each detector: share of units whose heart rate (60 / mean RR and 60 / median RR) is within
5 bpm of VentricularRate, and whose R-peak count is within 1 of QRSCount, per class and weighted
by the development class counts. Development data only; labels are used only to stratify.

    python src/qc_rpeak_detectors.py            # prints the table, writes results/features/qc_rpeak_detectors.csv
"""
import csv
import sys
import time
import warnings

warnings.filterwarnings("ignore")
from pathlib import Path
REPO = str(Path(__file__).resolve().parent.parent)
sys.path.insert(0, REPO + "/src")
import ecg_io  # noqa: E402
import neurokit2 as nk  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from multiprocessing import Pool  # noqa: E402

METHODS = [("neurokit", False), ("neurokit", True), ("pantompkins1985", False), ("hamilton2002", False),
           ("elgendi2010", False), ("engzeemod2012", False), ("rodrigues2021", False), ("manikandan2012", False)]


def init():
    global man, diag
    warnings.filterwarnings("ignore")
    man = ecg_io.read_parts_manifest()
    diag = ecg_io.read_diagnostics(ecg_io.DEFAULT_DATA_ROOT)


def work(u):
    if u["label"] == "SI":
        s = ecg_io.load_figshare_signal(ecg_io.DEFAULT_DATA_ROOT, diag[int(u["record"][2:]) - 1]["FileName"])
    else:
        s = ecg_io.load_part1_signal(ecg_io.DEFAULT_DATA_ROOT, u["record"], man[u["record"]]["folder"])
    c = nk.ecg_clean(s[1].astype(float), sampling_rate=500, method="neurokit")
    out = []
    for m, corr in METHODS:
        name = m + ("+corr" if corr else "")
        try:
            r = np.asarray(nk.ecg_peaks(c, sampling_rate=500, method=m, correct_artifacts=corr)[1]["ECG_R_Peaks"])
        except Exception:
            r = np.array([])
        rr = np.diff(r) / 500
        hm = 60 / np.mean(rr) if len(r) > 1 else np.nan
        hd = 60 / np.median(rr) if len(r) > 1 else np.nan
        out.append((u["record"], u["label"], name, hm, hd, len(r)))
    return out


if __name__ == "__main__":
    init()
    vr = {f"JS{k:05d}": float(r["VentricularRate"]) for k, r in enumerate(diag, 1)}
    qc = {f"JS{k:05d}": float(r["QRSCount"]) for k, r in enumerate(diag, 1)}
    dev = list(csv.DictReader(open(REPO + "/results/splits/shaoxing_dev_folds.csv")))
    rng = np.random.default_rng(4400)
    sample = []
    for lab in ("SR", "SB", "ST", "SI", "AFIB", "AFL"):
        us = [u for u in dev if u["label"] == lab]
        sample += [us[i] for i in rng.choice(len(us), 300, replace=False)]
    t = time.time()
    with Pool(7, initializer=init) as p:
        res = [row for rows in p.map(work, sample, chunksize=10) for row in rows]
    d = pd.DataFrame(res, columns=["record", "label", "method", "hr_mean", "hr_median", "n"])
    d["vr"] = d.record.map(vr)
    d["qrscount"] = d.record.map(qc)
    d["mean_ok"] = (d.hr_mean - d.vr).abs() <= 5
    d["median_ok"] = (d.hr_median - d.vr).abs() <= 5
    d["count_ok"] = (d.n - d.qrscount).abs() <= 1
    w = {"SB": 3110, "SR": 1460, "AFIB": 1422, "ST": 1250, "AFL": 350, "SI": 317}
    g = d.groupby(["method", "label"])[["mean_ok", "median_ok", "count_ok"]].mean()
    tbl = g["mean_ok"].unstack().round(3)
    for col in ("mean_ok", "median_ok", "count_ok"):
        u = g[col].unstack()
        tbl["W_" + col] = sum(u[k] * v for k, v in w.items()) / sum(w.values())
    print(f"{time.time() - t:.0f} s; per-class share within 5 bpm using MEAN RR; W_ = dev-weighted totals")
    print(tbl.round(3).sort_values("W_mean_ok", ascending=False).to_string())
    tbl.round(4).to_csv(REPO + "/results/features/qc_rpeak_detectors.csv")
