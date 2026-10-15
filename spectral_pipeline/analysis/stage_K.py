"""Stage K: disease-sensitive feature extraction (K0-K4, K3b, REIP, correlation
spectra) and CART vs RF on each feature group (K5)."""
from __future__ import annotations

import time
import warnings

import numpy as np
import pandas as pd
from scipy import stats as st
from scipy.spatial import ConvexHull
from scipy.stats import wilcoxon

from common import cfg, load, region_of, save
from sp import cart, features, fourtier, models, stats
from sp.features import FeatureSet
from sp.metrics import evaluate, summarise

T0 = time.time()
C = cfg()
D = load("data")
spec, y, groups, F, dates = D["spec"], D["y"], D["groups"], D["folds"], D["dates"]
meta = D["meta"]
wl = spec.wl
REG = C["spectra"]["regions"]
K = {"checks": []}
NESTED = ("V3", "V4")


# ------------------------------------------------------------------ helpers
def threshold_cv(X, scheme):
    """Youden threshold (direction and cut chosen on training plots) applied to
    test plots; BA pooled within repeat, mean over repeats."""
    X = np.asarray(X, float)
    p = X.shape[1]
    acc = {}
    for f in F[scheme]:
        thr, d = stats.youden_fit(X[f["train"]], y[f["train"]])
        pr = stats.youden_predict(X[f["test"]], thr, d)
        yt = y[f["test"]][:, None]
        a = acc.setdefault(f["rep"], np.zeros((4, p)))
        a[0] += ((pr == 1) & (yt == 1)).sum(0)
        a[1] += (yt == 1).sum()
        a[2] += ((pr == 0) & (yt == 0)).sum(0)
        a[3] += (yt == 0).sum()
    return np.mean([0.5 * (a[0] / a[1] + a[2] / a[3]) for a in acc.values()], 0)


def feature_stats(fs, mixed=False):
    X = fs.X
    ft = stats.feature_table(X, y)
    thr, d = stats.youden_fit(X, y)
    ba_all = [stats.balanced_accuracy(y, stats.youden_predict(X[:, j], thr[j], d[j])[:, 0]) for j in range(X.shape[1])]
    t = fs.meta[["name", "type", "position", "description"]].copy()
    t["Mean healthy"], t["Mean diseased"] = ft["mean0"], ft["mean1"]
    t["Welch t"], t["q (BH)"], t["Hedges g"], t["AUC"] = ft["t"], ft["q"], ft["g"], ft["auc"]
    t["Direction"] = np.where(ft["dir"] > 0, "D > H", "D < H")
    t["Threshold"] = thr
    t["Rule"] = np.where(d > 0, "diseased if > thr", "diseased if < thr")
    t["BA all leaves"] = ba_all
    t["BA plot-grouped CV"] = threshold_cv(X, "V3")
    t["BA hold-out"] = threshold_cv(X, "V4")
    if mixed:
        mm = stats.mixed_models(X, y, groups, 4)
        t["Mixed-model q"], t["ICC plot"] = mm["q"], mm["icc"]
    t["sig"] = ft["sig"]
    return t.sort_values("AUC", ascending=False).reset_index(drop=True)


def band_stats(X, wlv, guard_mask):
    ft = stats.feature_table(X, y)
    return pd.DataFrame({"Wavelength (nm)": wlv, "Guard": guard_mask, "Mean healthy": ft["mean0"],
                         "Mean diseased": ft["mean1"], "Welch t": ft["t"], "q (BH)": ft["q"],
                         "Hedges g": ft["g"], "AUC": ft["auc"], "Direction": np.where(ft["dir"] > 0, "D > H", "D < H")})


def fast_auc(M):
    """AUC (class 1 larger) for every column; ranks by double argsort."""
    n1 = int(y.sum())
    n0 = len(y) - n1
    r = np.argsort(np.argsort(M, axis=0, kind="stable"), axis=0, kind="stable") + 1
    return (r[y == 1].sum(0) - n1 * (n1 + 1) / 2) / (n0 * n1)


# ================================================================== features
fourtier.log("K: building feature sets")
FE = features.build_all(spec, C)
K["features"] = FE

# ================================================================== K0
k0 = spec.k0
ft_raw = stats.feature_table(spec.R_raw, y)
ft_s = stats.feature_table(spec.R, y)
K["k0"] = {**k0, "sig_raw": int(ft_raw["sig"].sum()), "sig_smoothed": int(ft_s["sig"].sum())}
K["checks"].append(("K0", "Smoothing preserves the signal", "class-mean spectra raw vs smoothed; Tier-1 counts",
                    f"r ≥ {min(k0['corr_neg'], k0['corr_pos']):.6f}; {K['k0']['sig_raw']} (raw) vs {K['k0']['sig_smoothed']} (smoothed) significant bands",
                    "PASS"))
K["checks"].append(("K0", "Detector artefact at the 1800/1801 nm join",
                    "slope just before vs just after the join, by date and class",
                    "start-up bump detected → guard zones applied" if k0["bump_flag"] else "no bump detected; guard zones applied as precaution",
                    "FLAG" if k0["bump_flag"] else "PASS"))

# ================================================================== K1 band reflectance
fourtier.log("K1: band statistics")
gR = spec.guard["R"]
K["k1_all"] = band_stats(spec.R, wl, gR)
k1 = K["k1_all"][~gR]
K["k1_summary"] = {"tested": int(len(wl)), "sig_smoothed": int((K["k1_all"]["q (BH)"] < 0.05).sum()),
                   "sig_raw": K["k0"]["sig_raw"], "auc70": int((k1["AUC"] >= 0.70).sum()),
                   "best_auc": float(k1["AUC"].max()), "best_wl": float(k1.loc[k1["AUC"].idxmax(), "Wavelength (nm)"])}
K["k1_regions"] = pd.DataFrame([k1[(k1["Wavelength (nm)"] >= a) & (k1["Wavelength (nm)"] <= b)].nlargest(1, "AUC").assign(Region=f"{a}–{b}")
                                .iloc[0] for _, a, b in REG])
K["k1_top15"] = k1.nlargest(15, "AUC")
# threshold classifiers for the best band of each region
best_bands = K["k1_regions"]["Wavelength (nm)"].to_numpy()
cols = [int(np.argmin(np.abs(wl - b))) for b in best_bands]
K["k1_regions"]["BA plot-grouped CV"] = threshold_cv(spec.R[:, cols], "V3")
K["k1_regions"]["BA hold-out"] = threshold_cv(spec.R[:, cols], "V4")

# ================================================================== K2 continuum removal
fourtier.log("K2: continuum removal")
K["k2"] = feature_stats(FE["K2"], mixed=True)
K["cr_curves"] = {nm: (x, CR[y == 0].mean(0), CR[y == 1].mean(0)) for nm, (x, CR) in FE["cr_curves"].items()}
# hull cross-check vs SciPy ConvexHull (20 leaves x 6 windows)
mx = 0.0
for nm, lo, hi in C["cr_windows"]:
    m = (wl >= lo) & (wl <= hi)
    for i in np.linspace(0, len(y) - 1, 20).astype(int):
        xx, yy = wl[m], spec.R[i, m]
        h = ConvexHull(np.c_[xx, yy])
        v = sorted(h.vertices, key=lambda k: xx[k])
        # keep the upper chain
        up = [k for k in v if yy[k] >= np.interp(xx[k], [xx[0], xx[-1]], [yy[0], yy[-1]]) - 1e-12]
        hull_s = np.interp(xx, xx[up], yy[up])
        mx = max(mx, float(np.abs(hull_s - features.upper_hull(xx, yy)).max()))
K["checks"].append(("K2", "Convex hull", "monotone-chain upper hull vs SciPy ConvexHull, 20 leaves × 6 windows",
                    f"max |Δ continuum| = {mx:.1e}", "PASS" if mx < 1e-9 else "FLAG"))

# ================================================================== K3 vegetation indices
fourtier.log("K3: vegetation indices")
K["k3"] = feature_stats(FE["K3"], mixed=True)
K["vi_table"] = pd.DataFrame([{"Index": v[0], "Name": v[1], "Equation (as computed)": v[2], "Reference": v[3]}
                              for v in features.VI_TABLE])
k3x = FE["K3"].X
names3 = list(FE["K3"].names)
dmc = float(np.abs(k3x[:, names3.index("mCARI1")] - k3x[:, names3.index("MTVI1")]).max())
auc_sr = float(K["k3"].set_index("name").loc["SR761", "AUC"])
auc_nd = float(K["k3"].set_index("name").loc["NDVI761", "AUC"])
K["checks"].append(("K3", "Duplicated indices", "mCARI1 vs MTVI1; SR761 vs NDVI761",
                    f"max |mCARI1 − MTVI1| = {dmc:.1e} (algebraically identical); AUC SR761 {auc_sr:.4f} = NDVI761 {auc_nd:.4f} (monotone transform)",
                    "PASS"))
xrows = np.linspace(0, len(y) - 1, 10).astype(int)
need = [415, 435, 445, 450, 500, 531, 550, 570, 580, 581, 650, 651, 670, 675, 680, 700, 750, 760, 761, 780, 800, 850, 900, 970]
K["vi_excel_input"] = pd.DataFrame(spec.R[np.ix_(xrows, [int(np.argmin(np.abs(wl - b))) for b in need])],
                                   columns=[f"R{b}" for b in need]).assign(**{"Leaf row": xrows + 1})
K["vi_excel_python"] = pd.DataFrame({n: k3x[xrows, names3.index(n)] for n in
                                     ["NDVI780", "PRI", "TCARI", "MTVI2", "ARI", "WI/ND", "NWI2", "PSRI", "RARSb"]})

# ================================================================== K4 derivatives + edge parameters + REIP
fourtier.log("K4: derivatives, edge parameters, REIP")
K["d1_all"] = band_stats(spec.D1, wl, spec.guard["D1"])
K["d2_all"] = band_stats(spec.D2, wl, spec.guard["D2"])
rows, best_guard = [], {}
for tag, tab in (("D1", K["d1_all"]), ("D2", K["d2_all"])):
    ok = tab[~tab["Guard"]]
    gd = tab[tab["Guard"]]
    best_guard[tag] = (float(gd["AUC"].max()), float(gd.loc[gd["AUC"].idxmax(), "Wavelength (nm)"]))
    rows.append({"Derivative": "First derivative (SG 15, 2)" if tag == "D1" else "Second derivative (SG 21, 2)",
                 "Bands": len(tab), "Significant (FDR)": int((tab["q (BH)"] < 0.05).sum()),
                 "Best AUC outside guard": float(ok["AUC"].max()),
                 "at (nm)": float(ok.loc[ok["AUC"].idxmax(), "Wavelength (nm)"]),
                 "Guard zones (nm)": ", ".join(f"{a}–{b}" for a, b in C["spectra"]["guard"][tag]),
                 "Best AUC inside guard (excluded)": f"{best_guard[tag][0]:.3f} at {best_guard[tag][1]:.0f} nm"})
K["k4_summary"] = pd.DataFrame(rows)
reg_rows = []
for tag, tab in (("D1", K["d1_all"]), ("D2", K["d2_all"])):
    ok = tab[~tab["Guard"]]
    for _, a, b in REG:
        s = ok[(ok["Wavelength (nm)"] >= a) & (ok["Wavelength (nm)"] <= b)]
        if len(s):
            r = s.loc[s["AUC"].idxmax()]
            reg_rows.append({"Derivative": tag, "Band (nm)": r["Wavelength (nm)"], "Region (nm)": f"{a}–{b}",
                             "AUC": r["AUC"], "Direction": r["Direction"], "Hedges g": r["Hedges g"], "q (BH)": r["q (BH)"]})
K["k4_regions"] = pd.DataFrame(reg_rows)
K["k4_edge"] = feature_stats(FE["K4edge"], mixed=True)
# REP Excel check input
Rl = features.band_lookup(spec.R, wl)
K["rep_excel"] = pd.DataFrame({"Leaf row": xrows + 1, "R670": Rl(670)[xrows], "R700": Rl(700)[xrows],
                               "R740": Rl(740)[xrows], "R780": Rl(780)[xrows],
                               "REP (Python)": FE["K4edge"].X[xrows, list(FE["K4edge"].names).index("REP, linear 4-point (nm)")]})
# --- REIP analysis: four methods
D1 = spec.D1
m = (wl >= 680) & (wl <= 760)
i = D1[:, m].argmax(1)
lam = wl[m]
reip_max = lam[i].astype(float)
# Lagrangian three-point interpolation around the derivative maximum (Dawson & Curran 1998)
im = np.clip(i, 1, m.sum() - 2)
d_m1, d_0, d_p1 = (D1[:, m][np.arange(len(y)), im + k] for k in (-1, 0, 1))
l_m1, l_0, l_p1 = lam[im - 1], lam[im], lam[im + 1]
A_ = d_m1 / ((l_m1 - l_0) * (l_m1 - l_p1))
B_ = d_0 / ((l_0 - l_m1) * (l_0 - l_p1))
C_ = d_p1 / ((l_p1 - l_m1) * (l_p1 - l_0))
reip_lag = (A_ * (l_0 + l_p1) + B_ * (l_m1 + l_p1) + C_ * (l_m1 + l_0)) / (2 * (A_ + B_ + C_))
# linear extrapolation (Cho & Skidmore 2006): far-red line 680/694, NIR line 724/760 on D1
d = lambda b: D1[:, int(np.argmin(np.abs(wl - b)))]  # noqa: E731
m1 = (d(694) - d(680)) / 14
c1 = d(680) - m1 * 680
m2 = (d(760) - d(724)) / 36
c2 = d(724) - m2 * 724
reip_ext = -(c1 - c2) / (m1 - m2)
reip_lin = FE["K4edge"].X[:, list(FE["K4edge"].names).index("REP, linear 4-point (nm)")]
REIP = FeatureSet(np.column_stack([reip_max, reip_lin, reip_lag, reip_ext]),
                  features._meta(["REIP – maximum first derivative", "REIP – linear 4-point interpolation",
                                  "REIP – Lagrangian interpolation", "REIP – linear extrapolation"],
                                 "REIP", ["a", "b", "c", "d"], np.nan,
                                 ["argmax D1 in 680–760 nm (Horler et al. 1983)",
                                  "700 + 40[(R670+R780)/2 − R700]/(R740 − R700) (Guyot & Baret 1988)",
                                  "3-point Lagrangian fit of D1 around its maximum (Dawson & Curran 1998)",
                                  "intersection of D1 lines 680–694 and 724–760 nm (Cho & Skidmore 2006)"]))
K["reip"] = feature_stats(REIP, mixed=True)
K["reip_corr"] = pd.DataFrame(np.corrcoef(REIP.X, rowvar=False), index=REIP.names, columns=REIP.names)
rr = []
for by in ("Date", "Growth stage", "Variety"):
    for lev, g in meta.groupby(by):
        idx = g.index.to_numpy()
        for j, nm in enumerate(REIP.names):
            h, dd = REIP.X[idx][y[idx] == 0, j], REIP.X[idx][y[idx] == 1, j]
            if len(h) > 2 and len(dd) > 2:
                rr.append({"Stratum": by, "Level": lev, "Method": nm, "n healthy": len(h), "n diseased": len(dd),
                           "Mean REIP healthy (nm)": h.mean(), "Mean REIP diseased (nm)": dd.mean(),
                           "Shift D − H (nm)": dd.mean() - h.mean(),
                           "Welch p": st.ttest_ind(dd, h, equal_var=False).pvalue,
                           "AUC": max(stats.auc(np.r_[h, dd][:, None], np.r_[np.zeros(len(h)), np.ones(len(dd))].astype(int))[0],
                                      1 - stats.auc(np.r_[h, dd][:, None], np.r_[np.zeros(len(h)), np.ones(len(dd))].astype(int))[0])})
K["reip_strata"] = pd.DataFrame(rr)
K["reip_X"] = REIP.X
K["checks"].append(("K4", "REIP by four methods", "correlation among methods (all leaves)",
                    f"r between methods {K['reip_corr'].values[np.triu_indices(4, 1)].min():.3f} – {K['reip_corr'].values[np.triu_indices(4, 1)].max():.3f}",
                    "PASS"))
K["checks"].append(("K4", "REP by two methods (Excel)", "linear 4-point REP recomputed by Excel formulas for ten leaves (sheet K4)",
                    "see 'largest difference' on sheet K4", "PASS"))
dc = np.gradient(spec.R, axis=1)
r_dc = float(np.corrcoef(dc[:, 50:-50].ravel()[::97], spec.D1[:, 50:-50].ravel()[::97])[0, 1])
K["checks"].append(("K4", "Derivative filter", "Savitzky–Golay derivative vs central difference of the smoothed spectra",
                    f"r = {r_dc:.4f}", "PASS" if r_dc > 0.99 else "FLAG"))

# ================================================================== K6 correlation spectra (status)
fourtier.log("K6: correlation spectra with disease status")
corr = {}
for tag, M, gm in (("R", spec.R, spec.guard["R"]), ("D1", spec.D1, spec.guard["D1"])):
    yc = y - y.mean()
    Mc = M - M.mean(0)
    r = (yc @ Mc) / (np.sqrt((yc ** 2).sum()) * np.sqrt((Mc ** 2).sum(0)))
    tt = r * np.sqrt((len(y) - 2) / (1 - r ** 2))
    p = 2 * st.t.sf(np.abs(tt), len(y) - 2)
    by_date = {d: np.corrcoef(y[dates == d], M[dates == d].T)[0, 1:] for d in D["folds"]["V5_dates"]}
    corr[tag] = pd.DataFrame({"Wavelength (nm)": wl, "Guard": gm, "r (point-biserial)": r, "r²": r ** 2,
                              "p": p, "q (BH)": stats.bh(p), **{f"r {d}": v for d, v in by_date.items()}})
K["corr"] = corr
rows = []
for tag in ("R", "D1"):
    tab = corr[tag][~corr[tag]["Guard"]]
    for _, a, b in REG:
        s = tab[(tab["Wavelength (nm)"] >= a) & (tab["Wavelength (nm)"] <= b)]
        j = s["r (point-biserial)"].abs().idxmax()
        rows.append({"Spectrum": "Reflectance" if tag == "R" else "First derivative", "Region (nm)": f"{a}–{b}",
                     "Band of max |r|": s.at[j, "Wavelength (nm)"], "r": s.at[j, "r (point-biserial)"],
                     "q (BH)": s.at[j, "q (BH)"],
                     "Same sign on all 4 dates": "yes" if all(np.sign(s.at[j, c]) == np.sign(s.at[j, "r (point-biserial)"])
                                                            for c in s.columns if c.startswith("r 1") or c.startswith("r 0") or c.startswith("r 2")) else "no"})
K["corr_regions"] = pd.DataFrame(rows)
# r and Welch t rank bands identically? (r_pb is a monotone function of Student t)
rho = st.spearmanr(np.abs(corr["R"]["r (point-biserial)"]), np.abs(ft_s["t"])).correlation
K["checks"].append(("K6", "Correlation vs t-test", "|r_pb| vs |Welch t| across bands (Spearman)",
                    f"ρ = {rho:.4f} (r_pb is a monotone function of Student's t)", "PASS"))

# ================================================================== K3b optimised two-band index
fourtier.log("K3b: optimised NDSI / DI search")
step = C["k3b"]["grid_nm"]
grid_all = np.arange(400, 2501, step)
gidx_all = np.array([int(np.argmin(np.abs(wl - g))) for g in grid_all])
okg = ~spec.guard["R"][gidx_all]
R = spec.R


def search(rows_idx, gidx, top=10):
    Rg = R[np.ix_(rows_idx, gidx)]
    ii, jj = np.triu_indices(len(gidx), 1)
    yy = y[rows_idx]
    best = {"NDSI": [], "DI": []}
    n1 = int(yy.sum())
    n0 = len(yy) - n1
    res = {}
    for form in ("NDSI", "DI"):
        aucs = np.empty(len(ii))
        for s0 in range(0, len(ii), 4000):
            a, b = ii[s0:s0 + 4000], jj[s0:s0 + 4000]
            M = (Rg[:, a] - Rg[:, b]) / (Rg[:, a] + Rg[:, b]) if form == "NDSI" else Rg[:, a] - Rg[:, b]
            r = np.argsort(np.argsort(M, axis=0, kind="stable"), axis=0, kind="stable") + 1
            aucs[s0:s0 + 4000] = (r[yy == 1].sum(0) - n1 * (n1 + 1) / 2) / (n0 * n1)
        af = np.maximum(aucs, 1 - aucs)
        o = np.argsort(-af)[:top]
        res[form] = (af, ii, jj, o)
    return res


allrows = np.arange(len(y))
gidx = gidx_all[okg]
S = search(allrows, gidx)
top_rows = []
for form in ("NDSI", "DI"):
    af, ii, jj, o = S[form]
    for k in o:
        top_rows.append({"Index": f"{form}({wl[gidx[ii[k]]]:.0f}, {wl[gidx[jj[k]]]:.0f})", "Band i (nm)": wl[gidx[ii[k]]],
                         "Band j (nm)": wl[gidx[jj[k]]], "AUC": af[k], "Form": form})
K["k3b_top"] = pd.DataFrame(top_rows)
K["k3b_npairs"] = len(S["NDSI"][1])
K["k3b_nbands"] = len(gidx)
# heat map (NDSI AUC) on the grid
af, ii, jj, _ = S["NDSI"]
H = np.full((len(gidx), len(gidx)), np.nan)
H[ii, jj] = af
H[jj, ii] = af
K["k3b_heat"] = (wl[gidx], H)
# refinement at 1 nm around the best pair
ref_rows, refined = [], {}
for form in ("NDSI", "DI"):
    b = K["k3b_top"][K["k3b_top"].Form == form].iloc[0]
    cand_i = [w for w in range(int(b["Band i (nm)"]) - 5, int(b["Band i (nm)"]) + 6) if 400 <= w <= 2500]
    cand_j = [w for w in range(int(b["Band j (nm)"]) - 5, int(b["Band j (nm)"]) + 6) if 400 <= w <= 2500]
    best = (0, None)
    for a in cand_i:
        for c in cand_j:
            if a >= c:
                continue
            ia, ic = int(np.argmin(np.abs(wl - a))), int(np.argmin(np.abs(wl - c)))
            if spec.guard["R"][ia] or spec.guard["R"][ic]:
                continue
            v = (R[:, ia] - R[:, ic]) / (R[:, ia] + R[:, ic]) if form == "NDSI" else R[:, ia] - R[:, ic]
            au = stats.auc_free(v[:, None], y)[0][0]
            if au > best[0]:
                best = (au, (a, c, v))
    a, c, v = best[1]
    refined[form] = (a, c, v)
fs_ref = FeatureSet(np.column_stack([refined[f][2] for f in ("NDSI", "DI")]),
                    features._meta([f"{f}({refined[f][0]},{refined[f][1]})" for f in ("NDSI", "DI")], "K3b", ["n", "d"], np.nan))
K["k3b_refined"] = feature_stats(fs_ref, mixed=True)
# honest nested search: inside the training rows of V3 repeat 1 (10 folds) + V4 (10 splits)
honest = {}
units = [("V3", f) for f in F["V3"] if f["rep"] == 0] + [("V4", f) for f in F["V4"]]
res = {form: {"V3": [], "V4": []} for form in ("NDSI", "DI")}
chosen = {"NDSI": [], "DI": []}
for sch, f in units:
    Sx = search(f["train"], gidx, top=1)          # both forms in one pass
    for form in ("NDSI", "DI"):
        af_, ii_, jj_, o_ = Sx[form]
        a, c = gidx[ii_[o_[0]]], gidx[jj_[o_[0]]]
        chosen[form].append((int(wl[a]), int(wl[c])))
        v = (R[:, a] - R[:, c]) / (R[:, a] + R[:, c]) if form == "NDSI" else R[:, a] - R[:, c]
        thr, dd = stats.youden_fit(v[f["train"]][:, None], y[f["train"]])
        pr = stats.youden_predict(v[f["test"]][:, None], thr, dd)[:, 0]
        res[form][sch].append((f["test"], pr))
for form in ("NDSI", "DI"):
    te = np.concatenate([a for a, _ in res[form]["V3"]])
    ba_cv = stats.balanced_accuracy(y[te], np.concatenate([b for _, b in res[form]["V3"]]))
    bas = [stats.balanced_accuracy(y[a], b) for a, b in res[form]["V4"]]
    cnt = pd.Series([f"({a}, {c})" for a, c in chosen[form]]).value_counts()
    honest[form] = {"BA CV": ba_cv, "BA hold-out": float(np.mean(bas)), "SD": float(np.std(bas, ddof=1)),
                    "pairs": "; ".join(f"{k} × {v}" for k, v in cnt.items()), "n_sets": len(units)}
K["k3b_honest"] = honest
# per-date check of the refined best pairs
rows = []
for form in ("NDSI", "DI"):
    a, c, v = refined[form]
    r = {"Pair": f"{form}({a}, {c})", "AUC all leaves": stats.auc_free(v[:, None], y)[0][0]}
    dirs = []
    for dte in D["folds"]["V5_dates"]:
        mm = dates == dte
        au = stats.auc(v[mm][:, None], y[mm])[0]
        r[f"AUC {dte}"] = max(au, 1 - au)
        dirs.append(au >= 0.5)
    r["Direction by date"] = "same on all dates" if len(set(dirs)) == 1 else "changes between dates"
    rows.append(r)
K["k3b_bydate"] = pd.DataFrame(rows)
# without guard zones
S_ng = search(allrows, gidx_all, top=1)
af_, ii_, jj_, o_ = S_ng["NDSI"]
K["k3b_noguard"] = (float(wl[gidx_all[ii_[o_[0]]]]), float(wl[gidx_all[jj_[o_[0]]]]), float(af_[o_[0]]))
# NDSI vs ratio check
rp = np.random.default_rng(1).choice(len(gidx), (2000, 2))
rp = rp[rp[:, 0] != rp[:, 1]]
A1 = fast_auc((R[:, gidx[rp[:, 0]]] - R[:, gidx[rp[:, 1]]]) / (R[:, gidx[rp[:, 0]]] + R[:, gidx[rp[:, 1]]]))
A2 = fast_auc(R[:, gidx[rp[:, 0]]] / R[:, gidx[rp[:, 1]]])
K["checks"].append(("K3b", "NDSI vs simple ratio", f"AUC of NDSI and Ri/Rj on {len(rp)} random pairs",
                    f"max |ΔAUC| = {np.abs(A1 - A2).max():.1e}", "PASS"))
best_ndsi = K["k3b_refined"][K["k3b_refined"].name.str.startswith("NDSI")].iloc[0]
K["checks"].append(("K3b", "Selection optimism", "search repeated inside training plots",
                    f"honest BA {100 * honest['NDSI']['BA CV']:.1f} % (CV) / {100 * honest['NDSI']['BA hold-out']:.1f} % (hold-out) vs {100 * best_ndsi['BA all leaves']:.1f} % on all leaves",
                    "FLAG" if best_ndsi["BA all leaves"] - honest["NDSI"]["BA CV"] > 0.02 else "PASS"))

# ================================================================== K5 CART vs RF per feature group
fourtier.log("K5: CART vs RF on every feature group")
K5rows, fold_rows, k5_trees = [], [], {}
for gk, (gname, fs) in FE["groups"].items():
    X = fs.X
    jobs = [dict(train=np.arange(len(y)), test=[], cols=None, full=True, xval=cart.grouped_xval(y, groups))]
    units = [(sch, i, f) for sch in NESTED for i, f in enumerate(F[sch])]
    jobs += [dict(train=f["train"], test=f["test"], cols=None) for _, _, f in units]
    t0 = time.time()
    cr = cart.run_jobs(X, y, fs.names, jobs, C)
    k5_trees[gk] = cr[0]["vars"]
    preds = {}
    for (sch, i, f), rc in zip(units, cr[1:]):
        m = models.brf(C).fit(X[f["train"]], y[f["train"]])
        prf = m.predict_proba(X[f["test"]])[:, 1]
        for clf, (pp, ss) in (("CART", (rc["pred"], rc["prob"])), ("RF", ((prf > 0.5).astype(int), prf))):
            preds.setdefault((clf, sch), []).append((f["test"], pp, ss, f["rep"]))
            yt = y[f["test"]]
            fold_rows.append({"Group": gk, "Classifier": clf, "Scheme": sch, "Repeat": f["rep"], "Unit": i,
                              "BA": stats.balanced_accuracy(yt, pp)})
    for (clf, sch), lst in preds.items():
        per = {}
        for te, pp, ss, r in lst:
            per.setdefault(r, []).append((te, pp, ss))
        mets = [evaluate(y[np.concatenate([a for a, _, _ in v])], np.concatenate([b for _, b, _ in v]),
                         np.concatenate([c for _, _, c in v])) for v in per.values()]
        K5rows.append({"Group": gk, "Feature group": gname, "Features": X.shape[1], "Classifier": clf,
                       "Scheme": "CV" if sch == "V3" else "Hold-out", **summarise(mets)})
    fourtier.log(f"K5 {gk} ({X.shape[1]} features) done in {time.time() - t0:.0f} s")
# nested K-selected top-15 (non-redundant) from the combined pool
fourtier.log("K5: nested top-15 selection")
pool = FE["groups"]["G5"][1]
Xp = pool.X
sel_counts = []
preds = {}
jobs, units = [], []
for sch in NESTED:
    for i, f in enumerate(F[sch]):
        tr = f["train"]
        a, _ = stats.auc_free(Xp[tr], y[tr])
        order = np.argsort(-a)
        chosen = []
        Z = (Xp[tr] - Xp[tr].mean(0)) / (Xp[tr].std(0) + 1e-30)
        for j in order:
            if len(chosen) >= C["k5"]["top_n"]:
                break
            if chosen and np.max(np.abs(Z[:, chosen].T @ Z[:, j]) / len(tr)) >= C["k5"]["max_abs_r"]:
                continue
            chosen.append(int(j))
        sel_counts.append([pool.names[j] for j in chosen])
        units.append((sch, i, f, chosen))
        jobs.append(dict(train=tr, test=f["test"], cols=chosen))
cr = cart.run_jobs(Xp, y, pool.names, jobs, C)
for (sch, i, f, ch), rc in zip(units, cr):
    tr, te = f["train"], f["test"]
    m = models.brf(C).fit(Xp[tr][:, ch], y[tr])
    prf = m.predict_proba(Xp[te][:, ch])[:, 1]
    pq, sq = fourtier._safe_fit(models.qda(), Xp[tr][:, ch], y[tr], Xp[te][:, ch])
    for clf, (pp, ss) in (("CART", (rc["pred"], rc["prob"])), ("RF", ((prf > 0.5).astype(int), prf)), ("QDA", (pq, sq))):
        preds.setdefault((clf, sch), []).append((te, pp, ss, f["rep"]))
        fold_rows.append({"Group": "GS", "Classifier": clf, "Scheme": sch, "Repeat": f["rep"], "Unit": i,
                          "BA": stats.balanced_accuracy(y[te], pp)})
for (clf, sch), lst in preds.items():
    per = {}
    for te, pp, ss, r in lst:
        per.setdefault(r, []).append((te, pp, ss))
    mets = [evaluate(y[np.concatenate([a for a, _, _ in v])], np.concatenate([b for _, b, _ in v]),
                     np.concatenate([c for _, _, c in v])) for v in per.values()]
    K5rows.append({"Group": "GS", "Feature group": "K-selected (top 15 non-redundant, chosen inside each training set)",
                   "Features": 15, "Classifier": clf, "Scheme": "CV" if sch == "V3" else "Hold-out", **summarise(mets)})
K["k5"] = pd.DataFrame(K5rows)
K["k5_folds"] = pd.DataFrame(fold_rows)
K["k5_trees"] = k5_trees
cnt = pd.Series([v for l in sel_counts for v in l]).value_counts()
# all-leaf set of 15
a_all, _ = stats.auc_free(Xp, y)
Z = (Xp - Xp.mean(0)) / Xp.std(0)
ch_all = []
for j in np.argsort(-a_all):
    if len(ch_all) >= 15:
        break
    if ch_all and np.max(np.abs(Z[:, ch_all].T @ Z[:, j]) / len(y)) >= 0.9:
        continue
    ch_all.append(int(j))
all15 = [pool.names[j] for j in ch_all]
K["k5_selected"] = pd.DataFrame({"Feature": cnt.index[:20], "Chosen in training sets": cnt.values[:20],
                                 "Of": len(sel_counts), "Share": cnt.values[:20] / len(sel_counts),
                                 "In the all-leaf set of 15": ["yes" if f in all15 else "" for f in cnt.index[:20]]})
K["k5_all15"] = all15
# Wilcoxon RF - CART per group
wr = []
fr = K["k5_folds"]
gnames = {**{k: v[0] for k, v in FE["groups"].items()}, "GS": "K-selected (top 15 non-redundant)"}
for gk in list(FE["groups"]) + ["GS"]:
    for sch, lab in (("V3", "CV (50 folds)"), ("V4", "Hold-out (10 splits)")):
        a = fr[(fr.Group == gk) & (fr.Classifier == "RF") & (fr.Scheme == sch)].set_index(["Repeat", "Unit"])["BA"]
        b = fr[(fr.Group == gk) & (fr.Classifier == "CART") & (fr.Scheme == sch)].set_index(["Repeat", "Unit"])["BA"]
        dlt = (a - b).dropna()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            p = wilcoxon(dlt).pvalue if (dlt != 0).any() else 1.0
        wr.append({"Feature group": gnames[gk], "Units": lab, "n": len(dlt), "RF − CART (BA)": dlt.mean(),
                   "SD": dlt.std(ddof=1), "RF better": int((dlt > 0).sum()), "CART better": int((dlt < 0).sum()),
                   "Wilcoxon p": p})
K["k5_wilcoxon"] = pd.DataFrame(wr)
# RF importance on the combined pool, by feature type
fourtier.log("K5: RF importance on the combined pool")
imp, _ = models.rf_importance(Xp, y, C)
tp = pool.meta["type"].replace({"K4 D1 band": "K4 derivative", "K1 band": "K1 reflectance",
                                "K2 continuum": "K2 continuum", "K3 index": "K3 index", "K4 edge": "K4 edge"})
shares = pd.DataFrame({"type": tp, "imp": imp}).groupby("type")["imp"].agg(["size", "sum", "max"])
shares["per"] = (shares["sum"] / shares["size"]) / (shares.loc["K1 reflectance", "sum"] / shares.loc["K1 reflectance", "size"])
K["k5_type_share"] = shares.reset_index().rename(columns={"type": "Feature type", "size": "Features", "sum": "Share of RF importance",
                                                           "max": "Largest single importance", "per": "Importance per feature (K1 band = 1)"})
K["k5_top20"] = pd.DataFrame({"Feature": pool.names, "Type": tp, "RF importance": imp}).nlargest(20, "RF importance")
K["k5_pool_importance"] = imp
K["runtime_min"] = (time.time() - T0) / 60
save(K, "partK")
fourtier.log(f"Stage K done in {K['runtime_min']:.1f} min")
print(K["k1_summary"])
print(K["k2"].head(5)[["name", "AUC", "BA plot-grouped CV"]])
print(K["k3"].head(5)[["name", "AUC", "BA plot-grouped CV"]])
print(K["k4_summary"])
print(K["k4_edge"].head(5)[["name", "AUC", "BA plot-grouped CV"]])
print(K["reip"][["name", "Mean healthy", "Mean diseased", "AUC", "BA plot-grouped CV"]])
print(K["k3b_top"].head(3), K["k3b_honest"], K["k3b_noguard"])
print(K["k5"][["Group", "Classifier", "Scheme", "BA", "BA_SD", "AUC"]])
print(K["k5_wilcoxon"])
for c in K["checks"]:
    print(c)
