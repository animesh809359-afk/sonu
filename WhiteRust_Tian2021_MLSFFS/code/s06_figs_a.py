"""Figures of the data-preparation and feature-selection steps (Steps 1-5)."""
import sys, pickle, numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import FancyBboxPatch
sys.path.insert(0, ".")
from mlsffs import *

S = sys.argv[1]
FIG = f"{S}/figs"
import os; os.makedirs(FIG, exist_ok=True)
c = pickle.load(open(f"{S}/out/cache.pkl", "rb"))
feats, y, _ = pickle.load(open(f"{S}/out/feats.pkl", "rb"))
P = pickle.load(open(f"{S}/out/pool_full.pkl", "rb"))
PH = pickle.load(open(f"{S}/out/physio.pkl", "rb"))

H_COL, D_COL = "#2a78d6", "#eb6834"           # healthy / diseased (categorical slots 1-2)
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
SEQ = LinearSegmentedColormap.from_list("seqblue", ["#fcfcfb", "#cde2fb", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"])
DATE_COL = ["#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
                     "savefig.dpi": 200, "savefig.bbox": "tight", "legend.frameon": False})


def save(fig, name):
    fig.savefig(f"{FIG}/{name}.png", facecolor="white")
    plt.close(fig)


# ---- Fig 1: workflow (analogue of Tian et al. 2021 Fig. 2)
fig, ax = plt.subplots(figsize=(7.2, 9.4)); ax.axis("off"); ax.set_xlim(0, 10); ax.set_ylim(0, 22)
def box(x, y_, w, h, txt, fc="#eef4fc", ec="#3987e5", fs=8.5, bold=False):
    ax.add_patch(FancyBboxPatch((x, y_), w, h, boxstyle="round,pad=0.08,rounding_size=0.25", fc=fc, ec=ec, lw=1.2))
    ax.text(x + w / 2, y_ + h / 2, txt, ha="center", va="center", fontsize=fs, color=INK, wrap=True,
            fontweight="bold" if bold else "normal")
def arrow(y0, y1, x=5):
    ax.annotate("", (x, y1), (x, y0), arrowprops=dict(arrowstyle="-|>", color=INK2, lw=1.2))
box(0.5, 20.4, 9, 1.2, "Plot-average raw reflectance (350–2500 nm) of 48 plots × 4 dates (T1–T4)\n12 controls vs 36 inoculated plots (3 varieties × 4 inoculation timings × 3 reps)", fc="#fdf0ea", ec="#eb6834", bold=True, fs=8)
arrow(20.4, 19.7)
box(0.5, 17.6, 9, 2.0, "STEP 1  Data preparation & quality control\nlabel/plot consistency · exclusion of 350–399, 2401–2500 nm and detector-join guard zones\n(990–1010, 1795–1835 nm) · CWT (Mexican hat, scales 2³–2⁸) · duplicate features · confounds")
arrow(17.6, 16.9)
box(0.5, 15.5, 9, 1.3, "STEP 2  Physiological interpretation (proxy indices for Chl, Car, Anth, water)\nmedian ± 3 MAD outliers · Shapiro–Wilk & Levene → t-test or Mann–Whitney U · BH-FDR")
arrow(15.5, 14.8)
box(0.5, 12.2, 9, 2.5, "STEP 3  Spectral separability (thresholding, Mahlein et al. 2013)\n100 thresholds between class means Mi and Mh → best balanced accuracy\nCandidate features: R(λ) · D1–D3(λ) · CWT(scale, λ) · 87 VIs · 48 CR · 23 red-edge\n→ classification scalograms per date")
arrow(12.2, 11.5)
box(0.5, 9.1, 9, 2.3, "STEP 4  Disease-specific spectral features (DSSFs)\nspectral families: top 5 % per date → common to k* dates → 1 representative per region\nscalar families: top 10 % per date → union over dates · exact duplicates removed")
arrow(9.1, 8.4)
box(0.5, 7.1, 9, 1.2, "STEP 5  Collinearity reduction: iterative VIF < 10 (relevance-aware)")
arrow(7.1, 6.4)
box(0.5, 3.3, 9, 3.0, "STEP 6  ML-SFFS classification (Pudil et al. 1994)\ncriterion classifiers LDA · k-NN (k = 3) · SVM-RBF (grid search C, γ)\nA  paper-faithful: 4-fold CV × 100 repetitions, OA criterion → OA, OFC\nB  corrected: nested CV (pipeline re-run in every outer fold), balanced accuracy\nC  permutation null of A (labels shuffled, whole pipeline repeated)\nD  infection stage: controls vs each inoculation timing D1–D4 at T1–T4", fs=8.2)
arrow(3.3, 2.8)
box(0.5, 1.2, 9, 1.5, "STEP 7  Evaluation & cross-checks\nOA · BA · κ · sensitivity · specificity · OFC frequency · SVM-SFFS vs SVM-all", fc="#e8f6ef", ec="#1baf7a", bold=False)
save(fig, "fig01_workflow")

# ---- Fig 2: mean spectra by class per date
fig, axs = plt.subplots(2, 2, figsize=(9, 6.2), sharex=True, sharey=True)
for ax, d in zip(axs.flat, DATES):
    R = c[d]["R"]; m = c[d]["meta"]; h = (m.Class == "Healthy").values
    wl = np.array(R.columns)
    for msk, col, lab in [(h, H_COL, "Healthy (n = 12)"), (~h, D_COL, "Diseased (n = 36)")]:
        mu, sd = R[msk].mean().values, R[msk].std().values
        ax.fill_between(wl, mu - sd, mu + sd, color=col, alpha=0.18, lw=0)
        ax.plot(wl, mu, color=col, lw=1.4, label=lab)
    for a, b in GUARDS + [(350, 399), (2401, 2500)]:
        ax.axvspan(a, b, color="#d9d8d3", alpha=0.6, lw=0)
    ax.set_title(DLAB[d], fontsize=10, color=INK, loc="left")
axs[0, 0].legend(loc="upper right")
for ax in axs[1]: ax.set_xlabel("Wavelength (nm)")
for ax in axs[:, 0]: ax.set_ylabel("Reflectance")
fig.suptitle("Plot-average reflectance (mean ± 1 SD); grey = excluded edges and detector-join guard zones", fontsize=9.5, color=INK2, x=0.02, ha="left")
save(fig, "fig02_mean_spectra")

# ---- Fig 3: thresholding concept (analogue of Tian et al. Fig. 3) for the best pool feature on D3
d = DATES[2]
best = P["sep"][(d, "VI")].BA.idxmax()
v = feats[d]["VI"][best].values; yy = y[d]
s = P["sep"][(d, "VI")].loc[best]
fig, ax = plt.subplots(figsize=(6.4, 3.6))
idx = np.arange(1, 49)
ax.scatter(idx[yy == 1], v[yy == 1], s=26, color=D_COL, edgecolor="white", lw=0.8, label="Diseased", zorder=3)
ax.scatter(idx[yy == 0], v[yy == 0], s=26, color=H_COL, edgecolor="white", lw=0.8, label="Healthy", zorder=3)
ax.axhline(s.Mi, color=D_COL, ls="--", lw=1); ax.text(49.5, s.Mi, "Mi", color=INK2, va="center")
ax.axhline(s.Mh, color=H_COL, ls="--", lw=1); ax.text(49.5, s.Mh, "Mh", color=INK2, va="center")
ax.axhline(s.threshold, color=INK, lw=1.2); ax.text(30, s.threshold, f"optimal threshold (BA = {s.BA:.3f}, OA = {s.OA:.3f})", color=INK, va="bottom", ha="center", fontsize=8, bbox=dict(fc="white", ec="none", pad=1.5))
ax.set_xlabel("Plot number"); ax.set_ylabel(best); ax.legend(loc="best")
ax.set_title(f"Thresholding separability of {best} on {DLAB[d]}", loc="left", fontsize=10)
save(fig, "fig03_threshold_concept")

# ---- Fig 4: scalograms for R, D1, D2, D3 (analogue of Tian et al. Fig. 6)
for f in ["R", "D1", "D2", "D3"]:
    names = P["sep"][(DATES[0], f)].index
    wl = np.array([int(n.split("_")[1]) for n in names])
    full = np.arange(400, 2401)
    M = np.full((6, len(full)), np.nan); TOP = np.zeros((6, len(full)), bool)
    for i, d in enumerate(DATES):
        ba = P["sep"][(d, f)].BA.values
        M[i, wl - 400] = ba
        TOP[i, wl - 400] = top_fraction(ba, 0.05)
    cnt = P["consistency"][f].values
    M[4, wl - 400] = cnt / 4.0
    lev = P["level"][f]
    TOP[4, wl - 400] = cnt >= lev
    reps = [r for r in P["reps"].itertuples() if r.family == f]
    fig, ax = plt.subplots(figsize=(9.5, 2.9))
    show = M.copy(); show[5] = np.nan
    im = ax.imshow(show[:5], aspect="auto", cmap=SEQ, vmin=0.5, vmax=1.0, extent=[399.5, 2400.5, 4.5, -0.5], interpolation="nearest")
    for i in range(5):
        xs = full[TOP[i]]
        ax.scatter(xs, np.full(len(xs), i), marker="|", s=40, color=D_COL, lw=1.0)
    for r in reps:
        ax.scatter(int(r.feature.split("_")[1]), 4, marker="v", s=40, color=INK, zorder=5)
    for a, b in GUARDS:
        ax.axvspan(a, b, color="#d9d8d3", lw=0)
    ax.set_yticks(range(5)); ax.set_yticklabels([DLAB[d] for d in DATES] + [f"common (≥{lev} dates)"])
    ax.grid(False); ax.set_xlabel("Wavelength (nm)")
    cb = fig.colorbar(im, ax=ax, pad=0.01, fraction=0.03); cb.set_label("Balanced accuracy", fontsize=8)
    ax.set_title(f"Classification scalogram – {FAM_NAME[f]} (orange ticks = top 5 % per date; ▼ = region representative)", loc="left", fontsize=9.5)
    save(fig, f"fig04_scalogram_{f}")

# ---- Fig 5: CWT scalograms (analogue of Tian et al. Fig. 7)
names = P["sep"][(DATES[0], "CWT")].index
sc = np.array([int(n.split("_")[0][1:]) for n in names]); wl = np.array([int(n.split("_")[1]) for n in names])
full = np.arange(400, 2401)
fig, axs = plt.subplots(5, 1, figsize=(9.5, 8.6), sharex=True)
for i, d in enumerate(DATES + ["common"]):
    G = np.full((len(CWT_KEEP), len(full)), np.nan)
    ax = axs[i]
    if d != "common":
        ba = P["sep"][(d, "CWT")].BA.values
        G[sc - 3, wl - 400] = ba
        top = top_fraction(ba, 0.05)
        title = DLAB[d]
    else:
        cnt = P["consistency"]["CWT"].values
        G[sc - 3, wl - 400] = cnt / 4
        top = cnt >= P["level"]["CWT"]
        title = f"common to ≥{P['level']['CWT']} dates (shade = share of dates in top 5 %)"
    im = ax.imshow(G, aspect="auto", cmap=SEQ, vmin=0.5 if d != "common" else 0, vmax=1, extent=[399.5, 2400.5, 8.5, 2.5], interpolation="nearest")
    if d == DATES[0]:
        im_date = im
    ax.scatter(wl[top], sc[top], marker="s", s=3, color=D_COL, lw=0)
    if d == "common":
        for r in P["reps"].itertuples():
            if r.family == "CWT":
                ax.scatter(int(r.feature.split("_")[1]), int(r.feature.split("_")[0][1:]), marker="v", s=36, color=INK, zorder=5)
    for a, b in GUARDS:
        ax.axvspan(a, b, color="#d9d8d3", lw=0)
    ax.set_ylabel("Scale"); ax.set_yticks(CWT_KEEP); ax.grid(False)
    ax.set_title(title, loc="left", fontsize=9)
axs[-1].set_xlabel("Wavelength (nm)")
cb = fig.colorbar(im_date, ax=axs[:4], pad=0.01, fraction=0.02); cb.set_label("Balanced accuracy (date panels)", fontsize=8)
cb2 = fig.colorbar(im, ax=axs[4], pad=0.01, fraction=0.02); cb2.set_label("Share of dates", fontsize=7)
fig.suptitle("Wavelet (CWT, Mexican hat) classification scalograms; orange = top 5 % per date; ▼ = representative", x=0.02, y=0.93, ha="left", fontsize=10)
save(fig, "fig05_scalogram_CWT")

# ---- Fig 6: physiological proxies (analogue of Tian et al. Fig. 4)
T = PH["proxy"]; RAW = PH["proxy_raw"]
proxies = list(dict.fromkeys(T.proxy))
fig, axs = plt.subplots(2, 4, figsize=(11, 5.6))
for ax, pr in zip(axs.flat, proxies):
    pos = []
    for i, d in enumerate(DATES):
        for j, (cl, col) in enumerate([("Healthy", H_COL), ("Diseased", D_COL)]):
            v = RAW[(RAW.date == d) & (RAW.proxy == pr) & (RAW.Class == cl)].value.values
            p = i * 3 + j
            bp = ax.boxplot(v, positions=[p], widths=0.75, patch_artist=True, showfliers=True,
                            medianprops=dict(color=INK, lw=1), flierprops=dict(marker="o", ms=2.5, mfc=col, mec=col),
                            whiskerprops=dict(color=INK2), capprops=dict(color=INK2), boxprops=dict(color=INK2))
            bp["boxes"][0].set_facecolor(col); bp["boxes"][0].set_alpha(0.85)
        q = T[(T.date == d) & (T.proxy == pr)].q_BH.values[0]
        star = "***" if q < 0.001 else "**" if q < 0.01 else "*" if q < 0.05 else "ns"
        ax.text(i * 3 + 0.5, 1.02, star, transform=ax.get_xaxis_transform(), ha="center", fontsize=8, color=INK)
    ax.set_xticks([i * 3 + 0.5 for i in range(4)]); ax.set_xticklabels(["T1", "T2", "T3", "T4"])
    short = pr if len(pr) < 20 else "REIP (4-point)"
    ax.set_title(f"{short}\n({T[T.proxy == pr].constituent.iloc[0]})", fontsize=8.5, loc="left", pad=12)
axs[0, 0].legend([plt.Rectangle((0, 0), 1, 1, fc=H_COL), plt.Rectangle((0, 0), 1, 1, fc=D_COL)], ["Healthy", "Diseased"], loc="lower left", fontsize=7.5)
fig.tight_layout()
save(fig, "fig06_physiology_boxplots")

# ---- Fig 7: VIF of the final pool and relevance
last = P["vif_log"][-1]["vif"]
r = P["reps"].set_index("feature")
pool = P["pool"]
short = lambda n: (n.replace(" water absorption", "").replace(" red absorption", "").replace(" blue absorption", "")
                   .replace(" (nm)", "").replace(" (1/nm)", "")[:42])
fig, ax = plt.subplots(figsize=(7.5, 5))
yy_ = np.arange(len(pool))
ax.barh(yy_, [last[n] for n in pool], color="#3987e5", height=0.6)
ax.axvline(10, color=D_COL, lw=1.2, ls="--"); ax.text(10.1, len(pool) - 0.5, "VIF = 10", color=INK2, fontsize=8)
ax.set_yticks(yy_); ax.set_yticklabels([f"F{i + 1}  {short(n)}" for i, n in enumerate(pool)], fontsize=7.5)
ax.invert_yaxis(); ax.set_xlabel("Variance inflation factor (final pool)")
ax.set_title(f"Collinearity reduction: {len(P['pool_pre_vif'])} candidate DSSFs → {len(pool)} with VIF < 10", loc="left", fontsize=10)
save(fig, "fig07_vif")
print("figures A done")
