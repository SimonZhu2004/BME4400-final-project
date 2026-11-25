# BME 4191 — Project 5

Your personal repository for Project 5.

**The assignment text in Canvas is the authority for what to do and when. If this file disagrees with it, the assignment text wins.**

## Layout

Keep to this layout; staff tools and graders look in these places.

```text
README.md                    this file
AI_USE_APPENDIX.md           your record of material AI contributions (the file explains what to record)
vcm/VCM.md                   your Versioned Claim Memo: section headings only; you fill it in
dra/DRA.md                   your Data Reality Audit: section headings only
prds/                        your PRD(s), in whatever form you choose
src/                         all your code: .py modules and scripts (and notebooks, if you use any)
tests/                       your verification checks
results/                     outputs you commit as evidence: tables, figures, fitted model files
report/                      your report
drafts/                      scratch space, ignored by Git
checks/check_environment.py  environment self-check
environment.yml              the bme4191-p5 conda environment
```

- Run your code from the repository root, with paths relative to it.
- Your dataset stays outside this repository unless the assignment text says otherwise.
- File names inside these folders are yours, except where the assignment text
  names one.
- If you use a coding agent, tell it to follow this layout; it can read this
  file.

## Clone

```text
git clone https://github.com/BME4191/p5-<your-username>.git
cd p5-<your-username>
```

(Git/SSO trouble? See `GitHub_Access_Fix.md` from Project 1 on Canvas.)

## Environment

```text
conda env create -f environment.yml
conda activate bme4191-p5
python checks/check_environment.py
```

In VS Code: **Python: Select Interpreter** → `bme4191-p5`.

## Commit, push, submit

Commit and push your work as you go. To submit, as in Project 4:

```text
git push
git log -1 --format=%H        # paste this SHA into Canvas
```

(In VS Code: Source Control → message → ✓ Commit → ↻ Sync Changes; the SHA
is in the Timeline view or on GitHub.)

## Getting updates

If staff release material to this repository, commit your work first, then
`git pull`.
