"""Stages 3-5: bias correction (global QM, regime QM, regime-aware GBM) and heavy-rain exceedance probability."""
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from common import *

WET = 0.1
MIN_N = 200  # min training samples for a regime-specific mapping, else fall back to global


class QM:
    """Empirical quantile mapping with wet-day frequency adaptation.
    Forecast value x >= WET -> its ECDF position p among ALL training forecasts -> observed quantile at p.
    Dry forecasts stay dry; forecasts whose p falls in the observed dry mass map to 0.
    Above the training max the top observed value is scaled by min(x/fmax, 2)."""

    def __init__(self, fc, obs):
        self.f, self.o = np.sort(fc), np.sort(obs)

    def __call__(self, x):
        x = np.asarray(x, float)
        out = np.zeros_like(x)
        w = x >= WET
        xw = x[w]
        n = len(self.f)
        p = (np.searchsorted(self.f, xw, "left") + np.searchsorted(self.f, xw, "right")) / 2 / n
        y = np.quantile(self.o, np.clip(p, 0, 1))
        fmax = self.f[-1]
        if fmax > 0:
            over = xw > fmax
            y[over] = self.o[-1] * np.minimum(xw[over] / fmax, 2.0)
        out[w] = np.where(y < WET, 0.0, y)
        return out


class RegimeQM:
    def __init__(self, fc, obs, reg):
        self.glob = QM(fc, obs)
        self.by = {}
        self.fallback = []
        for r in REGIMES:
            m = reg == r
            if m.sum() >= MIN_N:
                self.by[r] = QM(fc[m], obs[m])
            else:
                self.fallback.append((r, int(m.sum())))

    def __call__(self, x, reg):
        out = self.glob(x)
        for r, q in self.by.items():
            m = reg == r
            if m.any():
                out[m] = q(x[m])
        return out


def gbm_features(fc, fcprev, reg, tag, zfc, month):
    ri = np.array([REGIMES.index(r) for r in reg])
    ti = np.array([TAGS.index(t) for t in tag])
    return np.c_[np.log1p(fc), np.log1p(fcprev), ri, ti, zfc, month]


class RegimeGBM:
    """Regularised comparison model: shallow HistGB on log1p(obs) with regime/geography as categorical inputs."""

    def __init__(self, X, obs):
        self.m = HistGradientBoostingRegressor(max_depth=3, learning_rate=0.05, max_iter=200, min_samples_leaf=100,
                                               l2_regularization=1.0, categorical_features=[2, 3], random_state=0)
        self.m.fit(X, np.log1p(obs))

    def __call__(self, X):
        y = np.expm1(self.m.predict(X))
        return np.where(y < WET, 0.0, np.maximum(y, 0.0))


class HeavyProb:
    """P(obs >= thr) by L2 logistic regression on log1p(forecast) (+ regime dummies for the regime-conditioned version)."""

    def __init__(self, fc, obs, reg, thr, use_regime):
        self.thr, self.use_regime = thr, use_regime
        y = obs >= thr
        self.n_events = int(y.sum())
        self.ok = self.n_events >= 10
        self.base = float(y.mean())
        if self.ok:
            X = self._X(fc, reg)
            self.sc = StandardScaler().fit(X)
            self.clf = LogisticRegression(C=1.0, max_iter=2000).fit(self.sc.transform(X), y)

    def _X(self, fc, reg):
        cols = [np.log1p(fc)]
        if self.use_regime:
            cols += [(reg == r).astype(float) for r in REGIMES[:-1]]
        return np.column_stack(cols)

    def __call__(self, fc, reg):
        if not self.ok:
            return np.full(fc.shape, self.base)
        return self.clf.predict_proba(self.sc.transform(self._X(fc, reg)))[:, 1]
