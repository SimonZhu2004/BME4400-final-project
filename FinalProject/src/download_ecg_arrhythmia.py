#!/usr/bin/env python3
"""Download PhysioNet "A large scale 12-lead electrocardiogram database for
arrhythmia study" v1.0.0 (ecg-arrhythmia) to a folder OUTSIDE this repository.

The release has two parts, by hospital (results/source_data/ecg_arrhythmia_parts.csv, built
by src/build_ecg_parts_manifest.py):

    part 1  Chapman-Shaoxing   10,247 records  JS00001-JS10646   DOWNLOADED
    part 2  Ningbo             34,905 records  JS10647-JS45551   PROTECTED

By default only part 1 is fetched: its .hea + .mat pairs, the per-folder
RECORDS files of folders that hold only part-1 records, and the top-level
RECORDS, ConditionNames_SNOMED-CT.csv and LICENSE.txt. Part 2 is never fetched
unless you pass --part 2 --unseal-part2, which is a deliberate, recorded step.

Checksums come from PhysioNet's SHA256SUMS.txt for v1.0.0, which is pinned
below (PINNED_SUMS_SHA256), as is the parts manifest, so a changed list is
detected rather than trusted.

Files land in PhysioNet's own layout under --data-root (default
~/bme4191_ecg, an absolute path that does not depend on where you run this):

    <data-root>/ecg-arrhythmia/1.0.0/WFDBRecords/01/010/JS00001.hea

Keep --data-root OUTSIDE this repository: raw recordings must never be
committed, and whatever an AI tool or coding agent can read is inside your
evidence boundary. The resolved folder is printed at the start and the end.

Every file is verified against SHA256SUMS.txt. Re-running is safe: files that
already verify are skipped. Needs only the Python standard library.

Usage (from the repository root; any Python 3.10+ works, no packages needed):

    python src/download_ecg_arrhythmia.py --check            # top-level files + WFDBRecords/01/010 only (~13 MB)
    python src/download_ecg_arrhythmia.py                    # all of part 1 (Shaoxing; 20,494 record files, ~1.2 GB)
    python src/download_ecg_arrhythmia.py --folder 01 --folder 02/020
    python src/download_ecg_arrhythmia.py --data-root /some/other/place
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import sys
import time
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

DATASET, VERSION = "ecg-arrhythmia", "1.0.0"
MIRROR = f"https://physionet-open.s3.amazonaws.com/{DATASET}/{VERSION}/"
ORIGIN = f"https://physionet.org/files/{DATASET}/{VERSION}/"
SUMS_URL = ORIGIN + "SHA256SUMS.txt"
# sha256 of SHA256SUMS.txt as fetched from SUMS_URL on 2026-11-04 (8,711,012 bytes, 90,759 lines).
PINNED_SUMS_SHA256 = "dfad0c26a276ce7e450e5002051f4c749304552d9add4d592928bbdcb6e4f31c"
EXPECTED = {"files": 90759, "hea": 45152, "mat": 45152}
CHECK_FOLDER = "01/010"
PARTS_MANIFEST = Path(__file__).resolve().parents[1] / "results" / "source_data" / "ecg_arrhythmia_parts.csv"
PINNED_PARTS_SHA256 = "6720d3b3177bfce0eefa93e92275cd7f0b7b9fa7216ee3fa6c72181b75cc0d1a"
PART_NAMES = {1: "Chapman-Shaoxing", 2: "Ningbo (PROTECTED)"}
REPO_ROOT = Path(__file__).resolve().parents[1]


def sha256_of(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def http_get(url: str, dest: Path, timeout: int = 120) -> int:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".part")
    with urllib.request.urlopen(url, timeout=timeout) as r, tmp.open("wb") as f:
        expected = r.headers.get("Content-Length")
        n = 0
        for chunk in iter(lambda: r.read(1 << 20), b""):
            f.write(chunk)
            n += len(chunk)
    if expected is not None and int(expected) != n:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"short read {n}/{expected} for {url}")
    os.replace(tmp, dest)
    return n


def load_sums(root: Path, url: str, allow_unpinned: bool) -> dict[str, str]:
    path = root / "SHA256SUMS.txt"
    if not path.exists() or sha256_of(path) != PINNED_SUMS_SHA256:
        print(f"fetching checksums from {url}", flush=True)
        http_get(url, path, timeout=300)
    got = sha256_of(path)
    if got != PINNED_SUMS_SHA256 and not allow_unpinned:
        sys.exit(f"SHA256SUMS.txt does not match the pinned checksum (got {got[:12]}, want "
                 f"{PINNED_SUMS_SHA256[:12]}). PhysioNet's list changed; stop and investigate "
                 "(--allow-unpinned-sums overrides, and must be recorded).")
    sums: dict[str, str] = {}
    for line in path.read_text().splitlines():
        parts = line.split(maxsplit=1)
        if len(parts) == 2:
            sums[parts[1].strip()] = parts[0]
    n_hea = sum(k.endswith(".hea") for k in sums)
    n_mat = sum(k.endswith(".mat") for k in sums)
    if (len(sums), n_hea, n_mat) != (EXPECTED["files"], EXPECTED["hea"], EXPECTED["mat"]) and not allow_unpinned:
        sys.exit(f"unexpected checksum list contents: {len(sums)} files, {n_hea} .hea, {n_mat} .mat")
    return sums


def files_for_part(sums: dict[str, str], part: int) -> list[str]:
    if sha256_of(PARTS_MANIFEST) != PINNED_PARTS_SHA256:
        sys.exit(f"{PARTS_MANIFEST} does not match its pinned checksum; it was edited. Rebuild it with "
                 "src/build_ecg_parts_manifest.py and investigate before downloading anything.")
    part_of: dict[str, int] = {}
    with PARTS_MANIFEST.open(newline="") as f:
        for row in csv.DictReader(f):
            part_of[row["record"]] = int(row["part"])
    folder_parts: dict[str, set[int]] = defaultdict(set)
    for rel in sums:
        if rel.endswith(".hea"):
            folder_parts["/".join(rel.split("/")[:3])].add(part_of[Path(rel).stem])
    keep = []
    for rel in sums:
        if rel == "SHA256SUMS.txt":
            continue
        if not rel.startswith("WFDBRecords/"):
            keep.append(rel)                                   # top-level RECORDS, csv, LICENSE
        elif rel.endswith("/RECORDS"):
            if folder_parts["/".join(rel.split("/")[:3])] == {part}:
                keep.append(rel)                               # folder holds only this part
        elif part_of[Path(rel).stem] == part:
            keep.append(rel)
    return keep


def group_of(rel: str) -> str:
    parts = rel.split("/")
    return "/".join(parts[1:3]) if parts[0] == "WFDBRecords" and len(parts) >= 4 else "(top level)"


def fetch_group(name: str, files: list[str], root: Path, base_url: str, sums: dict[str, str],
                attempts: int = 4) -> dict:
    res = {"group": name, "ok": True, "fetched": 0, "skipped": 0, "bytes": 0, "errors": []}
    for rel in files:
        dest, want = root / rel, sums[rel]
        if dest.exists() and sha256_of(dest) == want:
            res["skipped"] += 1
            res["bytes"] += dest.stat().st_size
            continue
        last = None
        for i in range(attempts):
            try:
                n = http_get(base_url + rel, dest)
                got = sha256_of(dest)
                if got != want:
                    dest.unlink(missing_ok=True)
                    raise RuntimeError(f"sha256 mismatch: got {got[:12]} want {want[:12]}")
                res["fetched"] += 1
                res["bytes"] += n
                last = None
                break
            except Exception as e:  # noqa: BLE001
                last = f"{rel}: {type(e).__name__}: {e}"
                time.sleep(3 * (i + 1))
        if last:
            res["ok"] = False
            res["errors"].append(last)
    return res


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-root", default=str(Path.home() / "bme4191_ecg"),
                    help="where the raw files go; must be outside the repository (default ~/bme4191_ecg)")
    ap.add_argument("--folder", action="append", metavar="NN[/NNN]",
                    help="fetch only this WFDBRecords folder (repeatable), e.g. --folder 01 or --folder 01/010")
    ap.add_argument("--check", action="store_true",
                    help=f"fetch top-level files + WFDBRecords/{CHECK_FOLDER} only, to catch path/network problems first")
    ap.add_argument("--part", type=int, choices=[1, 2], default=1,
                    help="which hospital part to fetch (default 1 = Chapman-Shaoxing); 2 is protected")
    ap.add_argument("--unseal-part2", action="store_true",
                    help="required with --part 2: confirms the protected Ningbo part is being released on purpose")
    ap.add_argument("--base-url", default=MIRROR, help=f"file source (default mirror {MIRROR}; origin {ORIGIN})")
    ap.add_argument("--sums-url", default=SUMS_URL)
    ap.add_argument("--allow-unpinned-sums", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--workers", type=int, default=16)
    a = ap.parse_args()

    if a.part == 2 and not a.unseal_part2:
        sys.exit("part 2 (Ningbo) is PROTECTED. Fetching it is a deliberate step: record why in the VCM/PRD, "
                 "then re-run with --part 2 --unseal-part2.")
    data_root = Path(a.data_root).expanduser().resolve()
    if data_root == REPO_ROOT or REPO_ROOT in data_root.parents:
        sys.exit(f"--data-root {data_root} is inside the repository; choose a folder outside it")
    root = data_root / DATASET / VERSION
    root.mkdir(parents=True, exist_ok=True)
    print(f"raw data folder: {root}", flush=True)

    sums = load_sums(root, a.sums_url, a.allow_unpinned_sums)
    groups: dict[str, list[str]] = defaultdict(list)
    for rel in files_for_part(sums, a.part):
        groups[group_of(rel)].append(rel)
    print(f"part {a.part}: {PART_NAMES[a.part]}", flush=True)

    wanted = [CHECK_FOLDER] if a.check else a.folder
    if wanted:
        wanted = [w.strip().strip("/") for w in wanted]
        sel = {g: f for g, f in groups.items()
               if g == "(top level)" or any(g == w or g.startswith(w + "/") for w in wanted)}
        if len(sel) == 1:
            sys.exit(f"no WFDBRecords folder matches {wanted}")
        groups = sel
    full = not wanted
    n_files = sum(len(v) for v in groups.values())
    free = shutil.disk_usage(root).free
    print(f"{len(groups)} folder(s), {n_files} file(s) selected; "
          f"already-verified files are skipped; {free / 1e9:.1f} GB free", flush=True)

    t0 = time.time()
    results = []
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = [ex.submit(fetch_group, g, sorted(fs), root, a.base_url, sums) for g, fs in sorted(groups.items())]
        for n, f in enumerate(as_completed(futs), 1):
            r = f.result()
            results.append(r)
            tag = (f"ok  ({r['fetched']} fetched, {r['skipped']} already verified)" if r["ok"]
                   else "ERR " + " | ".join(r["errors"][:3]))
            print(f"[{n:3d}/{len(groups)}] {r['group']} {tag} ({time.time() - t0:.0f}s)", flush=True)
    results.sort(key=lambda r: r["group"])
    failed = [r["group"] for r in results if not r["ok"]]
    total = sum(r["bytes"] for r in results)
    elapsed = round(time.time() - t0, 1)
    if full:
        inv = {
            "dataset": f"{DATASET} {VERSION}",
            "part": a.part,
            "part_name": PART_NAMES[a.part],
            "parts_manifest_sha256": PINNED_PARTS_SHA256,
            "doi": "10.13026/wgex-er52",
            "source": a.base_url,
            "checksums": a.sums_url,
            "checksums_sha256": sha256_of(root / "SHA256SUMS.txt"),
            "data_root": str(root),
            "n_files": n_files,
            "n_folders_ok": len(results) - len(failed),
            "failed_folders": failed,
            "total_bytes": total,
            "elapsed_s": elapsed,
            "finished_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        (data_root / f"download_inventory_part{a.part}.json").write_text(json.dumps(inv, indent=2))
    print(f"done: {len(results) - len(failed)}/{len(results)} folder(s) verified, {total / 1e6:.0f} MB, {elapsed} s",
          flush=True)
    print(f"raw data folder: {root}", flush=True)
    if failed:
        print(f"FAILED: {', '.join(failed)} — re-run the same command; verified files are skipped", flush=True)
        return 1
    if a.check:
        print("check OK — now run the same command without --check to fetch everything", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
