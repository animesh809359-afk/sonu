"""Classification metrics and the error matrix in Das et al. layout
(rows = classified, columns = reference)."""
from __future__ import annotations

import numpy as np
from sklearn.metrics import roc_auc_score


def evaluate(y, pred, score=None):
    y, pred = np.asarray(y, int), np.asarray(pred, int)
    hh = int(((y == 0) & (pred == 0)).sum())   # healthy classified healthy
    hd = int(((y == 0) & (pred == 1)).sum())   # healthy classified diseased
    dh = int(((y == 1) & (pred == 0)).sum())
    dd = int(((y == 1) & (pred == 1)).sum())
    n = hh + hd + dh + dd
    pa0 = hh / (hh + hd) if hh + hd else np.nan
    pa1 = dd / (dh + dd) if dh + dd else np.nan
    ua0 = hh / (hh + dh) if hh + dh else np.nan
    ua1 = dd / (hd + dd) if hd + dd else np.nan
    oa = (hh + dd) / n
    pe = ((hh + hd) * (hh + dh) + (dh + dd) * (hd + dd)) / n ** 2
    kappa = (oa - pe) / (1 - pe) if pe < 1 else np.nan
    f1_0 = 2 * pa0 * ua0 / (pa0 + ua0) if (pa0 + ua0) else np.nan
    f1_1 = 2 * pa1 * ua1 / (pa1 + ua1) if (pa1 + ua1) else np.nan
    auc = np.nan
    if score is not None and len(np.unique(y)) == 2:
        s = np.asarray(score, float)
        if np.isfinite(s).all():
            auc = roc_auc_score(y, s)
    return {"HH": hh, "HD": hd, "DH": dh, "DD": dd, "N": n, "OA": oa,
            "BA": 0.5 * (pa0 + pa1), "kappa": kappa, "AUC": auc,
            "PA_H": pa0, "PA_D": pa1, "UA_H": ua0, "UA_D": ua1,
            "F1_H": f1_0, "F1_D": f1_1}


def summarise(per_rep):
    """Mean and SD over repeats of a list of metric dicts (pooled within repeat)."""
    keys = ["OA", "BA", "kappa", "AUC", "PA_H", "PA_D", "UA_H", "UA_D", "F1_H", "F1_D"]
    out = {k: float(np.nanmean([m[k] for m in per_rep])) for k in keys}
    out["BA_SD"] = float(np.std([m["BA"] for m in per_rep], ddof=1)) if len(per_rep) > 1 else np.nan
    for k in ("HH", "HD", "DH", "DD", "N"):
        out[k] = int(sum(m[k] for m in per_rep))
    out["repeats"] = len(per_rep)
    return out
