"""Figures and JSON for the disease-specific-feature presentation (Part FS follow-up)."""
from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

from common import ROOT, WORK, load  # noqa: E402

FIG = WORK / "figures_fsfeat"
FIG.mkdir(exist_ok=True)
H_COL, D_COL = "#1baf7a", "#eb6834"
INK, INK2, GRID, GUARD = "#0b0b0b", "#52514e", "#e5e4df", "#d9d8d2"
SEQ = LinearSegmentedColormap.from_list("seq", ["#f4f4f1", "#c6dcf7", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"])
TIER_COL = {"Core": "#0d366b", "Supporting": "#3987e5", "Complementary": "#86b6ef", "Occasional": "#c6dcf7"}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": GRID,
                     "grid.linewidth": 0.6, "legend.frameon": False, "axes.titleweight": "bold", "axes.titlesize": 10, "savefig.dpi": 200,
                     "savefig.bbox": "tight"})
F = load("fsfeat")
R = load("partFS")
D = load("data")
spec, y = D["spec"], D["y"]
done = []


def save(fig, name):
    fig.savefig(FIG / f"{name}.png")
    plt.close(fig)
    done.append(name)


STABLE_REGIONS = [(1900, 1960, "1940-nm water (CR6, D1 1915–1945)"), (955, 995, "970-nm water (CR3)"),
                  (830, 915, "NIR slope (D1 832–911)"), (1715, 1750, "C–H 1724–1744"), (2200, 2310, "C–H/N–H 2209–2306")]


def fd01_spectrum():
    m = ~spec.excluded
    wl = spec.wl[m]
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 5.6), sharex=True)
    for c, col, lab in ((0, H_COL, "healthy"), (1, D_COL, "diseased")):
        a1.plot(wl, spec.R[y == c][:, m].mean(0), color=col, lw=1.5, label=lab)
        a2.plot(wl, spec.D1[y == c][:, m].mean(0) * 1000, color=col, lw=1.3, label=lab)
    for ax in (a1, a2):
        for a, b in ((990, 1010), (1795, 1835)):
            ax.axvspan(a, b, color=GUARD, lw=0, zorder=0)
        for k, (a, b, lab) in enumerate(STABLE_REGIONS):
            ax.axvspan(a, b, color="#3987e5", alpha=0.13 if k < 3 else 0.07, lw=0, zorder=0)
    for k, (a, b, lab) in enumerate(STABLE_REGIONS):
        a1.text((a + b) / 2, 0.735, lab.replace("\n", " "), rotation=90, ha="center", va="top", fontsize=7, color="#0d366b" if k < 3 else INK2)
    a1.set_ylim(0, 0.75)
    a1.set_ylabel("Reflectance")
    a2.set_ylabel("First derivative (×10⁻³ nm⁻¹)")
    a2.set_xlabel("Wavelength (nm)")
    a1.legend(loc="upper right", fontsize=8)
    a1.set_title("Stable disease-specific regions on the mean spectra (dark shading = selected by most methods; light = complementary; grey = detector joins)")
    save(fig, "FD01_regions_on_spectrum")


def fd02_region_map():
    rm = F["region_map"].set_index("Method")
    rs = F["region_summary"]
    cols = [c for c in rs["Region"] if c in rm.columns][:16]
    M = rm[cols]
    fig, ax = plt.subplots(figsize=(12, 7.2))
    im = ax.imshow(M.values, aspect="auto", cmap=SEQ, vmin=0, vmax=1)
    labels = [f"{c}  ({int(rs.set_index('Region').loc[c, 'Methods selecting it in ≥ 50 % of training sets'])})" for c in cols]
    ax.set_xticks(range(len(cols)), labels, rotation=55, ha="right", fontsize=7.5)
    ax.set_yticks(range(len(M)), M.index, fontsize=8)
    ax.grid(False)
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            v = M.values[i, j]
            if v >= 0.5:
                ax.text(j, i, f"{v:.1f}" if v < 1 else "1", ha="center", va="center", fontsize=6.5, color="white" if v > 0.7 else INK)
    cb = fig.colorbar(im, ax=ax, pad=0.01)
    cb.set_label("Share of the 20 training sets with ≥ 1 top-10 feature in the region")
    ax.set_title("Which spectral regions does each method select? (number of methods selecting the region in ≥ 50 % of training sets in brackets)")
    save(fig, "FD02_region_map")


def fd03_tiers():
    c = F["consensus"].head(20).iloc[::-1]
    fig, ax = plt.subplots(figsize=(8.5, 6.2))
    cols = [TIER_COL[t.split()[0]] for t in c["Tier"]]
    bars = ax.barh(c["Feature"], c["Methods ≥ 50 % of training sets"], color=cols, height=0.7)
    for b, nj in zip(bars, c["Near detector join"]):
        if nj:
            b.set_hatch("///")
            b.set_edgecolor("white")
    for i, (_, r) in enumerate(c.iterrows()):
        ax.text(r["Methods ≥ 50 % of training sets"] + 0.2, i, f"{r['Methods ≥ 50 % of training sets']}  (AUC {r['AUC']:.2f}, {r['Direction in diseased']} in diseased)",
                va="center", fontsize=7.5)
    ax.axvline(10.5, color=INK2, lw=0.8, ls="--")
    ax.text(10.6, len(c) - 0.6, "half of the 21 methods", fontsize=7.5, color=INK2)
    ax.set_xlim(0, 27)
    ax.set_xlabel("Number of methods (of 21) selecting the feature (±10 nm) in ≥ 50 % of the training sets")
    ax.grid(axis="y", visible=False)
    ax.legend(handles=[Patch(color=TIER_COL[k], label=lab) for k, lab in (("Core", "Core: ≥ 10 methods"), ("Supporting", "Supporting: 5–9"),
                                                                       ("Complementary", "Complementary: 3–4"), ("Occasional", "Occasional: ≤ 2"))]
              + [Patch(facecolor="#86b6ef", hatch="///", edgecolor="white", label="within 10 nm of a detector join")], fontsize=7.5, loc="lower right")
    ax.set_title("How many methods agree on each feature?")
    save(fig, "FD03_feature_agreement")


def fd04_strata():
    s = F["strata"].set_index("Feature")
    cols = [c for c in s.columns if c.startswith(("Date:", "Growth stage:", "Variety:"))]
    M = s[["AUC all leaves"] + cols]
    fig, ax = plt.subplots(figsize=(11, 0.34 * len(M) + 1.6))
    im = ax.imshow(M.values, aspect="auto", cmap=SEQ, vmin=0.5, vmax=0.95)
    ax.set_xticks(range(M.shape[1]), [c.replace("Growth stage: ", "").replace("Date: ", "").replace("Variety: ", "Var. ") for c in M.columns],
                  rotation=40, ha="right", fontsize=8)
    ax.set_yticks(range(len(M)), M.index, fontsize=8)
    ax.grid(False)
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            ax.text(j, i, f"{M.values[i, j]:.2f}", ha="center", va="center", fontsize=6.5, color="white" if M.values[i, j] > 0.8 else INK)
    for x in (0.5, 4.5, 7.5):
        ax.axvline(x, color="white", lw=2)
    ax.set_title("AUC of each consensus feature within every date, growth stage and variety (direction-free; same direction as all leaves unless listed in the table)")
    cb = fig.colorbar(im, ax=ax, pad=0.01)
    cb.set_label("AUC (0.5 = no discrimination)")
    save(fig, "FD04_consistency_strata")


def fd05_boxes():
    cons = F["consensus"].set_index("Feature")
    feats = ["CR3 water 970 width", "CR6 water 1940 position", "CR6 water 1940 symmetry", "D1_1934", "D1_1915", "D1_848", "D1_898", "ARI"]
    meta = R["pool_meta"]
    from stage_FS import build_pool
    _, P, _ = build_pool()
    fig, axs = plt.subplots(2, 4, figsize=(12, 5.6))
    for ax, f in zip(axs.ravel(), feats):
        j = int(cons.loc[f, "idx"])
        v = P.X[:, j] * (1000 if f.startswith("D1") else 1)
        bp = ax.boxplot([v[y == 0], v[y == 1]], tick_labels=["healthy", "diseased"], widths=0.55, patch_artist=True, showfliers=False,
                        medianprops=dict(color=INK, lw=1.2))
        for patch, col in zip(bp["boxes"], (H_COL, D_COL)):
            patch.set_facecolor(col)
            patch.set_alpha(0.75)
            patch.set_edgecolor(INK2)
        unit = {"CR3 water 970 width": "nm", "CR6 water 1940 position": "nm"}.get(f, "×10⁻³ nm⁻¹" if f.startswith("D1") else "")
        ax.set_title(f"{f}\nAUC {cons.loc[f, 'AUC']:.2f} · {cons.loc[f, 'Direction in diseased']} in diseased", fontsize=8.5)
        ax.set_ylabel(unit, fontsize=8)
        ax.grid(axis="x", visible=False)
    fig.suptitle("Healthy vs diseased leaves for the stable disease-specific features (boxes: interquartile range; whiskers: 1.5 × IQR)",
                 fontsize=10, fontweight="bold", y=1.0)
    fig.tight_layout()
    save(fig, "FD05_class_distributions")


def fd06_performance():
    fx = F["fixed"].set_index("Set")
    s = R["summary"]
    g = s[(s.Guard == "yes") & (s.k == 10)].set_index("Method")
    ref = R["fourtier_ref"].groupby("Method")["BA QDA"].mean()
    rows = [(k.replace(" (", "\n("), fx.loc[k, "BA QDA"], fx.loc[k, "BA RF"]) for k in fx.index]
    rows += [("Consensus (Borda),\nre-selected in each training set", g.loc["Consensus (Borda)", "BA QDA"], g.loc["Consensus (Borda)", "BA RF"]),
             ("SVM-RFE top-10,\nre-selected in each training set", g.loc["SVM-RFE", "BA QDA"], g.loc["SVM-RFE", "BA RF"]),
             ("Four-tier RF-17 (Part C)", ref["Four-tier RF-17 (Part C)"], np.nan)]
    df = pd.DataFrame(rows, columns=["Set", "QDA", "RF"]).iloc[::-1]
    fig, ax = plt.subplots(figsize=(9, 5.2))
    yv = np.arange(len(df))
    ax.barh(yv + 0.18, df["QDA"] * 100, 0.34, color="#2a78d6", label="QDA (equal priors)")
    ax.barh(yv - 0.18, df["RF"] * 100, 0.34, color="#eda100", label="Balanced Random Forest")
    for i, (_, r) in enumerate(df.iterrows()):
        ax.text(r["QDA"] * 100 + 0.4, i + 0.18, f"{100 * r['QDA']:.1f}", va="center", fontsize=7.5)
        if pd.notna(r["RF"]):
            ax.text(r["RF"] * 100 + 0.4, i - 0.18, f"{100 * r['RF']:.1f}", va="center", fontsize=7.5)
    ax.set_yticks(yv, df["Set"], fontsize=8)
    ax.set_xlim(60, 92)
    ax.set_xlabel("Balanced accuracy on held-out plots (%, mean of 20)")
    ax.grid(axis="y", visible=False)
    ax.legend(fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2)
    ax.set_title("How well do the stable features discriminate healthy and diseased leaves?")
    save(fig, "FD06_performance")


def export():
    cons = F["consensus"]
    pm = F["per_method"]
    fx = F["fixed"]
    st = F["strata"]
    rs = F["region_summary"]
    pct = lambda v: "–" if pd.isna(v) else f"{100 * v:.1f} %"  # noqa: E731
    J = {"fig": str(FIG), "fig_fs": str(WORK / "figures_fs")}
    J["per_method"] = {fam: [["Method", "Top-10 features (all leaves, redundancy-controlled)", "Regions (number of features)"]] +
                       [[r["Method"], r["Top-10 (all leaves)"], r["Regions"]] for _, r in pm[pm.Family.isin(fams)].iterrows()]
                       for fam, fams in (("Filter", ["Filter"]), ("Wrapper", ["Wrapper"]), ("Embedded", ["Embedded", "Ensemble"]))}
    J["regions"] = [["Spectral region / feature group", "Meaning", "Methods ≥ 50 %", "Mean frequency"]] + [
        [r["Region"], r["Physiological meaning"], str(int(r["Methods selecting it in ≥ 50 % of training sets"])), f"{r['Mean selection frequency']:.2f}"]
        for _, r in rs.head(10).iterrows()]
    J["tiers"] = [["Feature", "Tier", "Methods ≥ 50 %", "AUC", "Healthy → diseased", "Note"]]
    for _, r in cons[cons.Tier != "Occasional"].head(16).iterrows():
        fmt = (lambda v: f"{v:.1f}") if r["Feature"].startswith("CR") and ("width" in r["Feature"] or "position" in r["Feature"]) else \
              ((lambda v: f"{1000 * v:.3f}") if r["Feature"].startswith("D1") else (lambda v: f"{v:.3f}"))
        note = "near detector join" if r["Near detector join"] else ("weak alone" if r["AUC"] < 0.6 else "")
        J["tiers"].append([r["Feature"], r["Tier"].split(" (")[0], str(int(r["Methods ≥ 50 % of training sets"])), f"{r['AUC']:.2f}",
                           f"{fmt(r['Mean healthy'])} → {fmt(r['Mean diseased'])} ({r['Direction in diseased']})", note])
    J["which"] = [["Feature", "Methods selecting it in ≥ 50 % of the training sets"]] + [
        [r["Feature"], r["Which methods (≥ 50 % of training sets)"]] for _, r in cons.head(7).iterrows()]
    J["fixed"] = [["Feature set", "k", "QDA BA", "LDA BA", "RF BA", "AUC", "J–M"]] + [
        [r["Set"], str(int(r["k"])), pct(r["BA QDA"]), pct(r["BA LDA"]), pct(r["BA RF"]), f"{r['AUC QDA']:.3f}", f"{r['J–M (all leaves)']:.2f}"] for _, r in fx.iterrows()]
    J["fixed_sets"] = F["fixed_sets"]
    sc = [c for c in st.columns if c.startswith("Same direction")]
    J["strata"] = [["Feature", "AUC all", "AUC range dates", "AUC range stages", "AUC range varieties", "Same direction (dates / stages / varieties)"]]
    for _, r in st.iterrows():
        rng = []
        for by in ("Date:", "Growth stage:", "Variety:"):
            v = [r[c] for c in st.columns if c.startswith(by)]
            rng.append(f"{min(v):.2f}–{max(v):.2f}")
        J["strata"].append([r["Feature"], f"{r['AUC all leaves']:.2f}"] + rng + [" / ".join(r[c] for c in sc)])
    J["borda"] = F["borda_honest"]
    s = R["summary"]
    g = s[(s.Guard == "yes") & (s.k == 10)].set_index("Method")
    J["svm"] = float(g.loc["SVM-RFE", "BA QDA"])
    J["svm_rf"] = float(g.loc["SVM-RFE", "BA RF"])
    J["refs"] = json.loads((ROOT / "analysis" / "fs_references.json").read_text())
    (WORK / "fsfeat.json").write_text(json.dumps(J, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    for f in (fd01_spectrum, fd02_region_map, fd03_tiers, fd04_strata, fd05_boxes, fd06_performance):
        f()
    export()
    print(len(done), "figures", done)
