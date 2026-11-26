# BME4400 Final Project

## Dataset

**A large scale 12-lead electrocardiogram database for arrhythmia study**,
PhysioNet, version 1.0.0 (published 2022-08-24).
https://physionet.org/content/ecg-arrhythmia/1.0.0/ —
DOI [10.13026/wgex-er52](https://doi.org/10.13026/wgex-er52), CC BY 4.0.

Authors: Zheng J, Guo H, Chu H. Original paper: Zheng J, Chu H, Struppa D,
et al. (2020), *Sci Rep* 10, doi:10.1038/s41598-020-59821-7.

The database holds 45,152 12-lead ECG records in WFDB format, each a `.hea`
header and a `.mat` signal file, with diagnoses coded in SNOMED-CT
(`ConditionNames_SNOMED-CT.csv`). It is 5.1 GB uncompressed (2.3 GB as a ZIP).

The records come from two hospitals:

| Part | Hospital | Records | Record IDs |
|---|---|---|---|
| 1 | Chapman University / Shaoxing People's Hospital | 10,247 | JS00001–JS10646 (with gaps) |
| 2 | Ningbo First Hospital | 34,905 | JS10647–JS45551 |

PhysioNet does not say which record came from which hospital. The mapping in
`results/source_data/ecg_arrhythmia_parts.csv` comes from the PhysioNet/CinC
Challenge 2021 v1.0.3 release (DOI 10.13026/34va-7q14), which ships the same
recordings split into `chapman_shaoxing` and `ningbo` folders.

The raw data are not stored in this repository. See
`results/source_data/ecg_arrhythmia_README.md` for download instructions.

## How to reproduce

The plan is in `vcm/VCM.md` (what we claim and how it is judged) and
`prds/PRD.md` (exact procedure). Run every command from this folder
(`FinalProject/`).

**1. Environment.** Every package is pinned to an exact version.

```text
conda env create -f environment.yml
conda activate bme4400-final
python checks/check_environment.py        # every line must say PASS
```

**2. Data, outside the repository** (default `~/bme4191_ecg/`; any other folder
works with `--data-root`).

PhysioNet part 1 (Shaoxing):

```text
python src/download_ecg_arrhythmia.py
```

Do **not** download part 2 (Ningbo). It stays sealed until the models are
frozen (PRD §5 step C2).

figshare *ChapmanECG* files (needed for the labels and the 399 SI records):

```text
mkdir -p ~/bme4191_ecg/figshare_chapman && cd ~/bme4191_ecg/figshare_chapman
curl -L -o Diagnostics.xlsx https://ndownloader.figshare.com/files/15653771
curl -L -o ECGData.zip      https://ndownloader.figshare.com/files/15651326
md5 Diagnostics.xlsx ECGData.zip     # Linux: md5sum
#   Diagnostics.xlsx  f9795256cd8590f8b22f2f8f6762d89e
#   ECGData.zip       2bf32d649e30c5648ba4a5938a1398f8
unzip -q ECGData.zip                 # creates ECGData/ with 10,646 CSV files
cd -
```

**3. Split.** The split is already committed. Rerunning it must give the same
files:

```text
python src/make_split.py
git status results/splits/            # must show no changes
```

`make_split.py` checks every count in VCM §8.1 and stops if one differs. The
split is stratified by label with seed 4400. Every random seed used anywhere
in the analysis is listed in PRD §3.

**4. Feature tables.** The development tables are committed in
`results/features/tables/` (16 features, windows 2, 4, 6, 8 and 10 s).
Rerunning the extraction must reproduce them exactly:

```text
python src/features.py --split dev    # about 4 minutes
git status results/features/          # must show no changes
python src/feature_qc.py              # heart-rate check etc. -> results/features/qc_dev.json
```

Do not run `--split test` until PRD §5 step B3.

**Dataset figures (for presentations).** Six 16:9 PNGs in `report/figures/`
(unit funnel, class counts, example strips, heart rate / age by rhythm, R peaks
per window). They read only the committed split, the committed development
feature tables, figshare metadata and six development records' signals:

```text
python src/make_dataset_figures.py
```

**5. Evidence boundary.** Before every commit:

```text
python checks/check_evidence_boundary.py
```
