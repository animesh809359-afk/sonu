"""Four-tier hierarchical analysis (Das et al. 2020) + Random Forest comparison on SMACC endmembers.
Writes tables (CSV/pickle) and figures to ./results."""
import json, os, pickle, time, warnings
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.tree import DecisionTreeClassifier
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import confusion_matrix, cohen_kappa_score, accuracy_score
from sklearn.cluster import KMeans
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from statsmodels.stats.multitest import multipletests

warnings.filterwarnings("ignore")
os.makedirs("results", exist_ok=True)
SEED = 42
R = {}           # every result goes here -> results/results.pkl
CHECKS = []      # cross-checks: (step, check, expected, obtained, pass)

def check(step, what, expected, obtained, ok):
    CHECKS.append(dict(step=step, check=what, expected=str(expected), obtained=str(obtained), result="PASS" if ok else "FAIL"))
    print(("  [PASS] " if ok else "  [FAIL] ") + f"{step}: {what} -> {obtained}")

# =====================================================================
# STEP 0  Load data
# =====================================================================
raw = pd.read_csv("endmembers.csv")
band_cols_all = list(raw.columns[6:])
wl_all = np.array([float(c) for c in band_cols_all])
X_all = raw[band_cols_all].to_numpy(float)
y_all = raw["class"].to_numpy()
print("STEP 0 data", raw.shape)
check("0 Data", "rows x columns", "600 x 489", f"{raw.shape[0]} x {raw.shape[1]}", raw.shape == (600, 489))
check("0 Data", "spectra per class", "300 healthy / 300 diseased", raw["class"].value_counts().to_dict(),
      (raw["class"] == "healthy").sum() == 300 and (raw["class"] == "diseased").sum() == 300)
check("0 Data", "missing values", 0, int(np.isnan(X_all).sum()), np.isnan(X_all).sum() == 0)
check("0 Data", "duplicate pixel locations", 0, int(raw.duplicated(["row_0based", "col_0based"]).sum()),
      raw.duplicated(["row_0based", "col_0based"]).sum() == 0)
check("0 Data", "wavelengths strictly increasing", True, bool(np.all(np.diff(wl_all) > 0)), np.all(np.diff(wl_all) > 0))

# =====================================================================
# STEP 1  Data check (no spectra are removed: every SMACC endmember is analysed)
# =====================================================================
flags = pd.DataFrame({"class": y_all, "endmember_no": raw["endmember_no"], "row_0based": raw["row_0based"],
                      "col_0based": raw["col_0based"], "n_negative_bands": (X_all < 0).sum(1),
                      "min_reflectance": X_all.min(1), "max_reflectance": X_all.max(1)})
R["flags"] = flags
neg_by_band = pd.DataFrame({"wavelength_nm": wl_all,
                            "neg_healthy": (X_all[y_all == "healthy"] < 0).sum(0),
                            "neg_diseased": (X_all[y_all == "diseased"] < 0).sum(0)})
R["neg_by_band"] = neg_by_band
print("STEP 1: all", len(flags), "spectra kept; spectra with negative values:", int((flags.n_negative_bands > 0).sum()))

# Band set for analysis: noisy detector edges removed (same rule as the SMACC search)
band_keep = (wl_all >= 420) & (wl_all <= 2350)
R["band_table"] = pd.DataFrame({"wavelength_nm": wl_all, "used": np.where(band_keep, "yes", "no (noisy detector edge)")})
data = raw.reset_index(drop=True)
bcols = [c for c, k in zip(band_cols_all, band_keep) if k]
wl = wl_all[band_keep]
X = data[bcols].to_numpy(float)
y = data["class"].to_numpy()
yb = (y == "diseased").astype(int)          # 1 = diseased, 0 = healthy
N, P = X.shape
nH, nD = (yb == 0).sum(), (yb == 1).sum()
print(f"Analysis set: {N} spectra ({nH} H, {nD} D) x {P} bands")
check("1 Data check", "analysis set size (all spectra, noisy edge bands excluded)", "600 spectra x 463 bands", f"{N} x {P}", (N, P) == (600, 463))
R["analysis_set"] = dict(N=int(N), P=int(P), nH=int(nH), nD=int(nD), wl_min=float(wl.min()), wl_max=float(wl.max()))

def fmt(w): return f"{w:.1f}"

# =====================================================================
# Class spectra
# =====================================================================
cs = pd.DataFrame({"wavelength_nm": wl,
                   "mean_healthy": X[yb == 0].mean(0), "sd_healthy": X[yb == 0].std(0, ddof=1),
                   "mean_diseased": X[yb == 1].mean(0), "sd_diseased": X[yb == 1].std(0, ddof=1)})
cs["difference_D_minus_H"] = cs.mean_diseased - cs.mean_healthy
cs["percent_difference"] = 100 * cs.difference_D_minus_H / cs.mean_healthy
R["class_spectra"] = cs

# =====================================================================
# TIER 1  One-way ANOVA + Tukey HSD at every band
# =====================================================================
def anova_F(X, yb):
    """Vectorised one-way ANOVA for two groups -> F, p, SSB, SSW."""
    g0, g1 = X[yb == 0], X[yb == 1]
    n0, n1 = len(g0), len(g1)
    gm = X.mean(0)
    ssb = n0 * (g0.mean(0) - gm) ** 2 + n1 * (g1.mean(0) - gm) ** 2
    ssw = ((g0 - g0.mean(0)) ** 2).sum(0) + ((g1 - g1.mean(0)) ** 2).sum(0)
    dfb, dfw = 1, n0 + n1 - 2
    F = (ssb / dfb) / (ssw / dfw)
    p = stats.f.sf(F, dfb, dfw)
    return F, p, ssb, ssw

t0 = time.time()
F, p, ssb, ssw = anova_F(X, yb)
F_scipy = np.array([stats.f_oneway(X[yb == 0, j], X[yb == 1, j])[0] for j in range(P)])
p_scipy = np.array([stats.f_oneway(X[yb == 0, j], X[yb == 1, j])[1] for j in range(P)])
t_eq = np.array([stats.ttest_ind(X[yb == 0, j], X[yb == 1, j])[0] for j in range(P)])
tukey_p = np.array([float(pairwise_tukeyhsd(X[:, j], y, alpha=0.05).pvalues[0]) for j in range(P)])
welch_p = np.array([stats.ttest_ind(X[yb == 0, j], X[yb == 1, j], equal_var=False)[1] for j in range(P)])
levene_p = np.array([stats.levene(X[yb == 0, j], X[yb == 1, j])[1] for j in range(P)])
fdr_q = multipletests(p, method="fdr_bh")[1]
bonf_p = multipletests(p, method="bonferroni")[1]
sp = np.sqrt(((nH - 1) * cs.sd_healthy ** 2 + (nD - 1) * cs.sd_diseased ** 2) / (nH + nD - 2))
cohen_d = (cs.mean_diseased - cs.mean_healthy) / sp
tier1 = pd.DataFrame({"wavelength_nm": wl, "mean_healthy": cs.mean_healthy, "mean_diseased": cs.mean_diseased,
                      "SS_between": ssb, "SS_within": ssw, "df_between": 1, "df_within": N - 2,
                      "F": F, "p_ANOVA": p, "Tukey_HSD_p": tukey_p, "significant_p<0.05": np.where(p < 0.05, "yes", "no"),
                      "Welch_t_p": welch_p, "Levene_p": levene_p, "FDR_q_BH": fdr_q, "Bonferroni_p": bonf_p,
                      "Cohen_d_D_minus_H": cohen_d.to_numpy()})
sig = p < 0.05
R["tier1"] = tier1
print(f"TIER 1: {sig.sum()} / {P} bands significant at p<0.05 ({time.time()-t0:.0f}s)")
check("Tier 1", "manual F = scipy f_oneway F (max |diff|)", "< 1e-6", f"{np.max(np.abs(F - F_scipy)):.2e}", np.max(np.abs(F - F_scipy) / F_scipy) < 1e-8)
check("Tier 1", "manual p = scipy p (max |diff|)", "< 1e-9", f"{np.max(np.abs(p - p_scipy)):.2e}", np.max(np.abs(p - p_scipy)) < 1e-9)
check("Tier 1", "t-test squared equals F (two groups)", "t^2 = F", f"max rel diff {np.max(np.abs(t_eq**2 - F) / F):.1e}", np.max(np.abs(t_eq ** 2 - F) / F) < 1e-8)
check("Tier 1", "Tukey HSD p equals ANOVA p (two groups, one pair)", "identical significance",
      f"same decision at all {P} bands: {bool(np.all((tukey_p < 0.05) == sig))}", bool(np.all((tukey_p < 0.05) == sig)))
regions = [("VIS (420-700)", 420, 700), ("Red-edge (700-750)", 700, 750), ("NIR (750-1330)", 750, 1330),
           ("SWIR-1 (1460-1780)", 1460, 1780), ("SWIR-2 (1970-2350)", 1970, 2350)]
reg_rows = []
for name, lo, hi in regions:
    m = (wl >= lo) & (wl < hi) if hi != 2350 else (wl >= lo) & (wl <= hi)
    j = np.argmax(np.where(m, F, -1))
    reg_rows.append(dict(region=name, bands=int(m.sum()), significant_p05=int((sig & m).sum()),
                         significant_FDR=int(((fdr_q < 0.05) & m).sum()), significant_Bonferroni=int(((bonf_p < 0.05) & m).sum()),
                         max_F_band_nm=fmt(wl[j]), max_F=round(float(F[j]), 1), direction=("D > H" if cs.difference_D_minus_H[j] > 0 else "D < H")))
R["tier1_regions"] = pd.DataFrame(reg_rows)
check("Tier 1", "region band counts add up", P, int(R["tier1_regions"].bands.sum()), R["tier1_regions"].bands.sum() == P)

# =====================================================================
# TIER 2  CART (rpart-equivalent: Gini, minsplit 20, minbucket 7, cost-complexity on misclassification)
# =====================================================================
class RpartTree:
    """Grows a Gini tree with rpart's default stopping rules and prunes it by cost-complexity
    using misclassification risk, exactly as rpart's cp does."""
    def __init__(self, seed=0):
        self.seed = seed

    def fit(self, X, yb, feat_idx):
        self.feat_idx = np.asarray(feat_idx)
        self.clf = DecisionTreeClassifier(criterion="gini", min_samples_split=20, min_samples_leaf=7,
                                          max_depth=30, random_state=self.seed).fit(X[:, self.feat_idx], yb)
        t = self.clf.tree_
        self.left, self.right, self.feat, self.thr = t.children_left, t.children_right, t.feature, t.threshold
        path = self.clf.decision_path(X[:, self.feat_idx]).toarray().astype(bool)
        self.counts = np.stack([(path & (yb == k)[:, None]).sum(0) for k in (0, 1)], axis=1)  # node x class
        self.n = len(yb)
        self.risk = (self.counts.sum(1) - self.counts.max(1)) / self.n                          # misclassification
        self.root_risk = self.risk[0]
        self._prune_sequence()
        return self

    def _subtree(self, node, pruned):
        """leaves and summed leaf risk of the subtree rooted at node, given pruned set"""
        if self.left[node] == -1 or node in pruned:
            return 1, self.risk[node]
        l1, r1 = self._subtree(self.left[node], pruned)
        l2, r2 = self._subtree(self.right[node], pruned)
        return l1 + l2, r1 + r2

    def _internal(self, node, pruned, out):
        if self.left[node] == -1 or node in pruned:
            return
        out.append(node)
        self._internal(self.left[node], pruned, out)
        self._internal(self.right[node], pruned, out)

    def _prune_sequence(self):
        pruned, seq = set(), []
        leaves, _ = self._subtree(0, pruned)
        seq.append((0.0, frozenset(pruned), leaves - 1))
        while True:
            internal = []
            self._internal(0, pruned, internal)
            if not internal:
                break
            g = {}
            for t in internal:
                L, Rt = self._subtree(t, pruned)
                g[t] = (self.risk[t] - Rt) / (L - 1)
            gmin = min(g.values())
            for t, v in g.items():
                if v <= gmin + 1e-12:
                    pruned.add(t)
            leaves, _ = self._subtree(0, pruned)
            seq.append((gmin, frozenset(pruned), leaves - 1))
        # cp = alpha / root risk (rpart scaling); keep the smallest tree for each alpha
        self.seq = [(a / self.root_risk, pr, ns) for a, pr, ns in seq]

    def pruned_at(self, cp):
        """pruned-node set of the subtree for complexity parameter cp"""
        best = self.seq[0][1]
        for c, pr, ns in self.seq:
            if c <= cp + 1e-12:
                best = pr
        return best

    def predict(self, X, pruned):
        Xf = X[:, self.feat_idx]
        out = np.empty(len(Xf), int)
        for i, x in enumerate(Xf):
            node = 0
            while self.left[node] != -1 and node not in pruned:
                node = self.left[node] if x[self.feat[node]] <= self.thr[node] else self.right[node]
            out[i] = int(np.argmax(self.counts[node]))
        return out

    def used_features(self, pruned):
        internal = []
        self._internal(0, pruned, internal)
        return internal, sorted({int(self.feat_idx[self.feat[t]]) for t in internal})

def cp_table(tree, X, yb, feat_idx, n_folds=10, seed=SEED):
    """rpart printcp equivalent: CP, nsplit, rel error, xerror, xstd (10-fold CV)."""
    cps = [c for c, _, _ in tree.seq]
    # rpart evaluates each cp at the geometric mean of consecutive cp values
    eval_cp = [np.sqrt(cps[i] * cps[i + 1]) if i + 1 < len(cps) else cps[i] * 10 for i in range(len(cps))]
    rows = []
    skf = StratifiedKFold(n_folds, shuffle=True, random_state=seed)
    err = np.zeros((len(cps), len(yb)))
    for tr, te in skf.split(X, yb):
        ft = RpartTree().fit(X[tr], yb[tr], feat_idx)
        for k, c in enumerate(eval_cp):
            err[k, te] = ft.predict(X[te], ft.pruned_at(c)) != yb[te]
    root_err = tree.root_risk * len(yb)
    for k, (c, pr, ns) in enumerate(tree.seq):
        rel = tree._subtree(0, pr)[1] / tree.root_risk
        xerr = err[k].sum() / root_err
        xstd = np.sqrt(err[k].mean() * (1 - err[k].mean()) * len(yb)) / root_err  # binomial SE, as in rpart
        rows.append(dict(CP=c, nsplit=ns, rel_error=rel, xerror=xerr, xstd=xstd))
    df = pd.DataFrame(rows).sort_values("nsplit", ascending=False).reset_index(drop=True)
    df = df.drop_duplicates("nsplit").sort_values("nsplit").reset_index(drop=True)
    return df

sig_idx = np.where(sig)[0]
t0 = time.time()
cart = RpartTree().fit(X, yb, sig_idx)
# check: unpruned predictions = sklearn predictions
check("Tier 2", "custom tree (unpruned) reproduces sklearn predictions", "100% agreement",
      f"{(cart.predict(X, frozenset()) == cart.clf.predict(X[:, sig_idx])).mean()*100:.1f}%",
      np.all(cart.predict(X, frozenset()) == cart.clf.predict(X[:, sig_idx])))
cpt = cp_table(cart, X, yb, sig_idx)
R["cp_table"] = cpt
# Tree A: rpart default cp = 0.01 (paper-faithful)
prA = cart.pruned_at(0.01)
nodesA, bandsA = cart.used_features(prA)
# Tree B: 1-SE rule
imin = cpt.xerror.idxmin()
thr_1se = cpt.xerror[imin] + cpt.xstd[imin]
row1se = cpt[cpt.xerror <= thr_1se].iloc[0]          # smallest tree within 1 SE
cp_1se = float(row1se.CP)
prB = cart.pruned_at(cp_1se)
nodesB, bandsB = cart.used_features(prB)
print(f"TIER 2: tree cp=0.01 uses {len(bandsA)} bands {[fmt(wl[b]) for b in bandsA]}; 1-SE tree (cp={cp_1se:.4f}) uses {len(bandsB)} bands ({time.time()-t0:.0f}s)")

def tree_nodes(tree, pruned):
    """Table of the nodes of the pruned tree (rpart-like print)."""
    rows = []
    def walk(node, depth, rule):
        is_leaf = tree.left[node] == -1 or node in pruned
        cH, cD = tree.counts[node]
        rows.append(dict(node_id=node, depth=depth, rule_from_parent=rule, n=int(cH + cD), n_healthy=int(cH), n_diseased=int(cD),
                         predicted=("diseased" if cD > cH else "healthy"), purity_pct=round(100 * max(cH, cD) / (cH + cD), 1),
                         type="leaf" if is_leaf else "split",
                         split=("" if is_leaf else f"R({fmt(wl[tree.feat_idx[tree.feat[node]]])} nm) <= {tree.thr[node]:.4f}")))
        if not is_leaf:
            walk(tree.left[node], depth + 1, "yes (<=)")
            walk(tree.right[node], depth + 1, "no (>)")
    walk(0, 0, "root")
    return pd.DataFrame(rows)
R["treeA_nodes"] = tree_nodes(cart, prA)
R["treeB_nodes"] = tree_nodes(cart, prB)
# variable importance (sum of Gini decrease over splits of the pruned tree, as rpart's primary-split part)
def importance(tree, pruned):
    t = tree.clf.tree_
    imp = {}
    internal, _ = tree.used_features(pruned)
    for nd in internal:
        l, r = tree.left[nd], tree.right[nd]
        dec = t.weighted_n_node_samples[nd] * t.impurity[nd] - t.weighted_n_node_samples[l] * t.impurity[l] - t.weighted_n_node_samples[r] * t.impurity[r]
        b = int(tree.feat_idx[tree.feat[nd]])
        imp[b] = imp.get(b, 0) + dec
    tot = sum(imp.values())
    return pd.DataFrame([dict(wavelength_nm=fmt(wl[b]), band_index=b, gini_decrease=v, importance_pct=100 * v / tot) for b, v in imp.items()]).sort_values("importance_pct", ascending=False)
R["treeA_importance"] = importance(cart, prA)
accA_train = (cart.predict(X, prA) == yb).mean()
accB_train = (cart.predict(X, prB) == yb).mean()
# CV accuracy of the CART classifier itself (cp=0.01)
skf = StratifiedKFold(10, shuffle=True, random_state=SEED)
pred_cart = np.empty(N, int)
for tr, te in skf.split(X, yb):
    ft = RpartTree().fit(X[tr], yb[tr], sig_idx)
    pred_cart[te] = ft.predict(X[te], ft.pruned_at(0.01))
R["cart_summary"] = dict(n_input_bands=int(len(sig_idx)), cpA=0.01, nsplitA=len(nodesA), bandsA=[float(wl[b]) for b in bandsA],
                         cp_1se=cp_1se, nsplitB=len(nodesB), bandsB=[float(wl[b]) for b in bandsB],
                         train_acc_A=float(accA_train), train_acc_B=float(accB_train), cv_acc_cart_A=float((pred_cart == yb).mean()))
check("Tier 2", "rel error of cp=0.01 tree equals 1 - training accuracy scaled", "consistent",
      f"rel error {cart._subtree(0, prA)[1]/cart.root_risk:.3f}; train acc {accA_train:.3f}",
      abs((1 - accA_train) - cart._subtree(0, prA)[1]) < 1e-9)

SEL = bandsA                           # bands passed to tiers 3 and 4 (paper-faithful tree)
sel_wl = wl[SEL]

# =====================================================================
# TIER 3  Jeffries-Matusita distance
# =====================================================================
def bhattacharyya(X0, X1):
    m0, m1 = X0.mean(0), X1.mean(0)
    C0, C1 = np.atleast_2d(np.cov(X0, rowvar=False)), np.atleast_2d(np.cov(X1, rowvar=False))
    C = (C0 + C1) / 2
    d = (m1 - m0)
    term1 = d @ np.linalg.solve(C, d) / 8
    s, ld = np.linalg.slogdet(C); s0, ld0 = np.linalg.slogdet(C0); s1, ld1 = np.linalg.slogdet(C1)
    term2 = 0.5 * (ld - 0.5 * (ld0 + ld1))
    return term1 + term2, term1, term2, (s > 0 and s0 > 0 and s1 > 0)
def jm2(B): return 2 * (1 - np.exp(-B))           # 0..2 scale (Richards)
B, b1, b2, okdet = bhattacharyya(X[yb == 0][:, SEL], X[yb == 1][:, SEL])
JM2, JMs = jm2(B), np.sqrt(jm2(B))
# direct determinant cross-check
C0 = np.cov(X[yb == 0][:, SEL], rowvar=False); C1 = np.cov(X[yb == 1][:, SEL], rowvar=False); Cm = (C0 + C1) / 2
B_direct = (X[yb == 1][:, SEL].mean(0) - X[yb == 0][:, SEL].mean(0)) @ np.linalg.inv(Cm) @ (X[yb == 1][:, SEL].mean(0) - X[yb == 0][:, SEL].mean(0)) / 8 \
    + 0.5 * np.log(np.linalg.det(Cm) / np.sqrt(np.linalg.det(C0) * np.linalg.det(C1)))
check("Tier 3", "Bhattacharyya B: log-determinant vs direct determinant", "equal", f"{B:.6f} vs {B_direct:.6f}", abs(B - B_direct) < 1e-6 * max(1, abs(B)))
# univariate JM per band + closed-form 1-D check
def B1d(a, b):
    m0, m1, v0, v1 = a.mean(), b.mean(), a.var(ddof=1), b.var(ddof=1)
    return (m1 - m0) ** 2 / (4 * (v0 + v1)) + 0.5 * np.log((v0 + v1) / (2 * np.sqrt(v0 * v1)))
jm_band = np.array([jm2(bhattacharyya(X[yb == 0][:, [j]], X[yb == 1][:, [j]])[0]) for j in range(P)])
jm_band_cf = np.array([jm2(B1d(X[yb == 0, j], X[yb == 1, j])) for j in range(P)])
check("Tier 3", "per-band JM: matrix formula vs 1-D closed form", "equal", f"max |diff| {np.max(np.abs(jm_band - jm_band_cf)):.1e}", np.max(np.abs(jm_band - jm_band_cf)) < 1e-9)
R["jm_band"] = pd.DataFrame({"wavelength_nm": wl, "JM_0to2": jm_band, "JM_sqrt_form": np.sqrt(jm_band), "selected_by_CART": np.isin(np.arange(P), SEL)})
# cumulative JM in CART importance order
order = [int(r.band_index) for r in R["treeA_importance"].itertuples()]
cum = []
for k in range(1, len(order) + 1):
    Bk = bhattacharyya(X[yb == 0][:, order[:k]], X[yb == 1][:, order[:k]])[0]
    cum.append(dict(n_bands=k, added_band_nm=fmt(wl[order[k - 1]]), JM_0to2=jm2(Bk), JM_sqrt_form=np.sqrt(jm2(Bk)), B=Bk))
R["jm_cumulative"] = pd.DataFrame(cum)
# singularity demonstration with all significant bands
C_all = np.cov(X[yb == 0][:, sig_idx], rowvar=False)
rank_all = np.linalg.matrix_rank(C_all)
R["tier3"] = dict(B=float(B), mahalanobis_term=float(b1), covariance_term=float(b2), JM_0to2=float(JM2), JM_sqrt=float(JMs),
                  threshold_0to2=1.94, separable=bool(JM2 >= 1.94), n_bands=len(SEL),
                  cov_rank_all_sig=int(rank_all), n_sig=int(len(sig_idx)), n_per_class=int(nH))
print(f"TIER 3: JM(0-2) = {JM2:.4f}, sqrt form = {JMs:.4f}; covariance rank with {len(sig_idx)} bands = {rank_all}")
for k, nm in ((0, "healthy"), (1, "diseased")):
    Ck = np.cov(X[yb == k][:, SEL], rowvar=False); ev = np.linalg.eigvalsh(Ck)
    R.setdefault("cov_info", {})[nm] = dict(rank=int(np.linalg.matrix_rank(Ck)), cond=float(ev.max() / ev.min()))
    check("Tier 3", f"{nm} covariance of CART bands is full rank (needed for JM and QDA)", f"rank {len(SEL)}",
          f"rank {np.linalg.matrix_rank(Ck)}, condition number {ev.max()/ev.min():.0f}", np.linalg.matrix_rank(Ck) == len(SEL))
check("Tier 3", "JM forms consistent: sqrt-form^2 = 0-2 form", "equal", f"{JMs**2:.6f} vs {JM2:.6f}", abs(JMs ** 2 - JM2) < 1e-12)

# =====================================================================
# TIER 4  QDA with 10-fold cross-validation  (+ Random Forest comparison)
# =====================================================================
def metrics(yt, yp):
    cm = confusion_matrix(yt, yp, labels=[0, 1])   # rows = reference (H, D), cols = predicted (H, D)
    oa = np.trace(cm) / cm.sum()
    pa = np.diag(cm) / cm.sum(1); ua = np.diag(cm) / cm.sum(0)
    kap = cohen_kappa_score(yt, yp)
    return dict(cm=cm, OA=oa, PA_H=pa[0], PA_D=pa[1], UA_H=ua[0], UA_D=ua[1], kappa=kap,
                balanced_acc=pa.mean(), F1_D=2 * pa[1] * ua[1] / (pa[1] + ua[1]))

QDA_FALLBACKS = []
class SafeQDA:
    """QDA (equal priors). sklearn's default rank tolerance (1e-4, absolute) wrongly rejects reflectance-scale
    covariance matrices, so tol=1e-12 is used. If a covariance matrix is truly singular, a tiny ridge
    (reg_param=1e-4) is used and the event is logged."""
    def fit(self, X, y):
        try:
            self.m = QuadraticDiscriminantAnalysis(priors=[0.5, 0.5], tol=1e-12).fit(X, y)
        except np.linalg.LinAlgError:
            QDA_FALLBACKS.append(X.shape[1])
            self.m = QuadraticDiscriminantAnalysis(priors=[0.5, 0.5], reg_param=1e-4).fit(X, y)
        return self
    def predict(self, X): return self.m.predict(X)
def qda(): return SafeQDA()
def rf(): return RandomForestClassifier(n_estimators=500, max_features="sqrt", random_state=SEED, n_jobs=-1)

def cv_predict(make, feats, n_rep=1, seed=SEED, folds=None):
    """returns out-of-fold predictions for each repetition and fold accuracies"""
    preds, fold_acc = [], []
    for r in range(n_rep):
        pr = np.empty(N, int)
        splits = folds if folds is not None else StratifiedKFold(10, shuffle=True, random_state=seed + r).split(X, yb)
        for tr, te in splits:
            m = make().fit(X[tr][:, feats], yb[tr])
            pr[te] = m.predict(X[te][:, feats])
            fold_acc.append((pr[te] == yb[te]).mean())
        preds.append(pr)
    return preds, np.array(fold_acc)

t0 = time.time()
q_pred, q_fold = cv_predict(qda, SEL, n_rep=10)
q_m = metrics(yb, q_pred[0])
q_rep = np.array([accuracy_score(yb, pp) for pp in q_pred])
folds0 = list(StratifiedKFold(10, shuffle=True, random_state=SEED).split(X, yb))
R["qda"] = dict(metrics=q_m, fold_acc_rep1=q_fold[:10], rep_acc=q_rep)
print(f"TIER 4 QDA (paper-style 10-fold CV): OA {q_m['OA']*100:.2f}%, kappa {q_m['kappa']:.3f}; 10x repeated {q_rep.mean()*100:.2f} ± {q_rep.std()*100:.2f}")
check("Tier 4", "confusion-matrix total equals number of spectra", N, int(q_m["cm"].sum()), q_m["cm"].sum() == N)
check("Tier 4", "OA from confusion matrix = sklearn accuracy", "equal", f"{q_m['OA']:.4f} vs {accuracy_score(yb, q_pred[0]):.4f}", abs(q_m["OA"] - accuracy_score(yb, q_pred[0])) < 1e-12)
# manual QDA discriminant check on fold 1
tr, te = folds0[0]
mdl = qda().fit(X[tr][:, SEL], yb[tr]).m
def qda_manual(Xtr, ytr, Xte):
    sc = []
    for k in (0, 1):
        Xk = Xtr[ytr == k]; mu = Xk.mean(0); C = np.cov(Xk, rowvar=False)
        s, ld = np.linalg.slogdet(C); d = Xte - mu
        sc.append(-0.5 * ld - 0.5 * np.einsum("ij,ij->i", d @ np.linalg.inv(C), d) + np.log(0.5))
    return np.argmax(np.stack(sc, 1), 1)
man = qda_manual(X[tr][:, SEL], yb[tr], X[te][:, SEL])
check("Tier 4", "QDA: hand-coded Gaussian discriminant = sklearn QDA (fold 1)", "100% agreement",
      f"{(man == mdl.predict(X[te][:, SEL])).mean()*100:.1f}%", np.all(man == mdl.predict(X[te][:, SEL])))

# Random Forest on three band sets, same folds
feature_sets = {"CART bands (tiers 2-3)": SEL, "All ANOVA-significant bands": list(sig_idx), "All 463 bands": list(range(P))}
rf_res = {}
for name, fs in feature_sets.items():
    pr, fa = cv_predict(rf, fs, n_rep=1, folds=folds0)
    oob = RandomForestClassifier(n_estimators=500, max_features="sqrt", random_state=SEED, n_jobs=-1, oob_score=True).fit(X[:, fs], yb).oob_score_
    rf_res[name] = dict(metrics=metrics(yb, pr[0]), fold_acc=fa, oob=oob, n_bands=len(fs))
    print(f"  RF [{name}] {len(fs)} bands: CV OA {rf_res[name]['metrics']['OA']*100:.2f}%  OOB {oob*100:.2f}%")
# QDA also evaluated on identical folds (rep 1 used folds0 already since seed+0)
R["rf"] = rf_res
# QDA on all significant bands is impossible (singular) -> regularised check not done; record
rf_all = RandomForestClassifier(n_estimators=500, max_features="sqrt", random_state=SEED, n_jobs=-1).fit(X, yb)
imp = pd.DataFrame({"wavelength_nm": wl, "MDI_importance": rf_all.feature_importances_})
imp["rank"] = imp.MDI_importance.rank(ascending=False).astype(int)
R["rf_importance"] = imp
rf_again = RandomForestClassifier(n_estimators=500, max_features="sqrt", random_state=SEED, n_jobs=-1).fit(X, yb)
check("RF", "same seed reproduces identical forest importances", "identical",
      f"max |diff| {np.max(np.abs(rf_again.feature_importances_ - rf_all.feature_importances_)):.1e}",
      np.allclose(rf_again.feature_importances_, rf_all.feature_importances_))
check("RF", "OOB accuracy close to 10-fold CV accuracy (all bands)", "within 2 percentage points",
      f"OOB {rf_res['All 463 bands']['oob']*100:.2f}% vs CV {rf_res['All 463 bands']['metrics']['OA']*100:.2f}%",
      abs(rf_res['All 463 bands']['oob'] - rf_res['All 463 bands']['metrics']['OA']) < 0.02)
print(f"  ({time.time()-t0:.0f}s)")

# =====================================================================
# VALIDATION CROSS-CHECKS
# =====================================================================
def select_bands(Xtr, ytr):
    Ft, pt, _, _ = anova_F(Xtr, ytr)
    si = np.where(pt < 0.05)[0]
    if len(si) == 0:
        return [], 0
    tr_ = RpartTree().fit(Xtr, ytr, si)
    _, b = tr_.used_features(tr_.pruned_at(0.01))
    return b, len(si)

def nested(folds, Xm=None, ym=None, with_rf=True):
    Xm = X if Xm is None else Xm; ym = yb if ym is None else ym
    pq, prf, prf_all = np.empty(len(ym), int), np.empty(len(ym), int), np.empty(len(ym), int)
    chosen = []
    for tr, te in folds:
        b, ns = select_bands(Xm[tr], ym[tr])
        chosen.append(b)
        if len(b) == 0:
            pq[te] = prf[te] = np.bincount(ym[tr]).argmax(); prf_all[te] = pq[te]; continue
        pq[te] = qda().fit(Xm[tr][:, b], ym[tr]).predict(Xm[te][:, b])
        if with_rf:
            prf[te] = rf().fit(Xm[tr][:, b], ym[tr]).predict(Xm[te][:, b])
            prf_all[te] = rf().fit(Xm[tr], ym[tr]).predict(Xm[te])
    return pq, prf, prf_all, chosen

t0 = time.time()
# (a) nested random 10-fold
nq, nrf, nrf_all, chosen = nested(folds0)
freq = pd.Series([fmt(wl[b]) for c in chosen for b in c]).value_counts()
R["nested"] = dict(qda=metrics(yb, nq), rf_sel=metrics(yb, nrf), rf_all=metrics(yb, nrf_all),
                   n_bands_per_fold=[len(c) for c in chosen], band_frequency=freq)
print(f"NESTED 10-fold: QDA {R['nested']['qda']['OA']*100:.2f}%, RF(sel) {R['nested']['rf_sel']['OA']*100:.2f}%, RF(all) {R['nested']['rf_all']['OA']*100:.2f}%  ({time.time()-t0:.0f}s)")

# (b) spatial block CV: 5 k-means blocks per class on pixel coordinates, fold i = H-block i + D-block i
coords = data[["row_0based", "col_0based"]].to_numpy(float)
block = np.empty(N, int)
for k in (0, 1):
    m = yb == k
    km = KMeans(5, n_init=10, random_state=SEED).fit(coords[m])
    lab = km.labels_
    # order blocks by mean row so pairing is deterministic
    order_ = np.argsort(km.cluster_centers_[:, 0])
    remap = {old: new for new, old in enumerate(order_)}
    block[m] = [remap[l] for l in lab]
sfolds = [(np.where(block != b)[0], np.where(block == b)[0]) for b in range(5)]
sq, srf, srf_all, schosen = nested(sfolds)
blk = pd.DataFrame({"class": y, "block": block, "row": coords[:, 0], "col": coords[:, 1]})
R["spatial"] = dict(qda=metrics(yb, sq), rf_sel=metrics(yb, srf), rf_all=metrics(yb, srf_all),
                    block_sizes=blk.groupby(["class", "block"]).size().unstack().to_dict(), blocks=blk,
                    per_fold=[dict(fold=b + 1, n_test=int((block == b).sum()),
                                   qda=float((sq[block == b] == yb[block == b]).mean()),
                                   rf_sel=float((srf[block == b] == yb[block == b]).mean()),
                                   rf_all=float((srf_all[block == b] == yb[block == b]).mean()),
                                   bands=", ".join(fmt(wl[i]) for i in schosen[b])) for b in range(5)])
print(f"SPATIAL block CV: QDA {R['spatial']['qda']['OA']*100:.2f}%, RF(sel) {R['spatial']['rf_sel']['OA']*100:.2f}%, RF(all) {R['spatial']['rf_all']['OA']*100:.2f}%  ({time.time()-t0:.0f}s)")

# (c) location-only control: split each class into two spatial halves and try to discriminate them
ctrl = []
for k, name in ((0, "healthy"), (1, "diseased")):
    m = np.where(yb == k)[0]
    km = KMeans(2, n_init=10, random_state=SEED).fit(coords[m])
    yy = km.labels_.astype(int)
    Xm = X[m]
    f = list(StratifiedKFold(10, shuffle=True, random_state=SEED).split(Xm, yy))
    b, _ = select_bands(Xm, yy)
    pq_ = np.empty(len(yy), int)
    for tr, te in f:
        pq_[te] = qda().fit(Xm[tr][:, b], yy[tr]).predict(Xm[te][:, b])
    nq_, _, _, _ = nested(f, Xm, yy, with_rf=False)
    ctrl.append(dict(control=f"{name}: half A vs half B", n=f"{(yy==0).sum()} vs {(yy==1).sum()}",
                     paper_style_QDA_OA=float((pq_ == yy).mean()), nested_QDA_OA=float((nq_ == yy).mean()),
                     bands=", ".join(fmt(wl[i]) for i in b)))
R["location_control"] = pd.DataFrame(ctrl)
print(R["location_control"])

# (d) permutation test (nested pipeline, QDA)
t0 = time.time()
rng = np.random.default_rng(SEED)
NPERM = 200
perm_acc = []
for i in range(NPERM):
    yp_ = rng.permutation(yb)
    f = list(StratifiedKFold(10, shuffle=True, random_state=SEED).split(X, yp_))
    pq_, _, _, _ = nested(f, X, yp_, with_rf=False)
    perm_acc.append((pq_ == yp_).mean())
perm_acc = np.array(perm_acc)
obs = R["nested"]["qda"]["OA"]
R["permutation"] = dict(n=NPERM, acc=perm_acc, observed=obs, p=(1 + (perm_acc >= obs).sum()) / (NPERM + 1))
print(f"PERMUTATION: null mean {perm_acc.mean()*100:.1f}% (max {perm_acc.max()*100:.1f}%), observed {obs*100:.2f}%, p = {R['permutation']['p']:.4f} ({time.time()-t0:.0f}s)")
check("Validation", "permutation null centred near chance", "≈ 50%", f"{perm_acc.mean()*100:.1f}%", abs(perm_acc.mean() - 0.5) < 0.05)

# (e) sensitivity analyses (paper-style pipeline)
def paper_pipeline(Xm, ym, wlm):
    Ft, pt, _, _ = anova_F(Xm, ym); si = np.where(pt < 0.05)[0]
    t_ = RpartTree().fit(Xm, ym, si); _, b = t_.used_features(t_.pruned_at(0.01))
    f = StratifiedKFold(10, shuffle=True, random_state=SEED).split(Xm, ym)
    pr = np.empty(len(ym), int)
    for tr, te in f:
        pr[te] = qda().fit(Xm[tr][:, b], ym[tr]).predict(Xm[te][:, b])
    B_ = bhattacharyya(Xm[ym == 0][:, b], Xm[ym == 1][:, b])[0]
    rfp = np.empty(len(ym), int)
    for tr, te in StratifiedKFold(10, shuffle=True, random_state=SEED).split(Xm, ym):
        rfp[te] = rf().fit(Xm[tr], ym[tr]).predict(Xm[te])
    return dict(n_sig=len(si), bands=", ".join(fmt(wlm[i]) for i in b), n_sel=len(b), JM=jm2(B_), QDA_OA=(pr == ym).mean(), RF_all_OA=(rfp == ym).mean())
sens = []
s = paper_pipeline(X, yb, wl); s.update(case="Main analysis: 600 spectra, 420-2350 nm (463 bands)"); sens.append(s)
yb_all = (y_all == "diseased").astype(int)
m_ns2 = wl < 1900
s = paper_pipeline(X[:, m_ns2], yb, wl[m_ns2]); s.update(case="SWIR-2 excluded (420-1780 nm, 399 bands)"); sens.append(s)
m_vnir = wl < 1000
s = paper_pipeline(X[:, m_vnir], yb, wl[m_vnir]); s.update(case="VNIR only (420-1000 nm)"); sens.append(s)
s = paper_pipeline(X_all, yb_all, wl_all); s.update(case="All 483 bands incl. noisy edges (399-2398 nm)"); sens.append(s)
R["sensitivity"] = pd.DataFrame(sens)[["case", "n_sig", "n_sel", "bands", "JM", "QDA_OA", "RF_all_OA"]]
print(R["sensitivity"])

R["qda_fallbacks"] = len(QDA_FALLBACKS)
print("QDA fits that needed the ridge fallback:", len(QDA_FALLBACKS))
R["checks"] = pd.DataFrame(CHECKS)
R["wl"] = wl; R["X"] = X; R["y"] = y; R["data"] = data; R["SEL"] = SEL; R["sig"] = sig; R["wl_all"] = wl_all
R["cart_obj"] = dict(left=cart.left, right=cart.right, feat=cart.feat, thr=cart.thr, counts=cart.counts, feat_idx=cart.feat_idx, prA=prA, prB=prB)
with open("results/results.pkl", "wb") as fh:
    pickle.dump(R, fh)
print("saved results/results.pkl;", (R["checks"].result == "PASS").sum(), "/", len(R["checks"]), "checks passed")
