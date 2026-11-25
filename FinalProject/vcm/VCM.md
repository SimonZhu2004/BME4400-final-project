# Versioned Claim Memo (VCM) — BME4400 Final Project

This file keeps one name; Git history holds its versions.

---

## How to use this template

**Do not delete an omitted section.** Keep the heading and write:

> _Not applicable at this version — [reason]._

Keeping the skeleton stable means the memo diffs cleanly from one version to the next, so a reader can see exactly which claim states changed and which did not.

Sections 1–7 are **pre-evidence**. They can be completed honestly before you have inspected any data. Sections 8–12 require evidence and should stay marked not-applicable until you have it.

The point of a VCM is not to be right. It is to make your reasoning specific enough that it can be shown wrong later.

---

## 1. Current scientific question

Use the wording given in the assignment text.

**Version (v2):** In 12-lead ECGs from one clinical location (Shaoxing People's Hospital), how does using only the first 8, 6, 4 or 2 s of the recording, instead of the full 10 s, change the classification of six cardiac rhythms — sinus rhythm, sinus bradycardia, sinus tachycardia, sinus irregularity, atrial fibrillation and atrial flutter — and do models trained on the raw ECG signal lose less than models trained on a table of extracted features? Do the same patterns hold when models trained on Shaoxing are tested on a second site (Ningbo First Hospital)?

(The v1 wording is quoted in §12.)

**Source:**
- PhysioNet, *A large scale 12-lead electrocardiogram database for arrhythmia study*, v1.0.0 — https://physionet.org/content/ecg-arrhythmia/1.0.0/. Part 1 = the 10,247 Chapman-Shaoxing records (Shaoxing People's Hospital; `dra/DRA.md` §2).
- The 399 sinus-irregularity records, which part 1 lacks, come from the original 10,646-record release of the same data on figshare (collection *ChapmanECG*, 4560497). Part 1 is that release minus those 399 records, and its signals equal the figshare signals rounded to whole µV (DRA O22, O24, O30, O31).
- Part 2 (Ningbo First Hospital, 34,905 records) is sealed and has not been examined. It is used only as an external test set, downloaded after the models are frozen (§8.2).

**Rhythm classes.** In the data's own labels the six main rhythms are SR (sinus rhythm), SB (sinus bradycardia), ST (sinus tachycardia), SA (sinus irregularity), AFIB (atrial fibrillation) and AF (atrial flutter). Below, SI = sinus irregularity and AFL = atrial flutter.

| Rhythm | Records |
|---|---|
| SB | 3,889 |
| SR | 1,826 |
| AFIB | 1,780 |
| ST | 1,568 |
| AFL | 445 |
| SI | 399 |

Counts come from the figshare `Diagnostics.xlsx` and equal the 2020 paper's Table 2. Rhythm is effectively a single label per record. Other rhythms in the data: SVT (587), AT (121), AVNRT (16), AVRT (8) and SAAWR (7).

**What is known about the records:**
- **Each record** is one 10-s 12-lead resting ECG at 500 Hz: 12 leads × 5,000 samples, lead order I, II, III, aVR, aVL, aVF, V1–V6 (DRA O11). The signal is the part-1 `.mat` `val` array in µV. For the SI records it is round(figshare CSV), which is exactly how part-1 signals relate to figshare (DRA O30).
- **Row order:** row *k* of the figshare `Diagnostics.xlsx` is record JS*k* (DRA O22).
- **SI is recoverable** [O]: the 399 record IDs missing from part 1 are exactly the 399 SI rows of the original release, and their signals are complete and in the same format (DRA O24, O30, O31).
- **Sinus labels are rate labels** [O]: SB / SR / ST labels follow 60 / 100 bpm thresholds on the measured ventricular rate (`VentricularRate`) in 7,253 of 7,283 records, 99.6% (DRA O25).
- **SI is not rate-defined** [O]: 376 of its 399 records lie at 60–100 bpm, overlapping SR. AFIB and AFL span the whole rate range (DRA O26).
- **One ECG = one patient** [I], from the paper's equal subject and record counts. No file carries a patient identifier (DRA U5).
- **Duplicates** [O]: 13 pairs of part-1 records are byte-identical (DRA O10, O32). One more pair is among the SI records: the figshare CSVs of JS02561 and JS04771 are byte-identical, with identical Rhythm, age, sex and ventricular rate but different file names and timestamps (found by `src/make_split.py`, 2026-11-25; not in the DRA).
- **Zero leads** [O]: 15 records have at least one all-zero lead (DRA O9), plus 2 of the SI records (DRA O31).
- **Demographics:** rhythms differ by age and sex (e.g. AFIB patients are older).

## 2. Provisional expectation / claim

_What do you currently expect, and why do you expect it?_

I expect **shorter windows to hurt, unevenly across rhythms, and to hurt the feature-table model more than the raw-signal model**.

Because SB / SR / ST labels are heart-rate thresholds (§1), their recall mostly measures whether heart rate was estimated correctly. The claim is therefore stated on the three rhythms that are not rate-defined: **SI, AFIB and AFL**. "R3" below means macro recall over these three classes.

The claim has three parts:

1. **Window length.** For both main models, R3 falls as the window shortens. The loss is small from 10 s to 6 s and grows at 4 s and 2 s.
2. **Which rhythm loses most.** From 10 s to 2 s, SI loses the most recall, AFL the least, and AFIB is in between (drop_SI > drop_AFIB > drop_AFL).
3. **Raw signal vs features.** At 10 s the two main models are close. As the window shortens, the raw-signal model loses less than the feature-table model, so the gap (raw − feature) grows.

At Ningbo I expect parts 1–3 to hold in direction, with lower R3 overall than at Shaoxing. This expectation is reported but is not one of the three parts.

Why I expect this:

- **SI** is defined by beat-to-beat variation in RR intervals with normal P waves. At ~70 bpm a 2-s window holds two or three beats and a 4-s window about five, so there is little variation to see. In short windows SI should look like SR.
- **AFIB** has two signatures: irregular RR intervals, which need several beats, and absent P waves with fibrillatory baseline activity (f waves), which are visible in a single beat. In short windows it loses the first and keeps the second, so it should drop, but less than SI.
- **AFL** has flutter waves at ~300/min, i.e. about five per second. Even a 2-s window contains about ten, so AFL should be the most robust class.
- **Features vs raw signal.** The hand-crafted features lean on RR intervals (rate, RR variability), which become undefined when a window holds fewer than three R peaks — the case for most 2-s windows. P-wave and atrial-spectrum features are also estimated from fewer beats and get noisier. A model on the raw signal does not need R-peak detection or delineation, and can use whatever waveform shape is present. At 10 s the features summarise the rhythm well, so I expect the two to be close there.

## 3. Plausible alternative

_What is at least one different outcome that a reasonable person could expect instead?_

1. **The feature-table model holds up as well as, or better than, the raw-signal model at all windows.** The development set has about 7,900 records, and only about 320 SI and 350 AFL. That is small for a neural network. A raw-signal model may underfit the small classes, so the gap may not grow, or may favour the features.
2. **Window length barely matters down to 2 s.** If atrial activity (absent P waves, f waves, flutter waves) carries most of the information for AFIB and AFL, both models may lose little across the whole grid. Only SI would drop.
3. **SI is already poor at 10 s.** Ten seconds holds only ~11–12 beats, and sinus irregularity is often mild. If SI recall is low at 10 s, there is little left to lose, and part 2's ordering would fail for a trivial reason.
4. **AFL is not the most robust class.** With 2:1 conduction AFL looks like ST at ~150 bpm, and in short windows the flutter waves may be hidden by QRS and T waves. AFL could then drop as much as AFIB.

## 4. Claim boundary / stronger nonclaim

_What is the tempting stronger statement that your evidence will not support?_

The evidence will **not** support:

- that a **short strip from a wearable or single-lead device** is enough. This project keeps all 12 leads; it varies only the window length. Fewer leads is a separate question and is out of scope.
- anything about **windows shorter than 2 s**, or windows taken from elsewhere in the record (only the first T s is used).
- that the results apply to **hospitals, devices or populations other than Shaoxing and Ningbo**, or to ambulatory monitoring.
- **why** performance differs between Shaoxing and Ningbo. Patients, devices and labelling practice all differ between sites, and this design cannot separate them.
- that **raw-signal models are better than feature models in general**. The comparison is between the specific models and the one feature set declared in §8, each with a fixed development budget.
- that the raw-signal model **uses physiological information** such as flutter waves. Without separate interpretation work, its performance only shows association within this dataset.
- that SB / SR / ST are **recognised from their physiology**. Their labels are rate thresholds.
- that the result holds for **rarer rhythms** (SVT, AT, AVNRT, AVRT, SAAWR) or for **beat-level events** (e.g. premature beats), which can be absent from a short window.
- that a **clinical diagnosis** can be made from a short window. The labels are one hospital's physician labels on resting 10-s ECGs.

## 5. Important unknowns

_What do you not yet know that could change how this result should be interpreted?_

Unknowns about the dataset:

- **Why PhysioNet removed the 399 SI records** (DRA U1). Their signals look structurally normal (DRA O31), but two have all-zero leads.
- **Whether each record is a different patient** (DRA U5). The 14 identical pairs (DRA O10, O32, and the SI pair in §1) show that at least some duplication happened.
- **How the labels were made for SI, AFIB and AFL** (DRA U9). SB/SR/ST follow the machine-measured rate; it is not known whether the others also follow a machine statement.
- **Whether the "raw" signals were filtered before export** (DRA U8). Filtering affects P-wave and baseline features, and what the raw-signal models can see.

Unknowns about the design:

- **Whether a 10-s label still holds for a short crop.** AFIB and AFL are usually present through the whole strip. Sinus irregularity is often linked to breathing (a cycle of a few seconds), so a 2- or 4-s crop of an SI record may contain no irregularity at all. Near the 60 / 100 bpm boundaries, a crop's rate can also cross the threshold its 10-s label was based on. Part of any short-window loss may be the label no longer fitting the crop, not the model failing.
- **Whether the raw-signal models are trained well enough.** With ~320 SI and ~350 AFL development records, the CNN's result may depend on architecture and training choices more than the feature models'.
- **How many R peaks a short crop holds.** At 47 bpm (slow SB), a 2-s crop can contain a single R peak. The feature models must then work with missing rate and RR features.
- **Test-set size for small classes:** about 79 SI and 88 AFL. Per-class recall will have wide intervals, which may make parts 2 and 3 impossible to settle.

Unknowns about Ningbo (part 2, not yet examined):

- **How many records of each class it has**, and whether SI appears at all. In part 1, SI was removed from the PhysioNet release (DRA U1); part 2 may differ.
- **Whether its labels mean the same thing.** Ningbo labels come only from the header SNOMED codes, whereas Shaoxing labels come from the figshare Rhythm field. A different hospital may also have labelled rhythms differently.
- **Whether its records have the same format and quality** (12 leads × 5,000 samples at 500 Hz, zero leads, duplicates).

## 6. Revision trigger

_What specific evidence or reasoning would make you change your claim?_

I will revise the claim (before any test-set evaluation, if the trigger occurs during development) if:

- **SI recall at 10 s is near M_HR's** in development cross-validation. Then SI carries no signal even at full length (alternative 3). I report SI separately and state parts 1–2 on AFIB and AFL only.
- **The CNN does not beat M_HR at 10 s** in development. Then it is not trained adequately. I fix the training within the declared budget (§8.6), or narrow part 3 to "this CNN".
- **Visual inspection of short SI crops** (a random sample of 30 dev records at 2 s) shows that most contain no visible irregularity. Then I reinterpret SI's short-window loss as a label problem, not a model failure, and say so in §10.
- **My heart rate disagrees with VentricularRate** in more than 5% of development records by more than 5 bpm at 10 s. I fix the R-peak detection before interpreting anything.
- **The evaluation in §8 lands in the "weaken" or "refute" region.** I rewrite §10 accordingly; I do not change the rule in §8 after the fact.

## 7. Independent commitment statement

_One sentence: why are you committing this claim state using only your own background knowledge, before consulting peers, AI, literature, or the dataset?_

**Where this version came from:**
- **The question** (compare window lengths of 2, 4, 6, 8 and 10 s, and train on a feature table vs on the raw ECG) was chosen by our team on 2026-11-25. In v2 the team fixed the window as the first T s, kept 20% of Shaoxing as the test set, and added Ningbo as an external test site.
- **The model list** follows a teammate's draft plan (`lead_duration_sweep_idea.md`): logistic regression, gradient-boosted trees and an MLP on features; MiniRocket and a 1D CNN on the raw signal; heart rate only as the floor. That plan also swept the number of leads; we kept the window sweep and dropped the lead sweep.
- **From the earlier project and its DRA:** the dataset, the six classes, the restored SI records, and the finding that SB / SR / ST labels are rate thresholds. That finding is why the claim is stated on SI, AFIB and AFL.
- **AI (Claude Code):** drafted this memo's text and the physiology-based expectations in §2 (which rhythm needs how many beats). These are to be checked against our own understanding before the memo is committed as ours (AI-use appendix).
- **No feature has been computed and no model fitted** at this version.

## 8. Evidence contract / evaluation plan

_What analysis will you accept as answering the question, specified before you run it?_

Written 2026-11-25. No feature has been computed and no model fitted.

**8.1 Unit and number of independent units**

- **Unit:** one 12-lead ECG record, taken to be one patient (inferred; §5). Crops are not units; every crop belongs to its record.
- **Unit list rule:**
  1. Start from the 10,646 rows of the figshare `Diagnostics.xlsx`. Row *k* is record JS*k* (DRA O22).
  2. Keep rows whose Rhythm is SB, SR, ST, SA, AFIB or AF: **9,907**.
  3. Among records with identical signal arrays, keep the lowest JS id. In the six classes this drops five of the 13 part-1 pairs of DRA O10 (JS03005, JS03435, JS05900, JS06490, JS08755) and one SI pair (JS04771, identical to JS02561): **9,901**.
  4. Drop records with any all-zero lead: the 15 of DRA O9 and the 2 SI of DRA O31. Fourteen of them fall in the six classes: **9,887 units**.
- **Final counts:** SB 3,888, SR 1,825, AFIB 1,778, ST 1,562, AFL 438, SI 396.
- **Script:** `python src/make_split.py` builds this list, asserts every count above, and writes `results/splits/` (§8.2).
- **Label:** the `Diagnostics.xlsx` Rhythm value, applied to every crop of the record.
- **Signal:** all 12 leads, the part-1 `.mat` `val` (µV). For the SI records, round(figshare CSV) (DRA O30).

**8.2 Held-out data**

- Sort the 9,887 units by JS id and split them with `sklearn.model_selection.train_test_split(test_size=0.2, stratify=label, random_state=4400)`, so each class keeps its proportion in both parts. This gives a **test set of 1,978 records** (SB 778, SR 365, AFIB 356, ST 312, AFL 88, SI 79) and a **development set of 7,909** (SB 3,110, SR 1,460, AFIB 1,422, ST 1,250, AFL 350, SI 317).
- The split and the 5 development folds are in `results/splits/` with their SHA-256 in `results/splits/SHA256SUMS`. Every class is within one record of its expected share in the test set, the development set and every fold.
- The test-ID list is written to a file, and its SHA-256 is committed **before** any feature is computed or any model trained. That committed file, not the code, defines the split.
- All feature design, model choice and tuning use the development set only, with 5-fold `StratifiedKFold` (seed 4400), the same folds for every model and window. Each record gives one crop per window, so a record is never in two folds. The 1D CNN's early stopping uses 10% of the training folds, never the held-out fold.
- The Shaoxing test set is evaluated **once**, by one script, after the PRD freezes all models.
- **External test (Ningbo):** the selected settings are refit on all 9,887 Shaoxing units, frozen, and only then is part 2 downloaded. Ningbo units are records with exactly one rhythm code that is one of the six classes, after the same exclusions as Shaoxing (zero leads, duplicates); the exact rule is in PRD §5 step C3. Ningbo is predicted **once** at every window and never used for tuning.

**8.3 Windows, models and main quantities**

- **Windows:** T ∈ {10, 8, 6, 4, 2} s. The crop is the **first T seconds** of each record (samples 0 to 500·T), for training, validation and testing, at both sites. A separate set of models is trained at every T. All processing uses only the crop.
- **Feature table:** computed once per lead per crop.
  - Groups: rate (60 / median RR); RR variability (SDNN, RMSSD, pNN50, RR range, coefficient of variation); P wave (fraction of beats with a detected P wave, P amplitude, PR interval and its variability); atrial spectrum (power 4–9 Hz, dominant frequency, peak sharpness near 4–6 Hz); QRS width and amplitude.
  - RR-variability features are missing when a crop has fewer than 3 R peaks.
  - Feature selection, if any, is done inside each CV fold.
- **Models, each fit separately at every T:**

| Model | Input | Role |
|---|---|---|
| M_HR | heart rate only (R peaks on lead II) | floor |
| **M_feat: gradient-boosted trees** (`HistGradientBoostingClassifier`, accepts missing values) | feature table | **main feature model** |
| Logistic regression (multinomial, standardized; missing values imputed) | feature table | secondary |
| MLP | feature table | secondary |
| **M_raw: 1D CNN** (small residual network) | raw 12-lead crop | **main raw-signal model** |
| MiniRocket | raw 12-lead crop | secondary |

  - The raw signal may be downsampled from 500 Hz to 250 Hz for both raw-signal models.
  - The exact feature list, R-peak detector, network architecture and training settings are development choices, fixed in the PRD before the test set is touched. The rules below do not depend on them.
  - No model uses age or sex. All use class-balanced weighting.
- **Per-class recall** on the test set: recall_c = (test records of class c predicted as c) / (test records of class c).
- **R3(model, T)** = the unweighted mean of recall_SI, recall_AFIB and recall_AFL. This is the main measure.
- **Main quantities** (main models only):
  - **Part 1, window loss:** L(model, T) = R3(model, 10 s) − R3(model, T), for M_feat and M_raw.
  - **Part 2, per-class loss:** drop_c = recall_c(M_feat, 10 s) − recall_c(M_feat, 2 s), for c ∈ {SI, AFIB, AFL}.
  - **Part 3, raw vs features:** G(T) = R3(M_raw, T) − R3(M_feat, T), and the change **ΔG = G(2 s) − G(10 s)**.
- Always reported alongside: all six per-class recalls for every model and window, macro recall over all six classes, and the gain over M_HR.
- **F1, secondary:** per-class F1, F1-3 (macro F1 over SI, AFIB and AFL) and macro F1 over all six, with the same bootstrap intervals. Recall ignores false positives (labelling many SR records as SI raises recall_SI without penalty); F1 does not. F1 depends on class proportions, which differ between sites, so it is not compared across sites and R3 stays the primary measure. The quantities L, drop_c, G and ΔG are also reported with F1 in place of recall; they do not decide the claim, but disagreement with the recall versions is stated.
- **Secondary models** are reported with the same quantities. They do not count in §8.4, but if they point the opposite way from the main pair I say so in §10.
- **At Ningbo**, the same quantities are computed, plus the site gap R3_Shaoxing-test(model, T) − R3_Ningbo(model, T).

**8.4 What supports, weakens or refutes the claim**

The Shaoxing test set decides parts 1–3. Ningbo is judged by the same rules and reported beside it; if a class has fewer than 30 Ningbo units, it is left out of Ningbo's R3 and reported on its own. If the two sites disagree, both are reported and the claim is bounded to the site where it held.

Part 1 (window loss):
- **Supports:** for both M_feat and M_raw, R3 decreases from 10 → 8 → 6 → 4 → 2 s (point estimates; equal values count as no decrease), and the 95% interval of L(model, 2 s) lies above 0.
- **Weakens:** R3 decreases for one main model only, or the interval of L(model, 2 s) includes 0.
- **Refutes:** L(model, 2 s) ≤ 0 for both main models. Then window length down to 2 s does not affect these rhythms.

Part 2 (which rhythm loses most), using M_feat:
- **Supports:** drop_SI > drop_AFIB > drop_AFL (point estimates).
- **Weakens:** only part of the order holds, or the intervals of the differences include 0.
- **Refutes:** the 95% interval of (drop_SI − drop_AFL) lies entirely below 0. Then AFL loses more than SI, and alternatives 3 or 4 in §3 are right.

Part 3 (raw vs features):
- **Supports:** the 95% interval of ΔG lies above 0, i.e. the raw-signal model's advantage grows as the window shortens.
- **Weakens:** ΔG > 0 but its interval includes 0.
- **Refutes:** ΔG ≤ 0. Then the feature-table model holds up at least as well as the raw-signal model (alternative 1 in §3).

**8.5 Uncertainty**

- **Can be quantified, at the record level:** paired, class-stratified bootstrap over test records (2,000 resamples, seed 4400). Every model and window is scored on the same resample. It gives 95% percentile intervals for every R3, L, drop_c, G and ΔG. It covers sampling variation among the test ECGs only.
- **Reported from development but not part of the test intervals:** the spread of the CNN over 3 training seeds at each T (the test uses one seed fixed in the PRD).
- **Can only be described:**
  - label error, especially at the 60/100 bpm boundaries and for mild SI;
  - whether a 10-s label fits a short crop (§5);
  - the position of the single test crop;
  - whether units are truly independent patients (U5);
  - why the SI records were removed (U1);
  - pre-export filtering (U8);
  - variation from the single random split and from development choices;
  - that all data come from one hospital and one device system.

**8.6 Ways the analysis could mislead me, and the check for each**

1. **One record in both training and evaluation.** *Check:* each record gives one crop per window and belongs to one fold. Confirm no test JS id appears in the development set, and compute the SHA-256 of every unit's signal array to confirm all 9,887 are distinct (`src/make_split.py` does both).
2. **SB / SR / ST inflating the result.** *Check:* the main measure is R3 over SI, AFIB and AFL; SB/SR/ST are reported but do not count for or against the claim. M_HR is fit at every window.
3. **Unequal effort on the two sides.** Part 3 could reflect which model was tuned harder. *Check:* M_feat and M_raw get the same development budget, at most 20 configurations each, declared in the PRD. The number of configurations tried is reported.
4. **Choosing test crops.** *Check:* the crop is always the first T seconds, whatever it contains. Crops are never selected or filtered by content.
5. **Tuning on the test set.** *Check:* the test-ID file and its hash are committed before any feature or model code runs. The single test evaluation is a separate commit that comes after the PRD that freezes the models. The Git log shows the order.
6. **Ningbo influencing the models.** *Check:* part 2 is downloaded only after the all-Shaoxing model manifest is committed, with the download script's `--unseal-part2` flag. Model hashes are checked against the manifest before Ningbo is predicted.
7. **Too many models and windows.** Six models × five windows invites picking the comparison that looks best. *Check:* only the main pair (M_feat, M_raw) and the quantities in §8.3 decide the claim, fixed here before any result.
8. **Demographic shortcut.** *Check:* no model is given age or sex.

**8.7 Additional items the claim needs**

- **Classify → held-out data at the claim's unit:** §8.2. Records (= patients, inferred) are held out; crops never cross the split.
- **"Loses less" → comparator:** M_feat and M_raw are compared on the same test crops at every window. M_HR is the floor.
- **Confounding / selection found in the DRA, and how each is handled:**
  - SI removed from the public release: restored from the same export (DRA O30, O31). The reason for removal remains unknown (§5).
  - Duplicate records: removed (§8.1).
  - Zero-lead records: excluded (§8.1). This removes 7 of the 445 AFL records; I will report this.
  - Age and sex differ by class: not used as features.
  - Class imbalance: class-balanced weighting, and macro recall rather than accuracy.
- **Reach beyond the data:** the claim is decided on 12-lead resting ECGs from Shaoxing, with Ningbo as one external site. Saying the same about short strips in general would need more hospitals and devices, and saying it about wearables would need fewer leads. Neither is part of this project.

## 9. Observed evidence

_What did the declared analysis actually produce?_

> _Not applicable at this version — no analysis has been run yet._

## 10. Evidence-supported bounded claim

_What can you now assert, bounded to what you actually examined?_

> _Not applicable at this version — no analysis has been run yet._

## 11. Verification / provenance note

_How would someone else confirm this?_

> _Not applicable at this version — no analysis has been run yet._

## 12. Revision rationale

_What changed since the previous version, and what caused it?_

v1 → v2 (2026-11-25), written with PRD v0:

- **§1:** the v1 wording read: *"…how does shortening the recording window from 10 s to 8, 6, 4 and 2 s change the classification of six cardiac rhythms … and do models trained on the raw ECG signal lose less than models trained on a table of extracted features?"* v2 specifies the **first** T seconds and adds the Ningbo question.
- **§8.3, crop:** v1 trained on random crops and tested on the middle T s. v2 uses the first T s for training and testing. One crop per record means no crop augmentation and no grouping problem in CV.
- **§8.2, external test:** Ningbo (part 2) is unsealed after the models are frozen and used once as an external test set. §4 and §5 are updated to match.
- **§8.2, CV:** plain stratified 5-fold CV (one crop per record), with model settings selected on pooled out-of-fold R3.
- **Why:** the team decided the window should be the start of the recording, as when a recording is stopped early, and wanted to see whether models trained at one site hold at another.
- §2 parts 1–3 are unchanged. §9–11 remain not applicable.
- **Amended the same day, when the split was built:** `src/make_split.py` found a 14th identical pair, two SI records (JS02561, JS04771) whose figshare CSVs are byte-identical. The DRA had checked duplicates only among part-1 `.mat` files, which do not include SI. Under the existing rule (keep the lower JS id) JS04771 is dropped: units 9,888 → 9,887, SI 397 → 396. The test set is unchanged in size (1,978).

v0 → v1 (2026-11-25):

- **§1:** the question is stated for the first time: the effect of window length (10, 8, 6, 4, 2 s) on six-rhythm classification, and models trained on a feature table vs on the raw ECG. The dataset description is unchanged.
- **§2–4, §6–8:** written for the first time.
- **§5:** the dataset unknowns are unchanged; unknowns about the design are added (whether a label fits a short crop, raw-model training, R peaks in short crops, small test classes).
- **Why:** the team chose to compare recording lengths, and asked whether models on the raw ECG and on extracted features respond to shorter recordings differently. The models follow a teammate's draft plan. That plan also swept the number of leads; the lead sweep is not part of this version, to keep the project to one main factor (window length) and one comparison (features vs raw signal).
- §9–11 remain not applicable.
