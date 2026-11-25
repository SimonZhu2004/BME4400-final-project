# Dataset

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
