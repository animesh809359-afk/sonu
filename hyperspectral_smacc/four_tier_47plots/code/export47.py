"""Export the numbers the slide deck needs (results/r47.pkl -> results/deck47.json)."""
import json, os, pickle
from collections import Counter
import numpy as np, pandas as pd
from refs47 import REFS
from abbrev47 import ABBR

R = pickle.load(open(os.environ.get("R47", "results/r47.pkl"), "rb"))
V, full, wl, y, groups, td = R["V"], R["full"], R["wl"], R["y"], R["groups"], R["design"]
t1 = R["tier1"]; ns = R["neg_spectra"]
def fl(v): return None if v is None or (isinstance(v, float) and np.isnan(v)) else float(v)
def accd(m):
    o = {k: fl(m[k]) for k in ("OA", "BA", "kappa", "PA_H", "UA_H", "PA_D", "UA_D", "F1_H", "F1_D", "MCC", "QD", "AD")}
    o["cm"] = np.asarray(m["cm"]).astype(int).tolist(); o["n"] = int(np.asarray(m["cm"]).sum())
    if "ci" in m: o["ci"] = {k: [float(m["ci"][k][0]), float(m["ci"][k][1])] for k in ("OA", "BA", "kappa", "PA_H", "PA_D", "UA_H", "UA_D")}
    return o
def ms(v): return [float(np.mean(v)), float(np.std(v, ddof=1)) if len(v) > 1 else 0.0]
out = dict(N=int(len(y)), nH=int((y == 0).sum()), nD=int((y == 1).sum()), P=int(len(wl)), wl_min=float(wl.min()), wl_max=float(wl.max()),
           PH=R["PH"], PD=R["PD"], neg=ns, neg_bands=int(((R["neg"].neg_healthy + R["neg"].neg_diseased) > 0).sum()),
           gt1_bands=int(((R["neg"].gt1_healthy + R["neg"].gt1_diseased) > 0).sum()),
           tier1=dict(sig=int((t1.p_ANOVA < 0.05).sum()), fdr=int((t1.FDR_q < 0.05).sum()), bonf=int((t1.Bonferroni_p < 0.05).sum()),
                      welch=int((t1.Welch_p < 0.05).sum()), levene=int((t1.Levene_p < 0.05).sum()), plotmean=int((t1.p_plot_means < 0.05).sum()),
                      dmax=float(t1.Cohen_d.abs().max()), wl_dmax=float(t1.wavelength_nm[t1.Cohen_d.abs().idxmax()]),
                      n_d_small=int((t1.Cohen_d.abs() >= 0.2).sum()), n_d_medium=int((t1.Cohen_d.abs() >= 0.5).sum()),
                      lower_D=int(((t1.mean_diseased < t1.mean_healthy) & (t1.p_ANOVA < 0.05)).sum()),
                      higher_D=int(((t1.mean_diseased > t1.mean_healthy) & (t1.p_ANOVA < 0.05)).sum()),
                      regions={nm: [int(((t1.wavelength_nm >= lo) & (t1.wavelength_nm < hi)).sum()), int(((t1.wavelength_nm >= lo) & (t1.wavelength_nm < hi) & (t1.p_ANOVA < 0.05)).sum()),
                                    int(((t1.wavelength_nm >= lo) & (t1.wavelength_nm < hi) & (t1.p_plot_means < 0.05)).sum())]
                               for nm, lo, hi in [("VIS", 0, 700), ("Red-edge", 700, 750), ("NIR", 750, 1350), ("SWIR-1", 1350, 1800), ("SWIR-2", 1800, 3000)]}),
           jm_band_max=float(np.max(R["jm_band"])), wl_jm_max=float(wl[int(np.argmax(R["jm_band"]))]), fallbacks=int(R["fallbacks"]))
out["full"] = {}
for t2 in ("CART", "RF"):
    f = full[t2]
    out["full"][t2] = dict(bands=[round(float(w), 1) for w in f["wl"]], jm_single=[float(v) for v in f["jm_single"]], cum=[float(v) for v in f["cum"]], JM=float(f["JM"]))
out["full"]["CART"].update(nodes=int(full["CART"]["nodes"]), train_acc=float(full["CART"]["train_acc"]))
tr = full["CART"]["tree"]
out["full"]["CART"]["root"] = dict(band=float(wl[tr["feat_idx"][tr["f"][0]]]), thr=float(tr["thr"][0]), left=[int(v) for v in tr["counts"][tr["L"][0]]], right=[int(v) for v in tr["counts"][tr["Rr"][0]]])
out["cv"] = {}
for t2 in ("CART", "RF"):
    o = {}
    for k in ("CV1", "CV2", "CV3", "CV4", "CV5", "CV6"):
        e = V[(t2, "S0")][k]; reps = e["reps"]
        o[k] = dict(BA=ms([m["BA"] for m in reps]), OA=ms([m["OA"] for m in reps]), kappa=ms([m["kappa"] for m in reps]), MCC=ms([m["MCC"] for m in reps]),
                    AUC=ms([m["AUC"] for m in reps if "AUC" in m]), plotBA=ms([m["plot"]["BA"] for m in reps]),
                    acc={lev: accd(e["acc"][lev]) for lev in ("spectra", "plots")})
        if k == "CV1": o[k]["rep1"] = accd(e["acc_rep1"]["spectra"])
        if k == "CV3":
            tb = reps[0]["plot"]["table"]
            o[k]["correct"] = int((tb.pred == tb.t).sum()); o[k]["wrongH"] = [int(g) for g in tb.index if tb.t[g] == 0 and tb.pred[g] != 0]
            o[k]["wrongD"] = [int(g) for g in tb.index if tb.t[g] == 1 and tb.pred[g] != 1]
        if k in ("CV4", "CV5", "CV6"):
            o[k]["per_fold"] = [[pf["label"], pf["acc"], pf["BA"]] for pf in reps[0]["per_fold"]]; o[k]["no_band"] = int(reps[0]["no_band_folds"])
            tb = reps[0]["plot"]["table"]; o[k]["correct"] = int((tb.pred == tb.t).sum())
        if k == "CV2":
            stab = Counter(b for m in reps for fb in m["bands"] for b in fb); nf = sum(len(m["bands"]) for m in reps)
            o[k]["stable"] = [[round(float(wl[b]), 1), round(c / nf, 2)] for b, c in stab.most_common(10)]
            o[k]["kfold"] = float(np.mean([len(fb) for m in reps for fb in m["bands"]]))
    out["cv"][t2] = o
out["schemes"] = {k: [v[0], list(v[1])] for k, v in R["SCHEMES"].items()}
out["perm"] = {t2: dict(observed=float(p["observed"]), p=float(p["p"]), null_mean=float(np.mean(p["null"])), null_max=float(np.max(p["null"])),
                        q95=float(np.quantile(p["null"], 0.95)), n=int(len(p["null"]))) for t2, p in R["perm"].items()}
out["nc"] = [dict(pair=r["pair"], kind=r["kind"], dist=float(r["distance_m"]), sig=int(r["sig"]), sig_plot=int(r["sig_plot"]), jm=float(r["jm_band_max"]), n=list(r["n"]),
                  CART=dict(BA=list(r["CART"]["BA"]), plotBA=list(r["CART"]["plotBA"])), RF=dict(BA=list(r["RF"]["BA"]), plotBA=list(r["RF"]["plotBA"]))) for r in R["NC"].values()]
out["rp"] = {t2: dict(ba=v["ba"], p=float(v["p"]), rank=int(v["rank"])) for t2, v in R["RP"].items()}
out["det"] = {t2: dict(by_block={b: float(x) for b, x in v["by_block"].items()}, kw={k: list(map(float, x)) for k, x in v["kw"].items()}, kw_block=list(map(float, v["kw_block"])),
                       by_class={c: float(v["table"][v["table"]["class"] == c].pD_CV2.mean()) for c in ("healthy", "diseased")}) for t2, v in R["DET"].items()}
out["sens"] = R["SENS"]
X_ = R["X"]
out["disp"] = dict(sd_H=float(X_[y == 0].std(0).mean()), sd_D=float(X_[y == 1].std(0).mean()),
                   logdet={t2: [float(np.linalg.slogdet(np.cov(X_[y == k][:, full[t2]["bands"]], rowvar=False))[1]) for k in (0, 1)] for t2 in ("CART", "RF")})
bc = R["block_centroids"]; out["blocks"] = {b: [float(bc.loc[b, "x_m"]), float(bc.loc[b, "y_m"])] for b in bc.index}
out["design"] = dict(varieties=sorted(td.variety.unique()), dates=sorted(td.date.unique()))
ck = R["checks"]; out["checks"] = dict(n=int(len(ck)), passed=int((ck.result == "PASS").sum()), rows=ck[["step", "check", "obtained", "result"]].values.tolist())
out["refs"] = [list(r) for r in REFS]; out["abbr"] = [list(r) for r in ABBR]
json.dump(out, open(os.environ.get("OUTJ", "results/deck47.json"), "w"), indent=1, default=float)
print("written")
for t2 in ("CART", "RF"):
    c = out["cv"][t2]
    print(t2, "bands", out["full"][t2]["bands"], "JM", round(out["full"][t2]["JM"], 3), "| CV1 OA", round(c["CV1"]["OA"][0], 3), "CV2 BA", round(c["CV2"]["BA"][0], 3),
          "plot", round(c["CV2"]["plotBA"][0], 3), "| CV3", c["CV3"]["correct"], "| CV4-6", [round(c[k]["BA"][0], 3) for k in ("CV4", "CV5", "CV6")])
