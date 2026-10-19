"""Steps 11-14 - feature extraction: K1 band reflectance, K2 continuum-removed
absorption parameters, K3 vegetation indices, K4 derivatives + edge parameters.
Every feature carries metadata (type, series, wavelength) so the combined pool
(K1+K2+K3+K4) can be analysed by the same four-tier machinery."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class FeatureSet:
    X: np.ndarray
    meta: pd.DataFrame      # name, type, series, position, group, description

    @property
    def names(self):
        return self.meta["name"].to_numpy()

    def subset(self, mask):
        mask = np.asarray(mask)
        return FeatureSet(self.X[:, mask], self.meta[mask].reset_index(drop=True))

    @staticmethod
    def concat(sets):
        return FeatureSet(np.hstack([s.X for s in sets]),
                          pd.concat([s.meta for s in sets], ignore_index=True))


def _meta(names, ftype, series, position, desc=None):
    n = len(names)
    return pd.DataFrame({"name": names, "type": [ftype] * n,
                         "series": series if isinstance(series, (list, np.ndarray)) else [series] * n,
                         "position": position, "description": desc if desc is not None else [""] * n})


# ------------------------------------------------------------------ K1
def k1_bands(spec, guard=True, raw=False):
    m = ~spec.excluded
    if guard:
        m &= ~spec.guard["R"]
    wl = spec.wl[m]
    X = (spec.R_raw if raw else spec.R)[:, m]
    suffix = " (raw)" if raw else ""
    names = [f"R{int(w)}{suffix}" for w in wl]
    return FeatureSet(X, _meta(names, "K0 raw" if raw else "K1 band", "Rraw" if raw else "R", wl.astype(float)))


# ------------------------------------------------------------------ K2
def upper_hull(x, y):
    """Upper convex hull (monotone chain); returns hull y interpolated at x."""
    pts = []
    for i in range(len(x)):
        while len(pts) >= 2:
            (x1, y1), (x2, y2) = pts[-2], pts[-1]
            if (x2 - x1) * (y[i] - y1) - (y2 - y1) * (x[i] - x1) >= 0:
                pts.pop()
            else:
                break
        pts.append((x[i], y[i]))
    hx, hy = zip(*pts)
    return np.interp(x, hx, hy)


def continuum_removed(R, wl, lo, hi):
    m = (wl >= lo) & (wl <= hi)
    x = wl[m]
    CR = np.empty((R.shape[0], m.sum()))
    for i in range(R.shape[0]):
        CR[i] = R[i, m] / upper_hull(x, R[i, m])
    return x, CR


def cr_parameters(x, CR):
    depthcurve = 1 - CR
    imin = depthcurve.argmax(1)
    depth = depthcurve.max(1)
    pos = x[imin]
    area = depthcurve.sum(1) * np.median(np.diff(x))
    width = np.empty(len(CR))
    sym = np.empty(len(CR))
    for i in range(len(CR)):
        half = depthcurve[i] >= depth[i] / 2
        a = b = imin[i]
        while a > 0 and half[a - 1]:
            a -= 1
        while b < len(x) - 1 and half[b + 1]:
            b += 1
        width[i] = x[b] - x[a] + 1
        tot = depthcurve[i].sum()
        sym[i] = depthcurve[i, :imin[i] + 1].sum() / tot if tot > 0 else np.nan
    return {"depth": depth, "position": pos.astype(float), "area": area,
            "width": width, "symmetry": sym}


def k2_continuum(spec, windows):
    cols, names, desc, curves = [], [], [], {}
    for name, lo, hi in windows:
        x, CR = continuum_removed(spec.R, spec.wl, lo, hi)
        curves[name] = (x, CR)
        p = cr_parameters(x, CR)
        for k in ("depth", "position", "area", "width", "symmetry"):
            cols.append(p[k])
            names.append(f"{name} {k}")
            desc.append(f"{k} of the continuum-removed feature {lo}-{hi} nm")
    fs = FeatureSet(np.column_stack(cols), _meta(names, "K2 continuum", list(names), np.nan, desc))
    return fs, curves


# ------------------------------------------------------------------ K3
# (name, full name, equation as computed, reference, function of R(lambda))
VI_TABLE = [
    ("WI", "Water Index", "R900 / R970", "Peñuelas et al., 1997", lambda R: R(900) / R(970)),
    ("mCARI1", "Modified Chlorophyll Absorption in Reflectance Index 1",
     "1.2[2.5(R761 − R651) − 1.3(R761 − R581)]", "Haboudane et al., 2004",
     lambda R: 1.2 * (2.5 * (R(761) - R(651)) - 1.3 * (R(761) - R(581)))),
    ("MTVI1", "Modified Triangular Vegetation Index 1", "1.2[1.2(R761 − R581) − 2.5(R651 − R581)]",
     "Haboudane et al., 2004", lambda R: 1.2 * (1.2 * (R(761) - R(581)) - 2.5 * (R(651) - R(581)))),
    ("MTVI2", "Modified Triangular Vegetation Index 2",
     "1.5[1.2(R761 − R581) − 2.5(R651 − R581)] / √[(2R761 + 1)² − (6R761 − 5√R651) − 0.5]",
     "Haboudane et al., 2004",
     lambda R: 1.5 * (1.2 * (R(761) - R(581)) - 2.5 * (R(651) - R(581))) /
     np.sqrt((2 * R(761) + 1) ** 2 - (6 * R(761) - 5 * np.sqrt(R(651))) - 0.5)),
    ("SR900", "Simple Ratio Index 900", "R900 / R680", "Jordan, 1969", lambda R: R(900) / R(680)),
    ("SR850", "Simple Ratio Index 850", "R850 / R680", "Jordan, 1969", lambda R: R(850) / R(680)),
    ("GNDVI", "Green NDVI", "(R850 − R580) / (R850 + R580)", "Gitelson and Merzlyak, 1996",
     lambda R: (R(850) - R(580)) / (R(850) + R(580))),
    ("PRI", "Photochemical Reflectance Index", "(R531 − R570) / (R531 + R570)", "Gamon et al., 1992",
     lambda R: (R(531) - R(570)) / (R(531) + R(570))),
    ("RARSa", "Ratio Analysis of Reflectance Spectra, chlorophyll a", "R675 / R700",
     "Chappelle et al., 1992", lambda R: R(675) / R(700)),
    ("RARSb", "Ratio Analysis of Reflectance Spectra, chlorophyll b", "R675 / (R700 × R650)",
     "Chappelle et al., 1992", lambda R: R(675) / (R(700) * R(650))),
    ("RARSc", "Ratio Analysis of Reflectance Spectra, carotenoids", "R750 / R700",
     "Chappelle et al., 1992", lambda R: R(750) / R(700)),
    ("PSSRa", "Pigment Specific Simple Ratio a", "R800 / R680", "Blackburn, 1998", lambda R: R(800) / R(680)),
    ("NDVI780", "Normalized Difference Vegetation Index 780", "(R780 − R670) / (R780 + R670)",
     "Raun et al., 2001", lambda R: (R(780) - R(670)) / (R(780) + R(670))),
    ("SIPI", "Structure Insensitive Pigment Index", "(R800 − R445) / (R800 − R680)",
     "Peñuelas et al., 1995", lambda R: (R(800) - R(445)) / (R(800) - R(680))),
    ("NCPI", "Normalized Chlorophyll Pigment Ratio Index", "(R670 − R450) / (R670 + R450)",
     "Peñuelas et al., 1994", lambda R: (R(670) - R(450)) / (R(670) + R(450))),
    ("NPQI", "Normalized Phaeophytinization Index", "(R415 − R435) / (R415 + R435)",
     "Barnes et al., 1992", lambda R: (R(415) - R(435)) / (R(415) + R(435))),
    ("PSRI", "Plant Senescence Reflectance Index", "(R680 − R500) / R750",
     "Merzlyak et al., 1999", lambda R: (R(680) - R(500)) / R(750)),
    ("WI/ND", "Ratio of WI and NDVI", "(R900 / R970) / [(R900 − R680) / (R900 + R680)]",
     "Peñuelas et al., 1997",
     lambda R: (R(900) / R(970)) / ((R(900) - R(680)) / (R(900) + R(680)))),
    ("TCARI", "Transformed Chlorophyll Absorption in Reflectance Index",
     "3[(R700 − R670) − 0.2(R700 − R550)(R700 / R670)]", "Haboudane et al., 2002",
     lambda R: 3 * ((R(700) - R(670)) - 0.2 * (R(700) - R(550)) * (R(700) / R(670)))),
    ("VIGreen", "Green Vegetation Index", "(R760 − R550) / (R760 + R550)", "Gitelson et al., 2002",
     lambda R: (R(760) - R(550)) / (R(760) + R(550))),
    ("RVS1", "Red-Edge Vegetation Stress Index 1", "R651 + R750", "Merton, 1998",
     lambda R: R(651) + R(750)),
    ("RVS2", "Red-Edge Vegetation Stress Index 2", "(R651 + R750) / (R651 − R750)", "Merton, 1998",
     lambda R: (R(651) + R(750)) / (R(651) - R(750))),
    ("TVI", "Triangle Vegetation Index", "0.5[120(R761 − R581) − 200(R651 − R581)]",
     "Broge and Leblanc, 2001", lambda R: 0.5 * (120 * (R(761) - R(581)) - 200 * (R(651) - R(581)))),
    ("RDVI", "Renormalized Difference Vegetation Index", "(R761 − R651) / √(R761 + R651)",
     "Roujean and Breon, 1995", lambda R: (R(761) - R(651)) / np.sqrt(R(761) + R(651))),
    ("NDVI850", "Normalized Difference Vegetation Index 850", "(R850 − R651) / (R850 + R651)",
     "Raun et al., 2001", lambda R: (R(850) - R(651)) / (R(850) + R(651))),
    ("SR761", "Simple Ratio Index 761", "R761 / R651", "Jordan, 1969", lambda R: R(761) / R(651)),
    ("NDVI761", "Normalized Difference Vegetation Index 761", "(R761 − R651) / (R761 + R651)",
     "Raun et al., 2001", lambda R: (R(761) - R(651)) / (R(761) + R(651))),
    ("PPR", "Plant Pigment Ratio", "R550 / R450", "Metternicht, 2003", lambda R: R(550) / R(450)),
    ("NWI2", "Normalized Water Index 2", "(R970 − R850) / (R970 + R850)", "Babar et al., 2006",
     lambda R: (R(970) - R(850)) / (R(970) + R(850))),
    ("NRI", "Nitrogen Reflectance Index", "(R570 − R670) / (R570 + R670)", "Bausch and Duke, 1996",
     lambda R: (R(570) - R(670)) / (R(570) + R(670))),
    ("ARI", "Anthocyanin Reflectance Index", "1/R550 − 1/R700", "Gitelson et al., 2001",
     lambda R: 1 / R(550) - 1 / R(700)),
]


def band_lookup(R, wl):
    def f(lam):
        return R[:, int(np.argmin(np.abs(wl - lam)))]
    return f


def k3_indices(spec):
    Rf = band_lookup(spec.R, spec.wl)
    cols = [fn(Rf) for _, _, _, _, fn in VI_TABLE]
    names = [v[0] for v in VI_TABLE]
    desc = [f"{v[1]}: {v[2]} ({v[3]})" for v in VI_TABLE]
    return FeatureSet(np.column_stack(cols), _meta(names, "K3 index", list(names), np.nan, desc))


# ------------------------------------------------------------------ K4
EDGE_NAMES = [
    "Db (blue-edge amplitude)", "λb (blue-edge position, nm)", "SDb (blue-edge area)",
    "Dy (yellow-edge amplitude)", "λy (yellow-edge position, nm)", "SDy (yellow-edge area)",
    "Dr = REV (red-edge amplitude)", "λr = REP (red-edge position, nm)", "SDr (red-edge area)",
    "Rg (green peak reflectance)", "λg (green peak position, nm)",
    "Ro (red well reflectance)", "λo (red well position, nm)",
    "REP, linear 4-point (nm)", "Rg/Ro", "(Rg − Ro)/(Rg + Ro)", "SDr/SDb", "SDr/SDy",
    "(SDr − SDb)/(SDr + SDb)", "(SDr − SDy)/(SDr + SDy)",
]


def edge_parameters(spec):
    wl, D1, R = spec.wl, spec.D1, spec.R

    def win(a, b):
        return (wl >= a) & (wl <= b)
    out = {}
    for tag, (a, b), fn in (("b", (490, 530), np.argmax), ("y", (550, 582), np.argmin),
                            ("r", (680, 760), np.argmax)):
        m = win(a, b)
        i = fn(D1[:, m], axis=1)
        out["D" + tag] = D1[:, m][np.arange(len(R)), i]
        out["λ" + tag] = wl[m][i].astype(float)
        out["SD" + tag] = D1[:, m].sum(1)
    m = win(510, 560)
    i = R[:, m].argmax(1)
    out["Rg"], out["λg"] = R[:, m][np.arange(len(R)), i], wl[m][i].astype(float)
    m = win(640, 680)
    i = R[:, m].argmin(1)
    out["Ro"], out["λo"] = R[:, m][np.arange(len(R)), i], wl[m][i].astype(float)
    Rl = band_lookup(R, wl)
    rre = (Rl(670) + Rl(780)) / 2
    out["REPlin"] = 700 + 40 * (rre - Rl(700)) / (Rl(740) - Rl(700))
    cols = [out["Db"], out["λb"], out["SDb"], out["Dy"], out["λy"], out["SDy"],
            out["Dr"], out["λr"], out["SDr"], out["Rg"], out["λg"], out["Ro"], out["λo"],
            out["REPlin"], out["Rg"] / out["Ro"], (out["Rg"] - out["Ro"]) / (out["Rg"] + out["Ro"]),
            out["SDr"] / out["SDb"], out["SDr"] / out["SDy"],
            (out["SDr"] - out["SDb"]) / (out["SDr"] + out["SDb"]),
            (out["SDr"] - out["SDy"]) / (out["SDr"] + out["SDy"])]
    desc = ["Gong et al. (2002)"] * 13 + ["Guyot & Baret (1988)"] + ["ratio (Gong et al. 2002)"] * 6
    return FeatureSet(np.column_stack(cols), _meta(EDGE_NAMES, "K4 edge", list(EDGE_NAMES), np.nan, desc))


def k4_derivative_bands(spec, guard=True, which="D1"):
    m = ~spec.excluded
    if guard:
        m &= ~spec.guard[which]
    wl = spec.wl[m]
    X = {"D1": spec.D1, "D2": spec.D2, "D3": spec.D3}[which][:, m]
    return FeatureSet(X, _meta([f"{which}_{int(w)}" for w in wl], f"K4 {which} band", which, wl.astype(float)))


# ------------------------------------------------------------------ extended set (plot-average analysis)
CR_EXTRA = ["left area", "right area", "depth/area"]


def _pf():
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))
    import plotavg_features as pf
    return pf


def k2_continuum_ext(spec, windows):
    """8 parameters per window: depth, position, area, width, symmetry (= left area / area), left area, right area, depth/area."""
    cols, names, desc, curves = [], [], [], {}
    for name, lo, hi in windows:
        x, CR = continuum_removed(spec.R, spec.wl, lo, hi)
        curves[name] = (x, CR)
        p = cr_parameters(x, CR)
        BD = 1 - CR
        imin = BD.argmax(1)
        step = np.median(np.diff(x))
        left = np.array([BD[i, :imin[i] + 1].sum() for i in range(len(CR))]) * step
        extra = {"left area": left, "right area": p["area"] - left,
                 "depth/area": np.where(p["area"] > 0, p["depth"] / np.where(p["area"] > 0, p["area"], 1), np.nan)}
        for k in ("depth", "position", "area", "width", "symmetry"):
            cols.append(p[k])
            names.append(f"{name} {k}")
            desc.append(f"{k} of the continuum-removed feature {lo}-{hi} nm")
        for k in CR_EXTRA:
            cols.append(extra[k])
            names.append(f"{name} {k}")
            desc.append(f"{k} of the continuum-removed feature {lo}-{hi} nm")
    return FeatureSet(np.column_stack(cols), _meta(names, "K2 continuum", list(names), np.nan, desc)), curves


def vi_definitions(cfg):
    if cfg.get("features", {}).get("extended"):
        pf = _pf()
        return [(v[0], v[1], v[2], v[3]) for v in pf.VI]
    return [v[:4] for v in VI_TABLE]


def k3_indices_ext(spec):
    pf = _pf()
    D = pf.indices(spec.R, spec.wl)
    desc = [f"{v[1]}: {v[2]} ({v[3]})" for v in pf.VI]
    return FeatureSet(D.to_numpy(float), _meta(list(D.columns), "K3 index", list(D.columns), np.nan, desc))


EDGE_EXTRA = ["REIP, Lagrangian interpolation (nm)", "REIP, linear extrapolation (nm)", "Red-edge slope (R750 − R700)/50"]


def edge_parameters_ext(spec):
    base = edge_parameters(spec)
    pf = _pf()
    re = pf.red_edge(spec.R, spec.D1, spec.wl)
    X = np.column_stack([re["REIP, Lagrangian interpolation (nm)"], re["REIP, linear extrapolation (nm)"],
                         re["Red-edge slope (R750 − R700)/50 (1/nm)"]])
    extra = FeatureSet(X, _meta(EDGE_EXTRA, "K4 edge", list(EDGE_EXTRA), np.nan,
                                ["Dawson & Curran (1998)", "Cho & Skidmore (2006)", "Filella & Peñuelas (1994)"]))
    return FeatureSet.concat([base, extra])


def build_all(spec, cfg):
    """All feature groups G0-G6 used by K5 and Part C."""
    if cfg.get("features", {}).get("extended"):
        return build_all_ext(spec, cfg)
    k1 = k1_bands(spec)
    k2, curves = k2_continuum(spec, cfg["cr_windows"])
    k3 = k3_indices(spec)
    edge = edge_parameters(spec)
    d1 = k4_derivative_bands(spec)
    d1_all = k4_derivative_bands(spec, guard=False)
    k4 = FeatureSet.concat([d1, edge])
    groups = {
        "G0": ("Full spectrum (raw reflectance)", k1_bands(spec, guard=False, raw=True)),
        "G1": ("K1 band reflectance", k1),
        "G2": ("K2 continuum-removed parameters", k2),
        "G3": ("K3 vegetation indices", k3),
        "G4": ("K4 derivatives + edge parameters", k4),
        "G5": ("K1–K4 combined pool", FeatureSet.concat([k1, k2, k3, k4])),
        "G6": ("K4 incl. guard-zone bands (artefact test)", FeatureSet.concat([d1_all, edge])),
    }
    return {"K1": k1, "K2": k2, "K3": k3, "K4edge": edge, "K4d1": d1,
            "K4": k4, "D2": k4_derivative_bands(spec, which="D2"),
            "cr_curves": curves, "groups": groups}


def build_all_ext(spec, cfg):
    """Extended pool: reflectance + 8 continuum-removal parameters × 6 windows + 86 indices + first, second and third
    derivative bands + 23 red-edge / edge parameters (all from spec.R, i.e. raw reflectance when feature_source = raw)."""
    k1 = k1_bands(spec)
    k2, curves = k2_continuum_ext(spec, cfg["cr_windows"])
    k3 = k3_indices_ext(spec)
    edge = edge_parameters_ext(spec)
    d1, d2, d3 = (k4_derivative_bands(spec, which=w) for w in ("D1", "D2", "D3"))
    k4 = FeatureSet.concat([d1, d2, d3, edge])
    all_d = FeatureSet.concat([k4_derivative_bands(spec, guard=False, which=w) for w in ("D1", "D2", "D3")] + [edge])
    groups = {
        "G0": ("Full spectrum (raw reflectance)", k1_bands(spec, guard=False, raw=True)),
        "G1": ("K1 band reflectance", k1),
        "G2": ("K2 continuum-removed parameters", k2),
        "G3": ("K3 vegetation indices", k3),
        "G4": ("K4 derivatives + edge parameters", k4),
        "G5": ("K1–K4 combined pool", FeatureSet.concat([k1, k2, k3, k4])),
        "G6": ("K4 incl. guard-zone bands (artefact test)", all_d),
    }
    return {"K1": k1, "K2": k2, "K3": k3, "K4edge": edge, "K4d1": d1, "K4": k4, "D2": d2, "D3": d3,
            "cr_curves": curves, "groups": groups}
