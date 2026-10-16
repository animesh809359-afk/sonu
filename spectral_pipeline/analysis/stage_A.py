"""Stage A: four-tier analysis of Das et al. (2020) on the raw leaf reflectance
(400-2500 nm, water bands kept) with imbalance corrections - CART (rpart) and
Random Forest as Tier-2 selectors - plus validation and cross-checks."""
from __future__ import annotations

import copy
import json
import subprocess
import tempfile
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as st
from sklearn.tree import DecisionTreeClassifier

from common import cfg, contiguous, load, region_of, save, subset_mask, v3_label, v5_label
from sp import cart, folds as fl, fourtier, models, stats
from sp.features import FeatureSet, _meta
from sp.metrics import evaluate, summarise

T0 = time.time()
C = cfg()
D = load("data")
spec, y, groups, F = D["spec"], D["y"], D["groups"], D["folds"]
wl = spec.wl
REG = C["spectra"]["regions"]


def raw_fs(R, wlv):
    return FeatureSet(R, _meta([f"WV{int(w)}" for w in wlv], "Raw reflectance", "WV", wlv.astype(float)))


fsA = raw_fs(spec.R_raw, wl)
A = fourtier.run(fsA, y, groups, F, C, "Part A (raw reflectance)", mixed=True)
A["qda_failures"] = list(fourtier.QDA_FAILURES)
X = fsA.X
name_to_col = {n: i for i, n in enumerate(fsA.names)}
cart_set = A["sets"][A["cart_name"]]
cart_cols = [name_to_col[v] for v in cart_set]
one_se_name = [k for k in A["sets"] if "1-SE" in k]

# =================================================================== Tier 1 extras
fourtier.log("Tier 1 extras: ANOVA, Levene, balanced subsets")
t1 = A["tier1"]
X0, X1 = X[y == 0], X[y == 1]
n0, n1 = len(X0), len(X1)
sp_ = np.sqrt(((n0 - 1) * X0.var(0, ddof=1) + (n1 - 1) * X1.var(0, ddof=1)) / (n0 + n1 - 2))
t_student = (X1.mean(0) - X0.mean(0)) / (sp_ * np.sqrt(1 / n0 + 1 / n1))
F_anova = t_student ** 2
p_anova = st.f.sf(F_anova, 1, n0 + n1 - 2)
F_check = np.array([st.f_oneway(X0[:, j], X1[:, j]).statistic for j in range(0, X.shape[1], 50)])
t1["anova_F"], t1["anova_p"], t1["anova_q"] = F_anova, p_anova, stats.bh(p_anova)
t1["levene_p"] = [st.levene(X0[:, j], X1[:, j], center="median").pvalue for j in range(X.shape[1])]
rng = np.random.default_rng(2024)
B = 1000
sig_count = np.zeros(X.shape[1])
n_sig_sub = []
i0, i1 = np.where(y == 0)[0], np.where(y == 1)[0]
for b in range(B):
    sub = np.concatenate([i0, rng.choice(i1, n0, replace=False)])
    q = stats.bh(stats.welch(X[sub], y[sub])["p"])
    sig_count += q < 0.05
    n_sig_sub.append(int((q < 0.05).sum()))
t1["balanced_pct"] = 100 * sig_count / B
t1["region"] = [region_of(w, REG) for w in wl]
A["tier1_tests"] = pd.DataFrame([
    ("Welch t-test + BH-FDR q < 0.05 (used for Tier 2)", int(t1["sig"].sum())),
    ("One-way ANOVA p < 0.05, uncorrected (rule of Das et al.)", int((p_anova < 0.05).sum())),
    ("One-way ANOVA + BH-FDR q < 0.05", int((t1["anova_q"] < 0.05).sum())),
    ("Welch t-test p < 0.05, uncorrected", int((t1["p"] < 0.05).sum())),
    ("Mixed model (random plot effect) + BH-FDR q < 0.05", int(t1["mm_sig"].sum())),
    (f"Balanced subsets ({n0} vs {n0}): significant in ≥ 95 % of 1000 subsets", int((t1["balanced_pct"] >= 95).sum())),
    ("Levene test p < 0.05 (unequal variances → Welch)", int((np.array(t1["levene_p"]) < 0.05).sum())),
], columns=["Test", "Significant bands"])
_cols = list(range(0, X.shape[1], 50))
_sm = stats.mixed_models_statsmodels(X[:, _cols], y, groups, 4)
_rho = st.spearmanr(_sm["p"], t1["mm_p"].to_numpy()[_cols]).correlation
A["checks"].append(("Tier 1", "Mixed model implementation", "R nlme::lme vs Python statsmodels MixedLM (Powell), every 50th band",
                    f"Spearman ρ of p-values {_rho:.3f} (statsmodels uses a Wald z-test, nlme a t-test with 46 df, so nlme p-values are larger)",
                    "PASS" if _rho > 0.95 else "FLAG"))
A["tier1_balanced"] = {"subsets": B, "per_subset": f"{n0} + {n0}", "median": float(np.median(n_sig_sub)),
                       "min": int(np.min(n_sig_sub)), "max": int(np.max(n_sig_sub)),
                       "all": int((t1["balanced_pct"] == 100).sum()),
                       "ge95": int((t1["balanced_pct"] >= 95).sum()),
                       "never": int((t1["balanced_pct"] == 0).sum())}
A["tier1_ranges"] = pd.DataFrame([{"Range (nm)": f"{a:.0f}–{b:.0f}", "Bands": n,
                                   "Result": "significant" if v else "not significant"}
                                  for a, b, n, v in contiguous(t1["sig"].to_numpy(), wl)])
reg_rows = []
for nm, a, b in REG:
    m = (wl >= a) & (wl <= b)
    sub = t1[m]
    j = sub["t"].abs().idxmax()
    reg_rows.append({"Region": f"{nm} ({a}–{b})", "Bands": int(m.sum()), "Welch+FDR significant": int(sub["sig"].sum()),
                     "Mixed-model significant": int(sub["mm_sig"].sum()),
                     "Band of max |t|": float(sub.at[j, "position"]), "Max t": float(sub.at[j, "t"]),
                     "Mean diff (D − H)": float(sub.at[j, "mean1"] - sub.at[j, "mean0"])})
A["tier1_regions"] = pd.DataFrame(reg_rows)
from statsmodels.stats.multitest import multipletests  # noqa: E402
BH_CHECK = float(np.max(np.abs(multipletests(t1["p"], method="fdr_bh")[1] - t1["q"])))
A["checks"] += [
    ("Tier 1", "Welch t-statistic", "SciPy ttest_ind(equal_var=False) vs vectorised formula",
     f"max |Δt| = {np.max(np.abs(st.ttest_ind(X1, X0, equal_var=False).statistic - t1['t'])):.1e}", "PASS"),
    ("Tier 1", "Benjamini–Hochberg q-values", "statsmodels multipletests vs own step-up",
     f"max |Δq| = {BH_CHECK:.1e}", "PASS" if BH_CHECK < 1e-12 else "FAIL"),
    ("Tier 1", "ANOVA equivalence", "one-way ANOVA F (SciPy, every 50th band) vs Student t²",
     f"max relative |F − t²| = {np.max(np.abs(F_check - F_anova[::50]) / F_anova[::50]):.1e}", "PASS"),
    ("Tier 1", "Class imbalance", f"{B} balanced subsets ({n0} vs {n0} leaves)",
     f"median {np.median(n_sig_sub):.0f} significant bands per subset vs {int(t1['sig'].sum())} on all leaves", "PASS"),
    ("Tier 1", "Pseudo-replication",
     "linear mixed model v ~ Disease + (1|plot), REML, R nlme::lme (t-test, 46 df), BH-FDR",
     f"{int(t1['mm_sig'].sum())} of {len(t1)} bands significant (Welch: {int(t1['sig'].sum())}); plot ICC median {np.nanmedian(t1['icc']):.3f}",
     "PASS"),
]

# =================================================================== Tier 2 extras (CART)
fourtier.log("Tier 2 extras: 200 plot-level bootstrap trees, sklearn cross-check")
sig = np.where(t1["sig"].to_numpy())[0]
rngb = np.random.default_rng(42)
plots0, plots1 = np.unique(groups[y == 0]), np.unique(groups[y == 1])
rows_by_plot = {p: np.where(groups == p)[0] for p in np.unique(groups)}
jobs = []
for b in range(200):
    pp = np.concatenate([rngb.choice(plots0, len(plots0)), rngb.choice(plots1, len(plots1))])
    jobs.append(dict(train=np.concatenate([rows_by_plot[p] for p in pp]), test=[], cols=sig))
boot = cart.run_jobs(X, y, fsA.names, jobs, C)
boot_sets = [r["vars"] for r in boot]


def resel(band, lists, tol=10):
    w = float(band[2:])
    return float(np.mean([any(abs(float(v[2:]) - w) <= tol for v in l) for l in lists]))


v3_cart = [A["fold_vars"][("V3", i)]["CART"] for i in range(len(F["V3"]))]
frame = A["cart_full"]["frame"]
first_node = {}
for _, r in frame.iterrows():
    if r["var"] != "leaf" and r["var"] not in first_node:
        first_node[r["var"]] = (int(r["node"]), int(r["depth"]))
interp = {"Blue": "blue/violet: chlorophyll and carotenoid absorption",
          "Green": "green peak: chlorosis / pigment ratio change",
          "Red": "chlorophyll-a absorption well",
          "Red edge": "red edge: chlorophyll loss and leaf structure",
          "NIR": "NIR plateau: mesophyll structure / cell damage",
          "Water band I": "leaf water absorption (≈1400 nm)",
          "SWIR-1": "SWIR-1: water, dry matter",
          "Water band II": "leaf water absorption (O–H, ≈1940 nm)",
          "SWIR-2": "SWIR-2: water wing, protein / cellulose / lignin",
          "SWIR-2 end": "cellulose/lignin; detector edge with higher noise"}
cart_tab = []
for v in sorted(cart_set, key=lambda s: float(s[2:])):
    j = name_to_col[v]
    reg = region_of(wl[j], REG)
    cart_tab.append({"Band (nm)": float(wl[j]), "Region": reg, "First used at node": first_node[v][0],
                     "Tree depth": first_node[v][1], "Mean healthy": float(t1.at[j, "mean0"]),
                     "Mean diseased": float(t1.at[j, "mean1"]), "Welch t": float(t1.at[j, "t"]),
                     "q (BH)": float(t1.at[j, "q"]), "Bootstrap re-selection (±10 nm)": resel(v, boot_sets),
                     "Nested-CV re-selection (±10 nm)": resel(v, v3_cart),
                     "Mixed model significant": "yes" if t1.at[j, "mm_sig"] else "no",
                     "Interpretation": interp.get(reg.split(" (")[0], "")})
A["cart_table"] = pd.DataFrame(cart_tab)
A["boot_sets"] = boot_sets
# scikit-learn cross-check of the root split
skl = DecisionTreeClassifier(criterion="gini", min_samples_split=20, min_samples_leaf=7,
                             class_weight="balanced", random_state=0, max_depth=8).fit(X[:, sig], y)
root_f = fsA.names[sig][skl.tree_.feature[0]]
root_thr = skl.tree_.threshold[0]
left = skl.tree_.children_left[0]
l_f = fsA.names[sig][skl.tree_.feature[left]] if skl.tree_.feature[left] >= 0 else "leaf"
skl_vars = [fsA.names[sig][f] for f in skl.tree_.feature if f >= 0]
fr = frame.set_index("node")
r_root = fr.loc[2, "label"] if 2 in fr.index else ""
r_left = fr.loc[4, "label"] if 4 in fr.index else ""
A["cart_sklearn"] = pd.DataFrame([
    ("Root split", r_root, f"{root_f} < {root_thr:.5g}", "identical variable" if root_f in r_root.split("<")[0].split(">")[0] else "different"),
    ("Split of the left child", r_left, f"{l_f}", "identical variable" if l_f in r_left else "different"),
    ("Bands used by the trees", f"{len(cart_set)} bands (cp = 0.01)",
     f"{len(set(skl_vars))} bands (depth ≤ 8)",
     f"{sum(any(abs(float(a[2:]) - float(b[2:])) <= 5 for b in skl_vars) for a in cart_set)} of {len(cart_set)} rpart bands within ±5 nm"),
], columns=["Item", "rpart (R)", "scikit-learn (balanced class weights)", "Agreement"])
A["checks"].append(("Tier 2", "CART implementation", "rpart (R) vs scikit-learn DecisionTreeClassifier",
                    f"root variable rpart '{r_root}' vs sklearn '{root_f} < {root_thr:.4g}'",
                    "PASS" if root_f in r_root else "FLAG"))
A["checks"].append(("Tier 2", "Stability of the selected bands",
                    "200 plot-level bootstrap trees; 50 nested-CV training sets",
                    "; ".join(f"{int(r['Band (nm)'])} nm {100 * r['Nested-CV re-selection (±10 nm)']:.0f} %"
                              for r in sorted(cart_tab, key=lambda r: -r["Nested-CV re-selection (±10 nm)"])[:3]),
                    "PASS"))

# =================================================================== Tier 3 extras
A["jm_self"] = float(models.jm(np.vstack([X[y == 0][:, cart_cols]] * 2), np.r_[np.zeros((y == 0).sum()), np.ones((y == 0).sum())].astype(int))[0])
A["checks"].append(("Tier 3", "J–M formula", "J–M of the healthy class with itself (must be 0)",
                    f"{A['jm_self']:.1e}", "PASS" if abs(A["jm_self"]) < 1e-9 else "FAIL"))

# =================================================================== Tier 4: R MASS::qda cross-check
fourtier.log("Tier 4: MASS::qda cross-check")
v1fold = np.zeros(len(y), int)
for k, f in enumerate(F["V1"]):
    v1fold[f["test"]] = k + 1


def mass_qda(cols, priors):
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        pd.DataFrame(X[:, cols], columns=[f"b{i}" for i in range(len(cols))]).assign(y=y, fold=v1fold).to_csv(td / "d.csv", index=False)
        pr = "prior = c(0.5, 0.5)," if priors == "equal" else ""
        (td / "q.R").write_text(f"""
suppressMessages(library(MASS)); d <- read.csv('{td}/d.csv'); d$y <- factor(d$y, levels=c(0,1))
p <- numeric(nrow(d)); X <- d[, grep('^b', names(d))]
for (k in sort(unique(d$fold))) {{ tr <- d$fold != k
  m <- qda(X[tr, , drop=FALSE], d$y[tr], {pr} method='moment')
  p[!tr] <- predict(m, X[!tr, , drop=FALSE])$posterior[, 2] }}
write.csv(data.frame(p=p), '{td}/p.csv', row.names=FALSE)""")
        subprocess.run(["Rscript", str(td / "q.R")], check=True, capture_output=True)
        return (pd.read_csv(td / "p.csv")["p"].to_numpy() > 0.5).astype(int)


qrows, QTIES = [], []
for sname in [A["cart_name"]] + one_se_name + [A["rf_name"]]:
    cols = [name_to_col[v] for v in A["sets"][sname]]
    for pri in ("equal", "sample"):
        p_py, prob_py = fourtier._qda_cv(X[:, cols], y, F["V1"], pri)
        p_r = mass_qda(cols, pri)
        qrows.append((sname, pri, float((p_py == p_r).mean())))
        QTIES.extend(np.abs(prob_py[p_py != p_r] - 0.5).tolist())
A["mass_check"] = qrows
A["checks"].append(("Tier 4", "QDA in R", "MASS::qda on the same V1 folds (equal and sample priors)",
                    "; ".join(f"{s} {p}: {100 * v:.2f} % identical" for s, p, v in qrows)
                    + f" — differing predictions have |P(diseased) − 0.5| ≤ {max(QTIES) if QTIES else 0:.4f} (ties at the boundary)",
                    "PASS" if min(v for *_, v in qrows) > 0.999 or (QTIES and max(QTIES) < 0.01) else "FLAG"))

# =================================================================== Validation extras (QDA on CART bands)
fourtier.log("Validation extras: V2, sample priors, RUS")
val_rows = []


def pooled(units, pri, colsel):
    per_rep = {}
    for f, cols in units:
        if len(cols) == 0:
            continue
        p, pr = fourtier._safe_fit(models.qda(pri), X[f["train"]][:, cols], y[f["train"]], X[f["test"]][:, cols])
        per_rep.setdefault(f["rep"], []).append((f["test"], p, pr))
    mets = []
    for parts in per_rep.values():
        te = np.concatenate([a for a, _, _ in parts])
        mets.append(evaluate(y[te], np.concatenate([b for _, b, _ in parts]), np.concatenate([c for _, _, c in parts])))
    return summarise(mets)


_v2, _ = fl.group_folds(y, groups, F["v3_k"], 42)
V2 = [{"train": tr, "test": te, "rep": 0} for tr, te in _v2]
for pri, plab in (("equal", "equal (corrected)"), ("sample", "sample (uncorrected)")):
    val_rows.append({"Scheme": "V1 · leaf-level 10-fold, bands fixed", "Priors": plab,
                     **pooled([(f, cart_cols) for f in F["V1"]], pri, None)})
    val_rows.append({"Scheme": f"V2 · plot-grouped {F['v3_k']}-fold, bands fixed", "Priors": plab,
                     **pooled([(f, cart_cols) for f in V2], pri, None)})
    val_rows.append({"Scheme": f"V3 · nested plot-grouped {v3_label(F)}", "Priors": plab,
                     **pooled([(f, [name_to_col[v] for v in A["fold_vars"][("V3", i)]["CART"]]) for i, f in enumerate(F["V3"])], pri, None)})
    val_rows.append({"Scheme": "V4 · 30 % plot hold-out × 10", "Priors": plab,
                     **pooled([(f, [name_to_col[v] for v in A["fold_vars"][("V4", i)]["CART"]]) for i, f in enumerate(F["V4"])], pri, None)})
    val_rows.append({"Scheme": f"V5 · {v5_label(F)} ({len(F['V5'])} units)", "Priors": plab,
                     **pooled([(f, [name_to_col[v] for v in A["fold_vars"][("V5", i)]["CART"]]) for i, f in enumerate(F["V5"])], pri, None)})
# V3-RUS: random under-sampling of diseased leaves inside each training set (repeat 1)
rus_jobs, rus_units = [], []
rngr = np.random.default_rng(42)
for f in [f for f in F["V3"] if f["rep"] == 0]:
    tr = f["train"]
    t0_, t1_ = tr[y[tr] == 0], tr[y[tr] == 1]
    trb = np.concatenate([t0_, rngr.choice(t1_, len(t0_), replace=False)])
    s_, _ = fourtier.tier1_cols(stats.feature_table(X[trb], y[trb]))
    rus_jobs.append(dict(train=trb, test=f["test"], cols=s_))
    rus_units.append({"train": trb, "test": f["test"], "rep": 0})
rus = cart.run_jobs(X, y, fsA.names, rus_jobs, C)
for pri, plab in (("equal", "equal (corrected)"), ("sample", "sample (uncorrected)")):
    val_rows.append({"Scheme": "V3-RUS · nested + random under-sampling", "Priors": plab,
                     **pooled([(u, [name_to_col[v] for v in r["vars"]]) for u, r in zip(rus_units, rus)], pri, None)})
A["validation_qda_cart"] = pd.DataFrame(val_rows)
A["V2_folds"] = V2

# =================================================================== RF checks (A1)
fourtier.log("RF checks: R randomForest, permutation importance, class weights")
imp = A["rf_importance"]
Xs = X[:, sig]
with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    np.savetxt(td / "X.csv", Xs, delimiter=",")
    np.savetxt(td / "y.csv", y, fmt="%d")
    (td / "rf.R").write_text(f"""
suppressMessages(library(randomForest)); set.seed(42)
X <- as.matrix(read.csv('{td}/X.csv', header=FALSE)); y <- factor(scan('{td}/y.csv', quiet=TRUE))
m <- randomForest(X, y, ntree=1000, mtry=floor(sqrt(ncol(X))), strata=y, sampsize=c({n0},{n0}), replace=TRUE)
write.csv(data.frame(imp=m$importance[,1]), '{td}/imp.csv', row.names=FALSE)
cm <- table(m$y, m$predicted); ba <- mean(diag(cm)/rowSums(cm)); write(ba, '{td}/ba.txt')""")
    subprocess.run(["Rscript", str(td / "rf.R")], check=True, capture_output=True)
    r_imp = pd.read_csv(td / "imp.csv")["imp"].to_numpy()
    r_ba = float(open(td / "ba.txt").read())
msig = fsA.meta.iloc[sig].reset_index(drop=True)
idx_r, _ = models.select_peaks(r_imp, msig["series"].to_numpy(), msig["position"].to_numpy(float), len(A["sets"][A["rf_name"]]), 10)
r_peaks = list(msig["name"].iloc[idx_r])
rf17 = A["sets"][A["rf_name"]]
rho_r = float(pd.Series(imp["importance"].to_numpy()).corr(pd.Series(r_imp), method="spearman"))
within_r = sum(any(abs(float(a[2:]) - float(b[2:])) <= 10 for b in r_peaks) for a in rf17)
# permutation importance (drop in AUC) for the top-50 MDI bands, 5 plot-grouped folds
from sklearn.metrics import roc_auc_score  # noqa: E402
top50 = np.argsort(-imp["importance"].to_numpy())[:50]
drops = np.zeros(50)
_k5 = min(5, F["v3_k"])
_sg5, _ = fl.group_folds(y, groups, _k5, 42)
prng = np.random.default_rng(0)
for tr, te in _sg5:
    m = models.brf(C).fit(Xs[tr], y[tr])
    base = roc_auc_score(y[te], m.predict_proba(Xs[te])[:, 1])
    for k, j in enumerate(top50):
        Xp = Xs[te].copy()
        Xp[:, j] = prng.permutation(Xp[:, j])
        drops[k] += (base - roc_auc_score(y[te], m.predict_proba(Xp)[:, 1])) / _k5
rho_perm = float(pd.Series(imp["importance"].to_numpy()[top50]).corr(pd.Series(drops), method="spearman"))
from sklearn.ensemble import RandomForestClassifier  # noqa: E402
cw = RandomForestClassifier(500, class_weight="balanced", oob_score=True, random_state=42, n_jobs=-1).fit(Xs, y)
oob_pred = cw.oob_decision_function_.argmax(1)
cw_ba = stats.balanced_accuracy(y, oob_pred)
cw_rec = float((oob_pred[y == 0] == 0).mean())
A["rf_checks"] = pd.DataFrame([
    ("Reproducibility: importance of seed 42 vs seed 7 (Spearman ρ)", f"{A['rf_seed_check']['rho']:.3f}",
     f"{A['rf_seed_check']['within10']} of {len(rf17)} peaks within ±10 nm", "PASS" if A["rf_seed_check"]["within10"] >= 0.7 * len(rf17) else "FLAG"),
    (f"R randomForest (stratified sampsize {n0} + {n0}), mean decrease in Gini", f"ρ = {rho_r:.3f}",
     f"{within_r} of {len(rf17)} peaks within ±10 nm; R out-of-bag BA {r_ba:.3f}", "PASS" if within_r >= 0.7 * len(rf17) else "FLAG"),
    (f"Permutation importance (drop in AUC, {_k5} plot-grouped folds) vs Gini, top-50 bands", f"ρ = {rho_perm:.2f}",
     "shuffling one band hardly changes the forest because its neighbours carry the same information"
     if rho_perm < 0.3 else "permutation and Gini rankings agree", "FLAG" if rho_perm < 0.3 else "PASS"),
    ("Ordinary RF with class weights only (no balanced bootstrap), out-of-bag", f"BA {cw_ba:.3f}",
     f"healthy recall {cw_rec:.2f}: class weights alone leave the forest biased" if cw_rec < 0.6 else f"healthy recall {cw_rec:.2f}",
     "PASS"),
], columns=["Check", "Value", "Result", "Status"])
A["rf_r_importance"] = r_imp
for _, r in A["rf_checks"].iterrows():
    A["checks"].append(("A1", r["Check"], "", f"{r['Value']}; {r['Result']}", r["Status"]))

# =================================================================== sensitivity runs (CART-QDA pipeline)
fourtier.log("Sensitivity: band range and duplicates kept")
Clight = copy.deepcopy(C)
Clight["rf"]["n_estimators"] = 50
Clight["rf"]["n_estimators_importance"] = 50
Clight["tier1"]["mixed_model"] = False
Flight = {k: v for k, v in F.items() if k in ("V1", "V3", "V4", "table")}
sens = []
for lab, lo, hi in (("400–2500 nm (main: 350–399 removed)", 400, 2500),
                    ("350–2500 nm (nothing removed)", 350, 2500),
                    ("450–2450 nm (both detector edges trimmed)", 450, 2450)):
    m = (D["wl_full"] >= lo) & (D["wl_full"] <= hi)
    if lab.startswith("400"):
        r = A
    else:
        r = fourtier.run(raw_fs(D["R_full"][:, m], D["wl_full"][m]), y, groups, Flight, Clight, f"sens {lo}-{hi}", mixed=False)
    v = r["validation"].set_index(["Pipeline", "Scheme"])
    sens.append({"Band set": lab, "CART bands": len(r["sets"][r["cart_name"]]),
                 "BA V1": v.loc[("QDA on CART features", "V1"), "BA"], "BA V3 nested": v.loc[("QDA on CART features", "V3"), "BA"],
                 "BA V4 hold-out": v.loc[("QDA on CART features", "V4"), "BA"],
                 "CART bands (nm)": ", ".join(str(int(float(b[2:]))) for b in sorted(r["sets"][r["cart_name"]], key=lambda s: float(s[2:])))})
A["sensitivity_range"] = pd.DataFrame(sens)
# duplicates kept (the 4 unnamed plot-27 copies of 11-02-2026; folds rebuilt with the same seeds)
keepall = ~D["meta_all"]["Exact duplicate (removed)"].to_numpy() | D["meta_all"]["Unnamed"].to_numpy()
keepall &= subset_mask(D["meta_all"], C)
_main = A["validation"].set_index(["Pipeline", "Scheme"])
_rows = [{"Data": f"main: exact duplicates removed (n = {len(y)})", "CART bands": len(cart_set),
          "BA V1": _main.loc[("QDA on CART features", "V1"), "BA"], "BA V3": _main.loc[("QDA on CART features", "V3"), "BA"],
          "BA V4": _main.loc[("QDA on CART features", "V4"), "BA"]}]
if keepall.sum() > len(y):
    ma = D["meta_all"][keepall].reset_index(drop=True)
    Ra = D["R_all"][keepall]
    ya = (ma["Class"].values == "Diseased").astype(int)
    ga = ma["Plot"].astype(str).values
    Fa = fl.make_folds(ya, ga, C)
    ma_wl = (D["wl_full"] >= 400) & (D["wl_full"] <= 2500)
    r = fourtier.run(raw_fs(Ra[:, ma_wl], D["wl_full"][ma_wl]), ya, ga, {k: Fa[k] for k in ("V1", "V3", "V4")}, Clight,
                     "sens duplicates kept", mixed=False)
    v = r["validation"].set_index(["Pipeline", "Scheme"])
    _rows.append({"Data": f"{int(keepall.sum()) - len(y)} unnamed plot-27 copies kept (n = {len(ya)})",
                  "CART bands": len(r["sets"][r["cart_name"]]),
                  "BA V1": v.loc[("QDA on CART features", "V1"), "BA"], "BA V3": v.loc[("QDA on CART features", "V3"), "BA"],
                  "BA V4": v.loc[("QDA on CART features", "V4"), "BA"]})
    A["sensitivity_dups_applicable"] = True
else:
    A["sensitivity_dups_applicable"] = False
A["sensitivity_dups"] = pd.DataFrame(_rows)

A["runtime_min"] = (time.time() - T0) / 60
save(A, "partA")
fourtier.log(f"Stage A done in {A['runtime_min']:.1f} min")
print(A["tier1_tests"])
print(A["sets"])
print(A["tier3"].drop(columns="List"))
print(A["validation"][["Pipeline", "Scheme", "BA", "BA_SD", "AUC", "kappa"]])
print(A["validation_qda_cart"][["Scheme", "Priors", "BA", "BA_SD", "OA"]])
print(A["wilcoxon"])
print(A["sensitivity_range"])
print(A["sensitivity_dups"])
print(A["rf_checks"])
print(A["stability"]["index"].T)
for c in A["checks"]:
    print(c)
