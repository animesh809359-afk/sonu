"""Stage C′ (variant of Part C): the four-tier analysis on a pool built from the
RAW reflectance (all 2101 bands, 400–2500 nm, as used in Part A / Das et al.)
+ K2 continuum-removed parameters + K3 vegetation indices + K4 first-derivative
bands and edge parameters. Identical engine, settings, seeds and folds as Part C,
so the two pools can be compared fold by fold."""
from __future__ import annotations

import time

import numpy as np
import pandas as pd

from common import cfg, load, save
from sp import features, fourtier

T0 = time.time()
C = cfg()
D = load("data")
spec, y, groups, F = D["spec"], D["y"], D["groups"], D["folds"]
FE = features.build_all(spec, C)
raw = features.k1_bands(spec, guard=False, raw=True)          # 2101 raw bands, names "R400 (raw)"
pool = features.FeatureSet.concat([raw, FE["K2"], FE["K3"], FE["K4"]])

# exact / numerical duplicates among the scalar features (as in Part C)
Z = (pool.X - pool.X.mean(0)) / pool.X.std(0)
scalar = np.where(pool.meta["position"].isna())[0]
drop, dup_rows = set(), []
for a_i, a in enumerate(scalar):
    for b in scalar[a_i + 1:]:
        if b in drop:
            continue
        r = float(Z[:, a] @ Z[:, b] / len(y))
        if abs(r) >= C["combined"]["dedupe_abs_r"]:
            drop.add(b)
            dup_rows.append({"Kept": pool.names[a], "Removed": pool.names[b], "r": r})
keep = np.array([j not in drop for j in range(pool.X.shape[1])])
poolR = pool.subset(keep)
poolR.meta["type"] = poolR.meta["type"].replace({
    "K0 raw": "Raw reflectance band", "K2 continuum": "K2 continuum removal", "K3 index": "K3 vegetation index",
    "K4 D1 band": "K4 first-derivative band", "K4 edge": "K4 edge parameter"}).values
fourtier.log(f"Part C′ pool: {pool.X.shape[1]} features, {len(drop)} duplicates removed → {poolR.X.shape[1]}")

R = fourtier.run(poolR, y, groups, F, C, "Part C′ (raw + K2 + K3 + K4)", collinear_guard=True, mixed=True)
R["pool_size_raw"] = pool.X.shape[1]
R["pool_dups"] = pd.DataFrame(dup_rows)
R["pool_meta"] = poolR.meta
R["qda_failures"] = list(fourtier.QDA_FAILURES)
t1 = R["tier1"]
comp = t1.groupby("type").agg(Features=("name", "size"), Tier1_significant=("sig", "sum"))
for sname, lst in R["sets"].items():
    comp[sname] = t1.set_index("name").loc[lst, "type"].value_counts().reindex(comp.index).fillna(0).astype(int).values
R["composition"] = comp.reset_index().rename(columns={"type": "Feature type", "Tier1_significant": "Tier-1 significant"})
ty = dict(zip(t1["name"], t1["type"]))
fold_comp = []
for meth in ("CART", "RF"):
    lists = R["fold_selections"][meth]
    tot = sum(len(l) for l in lists)
    for k, v in pd.Series([ty[v] for l in lists for v in l]).value_counts().items():
        fold_comp.append({"Selector": meth, "Feature type": k, "Selected (50 training sets)": int(v), "Share": v / tot})
R["fold_composition"] = pd.DataFrame(fold_comp)
R["runtime_min"] = (time.time() - T0) / 60
save(R, "partCR")
fourtier.log(f"Stage C′ done in {R['runtime_min']:.1f} min")
print(R["composition"])
print(R["sets"])
print(R["tier3"][["Set", "Features", "JM"]])
print(R["validation"][["Pipeline", "Scheme", "BA", "BA_SD", "AUC"]])
print(R["stability"]["index"].T)
for c in R["checks"]:
    print(c)
