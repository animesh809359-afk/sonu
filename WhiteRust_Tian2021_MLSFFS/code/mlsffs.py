"""Core methods of the ML-SFFS workflow (Tian et al., 2021, Remote Sens. Environ. 257, 112350)
re-implemented for the white-rust mustard plot-average data, with the corrections documented
in the report (balanced accuracy, guard zones, nested cross-validation).
"""
import numpy as np, pandas as pd, pywt
from scipy import ndimage
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.model_selection import StratifiedKFold

DATES = ["11-02-2026", "24-02-2026", "03-03-2026", "13-03-2026"]
DLAB = {"11-02-2026": "T1 (11 Feb)", "24-02-2026": "T2 (24 Feb)", "03-03-2026": "T3 (3 Mar)", "13-03-2026": "T4 (13 Mar)"}
# spectral range used (correction C1): noisy detector edges and the detector-join guard zones are excluded
WL_MIN, WL_MAX = 400, 2400
GUARDS = [(990, 1010), (1795, 1835)]
CWT_SCALES = [2 ** j for j in range(1, 9)]       # dyadic scales 2^1 ... 2^8 (Cheng et al., 2010)
CWT_KEEP = [3, 4, 5, 6, 7, 8]                    # scales 3-8 retained as in Tian et al. (2021)
SPECTRAL_FAMS = ["R", "D1", "D2", "D3", "CWT"]
SCALAR_FAMS = ["VI", "CR", "RE"]
FAM_NAME = {"R": "Reflectance band", "D1": "First derivative", "D2": "Second derivative",
            "D3": "Third derivative", "CWT": "Wavelet coefficient (CWT, Mexican hat)",
            "VI": "Vegetation index", "CR": "Continuum-removal parameter", "RE": "Red-edge parameter"}


def in_range(wl):
    wl = np.asarray(wl)
    ok = (wl >= WL_MIN) & (wl <= WL_MAX)
    for a, b in GUARDS:
        ok &= ~((wl >= a) & (wl <= b))
    return ok


def cwt_features(R):
    """Continuous wavelet transform of every plot spectrum (Mexican hat, dyadic scales).
    R: DataFrame plots x wavelengths (350-2500 nm, 1 nm). Returns DataFrame with columns 'Ssc_λ'."""
    out = {}
    X = R.values
    coefs = np.stack([pywt.cwt(x, CWT_SCALES, "mexh")[0] for x in X])  # plots x scales x wl
    wl = np.array(R.columns)
    keep = in_range(wl)
    for si, s in enumerate(CWT_SCALES, start=1):
        if si not in CWT_KEEP:
            continue
        for j in np.where(keep)[0]:
            out[f"S{si}_{wl[j]}"] = coefs[:, si - 1, j]
    return pd.DataFrame(out, index=R.index)


def build_features(day):
    """All candidate features of one date as {family: DataFrame plots x features}."""
    fam = {}
    for f in ["R", "D1", "D2", "D3"]:
        df = day[f]
        cols = [c for c in df.columns if in_range([c])[0]]
        fam[f] = df[cols].rename(columns=lambda c, f=f: f"{f}_{c}")
    fam["CWT"] = cwt_features(day["R"])
    for f in SCALAR_FAMS:
        fam[f] = day[f].copy()
    return fam


# ---------------------------------------------------------------- separability (thresholding)
def threshold_separability(X, y, n_steps=100):
    """Thresholding technique of Tian et al. (2021, Fig. 3) after Mahlein et al. (2013).
    For each feature the interval between the class means Mi (infected) and Mh (healthy) is divided
    into n_steps equal parts; every division point is used as a threshold and the best one is kept.
    Returns DataFrame with Mi, Mh, threshold, OA and balanced accuracy (BA) of the best threshold.
    The best threshold is chosen by BA (correction C2: 12 healthy vs 36 diseased plots)."""
    X = np.asarray(X, float)
    y = np.asarray(y)
    mi = X[y == 1].mean(0)
    mh = X[y == 0].mean(0)
    frac = (np.arange(n_steps + 1) / n_steps)[:, None]
    thr = mh[None, :] + frac * (mi - mh)[None, :]                  # (steps+1) x features
    sign = np.where(mi >= mh, 1.0, -1.0)                           # infected above or below
    pred = (sign[None, None, :] * (X[None, :, :] - thr[:, None, :])) > 0   # steps x n x p
    pos = (y == 1)[None, :, None]
    tp = (pred & pos).sum(1)
    tn = (~pred & ~pos).sum(1)
    n1, n0 = (y == 1).sum(), (y == 0).sum()
    sens = tp / n1
    spec = tn / n0
    ba = 0.5 * (sens + spec)
    oa = (tp + tn) / len(y)
    k = ba.argmax(0)
    idx = np.arange(X.shape[1])
    return pd.DataFrame({"Mi": mi, "Mh": mh, "threshold": thr[k, idx], "BA": ba[k, idx],
                         "OA": oa[k, idx], "sens": sens[k, idx], "spec": spec[k, idx],
                         "OA_max": oa.max(0)})


def top_fraction(scores, frac):
    """Boolean mask of the features whose score lies in the top `frac` (ties included)."""
    cut = np.quantile(scores, 1 - frac)
    return scores >= cut


# ---------------------------------------------------------------- regions and representatives
def regions_1d(names):
    """Group feature names 'F_λ' into contiguous wavelength regions."""
    wl = sorted(int(n.split("_")[1]) for n in names)
    regs, cur = [], [wl[0]] if wl else []
    for a in wl[1:]:
        if a == cur[-1] + 1:
            cur.append(a)
        else:
            regs.append(cur); cur = [a]
    if cur:
        regs.append(cur)
    return regs


def regions_cwt(names, wl_all):
    """Connected regions (8-connectivity) of selected wavelet features in the scale x wavelength plane."""
    wl_idx = {w: i for i, w in enumerate(wl_all)}
    grid = np.zeros((len(CWT_KEEP), len(wl_all)), bool)
    for n in names:
        s, w = n.split("_")
        grid[CWT_KEEP.index(int(s[1:])), wl_idx[int(w)]] = True
    lab, nlab = ndimage.label(grid, structure=np.ones((3, 3)))
    regs = []
    for k in range(1, nlab + 1):
        ss, ww = np.where(lab == k)
        regs.append([f"S{CWT_KEEP[a]}_{wl_all[b]}" for a, b in zip(ss, ww)])
    return regs


# ---------------------------------------------------------------- VIF
def vif(X):
    C = np.corrcoef(X, rowvar=False)
    return np.diag(np.linalg.pinv(C))


def vif_reduce(X, names, limit=10.0, relevance=None):
    """Iterative VIF reduction until every VIF < limit.
    relevance=None : drop the feature with the largest VIF (plain rule).
    relevance=array: among the features with VIF >= limit drop the least separable one
                     (relevance-aware rule used for the DSSF pool)."""
    names = list(names)
    X = np.asarray(X, float)
    rel = None if relevance is None else list(relevance)
    log = []
    while True:
        v = vif(X)
        if v.max() < limit or len(names) <= 1:
            log.append(dict(step=len(log) + 1, removed=None, vif=dict(zip(names, v))))
            return names, log
        if rel is None:
            j = int(np.argmax(v))
        else:
            over = np.where(v >= limit)[0]
            j = int(over[np.argmin([rel[i] for i in over])])
        log.append(dict(step=len(log) + 1, removed=names[j], removed_vif=float(v[j]), vif=dict(zip(names, v))))
        names.pop(j)
        if rel is not None:
            rel.pop(j)
        X = np.delete(X, j, axis=1)


# ---------------------------------------------------------------- classifiers and CV criterion
SVM_C = [2.0 ** k for k in (-1, 1, 3, 5, 7)]
SVM_G = [2.0 ** k for k in (-5, -3, -1, 1)]   # multiplied by 1/n_features (standardised inputs)


def make_clf(name, balanced=False, C=1.0, g=1.0, nfeat=1):
    if name == "LDA":
        return LinearDiscriminantAnalysis(priors=[0.5, 0.5] if balanced else None)
    if name == "kNN":
        return KNeighborsClassifier(n_neighbors=3, metric="minkowski", p=2)
    if name == "SVM":
        return SVC(kernel="rbf", C=C, gamma=g / nfeat, class_weight="balanced" if balanced else None)
    raise ValueError(name)


def metrics(y, p):
    y = np.asarray(y); p = np.asarray(p)
    tp = np.sum((p == 1) & (y == 1)); tn = np.sum((p == 0) & (y == 0))
    fp = np.sum((p == 1) & (y == 0)); fn = np.sum((p == 0) & (y == 1))
    n = len(y)
    oa = (tp + tn) / n
    sens = tp / (tp + fn) if tp + fn else np.nan
    spec = tn / (tn + fp) if tn + fp else np.nan
    pe = ((tp + fp) * (tp + fn) + (fn + tn) * (fp + tn)) / n ** 2
    kappa = (oa - pe) / (1 - pe) if pe < 1 else 0.0
    return dict(OA=oa, BA=0.5 * (sens + spec), kappa=kappa, sens=sens, spec=spec)


def _zfit(Xtr, Xte):
    mu = Xtr.mean(0); sd = Xtr.std(0); sd[sd == 0] = 1
    return (Xtr - mu) / sd, (Xte - mu) / sd


def cv_predict(X, y, folds, clf_name, balanced, C=1.0, g=1.0):
    p = np.empty(len(y), int)
    for tr, te in folds:
        a, b = _zfit(X[tr], X[te])
        try:
            m = make_clf(clf_name, balanced, C, g, X.shape[1]).fit(a, y[tr])
            p[te] = m.predict(b)
        except (IndexError, ValueError, np.linalg.LinAlgError):
            # degenerate training fold (a feature constant within both classes): the classifier
            # cannot be fitted, so the uninformative majority-class prediction is used
            p[te] = np.bincount(y[tr]).argmax()
    return p


def evaluate_subset(X, y, folds_list, clf_name, criterion, balanced):
    """Cross-validated criterion of a feature subset. For the SVM the grid of (C, gamma) is searched and
    the best value is returned (grid search as in Tian et al., 2021). Returns (score, params, metrics)."""
    grid = [(C, g) for C in SVM_C for g in SVM_G] if clf_name == "SVM" else [(1.0, 1.0)]
    best = (-1, None, None)
    for C, g in grid:
        ms = []
        for folds in folds_list:
            ms.append(metrics(y, cv_predict(X, y, folds, clf_name, balanced, C, g)))
        m = {k: float(np.mean([d[k] for d in ms])) for k in ms[0]}
        if m[criterion] > best[0] + 1e-12:
            best = (m[criterion], (C, g), m)
    return best


def sffs(X, y, folds_list, clf_name, criterion="OA", balanced=False, kmax=8):
    """Sequential floating forward selection (Pudil et al., 1994) with a classifier as criterion function.
    Returns the optimal feature combination (OFC) = subset with the highest criterion (ties -> fewer
    features), its score, SVM parameters and metrics, and the best subset of every size."""
    p = X.shape[1]
    kmax = min(kmax, p)
    cache = {}

    def J(sub):
        key = tuple(sorted(sub))
        if key not in cache:
            cache[key] = evaluate_subset(X[:, list(key)], y, folds_list, clf_name, criterion, balanced)
        return cache[key]

    best = {}          # size -> (score, subset)
    cur = []
    while len(cur) < kmax:
        # step 1: inclusion of the most significant feature
        cand = [f for f in range(p) if f not in cur]
        sc = [J(cur + [f])[0] for f in cand]
        cur = cur + [cand[int(np.argmax(sc))]]
        k = len(cur)
        s = max(sc)
        if k not in best or s > best[k][0] + 1e-12:
            best[k] = (s, list(cur))
        else:
            cur = list(best[k][1])
        if best[k][0] >= 1 - 1e-12:      # criterion cannot be exceeded; ties are resolved to fewer features
            break
        # steps 2-3: conditional exclusion of the least significant feature
        while len(cur) > 2:
            sc = [J([f for f in cur if f != r])[0] for r in cur]
            j = int(np.argmax(sc))
            if sc[j] > best[len(cur) - 1][0] + 1e-12:
                cur = [f for f in cur if f != cur[j]]
                best[len(cur)] = (sc[j], list(cur))
            else:
                break
    kbest = max(best, key=lambda k: (round(best[k][0], 12), -k))
    sub = sorted(best[kbest][1])
    score, params, m = J(sub)
    return dict(subset=sub, score=score, params=params, metrics=m,
                path={k: (v[0], sorted(v[1])) for k, v in best.items()}, n_eval=len(cache))


def strat_folds(y, n_splits, seed):
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    return list(skf.split(np.zeros(len(y)), y))


# ---------------------------------------------------------------- DSSF pool (Tian et al. 2021, Section 2.3)
def zscore_within_date(feats, names, plots=None):
    """Stack the given features of all dates, z-scored within each date (used for the VIF)."""
    blocks = []
    for d in DATES:
        X = pd.concat([feats[d][f] for f in feats[d]], axis=1)[names]
        if plots is not None:
            X = X.loc[plots]
        blocks.append(((X - X.mean()) / X.std()).values)
    return np.vstack(blocks)


def build_pool(feats, y, plots=None, top_spec=0.05, top_scalar=0.10, vif_limit=10.0):
    """Disease-specific spectral feature (DSSF) pool from the plots given (all plots if None).
    Returns dict with the separability tables, consistency counts, regions, representatives,
    the pool before and after VIF and the VIF log."""
    out = dict(sep={}, consistency={}, level={}, regions={}, reps=[], scalar_top={}, scalar_union=[])
    alln = feats[DATES[0]]
    for f in list(alln):
        cols = None
        for d in DATES:
            X = feats[d][f] if plots is None else feats[d][f].loc[plots]
            yy = y[d] if plots is None else pd.Series(y[d], index=feats[d][f].index).loc[plots].values
            X = X.loc[:, X.std() > 0]
            cols = X.columns if cols is None else cols.intersection(X.columns)
            s = threshold_separability(X.values, yy); s.index = X.columns
            out["sep"][(d, f)] = s
        for d in DATES:
            out["sep"][(d, f)] = out["sep"][(d, f)].loc[cols]
    for f in SPECTRAL_FAMS:
        names = out["sep"][(DATES[0], f)].index
        cnt = pd.Series(0, index=names)
        for d in DATES:
            cnt += top_fraction(out["sep"][(d, f)].BA.values, top_spec).astype(int)
        out["consistency"][f] = cnt
        lev = next(k for k in (4, 3, 2, 1) if (cnt >= k).any())
        out["level"][f] = lev
        common = list(cnt[cnt >= lev].index)
        meanba = sum(out["sep"][(d, f)].BA for d in DATES) / len(DATES)
        if f == "CWT":
            wl_all = sorted({int(n.split("_")[1]) for n in names})
            regs = regions_cwt(common, wl_all)
        else:
            regs = [[f"{f}_{w}" for w in r] for r in regions_1d(common)]
        out["regions"][f] = regs
        for r in regs:
            rep = meanba.loc[r].idxmax()
            out["reps"].append(dict(family=f, feature=rep, region=f"{r[0]} … {r[-1]}" if len(r) > 1 else r[0],
                                    region_size=len(r), mean_BA=float(meanba.loc[rep]), dates_in_top=int(cnt.loc[rep])))
    for f in SCALAR_FAMS:
        tops = {}
        for d in DATES:
            s = out["sep"][(d, f)].BA.sort_values(ascending=False, kind="mergesort")
            k = int(np.ceil(top_scalar * len(s)))
            cut = s.iloc[k - 1]
            tops[d] = list(s[s >= cut].index)            # ties at the cut-off are kept
        out["scalar_top"][f] = tops
        union = []
        for d in DATES:
            union += [n for n in tops[d] if n not in union]
        meanba = sum(out["sep"][(d, f)].BA for d in DATES) / len(DATES)
        for n in union:
            out["reps"].append(dict(family=f, feature=n, region="-", region_size=1, mean_BA=float(meanba.loc[n]),
                                    dates_in_top=sum(n in tops[d] for d in DATES)))
    reps = pd.DataFrame(out["reps"])
    # exact or near-exact duplicates (|r| > 0.9999 in every date) are removed before the VIF
    names = list(reps.feature)
    Z = zscore_within_date(feats, names, plots)
    C = np.corrcoef(Z, rowvar=False)
    drop = set()
    order = np.argsort(-reps.mean_BA.values, kind="mergesort")
    for i in order:
        if names[i] in drop:
            continue
        for j in order:
            if j != i and names[j] not in drop and abs(C[i, j]) > 0.9999 and reps.mean_BA.values[j] <= reps.mean_BA.values[i]:
                drop.add(names[j])
    out["duplicates"] = sorted(drop)
    names = [n for n in names if n not in drop]
    Z = zscore_within_date(feats, names, plots)
    rel = reps.set_index("feature").mean_BA.loc[names].values
    kept, log = vif_reduce(Z, names, vif_limit, relevance=rel)
    out["pool_plain_vif"] = vif_reduce(Z, names, vif_limit)[0]
    out["pool_pre_vif"] = names
    out["vif_log"] = log
    out["pool"] = kept
    out["reps"] = reps
    return out


def date_matrix(feats, d, names, plots=None):
    X = pd.concat([feats[d][f] for f in feats[d]], axis=1)[names]
    return X if plots is None else X.loc[plots]
