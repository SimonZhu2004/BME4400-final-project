#!/usr/bin/env python3
"""CNN and MiniRocket on RAW Shaoxing ECGs using the teammate's FROZEN split.

Setup: Python 3.12 recommended. Install requirements_shaoxing_raw.txt in a fresh
environment and select the PyTorch CPU/CUDA build appropriate for your hardware.

Data check ONLY (no model imports, cached tensors, fitting or predictions):
    python train_shaoxing_raw_models.py --check-data-only --output-dir preflight_raw
Full experiment, both models, first 2/4/6/8/10 seconds:
    python train_shaoxing_raw_models.py --output-dir results_shaoxing_raw
Optional model/window selection, fixed BEFORE seeing results:
    python train_shaoxing_raw_models.py --models cnn --output-dir results_cnn_raw
    python train_shaoxing_raw_models.py --models minirocket --durations 10 --output-dir results_minirocket_10s
Explicit source paths:
    python train_shaoxing_raw_models.py --physionet-dir "physionet data/ecg-arrhythmia-1.0.0" \
        --split-dir "physionet data/split" --figshare-raw data/ECGData.zip \
        --diagnostics data/Diagnostics.xlsx --output-dir results_shaoxing_raw

Frozen inputs -- NEVER rebuild the split or silently exclude units
----------------------------------------------------------------
* Exactly 9,887 Shaoxing records from shaoxing_units.csv: 9,491 original PhysioNet
  MAT files plus 396 original figshare SI CSVs. No Ningbo signal is loaded.
* Target order: SR=0, SB=1, ST=2, SI=3, AFIB=4, AFL=5. Other Dx are not targets.
* Read the existing 7,909 development records/folds and 1,978 test IDs directly.
  All three input CSVs must match their PRD SHA256 fingerprints. --seed affects
  fitting and inner early stopping, NOT a new outer split/fold assignment.
* PhysioNet: scipy.io.loadmat(...)["val"], 12 x 5000 int16, in whole microvolts
  under the project's verified convention. Publisher file hashes are checked.
  Malformed header first-line fields (notably JS01052) are reported; a matching,
  structurally valid MAT array is not dropped solely for that text-field error.
* SI: ORIGINAL ECGData.zip or an extracted original ECGData directory. JS id k
  maps to Diagnostics.xlsx data row k. Round CSV to whole uV, transpose, int16.
  Every converted signal must match the frozen unit's hash, verifying this mapping.
  ECGDataDenoised is NOT read. No age, sex, measured rate or Beat inputs are used.
* Canonical signal SHA256: C-contiguous little-endian int16 array [12,5000].
* Missing/changed signals, NaN/Inf, zero leads, duplicate hashes or label mismatch
  stop the run. Resolve the source or amend the shared protocol; no auto-exclusion.
* One record is assumed one patient; actual patient identities are not verified.

Experiment
----------
* Crop the FIRST T seconds [0,500*T), THEN decimate 500 -> 250 Hz (zero_phase=True)
  and z-score each lead within that crop alone. No full-record pre-denoising.
* CNN: residual 1D network with explicit temporal mean pooling. Learning rates
  are selected on the five fixed outer development folds. Early stopping uses
  an INNER stratified 10% of each fold's training portion, never the outer fold
  or test. Default selection is PRD R3 (mean recall of SI/AFIB/AFL); optional
  --selection-metric macro_f1 is a prior protocol choice, not a test-based change.
* Final CNN trains on ALL 7,909 development records for the median best epoch
  from the winning configuration's five folds, with no test-based stopping.
* MiniRocketMultivariate -> StandardScaler -> balanced RidgeClassifierCV. All
  transforms fit only on the current training subset. Ridge selects alpha with
  internal analytical leave-one-out CV inside each outer training fold.
* Complete ALL development tuning, refit/freeze ALL final models, then predict
  the test set once per model/window. No test metric affects model selection.
* Determinism defaults to "warn": request deterministic kernels where available
  but warn for unsupported operations. Seeds do NOT guarantee bitwise repeats in
  this mode. --determinism strict raises instead; CPU is another option.

Reports
-------
Per-class and macro precision/recall/F1, R3, accuracy, per-class/macro one-vs-rest
AUROC and AUPRC. AUPRC means average_precision_score (AP), not trapezoidal area.
CNN scores are probabilities; Ridge scores are decision margins, not probabilities.
CV AUROC/AP use five-fold mean/std; pooled OOF outputs contain classification
metrics only because fold margin scales can differ. Selected-config CV results
are development estimates; the untouched 20% provides final evaluation.

Output: frozen input copies/hashes, unit/split/source-audit tables, versions and
settings, CV histories/predictions/metrics, selected configs, frozen models/hashes,
test predictions/metrics/confusion matrices and evaluation_report.txt. Use a NEW
empty output directory. Signal caches can occupy several GB. This script never
downloads data, modifies source records/splits, or changes the frozen cohort.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import gc
import hashlib
import importlib.metadata
import io
import json
import os
from pathlib import Path
import platform
import random
import sys
import time
import zipfile


CLASSES = ("SR", "SB", "ST", "SI", "AFIB", "AFL")
LEADS = ("I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6")
RHYTHMS = {name: name for name in CLASSES} | {"SA": "SI", "AF": "AFL"}
FS = 500
LABELS = tuple(range(len(CLASSES)))
TRAINING_VERSION_PINS = {"scikit-learn": "1.7.2", "sktime": "0.40.1"}

FROZEN_SPLIT_HASHES = {
    "shaoxing_units.csv": "b708bacdaa9d986112c9b2c232b798184629202fc15213199c1b345f6372e5a3",
    "shaoxing_test_ids.csv": "2c95db54fdc3d65e611b0a8c8c7ea1f0e867dfdf4d545f982eb30945757c9d8a",
    "shaoxing_dev_folds.csv": "252f3eed531bee991abf774adaa82ecdd924e511bf426ade619fcce006047b28",
}
FROZEN_CLASS_COUNTS = {"SR": 1825, "SB": 3888, "ST": 1562, "SI": 396, "AFIB": 1778, "AFL": 438}
RHYTHM_CODES = dict(zip(CLASSES, ("426783006", "426177001", "427084000", "427393009", "164889003", "164890007")))



def parse_args():
    here = Path(__file__).resolve().parent
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data-dir", type=Path, default=here / "data", help="Original figshare source directory")
    p.add_argument("--physionet-dir", type=Path, default=here / "physionet data" / "ecg-arrhythmia-1.0.0",
                   help="Dataset root or its containing directory; shallow auto-discovery")
    p.add_argument("--split-dir", type=Path, default=here / "physionet data" / "split")
    p.add_argument("--figshare-raw", type=Path, help="Original ECGData.zip or extracted ECGData directory")
    p.add_argument("--diagnostics", type=Path, help="Default: DATA_DIR/Diagnostics.xlsx")
    p.add_argument("--output-dir", type=Path, default=None)
    p.add_argument("--check-data-only", "--preflight-only", action="store_true", dest="check_data_only",
                   help="Verify frozen split and all 9,887 signals; no model imports/training")
    p.add_argument("--models", nargs="+", choices=("cnn", "minirocket"), default=["cnn", "minirocket"])
    p.add_argument("--durations", type=int, nargs="+", choices=(2, 4, 6, 8, 10), default=[2, 4, 6, 8, 10])
    p.add_argument("--seed", type=int, default=4400, help="Model/inner-validation seed; frozen outer split never changes")
    p.add_argument("--selection-metric", choices=("r3", "macro_f1"), default="r3")
    p.add_argument("--device", choices=("auto", "cpu", "cuda", "mps"), default="auto")
    p.add_argument("--determinism", choices=("strict", "warn"), default="warn")
    p.add_argument("--epochs", type=int, default=40)
    p.add_argument("--patience", type=int, default=8)
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--cnn-lrs", type=float, nargs="+", default=[1e-3, 3e-4])
    p.add_argument("--minirocket-kernels", type=int, default=10000)
    p.add_argument("--ridge-alphas", type=float, nargs="+", default=[10.0 ** x for x in (-3, -2, -1, 0, 1, 2, 3)])
    p.add_argument("--jobs", type=int, default=4, help="Positive CPU/Numba/PyTorch thread count")
    args = p.parse_args()
    if min(args.epochs, args.patience, args.batch_size, args.jobs) < 1:
        p.error("epochs, patience, batch-size and jobs must be positive")
    if args.minirocket_kernels < 84 or any(x <= 0 for x in args.cnn_lrs + args.ridge_alphas):
        p.error("MiniRocket needs >=84 kernels; learning rates and alphas must be positive")
    args.data_dir = args.data_dir.resolve()
    args.diagnostics = (args.diagnostics or args.data_dir / "Diagnostics.xlsx").resolve()
    args.figshare_raw = (args.figshare_raw or args.data_dir / "ECGData.zip").resolve()
    args.physionet_dir = args.physionet_dir.resolve()
    args.split_dir = args.split_dir.resolve()
    args.output_dir = (args.output_dir or here / ("preflight_shaoxing_raw" if args.check_data_only else "results_shaoxing_raw")).resolve()
    args.models = list(dict.fromkeys(args.models))
    args.durations = sorted(set(args.durations))
    args.cnn_lrs = list(dict.fromkeys(args.cnn_lrs))
    return args


def log(message):
    print(time.strftime("[%H:%M:%S] ") + message, flush=True)


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def clean_json(value):
    if isinstance(value, dict):
        return {str(k): clean_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean_json(v) for v in value]
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def write_json(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(clean_json(data), indent=2, allow_nan=False), encoding="utf-8")


def write_rows(path, rows):
    if not rows:
        return
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)


def training_environment_status(args):
    packages = {}
    for name in ("numpy", "pandas", "scipy", "scikit-learn", "torch", "sktime", "numba", "openpyxl", "joblib"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    problems = []
    if not (3, 11) <= sys.version_info[:2] < (3, 14):
        problems.append("Use Python 3.11-3.13, preferably 3.12")
    critical = {"scikit-learn": TRAINING_VERSION_PINS["scikit-learn"]}
    if "minirocket" in args.models:
        critical["sktime"] = TRAINING_VERSION_PINS["sktime"]
    for name, expected in critical.items():
        if packages[name] != expected:
            problems.append(f"{name}: found {packages[name] or 'not installed'}, need {expected}")
    needed = ["numpy", "pandas", "scipy", "openpyxl", "joblib"]
    if "cnn" in args.models:
        needed.append("torch")
    if "minirocket" in args.models:
        needed.append("numba")
    for name in needed:
        if packages[name] is None:
            problems.append(f"{name}: not installed")
    return {"ready": not problems, "packages": packages, "problems": problems,
            "note": "Version/package presence check only; not a GPU forward/backward test"}


def check_training_versions(args):
    status = training_environment_status(args)
    if not status["ready"]:
        requirements = Path(__file__).with_name("requirements_shaoxing_raw.txt")
        raise SystemExit("Training environment is not ready:\n  " + "\n  ".join(status["problems"]) +
                         f'\nInstall in a fresh environment: python -m pip install -r "{requirements}"' +
                         "\n--check-data-only can still verify sources without model dependencies.")
    return status


def find_physionet_root(path):
    candidates = [path]
    for _ in range(3):
        roots = [p for p in candidates if (p / "WFDBRecords").is_dir() and (p / "SHA256SUMS.txt").is_file()]
        if len(roots) == 1:
            return roots[0].resolve()
        if len(roots) > 1:
            raise ValueError("Multiple datasets found; point --physionet-dir at the dataset root")
        candidates = [child for parent in candidates if parent.is_dir() for child in parent.iterdir()
                      if child.is_dir() and child.name != "WFDBRecords"]
    raise FileNotFoundError(f"Cannot find WFDBRecords plus SHA256SUMS.txt under {path}")


def read_frozen_table(args, name):
    path = args.split_dir / name
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != FROZEN_SPLIT_HASHES[name]:
        raise ValueError(f"Frozen split fingerprint mismatch: {path}; do not regenerate or silently replace it")
    return pd.read_csv(io.BytesIO(raw)), raw


def signal_hash(data):
    if data.shape != (12, 5000) or data.dtype.kind != "i" or data.dtype.itemsize != 2:
        raise ValueError("Canonical frozen source must be int16 [12,5000] before hashing")
    return hashlib.sha256(np.asarray(data, dtype="<i2", order="C").tobytes()).hexdigest()


def parse_original_csv(raw, origin):
    first = next((line.strip() for line in raw.decode("utf-8-sig").splitlines() if line.strip()), "")
    columns = [value.strip().strip('"') for value in first.split(",")]
    if columns != list(LEADS):
        raise ValueError(f"{origin}: expected the publisher's original 12 lead column names/order")
    values = np.loadtxt(io.BytesIO(raw), delimiter=",", skiprows=1, dtype=np.float64, encoding="utf-8-sig")
    if values.shape != (5000, 12) or not np.isfinite(values).all():
        raise ValueError(f"{origin}: invalid/nonfinite original SI CSV")
    rounded = np.rint(values)
    if rounded.min() < -32768 or rounded.max() > 32767:
        raise ValueError(f"{origin}: rounded original SI values outside int16 range")
    return np.ascontiguousarray(rounded.T, dtype="<i2")


class RawSignalReader:
    """Load only whitelisted units; no Ningbo loading or source modification."""
    def __init__(self, args):
        self.args = args
        self.archive = None
        self.csv_paths = {}

    def __enter__(self):
        source = self.args.figshare_raw
        if "denoised" in source.name.lower():
            raise ValueError("SI supplementation needs ORIGINAL ECGData, not ECGDataDenoised")
        if source.is_file():
            self.archive = zipfile.ZipFile(source)
            names = [n for n in self.archive.namelist() if n.lower().endswith(".csv") and Path(n).stem.startswith("MUSE_")]
            for name in names:
                key = Path(name).stem
                if key in self.csv_paths:
                    self.archive.close()
                    raise ValueError(f"Ambiguous original SI filename in ZIP: {key}")
                self.csv_paths[key] = name
        elif source.is_dir():
            for path in source.rglob("*.csv"):
                if not path.stem.startswith("MUSE_"):
                    continue
                if path.stem in self.csv_paths:
                    raise ValueError(f"Ambiguous original SI CSV filename: {path.stem}")
                self.csv_paths[path.stem] = path
        else:
            raise FileNotFoundError(f"Missing original SI source: {source}; 396 units need ECGData.zip")
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.archive is not None:
            self.archive.close()

    def load(self, row, include_header_check=False):
        if not row.record.startswith("JS") or not row.record[2:].isdigit() or not 1 <= int(row.record[2:]) <= 10646:
            raise ValueError(f"Refusing non-Shaoxing record: {row.record}")
        header_issue = False
        if row.source == "physionet_part1":
            path = Path(row.path)
            if not path.resolve().is_relative_to(self.args.physionet_dir):
                raise ValueError("Source path escapes the specified PhysioNet root")
            raw = path.read_bytes()
            if hashlib.sha256(raw).hexdigest() != row.publisher_mat_sha256:
                raise ValueError(f"Publisher MAT checksum mismatch: {row.record}")
            data = loadmat(io.BytesIO(raw))["val"]
            if include_header_check:
                header_raw = path.with_suffix(".hea").read_bytes()
                if hashlib.sha256(header_raw).hexdigest() != row.publisher_header_sha256:
                    raise ValueError(f"Publisher header checksum mismatch: {row.record}")
                lines = header_raw.decode().splitlines()
                header_issue = lines[0].split()[:4] != [row.record, "12", "500", "5000"]
                diagnoses = next((line.split(":", 1)[1].strip().split(",") for line in lines if line.startswith("#Dx:")), [])
                if RHYTHM_CODES[row.class_name] not in diagnoses:
                    raise ValueError(f"Frozen target absent from header labels: {row.record}")
        elif row.source == "figshare_csv" and row.class_name == "SI":
            member = self.csv_paths.get(row.FileName)
            if member is None:
                raise FileNotFoundError(f"No original SI CSV for {row.record}: {row.FileName}")
            raw = self.archive.read(member) if self.archive is not None else member.read_bytes()
            data = parse_original_csv(raw, row.FileName)
        else:
            raise ValueError(f"Unsupported source/label combination: {row.record}, {row.source}, {row.class_name}")
        if data.shape != (12, 5000) or data.dtype.kind != "i" or data.dtype.itemsize != 2:
            raise ValueError(f"{row.record}: expected int16 [12,5000], got {data.dtype} {data.shape}")
        if not np.isfinite(data).all() or np.any(np.all(data == 0, axis=1)):
            raise ValueError(f"{row.record}: invalid/zero-lead frozen signal; do not silently drop it")
        data = np.ascontiguousarray(data, dtype="<i2")
        if signal_hash(data) != row.signal_sha256:
            raise ValueError(f"Frozen signal hash mismatch: {row.record}")
        return (data, header_issue) if include_header_check else data


def prepare_cohort(args):
    args.physionet_dir = find_physionet_root(args.physionet_dir)
    frozen, _ = read_frozen_table(args, "shaoxing_units.csv")
    required = {"record", "label", "code", "source", "signal_sha256"}
    if not required.issubset(frozen.columns) or frozen.record.duplicated().any():
        raise ValueError("Invalid frozen unit schema or repeated record IDs")
    if len(frozen) != 9887 or frozen.label.value_counts().to_dict() != FROZEN_CLASS_COUNTS:
        raise ValueError("Frozen cohort must contain the PRD's exact 9,887 units and class counts")
    if frozen.signal_sha256.nunique() != len(frozen):
        raise ValueError("Frozen unit hashes are not unique")
    if frozen.source.value_counts().to_dict() != {"physionet_part1": 9491, "figshare_csv": 396}:
        raise ValueError("Expected 9,491 PhysioNet units plus 396 original figshare SI units")
    if not frozen.record.str.fullmatch(r"JS\d{5}").all() or not frozen.record.str[2:].astype(int).between(1, 10646).all():
        raise ValueError("Frozen units contain a non-Shaoxing record ID")
    if any(CLASSES[int(row.code)] != row.label for row in frozen.itertuples()):
        raise ValueError("Frozen numeric codes do not agree with the six-class order")
    diagnostics = pd.read_excel(args.diagnostics, engine="openpyxl", usecols=["FileName", "Rhythm"])
    if len(diagnostics) != 10646 or diagnostics.FileName.isna().any() or diagnostics.FileName.duplicated().any():
        raise ValueError("Expected original 10,646-row Diagnostics.xlsx with unique FileNames")
    publisher = {}
    manifest_path = args.physionet_dir / "SHA256SUMS.txt"
    for line in manifest_path.read_text().splitlines():
        digest, relative = line.split(maxsplit=1)
        relative = relative.lstrip("*").removeprefix("./")
        relative_path = Path(relative)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise ValueError("Unsafe path in publisher checksum manifest")
        publisher[relative] = digest
    mat_paths = {Path(path).stem: path for path in publisher if path.endswith(".mat")}
    rows = []
    for row in frozen.sort_values("record").itertuples(index=False):
        diag = diagnostics.iloc[int(row.record[2:]) - 1]
        if RHYTHMS.get(str(diag.Rhythm).strip().upper()) != row.label:
            raise ValueError(f"Frozen label and original diagnostics disagree: {row.record}")
        filename = str(diag.FileName).strip()
        if not filename.startswith("MUSE_") or Path(filename).name != filename:
            raise ValueError(f"Unexpected original FileName for {row.record}")
        entry = {"record": row.record, "FileName": filename, "class_name": row.label,
                 "label": int(row.code), "code": int(row.code), "source": row.source,
                 "signal_sha256": row.signal_sha256, "path": "",
                 "publisher_mat_sha256": "", "publisher_header_sha256": ""}
        if row.source == "physionet_part1":
            relative = mat_paths.get(row.record)
            if relative is None:
                raise FileNotFoundError(f"No PhysioNet MAT entry for {row.record}")
            entry.update(path=str(args.physionet_dir / relative), publisher_mat_sha256=publisher[relative],
                         publisher_header_sha256=publisher[str(Path(relative).with_suffix('.hea')).replace('\\', '/')])
        elif row.label != "SI":
            raise ValueError("Only SI supplementation may use figshare_csv")
        rows.append(entry)
    units = pd.DataFrame(rows)
    units.to_csv(args.output_dir / "units.csv", index=False)
    write_json(args.output_dir / "data_summary.json", {
        "dataset": "Frozen raw Shaoxing cohort", "records": len(units),
        "class_counts": units.class_name.value_counts().to_dict(), "source_counts": units.source.value_counts().to_dict(),
        "physionet_root": args.physionet_dir, "figshare_raw": args.figshare_raw,
        "diagnostics_sha256": sha256_file(args.diagnostics), "publisher_manifest_sha256": sha256_file(manifest_path),
        "lead_order": LEADS, "source_hz": FS, "processed_hz": 250,
        "si_conversion": "round original CSV to whole uV, transpose, little-endian int16",
        "no_new_exclusions": True, "unit_assumption": "one ECG record per patient; patient identity not verified",
    })
    log(f"Frozen cohort: {len(units)} units; no new sampling, relabeling or exclusion")
    return units


def make_manifest(units, args):
    development, dev_raw = read_frozen_table(args, "shaoxing_dev_folds.csv")
    test_table, test_raw = read_frozen_table(args, "shaoxing_test_ids.csv")
    _, units_raw = read_frozen_table(args, "shaoxing_units.csv")
    for table, expected in ((development, 7909), (test_table, 1978)):
        if not {"record", "label", "code"}.issubset(table.columns) or len(table) != expected or table.record.duplicated().any():
            raise ValueError("Invalid frozen development/test table")
    dev_ids, test_ids = set(development.record), set(test_table.record)
    if dev_ids & test_ids or dev_ids | test_ids != set(units.record):
        raise ValueError("Frozen split overlaps or does not cover all units exactly once")
    if "fold" not in development or set(development.fold) != set(range(5)):
        raise ValueError("Frozen development folds must be 0..4")
    lookup = units.set_index("record")
    for table in (development, test_table):
        for row in table.itertuples(index=False):
            unit = lookup.loc[row.record]
            if row.label != unit.class_name or int(row.code) != unit.label:
                raise ValueError(f"Frozen split label/code mismatch: {row.record}")
    manifest = units[["record", "FileName", "source", "label", "class_name", "signal_sha256"]].copy()
    fold_map = development.set_index("record").fold.to_dict()
    manifest["split"] = ["dev" if r in dev_ids else "test" for r in units.record]
    manifest["fold"] = [int(fold_map[r]) if r in dev_ids else -1 for r in units.record]
    dev = np.flatnonzero(manifest.split.to_numpy() == "dev")
    test = np.flatnonzero(manifest.split.to_numpy() == "test")
    y = units.label.to_numpy(dtype=np.int64)
    if len(test) != int(np.ceil(0.2 * len(units))) or set(y[test]) != set(LABELS):
        raise ValueError("Frozen test allocation is not the six-class 20% holdout")
    for c in LABELS:
        if abs(np.sum(y[test] == c) - .2 * np.sum(y == c)) > 1:
            raise ValueError("Frozen test allocation is not stratified")
        counts = [int(np.sum((y[dev] == c) & (manifest.loc[dev, "fold"].to_numpy() == f))) for f in range(5)]
        if min(counts) == 0 or max(counts) - min(counts) > 1:
            raise ValueError("Frozen five-fold allocation is not stratified")
    frozen_dir = args.output_dir / "frozen_split_inputs"
    frozen_dir.mkdir()
    for name, raw in (("shaoxing_units.csv", units_raw), ("shaoxing_dev_folds.csv", dev_raw), ("shaoxing_test_ids.csv", test_raw)):
        (frozen_dir / name).write_bytes(raw)
    manifest.to_csv(args.output_dir / "split_manifest.csv", index=False)
    write_json(args.output_dir / "split_summary.json", {
        "origin": "Existing frozen CSVs; NOT regenerated", "frozen_split_seed": 4400,
        "model_seed": args.seed, "records": len(units), "dev": len(dev), "test": len(test), "folds": 5,
        "frozen_input_hashes": FROZEN_SPLIT_HASHES, "dev_test_overlap": 0,
        "manifest_sha256": sha256_file(args.output_dir / "split_manifest.csv"),
        "counts": manifest.groupby(["split", "class_name"]).size().unstack(fill_value=0).to_dict(),
    })
    log(f"Using existing split: {len(dev)} development, {len(test)} test, five existing folds")
    return manifest, dev, test


def audit_frozen_sources(units, args):
    rows = []
    with RawSignalReader(args) as reader:
        def inspect(row):
            try:
                data, header_issue = reader.load(row, include_header_check=True)
                return {"record": row.record, "class_name": row.class_name, "source": row.source,
                        "status": "ok", "team_hash_match": True, "shape": "12x5000",
                        "header_first_line_issue": header_issue, "error": ""}
            except Exception as exc:
                return {"record": row.record, "class_name": row.class_name, "source": row.source,
                        "status": "error", "team_hash_match": False, "shape": "",
                        "header_first_line_issue": False, "error": str(exc)}
        with ThreadPoolExecutor(max_workers=args.jobs) as executor:
            futures = [executor.submit(inspect, row) for row in units.itertuples(index=False)]
            for count, future in enumerate(as_completed(futures), 1):
                rows.append(future.result())
                if count % 1000 == 0 or count == len(units):
                    log(f"Frozen raw source verification: {count}/{len(units)}; no training")
    frame = pd.DataFrame(rows).sort_values("record")
    frame.to_csv(args.output_dir / "source_audit.csv", index=False)
    failed = frame[frame.status != "ok"]
    failed.to_csv(args.output_dir / "source_audit_failures.csv", index=False)
    summary = {"checked": len(frame), "passed": int((frame.status == "ok").sum()), "failed": len(failed),
               "header_first_line_issues": frame[frame.header_first_line_issue].record.tolist(),
               "note": "Header text issues do not invalidate matching, structurally valid MAT arrays"}
    write_json(args.output_dir / "source_audit_summary.json", summary)
    if len(failed):
        raise ValueError(f"{len(failed)} frozen sources failed; see source_audit_failures.csv. No records were dropped.")
    log(f"All {len(frame)} frozen raw signals verified; header text issues: {summary['header_first_line_issues']}")
    return summary


def preprocess_crop(raw, seconds):
    if raw.shape != (12, 5000):
        raise ValueError("Expected canonical [12,5000] source")
    crop = np.asarray(raw[:, :FS * seconds], dtype=np.float64)
    x = decimate(crop, q=2, axis=1, zero_phase=True)
    if x.shape != (12, 250 * seconds):
        raise ValueError("Unexpected crop/resampling length")
    mean, std = x.mean(axis=1, keepdims=True), x.std(axis=1, keepdims=True)
    x = (x - mean) / np.maximum(std, 1e-8)
    if not np.isfinite(x).all():
        raise ValueError("Nonfinite processed crop")
    return x.astype(np.float32)


def prepare_tensors(units, args):
    cache_dir = args.output_dir / "signal_cache"
    cache_dir.mkdir()
    arrays = {t: np.lib.format.open_memmap(cache_dir / f"prefix_{t}s.npy", mode="w+", dtype=np.float32,
                                          shape=(len(units), 12, 250 * t)) for t in args.durations}
    log("Building raw-prefix tensors: crop first, then resample and normalize")
    with RawSignalReader(args) as reader:
        for i, row in enumerate(units.itertuples(index=False)):
            raw = reader.load(row)
            for t, target in arrays.items():
                target[i] = preprocess_crop(raw, t)
            if (i + 1) % 500 == 0:
                log(f"Raw prefix tensors: {i + 1}/{len(units)}")
    for array in arrays.values():
        array.flush()
    del arrays
    return {t: cache_dir / f"prefix_{t}s.npy" for t in args.durations}




def classification_summary(y_true, y_pred):
    precision, recall, f1, _ = precision_recall_fscore_support(y_true, y_pred, labels=LABELS, zero_division=0)
    return {"precision_macro": float(precision.mean()), "recall_macro": float(recall.mean()),
            "macro_f1": float(f1.mean()), "r3": float(recall[[3, 4, 5]].mean()),
            "accuracy": float(np.mean(y_true == y_pred))}


def evaluate(y_true, y_pred, scores=None):
    summary = classification_summary(y_true, y_pred)
    precision, recall, f1, support = precision_recall_fscore_support(y_true, y_pred, labels=LABELS, zero_division=0)
    per_class = []
    if scores is not None:
        if scores.shape != (len(y_true), 6) or not np.isfinite(scores).all():
            raise ValueError("Scores must be finite with columns in the fixed six-class order")
    for c, name in enumerate(CLASSES):
        binary = (y_true == c).astype(int)
        valid = scores is not None and 0 < binary.sum() < len(binary)
        per_class.append({"class_name": name, "label": c, "support": int(support[c]),
                          "precision": float(precision[c]), "recall": float(recall[c]), "f1": float(f1[c]),
                          "auroc_ovr": float(roc_auc_score(binary, scores[:, c])) if valid else None,
                          "auprc_ap_ovr": float(average_precision_score(binary, scores[:, c])) if valid else None})
    if scores is not None:
        if any(r["auroc_ovr"] is None for r in per_class):
            raise ValueError("AUROC/AP needs positive and negative examples for every class")
        summary["auroc_macro_ovr"] = float(np.mean([r["auroc_ovr"] for r in per_class]))
        summary["auprc_macro_ap_ovr"] = float(np.mean([r["auprc_ap_ovr"] for r in per_class]))
    return summary, per_class


def save_predictions(path, units, indices, y, pred, scores, score_type, folds=None):
    frame = units.iloc[indices][["record", "FileName", "source", "class_name"]].reset_index(drop=True)
    frame["true_label"] = y[indices]
    frame["pred_label"] = pred
    frame["pred_class"] = [CLASSES[int(c)] for c in pred]
    frame["score_type"] = score_type
    if folds is not None:
        frame["fold"] = folds
    for c, name in enumerate(CLASSES):
        frame[f"score_{name}"] = scores[:, c]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


def set_torch_seed(seed, jobs, determinism):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.set_num_threads(jobs)
    torch.use_deterministic_algorithms(True, warn_only=(determinism == "warn"))
    torch.backends.cudnn.benchmark = False


def build_cnn():
    class TemporalMean(nn.Module):
        def forward(self, x):
            # Explicit global temporal mean; no adaptive-pooling backward kernel.
            # keepdim + Flatten preserves the original head's module indices.
            return x.mean(dim=-1, keepdim=True)

    class ResidualBlock(nn.Module):
        def __init__(self, cin, cout):
            super().__init__()
            self.main = nn.Sequential(nn.Conv1d(cin, cout, 7, stride=2, padding=3, bias=False),
                                      nn.BatchNorm1d(cout), nn.ReLU(),
                                      nn.Conv1d(cout, cout, 7, padding=3, bias=False), nn.BatchNorm1d(cout))
            self.skip = nn.Sequential(nn.Conv1d(cin, cout, 1, stride=2, bias=False), nn.BatchNorm1d(cout))
            self.activation = nn.ReLU()

        def forward(self, x):
            return self.activation(self.main(x) + self.skip(x))

    return nn.Sequential(nn.Conv1d(12, 32, 15, stride=2, padding=7, bias=False),
                         nn.BatchNorm1d(32), nn.ReLU(),
                         ResidualBlock(32, 32), ResidualBlock(32, 64),
                         ResidualBlock(64, 64), ResidualBlock(64, 128),
                         TemporalMean(), nn.Flatten(), nn.Dropout(0.3), nn.Linear(128, 6))


def make_loader(x, y, indices, args, seed, shuffle=False):
    class ECGSubset(torch.utils.data.Dataset):
        def __len__(self):
            return len(indices)

        def __getitem__(self, item):
            i = indices[item]
            return torch.from_numpy(np.array(x[i], dtype=np.float32, copy=True)), int(y[i])

    generator = torch.Generator().manual_seed(seed)
    return torch.utils.data.DataLoader(ECGSubset(), batch_size=args.batch_size, shuffle=shuffle,
                                      generator=generator, num_workers=0, drop_last=False)


def predict_cnn(model, x, y, indices, args, device):
    model.eval()
    chunks = []
    with torch.no_grad():
        for batch, _ in make_loader(x, y, indices, args, args.seed):
            chunks.append(torch.softmax(model(batch.to(device)), dim=1).cpu().numpy())
    scores = np.concatenate(chunks)
    return scores.argmax(axis=1), scores


def fit_cnn(x, y, train_indices, args, device, lr, seed, val_indices=None, fixed_epochs=None):
    set_torch_seed(seed, args.jobs, args.determinism)
    model = build_cnn().to(device)
    counts = np.bincount(y[train_indices], minlength=6)
    if (counts == 0).any():
        raise ValueError("CNN training subset must contain all six classes")
    weights = len(train_indices) / (6 * counts)
    criterion = nn.CrossEntropyLoss(weight=torch.tensor(weights, dtype=torch.float32, device=device))
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    loader = make_loader(x, y, train_indices, args, seed, shuffle=True)
    best_state, best_score, best_epoch, stale = None, -np.inf, 0, 0
    history = []
    epochs = fixed_epochs if fixed_epochs is not None else args.epochs
    for epoch in range(1, epochs + 1):
        model.train()
        loss_total, seen = 0.0, 0
        for batch, labels in loader:
            batch, labels = batch.to(device), labels.to(device)
            optimizer.zero_grad(set_to_none=True)
            loss = criterion(model(batch), labels)
            if not torch.isfinite(loss):
                raise RuntimeError("CNN produced a nonfinite training loss")
            loss.backward()
            optimizer.step()
            loss_total += loss.item() * len(labels)
            seen += len(labels)
        row = {"epoch": epoch, "train_loss": loss_total / seen}
        if val_indices is not None:
            pred, _ = predict_cnn(model, x, y, val_indices, args, device)
            score = classification_summary(y[val_indices], pred)[args.selection_metric]
            row["inner_validation_" + args.selection_metric] = score
            if score > best_score + 1e-12:
                best_score, best_epoch, stale = score, epoch, 0
                best_state = {name: tensor.detach().cpu().clone() for name, tensor in model.state_dict().items()}
            else:
                stale += 1
        history.append(row)
        if epoch == 1 or epoch % 5 == 0:
            log(f"CNN epoch {epoch}/{epochs}, loss={row['train_loss']:.4f}" +
                (f", inner {args.selection_metric}={score:.4f}" if val_indices is not None else ""))
        if val_indices is not None and stale >= args.patience:
            break
    if val_indices is not None:
        if best_state is None:
            raise RuntimeError("No valid CNN checkpoint")
        model.load_state_dict(best_state)
    else:
        best_epoch = epochs
    return model, int(best_epoch), history


def fit_minirocket(x, y, indices, args, seed):
    # Only these outer training rows may fit the transform/scaler/Ridge.
    pipeline = Pipeline([
        ("minirocket", MiniRocketMultivariate(num_kernels=args.minirocket_kernels,
                                              random_state=seed, n_jobs=args.jobs)),
        ("scaler", StandardScaler()),
        ("ridge", RidgeClassifierCV(alphas=np.asarray(args.ridge_alphas), class_weight="balanced")),
    ])
    pipeline.fit(np.ascontiguousarray(x[indices]), y[indices])
    if not np.array_equal(pipeline.classes_, np.asarray(LABELS)):
        raise RuntimeError("Unexpected MiniRocket class-column order")
    return pipeline


def predict_minirocket(pipeline, x, indices):
    scores = np.asarray(pipeline.decision_function(np.ascontiguousarray(x[indices])))
    return pipeline.classes_[scores.argmax(axis=1)], scores


def run_cv(units, manifest, dev, tensor_paths, args, device):
    y = units.label.to_numpy(dtype=np.int64)
    folds = manifest.fold.to_numpy()
    summary_rows, class_rows, selected = [], [], {}
    for t, tensor_path in tensor_paths.items():
        x = np.load(tensor_path, mmap_mode="r")
        for model_name in args.models:
            candidates = ([{"learning_rate": lr} for lr in args.cnn_lrs] if model_name == "cnn" else [{}])
            winner, winner_score = None, -np.inf
            for candidate_id, config in enumerate(candidates):
                oof_pred = np.full(len(units), -1, dtype=np.int64)
                oof_scores = np.full((len(units), 6), np.nan, dtype=np.float32)
                epochs, alpha_values = [], []
                config_dir = args.output_dir / "cv" / f"{t}s" / model_name / f"config_{candidate_id}"
                config_dir.mkdir(parents=True)
                for fold in range(5):
                    outer_train = dev[folds[dev] != fold]
                    outer_val = dev[folds[dev] == fold]
                    log(f"CV: {model_name}, T={t}s, config={config}, fold={fold + 1}/5")
                    if model_name == "cnn":
                        inner_train, inner_val = train_test_split(outer_train, test_size=0.1,
                                                                 stratify=y[outer_train], random_state=args.seed)
                        model, epoch, history = fit_cnn(x, y, inner_train, args, device,
                                                       config["learning_rate"], args.seed + fold,
                                                       val_indices=inner_val)
                        pred, scores = predict_cnn(model, x, y, outer_val, args, device)
                        epochs.append(epoch)
                        write_rows(config_dir / f"fold_{fold}_history.csv", history)
                    else:
                        model = fit_minirocket(x, y, outer_train, args, args.seed + fold)
                        pred, scores = predict_minirocket(model, x, outer_val)
                        alpha_values.append(float(model.named_steps["ridge"].alpha_))
                    metrics, per_class = evaluate(y[outer_val], pred, scores)
                    context = {"model": model_name, "T_seconds": t, "config_id": candidate_id, "fold": fold}
                    summary_rows.append({**context, **metrics})
                    class_rows.extend({**context, **row} for row in per_class)
                    oof_pred[outer_val], oof_scores[outer_val] = pred, scores
                    log(f"Outer fold: macro F1={metrics['macro_f1']:.4f}, AUROC={metrics['auroc_macro_ovr']:.4f}")
                    del model
                    gc.collect()
                    if "cnn" in args.models and device == "cuda":
                        torch.cuda.empty_cache()
                    # Save each completed fold's metrics even if a later fit fails.
                    write_rows(args.output_dir / "cv_fold_metrics.csv", summary_rows)
                    write_rows(args.output_dir / "cv_per_class_metrics.csv", class_rows)
                if (oof_pred[dev] < 0).any() or not np.isfinite(oof_scores[dev]).all():
                    raise RuntimeError("OOF predictions are incomplete")
                pooled, pooled_class = evaluate(y[dev], oof_pred[dev])
                score_type = "softmax_probability" if model_name == "cnn" else "ridge_decision_margin"
                save_predictions(config_dir / "oof_predictions.csv", units, dev, y, oof_pred[dev],
                                 oof_scores[dev], score_type, folds[dev])
                write_json(config_dir / "pooled_classification_metrics.json", {
                    "summary": pooled, "per_class": pooled_class,
                    "ranking_metrics": "Use CV fold mean/std; do not pool margins from different fitted models",
                    "config": config, "best_epochs": epochs, "ridge_alphas": alpha_values,
                })
                score = pooled[args.selection_metric]
                if score > winner_score + 1e-12:
                    winner_score = score
                    winner = {"model": model_name, "T_seconds": t, "config_id": candidate_id,
                              "config": config, "selection_metric": args.selection_metric,
                              "development_selection_score": score,
                              "final_epochs": max(1, int(np.median(epochs))) if epochs else None,
                              "fold_best_epochs": epochs, "fold_ridge_alphas": alpha_values}
            selected[f"{model_name}_{t}s"] = winner
            write_json(args.output_dir / "selected_configs.json", selected)
        del x
    metrics = pd.DataFrame(summary_rows)
    keys = ["model", "T_seconds", "config_id"]
    aggregate = metrics.groupby(keys)[list(classification_summary(np.arange(6), np.arange(6))) +
                                    ["auroc_macro_ovr", "auprc_macro_ap_ovr"]].agg(["mean", "std"])
    aggregate.columns = ["_".join(c) for c in aggregate.columns]
    aggregate.reset_index().to_csv(args.output_dir / "cv_summary.csv", index=False)
    write_json(args.output_dir / "cv_metric_notes.json", {
        "ranking": "macro one-vs-rest AUROC; AUPRC is average precision (AP)",
        "summary": "Mean and sample standard deviation across five outer folds, for every configuration",
        "selection_bias": "CNN selected-config CV metrics are development estimates; use final test for confirmation",
    })
    return selected


def refit_and_freeze(units, dev, tensor_paths, selected, args, device):
    y = units.label.to_numpy(dtype=np.int64)
    directory = args.output_dir / "models"
    directory.mkdir()
    frozen = {}
    for key, choice in selected.items():
        t, model_name = choice["T_seconds"], choice["model"]
        x = np.load(tensor_paths[t], mmap_mode="r")
        log(f"Final refit on all {len(dev)} development records: {key}")
        if model_name == "cnn":
            model, _, history = fit_cnn(x, y, dev, args, device, choice["config"]["learning_rate"],
                                        args.seed, fixed_epochs=choice["final_epochs"])
            path = directory / f"{key}.pt"
            torch.save({"state_dict": {k: v.detach().cpu() for k, v in model.state_dict().items()},
                        "architecture": "PRD_residual_1d_cnn_v1", "class_order": CLASSES,
                        "determinism": args.determinism,
                        "duration_seconds": t, "sample_rate": 250, "lead_order": LEADS,
                        "input_source": "frozen_physionet_raw_plus_original_si",
                        "frozen_unit_manifest_sha256": FROZEN_SPLIT_HASHES["shaoxing_units.csv"],
                        "preprocessing": "prefix -> decimate(q=2,zero_phase=True) -> per-lead z-score",
                        "training_choice": choice}, path)
            write_rows(directory / f"{key}_training_history.csv", history)
        else:
            model = fit_minirocket(x, y, dev, args, args.seed)
            path = directory / f"{key}.joblib"
            joblib.dump(model, path, compress=3)
        frozen[key] = {"path": str(path), "sha256": sha256_file(path), "choice": choice}
        if model_name == "minirocket":
            frozen[key]["final_ridge_alpha"] = float(model.named_steps["ridge"].alpha_)
        del model, x
        gc.collect()
    write_json(args.output_dir / "model_manifest.json", frozen)
    return frozen


def test_frozen_models(units, test, tensor_paths, frozen, args, device):
    # A marker is written BEFORE any test predictions, not after viewing metrics.
    marker = args.output_dir / "TEST_EVALUATION_STARTED.json"
    with marker.open("x", encoding="utf-8") as f:
        json.dump({"timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   "model_manifest_sha256": sha256_file(args.output_dir / "model_manifest.json")}, f)
    y = units.label.to_numpy(dtype=np.int64)
    summaries, classes = [], []
    for key, saved in frozen.items():
        choice = saved["choice"]
        t, model_name = choice["T_seconds"], choice["model"]
        path = Path(saved["path"])
        if sha256_file(path) != saved["sha256"]:
            raise RuntimeError(f"Frozen model changed: {path}")
        x = np.load(tensor_paths[t], mmap_mode="r")
        log(f"One-time held-out test evaluation: {key}")
        if model_name == "cnn":
            checkpoint = torch.load(path, map_location="cpu", weights_only=True)
            model = build_cnn().to(device)
            model.load_state_dict(checkpoint["state_dict"])
            pred, scores = predict_cnn(model, x, y, test, args, device)
            score_type = "softmax_probability"
        else:
            model = joblib.load(path)
            pred, scores = predict_minirocket(model, x, test)
            score_type = "ridge_decision_margin"
        metrics, per_class = evaluate(y[test], pred, scores)
        context = {"model": model_name, "T_seconds": t}
        summaries.append({**context, **metrics})
        classes.extend({**context, **row} for row in per_class)
        directory = args.output_dir / "test" / key
        directory.mkdir(parents=True)
        save_predictions(directory / "predictions.csv", units, test, y, pred, scores, score_type)
        write_json(directory / "metrics.json", {"summary": metrics, "per_class": per_class,
                                                "score_type": score_type, "auprc_definition": "average precision"})
        pd.DataFrame(confusion_matrix(y[test], pred, labels=LABELS), index=CLASSES, columns=CLASSES).to_csv(
            directory / "confusion_matrix.csv", index_label="true_class")
        del model, x
        gc.collect()
    write_rows(args.output_dir / "test_summary.csv", summaries)
    write_rows(args.output_dir / "test_per_class_metrics.csv", classes)
    report = ["Shaoxing RAW ECG: CNN / MiniRocket, frozen team split", "",
              f"Classes: {', '.join(CLASSES)}; held-out test records: {len(test)}.",
              "CV: see cv_summary.csv (five-fold mean/std, development data only).",
              "AUROC: macro one-vs-rest. AUPRC: macro one-vs-rest average precision (AP).",
              "MiniRocket margins are ranking scores, not probabilities.",
              "Inputs: 9,491 PhysioNet raw MAT + 396 rounded ORIGINAL figshare SI CSVs; processing after crop.", "",
              pd.DataFrame(summaries).to_string(index=False), "", "Per-class held-out test metrics:",
              pd.DataFrame(classes).to_string(index=False)]
    (args.output_dir / "evaluation_report.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    log("Held-out test summary:\n" + pd.DataFrame(summaries).to_string(index=False))


def main():
    args = parse_args()
    # Preflight imports source-reading dependencies, never model frameworks.
    global np, pd, loadmat, decimate, train_test_split
    global precision_recall_fscore_support, roc_auc_score, average_precision_score, confusion_matrix
    global Pipeline, StandardScaler, RidgeClassifierCV, MiniRocketMultivariate, joblib, torch, nn
    try:
        import numpy as np
        import pandas as pd
        from scipy.io import loadmat
        from scipy.signal import decimate
    except ImportError as exc:
        raise SystemExit(f"Source checks need numpy, pandas, scipy and openpyxl: {exc}") from exc
    environment = training_environment_status(args)
    if not args.check_data_only:
        check_training_versions(args)
        os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
        try:
            from sklearn.model_selection import train_test_split
            from sklearn.metrics import (precision_recall_fscore_support, roc_auc_score,
                                         average_precision_score, confusion_matrix)
            from sklearn.pipeline import Pipeline
            from sklearn.preprocessing import StandardScaler
            from sklearn.linear_model import RidgeClassifierCV
            import joblib
            if "cnn" in args.models:
                import torch
                from torch import nn
            if "minirocket" in args.models:
                from sktime.transformations.panel.rocket import MiniRocketMultivariate
        except ImportError as exc:
            raise SystemExit(f"Missing/incompatible model dependency: {exc}; install requirements_shaoxing_raw.txt") from exc
    device = "not_used_preflight" if args.check_data_only else "cpu"
    if not args.check_data_only and "cnn" in args.models:
        if args.device == "auto":
            device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
        else:
            device = args.device
        if device == "cuda" and not torch.cuda.is_available():
            raise SystemExit("CUDA unavailable. Install the matching PyTorch CUDA build or choose --device cpu")
        if device == "mps" and not torch.backends.mps.is_available():
            raise SystemExit("MPS unavailable. Choose --device cpu")
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise SystemExit("Output directory is not empty. Use a new --output-dir; prior results are never overwritten.")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    random.seed(args.seed)
    np.random.seed(args.seed)
    write_json(args.output_dir / "environment_check.json", environment)
    log(f"Mode={'PREFLIGHT ONLY' if args.check_data_only else 'TRAINING'}, source=RAW, models={args.models}, windows={args.durations}s")
    units = prepare_cohort(args)
    manifest, dev, test = make_manifest(units, args)
    source_audit = audit_frozen_sources(units, args)
    write_json(args.output_dir / "run_config.json", {
        "mode": "preflight_only" if args.check_data_only else "training",
        "arguments": vars(args), "classes": CLASSES, "packages": environment["packages"],
        "python": sys.version, "platform": platform.platform(), "device": device,
        "script_sha256": sha256_file(__file__), "input_source": "frozen_physionet_raw_plus_original_figshare_si",
        "frozen_input_hashes": FROZEN_SPLIT_HASHES, "source_audit": source_audit,
        "determinism": {"mode": args.determinism, "strict_enforcement": args.determinism == "strict",
                        "note": "warn mode does not guarantee bitwise reproducibility"},
        "auprc_definition": "macro average of per-class one-vs-rest average precision (AP)",
        "final_cnn_training": "All 7,909 development rows; median winning-CV best epoch; no test-based stopping",
    })
    if args.check_data_only:
        write_json(args.output_dir / "PREFLIGHT_COMPLETE.json", {
            "records": len(units), "dev": len(dev), "test": len(test), "data_ready": True,
            "training_environment_ready": environment["ready"], "environment_problems": environment["problems"],
            "source_audit": source_audit, "model_imports": False, "training_performed": False,
        })
        log(f"Data/split preflight PASS. Training environment ready: {environment['ready']}. No models imported or fitted.")
        return
    tensors = prepare_tensors(units, args)
    selected = run_cv(units, manifest, dev, tensors, args, device)
    frozen = refit_and_freeze(units, dev, tensors, selected, args, device)
    test_frozen_models(units, test, tensors, frozen, args, device)
    write_json(args.output_dir / "RUN_COMPLETE.json", {"test_records": len(test), "model_count": len(frozen)})
    log(f"Complete. Results: {args.output_dir}")


if __name__ == "__main__":
    main()
