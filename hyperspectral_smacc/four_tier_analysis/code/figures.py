"""Figures for the deck and workbook (reads results/results.pkl)."""
import pickle
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

R = pickle.load(open("results/results.pkl", "rb"))
wl, X, y, SEL, sig = R["wl"], R["X"], R["y"], R["SEL"], R["sig"]
CH, CD = "#1baf7a", "#eb6834"            # healthy / diseased (validated pair)
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.edgecolor": INK2, "axes.labelcolor": INK,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
                     "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False, "savefig.dpi": 200,
                     "figure.facecolor": "white", "axes.titleweight": "bold", "axes.titlesize": 12})
REG = [(420, 700, "VIS"), (700, 750, "RE"), (750, 1330, "NIR"), (1460, 1780, "SWIR-1"), (1970, 2350, "SWIR-2")]

def gapped(x, yv):
    d = np.diff(x); nb = np.maximum(np.r_[d[1], d[:-1]], np.r_[d[1:], d[-2]])
    g = np.where(d > 2.5 * nb)[0] + 1
    return np.insert(x.astype(float), g, np.nan), np.insert(np.asarray(yv, float), g, np.nan, axis=-1)

def region_labels(ax, ytext):
    for lo, hi, name in REG:
        ax.text((lo + hi) / 2, ytext, name, ha="center", va="bottom", fontsize=9, color=INK2, transform=ax.get_xaxis_transform())

H, D = X[y == "healthy"], X[y == "diseased"]

# ---- 1 endmember locations
import pandas as pd
data = pd.read_csv("endmembers.csv")          # all 600 endmembers as extracted
fig, ax = plt.subplots(figsize=(6.4, 5.6))
for cls, c in (("healthy", CH), ("diseased", CD)):
    m = data["class"] == cls
    ax.scatter(data.col_0based[m], data.row_0based[m], s=14, c=c, edgecolors="white", linewidths=0.4, label=f"{cls} (n={m.sum()})")
ax.invert_yaxis(); ax.set_xlabel("Image column"); ax.set_ylabel("Image row"); ax.set_aspect("equal")
ax.set_title("Image position of the SMACC endmembers"); ax.legend(loc="upper right")
fig.tight_layout(); fig.savefig("results/fig01_locations.png"); plt.close(fig)

# ---- 2 all endmember spectra (all 600 as extracted, all 483 bands)
import pandas as pd
raw = pd.read_csv("endmembers.csv"); wl_raw = R["wl_all"]; Xr = raw[raw.columns[6:]].to_numpy(float)
fig, axes = plt.subplots(1, 2, figsize=(12, 4.4), sharey=True)
for ax, S, c, name in ((axes[0], Xr[raw["class"] == "healthy"], CH, "Healthy"), (axes[1], Xr[raw["class"] == "diseased"], CD, "Diseased")):
    for s in S:
        ax.plot(*gapped(wl_raw, s), color=c, lw=0.5, alpha=0.12)
    ax.plot(*gapped(wl_raw, S.mean(0)), color=INK, lw=2, label="class mean")
    ax.set_title(f"{name} endmembers (n={len(S)})"); ax.set_xlabel("Wavelength (nm)"); ax.legend(loc="upper right")
axes[0].set_ylabel("Reflectance")
fig.tight_layout(); fig.savefig("results/fig02_spectra.png"); plt.close(fig)

# ---- 3 mean ± SD
fig, ax = plt.subplots(figsize=(11, 4.6))
for S, c, name in ((H, CH, "Healthy"), (D, CD, "Diseased")):
    x, m = gapped(wl, S.mean(0)); _, sd = gapped(wl, S.std(0, ddof=1))
    ax.fill_between(x, m - sd, m + sd, color=c, alpha=0.18, lw=0)
    ax.plot(x, m, color=c, lw=2.2, label=f"{name} mean ± SD")
ax.set_xlabel("Wavelength (nm)"); ax.set_ylabel("Reflectance"); ax.legend(loc="upper right")
region_labels(ax, 1.0); ax.set_title("Mean reflectance spectra", pad=18)
fig.tight_layout(); fig.savefig("results/fig03_mean_sd.png"); plt.close(fig)

# ---- 4 data quality: negative values per band
nb = R["neg_by_band"]
fig, ax = plt.subplots(figsize=(8, 4.0))
ax.plot(*gapped(nb.wavelength_nm.values, nb.neg_diseased.values), color=CD, lw=2, label="Diseased")
ax.plot(*gapped(nb.wavelength_nm.values, nb.neg_healthy.values), color=CH, lw=2, label="Healthy")
ax.set_xlabel("Wavelength (nm)"); ax.set_ylabel("Spectra with reflectance < 0"); ax.legend(loc="upper left")
ax.set_title("Physically impossible (negative) reflectance, by band")
fig.tight_layout(); fig.savefig("results/fig04_negatives.png"); plt.close(fig)

# ---- 5 tier 1
t1 = R["tier1"]
fig, axes = plt.subplots(3, 1, figsize=(11, 8.2), sharex=True, gridspec_kw={"height_ratios": [1.3, 1, 1]})
ax = axes[0]
for S, c, name in ((H, CH, "Healthy"), (D, CD, "Diseased")):
    ax.plot(*gapped(wl, S.mean(0)), color=c, lw=2, label=name)
for a in axes:
    for j in np.where(~sig)[0]:
        a.axvspan(wl[j] - 1, wl[j] + 1, color="#b0b0b0", alpha=0.5, lw=0)
ax.set_ylabel("Mean reflectance"); ax.legend(loc="upper right"); ax.set_title("Tier 1 — one-way ANOVA at every band (grey = not significant, p ≥ 0.05)")
ax = axes[1]
lp = -np.log10(np.clip(t1.p_ANOVA.values, 1e-300, 1))
ax.plot(*gapped(wl, lp), color="#2a78d6", lw=1.8)
ax.axhline(-np.log10(0.05), color=INK, ls="--", lw=1); ax.text(wl.max(), -np.log10(0.05), " p = 0.05", va="bottom", ha="right", fontsize=9)
ax.set_ylabel("−log10(p)")
ax = axes[2]
ax.plot(*gapped(wl, t1.Cohen_d_D_minus_H.values), color="#6250d6", lw=1.8)
ax.axhline(0, color=INK2, lw=0.8)
for v in (0.8, -0.8):
    ax.axhline(v, color=INK2, ls=":", lw=0.8)
ax.text(wl.max(), 0.8, " |d| = 0.8 (large)", va="bottom", ha="right", fontsize=9)
ax.set_ylabel("Cohen's d (D − H)"); ax.set_xlabel("Wavelength (nm)")
fig.tight_layout(); fig.savefig("results/fig05_tier1.png"); plt.close(fig)

# ---- 6 cp plot
cp = R["cp_table"]
fig, ax = plt.subplots(figsize=(6.4, 4.2))
ax.errorbar(cp.nsplit, cp.xerror, yerr=cp.xstd, color="#2a78d6", marker="o", ms=5, lw=1.6, capsize=3, label="10-fold CV error (xerror ± SE)")
ax.plot(cp.nsplit, cp.rel_error, color=INK2, marker="s", ms=4, lw=1.2, label="Resubstitution error (rel error)")
imin = cp.xerror.idxmin(); ax.axhline(cp.xerror[imin] + cp.xstd[imin], color=INK, ls="--", lw=1, label="1-SE line")
cs = R["cart_summary"]
ax.axvline(cs["nsplitA"], color=CD, lw=1.4, ls=":", label=f"cp = 0.01 tree ({cs['nsplitA']} splits)")
ax.set_xlabel("Number of splits"); ax.set_ylabel("Error relative to root node"); ax.legend(fontsize=8.5, loc="upper right")
ax.set_title("CART complexity (rpart printcp equivalent)")
fig.tight_layout(); fig.savefig("results/fig06_cp.png"); plt.close(fig)

# ---- 7 tree diagram (cp = 0.01 tree)
co = R["cart_obj"]
L, Rr, feat, thr, counts, fidx, pr = co["left"], co["right"], co["feat"], co["thr"], co["counts"], co["feat_idx"], co["prA"]
def is_leaf(n): return L[n] == -1 or n in pr
pos, leaves = {}, []
def lay(n, d):
    if is_leaf(n):
        pos[n] = (len(leaves), d); leaves.append(n); return pos[n][0]
    a = lay(L[n], d + 1); b = lay(Rr[n], d + 1)
    pos[n] = ((a + b) / 2, d); return pos[n][0]
lay(0, 0)
nl = len(leaves); depth = max(v[1] for v in pos.values())
fig, ax = plt.subplots(figsize=(12.1, 5.35))
for n, (x, d) in pos.items():
    if not is_leaf(n):
        for ch, lab in ((L[n], "≤"), (Rr[n], ">")):
            ax.plot([x, pos[ch][0]], [-d, -pos[ch][1]], color=INK2, lw=1, zorder=1)
for n, (x, d) in pos.items():
    cH, cD = counts[n]
    if is_leaf(n):
        col = CD if cD > cH else CH
        txt = f"{'Diseased' if cD > cH else 'Healthy'}\nH {cH} | D {cD}"
        ax.text(x, -d, txt, ha="center", va="center", fontsize=9, color="white", fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.35", fc=col, ec="none"), zorder=3)
    else:
        txt = f"R{wl[fidx[feat[n]]]:.0f} ≤ {thr[n]:.3f}\nH {cH} | D {cD}"
        ax.text(x, -d, txt, ha="center", va="center", fontsize=9, color=INK,
                bbox=dict(boxstyle="round,pad=0.35", fc="#f2f2f0", ec=INK2, lw=0.8), zorder=3)
ax.set_xlim(-0.6, nl - 0.4); ax.set_ylim(-depth - 0.45, 0.45); ax.axis("off")
fig.subplots_adjust(left=0.005, right=0.995, top=0.99, bottom=0.01); fig.savefig("results/fig07_tree.png"); plt.close(fig)

# ---- 8 selected bands on spectra
fig, ax = plt.subplots(figsize=(11, 4.4))
for S, c, name in ((H, CH, "Healthy"), (D, CD, "Diseased")):
    ax.plot(*gapped(wl, S.mean(0)), color=c, lw=2, label=name)
ymax = max(H.mean(0).max(), D.mean(0).max())
for k, b in enumerate(sorted(SEL)):
    ax.axvline(wl[b], color=INK, lw=1, ls="--")
    ax.text(wl[b], ymax * (1.04 + 0.07 * (k % 2)), f"{wl[b]:.0f}", ha="center", fontsize=9, color=INK)
ax.set_ylim(0, ymax * 1.22); ax.set_xlabel("Wavelength (nm)"); ax.set_ylabel("Mean reflectance"); ax.legend(loc="center right")
ax.set_title(f"Tier 2 — {len(SEL)} bands selected by CART")
fig.tight_layout(); fig.savefig("results/fig08_selected_bands.png"); plt.close(fig)

# ---- 9 JM
jb, jc = R["jm_band"], R["jm_cumulative"]
fig, axes = plt.subplots(2, 1, figsize=(7.0, 6.2))
ax = axes[0]
ax.plot(*gapped(wl, jb.JM_0to2.values), color="#2a78d6", lw=1.8, label="single-band JM")
ax.scatter(wl[SEL], jb.JM_0to2.values[SEL], color=CD, zorder=3, s=30, label="CART bands")
ax.axhline(1.94, color=INK, ls="--", lw=1); ax.text(wl.min(), 1.94, "threshold 1.94", va="bottom", fontsize=9)
ax.set_ylim(0, 2.05); ax.set_xlabel("Wavelength (nm)"); ax.set_ylabel("JM distance (0–2)"); ax.legend(loc="center right")
ax.set_title("Separability of single bands")
ax = axes[1]
ax.bar(jc.n_bands, jc.JM_0to2, color="#2a78d6", width=0.7)
for r in jc.itertuples():
    ax.text(r.n_bands, r.JM_0to2 + 0.03, f"{r.JM_0to2:.2f}", ha="center", fontsize=8.5)
ax.axhline(1.94, color=INK, ls="--", lw=1)
ax.set_xticks(jc.n_bands); ax.set_xticklabels(jc.added_band_nm, rotation=60, fontsize=8)
ax.set_ylim(0, 2.1); ax.set_xlabel("Bands added (CART importance order, nm)"); ax.set_ylabel("Cumulative JM (0–2)")
ax.set_title("Cumulative separability")
fig.tight_layout(); fig.savefig("results/fig09_jm.png"); plt.close(fig)

# ---- 10 RF importance
imp = R["rf_importance"]
fig, ax = plt.subplots(figsize=(11, 4.2))
ax.plot(*gapped(wl, imp.MDI_importance.values), color="#eda100", lw=1.8, label="RF importance (all 463 bands)")
picked = []
for r in imp.sort_values("MDI_importance", ascending=False).itertuples():
    if all(abs(r.wavelength_nm - p_) > 40 for p_ in picked):
        picked.append(r.wavelength_nm)
        ax.annotate(f"{r.wavelength_nm:.0f} nm", (r.wavelength_nm, r.MDI_importance), textcoords="offset points", xytext=(-6, 4), ha="right", fontsize=9)
    if len(picked) == 3: break
for b in SEL:
    ax.axvline(wl[b], color=INK2, lw=0.9, ls=":")
ax.plot([], [], color=INK2, lw=0.9, ls=":", label="CART-selected bands")
ax.set_xlabel("Wavelength (nm)"); ax.set_ylabel("Mean decrease in Gini"); ax.legend(loc="upper left")
ax.set_title("Random Forest band importance")
fig.tight_layout(); fig.savefig("results/fig10_rf_importance.png"); plt.close(fig)

# ---- 11 permutation
pm = R["permutation"]
fig, ax = plt.subplots(figsize=(6.4, 3.8))
ax.hist(pm["acc"] * 100, bins=20, color="#b0b0b0", edgecolor="white")
ax.axvline(pm["observed"] * 100, color=CD, lw=2.2)
ax.text(pm["observed"] * 100, ax.get_ylim()[1] * 0.9, f" observed\n {pm['observed']*100:.1f}%", color=INK, fontsize=9, va="top",
        ha="right" if pm["observed"] > 0.9 else "left")
ax.set_xlabel("Nested-CV QDA accuracy with shuffled labels (%)"); ax.set_ylabel("Permutations")
ax.set_title(f"Permutation test ({pm['n']} label shuffles)")
fig.tight_layout(); fig.savefig("results/fig11_permutation.png"); plt.close(fig)

# ---- 12 spatial blocks
blk = R["spatial"]["blocks"]
fig, ax = plt.subplots(figsize=(7.4, 5.6))
mk = ["o", "s", "^", "D", "v"]
for cls, c in (("healthy", CH), ("diseased", CD)):
    for b in range(5):
        m = (blk["class"] == cls) & (blk.block == b)
        ax.scatter(blk.col[m], blk.row[m], s=16, c=c, marker=mk[b], edgecolors="white", linewidths=0.3)
for b in range(5):
    ax.scatter([], [], marker=mk[b], c="#808080", label=f"fold {b+1}")
ax.invert_yaxis(); ax.set_aspect("equal"); ax.set_xlabel("Image column"); ax.set_ylabel("Image row")
ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1.0), fontsize=9, title="spatial fold", title_fontsize=9)
ax.set_title("Spatial blocks for block cross-validation")
fig.tight_layout(); fig.savefig("results/fig12_blocks.png"); plt.close(fig)
print("figures written")
