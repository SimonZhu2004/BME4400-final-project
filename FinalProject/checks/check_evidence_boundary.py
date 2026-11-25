"""BME 4191 Project 5 evidence-boundary check.  Run from the repository root:
    python checks/check_evidence_boundary.py

Scans the whole repository directory, INCLUDING files Git ignores, for raw
recordings that must never sit inside this project tree:

  * raw recording files: *.edf, *.event (including *.edf.event), *.fif, *.fif.gz,
    and WFDB/ECG files: *.hea, *.mat, *.dat
  * folders that hold downloaded recordings: raw/, mne_data/, MNE-eegbci-data/,
    eegmmidb/, physionet/, bme4191_eeg/, bme4191_ecg/, ecg-arrhythmia/, WFDBRecords/
  * folders named sealed/ or holdout/

Teaching point: .gitignore is not an evidence boundary. Whatever an AI tool or
coding agent can read is inside your evidence boundary, including ignored
files. This script is a guardrail, not proof of isolation."""
from __future__ import annotations
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BAD_SUFFIXES = {".edf", ".event", ".fif", ".hea", ".mat", ".dat"}
BAD_DIR_NAMES = {"raw", "mne_data", "mne-eegbci-data", "eegmmidb", "physionet", "bme4191_eeg", "bme4191_ecg", "ecg-arrhythmia", "wfdbrecords", "sealed", "holdout"}
SKIP_DIRS = {".git", ".venv", "site-packages"}  # installed packages ship their own example files


def main() -> int:
    flagged: list[str] = []
    for p in sorted(REPO_ROOT.rglob("*")):
        rel = p.relative_to(REPO_ROOT)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        name = p.name.lower()
        if p.is_dir():
            if name in BAD_DIR_NAMES:
                flagged.append(f"{rel}/  (folder name suggests raw or sealed recordings)")
            continue
        if p.suffix.lower() in BAD_SUFFIXES or name.endswith(".fif.gz"):
            flagged.append(f"{rel}  (raw recording file type)")
    if flagged:
        print("FAIL — the following must not be inside this repository directory (Git-ignored or not):")
        for f in flagged:
            print(f"  {f}")
        print("\nMove them outside this folder. .gitignore does not hide a file from tools that can read this folder.")
        return 1
    print("PASS — no raw recordings found under", REPO_ROOT)
    print("Remember: this is a guardrail, not proof of isolation. Keep course data outside this folder, in the")
    print("directories the assignment names, and give AI tools and coding agents only the folders they need.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
