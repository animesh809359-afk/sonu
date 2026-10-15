"""Figures for Part FS (feature-selection comparison)."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Patch  # noqa: E402

from common import WORK, load  # noqa: E402

FIG = WORK / "figures_fs"
FIG.mkdir(exist_ok=True)
FAM = {"Filter": "#2a78d6", "Wrapper": "#eda100", "Embedded": "#1baf7a", "Ensemble": "#6250d6"}
H_COL, D_COL = "#1baf7a", "#eb6834"
INK, INK2, GRID, GUARD = "#0b0b0b", "#52514e", "#e5e4df", "#d9d8d2"
SEQ = ["#f4f4f1", "#c6dcf7", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "legend.frameon": False,
                     "axes.titleweight": "bold", "axes.titlesize": 10, "savefig.dpi": 200, "savefig.bbox": "tight",
                     "lines.linewidth": 1.6})
R = load("partFS")
D = load("data")
meta = R["pool_meta"]
ser = meta["series"].to_numpy()
pos = meta["position"].to_numpy(float)
GZ = [(990, 1010), (1795, 1835)]
done = []


def save(fig, name):
    fig.savefig(FIG / f"{name}.png")
    plt.close(fig)
    done.append(name)


def shade(ax):
    for a, b in GZ:
        ax.axvspan(a, b, color=GUARD, lw=0, zorder=0)


def fs01_workflow():
    fig, ax = plt.subplots(figsize=(12, 4.6))
    ax.axis("off")
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 4.6)

    def box(x, y, w, h, t, fc="#f0efec", ec=INK2, fs=8.5, bold=False):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.04,rounding_size=0.08", fc=fc, ec=ec, lw=0.8))
        ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=fs, color=INK, wrap=True,
                fontweight="bold" if bold else "normal")

    def arr(x1, y1, x2, y2):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="-|>", color=INK2, lw=0.9))
    box(0.1, 1.6, 1.9, 1.4, f"K1–K4 pool\n{len(meta)} features\n(K1 2039 · K2 30 · K3 30\nK4 2031 + 20)\n2264 leaves", bold=False)
    box(2.4, 1.6, 1.9, 1.4, "20 training sets\nV3: 10 plot-grouped folds\nV4: 10 × 30 % plot hold-out\n+ all leaves (reporting)")
    for i, (fam, txt) in enumerate((("Filter", "Filter (11)\nr · ANOVA F · Fisher · χ² · MI · ReliefF\nJ–M · mRMR · SPA · MC-UVE · CWT scalogram"),
                                     ("Wrapper", "Wrapper (6)\nSVM-RFE · RF-RFE · CARS\nSFFS (QDA) · SFFS (J–M) · GA"),
                                     ("Embedded", "Embedded (6) + ensemble\nRF · CART · Boruta · PLS-VIP\nLASSO · gradient boosting · Borda"))):
        box(4.7, 3.15 - i * 1.25, 3.0, 1.05, txt, fc=FAM[fam] + "33", ec=FAM[fam], fs=8)
    box(8.1, 1.6, 1.8, 1.4, "Top-k (5–20)\nplain vs redundancy-\ncontrolled (|r| < 0.95)\nselection inside the\ntraining set only")
    box(10.2, 2.65, 1.7, 1.1, "Held-out plots:\nQDA · LDA · RF\nbalanced accuracy")
    box(10.2, 1.3, 1.7, 1.1, "Stability (Kuncheva,\nJaccard ±10 nm)\nJ–M (all leaves)")
    box(4.7, 0.05, 7.2, 0.6, "Friedman + Nemenyi · Wilcoxon–Holm → composite ranking → consensus disease-specific features", fc="#e3f4ec", ec=H_COL)
    arr(2.0, 2.3, 2.4, 2.3)
    for i in range(3):
        arr(4.3, 2.3, 4.7, 3.65 - i * 1.25)
        arr(7.7, 3.65 - i * 1.25, 8.1, 2.3)
    arr(9.9, 2.5, 10.2, 3.2)
    arr(9.9, 2.1, 10.2, 1.85)
    arr(11.05, 1.3, 11.05, 0.65)
    save(fig, "FS01_workflow")


def fs02_score_spectra():
    sc = R["full_score"]
    U = R["univariate_all"]
    items = [("ANOVA F (= r, Fisher)", U["F"]), ("Chi-square", sc.get("Chi-square")), ("Mutual information", sc.get("Mutual information")),
             ("ReliefF", sc.get("ReliefF")), ("J–M (univariate)", U["jm"]), ("MC-UVE reliability", sc.get("MC-UVE")),
             ("RF importance", sc.get("RF importance")), ("Boruta mean importance", sc.get("Boruta")), ("PLS-VIP", sc.get("PLS-VIP")),
             ("Gradient boosting", sc.get("Gradient boosting"))]
    items = [(n, v) for n, v in items if v is not None and np.ndim(v) == 1 and len(v) == len(meta)]
    fig, axs = plt.subplots(len(items), 1, figsize=(10, 1.05 * len(items) + 0.6), sharex=True)
    for ax, (n, v) in zip(axs, items):
        v = np.asarray(v, float)
        v = np.where(np.isfinite(v), v, 0)
        v = v / np.nanmax(np.abs(v)) if np.nanmax(np.abs(v)) > 0 else v
        shade(ax)
        for s, col, lab in (("R", "#9a998f", "K1 reflectance"), ("D1", "#2a78d6", "K4 first derivative")):
            m = ser == s
            o = np.argsort(pos[m])
            ax.plot(pos[m][o], v[m][o], color=col, lw=0.9, label=lab)
        sc_m = ~np.isin(ser, ["R", "D1"])
        top = np.argsort(-v * sc_m)[:2]
        ax.text(2510, 0.55, "best scalar: " + ", ".join(meta["name"].iloc[top]), fontsize=6.5, color=INK2, va="center")
        ax.set_ylim(-0.05, 1.08)
        ax.set_yticks([0, 1])
        ax.text(405, 0.92, n, fontsize=8, fontweight="bold", va="top")
    axs[0].legend(loc="upper right", fontsize=7, ncol=2)
    axs[-1].set_xlabel("Wavelength (nm)")
    axs[-1].set_xlim(400, 2500)
    fig.suptitle("Where each method finds information (all leaves; score scaled to its maximum; grey = detector-join guard zones)",
                 fontsize=10, fontweight="bold", y=1.0)
    save(fig, "FS02_score_spectra")


def fs03_scalogram():
    cw = R["cwt"]
    sep = np.asarray(R["full_score"]["CWT scalogram"], float).reshape(cw["shape"])
    val = np.asarray(cw["valid"]).reshape(cw["shape"])
    sep = np.where(val, sep, np.nan)
    fig, ax = plt.subplots(figsize=(10, 3.2))
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("seq", SEQ)
    im = ax.imshow(sep, aspect="auto", cmap=cmap, extent=[cw["wl"][0], cw["wl"][-1], len(cw["scales"]) - 0.5, -0.5],
                   interpolation="nearest")
    ax.set_yticks(range(len(cw["scales"])), [f"{a}" for a in cw["scales"]])
    ax.set(xlabel="Wavelength (nm)", ylabel="Wavelet scale (nm)")
    ax.grid(False)
    full = R["full"].set_index("Method")
    S = full.loc["CWT scalogram", "idx"]
    nm = cw["names"][S]
    for t in nm:
        _, s, w = t.split()
        ax.plot(float(w), cw["scales"].index(int(s[1:])), marker="o", ms=6, mfc="none", mec=INK, mew=1.2)
    cb = fig.colorbar(im, ax=ax, pad=0.01)
    cb.set_label("J–M distance (0–2)")
    ax.set_title("CWT separability scalogram (Cheng et al. 2010 approach): J–M of each wavelet feature; ○ = top-10 selected (all leaves)")
    save(fig, "FS03_cwt_scalogram")


def fs04_ba_vs_k():
    s = R["summary"]
    s = s[s.Guard == "yes"]
    ref = R["fourtier_ref"].groupby("Method")["BA QDA"].mean()
    fams = ["Filter", "Wrapper", "Embedded"]
    fig, axs = plt.subplots(1, 3, figsize=(12, 3.8), sharey=True)
    for ax, fam in zip(axs, fams):
        ms = [m for m in dict.fromkeys(s.Method) if s[s.Method == m].Family.iloc[0] in (fam, "Ensemble" if fam == "Embedded" else "")]
        ms = [m for m in ms if m not in ("Pearson r", "Fisher score")]
        best = s[(s.k == 10) & s.Method.isin(ms)].set_index("Method")["BA QDA"].sort_values(ascending=False)
        for i, m in enumerate(best.index):
            q = s[s.Method == m].sort_values("k")
            col = FAM[q.Family.iloc[0]] if i < 3 or m == "Consensus (Borda)" else "#bdbcb5"
            lw = 2 if i < 3 or m == "Consensus (Borda)" else 1
            ax.plot(q.k, q["BA QDA"] * 100, color=col, lw=lw, marker="o", ms=3.5)
            if i < 3 or m == "Consensus (Borda)":
                ax.text(20.4, q["BA QDA"].iloc[-1] * 100, m, fontsize=7, color=INK, va="center")
        for lab, ls in (("Four-tier CART-13 (Part C)", ":"), ("Four-tier RF-17 (Part C)", "--")):
            ax.axhline(ref[lab] * 100, color=INK2, lw=0.8, ls=ls)
        ax.set_title(f"{fam} methods" + (" + consensus" if fam == "Embedded" else ""))
        ax.set_xticks(list((5, 10, 15, 20)))
        ax.set_xlim(4, 26)
        ax.set_xlabel("Features used (k)")
    axs[0].set_ylabel("QDA balanced accuracy on held-out plots (%)")
    axs[0].text(4.3, ref["Four-tier RF-17 (Part C)"] * 100 + 0.4, "four-tier RF-17 (dashed) / CART-13 (dotted)", fontsize=6.5, color=INK2)
    fig.suptitle("Accuracy vs number of features (redundancy-controlled top-k; mean of 20 held-out sets; best three of each family coloured)",
                 fontsize=10, fontweight="bold", y=1.02)
    save(fig, "FS04_ba_vs_k")


def fs05_accuracy():
    s = R["summary"]
    a = s[(s.k == 10) & (s.Guard == "yes")].set_index("Method")
    b = s[(s.k == 10) & (s.Guard == "no")].set_index("Method")
    o = a["BA QDA"].sort_values().index
    fig, ax = plt.subplots(figsize=(8, 7))
    yv = np.arange(len(o))
    for i, m in enumerate(o):
        ax.plot([b.loc[m, "BA QDA"] * 100, a.loc[m, "BA QDA"] * 100], [i, i], color=GRID, lw=2, zorder=1)
    ax.scatter(b.loc[o, "BA QDA"] * 100, yv, s=36, facecolor="white", edgecolor=INK2, zorder=2, label="QDA · plain top-10")
    ax.scatter(a.loc[o, "BA QDA"] * 100, yv, s=46, c=[FAM[a.loc[m, "Family"]] for m in o], edgecolor="white", lw=1.5, zorder=3,
               label="QDA · redundancy-controlled top-10")
    ax.scatter(a.loc[o, "BA RF"] * 100, yv, s=30, marker="D", facecolor="none", edgecolor=INK, lw=0.9, zorder=3, label="RF · redundancy-controlled top-10")
    ax.set_yticks(yv, o, fontsize=8)
    for t, m in zip(ax.get_yticklabels(), o):
        t.set_color(FAM[a.loc[m, "Family"]] if a.loc[m, "Family"] != "Filter" else "#1c5cab")
    ref = R["fourtier_ref"].groupby("Method")["BA QDA"].mean()
    ax.axvline(ref["Four-tier RF-17 (Part C)"] * 100, color=INK2, ls="--", lw=0.8)
    ax.text(ref["Four-tier RF-17 (Part C)"] * 100 + 0.2, -0.9, "four-tier RF-17", fontsize=7, color=INK2)
    ax.set_xlabel("Balanced accuracy on held-out plots (%, mean of 20)")
    ax.legend(handles=ax.get_legend_handles_labels()[0] + [Patch(color=c, label=f) for f, c in FAM.items()],
              fontsize=7, loc="lower right")
    ax.set_title("Ten features per method: accuracy of QDA and RF on new plots")
    save(fig, "FS05_accuracy_k10")


def fs06_stab_acc():
    s = R["summary"]
    a = s[(s.k == 10) & (s.Guard == "yes")].set_index("Method")
    st = R["stability"]
    st = st[st.Guard == "yes"].set_index("Method")
    ms = [m for m in a.index if m in st.index and m not in ("Pearson r", "Fisher score")]
    fig, ax = plt.subplots(figsize=(8.5, 5.4))
    for m in ms:
        x, yv = st.loc[m, "Jaccard (±10 nm)"], a.loc[m, "BA QDA"] * 100
        ax.scatter(x, yv, s=60, color=FAM[a.loc[m, "Family"]], edgecolor="white", lw=1.5, zorder=3)
        ax.annotate(m, (x, yv), xytext=(4, 3), textcoords="offset points", fontsize=7, color=INK)
    ax.set(xlabel="Stability: mean pairwise Jaccard of the 20 top-10 sets (±10 nm)", ylabel="QDA balanced accuracy (%), top-10")
    ax.legend(handles=[Patch(color=c, label=f) for f, c in FAM.items()], fontsize=7.5, loc="lower right")
    ax.set_title("Stable and informative: methods in the upper right are both accurate and reproducible")
    save(fig, "FS06_stability_vs_accuracy")


def fs07_cd():
    mr = R["mean_ranks"].set_index("Method")["Mean rank"].sort_values()
    cd = R["friedman"]["CD"]
    k = len(mr)
    fam = R["methods"].set_index("Method")["Family"]
    fig, ax = plt.subplots(figsize=(11, 0.28 * k + 1.8))
    ax.axis("off")
    lo, hi = 1, k
    ax.set_xlim(lo - 1.5, hi + 1.5)
    ax.set_ylim(-(k / 2) * 0.35 - 0.8, 1.2)
    ax.plot([lo, hi], [0, 0], color=INK, lw=1)
    for t in range(lo, hi + 1):
        ax.plot([t, t], [0, 0.12], color=INK, lw=0.8)
        ax.text(t, 0.2, str(t), ha="center", fontsize=7.5)
    ax.plot([lo, lo + cd], [0.85, 0.85], color=INK, lw=1.5)
    ax.text(lo + cd / 2, 0.95, f"CD = {cd:.2f}", ha="center", fontsize=8)
    names = list(mr.index)
    half = (k + 1) // 2
    for i, m in enumerate(names):
        r = mr[m]
        left = i < half
        yy = -0.35 * (i if left else (k - 1 - i)) - 0.4
        xe = lo - 0.6 if left else hi + 0.6
        ax.plot([r, r, xe], [0, yy, yy], color=FAM.get(fam.get(m, "Filter"), INK2), lw=0.9)
        ax.text(xe - 0.1 if left else xe + 0.1, yy, f"{m} ({r:.1f})", ha="right" if left else "left", va="center", fontsize=7.5)
    # cliques: maximal groups whose rank range < CD
    vals = mr.values
    cl = []
    for i in range(k):
        j = i
        while j + 1 < k and vals[j + 1] - vals[i] < cd:
            j += 1
        if j > i and not any(a <= i and j <= b for a, b in cl):
            cl.append((i, j))
    for n, (i, j) in enumerate(cl):
        yy = -0.12 - 0.09 * (n % 4)
        ax.plot([vals[i] - 0.05, vals[j] + 0.05], [yy, yy], color=INK, lw=3, solid_capstyle="round")
    ax.set_title(f"Critical-difference diagram (Friedman χ² = {R['friedman']['chi2']:.1f}, p = {R['friedman']['p']:.1e}; Nemenyi α = 0.05): "
                 "mean rank of QDA balanced accuracy over 20 held-out sets (1 = best); bars join methods not significantly different",
                 fontsize=9)
    save(fig, "FS07_cd_diagram")


def fs08_freq():
    Fq = R["consensus_freq"].set_index("Feature")
    cols = [c for c in Fq.columns if c not in ("Consensus score", "Methods ≥ 50 %")]
    M = Fq[cols].T.iloc[:, :20]
    fig, ax = plt.subplots(figsize=(11, 0.32 * len(cols) + 1.6))
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("seq", SEQ)
    im = ax.imshow(M.values, aspect="auto", cmap=cmap, vmin=0, vmax=1)
    ax.set_xticks(range(M.shape[1]), M.columns, rotation=60, ha="right", fontsize=7.5)
    ax.set_yticks(range(len(cols)), cols, fontsize=7.5)
    ax.grid(False)
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            v = M.values[i, j]
            if v >= 0.5:
                ax.text(j, i, f"{v:.1f}"[1:] if v < 1 else "1", ha="center", va="center", fontsize=6, color="white" if v > 0.7 else INK)
    cb = fig.colorbar(im, ax=ax, pad=0.01)
    cb.set_label("Share of the 20 training sets in which the feature (±10 nm) was in the top-10")
    ax.set_title("Which features do the methods agree on? Selection frequency of the 20 consensus features (ordered by consensus score)")
    save(fig, "FS08_selection_frequency")


def fs09_consensus_spectrum():
    spec = D["spec"]
    y = D["y"]
    m = ~spec.excluded
    wl = spec.wl[m]
    cons = R["consensus"].head(15)
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(10, 5.6), sharex=True)
    for c, col, lab in ((0, H_COL, "healthy"), (1, D_COL, "diseased")):
        a1.plot(wl, spec.R[y == c][:, m].mean(0), color=col, lw=1.4, label=lab)
        a2.plot(wl, spec.D1[y == c][:, m].mean(0) * 1000, color=col, lw=1.2, label=lab)
    for ax in (a1, a2):
        shade(ax)
    for _, r in cons.iterrows():
        w = r["Wavelength (nm)"]
        if not np.isfinite(w):
            continue
        ax = a2 if r["Feature"].startswith("D1") else a1
        ax.axvline(w, color=INK, lw=0.7, ls=":")
        ax.text(w, ax.get_ylim()[1], r["Feature"].replace("D1_", ""), rotation=90, fontsize=6.5, va="top", ha="right")
    sc = cons[~np.isfinite(cons["Wavelength (nm)"].astype(float))]["Feature"].tolist()
    a1.set_ylabel("Reflectance")
    a2.set_ylabel("First derivative (×10⁻³ nm⁻¹)")
    a2.set_xlabel("Wavelength (nm)")
    a1.legend(fontsize=8, loc="upper right")
    a1.set_title("Consensus features on the mean spectra" + (f" · scalar features: {', '.join(sc)}" if sc else ""))
    save(fig, "FS09_consensus_on_spectrum")


def fs10_composite():
    c = R["composite"].sort_values("Mean rank", ascending=False)
    fig, ax = plt.subplots(figsize=(8, 6.4))
    ax.barh(c["Method"], c["Mean rank"], color=[FAM[f] for f in c["Family"]], height=0.65)
    for i, (_, r) in enumerate(c.iterrows()):
        ax.text(r["Mean rank"] + 0.15, i, f"{r['Mean rank']:.1f}", va="center", fontsize=7.5)
    ax.set_xlabel("Mean rank over accuracy (QDA, RF), stability and J–M (lower = better)")
    ax.grid(axis="y", visible=False)
    ax.legend(handles=[Patch(color=v, label=k) for k, v in FAM.items()], fontsize=7.5, loc="lower right")
    ax.set_title("Composite ranking of the feature-selection methods")
    save(fig, "FS10_composite_ranking")


def fs11_runtime():
    rt = R["runtime"].dropna(subset=["Mean seconds per training set"])
    rt = rt[~rt.Method.isin(["Pearson r", "Fisher score", "Consensus (Borda)"])].sort_values("Mean seconds per training set")
    fig, ax = plt.subplots(figsize=(7.5, 5.2))
    ax.barh(rt["Method"], rt["Mean seconds per training set"].clip(lower=0.01), color=[FAM[f] for f in rt["Family"]], height=0.65)
    ax.set_xscale("log")
    ax.set_xlabel("Seconds per training set (≈ 2000 leaves × 4150 features, one CPU core; log scale)")
    ax.grid(axis="y", visible=False)
    ax.set_title("Computing cost of each method")
    save(fig, "FS11_runtime")


def fs12_search():
    fs = R["full_sffs"]
    fig, axs = plt.subplots(1, 3, figsize=(12, 3.2))
    for lab, col in (("SFFS (QDA)", FAM["Wrapper"]),):
        crit = fs[lab][1]
        ks = sorted(crit)
        axs[0].plot(ks, [crit[k] * 100 for k in ks], color=col, marker="o", ms=3)
    axs[0].set(xlabel="Subset size", ylabel="Inner-CV QDA balanced accuracy (%)", title="SFFS (QDA): criterion by subset size")
    crit = fs["SFFS (J–M)"][1]
    ks = sorted(crit)
    axs[1].plot(ks, [crit[k] for k in ks], color=FAM["Wrapper"], marker="o", ms=3)
    axs[1].axhline(1.9, color=INK2, ls="--", lw=0.8)
    axs[1].set(xlabel="Subset size", ylabel="J–M (0–2)", title="SFFS (J–M): separability by subset size")
    if R.get("ga_hist"):
        axs[2].plot(np.arange(1, len(R["ga_hist"]) + 1), np.array(R["ga_hist"]) * 100, color=FAM["Wrapper"])
        axs[2].set(xlabel="Generation", ylabel="Best fitness (×100)", title="Genetic algorithm: best fitness")
    save(fig, "FS12_wrapper_search")
    if R.get("cars_sizes"):
        fig, ax = plt.subplots(figsize=(5, 3))
        ax.plot(np.arange(1, len(R["cars_sizes"]) + 1), R["cars_sizes"], color=FAM["Wrapper"], marker="o", ms=3)
        ax.set_yscale("log")
        ax.set(xlabel="Sampling run", ylabel="Variables kept (log)", title="CARS: exponentially decreasing variable set")
        b = R["full_info"]["CARS"]["best run"]
        ax.axvline(b, color=INK2, ls="--", lw=0.8)
        ax.text(b + 0.5, R["cars_sizes"][0] / 2, f"best run {b}\n({R['cars_sizes'][b - 1]} variables)", fontsize=7.5)
        save(fig, "FS13_cars")


def fs14_positions():
    full = R["full"]
    full = full[~full.Method.isin(["Pearson r", "Fisher score"])]
    fig, ax = plt.subplots(figsize=(11, 0.32 * len(full) + 1.2))
    shade(ax)
    for i, (_, r) in enumerate(full.iloc[::-1].iterrows()):
        if r["space"] == "cwt":
            names = r["Selected (top-10, redundancy-controlled)"].split(", ")
            ws = [float(n.split()[-1]) for n in names]
            ax.scatter(ws, [i] * len(ws), marker="s", s=22, color=FAM[r["Family"]], edgecolor="white", lw=0.5, zorder=3)
            continue
        idx = r["idx"]
        for j in idx:
            if np.isfinite(pos[j]):
                ax.scatter(pos[j], i, marker="o" if ser[j] == "R" else "^", s=26, color=FAM[r["Family"]], edgecolor="white", lw=0.6, zorder=3)
        sc = [meta["name"].iloc[j] for j in idx if not np.isfinite(pos[j])]
        if sc:
            ax.text(2530, i, ", ".join(s.replace(" water ", " ") for s in sc), fontsize=6, va="center", color=INK2)
    ax.set_yticks(range(len(full)), full["Method"].iloc[::-1], fontsize=7.5)
    ax.set_xlim(400, 2500)
    ax.set_xlabel("Wavelength (nm)   ● K1 reflectance   ▲ K4 first derivative   ■ CWT feature   (scalar features listed on the right)")
    ax.set_title("Top-10 features chosen by each method on all leaves (redundancy-controlled)")
    save(fig, "FS14_selected_positions")


def fs15_guard():
    g = R["guard_effect"].dropna()
    g = g[~g.Method.isin(["Pearson r", "Fisher score"])].sort_values("Difference")
    fig, ax = plt.subplots(figsize=(7.5, 5.8))
    yv = np.arange(len(g))
    for i, (_, r) in enumerate(g.iterrows()):
        ax.plot([r["Plain top-10"] * 100, r["Redundancy-controlled top-10"] * 100], [i, i], color=GRID, lw=2.5, zorder=1)
    ax.scatter(g["Plain top-10"] * 100, yv, s=36, facecolor="white", edgecolor=INK2, zorder=2, label="plain top-10")
    ax.scatter(g["Redundancy-controlled top-10"] * 100, yv, s=40, color="#2a78d6", zorder=3, label="redundancy-controlled (|r| < 0.95)")
    ax.set_yticks(yv, g["Method"], fontsize=8)
    ax.set_xlabel("QDA balanced accuracy (%), mean of 20 held-out sets")
    ax.legend(fontsize=7.5, loc="lower right")
    ax.set_title("Effect of removing near-duplicate features from a ranking")
    save(fig, "FS15_redundancy_control")


if __name__ == "__main__":
    for f in (fs01_workflow, fs02_score_spectra, fs03_scalogram, fs04_ba_vs_k, fs05_accuracy, fs06_stab_acc, fs07_cd, fs08_freq,
              fs09_consensus_spectrum, fs10_composite, fs11_runtime, fs12_search, fs14_positions, fs15_guard):
        f()
    print(len(done), "figures:", done)
