"""Stage 6: verification metrics (RMSE/MAE/bias, POD/FAR/CSI/ETS, station-neighbourhood FSS, Brier/AUC) + block bootstrap."""
import numpy as np
from sklearn.metrics import roc_auc_score
from common import *


def cat_counts(o, p, thr):
    ob, pb = o >= thr, p >= thr
    return np.array([(ob & pb).sum(), (ob & ~pb).sum(), (~ob & pb).sum(), (~ob & ~pb).sum()], float)  # H M F CN


def cat_scores(c):
    H, M, F, CN = c
    N = c.sum()
    hr = (H + M) * (H + F) / N if N else 0
    d = lambda a, b: float(a / b) if b > 0 else None
    return dict(pod=d(H, H + M), far=d(F, H + F), csi=d(H, H + M + F), ets=d(H - hr, H + M + F - hr),
                freq_bias=d(H + F, H + M), hits=int(H), misses=int(M), false_alarms=int(F), n_obs_events=int(H + M))


def cont_scores(o, p):
    e = p - o
    return dict(rmse=float(np.sqrt(np.mean(e ** 2))), mae=float(np.mean(np.abs(e))), bias=float(np.mean(e)),
                mean_obs=float(o.mean()), mean_pred=float(p.mean()), n=int(o.size))


def score_flat(o, p):
    d = cont_scores(o, p)
    d["cat"] = {str(t): cat_scores(cat_counts(o, p, t)) for t in THRESH}
    return d


def nbr_matrix(radius):
    D = haversine_km()
    W = (D <= radius).astype(float)
    return W / W.sum(1, keepdims=True)


def fss_terms(o2, p2, thr, W):
    """Per-date sums (num, den) of the fractions skill score over stations, W = row-normalised neighbourhood."""
    fo, fp = (o2 >= thr).astype(float) @ W.T, (p2 >= thr).astype(float) @ W.T
    return ((fp - fo) ** 2).sum(1), (fp ** 2 + fo ** 2).sum(1)


class PerDate:
    """Additive per-date statistics so any date-resample can be scored without refitting."""

    def __init__(self, o2, p2):
        e = p2 - o2
        self.sse = (e ** 2).sum(1)
        self.n = np.full(len(o2), o2.shape[1], float)
        self.cont = {t: np.array([cat_counts(o2[i], p2[i], t) for i in range(len(o2))]) for t in THRESH}
        self.fss = {}
        for R in FSS_RADII:
            W = nbr_matrix(R)
            for t in THRESH:
                self.fss[(R, t)] = np.c_[fss_terms(o2, p2, t, W)]

    def metrics(self, ix):
        m = {"rmse": float(np.sqrt(self.sse[ix].sum() / self.n[ix].sum()))}
        for t in THRESH:
            sc = cat_scores(self.cont[t][ix].sum(0))
            m[f"csi_{t}"], m[f"ets_{t}"], m[f"pod_{t}"], m[f"far_{t}"] = sc["csi"], sc["ets"], sc["pod"], sc["far"]
        for (R, t), a in self.fss.items():
            s = a[ix].sum(0)
            m[f"fss_{R}km_{t}"] = float(1 - s[0] / s[1]) if s[1] > 0 else None
        return m


def block_bootstrap(stats: dict, ref="raw", B=1000, block=7, seed=0):
    """Paired block bootstrap over dates: CI of (method - raw) for headline metrics. block=7 keeps weather persistence."""
    T = len(stats[ref].sse)
    rng = np.random.default_rng(seed)
    nb = int(np.ceil(T / block))
    ixs = [np.concatenate([np.arange(s, s + block) % T for s in rng.integers(0, T, nb)])[:T] for _ in range(B)]
    keys = None
    res = {}
    base = [stats[ref].metrics(ix) for ix in ixs]
    for name, st in stats.items():
        if name == ref:
            continue
        ms = [st.metrics(ix) for ix in ixs]
        keys = ms[0].keys()
        r = {}
        for k in keys:
            d = np.array([(a[k] - b[k]) if (a[k] is not None and b[k] is not None) else np.nan for a, b in zip(ms, base)])
            d = d[~np.isnan(d)]
            if len(d) < B * 0.5:
                continue
            r[k] = dict(diff_mean=float(d.mean()), lo=float(np.percentile(d, 2.5)), hi=float(np.percentile(d, 97.5)),
                        p_gt0=float((d > 0).mean()))
        res[name] = r
    return res


def prob_scores(y, p, base):
    y = y.astype(float)
    bs = float(np.mean((p - y) ** 2))
    bs_clim = float(np.mean((base - y) ** 2))
    out = dict(brier=bs, brier_clim=bs_clim, bss=(1 - bs / bs_clim) if bs_clim > 0 else None, n=int(y.size), n_events=int(y.sum()))
    out["auc"] = float(roc_auc_score(y, p)) if 0 < y.sum() < len(y) and len(np.unique(p)) > 1 else None
    return out


def reliability(y, p, bins=(0, .02, .05, .1, .2, .3, .5, .75, 1.0001)):
    rows = []
    for lo, hi in zip(bins[:-1], bins[1:]):
        m = (p >= lo) & (p < hi)
        if m.sum():
            rows.append(dict(lo=lo, hi=min(hi, 1.0), n=int(m.sum()), mean_p=float(p[m].mean()), obs_freq=float(y[m].mean())))
    return rows
