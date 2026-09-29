# SIH26080 – Regime-Aware Post-Processing of Monsoon Rainfall: Verification Report

Generated 2026-09-29T23:02:07 from real data only (2024-02-01 → 2026-09-25, 46 districts). Every number below is produced by `pipeline/run.py`; nothing is hand-entered.

## Setup
- **Truth:** ERA5 daily precipitation (Open-Meteo archive API) – a reanalysis proxy, not IMD gauge data.
- **Raw forecast:** archived GFS (`gfs_seamless`) *previous-runs* precipitation at lead 1/2/3 days, hourly values summed to IST days.
- **Test A (headline, as specified):** fit on JJAS 2024, verify on held-out JJAS 2025 (122 days × 46 districts).
- **Test B (confirmation):** fit on JJAS 2024+2025, verify on JJAS 2026 to 2026-09-25 (117 days).
- **No leakage:** regime labels use observed rain (Rajeevan et al. 2010 index for active/break; obs-based depression proxy), but the *correction* only sees regimes **predicted from forecast-time information** (forecast core-zone index, forecast rainfall). The oracle-regime row shows what perfect regime knowledge would do.
- **Methods:** Raw · Global QM (one wet-day-adaptive quantile map) · Regime QM (map per regime, ≥200 training samples else global) · Regime GBM (shallow, regularised HistGB on log rain with regime/geography inputs).
- Categorical scores at IMD thresholds ≥2.5, ≥15.6 (moderate), ≥64.5 mm (heavy). FSS is a station-neighbourhood version (46 scattered stations; neighbourhood = stations within 250/500 km).
- Uncertainty: paired 7-day block bootstrap over dates, 1000 resamples; **\*** marks a 95% interval that excludes 0.

## Test A – JJAS 2025, lead 1
| Method | RMSE | Bias | POD≥15.6 | FAR≥15.6 | CSI≥15.6 | ETS≥15.6 | CSI≥64.5 | ETS≥64.5 | FSS 250km ≥15.6 |
|---|---|---|---|---|---|---|---|---|---|
| Raw GFS | 13.47 | -1.34 | 0.46 | 0.44 | 0.33 | 0.24 | 0.16 | 0.15 | 0.595 |
| Global QM | 13.79 | +1.14 | 0.56 | 0.50 | 0.36 | 0.24 | 0.16 | 0.15 | 0.619 |
| Regime QM | 14.39 | +0.98 | 0.53 | 0.51 | 0.34 | 0.23 | 0.17 | 0.16 | 0.605 |
| Regime QM (oracle regime) | 17.52 | +2.42 | 0.55 | 0.51 | 0.35 | 0.24 | 0.12 | 0.11 | 0.612 |
| Regime GBM | 11.25 | -2.14 | 0.38 | 0.33 | 0.32 | 0.25 | 0.09 | 0.09 | 0.560 |

Observed heavy (≥64.5 mm) events in test: 68.

Paired difference vs raw (mean [95% CI]):

| Method − Raw | RMSE | CSI≥15.6 | ETS≥15.6 | CSI≥64.5 | FSS250 ≥15.6 |
|---|---|---|---|---|---|
| Global QM | +0.339 [-0.180, +0.790] | +0.021 [+0.002, +0.039] **\*** | +0.003 [-0.015, +0.020] | +0.001 [-0.021, +0.025] | +0.024 [-0.001, +0.048] |
| Regime QM | +0.929 [+0.409, +1.455] **\*** | +0.007 [-0.017, +0.031] | -0.010 [-0.034, +0.013] | +0.012 [-0.018, +0.042] | +0.011 [-0.022, +0.042] |
| Regime GBM | -2.207 [-3.411, -1.106] **\*** | -0.015 [-0.038, +0.007] | +0.005 [-0.018, +0.027] | -0.069 [-0.166, +0.046] | -0.036 [-0.066, -0.009] **\*** |


### By regime (predicted regime, lead 1)
| Regime | n | RMSE raw | RMSE global QM | RMSE regime QM | RMSE GBM | Bias raw | Bias global QM | Bias regime QM |
|---|---|---|---|---|---|---|---|---|
| active | 246 | 9.99 | 10.35 | 10.35 | 7.91 | -1.77 | +0.32 | +0.32 |
| break | 329 | 11.64 | 13.00 | 13.00 | 9.24 | -0.63 | +1.46 | +1.46 |
| normal | 2034 | 9.18 | 9.64 | 9.93 | 8.53 | -1.34 | +0.44 | +1.05 |
| depression | 211 | 31.54 | 34.04 | 26.88 | 22.34 | +13.36 | +21.36 | +1.32 |
| orographic | 1708 | 16.35 | 16.15 | 18.65 | 13.60 | -1.68 | +1.31 | +1.32 |
| coastal | 1084 | 10.12 | 9.91 | 11.10 | 9.51 | -3.78 | -1.64 | +0.26 |


### Regime classifier
| Phase classifier (held-out days) | Accuracy | Balanced accuracy |
|---|---|---|
| deployed forecast index rule | 0.72 | 0.59 |
| fitted logistic comparator | 0.66 | 0.44 |
| persistence | 0.66 | 0.55 |
| majority | 0.66 | 0.33 |

Depression proxy (core+coastal districts): 56 true district-days, 211 flagged, POD 0.55, FAR 0.85. Days: {'break': 28, 'normal': 80, 'active': 14}.


### Heavy-rain exceedance probability (Brier skill score vs training climatology)
| Threshold | Train / test events | Raw binary BSS | Global logistic BSS | Regime logistic BSS | Regime logistic AUC |
|---|---|---|---|---|---|
| ≥15.6 mm | 1341 / 1155 | -0.134 | 0.232 | 0.236 | 0.824 |
| ≥64.5 mm | 113 / 68 | -0.421 | 0.122 | 0.121 | 0.928 |
| ≥115.6 mm | 19 / 10 | -0.501 | 0.094 | 0.107 | 0.965 |


## Test B – JJAS 2026 (to 2026-09-25), lead 1
| Method | RMSE | Bias | POD≥15.6 | FAR≥15.6 | CSI≥15.6 | ETS≥15.6 | CSI≥64.5 | ETS≥64.5 | FSS 250km ≥15.6 |
|---|---|---|---|---|---|---|---|---|---|
| Raw GFS | 14.95 | -2.26 | 0.43 | 0.43 | 0.32 | 0.24 | 0.18 | 0.17 | 0.584 |
| Global QM | 14.85 | -0.56 | 0.51 | 0.47 | 0.35 | 0.27 | 0.19 | 0.18 | 0.615 |
| Regime QM | 14.87 | -0.57 | 0.51 | 0.47 | 0.35 | 0.26 | 0.18 | 0.17 | 0.615 |
| Regime QM (oracle regime) | 16.56 | -0.25 | 0.49 | 0.49 | 0.33 | 0.24 | 0.17 | 0.16 | 0.583 |
| Regime GBM | 12.94 | -2.99 | 0.32 | 0.29 | 0.28 | 0.23 | 0.12 | 0.12 | 0.512 |

| Method − Raw | RMSE | CSI≥15.6 | ETS≥15.6 | CSI≥64.5 | FSS250 ≥15.6 |
|---|---|---|---|---|---|
| Global QM | -0.091 [-0.362, +0.199] | +0.032 [+0.019, +0.042] **\*** | +0.021 [+0.009, +0.032] **\*** | +0.004 [-0.031, +0.036] | +0.031 [+0.016, +0.047] **\*** |
| Regime QM | -0.057 [-0.558, +0.471] | +0.030 [+0.011, +0.050] **\*** | +0.020 [+0.000, +0.039] **\*** | -0.001 [-0.055, +0.057] | +0.032 [+0.009, +0.054] **\*** |
| Regime GBM | -1.957 [-3.417, -0.709] **\*** | -0.041 [-0.085, +0.001] | -0.019 [-0.057, +0.021] | -0.062 [-0.167, +0.030] | -0.075 [-0.146, -0.017] **\*** |


### By regime
| Regime | n | RMSE raw | RMSE global QM | RMSE regime QM | RMSE GBM | Bias raw | Bias global QM | Bias regime QM |
|---|---|---|---|---|---|---|---|---|
| active | 206 | 9.16 | 9.12 | 9.88 | 10.64 | -2.51 | -1.10 | -0.78 |
| break | 220 | 7.65 | 8.21 | 7.73 | 5.32 | -0.56 | +0.38 | +0.29 |
| normal | 2085 | 9.51 | 9.73 | 9.94 | 9.14 | -1.49 | -0.17 | +0.16 |
| depression | 146 | 51.15 | 51.17 | 47.87 | 31.31 | +13.94 | +19.44 | +3.67 |
| orographic | 1638 | 15.68 | 15.49 | 16.41 | 14.82 | -2.76 | -0.65 | -0.71 |
| coastal | 1087 | 13.55 | 12.92 | 12.71 | 13.36 | -5.46 | -3.97 | -2.44 |


### Heavy-rain exceedance probability
| Threshold | Train / test events | Raw binary BSS | Global logistic BSS | Regime logistic BSS | Regime logistic AUC |
|---|---|---|---|---|---|
| ≥15.6 mm | 2496 / 962 | -0.083 | 0.252 | 0.264 | 0.835 |
| ≥64.5 mm | 181 / 71 | -0.170 | 0.179 | 0.173 | 0.937 |
| ≥115.6 mm | 29 / 21 | 0.044 | 0.144 | 0.157 | 0.938 |


## All leads
| Test | Lead | RMSE raw | RMSE global QM | RMSE regime QM | RMSE GBM | CSI≥15.6 raw → global QM | CSI≥64.5 raw → global QM |
|---|---|---|---|---|---|---|---|
| A (2025) | 1 | 13.47 | 13.79 | 14.39 | 11.25 | 0.33 → 0.36 | 0.16 → 0.16 |
| A (2025) | 2 | 14.31 | 14.68 | 15.44 | 12.06 | 0.27 → 0.31 | 0.15 → 0.14 |
| A (2025) | 3 | 14.69 | 15.56 | 18.87 | 12.17 | 0.26 → 0.29 | 0.10 → 0.10 |
| B (2026) | 1 | 14.95 | 14.85 | 14.87 | 12.94 | 0.32 → 0.35 | 0.18 → 0.19 |
| B (2026) | 2 | 14.84 | 15.03 | 15.34 | 13.61 | 0.29 → 0.33 | 0.14 → 0.16 |
| B (2026) | 3 | 16.70 | 17.10 | 17.53 | 14.49 | 0.26 → 0.29 | 0.11 → 0.12 |


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
- The final 2 days of the fetched range are dropped (latest-run / ERA5T lag).
- Deviation from the review document: the district table sums to **46** (8+10+6+4+4+6+3+5), not 42 as the document stated; all 46 are used.
- The fitted multinomial-logistic phase classifier did worse than applying the ±1σ rule to the forecast index, so the rule is what is deployed; the logistic is reported as a comparator.
