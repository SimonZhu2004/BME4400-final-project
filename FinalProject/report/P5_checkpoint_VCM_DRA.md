# Project 5 checkpoint — VCM §1–2 (all versions) and initial DRA

Contents:
1. VCM v0, §1–2 (pre-DRA)
2. VCM v1, §1–2 (after the DRA; SI dropped)
3. VCM v2, §1–2 (current; SI kept, with the inference that the 399 missing records are SI)
4. Initial Data Reality Audit — PhysioNet ecg-arrhythmia v1.0.0, part 1 (Chapman-Shaoxing)

---

## Part 1. VCM v0 (pre-DRA)

### 1. Current scientific question


**Question 2:** Can we classify the kind of arrhythmia of the patient, based on a certain set of features extracted from the raw ECG recordings, in the dataset from a certain clinical location?

**Version:** Can we classify different cardiac rhythms, such as atrial fibrillation, atrial flutter, sinus rhythm, sinus irregularity, sinus bradycardia, and sinus tachycardia, using features extracted from 12-lead ECG recordings in the certain database?

**Source:** PhysioNet, *A large scale 12-lead electrocardiogram database for arrhythmia study*, v1.0.0 — https://physionet.org/content/ecg-arrhythmia/1.0.0/ (open download).

### 2. Provisional expectation / claim

I expect **yes, with an uneven answer across classes**. A classifier using features from the 12-lead ECGs (heart rate, RR-interval statistics, P-wave presence and morphology, P–QRS relationship, atrial-activity / baseline spectral content) will classify the six rhythms — sinus rhythm (SR), sinus bradycardia (SB), sinus tachycardia (ST), sinus irregularity (SI), atrial fibrillation (AF), atrial flutter (AFL) — clearly better than a majority-class baseline, evaluated with a split that keeps records from the same patient together. Other diagnoses in the database are left out because each is too rare to train and evaluate on.

Why I expect this, from background physiology:

- **SB / SR / ST** are all sinus rhythms that differ mainly in rate (SB below ~60 bpm, SR ~60–100 bpm, ST above ~100 bpm). Heart rate alone should separate them well; the remaining errors should sit near the 60 and 100 bpm boundaries.
- **AF** is "irregularly irregular" with no organised P waves. RR-interval variability marks it as irregular, but without correct P waves the atrial features (P-wave presence, morphology, P–QRS relationship) are harder to extract reliably, so AF should be harder to classify than SI.
- **SI** has normal sinus P waves but beat-to-beat RR variation (often respiratory). Because its P waves are intact, P-wave features can be extracted reliably and, together with RR variability, should identify it more easily than AF. Its mild cases may still overlap with SR (and SB, since sinus arrhythmia is common at slow rates).
- **AFL** should be the hardest class: with 2:1 conduction its ventricular rate (~150 bpm) is regular and overlaps with ST; with variable block its RR intervals become irregular and overlap with AF. It is also likely to be one of the smallest classes.

Specific, falsifiable form: per-class recall will be highest for the rate-defined sinus classes (SB, SR, ST), then SI, then AF, and **lowest for AFL** (in particular, SI recall > AF recall). Most SI errors will be confused with SR (or SB), and most AFL errors with ST or AF.

---

## Part 2. VCM v1 (revised after the DRA)

### 1. Current scientific question

Use the wording given in the assignment text.

**Question 2:** Can we classify the kind of arrhythmia of the patient, based on a certain set of features extracted from the raw ECG recordings, in the dataset from a certain clinical location?

**Version (v1, revised after the DRA):** Can we classify five cardiac rhythms — sinus rhythm, sinus bradycardia, sinus tachycardia, atrial fibrillation and atrial flutter — using features extracted from 12-lead ECG recordings from one clinical location, Shaoxing People's Hospital (part 1 of the database)?

**Source:** PhysioNet, *A large scale 12-lead electrocardiogram database for arrhythmia study*, v1.0.0 — https://physionet.org/content/ecg-arrhythmia/1.0.0/. Part 1 = the 10,247 Chapman-Shaoxing records (see `dra/DRA.md` §2).

### 2. Provisional expectation / claim

_What do you currently expect, and why do you expect it?_

I expect **yes, with an uneven answer across classes**. A classifier using features from the 12-lead ECGs (heart rate, RR-interval statistics, P-wave presence and morphology, P–QRS relationship, atrial-activity / baseline spectral content) will classify the five rhythms clearly better than always predicting the most common rhythm. In the data's own labels the five rhythms are SR, SB, ST, AFIB (atrial fibrillation) and AF (atrial flutter); I write AFL for atrial flutter.

What the DRA established that this claim now rests on:

- **Classes available** [O]: SB 3,887, SR 1,826, AFIB 1,780, ST 1,568, AFL 445 records. In each of these records that is the only rhythm label, so rhythm is effectively single-label.
- **Sinus irregularity is dropped.** SI has 0 records in part 1. From the 2020 paper's counts, I infer that the 399 records missing from the ID range are the 399 SI records, which were removed from this release [I]. The v0 prediction "SI recall > AF recall" cannot be tested here.
- **One ECG = one patient** [I], from the paper's equal subject and record counts. The release has no patient ID to confirm this.
- **Excluded rhythms:** AT (121), AVRT (8) and the 23 records with unmapped rhythm codes are too rare. SVT (587) is excluded because it is not one of the rhythms in the question, not because it is rare.

Why I expect this, from background physiology:

- **SB / SR / ST** are sinus rhythms that differ mainly in rate (SB below ~60 bpm, SR ~60–100 bpm, ST above ~100 bpm). Heart rate alone should separate them well; the remaining errors should sit near the 60 and 100 bpm boundaries.
- **AFIB** is "irregularly irregular" with no organised P waves. RR irregularity flags it, but without correct P waves the atrial features are harder to extract reliably. So AFIB should be harder to classify than the sinus classes, whose P waves are intact. This is the same reasoning that ranked SI above AF in v0.
- **AFL** should be the hardest class. With 2:1 conduction its ventricular rate (~150 bpm) is regular and overlaps with ST; with variable block its RR intervals become irregular and overlap with AFIB. It is also the smallest class (445).
- **SI** has normal sinus P waves but beat-to-beat RR variation (often respiratory). Because its P waves are intact, P-wave features can be extracted reliably and, together with RR variability, should identify it more easily than AF. Its mild cases may still overlap with SR (and SB, since sinus arrhythmia is common at slow rates). The data has 0 records of SI. 399 records without any label were inferred to be SI. [I]

Specific, falsifiable form: per-class recall will be highest for the rate-defined sinus classes (SB, SR, ST), lower for SI, then AFIB, and **lowest for AFL**. Most AFL errors will be confused with ST or AFIB.

**What changed (v0 → v1):**

v0 → v1, after the DRA:
- Dropped sinus irregularity (0 records in part 1; inferred removed from the release).
- Named the clinical location (Shaoxing, part 1).
- Adopted the data's labels (AFIB = fibrillation, AF = flutter).
- Added the one-ECG-per-patient inference.
- Removed the validation-split wording, because no validation strategy belongs at this checkpoint.
- The prediction keeps its logic: rate-defined sinus classes > AFIB > AFL.

---

## Part 3. VCM v2 (current)

### 1. Current scientific question

Use the wording given in the assignment text.

**Question 2:** Can we classify the kind of arrhythmia of the patient, based on a certain set of features extracted from the raw ECG recordings, in the dataset from a certain clinical location?

**Version (v2):** Can we classify six cardiac rhythms — sinus rhythm, sinus bradycardia, sinus tachycardia, sinus irregularity, atrial fibrillation and atrial flutter — using features extracted from 12-lead ECG recordings from one clinical location, Shaoxing People's Hospital (part 1 of the database)?

**Source:** PhysioNet, *A large scale 12-lead electrocardiogram database for arrhythmia study*, v1.0.0 — https://physionet.org/content/ecg-arrhythmia/1.0.0/. Part 1 = the 10,247 Chapman-Shaoxing records (see `dra/DRA.md` §2).

### 2. Provisional expectation / claim

_What do you currently expect, and why do you expect it?_

I expect **yes, with an uneven answer across classes**. A classifier using features from the 12-lead ECGs (heart rate, RR-interval statistics, P-wave presence and morphology, P–QRS relationship, atrial-activity / baseline spectral content) will classify the six rhythms clearly better than always predicting the most common rhythm. In the data's own labels the six rhythms are SR, SB, ST, SA (sinus irregularity), AFIB (atrial fibrillation) and AF (atrial flutter); I write SI for sinus irregularity and AFL for atrial flutter.

What the DRA established that this claim now rests on:

- **Classes in part 1** [O]: SB 3,887, SR 1,826, AFIB 1,780, ST 1,568, AFL 445 and **SI 0** records. In each of these records that is the only rhythm label, so rhythm is effectively single-label.
- **I infer that the 399 missing records are the SI records** [I]. The 2020 paper lists 399 SI ECGs in the original 10,646-record Shaoxing release. Part 1 has 10,247 records, and exactly 399 IDs are missing from its range. The missing records match the SI row's sex split (223 male, 176 female), and every other rhythm count matches the paper exactly. So I infer the SI records exist but were removed from this release. This is inferred, not observed: the missing IDs have no files (DRA §8 item 1, U1).
- **Consequence:** SI stays in the question, but **the SI part of the claim cannot be tested on part 1 as released**. It is conditional on obtaining the SI records, for example from the original 10,646-record Shaoxing release, which the paper says was shared on figshare. Until then, only the five-class part of the claim can be evaluated.
- **One ECG = one patient** [I], from the paper's equal subject and record counts. The release has no patient ID to confirm this.
- **Excluded rhythms:** AT (121), AVRT (8) and the 23 records with unmapped rhythm codes are too rare. SVT (587) is excluded because it is not one of the rhythms in the question, not because it is rare.

Why I expect this, from background physiology:

- **SB / SR / ST** are sinus rhythms that differ mainly in rate (SB below ~60 bpm, SR ~60–100 bpm, ST above ~100 bpm). Heart rate alone should separate them well; the remaining errors should sit near the 60 and 100 bpm boundaries.
- **SI** has normal sinus P waves but beat-to-beat RR variation. Because its P waves are intact, P-wave features can be extracted reliably and, together with RR variability, should identify it more easily than AFIB. Its mild cases may overlap with SR or SB.
- **AFIB** is "irregularly irregular" with no organised P waves. RR irregularity flags it, but without correct P waves the atrial features are harder to extract reliably, so AFIB should be harder to classify than SI.
- **AFL** should be the hardest class. With 2:1 conduction its ventricular rate (~150 bpm) is regular and overlaps with ST; with variable block its RR intervals become irregular and overlap with AFIB. It is also the smallest class available (445).

Specific, falsifiable form: per-class recall will be highest for the rate-defined sinus classes (SB, SR, ST), then SI, then AFIB, and **lowest for AFL** (in particular, SI recall > AFIB recall, if SI records can be obtained). Most SI errors will be confused with SR or SB, and most AFL errors with ST or AFIB.

**What changed:**

v1 → v2:
- Restored sinus irregularity to the question and the prediction.
- Stated explicitly my inference that the 399 records missing from part 1 are the SI records.
- Marked the SI part of the claim as untestable on part 1 as released, conditional on obtaining those records.

---

## Part 4. Initial Data Reality Audit — PhysioNet ecg-arrhythmia v1.0.0, part 1 (Chapman-Shaoxing)

### 1. Purpose and epistemic boundary

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

### 2. Dataset identity and acquisition record

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

### 3. What the documentation states

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

### 4. What the released file(s) actually contain

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

### 5. Record unit and observational hierarchy

_What one record represents [D], how records relate to higher-level units [O], and the hierarchy that follows [I], without deciding what analytical unit you'll use._

- [D] One record is one 10-s, 12-lead resting ECG, stored as a `.hea` + `.mat` pair (D4, D7). The documentation counts "patient ECGs" (D1, D13). The 2020 paper gives equal subject and record counts (10,646).
- [O] Records sit in a storage hierarchy, `WFDBRecords/NN/NNN/`, of up to 100 records per folder (O3). Nothing in a record links it to a patient, visit or date, apart from the 1,000 base times in O14 (O15).
- [O] 13 pairs of records are byte-identical in signal and metadata (O10).
- [I] **One ECG corresponds to one individual patient.** The Zheng et al. 2020 paper describes the original Shaoxing release as "10,646 patient ECGs" and gives equal counts of subjects and records (10,646 each) in Table 1 (D13). Part 1 is a subset of that release (D3, D16), so I take each part-1 record to be a different patient. This is inferred from the documentation, not observed: no header carries a patient identifier (O15).
- [I] The hierarchy that follows is: hospital (part 1 = Shaoxing, from the Challenge folders) → patient = record → 12 leads × 5,000 samples. Labels and demographics are attached at the record and patient level.
- [I] The storage folders follow ID order (O3), so they look like a filing scheme rather than a clinical grouping.
- [U] The one-to-one inference cannot be confirmed from the files, because there is no patient ID (U5). The 13 identical pairs (O10) are in tension with it: each looks like one ECG released twice under two IDs. Whether that is what they are is unresolved (U6).

### 6. Central recorded quantities and their construction

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
  | **Sinus irregularity (SA)** | 427393009 | **0** (the code never occurs; I infer the 399 SI records are the 399 absent IDs, §8 item 1) |

- [O] Rhythm codes are almost exclusive within a record:
  - 10,222 records carry exactly one of the 11 rhythm codes in the condition table.
  - 2 records carry two: SB plus 195101003, a code shared by WAVN and SAAWR.
  - 23 records carry none. All 23 carry 251166008 (16 records) or 17366009 (7 records), which are not in the table (O19).
- [I] In part 1 the rhythm is effectively a single label per record. The non-rhythm conditions are what make records multi-label (O18).
- [I] The table uses **"AF" for atrial flutter** and **"AFIB" for atrial fibrillation**. Any reading of "AF" has to say which one it means.
- [U] What 251166008, 17366009, 55827005 and 67751000119106 denote (U2, U3).
- [U] How the physicians decided between SB, SR and ST, i.e. whether the rate thresholds were applied mechanically or by MUSE measurements (U9).

**Signal amplitude: the `.mat` `val` array and the header gain.**
- [D] Units are microvolts; "volts per A/D bit is 4.88"; 32-bit A/D (D8).
- [O] Stored as int16 with header gain `1000/mV` and ADC resolution 16 (O5, O13). Taken at face value, that header means 1 ADU = 1 µV.
- [U] Which scale is correct (U7).

**Sampling rate and duration.**
- [D] 500 Hz, 10 s (D1, D4).
- [O] 500 Hz and 5,000 samples in every parseable header, and 5,000 columns in every `.mat` (O5, O11).

**Signal processing state.**
- [D] The `.mat` files contain "raw data" (D7). The CSV release also had denoised data (D3 context).
- [U] Whether MUSE applied any filtering before export (U8).

**Age and Sex (`#Age:`, `#Sex:`).**
- [D] The headers contain age and gender (D7).
- [O] O16, O17.
- [U] Whether ages were capped (U4).

### 7. Cohort / population represented in the released records

_Who or what is actually represented, and which relevant characteristics are absent or undocumented, recorded as absences rather than judgments about adequacy._

- [D/I] Part 1 is 10,247 resting 12-lead ECGs that the Challenge 2021 release attributes to Chapman University / Shaoxing People's Hospital (D2, D16, §2).
- [O] Ages run from 4 to 89, with median 62; 144 records are under 18. 56% are male (5,733) and 44% female (4,514) (O16, O17).
- [O] The rhythm mix is dominated by sinus bradycardia, then sinus rhythm, AFIB, sinus tachycardia, SVT and atrial flutter, with small AT, AVRT and unmapped groups. **Sinus irregularity is absent** (§6).
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

### 8. Documentation-record discrepancies and tensions

_For each place the documentation and the records disagree: the [D] claim, the [O] observation, and a [U] noting that you can't explain the gap from what you have._

1. **Sinus irregularity is missing.**
   - [D] The paper lists 399 SI ECGs (D12), and the condition table lists SA = 427393009.
   - [O] Code 427393009 never occurs in part 1 (§6). The ID range has exactly 399 absent IDs (O2).
   - [O] Paper male and female counts minus the SI row (5,956 − 223 = 5,733; 4,690 − 176 = 4,514) equal the observed counts (O17).
   - [O] Every other rhythm count in part 1 equals the paper's Table 2 exactly: SB 3,889 (3,887 alone + 2 with 195101003), SR 1,826, AFIB 1,780, ST 1,568, atrial flutter 445, SVT 587, AT 121, AVRT 8. The two unmapped codes also match: 251166008 = 16 = AVNRT and 17366009 = 7 = SAAWR (item 2). Only SI differs, at 0 vs 399 (§6, `results/dra/dx_code_counts.csv`).
   - [I] **The 399 absent record IDs are the 399 SI records.** The original Shaoxing release had 10,646 ECGs including 399 SI. The present part 1 has 10,247 records and is missing exactly 399 IDs, exactly 223 male and 176 female records (the SI row's sex split), and only the SI class. This also explains 10,646 vs 10,247 (D3, D16).
   - [U] The inference is not directly observed: the absent IDs have no files, so their labels cannot be checked in this release. Why the SI records were removed, and whether anything else changed with them, is also unresolved (U1).
2. **AVNRT and SAAWR codes.**
   - [D] The table gives AVNRT = 233896004 and SAAWR = 195101003. The paper lists AVNRT 16 and SAAWR 7 (D12).
   - [O] 233896004 never occurs. 195101003 occurs in 2 records, both together with SB. Codes 251166008 (16 records) and 17366009 (7 records) are not in the table, and each record carrying one of them has no other rhythm code.
   - [I] Their counts match AVNRT and SAAWR.
   - [U] What these codes actually denote (U2).
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
6. **Age range.**
   - [D] Paper Table 1 gives "4–98" (D14).
   - [O] 4–89 (O16).
   - [U] Whether ages ≥ 90 were capped, removed or misprinted (U4).
7. **One ECG per patient.**
   - [D] Equal subject and record counts (D13), and "patient ECGs" (D1).
   - [O] 13 byte-identical pairs with identical metadata (O10). No patient ID exists to check further (O15).
   - [I] My reading of D13 is that each ECG belongs to a different patient (§5).
   - [U] Whether the 13 pairs are duplicated releases of one ECG (U6). The one-to-one inference cannot be checked directly without a patient ID (U5).
8. **Header contents.**
   - [D] The header holds the lead configuration (D7).
   - [O] JS01052 describes only 11 leads, because of the malformed first line (O12). 1,000 headers, and only those, carry a 24-Mar-2021 base time (O14).
   - [U] What that base time means (U10).
9. **Zero leads.**
   - [O] 15 records have one or more all-zero chest leads (O9).
   - [D] No statement about missing or disconnected leads was found in the text I read verbatim.

### 9. Unresolved evidence ledger

_Numbered list of every [U] item you raised above, gathered in one place._

- U1. Confirming that the 399 absent IDs are the SI records, which I infer in §8 item 1. This would need the original 10,646-record release (figshare). Also unresolved: why they were removed from v1.0.0, and whether that removal changed anything else.
- U2. What SNOMED codes 251166008 (16 records) and 17366009 (7 records) denote. Their counts match the paper's AVNRT and SAAWR.
- U3. What 55827005 (1,295 records) and 67751000119106 (8 records) denote. Neither is in the condition table.
- U4. Why the maximum age is 89 while the paper reports 4–98 (capping, removal or typo).
- U5. Whether each record really is a different patient. I infer one ECG per patient from the paper (D13, §5), but the files cannot confirm it because there is no patient identifier.
- U6. Whether the 13 byte-identical pairs are duplicated releases of one ECG.
- U7. The true amplitude scale: 1 µV/ADU from the header, or 4.88 per bit from the documentation.
- U8. Whether the "raw" signals had any filtering applied before export from MUSE.
- U9. How the SB/SR/ST labels relate to measured heart rate (physician judgment vs. MUSE measurement).
- U10. What the 24-Mar-2021 base time in 1,000 headers represents (acquisition time or conversion time), and why it appears in only those folders.
- U11. The collection period, device model, care setting and indication for the ECGs.
- U12. Why JS01052's header lost the lead-I line, and whether any other metadata in it is affected.

### 10. Canonical data statement, v0

_One paragraph: the compact, evidence-bounded description of what the released records are, drawing only on your D/O/I statements above, and stating explicitly what remains unresolved._

Part 1 of PhysioNet ecg-arrhythmia v1.0.0 is 10,247 ten-second, 12-lead resting ECGs (500 Hz, 5,000 int16 samples per lead) that the Challenge 2021 release attributes to Chapman University / Shaoxing People's Hospital. All files were downloaded and checksum-verified. Following the 2020 paper's equal subject and record counts, I take each record to be a different patient [I]. Each record carries the patient's age (4–89), sex (5,733 male, 4,514 female) and 1–10 physician-assigned SNOMED CT codes, but no patient identifier, date (except 1,000 headers), medication, history or symptom information. Rhythm is effectively a single label per record: 10,222 records carry exactly one rhythm code (SB 3,887, SR 1,826, AFIB 1,780, ST 1,568, SVT 587, atrial flutter 445, AT 121, AVRT 8), 2 carry SB plus a code the table shares between WAVN and SAAWR, and 23 carry only codes absent from the condition table. Sinus irregularity, which the 2020 paper counts at 399 ECGs, does not occur. Every other rhythm count equals the paper's. The 399 missing IDs and the missing 223 male / 176 female records match the SI row, so I infer that the 399 absent records are the SI records [I]. The signals are structurally clean: every first sample matches the header and every checksum agrees. Exceptions are 15 records with all-zero chest leads, 13 byte-identical record pairs, and one malformed header. Unresolved: direct confirmation of the SI inference and why those records were removed, the meaning of four unmapped codes, the amplitude scale, age capping, whether the one-ECG-per-patient inference holds (and what the identical pairs are), and the acquisition context (U1–U12).

### 11. Verification and provenance

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
