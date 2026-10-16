"""Step 8 - validation design. Identical folds are used by every step.

V1  leaf-level stratified 10-fold CV (paper protocol; may be optimistic)
V3  plot-grouped stratified k-fold CV x 5 repeats (seeds 101-105); k = 10, or the number of
    plots of the smaller class when that is lower (every test fold must contain both classes)
V4  hold-out of 30 % of plots (per class) x 10 splits (default_rng(2026))
V5  transfer: leave one date out on new plots, or leave one variety out (single-date subsets)
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold, StratifiedKFold


def n_group_folds(y, groups, k_max=10):
    """Number of plot-grouped folds: at most k_max and at most the number of plots of the smaller class."""
    y = np.asarray(y)
    groups = np.asarray(groups)
    return int(min(k_max, len(np.unique(groups[y == 0])), len(np.unique(groups[y == 1]))))


def group_folds(y, groups, k, seed):
    """Plot-grouped stratified k-fold split in which every test fold contains plots of both classes.
    scikit-learn's StratifiedGroupKFold is used when it satisfies this; otherwise the plots of each class
    are shuffled and dealt round-robin to the k folds (stratified group assignment)."""
    y = np.asarray(y)
    groups = np.asarray(groups)
    idx = np.arange(len(y))
    sgk = StratifiedGroupKFold(k, shuffle=True, random_state=seed)
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        splits = list(sgk.split(idx, y, groups))
    if all(len(np.unique(y[te])) == 2 for _, te in splits):
        return splits, "StratifiedGroupKFold"
    rng = np.random.default_rng(seed)
    fold_of = {}
    for c in (0, 1):
        plots = rng.permutation(np.unique(groups[y == c]))
        for i, p in enumerate(plots):
            fold_of[p] = i % k
    f = np.array([fold_of[g] for g in groups])
    return [(idx[f != j], idx[f == j]) for j in range(k)], "stratified group assignment (round-robin per class)"


def make_folds(y, groups, cfg):
    v = cfg["validation"]
    n = len(y)
    idx = np.arange(n)
    out = {"V1": [], "V3": [], "V4": []}
    k3 = n_group_folds(y, groups, v["v3_folds"])
    out["v3_k"] = k3
    out["v3_method"] = set()
    table = pd.DataFrame({"row": idx, "plot": groups, "y": y})

    skf = StratifiedKFold(v["v1_folds"], shuffle=True, random_state=v["v1_seed"])
    col = np.zeros(n, int)
    for k, (tr, te) in enumerate(skf.split(idx, y)):
        out["V1"].append({"train": tr, "test": te, "rep": 0, "fold": k})
        col[te] = k + 1
    table["V1_fold"] = col

    for r, seed in enumerate(v["v3_seeds"]):
        splits, how = group_folds(y, groups, k3, seed)
        out["v3_method"].add(how)
        col = np.zeros(n, int)
        for k, (tr, te) in enumerate(splits):
            assert not set(groups[tr]) & set(groups[te])
            out["V3"].append({"train": tr, "test": te, "rep": r, "fold": k})
            col[te] = k + 1
        table[f"V3_rep{r + 1}_fold"] = col

    rng = np.random.default_rng(v["v4_seed"])
    plots0 = np.unique(groups[y == 0])
    plots1 = np.unique(groups[y == 1])
    k0 = max(1, int(round(v["v4_fraction"] * len(plots0))))
    k1 = max(1, int(round(v["v4_fraction"] * len(plots1))))
    for s in range(v["v4_splits"]):
        test_plots = set(rng.choice(plots0, k0, replace=False)) | set(rng.choice(plots1, k1, replace=False))
        te_mask = np.isin(groups, list(test_plots))
        out["V4"].append({"train": idx[~te_mask], "test": idx[te_mask], "rep": s, "fold": 0})
        table[f"V4_split{s + 1}_test"] = te_mask.astype(int)
    out["table"] = table
    out["v4_plots"] = (k0, k1)
    out["v3_method"] = "; ".join(sorted(out["v3_method"]))
    return out


def pooled_by_rep(folds, scheme):
    """Group fold indices of a scheme by repeat (V3: 10 folds per repeat)."""
    reps = {}
    for i, f in enumerate(folds[scheme]):
        reps.setdefault(f["rep"], []).append(i)
    return reps


def add_lodo(folds, dates, groups, y=None, min_train=5):
    """V5 - leave one date out on new plots: for every V4 split and every date,
    train on the other dates' leaves of the training plots, test on the held-out
    date's leaves of the test plots (unseen date AND unseen plots)."""
    dates = np.asarray(dates)
    udates = list(dict.fromkeys(dates))
    out, dropped = [], []
    for s, f4 in enumerate(folds["V4"]):
        test_plots = set(groups[f4["test"]])
        for d in udates:
            is_tp = np.isin(groups, list(test_plots))
            tr = np.where((dates != d) & ~is_tp)[0]
            te = np.where((dates == d) & is_tp)[0]
            if y is not None and (len(te) == 0 or min((y[tr] == 0).sum(), (y[tr] == 1).sum()) < min_train):
                # the held-out date has no leaves of the test plots, or the training set lacks a class
                dropped.append({"split": s + 1, "date": d, "n_test": int(len(te)),
                                "train_healthy": int((y[tr] == 0).sum()), "train_diseased": int((y[tr] == 1).sum())})
                continue
            out.append({"train": tr, "test": te, "rep": s, "fold": udates.index(d), "date": d})
    folds["V5_dropped"] = dropped
    folds["V5"] = out
    folds["V5_dates"] = udates
    return folds


def add_transfer(folds, dates, varieties, groups, by="auto", y=None):
    """V5 transfer test. by = "Date": leave one date out on the V4 test plots (as add_lodo);
    by = "Variety": train on the other varieties, test on all leaves of the held-out variety
    (its plots are new by construction). "auto" = Date when the data hold more than one date."""
    dates = np.asarray(dates)
    varieties = np.asarray(varieties)
    if by == "auto":
        by = "Date" if len(np.unique(dates)) > 1 else "Variety"
    if by == "Date":
        folds = add_lodo(folds, dates, groups, y)
    else:
        levels = list(dict.fromkeys(sorted(varieties)))
        out = []
        for k, lev in enumerate(levels):
            tr = np.where(varieties != lev)[0]
            te = np.where(varieties == lev)[0]
            out.append({"train": tr, "test": te, "rep": 0, "fold": k, "date": lev})
        folds["V5"] = out
        folds["V5_dates"] = levels
        folds["V5_dropped"] = []
    folds["V5_by"] = by
    return folds
