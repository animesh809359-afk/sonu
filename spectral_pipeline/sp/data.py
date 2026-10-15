"""Step 0 - data preparation and audit."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

import numpy as np
import pandas as pd


@dataclass
class Dataset:
    meta: pd.DataFrame            # one row per spectrum (leaf)
    wl_full: np.ndarray           # all wavelengths in the file
    R_full: np.ndarray            # n x len(wl_full) reflectance (0-1)
    y: np.ndarray                 # 1 = positive (diseased), 0 = negative (healthy)
    groups: np.ndarray            # plot id per spectrum
    dates: np.ndarray | None
    audit: dict = field(default_factory=dict)


def _wavelength_columns(columns, regex):
    pat = re.compile(regex)
    wl_cols, wls = [], []
    for c in columns:
        m = pat.match(str(c).strip())
        if m:
            wl_cols.append(c)
            wls.append(float(m.group(1)))
    return wl_cols, np.array(wls)


def load(cfg: dict) -> Dataset:
    d = cfg["data"]
    f = d["file"]
    if f is None:
        raise ValueError("config: data.file is not set")
    if str(f).lower().endswith((".xlsx", ".xls", ".xlsm")):
        df = pd.read_excel(f, sheet_name=d["sheet"] or 0)
    else:
        df = pd.read_csv(f)
    wl_cols, wls = _wavelength_columns(df.columns, d["wavelength_regex"])
    if len(wl_cols) < 50:
        raise ValueError(f"only {len(wl_cols)} wavelength columns recognised; "
                         "check data.wavelength_regex")
    order = np.argsort(wls)
    wl_cols = [wl_cols[i] for i in order]
    wls = wls[order]
    R = df[wl_cols].to_numpy(dtype=float)
    if np.nanmax(R) > 2.0:          # stored as percent
        R = R / 100.0
    meta = df.drop(columns=wl_cols).copy()

    neg, pos = cfg["classes"]["negative"], cfg["classes"]["positive"]
    raw = meta[d["class_col"]]
    cmap = {str(k): v for k, v in (d["class_map"] or {}).items()}
    labels = raw.astype(str).map(cmap) if cmap else raw.astype(str)
    if labels.isna().any() or not set(labels.unique()) <= {neg, pos}:
        bad = sorted(set(raw.astype(str)[labels.isna() | ~labels.isin([neg, pos])]))
        raise ValueError(f"class values not mapped to {neg}/{pos}: {bad[:10]}")
    meta["Class"] = labels.values
    y = (labels.values == pos).astype(int)
    groups = meta[d["plot_col"]].astype(str).values
    dates = meta[d["date_col"]].astype(str).values if d.get("date_col") else None

    # plots must be pure (one class per plot)
    mix = meta.groupby(d["plot_col"])["Class"].nunique()
    if (mix > 1).any():
        raise ValueError(f"plots with both classes: {list(mix[mix > 1].index)[:10]}")

    audit = audit_data(meta, R, wls, y, groups, cfg)
    return Dataset(meta=meta.reset_index(drop=True), wl_full=wls, R_full=R, y=y,
                   groups=groups, dates=dates, audit=audit)


def audit_data(meta, R, wls, y, groups, cfg) -> dict:
    neg, pos = cfg["classes"]["negative"], cfg["classes"]["positive"]
    plot_col = cfg["data"]["plot_col"]
    counts = []
    for lab, cls in ((0, neg), (1, pos)):
        m = y == lab
        counts.append({"Class": cls, "Plots": int(len(np.unique(groups[m]))),
                       "Spectra": int(m.sum())})
    per_plot = (meta.assign(_g=groups).groupby("_g")
                .agg(Class=("Class", "first"), Spectra=("Class", "size"))
                .reset_index().rename(columns={"_g": plot_col}))
    try:
        per_plot["_k"] = pd.to_numeric(per_plot[plot_col])
        per_plot = per_plot.sort_values("_k").drop(columns="_k")
    except (ValueError, TypeError):
        per_plot = per_plot.sort_values(plot_col)
    dist = (per_plot.groupby(["Class", "Spectra"]).size()
            .reset_index(name="Plots"))
    finite = np.isfinite(R)
    dup = int(pd.DataFrame(R).duplicated().sum())
    checks = [
        ("Missing values in spectra", int((~finite).sum()),
         "PASS" if finite.all() else "FAIL"),
        ("Reflectance range (all bands)",
         f"{np.nanmin(R):.3f} - {np.nanmax(R):.3f}",
         "PASS" if np.nanmin(R) >= 0 and np.nanmax(R) <= 1 else "FLAG"),
        ("Duplicate spectra (identical rows)", dup, "PASS" if dup == 0 else "FLAG"),
        ("Plots containing both classes", 0, "PASS"),
        ("Wavelength step (nm)", f"{np.median(np.diff(wls)):.1f}",
         "PASS" if np.allclose(np.diff(wls), 1) else "FLAG"),
    ]
    return {"counts": counts, "per_plot": per_plot, "per_plot_dist": dist,
            "checks": checks, "n": int(len(y)), "n_bands_file": int(len(wls)),
            "wl_min": float(wls.min()), "wl_max": float(wls.max()),
            "imbalance": float((y == 1).sum() / max((y == 0).sum(), 1))}
