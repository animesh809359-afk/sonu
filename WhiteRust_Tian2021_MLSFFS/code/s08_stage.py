"""Step 6D - detection by infection stage using the treatment design (analogue of Tian et al. 2021, Table 3 by DAI).
Infection stage = measurement date (T1-T4) x inoculation timing (D1-D4, days after sowing).
A-stage: paper-faithful ML-SFFS, 12 control plots vs the 9 plots of one inoculation timing (3 varieties x 3 reps),
         fixed DSSF pool, stratified 4-fold CV x NREP repetitions, OA criterion.
B-stage: unbiased detection rates of every inoculation group / variety from the nested-CV predictions (Step 6B)."""
import sys, pickle, warnings, numpy as np, pandas as pd
from joblib import Parallel, delayed
warnings.filterwarnings("ignore")
sys.path.insert(0, ".")
from mlsffs import *

S = sys.argv[1]; NREP = int(sys.argv[2])
O = f"{S}/out"
feats, y, _ = pickle.load(open(f"{O}/feats.pkl", "rb"))
P = pickle.load(open(f"{O}/pool_full.pkl", "rb"))
TR = pd.read_pickle(f"{O}/treatment.pkl")
N = pd.DataFrame(pickle.load(open(f"{O}/res_nested.pkl", "rb")))
pool = P["pool"]
plots = np.array(feats[DATES[0]]["R"].index)
ctrl = plots[TR.loc[plots].Replication.values == "C"]


def run(d, g, clf, rep):
    inoc = plots[(TR.loc[plots].Replication.values != "C") & (TR.loc[plots].Inoculation.values == g)]
    sub = list(ctrl) + list(inoc)
    X = date_matrix(feats, d, pool, sub).values
    yy = np.array([0] * len(ctrl) + [1] * len(inoc))
    folds = [strat_folds(yy, 4, rep)]
    r = sffs(X, yy, folds, clf, "OA", False, 8)
    return dict(date=d, group=g, clf=clf, rep=rep, ofc=tuple(pool[i] for i in r["subset"]), k=len(r["subset"]), **r["metrics"])


tasks = [(d, g, c, r) for d in DATES for g in ["D1", "D2", "D3", "D4"] for c in ["SVM", "LDA", "kNN"] for r in range(NREP)]
res = pd.DataFrame(Parallel(n_jobs=4)(delayed(run)(*t) for t in tasks))

# unbiased detection rates from the nested predictions
rows = []
for _, r in N.iterrows():
    for p, yt, yp in zip(r.plots, r.y, r.pred):
        rows.append(dict(rep=r.rep, date=r.date, clf=r.clf, plot=p, y=yt, pred=yp,
                         group=TR.loc[p, "Inoculation"] if TR.loc[p, "Replication"] != "C" else "Control",
                         variety=TR.loc[p, "Variety_t"]))
PR = pd.DataFrame(rows)
pickle.dump(dict(stageA=res, nested_pred=PR), open(f"{O}/res_stage.pkl", "wb"))
pd.set_option("display.width", 220)
print(res.groupby(["date", "group", "clf"])[["OA", "BA", "k"]].mean().unstack("clf").round(3).to_string())
det = PR.groupby(["date", "clf", "group"]).apply(lambda g: (g.pred == 1).mean()).unstack("group")
print(det.round(3).to_string())
