"""Shared paths and helpers for the white-rust all-dates analysis."""
from __future__ import annotations

import os
import pickle
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sp.config import load_config  # noqa: E402

CFG_PATH = Path(os.environ.get("SP_CONFIG", ROOT / "configs" / "whiterust_all_dates.yaml"))
WORK = Path(os.environ.get("SP_WORK", ROOT / "work"))
RAW_DIR = Path(os.environ.get("SP_RAW", ROOT / "raw_data"))
WORK.mkdir(parents=True, exist_ok=True)


def cfg():
    c = load_config(CFG_PATH if CFG_PATH.is_absolute() else ROOT / CFG_PATH)
    c["tier1"]["mixed_model_jobs"] = 4
    return c


def save(obj, name):
    with open(WORK / f"{name}.pkl", "wb") as fh:
        pickle.dump(obj, fh, protocol=pickle.HIGHEST_PROTOCOL)


def load(name):
    with open(WORK / f"{name}.pkl", "rb") as fh:
        return pickle.load(fh)


def region_of(wl, regions):
    for name, a, b in regions:
        if a <= wl <= b:
            return f"{name} ({a}–{b})"
    return ""


def contiguous(mask, wl):
    """Contiguous runs of a boolean mask -> list of (start, end, n, value)."""
    out = []
    start = 0
    for i in range(1, len(mask) + 1):
        if i == len(mask) or mask[i] != mask[start]:
            out.append((float(wl[start]), float(wl[i - 1]), i - start, bool(mask[start])))
            start = i
    return out


def nearest(wl_list, w):
    wl_list = np.asarray(wl_list, float)
    i = int(np.argmin(np.abs(wl_list - w)))
    return wl_list[i], abs(wl_list[i] - w)


def subset_mask(meta, C):
    """Rows of `meta` that belong to the configured subset (all rows when no subset is set)."""
    sub = C["data"].get("subset") or {}
    m = np.ones(len(meta), bool)
    for col, val in sub.items():
        m &= meta[col].astype(str).to_numpy() == str(val)
    return m


def subset_label(C):
    return C["data"].get("subset_label") or "all dates, growth stages and varieties combined"


def present_dates(D):
    """Dates present in the (subset) data, in file order."""
    return list(dict.fromkeys(D["dates"]))


def v3_label(F):
    """'k-fold × r' label of the nested plot-grouped CV."""
    reps = len({f["rep"] for f in F["V3"]})
    return f"{F.get('v3_k', 10)}-fold × {reps} = {len(F['V3'])} folds"


def v5_label(F, short=False):
    """Description of the V5 transfer test."""
    by = F.get("V5_by", "Date")
    if by == "Date":
        return "new date + plots" if short else "leave-one-date-out on new plots"
    return "new variety" if short else "leave-one-variety-out (train on the other varieties)"


def v5_level(F):
    return "Held-out date" if F.get("V5_by", "Date") == "Date" else "Held-out variety"
