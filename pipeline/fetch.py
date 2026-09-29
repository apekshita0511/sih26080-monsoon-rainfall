"""Stage 1: fetch real ERA5 truth + archived GFS previous-runs forecasts for all districts.
Output: data/raw/<district>.csv  (date, obs, fc_d1, fc_d2, fc_d3) daily totals in IST, mm."""
import sys, time, io
from pathlib import Path
import requests, pandas as pd
from districts import DISTRICTS

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
START, END = "2024-02-01", sys.argv[1] if len(sys.argv) > 1 else "2026-09-27"
ARCH = "https://archive-api.open-meteo.com/v1/archive"
PREV = "https://previous-runs-api.open-meteo.com/v1/forecast"

def get(url, params, tries=8):
    for i in range(tries):
        try:
            r = requests.get(url, params=params, timeout=90)
        except requests.exceptions.RequestException:
            time.sleep(10 * (i + 1)); continue
        if r.status_code == 200:
            return r.json()
        if r.status_code == 429 or r.status_code >= 500:
            time.sleep(15 * (i + 1)); continue
        raise RuntimeError(f"{r.status_code} {r.text[:200]}")
    raise RuntimeError("retries exhausted")

def fetch_one(name, lat, lon):
    base = dict(latitude=lat, longitude=lon, start_date=START, end_date=END, timezone="Asia/Kolkata")
    a = get(ARCH, {**base, "daily": "precipitation_sum"})
    obs = pd.Series(a["daily"]["precipitation_sum"], index=pd.to_datetime(a["daily"]["time"]), name="obs")
    f = get(PREV, {**base, "models": "gfs_seamless",
                   "hourly": "precipitation_previous_day1,precipitation_previous_day2,precipitation_previous_day3"})
    h = pd.DataFrame(f["hourly"]); h["time"] = pd.to_datetime(h["time"]); h = h.set_index("time")
    # daily sum only over days with all 24 hourly values present, else NaN
    g = h.groupby(h.index.normalize())
    daily = g.sum(min_count=24)
    daily.columns = ["fc_d1", "fc_d2", "fc_d3"]
    return pd.concat([obs, daily], axis=1).rename_axis("date")

if __name__ == "__main__":
    RAW.mkdir(parents=True, exist_ok=True)
    for name, lat, lon, tag in DISTRICTS:
        out = RAW / f"{name}.csv"
        if out.exists():
            continue
        df = fetch_one(name, lat, lon)
        df.to_csv(out)
        print(f"{name:20s} rows={len(df)} obs_nan={df.obs.isna().sum()} fc1_nan={df.fc_d1.isna().sum()}", flush=True)
        time.sleep(2)
