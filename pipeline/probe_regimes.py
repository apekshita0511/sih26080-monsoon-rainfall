import json, collections
from common import *
from regimes import *

P = load_panel()
for k in P:
    print(k, int(P[k].isna().sum().sum()), P[k].shape)
rm = RegimeModel(P, 1, [2024])
idx = P["obs"].index
te = (idx.year == 2025) & (idx.month >= 6) & (idx.month <= 9)
print(json.dumps(rm.report(te), indent=1))
print("pred train", collections.Counter(rm.assign()[rm.train].ravel()))
print("pred test ", collections.Counter(rm.assign()[te].ravel()))
print("oracle test", collections.Counter(rm.assign(True)[te].ravel()))
