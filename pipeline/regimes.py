"""Stage 2: regime labels (from observations, oracle) and forecast-time regime classifiers (deployable)."""
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import f1_score, balanced_accuracy_score
from common import *

PHASES = ["break", "normal", "active"]


def shift(a, k):
    """a[t-k] along axis 0 (first k rows repeat row 0)."""
    if k == 0:
        return a
    return np.concatenate([np.repeat(a[:1], k, 0), a[:-k]], 0)


class Stats:
    """Climatology from TRAINING JJAS days only; used to standardise the core-zone index (Rajeevan et al. 2010)."""

    def __init__(self, core, months, train):
        self.mu = {m: core[train & (months == m)].mean() for m in (6, 7, 8, 9)}
        resid = core[train] - np.array([self.mu[m] for m in months[train]])
        self.sd = resid.std()

    def z(self, core, months):
        mm = np.clip(months, 6, 9)
        return (core - np.array([self.mu[m] for m in mm])) / self.sd


def phase_label(z):  # 0 break, 1 normal, 2 active
    return np.where(z >= 1, 2, np.where(z <= -1, 0, 1))


def depression_label(obs, train):
    """Heuristic proxy: core/coastal district, 3-day centred obs sum >= district train-JJAS P95, and day >= 10 mm."""
    r3 = shift(obs, 1) + obs + np.concatenate([obs[1:], obs[-1:]], 0)
    lab = np.zeros(obs.shape, bool)
    for j, n in enumerate(NAMES):
        if TAG[n] in ("core", "coastal"):
            thr = np.percentile(r3[train, j], 95)
            lab[:, j] = (r3[:, j] >= thr) & (obs[:, j] >= 10)
    return lab


class RegimeModel:
    def __init__(self, P, lead, train_years):
        self.lead = lead
        idx = P["obs"].index
        self.idx = idx
        self.months = idx.month.values
        self.train = np.isin(idx.year, train_years) & (self.months >= 6) & (self.months <= 9)
        self.obs = P["obs"].values
        self.fc = P[f"fc_d{lead}"].values
        core_o = self.obs[:, CORE_IDX].mean(1)
        core_f = self.fc[:, CORE_IDX].mean(1)
        so, sf = Stats(core_o, self.months, self.train), Stats(core_f, self.months, self.train)
        self.z_obs, self.z_fc = so.z(core_o, self.months), sf.z(core_f, self.months)
        self.phase_true = phase_label(self.z_obs)  # oracle label
        self.dep_true = depression_label(self.obs, self.train)
        self.elig = np.array([TAG[n] in ("core", "coastal") for n in NAMES])
        self._fit()

    def _phase_X(self):
        return np.c_[self.z_fc, shift(self.z_fc, 1), shift(self.z_obs, self.lead)]

    def _dep_rows(self, dmask):
        T, J = self.fc.shape
        f0, f1 = np.log1p(self.fc), np.log1p(shift(self.fc, 1))
        zc = np.repeat(self.z_fc[:, None], J, 1)
        sel = dmask[:, None] & self.elig[None]
        return np.c_[f0[sel], f1[sel], zc[sel]], sel

    def _fit(self):
        X, y = self._phase_X(), self.phase_true
        self.sc = StandardScaler().fit(X[self.train])
        self.phase_clf = LogisticRegression(C=1.0, max_iter=2000).fit(self.sc.transform(X[self.train]), y[self.train])
        self.phase_logit = self.phase_clf.predict(self.sc.transform(X))  # comparator only
        # deployed: Rajeevan +/-1 sd rule applied to the *forecast* core-zone index (no fitted parameters)
        self.phase_pred = phase_label(self.z_fc)
        Xd, seld = self._dep_rows(self.train)
        yd = self.dep_true[seld]
        self.dep_sc = StandardScaler().fit(Xd)
        self.dep_clf = LogisticRegression(C=1.0, class_weight="balanced", max_iter=2000).fit(self.dep_sc.transform(Xd), yd)
        p = self.dep_clf.predict_proba(self.dep_sc.transform(Xd))[:, 1]
        ths = np.linspace(0.2, 0.95, 31)
        self.dep_thr = float(ths[int(np.argmax([f1_score(yd, p >= t) for t in ths]))])
        Xa, sela = self._dep_rows(np.ones(len(self.idx), bool))
        pa = self.dep_clf.predict_proba(self.dep_sc.transform(Xa))[:, 1]
        self.dep_pred = np.zeros(self.fc.shape, bool)
        self.dep_pred[sela] = pa >= self.dep_thr

    def assign(self, oracle=False):
        """T x J array of regime names."""
        ph = self.phase_true if oracle else self.phase_pred
        dep = self.dep_true if oracle else self.dep_pred
        T, J = self.fc.shape
        out = np.empty((T, J), object)
        base = np.array(PHASES, object)[ph]
        for j, n in enumerate(NAMES):
            t = TAG[n]
            if t in ("orographic", "himalayan", "northeast"):
                out[:, j] = "orographic"
            elif t == "coastal":
                out[:, j] = np.where(dep[:, j], "depression", "coastal")
            elif t == "core":
                out[:, j] = np.where(dep[:, j], "depression", base)
            else:
                out[:, j] = base
        return out

    def report(self, test):
        """Classifier skill on held-out test days vs naive baselines."""
        y = self.phase_true[test]
        f = lambda p: dict(acc=float((p == y).mean()), bal_acc=float(balanced_accuracy_score(y, p)))
        rep = dict(n_days=int(test.sum()), true_counts={PHASES[k]: int((y == k).sum()) for k in range(3)},
                   deployed_forecast_index_rule=f(self.phase_pred[test]),
                   fitted_logistic_comparator=f(self.phase_logit[test]),
                   persistence=f(phase_label(shift(self.z_obs, self.lead))[test]),
                   majority=f(np.full_like(y, np.bincount(self.phase_true[self.train]).argmax())))
        sel = test[:, None] & self.elig[None]
        yt, yp = self.dep_true[sel], self.dep_pred[sel]
        tp = int((yt & yp).sum())
        rep["depression"] = dict(threshold=self.dep_thr, n_true=int(yt.sum()), n_pred=int(yp.sum()), hits=tp,
                                 pod=tp / max(int(yt.sum()), 1), far=(int(yp.sum()) - tp) / max(int(yp.sum()), 1))
        return rep
