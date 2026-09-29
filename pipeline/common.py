from pathlib import Path
import numpy as np, pandas as pd
from districts import DISTRICTS, CORE

ROOT = Path(__file__).resolve().parent.parent
RAW, OUT = ROOT / "data" / "raw", ROOT / "outputs"
NAMES = [d[0] for d in DISTRICTS]
TAGS = ["core", "coastal", "orographic", "himalayan", "northeast", "gangetic", "arid", "interior"]
TAG = {d[0]: d[3] for d in DISTRICTS}
LATLON = np.array([[d[1], d[2]] for d in DISTRICTS])
CORE_IDX = [NAMES.index(n) for n in CORE]
DROP_LAST = 2                      # final days: ERA5T / latest-run lag, partial-day signature
THRESH = [2.5, 15.6, 64.5]         # IMD: light+, moderate+, heavy+
HEAVY_THR = [15.6, 64.5, 115.6]    # exceedance-probability thresholds (115.6 = IMD very heavy)
REGIMES = ["active", "break", "normal", "depression", "orographic", "coastal"]
FSS_RADII = [0, 250, 500]          # km, station-neighbourhood
SPLITS = {"A": ([2024], 2025), "B": ([2024, 2025], 2026)}   # (train seasons, test season)
LEADS = [1, 2, 3]


def load_panel():
    frames = {n: pd.read_csv(RAW / f"{n}.csv", parse_dates=["date"]).set_index("date") for n in NAMES}
    idx = frames[NAMES[0]].index[:-DROP_LAST]
    return {k: pd.DataFrame({n: frames[n][k].reindex(idx) for n in NAMES}) for k in ["obs", "fc_d1", "fc_d2", "fc_d3"]}


def haversine_km():
    la, lo = np.radians(LATLON[:, 0]), np.radians(LATLON[:, 1])
    a = np.sin((la[:, None] - la[None]) / 2) ** 2 + np.cos(la[:, None]) * np.cos(la[None]) * np.sin((lo[:, None] - lo[None]) / 2) ** 2
    return 6371 * 2 * np.arcsin(np.sqrt(a))
