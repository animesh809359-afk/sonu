"""Four-tier analysis (Das et al. 2020) on 48-plot SMACC endmembers, with
 - Tier 2 by CART or by Random Forest,
 - four ways of handling class imbalance (none, class weights, random under-sampling, SMOTE),
 - three validation schemes (paper-style random 10-fold; plot-grouped nested 4-fold x10; leave-one-plot-out),
 - permutation test with plot labels, and step-by-step cross-checks.
All 1417 endmember spectra and all 483 reflectance bands are used. Results -> results/r48.pkl"""
import pickle, time, warnings, sys
import numpy as np, pandas as pd
from scipy import stats
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis
from sklearn.model_selection import StratifiedKFold, StratifiedGroupKFold
from sklearn.metrics import (confusion_matrix, cohen_kappa_score, matthews_corrcoef, f1_score,
                             balanced_accuracy_score, roc_auc_score, accuracy_score)
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from statsmodels.stats.multitest import multipletests
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler
from load48 import load
from pipeline48 import *
from pipeline48 import FALLBACK, NO_BANDS
warnings.filterwarnings("ignore")
SEED, NREP, NPERM = 42, 10, 100
T0 = time.time()
def log(*a):
    print(f"[{time.time()-T0:6.0f}s]", *a, flush=True)
R, CHECKS = {}, []
def check(step, what, expected, obtained, ok):
    CHECKS.append(dict(step=step, check=what, expected=str(expected), obtained=str(obtained), result="PASS" if ok else "FAIL"))
    log(("[PASS] " if ok else "[FAIL] ") + f"{step}: {what} -> {obtained}")

# ======================================================================= data
meta, wl, X = load()
order = np.lexsort((meta.em.values, meta["plot"].values, (meta["class"] == "diseased").values))   # healthy first, then plot, EM
meta, X = meta.iloc[order].reset_index(drop=True), X[order]
y = (meta["class"] == "diseased").to_numpy().astype(int)
groups = meta["plot"].to_numpy()
N, P = X.shape; nH, nD = int((y == 0).sum()), int((y == 1).sum())
R.update(meta=meta, wl=wl, X=X, y=y, groups=groups)
log(f"data {N} spectra ({nH} healthy, {nD} diseased) x {P} bands; ratio 1:{nD/nH:.2f}")
check("Data", "spectra and bands", "1417 x 483", f"{N} x {P}", (N, P) == (1417, 483))
check("Data", "plots 1-12 healthy, 13-48 diseased", "12 + 36 plots", f"{len(set(groups[y==0]))} + {len(set(groups[y==1]))}",
      set(groups[y == 0]) == set(range(1, 13)) and set(groups[y == 1]) == set(range(13, 49)))
check("Data", "no missing values", 0, int(np.isnan(X).sum()), not np.isnan(X).any())
check("Data", "every spectrum belongs to exactly one plot", "1417", int(meta.spectrum_id.nunique()), meta.spectrum_id.nunique() == N)
R["counts"] = meta.groupby(["plot", "class"]).size().rename("n").reset_index()
R["neg"] = pd.DataFrame({"wavelength_nm": wl, "neg_healthy": (X[y == 0] < 0).sum(0), "neg_diseased": (X[y == 1] < 0).sum(0)})
R["neg_spectra"] = {"healthy": int((X[y == 0] < 0).any(1).sum()), "diseased": int((X[y == 1] < 0).any(1).sum())}

F, p, ssb, ssw = anova(X, y)
Fs = np.array([stats.f_oneway(X[y == 0, j], X[y == 1, j])[0] for j in range(P)])
tuk = np.array([float(pairwise_tukeyhsd(X[:, j], y, alpha=0.05).pvalues[0]) for j in range(P)])
welch = np.array([stats.ttest_ind(X[y == 0, j], X[y == 1, j], equal_var=False)[1] for j in range(P)])
lev = np.array([stats.levene(X[y == 0, j], X[y == 1, j])[1] for j in range(P)])
fdr = multipletests(p, method="fdr_bh")[1]; bonf = multipletests(p, method="bonferroni")[1]
sdH, sdD = X[y == 0].std(0, ddof=1), X[y == 1].std(0, ddof=1)
sp_ = np.sqrt(((nH - 1) * sdH ** 2 + (nD - 1) * sdD ** 2) / (N - 2))
d = (X[y == 1].mean(0) - X[y == 0].mean(0)) / sp_
# plot-level ANOVA (48 plot means; Hurlbert 1984 pseudo-replication check)
pm = pd.DataFrame(X).groupby(groups).mean(); pm_y = np.array([0 if g <= 12 else 1 for g in pm.index])
Fp, pp, _, _ = anova(pm.to_numpy(), pm_y)
R["plot_means"] = pm; R["plot_means_y"] = pm_y
sig = p < 0.05
R["tier1"] = pd.DataFrame({"wavelength_nm": wl, "mean_healthy": X[y == 0].mean(0), "mean_diseased": X[y == 1].mean(0), "sd_healthy": sdH, "sd_diseased": sdD,
    "SS_between": ssb, "SS_within": ssw, "F": F, "p_ANOVA": p, "Tukey_p": tuk, "sig_p05": np.where(sig, "yes", "no"), "Welch_p": welch,
    "Levene_p": lev, "FDR_q": fdr, "Bonferroni_p": bonf, "Cohen_d": d, "F_plot_means": Fp, "p_plot_means": pp})
log(f"Tier 1: {sig.sum()} / {P} bands p<0.05 (FDR {int((fdr<0.05).sum())}, Bonferroni {int((bonf<0.05).sum())}, Welch {int((welch<0.05).sum())}); plot-mean ANOVA {int((pp<0.05).sum())}")
check("Tier 1", "manual F = scipy f_oneway", "max rel diff < 1e-8", f"{np.max(np.abs(F-Fs)/Fs):.1e}", np.max(np.abs(F - Fs) / Fs) < 1e-8)
check("Tier 1", "Tukey HSD decision = ANOVA decision (one pair)", "identical", f"identical at all {P} bands: {bool(np.all((tuk<0.05)==sig))}", bool(np.all((tuk < 0.05) == sig)))


CONFIGS = [(t2, s) for t2 in ("CART", "RF") for s in STRATS]
R.update(STRATS=STRATS, CONFIGS=CONFIGS)

jm_band = np.array([jm2(B1d(X[y == 0, j], X[y == 1, j])) for j in range(P)])
R["jm_band"] = jm_band
sig_idx_all = np.where(sig)[0]
full = {}
for s in STRATS:
    Xr, yr, w = resample(X, y, s, SEED)
    cb, tree, pr = cart_select(Xr, yr, w, sig_idx_all)
    rb, imp = rf_select(Xr, yr, s, sig_idx_all, len(cb))
    if s == "S1":
        # rpart printcp equivalent + 1-SE for the record
        R["tree_S1"] = dict(L=tree.L, Rr=tree.Rr, f=tree.f, thr=tree.thr, counts=tree.counts, feat_idx=tree.feat_idx, pr=pr)
    for t2, b in (("CART", cb), ("RF", rb)):
        Bv = bhatt(X[y == 0][:, b], X[y == 1][:, b])
        cum = [jm2(bhatt(X[y == 0][:, b[:k + 1]], X[y == 1][:, b[:k + 1]])) for k in range(len(b))]
        full[(t2, s)] = dict(bands=b, wl=[float(wl[i]) for i in b], JM=jm2(Bv), B=Bv, cum=cum,
                             cond=[float(np.linalg.cond(np.cov(X[y == k][:, b], rowvar=False))) for k in (0, 1)])
    full[("CART", s)]["tree_nodes"] = len(tree.internal(pr)); full[("RF", s)]["importance"] = imp
    full[("CART", s)]["n_train"] = (int((yr == 0).sum()), int((yr == 1).sum()))
    log(f"full data {s}: CART {len(cb)} bands {[round(float(wl[i])) for i in cb]}  JM {full[('CART', s)]['JM']:.3f} | RF {[round(float(wl[i])) for i in rb]} JM {full[('RF', s)]['JM']:.3f}")
R["full"] = full
check("Imbalance", "under-sampling balances classes", "equal counts", str(full[("CART", "S2")]["n_train"]), full[("CART", "S2")]["n_train"][0] == full[("CART", "S2")]["n_train"][1])
check("Imbalance", "SMOTE balances classes", "equal counts", str(full[("CART", "S3")]["n_train"]), full[("CART", "S3")]["n_train"][0] == full[("CART", "S3")]["n_train"][1])
check("Tier 3", "single-band JM: 1-D closed form = matrix form", "equal", "",
      abs(jm_band[10] - jm2(bhatt(X[y == 0][:, [10]], X[y == 1][:, [10]]))) < 1e-10)

# ======================================================================= Validation V1: paper-style random 10-fold
def v1(t2, s, reps=5):
    b = full[(t2, s)]["bands"]; res = []
    for r in range(reps):
        yp = np.empty(N, int); pb = np.empty(N)
        for tr, te in StratifiedKFold(10, shuffle=True, random_state=SEED + r).split(X, y):
            Xr, yr, _ = resample(X[tr][:, b], y[tr], s, SEED + r)
            m = qda_fit(Xr, yr, s); yp[te] = m.predict(X[te][:, b]); pb[te] = m.predict_proba(X[te][:, b])[:, 1]
        res.append(metrics(y, yp, pb))
    return res
# ======================================================================= Validation V2: plot-grouped nested 4-fold x NREP
def grouped_folds(rep, yy=None):
    yy = y if yy is None else yy
    return list(StratifiedGroupKFold(4, shuffle=True, random_state=SEED + rep).split(X, yy, groups))
def v2(t2, s, yy=None, reps=NREP):
    yy = y if yy is None else yy; out = []
    for r in range(reps):
        yp = np.full(N, -1); pb = np.zeros(N); bands_f = []
        for tr, te in grouped_folds(r, yy):
            m, b, _ = fit_pipeline(X[tr], yy[tr], s, t2, SEED + r)
            yp[te] = m.predict(X[te][:, b]); pb[te] = m.predict_proba(X[te][:, b])[:, 1]; bands_f.append(b)
        mm = metrics(yy, yp, pb); mm["plot"] = plot_level(yy, yp, groups); mm["bands"] = bands_f; out.append(mm)
    return out
# ======================================================================= Validation V3: leave-one-plot-out nested
def v3(t2, s):
    yp = np.full(N, -1); pb = np.zeros(N); bands_f = {}
    for g in range(1, 49):
        te = np.where(groups == g)[0]; tr = np.where(groups != g)[0]
        m, b, _ = fit_pipeline(X[tr], y[tr], s, t2, SEED + g)
        yp[te] = m.predict(X[te][:, b]); pb[te] = m.predict_proba(X[te][:, b])[:, 1]; bands_f[g] = b
    mm = metrics(y, yp, pb); mm["plot"] = plot_level(y, yp, groups); mm["bands"] = bands_f; mm["yp"] = yp; return mm

# leakage checks for the fold generators
f0 = grouped_folds(0)
check("Validation", "grouped folds: no plot in both training and test", "0 shared plots",
      f"max shared = {max(len(set(groups[tr]) & set(groups[te])) for tr, te in f0)}", all(len(set(groups[tr]) & set(groups[te])) == 0 for tr, te in f0))
check("Validation", "grouped folds: every test fold has both classes", "yes",
      str([(len(set(groups[te][y[te]==0])), len(set(groups[te][y[te]==1]))) for tr, te in f0]), all(len(set(y[te])) == 2 for tr, te in f0))
Xr_, yr_, _ = resample(X[f0[0][0]], y[f0[0][0]], "S3", SEED)
check("Validation", "SMOTE applied to training part only (test spectra untouched)", f"train {len(f0[0][0])} -> balanced; test {len(f0[0][1])}",
      f"resampled train {len(yr_)} ({(yr_==0).sum()}/{(yr_==1).sum()}); test {len(f0[0][1])}", (yr_ == 0).sum() == (yr_ == 1).sum())

import os
RESUME = "--resume" in sys.argv and os.path.exists("results/r48_partial.pkl")
V = {}
if RESUME:     # V1-V3 already computed by an earlier run with identical code and seeds
    V = pickle.load(open("results/r48_partial.pkl", "rb"))["V"]; log("resumed V1-V3 from results/r48_partial.pkl")
    assert all("v3" in V[c] for c in CONFIGS)
for (t2, s) in ([] if RESUME else CONFIGS):
    V[(t2, s)] = dict(v1=v1(t2, s))
    log(f"V1 {t2}-{s}: BA {np.mean([m['BA'] for m in V[(t2,s)]['v1']]):.3f}")
for (t2, s) in ([] if RESUME else CONFIGS):
    V[(t2, s)]["v2"] = v2(t2, s)
    log(f"V2 {t2}-{s}: BA {np.mean([m['BA'] for m in V[(t2,s)]['v2']]):.3f} ± {np.std([m['BA'] for m in V[(t2,s)]['v2']]):.3f}; plot BA {np.mean([m['plot']['BA'] for m in V[(t2,s)]['v2']]):.3f}")
    pickle.dump(dict(R=R, V=V), open("results/r48_partial.pkl", "wb"))
for (t2, s) in ([] if RESUME else CONFIGS):
    V[(t2, s)]["v3"] = v3(t2, s)
    log(f"V3 {t2}-{s}: BA {V[(t2,s)]['v3']['BA']:.3f}; plots correct {int((V[(t2,s)]['v3']['plot']['table'].pred == V[(t2,s)]['v3']['plot']['table'].t).sum())}/48")
    pickle.dump(dict(R=R, V=V), open("results/r48_partial.pkl", "wb"))
R["V"] = V
R["no_bands_real"] = len(NO_BANDS); log("folds without any significant/selected band (real labels):", len(NO_BANDS))
NO_BANDS.clear()

# ======================================================================= benchmark: RF classifier on all 483 bands (class-weighted)
def rf_bench_v2(reps=NREP):
    out = []
    for r in range(reps):
        yp = np.full(N, -1); pb = np.zeros(N)
        for tr, te in grouped_folds(r):
            m = rf_model("S1").fit(X[tr], y[tr]); yp[te] = m.predict(X[te]); pb[te] = m.predict_proba(X[te])[:, 1]
        mm = metrics(y, yp, pb); mm["plot"] = plot_level(y, yp, groups); out.append(mm)
    return out
R["bench_rf_v2"] = rf_bench_v2()
log(f"RF benchmark (all bands, class-weighted) V2 BA {np.mean([m['BA'] for m in R['bench_rf_v2']]):.3f}")

# ======================================================================= permutation test (plot labels shuffled; grouped 4-fold, 1 repetition)
best = {}
for t2 in ("CART", "RF"):
    best[t2] = max(STRATS, key=lambda s: np.mean([m["BA"] for m in V[(t2, s)]["v2"]]))
R["best"] = best
log("best strategy per tier-2:", best)
rng = np.random.default_rng(SEED); perm = {}
plot_ids = np.arange(1, 49); true_plot_lab = np.array([0 if g <= 12 else 1 for g in plot_ids])
for t2 in ("CART", "RF"):
    s = best[t2]; null = []
    nperm = NPERM
    for i in range(nperm):
        lab = rng.permutation(true_plot_lab); yy = lab[groups - 1]
        null.append(v2(t2, s, yy=yy, reps=1)[0]["BA"])
        if i % 10 == 0: log(f"perm {t2} {i}/{nperm}")
    obs = V[(t2, s)]["v2"][0]["BA"]
    perm[t2] = dict(strategy=s, null=np.array(null), observed=obs, p=(1 + np.sum(np.array(null) >= obs)) / (len(null) + 1))
    log(f"permutation {t2}-{s}: observed BA {obs:.3f}, null mean {np.mean(null):.3f} max {np.max(null):.3f}, p = {perm[t2]['p']:.4f}")
    check("Validation", f"permutation null ({t2}) centred near chance", "≈ 0.50", f"{np.mean(null):.3f}", abs(np.mean(null) - 0.5) < 0.06)
R["perm"] = perm
R["no_bands_perm"] = len(NO_BANDS); log("permutation folds without any significant/selected band (prior-only prediction):", len(NO_BANDS))

# ======================================================================= remaining cross-checks
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis as QDA
b = full[("CART", "S1")]["bands"]; tr, te = f0[0]
m = qda_fit(X[tr][:, b], y[tr], "S1")
def qda_manual(Xt, yt, Xe, pri):
    sc = []
    for k in (0, 1):
        Xk = Xt[yt == k]; mu = Xk.mean(0); C = np.cov(Xk, rowvar=False); dd = Xe - mu
        sc.append(-0.5 * np.linalg.slogdet(C)[1] - 0.5 * np.einsum("ij,ij->i", dd @ np.linalg.inv(C), dd) + np.log(pri[k]))
    return np.argmax(np.stack(sc, 1), 1)
check("Tier 4", "hand-coded QDA (equal priors) = sklearn QDA", "100% agreement",
      f"{(qda_manual(X[tr][:, b], y[tr], X[te][:, b], [0.5, 0.5]) == m.predict(X[te][:, b])).mean()*100:.1f}%",
      np.all(qda_manual(X[tr][:, b], y[tr], X[te][:, b], [0.5, 0.5]) == m.predict(X[te][:, b])))
mm = V[("CART", "S1")]["v2"][0]
check("Tier 4", "balanced accuracy = mean of sensitivity and specificity", "equal", f"{mm['BA']:.4f} vs {(mm['sens_D']+mm['spec_H'])/2:.4f}", abs(mm["BA"] - (mm["sens_D"] + mm["spec_H"]) / 2) < 1e-12)
check("Tier 4", "confusion matrix total = all spectra", N, int(mm["cm"].sum()), mm["cm"].sum() == N)
tt = RpartTree().fit(X, y, resample(X, y, "S1", SEED)[2], sig_idx_all)
check("Tier 2", "weighted tree: root weighted counts equal (class weighting works)", "healthy weight = diseased weight",
      f"{tt.counts[0,0]:.1f} vs {tt.counts[0,1]:.1f}", abs(tt.counts[0, 0] - tt.counts[0, 1]) < 1e-6)
check("Tier 2", "unpruned custom tree reproduces sklearn predictions", "100%",
      f"{(tt.predict(X, np.zeros(len(tt.L), bool)) == tt.clf.predict(X[:, sig_idx_all])).mean()*100:.1f}%",
      np.all(tt.predict(X, np.zeros(len(tt.L), bool)) == tt.clf.predict(X[:, sig_idx_all])))
for (t2, s), v in full.items():
    if not set(v["bands"]) <= set(sig_idx_all): check("Tier 2", f"{t2}-{s} bands within significant set", "subset", "NOT subset", False)
check("Tier 2", "all selected band sets are subsets of the ANOVA-significant bands", "subset", "yes", all(set(v["bands"]) <= set(sig_idx_all) for v in full.values()))
R["fallbacks"] = len(FALLBACK); log("QDA fallbacks:", len(FALLBACK))
R["checks"] = pd.DataFrame(CHECKS)
pickle.dump(R, open("results/r48.pkl", "wb"))
log("DONE;", (R["checks"].result == "PASS").sum(), "/", len(R["checks"]), "checks pass")
