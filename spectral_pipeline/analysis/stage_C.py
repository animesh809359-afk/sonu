"""Stage C: the four-tier analysis applied to the combined feature pool
(K1 band reflectance + K2 continuum-removed parameters + K3 vegetation indices
+ K4 first-derivative bands and edge parameters), CART and RF as Tier-2
selectors, J-M, QDA, nested validation on identical folds."""
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
pool = FE["groups"]["G5"][1]

# ---- exact / numerical duplicates in the pool (would make covariances singular)
Z = (pool.X - pool.X.mean(0)) / pool.X.std(0)
scalar = np.where(pool.meta["position"].isna())[0]          # CR, VI, edge features
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
poolC = pool.subset(keep)
types = poolC.meta["type"].replace({"K1 band": "K1 band reflectance", "K2 continuum": "K2 continuum removal",
                                    "K3 index": "K3 vegetation index", "K4 D1 band": "K4 first-derivative band",
                                    "K4 edge": "K4 edge parameter"})
poolC.meta["type"] = types.values
fourtier.log(f"Part C pool: {pool.X.shape[1]} features, {len(drop)} duplicates removed → {poolC.X.shape[1]}")

Cres = fourtier.run(poolC, y, groups, F, C, "Part C (combined pool)", collinear_guard=True, mixed=True)
Cres["pool_size_raw"] = pool.X.shape[1]
Cres["pool_dups"] = pd.DataFrame(dup_rows)
Cres["pool_meta"] = poolC.meta
Cres["qda_failures"] = list(fourtier.QDA_FAILURES)

# ---- composition by feature type
t1 = Cres["tier1"]
comp = t1.groupby("type").agg(Features=("name", "size"), Tier1_significant=("sig", "sum"))
for sname, lst in Cres["sets"].items():
    comp[sname] = t1.set_index("name").loc[lst, "type"].value_counts().reindex(comp.index).fillna(0).astype(int).values
Cres["composition"] = comp.reset_index().rename(columns={"type": "Feature type", "Tier1_significant": "Tier-1 significant"})
ty = dict(zip(t1["name"], t1["type"]))
fold_comp = []
for meth in ("CART", "RF"):
    lists = Cres["fold_selections"][meth]
    tot = sum(len(l) for l in lists)
    vc = pd.Series([ty[v] for l in lists for v in l]).value_counts()
    for k, v in vc.items():
        fold_comp.append({"Selector": meth, "Feature type": k, "Selected (50 training sets)": int(v),
                          "Share": v / tot})
Cres["fold_composition"] = pd.DataFrame(fold_comp)
Cres["runtime_min"] = (time.time() - T0) / 60
save(Cres, "partC")
fourtier.log(f"Stage C done in {Cres['runtime_min']:.1f} min")
print(Cres["pool_dups"])
print(Cres["composition"])
print(Cres["sets"])
print(Cres["tier3"].drop(columns="List"))
print(Cres["validation"][["Pipeline", "Scheme", "BA", "BA_SD", "AUC", "kappa"]])
print(Cres["wilcoxon"])
print(Cres["stability"]["index"].T)
print(Cres["collinear_skipped"], len(Cres["qda_failures"]))
