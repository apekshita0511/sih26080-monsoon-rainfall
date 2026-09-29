"""Compact web data from outputs/: per-district series + summary. Run after make_report.py."""
import json, shutil
import pandas as pd
from common import *

WEB = ROOT / "dashboard" / "public" / "data"
WEB.mkdir(parents=True, exist_ok=True)
for split in ("A", "B"):
    df = pd.read_csv(OUT / f"predictions_{split}_lead1.csv")
    out = {"dates": sorted(df.date.unique().tolist()), "regimes": REGIMES, "d": {}}
    for n, g in df.groupby("district"):
        g = g.sort_values("date")
        out["d"][n] = dict(obs=g.obs.round(1).tolist(), raw=g.raw.round(1).tolist(), gq=g.global_qm.round(1).tolist(),
                           rq=g.regime_qm.round(1).tolist(), gbm=g.regime_gbm.round(1).tolist(),
                           reg=[REGIMES.index(r) for r in g.regime], p15=g["p_ge_15.6"].round(3).tolist(),
                           p64=g["p_ge_64.5"].round(3).tolist())
    (WEB / f"series_{split}.json").write_text(json.dumps(out, separators=(",", ":")))
shutil.copy(OUT / "dashboard" / "summary.json", WEB / "summary.json")
shutil.copy(OUT / "dashboard" / "districts.json", WEB / "districts.json")
print({p.name: p.stat().st_size // 1024 for p in WEB.iterdir()})
