"""Exports the Part FS numbers and small tables used by the presentation."""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from common import ROOT, WORK, load

R = load("partFS")
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
J["consensus"] = [["Feature", "Type", "Consensus", "Methods ≥ 50 %", "AUC", "Diseased"]] + [
    [r["Feature"], r["Type"].replace("K4 first-derivative band", "K4 D1 band").replace("K2 continuum removal", "K2 CR").replace("K1 band reflectance", "K1 R"),
     f3(r["Consensus score"], 2), str(int(r["Methods ≥ 50 % of training sets"])), f3(r["AUC"], 3), r["Direction in diseased"]] for _, r in co.iterrows()]
J["consensus_set"] = {"names": R["consensus_set"]["names"], "jm": float(R["consensus_set"]["J–M"]), "v1": float(R["consensus_set"]["QDA BA V1"])}
st2 = st[st.Guard == "yes"].sort_values("Jaccard (±10 nm)", ascending=False)
J["stability"] = [["Method", "Kuncheva", "Jaccard exact", "Jaccard ±10 nm"]] + [
    [r["Method"], f3(r["Kuncheva index"], 2), f3(r["Jaccard (exact)"], 2), f3(r["Jaccard (±10 nm)"], 2)] for _, r in st2.iterrows()
    if r["Method"] not in ("Pearson r", "Fisher score")]
rt = R["runtime"].dropna(subset=["Mean seconds per training set"])
J["runtime"] = {r["Method"]: float(r["Mean seconds per training set"]) for _, r in rt.iterrows()}
J["checks"] = [["Check", "Result", "Status"]] + [[r["What was checked"], str(r["Result"]), r["Status"]] for _, r in R["checks"].iterrows()]
J["refs"] = REFS
J["txt"] = TXT
(WORK / "fs_results.json").write_text(json.dumps(J, indent=1, ensure_ascii=False, default=lambda o: o.item() if hasattr(o, "item") else str(o)))
print("fs_results.json written", len(json.dumps(J)) // 1024, "kB")
