"""Data-driven interpretation text for one (subset) run: conclusions, recommendations and a short
'result in brief' for the main sheets. Every number is read from the result pickles of this run,
so the text of each workbook matches its own tables. Writes WORK/conclusions.json."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from common import ROOT, WORK, cfg, load, present_dates, subset_label, v3_label, v5_label

C = cfg()
D, A, K, Cc, X = load("data"), load("partA"), load("partK"), load("partC"), load("compare")
y, F, meta = D["y"], D["folds"], D["meta"]
nH, nD = int((y == 0).sum()), int((y == 1).sum())
PD = present_dates(D)
SUB = subset_label(C)
NSETS, NV4 = len(F["V3"]), len(F["V4"])


def pc(v):
    return f"{100 * float(v):.1f} %"


def ba(R, pipe, sch):
    return float(R["validation"].set_index(["Pipeline", "Scheme"]).loc[(pipe, sch), "BA"])


def sd(R, pipe, sch):
    return float(R["validation"].set_index(["Pipeline", "Scheme"]).loc[(pipe, sch), "BA_SD"])


def pfmt(p):
    if not np.isfinite(p):
        return "p n/a"
    return f"p = {p:.3f}" if p >= 0.001 else f"p = {p:.1e}"


def wil(R, comp, units):
    w = R["wilcoxon"]
    r = w[(w.Comparison == comp) & (w.Units.str.startswith(units))]
    return None if r.empty else r.iloc[0]


def bands(lst, n=None):
    out = [str(v).replace("WV", "") for v in lst]
    return ", ".join(out[:n] if n else out)


def k5(group, clf, scheme="CV"):
    t = K["k5"]
    r = t[(t.Group == group) & (t.Classifier == clf) & (t.Scheme == scheme)]
    return float(r["BA"].iloc[0]) if len(r) else np.nan


# ---------------------------------------------------------------- numbers
tt = A["tier1_tests"].set_index("Test")["Significant bands"]
n_sig = int(A["n_sig"])
n_mm = int(tt[[i for i in tt.index if i.startswith("Mixed model")][0]])
n_bal = int(tt[[i for i in tt.index if i.startswith("Balanced subsets")][0]])
nb = int(A["n_features"])
t3 = A["tier3"].set_index("Set")
jm_c, jm_r = float(t3.loc[A["cart_name"], "JM"]), float(t3.loc[A["rf_name"], "JM"])
em = A["errmat"][A["cart_name"]]
cart = A["sets"][A["cart_name"]]
root = A["cart_full"]["vars"][0] if A["cart_full"]["vars"] else "—"
s1 = K["k1_summary"]
w_rc = wil(A, "RF classifier − CART classifier", "V3")
w_q = wil(A, "QDA on RF features − QDA on CART features", "V3")
stab = A["stability"]["index"].set_index("Method")
cstab = Cc["stability"]["index"].set_index("Method")
best_c = max(("QDA on CART features", "QDA on RF features", "RF classifier", "CART classifier"), key=lambda p: ba(Cc, p, "V3"))
best_a = max(("QDA on CART features", "QDA on RF features", "RF classifier", "CART classifier"), key=lambda p: ba(A, p, "V3"))
gain = ba(Cc, "QDA on RF features", "V3") - ba(A, "QDA on RF features", "V3")
groups = {"G1": "K1 reflectance", "G2": "K2 continuum removal", "G3": "K3 vegetation indices", "G4": "K4 derivatives + edge parameters"}
k5_rf = {g: k5(g, "RF") for g in groups}
best_g = max(k5_rf, key=lambda g: k5_rf[g])
reip = K["reip"].iloc[0]
shift = float(reip["Mean diseased"] - reip["Mean healthy"])
jf = K["k3b_jf"]
jf_best = jf["refined"].iloc[0]
types = Cc["composition"].set_index("Feature type") if "composition" in Cc else None
lodo = X["lodo"]
lev = [c for c in lodo.columns if c.startswith("Held-out")][0]
lo_c = lodo[(lodo["Feature set"] == "Combined pool (Part C)")]
lo_a = lodo[(lodo["Feature set"] == "Reflectance (Part A)")]
v5_a, v5_c = ba(A, "QDA on CART features", "V5"), ba(Cc, "QDA on RF features", "V5")
k2b, k3b_, k4b = K["k2"].iloc[0], K["k3"].iloc[0], K["k4_edge"].iloc[0]
d1 = K["d1_all"][~K["d1_all"]["Guard"]].nlargest(1, "AUC").iloc[0]
qda_v3, qda_v4 = ba(A, "QDA on CART features", "V3"), ba(A, "QDA on CART features", "V4")
c_v3, c_v4 = ba(Cc, "QDA on RF features", "V3"), ba(Cc, "QDA on RF features", "V4")

# pooled (all dates) reference, when available
ref = {}
try:
    import pickle
    w0 = ROOT / "work"
    if w0.resolve() != WORK.resolve() and (w0 / "partA.pkl").exists():
        A0 = pickle.load(open(w0 / "partA.pkl", "rb"))
        C0 = pickle.load(open(w0 / "partC.pkl", "rb"))
        ref = {"a": ba(A0, "QDA on CART features", "V3"), "c": ba(C0, "QDA on RF features", "V3"),
               "jm": float(A0["tier3"].set_index("Set").loc[A0["cart_name"], "JM"]), "n": len(A0["tier1"])}
except Exception:  # noqa: BLE001
    ref = {}

sep_c = "≥ 1.90 (separable)" if jm_c >= 1.9 else "< 1.90 (not separable by the J–M criterion)"

# ---------------------------------------------------------------- conclusions
con = [
    f"Subset: {SUB} — {len(y)} leaves ({nH} healthy, {nD} diseased; imbalance 1 : {nD / nH:.1f}), "
    f"{len(set(D['groups'][y == 0]))} healthy and {len(set(D['groups'][y == 1]))} diseased plots, {'dates' if len(PD) > 1 else 'date'} {', '.join(PD)}.",
    f"Tier 1: healthy and white-rust leaves differ significantly at {n_sig} of {nb} bands (Welch + BH-FDR); {n_mm} bands remain "
    f"significant with a random plot effect and {n_bal} in ≥ 95 % of 1000 balanced subsets. The most sensitive single band "
    f"(smoothed reflectance) reaches AUC {s1['best_auc']:.2f} at {s1['best_wl']:.0f} nm."
    + ("" if A.get("tier1_rule", "FDR") == "FDR" else
       f" Because fewer than 2 bands passed the FDR correction, Tier 2 used the {len(A['sig_cols'])} bands with "
       + ("uncorrected p < 0.05." if A["tier1_rule"] == "uncorrected p" else "the smallest p-values.")),
    f"Tier 2: CART (rpart, prior 0.5/0.5) selected {len(cart)} bands (root {str(root).replace('WV', '')} nm): {bands(cart)} nm. "
    f"The Balanced RF importance peaks ({A['rf_name']}) were {bands(A['sets'][A['rf_name']])} nm.",
    f"Tier 3: J–M = {jm_c:.2f} on the CART bands and {jm_r:.2f} on the RF bands: "
    + ("both sets separate the classes (≥ 1.90)." if min(jm_c, jm_r) >= 1.9 else
       "neither set reaches the 1.90 separability threshold (Das et al. used 1.94)." if max(jm_c, jm_r) < 1.9 else
       f"only the {'RF' if jm_r >= 1.9 else 'CART'} bands reach the 1.90 separability threshold"
       + (" (and the 1.94 threshold of Das et al.)." if max(jm_c, jm_r) >= 1.94 else " (but not 1.94, the threshold of Das et al.).")),
    f"Tier 4: QDA with equal priors on the CART bands gives BA {pc(em['BA'])} in the paper's protocol (V1; healthy recall "
    f"{pc(em['PA_H'])}, diseased recall {pc(em['PA_D'])}) and {pc(qda_v3)} ± {pc(sd(A, 'QDA on CART features', 'V3'))} (V3 nested, "
    f"plot-grouped) / {pc(qda_v4)} (V4 hold-out plots) on new plots.",
]
if w_rc is not None:
    _d = float(w_rc["Mean difference"])
    _fold = f"V3, RF better in {int(w_rc['First better'])} of {int(w_rc['n'])} folds, {pfmt(w_rc['Wilcoxon p'])}"
    if abs(_d) < 0.01 or w_rc["Wilcoxon p"] >= 0.05:
        _cls = f"as classifiers RF and CART perform alike ({100 * _d:+.1f} points; {_fold})"
    else:
        _cls = f"as classifiers RF {'beats' if _d > 0 else 'is worse than'} CART by {abs(100 * _d):.1f} points ({_fold})"
    _js = stab.loc["RF", "Mean pairwise Jaccard (±10 nm)"], stab.loc["CART", "Mean pairwise Jaccard (±10 nm)"]
    con.append(f"CART vs RF: {_cls}; as band selectors for QDA the RF bands give {100 * w_q['Mean difference']:+.1f} points "
               f"vs the CART bands ({pfmt(w_q['Wilcoxon p'])}). RF selection is "
               f"{'more' if _js[0] > _js[1] + 0.02 else 'less' if _js[0] < _js[1] - 0.02 else 'about as'} stable "
               f"{'as' if abs(_js[0] - _js[1]) <= 0.02 else 'than'} CART selection (Jaccard ±10 nm {_js[0]:.2f} vs {_js[1]:.2f}).")
con.append(f"Disease-sensitive features (Part K): the strongest group for RF is {groups[best_g]} (BA {pc(k5_rf[best_g])}, V3) vs "
           f"{pc(k5_rf['G1'])} for reflectance; best single features: first derivative at {d1['Wavelength (nm)']:.0f} nm (AUC {d1['AUC']:.2f}), "
           f"{k2b['name']} (AUC {k2b['AUC']:.2f}), {k3b_['name']} (AUC {k3b_['AUC']:.2f}), {k4b['name']} (AUC {k4b['AUC']:.2f}). "
           f"REIP ({reip['name'].replace('REIP – ', '')}) shifts by {shift:+.1f} nm in diseased leaves (AUC {reip['AUC']:.2f}).")
con.append(f"Part C (four tiers on the combined K1 + K2–K4 pool, {Cc['n_features']} features, {Cc['n_sig']} significant): CART chose "
           f"{len(Cc['sets'][Cc['cart_name']])} features, RF {len(Cc['sets'][Cc['rf_name']])} (J–M {float(Cc['tier3'].set_index('Set').loc[Cc['cart_name'], 'JM']):.2f} / "
           f"{float(Cc['tier3'].set_index('Set').loc[Cc['rf_name'], 'JM']):.2f}); QDA on the RF features reaches "
           f"{pc(c_v3)} (V3) / {pc(c_v4)} (V4), {100 * gain:+.1f} points vs QDA on RF reflectance bands; best pipeline on the pool: "
           f"{best_c} ({pc(ba(Cc, best_c, 'V3'))}, V3).")
_v5 = [(f"{lab}: {p}", ba(R, p, "V5")) for lab, R in (("reflectance", A), ("combined pool", Cc))
       for p in ("CART classifier", "RF classifier", "QDA on CART features", "QDA on RF features")]
_v5 = [t for t in _v5 if np.isfinite(t[1])]
V5_BEST = max(_v5, key=lambda t: t[1]) if _v5 else ("—", np.nan)
if F.get("V5_by", "Date") == "Date":
    con.append(f"Transfer (V5, leave-one-date-out on new plots): QDA on CART reflectance bands {pc(v5_a)}, QDA on combined-pool RF features "
               f"{pc(v5_c)} — {'a clear drop from' if v5_c < c_v3 - 0.05 else 'close to'} the V3 estimate ({pc(c_v3)}); the date/stage effect "
               f"{'limits' if v5_c < c_v3 - 0.05 else 'hardly affects'} transfer. Best pipeline under transfer: {V5_BEST[0]} ({pc(V5_BEST[1])}).")
else:
    con.append(f"Transfer (V5, leave-one-variety-out): QDA on CART reflectance bands {pc(v5_a)}, QDA on combined-pool RF features {pc(v5_c)} "
               f"({'a clear drop from' if v5_c < c_v3 - 0.05 else 'close to'} the V3 estimate, {pc(c_v3)}), i.e. features chosen on two "
               f"varieties {'transfer only partly' if v5_c < c_v3 - 0.05 else 'transfer well'} to the third. Best pipeline under transfer: "
               f"{V5_BEST[0]} ({pc(V5_BEST[1])}).")
if ref:
    con.append(f"Compared with all dates, stages and varieties pooled (V3: reflectance QDA-CART {pc(ref['a'])}, combined-pool QDA-RF "
               f"{pc(ref['c'])}; J–M {ref['jm']:.2f}), this subset gives {pc(qda_v3)} and {pc(c_v3)} (J–M {jm_c:.2f}): "
               + ("analysing it separately improves discrimination." if c_v3 > ref["c"] + 0.02 else
                  ("discrimination is lower than in the pooled analysis (same plots, but only one leaf level, i.e. fewer leaves per plot)." if "Leaf level" in (C["data"].get("subset") or {}) else "discrimination is lower than in the pooled analysis (fewer leaves and plots).") if c_v3 < ref["c"] - 0.02 else
                  "discrimination is similar to the pooled analysis."))

rec = [
    f"Use {'first-derivative and continuum-removed' if best_g in ('G2', 'G4') else groups[best_g]} features rather than single reflectance "
    f"bands for this subset; the four-tier selection with RF importance on the combined pool and a QDA or RF classifier is the recommended pipeline.",
    "Report balanced accuracy with both class recalls and the priors used; the classes are imbalanced "
    f"(1 : {nD / nH:.1f}) and equal priors / balanced sampling were applied throughout.",
    f"Base conclusions on the plot-grouped estimates (V3 {v3_label(F)}, V4 {NV4} hold-outs), not on the leaf-level V1 estimate.",
    "Interpret features near the ASD detector joins (≈ 1000 and 1800 nm) with care; guard zones were excluded from the rankings.",
]
rec.append(f"For application to a new {'date' if F.get('V5_by', 'Date') == 'Date' else 'variety'}, the most robust pipeline here was "
           f"{V5_BEST[0]} (V5 BA {pc(V5_BEST[1])})"
           + ("; accuracy on an unseen date is much lower than within the date, so calibrate with leaves of the target date or growth stage."
              if F.get("V5_by", "Date") == "Date" and V5_BEST[1] < c_v3 - 0.05 else "."))
if len(set(D["groups"][y == 0])) < 8:
    rec.append(f"Only {len(set(D['groups'][y == 0]))} healthy plots are in this subset: validation folds hold few healthy plots each, so "
               "the SDs of V3/V4 are large and the results should be confirmed with more healthy plots.")

# ---------------------------------------------------------------- per-sheet readings
rd = {}
rd["05_Tier1_Ttest"] = [con[1], f"Uncorrected, {int(tt.iloc[3])} bands have p < 0.05; ANOVA + FDR gives {int(tt.iloc[2])} (same ranking as Welch)."]
rd["06_Tier2_CART"] = [con[2], "Re-selection of each CART band in plot-level bootstraps and in the nested training sets is shown in Table 3.1 and Figure 6b; "
                       "bands re-selected in < 50 % of the training sets should not be interpreted individually."]
rd["07_Tier3_JM"] = [con[3]]
rd["08_Tier4_QDA"] = [con[4]]
v = A["validation_qda_cart"]
rd["09_Validation"] = [f"QDA on CART bands, equal priors: V1 {pc(ba(A, 'QDA on CART features', 'V1'))}, V3 {pc(qda_v3)}, V4 {pc(qda_v4)}, "
                       f"V5 ({v5_label(F)}) {pc(v5_a)}. "
                       + ("Leaf-level CV is optimistic here (V1 − V3 > 3 points): plot effects and selection bias matter."
                          if ba(A, 'QDA on CART features', 'V1') - qda_v3 > 0.03 else
                          "V1 and the plot-grouped estimates agree within 3 points: selection bias and plot leakage are small.")]
if w_rc is not None:
    rd["12_A3_CART_vs_RF"] = [con[5]]
rd["13_A4_Band_Stability"] = [f"Mean pairwise Jaccard (±10 nm): RF {stab.loc['RF', 'Mean pairwise Jaccard (±10 nm)']:.2f}, CART "
                              f"{stab.loc['CART', 'Mean pairwise Jaccard (±10 nm)']:.2f} over {NSETS} nested training sets."]
rd["15_K1_Band_Reflectance"] = [f"{s1['sig_smoothed']} of {s1['tested']} smoothed bands significant; {s1['auc70']} bands with AUC ≥ 0.70; "
                                f"best band {s1['best_wl']:.0f} nm (AUC {s1['best_auc']:.2f})."]
rd["16_K2_Continuum_Removal"] = [f"Most sensitive continuum-removed parameter: {k2b['name']} (AUC {k2b['AUC']:.2f}, BA plot-grouped CV {pc(k2b['BA plot-grouped CV'])})."]
rd["17_K3_Vegetation_Indices"] = [f"Most sensitive index: {k3b_['name']} (AUC {k3b_['AUC']:.2f}, BA plot-grouped CV {pc(k3b_['BA plot-grouped CV'])})."]
rd["18_K3b_Optimised_Index"] = [f"Best join-free two-band index: {jf_best['name']} (AUC {jf_best['AUC']:.2f}); honest nested BA "
                                f"{pc(jf['honest']['NDSI']['BA CV'])} (CV) / {pc(jf['honest']['NDSI']['BA hold-out'])} (hold-out)."]
rd["19_K4_Derivatives"] = [f"Best first-derivative band outside the guard zones: {d1['Wavelength (nm)']:.0f} nm (AUC {d1['AUC']:.2f}); "
                           f"best edge parameter {k4b['name']} (AUC {k4b['AUC']:.2f})."]
rd["20_K4b_REIP"] = [f"{reip['name']}: healthy {reip['Mean healthy']:.1f} nm, diseased {reip['Mean diseased']:.1f} nm (shift {shift:+.1f} nm, "
                     f"AUC {reip['AUC']:.2f}). " + ("A blue shift (chlorophyll loss) is present." if shift < -0.5 else
                                                    "No clear blue shift in this subset.")]
rd["22_K5_CART_vs_RF"] = [con[6], f"RF vs CART on the combined pool (V3): {pc(k5('G5', 'RF'))} vs {pc(k5('G5', 'CART'))}; "
                          f"guard-zone artefact test (K4 with guard bands) RF {pc(k5('G6', 'RF'))} vs {pc(k5('G4', 'RF'))} without."]
rd["28_C5_Validation"] = [con[7]]
rd["29_C6_Stability"] = [f"Mean pairwise Jaccard (±10 nm) on the combined pool: RF {cstab.loc['RF', 'Mean pairwise Jaccard (±10 nm)']:.2f}, "
                         f"CART {cstab.loc['CART', 'Mean pairwise Jaccard (±10 nm)']:.2f}."]
lv = lo_c[lo_c.Pipeline == "QDA on RF features"]
rd["31_V5_Transfer"] = [con[8]] + ([("By held-out level (QDA on combined-pool RF features): "
                                     + "; ".join(f"{r[lev]} {pc(r['BA mean'])}" for _, r in lv.iterrows() if np.isfinite(r["BA mean"])) + ".")]
                                   if len(lv) else [])
out = {"conclusions": con, "recommendations": rec, "readings": rd}
(WORK / "conclusions.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
for t in con + rec:
    print("-", t)
