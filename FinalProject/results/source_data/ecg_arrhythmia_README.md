# Raw source data: what to download, where it goes

**Source:** PhysioNet, *A large scale 12-lead electrocardiogram database for
arrhythmia study*, version 1.0.0 (published 2022-08-24) —
https://physionet.org/content/ecg-arrhythmia/1.0.0/ —
DOI [10.13026/wgex-er52](https://doi.org/10.13026/wgex-er52), CC BY 4.0.
Citation: Zheng J, Guo H, Chu H; original paper Zheng J, Chu H, Struppa D, et
al. (2020), *Sci Rep* 10, doi:10.1038/s41598-020-59821-7.

## What is included

Everything listed in PhysioNet's `SHA256SUMS.txt` for v1.0.0
(sha256 `dfad0c26a276ce7e450e5002051f4c749304552d9add4d592928bbdcb6e4f31c`,
90,759 lines, fetched 2026-11-04):

| Files | Count |
|---|---|
| `WFDBRecords/NN/NNN/JSxxxxx.hea` (WFDB header) | 45,152 |
| `WFDBRecords/NN/NNN/JSxxxxx.mat` (signal) | 45,152 |
| `WFDBRecords/NN/NNN/RECORDS` | 452 |
| `RECORDS`, `ConditionNames_SNOMED-CT.csv`, `LICENSE.txt` | 3 |

PhysioNet lists 5.1 GB uncompressed (2.3 GB as a ZIP). These counts come from
the checksum list only; no record has been opened yet. What the records
contain belongs in `dra/DRA.md`, not here.

## Two parts, by hospital: part 1 downloaded, part 2 protected

| Part | Hospital | Records | Record IDs | Status |
|---|---|---|---|---|
| 1 | Chapman University / Shaoxing People's Hospital | 10,247 | JS00001–JS10646 (with gaps) | downloaded |
| 2 | Ningbo First Hospital | 34,905 | JS10647–JS45551 | **protected: not downloaded** |

The ecg-arrhythmia page names both hospitals but does not say which record
came from which. The mapping comes from the PhysioNet/CinC Challenge 2021
v1.0.3 release (DOI 10.13026/34va-7q14), which ships the same recordings in
`training/chapman_shaoxing/` (10,247) and `training/ningbo/` (34,905).
`src/build_ecg_parts_manifest.py` joins the two releases by record ID
using only their published `SHA256SUMS.txt` files and writes
`ecg_arrhythmia_parts.csv` (`record, folder, hospital, part`). It refuses to
write unless the join is exact. On 2026-11-04 it was: every record falls in
exactly one hospital, the counts match the Challenge page, and all 45,152
`.mat` files are byte-identical across the two releases (the `.hea` files all
differ, so headers were rewritten between releases).

One Challenge quirk: Ningbo record JS23074 has a `.mat` but no `.hea` in the
Challenge checksum list; it is assigned by its `.mat` path.

Folder `WFDBRecords/11/112` holds 47 part-1 and 53 part-2 records. Its
`RECORDS` file is not downloaded (it would name part-2 records); use the
parts manifest as the record list.

Part 2 is never fetched unless you pass `--part 2 --unseal-part2`. Treat
that as a recorded decision (VCM/PRD), not a convenience.

## Where the files go: outside this repository

By default `~/bme4191_ecg/`, in PhysioNet's layout (part 1 only):

```text
~/bme4191_ecg/ecg-arrhythmia/1.0.0/WFDBRecords/01/010/JS00001.hea
~/bme4191_ecg/ecg-arrhythmia/1.0.0/SHA256SUMS.txt
~/bme4191_ecg/download_inventory_part1.json    (written after a full part-1 download)
```

Pass `--data-root /some/other/place` to change it; the script refuses a folder
inside this repository. `.gitignore` blocks `*.hea`, `*.mat`, `*.dat`; that is
hygiene, not an access boundary. `python checks/check_evidence_boundary.py`
must pass.

## Download

From the repository root (any Python 3.10+; standard library only):

```text
python src/download_ecg_arrhythmia.py --check              # top level + WFDBRecords/01/010 (~200 files)
python src/download_ecg_arrhythmia.py                      # all of part 1: 20,599 files
python src/download_ecg_arrhythmia.py --folder 01 --folder 02/020   # part-1 records in these folders
```

Files come from PhysioNet's open S3 mirror
(`https://physionet-open.s3.amazonaws.com/ecg-arrhythmia/1.0.0/`); use
`--base-url https://physionet.org/files/ecg-arrhythmia/1.0.0/` for the origin.
The checksum list and the parts manifest are pinned: if PhysioNet's `SHA256SUMS.txt` ever changes, the
script stops instead of trusting it. Every file is verified against that list,
and re-running skips files that already verify.
