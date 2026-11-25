# BME4400 Final Project — Dataset description

## Source

- PhysioNet, *A large scale 12-lead electrocardiogram database for arrhythmia
  study*, v1.0.0 — https://physionet.org/content/ecg-arrhythmia/1.0.0/.
  Part 1 = the 10,247 Chapman-Shaoxing records (Shaoxing People's Hospital;
  `dra/DRA.md` §2).
- The 399 sinus-irregularity records, which part 1 lacks, come from the
  original 10,646-record release of the same data on figshare (collection
  *ChapmanECG*, 4560497). Part 1 is that release minus those 399 records, and
  its signals equal the figshare signals rounded to whole µV (DRA O22, O24,
  O30, O31).
- Part 2 (Ningbo First Hospital, 34,905 records) is sealed and has not been
  examined.

## Rhythm classes

In the data's own labels the six rhythms of interest are SR (sinus rhythm),
SB (sinus bradycardia), ST (sinus tachycardia), SA (sinus irregularity),
AFIB (atrial fibrillation) and AF (atrial flutter). Below, SI = sinus
irregularity and AFL = atrial flutter.

| Rhythm | Records |
|---|---|
| SB | 3,889 |
| SR | 1,826 |
| AFIB | 1,780 |
| ST | 1,568 |
| AFL | 445 |
| SI | 399 |

Counts come from the figshare `Diagnostics.xlsx` and equal the 2020 paper's
Table 2. Rhythm is effectively a single label per record.

Other rhythms in the data: SVT (587), AT (121), AVNRT (16), AVRT (8) and
SAAWR (7).

## What is known about the records

- **Each record** is one 10-s 12-lead resting ECG. The signal is the part-1
  `.mat` `val` array in µV. For the SI records it is round(figshare CSV),
  which is exactly how part-1 signals relate to figshare (DRA O30).
- **Row order:** row *k* of the figshare `Diagnostics.xlsx` is record JS*k*
  (DRA O22).
- **SI is recoverable:** the 399 record IDs missing from part 1 are exactly
  the 399 SI rows of the original release, and their signals are complete and
  in the same format (DRA O24, O30, O31).
- **Sinus labels are rate labels:** SB / SR / ST labels follow 60 / 100 bpm
  thresholds on the measured ventricular rate (`VentricularRate`) in 7,253 of
  7,283 records, 99.6% (DRA O25).
- **SI is not rate-defined:** 376 of its 399 records lie at 60–100 bpm,
  overlapping SR. AFIB and AFL span the whole rate range (DRA O26).
- **One ECG = one patient** (inferred from the paper's equal subject and
  record counts). No file carries a patient identifier (DRA U5).
- **Duplicates:** 13 pairs of records are byte-identical (DRA O10, O32).
- **Zero leads:** 15 records have at least one all-zero lead (DRA O9), plus 2
  of the SI records (DRA O31).
- **Demographics:** rhythms differ by age and sex (e.g. AFIB patients are
  older).

## Open questions about the data

- **Why PhysioNet removed the 399 SI records** (DRA U1). Their signals look
  structurally normal (DRA O31), but two have all-zero leads.
- **Whether each record is a different patient** (DRA U5). The 13 identical
  pairs show that at least some duplication happened.
- **How the labels were made for SI, AFIB and AFL** (DRA U9). SB/SR/ST follow
  the machine-measured rate; it is not known whether the others also follow a
  machine statement.
- **Whether the "raw" signals were filtered before export** (DRA U8).
