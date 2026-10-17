"""Export the numbers the slide deck needs from results/r48.pkl to results/deck48.json."""
import json, pickle
from collections import Counter
import numpy as np
from refs48 import REFS

R = pickle.load(open("results/r48.pkl", "rb"))
V, full, wl, y, groups = R["V"], R["full"], R["wl"], R["y"], R["groups"]
t1 = R["tier1"]; cnt = R["counts"]
STR = R["STRATS"]

def summ(lst, key):
    v = [m[key] for m in lst if key in m]
    return [float(np.mean(v)), float(np.std(v, ddof=1)) if len(v) > 1 else 0.0]

out = dict(
    N=int(len(y)), nH=int((y == 0).sum()), nD=int((y == 1).sum()), P=int(len(wl)), wl_min=float(wl.min()), wl_max=float(wl.max()),
    em_min=int(cnt.n.min()), em_max=int(cnt.n.max()), em_H=[int(cnt[cnt["class"] == "healthy"].n.min()), int(cnt[cnt["class"] == "healthy"].n.max())],
    em_D=[int(cnt[cnt["class"] == "diseased"].n.min()), int(cnt[cnt["class"] == "diseased"].n.max())],
    removed=int(48 * 30 - len(y)), neg=R["neg_spectra"],
    neg_bands=int(((R["neg"].neg_healthy + R["neg"].neg_diseased) > 0).sum()),
    tier1=dict(sig=int((t1.p_ANOVA < 0.05).sum()), fdr=int((t1.FDR_q < 0.05).sum()), bonf=int((t1.Bonferroni_p < 0.05).sum()),
               welch=int((t1.Welch_p < 0.05).sum()), plotmean=int((t1.p_plot_means < 0.05).sum()),
               levene=int((t1.Levene_p < 0.05).sum()), dmax=float(t1.Cohen_d.abs().max()),
               wl_dmax=float(t1.wavelength_nm[t1.Cohen_d.abs().idxmax()]),
               n_d_large=int((t1.Cohen_d.abs() >= 0.8).sum()), n_d_medium=int((t1.Cohen_d.abs() >= 0.5).sum())),
    strats=STR, best=R["best"], fallbacks=int(R["fallbacks"]),
    jm_band_max=float(np.max(R["jm_band"])), wl_jm_max=float(wl[int(np.argmax(R["jm_band"]))]),
)
cfg = {}
for (t2, s), f in full.items():
    v = V[(t2, s)]
    v2, v3, v1 = v["v2"], v["v3"], v["v1"]
    stab = Counter(b for m in v2 for fb in m["bands"] for b in fb)
    nfold = sum(len(m["bands"]) for m in v2)
    v3tab = v3["plot"]["table"]
    cfg[f"{t2}-{s}"] = dict(
        t2=t2, s=s, name=STR[s], bands=[round(w, 1) for w in f["wl"]], k=len(f["bands"]), JM=float(f["JM"]),
        cum=[float(c) for c in f["cum"]], nodes=f.get("tree_nodes"),
        v1=dict(BA=summ(v1, "BA"), OA=summ(v1, "OA"), kappa=summ(v1, "kappa")),
        v2={k: summ(v2, k) for k in ("BA", "OA", "kappa", "MCC", "F1_H", "F1_D", "sens_D", "spec_H", "AUC")},
        v2plot={k: summ([m["plot"] for m in v2], k) for k in ("BA", "OA", "sens_D", "spec_H", "MCC")},
        v2_kfold=float(np.mean([len(fb) for m in v2 for fb in m["bands"]])),
        v2_stable=[[round(float(wl[b]), 1), round(c / nfold, 2)] for b, c in stab.most_common(8)],
        v3=dict(BA=float(v3["BA"]), OA=float(v3["OA"]), kappa=float(v3["kappa"]), MCC=float(v3["MCC"]), sens_D=float(v3["sens_D"]),
                spec_H=float(v3["spec_H"]), AUC=float(v3.get("AUC", np.nan)), plotBA=float(v3["plot"]["BA"]),
                correct=int((v3tab.pred == v3tab.t).sum()), wrongH=[int(g) for g in v3tab.index if v3tab.t[g] == 0 and v3tab.pred[g] != 0],
                wrongD=[int(g) for g in v3tab.index if v3tab.t[g] == 1 and v3tab.pred[g] != 1], cm=v3["cm"].tolist()),
    )
out["cfg"] = cfg
b = R["bench_rf_v2"]
out["bench"] = dict(BA=summ(b, "BA"), OA=summ(b, "OA"), kappa=summ(b, "kappa"), MCC=summ(b, "MCC"), AUC=summ(b, "AUC"),
                    sens_D=summ(b, "sens_D"), spec_H=summ(b, "spec_H"), plotBA=summ([m["plot"] for m in b], "BA"))
out["no_bands_perm"] = int(R.get("no_bands_perm", 0))
out["perm"] = {t2: dict(strategy=p["strategy"], observed=float(p["observed"]), p=float(p["p"]), null_mean=float(np.mean(p["null"])),
                        null_max=float(np.max(p["null"])), n=int(len(p["null"])), q95=float(np.quantile(p["null"], 0.95)))
               for t2, p in R["perm"].items()}
ck = R["checks"]
out["checks"] = dict(n=int(len(ck)), passed=int((ck.result == "PASS").sum()), rows=ck[["step", "check", "obtained", "result"]].values.tolist())
out["refs"] = [list(r) for r in REFS]
json.dump(out, open("results/deck48.json", "w"), indent=1)
print("written; configs", list(cfg))
for k, c in cfg.items():
    print(k, c["k"], f"JM {c['JM']:.3f} V1 {c['v1']['BA'][0]:.3f} V2 {c['v2']['BA'][0]:.3f} plot {c['v2plot']['BA'][0]:.3f} V3 {c['v3']['BA']:.3f} plots {c['v3']['correct']}/48", c["v2_stable"][:4])
print("bench", out["bench"]["BA"], out["bench"]["plotBA"]); print("perm", out["perm"])
