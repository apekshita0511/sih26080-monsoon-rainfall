"""Stages 2-6 end to end on the real fetched data. Usage: python run.py [--fast]"""
import sys, json, hashlib, platform, datetime
import numpy as np, pandas as pd, sklearn, scipy
from common import *
from regimes import RegimeModel, shift
from correct import QM, RegimeQM, RegimeGBM, gbm_features, HeavyProb
from verify import *

FAST = "--fast" in sys.argv
B = 100 if FAST else 1000
OUT.mkdir(exist_ok=True)
P = load_panel()
idx = P["obs"].index
months = idx.month.values
tags = np.array([TAG[n] for n in NAMES])
METHODS = ["raw", "global_qm", "regime_qm", "regime_qm_oracle", "regime_gbm"]


def flat(a, m):  # rows of dates m x all districts
    return a[m].ravel()


def rows(rm, m, reg):
    T, J = rm.fc.shape
    fcprev = shift(rm.fc, 1)
    tagm = np.tile(tags, (T, 1))
    zf = np.repeat(rm.z_fc[:, None], J, 1)
    mo = np.repeat(months[:, None], J, 1)
    return dict(fc=flat(rm.fc, m), fcprev=flat(fcprev, m), obs=flat(rm.obs, m), reg=flat(reg, m),
                tag=flat(tagm, m), z=flat(zf, m), mo=flat(mo, m))


def run(split, lead):
    tr_years, te_year = SPLITS[split]
    rm = RegimeModel(P, lead, tr_years)
    te = (idx.year == te_year) & (months >= 6) & (months <= 9)
    reg_p, reg_o = rm.assign(), rm.assign(True)
    R_tr, R_te = rows(rm, rm.train, reg_p), rows(rm, te, reg_p)
    R_teo = rows(rm, te, reg_o)
    nT = int(te.sum())
    shp = (nT, len(NAMES))

    gq = QM(R_tr["fc"], R_tr["obs"])
    rq = RegimeQM(R_tr["fc"], R_tr["obs"], R_tr["reg"])
    Xtr = gbm_features(R_tr["fc"], R_tr["fcprev"], R_tr["reg"], R_tr["tag"], R_tr["z"], R_tr["mo"])
    gb = RegimeGBM(Xtr, R_tr["obs"])
    Xte = gbm_features(R_te["fc"], R_te["fcprev"], R_te["reg"], R_te["tag"], R_te["z"], R_te["mo"])

    pred = {"raw": R_te["fc"], "global_qm": gq(R_te["fc"]), "regime_qm": rq(R_te["fc"], R_te["reg"]),
            "regime_qm_oracle": rq(R_te["fc"], R_teo["reg"]), "regime_gbm": gb(Xte)}
    o = R_te["obs"]
    pred2 = {k: v.reshape(shp) for k, v in pred.items()}
    o2 = o.reshape(shp)
    regf = R_te["reg"]
    dfl = np.tile(np.array(NAMES), nT)

    res = dict(split=split, lead=lead, train_years=tr_years, test_year=te_year,
               test_days=nT, test_first=str(idx[te][0].date()), test_last=str(idx[te][-1].date()),
               regime_classifier=rm.report(te), qm_fallback_regimes=rq.fallback,
               train_regime_counts={r: int((R_tr["reg"] == r).sum()) for r in REGIMES},
               test_regime_counts={r: int((regf == r).sum()) for r in REGIMES})
    res["overall"] = {k: score_flat(o, v) for k, v in pred.items()}
    res["by_regime"] = {r: {"n": int((regf == r).sum()),
                            **{k: score_flat(o[regf == r], v[regf == r]) for k, v in pred.items()}}
                        for r in REGIMES if (regf == r).sum() > 0}
    res["by_district"] = {n: {k: cont_scores(o[dfl == n], v[dfl == n]) for k, v in pred.items()} for n in NAMES}
    stats = {k: PerDate(o2, v) for k, v in pred2.items()}
    full = np.arange(nT)
    res["fss"] = {k: {f"{R}km_{t}": stats[k].metrics(full)[f"fss_{R}km_{t}"] for R in FSS_RADII for t in THRESH} for k in pred}
    res["bootstrap_vs_raw"] = block_bootstrap(stats, "raw", B=B)
    # heavy-rain exceedance probability
    hv = {}
    for thr in HEAVY_THR:
        y = o >= thr
        g = HeavyProb(R_tr["fc"], R_tr["obs"], R_tr["reg"], thr, False)
        h = HeavyProb(R_tr["fc"], R_tr["obs"], R_tr["reg"], thr, True)
        pg, ph = g(R_te["fc"], R_te["reg"]), h(R_te["fc"], regf)
        pdet = (R_te["fc"] >= thr).astype(float)
        base = g.base
        hv[str(thr)] = dict(train_events=g.n_events, test_events=int(y.sum()), fitted=g.ok, base_rate_train=base,
                            climatology=prob_scores(y, np.full(y.shape, base), base),
                            raw_forecast_binary=prob_scores(y, pdet, base),
                            global_logistic=prob_scores(y, pg, base), regime_logistic=prob_scores(y, ph, base),
                            reliability_regime_logistic=reliability(y, ph))
        pred[f"_p{thr}"] = ph
    res["heavy_rain"] = hv

    df = pd.DataFrame({"date": np.repeat(idx[te].strftime("%Y-%m-%d"), len(NAMES)), "district": dfl, "regime": regf,
                       "obs": o, **{k: np.round(v, 2) for k, v in pred.items() if not k.startswith("_")},
                       **{f"p_ge_{t}": np.round(pred[f"_p{t}"], 4) for t in HEAVY_THR}})
    df.to_csv(OUT / f"predictions_{split}_lead{lead}.csv", index=False)
    return res


if __name__ == "__main__":
    results = {}
    for s in SPLITS:
        for L in LEADS:
            results[f"{s}_lead{L}"] = run(s, L)
            r = results[f"{s}_lead{L}"]["overall"]
            print(s, L, {k: round(v["rmse"], 2) for k, v in r.items()}, flush=True)
    sha = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()[:16] for p in sorted(RAW.glob("*.csv"))}
    manifest = dict(generated=datetime.datetime.now().isoformat(timespec="seconds"), bootstrap_B=B, drop_last_days=DROP_LAST,
                    data_span=[str(idx[0].date()), str(idx[-1].date())], n_districts=len(NAMES),
                    sources=dict(truth="https://archive-api.open-meteo.com/v1/archive (ERA5 daily precipitation_sum, IST)",
                                 forecast="https://previous-runs-api.open-meteo.com/v1/forecast models=gfs_seamless, hourly precipitation_previous_day{1,2,3} summed to IST days"),
                    versions=dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__,
                                  sklearn=sklearn.__version__, scipy=scipy.__version__), raw_sha256_16=sha)
    (OUT / "results.json").write_text(json.dumps(dict(manifest=manifest, results=results), indent=1, default=float))
    print("wrote outputs/results.json")
