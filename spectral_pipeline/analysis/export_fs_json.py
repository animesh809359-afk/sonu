"""Exports the Part FS numbers and small tables used by the presentation."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from common import ROOT, WORK, load

R = load(__import__("os").environ.get("FS_RES", "partFS"))
D = load("data")
REFS = json.loads((ROOT / "analysis" / "fs_references.json").read_text())
TXT = json.loads((WORK / "fs_conclusions.json").read_text()) if (WORK / "fs_conclusions.json").exists() else {}
meta = R["pool_meta"]
names = meta["name"].to_numpy()


def pct(v, d=1):
    return "–" if v is None or (isinstance(v, float) and np.isnan(v)) else f"{100 * v:.{d}f} %"


def f3(v, d=3):
    return "–" if v is None or (isinstance(v, float) and np.isnan(v)) else f"{v:.{d}f}"


def top(m, n=10):
    r = R["full_rank"].get(m)
    if r is None:
        return []
    if m == "CWT scalogram":
        return [str(R["cwt"]["names"][int(j)]) for j in list(r)[:n]]
    return [str(names[int(j)]) for j in list(r)[:n]]


J = {"n": int(len(D["y"])), "nH": int((D["y"] == 0).sum()), "nD": int((D["y"] == 1).sum()), "p": int(len(meta)),
     "n_cwt": int(len(R["cwt"]["names"])), "fig": str(WORK / "figures_fs")}
J["methods"] = [[r["Method"], r["Family"], r["Principle"], r["Reference"]] for _, r in R["methods"].iterrows()]
full = R["full"].set_index("Method")
J["full"] = {m: {"set": full.loc[m, "Selected (top-10, redundancy-controlled)"], "jm": float(full.loc[m, "J–M"]),
                 "v1": float(full.loc[m, "QDA BA (V1, leaf 10-fold)"]), "native": None if pd.isna(full.loc[m, "Native subset size"]) else int(full.loc[m, "Native subset size"]),
                 "auc": float(full.loc[m, "Mean AUC"]), "red": float(full.loc[m, "Mean |r| within set"])} for m in full.index}
J["top"] = {m: top(m) for m in R["full_rank"]}
J["info"] = {m: {k: (v if isinstance(v, (int, float, str)) else None) for k, v in (R["full_info"].get(m) or {}).items()} for m in R["full_info"]}
J["native_n"] = {m: (None if v is None else int(len(v))) for m, v in R["full_native"].items()}
s = R["summary"]
g = s[(s.Guard == "yes") & (s.k == 10)].set_index("Method")
gn = s[(s.Guard == "no") & (s.k == 10)].set_index("Method")
st = R["stability"]
sty = st[st.Guard == "yes"].set_index("Method")
J["acc"] = {m: {"qda": float(g.loc[m, "BA QDA"]), "sd": float(g.loc[m, "SD QDA"]), "rf": float(g.loc[m, "BA RF"]), "lda": float(g.loc[m, "BA LDA"]),
                "qda_plain": float(gn.loc[m, "BA QDA"]) if m in gn.index else None,
                "jac": float(sty.loc[m, "Jaccard (±10 nm)"]) if m in sty.index else None,
                "ki": float(sty.loc[m, "Kuncheva index"]) if m in sty.index and pd.notna(sty.loc[m, "Kuncheva index"]) else None}
            for m in g.index}
ref = R["fourtier_ref"].groupby("Method")["BA QDA"].mean()
J["fourtier"] = {k: float(v) for k, v in ref.items()}
cp = R["composite"]
J["composite"] = [["#", "Method", "Family", "QDA BA", "RF BA", "Stability", "J–M", "Mean rank"]] + [
    [str(int(r["Overall rank"])), r["Method"], r["Family"], pct(r["BA QDA (k=10)"]), pct(r["BA RF (k=10)"]), f3(r["Stability Jaccard (±10 nm)"], 2),
     f3(r["J–M (all leaves)"], 2), f3(r["Mean rank"], 1)] for _, r in cp.iterrows()]
J["best"] = cp["Method"].tolist()
fr = R["friedman"]
J["friedman"] = {k: (float(v) if isinstance(v, (int, float, np.floating, np.integer)) else v) for k, v in fr.items()}
J["wilcoxon"] = [["Other method", "Δ BA (best − other)", "Best better", "Holm p", "Sig."]] + [
    [r["Other"], f"{100 * r['Mean difference']:+.1f} pts", f"{r['Best better']}/{r['Best better'] + r['Other better']}",
     f"{r['Holm p']:.1e}" if r["Holm p"] < 0.001 else f"{r['Holm p']:.3f}", r["Significant (Holm 0.05)"]] for _, r in R["wilcoxon"].iterrows()]
J["vs4"] = [["Method", "vs", "Method BA", "Four-tier BA", "Δ", "Wins", "p"]] + [
    [r["Method (top-10)"], r["Four-tier set"].replace(" (Part C)", ""), pct(r["Method BA"]), pct(r["Four-tier BA"]), f"{100 * r['Mean difference']:+.1f} pts",
     f"{r['Method better']}/{r['Method better'] + r['Four-tier better']}", f"{r['Wilcoxon p']:.3f}"] for _, r in R["vs_fourtier"].iterrows()]
co = R["consensus"].head(15)
short = lambda n: "; ".join(x for x in (("next to join" if "detector join" in n else ""), ("complementary" if "weak on its own" in n else "")) if x)  # noqa: E731
J["consensus"] = [["Feature", "Type", "Consensus", "Methods ≥ 50 %", "AUC", "Diseased", "Note"]] + [
    [r["Feature"], r["Type"].replace("K4 first-derivative band", "K4 D1 band").replace("K2 continuum removal", "K2 CR").replace("K1 band reflectance", "K1 R"),
     f3(r["Consensus score"], 2), str(int(r["Methods ≥ 50 % of training sets"])), f3(r["AUC"], 3), r["Direction in diseased"], short(r.get("Note", ""))] for _, r in co.iterrows()]
J["consensus_set"] = {"names": R["consensus_set"]["names"], "jm": float(R["consensus_set"]["J–M"]), "v1": float(R["consensus_set"]["QDA BA V1"])}
st2 = st[st.Guard == "yes"].sort_values("Jaccard (±10 nm)", ascending=False)
J["stability"] = [["Method", "Kuncheva", "Jaccard exact", "Jaccard ±10 nm"]] + [
    [r["Method"], f3(r["Kuncheva index"], 2), f3(r["Jaccard (exact)"], 2), f3(r["Jaccard (±10 nm)"], 2)] for _, r in st2.iterrows()
    if r["Method"] not in ("Pearson r", "Fisher score")]
rt = R["runtime"].dropna(subset=["Mean seconds per training set"])
J["runtime"] = {r["Method"]: float(r["Mean seconds per training set"]) for _, r in rt.iterrows()}
J["checks"] = [["Check", "Result", "Status"]] + [[r["What was checked"], str(r["Result"]), r["Status"]] for _, r in R["checks"].iterrows()]
e = R["edge"]
J["edge"] = [["Method", "Near-join share", "QDA BA", "Join bands excluded", "Δ", "p"]] + [
    [r["Method"], pct(r["Share"]), pct(r["QDA BA top-10"]), pct(r["QDA BA, join-adjacent bands excluded"]), f"{100 * r['Difference']:+.1f} pts",
     f"{r['Wilcoxon p']:.3f}"] for _, r in e.sort_values("Share", ascending=False).iterrows() if r["Share"] > 0]
J["refs"] = REFS
J["txt"] = TXT
(WORK / "fs_results.json").write_text(json.dumps(J, indent=1, ensure_ascii=False, default=lambda o: o.item() if hasattr(o, "item") else str(o)))
print("fs_results.json written", len(json.dumps(J)) // 1024, "kB")

# ---------------------------------------------------------------- per-method detail for the Word report
g10 = s[s.Guard == "yes"]
nat = R["native"].set_index("Method")
edg = R["edge"].set_index("Method")
mr = R["mean_ranks"].set_index("Method")["Mean rank"]
cpr = R["composite"].set_index("Method")["Overall rank"]
stk = st[st.Guard == "yes"].set_index("Method")
rtm = R["runtime"].set_index("Method")
detail = {}
for m in R["methods"]["Method"]:
    q = g10[g10.Method == m].set_index("k")
    d = {"k_rows": [["k (features)", "QDA BA", "SD", "LDA BA", "AUC (QDA)"]] + [
        [str(k), pct(q.loc[k, "BA QDA"]), pct(q.loc[k, "SD QDA"]), pct(q.loc[k, "BA LDA"]), f3(q.loc[k, "AUC QDA"])] for k in (5, 10, 15, 20)],
        "rf10": float(q.loc[10, "BA RF"]), "qda10": float(q.loc[10, "BA QDA"])}
    sel = full.loc[m, "Selected (top-10, redundancy-controlled)"] if m in full.index else ""
    d["set"] = sel
    d["jm"] = float(full.loc[m, "J–M"]) if m in full.index else None
    d["v1"] = float(full.loc[m, "QDA BA (V1, leaf 10-fold)"]) if m in full.index else None
    d["red"] = float(full.loc[m, "Mean |r| within set"]) if m in full.index else None
    d["jac"] = float(stk.loc[m, "Jaccard (±10 nm)"]) if m in stk.index else None
    d["ki"] = float(stk.loc[m, "Kuncheva index"]) if m in stk.index and pd.notna(stk.loc[m, "Kuncheva index"]) else None
    d["native"] = None if m not in nat.index else {"mean": float(nat.loc[m, "Mean size"]), "min": int(nat.loc[m, "Min size"]), "max": int(nat.loc[m, "Max size"]),
                                                   "rf": float(nat.loc[m, "BA RF"]), "qda": None if pd.isna(nat.loc[m, "BA QDA"]) else float(nat.loc[m, "BA QDA"])}
    d["edge"] = None if m not in edg.index else {"share": float(edg.loc[m, "Share"]), "diff": float(edg.loc[m, "Difference"]), "p": float(edg.loc[m, "Wilcoxon p"]),
                                                 "excl": float(edg.loc[m, "QDA BA, join-adjacent bands excluded"])}
    sec_ = rtm.loc[m, "Mean seconds per training set"] if m in rtm.index else np.nan
    d["sec"] = None if pd.isna(sec_) else float(sec_)
    d["mean_rank"] = float(mr[m]) if m in mr.index else None
    d["overall"] = int(cpr[m]) if m in cpr.index else None
    rk = R["full_rank"].get(m)
    sc = R["full_score"].get(m)
    rows = [["Rank", "Feature", "Type", "Score"]]
    if rk is not None:
        for i, j in enumerate(list(rk)[:15]):
            j = int(j)
            if m == "CWT scalogram":
                nm_, ty_ = str(R["cwt"]["names"][j]), "CWT wavelet coefficient"
            else:
                nm_, ty_ = str(names[j]), str(meta["type"].iloc[j])
            if isinstance(sc, dict):
                v = sc.get(j)
            elif sc is not None and np.ndim(sc) == 1 and j < len(sc):
                v = sc[j]
            else:
                v = None
            if m in ("ANOVA F", "Pearson r", "Fisher score", "J–M (univariate)"):
                U_ = R["univariate_all"]
                v = {"ANOVA F": U_["F"], "Pearson r": U_["abs_r"], "Fisher score": U_["fisher"], "J–M (univariate)": U_["jm"]}[m][j]
            rows.append([str(i + 1), nm_, ty_, "–" if v is None else (f"{v:.3g}")])
    d["top15"] = rows
    detail[m] = d
J["detail"] = detail
J["summary_table"] = [["Method", "Family", "QDA k=5", "k=10", "k=15", "k=20", "RF k=10", "Stability", "J–M", "Overall rank"]] + [
    [m, R["methods"].set_index("Method").loc[m, "Family"]] + [pct(g10[(g10.Method == m) & (g10.k == k)]["BA QDA"].iloc[0]) for k in (5, 10, 15, 20)] +
    [pct(detail[m]["rf10"]), f3(detail[m]["jac"], 2), f3(detail[m]["jm"], 2), str(detail[m]["overall"] or "= ANOVA F")]
    for m in R["methods"]["Method"]]
ge = R["guard_effect"]
J["guard"] = [["Method", "Plain top-10", "Redundancy-controlled", "Difference"]] + [
    [r["Method"], pct(r["Plain top-10"]), pct(r["Redundancy-controlled top-10"]), f"{100 * r['Difference']:+.1f} pts"]
    for _, r in ge.sort_values("Difference", ascending=False).iterrows() if r["Method"] not in ("Pearson r", "Fisher score")]
J["mean_ranks"] = [["Method", "Mean rank"]] + [[r["Method"], f3(r["Mean rank"], 2)] for _, r in R["mean_ranks"].iterrows()]
J["native_tab"] = [["Method", "Mean size", "Range", "QDA BA", "RF BA"]] + [
    [r["Method"], f3(r["Mean size"], 1), f"{int(r['Min size'])}–{int(r['Max size'])}", pct(r["BA QDA"]) if pd.notna(r["BA QDA"]) else "– (> 30 features)", pct(r["BA RF"])]
    for _, r in R["native"].iterrows()]
J["runtime_tab"] = [["Method", "Family", "Seconds per training set", "All leaves (s)"]] + [
    [r["Method"], r["Family"], f3(r["Mean seconds per training set"], 1) if pd.notna(r["Mean seconds per training set"]) else "< 0.1", f3(r["All leaves (s)"], 1) if pd.notna(r["All leaves (s)"]) else "< 0.1"]
    for _, r in R["runtime"].iterrows() if r["Method"] != "Consensus (Borda)"]
J["consensus_full"] = [["Feature", "Type", "Consensus", "Methods ≥ 50 %", "AUC", "Hedges g", "Diseased", "Note"]] + [
    [r["Feature"], r["Type"], f3(r["Consensus score"], 2), str(int(r["Methods ≥ 50 % of training sets"])), f3(r["AUC"], 3), f3(r["Hedges g"], 2),
     r["Direction in diseased"], r.get("Note", "")] for _, r in R["consensus"].head(20).iterrows()]
(WORK / "fs_results.json").write_text(json.dumps(J, indent=1, ensure_ascii=False, default=lambda o: o.item() if hasattr(o, "item") else str(o)))
print("fs_results.json (with detail) written", len(json.dumps(J, default=str)) // 1024, "kB")
