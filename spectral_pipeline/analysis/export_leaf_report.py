"""Collects the results of the three leaf-level runs (L3, L5, LL) for the Word report: one JSON with every number
and table the report uses (texts written with full names, no V1-V5 / K1-K4 codes), cross-level comparison figures,
and size-reduced copies of the per-level figures. Output: work_subsets/report_leaf/ (subsets.json, figures/)."""
from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from PIL import Image  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import yaml  # noqa: E402

WS = ROOT / "work_subsets"
OUT = WS / "report_leaf"
FIG = OUT / "figures"
FIG.mkdir(parents=True, exist_ok=True)
A0W = ROOT / "work"
PIPES = ["CART classifier", "RF classifier", "QDA on CART features", "QDA on RF features"]
# categorical palette (validated: CVD ΔE ≥ 9, normal ΔE ≥ 22.9 on the light surface)
C1, C2, C3, C4 = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e5e4df"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "legend.frameon": False,
                     "axes.titleweight": "bold", "axes.titlesize": 10, "savefig.dpi": 200, "savefig.bbox": "tight"})


def L(w, n):
    with open(w / f"{n}.pkl", "rb") as fh:
        return pickle.load(fh)


def f(v, nd=4):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    return None if not np.isfinite(v) else round(v, nd)


def recs(df, cols=None, nd=4):
    df = df if cols is None else df[cols]
    out = []
    for _, r in df.iterrows():
        out.append({c: (f(r[c], nd) if isinstance(r[c], (int, float, np.integer, np.floating)) and not isinstance(r[c], bool)
                        else (str(r[c]) if r[c] is not None else "")) for c in df.columns})
    return out


def vtab(R):
    v = R["validation"].set_index(["Pipeline", "Scheme"])
    return {f"{p}|{s}": {"BA": f(v.loc[(p, s), "BA"]), "SD": f(v.loc[(p, s), "BA_SD"]), "OA": f(v.loc[(p, s), "OA"]),
                         "AUC": f(v.loc[(p, s), "AUC"]), "kappa": f(v.loc[(p, s), "kappa"]),
                         "PA_H": f(v.loc[(p, s), "PA_H"]), "PA_D": f(v.loc[(p, s), "PA_D"])}
            for p, s in v.index}


def em(m):
    return {k: (int(m[k]) if k in ("HH", "HD", "DH", "DD", "N") else f(m[k])) for k in
            ("HH", "HD", "DH", "DD", "N", "OA", "BA", "kappa", "PA_H", "PA_D", "UA_H", "UA_D")}


def jm(R, name):
    return f(R["tier3"].set_index("Set").loc[name, "JM"], 3)


def short(n):
    return str(n).replace("WV", "")


def copy_fig(src: Path, name: str, width=1500):
    if not src.exists():
        return None
    im = Image.open(src)
    if im.width > width:
        im = im.resize((width, int(im.height * width / im.width)), Image.LANCZOS)
    dst = FIG / f"{name}.png"
    im.convert("RGB").save(dst, optimize=True)
    return dst.name


SUB = []
sys.path.insert(0, str(ROOT / "analysis"))
from naming import Namer  # noqa: E402
NM = Namer("Date")
TX = NM.text


def txrec(rows):
    return [{k: (TX(v) if isinstance(v, str) and k not in ("Level", "Variety") else v) for k, v in r.items()} for r in rows]


for cfgf in sorted((ROOT / "configs" / "leaf_levels").glob("[123]_*.yaml")):
    name = cfgf.stem
    w = WS / name
    cfg = yaml.safe_load(open(cfgf))
    D, A, K, Cc, X = (L(w, n) for n in ("data", "partA", "partK", "partC", "compare"))
    TXT = json.loads((w / "conclusions.json").read_text())
    y, F, meta, groups = D["y"], D["folds"], D["meta"], D["groups"]
    PD = list(dict.fromkeys(D["dates"]))
    s = {"key": name, "label": cfg["data"]["subset_label"], "group": "Leaf level",
         "short": "Leaf level " + cfg["data"]["subset"]["Leaf level"], "level": cfg["data"]["subset"]["Leaf level"],
         "n": int(len(y)), "nH": int((y == 0).sum()), "nD": int((y == 1).sum()),
         "pH": len(set(groups[y == 0])), "pD": len(set(groups[y == 1])), "dates": PD,
         "stages": sorted(meta["Growth stage"].unique()), "varieties": sorted(meta["Variety"].unique()),
         "k3": int(F["v3_k"]), "v3_method": F["v3_method"], "nV3": len(F["V3"]), "v4": list(map(int, F["v4_plots"])),
         "v5_by": F.get("V5_by", "Date"), "nV5": len(F["V5"]), "v5_dropped": len(F.get("V5_dropped", [])),
         "by_stage": recs(D["audit"]["by_stage"].reset_index()), "by_variety": recs(D["audit"]["by_variety"].reset_index()),
         "by_date": recs(D["audit"]["by_date"].reset_index()), "leaf_n": int(D["audit"]["leaf"]["n_files"]),
         "by_stage_total": recs(D["audit"]["by_stage_total"].reset_index())}
    t1 = A["tier1"]
    tt = A["tier1_tests"]
    s["tier1_tests"] = [[r["Test"], int(r["Significant bands"])] for _, r in tt.iterrows()]
    s["n_sig"], s["n_feat"] = int(A["n_sig"]), int(A["n_features"])
    s["tier1_rule"], s["n_cand"] = A.get("tier1_rule", "FDR"), int(len(A.get("sig_cols", [])))
    s["n_mm"] = int(t1["mm_sig"].sum())
    s["regions"] = recs(A["tier1_regions"])
    s["ranges"] = recs(A["tier1_ranges"][A["tier1_ranges"]["Result"] == "significant"].sort_values("Bands", ascending=False).head(8))
    top = t1.reindex(t1["t"].abs().sort_values(ascending=False).index).head(10)
    s["top_bands"] = [[int(r["position"]), f(r["mean0"]), f(r["mean1"]), f(r["t"], 2), f(r["q"], 8), f(r["g"], 2), f(r["auc"], 3)]
                      for _, r in top.iterrows()]
    s["cart_name"], s["rf_name"] = A["cart_name"], A["rf_name"]
    s["cart_bands"] = [short(b) for b in A["sets"][A["cart_name"]]]
    s["rf_bands"] = [short(b) for b in A["sets"][A["rf_name"]]]
    ct = A["cart_table"]
    s["cart_table"] = [[int(r["Band (nm)"]), r["Region"], int(r["First used at node"]) if pd.notna(r["First used at node"]) else "",
                        f(r["Bootstrap re-selection (±10 nm)"], 3), f(r["Nested-CV re-selection (±10 nm)"], 3), str(r["Interpretation"])]
                       for _, r in ct.iterrows()]
    s["root"] = short(A["cart_full"]["vars"][0]) if A["cart_full"]["vars"] else "—"
    s["tier3"] = [[r["Set"], int(r["Features"]), f(r["alpha"], 3), f(r["JM"], 3), f(np.sqrt(r["JM"]), 3)] for _, r in A["tier3"].iterrows()]
    s["jm_c"], s["jm_r"] = jm(A, A["cart_name"]), jm(A, A["rf_name"])
    s["em_cart"], s["em_rf"] = em(A["errmat"][A["cart_name"]]), em(A["errmat"][A["rf_name"]])
    t4 = A["tier4"]
    s["tier4"] = [[r["Set"], r["Classifier"], f(r["OA"]), f(r["BA"]), f(r["PA_H"]), f(r["PA_D"]), f(r["kappa"], 3)] for _, r in t4.iterrows()]
    s["vA"], s["vC"] = vtab(A), vtab(Cc)
    vq = A["validation_qda_cart"]
    s["val_qda"] = [[r["Scheme"], r["Priors"], f(r["BA"]), f(r["BA_SD"]), f(r["OA"]), f(r["PA_H"]), f(r["PA_D"])] for _, r in vq.iterrows()]
    s["wil_A"] = recs(A["wilcoxon"][["Comparison", "Units", "n", "Mean difference", "First better", "Second better", "Wilcoxon p"]], nd=6)
    st = A["stability"]["index"].set_index("Method")
    s["stab_A"] = {m: {"jacc": f(st.loc[m, "Mean pairwise Jaccard (±10 nm)"], 3), "all10": int(st.loc[m, "Selected in all sets (±10 nm)"]),
                       "union": int(st.loc[m, "Unique features (union)"])} for m in st.index}
    s["sens_range"] = [[r["Band set"], int(r["CART bands"]), f(r["BA V1"]), f(r["BA V3 nested"]), f(r["BA V4 hold-out"])]
                       for _, r in A["sensitivity_range"].iterrows()]
    # ---- Part K
    s["k1_best"] = [f(K["k1_summary"]["best_wl"], 0), f(K["k1_summary"]["best_auc"], 3), int(K["k1_summary"]["auc70"])]
    s["k1_regions"] = [[int(r["Wavelength (nm)"]), r["Region"], f(r["AUC"], 3), r["Direction"], f(r["BA plot-grouped CV"])]
                       for _, r in K["k1_regions"].iterrows()]

    def topfeat(df, n=5):
        return [[r["name"], f(r["AUC"], 3), r["Direction"], f(r["Hedges g"], 2), f(r["BA plot-grouped CV"]), f(r["BA hold-out"])]
                for _, r in df.head(n).iterrows()]
    s["k2_top"], s["k3_top"], s["k4e_top"] = topfeat(K["k2"]), topfeat(K["k3"]), topfeat(K["k4_edge"])
    d1 = K["d1_all"][~K["d1_all"]["Guard"]].nlargest(5, "AUC")
    s["d1_top"] = [[int(r["Wavelength (nm)"]), f(r["AUC"], 3), r["Direction"], f(r["Hedges g"], 2)] for _, r in d1.iterrows()]
    rp = K["reip"]
    s["reip"] = [[r["name"].replace("REIP – ", ""), f(r["Mean healthy"], 1), f(r["Mean diseased"], 1),
                  f(r["Mean diseased"] - r["Mean healthy"], 2), f(r["AUC"], 3), f(r["BA plot-grouped CV"])] for _, r in rp.iterrows()]
    jf = K["k3b_jf"]
    s["k3b"] = [[r["name"], f(r["AUC"], 3), f(r["BA plot-grouped CV"])] for _, r in jf["refined"].iterrows()]
    s["k3b_honest"] = {k: {"cv": f(v["BA CV"]), "ho": f(v["BA hold-out"]), "pairs": v["pairs"]} for k, v in jf["honest"].items()}
    k5 = K["k5"]
    s["k5"] = [[r["Group"], r["Feature group"], int(r["Features"]), r["Classifier"], r["Scheme"], f(r["BA"]), f(r["BA_SD"])]
               for _, r in k5.iterrows()]
    # ---- Part C
    s["C_nfeat"], s["C_nsig"] = int(Cc["n_features"]), int(Cc["n_sig"])
    s["C_cart_name"], s["C_rf_name"] = Cc["cart_name"], Cc["rf_name"]
    s["C_cart"], s["C_rf"] = list(Cc["sets"][Cc["cart_name"]]), list(Cc["sets"][Cc["rf_name"]])
    s["C_jm_c"], s["C_jm_r"] = jm(Cc, Cc["cart_name"]), jm(Cc, Cc["rf_name"])
    comp = Cc["composition"]
    s["C_comp"] = [[r["Feature type"], int(r["Features"]), int(r["Tier-1 significant"]), int(r[Cc["cart_name"]]), int(r[Cc["rf_name"]])]
                   for _, r in comp.iterrows()]
    s["C_em_rf"] = em(Cc["errmat"][Cc["rf_name"]])
    cst = Cc["stability"]["index"].set_index("Method")
    s["stab_C"] = {m: f(cst.loc[m, "Mean pairwise Jaccard (±10 nm)"], 3) for m in cst.index}
    cw = X["cross_wilcoxon"]
    s["cross"] = [[r["First"], r["Second"], r["Units"], f(r["Mean difference (BA)"]), int(r["First better"]), int(r["n"]), f(r["Wilcoxon p"], 8)]
                  for _, r in cw.iterrows()]
    lo = X["lodo"]
    lev = [c for c in lo.columns if c.startswith("Held-out")][0]
    s["lodo_level"] = lev
    s["lodo"] = [[r["Feature set"].split(" (")[0], r["Pipeline"], str(r[lev]), int(r["Splits"]), f(r["BA mean"]), f(r["BA SD"])]
                 for _, r in lo.iterrows()]
    s["txt"] = TXT
    # cross-check summary
    rows = [("Step 0", *c) for c in D["audit"]["checks"]] + [tuple(c) for c in A["checks"]] + [tuple(c) for c in K["checks"]] + \
           [("Part C · " + c[0], *c[1:]) for c in Cc["checks"]]
    st_ = [r[-1] for r in rows]
    s["checks"] = {"PASS": st_.count("PASS"), "FLAG": st_.count("FLAG"), "FAIL": st_.count("FAIL")}
    s["flags"] = [[str(r[0]), str(r[1]), str(r[-2])[:240]] for r in rows if r[-1] == "FLAG"]
    # per-subset figures
    src = w / "figures"
    s["figs"] = {}
    for key, fn in (("mean", "F02_mean_spectra"), ("bydate", "F02b_mean_spectra_by_date"), ("logp", "F05_minus_log10_p"),
                    ("tree", "F06_cart_tree"), ("rfimp", "F12_A1_rf_importance"), ("pipesA", "F13_A3_pipelines"),
                    ("inc", "F09_tier3_tier4_incremental"), ("k1auc", "F16_K1_K4_band_auc"), ("k5", "F23_K5_cart_vs_rf"),
                    ("reip", "F21_K4_REIP"), ("ctop", "F25_C_top_importance"), ("pipesC", "F28_C_pipelines"),
                    ("v5", "F30_V5_leave_one_date_out"), ("stabA", "F14_A4_stability")):
        s["figs"][key] = copy_fig(src / f"{fn}.png", f"{name}_{key}")
    s["_t1"] = t1  # for cross figures (dropped before json)
    s["_A"], s["_C"], s["_spec"], s["_K"] = A, Cc, D["spec"], K
    SUB.append(s)
    print("collected", name)

# ---------------------------------------------------------------- all-dates reference
ref = {}
if (A0W / "partA.pkl").exists():
    A0, C0 = L(A0W, "partA"), L(A0W, "partC")
    ref = {"vA": vtab(A0), "vC": vtab(C0), "jm_c": jm(A0, A0["cart_name"]), "jm_r": jm(A0, A0["rf_name"]),
           "n_sig": int(A0["n_sig"]), "cart_bands": [short(b) for b in A0["sets"][A0["cart_name"]]],
           "rf_bands": [short(b) for b in A0["sets"][A0["rf_name"]]], "C_jm_r": jm(C0, C0["rf_name"])}

# ---------------------------------------------------------------- cross-subset figures
labels = [s["short"] for s in SUB]
labels2 = [lab.replace("Leaf level ", "Leaf level\n") for lab in labels]
x = np.arange(len(SUB))
GROUPS = [("Leaf level", "Leaf levels L3, L5 and LL (all dates, growth stages and varieties combined)")]


def _full(fig):
    """Full names in every text and tick label of a figure (as make_figures with naming = full)."""
    import matplotlib.text as mtext
    from matplotlib.ticker import FixedFormatter
    for t in fig.findobj(mtext.Text):
        if t.get_text():
            t.set_text(TX(t.get_text()))
    fig.canvas.draw()
    for ax in fig.axes:
        for axis in (ax.xaxis, ax.yaxis):
            labs = [t.get_text() for t in axis.get_ticklabels()]
            new = [TX(t) for t in labs]
            if new != labs:
                axis.set_major_formatter(FixedFormatter(new))


def sep_lines(ax):
    return None


def bar4(ax, vals, names, cols, ylab):
    wdt = 0.8 / len(vals)
    for k, (v, nm, c) in enumerate(zip(vals, names, cols)):
        ax.bar(x + (k - (len(vals) - 1) / 2) * wdt, np.array(v) * 100, wdt * 0.9, color=c, label=nm, zorder=3)
    ax.set_xticks(x, labels2, rotation=0, fontsize=7.5)
    ax.set_ylabel(ylab)
    sep_lines(ax)


# X1: four pipelines, V3, Part A and Part C
fig, axs = plt.subplots(2, 1, figsize=(10, 6.2), sharex=True)
for ax, key, ttl in ((axs[0], "vA", "Part A · raw reflectance (four tiers on bands)"), (axs[1], "vC", "Part C · combined K1 + K2–K4 pool")):
    vals = [[s[key][f"{p}|V3"]["BA"] for s in SUB] for p in PIPES]
    bar4(ax, vals, PIPES, [C1, C2, C3, C4], "Balanced accuracy (%)")
    ax.set_ylim(40, 100)
    ax.set_title(ttl, loc="left")
    if ref:
        ax.axhline(100 * ref[key][f"QDA on RF features|V3"]["BA"] if key == "vC" else 100 * ref[key]["QDA on CART features|V3"]["BA"],
                   color=INK, lw=0.8, ls="--", zorder=4)
axs[0].legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, 1.32), fontsize=8)
fig.text(0.99, 0.005, "Dashed line: all dates pooled (Part A: QDA on CART bands; Part C: QDA on RF features). V3 = nested plot-grouped CV.",
         ha="right", fontsize=7, color=INK2)
_full(fig)
fig.savefig(FIG / "X1_pipelines_by_subset.png")
plt.close(fig)

# X2: honest validation schemes for the recommended pipeline (Part C, QDA on RF features) + RF classifier
fig, axs = plt.subplots(2, 1, figsize=(10, 6.4), sharex=True)
for ax, p in zip(axs, ("QDA on RF features", "RF classifier")):
    vals = [[s["vC"][f"{p}|{sch}"]["BA"] for s in SUB] for sch in ("V1", "V3", "V4", "V5")]
    bar4(ax, vals, ["V1 leaf 10-fold", "V3 nested plot-grouped", "V4 plot hold-out", "V5 transfer (date / variety)"],
         ["#86b6ef", "#3987e5", "#1c5cab", "#0d366b"], "Balanced accuracy (%)")
    ax.set_ylim(40, 100)
    ax.set_title(f"Part C · {p}", loc="left")
    ax.tick_params(axis="x", labelsize=6.5)
axs[0].legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, 1.3), fontsize=8)
_full(fig)
fig.savefig(FIG / "X2_validation_schemes.png")
plt.close(fig)

# X3: significance spectra (-log10 q Welch) per subset, small multiples by group
fig, ax0 = plt.subplots(1, 1, figsize=(9, 3.6))
axs = [ax0]
for ax, (g, gt) in zip(axs, GROUPS):
    ss = [s for s in SUB if s["group"] == g]
    for s, c in zip(ss, [C1, C2, C3, C4]):
        t1 = s["_t1"]
        ax.plot(t1["position"], -np.log10(np.clip(t1["q"], 1e-300, 1)), color=c, lw=1.1, label=s["short"])
    ax.axhline(-np.log10(0.05), color=INK, lw=0.7, ls="--")
    ax.set_yscale("symlog", linthresh=2)
    ax.set_ylim(0, None)
    ax.set_ylabel("−log₁₀ q (Welch + FDR)")
    ax.set_title(gt, loc="left")
    ax.legend(fontsize=8, loc="upper left", bbox_to_anchor=(1.01, 1.0))
axs[-1].set_xlabel("Wavelength (nm)")
axs[-1].set_xlim(400, 2500)
_full(fig)
fig.savefig(FIG / "X3_significance_spectra.png")
plt.close(fig)

# X4: mean difference spectra (diseased − healthy)
fig, ax0 = plt.subplots(1, 1, figsize=(9, 3.6))
axs = [ax0]
for ax, (g, gt) in zip(axs, GROUPS):
    for s, c in zip([s for s in SUB if s["group"] == g], [C1, C2, C3, C4]):
        t1 = s["_t1"]
        ax.plot(t1["position"], (t1["mean1"] - t1["mean0"]) * 100, color=c, lw=1.1, label=s["short"])
    ax.axhline(0, color=INK, lw=0.7)
    ax.set_ylabel("Diseased − healthy\n(reflectance, %)")
    ax.set_title(gt, loc="left")
    ax.legend(fontsize=8, loc="upper left", bbox_to_anchor=(1.01, 1.0))
axs[-1].set_xlabel("Wavelength (nm)")
axs[-1].set_xlim(400, 2500)
_full(fig)
fig.savefig(FIG / "X4_difference_spectra.png")
plt.close(fig)

# X5: K5 heatmap (RF BA, V3) feature groups × subsets
gord = [("G1", "K1 reflectance"), ("G2", "K2 continuum removal"), ("G3", "K3 indices"), ("G4", "K4 derivatives + edge"),
        ("G5", "K1–K4 combined"), ("G0", "Full raw spectrum")]
M = np.array([[next((r[5] for r in s["k5"] if r[0] == g and r[3] == "RF" and r[4] == "CV"), np.nan) for s in SUB] for g, _ in gord])
fig, ax = plt.subplots(figsize=(10, 3.4))
im = ax.imshow(M * 100, cmap="Blues", vmin=50, vmax=100, aspect="auto")
ax.set_xticks(x, labels2, fontsize=7.5)
ax.set_yticks(range(len(gord)), [t for _, t in gord], fontsize=8)
ax.grid(False)
for i in range(M.shape[0]):
    for j in range(M.shape[1]):
        ax.text(j, i, f"{100 * M[i, j]:.1f}", ha="center", va="center", fontsize=7.5, color="white" if M[i, j] > 0.8 else INK)
cb = fig.colorbar(im, ax=ax, fraction=0.025)
cb.set_label("BA (%), RF, V3")
ax.set_title("K5 · Balanced RF on each disease-sensitive feature group (plot-grouped CV)", loc="left")
_full(fig)
fig.savefig(FIG / "X5_k5_heatmap.png")
plt.close(fig)

# X6: selected bands per subset (Part A), CART vs RF
fig, ax = plt.subplots(figsize=(10, 4.2))
for j, s in enumerate(SUB):
    cb_ = [float(b) for b in s["cart_bands"]]
    rb_ = [float(b) for b in s["rf_bands"]]
    ax.scatter(cb_, [j + 0.15] * len(cb_), marker="v", s=28, color=C1, label="CART bands" if j == 0 else None, zorder=3)
    ax.scatter(rb_, [j - 0.15] * len(rb_), marker="o", s=18, color=C2, label="RF-17 peaks" if j == 0 else None, zorder=3)
for a, b in ((1350, 1430), (1800, 1950)):
    ax.axvspan(a, b, color="#f0efec", zorder=0)
ax.set_yticks(range(len(SUB)), labels, fontsize=8)
ax.invert_yaxis()
ax.set_xlim(400, 2500)
ax.set_xlabel("Wavelength (nm)  (shaded: water bands I and II, kept for the contact probe)")
ax.set_title("Tier 2 · bands selected by CART and by Random Forest in each subset (Part A)", loc="left")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.17), ncol=2, fontsize=8)
_full(fig)
fig.savefig(FIG / "X6_selected_bands.png")
plt.close(fig)

# X7: J–M by subset (Part A CART/RF, Part C CART/RF)
fig, ax = plt.subplots(figsize=(10, 3.4))
vals = [[s["jm_c"] for s in SUB], [s["jm_r"] for s in SUB], [s["C_jm_c"] for s in SUB], [s["C_jm_r"] for s in SUB]]
wdt = 0.2
for k, (v, nm, c) in enumerate(zip(vals, ["Part A · CART bands", "Part A · RF-17 bands", "Part C · CART features", "Part C · RF-17 features"],
                                   [C1, C2, C3, C4])):
    ax.bar(x + (k - 1.5) * wdt, v, wdt * 0.9, color=c, label=nm, zorder=3)
ax.axhline(1.90, color=INK, lw=0.8, ls="--")
ax.axhline(1.94, color=INK, lw=0.8, ls=":")
ax.text(len(SUB) - 0.4, 1.905, "1.90", fontsize=7, va="bottom", ha="right")
ax.text(len(SUB) - 0.4, 1.945, "1.94 (Das et al.)", fontsize=7, va="bottom", ha="right")
ax.set_ylim(0, 2.05)
ax.set_xticks(x, labels2, fontsize=7.5)
ax.set_ylabel("J–M distance (0–2)")
sep_lines(ax)
ax.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.12), fontsize=8)
ax.set_title("Tier 3 · Jeffries–Matusita separability of healthy and diseased leaves", loc="left")
_full(fig)
fig.savefig(FIG / "X7_jm_by_subset.png")
plt.close(fig)

# X8: Part C feature types selected (CART and RF), stacked
types = [r[0] for r in SUB[0]["C_comp"]]
tcol = {"K1 band reflectance": C1, "K2 continuum removal": C2, "K3 vegetation index": C3, "K4 edge parameter": "#e87ba4",
        "K4 first-derivative band": C4}
fig, axs = plt.subplots(1, 2, figsize=(11, 3.6), sharey=True)
for ax, idx, ttl in ((axs[0], 3, "CART-selected features"), (axs[1], 4, "RF-selected features (RF-17)")):
    bottom = np.zeros(len(SUB))
    for t in types:
        v = np.array([next(r[idx] for r in s["C_comp"] if r[0] == t) for s in SUB], float)
        ax.bar(x, v, 0.7, bottom=bottom, color=tcol.get(t, "#999"), label=t, edgecolor="white", linewidth=1, zorder=3)
        bottom += v
    ax.set_xticks(x, labels, fontsize=7, rotation=30, ha="right")
    ax.set_title(f"Part C · {ttl}", loc="left")
axs[0].set_ylabel("Number of features")
axs[0].legend(ncol=5, loc="upper center", bbox_to_anchor=(1.05, 1.28), fontsize=7.5)
_full(fig)
fig.savefig(FIG / "X8_partC_types.png")
plt.close(fig)

# X9: REIP shift and V3 vs V5 drop
fig, axs = plt.subplots(1, 2, figsize=(11, 3.4))
sh = [next((r[3] for r in s["reip"] if r[0].startswith("Lagrangian")), np.nan) for s in SUB]
axs[0].bar(x, sh, 0.6, color=[C2 if v < 0 else C1 for v in sh], zorder=3)
axs[0].axhline(0, color=INK, lw=0.7)
axs[0].set_xticks(x, labels, fontsize=7, rotation=30, ha="right")
axs[0].set_ylabel("REIP shift, diseased − healthy (nm)")
axs[0].set_title("K4b · red-edge inflection point (Lagrangian)", loc="left")
v3 = [s["vC"]["RF classifier|V3"]["BA"] * 100 for s in SUB]
v5 = [s["vC"]["RF classifier|V5"]["BA"] * 100 for s in SUB]
for j in range(len(SUB)):
    axs[1].plot([j, j], [v5[j], v3[j]], color=GRID, lw=3, zorder=2)
axs[1].scatter(x, v3, s=40, color=C1, label="V3 nested plot-grouped CV", zorder=3)
axs[1].scatter(x, v5, s=40, color=C2, label="V5 transfer (new date or variety)", zorder=3)
axs[1].set_xticks(x, labels, fontsize=7, rotation=30, ha="right")
axs[1].set_ylim(40, 100)
axs[1].set_ylabel("Balanced accuracy (%)")
axs[1].set_title("Part C · RF classifier: within vs transfer", loc="left")
axs[1].legend(fontsize=7.5, loc="lower left")
_full(fig)
fig.savefig(FIG / "X9_reip_transfer.png")
plt.close(fig)

# X10: mean spectra healthy vs diseased per subset (3×3 small multiples)
fig, axs = plt.subplots(1, 3, figsize=(11, 3.2), sharex=True, sharey=True, squeeze=False)
for ax, s in zip(axs.ravel(), SUB):
    t1 = s["_t1"]
    ax.plot(t1["position"], t1["mean0"], color=C3, lw=1, label="Healthy")
    ax.plot(t1["position"], t1["mean1"], color=C2, lw=1, label="Diseased")
    ax.set_title(f"{s['short']} (n = {s['nH']} / {s['nD']})", fontsize=9)
axs[0, 0].legend(fontsize=7)
for ax in axs[-1]:
    ax.set_xlabel("Wavelength (nm)")
for ax in axs[:, 0]:
    ax.set_ylabel("Reflectance")
_full(fig)
fig.savefig(FIG / "X10_mean_spectra_grid.png")
plt.close(fig)

# workflow figure from the first subset
copy_fig(WS / SUB[0]["key"] / "figures" / "F01_workflow.png", "workflow", 1600)

def _tx_all(o, key=None):
    if isinstance(o, dict):
        return {k: (v if k in ("key", "figs", "short", "level", "label") else _tx_all(v, k)) for k, v in o.items()}
    if isinstance(o, list):
        return [_tx_all(v, key) for v in o]
    return TX(o) if isinstance(o, str) else o


for i, s in enumerate(SUB):
    for k in [k for k in s if k.startswith("_")]:
        del s[k]
    SUB[i] = _tx_all(s)
J = {"subsets": SUB, "ref": ref, "fig": str(FIG)}
(OUT / "subsets.json").write_text(json.dumps(J, ensure_ascii=False, indent=0))
print("written", OUT / "subsets.json", len(list(FIG.glob("*.png"))), "figures")
