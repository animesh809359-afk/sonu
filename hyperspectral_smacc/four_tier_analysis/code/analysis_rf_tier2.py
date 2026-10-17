"""Tier 2 alternative: Random Forest band selection instead of CART, followed by tiers 3 (J-M) and 4 (QDA).
Adds results to results/results.pkl (keys prefixed rf2_)."""
import pickle, time, warnings
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import RandomForestClassifier
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import confusion_matrix, cohen_kappa_score

warnings.filterwarnings("ignore")
SEED = 42
R = pickle.load(open("results/results.pkl", "rb"))
X, y, wl, SEL_CART = R["X"], R["y"], R["wl"], R["SEL"]
yb = (y == "diseased").astype(int)
N, P = X.shape
K = len(SEL_CART)                      # same number of bands as CART -> fair comparison
R_THR = 0.95                           # redundancy filter for variant B
CHECKS = []
def check(what, expected, obtained, ok):
    CHECKS.append(dict(step="Tier 2 (RF)", check=what, expected=str(expected), obtained=str(obtained), result="PASS" if ok else "FAIL"))
    print(("  [PASS] " if ok else "  [FAIL] ") + f"{what} -> {obtained}")

def anova_p(Xm, ym):
    g0, g1 = Xm[ym == 0], Xm[ym == 1]
    gm = Xm.mean(0)
    ssb = len(g0) * (g0.mean(0) - gm) ** 2 + len(g1) * (g1.mean(0) - gm) ** 2
    ssw = ((g0 - g0.mean(0)) ** 2).sum(0) + ((g1 - g1.mean(0)) ** 2).sum(0)
    F = ssb / (ssw / (len(ym) - 2))
    return stats.f.sf(F, 1, len(ym) - 2)

def rf_model(): return RandomForestClassifier(n_estimators=500, max_features="sqrt", random_state=SEED, n_jobs=-1)

def rf_select(Xm, ym, decorrelate):
    """Tier-1 significant bands -> RF importance (mean decrease Gini) -> K bands."""
    sig = np.where(anova_p(Xm, ym) < 0.05)[0]
    imp = rf_model().fit(Xm[:, sig], ym).feature_importances_
    order = sig[np.argsort(-imp)]
    if not decorrelate:
        return list(order[:K]), sig, imp
    chosen = []
    Cm = np.corrcoef(Xm[:, order], rowvar=False)
    for i, b in enumerate(order):
        if all(abs(Cm[i, list(order).index(c)]) < R_THR for c in chosen):
            chosen.append(int(b))
        if len(chosen) == K:
            break
    return chosen, sig, imp

def bhatt(X0, X1):
    m0, m1 = X0.mean(0), X1.mean(0)
    C0, C1 = np.atleast_2d(np.cov(X0, rowvar=False)), np.atleast_2d(np.cov(X1, rowvar=False))
    C = (C0 + C1) / 2; d = m1 - m0
    return d @ np.linalg.solve(C, d) / 8 + 0.5 * (np.linalg.slogdet(C)[1] - 0.5 * (np.linalg.slogdet(C0)[1] + np.linalg.slogdet(C1)[1]))
def jm2(B): return 2 * (1 - np.exp(-B))

FALLBACK = []
class SafeQDA:
    def fit(self, Xm, ym):
        try:
            self.m = QuadraticDiscriminantAnalysis(priors=[0.5, 0.5], tol=1e-12).fit(Xm, ym)
        except np.linalg.LinAlgError:
            FALLBACK.append(Xm.shape[1]); self.m = QuadraticDiscriminantAnalysis(priors=[0.5, 0.5], reg_param=1e-4).fit(Xm, ym)
        return self
    def predict(self, Xm): return self.m.predict(Xm)

def metrics(yt, yp):
    cm = confusion_matrix(yt, yp, labels=[0, 1]); pa = np.diag(cm) / cm.sum(1); ua = np.diag(cm) / cm.sum(0)
    return dict(cm=cm, OA=np.trace(cm) / cm.sum(), PA_H=pa[0], PA_D=pa[1], UA_H=ua[0], UA_D=ua[1], kappa=cohen_kappa_score(yt, yp), balanced_acc=pa.mean())

folds0 = list(StratifiedKFold(10, shuffle=True, random_state=SEED).split(X, yb))
block = R["spatial"]["blocks"]["block"].to_numpy()
sfolds = [(np.where(block != b)[0], np.where(block == b)[0]) for b in range(5)]

def paper_style(bands, make, reps=10):
    accs, first = [], None
    for r in range(reps):
        pr = np.empty(N, int)
        for tr, te in StratifiedKFold(10, shuffle=True, random_state=SEED + r).split(X, yb):
            pr[te] = make().fit(X[tr][:, bands], yb[tr]).predict(X[te][:, bands])
        accs.append((pr == yb).mean())
        if r == 0: first = metrics(yb, pr)
    return first, np.array(accs)

def nested(folds, decorrelate):
    pr = np.empty(N, int); chosen = []
    for tr, te in folds:
        b, _, _ = rf_select(X[tr], yb[tr], decorrelate)
        chosen.append(b)
        pr[te] = SafeQDA().fit(X[tr][:, b], yb[tr]).predict(X[te][:, b])
    return metrics(yb, pr), chosen

out = {}
t0 = time.time()
for key, deco, label in (("RF-A", False, f"RF top-{K} (importance only)"), ("RF-B", True, f"RF top-{K}, redundancy filter |r| < {R_THR}")):
    bands, sig, imp = rf_select(X, yb, deco)
    bands_sorted_imp = bands                                # already in importance order
    Ck = [np.cov(X[yb == k][:, bands], rowvar=False) for k in (0, 1)]
    conds = [float(np.linalg.cond(c)) for c in Ck]; ranks = [int(np.linalg.matrix_rank(c)) for c in Ck]
    B = bhatt(X[yb == 0][:, bands], X[yb == 1][:, bands])
    cum = [dict(n_bands=k + 1, added_band_nm=round(float(wl[bands[k]]), 1),
                JM_0to2=jm2(bhatt(X[yb == 0][:, bands[:k + 1]], X[yb == 1][:, bands[:k + 1]]))) for k in range(K)]
    qp, qrep = paper_style(bands, SafeQDA)
    rp, _ = paper_style(bands, rf_model, reps=1)
    nm, nchosen = nested(folds0, deco)
    sm, schosen = nested(sfolds, deco)
    out[key] = dict(label=label, bands=bands, wl=[float(wl[b]) for b in bands], B=float(B), JM_0to2=float(jm2(B)), JM_sqrt=float(np.sqrt(jm2(B))),
                    cov_rank=ranks, cov_cond=conds, cum=pd.DataFrame(cum), qda_paper=qp, qda_rep=qrep, rf_paper=rp,
                    qda_nested=nm, qda_spatial=sm,
                    nested_freq=pd.Series([round(float(wl[b]), 1) for c in nchosen for b in c]).value_counts(),
                    spatial_bands=[", ".join(f"{wl[b]:.1f}" for b in c) for c in schosen],
                    max_abs_r=float(np.max(np.abs(np.corrcoef(X[:, bands], rowvar=False)[np.triu_indices(K, 1)]))))
    imp_tab = pd.DataFrame({"wavelength_nm": wl[sig], "MDI_importance": imp}).sort_values("MDI_importance", ascending=False).reset_index(drop=True)
    imp_tab["rank"] = np.arange(1, len(imp_tab) + 1)
    out[key]["importance"] = imp_tab
    print(f"{key} ({label}): bands {[round(w,1) for w in out[key]['wl']]}")
    print(f"   JM {out[key]['JM_0to2']:.4f}; cov rank {ranks} cond {[f'{c:.1e}' for c in conds]}; max|r| {out[key]['max_abs_r']:.4f}")
    print(f"   QDA paper {qp['OA']*100:.2f}% (10x {qrep.mean()*100:.2f}±{qrep.std(ddof=1)*100:.2f}); RF paper {rp['OA']*100:.2f}%; QDA nested {nm['OA']*100:.2f}%; QDA spatial {sm['OA']*100:.2f}%  ({time.time()-t0:.0f}s)")
    check(f"{key}: {K} bands selected, all from the ANOVA-significant set", f"{K} bands ⊂ significant", f"{len(bands)} bands, all significant: {set(bands) <= set(sig)}", len(bands) == K and set(bands) <= set(sig))
    check(f"{key}: class covariance matrices full rank", f"rank {K}", f"ranks {ranks}", all(r == K for r in ranks))

# same importance ranking reproduced with the same seed
b2, _, _ = rf_select(X, yb, False)
check("RF importance ranking reproducible with seed 42", "identical band list", f"identical: {b2 == out['RF-A']['bands']}", b2 == out["RF-A"]["bands"])
check("RF-B: no selected pair has |r| ≥ 0.95", f"max |r| < {R_THR}", f"max |r| = {out['RF-B']['max_abs_r']:.3f}", out["RF-B"]["max_abs_r"] < R_THR)

# single-band JM for every band selected by CART or RF
jb = R["jm_band"].set_index(R["jm_band"].wavelength_nm.round(2))
rows = []
union = sorted(set(SEL_CART) | set(out["RF-A"]["bands"]) | set(out["RF-B"]["bands"]))
for b in union:
    w = round(float(wl[b]), 2)
    rows.append(dict(wavelength_nm=w, region=next((n for n, lo, hi in [("VIS", 420, 700), ("Red-edge", 700, 750), ("NIR", 750, 1330), ("SWIR-1", 1460, 1780), ("SWIR-2", 1970, 2351)] if lo <= w < hi), ""),
                     CART="yes" if b in SEL_CART else "", RF_A="yes" if b in out["RF-A"]["bands"] else "", RF_B="yes" if b in out["RF-B"]["bands"] else "",
                     JM_0to2=float(jb.loc[w, "JM_0to2"]), JM_sqrt=float(jb.loc[w, "JM_sqrt_form"]),
                     F=float(R["tier1"].F[b]), Cohen_d=float(R["tier1"].Cohen_d_D_minus_H[b])))
sb = pd.DataFrame(rows)
print(sb.round(4).to_string())
# CART multivariate (already computed) for the set table
sets = pd.DataFrame([
    dict(selection="CART (cp = 0.01)", bands=", ".join(f"{wl[b]:.1f}" for b in sorted(SEL_CART)), JM_0to2=R["tier3"]["JM_0to2"], JM_sqrt=R["tier3"]["JM_sqrt"],
         QDA_paper=R["qda"]["metrics"]["OA"], QDA_rep_mean=float(R["qda"]["rep_acc"].mean()), RF_paper=R["rf"]["CART bands (tiers 2-3)"]["metrics"]["OA"],
         QDA_nested=R["nested"]["qda"]["OA"], QDA_spatial=R["spatial"]["qda"]["OA"], kappa_paper=R["qda"]["metrics"]["kappa"]),
] + [dict(selection=v["label"], bands=", ".join(f"{w:.1f}" for w in sorted(v["wl"])), JM_0to2=v["JM_0to2"], JM_sqrt=v["JM_sqrt"],
          QDA_paper=v["qda_paper"]["OA"], QDA_rep_mean=float(v["qda_rep"].mean()), RF_paper=v["rf_paper"]["OA"],
          QDA_nested=v["qda_nested"]["OA"], QDA_spatial=v["qda_spatial"]["OA"], kappa_paper=v["qda_paper"]["kappa"]) for v in out.values()])
print(sets.drop(columns="bands").round(4).to_string())
# cross-check: single-band JM table equals 1-D closed form
def B1d(a, c):
    m0, m1, v0, v1 = a.mean(), c.mean(), a.var(ddof=1), c.var(ddof=1)
    return (m1 - m0) ** 2 / (4 * (v0 + v1)) + 0.5 * np.log((v0 + v1) / (2 * np.sqrt(v0 * v1)))
cf = np.array([jm2(B1d(X[yb == 0, b], X[yb == 1, b])) for b in union])
check("single-band JM of selected bands = 1-D closed form", "equal", f"max |diff| {np.max(np.abs(cf - sb.JM_0to2.values)):.1e}", np.max(np.abs(cf - sb.JM_0to2.values)) < 1e-9)
print("QDA ridge fallbacks:", len(FALLBACK))
R["rf2"] = out; R["rf2_selected_bands"] = sb; R["rf2_sets"] = sets; R["rf2_fallbacks"] = len(FALLBACK); R["rf2_K"] = K; R["rf2_rthr"] = R_THR
R["checks"] = pd.concat([R["checks"][R["checks"].step != "Tier 2 (RF)"], pd.DataFrame(CHECKS)], ignore_index=True)
pickle.dump(R, open("results/results.pkl", "wb"))
print("saved;", (R["checks"].result == "PASS").sum(), "/", len(R["checks"]), "checks pass")
