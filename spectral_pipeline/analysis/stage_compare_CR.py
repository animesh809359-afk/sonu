"""Part C′ (raw reflectance + K2 + K3 + K4) vs Part C (K1 reflectance + K2 + K3 + K4) vs Part A
(raw reflectance alone): side-by-side summary, validation, paired Wilcoxon tests on identical
folds, feature-type composition of the nested selections, overlap of the selected features,
V5 by held-out date and synthesis rows. Run after stage_C.py, stage_CR.py and stage_compare.py."""
from __future__ import annotations

import re
import warnings

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from common import load, save
from sp import stats

D = load("data")
A, Cc, CR = load("partA"), load("partC"), load("partCR")
y, F = D["y"], D["folds"]
PIPES = ["CART classifier", "RF classifier", "QDA on CART features", "QDA on RF features"]
out = {}


def fmt_set(R, nm):
    return f"{nm}: " + ", ".join(R["sets"][nm])


def jm(R, nm):
    t = R["tier3"].set_index("Set")
    return t.loc[nm, "JM"]


def val(R, p, s, c="BA"):
    return R["validation"].set_index(["Pipeline", "Scheme"]).loc[(p, s), c]


# ---------------------------------------------------------------- side by side
def comp_txt(R):
    c = R["composition"]
    return "; ".join(f"{r['Feature type']} {int(r['Features'])}" for _, r in c.iterrows())


def sig_txt(R):
    c = R["composition"]
    return "; ".join(f"{r['Feature type']} {int(r['Tier-1 significant'])}/{int(r['Features'])}" for _, r in c.iterrows())


rows = [
    ("Reflectance part of the pool", "Raw reflectance, 2101 bands 400–2500 nm (as measured; = Part A input)",
     "K1 reflectance, 2039 bands (splice-corrected, SG-smoothed, guard zones removed)", ""),
    ("Pool size (after duplicate removal)", f"{CR['pool_size_raw']} → {CR['n_features']}", f"{Cc['pool_size_raw']} → {Cc['n_features']}",
     f"{CR['n_features'] - Cc['n_features']:+d}"),
    ("Pool composition", comp_txt(CR), comp_txt(Cc), ""),
    ("Tier 1: significant (q < 0.05)", f"{CR['n_sig']} of {CR['n_features']}", f"{Cc['n_sig']} of {Cc['n_features']}",
     f"{CR['n_sig'] - Cc['n_sig']:+d}"),
    ("Tier 1: significant by type", sig_txt(CR), sig_txt(Cc), ""),
    ("Tier 2: CART set (all leaves)", fmt_set(CR, CR["cart_name"]), fmt_set(Cc, Cc["cart_name"]), ""),
    ("Tier 2: RF set (all leaves)", fmt_set(CR, CR["rf_name"]), fmt_set(Cc, Cc["rf_name"]), ""),
    ("Tier 3: J–M of the CART set", f"{jm(CR, CR['cart_name']):.3f}", f"{jm(Cc, Cc['cart_name']):.3f}",
     f"{jm(CR, CR['cart_name']) - jm(Cc, Cc['cart_name']):+.3f}"),
    ("Tier 3: J–M of the RF set", f"{jm(CR, CR['rf_name']):.3f}", f"{jm(Cc, Cc['rf_name']):.3f}",
     f"{jm(CR, CR['rf_name']) - jm(Cc, Cc['rf_name']):+.3f}"),
]
for p in PIPES:
    for s, lab in (("V1", "V1 leaf 10-fold"), ("V3", "V3 nested CV"), ("V4", "V4 hold-out plots")):
        a, b = val(CR, p, s), val(Cc, p, s)
        rows.append((f"BA {lab}: {p}", f"{a:.1%}", f"{b:.1%}", f"{(a - b) * 100:+.1f} pp"))
for m in ("CART", "RF"):
    a = CR["stability"]["index"].set_index("Method").loc[m, "Mean pairwise Jaccard (±10 nm)"]
    b = Cc["stability"]["index"].set_index("Method").loc[m, "Mean pairwise Jaccard (±10 nm)"]
    rows.append((f"Stability: {m} mean pairwise Jaccard (±10 nm)", f"{a:.3f}", f"{b:.3f}", f"{a - b:+.3f}"))
out["side_by_side"] = pd.DataFrame(rows, columns=["Item", "Part C′ (raw + K2 + K3 + K4)", "Part C (K1 + K2 + K3 + K4)", "Difference (C′ − C)"])

# ---------------------------------------------------------------- validation side by side
vs = []
for p in PIPES:
    for s in ("V1", "V3", "V4", "V5"):
        a, cr, c = val(A, p, s), val(CR, p, s), val(Cc, p, s)
        vs.append({"Pipeline": p, "Scheme": s, "Part A (raw reflectance)": a, "Part C′ (raw + K2–K4)": cr,
                   "Part C (K1 + K2–K4)": c, "Δ C′ − A": cr - a, "Δ C′ − C": cr - c,
                   "SD C′": val(CR, p, s, "BA_SD"), "AUC C′": val(CR, p, s, "AUC"), "κ C′": val(CR, p, s, "kappa")})
out["val_side"] = pd.DataFrame(vs)


# ---------------------------------------------------------------- paired Wilcoxon
def fb(R, pipe, sch):
    f = R["fold_ba"]
    return f[(f.Pipeline == pipe) & (f.Scheme == sch)].set_index(["Repeat", "Unit"])["BA"]


wr = []
for p in PIPES:
    for other, R2 in (("Part C (K1 + K2–K4)", Cc), ("Part A (raw reflectance)", A)):
        for sch, lab in (("V3", "V3 nested (50 folds)"), ("V4", "V4 hold-out (10 splits)")):
            d = (fb(CR, p, sch) - fb(R2, p, sch)).dropna()
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                pv = wilcoxon(d).pvalue if (d != 0).any() else 1.0
            wr.append({"First": f"Part C′: {p}", "Second": f"{other}: {p}", "Units": lab, "n": len(d),
                       "Mean difference (BA)": d.mean(), "SD": d.std(ddof=1), "First better": int((d > 0).sum()),
                       "Second better": int((d < 0).sum()), "Wilcoxon p": pv})
out["wilcoxon"] = pd.DataFrame(wr)

# ---------------------------------------------------------------- fold composition
REN = {"K1 band reflectance": "Reflectance band", "Raw reflectance band": "Reflectance band"}
cs = []
for meth in ("CART", "RF"):
    a = CR["fold_composition"][CR["fold_composition"].Selector == meth].assign(t=lambda d: d["Feature type"].replace(REN)).set_index("t")
    b = Cc["fold_composition"][Cc["fold_composition"].Selector == meth].assign(t=lambda d: d["Feature type"].replace(REN)).set_index("t")
    for t in ["Reflectance band", "K2 continuum removal", "K3 vegetation index", "K4 first-derivative band", "K4 edge parameter"]:
        cs.append({"Selector": meth, "Feature type": t + (" (raw in C′, K1 in C)" if t == "Reflectance band" else ""),
                   "C′ selected": int(a["Selected (50 training sets)"].get(t, 0)), "C′ share": float(a["Share"].get(t, 0.0)),
                   "C selected": int(b["Selected (50 training sets)"].get(t, 0)), "C share": float(b["Share"].get(t, 0.0))})
out["comp_side"] = pd.DataFrame(cs)


# ---------------------------------------------------------------- overlap of selected sets
def norm(n):
    return re.sub(r" \(raw\)$", "", n)


def wl(n):
    m = re.fullmatch(r"(R|D1_)(\d+)", norm(n))
    return (m.group(1), int(m.group(2))) if m else None


def near(n, other, tol=10):
    w = wl(n)
    if w is None:
        return norm(n) in {norm(o) for o in other}
    return any(wl(o) and wl(o)[0] == w[0] and abs(wl(o)[1] - w[1]) <= tol for o in other)


ov = []
for lab, a_nm, b_nm in (("CART (all leaves)", CR["cart_name"], Cc["cart_name"]), ("RF (all leaves)", CR["rf_name"], Cc["rf_name"])):
    a, b = CR["sets"][a_nm], Cc["sets"][b_nm]
    na, nb = {norm(v) for v in a}, {norm(v) for v in b}
    ov.append({"Selector": lab, "C′ set": f"{a_nm}", "C set": f"{b_nm}", "Same feature (exact)": ", ".join(v for v in a if norm(v) in nb) or "none",
               "Same within ±10 nm": sum(near(v, b) for v in a), "Only in C′": ", ".join(v for v in a if not near(v, b)) or "none",
               "Only in C": ", ".join(v for v in b if not near(v, a)) or "none",
               "Jaccard (exact)": len(na & nb) / len(na | nb)})
out["overlap"] = pd.DataFrame(ov)

# where do the raw bands chosen in C′ lie (guard / join / noisy ends)?
GZ = [(990, 1010), (1795, 1835)]
rb = []
t1 = CR["tier1"].set_index("name")
for meth in ("CART", "RF"):
    lists = CR["fold_selections"][meth]
    raws = [v for l in lists for v in l if v.endswith("(raw)")]
    ws = np.array([int(re.search(r"\d+", v).group()) for v in raws]) if raws else np.array([], int)
    rb.append({"Selector": meth, "Raw bands selected (50 training sets)": len(raws),
               "In a guard zone (990–1010, 1795–1835 nm)": int(sum(any(a <= w <= b for a, b in GZ) for w in ws)),
               "Within 5 nm of a guard zone": int(sum(any((a - 5) <= w < a or b < w <= (b + 5) for a, b in GZ) for w in ws)),
               "Noisy ends (< 450 or > 2400 nm)": int(((ws < 450) | (ws > 2400)).sum()),
               "Water-absorption regions (1350–1450, 1800–1950 nm)": int((((ws >= 1350) & (ws <= 1450)) | ((ws >= 1800) & (ws <= 1950))).sum()),
               "Distinct raw bands": len(set(raws))})
allsel = CR["sets"][CR["cart_name"]] + CR["sets"][CR["rf_name"]]
out["raw_bands"] = pd.DataFrame(rb)
out["raw_bands_allleaf"] = sorted({v for v in allsel if v.endswith("(raw)")})

# ---------------------------------------------------------------- V5 by date + synthesis rows
dates = F["V5_dates"]
lodo = []
for lab, R in (("Raw reflectance (Part A)", A), ("Raw + K2–K4 (Part C′)", CR), ("K1 + K2–K4 (Part C)", Cc)):
    for p in PIPES:
        for d in dates:
            bas = [stats.balanced_accuracy(y[te], pp) for te, pp, ss, rep, i in R["preds"][(p, "V5")] if F["V5"][i]["date"] == d]
            lodo.append({"Feature set": lab, "Pipeline": p, "Held-out date": d, "BA mean": float(np.mean(bas)),
                         "BA SD": float(np.std(bas, ddof=1))})
out["lodo"] = pd.DataFrame(lodo)
syn = []
for p, nm in (("QDA on CART features", f"QDA on {CR['cart_name']} (CART-selected)"),
              ("QDA on RF features", f"QDA on {CR['rf_name']} (RF-selected)"),
              ("CART classifier", "CART classifier (rpart)"), ("RF classifier", "RF classifier (Balanced RF)")):
    syn.append({"Approach": f"Part C′ · raw + K2–K4 four-tier: {nm}", "BA V1 (leaf 10-fold)": val(CR, p, "V1"),
                "BA V3 (nested CV)": val(CR, p, "V3"), "SD V3": val(CR, p, "V3", "BA_SD"),
                "BA V4 (hold-out plots)": val(CR, p, "V4"), "SD V4": val(CR, p, "V4", "BA_SD"),
                "BA V5 (new date + plots)": val(CR, p, "V5"), "AUC V3": val(CR, p, "V3", "AUC"), "κ V3": val(CR, p, "V3", "kappa")})
out["synthesis_rows"] = pd.DataFrame(syn)
save(out, "compareCR")
# add the C′ rows to the synthesis table of stage_compare (idempotent)
X = load("compare")
s0 = X["synthesis"][~X["synthesis"]["Approach"].str.startswith("Part C′")]
X["synthesis"] = pd.concat([s0, out["synthesis_rows"]], ignore_index=True).sort_values("BA V3 (nested CV)", ascending=False).reset_index(drop=True)
save(X, "compare")

pd.set_option("display.width", 250)
pd.set_option("display.max_colwidth", 120)
print(out["side_by_side"].to_string())
print(out["val_side"].to_string())
print(out["wilcoxon"].to_string())
print(out["comp_side"].to_string())
print(out["overlap"].to_string())
print(out["raw_bands"].to_string())
print(out["raw_bands_allleaf"])
print(out["lodo"].pivot_table(index=["Feature set", "Pipeline"], columns="Held-out date", values="BA mean"))
