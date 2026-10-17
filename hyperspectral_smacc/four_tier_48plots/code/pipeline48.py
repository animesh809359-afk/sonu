"""Shared pipeline for the 48-plot analysis: Tier 1 ANOVA, imbalance strategies, Tier 2 (CART / RF band selection),
Tier 3 (Bhattacharyya / Jeffries-Matusita), Tier 4 (QDA) and accuracy metrics. Used by analysis48.py and design48.py."""
import numpy as np, pandas as pd
from scipy import stats
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis
from sklearn.metrics import (confusion_matrix, cohen_kappa_score, matthews_corrcoef, f1_score,
                             balanced_accuracy_score, roc_auc_score, accuracy_score)
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler
SEED = 42
# ======================================================================= Tier 1
def anova(Xm, ym):
    g0, g1 = Xm[ym == 0], Xm[ym == 1]; gm = Xm.mean(0)
    ssb = len(g0) * (g0.mean(0) - gm) ** 2 + len(g1) * (g1.mean(0) - gm) ** 2
    ssw = ((g0 - g0.mean(0)) ** 2).sum(0) + ((g1 - g1.mean(0)) ** 2).sum(0)
    F = ssb / (ssw / (len(ym) - 2))
    return F, stats.f.sf(F, 1, len(ym) - 2), ssb, ssw

# ======================================================================= imbalance handling (training data only)
STRATS = {"S0": "No correction", "S1": "Class weighting (cost-sensitive)", "S2": "Random under-sampling", "S3": "SMOTE over-sampling"}
def resample(Xtr, ytr, s, seed):
    if s == "S2":
        Xr, yr = RandomUnderSampler(random_state=seed).fit_resample(Xtr, ytr)
    elif s == "S3":
        Xr, yr = SMOTE(k_neighbors=5, random_state=seed).fit_resample(Xtr, ytr)
    else:
        Xr, yr = Xtr, ytr
    if s == "S1":
        n0, n1 = (yr == 0).sum(), (yr == 1).sum()
        w = np.where(yr == 0, len(yr) / (2 * n0), len(yr) / (2 * n1))
    else:
        w = np.ones(len(yr))
    return Xr, yr, w

# ======================================================================= Tier 2a: CART (rpart-equivalent, weighted)
class RpartTree:
    """Gini tree with rpart defaults (minsplit 20, minbucket 7, maxdepth 30) and cost-complexity pruning on
    (weighted) misclassification risk = rpart's cp. Weights reproduce rpart's 'prior' for class balancing."""
    def fit(self, Xm, ym, w, feat_idx):
        self.feat_idx = np.asarray(feat_idx)
        self.clf = DecisionTreeClassifier(criterion="gini", min_samples_split=20, min_samples_leaf=7, max_depth=30,
                                          random_state=0).fit(Xm[:, self.feat_idx], ym, sample_weight=w)
        t = self.clf.tree_
        self.L, self.Rr, self.f, self.thr = t.children_left, t.children_right, t.feature, t.threshold
        path = self.clf.decision_path(Xm[:, self.feat_idx]).tocsc()
        oh = np.stack([(ym == k) * w for k in (0, 1)], 1)
        self.counts = np.asarray(path.T @ oh)                                   # weighted class totals per node
        self.risk = (self.counts.sum(1) - self.counts.max(1)) / w.sum()
        self._sequence(); return self
    def _sequence(self):
        n = len(self.L); pruned = np.zeros(n, bool); seq = [(0.0, pruned.copy())]
        post = []; st = [(0, False)]
        while st:
            nd, done = st.pop()
            if done or self.L[nd] == -1: post.append(nd); continue
            st += [(nd, True), (self.Rr[nd], False), (self.L[nd], False)]
        while True:
            leaves = np.zeros(n); rsk = np.zeros(n); active_internal = []
            for nd in post:
                if self.L[nd] == -1 or pruned[nd]:
                    leaves[nd], rsk[nd] = 1, self.risk[nd]
                else:
                    leaves[nd] = leaves[self.L[nd]] + leaves[self.Rr[nd]]; rsk[nd] = rsk[self.L[nd]] + rsk[self.Rr[nd]]
            # internal nodes reachable from root
            stack = [0]
            while stack:
                nd = stack.pop()
                if self.L[nd] != -1 and not pruned[nd]:
                    active_internal.append(nd); stack += [self.L[nd], self.Rr[nd]]
            if not active_internal: break
            g = np.array([(self.risk[t] - rsk[t]) / (leaves[t] - 1) for t in active_internal])
            gmin = g.min()
            for t, v in zip(active_internal, g):
                if v <= gmin + 1e-12: pruned[t] = True
            seq.append((gmin, pruned.copy()))
        self.seq = [(a / self.risk[0], pr) for a, pr in seq]
    def pruned_at(self, cp):
        best = self.seq[0][1]
        for c, pr in self.seq:
            if c <= cp + 1e-12: best = pr
        return best
    def internal(self, pr):
        out, st = [], [0]
        while st:
            nd = st.pop()
            if self.L[nd] != -1 and not pr[nd]: out.append(nd); st += [self.L[nd], self.Rr[nd]]
        return out
    def bands(self, pr): return sorted({int(self.feat_idx[self.f[t]]) for t in self.internal(pr)})
    def predict(self, Xm, pr):
        Xf = Xm[:, self.feat_idx]; out = np.empty(len(Xf), int)
        for i, x in enumerate(Xf):
            nd = 0
            while self.L[nd] != -1 and not pr[nd]:
                nd = self.L[nd] if x[self.f[nd]] <= self.thr[nd] else self.Rr[nd]
            out[i] = int(np.argmax(self.counts[nd]))
        return out

def cart_select(Xr, yr, w, sig_idx):
    t = RpartTree().fit(Xr, yr, w, sig_idx); pr = t.pruned_at(0.01)
    return t.bands(pr), t, pr

# ======================================================================= Tier 2b: Random Forest band selection
def rf_model(s, n=500):
    return RandomForestClassifier(n_estimators=n, max_features="sqrt", random_state=SEED, n_jobs=-1,
                                  class_weight="balanced" if s == "S1" else None)
def rf_select(Xr, yr, s, sig_idx, K, r_thr=0.95):
    imp = rf_model(s).fit(Xr[:, sig_idx], yr).feature_importances_
    ordr = sig_idx[np.argsort(-imp)]
    C = np.corrcoef(Xr[:, ordr], rowvar=False)
    chosen = []
    for i in range(len(ordr)):
        if all(abs(C[i, j]) < r_thr for j in chosen): chosen.append(i)
        if len(chosen) == K: break
    return [int(ordr[i]) for i in chosen], pd.DataFrame({"band": sig_idx, "importance": imp})

# ======================================================================= Tier 4: QDA
FALLBACK = []
def qda_fit(Xr, yr, s):
    pri = [0.5, 0.5] if s == "S1" else None          # S0: empirical priors; S2/S3: data already balanced
    try:
        return QuadraticDiscriminantAnalysis(priors=pri, tol=1e-12).fit(Xr, yr)
    except np.linalg.LinAlgError:
        FALLBACK.append(Xr.shape[1]); return QuadraticDiscriminantAnalysis(priors=pri, reg_param=1e-4).fit(Xr, yr)

class PriorModel:
    """Used when Tier 1 finds no significant band or Tier 2 keeps no band: nothing to discriminate with, so every
    spectrum gets the class with the larger (weighted) training prior; balanced accuracy is then exactly 0.5."""
    def __init__(self, yr, w): self.p1 = float(w[yr == 1].sum() / w.sum())
    def predict(self, Xe): return np.full(len(Xe), int(self.p1 >= 0.5))
    def predict_proba(self, Xe): return np.column_stack([np.full(len(Xe), 1 - self.p1), np.full(len(Xe), self.p1)])
NO_BANDS = []
def fit_pipeline(Xtr, ytr, s, tier2, seed, sig_idx=None):
    """Tier 1 on the original training spectra; Tier 2 and Tier 4 on the re-balanced training spectra."""
    if sig_idx is None:
        sig_idx = np.where(anova(Xtr, ytr)[1] < 0.05)[0]
    Xr, yr, w = resample(Xtr, ytr, s, seed)
    cb = cart_select(Xr, yr, w, sig_idx)[0] if len(sig_idx) else []
    if len(cb) == 0:
        NO_BANDS.append((tier2, s, len(sig_idx))); return PriorModel(yr, w), [0], len(sig_idx)
    bands = cb if tier2 == "CART" else rf_select(Xr, yr, s, sig_idx, len(cb))[0]
    return qda_fit(Xr[:, bands], yr, s), bands, len(sig_idx)

def metrics(yt, yp, prob=None):
    cm = confusion_matrix(yt, yp, labels=[0, 1]); pa = np.diag(cm) / cm.sum(1); ua = np.diag(cm) / np.maximum(cm.sum(0), 1)
    out = dict(cm=cm, OA=accuracy_score(yt, yp), BA=balanced_accuracy_score(yt, yp), kappa=cohen_kappa_score(yt, yp),
               MCC=matthews_corrcoef(yt, yp), F1_D=f1_score(yt, yp, pos_label=1), F1_H=f1_score(yt, yp, pos_label=0),
               sens_D=pa[1], spec_H=pa[0], UA_H=ua[0], UA_D=ua[1])
    if prob is not None and len(set(yt)) == 2: out["AUC"] = roc_auc_score(yt, prob)
    return out
def plot_level(yt, yp, grp):
    df = pd.DataFrame({"g": grp, "t": yt, "p": yp}).groupby("g").agg(t=("t", "first"), frac=("p", "mean"))
    df["pred"] = (df.frac > 0.5).astype(int)
    m = metrics(df.t.values, df.pred.values); m["table"] = df; return m

# ======================================================================= Tier 2/3 on all data (reported bands, J-M)
def bhatt(X0, X1):
    m0, m1 = X0.mean(0), X1.mean(0); C0, C1 = np.atleast_2d(np.cov(X0, rowvar=False)), np.atleast_2d(np.cov(X1, rowvar=False))
    C = (C0 + C1) / 2; dd = m1 - m0
    return dd @ np.linalg.solve(C, dd) / 8 + 0.5 * (np.linalg.slogdet(C)[1] - 0.5 * (np.linalg.slogdet(C0)[1] + np.linalg.slogdet(C1)[1]))
def jm2(B): return 2 * (1 - np.exp(-B))
def B1d(a, b):
    m0, m1, v0, v1 = a.mean(), b.mean(), a.var(ddof=1), b.var(ddof=1)
    return (m1 - m0) ** 2 / (4 * (v0 + v1)) + 0.5 * np.log((v0 + v1) / (2 * np.sqrt(v0 * v1)))
