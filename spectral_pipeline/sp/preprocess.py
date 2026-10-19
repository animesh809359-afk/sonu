"""Steps 1-2 (K0) - detector splice correction, Savitzky-Golay smoothing and
derivatives, guard zones."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.signal import savgol_filter


@dataclass
class Spectra:
    wl: np.ndarray        # analysed wavelengths (keep_range)
    R_raw: np.ndarray     # raw reflectance, analysed range
    R_sc: np.ndarray      # splice-corrected, unsmoothed
    R: np.ndarray         # splice-corrected + SG smoothed  (K1)
    D1: np.ndarray        # first derivative (per nm)       (K4)
    D2: np.ndarray        # second derivative (per nm)
    guard: dict           # name -> boolean mask over wl (True = inside guard)
    excluded: np.ndarray  # bands excluded from every analysis (canopy water bands)
    k0: dict              # tables for the report
    D3: np.ndarray = None # third derivative (raw feature source only)
    source: str = "smoothed"


def in_ranges(wl, ranges):
    m = np.zeros(len(wl), bool)
    for lo, hi in ranges:
        m |= (wl >= lo) & (wl <= hi)
    return m


def splice_correct(R, wl, joins, fit_nm=10):
    """Additive splice correction: shift each longer-wavelength detector so it
    continues the straight line fitted to the last `fit_nm` bands before the join."""
    R = R.copy()
    offsets = {}
    for j in joins:
        if j < wl.min() or j + 1 > wl.max():
            continue
        fit = (wl > j - fit_nm) & (wl <= j)
        x = wl[fit]
        xm = x.mean()
        Y = R[:, fit]
        slope = ((x - xm) * (Y - Y.mean(1, keepdims=True))).sum(1) / ((x - xm) ** 2).sum()
        pred = Y.mean(1) + slope * (j + 1 - xm)
        idx_next = int(np.argmin(np.abs(wl - (j + 1))))
        off = pred - R[:, idx_next]
        R[:, wl >= j + 1] += off[:, None]
        offsets[j] = off
    return R, offsets


def preprocess(ds, cfg) -> Spectra:
    s = cfg["spectra"]
    wl_full, R_full = ds.wl_full, ds.R_full
    steps = np.unique(np.round(np.diff(wl_full), 6))
    if len(steps) != 1:
        raise ValueError(f"wavelength grid is not regular: steps {steps}")
    dl = float(steps[0])          # 1 nm for ASD exports; SG windows below are in bands (= nm at 1-nm spacing)
    R_sc_full, offsets = splice_correct(R_full, wl_full, s["joins"], s["splice_fit_nm"])
    w, p = s["sg_smooth"]
    Rs_full = savgol_filter(R_sc_full, w, p, axis=1, mode="interp")
    w1, p1 = s["sg_d1"]
    D1_full = savgol_filter(R_sc_full, w1, p1, deriv=1, delta=dl, axis=1, mode="interp")
    w2, p2 = s["sg_d2"]
    D2_full = savgol_filter(R_sc_full, w2, p2, deriv=2, delta=dl, axis=1, mode="interp")

    D3_full = None
    if s.get("feature_source", "smoothed") == "raw":
        # features from RAW reflectance: central finite differences on the 1-nm grid, no splice correction, no smoothing
        D1_full, D2_full, D3_full = finite_differences(R_full)
    lo, hi = s["keep_range"]
    keep = (wl_full >= lo) & (wl_full <= hi)
    wl = wl_full[keep]
    guard = {k: in_ranges(wl, v) for k, v in s["guard"].items()}
    excluded = in_ranges(wl, s["water_bands"]) if s["canopy"] else np.zeros(len(wl), bool)

    y = ds.y
    neg, pos = cfg["classes"]["negative"], cfg["classes"]["positive"]
    k0 = {}
    # splice offsets by class
    rows = []
    for j, off in offsets.items():
        rows.append({"Join": f"{int(j)}/{int(j) + 1} nm",
                     f"Offset {neg} (mean)": off[y == 0].mean(), "SD (neg)": off[y == 0].std(ddof=1),
                     f"Offset {pos} (mean)": off[y == 1].mean(), "SD (pos)": off[y == 1].std(ddof=1)})
    k0["offsets"] = rows

    # date-dependent start-up bump after the second join
    rows = []
    j2 = max([j for j in s["joins"] if j < wl_full.max()], default=None)
    flag = False
    if j2 is not None and ds.dates is not None:
        def slope(Rm, a, b):
            m = (wl_full >= a) & (wl_full <= b)
            x = wl_full[m]
            return np.polyfit(x, Rm[m], 1)[0] * 1e5   # reflectance per 100 000 nm
        diffs_after, diffs_before = [], []
        for d in _ordered_dates(ds.dates):
            md = ds.dates == d
            mh, mdz = md & (y == 0), md & (y == 1)
            if mh.sum() < 2 or mdz.sum() < 2:
                continue
            Rh, Rd = R_sc_full[mh].mean(0), R_sc_full[mdz].mean(0)
            r = {"Date": d,
                 f"Slope {j2 - 14:.0f}-{j2:.0f} {neg}": slope(Rh, j2 - 14, j2),
                 f"Slope {j2 - 14:.0f}-{j2:.0f} {pos}": slope(Rd, j2 - 14, j2),
                 f"Slope {j2 + 1:.0f}-{j2 + 15:.0f} {neg}": slope(Rh, j2 + 1, j2 + 15),
                 f"Slope {j2 + 1:.0f}-{j2 + 15:.0f} {pos}": slope(Rd, j2 + 1, j2 + 15)}
            vals = list(r.values())[1:]
            diffs_before.append(vals[1] - vals[0])
            diffs_after.append(vals[3] - vals[2])
            rows.append(r)
        # flag a start-up bump if, on any date, the spectrum turns upward right
        # after the join although it falls before it, or if the class difference
        # just after the join varies between dates more than just before it
        sign_flip = any(np.sign(list(r.values())[1]) != np.sign(list(r.values())[3]) or
                        np.sign(list(r.values())[2]) != np.sign(list(r.values())[4]) for r in rows)
        if len(diffs_after) >= 2:
            flag = sign_flip or np.ptp(diffs_after) > np.ptp(diffs_before)
    k0["join_slopes"] = rows
    k0["bump_flag"] = bool(flag)

    # noise removed by smoothing, by region (full file range incl. dropped edge)
    regs = [["%d-%d" % (wl_full.min(), lo - 1), wl_full.min(), lo - 1]] if wl_full.min() < lo else []
    regs += [[f"{a}-{b}", a, b] for _, a, b in s["regions"]]
    resid = R_sc_full - Rs_full
    k0["noise"] = [{"Range (nm)": n, "Noise (SD raw - smoothed)":
                    float(resid[:, (wl_full >= a) & (wl_full <= b)].std())}
                   for n, a, b in regs if ((wl_full >= a) & (wl_full <= b)).any()]
    # signal preservation
    k0["corr_neg"] = float(np.corrcoef(R_full[y == 0][:, keep].mean(0), Rs_full[y == 0][:, keep].mean(0))[0, 1])
    k0["corr_pos"] = float(np.corrcoef(R_full[y == 1][:, keep].mean(0), Rs_full[y == 1][:, keep].mean(0))[0, 1])
    k0["max_change"] = float(np.abs(R_full[:, keep].mean(0) - Rs_full[:, keep].mean(0)).max())
    # mean spectra by date (for the join inspection figure)
    if ds.dates is not None:
        k0["date_means"] = {d: R_full[ds.dates == d].mean(0) for d in _ordered_dates(ds.dates)}
        k0["date_means_sc"] = {d: R_sc_full[ds.dates == d].mean(0) for d in _ordered_dates(ds.dates)}
    k0["wl_full"] = wl_full

    raw = s.get("feature_source", "smoothed") == "raw"
    return Spectra(wl=wl, R_raw=R_full[:, keep], R_sc=R_sc_full[:, keep],
                   R=(R_full if raw else Rs_full)[:, keep], D1=D1_full[:, keep], D2=D2_full[:, keep],
                   guard=guard, excluded=excluded, k0=k0,
                   D3=None if D3_full is None else D3_full[:, keep], source="raw" if raw else "smoothed")


def finite_differences(R):
    """First, second and third derivative by central finite differences (Δλ = 1 nm):
    D1 = [R(λ+1) − R(λ−1)]/2, D2 = R(λ+1) − 2R(λ) + R(λ−1), D3 = [R(λ+2) − 2R(λ+1) + 2R(λ−1) − R(λ−2)]/2.
    The one or two end bands without both neighbours take the value of the nearest defined band."""
    n = R.shape[1]
    D1 = np.empty_like(R)
    D2 = np.empty_like(R)
    D3 = np.empty_like(R)
    D1[:, 1:-1] = (R[:, 2:] - R[:, :-2]) / 2
    D2[:, 1:-1] = R[:, 2:] - 2 * R[:, 1:-1] + R[:, :-2]
    D3[:, 2:n - 2] = (R[:, 4:] - 2 * R[:, 3:-1] + 2 * R[:, 1:-3] - R[:, :-4]) / 2
    for D, k in ((D1, 1), (D2, 1), (D3, 2)):
        D[:, :k] = D[:, [k]]
        D[:, n - k:] = D[:, [n - k - 1]]
    return D1, D2, D3


def _ordered_dates(dates):
    import pandas as pd
    u = list(dict.fromkeys(dates))
    try:
        parsed = pd.to_datetime(pd.Series(u), dayfirst=True, errors="raise")
        return [u[i] for i in np.argsort(parsed.values)]
    except (ValueError, TypeError):
        return sorted(u)
