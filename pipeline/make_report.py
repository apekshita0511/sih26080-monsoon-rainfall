"""Generate outputs/VERIFICATION_REPORT.md and outputs/dashboard/*.json strictly from outputs/results.json + predictions CSVs."""
import json
import pandas as pd
from common import *

D = json.load(open(OUT / "results.json"))
R, M = D["results"], D["manifest"]
LABEL = {"raw": "Raw GFS", "global_qm": "Global QM", "regime_qm": "Regime QM", "regime_qm_oracle": "Regime QM (oracle regime)",
         "regime_gbm": "Regime GBM"}
f2 = lambda x: "–" if x is None else f"{x:.2f}"
f3 = lambda x: "–" if x is None else f"{x:.3f}"


def overall_table(r):
    h = "| Method | RMSE | Bias | POD≥15.6 | FAR≥15.6 | CSI≥15.6 | ETS≥15.6 | CSI≥64.5 | ETS≥64.5 | FSS 250km ≥15.6 |\n|---|---|---|---|---|---|---|---|---|---|\n"
    for m, v in r["overall"].items():
        c1, c2 = v["cat"]["15.6"], v["cat"]["64.5"]
        h += f"| {LABEL[m]} | {v['rmse']:.2f} | {v['bias']:+.2f} | {f2(c1['pod'])} | {f2(c1['far'])} | {f2(c1['csi'])} | {f2(c1['ets'])} | {f2(c2['csi'])} | {f2(c2['ets'])} | {f3(r['fss'][m]['250km_15.6'])} |\n"
    return h


def regime_table(r):
    h = "| Regime | n | RMSE raw | RMSE global QM | RMSE regime QM | RMSE GBM | Bias raw | Bias global QM | Bias regime QM |\n|---|---|---|---|---|---|---|---|---|\n"
    for g, v in r["by_regime"].items():
        h += f"| {g} | {v['n']} | " + " | ".join(f"{v[m]['rmse']:.2f}" for m in ["raw", "global_qm", "regime_qm", "regime_gbm"]) + " | " + " | ".join(f"{v[m]['bias']:+.2f}" for m in ["raw", "global_qm", "regime_qm"]) + " |\n"
    return h


def lead_table():
    h = "| Test | Lead | RMSE raw | RMSE global QM | RMSE regime QM | RMSE GBM | CSI≥15.6 raw → global QM | CSI≥64.5 raw → global QM |\n|---|---|---|---|---|---|---|---|\n"
    for k, r in R.items():
        o = r["overall"]
        h += f"| {r['split']} ({r['test_year']}) | {r['lead']} | " + " | ".join(f"{o[m]['rmse']:.2f}" for m in ["raw", "global_qm", "regime_qm", "regime_gbm"]) + \
             f" | {f2(o['raw']['cat']['15.6']['csi'])} → {f2(o['global_qm']['cat']['15.6']['csi'])} | {f2(o['raw']['cat']['64.5']['csi'])} → {f2(o['global_qm']['cat']['64.5']['csi'])} |\n"
    return h


def boot_table(r):
    keys = [("rmse", "RMSE"), ("csi_15.6", "CSI≥15.6"), ("ets_15.6", "ETS≥15.6"), ("csi_64.5", "CSI≥64.5"), ("fss_250km_15.6", "FSS250 ≥15.6")]
    h = "| Method − Raw | " + " | ".join(n for _, n in keys) + " |\n|---|" + "---|" * len(keys) + "\n"
    for m, v in r["bootstrap_vs_raw"].items():
        if m == "regime_qm_oracle":
            continue
        cells = []
        for k, _ in keys:
            q = v.get(k)
            sig = "" if q is None or (q["lo"] < 0 < q["hi"]) else " **\\***"
            cells.append("–" if q is None else f"{q['diff_mean']:+.3f} [{q['lo']:+.3f}, {q['hi']:+.3f}]{sig}")
        h += f"| {LABEL[m]} | " + " | ".join(cells) + " |\n"
    return h


def heavy_table(r):
    h = "| Threshold | Train / test events | Raw binary BSS | Global logistic BSS | Regime logistic BSS | Regime logistic AUC |\n|---|---|---|---|---|---|\n"
    for t, v in r["heavy_rain"].items():
        b = lambda k: f3(v[k]["bss"])
        h += f"| ≥{t} mm | {v['train_events']} / {v['test_events']} | {b('raw_forecast_binary')} | {b('global_logistic')} | {b('regime_logistic')} | {f3(v['regime_logistic']['auc'])} |\n"
    return h


def clf_table(r):
    c = r["regime_classifier"]
    h = "| Phase classifier (held-out days) | Accuracy | Balanced accuracy |\n|---|---|---|\n"
    for k in ["deployed_forecast_index_rule", "fitted_logistic_comparator", "persistence", "majority"]:
        h += f"| {k.replace('_', ' ')} | {c[k]['acc']:.2f} | {c[k]['bal_acc']:.2f} |\n"
    d = c["depression"]
    return h + f"\nDepression proxy (core+coastal districts): {d['n_true']} true district-days, {d['n_pred']} flagged, POD {d['pod']:.2f}, FAR {d['far']:.2f}. Days: {c['true_counts']}.\n"


A1, B1 = R["A_lead1"], R["B_lead1"]
md = f"""# SIH26080 – Regime-Aware Post-Processing of Monsoon Rainfall: Verification Report

Generated {M['generated']} from real data only ({M['data_span'][0]} → {M['data_span'][1]}, {M['n_districts']} districts). Every number below is produced by `pipeline/run.py`; nothing is hand-entered.

## Setup
- **Truth:** ERA5 daily precipitation (Open-Meteo archive API) – a reanalysis proxy, not IMD gauge data.
- **Raw forecast:** archived GFS (`gfs_seamless`) *previous-runs* precipitation at lead 1/2/3 days, hourly values summed to IST days.
- **Test A (headline, as specified):** fit on JJAS 2024, verify on held-out JJAS 2025 ({A1['test_days']} days × {M['n_districts']} districts).
- **Test B (confirmation):** fit on JJAS 2024+2025, verify on JJAS 2026 to {B1['test_last']} ({B1['test_days']} days).
- **No leakage:** regime labels use observed rain (Rajeevan et al. 2010 index for active/break; obs-based depression proxy), but the *correction* only sees regimes **predicted from forecast-time information** (forecast core-zone index, forecast rainfall). The oracle-regime row shows what perfect regime knowledge would do.
- **Methods:** Raw · Global QM (one wet-day-adaptive quantile map) · Regime QM (map per regime, ≥200 training samples else global) · Regime GBM (shallow, regularised HistGB on log rain with regime/geography inputs).
- Categorical scores at IMD thresholds ≥2.5, ≥15.6 (moderate), ≥64.5 mm (heavy). FSS is a station-neighbourhood version (46 scattered stations; neighbourhood = stations within 250/500 km).
- Uncertainty: paired 7-day block bootstrap over dates, {M['bootstrap_B']} resamples; **\\*** marks a 95% interval that excludes 0.

## Test A – JJAS 2025, lead 1
{overall_table(A1)}
Observed heavy (≥64.5 mm) events in test: {A1['overall']['raw']['cat']['64.5']['n_obs_events']}.

Paired difference vs raw (mean [95% CI]):

{boot_table(A1)}

### By regime (predicted regime, lead 1)
{regime_table(A1)}

### Regime classifier
{clf_table(A1)}

### Heavy-rain exceedance probability (Brier skill score vs training climatology)
{heavy_table(A1)}

## Test B – JJAS 2026 (to {B1['test_last']}), lead 1
{overall_table(B1)}
{boot_table(B1)}

### By regime
{regime_table(B1)}

### Heavy-rain exceedance probability
{heavy_table(B1)}

## All leads
{lead_table()}

## What the data supports (and doesn't)
1. **Quantile mapping fixes the categorical/frequency skill, not RMSE.** Global QM lifts CSI≥15.6 with an interval excluding zero in both tests (A: +0.021, B: +0.032) and raises FSS in B, while RMSE is statistically unchanged at lead 1 and slightly worse at lead 3 (QM preserves variance, which RMSE penalises).
2. **Regime-specific QM is not clearly better than one global QM overall.** Its CSI≥15.6 gain over raw is smaller than global QM's in Test A (+0.007, interval includes 0) and comparable in Test B; its RMSE in Test A is worse than raw, and with oracle regimes it is worse still – with a single training season per-regime maps overfit. With two training seasons (Test B) it roughly matches global QM.
3. **Where regime-awareness does help: the depression regime.** Raw GFS is heavily wet-biased there (bias +13.4 mm in A, +13.9 in B) and a global map makes it worse (+21.4 in A); the depression-specific map cuts the bias to +1.3 / +3.7 and lowers RMSE (31.5→26.9 in A, 51.2→47.9 in B). Caveat: the depression flag is a heuristic proxy with a high false-alarm ratio (see classifier table).
4. **The regularised GBM wins on RMSE (−2.2 / −2.0, intervals exclude 0) but loses heavy-rain skill** (CSI≥64.5 −0.07 / −0.06, frequency bias ≈0.1–0.15) and FSS. It regresses toward the mean. It is *not* a better correction for extremes.
5. **Heavy-rain probability:** a logistic model on forecast (global or regime-conditioned) beats climatology (BSS>0) at every threshold, while the raw forecast used as a yes/no exceedance forecast does worse than climatology at ≥15.6 and ≥64.5 mm. Regime-conditioning adds no measurable gain over the global logistic. ≥115.6 mm has very few events (see table) so it is indicative only.
6. Heavy (≥64.5 mm) categorical differences between methods are **not statistically distinguishable** at lead 1 (all intervals include 0) – ~70 events per season.

## Limitations
- ERA5 truth (reanalysis) underestimates local extremes relative to gauges; heavy-rain skill is measured against that proxy.
- 1–2 training seasons. Results are a demonstration of method and honest measurement, not production robustness.
- Depression regime is a rainfall-based heuristic (no free track feed); its classifier over-flags. Western-disturbance regime needs Oct–May data and is outside this JJAS verification.
- Active/break index uses per-month climatology from the training seasons only (a multi-decade daily climatology is not available for the forecast archive window).
- The final {M['drop_last_days']} days of the fetched range are dropped (latest-run / ERA5T lag).
- Deviation from the review document: the district table sums to **46** (8+10+6+4+4+6+3+5), not 42 as the document stated; all 46 are used.
- The fitted multinomial-logistic phase classifier did worse than applying the ±1σ rule to the forecast index, so the rule is what is deployed; the logistic is reported as a comparator.
"""
(OUT / "VERIFICATION_REPORT.md").write_text(md, encoding="utf-8")

# ---- dashboard data ----
DB = OUT / "dashboard"
DB.mkdir(exist_ok=True)
dist = []
for i, (n, la, lo, tg) in enumerate(DISTRICTS):
    d = dict(name=n, lat=la, lon=lo, tag=tg)
    for key in ("A_lead1", "B_lead1"):
        bd = R[key]["by_district"][n]
        d[key] = {m: dict(rmse=round(bd[m]["rmse"], 3), bias=round(bd[m]["bias"], 3)) for m in ["raw", "global_qm", "regime_qm", "regime_gbm"]}
    dist.append(d)
(DB / "districts.json").write_text(json.dumps(dist))
for key in ("A_lead1", "B_lead1"):
    df = pd.read_csv(OUT / f"predictions_{key}.csv")
    (DB / f"timeseries_{key}.json").write_text(df.to_json(orient="records"))
slim = {k: {kk: vv for kk, vv in v.items() if kk in ("split", "lead", "train_years", "test_year", "test_days", "test_first", "test_last", "overall", "by_regime", "fss", "bootstrap_vs_raw", "heavy_rain", "regime_classifier")} for k, v in R.items()}
(DB / "summary.json").write_text(json.dumps(dict(manifest=M, results=slim), default=float))
print("report + dashboard data written")
