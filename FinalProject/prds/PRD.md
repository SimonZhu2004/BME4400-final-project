# BME4400 PRD v0: models trained on the first 2–10 s of the ECG, tested at Shaoxing and Ningbo

Written 2026-11-25, before any feature is computed or any model trained. If the
analysis changes, this file is amended in a new commit before the change is run.

Do not delete a section that does not apply. Keep the heading and write:

> _Not applicable — [reason]._

**Amendments** (each made before the change was run on anything but the development set):

| # | Date | Section | Change | Reason and evidence |
|---|---|---|---|---|
| 1 | 2026-11-25 | §3, §4, §5 A1 | Shaoxing units 9,888 → 9,887 | `src/make_split.py` found a 14th identical pair (SI JS02561 = JS04771); JS04771 dropped by the existing duplicate rule (VCM v2 §12) |
| 2 | 2026-11-25 | §5 A3 | `hr` = 60000 / **mean** RR (was median) | `VentricularRate` is a mean rate; with the median, only 90.1% of development units were within 5 bpm of it at 10 s (AFIB 63%, AFL 69%); with the mean, 94.2% |
| 3 | 2026-11-25 | §5 A3 | DWT delineation features (P-wave fraction, P amplitude, PR median and SD, QRS width; per lead) replaced by `p_consistency` per lead: **24 → 16 features** | On the development set the DWT output was implausible: a P wave was "found" in nearly every AFIB beat (median `p_frac` 1.00), median QRS width 150–200 ms, only 52% of lead-II PR intervals in 80–300 ms. NeuroKit's `ecg_delineate` also refuses crops shorter than 4 s. `p_consistency` separates the classes at 10 s and 2 s (lead II median: sinus classes 0.89–0.97, AFL 0.49–0.50, AFIB −0.02 to 0.05; `results/features/qc_dev.json`) |
| 4 | 2026-11-25 | §4 item 5 | Heart-rate check **fails**: 94.2% < 95% | Eight NeuroKit R-peak detectors compared on 1,800 development units (`src/qc_rpeak_detectors.py`, `results/features/qc_rpeak_detectors.csv`); the default `neurokit` detector is best (94.1% on the sample). Errors: one extra peak in some SB records, missed peaks in some AFIB / AFL records. An amplitude filter on R peaks made it worse at every threshold tried (0.3–0.6 × median). |
| 5 | 2026-11-25 | §4 item 5, §9 | **Decision on amendment 4: proceed.** The check stays recorded as failed (94.2% < 95%); the 95% threshold is not lowered. The team accepts the deviation and narrows what M_HR can show (VCM §6) | The shortfall is in AFIB (87.8%) and AFL (86.0%), which the claim separates mainly by RR irregularity and atrial activity, not by rate; sinus classes agree for 94–99%. No available detector does better. Consequence: wherever M_HR or the gain over M_HR is reported, it is stated that heart rate disagrees with `VentricularRate` by more than 5 bpm in 12–14% of AFIB / AFL development units, so M_HR is a floor built on our heart-rate estimate, not on the recorded rate |

---

## 1. Purpose and evidence need

**Question (VCM §1).** If only the first T seconds of a 12-lead ECG are available (T = 2, 4, 6, 8 or 10 s), how well can six rhythms (SR, SB, ST, SI, AFIB, AFL) be classified by a model trained on recordings of that length? Do models trained on the raw ECG lose less than models trained on a feature table as T shrinks? Do the same patterns hold at a second site?

**Design:** a separate set of models is trained for every T, on the first T s of each record. The same crop is used for training and testing.

| Stage | Data | What it does | Kind of evidence |
|---|---|---|---|
| A | Shaoxing development set (80%), 5-fold CV | tune and compare models at every T | development |
| B | Shaoxing test set (20%) | refit each tuned model on the whole development set, predict the test set **once** at every T | confirmation (same site) |
| C | train: all Shaoxing; test: Ningbo | refit the same settings on all Shaoxing at every T, predict Ningbo **once** | confirmation (external site) |

**Main measure:** R3 = macro recall over SI, AFIB and AFL. SB / SR / ST labels are heart-rate thresholds (VCM §1, DRA O25), so they are reported but do not decide anything.

**This analysis does not establish:**
- anything about fewer leads, windows below 2 s, other rhythms, or windows taken from elsewhere in the record (only the first T s is used).
- that raw-signal models beat feature models in general: one CNN, one MiniRocket and one 16-feature table are compared.
- why performance differs between sites. A drop at Ningbo can come from different patients, devices or labelling practice; this analysis cannot separate them.

**Relation to the VCM.** VCM v1 already fits a separate model at every window and holds out 20% of Shaoxing. This PRD changes three things, which **VCM v2 must record before any code in §5 runs**: the windows are the **first** T s (not random crops in training and the middle crop in testing); Ningbo is added as an external test set; MiniRocket is a secondary model.

## 2. Inputs

Only these files may be read. Data folder `DATA = ~/bme4191_ecg` (outside the repository).

| Input | Path | Identity | Size | Origin |
|---|---|---|---|---|
| Parts manifest | `results/source_data/ecg_arrhythmia_parts.csv` | sha256 `6720d3b3177bfce0eefa93e92275cd7f0b7b9fa7216ee3fa6c72181b75cc0d1a` | 45,152 rows (part 1: 10,247; part 2: 34,905) | `src/build_ecg_parts_manifest.py` |
| PhysioNet checksum list | `DATA/ecg-arrhythmia/1.0.0/SHA256SUMS.txt` | sha256 `dfad0c26a276ce7e450e5002051f4c749304552d9add4d592928bbdcb6e4f31c` | 90,759 lines | PhysioNet ecg-arrhythmia v1.0.0 |
| Part-1 records | `DATA/ecg-arrhythmia/1.0.0/WFDBRecords/…/JS*.hea, .mat` | each verified against the checksum list | 10,247 records × 12 leads × 5,000 samples | PhysioNet |
| Shaoxing labels and SI signals | `DATA/figshare_chapman/Diagnostics.xlsx`, `DATA/figshare_chapman/ECGData/*.csv` | MD5 checked by `src/figshare_check.py` | 10,646 rows; 399 SI CSVs of 5,000 × 12 | figshare *ChapmanECG* 4560497 |
| Condition table | `DATA/ecg-arrhythmia/1.0.0/ConditionNames_SNOMED-CT.csv` | in the checksum list | — | PhysioNet |
| Shaoxing units, split and folds | `results/splits/shaoxing_units.csv`, `shaoxing_test_ids.csv`, `shaoxing_dev_folds.csv` | sha256 in `results/splits/SHA256SUMS` | 9,887 / 1,978 / 7,909 rows | `src/make_split.py` (step A1) |
| Part-2 records (Stage C only) | `DATA/ecg-arrhythmia/1.0.0/WFDBRecords/…/JS*.hea, .mat` for JS10647–JS45551 | each verified against the checksum list | 34,905 records | PhysioNet; downloaded only at step C2 (§15) |

No other file may be read.

## 3. What must remain fixed

- **Prediction unit and generalization unit:** one 12-lead ECG record (taken to be one patient, VCM §5). Splits are by record.
- **Shaoxing units:** the 9,887 records of VCM v2 §8.1 (SB 3,888, SR 1,825, AFIB 1,778, ST 1,562, AFL 438, SI 396).
- **Shaoxing split, stratified by label:** `train_test_split(test_size=0.2, stratify=label, random_state=4400)` on the units sorted by JS id (VCM v2 §8.2).

  | Class | All | Development (80%) | Test (20%) | Each dev fold |
  |---|---|---|---|---|
  | SR | 1,825 | 1,460 | 365 | 292 |
  | SB | 3,888 | 3,110 | 778 | 622 |
  | ST | 1,562 | 1,250 | 312 | 250 |
  | SI | 396 | 317 | 79 | 63–64 |
  | AFIB | 1,778 | 1,422 | 356 | 284–285 |
  | AFL | 438 | 350 | 88 | 70 |
  | **Total** | **9,887** | **7,909** | **1,978** | 1,581–1,582 |
- **Ningbo units:** the rule in §5 step C3, written now, before part 2 is downloaded.
- **Target coding:** 0 SR, 1 SB, 2 ST, 3 SI, 4 AFIB, 5 AFL.
  - Shaoxing labels: `Diagnostics.xlsx` Rhythm (SR, SB, ST, SA, AFIB, AF).
  - Ningbo labels: header `#Dx:` SNOMED codes 426783006 SR, 426177001 SB, 427084000 ST, 427393009 SI, 164889003 AFIB, 164890007 AFL.
- **Signal:** all 12 leads, µV, 500 Hz. Shaoxing SI records: round(figshare CSV) (DRA O30).
- **Windows:** T ∈ {2, 4, 6, 8, 10} s. The crop is the **first T s**: samples `[0, 500·T)`. The same crop rule is used for training, validation and testing, at both sites.
- **Crop before processing:** every filter, R-peak detection, feature and normalisation uses only the crop.
- **Metric:** R3 (primary); per-class recall, precision and F1 for all six; F1-3 (macro F1 over SI, AFIB, AFL); macro recall and macro F1 over six; accuracy (§7).
- **Floor:** M_HR (heart rate only).
- **Environment:** the `bme4400-final` conda environment from `environment.yml`, every package pinned to an exact version (§11).
- **Random seeds.** Every source of randomness has a fixed seed:

  | Step | Where the seed goes | Seed |
  |---|---|---|
  | 80/20 split | `train_test_split(random_state=…)` | 4400 |
  | 5 development folds | `StratifiedKFold(shuffle=True, random_state=…)` | 4400 |
  | HistGradientBoosting (M_HR, M_feat) | `random_state=…` | 4400 |
  | Logistic regression | `random_state=…` | 4400 |
  | MLP | `MLPClassifier(random_state=…)`; class-balance resampling `sklearn.utils.resample(random_state=…)` | 4400 |
  | MiniRocket | `MiniRocketMultivariate(random_state=…)` | 4400 |
  | 1D CNN weights, batch order, dropout | `random.seed`, `np.random.seed`, `torch.manual_seed`, and the `DataLoader`'s `generator=torch.Generator().manual_seed(…)` | 4400 (main); 4401 and 4402 for the spread (§7) |
  | CNN early-stopping validation split | `train_test_split(test_size=0.1, stratify=label, random_state=…)` | 4400 |
  | Negative control label shuffle | `np.random.default_rng(…).permutation` | 4400 |
  | Bootstrap | `np.random.default_rng(…)` | 4400 |
  | Feature extraction (NeuroKit2, SciPy) | deterministic, no seed | — |
- **Evidence boundary:** §15.

## 4. Replication of earlier work

Before any model result is interpreted, these must reproduce exactly (tolerance 0):
1. Parts manifest sha256 as in §2.
2. Shaoxing unit list: 9,907 → 9,901 → 9,887, and the six class counts in §3 (VCM v2 §8.1). `src/make_split.py` asserts these.
3. The split files' SHA-256 equal `results/splits/SHA256SUMS`:
   - `shaoxing_units.csv` `b708bacdaa9d986112c9b2c232b798184629202fc15213199c1b345f6372e5a3`
   - `shaoxing_test_ids.csv` `2c95db54fdc3d65e611b0a8c8c7ea1f0e867dfdf4d545f982eb30945757c9d8a`
   - `shaoxing_dev_folds.csv` `252f3eed531bee991abf774adaa82ecdd924e511bf426ade619fcce006047b28`
4. SB / SR / ST vs the 60 / 100 bpm rule on `VentricularRate`: 7,253 of 7,283 agree (DRA O25).

And within tolerance:
5. Heart rate from §5 step A3 at T = 10 s is within 5 bpm of `VentricularRate` for at least 95% of Shaoxing development units (VCM v2 §6). **Result 2026-11-25: 94.2% — failed; proceeding under amendment 5.** Reproduced by `python src/feature_qc.py` (`results/features/qc_dev.json`).

If any check fails: stop and diagnose (§13). Nothing downstream is run.

## 5. Exact procedure

**Stage A: Shaoxing development set, 5-fold CV, every T**

A1. **Units and split.** `python src/make_split.py` builds the 9,887-unit list and the 80/20 split (§3), asserts every count, and writes `results/splits/shaoxing_units.csv` (`record, label, code, source, signal_sha256`), `shaoxing_test_ids.csv` (`record, label, code`), `split_summary.json` and `SHA256SUMS`. **Done and committed 2026-11-25, before any feature is computed.** Teammates rerun it and check that `SHA256SUMS` is unchanged (§4).

A2. **Folds.** Same script: on the development set sorted by JS id, `StratifiedKFold(n_splits=5, shuffle=True, random_state=4400)`, written to `results/splits/shaoxing_dev_folds.csv` (`record, label, code, fold`). Every model and every T uses these folds. Later scripts read the fold column from this file; they never re-create the folds.

A3. **Features** (`src/features.py`), computed from the crop:
- Preprocessing: `neurokit2.ecg_clean(signal, sampling_rate=500, method="neurokit")` per lead.
- R peaks: `neurokit2.ecg_peaks(lead II, sampling_rate=500, method="neurokit")`.
- **Rate and RR (lead II):** heart rate = 60000 / **mean** RR in ms (needs ≥ 2 R peaks); SDNN, RMSSD, pNN50, RR range, coefficient of variation = SDNN / mean RR (need ≥ 3 R peaks). Otherwise NaN. (Amendment 2.)
- **P-wave consistency (leads II and V1):** for every lead-II R peak whose region starts inside the crop, take the cleaned signal from 250 ms to 60 ms before the R peak; `p_consistency` = median Pearson correlation over all pairs of these segments. NaN if fewer than 2 segments. High when every beat has the same P wave (sinus), near 0 when there is none (AFIB). (Amendment 3; replaces the DWT P-wave and QRS features.)
- **Atrial spectrum (leads II and V1):** replace 120 ms centred on each R peak by linear interpolation. Welch PSD with `nperseg = min(1000, len(crop))`. Features: power 4–9 Hz / power 1–40 Hz; dominant frequency in 3–12 Hz; maximum power in 4–6 Hz / **median power in 3–12 Hz** (exact form of "peak sharpness").
- **R amplitude (leads II and V1):** median cleaned amplitude at the lead-II R peak times.
- **16 features in total**, in this order: `hr, rr_sdnn, rr_rmssd, rr_pnn50, rr_range, rr_cv, p_consistency_II, p_consistency_V1, af_power_ratio_II, af_dom_freq_II, af_peak_ratio_II, af_power_ratio_V1, af_dom_freq_V1, af_peak_ratio_V1, r_amp_II, r_amp_V1`. Names, order and definitions are fixed in `src/features.py` and written to `results/features/feature_list.json`.
- One set of R peaks (lead II) is used for every feature of a crop.
- Run: `python src/features.py --split dev` (Stage A; about 4 minutes on 7 cores). `--split test` only at step B3.
- QC (development only): `python src/feature_qc.py` writes `results/features/qc_dev.json` (heart-rate check, R-peak counts, NaN shares, class medians).
- Feature tables are saved under `DATA/derived/` (outside the repository).

A4. **Models.** All balanced across classes, no age or sex, seed 4400.

| Model | Input | Library and class | Tuning grid (Stage A, per T) |
|---|---|---|---|
| M_HR (floor) | heart rate only | `sklearn.ensemble.HistGradientBoostingClassifier(class_weight="balanced")` | none; defaults |
| **M_feat (main)** | 16 features, NaN passed through | `HistGradientBoostingClassifier(class_weight="balanced")` | `learning_rate` ∈ {0.05, 0.1}, `max_leaf_nodes` ∈ {15, 31}, `max_iter` ∈ {200, 400} (8) |
| LR (secondary) | 16 features | `Pipeline(SimpleImputer(strategy="median"), StandardScaler(), LogisticRegression(class_weight="balanced", max_iter=5000))` | `C` ∈ {0.01, 0.1, 1, 10} (4) |
| MLP (secondary) | 16 features | `Pipeline(SimpleImputer(strategy="median"), StandardScaler(), MLPClassifier(early_stopping=True, max_iter=500))`; training rows resampled to equal class counts (`sklearn.utils.resample`), since `MLPClassifier` has no class weights | `hidden_layer_sizes` ∈ {(64,), (64, 32)}, `alpha` ∈ {1e-4, 1e-3} (4) |
| **M_raw (main)** | raw 12-lead crop at 250 Hz | PyTorch 1D CNN (below) | learning rate ∈ {1e-3, 3e-4} (2) |
| MiniRocket (secondary) | raw 12-lead crop at 250 Hz | `sktime.transformations.panel.rocket.MiniRocketMultivariate(random_state=4400)` → `StandardScaler` → `RidgeClassifierCV(alphas=np.logspace(-3, 3, 10), class_weight="balanced")` | none (alpha chosen internally) |

**Raw-signal input:** downsampled from 500 to 250 Hz (`scipy.signal.decimate(q=2, zero_phase=True)`), each lead z-scored within the crop.

**M_raw: 1D CNN.**
- Architecture: stem `Conv1d(12, 32, k=15, stride=2)` + BatchNorm + ReLU; 4 residual blocks (two `Conv1d(k=7)` each, channels 32, 64, 64, 128, stride 2 in the first conv of each block); global average pooling; dropout 0.3; linear to 6 classes. The same architecture is used at every T.
- Training: cross-entropy with balanced class weights; Adam; batch 64; up to 40 epochs; early stopping on validation R3 with patience 8. Inside CV the validation set is 10% of the training folds (stratified, seed 4400); the held-out fold is never used for early stopping.

A5. **CV.** For each T and each model configuration: train on 4 folds, predict the fifth, for all 5 folds. Pool the out-of-fold (OOF) predictions and compute R3. For each model and T, the configuration with the highest pooled R3 is selected. Its OOF predictions are the development result.

**Stage B: Shaoxing test set, once**

B1. For each T and each model: refit the selected configuration on the whole development set (CNN: 10% of it as the early-stopping validation set). Train the CNN with seeds 4400, 4401 and 4402; the test uses seed 4400, and the other two give the spread (§7).

B2. **Freeze.** Save models under `DATA/models/shaoxing_dev/`, write their SHA-256 to `results/models/manifest_dev.json`, commit.

B3. Predict the Shaoxing test set at every T, once, by one script, committed separately.

**Stage C: all Shaoxing → Ningbo, once**

C1. For each T and each model: refit the configuration selected in A5 on **all 9,887** Shaoxing units (CNN seed 4400; 10% early-stopping validation). No setting is changed. Save under `DATA/models/shaoxing_all/`, write `results/models/manifest_all.json`, commit.

C2. **Unseal Ningbo.** Only after C1 is committed: `python src/download_ecg_arrhythmia.py --part 2 --unseal-part2`. Record the date and commit hash in §15.

C3. **Ningbo unit list.** Rule, fixed now:
1. Start from the 34,905 part-2 records in the parts manifest.
2. Rhythm codes = the 11 codes in `src/dra_inspect.py` plus 251166008 and 17366009 (DRA §6).
3. Keep records with **exactly one** rhythm code, and that code is one of the six in §3.
4. Drop records with any all-zero lead, or with a header other than 12 leads × 5,000 samples at 500 Hz.
5. Among records with identical signal arrays, keep the lowest JS id (same rule as Shaoxing).
6. Drop any record whose signal hash equals a Shaoxing unit's.

C4. **Ningbo check, before any prediction.** Write `results/ningbo/unit_check.json`: counts per class, number dropped at each step, number of other Dx codes, and whether the format matches part 1. This looks at labels and format only, not at model output.

C5. Predict Ningbo at every T, once, by one script, committed separately.

**Order of commits:** VCM v2 → this PRD → split and fold files (A1–A2) → Stage A code and results → dev model manifest (B2) → Shaoxing test results (B3) → all-Shaoxing model manifest (C1) → Ningbo unit check (C2–C4) → Ningbo results (C5).

## 6. Validation procedure

- **Shaoxing test set (20%):** fixed in A1, never used for tuning, selection or early stopping, and predicted once (B3).
- **Development CV:** 5 folds from A2, the same for every model and T. Model selection (A5) uses pooled OOF R3 on these folds. Because selection uses the same folds, the selected configuration's CV R3 is slightly optimistic; the Shaoxing test set gives the unbiased estimate.
- **Stage C** uses the configurations selected in A5, refit on all Shaoxing. **Ningbo** is never used for tuning, selection or early stopping.
- Every record is one unit, so no record can be in two folds or in both development and test; this is checked (§12).

## 7. Primary metric and aggregation

- **Per-class recall** recall_c = (units of class c predicted as c) / (units of class c), on pooled OOF predictions, on the Shaoxing test set, and on Ningbo.
- **R3** = mean of recall_SI, recall_AFIB, recall_AFL (primary).
- **F1 (secondary):**
  - per-class precision_c = (units predicted as c that are c) / (units predicted as c); F1_c = 2·precision_c·recall_c / (precision_c + recall_c), with F1_c = 0 if class c is never predicted;
  - **F1-3** = mean of F1_SI, F1_AFIB, F1_AFL;
  - macro F1 over all six = `sklearn.metrics.f1_score(average="macro")`.
  - F1 is reported because recall alone ignores false positives: a model that labels many SR records as SI raises recall_SI without penalty, but lowers precision_SI and F1_SI.
  - F1 depends on class proportions, which differ between the Shaoxing test set and Ningbo, so F1 is not compared across sites. Recall does not depend on class proportions, which is why R3 stays the primary measure.
- Also: macro recall over all six; accuracy; confusion matrices.
- **Derived quantities**, per model, at each site:
  - window loss L(T) = R3(10 s) − R3(T);
  - per-class drop drop_c = recall_c(10 s) − recall_c(2 s);
  - raw − feature gap G(T) = R3(M_raw, T) − R3(M_feat, T), and ΔG = G(2 s) − G(10 s);
  - site gap = R3_Shaoxing-test(M, T) − R3_Ningbo(M, T).
- **Intervals:** paired, class-stratified bootstrap over test units, 2,000 resamples, seed 4400, every model and T on the same resample, for R3, F1-3 and every derived quantity. It covers test-unit sampling only.
- **F1 check on the decision:** the derived quantities L(T), drop_c, G(T) and ΔG are also computed with F1 in place of recall and reported beside the recall versions. They do not enter §9, but if they point the opposite way, this is stated.
- **CNN training spread:** R3 of seeds 4400–4402 on the Shaoxing test set, reported beside the seed-4400 interval but not merged into it.
- **Kept, not only the mean:** per-fold values in Stage A; every unit's prediction and probabilities.

## 8. Baseline and controls

All run through the same code path as the real analysis.

| Control | What | Pass criterion |
|---|---|---|
| Floor | M_HR at every T | reported; M_feat and M_raw must exceed it at 10 s for any comparison to mean anything |
| Majority class | always SB | R3 = 0 by definition; reported |
| Negative control | M_feat trained on **shuffled labels** (seed 4400), Stage A, T = 10 | R3 < 0.25 (chance ≈ 0.17) |
| Positive control | M_HR, Stage A, T = 10 | macro recall over SB / SR / ST ≥ 0.90, since those labels are rate thresholds |
| Crop identity | T = 10 crop | equals the full record, sample for sample |

## 9. Decision rule

Fixed now, before any result is seen. The **Shaoxing test set** decides the claim (VCM §8.4). Ningbo is judged by the same rules and reported beside it. Development CV is reported but decides nothing.

- **Part 1 (window loss):** supported if, for both M_feat and M_raw, R3 does not increase from 10 → 8 → 6 → 4 → 2 s and the 95% interval of L(2 s) lies above 0. Refuted if L(2 s) ≤ 0 for both.
- **Part 2 (which rhythm loses most, M_feat):** supported if drop_SI > drop_AFIB > drop_AFL. Refuted if the 95% interval of (drop_SI − drop_AFL) lies entirely below 0.
- **Part 3 (raw vs features):** supported if the 95% interval of ΔG lies above 0. Refuted if ΔG ≤ 0.
- Anything in between: weakened.
- **Small Ningbo classes:** if a class has fewer than 30 Ningbo units, it is dropped from Ningbo's R3 and reported on its own; parts 1–3 are then judged at Ningbo on the remaining classes and this is stated.
- **If Shaoxing and Ningbo disagree,** both are reported, and any claim about Ningbo is bounded accordingly.
- **Secondary models** (LR, MLP, MiniRocket) do not decide anything; disagreement with the main pair is reported.
- **No overall winner** is chosen between M_feat and M_raw. The question is how each changes with T.

## 10. Required outputs

Under `results/` (committed):

| Path | Content |
|---|---|
| `splits/shaoxing_test_ids.csv` (+ `.sha256`) | `record, label` |
| `splits/shaoxing_dev_folds.csv` | `record, label, fold` |
| `features/feature_list.json` | feature names, order and definitions |
| `features/manifest_dev.json`, `features/manifest_test.json` | feature-table hashes, row counts, NaN counts, versions |
| `features/qc_dev.json`, `features/qc_rpeak_detectors.csv` | feature QC (amendments 2–4) |
| `cv/oof_predictions.csv` | `record, fold, model, config, T, true, pred, p_SR … p_AFL` |
| `cv/metrics.csv` | `model, config, T, fold (or "pooled"), metric, value` |
| `cv/selected_configs.json` | selected configuration per model and T |
| `cv/controls.json` | §8 results with pass / fail |
| `models/manifest_dev.json`, `models/manifest_all.json` | model file names, SHA-256, settings, commit |
| `shaoxing_test/predictions.csv`, `metrics.csv`, `bootstrap.csv` | Stage B |
| `ningbo/unit_check.json` | C4 |
| `ningbo/predictions.csv`, `metrics.csv`, `bootstrap.csv` | Stage C |
| `versions.json` | §11 |

`bootstrap.csv` columns: `quantity, model, T, estimate, lo95, hi95`.

Figures (`results/figures/`):
1. R3 vs T, one line per model; panels for development CV, Shaoxing test and Ningbo; 95% intervals on the test panels.
2. Per-class recall vs T (six panels), M_feat and M_raw.
3. Confusion matrices at 10 s and 2 s, both main models, Shaoxing test and Ningbo.
4. G(T) and ΔG with intervals.

## 11. Library versions recorded

**Pinned environment** (`environment.yml`, conda-forge, environment name `bme4400-final`):

| Package | Version | Package | Version |
|---|---|---|---|
| python | 3.13.18 | statsmodels | 0.15.0 |
| numpy | 2.3.5 | wfdb | 5.0.0 |
| pandas | 2.3.3 | neurokit2 | 0.3.0 |
| scipy | 1.18.1 | pytorch | 2.14.1 |
| scikit-learn | 1.7.2 | sktime | 0.40.1 |
| matplotlib | 3.11.2 | pytest | 9.2.0 |

- The pins solve on macOS (arm64), Linux (CPU and CUDA builds) and Windows. `environment-lock-osx-arm64.txt` is the full exact package list of the reference Mac.
- `python checks/check_environment.py` must pass (every version equal to its pin) before any step in §5.

**Determinism settings for the CNN** (set at the top of the training script):
- `torch.use_deterministic_algorithms(True)`; `torch.backends.cudnn.benchmark = False`; environment variable `CUBLAS_WORKSPACE_CONFIG=:4096:8` on CUDA.
- `DataLoader(num_workers=0, generator=torch.Generator().manual_seed(seed))`; float32 throughout.
- With these, a rerun on the same device type reproduces the same predictions. Across device types (CPU, Apple MPS, NVIDIA CUDA) floating-point order differs, so CNN results may differ slightly; the tolerance is R3 within 0.01 (§12). The device used is recorded.

**Recorded at every run** in `results/versions.json`: Python and all pinned package versions, the device (CPU / MPS / CUDA and its name), the operating system, and the Git commit hash.

## 12. Verification and acceptance criteria

In `tests/` (pytest), all must pass before results are accepted:
- Input hashes in §2 match.
- §4 replication checks.
- `python checks/check_environment.py` passes.
- Shaoxing unit count 9,887 with the §3 class counts; all signal hashes distinct; split files match `SHA256SUMS`.
- Split and folds: the test-ID file hash equals the committed one; no record in both development and test; every development record in exactly one fold.
- Crop: length is exactly 500·T samples starting at sample 0; T = 10 returns the full record.
- Features computed on a crop do not change when samples after the crop are altered.
- §8 controls pass.
- Before B3 and C5: model files' SHA-256 equal the committed manifest.
- Ningbo: all IDs ≥ JS10647, none in the Shaoxing list, no signal hash shared with Shaoxing.
- Rerun: feature models and MiniRocket reproduce identical predictions; the CNN with the same seed reproduces R3 within 0.01.

## 13. Failure handling

- A check in §4 or §12 fails: stop, diagnose, record in the commit message. Do not continue.
- A record fails to load or hash: stop. Do not drop it silently; if it must be dropped, amend this PRD.
- A model fails to converge (warning): record it; raise `max_iter` only by amending this PRD.
- R peaks or delineation fail on a crop: features become NaN (expected at short T, not a failure). The count of NaN features per T is reported.
- A control fails (§8): stop and diagnose before reading any real result.
- Ningbo step C3 gives a class with fewer than 30 units: follow §9; do not change the rule.

## 14. Prohibited changes

Not allowed without amending this PRD first:
- tuning, selection, early stopping or feature choice that uses the Shaoxing test set or Ningbo;
- any change to models, features or settings after the B2 commit;
- re-running the Shaoxing test or Ningbo prediction, or running it on a subset;
- changing the split, the folds, the unit lists, the crop rule or the windows;
- adding age, sex or any non-ECG input;
- dropping records or classes after seeing results.

## 15. Protected-evidence boundary

- Raw records, figshare files, feature tables and model files stay in `~/bme4191_ecg/` (outside the repository). `.gitignore` blocks `*.hea`, `*.mat`, `*.dat`. `python checks/check_evidence_boundary.py` must pass before every commit.
- Signal values are not pasted into AI chats; scripts read them locally.
- **Ningbo (part 2) stays unread until the C1 model manifest is committed.** It is then downloaded with `--part 2 --unseal-part2`. Date and commit of the unsealing: _to be filled in at step C2._
