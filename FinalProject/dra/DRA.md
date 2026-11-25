# Data Reality Audit (DRA) — PhysioNet ecg-arrhythmia v1.0.0, part 1 (Chapman-Shaoxing)

This file keeps one name; Git history holds its versions.

---

## How to use this template

This template is for **your own** audit of a dataset — a record of what you've established about the data before deciding what you want them to mean. It is not a group deliverable and not something synthesized from other students' work.

Fill in the sections your assignment tells you to complete. **Do not delete the others.** For any section that doesn't apply yet, keep the heading and write:

> _Not applicable at this version._

Keeping every heading in place means this file diffs cleanly against later versions.

A DRA is not a judgment. It does not decide whether a dataset is good, useful, sufficient, or worth a particular analysis — those are separate, later decisions (they belong in your VCM). A DRA's only job is to say, carefully and in your own words, what you actually know and don't yet know about the data themselves.

---

## 1. Purpose and epistemic boundary

The Data Reality Audit records **what the data and their documentation say before you decide what you want them to mean**. It preserves four kinds of statements:

- **D - Documented:** the authoritative source states it.
- **O - Observed:** your own direct inspection of the released records establishes it.
- **I - Inferred:** it follows reasonably from documented and/or observed evidence but is not itself directly stated or observed.
- **U - Unresolved:** the available documentation and your own inspection do not settle it.

A missing answer is not silently completed. A discrepancy is not silently reconciled. An inference is not promoted into an observation.

_State exactly what you inspected: the instructions this audit responds to, the authoritative documentation (source/DOI/version), the released files you opened, and how you inspected them._

**Instructions.** Project 5, Question 2 (wording in `vcm/VCM.md` §1, v0): classifying cardiac rhythms from features of 12-lead ECGs in the dataset from one clinical location.

**Scope.** This audit covers **part 1 only**: the 10,247 records from Chapman University / Shaoxing People's Hospital. Part 2 (Ningbo First Hospital, 34,905 records) is protected. It was not downloaded or opened, and nothing here describes it. "The release" below means part 1 unless stated otherwise.

**Authoritative documentation read.**
- PhysioNet project page, *A large scale 12-lead electrocardiogram database for arrhythmia study*, v1.0.0 (DOI 10.13026/wgex-er52), and its file index and `SHA256SUMS.txt`.
- Zheng J, Zhang J, Danioko S, et al. *A 12-lead electrocardiogram database for arrhythmia research covering more than 10,000 patients.* Sci Data 7, 48 (2020), doi:10.1038/s41597-020-0386-x. The ecg-arrhythmia page cites it; I read it as the open-access full text on Europe PMC (PMC7016169). Only the text up to and including Table 2 was read verbatim. Later sections (Data Records, Technical Validation) were not, and nothing from them is used here.
- PhysioNet/CinC Challenge 2021 v1.0.3 page (DOI 10.13026/34va-7q14), its `training/` folder listing and its `SHA256SUMS.txt`. These were used only to map records to hospitals (see §2).

**Released files opened.** All 10,247 `.hea` and 10,247 `.mat` files of part 1. Also `ConditionNames_SNOMED-CT.csv`, the top-level `RECORDS`, the 103 per-folder `RECORDS` files of part 1, and `SHA256SUMS.txt`.

**How.** With `src/dra_inspect.py`, which parses every header, loads every `.mat` with `scipy.io.loadmat`, re-verifies every file's SHA-256, and counts. It computes no features and fits no model. It ran under Python 3.13.18, numpy 2.5.4 and scipy 1.18.1, and wrote `results/dra/`. A few headers and the condition table were also read by eye. Every [O] number below comes from `results/dra/dra_summary.json`, `dx_code_counts.csv`, `rhythm_cooccurrence.csv` or `record_table_part1.csv`.

**Repair, 2026-11-12 (Assignment 5.4, U1 and U9).** I also inspected the **original 10,646-record Chapman-Shaoxing release on figshare** (collection *ChapmanECG*, id 4560497, files published 2019-06-30), which D3 names as the first home of this data:
- `Diagnostics.xlsx`, `AttributesDictionary.xlsx`, `RhythmNames.xlsx`, `ConditionNames.xlsx` (all four read in full).
- `ECGData.zip` (the raw-signal CSVs).

`src/figshare_check.py` (standard library only) pairs the figshare metadata with part 1 and tabulates ventricular rate by rhythm; `src/figshare_signal_check.py` compares the figshare signals with the part-1 `.mat` files. Neither computes features or fits anything. Outputs are in `results/figshare_check/`. The new statements are O21–O30 and D17–D19 below.

## 2. Dataset identity and acquisition record

_Name the dataset, its authoritative ID/DOI/version and the released files used, and say how you actually acquired and inspected them._

- **Dataset:** *A large scale 12-lead electrocardiogram database for arrhythmia study*, PhysioNet, version 1.0.0, published 2022-08-24, DOI 10.13026/wgex-er52, CC BY 4.0. Authors: Zheng J, Guo H, Chu H.
- **Part definition:** `results/source_data/ecg_arrhythmia_parts.csv` (sha256 `6720d3b3…cc0d1a`), built by `src/build_ecg_parts_manifest.py`.
  - The builder joins this release with the Challenge 2021 release by record ID.
  - Part 1 is every record that the Challenge places in `training/chapman_shaoxing/`: 10,247 records, JS00001–JS10646.
  - The builder also confirmed that all 45,152 `.mat` files are byte-identical across the two releases.
  - The hospital assignment therefore rests on the Challenge folder names [D, Challenge 2021], not on anything inside the ecg-arrhythmia files.
- **Acquisition:** `src/download_ecg_arrhythmia.py` downloaded the files on 2026-11-04 (finished 21:54:12 UTC).
  - Source: the PhysioNet open S3 mirror.
  - Each file was verified against the release's `SHA256SUMS.txt`; that list's own sha256 is pinned at `dfad0c26…e4f31c`.
  - Result: 20,599 files, 1,236,922,396 bytes, 0 failures (`~/bme4191_ecg/download_inventory_part1.json`).
- **Location:** outside the repository, at `~/bme4191_ecg/ecg-arrhythmia/1.0.0/`.
- **Re-check during the audit:** `src/dra_inspect.py` re-hashed all 20,494 record files. 0 were missing and 0 failed the checksum [O]. The script confirmed that no part-2 record is present under the data root before it ran [O].
- **Original figshare release (repair, 2026-11-12):** downloaded with `curl` from the figshare API download links on 2026-11-11/12 to `~/bme4191_ecg/figshare_chapman/`, outside the repository. Every file's MD5 equals the MD5 figshare publishes:

  | File | figshare file id | Bytes | MD5 |
  |---|---|---|---|
  | `Diagnostics.xlsx` | 15653771 | 975,796 | `f9795256cd8590f8b22f2f8f6762d89e` |
  | `AttributesDictionary.xlsx` | 15653762 | 9,960 | `7c12a7053721aadb292d2d56e9d7d372` |
  | `RhythmNames.xlsx` | 15651296 | 8,756 | `a7af9552e948e073fbcbc72485b8ab12` |
  | `ConditionNames.xlsx` | 15651293 | 9,906 | `a37bbf63b9a179a89866f1879c6f824b` |
  | `ECGData.zip` | 15651326 | 754,581,129 | `2bf32d649e30c5648ba4a5938a1398f8` |

  `ECGDataDenoised.zip` (2.0 GB) was not downloaded.

## 3. What the documentation states

_List every [D] statement the authoritative documentation asserts about the dataset; record any tension with what you observe in §8 rather than correcting it here._

From the **PhysioNet ecg-arrhythmia v1.0.0 page**:
- D1. The database "consists of 45,152 patient ECGs", 12-lead, with a 500 Hz sampling rate. It "features multiple common rhythms and additional cardiovascular conditions, all labeled by professional experts."
- D2. It was created under Chapman University, Shaoxing People's Hospital (Shaoxing Hospital Zhejiang University School of Medicine) and Ningbo First Hospital. No per-record hospital is given.
- D3. "Initially, the part of this database (10,646 patient) was shared at figshare", then moved to PhysioNet and "increased … to 45,152".
- D4. Each ECG was "a 12-lead resting ECG test that was taken over a period of 10 seconds".
- D5. Labelling: "a licensed physician labeled the rhythm and other cardiac conditions. Another licensed physician performed a secondary validation. If there was a disagreement, a senior physician intervened and made a final decision."
- D6. The data were stored in the GE MUSE ECG system and exported to XML, then converted to CSV, then to WFDB.
- D7. Each ECG is "a mat-file containing the binary raw data and a corresponding header file". The header contains "lead configuration, age, gender, and SNOMED CT code". `ConditionNames_SNOMED-CT` maps the original acronyms to SNOMED CT codes.
- D8. "The number of volts per A/D bit is 4.88, and A/D converter had 32-bit resolution. The amplitude unit was microvolt."
- D9. Additional conditions (e.g. PVC, RBBB, LBBB, APB) were "applied to the entire sample rather than to specified beats."
- D10. The institutional review board allowed sharing after de-identification, and informed consent was waived.
- D11. Records are organised as `WFDBRecords/` → 46 first-level folders → 10 subfolders each → up to 100 records.

From **Zheng et al. 2020 (Sci Data)**, about the original 10,646-ECG Shaoxing release:
- D12. Table 2 rhythm frequencies: SB 3,889, SR 1,826, AFIB 1,780, ST 1,568, AF (atrial flutter) 445, SI (sinus irregularity) 399, SVT 587, AT 121, AVNRT 16, AVRT 8, SAAWR 7. All: 10,646. Male 5,956 (55.95%). The SI row lists male 223.
- D13. "Our data consists of 10,646 patient ECGs including 5,956 males and 4,690 females." Table 1 gives Subjects 10646 and Records "10646 (10 second)".
- D14. Table 1 gives the age column as "4–98".
- D15. The amplitude limits are 32,767 and −32,768.

From the **Challenge 2021 v1.0.3 page**:
- D16. "Chapman-Shaoxing … 10,247 recordings" and "Ningbo … 34,905 recordings". The two together are the 45,152 ECGs of this source, each 10 s at 500 Hz.

From the **figshare ChapmanECG collection** (repair, 2026-11-12):
- D17. `AttributesDictionary.xlsx` describes `Diagnostics.xlsx`: FileName is the "ECG data file name(unique ID)", Rhythm is the "Rhythm Label", Beat holds "Other conditions Label", and VentricularRate is "Ventricular rate in BPM". Age has range "0-999". Nothing states who or what produced VentricularRate.
- D18. `RhythmNames.xlsx` lists 11 rhythm acronyms, including **"SI" = Sinus Irregularity** (and "AF" = Atrial Flutter, "AFIB" = Atrial Fibrillation).
- D19. The collection's files were published on figshare on 2019-06-30 (figshare API metadata).

## 4. What the released file(s) actually contain

_What you actually counted and checked: dimensions, distinct units and records per unit, missing values, duplicates, ranges, anything structurally unexpected._

**Files and IDs**
- O1. 10,247 records, each with one `.hea` and one `.mat`, and all checksums verified.
- O2. IDs run from JS00001 to JS10646. 399 IDs in that range do not exist.
- O3. Records sit in folders `01/010` to `11/112`, with 100 per subfolder except at the boundary.
- O4. Each per-folder `RECORDS` file matches the records present. The `RECORDS` file of the mixed folder `11/112` (47 part-1 and 53 part-2 records) was not downloaded on purpose.

**Signals (`.mat`)**
- O5. Every file holds exactly one variable, `val`, of type int16 and shape 12 × 5000.
- O6. Values across all records range from −17,080 to 19,681 ADU. No sample equals −32,768 or 32,767.
- O7. In every record, the first sample of each lead equals the header's "initial value".
- O8. Every lead's checksum (sum mod 2¹⁶) agrees with the header. One lead (JS10055, aVR) writes −32,768 as 32768.
- O9. **15 records have at least one lead that is entirely zero:**

  | Zero leads | Records | Record IDs |
  |---|---|---|
  | 1 | 9 | JS00459, JS01040, JS01266, JS05212, JS05815, JS09412, JS10475, JS10477, JS10480 |
  | 2 | 1 | JS07788 |
  | 3 | 1 | JS02826 |
  | 6 | 4 | JS02113, JS04173, JS04957, JS06200 |

  Only chest leads are affected: V6 in 14 records, V2 in 6, V4 and V5 in 5 each, V1 and V3 in 4 each. No other lead is constant.
- O10. **13 pairs of records have byte-identical `.mat` files.** Within each pair, the Age, Sex and Dx are also identical:
  - JS01451/JS06490, JS01827/JS03435, JS02026/JS03005, JS02989/JS05900, JS05752/JS08755, JS09908/JS10086
  - JS10293/JS10614, JS10294/JS10617, JS10295/JS10612, JS10296/JS10625, JS10297/JS10628, JS10298/JS10609, JS10299/JS10624

  The last seven pairs are all SVT-labelled.

**Headers (`.hea`)**
- O11. 10,246 headers declare `12 500 5000`, i.e. 12 signals at 500 Hz with 5,000 samples (10 s). The lead order is I, II, III, aVR, aVL, aVF, V1–V6.
- O12. **JS01052's header is malformed.** Its first line, `JS01052 12 500 500000/mV 16 0 15 31255 0 I`, merges the record line with lead I's signal line, so only 11 signal lines (II–V6) are described. Its `.mat` file is a normal 12 × 5000 array.
- O13. All 122,963 signal lines show `fmt 16+24`, gain `1000/mV`, ADC resolution 16, ADC zero 0 and baseline 0.
- O14. **1,000 headers carry a base time and date; no other header does.** These are exactly the records in folders `09/090`–`09/099`. The values run from `24-Mar-2021 05:29:25` to `24-Mar-2021 06:34:48`.
- O15. Comment fields are Age, Sex, Dx, Rx, Hx and Sx, with no other keys. Rx, Hx and Sx are "Unknown" in all 10,247 records. **No header has a patient identifier.**

**Demographics and diagnoses**
- O16. Age is an integer in every record: range 4–89, median 62, IQR 50–72. 144 records are under 18, and none is 90 or over.
- O17. Sex is Male in 5,733 records and Female in 4,514, with no missing or other values.
- O18. Every record has at least one Dx code, and no code repeats within a record. The number of codes per record is: 1 → 5,141; 2 → 2,955; 3 → 1,277; 4 → 556; 5 → 210; 6 → 76; 7 → 26; 8 → 5; 10 → 1.
- O19. 54 distinct Dx codes occur. **Four of them are not in `ConditionNames_SNOMED-CT.csv`:**
  - 55827005 in 1,295 records
  - 251166008 in 16
  - 67751000119106 in 8
  - 17366009 in 7
- O20. `ConditionNames_SNOMED-CT.csv` has 63 rows but only 55 distinct codes, because four codes are shared by several acronyms:
  - 164865005 = MI, MIBW, MIFW, MILW, MISW
  - 164909002 = LBBB, LBBBB, LFBBB
  - 698252002 = IDC, IVB
  - 195101003 = WAVN, SAAWR

**Original figshare release (repair, 2026-11-12; `results/figshare_check/summary.json`, `id_alignment.csv`, `rate_by_rhythm.csv`)**
- O21. `Diagnostics.xlsx` has 10,646 data rows and 16 columns (FileName, Rhythm, Beat, PatientAge, Gender, VentricularRate, AtrialRate, QRSDuration, QTInterval, QTCorrected, RAxis, TAxis, QRSCount, QOnset, QOffset, TOffset). Its Rhythm counts equal the paper's Table 2 (D12) exactly: SB 3,889, SR 1,826, AFIB 1,780, ST 1,568, SVT 587, AF 445, **SA 399**, AT 121, AVNRT 16, AVRT 8, SAAWR 7. The 399 SA rows are 223 male and 176 female. The rhythm column writes sinus irregularity as **"SA"**, not "SI" as in `RhythmNames.xlsx` (D18).
- O22. **Row order pairs the two releases.** I compared JS id *k* with data row *k* of `Diagnostics.xlsx` (file order, not sorted). Of the 10,247 part-1 records, 10,056 agree on age, sex and rhythm together; all 10,247 agree on sex. As a control, the same comparison after sorting the rows by FileName agrees for only 61 records.
- O23. **Every one of the 191 disagreements has one of two explanations.**
  - 166 differ only in age: part 1 says 89 and figshare says 90–98. The figshare file has 168 ages ≥ 90; the other 2 are SA rows (absent from part 1).
  - 25 differ only in rhythm: the 16 records with code 251166008 are AVNRT in figshare, the 7 with code 17366009 are SAAWR, and the 2 records with SB + 195101003 are plain SB.
- O24. **The 399 absent JS ids are exactly the 399 SA rows.** Under the row pairing, every absent id falls on an SA row (399 of 399), and every SA row falls on an absent id. Their sex split is 223 male / 176 female.
- O25. **The SB / SR / ST labels follow the 60 / 100 bpm thresholds on VentricularRate.** With the rule "< 60 → SB, 60–100 → SR, > 100 → ST", 7,253 of the 7,283 sinus-labelled records agree. The 30 that do not: SB labelled at 60–103 bpm (21), SR at 58 or 101–115 (5), ST at 35–100 (4).
- O26. VentricularRate by label (min / 5th pct / median / 95th pct / max, bpm):

  | Label | n | min | p5 | median | p95 | max | < 60 | 60–100 | > 100 |
  |---|---|---|---|---|---|---|---|---|---|
  | SB | 3,889 | 34 | 47 | 56 | 59 | 103 | 3,868 | 20 | 1 |
  | SR | 1,826 | 58 | 62 | 74 | 94 | 115 | 1 | 1,821 | 4 |
  | ST | 1,568 | 35 | 101 | 108 | 136 | 175 | 2 | 2 | 1,564 |
  | SA (SI) | 399 | 42 | 60 | 72 | 92 | 108 | 18 | 376 | 5 |
  | AFIB | 1,780 | 39 | 59 | 91 | 148 | 225 | 92 | 1,067 | 621 |
  | AF (flutter) | 445 | 37 | 63 | 115 | 168 | 263 | 16 | 147 | 282 |
- O27. The figshare FileName has the form `MUSE_YYYYMMDD_hhmmss_NNNNN` (e.g. `MUSE_20180113_171327_27000` for JS00001).

**Figshare signals (`results/figshare_check/signal_summary.json`, `signal_match.csv`)**
- O28. `ECGData.zip` holds 10,646 CSV files, one per `Diagnostics.xlsx` FileName. Every file has the header `I,II,III,aVR,aVL,aVF,V1,…,V6` and 5,000 rows × 12 columns. No value is missing.
- O29. **Every figshare value is an integer multiple of 4.88** (all 10,646 files).
- O30. **The part-1 `.mat` signals are the figshare signals rounded to integers.** For all 10,247 paired records, `val` (transposed) equals `round(csv)` exactly, sample for sample and lead for lead. Least-squares scale between the two: 0.99980–1.00003; largest residual 0.71; every lead correlates ≥ 0.999 with the same lead.
- O31. **The 399 SA records have complete signals in figshare**: 399 of 399 CSVs exist, all 5,000 × 12, no missing values, values on the same 4.88 grid, range −6,763.68 to 6,710.00. Applying the O9 check (a lead that is all zero) to them: **2 SA records have all-zero leads**, JS00730 (6 leads) and JS08765 (5 leads). This check was run by hand in a one-line script on 2026-11-12, not by the committed scripts.
- O32. **Each of the 13 byte-identical part-1 pairs (O10) maps to two different figshare FileNames with different timestamps**, e.g. JS01451 → `MUSE_20180111_155249_70000` and JS06490 → `MUSE_20180113_121829_13000`. For the seven SVT pairs, one member is stamped 2018-07-12 15:06–15:07 and the other 2018-12-22 20:41–20:42.

## 5. Record unit and observational hierarchy

_What one record represents [D], how records relate to higher-level units [O], and the hierarchy that follows [I], without deciding what analytical unit you'll use._

- [D] One record is one 10-s, 12-lead resting ECG, stored as a `.hea` + `.mat` pair (D4, D7). The documentation counts "patient ECGs" (D1, D13). The 2020 paper gives equal subject and record counts (10,646).
- [O] Records sit in a storage hierarchy, `WFDBRecords/NN/NNN/`, of up to 100 records per folder (O3). Nothing in a record links it to a patient, visit or date, apart from the 1,000 base times in O14 (O15).
- [O] 13 pairs of records are byte-identical in signal and metadata (O10).
- [I] **One ECG corresponds to one individual patient.** The Zheng et al. 2020 paper describes the original Shaoxing release as "10,646 patient ECGs" and gives equal counts of subjects and records (10,646 each) in Table 1 (D13). Part 1 is a subset of that release (D3, D16), so I take each part-1 record to be a different patient. This is inferred from the documentation, not observed: no header carries a patient identifier (O15).
- [I] The hierarchy that follows is: hospital (part 1 = Shaoxing, from the Challenge folders) → patient = record → 12 leads × 5,000 samples. Labels and demographics are attached at the record and patient level.
- [I] The storage folders follow ID order (O3), so they look like a filing scheme rather than a clinical grouping.
- [U] The one-to-one inference cannot be confirmed from the files, because there is no patient ID (U5). The 13 identical pairs (O10) are in tension with it: each looks like one ECG released twice under two IDs. Whether that is what they are is unresolved (U6).
- [O] Repair: JS id *k* corresponds to `Diagnostics.xlsx` row *k* and to the figshare file named in that row (O22, O30). The 399 SA records therefore have a well-defined place in the same ID scheme (O24); they are records of the same kind, from the same export, as the other 10,247.

## 6. Central recorded quantities and their construction

_For each key variable your analysis will likely depend on: the recorded field, its documented description, what follows about its construction, and what is not established._

**Rhythm label: the `#Dx:` field (comma-separated SNOMED CT codes).**
- [D] Labelled by one physician, validated by a second, with disagreements decided by a senior physician (D5). Mapped from acronyms to SNOMED CT (D7).
- [O] Records with exactly one rhythm code:

  | Rhythm (table acronym) | Code | Records with it as the only rhythm code |
  |---|---|---|
  | Sinus bradycardia (SB) | 426177001 | 3,887 |
  | Sinus rhythm (SR) | 426783006 | 1,826 |
  | Atrial fibrillation (**AFIB**) | 164889003 | 1,780 |
  | Sinus tachycardia (ST) | 427084000 | 1,568 |
  | Supraventricular tachycardia (SVT) | 426761007 | 587 |
  | Atrial flutter (**AF** in the table) | 164890007 | 445 |
  | Atrial tachycardia (AT) | 713422000 | 121 |
  | AV reentrant tachycardia (AVRT) | 233897008 | 8 |
  | **Sinus irregularity (SA)** | 427393009 | **0** in part 1. The 399 SI records are the 399 absent IDs (O24, §8 item 1); they exist in the figshare release |

- [O] Rhythm codes are almost exclusive within a record:
  - 10,222 records carry exactly one of the 11 rhythm codes in the condition table.
  - 2 records carry two: SB plus 195101003, a code shared by WAVN and SAAWR.
  - 23 records carry none. All 23 carry 251166008 (16 records) or 17366009 (7 records), which are not in the table (O19).
- [I] In part 1 the rhythm is effectively a single label per record. The non-rhythm conditions are what make records multi-label (O18).
- [I] The table uses **"AF" for atrial flutter** and **"AFIB" for atrial fibrillation**. Any reading of "AF" has to say which one it means.
- [O] In this release 251166008 marks the 16 AVNRT records and 17366009 the 7 SAAWR records (O23). [U] Why those codes were used instead of the table's, and what 55827005 and 67751000119106 denote (U3).
- [O] **SB, SR and ST agree with the 60 / 100 bpm thresholds applied to the figshare VentricularRate in 7,253 of 7,283 records (99.6%)** (O25, O26).
- [I] For SB / SR / ST, the label is almost a deterministic function of ventricular rate. Whether the physicians applied the thresholds themselves or accepted a machine statement does not change this: a classifier that separates these three classes is, in effect, re-measuring heart rate. Errors near 60 and 100 bpm will mostly reflect disagreement between my rate estimate and VentricularRate, not physiology.
- [I] SI is not rate-defined: 376 of its 399 records lie at 60–100 bpm, overlapping SR almost completely (O26). AFIB and atrial flutter span the whole rate range.
- [U] Who or what produced VentricularRate (D17 does not say; presumably the MUSE measurement), and whether the physicians saw it when labelling (U9, narrowed).

**Signal amplitude: the `.mat` `val` array and the header gain.**
- [D] Units are microvolts; "volts per A/D bit is 4.88"; 32-bit A/D (D8).
- [O] Stored as int16 with header gain `1000/mV` and ADC resolution 16 (O5, O13). Taken at face value, that header means 1 ADU = 1 µV.
- [O] The figshare values are multiples of 4.88, and the `.mat` values are those numbers rounded to integers (O29, O30).
- [I] **This resolves U7.** The original A/D step was 4.88 µV (D8); figshare stores count × 4.88 in µV; the WFDB conversion rounded that to whole µV. So 1 ADU = 1 µV, as the header says, with a rounding error of at most 0.5 µV. The "4.88" in D8 describes the original converter step, not the `.mat` unit.

**Sampling rate and duration.**
- [D] 500 Hz, 10 s (D1, D4).
- [O] 500 Hz and 5,000 samples in every parseable header, and 5,000 columns in every `.mat` (O5, O11).

**Signal processing state.**
- [D] The `.mat` files contain "raw data" (D7). The CSV release also had denoised data (D3 context).
- [U] Whether MUSE applied any filtering before export (U8).

**Age and Sex (`#Age:`, `#Sex:`).**
- [D] The headers contain age and gender (D7).
- [O] O16, O17.
- [O] **Ages ≥ 90 were capped at 89 in part 1**: every part-1 age that differs from figshare is 89 in part 1 and 90–98 in figshare (O23). This resolves U4.

## 7. Cohort / population represented in the released records

_Who or what is actually represented, and which relevant characteristics are absent or undocumented, recorded as absences rather than judgments about adequacy._

- [D/I] Part 1 is 10,247 resting 12-lead ECGs that the Challenge 2021 release attributes to Chapman University / Shaoxing People's Hospital (D2, D16, §2).
- [O] Ages run from 4 to 89 (ages ≥ 90 capped at 89, O23), with median 62; 144 records are under 18. 56% are male (5,733) and 44% female (4,514) (O16, O17).
- [O] The rhythm mix is dominated by sinus bradycardia, then sinus rhythm, AFIB, sinus tachycardia, SVT and atrial flutter, with small AT, AVRT and unmapped groups. **Sinus irregularity is absent from part 1** (§6); its 399 records exist only in the figshare release (O24).
- **Absent from the records** [O]:
  - patient identifier
  - acquisition date (except the 1,000 base times in O14, whose meaning is unresolved)
  - medications, history and symptoms (Rx/Hx/Sx all "Unknown")
- **Not stated in the files or in the documentation read:**
  - ethnicity
  - height and weight
  - care setting (inpatient, outpatient or emergency)
  - why the ECG was taken
  - device model (only the MUSE storage system is named)
  - collection period
- Part 2 (Ningbo) is not represented here at all. Nothing in this audit describes that hospital's population.

## 8. Documentation-record discrepancies and tensions

_For each place the documentation and the records disagree: the [D] claim, the [O] observation, and a [U] noting that you can't explain the gap from what you have._

1. **Sinus irregularity is missing.**
   - [D] The paper lists 399 SI ECGs (D12), and the condition table lists SA = 427393009.
   - [O] Code 427393009 never occurs in part 1 (§6). The ID range has exactly 399 absent IDs (O2).
   - [O] Paper male and female counts minus the SI row (5,956 − 223 = 5,733; 4,690 − 176 = 4,514) equal the observed counts (O17).
   - [O] Every other rhythm count in part 1 equals the paper's Table 2 exactly: SB 3,889 (3,887 alone + 2 with 195101003), SR 1,826, AFIB 1,780, ST 1,568, atrial flutter 445, SVT 587, AT 121, AVRT 8. The two unmapped codes also match: 251166008 = 16 = AVNRT and 17366009 = 7 = SAAWR (item 2). Only SI differs, at 0 vs 399 (§6, `results/dra/dx_code_counts.csv`).
   - [I] **The 399 absent record IDs are the 399 SI records.** The original Shaoxing release had 10,646 ECGs including 399 SI. The present part 1 has 10,247 records and is missing exactly 399 IDs, exactly 223 male and 176 female records (the SI row's sex split), and only the SI class. This also explains 10,646 vs 10,247 (D3, D16).
   - [U] The inference is not directly observed: the absent IDs have no files, so their labels cannot be checked in this release. Why the SI records were removed, and whether anything else changed with them, is also unresolved (U1).
   - **Repair (2026-11-12): resolved [O].** In the original figshare release, JS id *k* is row *k* of `Diagnostics.xlsx` (O22), and the 399 absent ids are exactly the 399 SA rows (O24). For the 10,247 present records, the figshare signals rounded to integers equal the `.mat` signals exactly (O30), so nothing else about them changed. The 399 SA signals are complete and in the same format (O31). **Still unresolved:** *why* PhysioNet v1.0.0 dropped them (U1, narrowed).
2. **AVNRT and SAAWR codes.**
   - [D] The table gives AVNRT = 233896004 and SAAWR = 195101003. The paper lists AVNRT 16 and SAAWR 7 (D12).
   - [O] 233896004 never occurs. 195101003 occurs in 2 records, both together with SB. Codes 251166008 (16 records) and 17366009 (7 records) are not in the table, and each record carrying one of them has no other rhythm code.
   - [I] Their counts match AVNRT and SAAWR.
   - [U] What these codes actually denote (U2).
   - **Repair: resolved [O].** Under the row pairing, the 16 records with 251166008 are AVNRT and the 7 with 17366009 are SAAWR in figshare (O23). Why these codes were used instead of the table's remains unknown but no longer affects which rhythm a record has.
3. **Codes missing from the table.**
   - [D] The table maps the acronyms to codes (D7).
   - [O] 55827005 (1,295 records) and 67751000119106 (8) are not in it.
   - [U] Their meaning (U3).
4. **Codes shared in the table.**
   - [D] The table gives distinct acronyms (e.g. MI by wall, LBBB/LFBBB/LBBBB).
   - [O] Several acronyms share one code (O20), so the records cannot carry those distinctions.
5. **Amplitude scale.**
   - [D] 4.88 per A/D bit, 32-bit A/D, microvolts (D8).
   - [O] int16 storage, gain `1000/mV`, ADC resolution 16 (O5, O13).
   - [U] The true µV per ADU (U7).
   - **Repair: resolved [O/I].** The figshare values are count × 4.88 µV and the `.mat` values are those rounded to whole µV (O29, O30). The header (1 ADU = 1 µV) is right for the `.mat` files; D8's 4.88 is the original converter step (§6).
6. **Age range.**
   - [D] Paper Table 1 gives "4–98" (D14).
   - [O] 4–89 (O16).
   - [U] Whether ages ≥ 90 were capped, removed or misprinted (U4).
   - **Repair: resolved [O].** Capped: all 166 part-1 records whose figshare age is 90–98 read 89 in part 1 (O23). The paper's "4–98" is correct for the original release.
7. **One ECG per patient.**
   - [D] Equal subject and record counts (D13), and "patient ECGs" (D1).
   - [O] 13 byte-identical pairs with identical metadata (O10). No patient ID exists to check further (O15).
   - [I] My reading of D13 is that each ECG belongs to a different patient (§5).
   - [U] Whether the 13 pairs are duplicated releases of one ECG (U6). The one-to-one inference cannot be checked directly without a patient ID (U5).
   - **Repair: narrowed.** Each pair has two different MUSE file names and timestamps (O32). [I] Two separate acquisitions cannot produce byte-identical 12-lead signals, so each pair is most likely one ECG exported twice; the FileName timestamp is then an export time, not necessarily an acquisition time. I will treat each pair as one ECG. [U] This is still an inference (U6).
8. **Header contents.**
   - [D] The header holds the lead configuration (D7).
   - [O] JS01052 describes only 11 leads, because of the malformed first line (O12). 1,000 headers, and only those, carry a 24-Mar-2021 base time (O14).
   - [U] What that base time means (U10).
9. **Zero leads.**
   - [O] 15 records have one or more all-zero chest leads (O9).
   - [D] No statement about missing or disconnected leads was found in the text I read verbatim.

## 9. Unresolved evidence ledger

_Numbered list of every [U] item you raised above, gathered in one place._

- U1. ~~Confirming that the 399 absent IDs are the SI records.~~ **Resolved 2026-11-12** (O22, O24, O30, O31). Still open: *why* PhysioNet v1.0.0 removed them. Nothing in the files says, so a quality problem specific to those 399 records cannot be ruled out.
- U2. ~~What SNOMED codes 251166008 and 17366009 denote.~~ **Resolved 2026-11-12**: AVNRT and SAAWR in this release (O23).
- U3. What 55827005 (1,295 records) and 67751000119106 (8 records) denote. Neither is in the condition table.
- U4. ~~Why the maximum age is 89.~~ **Resolved 2026-11-12**: ages ≥ 90 were capped at 89 (O23).
- U5. Whether each record really is a different patient. I infer one ECG per patient from the paper (D13, §5), but the files cannot confirm it because there is no patient identifier.
- U6. Whether the 13 byte-identical pairs are duplicated releases of one ECG. **Narrowed 2026-11-12**: each pair has two MUSE file names and timestamps (O32); I infer one ECG exported twice and will keep one member of each pair.
- U7. ~~The true amplitude scale.~~ **Resolved 2026-11-12**: 1 ADU = 1 µV in the `.mat` files, rounded from 4.88-µV counts (O29, O30).
- U8. Whether the "raw" signals had any filtering applied before export from MUSE.
- U9. How the SB/SR/ST labels relate to measured heart rate. **Answered for the purpose of the claim 2026-11-12**: they agree with 60/100 bpm thresholds on VentricularRate in 7,253 of 7,283 records (O25). Still open: who produced VentricularRate and whether the physicians saw it; this does not change the consequence (§6).
- U10. What the 24-Mar-2021 base time in 1,000 headers represents (acquisition time or conversion time), and why it appears in only those folders.
- U11. The collection period, device model, care setting and indication for the ECGs.
- U12. Why JS01052's header lost the lead-I line, and whether any other metadata in it is affected.
- U13. Whether figshare's FileName timestamps are acquisition or export times (O27, O32). If they are acquisition times, they would bear on U5 and U11.

## 10. Canonical data statement, v0

_One paragraph: the compact, evidence-bounded description of what the released records are, drawing only on your D/O/I statements above, and stating explicitly what remains unresolved._

**v1 (2026-11-12, after the U1/U9 repair).** Part 1 of PhysioNet ecg-arrhythmia v1.0.0 is 10,247 ten-second, 12-lead resting ECGs (500 Hz, 5,000 int16 samples per lead, 1 ADU = 1 µV) that the Challenge 2021 release attributes to Chapman University / Shaoxing People's Hospital. It is the original 10,646-record figshare release (2019) minus its 399 sinus-irregularity (SA) records: JS id *k* is row *k* of the figshare `Diagnostics.xlsx`, the 399 absent ids are exactly the SA rows, and each part-1 signal is the figshare signal rounded to whole µV [O]. The 399 SA signals are complete in figshare and in the same format [O]. Following the 2020 paper's equal subject and record counts, I take each record to be a different patient [I]; no file carries a patient identifier. Each record carries age (4–89 in part 1, where ages ≥ 90 were capped; 4–98 in figshare), sex and physician-assigned diagnosis codes; rhythm is effectively a single label (SB 3,889, SR 1,826, AFIB 1,780, ST 1,568, SVT 587, atrial flutter 445, SI 399 in figshare only, AT 121, AVNRT 16, AVRT 8, SAAWR 7). **The SB / SR / ST labels agree with 60 / 100 bpm thresholds on the figshare VentricularRate in 99.6% of records**, so for those three classes the label is almost a function of heart rate [O]; SI, AFIB and atrial flutter are not rate-defined. The signals are structurally clean, except for 15 records with all-zero chest leads, 13 byte-identical pairs (most likely one ECG exported twice), and one malformed header. Unresolved: why SI was dropped from PhysioNet, the meaning of two unmapped codes, whether signals were filtered before export, whether the one-ECG-per-patient inference holds, and the acquisition context (U1 residual, U3, U5, U6, U8, U10–U13).

**v0 (2026-11-04, superseded; kept for the record).** Part 1 of PhysioNet ecg-arrhythmia v1.0.0 is 10,247 ten-second, 12-lead resting ECGs (500 Hz, 5,000 int16 samples per lead) that the Challenge 2021 release attributes to Chapman University / Shaoxing People's Hospital. All files were downloaded and checksum-verified. Following the 2020 paper's equal subject and record counts, I take each record to be a different patient [I]. Each record carries the patient's age (4–89), sex (5,733 male, 4,514 female) and 1–10 physician-assigned SNOMED CT codes, but no patient identifier, date (except 1,000 headers), medication, history or symptom information. Rhythm is effectively a single label per record: 10,222 records carry exactly one rhythm code (SB 3,887, SR 1,826, AFIB 1,780, ST 1,568, SVT 587, atrial flutter 445, AT 121, AVRT 8), 2 carry SB plus a code the table shares between WAVN and SAAWR, and 23 carry only codes absent from the condition table. Sinus irregularity, which the 2020 paper counts at 399 ECGs, does not occur. Every other rhythm count equals the paper's. The 399 missing IDs and the missing 223 male / 176 female records match the SI row, so I infer that the 399 absent records are the SI records [I]. The signals are structurally clean: every first sample matches the header and every checksum agrees. Exceptions are 15 records with all-zero chest leads, 13 byte-identical record pairs, and one malformed header. Unresolved: direct confirmation of the SI inference and why those records were removed, the meaning of four unmapped codes, the amplitude scale, age capping, whether the one-ECG-per-patient inference holds (and what the identical pairs are), and the acquisition context (U1–U12).

## 11. Verification and provenance

_Which AI tools helped and exactly what they did versus what you verified yourself, and how someone else could check your D/O/I/U statements._

**AI use** (Claude Code, Opus 5.5; details in `AI_USE_APPENDIX.md`, Entry 3): the AI fetched the documentation, wrote and ran `src/dra_inspect.py`, and drafted this DRA. AI output is not treated as evidence: every [O] comes from the script's outputs on the actual files, and every [D] is a verbatim quote from the primary source.

**What I did myself:** chose the hospital-based split and ran the download (all checksums passed). I made the two key inferences (one ECG per patient; the 399 absent IDs are the SI records), I checked the [D] statements against the paper myself, and I reviewed the D/O/I/U tags.

**How to check**, from the repository root, with the data at `~/bme4191_ecg/`:
```text
python src/download_ecg_arrhythmia.py          # re-verifies every part-1 file; skips verified ones
python -I src/dra_inspect.py                       # rewrites results/dra/
shasum -a 256 results/dra/*
```

Expected SHA-256 of the outputs that do not depend on the machine (2026-11-04):

| File | SHA-256 |
|---|---|
| `dx_code_counts.csv` | `71b72d4a936fbd309cc7fabd9faa9134ecd4f0f8f819379cc3f73adab1d822da` |
| `rhythm_cooccurrence.csv` | `07c2af32edda7918b0e46fa9c4dd3c38ab8da524068e2097559f6d24a8f7b7e7` |
| `record_table_part1.csv` | `ee79e79ae193ea8ff91719cdbece5eafe60bb68e0212ca426049b4aee40c3ba2` |

`dra_summary.json` embeds the absolute data path, so compare its contents rather than its hash.

- [D] statements can be checked against the PhysioNet page (DOI 10.13026/wgex-er52), the paper (PMC7016169, Tables 1–2), and the Challenge 2021 page (Data Access, items 7–8).
- The hospital split can be reproduced with `python src/build_ecg_parts_manifest.py`.

**Repair, 2026-11-12 (U1, U9; `AI_USE_APPENDIX.md`, Entry 7).** I decided to test U1 and U9 against the original figshare release, and to compare signals before deciding whether SI can be added back. The AI found the figshare collection through its public API, downloaded and MD5-checked the files, wrote and ran `src/figshare_check.py` and `src/figshare_signal_check.py`, and drafted the repair text in §1–§10. Every new [O] comes from those scripts' outputs; D17–D19 are read from the figshare files and API metadata.

How to check (data in `~/bme4191_ecg/figshare_chapman/`, `ECGData.zip` unzipped there; MD5s in §2):
```text
python -I src/figshare_check.py            # stdlib only; needs results/dra/record_table_part1.csv
python -I src/figshare_signal_check.py     # numpy, scipy, pandas; ran under Python 3.13.18, numpy 2.5.4, pandas 3.1.1
shasum -a 256 results/figshare_check/*
```

| File | SHA-256 (2026-11-12) |
|---|---|
| `summary.json` | `3cb4e85624ebb32b9d556fa5db91384f65ee76fd53adf8d5bd488cdf56c8e60a` |
| `id_alignment.csv` | `877806470ff66f18bdcf909a3e2a62710877c7c84628271fd151ae362998414c` |
| `rate_by_rhythm.csv` | `9203bb99833e082a3dd13683f95e76dad0fcbb1f2e7d098a193b392faa74b9c4` |

`signal_match.csv` and `signal_summary.json` contain floating-point least-squares values that may differ in the last digits between machines; compare their counts rather than their hashes.
