"""Figures of the classification steps (Step 6)."""
import sys, pickle, numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
sys.path.insert(0, ".")
from mlsffs import *

S = sys.argv[1]; FIG = f"{S}/figs"; O = f"{S}/out"
T = pickle.load(open(f"{O}/tables.pkl", "rb"))
feats, y, _ = pickle.load(open(f"{O}/feats.pkl", "rb"))
H_COL, D_COL = "#2a78d6", "#eb6834"
CLF_COL = {"LDA": "#2a78d6", "kNN": "#eb6834", "SVM": "#1baf7a"}
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
SEQ = LinearSegmentedColormap.from_list("seqblue", ["#fcfcfb", "#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"])
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
                     "savefig.dpi": 200, "savefig.bbox": "tight", "legend.frameon": False})
TL = [DLAB[d] for d in DATES]
XT = [t.split(" ")[0] for t in TL]


def save(fig, name):
    fig.savefig(f"{FIG}/{name}.png", facecolor="white"); plt.close(fig)


# ---- Fig 8: SFFS vs all DSSFs (analogue of Tian et al. Fig. 8), faithful (A) and nested (B)
fa = T["sffs_vs_all"]; ne = T["nested"]
fig, axs = plt.subplots(1, 3, figsize=(11, 3.4), sharey=True)
for ax, clf in zip(axs, ["LDA", "kNN", "SVM"]):
    a = fa[fa.Classifier == clf]; b = ne[ne.Classifier == clf]
    x = np.arange(4)
    ax.plot(x, 100 * a["SFFS OA"], "-o", color=CLF_COL[clf], lw=2, ms=6, label=f"{clf}-SFFS (A, faithful)")
    ax.plot(x, 100 * a["All-DSSF OA"], "--o", color=CLF_COL[clf], lw=1.4, ms=5, mfc="white", label=f"{clf}-all (A)")
    ax.plot(x, 100 * b["OA"], "-s", color=INK, lw=1.6, ms=5, label=f"{clf}-SFFS (B, nested)")
    ax.plot(x, 100 * b["All-DSSF OA"], "--s", color=INK2, lw=1.2, ms=4, mfc="white", label=f"{clf}-all (B)")
    ax.axhline(75, color=INK2, lw=0.8, ls=":"); ax.text(3.05, 75.5, "majority class", fontsize=7, color=INK2, ha="right")
    ax.set_xticks(x); ax.set_xticklabels(XT); ax.set_title(clf, loc="left", fontsize=10)
    ax.set_ylim(70, 101); ax.legend(fontsize=7, loc="lower right")
axs[0].set_ylabel("Overall accuracy (%)")
fig.suptitle("Classification with SFFS-selected features vs all DSSFs (A = paper-faithful CV; B = nested CV)", x=0.01, ha="left", fontsize=10)
fig.tight_layout(); save(fig, "fig08_sffs_vs_all")

# ---- Fig 9: A vs B vs permutation null (key correction figure)
pm = T.get("perm")
fig, axs = plt.subplots(1, 3, figsize=(11, 3.5), sharey=True)
for ax, clf in zip(axs, ["LDA", "kNN", "SVM"]):
    f_ = T["faithful"][T["faithful"].Classifier == clf]; n_ = ne[ne.Classifier == clf]
    x = np.arange(4)
    if pm is not None and len(pm[pm.Classifier == clf]):
        p_ = pm[pm.Classifier == clf]
        ax.fill_between(x, 100 * p_["Null BA mean"], 100 * p_["Null BA max"], color="#d9d8d3", alpha=0.8, lw=0, label="A with random labels (BA, mean–max)")
    ax.plot(x, 100 * f_["Mean BA"], "-o", color=D_COL, lw=2, ms=6, label="A: paper-faithful BA")
    ax.errorbar(x, 100 * n_["BA"], yerr=100 * n_["SD BA"], fmt="-s", color=H_COL, lw=2, ms=6, capsize=3, label="B: nested-CV BA (± SD)")
    ax.axhline(50, color=INK2, lw=0.8, ls=":"); ax.text(0, 51, "chance", fontsize=7, color=INK2)
    ax.set_xticks(x); ax.set_xticklabels(XT); ax.set_title(clf, loc="left", fontsize=10); ax.set_ylim(45, 102)
axs[0].set_ylabel("Balanced accuracy (%)"); axs[0].legend(fontsize=7, loc="lower left")
fig.suptitle("Optimism of the paper-faithful estimate: faithful (A) vs nested CV (B) vs permutation null (C)", x=0.01, ha="left", fontsize=10)
fig.tight_layout(); save(fig, "fig09_faithful_vs_nested_vs_null")

# ---- Fig 10: selection frequency of the DSSFs (faithful)
fr = T["faithful_freq"]
codes_ = [T["code"][n] for n in T["pool"]]
M = fr[codes_].values
fig, ax = plt.subplots(figsize=(9.5, 4.2))
im = ax.imshow(M, cmap=SEQ, vmin=0, vmax=100, aspect="auto")
ax.set_xticks(range(len(codes_))); ax.set_xticklabels(codes_)
ax.set_yticks(range(len(fr))); ax.set_yticklabels([f"{d.split(' ')[0]} · {c_}" for d, c_ in zip(fr.Date, fr.Classifier)], fontsize=8)
for i in range(M.shape[0]):
    for j in range(M.shape[1]):
        if M[i, j] >= 1:
            ax.text(j, i, f"{M[i, j]:.0f}", ha="center", va="center", fontsize=6.5, color="white" if M[i, j] > 60 else INK)
ax.grid(False); cb = fig.colorbar(im, ax=ax, pad=0.01); cb.set_label("Selected in % of 100 repetitions", fontsize=8)
ax.set_title("How often each DSSF entered the optimal feature combination (procedure A)", loc="left", fontsize=10)
save(fig, "fig10_selection_frequency")

# ---- Fig 11: permutation null distributions (LDA, kNN)
if pm is not None:
    raw = T["perm_raw"]
    fig, axs = plt.subplots(1, 4, figsize=(11, 3.1), sharey=True)
    for ax, d in zip(axs, DATES):
        for k, clf in enumerate(["LDA", "kNN", "SVM"]):
            g = raw[(raw.date == d) & (raw.clf == clf)]
            if not len(g): continue
            null = g.groupby("perm").OA.mean().values * 100
            ax.scatter(np.full(len(null), k) + np.random.default_rng(1).uniform(-0.15, 0.15, len(null)), null, s=14, color="#9c9b96", lw=0)
            obs = T["faithful"][(T["faithful"].Date == DLAB[d]) & (T["faithful"].Classifier == clf)]["Mean OA"].iloc[0] * 100
            ax.scatter([k], [obs], marker="D", s=40, color=CLF_COL[clf], zorder=5)
        ax.axhline(75, color=INK2, lw=0.8, ls=":")
        ax.set_xticks([0, 1, 2]); ax.set_xticklabels(["LDA", "kNN", "SVM"]); ax.set_title(DLAB[d], loc="left", fontsize=9)
    axs[0].set_ylabel("OA of procedure A (%)")
    fig.suptitle("Permutation null (grey = whole pipeline re-run with shuffled plot labels) vs observed OA (◆); dotted = 75 % majority class",
                 x=0.01, ha="left", fontsize=9)
    fig.tight_layout(); save(fig, "fig11_permutation_null")

# ---- Fig 12: stage-wise analysis
if "stageA" in T:
    sa = T["stageA"]; sd = T["stage_detection"]
    fig, axs = plt.subplots(1, 2, figsize=(11, 3.6), gridspec_kw=dict(wspace=0.45))
    piv = sa[sa.Classifier == "SVM"].pivot_table(index="Inoculation timing", columns="Date", values="Mean OA", observed=True) * 100
    im = axs[0].imshow(piv.values, cmap=SEQ, vmin=50, vmax=100, aspect="auto")
    for i in range(piv.shape[0]):
        for j in range(piv.shape[1]):
            axs[0].text(j, i, f"{piv.values[i, j]:.1f}", ha="center", va="center", fontsize=8, color="white" if piv.values[i, j] > 85 else INK)
    axs[0].set_xticks(range(4)); axs[0].set_xticklabels(XT); axs[0].set_yticks(range(4)); axs[0].set_yticklabels([f"C vs {g}" for g in piv.index])
    axs[0].grid(False); axs[0].set_title("A: SVM-SFFS OA (%), paper-faithful", loc="left", fontsize=9.5)
    fig.colorbar(im, ax=axs[0], pad=0.02, fraction=0.05).set_label("OA (%)", fontsize=8)
    q = sd[(sd.Classifier == "SVM")].pivot_table(index="Group", columns="Date", values="Called diseased (%)", observed=True)
    q = q.loc[["Control", "D1", "D2", "D3", "D4"]]
    im2 = axs[1].imshow(q.values, cmap=SEQ, vmin=0, vmax=100, aspect="auto")
    for i in range(q.shape[0]):
        for j in range(q.shape[1]):
            axs[1].text(j, i, f"{q.values[i, j]:.0f}", ha="center", va="center", fontsize=8, color="white" if q.values[i, j] > 60 else INK)
    axs[1].set_xticks(range(4)); axs[1].set_xticklabels(XT); axs[1].set_yticks(range(5))
    axs[1].set_yticklabels(["Control", "D1", "D2", "D3", "D4"])
    axs[1].grid(False); axs[1].set_title("B: % called 'diseased', nested CV, SVM\n(control row = false alarms; D rows = detection)", loc="left", fontsize=9)
    fig.colorbar(im2, ax=axs[1], pad=0.02, fraction=0.05).set_label("%", fontsize=8)
    save(fig, "fig12_stage_wise")

# ---- Fig 13: most frequently selected DSSFs by class and date
fr_tot = T["faithful_freq"][codes_].mean().sort_values(ascending=False)
top = list(fr_tot.index[:4])
inv = {v: k for k, v in T["code"].items()}
fig, axs = plt.subplots(1, 4, figsize=(11, 3.2))
for ax, code in zip(axs, top):
    n = inv[code]
    for i, d in enumerate(DATES):
        X = pd.concat([feats[d][f] for f in feats[d]], axis=1)[n].values
        for j, (cl, col) in enumerate([(0, H_COL), (1, D_COL)]):
            v = X[y[d] == cl]
            bp = ax.boxplot(v, positions=[i * 3 + j], widths=0.75, patch_artist=True, medianprops=dict(color=INK, lw=1),
                            flierprops=dict(marker="o", ms=2.5, mfc=col, mec=col), whiskerprops=dict(color=INK2),
                            capprops=dict(color=INK2), boxprops=dict(color=INK2))
            bp["boxes"][0].set_facecolor(col); bp["boxes"][0].set_alpha(0.85)
    ax.set_xticks([i * 3 + 0.5 for i in range(4)]); ax.set_xticklabels(XT)
    ax.set_title(f"{code}: {n[:34]}", loc="left", fontsize=8.5)
    ax.ticklabel_format(axis="y", style="sci", scilimits=(-3, 4))
axs[0].legend([plt.Rectangle((0, 0), 1, 1, fc=H_COL), plt.Rectangle((0, 0), 1, 1, fc=D_COL)], ["Healthy", "Diseased"], fontsize=7.5, loc="best")
fig.suptitle("The four most frequently selected DSSFs (procedure A, all classifiers and dates)", x=0.01, ha="left", fontsize=10)
fig.tight_layout(); save(fig, "fig13_top_dssf_boxplots")
print("figures B done", top)
