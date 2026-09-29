import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "pipeline"))
import numpy as np
from correct import QM, RegimeQM
from verify import cat_counts, cat_scores, cont_scores, nbr_matrix, fss_terms, PerDate
from regimes import shift, phase_label
from districts import DISTRICTS


def test_district_table():
    assert len(DISTRICTS) == 46 and len({d[0] for d in DISTRICTS}) == 46
    assert sum(d[3] == "core" for d in DISTRICTS) == 8


def test_perfect_forecast_scores():
    o = np.array([0, 3, 20, 70, 0.0])
    s = cat_scores(cat_counts(o, o, 15.6))
    assert s["csi"] == 1 and s["pod"] == 1 and s["far"] == 0 and s["ets"] == 1
    assert cont_scores(o, o)["rmse"] == 0


def test_contingency_known_case():
    o = np.array([20, 20, 0, 0, 20.0]); p = np.array([20, 0, 20, 0, 20.0])
    H, M, F, CN = cat_counts(o, p, 15.6)
    assert (H, M, F, CN) == (2, 1, 1, 1)
    s = cat_scores(np.array([H, M, F, CN]))
    assert abs(s["csi"] - 0.5) < 1e-9 and abs(s["pod"] - 2 / 3) < 1e-9 and abs(s["far"] - 1 / 3) < 1e-9


def test_qm_removes_multiplicative_bias_and_keeps_dry_dry():
    rng = np.random.default_rng(1)
    obs = np.where(rng.random(5000) < .4, rng.gamma(0.6, 12, 5000), 0.0)
    fc = obs * 1.5
    q = QM(fc, obs)
    assert abs(q(fc).mean() - obs.mean()) < 0.05 * obs.mean()
    assert (q(np.zeros(10)) == 0).all()
    assert (q(fc) >= 0).all()


def test_qm_monotone():
    rng = np.random.default_rng(2)
    obs = rng.gamma(0.7, 8, 3000) * (rng.random(3000) < .5); fc = rng.gamma(0.7, 12, 3000) * (rng.random(3000) < .6)
    q = QM(fc, obs)
    x = np.linspace(0, 200, 400)
    assert (np.diff(q(x)) >= -1e-9).all()


def test_regime_qm_falls_back_when_few_samples():
    rng = np.random.default_rng(3)
    fc = rng.gamma(1, 5, 1000); obs = fc * 0.8
    reg = np.array(["normal"] * 950 + ["active"] * 50)
    m = RegimeQM(fc, obs, reg)
    assert "normal" in m.by and "active" not in m.by
    assert m(fc[:5], reg[:5]).shape == (5,)


def test_fss_perfect_and_disjoint():
    W = np.eye(3)   # point-wise neighbourhood for 3 toy stations
    o = np.array([[20., 0, 0], [0, 20., 0]])
    n, d = fss_terms(o, o, 15.6, W)
    assert n.sum() == 0
    n, d = fss_terms(o, np.array([[0, 0, 20.], [20., 0, 0]]), 15.6, W)
    assert 1 - n.sum() / d.sum() == 0


def test_perdate_matches_flat_rmse():
    rng = np.random.default_rng(4)
    o = rng.gamma(.5, 10, (30, 46)); p = rng.gamma(.5, 10, (30, 46))
    pd_ = PerDate(o, p)
    assert abs(pd_.metrics(np.arange(30))["rmse"] - cont_scores(o.ravel(), p.ravel())["rmse"]) < 1e-9


def test_shift_no_leak_direction():
    a = np.arange(5.0)[:, None]
    assert shift(a, 1)[:, 0].tolist() == [0, 0, 1, 2, 3]   # value at t is a[t-1]


def test_phase_thresholds():
    assert phase_label(np.array([1.0, 0.99, -1.0, -0.5, 2])).tolist() == [2, 1, 0, 1, 2]
