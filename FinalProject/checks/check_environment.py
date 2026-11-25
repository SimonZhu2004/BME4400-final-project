"""BME 4191 Project 5 environment self-check.  Run from the repository root:
    python checks/check_environment.py
Operational readiness only; reports nothing about any dataset's contents."""
from __future__ import annotations
import os, shutil, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REQUIRED = ["numpy", "pandas", "matplotlib", "scipy", "sklearn", "statsmodels", "wfdb"]
CI_WARN_ONLY = {"wfdb", "scipy"}  # CI installs a lighter set; a missing one is a warning there, not a failure
EXPECTED_ENV = "bme4191-p5"
failures = 0

def report(ok, label, detail="", warn=False):
    global failures
    tag = "PASS" if ok else ("WARN" if warn else "FAIL")
    if not ok and not warn: failures += 1
    print(f"[{tag}] {label}" + (f": {detail}" if detail else ""))

def main() -> int:
    ci = "--ci" in sys.argv
    v = sys.version_info
    report(v >= (3, 13), "Python version", f"{v.major}.{v.minor}.{v.micro} at {sys.executable}", warn=ci)
    env = os.environ.get("CONDA_DEFAULT_ENV", "")
    report(env == EXPECTED_ENV or ci, "Active conda environment", env or "(none detected)", warn=True)
    for pkg in REQUIRED:
        try: __import__(pkg); report(True, f"Import {pkg}")
        except Exception as exc: report(False, f"Import {pkg}", repr(exc), warn=(ci and pkg in CI_WARN_ONLY))
    report(shutil.which("git") is not None, "Git available", shutil.which("git") or "not found")
    report(Path.cwd().resolve() == REPO_ROOT, "Run from repository root", str(Path.cwd()), warn=True)
    print()
    if failures:
        print(f"{failures} check(s) FAILED — record this and use the course support route."); return 1
    print("Required checks passed."); return 0

if __name__ == "__main__":
    sys.exit(main())
