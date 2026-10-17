"""Figures for the 47-plot analysis (reads results/r47.pkl, or the file named in env R47)."""
import os, pickle, numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MPoly, Patch
from matplotlib.path import Path as MPath
import matplotlib.patheffects as pe
R = pickle.load(open(os.environ.get("R47", "results/r47.pkl"), "rb"))
X, y, wl, groups, V, full, td = R["X"], R["y"], R["wl"], R["groups"], R["V"], R["full"], R["design"]
PH, PD = R["PH"], R["PD"]
CH, CD, CB, INK, INK2, GRID = "#1baf7a", "#eb6834", "#2a78d6", "#0b0b0b", "#52514e", "#e4e3df"
BLK = {"C": CH, "R3": "#f2b48f", "R2": "#eb6834", "R1": "#a8401a"}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "axes.spines.top": False,
                     "axes.spines.right": False, "legend.frameon": False, "savefig.dpi": 200, "figure.facecolor": "white",
                     "axes.titleweight": "bold", "axes.titlesize": 12})
def gapped(x, v):
    d = np.diff(x); nb = np.maximum(np.r_[d[1], d[:-1]], np.r_[d[1:], d[-2]]); g = np.where(d > 2.5 * nb)[0] + 1
    return np.insert(x.astype(float), g, np.nan), np.insert(np.asarray(v, float), g, np.nan, axis=-1)
H, D = X[y == 0], X[y == 1]
polys = R["polys_xy"]
def inside_point(q):
    c = q.mean(0); path = MPath(q)
    if path.contains_point(c): return c
    gx, gy = np.meshgrid(np.linspace(q[:, 0].min(), q[:, 0].max(), 60), np.linspace(q[:, 1].min(), q[:, 1].max(), 60))
    pts = np.column_stack([gx.ravel(), gy.ravel()]); ins = pts[path.contains_points(pts)]
    off = np.array([[a, b] for a in (-0.6, 0, 0.6) for b in (-0.6, 0, 0.6)])
    deep = ins[[all(path.contains_points(p + off)) for p in ins]]
    cand = deep if len(deep) else ins
    return cand[np.argmin(((cand - c) ** 2).sum(1))]
def plot_map(ax, colour_of, label_of, edge_of=None, title="", fs=8.5):
    for k, q in polys.items():
        ax.add_patch(MPoly(q, closed=True, fc=colour_of(k), ec=edge_of(k) if edge_of else "white", lw=2.2 if edge_of else 1.0))
        c = inside_point(q)
        ax.text(c[0], c[1], label_of(k), ha="center", va="center", fontsize=fs, color=INK, fontweight="bold", path_effects=[pe.withStroke(linewidth=2.4, foreground="white")])
    allq = np.vstack(list(polys.values()))
    ax.set_xlim(allq[:, 0].min() - 1, allq[:, 0].max() + 1); ax.set_ylim(allq[:, 1].min() - 1, allq[:, 1].max() + 1)
    ax.set_aspect("equal"); ax.set_xlabel("East (m)"); ax.set_ylabel("North (m)"); ax.set_title(title)
cfgs = R["CONFIGS"]
def CV(t2, k): return V[(t2, "S0")][k]

# f01 plot map
fig, ax = plt.subplots(figsize=(7.4, 6.2))
plot_map(ax, lambda k: CH if k in PH else CD, lambda k: str(k), title="47 plots analysed (plot 4 excluded)")
ax.legend(handles=[Patch(color=CH, label=f"healthy ({len(PH)} plots × 98 EM)"), Patch(color=CD, label=f"diseased ({len(PD)} plots × 30 EM)")], loc="lower right")
fig.tight_layout(); fig.savefig("results/f01_plotmap.png"); plt.close(fig)

# f02 counts
cnt = pd.Series(groups).value_counts().sort_index()
fig, ax = plt.subplots(figsize=(11, 3.4))
ax.bar(range(len(cnt)), cnt.values, color=[CH if k in PH else CD for k in cnt.index], width=0.75)
ax.set_xticks(range(len(cnt)), [str(k) for k in cnt.index], fontsize=8); ax.set_xlabel("Plot"); ax.set_ylabel("Endmember spectra")
ax.set_title(f"Endmember spectra per plot (healthy {len(H)} = 11 × 98; diseased {len(D)} = 36 × 30)")
fig.tight_layout(); fig.savefig("results/f02_counts.png"); plt.close(fig)

# f03 spectra / f04 mean ± SD
fig, axes = plt.subplots(1, 2, figsize=(12, 4.4), sharey=True)
for ax, S, c, nm in ((axes[0], H, CH, "Healthy"), (axes[1], D, CD, "Diseased")):
    for s in S: ax.plot(*gapped(wl, s), color=c, lw=0.4, alpha=0.05)
    ax.plot(*gapped(wl, S.mean(0)), color=INK, lw=2, label="class mean")
    ax.set_title(f"{nm} endmembers (n = {len(S)})"); ax.set_xlabel("Wavelength (nm)"); ax.legend(loc="upper right")
axes[0].set_ylabel("Reflectance"); fig.tight_layout(); fig.savefig("results/f03_spectra.png"); plt.close(fig)
fig, ax = plt.subplots(figsize=(11, 4.4))
for S, c, nm in ((H, CH, "Healthy"), (D, CD, "Diseased")):
    x, m = gapped(wl, S.mean(0)); _, sd = gapped(wl, S.std(0, ddof=1))
    ax.fill_between(x, m - sd, m + sd, color=c, alpha=0.18, lw=0); ax.plot(x, m, color=c, lw=2.2, label=f"{nm} mean ± SD")
ax.set_xlabel("Wavelength (nm)"); ax.set_ylabel("Reflectance"); ax.legend(loc="upper right"); ax.set_title("Mean reflectance ± 1 SD, all 483 bands")
fig.tight_layout(); fig.savefig("results/f04_mean_sd.png"); plt.close(fig)

# f05 data quality
ng = R["neg"]
fig, axes = plt.subplots(1, 2, figsize=(12, 3.9))
for ax, (a, b, ttl) in zip(axes, (("neg_diseased", "neg_healthy", "Reflectance < 0"), ("gt1_diseased", "gt1_healthy", "Reflectance > 1"))):
    ax.plot(*gapped(wl, ng[a].values), color=CD, lw=2, label="Diseased"); ax.plot(*gapped(wl, ng[b].values), color=CH, lw=2, label="Healthy")
    ax.set_xlabel("Wavelength (nm)"); ax.set_title(f"Spectra with {ttl.lower()} at each band"); ax.legend(loc="upper left")
axes[0].set_ylabel("Number of spectra"); fig.tight_layout(); fig.savefig("results/f05_quality.png"); plt.close(fig)

# f06 Tier 1
t1 = R["tier1"]; sig = t1.p_ANOVA.values < 0.05
fig, axes = plt.subplots(3, 1, figsize=(11, 8.2), sharex=True, gridspec_kw={"height_ratios": [1.2, 1, 1]})
for S, c, nm in ((H, CH, "Healthy"), (D, CD, "Diseased")): axes[0].plot(*gapped(wl, S.mean(0)), color=c, lw=2, label=nm)
for a in axes:
    for j in np.where(~sig)[0]: a.axvspan(wl[j] - 1.5, wl[j] + 1.5, color="#c8c8c8", alpha=0.6, lw=0)
axes[0].set_ylabel("Mean reflectance"); axes[0].legend(loc="upper right"); axes[0].set_title(f"Tier 1 — one-way ANOVA at every band: {sig.sum()} of {len(wl)} significant (grey = p ≥ 0.05)")
axes[1].plot(*gapped(wl, -np.log10(np.clip(t1.p_ANOVA.values, 1e-300, 1))), color=CB, lw=1.8, label=f"spectra as replicates (n = {len(y)})")
axes[1].plot(*gapped(wl, -np.log10(np.clip(t1.p_plot_means.values, 1e-300, 1))), color="#6250d6", lw=1.8, ls="--", label=f"plot means as replicates (n = {len(PH)+len(PD)})")
axes[1].axhline(-np.log10(0.05), color=INK, ls=":", lw=1); axes[1].set_ylabel("−log10(p)"); axes[1].legend(loc="upper left")
axes[2].plot(*gapped(wl, t1.Cohen_d.values), color="#6250d6", lw=1.8); axes[2].axhline(0, color=INK2, lw=0.8)
for v in (0.5, -0.5): axes[2].axhline(v, color=INK2, ls=":", lw=0.8)
axes[2].set_ylabel("Cohen's d (D − H)"); axes[2].set_xlabel("Wavelength (nm)")
fig.tight_layout(); fig.savefig("results/f06_tier1.png"); plt.close(fig)

# f07 CART tree (all data)
tr = full["CART"]["tree"]; L, Rr, f, thr, counts, fidx, pr = tr["L"], tr["Rr"], tr["f"], tr["thr"], tr["counts"], tr["feat_idx"], tr["pr"]
leaf = lambda n: L[n] == -1 or pr[n]
pos, leaves = {}, []
def lay(n, dd):
    if leaf(n): pos[n] = (len(leaves), dd); leaves.append(n); return pos[n][0]
    a = lay(L[n], dd + 1); b = lay(Rr[n], dd + 1); pos[n] = ((a + b) / 2, dd); return pos[n][0]
lay(0, 0); depth = max(v[1] for v in pos.values()); nl = len(leaves)
fig, ax = plt.subplots(figsize=(15, 6.6))
for n, (x0, dd) in pos.items():
    if not leaf(n):
        for ch in (L[n], Rr[n]): ax.plot([x0, pos[ch][0]], [-dd, -pos[ch][1]], color=INK2, lw=1, zorder=1)
for n, (x0, dd) in pos.items():
    cH, cD = counts[n]
    if leaf(n):
        ax.text(x0, -dd, f"{'D' if cD > cH else 'H'}\n{cH:.0f}|{cD:.0f}", ha="center", va="center", fontsize=10, color="white", fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.3", fc=CD if cD > cH else CH, ec="none"), zorder=3)
    else:
        ax.text(x0, -dd, f"R{wl[fidx[f[n]]]:.0f}≤{thr[n]:.4f}", ha="center", va="center", fontsize=10, color=INK,
                bbox=dict(boxstyle="round,pad=0.25", fc="#f2f2f0", ec=INK2, lw=0.7), zorder=3)
ax.set_xlim(-0.7, nl - 0.3); ax.set_ylim(-depth - 0.5, 0.5); ax.axis("off")
fig.subplots_adjust(left=0.005, right=0.995, top=0.99, bottom=0.01); fig.savefig("results/f07_tree.png"); plt.close(fig)

# f08 selected bands on the single-band J–M curve
jb = R["jm_band"]
fig, ax = plt.subplots(figsize=(11, 4.4))
ax.plot(*gapped(wl, jb), color="#a0a0a0", lw=1.5, label="single-band J–M, all 483 bands")
for t2, mk, c in (("CART", "o", CD), ("RF", "D", CB)):
    b = full[t2]["bands"]; ax.scatter(wl[b], jb[b], marker=mk, color=c, s=46, zorder=3, label=f"{t2} bands ({len(b)})", edgecolor="white", lw=0.6)
ax.set_xlabel("Wavelength (nm)"); ax.set_ylabel("J–M distance of the single band (0–2 scale)"); ax.set_ylim(0, np.nanmax(jb) * 1.35)
ax.set_title(f"Tier 2 bands and their individual J–M distance (max {np.nanmax(jb):.3f}; separability threshold 1.94 is off scale)"); ax.legend(loc="upper left")
fig.tight_layout(); fig.savefig("results/f08_bands_jm.png"); plt.close(fig)

# f09 cumulative J–M
fig, ax = plt.subplots(figsize=(8.5, 4.4))
for t2, c, mk in (("CART", CD, "o"), ("RF", CB, "D")):
    cu = full[t2]["cum"]; ax.plot(range(1, len(cu) + 1), cu, color=c, marker=mk, lw=2, label=f"{t2}: set JM = {full[t2]['JM']:.3f}")
ax.axhline(1.94, color=INK, ls="--", lw=1); ax.text(1, 1.94, " threshold 1.94 (Das et al. 2020)", va="bottom", fontsize=9)
ax.set_ylim(0, 2.05); ax.set_xlabel("Number of bands (CART: order of first use; RF: importance order)"); ax.set_ylabel("J–M distance of the first k bands")
ax.set_title("Tier 3 — cumulative J–M distance"); ax.legend(loc="center right")
fig.tight_layout(); fig.savefig("results/f09_jm_cumulative.png"); plt.close(fig)

# f10 RF importance
imp = full["RF"]["importance"]; iw = np.full(len(wl), np.nan); iw[imp.band.values] = imp.importance.values
fig, ax = plt.subplots(figsize=(11, 4.0))
ax.plot(*gapped(wl, iw), color="#eda100", lw=1.6, label="RF importance (mean decrease in Gini) of every ANOVA-significant band")
b = full["RF"]["bands"]; ax.scatter(wl[b], iw[b], marker="D", color=CB, s=40, zorder=3, label="bands kept (highest importance, |r| < 0.95 to bands already kept)")
ax.set_xlabel("Wavelength (nm)"); ax.set_ylabel("Importance"); ax.legend(loc="upper left", fontsize=9.5); ax.set_title("Tier 2 alternative — Random Forest band ranking")
fig.tight_layout(); fig.savefig("results/f10_rf_importance.png"); plt.close(fig)

# f11 leave-one-plot-out maps
for t2 in ("CART", "RF"):
    tab = CV(t2, "CV3")["reps"][0]["plot"]["table"]; cmap = plt.get_cmap("RdYlGn_r")
    fig, ax = plt.subplots(figsize=(7.4, 6.2))
    plot_map(ax, lambda k: cmap(tab.loc[k, "frac"]), lambda k: f"{k}\n{tab.loc[k,'frac']*100:.0f}%",
             edge_of=lambda k: ("#0b0b0b" if tab.loc[k, "pred"] != tab.loc[k, "t"] else "white"),
             title=f"Leave-one-plot-out (CV3), {t2} + QDA\n% of spectra predicted diseased; black outline = plot misclassified", fs=7.5)
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(0, 100)); cb = fig.colorbar(sm, ax=ax, shrink=0.7); cb.set_label("% predicted diseased")
    fig.tight_layout(); fig.savefig(f"results/f11_lopo_{t2}.png"); plt.close(fig)

# f12 permutation
fig, axes = plt.subplots(1, 2, figsize=(11, 3.8), sharey=True)
for ax, t2 in zip(axes, ("CART", "RF")):
    pmn = R["perm"][t2]
    ax.hist(pmn["null"], bins=20, color="#b0b0b0", edgecolor="white", label="shuffled plot labels"); ax.axvline(pmn["observed"], color=CD, lw=2.2, label="true labels")
    ax.set_title(f"{t2} + QDA: p = {pmn['p']:.3f}"); ax.set_xlabel("Balanced accuracy (CV2, one repetition)"); ax.legend(loc="upper left", fontsize=9)
axes[0].set_ylabel("Permutations"); fig.tight_layout(); fig.savefig("results/f12_permutation.png"); plt.close(fig)

# f13 design map
fig, ax = plt.subplots(figsize=(8.2, 6.4))
plot_map(ax, lambda k: BLK[td.block[k]], lambda k: f"{k}\n{td.variety[k]}·{td.date[k]}", title="Layout: block · variety (V1–V3) · inoculation date (D1–D4)", fs=7)
ax.legend(handles=[Patch(color=BLK["C"], label="C: control (healthy), plots 1–12 (4 excluded)"), Patch(color=BLK["R3"], label="R3: inoculated, plots 13–24"),
                   Patch(color=BLK["R2"], label="R2: inoculated, plots 25–36"), Patch(color=BLK["R1"], label="R1: inoculated, plots 37–48")], loc="lower right", fontsize=9)
fig.tight_layout(); fig.savefig("results/f13_design.png"); plt.close(fig)

# f14 negative control
NC = R["NC"]; order = [("C", "R3"), ("C", "R2"), ("C", "R1"), ("R3", "R2"), ("R2", "R1"), ("R3", "R1")]
fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.4), sharey=True)
for ax, key, ttl in ((axes[0], "BA", "Spectrum-level balanced accuracy"), (axes[1], "plotBA", "Plot-level balanced accuracy")):
    xs = np.arange(len(order))
    for j, (t2, hatch) in enumerate((("CART", ""), ("RF", "//"))):
        m = [NC[p_][t2][key][0] for p_ in order]; s_ = [NC[p_][t2][key][1] for p_ in order]
        ax.bar(xs + (j - 0.5) * 0.38, m, 0.36, yerr=s_, color=[CD if p_[0] == "C" else "#9a9a9a" for p_ in order], hatch=hatch, edgecolor="white", capsize=3, error_kw=dict(lw=1, ecolor=INK2))
        for x_, v in zip(xs + (j - 0.5) * 0.38, m): ax.text(x_, 0.31, f"{v:.2f}", ha="center", fontsize=8, color="white", fontweight="bold")
    ax.set_xticks(xs, [f"{a_} vs {b_}\n{NC[(a_, b_)]['distance_m']:.0f} m" for a_, b_ in order], fontsize=9)
    ax.axhline(0.5, color=INK, ls=":", lw=1); ax.set_title(ttl); ax.set_ylim(0.3, 1.0); ax.axvline(2.5, color=INK2, lw=0.8)
axes[0].set_ylabel("Balanced accuracy (mean ± SD)")
axes[0].legend(handles=[Patch(color=CD, label="control vs inoculated"), Patch(color="#9a9a9a", label="inoculated vs inoculated (negative control)"),
                        Patch(fc="white", ec=INK2, label="CART (plain)"), Patch(fc="white", ec=INK2, hatch="//", label="RF (hatched)")], loc="upper left", fontsize=8.5)
fig.tight_layout(); fig.savefig("results/f14_negative_control.png"); plt.close(fig)

# f15 detection by block
fig, axes = plt.subplots(1, 2, figsize=(12, 4.2), sharey=True)
for ax, t2 in zip(axes, ("CART", "RF")):
    tab = R["DET"][t2]["table"]; order = ["C", "R3", "R2", "R1"]; data = [tab[tab.block == b].pD_CV2.values for b in order]
    bp = ax.boxplot(data, widths=0.55, patch_artist=True, showfliers=False, medianprops=dict(color=INK))
    for p_, b in zip(bp["boxes"], order): p_.set_facecolor(BLK[b]); p_.set_alpha(0.75)
    for i, d_ in enumerate(data): ax.scatter(np.full(len(d_), i + 1) + np.random.default_rng(i).uniform(-0.12, 0.12, len(d_)), d_, s=14, color=INK, zorder=3)
    ax.set_xticks(range(1, 5), ["C\n(control)", "R3", "R2", "R1"]); ax.axhline(0.5, color=INK, ls=":", lw=1)
    ax.set_title(f"{t2}: share of each plot's spectra predicted diseased"); ax.set_xlabel("Block (west → east)")
axes[0].set_ylabel("Share predicted diseased (CV2, mean of reps)"); axes[0].set_ylim(0, 1)
fig.tight_layout(); fig.savefig("results/f15_detection_block.png"); plt.close(fig)
print("figures done")
