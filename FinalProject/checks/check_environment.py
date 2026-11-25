"""BME4400 final project environment self-check.  Run from the repository root:
    python checks/check_environment.py

Checks that the active environment matches the exact versions pinned in
environment.yml, so every teammate gets the same numerical results.
Operational readiness only; reports nothing about any dataset's contents.
With --ci (lighter CI install), a missing package or a version difference is a
warning instead of a failure."""
from __future__ import annotations
import os, re, shutil, sys
from importlib import import_module
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXPECTED_ENV = "bme4400-final"
# conda package name in environment.yml -> import name
IMPORT_NAME = {"scikit-learn": "sklearn", "pytorch": "torch"}
SKIP = {"python", "ipykernel"}  # python is checked separately; ipykernel is only for notebooks
failures = 0


def report(ok, label, detail="", warn=False):
    global failures
    tag = "PASS" if ok else ("WARN" if warn else "FAIL")
    if not ok and not warn: failures += 1
    print(f"[{tag}] {label}" + (f": {detail}" if detail else ""))


def pins() -> dict[str, str]:
    """name -> version from the '- name=version' lines of environment.yml."""
    text = (REPO_ROOT / "environment.yml").read_text()
    return {m.group(1): m.group(2) for m in re.finditer(r"^\s*-\s*([A-Za-z0-9_.-]+)=([0-9][^\s#]*)", text, re.M)}


def main() -> int:
    ci = "--ci" in sys.argv
    pinned = pins()
    v = sys.version_info
    got_py = f"{v.major}.{v.minor}.{v.micro}"
    report(got_py == pinned.get("python"), "Python version", f"{got_py} (pinned {pinned.get('python')}) at {sys.executable}", warn=ci)
    env = os.environ.get("CONDA_DEFAULT_ENV", "")
    report(env == EXPECTED_ENV or ci, "Active conda environment", env or "(none detected)", warn=True)
    for pkg, want in pinned.items():
        if pkg in SKIP:
            continue
        name = IMPORT_NAME.get(pkg, pkg)
        try:
            mod = import_module(name)
        except Exception as exc:
            report(False, f"Import {name}", repr(exc), warn=ci); continue
        have = getattr(mod, "__version__", "?").split("+")[0]
        report(have == want, f"{pkg} version", f"{have} (pinned {want})", warn=ci)
    report(shutil.which("git") is not None, "Git available", shutil.which("git") or "not found")
    report(Path.cwd().resolve() == REPO_ROOT, "Run from repository root", str(Path.cwd()), warn=True)
    print()
    if failures:
        print(f"{failures} check(s) FAILED — recreate the environment from environment.yml."); return 1
    print("Required checks passed."); return 0


if __name__ == "__main__":
    sys.exit(main())
