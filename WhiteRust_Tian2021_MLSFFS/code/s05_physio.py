"""Step 2 - physiological interpretation (analogue of Tian et al. 2021 Section 3.1 / Fig. 4).
No leaf biochemistry was measured, so published index proxies of the same four constituents are tested.
Procedure of Tian et al. (2021): outliers outside median +/- 3 MAD removed (Leys et al., 2013);
independent t-test when both groups are normal (Shapiro-Wilk) with equal variances (Levene),
otherwise Mann-Whitney U. Correction: Benjamini-Hochberg FDR over all tests."""
import sys, pickle, numpy as np, pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests
sys.path.insert(0, '.')
from mlsffs import DATES, DLAB
c = pickle.load(open(sys.argv[1], 'rb'))
PROXY = [("CIrededge", "VI", "Chlorophyll", "Gitelson et al., 2003"),
         ("MTCI", "VI", "Chlorophyll", "Dash and Curran, 2004"),
         ("CRI1", "VI", "Carotenoids", "Gitelson et al., 2002b"),
         ("ARI", "VI", "Anthocyanins", "Gitelson et al., 2001"),
         ("PRI", "VI", "Xanthophyll / photosynthetic efficiency", "Gamon et al., 1992"),
         ("WI", "VI", "Water", "Peñuelas et al., 1997"),
         ("NDWI", "VI", "Water", "Gao, 1996"),
         ("REIP, linear four-point interpolation (nm)", "RE", "Chlorophyll (red-edge position)", "Guyot and Baret, 1988")]

def mad_keep(v, k=3.0):
    med = np.median(v); mad = 1.4826 * np.median(np.abs(v - med))
    return np.abs(v - med) <= k * mad if mad > 0 else np.ones_like(v, bool)

def test(h, d):
    h0, d0 = h[mad_keep(h)], d[mad_keep(d)]
    norm = stats.shapiro(h0).pvalue > 0.05 and stats.shapiro(d0).pvalue > 0.05
    eqv = stats.levene(h0, d0).pvalue > 0.05
    if norm and eqv:
        t = stats.ttest_ind(d0, h0, equal_var=True); name, st, p = "Student t", t.statistic, t.pvalue
    else:
        u = stats.mannwhitneyu(d0, h0, alternative="two-sided"); name, st, p = "Mann-Whitney U", u.statistic, u.pvalue
    sp = np.sqrt(((len(h0) - 1) * h0.var(ddof=1) + (len(d0) - 1) * d0.var(ddof=1)) / (len(h0) + len(d0) - 2))
    g = (d0.mean() - h0.mean()) / sp * (1 - 3 / (4 * (len(h0) + len(d0)) - 9))
    return dict(n_H=len(h0), n_D=len(d0), outliers_removed=len(h) + len(d) - len(h0) - len(d0),
                normal=norm, equal_var=eqv, test=name, statistic=st, p=p, hedges_g=g,
                mean_H=h0.mean(), sd_H=h0.std(ddof=1), mean_D=d0.mean(), sd_D=d0.std(ddof=1),
                median_H=np.median(h0), median_D=np.median(d0))

rows, raw = [], []
for d in DATES:
    m = c[d]["meta"]; h = (m.Class == "Healthy").values
    for name, fam, const, ref in PROXY:
        v = c[d][fam][name].values
        r = test(v[h], v[~h]); r.update(date=d, date_label=DLAB[d], proxy=name, constituent=const, reference=ref)
        rows.append(r)
        for pid, val, cl in zip(m.index, v, m.Class):
            raw.append(dict(date=d, proxy=name, plot=pid, Class=cl, value=val))
T = pd.DataFrame(rows)
T["q_BH"] = multipletests(T.p, method="fdr_bh")[1]
T["significant (q<0.05)"] = T.q_BH < 0.05
T["direction"] = np.where(T.mean_D < T.mean_H, "lower in diseased", "higher in diseased")
print(T[["date", "proxy", "test", "p", "q_BH", "hedges_g", "direction", "outliers_removed"]].round(4).to_string())

# supplementary: every scalar feature, Mann-Whitney U + BH within family and date
sup = []
for d in DATES:
    m = c[d]["meta"]; h = (m.Class == "Healthy").values
    for fam in ["VI", "CR", "RE"]:
        X = c[d][fam]; part = []
        for col in X.columns:
            v = X[col].values
            if np.nanstd(v) == 0: continue
            u = stats.mannwhitneyu(v[~h], v[h], alternative="two-sided")
            auc = u.statistic / (h.sum() * (~h).sum())
            part.append(dict(date=d, family=fam, feature=col, mean_H=v[h].mean(), mean_D=v[~h].mean(),
                             U=u.statistic, p=u.pvalue, AUC=max(auc, 1 - auc)))
        part = pd.DataFrame(part); part["q_BH"] = multipletests(part.p, method="fdr_bh")[1]
        sup.append(part)
SUP = pd.concat(sup, ignore_index=True)
print(SUP.groupby(["date", "family"]).apply(lambda g: f"{(g.q_BH < 0.05).sum()}/{len(g)}"))
pickle.dump(dict(proxy=T, proxy_raw=pd.DataFrame(raw), scalar_tests=SUP), open(sys.argv[2], "wb"))
