"""Figures for the design-based validation (reads results/r48.pkl, results/d48.pkl and results/polys_xy.pkl)."""
import os, pickle, numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MPoly
from matplotlib.path import Path as MPath
import matplotlib.patheffects as pe
R = pickle.load(open("results/r48.pkl", "rb"))
D = pickle.load(open(os.environ.get("D48", "results/d48.pkl"), "rb"))
polys = pickle.load(open("results/polys_xy.pkl", "rb"))
td = D["design"]
CH, CD, INK, INK2, GRID = "#1baf7a", "#eb6834", "#0b0b0b", "#52514e", "#e4e3df"
BLK = {"C": CH, "R3": "#f2b48f", "R2": "#eb6834", "R1": "#a8401a"}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "axes.spines.top": False,
                     "axes.spines.right": False, "legend.frameon": False, "savefig.dpi": 200, "figure.facecolor": "white",
                     "axes.titleweight": "bold", "axes.titlesize": 12})
def inside_point(q):
    c = q.mean(0); path = MPath(q)
    if path.contains_point(c): return c
    gx, gy = np.meshgrid(np.linspace(q[:, 0].min(), q[:, 0].max(), 60), np.linspace(q[:, 1].min(), q[:, 1].max(), 60))
    pts = np.column_stack([gx.ravel(), gy.ravel()]); ins = pts[path.contains_points(pts)]
    off = np.array([[a, b] for a in (-0.6, 0, 0.6) for b in (-0.6, 0, 0.6)])
    deep = ins[[all(path.contains_points(p + off)) for p in ins]]
    cand = deep if len(deep) else ins
    return cand[np.argmin(((cand - c) ** 2).sum(1))]

# design map
fig, ax = plt.subplots(figsize=(8.2, 6.4))
for k, q in polys.items():
    ax.add_patch(MPoly(q, closed=True, fc=BLK[td.block[k]], ec="white", lw=1.0))
    c = inside_point(q)
    ax.text(c[0], c[1], f"{k}\n{td.variety[k]}·{td.date[k]}", ha="center", va="center", fontsize=7, color=INK, fontweight="bold",
            path_effects=[pe.withStroke(linewidth=2.2, foreground="white")])
allq = np.vstack(list(polys.values()))
ax.set_xlim(allq[:, 0].min() - 1, allq[:, 0].max() + 1); ax.set_ylim(allq[:, 1].min() - 1, allq[:, 1].max() + 1); ax.set_aspect("equal")
for b, nm in (("C", "C: control (healthy), plots 1–12"), ("R3", "R3: inoculated, plots 13–24"), ("R2", "R2: inoculated, plots 25–36"), ("R1", "R1: inoculated, plots 37–48")):
    ax.plot([], [], "s", color=BLK[b], ms=10, label=nm)
ax.legend(loc="lower right", fontsize=9); ax.set_xlabel("East (m)"); ax.set_ylabel("North (m)")
ax.set_title("Experimental layout: block · variety (V1–V3) · inoculation date (D1–D4)")
fig.tight_layout(); fig.savefig("results/f13_design.png"); plt.close(fig)

# negative control: grouped bars per block pair (control vs inoculated, then inoculated vs inoculated)
NC = D["NC"]
order = [("C", "R3"), ("C", "R2"), ("C", "R1"), ("R3", "R2"), ("R2", "R1"), ("R3", "R1")]
fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.4), sharey=True)
for ax, key, ttl in ((axes[0], "BA", "Spectrum-level balanced accuracy"), (axes[1], "plotBA", "Plot-level balanced accuracy")):
    xs = np.arange(len(order))
    for j, (t2, hatch) in enumerate((("CART", ""), ("RF", "//"))):
        m = [NC[p_][t2][key][0] for p_ in order]; sd_ = [NC[p_][t2][key][1] for p_ in order]
        cols = [CD if p_[0] == "C" else "#9a9a9a" for p_ in order]
        ax.bar(xs + (j - 0.5) * 0.38, m, 0.36, yerr=sd_, color=cols, hatch=hatch, edgecolor="white", capsize=3, error_kw=dict(lw=1, ecolor=INK2))
        for x_, v in zip(xs + (j - 0.5) * 0.38, m): ax.text(x_, 0.31, f"{v:.2f}", ha="center", fontsize=8, color="white", fontweight="bold")
    ax.set_xticks(xs, [f"{a_} vs {b_}\n{NC[(a_, b_)]['distance_m']:.0f} m" for a_, b_ in order], fontsize=9)
    ax.axhline(0.5, color=INK, ls=":", lw=1); ax.set_title(ttl); ax.set_ylim(0.3, 1.0); ax.axvline(2.5, color=INK2, lw=0.8)
axes[0].set_ylabel("Balanced accuracy (mean ± SD, 10 reps)")
from matplotlib.patches import Patch
axes[0].legend(handles=[Patch(color=CD, label="control vs inoculated"), Patch(color="#9a9a9a", label="inoculated vs inoculated (negative control)"),
                        Patch(fc="white", ec=INK2, label="CART (plain)"), Patch(fc="white", ec=INK2, hatch="//", label="RF (hatched)")],
               loc="upper left", fontsize=8.5, ncol=1)
fig.tight_layout(); fig.savefig("results/f14_negative_control.png"); plt.close(fig)

# detection by block (CV2, share of a plot's predictions = diseased)
fig, axes = plt.subplots(1, 2, figsize=(12, 4.2), sharey=True)
for ax, t2 in zip(axes, ("CART", "RF")):
    tab = D["DET"][t2]["table"]; order = ["C", "R3", "R2", "R1"]
    data = [tab[tab.block == b].pD_V2.values for b in order]
    bp = ax.boxplot(data, widths=0.55, patch_artist=True, showfliers=False, medianprops=dict(color=INK))
    for p_, b in zip(bp["boxes"], order): p_.set_facecolor(BLK[b]); p_.set_alpha(0.75)
    for i, (b, d_) in enumerate(zip(order, data)):
        ax.scatter(np.full(len(d_), i + 1) + np.random.default_rng(i).uniform(-0.12, 0.12, len(d_)), d_, s=14, color=INK, zorder=3)
    ax.set_xticks(range(1, 5), ["C\n(control)", "R3", "R2", "R1"]); ax.axhline(0.5, color=INK, ls=":", lw=1)
    ax.set_title(f"{t2}-{D['DET'][t2]['strategy']}: share of each plot's spectra predicted diseased"); ax.set_xlabel("Block (west → east)")
axes[0].set_ylabel("Share predicted diseased (CV2, 10 reps)"); axes[0].set_ylim(0, 1)
fig.tight_layout(); fig.savefig("results/f15_detection_block.png"); plt.close(fig)
print("design figures done")
