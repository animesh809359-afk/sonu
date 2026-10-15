"""Step 8 - validation design. Identical folds are used by every step.

V1  leaf-level stratified 10-fold CV (paper protocol; may be optimistic)
V3  plot-grouped stratified 10-fold CV x 5 repeats (seeds 101-105)
V4  hold-out of 30 % of plots (per class) x 10 splits (default_rng(2026))
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold, StratifiedKFold


def make_folds(y, groups, cfg):
    v = cfg["validation"]
    n = len(y)
    idx = np.arange(n)
    out = {"V1": [], "V3": [], "V4": []}
    table = pd.DataFrame({"row": idx, "plot": groups, "y": y})

    skf = StratifiedKFold(v["v1_folds"], shuffle=True, random_state=v["v1_seed"])
    col = np.zeros(n, int)
    for k, (tr, te) in enumerate(skf.split(idx, y)):
        out["V1"].append({"train": tr, "test": te, "rep": 0, "fold": k})
        col[te] = k + 1
    table["V1_fold"] = col

    for r, seed in enumerate(v["v3_seeds"]):
        sgk = StratifiedGroupKFold(v["v3_folds"], shuffle=True, random_state=seed)
        col = np.zeros(n, int)
        for k, (tr, te) in enumerate(sgk.split(idx, y, groups)):
            assert not set(groups[tr]) & set(groups[te])
            out["V3"].append({"train": tr, "test": te, "rep": r, "fold": k})
            col[te] = k + 1
        table[f"V3_rep{r + 1}_fold"] = col

    rng = np.random.default_rng(v["v4_seed"])
    plots0 = np.unique(groups[y == 0])
    plots1 = np.unique(groups[y == 1])
    k0 = int(round(v["v4_fraction"] * len(plots0)))
    k1 = int(round(v["v4_fraction"] * len(plots1)))
    for s in range(v["v4_splits"]):
        test_plots = set(rng.choice(plots0, k0, replace=False)) | set(rng.choice(plots1, k1, replace=False))
        te_mask = np.isin(groups, list(test_plots))
        out["V4"].append({"train": idx[~te_mask], "test": idx[te_mask], "rep": s, "fold": 0})
        table[f"V4_split{s + 1}_test"] = te_mask.astype(int)
    out["table"] = table
    out["v4_plots"] = (k0, k1)
    return out


def pooled_by_rep(folds, scheme):
    """Group fold indices of a scheme by repeat (V3: 10 folds per repeat)."""
    reps = {}
    for i, f in enumerate(folds[scheme]):
        reps.setdefault(f["rep"], []).append(i)
    return reps


def add_lodo(folds, dates, groups):
    """V5 - leave one date out on new plots: for every V4 split and every date,
    train on the other dates' leaves of the training plots, test on the held-out
    date's leaves of the test plots (unseen date AND unseen plots)."""
    dates = np.asarray(dates)
    udates = list(dict.fromkeys(dates))
    out = []
    for s, f4 in enumerate(folds["V4"]):
        test_plots = set(groups[f4["test"]])
        for d in udates:
            is_tp = np.isin(groups, list(test_plots))
            tr = np.where((dates != d) & ~is_tp)[0]
            te = np.where((dates == d) & is_tp)[0]
            out.append({"train": tr, "test": te, "rep": s, "fold": udates.index(d), "date": d})
    folds["V5"] = out
    folds["V5_dates"] = udates
    return folds
