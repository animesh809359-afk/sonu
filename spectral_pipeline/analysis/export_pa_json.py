"""Plot-average analysis: exports the numbers and small tables used by the deck and the Word report (all texts with full names)."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from common import WORK, cfg, load

C = cfg()
D, A, K, Cc, X = load("data"), load("partA"), load("partK"), load("partC"), load("compare")
TXT = json.loads((WORK / "conclusions.json").read_text()) if (WORK / "conclusions.json").exists() else {}
y = D["y"]
nH, nD = int((y == 0).sum()), int((y == 1).sum())


def pct(v, d=1):
    return "–" if v is None or (isinstance(v, float) and np.isnan(v)) else f"{100 * v:.{d}f} %"


def f(v, d=3):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "–"
    if isinstance(v, (int, np.integer)):
        return str(int(v))
    if abs(v) < 1e-3 and v != 0:
        return f"{v:.1e}"
    return f"{v:.{d}f}"


def tab(df, cols, fmt=None):
    fmt = fmt or {}
    rows = [list(cols)]
    for _, r in df.iterrows():
        rows.append([fmt[c](r[c]) if c in fmt else (f(r[c]) if isinstance(r[c], (float, np.floating)) else str(r[c])) for c in cols])
    return rows


def bands(lst):
    return ", ".join(str(v).replace("WV", "") for v in lst)


def vrow(R, p, s):
    return R["validation"].set_index(["Pipeline", "Scheme"]).loc[(p, s)]


J = {"n": len(y), "nH": nH, "nD": nD, "ratio": nD / nH, "n_bands": int(len(D["spec"].wl))}
J["by_date"] = [["Date", "Healthy", "Diseased", "Total"]] + [[d, str(int(r["Healthy"])), str(int(r["Diseased"])), str(int(r.sum()))]
                                                             for d, r in D["audit"]["by_date"].iterrows()]
J["by_stage"] = [["Growth stage", "Healthy", "Diseased"]] + [[s, str(int(r["Healthy"])), str(int(r["Diseased"]))]
                                                             for s, r in D["audit"]["by_stage_total"].iterrows()]
J["by_variety"] = [["Variety", "Healthy", "Diseased"]] + [[s, str(int(r["Healthy"])), str(int(r["Diseased"]))]
                                                          for s, r in D["audit"]["by_variety"].iterrows()]
J["checks0"] = [["Check", "Result", "Status"]] + [[c[0], str(c[1]), c[2]] for c in D["audit"]["checks"]]
J["noise"] = [["Range (nm)", "Noise (SD)", "× 500–699 nm"]] + [[r["Range (nm)"], f"{r['Noise (SD of SG residual)']:.1e}", f"{r['Ratio to 500–699 nm']:.1f}"] for r in D["audit"]["noise"]]
# ---- Part A
t1 = A["tier1"]
J["A"] = {
    "n_sig": A["n_sig"], "tests": [["Test", "Significant bands"]] + [[r["Test"], str(r["Significant bands"])] for _, r in A["tier1_tests"].iterrows()],
    "balanced": A["tier1_balanced"], "ranges": tab(A["tier1_ranges"], ["Range (nm)", "Bands", "Result"]),
    "regions": tab(A["tier1_regions"], ["Region", "Bands", "Welch+FDR significant", "Mixed-model significant", "Band of max |t|", "Max t"],
                   {"Band of max |t|": lambda v: f"{v:.0f}", "Max t": lambda v: f"{v:.1f}"}),
    "cart_name": A["cart_name"], "rf_name": A["rf_name"], "sets": {k: bands(v) for k, v in A["sets"].items()},
    "set_sizes": {k: len(v) for k, v in A["sets"].items()},
    "cart_table": tab(A["cart_table"], ["Band (nm)", "Region", "First used at node", "Welch t", "Bootstrap re-selection (±10 nm)",
                                        "Nested-CV re-selection (±10 nm)", "Mixed model significant"],
                      {"Band (nm)": lambda v: f"{v:.0f}", "Welch t": lambda v: f"{v:.1f}", "First used at node": lambda v: str(int(v)),
                       "Bootstrap re-selection (±10 nm)": pct, "Nested-CV re-selection (±10 nm)": pct,
                       "Region": lambda v: v.split(" (")[0]}),
    "cp": tab(A["cart_full"]["cptable"], ["CP", "nsplit", "rel error", "xerror", "xstd"], {"nsplit": lambda v: str(int(v))}),
    "tier3": tab(A["tier3"], ["Set", "Features", "JM"], {"Features": lambda v: str(int(v)), "JM": lambda v: f"{v:.3f}"}),
    "tier4": tab(A["tier4"], ["Set", "Classifier", "OA", "BA", "PA_H", "PA_D", "kappa", "AUC"],
                 {"OA": pct, "BA": pct, "PA_H": pct, "PA_D": pct, "kappa": lambda v: f"{v:.3f}", "AUC": lambda v: f"{v:.3f}"}),
    "errmat": {k: {kk: (int(vv) if kk in ("HH", "HD", "DH", "DD", "N") else float(vv)) for kk, vv in v.items()} for k, v in A["errmat"].items()},
    "val_qda": tab(A["validation_qda_cart"], ["Scheme", "Priors", "OA", "BA", "BA_SD", "kappa", "PA_H", "PA_D"],
                   {"OA": pct, "BA": pct, "BA_SD": pct, "kappa": lambda v: f"{v:.3f}", "PA_H": pct, "PA_D": pct}),
    "validation": tab(A["validation"], ["Pipeline", "Scheme", "BA", "BA_SD", "AUC", "kappa"],
                      {"BA": pct, "BA_SD": pct, "AUC": lambda v: f"{v:.3f}", "kappa": lambda v: f"{v:.3f}"}),
    "wilcoxon": tab(A["wilcoxon"], ["Comparison", "Units", "Mean difference", "First better", "Second better", "Wilcoxon p"],
                    {"Mean difference": lambda v: f"{100 * v:+.1f} pts", "First better": lambda v: str(int(v)),
                     "Second better": lambda v: str(int(v)), "Wilcoxon p": lambda v: f"{v:.1e}" if v < 0.001 else f"{v:.3f}"}),
    "stability": tab(A["stability"]["index"], ["Method", "Mean features", "Unique features (union)", "Stability index (exact) = all / union",
                                               "Stability index (±10 nm)", "Mean pairwise Jaccard (±10 nm)"],
                     {"Mean features": lambda v: f"{v:.1f}", "Unique features (union)": lambda v: str(int(v))}),
    "rf_checks": tab(A["rf_checks"], ["Check", "Value", "Status"]),
    "sens_range": tab(A["sensitivity_range"], ["Band set", "CART bands", "BA V1", "BA V3 nested", "BA V4 hold-out"],
                      {"BA V1": pct, "BA V3 nested": pct, "BA V4 hold-out": pct, "CART bands": lambda v: str(int(v))}),
    "sens_dups": tab(A["sensitivity_dups"], ["Data", "CART bands", "BA V1", "BA V3", "BA V4"],
                     {"BA V1": pct, "BA V3": pct, "BA V4": pct, "CART bands": lambda v: str(int(v))}),
    "v": {f"{p}|{s}": {"BA": float(vrow(A, p, s)["BA"]), "SD": float(vrow(A, p, s)["BA_SD"]) if vrow(A, p, s)["BA_SD"] == vrow(A, p, s)["BA_SD"] else None,
                        "AUC": float(vrow(A, p, s)["AUC"]), "kappa": float(vrow(A, p, s)["kappa"])}
          for p in ["CART classifier", "RF classifier", "QDA on CART features", "QDA on RF features"] for s in ["V1", "V3", "V4", "V5"]},
    "jm": {r["Set"]: float(r["JM"]) for _, r in A["tier3"].iterrows()},
    "mixed_sig": int(t1["mm_sig"].sum()), "boundary": int(t1["mm_boundary"].sum()),
}
vq = A["validation_qda_cart"]
J["A"]["vq"] = {f"{r['Scheme'].split(' ·')[0]}|{r['Priors'].split(' ')[0]}": float(r["BA"]) for _, r in vq.iterrows()}
# ---- K
k1 = K["k1_summary"]
J["K"] = {
    "k0": {"offsets": [[r["Join"], f"{list(r.values())[1]:.4f}", f"{list(r.values())[3]:.4f}"] for r in K["k0"]["offsets"]],
           "bump": bool(K["k0"]["bump_flag"]), "sig_raw": K["k0"]["sig_raw"], "sig_s": K["k0"]["sig_smoothed"],
           "corr": min(K["k0"]["corr_neg"], K["k0"]["corr_pos"])},
    "k1": k1,
    "k1_regions": tab(K["k1_regions"], ["Region", "Wavelength (nm)", "AUC", "Direction", "Hedges g", "BA plot-grouped CV", "BA hold-out"],
                      {"Wavelength (nm)": lambda v: f"{v:.0f}", "BA plot-grouped CV": pct, "BA hold-out": pct, "Hedges g": lambda v: f"{v:.2f}"}),
}
ft = lambda df, n=8: tab(df.head(n), ["name", "Mean healthy", "Mean diseased", "AUC", "Direction", "BA plot-grouped CV", "BA hold-out"],  # noqa: E731
                         {"BA plot-grouped CV": pct, "BA hold-out": pct, "AUC": lambda v: f"{v:.3f}"})
J["K"]["k2"] = ft(K["k2"])
J["K"]["k3"] = ft(K["k3"], 10)
J["K"]["k4_edge"] = ft(K["k4_edge"])
J["K"]["reip"] = ft(K["reip"], 4)
J["K"]["k4_summary"] = tab(K["k4_summary"], ["Derivative", "Significant (FDR)", "Best AUC outside guard", "at (nm)", "Best AUC inside guard (excluded)"],
                           {"at (nm)": lambda v: f"{v:.0f}", "Significant (FDR)": lambda v: str(int(v))})
J["K"]["k3b_top"] = tab(K["k3b_top"].groupby("Form").head(3), ["Index", "AUC"])
J["K"]["k3b_refined"] = ft(K["k3b_refined"], 2)
J["K"]["k3b_honest"] = K["k3b_honest"]
J["K"]["k3b_npairs"] = int(K["k3b_npairs"])
J["K"]["k3b_noguard"] = list(K["k3b_noguard"])
J["K"]["k3b_jf_refined"] = ft(K["k3b_jf"]["refined"], 2)
J["K"]["k3b_jf_honest"] = K["k3b_jf"]["honest"]
J["K"]["k3b_jf_top"] = tab(K["k3b_jf"]["top"].groupby("Form").head(3), ["Index", "AUC"])
J["K"]["corr_regions"] = tab(K["corr_regions"], ["Spectrum", "Region (nm)", "Band of max |r|", "r", "Same sign on all 4 dates"],
                             {"Band of max |r|": lambda v: f"{v:.0f}", "r": lambda v: f"{v:+.3f}"})
k5 = K["k5"]
J["K"]["k5"] = [["Feature group", "Features", "CART CV", "RF CV", "CART hold-out", "RF hold-out"]]
for g in list(dict.fromkeys(k5["Group"])):
    q = k5[k5.Group == g]
    get = lambda c, s: pct(q[(q.Classifier == c) & (q.Scheme == s)]["BA"].iloc[0]) if len(q[(q.Classifier == c) & (q.Scheme == s)]) else "–"  # noqa: E731
    J["K"]["k5"].append([q["Feature group"].iloc[0], str(int(q["Features"].iloc[0])), get("CART", "CV"), get("RF", "CV"),
                         get("CART", "Hold-out"), get("RF", "Hold-out")])
J["K"]["k5_wilcoxon"] = tab(K["k5_wilcoxon"], ["Feature group", "Units", "RF − CART (BA)", "RF better", "CART better", "Wilcoxon p"],
                            {"RF − CART (BA)": lambda v: f"{100 * v:+.1f} pts", "RF better": lambda v: str(int(v)),
                             "CART better": lambda v: str(int(v)), "Wilcoxon p": lambda v: f"{v:.1e}" if v < 0.001 else f"{v:.3f}"})
J["K"]["k5_share"] = tab(K["k5_type_share"], ["Feature type", "Features", "Share of RF importance", "Importance per feature (K1 band = 1)"],
                         {"Share of RF importance": pct, "Features": lambda v: str(int(v)), "Importance per feature (K1 band = 1)": lambda v: f"{v:.2f}"})
# ---- C (and C′)
def cblock(Cc):
    return {
    "pool_raw": Cc["pool_size_raw"], "n_features": Cc["n_features"], "n_sig": Cc["n_sig"],
    "dups": [[r["Kept"], r["Removed"]] for _, r in Cc["pool_dups"].iterrows()],
    "composition": [list(map(str, Cc["composition"].columns))] + [[str(v) for v in r] for r in Cc["composition"].values.tolist()],
    "cart_name": Cc["cart_name"], "rf_name": Cc["rf_name"], "sets": {k: ", ".join(v) for k, v in Cc["sets"].items()},
    "set_sizes": {k: len(v) for k, v in Cc["sets"].items()},
    "tier3": tab(Cc["tier3"], ["Set", "Features", "JM"], {"Features": lambda v: str(int(v)), "JM": lambda v: f"{v:.3f}"}),
    "tier4": tab(Cc["tier4"], ["Set", "Classifier", "OA", "BA", "PA_H", "PA_D", "kappa", "AUC"],
                 {"OA": pct, "BA": pct, "PA_H": pct, "PA_D": pct, "kappa": lambda v: f"{v:.3f}", "AUC": lambda v: f"{v:.3f}"}),
    "errmat": {k: {kk: (int(vv) if kk in ("HH", "HD", "DH", "DD", "N") else float(vv)) for kk, vv in v.items()} for k, v in Cc["errmat"].items()},
    "validation": tab(Cc["validation"], ["Pipeline", "Scheme", "BA", "BA_SD", "AUC", "kappa"],
                      {"BA": pct, "BA_SD": pct, "AUC": lambda v: f"{v:.3f}", "kappa": lambda v: f"{v:.3f}"}),
    "wilcoxon": tab(Cc["wilcoxon"], ["Comparison", "Units", "Mean difference", "First better", "Second better", "Wilcoxon p"],
                    {"Mean difference": lambda v: f"{100 * v:+.1f} pts", "First better": lambda v: str(int(v)),
                     "Second better": lambda v: str(int(v)), "Wilcoxon p": lambda v: f"{v:.1e}" if v < 0.001 else f"{v:.3f}"}),
    "stability": tab(Cc["stability"]["index"], ["Method", "Mean features", "Unique features (union)", "Stability index (±10 nm)", "Mean pairwise Jaccard (±10 nm)"],
                     {"Mean features": lambda v: f"{v:.1f}", "Unique features (union)": lambda v: str(int(v))}),
    "fold_comp": tab(Cc["fold_composition"], ["Selector", "Feature type", "Selected (50 training sets)", "Share"],
                     {"Share": pct, "Selected (50 training sets)": lambda v: str(int(v))}),
    "v": {f"{p}|{s}": {"BA": float(vrow(Cc, p, s)["BA"]), "AUC": float(vrow(Cc, p, s)["AUC"])}
          for p in ["CART classifier", "RF classifier", "QDA on CART features", "QDA on RF features"] for s in ["V1", "V3", "V4", "V5"]},
    "jm": {r["Set"]: float(r["JM"]) for _, r in Cc["tier3"].iterrows()},
    "stab_v": {r["Method"]: float(r["Mean pairwise Jaccard (±10 nm)"]) for _, r in Cc["stability"]["index"].iterrows()},
}


J["C"] = cblock(Cc)
HAS_CR = (WORK / "partCR.pkl").exists()
if HAS_CR:
    CR, XR = load("partCR"), load("compareCR")
    J["CR"] = cblock(CR)
pp = lambda v: f"{100 * v:+.1f} pts"  # noqa: E731
pv = lambda v: f"{v:.1e}" if v < 0.001 else f"{v:.3f}"  # noqa: E731
if HAS_CR:
  J["XR"] = {
    "side": tab(XR["side_by_side"], list(XR["side_by_side"].columns)),
    "val": tab(XR["val_side"][XR["val_side"].Scheme != "V1"], ["Pipeline", "Scheme", "Part A (raw reflectance)", "Part C′ (raw + K2–K4)", "Part C (K1 + K2–K4)", "Δ C′ − C"],
               {"Part A (raw reflectance)": pct, "Part C′ (raw + K2–K4)": pct, "Part C (K1 + K2–K4)": pct, "Δ C′ − C": pp}),
    "val_all": tab(XR["val_side"], ["Pipeline", "Scheme", "Part A (raw reflectance)", "Part C′ (raw + K2–K4)", "Part C (K1 + K2–K4)", "Δ C′ − A", "Δ C′ − C"],
                   {"Part A (raw reflectance)": pct, "Part C′ (raw + K2–K4)": pct, "Part C (K1 + K2–K4)": pct, "Δ C′ − A": pp, "Δ C′ − C": pp}),
    "wilcoxon": tab(XR["wilcoxon"], ["First", "Second", "Units", "Mean difference (BA)", "First better", "Second better", "Wilcoxon p"],
                    {"Mean difference (BA)": pp, "First better": lambda v: str(int(v)), "Second better": lambda v: str(int(v)), "Wilcoxon p": pv}),
    "comp": tab(XR["comp_side"], ["Selector", "Feature type", "C′ selected", "C′ share", "C selected", "C share"],
                {"C′ share": pct, "C share": pct, "C′ selected": lambda v: str(int(v)), "C selected": lambda v: str(int(v))}),
    "overlap": tab(XR["overlap"], ["Selector", "C′ set", "C set", "Same feature (exact)", "Same within ±10 nm", "Only in C′", "Only in C"],
                   {"Same within ±10 nm": lambda v: str(int(v))}),
    "raw_bands": tab(XR["raw_bands"], list(XR["raw_bands"].columns)),
    "raw_allleaf": XR["raw_bands_allleaf"],
    "lodo": [["Feature set · pipeline"] + D["folds"]["V5_dates"]] + [
        [f"{fs.split(' (')[0]} · {p}"] + [pct(XR["lodo"].query("`Feature set`==@fs and Pipeline==@p and `Held-out date`==@d")["BA mean"].iloc[0]) for d in D["folds"]["V5_dates"]]
        for fs, p in XR["lodo"][["Feature set", "Pipeline"]].drop_duplicates().values],
}
J["X"] = {
    "synthesis_all": tab(X["synthesis"], ["Approach", "BA V3 (nested CV)", "BA V4 (hold-out plots)", "BA V5 (new date + plots)"],
                         {"BA V3 (nested CV)": pct, "BA V4 (hold-out plots)": pct, "BA V5 (new date + plots)": pct}),
    "cross": tab(X["cross_wilcoxon"], ["First", "Second", "Units", "Mean difference (BA)", "First better", "Second better", "Wilcoxon p"],
                 {"Mean difference (BA)": lambda v: f"{100 * v:+.1f} pts", "First better": lambda v: str(int(v)),
                  "Second better": lambda v: str(int(v)), "Wilcoxon p": lambda v: f"{v:.1e}" if v < 0.001 else f"{v:.3f}"}),
    "lodo": [["Feature set · pipeline"] + D["folds"]["V5_dates"]] + [
        [f"{fs.split(' (')[0]} · {p}"] + [pct(X["lodo"].query("`Feature set`==@fs and Pipeline==@p and `Held-out date`==@d")["BA mean"].iloc[0]) for d in D["folds"]["V5_dates"]]
        for fs, p in X["lodo"][["Feature set", "Pipeline"]].drop_duplicates().values],
    "synthesis": tab(X["synthesis"].head(16), ["Approach", "BA V3 (nested CV)", "BA V4 (hold-out plots)", "BA V5 (new date + plots)"],
                     {"BA V3 (nested CV)": pct, "BA V4 (hold-out plots)": pct, "BA V5 (new date + plots)": pct}),
}
sa = X["strata_auc"]
J["X"]["strata_range"] = [["Feature", "AUC all leaves", "AUC range over dates", "over growth stages", "over varieties"]] + [
    [ft_, f"{sa[(sa.Feature == ft_) & (sa.Stratum == 'All leaves')]['AUC'].iloc[0]:.3f}"] +
    [f"{sa[(sa.Feature == ft_) & (sa.Stratum == s)]['AUC'].min():.2f}–{sa[(sa.Feature == ft_) & (sa.Stratum == s)]['AUC'].max():.2f}" for s in ("Date", "Growth stage", "Variety")]
    for ft_ in dict.fromkeys(sa["Feature"])]
chk = pd.read_pickle(WORK / "allchecks.pkl")
J["checks"] = {"n": len(chk), "pass": int((chk.Status == "PASS").sum()), "flag": int((chk.Status == "FLAG").sum()),
               "fail": int((chk.Status == "FAIL").sum()),
               "table": [["#", "Step", "What was checked", "Result", "Status"]] + [[str(r["#"]), r["Step"], r["What was checked"], str(r["Result"])[:110], r["Status"]] for _, r in chk.iterrows()]}
J["txt"] = TXT
# ---- plot-average facts
PAV = D["audit"].get("plotavg")
if PAV is not None:
    J["PA"] = {"n_leaf": PAV["n_leaf"], "n_avg": PAV["n_avg"], "n_ok": PAV["n_ok"], "n_cols": len(PAV["check"]),
               "leaf_tab": tab(PAV["leaf_tab"], list(PAV["leaf_tab"].columns),
                               {c: (lambda v: str(int(v))) for c in PAV["leaf_tab"].columns if c not in ("Date", "Class")})}
J["vi_table"] = tab(K["vi_table"], list(K["vi_table"].columns))
J["k3_all"] = tab(K["k3"], ["name", "Mean healthy", "Mean diseased", "AUC", "Direction", "BA plot-grouped CV", "BA hold-out"],
                  {"BA plot-grouped CV": pct, "BA hold-out": pct, "AUC": lambda v: f"{v:.3f}"})
J["k2_all"] = tab(K["k2"].head(20), ["name", "Mean healthy", "Mean diseased", "AUC", "Direction", "BA plot-grouped CV", "BA hold-out"],
                  {"BA plot-grouped CV": pct, "BA hold-out": pct, "AUC": lambda v: f"{v:.3f}"})
J["edge_all"] = tab(K["k4_edge"], ["name", "Mean healthy", "Mean diseased", "AUC", "Direction", "BA plot-grouped CV", "BA hold-out"],
                    {"BA plot-grouped CV": pct, "BA hold-out": pct, "AUC": lambda v: f"{v:.3f}"})
J["k4_regions"] = tab(K["k4_regions"], ["Derivative", "Region (nm)", "Band (nm)", "AUC", "Direction", "Hedges g"],
                      {"Band (nm)": lambda v: f"{v:.0f}", "AUC": lambda v: f"{v:.3f}", "Hedges g": lambda v: f"{v:.2f}"})
J["tier1_sig_by_test"] = {r["Test"]: int(r["Significant bands"]) for _, r in A["tier1_tests"].iterrows()}
# ---- disease-specific features: the CART and Random Forest selections of the combined pool, with their statistics
from sp import features as _feat  # noqa: E402
from sp import stats as _st  # noqa: E402
POOL = _feat.build_all(D["spec"], C)["groups"]["G5"][1]
_names = list(POOL.names)
TYPE_FULL = {"K1 band": "Band reflectance", "K2 continuum": "Continuum removal", "K3 index": "Vegetation index",
             "K4 D1 band": "First derivative", "K4 D2 band": "Second derivative", "K4 D3 band": "Third derivative",
             "K4 edge": "Red-edge / edge parameter"}
t1 = Cc["tier1"].set_index("name")
RESEL = {m: Cc["stability"][f"reselect_{m}"] for m in ("CART", "RF")}


def _share(m, nm):
    """share of the 50 nested training sets in which method m selected a feature of the same type within ±10 nm"""
    for tab_ in (RESEL["RF"], RESEL["CART"]):
        r = tab_[tab_["Feature"] == nm]
        col = [c for c in tab_.columns if c.startswith("Re-selected") and m in c]
        if len(r) and col:
            return float(r[col[0]].iloc[0])
    return None


def _label(nm):
    import re as _re
    m = _re.match(r"^(D[123])_(\d+)$", nm)
    if m:
        return {"D1": "First derivative", "D2": "Second derivative", "D3": "Third derivative"}[m.group(1)] + f" at {m.group(2)} nm"
    m = _re.match(r"^R(\d+)$", nm)
    if m:
        return f"Reflectance at {m.group(1)} nm"
    return nm


ds_rows = []
cart_set, rf_set = Cc["sets"][Cc["cart_name"]], Cc["sets"][Cc["rf_name"]]
for nm in list(dict.fromkeys(list(rf_set) + list(cart_set))):
    j = _names.index(nm)
    x = POOL.X[:, j]
    a = _st.auc(x[:, None], y)[0]
    by = "CART + Random Forest" if nm in cart_set and nm in rf_set else ("Random Forest" if nm in rf_set else "CART")
    r = t1.loc[nm]
    ds_rows.append({"Feature": _label(nm), "Type": TYPE_FULL.get(POOL.meta.at[j, "type"], POOL.meta.at[j, "type"]), "Selected by": by,
                    "Mean healthy": float(r["mean0"]), "Mean diseased": float(r["mean1"]), "Direction": "D > H" if r["mean1"] > r["mean0"] else "D < H",
                    "Welch t": float(r["t"]), "q (FDR)": float(r["q"]), "AUC": max(a, 1 - a),
                    "Re-selected, CART (50 sets)": _share("CART", nm), "Re-selected, RF (50 sets)": _share("RF", nm)})
DSdf = pd.DataFrame(ds_rows)
J["DS"] = {"rows": [["Feature", "Type", "Selected by", "Mean healthy", "Mean diseased", "Direction", "AUC", "q (FDR)", "Re-selected CART / RF"]]
           + [[r["Feature"], r["Type"], r["Selected by"], f(r["Mean healthy"], 4), f(r["Mean diseased"], 4), r["Direction"], f"{r['AUC']:.3f}",
               f"{r['q (FDR)']:.1e}", " / ".join("–" if v is None else f"{100 * v:.0f} %" for v in (r["Re-selected, CART (50 sets)"], r["Re-selected, RF (50 sets)"]))] for r in ds_rows],
           "colW": [2.6, 1.9, 1.9, 1.05, 1.05, 0.8, 0.7, 0.85, 1.38],
           "note": "Features of the combined pool chosen by CART and by Random Forest (highest importance peaks) on all 192 plot-average spectra; "
                   "AUC is direction-free; re-selected = share of the 50 nested cross-validation training sets in which a feature within ±10 nm "
                   "(same type) was selected again."}
DSdf.to_pickle(WORK / "disease_specific_features.pkl")
# ---- references: methods (Word report list) + vegetation-index sources (plot-average workbooks), alphabetical, de-duplicated
import re as _re2  # noqa: E402
from build_plotavg_workbooks import REFERENCES as _VI_REFS  # noqa: E402
_m = json.loads((Path(__file__).resolve().parent / "conclusions_whiterust_all_dates.json").read_text())["references"]
_all, _seen = [], set()
for r in [x for x in _m if not x.startswith("Vegetation-index sources")] + _VI_REFS:
    k = (_re2.match(r"[^\s,]+", r).group(0).lower(), (_re2.search(r"(19|20)\d\d[ab]?", r) or _re2.search(r"\d{4}", r)).group(0))
    if k in _seen:
        continue
    _seen.add(k)
    _all.append(r)
J["refs"] = sorted(_all, key=lambda t: t.lower())
# ---- full names (no codes) and plot-average wording in every string
if C.get("naming") == "full":
    from naming import Namer
    NM = Namer(D["folds"].get("V5_by", "Date"), unit="plot" if C["data"].get("plot_average") else "leaf")
    SKIP = {"fig", "sets", "refs"}

    def _tx(o, key=None):
        if key in SKIP:
            return o
        if isinstance(o, str):
            return NM.text(o)
        if isinstance(o, list):
            return [_tx(v) for v in o]
        if isinstance(o, dict):
            return {k: _tx(v, k) for k, v in o.items()}
        return o
    J = {k: (v if k in SKIP else _tx(v, k)) for k, v in J.items()}
J["fig"] = str(WORK / "figures")
(WORK / "results.json").write_text(json.dumps(J, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)))
print("results.json written", len(json.dumps(J)) // 1024, "kB")
