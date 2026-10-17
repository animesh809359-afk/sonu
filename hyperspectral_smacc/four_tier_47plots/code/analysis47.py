"""Four-tier analysis (Das et al. 2020) of SMACC endmembers from 47 plots (plot 4 excluded):
healthy plots 1-3, 5-12 (98 endmembers each), diseased plots 13-48 (30 each). Every endmember is one sample; reflectance only.
 Tier 1 one-way ANOVA (+ Tukey HSD)  ->  Tier 2 CART or Random Forest  ->  Tier 3 Jeffries-Matusita  ->  Tier 4 QDA
Validation: CV1 = Das et al. (10-fold CV of QDA, random over spectra), CV2 plot-grouped nested 4-fold x10, CV3 leave-one-plot-out,
CV4-CV6 leave-one-treatment-combination / variety / inoculation-date-out, plot-label permutation test, block-vs-block negative
control, restricted (block) permutation, sensitivity analysis with the band removal of Das et al. Results -> results/r47.pkl
Usage: python analysis47.py HEALTHY_SMACC_EM.csv DISEASED_SMACC_EM.csv treatment_detail.xlsx EXCEPTPLOT4.xml"""
import pickle, re, sys, time, warnings
import numpy as np, pandas as pd
from scipy import stats
from sklearn.model_selection import StratifiedKFold, StratifiedGroupKFold
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from statsmodels.stats.multitest import multipletests
from pipeline47 import *
from pipeline47 import FALLBACK, NO_BANDS
warnings.filterwarnings("ignore")
SEED, NREP, NPERM, NREP_NC, NBOOT = 42, 10, 100, 5, 2000
import os
QUICK = os.environ.get("QUICK") == "1"          # smoke test only (fewer repetitions, 50 trees) -> results/r47_quick.pkl
if QUICK:
    import pipeline47; pipeline47.rf_model.__defaults__ = (50,)
    NREP, NPERM, NREP_NC, NBOOT = 2, 3, 2, 50
T0 = time.time()
def log(*a): print(f"[{time.time()-T0:6.0f}s]", *a, flush=True)
R, CHECKS = {}, []
def check(step, what, expected, obtained, ok):
    CHECKS.append(dict(step=step, check=what, expected=str(expected), obtained=str(obtained), result="PASS" if ok else "FAIL"))
    log(("[PASS] " if ok else "[FAIL] ") + f"{step}: {what} -> {obtained}")
def save(name=None):
    name = name or ("results/r47_quick_partial.pkl" if os.environ.get("QUICK") == "1" else "results/r47_partial.pkl")
    R["checks"] = pd.DataFrame(CHECKS); pickle.dump(R, open(name, "wb"))

# ======================================================================= data
FH, FD, FT, FX = sys.argv[1:5]
recs = []
for f, cl in ((FH, "healthy"), (FD, "diseased")):
    df = pd.read_csv(f); wl_ = df.iloc[:, 0].to_numpy(float)
    if not recs: wl = wl_
    assert np.allclose(wl, wl_)
    for c in df.columns[1:]:
        m = re.match(r"P(\d+)_EM(\d+)$", c)
        recs.append(dict(plot=int(m.group(1)), em=int(m.group(2)), spectrum_id=c, cls=cl, vals=df[c].to_numpy(float)))
recs.sort(key=lambda r: (r["cls"] == "diseased", r["plot"], r["em"]))
X = np.array([r["vals"] for r in recs]); meta = pd.DataFrame([{k: r[k] for k in ("plot", "em", "spectrum_id", "cls")} for r in recs]).rename(columns={"cls": "class"})
y = (meta["class"] == "diseased").to_numpy().astype(int); groups = meta["plot"].to_numpy()
N, P = X.shape; nH, nD = int((y == 0).sum()), int((y == 1).sum())
PH, PD = sorted(int(g) for g in set(groups[y == 0])), sorted(int(g) for g in set(groups[y == 1]))
R.update(meta=meta, wl=wl, X=X, y=y, groups=groups, PH=PH, PD=PD)
log(f"data {N} spectra ({nH} healthy in {len(PH)} plots, {nD} diseased in {len(PD)} plots) x {P} bands")
check("Data", "spectra and bands", "2158 x 483", f"{N} x {P}", (N, P) == (2158, 483))
check("Data", "healthy plots 1-3, 5-12 (plot 4 absent); diseased plots 13-48", "11 + 36 plots", f"{PH} + {len(PD)} plots",
      PH == [1, 2, 3] + list(range(5, 13)) and PD == list(range(13, 49)))
cnt = meta.groupby("plot").size()
check("Data", "98 endmembers per healthy plot, 30 per diseased plot", "98 / 30", f"{sorted(set(cnt[PH]))} / {sorted(set(cnt[PD]))}",
      set(cnt[PH]) == {98} and set(cnt[PD]) == {30})
check("Data", "no missing values", 0, int(np.isnan(X).sum()), not np.isnan(X).any())
check("Data", "no duplicated spectrum", 0, int(pd.DataFrame(X).duplicated().sum()), not pd.DataFrame(X).duplicated().any())
R["counts"] = meta.groupby(["plot", "class"]).size().rename("n").reset_index()
R["neg"] = pd.DataFrame({"wavelength_nm": wl, "neg_healthy": (X[y == 0] < 0).sum(0), "neg_diseased": (X[y == 1] < 0).sum(0),
                         "gt1_healthy": (X[y == 0] > 1).sum(0), "gt1_diseased": (X[y == 1] > 1).sum(0)})
R["neg_spectra"] = {"healthy": int((X[y == 0] < 0).any(1).sum()), "diseased": int((X[y == 1] < 0).any(1).sum()),
                    "gt1_healthy": int((X[y == 0] > 1).any(1).sum()), "gt1_diseased": int((X[y == 1] > 1).any(1).sum())}
# design and plot positions
td = pd.read_excel(FT); td.columns = ["plot", "date", "variety", "block"]; td = td.astype({"plot": int}).set_index("plot").sort_index()
td = td.loc[PH + PD]
txt = open(FX).read(); cen, polys = {}, {}
for m in re.finditer(r'<Region name="ROI #(\d+)".*?<Coordinates>(.*?)</Coordinates>', txt, re.S):
    v = np.array(m.group(2).split(), float).reshape(-1, 2); polys[int(m.group(1))] = v
lat0 = np.mean([p[:, 1].mean() for p in polys.values()]); lon0 = np.mean([p[:, 0].mean() for p in polys.values()])
def xy(p): return np.column_stack([(p[:, 0] - lon0) * 111320 * np.cos(np.radians(lat0)), (p[:, 1] - lat0) * 110850])
R["polys_xy"] = {k: xy(p) for k, p in polys.items()}
td["x_m"] = [R["polys_xy"][k][:, 0].mean() for k in td.index]; td["y_m"] = [R["polys_xy"][k][:, 1].mean() for k in td.index]
td["class"] = np.where(td.block == "C", "healthy", "diseased"); td["n_spectra"] = cnt.reindex(td.index).values
check("Design", "ROI file has the 47 analysed plots (plot 4 absent)", "47", f"{len(polys)} ROIs; missing {sorted(set(range(1, 49)) - set(polys))}", sorted(polys) == PH + PD)
check("Design", "treatment sheet: block C = healthy plots, R1-R3 = diseased plots", "yes", str(td.groupby("block").size().to_dict()),
      set(td.index[td.block == "C"]) == set(PH) and set(td.index[td.block != "C"]) == set(PD))
R["design"] = td; R["block_centroids"] = td.groupby("block")[["x_m", "y_m"]].mean()
sb, sv, sd = td.block.reindex(groups).values, td.variety.reindex(groups).values, td.date.reindex(groups).values

# ======================================================================= Tier 1
F, p, ssb, ssw = anova(X, y)
Fs = np.array([stats.f_oneway(X[y == 0, j], X[y == 1, j])[0] for j in range(P)])
tuk = np.array([float(pairwise_tukeyhsd(X[:, j], y, alpha=0.05).pvalues[0]) for j in range(P)])
welch = np.array([stats.ttest_ind(X[y == 0, j], X[y == 1, j], equal_var=False)[1] for j in range(P)])
lev = np.array([stats.levene(X[y == 0, j], X[y == 1, j])[1] for j in range(P)])
fdr = multipletests(p, method="fdr_bh")[1]; bonf = multipletests(p, method="bonferroni")[1]
sdH, sdD = X[y == 0].std(0, ddof=1), X[y == 1].std(0, ddof=1)
d = (X[y == 1].mean(0) - X[y == 0].mean(0)) / np.sqrt(((nH - 1) * sdH ** 2 + (nD - 1) * sdD ** 2) / (N - 2))
pm = pd.DataFrame(X).groupby(groups).mean(); pm_y = np.array([0 if g in PH else 1 for g in pm.index])
Fp, pp, _, _ = anova(pm.to_numpy(), pm_y)
jm_band = np.array([jm2(B1d(X[y == 0, j], X[y == 1, j])) for j in range(P)])
sig = p < 0.05
R["tier1"] = pd.DataFrame({"wavelength_nm": wl, "mean_healthy": X[y == 0].mean(0), "mean_diseased": X[y == 1].mean(0), "sd_healthy": sdH, "sd_diseased": sdD,
    "SS_between": ssb, "SS_within": ssw, "F": F, "p_ANOVA": p, "Tukey_p": tuk, "sig_p05": np.where(sig, "yes", "no"), "Welch_p": welch, "Levene_p": lev,
    "FDR_q": fdr, "Bonferroni_p": bonf, "Cohen_d": d, "F_plot_means": Fp, "p_plot_means": pp, "JM_band": jm_band})
R["plot_means"] = pm; R["jm_band"] = jm_band
log(f"Tier 1: {sig.sum()}/{P} bands p<0.05 (FDR {(fdr<0.05).sum()}, Bonferroni {(bonf<0.05).sum()}, Welch {(welch<0.05).sum()}); plot means {(pp<0.05).sum()}")
check("Tier 1", "manual F = scipy f_oneway", "max rel diff < 1e-8", f"{np.max(np.abs(F-Fs)/Fs):.1e}", np.max(np.abs(F - Fs) / Fs) < 1e-8)
check("Tier 1", "Tukey HSD decision = ANOVA decision (one pair)", "identical", f"identical at all {P} bands: {bool(np.all((tuk<0.05)==sig))}", bool(np.all((tuk < 0.05) == sig)))
check("Tier 3", "single-band JM: 1-D closed form = matrix form", "equal", f"{jm_band[100]:.6f}", abs(jm_band[100] - jm2(bhatt(X[y == 0][:, [100]], X[y == 1][:, [100]]))) < 1e-10)

# ======================================================================= Tier 2 / Tier 3 on all data
CFG = [("CART", "S0"), ("RF", "S0")]
R["CONFIGS"] = CFG; R["STRATS"] = {"S0": "No re-sampling (classes balanced 1078 : 1080)"}
def first_use_order(tree, pr):
    """CART bands in the order they are first used, root first (breadth-first)."""
    order, q = [], [0]
    while q:
        nd = q.pop(0)
        if tree.L[nd] == -1 or pr[nd]: continue
        b = int(tree.feat_idx[tree.f[nd]])
        if b not in order: order.append(b)
        q += [tree.L[nd], tree.Rr[nd]]
    return order
def tier23(Xa, ya, sig_idx, tag=""):
    Xr, yr, w = resample(Xa, ya, "S0", SEED)
    cb, tree, pr = cart_select(Xr, yr, w, sig_idx); cb = first_use_order(tree, pr)
    rb, imp = rf_select(Xr, yr, "S0", sig_idx, len(cb))
    out = {}
    for t2, b in (("CART", cb), ("RF", rb)):
        Bv = bhatt(Xa[ya == 0][:, b], Xa[ya == 1][:, b])
        out[t2] = dict(bands=b, wl=[float(wl[i]) for i in b], JM=jm2(Bv), B=Bv,
                       cum=[jm2(bhatt(Xa[ya == 0][:, b[:k + 1]], Xa[ya == 1][:, b[:k + 1]])) for k in range(len(b))],
                       jm_single=[jm2(B1d(Xa[ya == 0, i], Xa[ya == 1, i])) for i in b])
    out["CART"].update(tree=dict(L=tree.L, Rr=tree.Rr, f=tree.f, thr=tree.thr, counts=tree.counts, feat_idx=tree.feat_idx, pr=pr),
                       nodes=len(tree.internal(pr)), seq=[(float(c), int(len(tree.internal(q_)))) for c, q_ in tree.seq],
                       train_acc=float(np.mean(tree.predict(Xa, pr) == ya)))
    out["RF"]["importance"] = imp
    return out
sig_idx_all = np.where(sig)[0]
full = tier23(X, y, sig_idx_all)
R["full"] = full
for t2 in ("CART", "RF"):
    log(f"Tier 2 {t2}: {len(full[t2]['bands'])} bands {[round(w) for w in full[t2]['wl']]}; Tier 3 JM {full[t2]['JM']:.3f}; max single-band JM {max(full[t2]['jm_single']):.3f}")
check("Tier 2", "CART and RF bands are ANOVA-significant", "subset", "yes", all(set(full[t]["bands"]) <= set(sig_idx_all) for t in ("CART", "RF")))
check("Tier 2", "RF keeps as many bands as CART", len(full["CART"]["bands"]), len(full["RF"]["bands"]), len(full["CART"]["bands"]) == len(full["RF"]["bands"]))
check("Tier 3", "cumulative JM of all bands = set JM", "equal", f"{full['CART']['cum'][-1]:.6f} vs {full['CART']['JM']:.6f}", abs(full["CART"]["cum"][-1] - full["CART"]["JM"]) < 1e-12)
save()

# ======================================================================= helpers for validation
def run_folds(folds, t2, s, Xs, ys, seeds, sig_idx=None):
    yp = np.full(len(ys), -1); pb = np.zeros(len(ys)); bands = []
    for (tr, te), sd_ in zip(folds, seeds):
        m, b, _ = fit_pipeline(Xs[tr], ys[tr], s, t2, sd_)
        yp[te] = m.predict(Xs[te][:, b]); pb[te] = m.predict_proba(Xs[te][:, b])[:, 1]; bands.append(b)
    return yp, pb, bands
def acc(cm):
    cm = np.asarray(cm, float); n = cm.sum(); a, b, c, d_ = cm[0, 0], cm[0, 1], cm[1, 0], cm[1, 1]
    dv = lambda u, v: u / v if v > 0 else np.nan
    OA = (a + d_) / n; PA_H, PA_D, UA_H, UA_D = dv(a, a + b), dv(d_, c + d_), dv(a, a + c), dv(d_, b + d_)
    pe = ((a + b) * (a + c) + (c + d_) * (b + d_)) / n ** 2
    Q = 0.5 * (abs((a + b) - (a + c)) + abs((c + d_) - (b + d_))) / n
    return dict(n=n, OA=OA, BA=(PA_H + PA_D) / 2, kappa=dv(OA - pe, 1 - pe), PA_H=PA_H, UA_H=UA_H, PA_D=PA_D, UA_D=UA_D,
                F1_H=dv(2 * PA_H * UA_H, PA_H + UA_H), F1_D=dv(2 * PA_D * UA_D, PA_D + UA_D),
                MCC=dv(a * d_ - b * c, np.sqrt((a + b) * (a + c) * (d_ + b) * (d_ + c))), QD=Q, AD=(1 - OA) - Q)
AKEYS = ["OA", "BA", "kappa", "PA_H", "UA_H", "PA_D", "UA_D", "F1_H", "F1_D", "MCC", "QD", "AD"]
RNG = np.random.default_rng(SEED)
def cm_by_plot(yt, yp, grp):
    return {int(g): np.array([[np.sum((yt[grp == g] == i) & (yp[grp == g] == j)) for j in (0, 1)] for i in (0, 1)]) for g in np.unique(grp)}
def cluster_ci(per_plot, nboot=NBOOT):
    vals = {k: [] for k in AKEYS}
    for _ in range(nboot):
        pick = list(RNG.choice(PH, len(PH))) + list(RNG.choice(PD, len(PD)))
        m = acc(sum(per_plot[g] for g in pick))
        for k in AKEYS: vals[k].append(m[k])
    return {k: (float(np.nanpercentile(v, 2.5)), float(np.nanpercentile(v, 97.5))) for k, v in vals.items()}
def assess(preds, ci=True):
    pp_s, pp_p = {}, {}
    for yp in preds:
        for g, c in cm_by_plot(y, yp, groups).items(): pp_s[g] = pp_s.get(g, 0) + c
        t = plot_level(y, yp, groups)["table"]
        for g in t.index:
            c = np.zeros((2, 2), int); c[int(t.t[g]), int(t.pred[g])] = 1; pp_p[int(g)] = pp_p.get(int(g), 0) + c
    cms, cmp_ = sum(pp_s.values()), sum(pp_p.values())
    o = dict(spectra=dict(cm=cms, **acc(cms), reps=len(preds)), plots=dict(cm=cmp_, **acc(cmp_), reps=len(preds)))
    if ci: o["spectra"]["ci"] = cluster_ci(pp_s); o["plots"]["ci"] = cluster_ci(pp_p)
    return o

# ======================================================================= CV1: Das et al. - 10-fold CV of QDA on the Tier-2 bands (random over spectra)
V = {c: {} for c in CFG}
for (t2, s) in CFG:
    b = full[t2]["bands"]; preds, reps = [], []
    for r in range(NREP):
        yp = np.empty(N, int); pb = np.empty(N)
        for tr, te in StratifiedKFold(10, shuffle=True, random_state=SEED + r).split(X, y):
            m = qda_fit(X[tr][:, b], y[tr], s); yp[te] = m.predict(X[te][:, b]); pb[te] = m.predict_proba(X[te][:, b])[:, 1]
        preds.append(yp); mm = metrics(y, yp, pb); mm["plot"] = plot_level(y, yp, groups); reps.append(mm)
    V[(t2, s)]["CV1"] = dict(reps=reps, preds=np.array(preds), acc=assess(preds, ci=False), acc_rep1=assess(preds[:1], ci=False))
    log(f"CV1 (Das et al.) {t2}: OA {reps[0]['OA']:.3f} (rep 1), mean OA {np.mean([m['OA'] for m in reps]):.3f}, BA {np.mean([m['BA'] for m in reps]):.3f}")
save()

# ======================================================================= CV2: plot-grouped nested 4-fold x 10
def grouped_folds(rep, yy=None, gg=None, XX=None):
    yy = y if yy is None else yy; gg = groups if gg is None else gg; XX = X if XX is None else XX
    return list(StratifiedGroupKFold(4, shuffle=True, random_state=SEED + rep).split(XX, yy, gg))
f0 = grouped_folds(0)
check("Validation", "CV2 folds: no plot in both training and test", "0 shared plots", f"max shared = {max(len(set(groups[tr]) & set(groups[te])) for tr, te in f0)}",
      all(len(set(groups[tr]) & set(groups[te])) == 0 for tr, te in f0))
check("Validation", "CV2 folds: every test fold has healthy and diseased plots", "yes",
      str([(len(set(groups[te][y[te] == 0])), len(set(groups[te][y[te] == 1]))) for tr, te in f0]), all(len(set(y[te])) == 2 for tr, te in f0))
for (t2, s) in CFG:
    preds, reps = [], []
    for r in range(NREP):
        yp, pb, bands = run_folds(grouped_folds(r), t2, s, X, y, [SEED + r] * 4)
        mm = metrics(y, yp, pb); mm["plot"] = plot_level(y, yp, groups); mm["bands"] = bands; reps.append(mm); preds.append(yp)
    V[(t2, s)]["CV2"] = dict(reps=reps, preds=np.array(preds), acc=assess(preds))
    a = V[(t2, s)]["CV2"]["acc"]
    log(f"CV2 {t2}: BA {np.mean([m['BA'] for m in reps]):.3f} ± {np.std([m['BA'] for m in reps], ddof=1):.3f}; pooled OA {a['spectra']['OA']:.3f} "
        f"BA {a['spectra']['BA']:.3f} [{a['spectra']['ci']['BA'][0]:.3f}, {a['spectra']['ci']['BA'][1]:.3f}]; plot BA {a['plots']['BA']:.3f}")
    save()

# ======================================================================= CV3: leave-one-plot-out
for (t2, s) in CFG:
    folds = [(np.where(groups != g)[0], np.where(groups == g)[0]) for g in PH + PD]
    yp, pb, bands = run_folds(folds, t2, s, X, y, [SEED + g for g in PH + PD])
    mm = metrics(y, yp, pb); mm["plot"] = plot_level(y, yp, groups); mm["bands"] = bands; mm["yp"] = yp
    V[(t2, s)]["CV3"] = dict(reps=[mm], preds=yp[None, :], acc=assess([yp]))
    tb = mm["plot"]["table"]
    log(f"CV3 {t2}: BA {mm['BA']:.3f}; plots correct {int((tb.pred == tb.t).sum())}/47; plot BA {mm['plot']['BA']:.3f}")
    save()

# ======================================================================= CV4-CV6: design-based (leave-one-level-out)
combos = sorted(td.groupby(["variety", "date"]).groups.keys())
SCHEMES = {"CV4": ("Leave-one-treatment-combination-out", [np.where((sv == v) & (sd == d_))[0] for v, d_ in combos], [f"{v}×{d_}" for v, d_ in combos]),
           "CV5": ("Leave-one-variety-out", [np.where(sv == v)[0] for v in sorted(td.variety.unique())], sorted(td.variety.unique())),
           "CV6": ("Leave-one-inoculation-date-out", [np.where(sd == d_)[0] for d_ in sorted(td.date.unique())], sorted(td.date.unique()))}
for k, (nm, tests, labels) in SCHEMES.items():
    allte = np.concatenate(tests)
    one_class = [lab for lab, te in zip(labels, tests) if len(set(y[te])) < 2]
    check("Validation", f"{k} {nm}: every spectrum tested exactly once", f"{len(tests)} folds", f"{len(tests)} folds; folds with one class only: {one_class or 'none'}",
          len(allte) == N and len(set(allte)) == N)
R["SCHEMES"] = {k: (v[0], v[2]) for k, v in SCHEMES.items()}
for k, (nm, tests, labels) in SCHEMES.items():
    folds = [(np.setdiff1d(np.arange(N), te), te) for te in tests]
    for (t2, s) in CFG:
        NO_BANDS.clear()
        yp, pb, bands = run_folds(folds, t2, s, X, y, [SEED + i for i in range(len(folds))])
        mm = metrics(y, yp, pb); mm["plot"] = plot_level(y, yp, groups); mm["bands"] = bands; mm["no_band_folds"] = len(NO_BANDS)
        mm["per_fold"] = [dict(label=lab, acc=float(np.mean(yp[te] == y[te])), BA=float(metrics(y[te], yp[te])["BA"]) if len(set(y[te])) == 2 else None,
                               plots=len(set(groups[te])), healthy_plots=len(set(groups[te][y[te] == 0]))) for lab, te in zip(labels, tests)]
        V[(t2, s)][k] = dict(reps=[mm], preds=yp[None, :], acc=assess([yp]))
        log(f"{k} {t2}: BA {mm['BA']:.3f}; plot BA {mm['plot']['BA']:.3f}")
R["V"] = V; save()

# ======================================================================= permutation test (plot labels shuffled, 11 healthy / 36 diseased kept)
perm = {}
true_lab = np.array([0] * len(PH) + [1] * len(PD)); plots_all = np.array(PH + PD)
rngp = np.random.default_rng(SEED)
for (t2, s) in CFG:
    null = []
    for i in range(NPERM):
        lab = dict(zip(plots_all, rngp.permutation(true_lab))); yy = np.array([lab[g] for g in groups])
        yp, pb, _ = run_folds(grouped_folds(0, yy), t2, s, X, yy, [SEED] * 4); null.append(metrics(yy, yp)["BA"])
        if i % 20 == 0: log(f"permutation {t2} {i}/{NPERM}")
    obs = V[(t2, s)]["CV2"]["reps"][0]["BA"]
    perm[t2] = dict(null=np.array(null), observed=obs, p=(1 + np.sum(np.array(null) >= obs)) / (NPERM + 1))
    log(f"permutation {t2}: observed {obs:.3f}, null mean {np.mean(null):.3f}, max {np.max(null):.3f}, p = {perm[t2]['p']:.4f}")
    check("Validation", f"permutation null ({t2}) centred near chance", "≈ 0.50", f"{np.mean(null):.3f}", abs(np.mean(null) - 0.5) < 0.06)
R["perm"] = perm; save()

# ======================================================================= negative control: block vs block (class weights, plot-grouped CV)
PAIRS = [("C", "R3"), ("C", "R2"), ("C", "R1"), ("R3", "R2"), ("R2", "R1"), ("R3", "R1")]
bc = R["block_centroids"]; NC = {}
for b0, b1 in PAIRS:
    idx = np.where((sb == b0) | (sb == b1))[0]; Xs, ys, gs = X[idx], (sb[idx] == b1).astype(int), groups[idx]
    pp_s = anova(Xs, ys)[1]; pmn = pd.DataFrame(Xs).groupby(gs).mean(); pmy = np.array([int(td.block[g] == b1) for g in pmn.index])
    res = dict(pair=f"{b0} vs {b1}", kind="control vs inoculated" if b0 == "C" else "inoculated vs inoculated (negative control)",
               n=(int((ys == 0).sum()), int((ys == 1).sum())), plots=(int(len(set(gs[ys == 0]))), int(len(set(gs[ys == 1])))),
               sig=int((pp_s < 0.05).sum()), sig_plot=int((anova(pmn.to_numpy(), pmy)[1] < 0.05).sum()),
               jm_band_max=float(max(jm2(B1d(Xs[ys == 0, j], Xs[ys == 1, j])) for j in range(P))), distance_m=float(np.hypot(*(bc.loc[b0] - bc.loc[b1]))))
    for t2 in ("CART", "RF"):
        bas, pbas = [], []
        for r in range(NREP_NC):
            yp, pb, _ = run_folds(grouped_folds(r, ys, gs, Xs), t2, "S1", Xs, ys, [SEED + r] * 4)
            bas.append(metrics(ys, yp)["BA"]); pbas.append(plot_level(ys, yp, gs)["BA"])
        res[t2] = dict(BA=(float(np.mean(bas)), float(np.std(bas, ddof=1))), plotBA=(float(np.mean(pbas)), float(np.std(pbas, ddof=1))))
    NC[(b0, b1)] = res
    log(f"block pair {b0} vs {b1} ({res['distance_m']:.1f} m): Tier-1 bands {res['sig']} (plot means {res['sig_plot']}); BA CART {res['CART']['BA'][0]:.3f} RF {res['RF']['BA'][0]:.3f}")
R["NC"] = NC; save()

# ======================================================================= restricted (block-level) permutation
RP = {}
for t2 in ("CART", "RF"):
    out = {}
    for hb in ["C", "R3", "R2", "R1"]:
        yy = (sb != hb).astype(int); bas = []
        for r in range(NREP_NC):
            yp, pb, _ = run_folds(grouped_folds(r, yy), t2, "S1", X, yy, [SEED + r] * 4); bas.append(metrics(yy, yp)["BA"])
        out[hb] = float(np.mean(bas)); log(f"restricted permutation {t2}: block {hb} labelled healthy -> BA {out[hb]:.3f}")
    RP[t2] = dict(ba=out, observed=out["C"], p=float(np.mean([v >= out["C"] - 1e-12 for v in out.values()])),
                  rank=int(sum(v > out["C"] + 1e-12 for v in out.values()) + 1))
R["RP"] = RP; save()

# ======================================================================= detection by block, variety and inoculation date
DET = {}
for (t2, s) in CFG:
    f2_ = pd.Series(V[(t2, s)]["CV2"]["preds"].mean(0)).groupby(groups).mean(); f3_ = V[(t2, s)]["CV3"]["reps"][0]["plot"]["table"].frac
    tab = td[["block", "variety", "date", "class"]].copy(); tab["pD_CV2"] = f2_.reindex(tab.index).values; tab["pD_CV3"] = f3_.reindex(tab.index).values
    kw = {}
    for fac in ("variety", "date"):
        for cl in ("healthy", "diseased"):
            gr = [g.pD_CV2.values for _, g in tab[tab["class"] == cl].groupby(fac)]; kv = stats.kruskal(*gr); kw[f"{fac}|{cl}"] = (float(kv.statistic), float(kv.pvalue))
    kb = stats.kruskal(*[g.pD_CV2.values for _, g in tab[tab["class"] == "diseased"].groupby("block")])
    DET[t2] = dict(table=tab, by_block=tab.groupby("block").pD_CV2.mean().reindex(["C", "R3", "R2", "R1"]),
                   by_variety=tab.pivot_table(index="variety", columns="class", values="pD_CV2"), by_date=tab.pivot_table(index="date", columns="class", values="pD_CV2"),
                   kw=kw, kw_block=(float(kb.statistic), float(kb.pvalue)))
    log(f"detection {t2} by block:", DET[t2]["by_block"].round(3).to_dict(), "KW date/variety (diseased):", kw["date|diseased"][1], kw["variety|diseased"][1])
R["DET"] = DET

# ======================================================================= sensitivity: band removal of Das et al. (bands >= 2350 nm removed)
keep = np.where(wl < 2350)[0]; Xk = X[:, keep]
Fk, pk, _, _ = anova(Xk, y); sigk = np.where(pk < 0.05)[0]
fullk = tier23(Xk, y, sigk)
SENS = dict(bands_used=int(len(keep)), sig=int(len(sigk)))
for t2 in ("CART", "RF"):
    bk = fullk[t2]["bands"]; reps1, reps2 = [], []
    for r in range(NREP):
        yp = np.empty(N, int)
        for tr, te in StratifiedKFold(10, shuffle=True, random_state=SEED + r).split(Xk, y):
            yp[te] = qda_fit(Xk[tr][:, bk], y[tr], "S0").predict(Xk[te][:, bk])
        reps1.append(metrics(y, yp))
        yp2, pb2, _ = run_folds(grouped_folds(r), t2, "S0", Xk, y, [SEED + r] * 4); m2 = metrics(y, yp2, pb2); m2["plot"] = plot_level(y, yp2, groups); reps2.append(m2)
    SENS[t2] = dict(bands=[float(wl[keep[i]]) for i in bk], JM=float(fullk[t2]["JM"]), CV1_OA=float(np.mean([m["OA"] for m in reps1])), CV1_BA=float(np.mean([m["BA"] for m in reps1])),
                    CV2_BA=(float(np.mean([m["BA"] for m in reps2])), float(np.std([m["BA"] for m in reps2], ddof=1))), CV2_plotBA=float(np.mean([m["plot"]["BA"] for m in reps2])))
    log(f"sensitivity (no bands >= 2350 nm) {t2}: {len(bk)} bands, JM {fullk[t2]['JM']:.3f}, CV1 OA {SENS[t2]['CV1_OA']:.3f}, CV2 BA {SENS[t2]['CV2_BA'][0]:.3f}")
R["SENS"] = SENS

# ======================================================================= final cross-checks
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis as QDA_
b = full["CART"]["bands"]; tr, te = f0[0]
def qda_manual(Xt, yt, Xe, pri):
    sc = []
    for k in (0, 1):
        Xk_ = Xt[yt == k]; mu = Xk_.mean(0); C = np.cov(Xk_, rowvar=False); dd = Xe - mu
        sc.append(-0.5 * np.linalg.slogdet(C)[1] - 0.5 * np.einsum("ij,ij->i", dd @ np.linalg.inv(C), dd) + np.log(pri[k]))
    return np.argmax(np.stack(sc, 1), 1)
m = qda_fit(X[tr][:, b], y[tr], "S0"); pri = [np.mean(y[tr] == 0), np.mean(y[tr] == 1)]
check("Tier 4", "hand-coded QDA (empirical priors) = sklearn QDA", "100% agreement", f"{(qda_manual(X[tr][:, b], y[tr], X[te][:, b], pri) == m.predict(X[te][:, b])).mean()*100:.1f}%",
      np.all(qda_manual(X[tr][:, b], y[tr], X[te][:, b], pri) == m.predict(X[te][:, b])))
mm = V[("CART", "S0")]["CV2"]["reps"][0]
check("Tier 4", "balanced accuracy = mean of sensitivity and specificity", "equal", f"{mm['BA']:.4f}", abs(mm["BA"] - (mm["sens_D"] + mm["spec_H"]) / 2) < 1e-12)
a = V[("CART", "S0")]["CV2"]["acc"]["spectra"]
check("Accuracy", f"pooled CV2 error matrix total = {NREP} x {N}", NREP * N, int(a["cm"].sum()), a["cm"].sum() == NREP * N)
check("Accuracy", "OA = 1 − quantity − allocation disagreement", "equal", f"{a['OA']:.4f}", abs(a["OA"] - (1 - a["QD"] - a["AD"])) < 1e-12)
from sklearn.metrics import cohen_kappa_score as _k
check("Accuracy", "kappa of pooled matrix = sklearn cohen_kappa_score", "equal", f"{a['kappa']:.6f}", abs(a["kappa"] - _k(np.tile(y, NREP), V[("CART", "S0")]["CV2"]["preds"].ravel())) < 1e-12)
check("Accuracy", "CV1 rep-1 OA from error matrix = sklearn accuracy", "equal", f"{V[('CART','S0')]['CV1']['acc_rep1']['spectra']['OA']:.6f}",
      abs(V[("CART", "S0")]["CV1"]["acc_rep1"]["spectra"]["OA"] - V[("CART", "S0")]["CV1"]["reps"][0]["OA"]) < 1e-12)
tt = full["CART"]["tree"]
tree_chk = RpartTree().fit(X, y, np.ones(N), sig_idx_all)
check("Tier 2", "unpruned custom tree reproduces sklearn predictions", "100%",
      f"{(tree_chk.predict(X, np.zeros(len(tree_chk.L), bool)) == tree_chk.clf.predict(X[:, sig_idx_all])).mean()*100:.1f}%",
      np.all(tree_chk.predict(X, np.zeros(len(tree_chk.L), bool)) == tree_chk.clf.predict(X[:, sig_idx_all])))
R["fallbacks"] = len(FALLBACK); log("QDA ridge fallbacks:", len(FALLBACK))
save("results/r47_quick.pkl" if QUICK else "results/r47.pkl")
log("DONE;", (R["checks"].result == "PASS").sum(), "/", len(R["checks"]), "checks pass")
