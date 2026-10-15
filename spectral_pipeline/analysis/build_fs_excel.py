"""Workbook for Part FS: feature-selection methods on the K1-K4 pool, step by step."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
from openpyxl import Workbook

import xl
from common import ROOT, WORK, cfg, load
from xl import F_NOTE, Sheet

C = cfg()
R = load("partFS")
D = load("data")
REFS = json.loads((ROOT / "analysis" / "fs_references.json").read_text())
TXT = json.loads((WORK / "fs_conclusions.json").read_text()) if (WORK / "fs_conclusions.json").exists() else {}
FIG = WORK / "figures_fs"
OUT = (ROOT / C["output"]["dir"]).resolve().parent / "WhiteRust_AllDates_FeatureSelection"
OUT.mkdir(parents=True, exist_ok=True)
meta = R["pool_meta"]
names = meta["name"].to_numpy()
y = D["y"]
PCT = "0.0%"
wb = Workbook()
wb.remove(wb.active)
SHEETS = []


def S_(name, title, sub=""):
    s = Sheet(wb, name, title, sub)
    SHEETS.append((name, title))
    return s


def top_table(m, n=20, score_label="Score"):
    r = R["full_rank"].get(m)
    if r is None:
        return pd.DataFrame()
    sc = R["full_score"].get(m)
    rows = []
    for i, j in enumerate(list(r)[:n]):
        j = int(j)
        rows.append({"Rank": i + 1, "Feature": names[j], "Type": meta["type"].iloc[j],
                     "Wavelength (nm)": meta["position"].iloc[j],
                     score_label: (float(sc[j]) if sc is not None and np.ndim(sc) == 1 and len(sc) == len(names) else
                                   (float(sc.get(j, np.nan)) if isinstance(sc, dict) else np.nan))})
    return pd.DataFrame(rows)


def ref_line(keys):
    return "References: " + "; ".join(k for k in keys)


methods = R["methods"]
full = R["full"].set_index("Method")
summ = R["summary"]

# ============================================================== 00 README / 01 Summary
readme = S_("00_README", "Feature-selection methods for white-rust detection — K1 + K2 + K3 + K4 pool",
            "Filter, wrapper and embedded feature selection compared on the same leaves, the same feature pool and the same "
            "held-out plots, to find stable and informative disease-specific features and the method that works best for this dataset.")

S = S_("01_Summary", "Summary — which feature-selection method works best, and which features are disease-specific")
for t in TXT.get("summary", []):
    S.para(t)
S.h2("Composite ranking (accuracy on new plots, stability, separability)")
cp = R["composite"]
S.table(cp[["Overall rank", "Method", "Family", "BA QDA (k=10)", "BA RF (k=10)", "Stability Jaccard (±10 nm)", "J–M (all leaves)", "Mean rank"]],
        fmts={"BA QDA (k=10)": PCT, "BA RF (k=10)": PCT, "Stability Jaccard (±10 nm)": "0.000", "J–M (all leaves)": "0.000", "Mean rank": "0.0"},
        key_rows=[0, 1, 2], widths={"B": 26})
S.h2("Consensus disease-specific features (agreed by many methods across the 20 training sets)")
co = R["consensus"].drop(columns=["idx"]).head(15)
S.table(co, fmts={"Consensus score": "0.000", "AUC": "0.000", "Hedges g": "0.00", "Mixed-model q": "0.0E+00", "Wavelength (nm)": "0"})
cs = R["consensus_set"]
S.para(f"Consensus set (10 features, redundancy-controlled): {', '.join(cs['names'])} — J–M {cs['J–M']:.3f}; QDA balanced accuracy "
       f"{100 * cs['QDA BA V1']:.1f} % in the leaf-level 10-fold protocol of Das et al. (optimistic, all leaves used to choose the set). "
       f"The honest estimate of the consensus approach is the 'Consensus (Borda)' method, whose rank aggregation is redone inside every training set.")

# ============================================================== 02 Design
S = S_("02_Design", "Study design — data, feature pool, training/test units, evaluation")
n_tr = [len(f["train"]) for f in D["folds"]["V4"]]
design = [
    ("Leaves", f"{len(y)} ({int((y == 0).sum())} healthy, {int((y == 1).sum())} diseased); 48 plots; 4 dates, 3 growth stages and 3 varieties pooled"),
    ("Feature pool", f"{len(meta)} features = K1 reflectance 2039 + K2 continuum removal 30 + K3 vegetation indices 30 (MTVI1 = mCARI1 removed) + "
                     "K4 first-derivative bands 2031 + K4 edge parameters 20 (identical to Part C)"),
    ("Extra feature space (CWT)", f"Mexican-hat continuous wavelet transform of the K1 spectrum, scales {R['cwt']['scales']} nm, 5-nm grid: "
                                  f"{len(R['cwt']['names'])} wavelet features ({int(np.sum(R['cwt']['valid']))} outside the cone of influence and the detector joins)"),
    ("Training / test units", "20 units: the 10 plot-grouped folds of the first V3 repeat (StratifiedGroupKFold, seed 101) and the 10 V4 splits "
                              "(30 % of plots held out: 4 healthy + 11 diseased plots). No plot is ever in both training and test leaves."),
    ("Where selection happens", "Every method runs inside each training set only (no information from test plots; Ambroise & McLachlan 2002). "
                                "A separate run on all leaves gives the reported feature lists."),
    ("Feature budget k", "5, 10, 15 and 20 features from each method's ranking; headline comparisons at k = 10"),
    ("Redundancy control", "Plain top-k (as published for most methods) and redundancy-controlled top-k: a candidate correlated |r| ≥ 0.95 "
                           "with an already chosen feature is skipped (cf. the 20-nm minimum distance of Wei et al. 2021)"),
    ("Classifiers on held-out plots", "QDA with equal priors (Tier 4 of Das et al. 2020), LDA with equal priors, Balanced Random Forest (300 trees, k = 10)"),
    ("Imbalance handling", "equal priors (QDA/LDA), balanced class weights (CART, SVM, LASSO, gradient boosting), class-balanced bootstrap "
                           "(Balanced RF, Boruta, RF-RFE), class-balanced Monte-Carlo sub-samples (CARS, MC-UVE), class-balanced instance sampling (ReliefF)"),
    ("Inner validation (methods that tune themselves)", "plot-grouped 5-fold (SPA length, CARS subset, PLS components, CART pruning) or 3-fold "
                                                        "(LASSO C, SFFS and GA criterion) inside the training set"),
    ("Stability", "Kuncheva (2007) index and Jaccard similarity of the 20 top-10 lists; tolerant Jaccard counts a feature of the same series within ±10 nm as the same"),
    ("Separability", "multivariate Jeffries–Matusita distance (0–2) of the top-10 set chosen on all leaves (Tier 3)"),
    ("Method comparison", "Friedman test over the 20 units and Nemenyi critical difference (Demšar 2006); paired Wilcoxon tests against the best method with Holm correction"),
    ("Composite ranking", "mean of the ranks for QDA balanced accuracy, RF balanced accuracy, stability (Jaccard ±10 nm) and J–M"),
    ("Training leaves per unit", f"V4: {min(n_tr)}–{max(n_tr)}; V3: about 2040"),
]
S.table(pd.DataFrame(design, columns=["Item", "Setting"]), widths={"A": 34, "B": 120})
S.image(FIG / "FS01_workflow.png", 1000)

# ============================================================== 03 Methods
S = S_("03_Methods", "The feature-selection methods — family, principle, settings, references")
settings = {
    "Pearson r": "|r| between feature and disease status (0/1)", "ANOVA F": "F = between-class MS / within-class MS (1, n−2 df)",
    "Fisher score": "Σ n_c(μ_c − μ)² / Σ n_c σ_c²", "Chi-square": "10 quantile bins per feature; χ² of the 2 × 10 table",
    "Mutual information": "Kraskov k-NN estimator, 3 neighbours, standardised features", "ReliefF": "10 nearest hits/misses, L1 distance, min–max scaled; all healthy + equal number of diseased leaves as instances",
    "J–M (univariate)": "Gaussian Bhattacharyya distance → J–M = 2(1 − e^−B)", "mRMR": "F-test correlation quotient: F / mean |r| with chosen features",
    "SPA": "chains from the 10 most significant features, ≤ 20 variables; chain and length by inner-CV LDA",
    "MC-UVE": "100 class-balanced 80 % sub-samples, PLS-DA 10 components; reliability c = mean(b)/sd(b); cut-off = max |c| of 4150 noise variables",
    "CWT scalogram": "Mexican-hat CWT, 8 dyadic scales; J–M of each wavelet feature; local maxima of the scalogram ranked by J–M",
    "SVM-RFE": "linear SVM (C = 0.01, balanced); 10 % removed per step to 100, then one at a time",
    "RF-RFE": "Balanced RF (150 trees); 20 % removed per step to 100, 5 at a time to 30, then one at a time",
    "CARS": "50 Monte-Carlo runs (class-balanced 80 %), PLS-DA 10 components, exponentially decreasing function + adaptive reweighted sampling; subset with best inner-CV BA",
    "SFFS (QDA)": "candidates: 100 most significant features (|r| < 0.95 among them); criterion: 3-fold plot-grouped inner-CV QDA BA; sizes 1–20",
    "SFFS (J–M)": "same candidates; criterion: J–M on the training leaves; sizes 1–20",
    "Genetic algorithm": "same candidates; 50 chromosomes × 40 generations, tournament 3, uniform crossover 0.8, mutation 1/100, elitism 2; fitness = inner-CV QDA BA − 0.002 × size",
    "RF importance": "Balanced RF, 500 trees, mean decrease in Gini", "CART importance": "Gini, balanced weights, minsplit 20, minbucket 7, cost-complexity pruning by inner CV",
    "Boruta": "Balanced RF (200 trees) with shuffled shadow features, 60 runs (100 on all leaves), two-sided binomial test, Bonferroni α = 0.01",
    "PLS-VIP": "PLS-DA, 1–15 components chosen by inner-CV BA; VIP > 1 = native subset",
    "LASSO": "L1-logistic regression, balanced weights, C on a 9-point grid 10⁻³–10⁻⁰·⁵ chosen by inner CV; ranking = order of entry along the path",
    "Gradient boosting": "150 trees, depth 3, learning rate 0.1, subsample 0.8, √p features per split, balanced sample weights",
    "Consensus (Borda)": "Borda count of the redundancy-controlled top-20 of every method (r and Fisher score counted once, as ANOVA F)",
}
mt = methods.copy()
mt["Settings used here"] = mt["Method"].map(settings)
mt["Output"] = mt["Method"].map(lambda m: "ranking + own subset" if m in ("SPA", "MC-UVE", "CARS", "Boruta", "PLS-VIP", "LASSO", "CART importance",
                                                                            "SFFS (QDA)", "SFFS (J–M)", "Genetic algorithm") else "ranking")
S.table(mt, widths={"A": 20, "B": 11, "C": 46, "D": 30, "E": 70, "F": 18})
S.para("Pearson r, ANOVA F and Fisher score are algebraically equivalent for two classes (r² = F/(F + n − 2); the Fisher score is F × "
       "constant), so they rank features identically (checked, sheet 31). They are listed for completeness and counted once (as ANOVA F) "
       "in the statistical comparison, the ranking and the consensus.", font=F_NOTE)

# ============================================================== 04 Pool
S = S_("04_Pool", "The feature pool (K1 + K2 + K3 + K4) and its univariate statistics")
comp = meta.groupby("type").size().rename("Features").reset_index().rename(columns={"type": "Feature type"})
S.table(comp)
U = R["univariate_all"]
ua = pd.DataFrame({"Feature": names, "Type": meta["type"], "Wavelength (nm)": meta["position"], "r (point-biserial)": U["r"],
                   "ANOVA F": U["F"], "Fisher score": U["fisher"], "J–M (univariate)": U["jm"]})
for m in ("Chi-square", "Mutual information", "ReliefF", "MC-UVE", "RF importance", "Boruta", "PLS-VIP", "Gradient boosting"):
    sc = R["full_score"].get(m)
    if sc is not None and np.ndim(sc) == 1 and len(sc) == len(names):
        ua[m] = sc
S.para("All scores computed on all 2264 leaves. Higher = more informative for every column (r: its absolute value).", font=F_NOTE)
f, l, L = S.table(ua)
S.ws.freeze_panes = S.ws.cell(row=f, column=2)

# ============================================================== 05-18 method sheets (all leaves)
S = S_("05_F1_Univariate", "Filter 1 — Pearson r, ANOVA F, Fisher score, chi-square, mutual information, univariate J–M",
       "Each feature is scored on its own; the top of the list is then dominated by neighbouring bands of the same region (see sheet 22).")
S.image(FIG / "FS02_score_spectra.png", 950)
for m, lab in (("ANOVA F", "F"), ("Chi-square", "χ²"), ("Mutual information", "MI (nats)"), ("J–M (univariate)", "J–M")):
    t = top_table(m, 20, lab)
    if m == "ANOVA F":
        t["r"] = [U["r"][list(names).index(v)] for v in t["Feature"]]
        t["Fisher score"] = [U["fisher"][list(names).index(v)] for v in t["Feature"]]
        t["Rank by |r|"] = [int(np.where(np.argsort(-U["abs_r"]) == list(names).index(v))[0][0]) + 1 for v in t["Feature"]]
        t["Rank by Fisher"] = [int(np.where(np.argsort(-U["fisher"]) == list(names).index(v))[0][0]) + 1 for v in t["Feature"]]
    S.table(t, title=f"Top 20 — {m}" + (" (identical order by |r| and by Fisher score)" if m == "ANOVA F" else ""), fmts={"Wavelength (nm)": "0"})
S.para(ref_line(["Pearson 1895", "Duda et al. 2001", "Abdulridha et al. 2023 (χ², ANOVA F)", "Kraskov et al. 2004", "Das et al. 2020 (J–M)"]), font=F_NOTE)

S = S_("06_F2_ReliefF", "Filter 2 — ReliefF (Kira & Rendell 1992; Kononenko 1994; used by Mahlein et al. 2013)",
       "ReliefF rewards features that differ between a leaf and its nearest leaves of the other class and agree with its nearest leaves of the same class — a multivariate filter.")
S.table(top_table("ReliefF", 30, "ReliefF weight"), fmts={"Wavelength (nm)": "0"})

S = S_("07_F3_mRMR_SPA_UVE", "Filter 3 — mRMR, successive projections (SPA) and Monte-Carlo UVE")
S.table(top_table("mRMR", 20, "—").drop(columns=["—"]), title="mRMR (F-test correlation quotient; Peng et al. 2005) — order of selection")
inf = R["full_info"].get("SPA") or {}
S.table(top_table("SPA", 20, "—").drop(columns=["—"]), title=f"SPA (Araújo et al. 2001; Zhu et al. 2017) — chain from {names[int(inf.get('start', 0))]}",
        note=f"Chain length chosen by plot-grouped inner-CV LDA: {len(R['full_native']['SPA'])} variables (inner BA {100 * inf.get('inner BA', np.nan):.1f} %).")
inf = R["full_info"].get("MC-UVE") or {}
S.table(top_table("MC-UVE", 20, "Reliability |c|"), title="MC-UVE (Centner et al. 1996; Cai et al. 2008)",
        note=f"Noise cut-off |c| = {inf.get('cutoff |c|', np.nan):.2f}; {len(R['full_native']['MC-UVE'])} of {len(names)} features are more reliable than every noise variable.")

S = S_("08_F4_CWT_Scalogram", "Filter 4 — continuous wavelet analysis: separability scalogram (Cheng et al. 2010)",
       "Every spectrum is decomposed with the Mexican-hat wavelet at 8 dyadic scales; the J–M separability of every wavelet coefficient forms a "
       "scale × wavelength scalogram whose local maxima are the candidate features.")
S.image(FIG / "FS03_cwt_scalogram.png", 950)
cwn = R["cwt"]["names"]
sep = np.asarray(R["full_score"]["CWT scalogram"], float)
o = list(R["full_rank"]["CWT scalogram"])[:25]
S.table(pd.DataFrame([{"Rank": i + 1, "Wavelet feature": cwn[j], "Scale (nm)": int(cwn[j].split()[1][1:]), "Wavelength (nm)": int(cwn[j].split()[2]),
                       "J–M": sep[j]} for i, j in enumerate(o)]), title="Top 25 scalogram peaks (all leaves)")
shp = R["cwt"]["shape"]
M = pd.DataFrame(np.where(np.asarray(R["cwt"]["valid"]).reshape(shp), sep.reshape(shp), np.nan).T, columns=[f"scale {a}" for a in R["cwt"]["scales"]])
M.insert(0, "Wavelength (nm)", R["cwt"]["wl"])
S.table(M, title="Separability scalogram (J–M; blank = cone of influence or detector join)", fmts={c: "0.000" for c in M.columns[1:]} | {"Wavelength (nm)": "0"})

S = S_("09_W1_RFE", "Wrapper 1 — recursive feature elimination: SVM-RFE and RF-RFE (Guyon et al. 2002; Wei et al. 2021; Liu et al. 2024)")
a, b = top_table("SVM-RFE", 20, "—").drop(columns=["—"]), top_table("RF-RFE", 20, "—").drop(columns=["—"])
S.table(a, title="SVM-RFE — last features to be eliminated (rank 1 = survived longest)")
S.table(b, title="RF-RFE — last features to be eliminated")

S = S_("10_W2_CARS", "Wrapper 2 — competitive adaptive reweighted sampling (CARS; Li et al. 2009)")
inf = R["full_info"].get("CARS") or {}
S.image(FIG / "FS13_cars.png", 600)
S.para(f"Best sampling run {inf.get('best run')} of 50 with {len(R['full_native']['CARS'])} variables (inner-CV PLS-DA BA {100 * inf.get('inner BA', np.nan):.1f} %).")
S.table(pd.DataFrame({"Run": np.arange(1, 51), "Variables kept": inf.get("subset sizes", [np.nan] * 50)}), title="Variables retained per run")
S.table(pd.DataFrame({"Feature": names[list(R["full_native"]["CARS"])]}).head(60), title="Variables in the selected CARS subset (first 60)")

S = S_("11_W3_SFFS", "Wrapper 3 — sequential floating forward selection (Pudil et al. 1994; used by Mustafa et al. 2023)",
       "SFFS adds the best feature, then removes features while that improves the criterion. Criterion 1: inner-CV QDA balanced accuracy "
       "(ML-based). Criterion 2: multivariate J–M distance (Tier 3 of Das et al. 2020).")
S.image(FIG / "FS12_wrapper_search.png", 950)
for lab in ("SFFS (QDA)", "SFFS (J–M)"):
    sets, crit = R["full_sffs"][lab]
    if sets:
        S.table(pd.DataFrame([{"Size": k, "Criterion": crit[k], "Features": ", ".join(names[sets[k]])} for k in sorted(sets)]), title=lab,
                widths={"C": 120})

S = S_("12_W4_GA", "Wrapper 4 — genetic algorithm (Leardi et al. 1992; Nagasubramanian et al. 2018)")
S.table(pd.DataFrame({"Feature": names[list(R["full_native"]["Genetic algorithm"])]}), title="Best chromosome (all leaves)")
S.table(top_table("Genetic algorithm", 20, "—").drop(columns=["—"]), title="Features ordered by frequency in the final population")
if R.get("ga_hist"):
    S.table(pd.DataFrame({"Generation": np.arange(1, len(R["ga_hist"]) + 1), "Best fitness": R["ga_hist"]}), title="Best fitness per generation")

S = S_("13_E1_Tree_Importance", "Embedded 1 — Random Forest, CART and gradient-boosting importance (Breiman 2001; Breiman et al. 1984; Friedman 2001; Chen & Guestrin 2016)")
for m, lab in (("RF importance", "MDI"), ("Gradient boosting", "Split-gain importance"), ("CART importance", "Gini importance")):
    S.table(top_table(m, 20, lab), title=m, fmts={"Wavelength (nm)": "0"})
inf = R["full_info"].get("CART importance") or {}
S.para(f"CART pruned at ccp α = {inf.get('ccp_alpha', np.nan):.4g} ({inf.get('leaves')} leaves); {len(R['full_native']['CART importance'])} features used in the tree.", font=F_NOTE)

S = S_("14_E2_Boruta", "Embedded 2 — Boruta all-relevant selection (Kursa & Rudnicki 2010; Mustafa et al. 2022, 2023)")
inf = R["full_info"].get("Boruta") or {}
S.para(f"After {inf.get('runs')} runs: {inf.get('confirmed')} features confirmed, {inf.get('tentative')} tentative, {inf.get('rejected')} rejected. "
       "Boruta answers a different question from the other methods — it finds ALL features that carry some disease information (all-relevant), "
       "not a minimal set — so its confirmed set is large; its ranking (by mean importance) is used for top-k.")
bt = top_table("Boruta", 30, "Mean importance")
S.table(bt, fmts={"Wavelength (nm)": "0"})
nat = R["full_native"]["Boruta"]
S.table(meta.iloc[list(nat)].groupby("type").size().rename("Confirmed").reset_index().rename(columns={"type": "Feature type"}), title="Confirmed features by type")

S = S_("15_E3_PLS_VIP", "Embedded 3 — PLS-DA variable importance in projection (Wold et al. 2001; Chong & Jun 2005)")
inf = R["full_info"].get("PLS-VIP") or {}
S.para(f"{inf.get('components')} PLS components (inner-CV BA {100 * inf.get('inner BA', np.nan):.1f} %); {len(R['full_native']['PLS-VIP'])} features with VIP > 1.")
S.table(top_table("PLS-VIP", 30, "VIP"), fmts={"Wavelength (nm)": "0"})

S = S_("16_E4_LASSO", "Embedded 4 — L1-penalised logistic regression (LASSO; Tibshirani 1996)")
inf = R["full_info"].get("LASSO") or {}
S.para(f"C = {inf.get('C', np.nan):.4g} chosen by inner CV (BA {100 * inf.get('inner BA', np.nan):.1f} %): {inf.get('nonzero at C')} non-zero coefficients.")
S.table(top_table("LASSO", 30, "—").drop(columns=["—"]), title="Order of entry along the regularisation path")

# ============================================================== 17 all-leaf sets
S = S_("17_Selected_AllLeaves", "Top-10 features of every method chosen on all leaves (redundancy-controlled), J–M and QDA (Das protocol)")
S.image(FIG / "FS14_selected_positions.png", 1000)
fl = R["full"].drop(columns=["idx", "space"])
S.table(fl, fmts={"J–M": "0.000", "QDA BA (V1, leaf 10-fold)": PCT, "Mean |r| within set": "0.00", "Mean AUC": "0.000",
                  "Runtime all leaves (s)": "0.0", "Native subset size": "0"}, widths={"C": 90})
S.para("QDA BA (V1) uses the set chosen on all leaves and leaf-level folds — the protocol of Das et al. (2020), optimistic. The honest "
       "comparison is on sheet 18.", font=F_NOTE)

# ============================================================== 18-19 accuracy
S = S_("18_Accuracy", "Accuracy of the selected features on held-out plots (mean of 20 units)",
       "Selection inside each training set; QDA/LDA/RF trained on the training leaves with the selected features; balanced accuracy on the test leaves.")
S.image(FIG / "FS05_accuracy_k10.png", 700)
S.image(FIG / "FS04_ba_vs_k.png", 1000)
g = summ[summ.Guard == "yes"]
pv = g.pivot_table(index=["Method", "Family"], columns="k", values="BA QDA").reset_index()
pv.columns = ["Method", "Family"] + [f"QDA BA k = {k}" for k in pv.columns[2:]]
k10 = g[g.k == 10].set_index("Method")
pv["SD k = 10"] = pv["Method"].map(k10["SD QDA"])
pv["LDA BA k = 10"] = pv["Method"].map(k10["BA LDA"])
pv["RF BA k = 10"] = pv["Method"].map(k10["BA RF"])
pv["AUC QDA k = 10"] = pv["Method"].map(k10["AUC QDA"])
f, l, L = S.table(pv.sort_values("QDA BA k = 10", ascending=False), title="Redundancy-controlled top-k",
                  fmts={c: PCT for c in pv.columns if "BA" in c or c.startswith("SD")} | {"AUC QDA k = 10": "0.000"})
# Excel recomputation of the k = 10 QDA column from the unit table (sheet 19)
S.cell(f - 1, len(pv.columns) + 2, "QDA k = 10 (Excel, from sheet 19)", xl.F_HEAD, fill=xl.FILL_HEAD, align=xl.CENTER, border=True)
mcol = L["Method"]
for r in range(f, l + 1):
    S.cell(r, len(pv.columns) + 2, f'=AVERAGEIFS(\'19_Accuracy_ByUnit\'!$I:$I,\'19_Accuracy_ByUnit\'!$C:$C,{mcol}{r},'
                                     f'\'19_Accuracy_ByUnit\'!$E:$E,"yes",\'19_Accuracy_ByUnit\'!$F:$F,10)', fmt=PCT, border=True)
ref = R["fourtier_ref"].groupby("Method")["BA QDA"].agg(["mean", "std"]).reset_index()
ref.columns = ["Four-tier reference (Part C, same 20 units)", "QDA BA", "SD"]
S.table(ref, fmts={"QDA BA": PCT, "SD": PCT})
gp = summ[summ.Guard == "no"].pivot_table(index="Method", columns="k", values="BA QDA").reset_index()
gp.columns = ["Method"] + [f"QDA BA k = {k}" for k in gp.columns[1:]]
S.table(gp, title="Plain top-k (no redundancy control)", fmts={c: PCT for c in gp.columns[1:]})

S = S_("19_Accuracy_ByUnit", "Balanced accuracy for every unit, method, k and variant (input of sheets 18, 23–25)")
ev = R["eval"][["Unit", "Scheme", "Method", "Family", "Guard", "k", "Size", "BA LDA", "BA QDA", "AUC QDA", "BA RF"]]
f, l, L = S.table(ev, fmts={"BA QDA": PCT, "BA LDA": PCT, "BA RF": PCT, "AUC QDA": "0.000"})
S.ws.freeze_panes = S.ws.cell(row=f, column=4)

S = S_("20_Native_Subsets", "Subsets chosen by each method's own stopping rule (size and accuracy on held-out plots)")
nt = R["native"]
S.table(nt, fmts={"BA QDA": PCT, "BA RF": PCT, "Mean size": "0.0"},
        note="QDA is only fitted when the subset has ≤ 30 features; RF works for any size.")

S = S_("21_Redundancy_Control", "Does removing near-duplicate features help? Plain vs redundancy-controlled top-10")
S.image(FIG / "FS15_redundancy_control.png", 650)
S.table(R["guard_effect"], fmts={c: PCT for c in R["guard_effect"].columns if c != "Method"})

S = S_("22_Stability", "Stability of the selections over the 20 training sets (k = 10)")
S.image(FIG / "FS06_stability_vs_accuracy.png", 750)
S.table(R["stability"], fmts={"Kuncheva index": "0.000", "Jaccard (exact)": "0.000", "Jaccard (±10 nm)": "0.000", "SD Jaccard (±10 nm)": "0.000"},
        note="Kuncheva index: 0 = chance overlap, 1 = identical lists (corrected for chance). Jaccard (±10 nm): a feature of the same spectral series "
             "within 10 nm counts as the same (neighbouring bands carry the same information).")

S = S_("23_Statistical_Tests", "Is the difference between methods real? Friedman, Nemenyi and Wilcoxon–Holm (QDA, top-10, redundancy-controlled)")
fr = R["friedman"]
S.table(pd.DataFrame([("Methods compared (k)", fr["k"]), ("Units (N)", fr["N"]), ("Friedman χ²", fr["chi2"]), ("p", fr["p"]),
                      ("q(0.05, k, ∞)/√2", fr["q_alpha"]), ("Nemenyi critical difference (mean rank)", fr["CD"]), ("Best mean BA", fr["best"])],
                     columns=["Statistic", "Value"]))
S.image(FIG / "FS07_cd_diagram.png", 1000)
S.table(R["mean_ranks"], title="Mean rank over the 20 units (1 = best)", fmts={"Mean rank": "0.00"})
S.table(R["wilcoxon"], title=f"Paired Wilcoxon tests: {fr['best']} vs every other method", fmts={"Mean difference": PCT, "p": "0.0E+00", "Holm p": "0.0E+00"})
bm = R["ba_matrix"].reset_index()
S.table(bm, title="Balanced-accuracy matrix (units × methods) used by the tests", fmts={c: PCT for c in bm.columns[1:]})

# ============================================================== 24 composite ranking with Excel formulas
S = S_("24_Ranking", "Composite ranking — which method works best for this dataset?")
S.image(FIG / "FS10_composite_ranking.png", 650)
cp2 = R["composite"][["Method", "Family", "BA QDA (k=10)", "BA RF (k=10)", "Stability Jaccard (±10 nm)", "J–M (all leaves)"]]
f, l, L = S.table(cp2, fmts={"BA QDA (k=10)": PCT, "BA RF (k=10)": PCT, "Stability Jaccard (±10 nm)": "0.000", "J–M (all leaves)": "0.000"})
for j, h_ in enumerate(["Rank QDA (Excel)", "Rank RF (Excel)", "Rank stability (Excel)", "Rank J–M (Excel)", "Mean rank (Excel)", "Overall (Excel)"]):
    S.cell(f - 1, 7 + j, h_, xl.F_HEAD, fill=xl.FILL_HEAD, align=xl.CENTER, border=True)
for r in range(f, l + 1):
    for j, col in enumerate("CDEF"):
        S.cell(r, 7 + j, f"=RANK({col}{r},{col}${f}:{col}${l},0)+(COUNTIF({col}${f}:{col}${l},{col}{r})-1)/2", fmt="0.0", border=True)
    S.cell(r, 11, f"=AVERAGE(G{r}:J{r})", fmt="0.00", border=True)
    S.cell(r, 12, f"=RANK(K{r},K${f}:K${l},1)", fmt="0", border=True)
S.para("Ranks with ties averaged (RANK + tie correction); lower mean rank = better. The Python ranking on sheet 01 must match these formulas.", font=F_NOTE)
S.table(R["vs_fourtier"], title="Best methods vs the four-tier sets of Part C on the same 20 units (QDA)",
        fmts={"Method BA": PCT, "Four-tier BA": PCT, "Mean difference": PCT, "Wilcoxon p": "0.000"})
S.table(R["runtime"], title="Computing cost (seconds, one CPU core)", fmts={"Mean seconds per training set": "0.0", "All leaves (s)": "0.0"})

# ============================================================== 25-26 consensus
S = S_("25_Consensus_Features", "Stable and informative disease-specific features — agreement between methods")
for t in TXT.get("consensus", []):
    S.para(t)
S.image(FIG / "FS08_selection_frequency.png", 1000)
S.image(FIG / "FS09_consensus_on_spectrum.png", 900)
S.table(R["consensus"].drop(columns=["idx"]), fmts={"Consensus score": "0.000", "AUC": "0.000", "Hedges g": "0.00", "Mixed-model q": "0.0E+00", "Wavelength (nm)": "0"},
        note="Consensus score = mean over the 21 distinct methods of the share of the 20 training sets in which the feature (±10 nm) was in the "
             "method's redundancy-controlled top-10. One representative per ±10 nm region.")
fq = R["consensus_freq"].reset_index(drop=True)
fq = fq[["Feature"] + [c for c in fq.columns if c != "Feature"]]
S.table(fq, title="Selection frequency by method", fmts={c: "0.00" for c in fq.columns[1:]})
cs = R["consensus_set"]
S.table(pd.DataFrame([("Consensus top-10 (redundancy-controlled)", ", ".join(cs["names"])), ("J–M (all leaves)", f"{cs['J–M']:.3f}"),
                      ("QDA BA, leaf-level 10-fold (Das protocol)", f"{100 * cs['QDA BA V1']:.1f} %")], columns=["Item", "Value"]),
        title="Consensus feature set", widths={"B": 100})

# ============================================================== 27 checks, 28 references
S = S_("26_CrossChecks", "Cross-checks of the implementations")
S.table(R["checks"], flag_col="Status", widths={"B": 50, "C": 46, "D": 40})
if R["errors"]:
    S.table(pd.DataFrame([(u, m, e.splitlines()[-1]) for (u, m), e in R["errors"].items()], columns=["Unit", "Method", "Error"]), title="Errors")

S = S_("27_References", "References")
used = ["Abdulridha 2023", "Ambroise 2002", "Araújo 2001", "Breiman 1984", "Breiman 2001", "Cai 2008", "Centner 1996", "Chen 2004", "Chen 2016",
        "Cheng 2010", "Chong 2005", "Das 2020", "Demšar 2006", "Duda 2001", "Friedman 2001", "Guyon 2002", "Guyon 2003", "Kira 1992", "Kohavi 1997",
        "Kononenko 1994", "Kraskov 2004", "Kuncheva 2007", "Kursa 2010", "Leardi 1992", "Lemaître 2017", "Li 2009", "Liu 2024", "Mahlein 2013",
        "Mustafa 2022", "Mustafa 2023", "Nagasubramanian 2018", "Nogueira 2018", "Pedregosa 2011", "Pearson", "Peng 2005", "Pudil 1994", "Rumpf 2010",
        "Saeys 2007", "Saeys 2008", "Thomas 2018", "Tibshirani 1996", "Wei 2021", "Wold 2001", "Zhu 2017"]
S.table(pd.DataFrame({"Reference": sorted(REFS[k] for k in used)}), widths={"A": 180})

# README guide
Rm = readme
Rm.h2("What was done")
Rm.para("The combined pool of disease-sensitive spectral features of Part C (K1 reflectance + K2 continuum removal + K3 vegetation indices + "
        "K4 first-derivative bands and edge parameters; 4150 features) was reduced with 23 feature-selection methods from the crop-disease "
        "literature — 11 filter, 6 wrapper and 6 embedded methods plus a consensus — under one protocol: selection inside the training "
        "leaves only, evaluation on leaves of plots never used for selection, the same 20 training/test units for every method.")
Rm.h2("Sheet guide")
Rm.table(pd.DataFrame([(n, t) for n, t in SHEETS if n != "00_README"], columns=["Sheet", "Contents"]), widths={"A": 26, "B": 120})
Rm.h2("Conventions")
Rm.para("BA = balanced accuracy (mean of healthy and diseased recall); J–M on the 0–2 scale; k = number of features; 'redundancy-controlled' = "
        "a feature correlated |r| ≥ 0.95 with an already chosen one is skipped. Columns marked (Excel) are live formulas.")
path = OUT / "WhiteRust_Mustard_Leaf_FeatureSelection_Filter_Wrapper_Embedded.xlsx"
wb.save(path)
print("saved", path, len(wb.sheetnames), "sheets")
