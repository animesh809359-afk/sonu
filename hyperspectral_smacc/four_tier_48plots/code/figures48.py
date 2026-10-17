"""Figures for the 48-plot analysis (reads results/r48.pkl and plots48.xml)."""
import pickle, re, numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MPoly
from matplotlib.path import Path as MPath
import matplotlib.patheffects as pe
R = pickle.load(open("results/r48.pkl", "rb"))
X, y, wl, groups, V, full, STRATS = R["X"], R["y"], R["wl"], R["groups"], R["V"], R["full"], R["STRATS"]
CH, CD, INK, INK2, GRID = "#1baf7a", "#eb6834", "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "axes.spines.top": False,
                     "axes.spines.right": False, "legend.frameon": False, "savefig.dpi": 200, "figure.facecolor": "white",
                     "axes.titleweight": "bold", "axes.titlesize": 12})
def gapped(x, v):
    d = np.diff(x); nb = np.maximum(np.r_[d[1], d[:-1]], np.r_[d[1:], d[-2]]); g = np.where(d > 2.5 * nb)[0] + 1
    return np.insert(x.astype(float), g, np.nan), np.insert(np.asarray(v, float), g, np.nan, axis=-1)
H, D = X[y == 0], X[y == 1]

# polygons
txt = open("plots48.xml").read()
polys = {}
for m in re.finditer(r'<Region name="ROI #(\d+)".*?<Coordinates>(.*?)</Coordinates>', txt, re.S):
    v = np.array(m.group(2).split(), float).reshape(-1, 2); polys[int(m.group(1))] = v
lat0 = np.mean([p[:, 1].mean() for p in polys.values()]); lon0 = np.mean([p[:, 0].mean() for p in polys.values()])
def xy(p): return np.column_stack([(p[:, 0] - lon0) * 111320 * np.cos(np.radians(lat0)), (p[:, 1] - lat0) * 110850])
def inside_point(q):
    """Vertex mean if it lies inside the polygon (plot 15 is L-shaped), else the interior point nearest to it."""
    c = q.mean(0); path = MPath(q)
    if path.contains_point(c): return c
    gx, gy = np.meshgrid(np.linspace(q[:, 0].min(), q[:, 0].max(), 60), np.linspace(q[:, 1].min(), q[:, 1].max(), 60))
    pts = np.column_stack([gx.ravel(), gy.ravel()]); ins = pts[path.contains_points(pts)]
    # prefer points far from the edge: keep those whose 8 neighbours (0.6 m away) are also inside
    off = np.array([[a, b] for a in (-0.6, 0, 0.6) for b in (-0.6, 0, 0.6)])
    deep = ins[[all(path.contains_points(p + off)) for p in ins]]
    cand = deep if len(deep) else ins
    return cand[np.argmin(((cand - c) ** 2).sum(1))]
def plot_map(ax, colour_of, label_of=None, edge_of=None, title=""):
    for k, p in polys.items():
        q = xy(p)
        ax.add_patch(MPoly(q, closed=True, fc=colour_of(k), ec=edge_of(k) if edge_of else "white", lw=2.2 if edge_of else 1.0))
        c = inside_point(q)
        ax.text(c[0], c[1], label_of(k) if label_of else str(k), ha="center", va="center", fontsize=8.5, color=INK, fontweight="bold",
                path_effects=[pe.withStroke(linewidth=2.5, foreground="white")])
    allq = np.vstack([xy(p) for p in polys.values()])
    ax.set_xlim(allq[:, 0].min() - 1, allq[:, 0].max() + 1); ax.set_ylim(allq[:, 1].min() - 1, allq[:, 1].max() + 1)
    ax.set_aspect("equal"); ax.set_xlabel("East (m)"); ax.set_ylabel("North (m)"); ax.set_title(title)
R["polys_xy"] = {k: xy(p) for k, p in polys.items()}

fig, ax = plt.subplots(figsize=(7.2, 6.2))
plot_map(ax, lambda k: CH if k <= 12 else CD, title="The 48 plots (ROIs) — plots 1–12 healthy, 13–48 diseased")
ax.plot([], [], "s", color=CH, ms=10, label="healthy (12 plots)"); ax.plot([], [], "s", color=CD, ms=10, label="diseased (36 plots)"); ax.legend(loc="lower right")
fig.tight_layout(); fig.savefig("results/f01_plotmap.png"); plt.close(fig)

cnt = pd.Series(groups).value_counts().sort_index()
fig, ax = plt.subplots(figsize=(11, 3.4))
ax.bar(cnt.index, cnt.values, color=[CH if k <= 12 else CD for k in cnt.index], width=0.75)
ax.set_xlabel("Plot"); ax.set_ylabel("Endmember spectra"); ax.set_ylim(0, 33); ax.set_xticks(range(1, 49, 1)); ax.tick_params(axis="x", labelsize=8)
ax.set_title(f"Endmember spectra per plot (healthy {int((y==0).sum())}, diseased {int((y==1).sum())}; total {len(y)})")
for k, v in cnt.items():
    if v < 30: ax.text(k, v + 0.4, str(v), ha="center", fontsize=8)
fig.tight_layout(); fig.savefig("results/f02_counts.png"); plt.close(fig)

fig, axes = plt.subplots(1, 2, figsize=(12, 4.4), sharey=True)
for ax, S, c, nm in ((axes[0], H, CH, "Healthy"), (axes[1], D, CD, "Diseased")):
    for s in S: ax.plot(*gapped(wl, s), color=c, lw=0.4, alpha=0.07)
    ax.plot(*gapped(wl, S.mean(0)), color=INK, lw=2, label="class mean")
    ax.set_title(f"{nm} endmembers (n = {len(S)})"); ax.set_xlabel("Wavelength (nm)"); ax.legend(loc="upper right")
axes[0].set_ylabel("Reflectance"); fig.tight_layout(); fig.savefig("results/f03_spectra.png"); plt.close(fig)

fig, ax = plt.subplots(figsize=(11, 4.4))
for S, c, nm in ((H, CH, "Healthy"), (D, CD, "Diseased")):
    x, m = gapped(wl, S.mean(0)); _, sd = gapped(wl, S.std(0, ddof=1))
    ax.fill_between(x, m - sd, m + sd, color=c, alpha=0.18, lw=0); ax.plot(x, m, color=c, lw=2.2, label=f"{nm} mean ± SD")
ax.set_xlabel("Wavelength (nm)"); ax.set_ylabel("Reflectance"); ax.legend(loc="upper right"); ax.set_title("Mean reflectance, all 483 bands")
fig.tight_layout(); fig.savefig("results/f04_mean_sd.png"); plt.close(fig)

ng = R["neg"]
fig, ax = plt.subplots(figsize=(8, 4.0))
ax.plot(*gapped(wl, ng.neg_diseased.values), color=CD, lw=2, label="Diseased"); ax.plot(*gapped(wl, ng.neg_healthy.values), color=CH, lw=2, label="Healthy")
ax.set_xlabel("Wavelength (nm)"); ax.set_ylabel("Spectra with reflectance < 0"); ax.legend(loc="upper left"); ax.set_title("Negative (impossible) reflectance by band")
fig.tight_layout(); fig.savefig("results/f05_negatives.png"); plt.close(fig)

t1 = R["tier1"]; sig = t1.p_ANOVA.values < 0.05
fig, axes = plt.subplots(3, 1, figsize=(11, 8.2), sharex=True, gridspec_kw={"height_ratios": [1.2, 1, 1]})
for S, c, nm in ((H, CH, "Healthy"), (D, CD, "Diseased")): axes[0].plot(*gapped(wl, S.mean(0)), color=c, lw=2, label=nm)
for a in axes:
    for j in np.where(~sig)[0]: a.axvspan(wl[j] - 1, wl[j] + 1, color="#b0b0b0", alpha=0.5, lw=0)
axes[0].set_ylabel("Mean reflectance"); axes[0].legend(loc="upper right"); axes[0].set_title("Tier 1 — one-way ANOVA at every band (grey = not significant, p ≥ 0.05)")
axes[1].plot(*gapped(wl, -np.log10(np.clip(t1.p_ANOVA.values, 1e-300, 1))), color="#2a78d6", lw=1.8, label="spectra (n = 1417)")
axes[1].plot(*gapped(wl, -np.log10(np.clip(t1.p_plot_means.values, 1e-300, 1))), color="#6250d6", lw=1.8, ls="--", label="plot means (n = 48)")
axes[1].axhline(-np.log10(0.05), color=INK, ls=":", lw=1); axes[1].set_ylabel("−log10(p)"); axes[1].legend(loc="upper left")
axes[2].plot(*gapped(wl, t1.Cohen_d.values), color="#6250d6", lw=1.8); axes[2].axhline(0, color=INK2, lw=0.8)
for v in (0.8, -0.8): axes[2].axhline(v, color=INK2, ls=":", lw=0.8)
axes[2].set_ylabel("Cohen's d (D − H)"); axes[2].set_xlabel("Wavelength (nm)")
fig.tight_layout(); fig.savefig("results/f06_tier1.png"); plt.close(fig)

# CART tree (class-weighted, S1)
tr = R["tree_S1"]; L, Rr, f, thr, counts, fidx, pr = tr["L"], tr["Rr"], tr["f"], tr["thr"], tr["counts"], tr["feat_idx"], tr["pr"]
leaf = lambda n: L[n] == -1 or pr[n]
pos, leaves = {}, []
def lay(n, dd):
    if leaf(n): pos[n] = (len(leaves), dd); leaves.append(n); return pos[n][0]
    a = lay(L[n], dd + 1); b = lay(Rr[n], dd + 1); pos[n] = ((a + b) / 2, dd); return pos[n][0]
wH, wD = len(y) / (2 * (y == 0).sum()), len(y) / (2 * (y == 1).sum())   # S1 class weights on the full data
assert abs(counts[0][0] / wH - (y == 0).sum()) < 1e-6 and abs(counts[0][1] / wD - (y == 1).sum()) < 1e-6
lay(0, 0); depth = max(v[1] for v in pos.values()); nl = len(leaves)
fig, ax = plt.subplots(figsize=(15, 6.6))
for n, (x0, dd) in pos.items():
    if not leaf(n):
        for ch in (L[n], Rr[n]): ax.plot([x0, pos[ch][0]], [-dd, -pos[ch][1]], color=INK2, lw=1, zorder=1)
for n, (x0, dd) in pos.items():
    cH, cD = counts[n]
    if leaf(n):
        col = CD if cD > cH else CH
        nH_, nD_ = cH / wH, cD / wD          # weighted totals back to numbers of spectra
        ax.text(x0, -dd, f"{'D' if cD > cH else 'H'}\n{nH_:.0f}|{nD_:.0f}", ha="center", va="center", fontsize=10, color="white", fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.3", fc=col, ec="none"), zorder=3)
    else:
        ax.text(x0, -dd, f"R{wl[fidx[f[n]]]:.0f}≤{thr[n]:.4f}", ha="center", va="center", fontsize=10, color=INK,
                bbox=dict(boxstyle="round,pad=0.25", fc="#f2f2f0", ec=INK2, lw=0.7), zorder=3)
ax.set_xlim(-0.7, nl - 0.3); ax.set_ylim(-depth - 0.5, 0.5); ax.axis("off")
fig.subplots_adjust(left=0.005, right=0.995, top=0.99, bottom=0.01); fig.savefig("results/f07_tree.png"); plt.close(fig)

# band selection matrix
cfgs = R["CONFIGS"]
fig, ax = plt.subplots(figsize=(11, 4.6))
ax.plot(*gapped(wl, (D.mean(0) - H.mean(0)) * 0 + 0), alpha=0)
for i, (t2, s) in enumerate(cfgs):
    yy = len(cfgs) - 1 - i
    ax.scatter(full[(t2, s)]["wl"], [yy] * len(full[(t2, s)]["wl"]), marker="o" if t2 == "CART" else "D", s=30,
               color=CD if t2 == "CART" else "#2a78d6", edgecolors="white", linewidths=0.5, zorder=3)
ax.set_yticks(range(len(cfgs))); ax.set_yticklabels([f"{t2} · {STRATS[s]}" for t2, s in cfgs][::-1], fontsize=9.5)
ax.set_xlabel("Wavelength (nm)"); ax.set_title("Tier 2 — bands selected on all data (CART: circles, RF: diamonds)"); ax.grid(axis="y", color=GRID)
ax.set_xlim(380, 2420); fig.tight_layout(); fig.savefig("results/f08_bands.png"); plt.close(fig)

# JM
jb = R["jm_band"]; bs = R["best"]
fig, axes = plt.subplots(1, 2, figsize=(12, 4.4), gridspec_kw={"width_ratios": [1.5, 1]})
ax = axes[0]; ax.plot(*gapped(wl, jb), color="#b0b0b0", lw=1.5, label="all bands")
for t2, mk, c in (("CART", "o", CD), ("RF", "D", "#2a78d6")):
    b = full[(t2, bs[t2])]["bands"]; ax.scatter(wl[b], jb[b], marker=mk, color=c, s=36, zorder=3, label=f"{t2}-{bs[t2]} bands ({STRATS[bs[t2]].split(' (')[0]})")
ax.set_ylim(0, np.nanmax(jb) * 1.45); ax.set_xlabel("Wavelength (nm)"); ax.set_ylabel("Single-band JM (0–2 scale)"); ax.legend(loc="upper left", fontsize=9)
ax.set_title(f"Single bands: max JM = {np.nanmax(jb):.3f} (threshold 1.94, off scale)")
ax = axes[1]
for t2, s in cfgs:
    c = full[(t2, s)]["cum"]
    ax.plot(range(1, len(c) + 1), c, color=CD if t2 == "CART" else "#2a78d6", lw=1.6, ls=["-", "--", ":", "-."][list(STRATS).index(s)],
            label=f"{t2}-{s}")
ax.axhline(1.94, color=INK, ls="--", lw=1); ax.set_ylim(0, 2.05); ax.set_xlabel("Bands added (CART: wavelength order; RF: importance order)"); ax.set_ylabel("Cumulative JM (0–2)")
ax.text(0.5, 1.94, "threshold 1.94", va="bottom", fontsize=9); ax.legend(fontsize=8, ncol=2, loc="center left"); ax.set_title("Selected band sets (cumulative)")
fig.tight_layout(); fig.savefig("results/f09_jm.png"); plt.close(fig)

# RF importance (class-weighted)
imp = full[("RF", "S1")]["importance"]; iw = np.zeros(len(wl)); iw[:] = np.nan; iw[imp.band.values] = imp.importance.values
fig, ax = plt.subplots(figsize=(11, 4.2))
ax.plot(*gapped(wl, iw), color="#eda100", lw=1.6, label="RF importance (significant bands, class-weighted RF)")
b = full[("RF", "S1")]["bands"]; ax.scatter(wl[b], iw[b], marker="D", color="#2a78d6", s=34, zorder=3, label="bands kept (|r| < 0.95)")
ax.set_xlabel("Wavelength (nm)"); ax.set_ylabel("Mean decrease in Gini"); ax.legend(loc="upper left"); ax.set_title("Tier 2 alternative — Random Forest band ranking")
fig.tight_layout(); fig.savefig("results/f10_rf_importance.png"); plt.close(fig)

# LOPO plot map for best configs
for t2 in ("CART", "RF"):
    s = bs[t2]; tab = V[(t2, s)]["v3"]["plot"]["table"]
    fig, ax = plt.subplots(figsize=(7.2, 6.2))
    cmap = plt.get_cmap("RdYlGn_r")
    plot_map(ax, lambda k: cmap(tab.loc[k, "frac"]), label_of=lambda k: f"{k}\n{tab.loc[k,'frac']*100:.0f}%",
             edge_of=lambda k: ("#0b0b0b" if tab.loc[k, "pred"] != tab.loc[k, "t"] else "white"),
             title=f"Leave-one-plot-out, {t2}-{s}: {STRATS[s]}, QDA\n% of spectra predicted diseased; black outline = plot misclassified")
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(0, 100)); cb = fig.colorbar(sm, ax=ax, shrink=0.7); cb.set_label("% predicted diseased")
    fig.tight_layout(); fig.savefig(f"results/f11_lopo_{t2}.png"); plt.close(fig)

# permutation
fig, axes = plt.subplots(1, 2, figsize=(11, 3.8), sharey=True)
for ax, t2 in zip(axes, ("CART", "RF")):
    pm = R["perm"][t2]
    ax.hist(pm["null"], bins=20, color="#b0b0b0", edgecolor="white"); ax.axvline(pm["observed"], color=CD, lw=2.2)
    ax.set_title(f"{t2}-{pm['strategy']} + QDA: p = {pm['p']:.3f}"); ax.set_xlabel("Balanced accuracy with shuffled plot labels")
axes[0].set_ylabel("Permutations"); fig.tight_layout(); fig.savefig("results/f12_permutation.png"); plt.close(fig)
pickle.dump(R["polys_xy"], open("results/polys_xy.pkl", "wb"))
print("figures done")
