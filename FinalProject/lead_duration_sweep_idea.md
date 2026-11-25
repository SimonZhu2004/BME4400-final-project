# Project idea: how few leads and how few seconds are enough?

Working draft of the plan. Not part of the VCM.

---

## 1. Idea in one paragraph

Instead of building one more 12-lead, 10-s arrhythmia classifier, sweep over **number of leads** and **recording duration** to find the smallest ECG that still classifies the rhythms well. Use the Chapman-Shaoxing part of PhysioNet ecg-arrhythmia v1.0.0, plus the 399 sinus-irregularity records recovered from figshare. Main approach: extract features from the raw ECG, then train classic models (logistic regression, random forest / gradient boosting, ANN). Optional: a model that works on the raw signal (1D CNN or MiniRocket) as an upper bound.

**Question:** For six rhythms (SR, SB, ST, SI, AFIB, AFL), what is the smallest combination of leads and duration whose classification is close to that of the full 12-lead, 10-s ECG, and does the answer differ by rhythm?

**Why it's interesting:** wearables and monitors record 1–3 leads, often in short strips. "Will two do?" (PhysioNet Challenge 2021) looked at a few fixed lead sets at full length. Sweeping *duration* together with *leads*, and asking *which rhythm needs what*, is less explored.

---

## 2. Two things that make or break the result

### 2.1 "Accurate" must not be driven by SB / SR / ST

- In this dataset, SB/SR/ST labels follow 60 / 100 bpm thresholds on the measured ventricular rate in 99.6% of records.
- Any single lead gives heart rate in a few seconds, so overall accuracy will say "1 lead, short window is enough". That answer only re-measures heart rate.
- So:
  - **Main measure:** macro recall over **SI, AFIB, AFL**.
  - Always report **per-class recall for all six** (heatmaps).
  - At every duration, also fit a **heart-rate-only model (M_HR)**. The interesting number is the gain over M_HR.

### 2.2 12 leads are really 8

- Four limb leads are computed from I and II:
  - III = II − I
  - aVR = −(I + II) / 2
  - aVL = I − II / 2
  - aVF = II − I / 2
- So "6 limb leads" carries the same information as "I + II". Search over the **8 independent leads: I, II, V1–V6**.
- Quick check to run first: confirm these identities hold in the stored signals (up to rounding).

---

## 3. Design

### 3.1 Data

- Units: the cleaned list of 9,888 ECGs (six rhythms; duplicates and all-zero-lead records removed).
- Split: same stratified 80/20 split (test ≈ 1,978; SI ≈ 79, AFL ≈ 88 in test).
- All choices are made on the development set with cross-validation. The test set is used once at the end.

### 3.2 Lead configurations

**Named sets (each has a clinical reason):**

| Set | Leads | Motivation |
|---|---|---|
| L1 | I | smartwatch-like |
| L2 | II | bedside / Holter monitor |
| L3 | V1 | best lead for atrial activity |
| L4 | II + V1 | rhythm strip + atrial lead |
| L5 | I + II | = all 6 limb leads |
| L6 | I + II + V1 | |
| L7 | I + II + V2 | Challenge 2021 three-lead set |
| L8 | I, II, V1–V6 | full information (reference) |

**Data-driven:** greedy forward selection over the 8 independent leads at each duration (development set only; ~36 fits per duration). It shows which lead gets added first, second, and so on.

### 3.3 Durations

- Grid: **10, 7.5, 5, 2.5 s**.
- Below ~2.5 s, slow rhythms (SB at ~47 bpm) may have only 1–2 R peaks, so RR features are undefined. Rule: if fewer than 3 R peaks, RR features are set to missing.
- **Training:** random crops of length T (also adds samples for small classes).
- **Testing:** one fixed crop (the middle T seconds). Don't average several crops, or more than T seconds is being used.
- All six classes are whole-strip rhythms, so a crop keeps its label (unlike PVC/APB).

### 3.4 Grid size

8 named lead sets × 4 durations = **32 configurations**, plus greedy selection.

---

## 4. Features (extracted from the raw ECG)

Computed **once per lead per crop**, then any configuration is just a choice of columns.

| Group | Examples | Mainly for |
|---|---|---|
| Rate | heart rate = 60 / median RR | SB, SR, ST |
| RR variability | SDNN, RMSSD, pNN50, RR range, coefficient of variation, successive-difference irregularity | SI, AFIB |
| P wave | P detected (fraction of beats), P amplitude, PR interval and its variability | SI vs AFIB, AFL |
| Atrial spectrum | power 4–9 Hz, dominant frequency, peak sharpness near 4–6 Hz (~300/min flutter) in II / V1 | AFIB vs AFL |
| QRS (minor) | QRS width, amplitude | general |

- Tools: NeuroKit2 (R peaks, P-wave delineation), SciPy (Welch spectrum).
- R peaks for heart rate come from the same detector in every model.
- **Feature selection** (mutual information, L1, or importances) must be done **inside each CV fold**, never on the whole development set.
- Age and sex are not used.

---

## 5. Models

| Model | Role |
|---|---|
| M_HR (heart rate only) | floor at every duration |
| Logistic regression (multinomial, standardized, balanced weights) | interpretable baseline |
| Random forest / HistGradientBoosting | **main model** (handles missing P-wave features natively) |
| MLP (ANN) on the features | optional; rarely beats boosting on tabular data |
| MiniRocket (sktime) on raw signal | optional, cheap raw-signal baseline (CPU, minutes) |
| 1D CNN on raw signal | optional upper bound |

- Use **one main model** for the headline heatmap. Others are secondary, to avoid too many comparisons.
- Class imbalance: `class_weight='balanced'`; report macro recall, not accuracy.

### 5.1 Raw-signal models: feasibility notes

- Size: 9,888 records × 8 leads at 250 Hz is < 1 GB in float32.
- Small 1D ResNet (a few hundred thousand parameters): minutes per run on a GPU (Colab / campus), tens of minutes on a laptop CPU.
- Use one train/validation split inside the development set, not 5-fold.
- For the sweep, train **one** CNN with random lead masking and random crop length, then evaluate it on every configuration. (This answers "one model that tolerates missing leads", which is slightly different from "a model fitted to each configuration"; state this.)
- Use: if the CNN clearly beats the features at some configuration, the features are missing information there.
- Expect SI to be the CNN's weakest class (~318 development records).
- LSTM / transformer: skip; slower and usually no better on 10-s strips.

---

## 6. Expectations (to check against results)

- **AFIB:** stays good down to 1 lead and short windows. Gross RR irregularity is visible in any lead.
- **SI:** limited by **duration**, not leads. It needs enough RR intervals to show variability; expect it to collapse first as T shrinks and to be confused with SR.
- **AFL:** limited by **which leads**, not duration. Needs a lead showing flutter waves (II or V1); sets without them (e.g. I alone) should confuse AFL with ST or AFIB.
- **SB / SR / ST:** near-perfect everywhere; consistency check only.

Alternative worth keeping in mind: SI may already be poor at 10 s (only ~11 beats), in which case duration won't matter much for it.

---

## 7. How "smallest" is decided

- **Reference:** L8, 10 s.
- **Margin δ:** a configuration is "enough" if its macro recall over SI/AFIB/AFL is within **δ = 0.05** of the reference (fix δ before running).
- **Selection:** on development-set CV, pick the smallest configuration that meets the margin (fewest leads first, then shortest duration). Also report the frontier: for each duration, the fewest leads that meet the margin.
- **Confirmation:** evaluate on the test set once; paired, class-stratified bootstrap (2,000 resamples) for the difference vs the reference.
- **Power:** with ~79 SI and ~88 AFL test records, intervals will be wide. "Inconclusive" is a possible and acceptable outcome; say so in advance.

---

## 8. Outputs

1. Heatmap: macro recall (SI/AFIB/AFL) over lead set × duration, main model.
2. Same heatmap as **gain over M_HR**.
3. Per-class heatmaps (six panels).
4. Greedy lead-selection curves per duration.
5. Confusion matrices at the reference and at the chosen minimal configuration.
6. (Optional) Feature model vs CNN/MiniRocket at selected configurations.

---

## 9. Pitfalls checklist

- [ ] Overall accuracy dominated by SB/SR/ST → use macro recall over SI/AFIB/AFL.
- [ ] Redundant limb leads → search over 8 leads; verify the identities.
- [ ] Feature selection or tuning outside CV folds → leakage.
- [ ] Choosing the minimal configuration on the test set → choose on development, confirm once.
- [ ] Too few R peaks at short durations → explicit missing-value rule.
- [ ] Averaging crops at test time → one fixed crop.
- [ ] Too many models × configurations → one main model.
- [ ] Zero-lead and duplicate records → already excluded in the unit list.

---

## 10. Rough timeline

| Step | Content |
|---|---|
| 1 | Verify limb-lead identities; build crop + feature extraction per lead |
| 2 | M_HR + LR + boosting over the 32 configurations (development CV) |
| 3 | Greedy lead selection; pick minimal configuration with the δ rule |
| 4 | (Optional) MiniRocket / masked CNN |
| 5 | Single test-set evaluation, bootstrap, figures |
| 6 | Write-up |
