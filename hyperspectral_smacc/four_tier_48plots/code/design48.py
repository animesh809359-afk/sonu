"""Validation that uses the treatment design (treatment_detail.xlsx) and a full accuracy assessment.
 - design check: control block C (plots 1-12) and inoculated blocks R3, R2, R1, each with 3 varieties x 4 inoculation dates
 - V2 re-run with stored predictions (must reproduce results/r48.pkl exactly) -> confusion matrices, PA/UA/OA/kappa/BA/F1/MCC,
   quantity and allocation disagreement, 95% CI by stratified cluster (plot) bootstrap
 - V4 leave-one-treatment-combination-out, V5 leave-one-variety-out, V6 leave-one-inoculation-date-out (all nested)
 - negative control: block-vs-block classification (inoculated vs inoculated) next to control-vs-inoculated
 - restricted (block-level) permutation: each of the 4 blocks in turn labelled 'healthy'
 - detection rate by block, variety and inoculation date
Usage: python design48.py treatment_detail.xlsx   -> results/d48.pkl"""
import pickle, re, sys, time, warnings
import numpy as np, pandas as pd
from scipy import stats
from sklearn.model_selection import StratifiedGroupKFold
from pipeline48 import *
from pipeline48 import NO_BANDS
warnings.filterwarnings("ignore")
T0 = time.time()
def log(*a): print(f"[{time.time()-T0:6.0f}s]", *a, flush=True)
CHECKS = []
def check(step, what, expected, obtained, ok):
    CHECKS.append(dict(step=step, check=what, expected=str(expected), obtained=str(obtained), result="PASS" if ok else "FAIL"))
    log(("[PASS] " if ok else "[FAIL] ") + f"{step}: {what} -> {obtained}")

R = pickle.load(open("results/r48.pkl", "rb"))
X, y, groups, wl, V, full, CFG, best = R["X"], R["y"], R["groups"], R["wl"], R["V"], R["full"], R["CONFIGS"], R["best"]
N, NREP, NBOOT = len(y), 10, 2000
import os
QUICK = os.environ.get("QUICK") == "1"          # smoke test only: 2 configurations, 1 repetition, results/d48_quick.pkl
if QUICK: CFG, NREP, NBOOT = [("CART", best["CART"]), ("RF", best["RF"])], 1, 50
OUTF = "results/d48_quick.pkl" if QUICK else "results/d48.pkl"
D = {}

# ======================================================================= design
td = pd.read_excel(sys.argv[1] if len(sys.argv) > 1 else "treatment_detail.xlsx")
td.columns = ["plot", "date", "variety", "block"]
td = td.astype({"plot": int}).set_index("plot").sort_index()
check("Design", "48 plots listed once each", "1..48", f"{td.index.min()}..{td.index.max()} ({td.index.nunique()} unique)", list(td.index) == list(range(1, 49)))
check("Design", "block C = plots 1-12 (healthy); R1-R3 = plots 13-48 (diseased)", "yes",
      str(td.groupby("block").apply(lambda d: f"{d.index.min()}-{d.index.max()}").to_dict()),
      set(td.index[td.block == "C"]) == set(range(1, 13)) and set(td.index[td.block != "C"]) == set(range(13, 49)))
combos_ok = all(td[td.block == b].groupby(["variety", "date"]).size().eq(1).all() and len(td[td.block == b]) == 12 for b in td.block.unique())
check("Design", "every block holds each variety x inoculation-date combination once", "3 x 4 = 12 per block", combos_ok, combos_ok)
txt = open("plots48.xml").read(); cen = {}
for m in re.finditer(r'<Region name="ROI #(\d+)".*?<Coordinates>(.*?)</Coordinates>', txt, re.S):
    v = np.array(m.group(2).split(), float).reshape(-1, 2); cen[int(m.group(1))] = v.mean(0)
lat0 = np.mean([c[1] for c in cen.values()]); lon0 = np.mean([c[0] for c in cen.values()])
td["x_m"] = [(cen[k][0] - lon0) * 111320 * np.cos(np.radians(lat0)) for k in td.index]
td["y_m"] = [(cen[k][1] - lat0) * 110850 for k in td.index]
td["class"] = np.where(td.block == "C", "healthy", "diseased")
td["n_spectra"] = pd.Series(groups).value_counts().reindex(td.index).values
D["design"] = td
blk_c = td.groupby("block")[["x_m", "y_m"]].mean()
D["block_centroids"] = blk_c
log("block centroids (m):", blk_c.round(1).to_dict("index"))
sb, sv, sd = td.block.reindex(groups).values, td.variety.reindex(groups).values, td.date.reindex(groups).values

# ======================================================================= helpers
def run_folds(folds, t2, s, Xs, ys, seeds):
    yp = np.full(len(ys), -1); pb = np.zeros(len(ys)); bands = []
    for (tr, te), sd_ in zip(folds, seeds):
        m, b, _ = fit_pipeline(Xs[tr], ys[tr], s, t2, sd_)
        yp[te] = m.predict(Xs[te][:, b]); pb[te] = m.predict_proba(Xs[te][:, b])[:, 1]; bands.append(b)
    return yp, pb, bands
def acc(cm):
    """Accuracy measures from a 2x2 error matrix (rows = reference H, D; columns = predicted H, D)."""
    cm = np.asarray(cm, float); n = cm.sum(); a, b, c, d = cm[0, 0], cm[0, 1], cm[1, 0], cm[1, 1]
    dv = lambda u, v: u / v if v > 0 else np.nan
    OA = (a + d) / n; PA_H, PA_D, UA_H, UA_D = dv(a, a + b), dv(d, c + d), dv(a, a + c), dv(d, b + d)
    pe = ((a + b) * (a + c) + (c + d) * (b + d)) / n ** 2
    den = np.sqrt((a + b) * (a + c) * (d + b) * (d + c))
    Q = 0.5 * (abs((a + b) - (a + c)) + abs((c + d) - (b + d))) / n            # quantity disagreement (Pontius & Millones 2011)
    return dict(n=n, OA=OA, BA=(PA_H + PA_D) / 2, kappa=dv(OA - pe, 1 - pe), PA_H=PA_H, UA_H=UA_H, PA_D=PA_D, UA_D=UA_D,
                F1_H=dv(2 * PA_H * UA_H, PA_H + UA_H), F1_D=dv(2 * PA_D * UA_D, PA_D + UA_D), MCC=dv(a * d - b * c, den),
                QD=Q, AD=(1 - OA) - Q)
AKEYS = ["OA", "BA", "kappa", "PA_H", "UA_H", "PA_D", "UA_D", "F1_H", "F1_D", "MCC", "QD", "AD"]
def cm_by_plot(yt, yp, grp):
    """2x2 counts per plot (summed over all predictions supplied)."""
    out = {}
    for g in np.unique(grp):
        k = grp == g; out[int(g)] = np.array([[np.sum((yt[k] == i) & (yp[k] == j)) for j in (0, 1)] for i in (0, 1)])
    return out
RNG = np.random.default_rng(42)
def cluster_ci(per_plot, plots_H, plots_D, nboot=NBOOT):
    """95% percentile CI: plots resampled with replacement within each class (stratified cluster bootstrap, Field & Welsh 2007)."""
    stack = {k: v for k, v in per_plot.items()}
    vals = {k: [] for k in AKEYS}
    for _ in range(nboot):
        pick = list(RNG.choice(plots_H, len(plots_H))) + list(RNG.choice(plots_D, len(plots_D)))
        m = acc(sum(stack[g] for g in pick))
        for k in AKEYS: vals[k].append(m[k])
    return {k: (float(np.nanpercentile(v, 2.5)), float(np.nanpercentile(v, 97.5))) for k, v in vals.items()}
def plot_votes(yt, yp, grp):
    t = plot_level(yt, yp, grp)["table"]; return t
def assess(ytrue, preds, grp, plots_H, plots_D):
    """preds: list of prediction vectors (one per repetition). Spectrum- and plot-level error matrices summed over repetitions."""
    pp_s = {}; pp_p = {}
    for yp in preds:
        for g, c in cm_by_plot(ytrue, yp, grp).items(): pp_s[g] = pp_s.get(g, 0) + c
        t = plot_votes(ytrue, yp, grp)
        for g in t.index:
            c = np.zeros((2, 2), int); c[int(t.t[g]), int(t.pred[g])] = 1; pp_p[int(g)] = pp_p.get(int(g), 0) + c
    cms, cmp_ = sum(pp_s.values()), sum(pp_p.values())
    return dict(spectra=dict(cm=cms, **acc(cms), ci=cluster_ci(pp_s, plots_H, plots_D), reps=len(preds)),
                plots=dict(cm=cmp_, **acc(cmp_), ci=cluster_ci(pp_p, plots_H, plots_D), reps=len(preds)))
PH, PD = list(range(1, 13)), list(range(13, 49))

# ======================================================================= 1. V2 again, keeping predictions (reproducibility check)
YP2 = {}
for (t2, s) in CFG:
    preds = []
    for r in range(NREP):
        folds = list(StratifiedGroupKFold(4, shuffle=True, random_state=42 + r).split(X, y, groups))
        yp, pb, _ = run_folds(folds, t2, s, X, y, [42 + r] * 4)
        preds.append(yp)
        if abs(metrics(y, yp, pb)["BA"] - V[(t2, s)]["v2"][r]["BA"]) > 1e-12:
            check("Reproducibility", f"V2 {t2}-{s} rep {r+1} = stored result", "identical", "DIFFERENT", False)
    YP2[(t2, s)] = np.array(preds)
    log(f"V2 re-run {t2}-{s} done")
check("Reproducibility", "V2 re-run with the shared pipeline module reproduces all 80 stored repetitions", "identical BA",
      "identical" if not any(c["result"] == "FAIL" and c["step"] == "Reproducibility" for c in CHECKS) else "different",
      not any(c["result"] == "FAIL" and c["step"] == "Reproducibility" for c in CHECKS))
D["YP2"] = YP2

# ======================================================================= 2. accuracy assessment
ACC = {}
for (t2, s) in CFG:
    v1cm = sum(m["cm"] for m in V[(t2, s)]["v1"])
    ACC[(t2, s)] = dict(V1=dict(spectra=dict(cm=v1cm, **acc(v1cm), reps=len(V[(t2, s)]["v1"]))),
                        V2=assess(y, list(YP2[(t2, s)]), groups, PH, PD),
                        V3=assess(y, [V[(t2, s)]["v3"]["yp"]], groups, PH, PD))
    a = ACC[(t2, s)]
    log(f"accuracy {t2}-{s}: V2 OA {a['V2']['spectra']['OA']:.3f} BA {a['V2']['spectra']['BA']:.3f} "
        f"[{a['V2']['spectra']['ci']['BA'][0]:.3f}, {a['V2']['spectra']['ci']['BA'][1]:.3f}] kappa {a['V2']['spectra']['kappa']:.3f}; "
        f"plots BA {a['V2']['plots']['BA']:.3f} [{a['V2']['plots']['ci']['BA'][0]:.3f}, {a['V2']['plots']['ci']['BA'][1]:.3f}]")
m0 = ACC[("CART", "S1")]["V2"]["spectra"]
check("Accuracy", f"pooled V2 error matrix total = {NREP} x {N} predictions", NREP * N, int(m0["cm"].sum()), m0["cm"].sum() == NREP * N)
ba_mean = np.mean([m["BA"] for m in V[("CART", "S1")]["v2"][:NREP]])
check("Accuracy", "pooled-matrix BA close to the mean of per-repetition BA (CART-S1)", "|Δ| < 0.005", f"{abs(m0['BA']-ba_mean):.5f}", abs(m0["BA"] - ba_mean) < 0.005)
check("Accuracy", "OA = 1 - quantity disagreement - allocation disagreement", "equal", f"{m0['OA']:.4f} vs {1-m0['QD']-m0['AD']:.4f}", abs(m0["OA"] - (1 - m0["QD"] - m0["AD"])) < 1e-12)
from sklearn.metrics import cohen_kappa_score as _k
yy_, pp_ = np.tile(y, NREP), YP2[("CART", "S1")].ravel()
check("Accuracy", "kappa from the pooled matrix = sklearn cohen_kappa_score", "equal", f"{m0['kappa']:.6f} vs {_k(yy_, pp_):.6f}", abs(m0["kappa"] - _k(yy_, pp_)) < 1e-12)
check("Accuracy", "V3 accuracy from matrix = stored V3 BA (CART-S1)", "equal", f"{ACC[('CART','S1')]['V3']['spectra']['BA']:.6f}", abs(ACC[("CART", "S1")]["V3"]["spectra"]["BA"] - V[("CART", "S1")]["v3"]["BA"]) < 1e-12)
D["ACC"] = ACC
pickle.dump(D, open(OUTF.replace(".pkl", "_partial.pkl"), "wb"))

# ======================================================================= 3. design-based validation (nested)
combos = sorted(td.groupby(["variety", "date"]).groups.keys())
SCHEMES = {
    "V4": ("Leave-one-treatment-combination-out", [np.where((sv == v) & (sd == d_))[0] for v, d_ in combos], [f"{v}×{d_}" for v, d_ in combos]),
    "V5": ("Leave-one-variety-out", [np.where(sv == v)[0] for v in sorted(td.variety.unique())], sorted(td.variety.unique())),
    "V6": ("Leave-one-inoculation-date-out", [np.where(sd == d_)[0] for d_ in sorted(td.date.unique())], sorted(td.date.unique())),
}
for k, (nm, tests, labels) in SCHEMES.items():
    allte = np.concatenate(tests)
    ok = len(allte) == N and len(set(allte)) == N and all(len(set(y[te])) == 2 for te in tests)
    check("Validation design", f"{k} {nm}: every spectrum tested once; every test fold has both classes", f"{len(tests)} folds",
          f"{len(tests)} folds; test plots/fold: {sorted({len(set(groups[te])) for te in tests})}; healthy:diseased plots {sorted({(len(set(groups[te][y[te]==0])), len(set(groups[te][y[te]==1]))) for te in tests})}", ok)
DV = {}
for k, (nm, tests, labels) in SCHEMES.items():
    folds = [(np.setdiff1d(np.arange(N), te), te) for te in tests]
    for (t2, s) in CFG:
        NO_BANDS.clear()
        yp, pb, bands = run_folds(folds, t2, s, X, y, [42 + i for i in range(len(folds))])
        mm = metrics(y, yp, pb); mm["plot"] = plot_level(y, yp, groups)
        mm["acc"] = assess(y, [yp], groups, PH, PD); mm["yp"] = yp; mm["bands"] = bands; mm["no_band_folds"] = len(NO_BANDS)
        mm["per_fold"] = [dict(label=lab, BA=float(metrics(y[te], yp[te])["BA"]), n=len(te), plots=len(set(groups[te]))) for lab, te in zip(labels, tests)]
        DV[(k, t2, s)] = mm
        log(f"{k} {t2}-{s}: BA {mm['BA']:.3f} [{mm['acc']['spectra']['ci']['BA'][0]:.3f}, {mm['acc']['spectra']['ci']['BA'][1]:.3f}]; plot BA {mm['plot']['BA']:.3f}")
D["DV"] = DV; D["SCHEMES"] = {k: (v[0], v[2]) for k, v in SCHEMES.items()}
pickle.dump(D, open(OUTF.replace(".pkl", "_partial.pkl"), "wb"))

# ======================================================================= 4. negative control: block vs block
PAIRS = [("C", "R3"), ("C", "R2"), ("C", "R1"), ("R3", "R2"), ("R2", "R1"), ("R3", "R1")]
NC = {}
for b0, b1 in PAIRS:
    idx = np.where((sb == b0) | (sb == b1))[0]; Xs, ys, gs = X[idx], (sb[idx] == b1).astype(int), groups[idx]
    Fp, pp, _, _ = anova(Xs, ys)
    pmn = pd.DataFrame(Xs).groupby(gs).mean(); pmy = np.array([int(td.block[g] == b1) for g in pmn.index])
    pp_plot = anova(pmn.to_numpy(), pmy)[1]
    jm_max = max(jm2(B1d(Xs[ys == 0, j], Xs[ys == 1, j])) for j in range(Xs.shape[1]))
    dist = float(np.hypot(*(blk_c.loc[b0] - blk_c.loc[b1])))
    res = dict(pair=f"{b0} vs {b1}", kind="control vs inoculated" if b0 == "C" else "inoculated vs inoculated (negative control)",
               n=(int((ys == 0).sum()), int((ys == 1).sum())), sig=int((pp < 0.05).sum()), sig_plot=int((pp_plot < 0.05).sum()),
               jm_band_max=float(jm_max), distance_m=dist)
    for t2 in ("CART", "RF"):
        bas, pbas = [], []
        for r in range(NREP):
            folds = list(StratifiedGroupKFold(4, shuffle=True, random_state=42 + r).split(Xs, ys, gs))
            yp, pb, _ = run_folds(folds, t2, "S0", Xs, ys, [42 + r] * 4)
            bas.append(metrics(ys, yp)["BA"]); pbas.append(plot_level(ys, yp, gs)["BA"])
        res[t2] = dict(BA=(float(np.mean(bas)), float(np.std(bas, ddof=1))), plotBA=(float(np.mean(pbas)), float(np.std(pbas, ddof=1))))
    NC[(b0, b1)] = res
    log(f"block pair {b0} vs {b1} ({dist:.1f} m): Tier-1 bands {res['sig']} (plot means {res['sig_plot']}); CART BA {res['CART']['BA'][0]:.3f}, RF BA {res['RF']['BA'][0]:.3f}; plot BA {res['CART']['plotBA'][0]:.3f}/{res['RF']['plotBA'][0]:.3f}")
D["NC"] = NC
pickle.dump(D, open(OUTF.replace(".pkl", "_partial.pkl"), "wb"))

# ======================================================================= 5. restricted permutation: which block is 'healthy'?
RP = {}
for t2 in ("CART", "RF"):
    s = best[t2]; out = {}
    for hb in ["C", "R3", "R2", "R1"]:
        yy = (sb != hb).astype(int); bas = []
        for r in range(NREP):
            folds = list(StratifiedGroupKFold(4, shuffle=True, random_state=42 + r).split(X, yy, groups))
            yp, pb, _ = run_folds(folds, t2, s, X, yy, [42 + r] * 4); bas.append(metrics(yy, yp)["BA"])
        out[hb] = float(np.mean(bas))
        log(f"restricted permutation {t2}-{s}: block {hb} labelled healthy -> mean BA {out[hb]:.3f}")
    obs = out["C"]; p = np.mean([v >= obs - 1e-12 for v in out.values()])
    RP[t2] = dict(strategy=s, ba=out, observed=obs, p=float(p), rank=int(sum(v > obs + 1e-12 for v in out.values()) + 1))
    log(f"restricted permutation {t2}: observed (C healthy) {obs:.3f}; rank {RP[t2]['rank']} of 4; p = {p:.2f}")
_ref = {t2: np.mean([m["BA"] for m in V[(t2, best[t2])]["v2"][:NREP]]) for t2 in ("CART", "RF")}
check("Validation design", "true labelling (C healthy) reproduces the main V2 result", f"CART {_ref['CART']:.4f}, RF {_ref['RF']:.4f}",
      f"CART {RP['CART']['observed']:.4f}, RF {RP['RF']['observed']:.4f}", all(abs(RP[t]["observed"] - _ref[t]) < 1e-12 for t in _ref))
D["RP"] = RP

# ======================================================================= 6. detection by block, variety and inoculation date
DET = {}
for t2 in ("CART", "RF"):
    s = best[t2]
    f2 = pd.Series(YP2[(t2, s)].mean(0)).groupby(groups).mean()               # V2: share of a plot's predictions = diseased
    f3 = V[(t2, s)]["v3"]["plot"]["table"].frac
    tab = td[["block", "variety", "date", "class"]].copy(); tab["pD_V2"] = f2.reindex(tab.index).values; tab["pD_V3"] = f3.reindex(tab.index).values
    tab["correct_V3"] = np.where(tab["class"] == "diseased", tab.pD_V3 > 0.5, tab.pD_V3 <= 0.5)
    kw = {}
    for fac in ("variety", "date"):
        for cl in ("healthy", "diseased"):
            sub = tab[tab["class"] == cl]; gr = [g.pD_V2.values for _, g in sub.groupby(fac)]
            kw[(fac, cl)] = stats.kruskal(*gr)
    kb = stats.kruskal(*[g.pD_V2.values for _, g in tab[tab["class"] == "diseased"].groupby("block")])
    DET[t2] = dict(strategy=s, table=tab, by_block=tab.groupby("block").pD_V2.agg(["mean", "min", "max"]).reindex(["C", "R3", "R2", "R1"]),
                   by_variety=tab.pivot_table(index="variety", columns="class", values="pD_V2"),
                   by_date=tab.pivot_table(index="date", columns="class", values="pD_V2"),
                   kw={f"{a}|{b}": (float(v.statistic), float(v.pvalue)) for (a, b), v in kw.items()}, kw_block=(float(kb.statistic), float(kb.pvalue)))
    log(f"detection {t2}-{s} by block (mean share predicted diseased, V2):", DET[t2]["by_block"]["mean"].round(3).to_dict())
    log(f"  Kruskal-Wallis (inoculated plots): date p={kw[('date','diseased')].pvalue:.3f}, variety p={kw[('variety','diseased')].pvalue:.3f}, block p={kb.pvalue:.3f}")
D["DET"] = DET
D["checks"] = pd.DataFrame(CHECKS)
pickle.dump(D, open(OUTF, "wb"))
log("DONE;", (D["checks"].result == "PASS").sum(), "/", len(D["checks"]), "checks pass")
