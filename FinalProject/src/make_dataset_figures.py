"""Presentation figures describing the Shaoxing data and the window design.

    python src/make_dataset_figures.py              # writes report/figures/*.png
    python src/make_dataset_figures.py --data-root ~/bme4191_ecg

Uses only: the committed split (results/splits/), the committed development
feature tables (meta_n_rpeaks), figshare Diagnostics.xlsx metadata already
audited in the DRA (ventricular rate, age, sex), and the raw signals of six
DEVELOPMENT records for the example strips.  No test-set signal or feature is
read, and nothing is fitted.  Every figure is 16:9, 2400 x 1350 px.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.lines  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402
from scipy import signal as sps  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ecg_io  # noqa: E402

REPO = ecg_io.REPO
FS = 500
WINDOWS = [10, 8, 6, 4, 2]                  # s, first T seconds (PRD §3)
W, H, DPI = 12, 6.75, 200

INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS, BG = "#e1e0d9", "#c3c2b7", "#ffffff"
BLUE, ORANGE, SINUS_GRAY = "#2a78d6", "#eb6834", "#a9a79f"

MAIN = ["SI", "AFIB", "AFL"]                # R3 classes (VCM §2)
NAMES = {"SR": "Sinus rhythm", "SB": "Sinus bradycardia", "ST": "Sinus tachycardia",
         "SI": "Sinus irregularity", "AFIB": "Atrial fibrillation", "AFL": "Atrial flutter"}
ORDER = ["SB", "SR", "ST", "SI", "AFIB", "AFL"]
# development-set examples, chosen by eye for clean lead-II signal
EXAMPLES = {"SR": "JS02831", "SB": "JS09894", "ST": "JS01377",
            "SI": "JS03966", "AFIB": "JS00589", "AFL": "JS02138"}

plt.rcParams.update({
    "font.family": ["Segoe UI", "Helvetica Neue", "Arial", "DejaVu Sans"], "font.size": 12,
    "text.color": INK, "axes.labelcolor": INK2, "xtick.color": MUTED, "ytick.color": INK2,
    "axes.edgecolor": AXIS, "axes.linewidth": 0.8, "axes.facecolor": BG,
    "figure.facecolor": BG, "savefig.facecolor": BG,
    "axes.spines.top": False, "axes.spines.right": False,
    "xtick.labelsize": 11, "ytick.labelsize": 12,
})
SOS = sps.butter(3, [0.5, 40.0], btype="band", fs=FS, output="sos")   # display only


def color_of(c: str) -> str:
    return BLUE if c in MAIN else SINUS_GRAY


def title(fig, text: str, sub: str | None = None) -> None:
    fig.text(0.04, 0.95, text, fontsize=19, fontweight="bold", va="top")
    if sub:
        fig.text(0.04, 0.885, sub, fontsize=12.5, color=INK2, va="top")


def note(fig, text: str) -> None:
    fig.text(0.04, 0.03, text, fontsize=9.5, color=MUTED, va="bottom")


def swatch(fig, x, y, col, w=0.009, h=0.018):
    fig.patches.append(FancyBboxPatch((x, y - h / 2), w, h, boxstyle="round,pad=0,rounding_size=0.002",
                                      transform=fig.transFigure, fc=col, ec="none"))


def tidy_rows(ax, n):
    ax.set_yticks(range(n), [f"{NAMES[c]} ({c})" for c in ORDER])
    ax.set_ylim(n - 0.5, -0.8)
    ax.xaxis.grid(True, color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)


def ecg_axes(ax, t0, t1, ylim):
    ax.set_xlim(t0, t1)
    ax.set_ylim(*ylim)
    for s in np.arange(np.ceil(t0 / 0.2) * 0.2, t1 + 1e-9, 0.2):
        ax.axvline(s, color=GRID, lw=0.9 if abs(s - round(s)) < 1e-6 else 0.5, zorder=0)
    for v in np.arange(np.ceil(ylim[0] * 2) / 2, ylim[1] + 1e-9, 0.5):
        ax.axhline(v, color=GRID, lw=0.5, zorder=0)
    ax.set_yticks([])
    for sp in ("left", "bottom"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(axis="x", length=0)


class Data:
    def __init__(self, data_root: Path):
        self.root = data_root
        sp = REPO / "results" / "splits"
        self.summary = json.loads((sp / "split_summary.json").read_text())
        self.units = pd.read_csv(sp / "shaoxing_units.csv")
        self.test = set(pd.read_csv(sp / "shaoxing_test_ids.csv").record)
        diag = pd.DataFrame(ecg_io.read_diagnostics(data_root))
        diag["record"] = [f"JS{k:05d}" for k in range(1, len(diag) + 1)]
        diag = diag.set_index("record")
        u = self.units.set_index("record")
        for col in ("FileName", "VentricularRate", "PatientAge", "Gender"):
            u[col] = diag.loc[u.index, col]
        u["VentricularRate"] = u.VentricularRate.astype(float)
        u["PatientAge"] = u.PatientAge.astype(float)
        u["split"] = np.where(u.index.isin(self.test), "test", "dev")
        self.u = u
        for c, rec in EXAMPLES.items():
            assert u.at[rec, "split"] == "dev" and u.at[rec, "label"] == c, rec
        self._parts = None

    def signal(self, rec: str) -> np.ndarray:
        assert self.u.at[rec, "split"] == "dev", "example strips come from development records only"
        if str(self.u.at[rec, "source"]).startswith("physionet"):
            if self._parts is None:
                self._parts = ecg_io.read_parts_manifest()
            return ecg_io.load_part1_signal(self.root, rec, self._parts[rec]["folder"])
        return ecg_io.load_figshare_signal(self.root, self.u.at[rec, "FileName"])

    def strip(self, rec, lead_idx=1, t0=0.0, t1=10.0):
        x = sps.sosfiltfilt(SOS, self.signal(rec)[lead_idx].astype(float)) / 1000.0   # mV
        i0, i1 = int(t0 * FS), int(t1 * FS)
        return np.arange(i0, i1) / FS, x[i0:i1]


# ---------------------------------------------------------------- 1 funnel
def fig_funnel(d: Data, out: Path) -> None:
    s = d.summary
    dev = sum(s["class_counts"]["dev"].values())
    test = sum(s["class_counts"]["test"].values())
    steps = [
        ("Original Shaoxing release", [(10247, BLUE, "10,247 on PhysioNet"),
                                       (399, ORANGE, "399 SI from figshare")], None),
        ("Keep the six target rhythms", [(s["steps"]["six_class_rows"], BLUE, None)],
         "minus SVT 587, AT 121, AVNRT 16, AVRT 8, SAAWR 7"),
        ("Remove identical duplicates", [(s["steps"]["after_duplicates"], BLUE, None)],
         f"minus {len(s['dropped_duplicates'])} second copies of the same signal"),
        ("Remove flat-lead records", [(s["steps"]["units"], BLUE, None)],
         f"minus {len(s['dropped_zero_lead'])} records with an all-zero lead"),
        ("Split 80 / 20 by rhythm", [(dev, BLUE, f"{dev:,} development"),
                                     (test, INK2, f"{test:,} test, held out")], None),
    ]
    fig = plt.figure(figsize=(W, H))
    title(fig, f"From 10,646 ECGs to {s['steps']['units']:,} analysis units",
          "One 10-s, 12-lead resting ECG per unit, 500 Hz, Shaoxing People's Hospital")
    top, row, bx0, bx1 = 0.76, 0.132, 0.37, 0.86
    scale = (bx1 - bx0) / 10646
    for i, (label, segs, detail) in enumerate(steps):
        y = top - i * row
        fig.text(0.04, y + 0.012, label, fontsize=14, fontweight="bold", va="center")
        x = bx0
        for k, (v, col, _) in enumerate(segs):
            gap = 0.002 if k else 0.0
            fig.patches.append(FancyBboxPatch((x + gap, y - 0.018), v * scale - gap, 0.036,
                                              boxstyle="round,pad=0,rounding_size=0.004",
                                              transform=fig.transFigure, fc=col, ec="none"))
            x += v * scale
        fig.text(x + 0.008, y, f"{sum(v for v, _, _ in segs):,}", fontsize=14, fontweight="bold",
                 va="center")
        if detail:
            fig.text(0.04, y - 0.030, detail, fontsize=11, color=INK2, va="center")
        for k, (col, key) in enumerate([(c, kk) for _, c, kk in segs if kk]):
            swatch(fig, 0.04 + 0.145 * k, y - 0.030, col)
            fig.text(0.04 + 0.145 * k + 0.013, y - 0.030, key, fontsize=11, color=INK2, va="center")
    note(fig, f"Unit rules: VCM §8.1, src/make_split.py. Split stratified by rhythm, seed {s['seed']}.")
    fig.savefig(out / "01_dataset_funnel.png", dpi=DPI)
    plt.close(fig)


# ---------------------------------------------------------------- 2 class counts
def fig_counts(d: Data, out: Path) -> None:
    counts = pd.Series(d.summary["class_counts"]["all"])
    test = pd.Series(d.summary["class_counts"]["test"])
    order = counts.sort_values(ascending=False).index.tolist()
    fig = plt.figure(figsize=(W, H))
    title(fig, "The rhythms we care most about are the smallest classes",
          f"Number of ECGs per rhythm ({counts.sum():,} units)")
    for k, (col, lab) in enumerate([(BLUE, "R3 classes: rhythms not defined by heart rate"),
                                    (SINUS_GRAY, "Rate-defined sinus rhythms")]):
        swatch(fig, 0.04 + 0.38 * k, 0.800, col, 0.012, 0.022)
        fig.text(0.057 + 0.38 * k, 0.800, lab, fontsize=11.5, color=INK2, va="center")
    ax = fig.add_axes([0.24, 0.13, 0.66, 0.62])
    for yi, c in enumerate(order):
        ax.barh(yi, counts[c], height=0.55, color=color_of(c))
        ax.text(counts[c] + 50, yi, f"{counts[c]:,}", va="center", fontsize=13, fontweight="bold")
        ax.text(counts[c] + 50 + 75 * len(f"{counts[c]:,}"), yi, f"  test {test[c]}",
                va="center", fontsize=11, color=MUTED)
    ax.set_yticks(range(len(order)), [f"{NAMES[c]} ({c})" for c in order])
    ax.invert_yaxis()
    ax.set_xlim(0, counts.max() * 1.22)
    ax.xaxis.grid(True, color=GRID, lw=0.8)
    ax.xaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter("{x:,.0f}"))
    ax.set_axisbelow(True)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel("ECGs")
    note(fig, f"R3 is macro recall over SI, AFIB and AFL, so the {counts['SI']} SI ECGs weigh as much "
              f"as the {counts['AFIB']:,} AFIB ECGs.")
    fig.savefig(out / "02_class_counts.png", dpi=DPI)
    plt.close(fig)


# ---------------------------------------------------------------- 3 example strips
def fig_examples(d: Data, out: Path) -> None:
    rows = ["SR", "SB", "ST", "SI", "AFIB", "AFL"]
    data = {c: d.strip(EXAMPLES[c]) for c in rows}
    lo = min(np.percentile(x, 0.2) for _, x in data.values())
    hi = max(np.percentile(x, 99.8) for _, x in data.values())
    fig = plt.figure(figsize=(W, H))
    title(fig, "What each rhythm looks like: one 10-second lead-II strip each",
          "Grey grid: 0.2 s across, 0.5 mV up")
    top, bottom, gap = 0.84, 0.09, 0.012
    h = (top - bottom - gap * (len(rows) - 1)) / len(rows)
    for k, c in enumerate(rows):
        y0 = top - (k + 1) * h - k * gap
        ax = fig.add_axes([0.20, y0, 0.77, h])
        t, x = data[c]
        ecg_axes(ax, 0, 10, (lo - 0.05, hi + 0.05))
        ax.plot(t, x, color=INK, lw=0.9)
        if k < len(rows) - 1:
            ax.set_xticks([])
        else:
            ax.set_xticks(range(11), [f"{s} s" for s in range(11)])
        yc = y0 + h / 2
        fig.text(0.19, yc + 0.012, NAMES[c], ha="right", va="center", fontsize=12.5, fontweight="bold")
        fig.text(0.19, yc - 0.018, f"{c} · {d.u.at[EXAMPLES[c], 'VentricularRate']:.0f} bpm",
                 ha="right", va="center", fontsize=10.5, color=INK2)
        swatch(fig, 0.03, yc, color_of(c), 0.006, 0.024)
    note(fig, "Development records: " + ", ".join(f"{c} {EXAMPLES[c]}" for c in rows)
         + ". Filtered 0.5-40 Hz for display only.")
    fig.savefig(out / "03_example_strips.png", dpi=DPI)
    plt.close(fig)


# ---------------------------------------------------------------- 4 / 5 strip plots
def strip_plot(d: Data, out: Path, col: str, fname: str, ttl: str, sub: str, xlabel: str,
               xlim, foot: str, cuts=(), right=None) -> None:
    rng = np.random.default_rng(0)
    fig = plt.figure(figsize=(W, H))
    title(fig, ttl, sub)
    ax = fig.add_axes([0.20, 0.13, 0.62 if right else 0.75, 0.66])
    for k, c in enumerate(ORDER):
        v = d.u.loc[d.u.label == c, col].to_numpy()
        ax.scatter(v, k + rng.uniform(-0.28, 0.28, len(v)), s=4, color=color_of(c), alpha=0.35,
                   linewidths=0)
        q1, med, q3 = np.percentile(v, [25, 50, 75])
        ax.plot([q1, q3], [k, k], color=INK, lw=2.2, solid_capstyle="round")
        ax.scatter([med], [k], s=60, color=INK, edgecolors=BG, linewidths=2, zorder=3)
        if right:
            right(ax, k, c, med)
    for cut in cuts:
        ax.axvline(cut, color=INK2, lw=1, zorder=0)
        ax.text(cut + 1.5, -0.62, f"{cut} bpm", ha="left", va="center", fontsize=11.5, color=INK2)
    tidy_rows(ax, len(ORDER))
    ax.set_xlim(*xlim)
    ax.set_xlabel(xlabel)
    note(fig, foot)
    fig.savefig(out / fname, dpi=DPI)
    plt.close(fig)


def fig_rate(d: Data, out: Path) -> None:
    s = d.u[d.u.label.isin(["SB", "SR", "ST"])]
    rule = np.select([s.VentricularRate < 60, s.VentricularRate > 100], ["SB", "ST"], "SR")
    agree = (rule == s.label).mean()
    strip_plot(d, out, "VentricularRate", "04_heart_rate_by_rhythm.png",
               "Sinus brady / normal / tachy labels are heart-rate thresholds",
               f"Ventricular rate per ECG. {agree:.1%} of SB, SR and ST labels follow the 60 / 100 bpm "
               "cut-offs; SI, AFIB and AFL do not",
               "Ventricular rate (bpm), as measured by the GE MUSE system", (30, 230),
               f"Dots: individual ECGs ({len(d.u):,}). Black bar: middle 50%; black dot: median. "
               "This is why heart rate alone (M_HR) is the floor model.", cuts=(60, 100))


def fig_age(d: Data, out: Path) -> None:
    def right(ax, k, c, med):
        male = (d.u.loc[d.u.label == c, "Gender"].str.upper() == "MALE").mean()
        ax.text(103, k, f"{male:.0%}", va="center", fontsize=13, fontweight="bold")
        ax.text(112, k, f"median {med:.0f} y", va="center", fontsize=11, color=INK2)
        if k == 0:
            ax.text(103, -0.75, "male", fontsize=11, color=INK2, va="bottom")
    strip_plot(d, out, "PatientAge", "05_age_sex_by_rhythm.png",
               "Patients differ by rhythm, so no model is given age or sex",
               "Age per ECG, and the share of male patients, by rhythm",
               "Age (years), figshare Diagnostics.xlsx", (0, 100),
               "Black bar: middle 50%; black dot: median.", right=right)


# ---------------------------------------------------------------- 6 windows
def fig_windows(d: Data, out: Path) -> None:
    rec = EXAMPLES["SI"]
    t, x = d.strip(rec)
    tabs = {T: pd.read_csv(REPO / "results" / "features" / "tables" / f"features_dev_T{T}.csv",
                           usecols=["record", "label", "meta_n_rpeaks"]) for T in WINDOWS}
    fig = plt.figure(figsize=(W, H))
    title(fig, "Shorter windows leave fewer beats to judge the rhythm",
          f"Sinus irregularity ({rec}), lead II. Each model sees only the first T seconds")
    ax = fig.add_axes([0.13, 0.52, 0.66, 0.30])
    ecg_axes(ax, 0, 10, (x.min() - 0.05, x.max() + 0.05))
    ax.plot(t, x, color=INK, lw=0.9)
    ax.set_xticks(range(11), [f"{s} s" for s in range(11)])
    fig.text(0.12, 0.67, "Lead II", ha="right", va="center", fontsize=13, fontweight="bold")
    ax2 = fig.add_axes([0.13, 0.11, 0.66, 0.34], sharex=ax)
    ax2.set_ylim(len(WINDOWS) - 0.4, -1.1)
    ax2.axis("off")
    fig.text(0.81, 0.455, "this record", fontsize=11, color=INK2, va="center")
    fig.text(0.905, 0.455, "dev crops\n< 3 R peaks", fontsize=10, color=INK2, va="center",
             linespacing=1.1)
    for k, T in enumerate(WINDOWS):
        tab = tabs[T]
        n_r = int(tab.loc[tab.record == rec, "meta_n_rpeaks"].iloc[0])
        few = (tab.meta_n_rpeaks < 3).mean()
        ax2.add_patch(FancyBboxPatch((0, k - 0.17), T, 0.34, boxstyle="round,pad=0,rounding_size=0.08",
                                     mutation_aspect=0.25, fc=BLUE, ec="none", alpha=1.0 - 0.15 * k))
        ax2.text(-0.15, k, f"{T} s", ha="right", va="center", fontsize=13, fontweight="bold")
        yfig = ax2.transData.transform((0, k))
        yf = fig.transFigure.inverted().transform(yfig)[1]
        fig.text(0.81, yf, f"{n_r} R peaks", fontsize=12, va="center")
        fig.text(0.905, yf, f"{few:.0%}", fontsize=12, va="center", fontweight="bold")
    ax2.set_xlim(0, 10)
    note(fig, "R-peak counts from the committed development feature tables (NeuroKit2, lead II). "
              "With fewer than 3 R peaks the RR-variability features are missing.")
    fig.savefig(out / "06_windows.png", dpi=DPI)
    plt.close(fig)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=ecg_io.DEFAULT_DATA_ROOT)
    ap.add_argument("--out", type=Path, default=REPO / "report" / "figures")
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    d = Data(a.data_root.expanduser())
    for f in (fig_funnel, fig_counts, fig_examples, fig_rate, fig_age, fig_windows):
        f(d, a.out)
    print("wrote", ", ".join(sorted(p.name for p in a.out.glob("*.png"))), "to", a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
