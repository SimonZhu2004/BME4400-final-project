# Versioned Claim Memo (VCM) — Project 5

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

**Question 2:** Can we classify the kind of arrhythmia of the patient, based on a certain set of features extracted from the raw ECG recordings, in the dataset from a certain clinical location?

**Version (v3):** Can features extracted from 12-lead ECGs classify six cardiac rhythms — sinus rhythm, sinus bradycardia, sinus tachycardia, sinus irregularity, atrial fibrillation and atrial flutter — in the records from one clinical location, Shaoxing People's Hospital, and do those features add information beyond heart rate?

**Source:**
- PhysioNet, *A large scale 12-lead electrocardiogram database for arrhythmia study*, v1.0.0 — https://physionet.org/content/ecg-arrhythmia/1.0.0/. Part 1 = the 10,247 Chapman-Shaoxing records (`dra/DRA.md` §2).
- The 399 sinus-irregularity records, which part 1 lacks, come from the original 10,646-record release of the same data on figshare (collection *ChapmanECG*, 4560497). Part 1 is that release minus those 399 records, and its signals equal the figshare signals rounded to whole µV (DRA O22, O24, O30, O31).

(Earlier wording of the Version, v0–v2, is quoted in §12.)

## 2. Provisional expectation / claim

_What do you currently expect, and why do you expect it?_

I expect **yes, with an uneven answer across classes, and with the gain over heart rate concentrated in the rhythms that are not defined by rate**. In the data's own labels the six rhythms are SR, SB, ST, SA (sinus irregularity), AFIB (atrial fibrillation) and AF (atrial flutter); I write SI for sinus irregularity and AFL for atrial flutter.

The claim has three parts:

1. **Main claim.** A classifier using rhythm features from the 12-lead ECG (heart rate, RR-interval statistics and irregularity, P-wave presence and morphology, P–QRS relationship, atrial-activity / baseline spectral content) will achieve higher macro-averaged recall over the six classes than the same kind of classifier given heart rate alone. The gain will come almost entirely from SI, AFIB and AFL.
2. **Ordering (kept from v0–v2).** Among the classes not defined by rate, SI recall > AFIB recall > AFL recall. Most SI errors will be confused with SR or SB, and most AFL errors with ST or AFIB.
3. **SB / SR / ST are a consistency check, not evidence.** Their labels follow 60 / 100 bpm thresholds on the measured ventricular rate in 99.6% of records (DRA O25). High recall for these three classes will only show that my heart-rate estimate agrees with the recorded rate. I no longer count it as support for the claim.

What the DRA established that this claim now rests on:

- **Classes** [O]: SB 3,889, SR 1,826, AFIB 1,780, ST 1,568, AFL 445, SI 399 records (figshare `Diagnostics.xlsx`, equal to the 2020 paper's Table 2). Rhythm is effectively a single label per record.
- **SI is recoverable** [O]: the 399 record IDs missing from part 1 are exactly the 399 SI rows of the original release, and their signals are complete and in the same format (DRA O24, O30, O31). The SI part of the claim is therefore testable. Why PhysioNet dropped them is not known (DRA U1).
- **Sinus labels are rate labels** [O]: see part 3 above. SI is not rate-defined: 376 of its 399 records lie at 60–100 bpm, overlapping SR. AFIB and AFL span the whole rate range (DRA O26).
- **One ECG = one patient** [I], from the paper's equal subject and record counts. No file carries a patient identifier (DRA U5).
- **Excluded rhythms:** AT (121), AVNRT (16), AVRT (8) and SAAWR (7) are too rare. SVT (587) is excluded because it is not one of the rhythms in the question, not because it is rare.

Why I expect this, from background physiology:

- **SB / SR / ST** are sinus rhythms that differ mainly in rate (SB below ~60 bpm, SR ~60–100 bpm, ST above ~100 bpm). Heart rate alone separates them; the remaining errors should sit near the 60 and 100 bpm boundaries. The data now show the labels were assigned essentially this way.
- **SI** has normal sinus P waves but beat-to-beat RR variation. Because its P waves are intact, P-wave features can be extracted reliably and, together with RR variability, should identify it more easily than AFIB. Heart rate alone cannot find it, because its rate overlaps SR. Its mild cases may overlap with SR or SB.
- **AFIB** is "irregularly irregular" with no organised P waves. RR irregularity flags it, but without correct P waves the atrial features are harder to extract reliably, so AFIB should be harder to classify than SI. Heart rate alone only partly separates it.
- **AFL** should be the hardest class. With 2:1 conduction its ventricular rate (~150 bpm) is regular and overlaps with ST; with variable block its RR intervals become irregular and overlap with AFIB. It is also the smallest class but one (445).

## 3. Plausible alternative

_What is at least one different outcome that a reasonable person could expect instead?_

1. **SI is harder than AFIB, not easier.** A 10-s ECG at ~70 bpm holds only about 11–12 beats. Sinus irregularity is often mild, so its RR variation over so few beats may be hard to tell apart from normal variation in SR. AFIB's irregularity, by contrast, is gross and needs no P-wave features at all. A reasonable person would then expect **AFIB recall > SI recall**, with SI largely absorbed into SR. This is the opposite of part 2 of my claim.
2. **AFL is not the hardest class.** Flutter waves (~300/min sawtooth, best seen in II, III, aVF and V1) have a strong, regular spectral signature. If the atrial-activity / spectral features capture it, AFL could be recognised better than AFIB, whose fibrillatory baseline is low-amplitude and variable.
3. **Heart rate alone does nearly as well as the full feature set.** Because four of six classes are partly separable by rate (SB, SR, ST, and AFL at ~150 bpm), the macro-recall gain from the other features could be small. This would make the main claim true only in a trivial sense.

## 4. Claim boundary / stronger nonclaim

_What is the tempting stronger statement that your evidence will not support?_

The evidence will **not** support:

- that the features (or a model built on them) can **diagnose arrhythmias clinically**, or perform at the level of a physician. The labels are one hospital's physician labels on resting 10-s ECGs, nothing more.
- that the classifier **generalises to other hospitals, devices or populations**, including Ningbo (part 2, sealed and not examined) or ambulatory / in-hospital monitoring.
- that **sinus bradycardia, sinus rhythm and sinus tachycardia are recognised from their physiology**. Their labels are rate thresholds; separating them shows only that heart rate was measured correctly.
- that any feature **explains the mechanism** of a rhythm. Feature usefulness is association within this dataset.
- that the result holds for **multi-rhythm or rarer rhythms** (SVT, AT, AVNRT, AVRT, SAAWR), which are excluded.
- that it holds **per patient** in a strict sense: the unit is one ECG, and one ECG per patient is an inference (§5).

## 5. Important unknowns

_What do you not yet know that could change how this result should be interpreted?_

- **Why PhysioNet removed the 399 SI records** (DRA U1, residual). If they were removed for a quality reason specific to them, SI results may not mean what they appear to. Their signals look structurally normal (DRA O31), but two have all-zero leads.
- **Whether each record is a different patient** (DRA U5). If some patients have several ECGs, records are not fully independent and the uncertainty in §8 is too narrow. The 13 identical pairs (DRA O10, O32) show that at least some duplication happened.
- **How the labels were made for SI, AFIB and AFL** (DRA U9, residual). SB/SR/ST follow the machine-measured rate. If SI, AFIB and AFL labels also follow a machine statement, the classifier would partly be re-learning MUSE's algorithm rather than physician judgment.
- **Whether the "raw" signals were filtered before export** (DRA U8). Filtering affects P-wave and baseline features, the ones my main claim depends on.
- **How many SI and AFL records the test set will hold**: about 79 and 88. Per-class recall for these classes will have wide uncertainty, which may make the ordering in claim part 2 impossible to settle.
- **Whether my heart-rate estimate agrees with the recorded VentricularRate.** If it does not, sinus-class errors and the heart-rate-only comparator would both reflect my measurement, not the rhythms.

## 6. Revision trigger

_What specific evidence or reasoning would make you change your claim?_

I will revise the claim (before any test-set evaluation, if the trigger occurs during development) if:

- **The SI records turn out to be defective.** If visual inspection of SI records, or development-set checks, show systematic quality problems absent from the other classes, I drop SI and return to the five-class claim of v1.
- **SI, AFIB or AFL labels turn out to follow a machine statement.** If documentation or the data show that, I narrow the claim to "reproduces the labelling algorithm" instead of "recognises the rhythm".
- **Patients repeat.** If evidence appears that many patients have several records, I change the unit and the split to the patient level, or state the claim at the ECG level only.
- **My heart rate disagrees with VentricularRate** in more than 5% of development units by more than 5 bpm. I fix the measurement before interpreting anything, and narrow the comparator if it cannot be fixed.
- **The evaluation in §8 lands in the "weaken" or "refute" region.** I rewrite §10 accordingly; I do not change the rule in §8 after the fact.

## 7. Independent commitment statement

_One sentence: why are you committing this claim state using only your own background knowledge, before consulting peers, AI, literature, or the dataset?_

**From my own thinking in Assignment 5.1 (VCM v0):** choosing Question 2 with rhythm classification at one hospital; choosing the six rhythms (I added sinus irregularity and sinus bradycardia myself); the physiology-based expectation, in particular that **SI is easier than AFIB** because SI keeps normal P waves. I kept this ordering when the AI's first draft ranked AF above SI (AI-use appendix, Entry 1).

**What has shaped the project since:**
- **Data:** the DRA showed SI missing from part 1, the AF/AFIB naming, the hospital split, duplicates and zero leads. The repair (2026-11-12) showed the 399 missing records are SI and recoverable, and that SB/SR/ST labels are rate thresholds. That last finding moved the claim from "can we classify" to "do features add information beyond heart rate".
- **My own inferences:** one ECG per patient; the 399 missing records are SI (now confirmed).
- **AI (Claude Code):** drafted text, wrote the inspection scripts, found the original figshare release, and proposed the heart-rate-only comparator and the reframing of SB/SR/ST as a consistency check. I accepted these after checking them against the outputs (AI-use appendix, Entries 1–7).
- **Instructors / course:** the assignment structure (DRA before analysis, evidence contract before results). Removing the validation-split wording in v1 was my decision for that checkpoint.

## 8. Evidence contract / evaluation plan

_What analysis will you accept as answering the question, specified before you run it?_

Written 2026-11-12. No feature has been computed and no model fitted.

**8.1 Unit and number of independent units**

- **Unit:** one 10-s 12-lead ECG record, taken to be one patient (inferred; §5).
- **Unit list rule:**
  1. Start from the 10,646 rows of the figshare `Diagnostics.xlsx`. Row *k* is record JS*k* (DRA O22).
  2. Keep rows whose Rhythm is SB, SR, ST, SA, AFIB or AF: **9,907**.
  3. From each of the 13 byte-identical pairs (DRA O10), drop the member with the higher JS id. Five of them fall in the six classes (JS03005, JS03435, JS05900, JS06490, JS08755): **9,902**.
  4. Drop records with any all-zero lead: the 15 of DRA O9 and the 2 SI of DRA O31. Fourteen of them fall in the six classes (AFL 7, ST 4, SR 1, SI 2): **9,888 units**.
- **Final counts:** SB 3,888, SR 1,825, AFIB 1,778, ST 1,562, AFL 438, SI 397.
- **Label:** the `Diagnostics.xlsx` Rhythm value.
- **Signal:** the part-1 `.mat` `val` (µV). For the SI records, round(figshare CSV), which is exactly how part-1 signals relate to figshare (DRA O30).
- **Independence:** the 9,888 units are treated as independent. This rests on the one-ECG-per-patient inference (U5) and on removing the known duplicates.

**8.2 Held-out data**

- Sort the 9,888 units by JS id and split them with `sklearn.model_selection.train_test_split(test_size=0.2, stratify=label, random_state=4191)`. This gives a **test set of about 1,978 units** (about SB 778, SR 365, AFIB 356, ST 312, AFL 88, SI 79) and a development set of the rest.
- The test-ID list is written to a file, and its SHA-256 is committed **before** any feature is computed. That committed file, not the code, defines the split.
- All feature design, model choice and tuning use the development set only, e.g. stratified 5-fold cross-validation inside it.
- The test set is evaluated **once**, by one script, after the PRD freezes both models.

**8.3 Main quantity and exact rule**

- **Two models of the same family and the same development procedure:**
  - **M_full** uses all signal features.
  - **M_HR** uses heart rate only.
  - Heart rate = 60 / (median RR interval in s), with R peaks detected on lead II by the same detector M_full uses.
  - Neither model uses age or sex.
- **Per-class recall** on the test set: recall_c = (test units of class c predicted as c) / (test units of class c).
- **Macro recall** = the unweighted mean of recall_c over the six classes.
- **Main quantity: Δ = macro recall(M_full) − macro recall(M_HR)**, reported together with all six per-class recalls of both models and the per-class gains g_c = recall_c(M_full) − recall_c(M_HR).
- **Baseline for scale:** always predicting the majority class (SB) has macro recall 1/6 ≈ 0.167. Both models must exceed it for any comparison to mean anything.
- **Unresolved:** the model family, the R-peak detector and the full feature list. These are development choices. They will be fixed in PRD v0 on the development set before the test set is touched, and the rule above does not depend on them.

**8.4 What supports, weakens or refutes the claim**

Main claim (part 1):
- **Supports:** the 95% interval of Δ (§8.5) lies above 0, **and** each of g_SI, g_AFIB, g_AFL is larger than every one of g_SB, g_SR, g_ST.
- **Weakens:** Δ > 0 but its interval includes 0; or the interval is above 0 but the gain is not concentrated in SI, AFIB and AFL (alternative 3 in §3).
- **Refutes:** Δ ≤ 0. In that case the features add nothing measurable beyond heart rate.

Ordering (part 2), using M_full:
- **Supports:** SI recall > AFIB recall > AFL recall (point estimates).
- **Weakens:** only part of the order holds, or the intervals of the differences include 0.
- **Refutes:** the 95% interval of (recall_SI − recall_AFIB) lies entirely below 0. This would mean alternative 1 in §3 is right and my v0 prediction is wrong.

Consistency check (part 3): I report SB/SR/ST recall and the agreement of my heart rate with VentricularRate. These do not count for or against the claim.

**8.5 Uncertainty**

- **Can be quantified, at the unit level:** paired, class-stratified bootstrap over test units (2,000 resamples, seed 4191; both models scored on the same resample). It gives 95% percentile intervals for Δ, each macro recall, each recall_c, each g_c and recall_SI − recall_AFIB. It covers sampling variation among the test ECGs only.
- **Can only be described:**
  - label error, especially at the 60/100 bpm boundaries and for mild SI;
  - whether units are truly independent patients (U5);
  - why the SI records were removed (U1);
  - pre-export filtering (U8);
  - variation from the single random split and from development choices;
  - that all data come from one hospital and one device system.

**8.6 Ways the analysis could mislead me, and the check for each**

1. **Leakage of the same ECG into both sets.** *Check:* compute the SHA-256 of every unit's signal array and confirm all 9,888 are distinct. Also confirm no test JS id appears in the development set.
2. **Heart-rate circularity inflating the result.** The sinus classes could make M_full look good, or M_HR could be crippled by a poor rate estimate. *Check:* also report macro recall over {SI, AFIB, AFL} only, for both models. On the development set, confirm that my heart rate is within 5 bpm of VentricularRate for at least 95% of units (§6).
3. **Demographic shortcut.** Rhythms differ in age and sex (e.g. AFIB patients are older), so a model could rank classes by who the patient is. *Check:* neither model is given age or sex. On the development set, fit an age-and-sex-only model with the same procedure and report its per-class recall. If it rivals M_full for a class, I say so in §10.
4. **Tuning on the test set.** *Check:* the test-ID file and its hash are committed before any feature code runs. The single test evaluation is a separate commit that comes after the PRD that freezes the models. The Git log shows the order.

**8.7 Additional items the claim needs**

- **Classify → held-out data at the claim's unit:** §8.2. Records (= patients, inferred) are held out.
- **"Beats" → comparator:** M_HR is the comparator for the main claim. The majority class (macro recall 1/6) is the floor.
- **Confounding / selection found in the DRA, and how each is handled:**
  - SI removed from the public release: restored from the same export (DRA O30, O31). The reason for removal remains unknown (§5, §6).
  - Duplicate records: removed (§8.1).
  - Zero-lead records: excluded (§8.1). This removes 7 of the 445 AFL records; I will report this.
  - Age and sex differ by class: not used as features (check 3).
  - Class imbalance: handled by using macro recall rather than accuracy.
- **Reach beyond the data:** the claim is limited to Shaoxing. Saying the features add information beyond heart rate in general would need independently labelled 12-lead ECGs from another hospital, e.g. Ningbo (part 2, sealed). I do not know whether that hospital labelled the same rhythms in the same way, so it is not part of this project.

## 9. Observed evidence

_What did the declared analysis actually produce?_

> _Not applicable at this version, no analysis has been run yet._

## 10. Evidence-supported bounded claim

_What can you now assert, bounded to what you actually examined?_

> _Not applicable at this version, no analysis has been run yet._

## 11. Verification / provenance note

_How would someone else confirm this?_

> _Not applicable at this version, no analysis has been run yet._

## 12. Revision rationale

_What changed since the previous version, and what caused it?_

v2 → v3 (2026-11-12, Assignment 5.4):

- **§1 changed, for a data reason.** The v2 Version read: *"Can we classify six cardiac rhythms — sinus rhythm, sinus bradycardia, sinus tachycardia, sinus irregularity, atrial fibrillation and atrial flutter — using features extracted from 12-lead ECG recordings from one clinical location, Shaoxing People's Hospital (part 1 of the database)?"*
  - v3 adds "do those features add information beyond heart rate?".
  - The data now include the 399 SI records from the original release (DRA O24, O30, O31), so the six classes are all testable.
- **§2 changed, for a scientific reason.** The v2 falsifiable form read: *"per-class recall will be highest for the rate-defined sinus classes (SB, SR, ST), then SI, then AFIB, and lowest for AFL (in particular, SI recall > AFIB recall, if SI records can be obtained)."*
  - The repair showed that SB/SR/ST labels follow 60/100 bpm thresholds on the measured rate (DRA O25). The first half of that prediction is therefore close to guaranteed and tests nothing.
  - v3 keeps the ordering SI > AFIB > AFL and the SI > AFIB prediction from v0, demotes SB/SR/ST to a consistency check, and makes "beats a heart-rate-only model" the main claim.
- §3–8 written for the first time. §9–11 remain not applicable.

**Readiness check and repair (Assignment 5.4).** On 2026-11-11 I answered:
1. Main records inspected? **No.** The 399 SI records had never been opened; they were not in the release.
2. Main quantity computable from a written rule? **Yes**, once §8 was written.
3. Unit named and counted? **Yes.**
4. All DRA issues that could change the claim's meaning resolved? **No.** U1: SI missing. U9: whether SB/SR/ST labels are rate thresholds.

So I was on the **Repair branch**.

What I did and found:
- I obtained the original figshare release and paired it with part 1 by row order. The 399 missing IDs are exactly the 399 SI rows, and every part-1 signal equals the figshare signal rounded to whole µV. **U1 resolved.**
- The SI signals are complete, and I opened and checked them structurally. Two have all-zero leads.
- **U9:** SB/SR/ST agree with 60/100 bpm thresholds on VentricularRate in 7,253 of 7,283 records. This changed what the claim means, so I reframed it (above).
- The same work resolved U2, U4 and U7, and narrowed U6.
- After the repair, all four answers are yes.

Still open: why SI was removed (U1), patient independence (U5), and pre-export filtering (U8).

Next: visually inspect a sample of SI and AFL records; commit the unit list and test-ID file; write PRD v0.

v1 → v2:
- Restored sinus irregularity to the question and the prediction.
- Stated explicitly my inference that the 399 records missing from part 1 are the SI records.
- Marked the SI part of the claim as untestable on part 1 as released, conditional on obtaining those records.

v0 → v1, after the DRA:
- Dropped sinus irregularity (0 records in part 1; inferred removed from the release).
- Named the clinical location (Shaoxing, part 1).
- Adopted the data's labels (AFIB = fibrillation, AF = flutter).
- Added the one-ECG-per-patient inference.
- Removed the validation-split wording, because no validation strategy belongs at this checkpoint.
- The prediction keeps its logic: rate-defined sinus classes > AFIB > AFL.
