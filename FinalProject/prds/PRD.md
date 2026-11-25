# Project 5 PRD: <analysis name>

**This is your PRD: a scaffold, not a finished specification.** Write it
before generating or running any final code, and commit it first. The Canvas
text for the assignment governs what this PRD must achieve; the headings below
are prompts to make sure it is complete. The test of a good PRD: an AI that has
never seen your conversation, given only this document and this repository,
rebuilds your analysis and gets the same numbers.

Keep it compact. One PRD per analysis (notebook or script), committed before
you run it. If the analysis changes, amend it in a new commit.

Do not delete a section that does not apply. Keep the heading and write:

> _Not applicable — [reason]._

---

## 1. Purpose and evidence need

_The scientific question (wording from the assignment text / VCM §1), what this
analysis must establish, and what kind of evidence it produces (development,
selection, confirmation). Say what it does **not** establish._

## 2. Inputs

_Every file the analysis may read: path (relative to the repository root or the
named data folder outside it), SHA-256, dimensions (units × records), and where
it came from. State that no other file may be read._

## 3. What must remain fixed

_Data, representation/features, target coding, prediction unit, generalization
unit, preprocessing, metric, aggregation, baseline, random seeds, and the
evidence boundary. Anything not listed here is free to change only if the PRD
is amended first._

## 4. Replication of earlier work

_Numbers from earlier projects/assignments this analysis must reproduce before
any new result is interpreted (with tolerance), and what to do if they do not
match (stop and diagnose)._

## 5. Exact procedure

_The computation, step by step: data loading, event/record definition,
preprocessing, features, model(s) with every setting written out (library,
class, arguments, version). No defaults left implicit._

## 6. Validation procedure

_How data are split (grouping variable, number of folds, fold assignment and
seed), and confirmation that every method uses identical splits._

## 7. Primary metric and aggregation

_The metric, the unit it is computed on, how it is aggregated (and weighted),
and which per-unit values are preserved, not only the mean._

## 8. Baseline and controls

_The baseline (chance, majority class, earlier model) and the negative/positive
controls, run through the same code path as the real analysis, with pass
criteria._

## 9. Decision rule

_Fixed before any result is seen: what counts as better than the baseline, how a
winner is chosen, and what happens if there is no clear winner._

## 10. Required outputs

_Each file the analysis writes (path under `results/`, format, columns), plus
figures and tables for the report._

## 11. Library versions recorded

_Python and package versions to record alongside the outputs._

## 12. Verification and acceptance criteria

_Checks (in `tests/` or inline) that must pass before results are accepted:
input hashes, shapes, replication match, control pass, no leakage across
splits, reproducibility on rerun._

## 13. Failure handling

_What to do when a check fails, a fit does not converge, or a file is
missing. Never silently continue._

## 14. Prohibited changes

_Changes that are not allowed without amending this PRD first (e.g., tuning on
held-out data, new features, different splits, dropping participants)._

## 15. Protected-evidence boundary

_What data stay outside this repository and outside every AI-accessible
surface, and how that is checked (`python checks/check_evidence_boundary.py`)._
