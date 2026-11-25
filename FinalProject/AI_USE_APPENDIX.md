# AI-Use Appendix — Project 5

**Fill this in as you work, and commit it with your work.** It records what
your AI interactions actually *contributed*.

## What to record

This appendix is for **auditability, not transcription**. You do not need to
preserve every routine question. Record every interaction that materially
affected:

- an analytical artifact: code, checks, or results;
- a decision;
- an interpretation; or
- text you submit.

AI use is permitted for both code and written interpretation, iteratively
and across more than one session. Where AI generated or substantially
revised code or text, include the prompt(s) responsible and the context you
supplied.

**AI output is not evidence.** Claims about results or choices must rest on
what *your own* analysis produced and *you* verified. AI must not introduce
analyses you did not run or results you did not obtain. You remain
responsible for the whole project and must be able to explain, defend,
modify, and repair any material AI contribution.

## Entries

Copy the block below once per material interaction, in the order they
happened. If you used no AI assistance at all, say so here instead.

### Entry 1 — VCM v0, sections 1–2

- **AI system / model and settings (when known):** Claude Code (Claude Opus 5.5, model id `claude-opus-5-5`), VS Code extension, 2026-11-04.
- **Purpose of the interaction:** Write the pre-evidence VCM v0 for Question 2: the scientific question (§1) and the provisional expectation (§2).
- **Inputs or artifacts provided to the AI:** The Question 2 text from the project topic list (question, version, source URL, why it fits, access, limitations) and the empty `vcm/VCM.md` template. The §1–2 drafts were written before the AI fetched any dataset documentation, and no ECG record has been opened.
- **Prompt(s) used** (English generalization of the original prompts):
  1. "This is the Project 5 topic: [Question 2 text]. Record the VCM and get ready to download the data."
  2. "I added two more rhythm classes (sinus irregularity and sinus bradycardia) to §1; update the predicted result accordingly. The dataset has other diagnoses, but each is too rare, so they are not included."
  3. "Also, delete the VCM content outside sections 1 and 2; those sections will be completed after the DRA."
- **Contribution:**
  - §1: the AI copied the Question 2 and Version wording verbatim from the topic text and added the source line. I then edited the Version sentence myself to add sinus irregularity and sinus bradycardia.
  - §2: the AI first drafted a four-class expectation (AF, AFL, SR, ST) from general ECG physiology; after prompt 2 it rewrote it for six classes (SR, SB, ST, SI, AF, AFL) and added the exclusion of rare diagnoses.
  - §3–7: the AI first drafted these (alternatives, nonclaims, unknowns, revision triggers) and left §7 for me. After prompt 3 it removed all of that content, keeping each heading with "Not applicable at this version — to be completed after the Data Reality Audit". §8–12 are marked not applicable (pre-evidence).
- **Disposition:** Accepted §1 and the overall structure of §2. Rejected the AI's class ordering in §2, which ranked AF above SI: I believe SI is easier to classify than AF, because SI keeps normal P waves while AF has no correct P waves, so atrial features are harder to extract for AF. §2 was revised to rank SB/SR/ST > SI > AF > AFL, with SI recall > AF recall as the falsifiable prediction.
- **Verification:** Re-read §2 against my own expectation of each rhythm's ECG features before committing.

### Entry 2 — Dataset download preparation and hospital split

- **AI system / model and settings (when known):** Claude Code (Claude Opus 5.5, model id `claude-opus-5-5`), VS Code extension, 2026-11-04.
- **Purpose of the interaction:** Prepare a verified download of the dataset that stays outside the repository, and split the release into a downloaded part 1 and a protected part 2.
- **Inputs or artifacts provided to the AI:** This repository's README and templates; Project 4's download script and specs README (layout reference); the PhysioNet ecg-arrhythmia 1.0.0 landing page, file index and `SHA256SUMS.txt`; the PhysioNet/CinC Challenge 2021 v1.0.3 page, training-folder listings and `SHA256SUMS.txt`. No ECG record was opened or downloaded.
- **Prompt(s) used** (English generalization of the original prompts):
  1. "…and get ready to download the data." (same message as Entry 1, prompt 1)
  2. "First check the dataset website. I remember the data being split into two parts: download the first part only and keep the second part protected. Meanwhile I will revise the VCM."
  3. "It should be split by hospital."
- **Contribution:**
  - Found that the ecg-arrhythmia page names two hospitals (Shaoxing, Ningbo) but does not map records to them. The AI took the mapping from the Challenge 2021 release, which stores the same recordings in `chapman_shaoxing/` and `ningbo/` folders.
  - Wrote `scripts/build_ecg_parts_manifest.py`, which joins the two releases by record ID using only their checksum files, and generated `specs/ecg_arrhythmia_parts.csv`: part 1 = Chapman-Shaoxing, 10,247 records, JS00001–JS10646; part 2 = Ningbo, 34,905 records, JS10647–JS45551.
  - Wrote `scripts/download_ecg_arrhythmia.py` (part 1 only by default; part 2 refused without `--unseal-part2`; every file verified against a pinned checksum list) and `specs/ecg_arrhythmia_README.md`.
  - Added WFDB file types and folders to `scripts/check_evidence_boundary.py` and `.gitignore`, replaced `mne-base` with `wfdb` in `environment.yml` and `checks/check_environment.py`, and filled in the README "Source data" section.
- **Disposition:** Accepted. 
- **Verification:** Ran `--check`; confirmed the manifest builder's counts (10,247 + 34,905 = 45,152) and that all `.mat` files are identical across the two releases; `python scripts/check_evidence_boundary.py` passes.

### Entry 3 — Data Reality Audit (part 1, Chapman-Shaoxing)

- **AI system / model and settings (when known):** Claude Code (Claude Opus 5.5, model id `claude-opus-5-5`), VS Code extension, 2026-11-04.
- **Purpose of the interaction:** Inspect the downloaded part-1 records and write the DRA.
- **Inputs or artifacts provided to the AI:**
  - The downloaded part-1 files in `~/bme4191_ecg/` (10,247 `.hea` + `.mat`, `ConditionNames_SNOMED-CT.csv`, `RECORDS`, `SHA256SUMS.txt`), the `dra/DRA.md` template and `specs/ecg_arrhythmia_parts.csv`.
  - Documentation fetched by the AI: the PhysioNet ecg-arrhythmia v1.0.0 page, Zheng et al. 2020 *Sci Data* (Europe PMC full text, PMC7016169; verbatim up to Table 2) and the Challenge 2021 v1.0.3 page.
  - Part 2 (Ningbo) was not downloaded, opened or inspected.
- **Prompt(s) used** (English generalization):
  1. "The data has been downloaded. Complete the DRA and record it in the AI-use appendix."
  2. "I infer from the Zheng (Zhang) paper that one ECG corresponds to one individual patient. Record this in the DRA."
  3. "I infer that the 399 absent records are actually the SI records. Record this in the DRA."
- **Contribution:**
  - Wrote `src/dra_inspect.py` and ran it on all part-1 records; it writes `results/dra/`. The script counts only; it computes no features and fits no model.
  - Drafted all 11 sections of `dra/DRA.md` from those outputs and the documentation, tagged D/O/I/U.
  - Corrected one of its own findings before drafting: a reported checksum mismatch (JS10055, aVR) was a header writing −32768 as 32768, not a signal error.
  - Main findings:
    - Sinus irregularity (code 427393009) does not occur in part 1. The paper lists 399 such ECGs, and 399 record IDs are absent from the range.
    - Four Dx codes are missing from the condition table.
    - 13 record pairs have byte-identical signals and metadata.
    - 15 records have all-zero chest leads.
    - One header (JS01052) is malformed.
    - The documented amplitude scale (4.88 per bit) conflicts with the header gain (1000/mV).
    - The maximum age is 89, while the paper reports 98.
- **Disposition:** I added my own inference: one ECG = one patient, from the paper's equal subject and record counts. It is recorded as [I] in DRA §5, §8 and §10, with U5 and U6 kept as the residual uncertainty. I also added my inference that the 399 absent record IDs are the 399 SI records. It is recorded as [I] in DRA §6, §8 item 1 and §10, supported by every other rhythm count matching the paper, with U1 kept for direct confirmation. _Rest to fill in._
- **Verification:** Re-ran `src/dra_inspect.py` and matched the CSV hashes in DRA §11; opened JS01052.hea and one zero-lead record myself; checked the D quotes against the PhysioNet page and the paper.

### Entry 4 — VCM v1 (post-DRA revision of §1–2)

- **AI system / model:** Claude Code (Claude Opus 5.5), 2026-11-04.
- **Prompt** (English generalization): "Modify the v1 VCM. Include the inferences and omit the split validation."
- **Contribution:** Revised `vcm/VCM_v1.md` §1–2 from the DRA findings:
  - narrowed the question to five rhythms at Shaoxing (SI dropped);
  - added my two inferences (one ECG per patient; the 399 SI records were removed);
  - removed the validation-split wording;
  - filled in §12.
- **Disposition / verification:** Accepted.

### Entry 5 — VCM v2

- **AI system / model:** Claude Code (Claude Opus 5.5), 2026-11-04.
- **Prompt** (English generalization): "Still include SI in VCM v2. Say clearly that I infer the 399 records to be SI."
- **Contribution:** Created `vcm/VCM_v2.md` from v1:
  - restored SI to §1–2, with my inference stated explicitly;
  - marked SI as untestable on part 1 as released (0 SI records);
  - added a v1 → v2 note in §12.
- **Disposition / verification:** Accepted.
### Entry 6 — Moving the local work into the official repository

- **AI system / model:** Claude Code (Claude Opus 5.5), VS Code extension, 2026-11-11.
- **Purpose:** Staff released the official `p5-jinzemao78` repository on 2026-11-11. Entries 1–5 were done in a local folder (`Project5`) built from the Project 4 layout. This interaction moved that work into the official layout.
- **Inputs provided to the AI:** Both folders: the official repository (templates only) and the local `Project5` folder (all files listed in Entries 1–5). No raw recordings.
- **Prompts** (English generalization): "Compare and evaluate the differences between the git repo and the local Project 5 folder." Then: "Move all the documents into the repo, putting everything into the corresponding folders."
- **Contribution:** Copied every file into the official layout and updated paths:
  - `vcm/VCM_v0.md`, `VCM_v1.md`, `VCM_v2.md` → one `vcm/VCM.md` (the official template keeps one file name, with versions in Git history);
  - `scripts/download_ecg_arrhythmia.py`, `scripts/build_ecg_parts_manifest.py` → `src/`;
  - `scripts/check_evidence_boundary.py` → `checks/`;
  - `specs/ecg_arrhythmia_parts.csv`, `specs/ecg_arrhythmia_README.md` → `results/source_data/`;
  - updated the matching paths in the code, DRA, PRD, checkpoint report and source-data README. The official `README.md` was left unchanged at my request; the local README's Source data, Evidence boundary and Tags sections were not carried over;
  - kept the local `environment.yml`, `checks/check_environment.py` (both add `wfdb`), `.gitignore` (raw-recording patterns) and `.github/workflows/gate_tags.yml`.
  - Entries 1–5 above are unchanged and keep the paths in use at the time. The mapping above translates them.
- **Disposition:** Accepted. I chose to keep the official `README.md` unchanged and not to carry over the local README's Source data, Evidence boundary and Tags sections. The three VCM versions became one `vcm/VCM.md`, with versions held in Git history as the official template requires.
- **Verification:** No file contents changed except paths. The scripts parse, `src/download_ecg_arrhythmia.py --help` runs and finds the manifest at its new path, and `python checks/check_evidence_boundary.py` passes. My own checks (2026-11-12): `diff` shows VCM v0, v1 and v2 in commits 998a28f, 147f0b3 and 1eb4005 are identical to `Project5/vcm/VCM_v0.md`, `VCM_v1.md` and `VCM_v2.md`; `cmp` shows `results/source_data/ecg_arrhythmia_parts.csv` is byte-identical to the local `specs/` copy; `diff` of the DRA and `src/dra_inspect.py` against the local copies shows only path changes; the evidence-boundary check passes.


### Entry 7 — Assignment 5.4 repair: U1 and U9 checked against the original figshare release

- **AI system / model:** Claude Code (Claude Opus 5.5, model id `claude-opus-5-5`), VS Code extension, 2026-11-11 to 2026-11-12.
- **Purpose:** Assignment 5.4 asks for the four readiness questions. The AI judged that "all DRA issues that could change the claim's meaning are resolved" was **no** (U1: SI missing; U9: SB/SR/ST labels possibly rate thresholds), so the project is on the Repair branch. This interaction carried out the repair for U1 and U9.
- **Inputs provided to the AI:** The Assignment 5.4 text, `vcm/VCM.md`, `dra/DRA.md`, `results/dra/record_table_part1.csv`, and the part-1 `.mat` files in `~/bme4191_ecg/`. The AI found and downloaded the figshare ChapmanECG collection (id 4560497) itself: the four metadata spreadsheets and `ECGData.zip`, all MD5-checked against figshare's published values, stored outside the repository. Part 2 (Ningbo) was not touched.
- **Prompts** (English generalization):
  1. "[Assignment 5.4 text] This is the assignment due Friday. What should we do? Answer me in Chinese."
  2. "OK, let's check U1 and U9 first. Help me do that."
  3. "1. Follow your recommendations. 2. Yes, tell me how to reclaim. 3. Yes, update the DRA."
  4. "OK, change the VCM. Tell me how to verify Diagnostics.xlsx."
- **Contribution:**
  - Wrote `src/figshare_check.py` (standard library only): pairs JS id *k* with `Diagnostics.xlsx` row *k*, explains every disagreement, tabulates VentricularRate by rhythm label. Writes `results/figshare_check/summary.json`, `id_alignment.csv`, `rate_by_rhythm.csv`.
  - Wrote `src/figshare_signal_check.py`: compares every paired figshare CSV with its part-1 `.mat`, and checks the 399 SA signals. Writes `signal_match.csv`, `signal_summary.json`. No features, no model.
  - Main findings (DRA O21–O32): the 399 absent ids are exactly the 399 SA rows; part-1 `.mat` = figshare signal rounded to whole µV for all 10,247 records; SA signals complete; ages ≥ 90 capped at 89; codes 251166008 / 17366009 = AVNRT / SAAWR; SB/SR/ST agree with 60/100 bpm thresholds on VentricularRate in 7,253 / 7,283 records; the 13 identical pairs carry two different MUSE file names.
  - Updated `dra/DRA.md`: §1, §2 (figshare acquisition and MD5s), §3 (D17–D19), §4 (O21–O32), §5, §6, §7, §8 (repair notes under items 1, 2, 5, 6, 7), §9 (U1, U2, U4, U7 resolved; U6, U9 narrowed; U13 added), §10 (data statement v1; v0 kept), §11.
  - Proposed how to restate the claim: SI back in from figshare; a heart-rate-only model as comparator, because a threshold rule cannot output SI/AFIB/AFL; SB/SR/ST demoted to a consistency check. After prompt 4 ("OK, change the VCM"), wrote VCM v3: §1–2 revised (v2 wording quoted in §12), §3–8 written, §9–11 marked not applicable, §12 change note and repair note. The unit counts in §8.1 (9,907 → 9,902 → 9,888) were computed from `results/figshare_check/id_alignment.csv`. The split seed (4191), test fraction (0.2), bootstrap settings, the 5-bpm / 95% heart-rate check and the support/weaken/refute thresholds were proposed by the AI.
- **Disposition:** Accepted the repair findings, the DRA update and VCM v3. I accepted the AI-proposed §8 conditions to support, weaken or refute the claim as written. I edited §7 myself.
- **Verification (2026-11-12, by me; all passed):**
  - MD5 of `Diagnostics.xlsx` matches figshare's published value.
  - In a copy of the spreadsheet: 10,646 rows; 399 SA, 223 of them male; counts match the paper's Table 2.
  - Row *k* ↔ JS*k* spot checks: JS00001 against its `.hea`; JS00003 and JS00028 are SA and have no part-1 file; JS00081 is 90 in figshare and 89 in its header.
  - U9 counts with COUNTIFS: SB < 60 bpm 3,868; SR 60–100 bpm 1,821; ST > 100 bpm 1,564.
  - Re-ran `src/figshare_check.py`; `summary.json` matches the SHA-256 in DRA §11.
