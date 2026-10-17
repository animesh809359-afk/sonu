"""Configuration: one YAML file per dataset.

Everything that changes between datasets (file, class labels, plot structure,
spectral range, guard zones, absorption windows) lives in the YAML file.
Settings, seeds and validation design are defaults here and normally stay as
they are, so results stay comparable across growth stages, leaf positions and
crops.
"""
from __future__ import annotations

import copy
from pathlib import Path

import yaml

DEFAULTS = {
    "title": "Healthy vs diseased",
    "subtitle": "",
    "author": "",
    "data": {
        "file": None,            # .xlsx or .csv
        "sheet": None,           # sheet name for .xlsx
        "plot_col": "Plot",
        "class_col": None,       # column holding the class (or a code mapped below)
        "class_map": {},         # raw value -> "Healthy" / "Diseased"
        "date_col": None,        # optional: measurement date (used in K0 / K3b checks)
        "id_cols": [],           # extra descriptor columns copied to the fold sheet
        "subset": None,          # optional {column: value} filter applied after cleaning (e.g. {Date: 11-02-2026})
        "subset_label": None,    # human-readable name of the subset
        "subset_family": None,   # sentence describing the set of subset analyses (README)
        "leaf_level_files": None,  # optional workbooks with leaf-level columns (L3, L5, LL), matched to the labelled files
        "wavelength_regex": r"^\D{0,3}(\d{3,4}(?:\.0+)?)$",
    },
    "classes": {"negative": "Healthy", "positive": "Diseased"},
    "spectra": {
        "keep_range": [400, 2500],      # analysed range (nm); outside = sensor noise
        "joins": [1000, 1800],          # ASD detector joins (last band of detector)
        "splice_fit_nm": 10,            # line fitted to the 10 nm before a join
        "canopy": False,                # True -> mask water-absorption bands
        "water_bands": [[1350, 1430], [1800, 1950], [2350, 2500]],
        "sg_smooth": [11, 2],
        "sg_d1": [15, 2],
        "sg_d2": [21, 2],
        "guard": {
            "R": [[990, 1010], [1795, 1835]],
            "D1": [[988, 1012], [1793, 1837]],
            "D2": [[985, 1015], [1790, 1840]],
        },
        "regions": [
            ["Blue", 400, 499], ["Green", 500, 599], ["Red", 600, 679],
            ["Red edge", 680, 759], ["NIR", 760, 1349], ["Water band I", 1350, 1430],
            ["SWIR-1", 1431, 1799], ["Water band II", 1800, 1950],
            ["SWIR-2", 1951, 2349], ["SWIR-2 end", 2350, 2500],
        ],
    },
    "cr_windows": [
        ["CR1 blue", 400, 548], ["CR2 red", 548, 765], ["CR3 water 970", 914, 1069],
        ["CR4 water 1200", 1069, 1258], ["CR5 water 1450", 1258, 1721],
        ["CR6 water 1940", 1721, 2304],
    ],
    "tier1": {"alpha": 0.05, "mixed_model": True, "mixed_model_jobs": 4},
    "cart": {"minsplit": 20, "minbucket": 7, "cp": 0.01, "maxcompete": 0,
             "maxsurrogate": 0, "split": "gini", "prior": [0.5, 0.5],
             "xval_folds": 10},
    "rf": {"n_estimators": 500, "n_estimators_importance": 1000,
           "max_features": "sqrt", "sampling_strategy": "all",
           "replacement": True, "bootstrap": False, "random_state": 42,
           "n_jobs": -1, "peak_min_sep_nm": 10, "top_k": [17, 10]},
    "validation": {"v1_folds": 10, "v1_seed": 42, "v3_folds": 10,
                   "v3_seeds": [101, 102, 103, 104, 105],
                   "v4_fraction": 0.30, "v4_splits": 10, "v4_seed": 2026,
                   "v5_by": "auto"},   # transfer test: "Date" (leave-one-date-out), "Variety" or "auto"
    "jm": {"threshold": 1.90, "threshold_strict": 1.94},
    "k3b": {"grid_nm": 5, "refine_nm": 5},
    "k5": {"top_n": 15, "max_abs_r": 0.9},
    "combined": {"dedupe_abs_r": 0.99999, "collinear_abs_r": 0.999},
    "output": {"dir": "output", "stem": "analysis"},
    "naming": "short",   # "full" = no codes (V1-V5, K1-K4) in workbook text, sheet names and figures
    "fast": False,   # True = reduced repeats / trees (for smoke tests only)
}


def _merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def load_config(path: str | Path) -> dict:
    path = Path(path)
    with open(path) as fh:
        user = yaml.safe_load(fh) or {}
    cfg = _merge(DEFAULTS, user)
    cfg["_config_path"] = str(path.resolve())
    base = path.resolve().parent
    if cfg["data"]["file"] and not Path(cfg["data"]["file"]).is_absolute():
        cfg["data"]["file"] = str((base / cfg["data"]["file"]).resolve())
    if not Path(cfg["output"]["dir"]).is_absolute():
        cfg["output"]["dir"] = str((base / cfg["output"]["dir"]).resolve())
    if cfg["fast"]:
        cfg["validation"]["v3_seeds"] = cfg["validation"]["v3_seeds"][:2]
        cfg["validation"]["v4_splits"] = 3
        cfg["rf"]["n_estimators"] = 100
        cfg["rf"]["n_estimators_importance"] = 200
        cfg["tier1"]["mixed_model"] = False
    return cfg
