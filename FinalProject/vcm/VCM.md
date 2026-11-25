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

> _Not applicable at this version — the scientific question has not been stated yet._

**Source:**
- PhysioNet, *A large scale 12-lead electrocardiogram database for arrhythmia study*, v1.0.0 — https://physionet.org/content/ecg-arrhythmia/1.0.0/. Part 1 = the 10,247 Chapman-Shaoxing records (Shaoxing People's Hospital; `dra/DRA.md` §2).
- The 399 sinus-irregularity records, which part 1 lacks, come from the original 10,646-record release of the same data on figshare (collection *ChapmanECG*, 4560497). Part 1 is that release minus those 399 records, and its signals equal the figshare signals rounded to whole µV (DRA O22, O24, O30, O31).
- Part 2 (Ningbo First Hospital, 34,905 records) is sealed and has not been examined.

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
- **Each record** is one 10-s 12-lead resting ECG. The signal is the part-1 `.mat` `val` array in µV. For the SI records it is round(figshare CSV), which is exactly how part-1 signals relate to figshare (DRA O30).
- **Row order:** row *k* of the figshare `Diagnostics.xlsx` is record JS*k* (DRA O22).
- **SI is recoverable** [O]: the 399 record IDs missing from part 1 are exactly the 399 SI rows of the original release, and their signals are complete and in the same format (DRA O24, O30, O31).
- **Sinus labels are rate labels** [O]: SB / SR / ST labels follow 60 / 100 bpm thresholds on the measured ventricular rate (`VentricularRate`) in 7,253 of 7,283 records, 99.6% (DRA O25).
- **SI is not rate-defined** [O]: 376 of its 399 records lie at 60–100 bpm, overlapping SR. AFIB and AFL span the whole rate range (DRA O26).
- **One ECG = one patient** [I], from the paper's equal subject and record counts. No file carries a patient identifier (DRA U5).
- **Duplicates** [O]: 13 pairs of records are byte-identical (DRA O10, O32).
- **Zero leads** [O]: 15 records have at least one all-zero lead (DRA O9), plus 2 of the SI records (DRA O31).
- **Demographics:** rhythms differ by age and sex (e.g. AFIB patients are older).

## 2. Provisional expectation / claim

_What do you currently expect, and why do you expect it?_

> _Not applicable at this version — no claim has been stated yet._

## 3. Plausible alternative

_What is at least one different outcome that a reasonable person could expect instead?_

> _Not applicable at this version — no claim has been stated yet._

## 4. Claim boundary / stronger nonclaim

_What is the tempting stronger statement that your evidence will not support?_

> _Not applicable at this version — no claim has been stated yet._

## 5. Important unknowns

_What do you not yet know that could change how this result should be interpreted?_

Unknowns about the dataset:

- **Why PhysioNet removed the 399 SI records** (DRA U1). Their signals look structurally normal (DRA O31), but two have all-zero leads.
- **Whether each record is a different patient** (DRA U5). The 13 identical pairs (DRA O10, O32) show that at least some duplication happened.
- **How the labels were made for SI, AFIB and AFL** (DRA U9). SB/SR/ST follow the machine-measured rate; it is not known whether the others also follow a machine statement.
- **Whether the "raw" signals were filtered before export** (DRA U8).

## 6. Revision trigger

_What specific evidence or reasoning would make you change your claim?_

> _Not applicable at this version — no claim has been stated yet._

## 7. Independent commitment statement

_One sentence: why are you committing this claim state using only your own background knowledge, before consulting peers, AI, literature, or the dataset?_

> _Not applicable at this version — no claim has been stated yet._

## 8. Evidence contract / evaluation plan

_What analysis will you accept as answering the question, specified before you run it?_

> _Not applicable at this version — no claim has been stated yet._

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

> _Not applicable at this version — this is the first version for the BME4400 final project._
