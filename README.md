# SIH26080 – Regime-Aware Post-Processing of Monsoon Rainfall (MoES / NCMRWF)

Real data only: ERA5 truth + archived GFS previous-runs forecasts (both via Open-Meteo), 46 districts, Feb 2024 → Sep 2026.

```
cd pipeline
python fetch.py            # stage 1: writes data/raw/<district>.csv (resumable)
python run.py              # stages 2-6: regimes, corrections, heavy-rain prob, verification (+ --fast for B=100 bootstrap)
python make_report.py      # outputs/VERIFICATION_REPORT.md + outputs/dashboard/*.json
cd .. && python -c "import sys;sys.path.insert(0,'tests');import test_core as t;[getattr(t,n)() for n in dir(t) if n.startswith('test_')]"
```

| Module | Role |
|---|---|
| `districts.py` | 46 districts (8 core, 10 coastal, 6 orographic, 4 Himalayan, 4 NE, 6 Gangetic, 3 arid, 5 interior) |
| `regimes.py` | Rajeevan active/break index, depression proxy, forecast-time regime prediction |
| `correct.py` | Global/regime quantile mapping, regularised GBM comparator, heavy-rain logistic |
| `verify.py` | RMSE, POD/FAR/CSI/ETS, station-neighbourhood FSS, Brier/AUC, block bootstrap |

Outputs are in `outputs/` (`results.json`, per-lead prediction CSVs, `VERIFICATION_REPORT.md`, `dashboard/`).
See the report for results and limitations; no number is hand-entered.

## Dashboard & deployment
`dashboard/` is a static Next.js app reading `dashboard/public/data/*.json` (regenerate with `python pipeline/export_web.py` after re-running the pipeline).

Live: https://sih26080-monsoon.vercel.app. The Vercel project is connected to this repo (production branch `main`, Root Directory `dashboard`), so every push to `main` redeploys. Do not run `vercel deploy` from inside `dashboard/` any more: with Root Directory set it would look for `dashboard/dashboard`; deploy from the repo root or just push.
