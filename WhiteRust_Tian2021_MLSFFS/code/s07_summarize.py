"""Collect every result table used by the Excel workbook, the Word report and the slides."""
import sys, os, pickle, collections, numpy as np, pandas as pd
sys.path.insert(0, ".")
from mlsffs import *

S = sys.argv[1]
O = f"{S}/out"
c = pickle.load(open(f"{O}/cache.pkl", "rb"))
feats, y, _ = pickle.load(open(f"{O}/feats.pkl", "rb"))
P = pickle.load(open(f"{O}/pool_full.pkl", "rb"))
PH = pickle.load(open(f"{O}/physio.pkl", "rb"))
F = pd.DataFrame(pickle.load(open(f"{O}/res_faithful.pkl", "rb")))
N = pd.DataFrame(pickle.load(open(f"{O}/res_nested.pkl", "rb")))
perm = []
for fn in ["res_perm_ldaknn.pkl", "res_perm_svm.pkl"]:
    if os.path.exists(f"{O}/{fn}"):
        perm += pickle.load(open(f"{O}/{fn}", "rb"))
PM = pd.DataFrame(perm)
CLFS = ["LDA", "kNN", "SVM"]
T = {}

# ---------------- feature codes (Table 2 analogue)
pool = P["pool"]
CODE = {n: f"F{i + 1}" for i, n in enumerate(pool)}
reps = P["reps"].set_index("feature")
MEANING = {
    "R_641": "Red reflectance at 641 nm, shoulder of the chlorophyll a/b red absorption; rises when chlorophyll is lost",
    "D1_852": "Slope of the NIR plateau at 852 nm; governed by mesophyll (intercellular) scattering - cf. WF850 of Tian et al. (2021)",
    "D2_1350": "Curvature at the onset of the 1400-nm water absorption band (leaf water)",
    "S3_1736": "Wavelet feature (scale 3) at 1736 nm; C-H absorption of lignin/cellulose/protein near 1730 nm (Kokaly and Clark, 1999)",
    "S3_1752": "Wavelet feature (scale 3) at 1752 nm; C-H / cellulose-lignin absorption region (cf. NDLI band 1754 nm)",
    "S3_1932": "Wavelet feature (scale 3) at 1932 nm; centre of the 1940-nm leaf-water absorption",
    "S3_2318": "Wavelet feature (scale 3) at 2318 nm; protein/cellulose absorption near 2.30 um (Kokaly and Clark, 1999)",
    "S4_634": "Wavelet feature (scale 4) at 634 nm; local shape of the yellow-red (chlorophyll) absorption edge - cf. WF608 of Tian et al. (2021)",
    "S5_1875": "Wavelet feature (scale 5) at 1875 nm; short-wave shoulder of the 1940-nm water band",
    "ARI2": "Modified anthocyanin reflectance index R800(1/R550 - 1/R700); anthocyanin accumulation (Gitelson et al., 2001)",
    "Lic": "Blue/red reflectance ratio R440/R690 (after the F440/F690 stress ratio of Lichtenthaler et al., 1996)",
    "CR6 water absorption 1721–2304 nm: left area (nm)": "Continuum-removed area of the 1940-nm water band, short-wave side",
    "CR3 water absorption 914–1069 nm: depth / area (1/nm)": "Band-depth / area of the 970-nm water band (shape of the weak water absorption)",
    "CR6 water absorption 1721–2304 nm: right area (nm)": "Continuum-removed area of the 1940-nm water band, long-wave side",
    "CR1 blue absorption 400–548 nm: right area (nm)": "Continuum-removed area of the blue (carotenoid + chlorophyll) absorption, long-wave side",
    "Blue-edge position λb (nm)": "Wavelength of the maximum first derivative in 490-530 nm (Gong et al., 2002)",
}
rows = []
for n in pool:
    r = reps.loc[n]
    d = dict(Code=CODE[n], Feature=n, Family=FAM_NAME[r.family], Region=r.region, Region_size=int(r.region_size),
             Dates_in_top=int(r.dates_in_top), Mean_BA=r.mean_BA, VIF=P["vif_log"][-1]["vif"][n], Meaning=MEANING.get(n, ""))
    for dd in DATES:
        d[f"BA {DLAB[dd]}"] = P["sep"][(dd, r.family)].BA.loc[n]
    rows.append(d)
T["dssf_final"] = pd.DataFrame(rows)

# ---------------- QC
qc = []
for d in DATES:
    m = c[d]["meta"]
    qc.append({"Date": DLAB[d], "Plots healthy": int((m.Class == "Healthy").sum()), "Plots diseased": int((m.Class == "Diseased").sum()),
               "Leaf spectra": int(m.Nleaf.sum()), "Leaves/plot healthy (mean)": m[m.Class == "Healthy"].Nleaf.mean(),
               "Leaves/plot diseased (mean)": m[m.Class == "Diseased"].Nleaf.mean(),
               "Growth stages": "; ".join(f"{k}: {v}" for k, v in m.Stage.value_counts().items()),
               "Stage x class (H)": "; ".join(f"{k}: {v}" for k, v in m[m.Class == "Healthy"].Stage.value_counts().items()),
               "Stage x class (D)": "; ".join(f"{k}: {v}" for k, v in m[m.Class == "Diseased"].Stage.value_counts().items()),
               "Spectrum no. range healthy": f"{int(m[m.Class == 'Healthy'].FirstSpectrumNo.min())}–{int(m[m.Class == 'Healthy'].FirstSpectrumNo.max())}",
               "Labels identical to 11-02": bool((m.Class == c[DATES[0]]["meta"].Class).all()),
               "Varieties identical to 11-02": bool((m.Variety == c[DATES[0]]["meta"].Variety).all())})
T["qc"] = pd.DataFrame(qc)
fam_counts = []
for d in DATES:
    row = {"Date": DLAB[d]}
    for f in feats[d]:
        row[FAM_NAME[f]] = feats[d][f].shape[1]
    fam_counts.append(row)
T["feature_counts"] = pd.DataFrame(fam_counts)

# ---------------- separability of scalar features (all, per date)
sc = []
for f in SCALAR_FAMS:
    for n in P["sep"][(DATES[0], f)].index:
        row = {"Family": FAM_NAME[f], "Feature": n}
        for d in DATES:
            s = P["sep"][(d, f)].loc[n]
            row[f"Mh {DLAB[d]}"] = s.Mh; row[f"Mi {DLAB[d]}"] = s.Mi; row[f"Threshold {DLAB[d]}"] = s.threshold
            row[f"OA {DLAB[d]}"] = s.OA; row[f"BA {DLAB[d]}"] = s.BA
            row[f"Top10% {DLAB[d]}"] = n in P["scalar_top"][f][d]
        row["Mean BA"] = np.mean([row[f"BA {DLAB[d]}"] for d in DATES])
        row["In DSSF union"] = any(row[f"Top10% {DLAB[d]}"] for d in DATES)
        row["In final pool"] = n in pool
        sc.append(row)
T["sep_scalar"] = pd.DataFrame(sc).sort_values(["Family", "Mean BA"], ascending=[True, False])

# ---------------- separability of spectral features (bands / derivatives) wide table
spec = {}
for f in ["R", "D1", "D2", "D3"]:
    idx = P["sep"][(DATES[0], f)].index
    df = pd.DataFrame({"Wavelength (nm)": [int(i.split("_")[1]) for i in idx]})
    for d in DATES:
        df[f"BA {DLAB[d]}"] = P["sep"][(d, f)].BA.values
        df[f"Top5% {DLAB[d]}"] = top_fraction(P["sep"][(d, f)].BA.values, 0.05)
    df["Dates in top 5%"] = P["consistency"][f].values
    df["Common (k* dates)"] = df["Dates in top 5%"] >= P["level"][f]
    spec[f] = df
T["sep_spectral"] = spec
cw = P["sep"][(DATES[0], "CWT")].index
cwt = pd.DataFrame({"Scale": [int(i.split("_")[0][1:]) for i in cw], "Wavelength (nm)": [int(i.split("_")[1]) for i in cw]})
for d in DATES:
    cwt[f"BA {DLAB[d]}"] = P["sep"][(d, "CWT")].BA.values
cwt["Dates in top 5%"] = P["consistency"]["CWT"].values
T["sep_cwt"] = cwt
summ = []
for f in SPECTRAL_FAMS:
    row = {"Family": FAM_NAME[f], "Candidates": len(P["consistency"][f])}
    for d in DATES:
        ba = P["sep"][(d, f)].BA.values
        row[f"Top-5% cut-off BA {DLAB[d]}"] = float(np.quantile(ba, 0.95))
        row[f"N top 5% {DLAB[d]}"] = int(top_fraction(ba, 0.05).sum())
        row[f"Max BA {DLAB[d]}"] = float(ba.max())
    cnt = P["consistency"][f]
    for k in (4, 3, 2):
        row[f"Common to ≥{k} dates"] = int((cnt >= k).sum())
    row["Consistency level k* used"] = P["level"][f]
    row["Regions"] = len(P["regions"][f])
    summ.append(row)
for f in SCALAR_FAMS:
    row = {"Family": FAM_NAME[f], "Candidates": len(P["sep"][(DATES[0], f)])}
    for d in DATES:
        ba = P["sep"][(d, f)].BA
        row[f"N top 10% {DLAB[d]}"] = len(P["scalar_top"][f][d]); row[f"Max BA {DLAB[d]}"] = float(ba.max())
    row["Union over dates"] = int((P["reps"].family == f).sum())
    summ.append(row)
T["selection_summary"] = pd.DataFrame(summ)
T["dssf_candidates"] = P["reps"].assign(Family=lambda d: d.family.map(FAM_NAME), Duplicate_removed=lambda d: d.feature.isin(P["duplicates"]),
                                        In_final_pool=lambda d: d.feature.isin(pool), In_plain_VIF_pool=lambda d: d.feature.isin(P["pool_plain_vif"]))

# ---------------- VIF log
vl = []
for st in P["vif_log"]:
    vl.append({"Iteration": st["step"], "Features in model": len(st["vif"]), "Max VIF": max(st["vif"].values()),
               "Removed feature": st.get("removed") or "— (all VIF < 10, stop)", "VIF of removed": st.get("removed_vif", np.nan),
               "Mean BA of removed": reps.mean_BA.get(st.get("removed"), np.nan) if st.get("removed") else np.nan})
T["vif_log"] = pd.DataFrame(vl)

# ---------------- A: faithful ML-SFFS (Table 3 analogue)
def codes(t):
    return ", ".join(sorted((CODE.get(n, n) for n in t), key=lambda s: int(s[1:]) if s[1:].isdigit() else 99))
F["OFC codes"] = F.ofc.apply(codes)
fa = []
for d in DATES:
    for clf in CLFS:
        g = F[(F.date == d) & (F.clf == clf)]
        vc = g["OFC codes"].value_counts()
        fa.append({"Date": DLAB[d], "Classifier": clf, "Most frequent OFC": vc.index[0], "OFC frequency (%)": 100 * vc.iloc[0] / len(g),
                   "Distinct OFCs": len(vc), "Mean no. of features": g.k.mean(),
                   "Mean OA": g.OA.mean(), "SD OA": g.OA.std(), "Mean BA": g.BA.mean(), "Mean kappa": g.kappa.mean(),
                   "Mean sensitivity": g.sens.mean(), "Mean specificity": g.spec.mean(),
                   f"{clf}-all OA": g.all_OA.mean(), f"{clf}-all BA": g.all_BA.mean(), "Repetitions": len(g)})
T["faithful"] = pd.DataFrame(fa)
best = T["faithful"].loc[T["faithful"].groupby("Date", sort=False)["Mean OA"].idxmax(), ["Date", "Classifier"]]
T["faithful_best"] = best
freq = []
for d in DATES:
    for clf in CLFS:
        g = F[(F.date == d) & (F.clf == clf)]
        row = {"Date": DLAB[d], "Classifier": clf}
        for n in pool:
            row[CODE[n]] = 100 * g.ofc.apply(lambda t: n in t).mean()
        freq.append(row)
T["faithful_freq"] = pd.DataFrame(freq)
top_ofc = []
for d in DATES:
    for clf in CLFS:
        g = F[(F.date == d) & (F.clf == clf)]
        vc = g.groupby("OFC codes").agg(n=("OA", "size"), OA=("OA", "mean"), BA=("BA", "mean")).sort_values("n", ascending=False).head(5)
        for k, r in vc.iterrows():
            top_ofc.append({"Date": DLAB[d], "Classifier": clf, "OFC": k, "Times selected (of 100)": int(r.n), "Mean OA when selected": r.OA, "Mean BA when selected": r.BA})
T["faithful_top_ofc"] = pd.DataFrame(top_ofc)
svmall = []
for d in DATES:
    for clf in CLFS:
        g = F[(F.date == d) & (F.clf == clf)]
        svmall.append({"Date": DLAB[d], "Classifier": clf, "SFFS OA": g.OA.mean(), "All-DSSF OA": g.all_OA.mean(), "Gain OA (pp)": 100 * (g.OA.mean() - g.all_OA.mean()),
                       "SFFS BA": g.BA.mean(), "All-DSSF BA": g.all_BA.mean(), "Gain BA (pp)": 100 * (g.BA.mean() - g.all_BA.mean())})
T["sffs_vs_all"] = pd.DataFrame(svmall)

# ---------------- B: nested CV
ne = []
nested_rep = []
for d in DATES:
    for clf in CLFS:
        g = N[(N.date == d) & (N.clf == clf)]
        per = []
        for r_, gg in g.groupby("rep"):
            yy = sum(gg.y, []); pp = sum(gg.pred, []); pa = sum(gg.pred_all, [])
            m = metrics(yy, pp); ma = metrics(yy, pa)
            per.append({**m, **{f"all_{k}": v for k, v in ma.items()}})
            nested_rep.append({"Date": DLAB[d], "Classifier": clf, "Repetition": r_ + 1, **m, "All-DSSF BA": ma["BA"]})
        per = pd.DataFrame(per)
        ne.append({"Date": DLAB[d], "Classifier": clf, "OA": per.OA.mean(), "SD OA": per.OA.std(), "BA": per.BA.mean(), "SD BA": per.BA.std(),
                   "kappa": per.kappa.mean(), "Sensitivity": per.sens.mean(), "Specificity": per.spec.mean(),
                   "All-DSSF OA": per.all_OA.mean(), "All-DSSF BA": per.all_BA.mean(),
                   "Mean no. of features": g.ofc.apply(len).mean(), "Inner-CV BA (optimistic)": g.inner_BA.mean(),
                   "Majority-class OA": 0.75, "Chance BA": 0.5})
T["nested"] = pd.DataFrame(ne)
T["nested_reps"] = pd.DataFrame(nested_rep)
# stability: share of outer folds whose pool / OFC contains each feature
pools = N.drop_duplicates(["rep", "fold"]).pool
cnt = collections.Counter(n for p in pools for n in p)
VI_N, CR_N = set(feats[DATES[0]]["VI"].columns), set(feats[DATES[0]]["CR"].columns)
def family_of(n):
    import re
    if re.match(r"^S\d_\d+$", n): return FAM_NAME["CWT"]
    for f in ["R", "D1", "D2", "D3"]:
        if re.match(rf"^{f}_\d+$", n): return FAM_NAME[f]
    return FAM_NAME["VI"] if n in VI_N else FAM_NAME["CR"] if n in CR_N else FAM_NAME["RE"]
stab = pd.DataFrame([{"Feature": n, "Code (full-data pool)": CODE.get(n, "—"), "Family": family_of(n),
                      "In pool of outer folds (%)": 100 * k / len(pools)} for n, k in cnt.most_common()])
sel = collections.Counter(n for o in N.ofc for n in o)
stab["Selected by SFFS (% of fold x date x classifier fits)"] = stab.Feature.map(lambda n: 100 * sel.get(n, 0) / len(N))
T["nested_stability"] = stab
T["nested_pool_size"] = pools.apply(len).describe().to_frame("Pool size across outer folds")

# ---------------- C: permutation null
if len(PM):
    pn = []
    for d in DATES:
        for clf in CLFS:
            g = PM[(PM.date == d) & (PM.clf == clf)]
            if not len(g):
                continue
            null = g.groupby("perm").OA.mean()
            nullba = g.groupby("perm").BA.mean()
            obs = F[(F.date == d) & (F.clf == clf)].OA.mean()
            obsba = F[(F.date == d) & (F.clf == clf)].BA.mean()
            pn.append({"Date": DLAB[d], "Classifier": clf, "Permutations": len(null), "Reps per permutation": int(g.groupby("perm").size().iloc[0]),
                       "Null OA mean": null.mean(), "Null OA max": null.max(), "Null BA mean": nullba.mean(), "Null BA max": nullba.max(),
                       "Observed OA (A)": obs, "Observed BA (A)": obsba, "p (OA)": (1 + (null >= obs).sum()) / (1 + len(null)),
                       "Null pool size (mean)": g.pool_size.mean()})
    T["perm"] = pd.DataFrame(pn)
    T["perm_raw"] = PM
# ---------------- optimism A - B
op = T["faithful"][["Date", "Classifier", "Mean OA", "Mean BA"]].merge(T["nested"][["Date", "Classifier", "OA", "BA"]], on=["Date", "Classifier"])
op["Optimism OA (pp)"] = 100 * (op["Mean OA"] - op["OA"]); op["Optimism BA (pp)"] = 100 * (op["Mean BA"] - op["BA"])
op = op.rename(columns={"Mean OA": "A: faithful OA", "Mean BA": "A: faithful BA", "OA": "B: nested OA", "BA": "B: nested BA"})
T["optimism"] = op
T["physio"] = PH["proxy"]; T["scalar_tests"] = PH["scalar_tests"]
# ---------------- treatment design and stage-wise analysis (Step 6D)
TR = pd.read_pickle(f"{O}/treatment.pkl")
T["treatment"] = TR.reset_index().rename(columns={"Inoculation": "Inoculation timing (DAS group)", "Variety_t": "Variety", "Replication": "Replication / block"})
T["design"] = pd.crosstab(TR["Replication"], [TR["Variety_t"], TR["Inoculation"]])
st = []
for d in DATES:
    m = c[d]["meta"].join(TR)
    for g, gg in m.groupby("Inoculation"):
        st.append({"Date": DLAB[d], "Inoculation timing": g, **{f"{k}": v for k, v in gg.Stage.value_counts().items()}})
T["stage_by_inoc"] = pd.DataFrame(st).fillna(0)
if os.path.exists(f"{O}/res_stage.pkl"):
    SR = pickle.load(open(f"{O}/res_stage.pkl", "rb"))
    A = SR["stageA"]; PR = SR["nested_pred"]
    A["OFC codes"] = A.ofc.apply(codes)
    sa = []
    for (d, g, clf), gg in A.groupby(["date", "group", "clf"]):
        vc = gg["OFC codes"].value_counts()
        sa.append({"Date": DLAB[d], "Inoculation timing": g, "Classifier": clf, "Mean OA": gg.OA.mean(), "SD OA": gg.OA.std(),
                   "Mean BA": gg.BA.mean(), "Mean kappa": gg.kappa.mean(), "Mean no. of features": gg.k.mean(),
                   "Most frequent OFC": vc.index[0], "OFC frequency (%)": 100 * vc.iloc[0] / len(gg), "Repetitions": len(gg)})
    sa = pd.DataFrame(sa)
    sa["Date"] = pd.Categorical(sa["Date"], [DLAB[d] for d in DATES], ordered=True)
    T["stageA"] = sa.sort_values(["Date", "Inoculation timing", "Classifier"]).reset_index(drop=True)
    det = []
    for (d, clf, g), gg in PR.groupby(["date", "clf", "group"]):
        det.append({"Date": DLAB[d], "Classifier": clf, "Group": g, "Plots": gg["plot"].nunique(),
                    "Called diseased (%)": 100 * (gg.pred == 1).mean(),
                    "Correct (%)": 100 * (gg.pred == gg.y).mean()})
    det = pd.DataFrame(det); det["Date"] = pd.Categorical(det["Date"], [DLAB[d] for d in DATES], ordered=True)
    T["stage_detection"] = det.sort_values(["Date", "Classifier", "Group"]).reset_index(drop=True)
    dv = []
    for (d, clf, v, cl), gg in PR.assign(cls=np.where(PR.y == 1, "Inoculated", "Control")).groupby(["date", "clf", "variety", "cls"]):
        dv.append({"Date": DLAB[d], "Classifier": clf, "Variety": v, "Class": cl, "Correct (%)": 100 * (gg.pred == gg.y).mean()})
    dv = pd.DataFrame(dv); dv["Date"] = pd.Categorical(dv["Date"], [DLAB[d] for d in DATES], ordered=True)
    T["variety_detection"] = dv.sort_values(["Date", "Classifier", "Variety", "Class"]).reset_index(drop=True)
T["code"] = CODE; T["pool"] = pool
pickle.dump(T, open(f"{O}/tables.pkl", "wb"))
pd.set_option("display.width", 250)
print(T["faithful"][["Date", "Classifier", "Most frequent OFC", "OFC frequency (%)", "Mean no. of features", "Mean OA", "SD OA", "Mean BA"]].round(3).to_string())
print(T["sffs_vs_all"].round(3).to_string())
print(T["nested"][["Date", "Classifier", "OA", "BA", "kappa", "Sensitivity", "Specificity", "All-DSSF BA", "Mean no. of features"]].round(3).to_string())
print(T["optimism"].round(3).to_string())
if "perm" in T: print(T["perm"].round(3).to_string())
print(T["nested_stability"].head(12).round(1).to_string())
if "stageA" in T:
    print(T["stageA"].pivot_table(index=["Date", "Inoculation timing"], columns="Classifier", values="Mean OA", observed=True).round(3).to_string())
    print(T["stage_detection"].pivot_table(index=["Date", "Classifier"], columns="Group", values="Called diseased (%)", observed=True).round(1).to_string())
    print(T["variety_detection"].pivot_table(index=["Date", "Classifier"], columns=["Variety", "Class"], values="Correct (%)", observed=True).round(1).to_string())
