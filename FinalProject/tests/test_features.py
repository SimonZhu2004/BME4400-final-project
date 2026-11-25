"""Checks for src/features.py (PRD §12). Needs no data: uses simulated ECGs.

    python -m pytest tests/test_features.py -q
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import features as F  # noqa: E402

warnings.filterwarnings("ignore")


def simulated_record(hr=75, seed=4400):
    """12 x 5000 int16 µV: the same simulated ECG on every lead, plus small lead-specific noise."""
    import neurokit2 as nk
    x = nk.ecg_simulate(duration=10, sampling_rate=500, heart_rate=hr, random_state=seed) * 1000
    rng = np.random.default_rng(seed)
    return np.stack([x + rng.normal(0, 5, x.size) for _ in range(12)]).astype(np.int16)


def same(a, b):
    return all((np.isnan(a[k]) and np.isnan(b[k])) or a[k] == b[k] for k in a)


def test_feature_list_fixed():
    assert len(F.FEATURES) == 16 and len(set(F.FEATURES)) == 16
    assert set(F.FEATURE_DOC) == {k.rsplit("_", 1)[0] if k.endswith(("_II", "_V1")) else k for k in F.FEATURES}


@pytest.mark.parametrize("T", F.WINDOWS)
def test_crop_is_first_T_seconds(T):
    sig = simulated_record()
    c = F.crop(sig, T)
    assert c.shape == (12, 500 * T)
    assert np.array_equal(c, sig[:, : 500 * T])
    if T == 10:
        assert np.array_equal(c, sig)


@pytest.mark.parametrize("T", [2, 4, 6, 8])
def test_features_use_only_the_crop(T):
    sig = simulated_record()
    before = F.crop_features(sig, T)
    changed = sig.copy()
    changed[:, 500 * T:] = np.random.default_rng(1).integers(-3000, 3000, changed[:, 500 * T:].shape)
    assert same(before, F.crop_features(changed, T))


def test_output_order_and_types():
    f = F.crop_features(simulated_record(), 10)
    assert list(f) == ["meta_n_rpeaks"] + F.FEATURES
    assert all(isinstance(v, float) for k, v in f.items() if k != "meta_n_rpeaks")


@pytest.mark.parametrize("hr", [55, 75, 110])
def test_heart_rate_on_simulated_ecg(hr):
    f = F.crop_features(simulated_record(hr=hr), 10)
    assert abs(f["hr"] - hr) < 3


def test_rr_missing_rules():
    one = F.rr_features(np.array([400]))
    assert all(np.isnan(v) for v in one.values())
    two = F.rr_features(np.array([400, 800]))
    assert two["hr"] == pytest.approx(75.0) and all(np.isnan(two[k]) for k in F.FEATURES[1:6])
    three = F.rr_features(np.array([400, 800, 1250]))
    assert not any(np.isnan(v) for v in three.values())


def test_rr_uses_mean_rr():
    f = F.rr_features(np.array([0, 400, 1000]))   # RR 800 and 1200 ms, mean 1000 ms
    assert f["hr"] == pytest.approx(60.0)


def test_p_consistency_rules():
    x = simulated_record()[1].astype(float)
    assert np.isnan(F.p_consistency(x, np.array([400])))           # one beat
    assert np.isnan(F.p_consistency(x, np.array([50, 400])))       # first region starts before the crop
    assert F.p_consistency(x, F.r_peaks(x)) > 0.8                  # regular simulated sinus rhythm
    noise = np.random.default_rng(0).normal(0, 50, x.size)
    assert abs(F.p_consistency(noise, F.r_peaks(x))) < 0.3          # no repeating P wave


def test_deterministic():
    sig = simulated_record()
    assert same(F.crop_features(sig, 4), F.crop_features(sig, 4))
