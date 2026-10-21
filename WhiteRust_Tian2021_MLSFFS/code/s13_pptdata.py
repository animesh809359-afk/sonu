"""Export the numbers used by the slides."""
import sys, json, pickle, numpy as np, pandas as pd
sys.path.insert(0, ".")
from mlsffs import *
from content import CORRECTIONS, TIAN_REF_ERRORS
S = sys.argv[1]; O = f"{S}/out"
T = pickle.load(open(f"{O}/tables.pkl", "rb")); CK = pickle.load(open(f"{O}/crosschecks.pkl", "rb"))
fa, ne, op, pm = T["faithful"], T["nested"], T["optimism"], T["perm"]
pc = lambda v: f"{100 * v:.1f}"
d = {}
d["ncand"] = int(T["feature_counts"].iloc[0, 1:].sum())
d["npool"] = len(T["pool"]); d["ncandidates"] = len(T["dssf_candidates"])
d["dssf"] = [[r.Code, r.Feature.replace(" water absorption", "").replace(" red absorption", "").replace(" blue absorption", "")[:38], r.Family.replace(" (CWT, Mexican hat)", ""), f"{r.Mean_BA:.3f}", f"{r.VIF:.1f}"] for r in T["dssf_final"].itertuples()]
d["faithful"] = [[r.Date.split(" ")[0], r.Classifier, r._3, f"{r._4:.0f}", pc(r._7), pc(r._9)] for r in fa.itertuples()]
d["nested"] = [[r.Date.split(" ")[0], r.Classifier, pc(r.OA), pc(r.BA), f"{r.kappa:.2f}", pc(r.Sensitivity), pc(r.Specificity)] for r in ne.itertuples()]
d["chart_labels"] = [f"{r.Date.split(' ')[0]} {r.Classifier}" for r in op.itertuples()]
d["chart_A"] = [round(100 * v, 1) for v in op["A: faithful BA"]]
d["chart_B"] = [round(100 * v, 1) for v in op["B: nested BA"]]
d["optmin"], d["optmax"] = f"{op['Optimism BA (pp)'].min():.1f}", f"{op['Optimism BA (pp)'].max():.1f}"
d["nestBAmin"], d["nestBAmax"] = pc(ne.BA.min()), pc(ne.BA.max())
d["faOAmin"] = pc(fa["Mean OA"].min())
d["nullOAmin"], d["nullOAmax"] = pc(pm["Null OA mean"].min()), pc(pm["Null OA mean"].max())
d["nullBAmin"], d["nullBAmax"] = pc(pm["Null BA mean"].min()), pc(pm["Null BA mean"].max())
d["corr"] = [[c[0], c[1], c[3][:175] + ("…" if len(c[3]) > 175 else "")] for c in sorted(CORRECTIONS, key=lambda x: int(x[0][1:]))]
d["ck_pass"] = int((CK.Status == "PASS").sum()); d["ck_flag"] = int((CK.Status == "FLAG").sum())
d["ck"] = [[r.Step, r.Check, r.Status] for r in CK.itertuples()]
d["referr"] = [[a, c] for a, b, c in TIAN_REF_ERRORS]
sd = T["stage_detection"]; q = sd[sd.Classifier == "SVM"].pivot_table(index="Group", columns="Date", values="Called diseased (%)", observed=True)
d["det_min"], d["det_max"] = f"{q.drop('Control').values.min():.0f}", f"{q.drop('Control').values.max():.0f}"
d["fa_min"], d["fa_max"] = f"{q.loc['Control'].min():.0f}", f"{q.loc['Control'].max():.0f}"
ph = T["physio"]; d["nsig"] = int(ph["significant (q<0.05)"].sum())
sa = T["stageA"]; d["stageOAmin"] = pc(sa[sa.Classifier == "SVM"]["Mean OA"].min()); d["stageOAmax"] = pc(sa[sa.Classifier == "SVM"]["Mean OA"].max())
d["T1BAbest"] = pc(ne[ne.Date.str.startswith("T1")].BA.max())
json.dump(d, open(f"{O}/pptdata.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in d.items() if not isinstance(v, list)}, ensure_ascii=False))
