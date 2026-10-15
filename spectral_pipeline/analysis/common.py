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

CFG_PATH = ROOT / "configs" / "whiterust_all_dates.yaml"
WORK = Path(os.environ.get("SP_WORK", ROOT / "work"))
RAW_DIR = Path(os.environ.get("SP_RAW", ROOT / "raw_data"))
WORK.mkdir(parents=True, exist_ok=True)


def cfg():
    c = load_config(CFG_PATH)
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
