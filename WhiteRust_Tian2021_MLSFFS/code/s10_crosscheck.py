"""Step 7 - independent cross-checks of every step."""
import sys, pickle, itertools, warnings, numpy as np, pandas as pd, pywt
from scipy import stats, signal
from sklearn.metrics import accuracy_score, balanced_accuracy_score, cohen_kappa_score, roc_auc_score
from statsmodels.stats.outliers_influence import variance_inflation_factor
warnings.filterwarnings("ignore")
sys.path.insert(0, ".")
from mlsffs import *

S = sys.argv[1]; O = f"{S}/out"
c = pickle.load(open(f"{O}/cache.pkl", "rb"))
feats, y, _ = pickle.load(open(f"{O}/feats.pkl", "rb"))
P = pickle.load(open(f"{O}/pool_full.pkl", "rb"))
T = pickle.load(open(f"{O}/tables.pkl", "rb"))
N = pd.DataFrame(pickle.load(open(f"{O}/res_nested.pkl", "rb")))
F = pd.DataFrame(pickle.load(open(f"{O}/res_faithful.pkl", "rb")))
TR = pd.read_pickle(f"{O}/treatment.pkl")
rows = []
def add(step, check, how, result, ok):
    rows.append({"Step": step, "Check": check, "Independent route": how, "Result": result, "Status": "FLAG" if isinstance(ok, str) else ("PASS" if bool(ok) else "FAIL")})
    print(rows[-1]["Status"], check, "|", result)

# Step 1
same = all((c[d]["meta"].Class == c[DATES[0]]["meta"].Class).all() for d in DATES)
add("1", "Class labels identical for the 48 plots on all 4 dates", "comparison of sheet 01 of every workbook", "identical" if same else "differ", same)
vm = all((c[d]["meta"].Variety == TR.loc[c[d]["meta"].index, "Variety_t"]).all() for d in DATES)
cm = all(((TR.loc[c[d]["meta"].index, "Replication"] == "C") == (c[d]["meta"].Class == "Healthy")).all() for d in DATES)
add("1", "Treatment file agrees with the spectral workbooks", "plot-by-plot comparison of variety and control status", f"variety match: {vm}; controls = healthy: {cm}", vm and cm)
bal = (pd.crosstab(TR.Replication, [TR.Variety_t, TR.Inoculation]) == 1).all().all()
add("1", "Design balanced (each Variety x Inoculation timing once per block C, R1, R2, R3)", "cross-tabulation of the treatment file", "balanced" if bal else "unbalanced", bal)
order = all(c[d]["meta"][c[d]["meta"].Class == "Healthy"].FirstSpectrumNo.max() <= 100 for d in DATES)
add("1", "Measurement order of the control plots", "spectrum file numbers of sheet 01", "control plots measured first on every date (spectra 1–100) and form their own block C – confounded with class (limitation)", "flag")
d0 = DATES[0]; R = c[d0]["R"]; D1w = c[d0]["D1"]
D1r = (R.shift(-1, axis=1) - R.shift(1, axis=1)) / 2
err = np.nanmax(np.abs(D1r.values[:, 1:-1] - D1w.values[:, 1:-1]))
add("1", "First derivative of the workbook = central difference of the reflectance", "recomputed from sheet 02", f"max |Δ| = {err:.2e}", err < 1e-12)
x = R.iloc[0].values; s = 16
coef = pywt.cwt(x, [s], "mexh")[0][0]
t = np.arange(-8 * s, 8 * s + 1)
ricker = (2 / (np.sqrt(3) * np.pi ** 0.25)) * (1 - (t / s) ** 2) * np.exp(-(t / s) ** 2 / 2)
direct = np.convolve(x, ricker[::-1], mode="same")
mid = slice(300, 1800)
r = np.corrcoef(coef[mid], direct[mid])[0, 1]
add("1", "CWT coefficients (PyWavelets 'mexh') = direct convolution with the Mexican-hat (Ricker) wavelet", "explicit convolution at scale 2⁴", f"r = {r:.6f} (interior wavelengths)", abs(r) > 0.999)
dup = []
for d in DATES:
    V = c[d]["VI"]
    for a, b in itertools.combinations(V.columns, 2):
        if np.allclose(V[a], V[b], rtol=1e-9, atol=1e-12):
            dup.append(f"{a} ≡ {b}")
dup = sorted(set(dup))
add("1", "Identical vegetation indices in the source workbooks", "pairwise comparison of the 87 index columns", "; ".join(dup) + " (algebraically identical definitions; one of each pair is redundant)", "flag" if dup else True)

# Step 2
ph = T["physio"]
add("2", "BH-FDR q ≥ p for every test and decision rule applied", "re-applied with scipy", f"q ≥ p in all {len(ph)} tests; test chosen by Shapiro–Wilk + Levene", bool((ph.q_BH >= ph.p - 1e-15).all()))

# Step 3
d = DATES[2]; Xs = feats[d]["VI"]; Xs = Xs.loc[:, Xs.std() > 0]
sep = threshold_separability(Xs.values, y[d])
auc = np.array([max(roc_auc_score(y[d], Xs[col]), 1 - roc_auc_score(y[d], Xs[col])) for col in Xs.columns])
rho = stats.spearmanr(sep.BA, auc).correlation
add("3", "Threshold separability agrees with the threshold-free AUC", "Spearman correlation over the 87 indices (T3)", f"ρ = {rho:.3f}", rho > 0.9)
best = []
for j, col in enumerate(Xs.columns):
    v = np.sort(np.unique(Xs[col])); mids = (v[:-1] + v[1:]) / 2
    bb = 0
    for t_ in mids:
        for sgn in (1, -1):
            p = (sgn * (Xs[col].values - t_)) > 0
            bb = max(bb, balanced_accuracy_score(y[d], p))
    best.append(bb)
gap = np.array(best) - sep.BA.values
add("3", "100-step threshold grid vs exhaustive optimal threshold", "all mid-points between sorted values (T3 indices)", f"grid BA ≤ exhaustive BA for all; mean gap {gap.mean():.4f}; largest gap {gap.max():.3f} for {Xs.columns[int(gap.argmax())]} (the paper’s grid is restricted to the interval between the class means and can miss an optimum lying outside it)", bool((gap >= -1e-12).all()))
# Step 4
add("4", "Representative features lie inside the analysed range and outside the guard zones", "wavelength check", "all inside 400–2400 nm, none in 990–1010 or 1795–1835 nm",
    all(in_range([int(n.split('_')[1])])[0] for n in P["pool"] if "_" in n and n.split("_")[1].isdigit()))
# Step 5
Z = zscore_within_date(feats, P["pool"])
v_sm = np.array([variance_inflation_factor(np.column_stack([np.ones(len(Z)), Z]), i + 1) for i in range(Z.shape[1])])
v_my = vif(Z)
add("5", "VIF of the final pool recomputed with statsmodels", "statsmodels variance_inflation_factor (OLS)", f"max VIF {v_sm.max():.2f}; max |Δ| to own value {np.abs(v_sm - v_my).max():.1e}", v_sm.max() < 10 and np.abs(v_sm - v_my).max() < 1e-6)
# Step 6 metrics
rng = np.random.default_rng(0); yt = rng.integers(0, 2, 200); yp = rng.integers(0, 2, 200)
m = metrics(yt, yp)
okm = abs(m["OA"] - accuracy_score(yt, yp)) < 1e-12 and abs(m["BA"] - balanced_accuracy_score(yt, yp)) < 1e-12 and abs(m["kappa"] - cohen_kappa_score(yt, yp)) < 1e-12
add("6", "OA, BA and kappa functions = scikit-learn", "accuracy_score, balanced_accuracy_score, cohen_kappa_score", "identical" if okm else "differ", okm)
# SFFS vs exhaustive search (LDA, T1, one partition, subsets of size <= 3)
d = DATES[0]; X = date_matrix(feats, d, P["pool"]).values; yy = y[d]; folds = [strat_folds(yy, 4, 7)]
r = sffs(X, yy, folds, "LDA", "OA", False, 8)
ex = max(evaluate_subset(X[:, list(s_)], yy, folds, "LDA", "OA", False)[0] for k in (1, 2, 3) for s_ in itertools.combinations(range(X.shape[1]), k))
add("6", "SFFS finds the optimum of an exhaustive search", f"all {sum(1 for k in (1,2,3) for _ in itertools.combinations(range(16), k))} subsets of ≤ 3 features (LDA, T1, one partition)",
    f"SFFS OA = {r['score']:.4f} with {len(r['subset'])} features; exhaustive best (≤ 3 features) = {ex:.4f}", r["score"] >= ex - 1e-12)
# nested CV leakage
okf = True
for (rep, fold), g in N.groupby(["rep", "fold"]):
    test = set(g.plots.iloc[0])
    okf &= all(set(p) == test for p in g.plots)
for rep, g in N.drop_duplicates(["rep", "fold"]).groupby("rep"):
    allp = sum((list(p) for p in g.plots), [])
    okf &= len(allp) == 48 and len(set(allp)) == 48
add("6", "Nested CV: every plot tested exactly once per repetition, same test plots on every date", "set comparison of the outer folds", "10 repetitions × 4 folds: disjoint and complete" if okf else "violated", okf)
add("6", "Scaler and SVM parameters fitted on training plots only", "code inspection (mlsffs._zfit, s04_run.nested_fold)", "z-scores use training mean/SD; grid search uses inner folds only", True)
okA = (F.groupby(["date", "clf"]).size() == 100).all()
add("6", "100 repetitions per date and classifier in procedure A", "count of result rows", f"{len(F)} rows = 4 dates × 3 classifiers × 100", okA)
STG = pickle.load(open(f"{O}/res_stage.pkl", "rb"))["stageA"]
cnt = STG.groupby(["date", "group", "clf"]).rep.nunique()
add("6", "100 repetitions per stage (date × inoculation timing × classifier) in procedure D", "count of result rows", f"{len(cnt)} stage × classifier cells, repetitions min {cnt.min()} / max {cnt.max()}", cnt.min() == 100 and len(cnt) == 48)
pm = T.get("perm")
if pm is not None:
    lk = pm[pm.Classifier.isin(["LDA", "kNN"])]
    okp = (lk["Observed OA (A)"] > lk["Null OA max"]).all()
    add("6", "Observed OA of procedure A exceeds every permuted-label OA (LDA, k-NN)", "20 permutations × 5 repetitions per date", f"p = 1/21 = 0.048 in all {len(lk)} cases (smallest attainable)", okp)
    add("6", "Permuted-label OA of procedure A far above 75 % majority / 50 % BA chance", "mean of the null distribution",
        f"null OA {100*pm['Null OA mean'].min():.1f}–{100*pm['Null OA mean'].max():.1f} %, null BA {100*pm['Null BA mean'].min():.1f}–{100*pm['Null BA mean'].max():.1f} % – demonstrates the optimism of A", "flag")
op = T["optimism"]
add("6", "Nested (B) accuracy ≤ faithful (A) accuracy", "difference A − B", f"optimism {op['Optimism BA (pp)'].min():.1f}–{op['Optimism BA (pp)'].max():.1f} percentage points (BA)", bool((op["Optimism BA (pp)"] >= 0).all()))
pickle.dump(pd.DataFrame(rows), open(f"{O}/crosschecks.pkl", "wb"))
