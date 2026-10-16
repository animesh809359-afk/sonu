"""All figures (PNG, 200 dpi) for the workbook, the deck and the Word report."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

from common import WORK, cfg, load, present_dates, subset_label, v3_label, v5_label  # noqa: E402

FIG = WORK / "figures"
FIG.mkdir(exist_ok=True)
H_COL, D_COL = "#1baf7a", "#eb6834"          # healthy / diseased
CART_COL, RF_COL = "#2a78d6", "#eda100"      # selectors
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e5e4df"
SEQ = ["#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]      # ordinal blue ramp (V1, V3, V4, V5)
GUARD = "#d9d8d2"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": INK2,
                     "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.color": GRID, "grid.linewidth": 0.6, "legend.frameon": False,
                     "axes.titleweight": "bold", "axes.titlesize": 10, "savefig.dpi": 200,
                     "savefig.bbox": "tight", "lines.linewidth": 1.4})

def _try(name):
    try:
        return load(name)
    except FileNotFoundError:
        return None


D = load("data")
A = _try("partA")
K = _try("partK")
Cc = _try("partC")
spec, y, wl = D["spec"], D["y"], D["spec"].wl
F = D["folds"]
PD = present_dates(D)
SUBSET = subset_label(cfg())
N0, N1 = int((y == 0).sum()), int((y == 1).sum())
NP0, NP1 = len(set(D["groups"][y == 0])), len(set(D["groups"][y == 1]))
NSETS = len(F["V3"])
CFG_GUARD = {"R": [[990, 1010], [1795, 1835]], "D1": [[988, 1012], [1793, 1837]]}
done = []


def save(fig, name):
    fig.savefig(FIG / f"{name}.png")
    plt.close(fig)
    done.append(name)


def shade_guard(ax, kind="R"):
    for a, b in CFG_GUARD[kind]:
        ax.axvspan(a, b, color=GUARD, alpha=0.8, lw=0, zorder=0)


# ------------------------------------------------------------- F01 workflow
def f01_workflow():
    fig, ax = plt.subplots(figsize=(10, 6.2))
    ax.axis("off")
    boxes = [
        (0.5, 0.95, f"Leaf spectra ({SUBSET}): {len(PD)} date(s) × {NP0 + NP1} plots ({NP0} healthy, {NP1} white rust)\n{len(y)} unique leaves · ASD FieldSpec contact probe · 350–2500 nm", "#f0efec"),
        (0.5, 0.82, f"Step 0–1 · Data audit, duplicates removed, 400–2500 nm (water bands kept)\nimbalance 1 : {N1 / N0:.1f} → equal priors / balanced sampling throughout", "#f0efec"),
        (0.5, 0.69, "Tier 1 · Welch t-test + Benjamini–Hochberg FDR at every band\n(+ ANOVA, mixed model with plot, 1000 balanced subsets, −log10 p spectrum)", "#cde2fb"),
        (0.27, 0.54, "Tier 2a · CART (rpart)\nprior 0.5/0.5 · split variables", "#cde2fb"),
        (0.73, 0.54, "Tier 2b · Balanced Random Forest\nMDI importance peaks ≥ 10 nm apart", "#fde2c5"),
        (0.5, 0.415, "Tier 3 · Jeffries–Matusita distance on each selected band set (threshold 1.90 / 1.94)", "#cde2fb"),
        (0.5, 0.295, "Tier 4 · QDA with equal priors · error matrix, OA, BA, κ, PA, UA", "#cde2fb"),
        (0.5, 0.175, f"Validation · V1 leaf 10-fold · V2 plot-grouped · V3 nested plot-grouped {v3_label(F)} · V4 30 % plot hold-out × {len(F['V4'])}\nV5 {v5_label(F)} · Wilcoxon tests · band stability", "#f0efec"),
        (0.5, 0.045, "Part K · K0 denoising → K1 reflectance · K2 continuum removal · K3 indices (+K3b)\nK4 derivatives / REIP · K6 correlation → K5 CART vs RF  |  Part C · four tiers on the combined K1–K4 pool", "#e3f4ec"),
    ]
    for x, y0, t, c in boxes:
        w = 0.42 if x != 0.5 else 0.92
        ax.add_patch(FancyBboxPatch((x - w / 2, y0 - 0.04), w, 0.08, boxstyle="round,pad=0.008,rounding_size=0.015",
                                    fc=c, ec=INK2, lw=0.8, transform=ax.transAxes))
        ax.text(x, y0, t, ha="center", va="center", fontsize=8.6, color=INK, transform=ax.transAxes)
    arrows = [(0.5, 0.91, 0.5, 0.86), (0.5, 0.78, 0.5, 0.73), (0.45, 0.65, 0.3, 0.58), (0.55, 0.65, 0.7, 0.58),
              (0.3, 0.50, 0.45, 0.455), (0.7, 0.50, 0.55, 0.455), (0.5, 0.375, 0.5, 0.335), (0.5, 0.255, 0.5, 0.215),
              (0.5, 0.135, 0.5, 0.085)]
    for x0, y0, x1, y1 in arrows:
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0), xycoords="axes fraction",
                    arrowprops=dict(arrowstyle="-|>", color=INK2, lw=1))
    save(fig, "F01_workflow")


# ------------------------------------------------------------- F02 mean spectra
def f02_mean_spectra():
    fig, ax = plt.subplots(figsize=(8, 4))
    for c, col, lab in ((0, H_COL, "Healthy"), (1, D_COL, "Diseased (white rust)")):
        m, s = spec.R_raw[y == c].mean(0), spec.R_raw[y == c].std(0)
        ax.fill_between(wl, m - s, m + s, color=col, alpha=0.15, lw=0)
        ax.plot(wl, m, color=col, label=f"{lab} (n = {(y == c).sum()})")
    ax.set(xlabel="Wavelength (nm)", ylabel="Reflectance", xlim=(400, 2500), ylim=(0, None))
    ax.set_title(f"Mean reflectance of healthy and diseased leaves (± 1 SD), {SUBSET}", fontsize=9)
    ax.legend(loc="upper right")
    save(fig, "F02_mean_spectra")
    # by date (small multiples)
    fig, axs = plt.subplots(1, len(PD), figsize=(max(4.5, 3 * len(PD)), 3), sharey=True, squeeze=False)
    axs = axs[0]
    for ax, d in zip(axs, PD):
        m = D["dates"] == d
        for c, col in ((0, H_COL), (1, D_COL)):
            ax.plot(wl, spec.R_raw[m & (y == c)].mean(0), color=col, lw=1.1)
        ax.set_title(d, fontsize=9)
        ax.set_xlabel("Wavelength (nm)")
    axs[0].set_ylabel("Reflectance")
    axs[0].legend(["Healthy", "Diseased"], loc="upper right", fontsize=8)
    save(fig, "F02b_mean_spectra_by_date")


# ------------------------------------------------------------- F03 significance shading (Das Fig 4)
def f03_sig_regions():
    t1 = A["tier1"]
    fig, ax = plt.subplots(figsize=(8, 4))
    sig = t1["sig"].to_numpy()
    ax.fill_between(wl, 0, 1, where=sig, color="#c9c8c1", alpha=0.7, lw=0, step="mid",
                    transform=ax.get_xaxis_transform(), label="significant (Welch + FDR, q < 0.05)")
    ax.plot(wl, t1["mean0"], color=H_COL, label="Healthy")
    ax.plot(wl, t1["mean1"], color=D_COL, label="Diseased")
    ax.set(xlabel="Wavelength (nm)", ylabel="Reflectance", xlim=(400, 2500), ylim=(0, None))
    ax.set_title(f"Tier 1: {int(sig.sum())} of {len(sig)} bands differ significantly (grey)")
    ax.legend(loc="upper right")
    save(fig, "F03_tier1_significant_regions")


# ------------------------------------------------------------- F04 balanced-subset frequency (Das Fig 5)
def f04_frequency():
    t1 = A["tier1"]
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(8, 5), sharex=True, gridspec_kw={"height_ratios": [2, 1.3]})
    a1.fill_between(wl, 0, t1["balanced_pct"], color="#b5b4ad", lw=0, step="mid")
    a1.axhline(95, color=INK2, lw=0.8, ls="--")
    a1.text(2490, 96, "95 %", ha="right", va="bottom", fontsize=8, color=INK2)
    a1.set(ylabel="Balanced subsets with\nsignificant difference (%)", ylim=(0, 102))
    a1.set_title(f"Significance frequency over 1000 balanced subsets ({N0} vs {N0} leaves)")
    a2.plot(wl, spec.R_raw.mean(0), color=INK)
    a2.set(xlabel="Wavelength (nm)", ylabel="Mean reflectance", xlim=(400, 2500))
    save(fig, "F04_tier1_frequency")


# ------------------------------------------------------------- F05 -log10 p
def f05_log10p():
    t1 = A["tier1"]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(wl, -np.log10(np.clip(t1["p"], 1e-300, 1)), color=INK2, lw=1, label="Welch p (unadjusted)")
    ax.plot(wl, -np.log10(np.clip(t1["q"], 1e-300, 1)), color=CART_COL, label="Welch q (BH-FDR)")
    ax.plot(wl, -np.log10(np.clip(t1["mm_q"], 1e-300, 1)), color=D_COL, label="mixed-model q (plot effect)")
    ax.axhline(-np.log10(0.05), color=INK, lw=0.8, ls="--")
    ax.text(1100, -np.log10(0.05) + 1.0, "p or q = 0.05 (dashed)", fontsize=8, color=INK, ha="center")
    ax.set(xlabel="Wavelength (nm)", ylabel="−log₁₀(p)", xlim=(400, 2500), ylim=(0, None))
    ax.set_title("Significance spectrum: −log₁₀(p) against wavelength (healthy vs diseased)")
    ax.legend(loc="upper left")
    save(fig, "F05_minus_log10_p")


# ------------------------------------------------------------- tree diagram
def _fmt_rule(rule):
    """Readable thresholds: derivative values shown × 10³ (per nm)."""
    import re
    m = re.match(r"^(.*?)(<|>=)\s*(-?[0-9.eE+-]+)$", str(rule).strip())
    if not m:
        return rule
    var, op, val = m.group(1).strip(), m.group(2), float(m.group(3))
    if var.startswith("D1_") or var.startswith("D2_"):
        return f"{var} {op} {val * 1000:.4g}×10⁻³"
    return f"{var} {op} {val:.4g}"

def tree_diagram(frame, name, title):
    fr = frame.copy()
    fr["node"] = fr["node"].astype(int)
    nodes = set(fr["node"])
    pos, xs = {}, [0]

    def walk(n, d):
        if 2 * n in nodes:
            walk(2 * n, d + 1)
            walk(2 * n + 1, d + 1)
            pos[n] = ((pos[2 * n][0] + pos[2 * n + 1][0]) / 2, d)
        else:
            pos[n] = (xs[0], d)
            xs[0] += 1
    walk(1, 0)
    maxd = max(p[1] for p in pos.values())
    fig, ax = plt.subplots(figsize=(max(9, 1.05 * xs[0]), 0.9 * (maxd + 1) + 1))
    ax.axis("off")
    lab = fr.set_index("node")
    for n, (x, d) in pos.items():
        if 2 * n in pos:
            for ch in (2 * n, 2 * n + 1):
                ax.plot([x, pos[ch][0]], [-d, -pos[ch][1]], color=INK2, lw=0.7, zorder=1)
    for n, (x, d) in pos.items():
        r = lab.loc[n]
        leaf = 2 * n not in pos
        cls = r["pred"]
        col = H_COL if cls == "H" else D_COL
        if leaf:
            txt = f"{'H' if cls == 'H' else 'D'}\n{int(r['nH'])}/{int(r['nD'])}"
            ax.text(x, -d, txt, ha="center", va="center", fontsize=6.5, color=INK, zorder=3,
                    bbox=dict(boxstyle="round,pad=0.25", fc="#bfe9d9" if cls == "H" else "#f9d2c2", ec="none"))
        else:
            rule = _fmt_rule(lab.loc[2 * n, "label"])
            ax.text(x, -d, rule, ha="center", va="center", fontsize=6.8, color=INK, zorder=3,
                    bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=INK2, lw=0.6))
    ax.set_title(title + "\n(left branch = rule true; leaves: predicted class, healthy/diseased leaves)", fontsize=9)
    save(fig, name)


# ------------------------------------------------------------- CART cp plot
def f07_cp():
    cp = A["cart_full"]["cptable"]
    fig, ax = plt.subplots(figsize=(6, 3.4))
    ax.errorbar(cp["nsplit"] + 1, cp["xerror"], yerr=cp["xstd"], color=CART_COL, marker="o", ms=4, capsize=2,
                label="plot-grouped CV error ± SE")
    ax.plot(cp["nsplit"] + 1, cp["rel error"], color=INK2, ls="--", marker="s", ms=3, label="resubstitution error")
    i = cp["xerror"].idxmin()
    ax.axhline(cp.at[i, "xerror"] + cp.at[i, "xstd"], color=D_COL, lw=0.8)
    ax.text(cp["nsplit"].max() + 1, cp.at[i, "xerror"] + cp.at[i, "xstd"] + 0.01, "1-SE rule", ha="right", fontsize=8, color=INK)
    ax.set(xlabel="Size of tree (terminal nodes)", ylabel="Relative error")
    ax.set_title("CART complexity table (rpart, prior 0.5/0.5)")
    ax.legend()
    save(fig, "F07_cart_cp")


def f08_reselection():
    t = A["cart_table"]
    fig, ax = plt.subplots(figsize=(7, 3.2))
    x = np.arange(len(t))
    ax.bar(x - 0.2, t["Bootstrap re-selection (±10 nm)"] * 100, 0.38, color="#86b6ef", label="200 plot-level bootstraps")
    ax.bar(x + 0.2, t["Nested-CV re-selection (±10 nm)"] * 100, 0.38, color=CART_COL, label=f"{NSETS} nested-CV training sets")
    ax.set_xticks(x, [f"{int(b)}" for b in t["Band (nm)"]], rotation=90)
    ax.set(xlabel="CART band (nm)", ylabel="Re-selected (%)", ylim=(0, 105))
    ax.set_title("Stability of the CART bands (a band within ± 10 nm counts)")
    ax.legend(loc="upper right", fontsize=8)
    save(fig, "F08_cart_reselection")


def f09_incremental(R, name, title):
    inc = R["tier3_incremental"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.4))
    for tag, col in (("CART", CART_COL), ("RF", RF_COL)):
        if f"{tag} J–M" in inc:
            s = inc.dropna(subset=[f"{tag} J–M"])
            a1.plot(s["Features used"], s[f"{tag} J–M"], color=col, marker="o", ms=3, label=f"{tag} order")
            a2.plot(s["Features used"], s[f"{tag} QDA BA"] * 100, color=col, marker="o", ms=3, label=f"{tag} order")
    for v in (1.90, 1.94):
        a1.axhline(v, color=INK2, lw=0.7, ls="--")
    a1.text(1, 1.91, "1.90 / 1.94", fontsize=7, color=INK2)
    a1.set(xlabel="Features used", ylabel="J–M distance (0–2)", ylim=(0, 2.05), title="Tier 3: J–M as features are added")
    a2.set(xlabel="Features used", ylabel="QDA balanced accuracy (%)", title="Tier 4: QDA (V1) as features are added")
    a1.legend()
    a2.legend()
    fig.suptitle(title, fontsize=10, fontweight="bold", y=1.03)
    save(fig, name)


def f11_validation_qda():
    v = A["validation_qda_cart"]
    fig, ax = plt.subplots(figsize=(8, 3.4))
    sch = list(dict.fromkeys(v["Scheme"]))
    x = np.arange(len(sch))
    for k, (pri, col) in enumerate((("equal (corrected)", CART_COL), ("sample (uncorrected)", "#b5b4ad"))):
        s = v[v.Priors == pri].set_index("Scheme").reindex(sch)
        ax.bar(x + (k - 0.5) * 0.38, s["BA"] * 100, 0.36, color=col, label=f"priors {pri}",
               yerr=s["BA_SD"].fillna(0) * 100, capsize=2, error_kw={"lw": 0.7})
        for xi, b, e in zip(x + (k - 0.5) * 0.38, s["BA"] * 100, s["BA_SD"].fillna(0) * 100):
            ax.text(xi, b + e + 0.8, f"{b:.1f}", ha="center", fontsize=7, color=INK)
    ax.set_xticks(x, [s.split(" · ")[0] for s in sch])
    ax.set(ylabel="Balanced accuracy (%)", ylim=(40, 100))
    ax.set_title("QDA on the CART bands under each validation scheme")
    ax.legend(loc="upper right", fontsize=8)
    save(fig, "F11_validation_qda_cart")


def f12_rf_importance(R, name, title):
    imp = R["rf_importance"]
    ser = imp[imp["series"].isin(["WV", "R", "D1"])]
    fig, ax = plt.subplots(figsize=(8, 3.6))
    for s, col in (("WV", "#9a998f"), ("R", "#9a998f"), ("D1", "#6da7ec")):
        q = ser[ser.series == s].sort_values("position")
        if len(q):
            xs_, ys_ = q["position"].to_numpy(float), q["importance"].to_numpy(float) * 1000
            gap = np.where(np.diff(xs_) > 1.5)[0]          # break the line at excluded bands
            xs_ = np.insert(xs_, gap + 1, np.nan)
            ys_ = np.insert(ys_, gap + 1, np.nan)
            ax.plot(xs_, ys_, color=col, lw=0.8,
                    label={"WV": "importance (Tier-1 bands)", "R": "K1 reflectance bands", "D1": "K4 first-derivative bands"}[s])
    rf = imp.set_index("name").loc[R["sets"][R["rf_name"]]]
    rf = rf[rf.series.isin(["WV", "R", "D1"])]
    ax.scatter(rf["position"], rf["importance"] * 1000, color=RF_COL, edgecolor=INK, lw=0.5, s=28, zorder=3,
               label=f"{R['rf_name']} peaks")
    cb = [v for v in R["sets"][R["cart_name"]] if v in imp.set_index("name").index]
    cbt = imp.set_index("name").loc[cb]
    cbt = cbt[cbt.series.isin(["WV", "R", "D1"])]
    ax.scatter(cbt["position"], np.full(len(cbt), ax.get_ylim()[1] * 0.97), marker="v", color=CART_COL, s=26,
               label=f"{R['cart_name']} bands", zorder=3)
    ax.set(xlabel="Wavelength (nm)", ylabel="Mean decrease in Gini × 1000", xlim=(400, 2500))
    ax.set_title(title)
    ax.legend(loc="center", fontsize=7.5, bbox_to_anchor=(0.55, 0.6))
    save(fig, name)


def pipelines_chart(R, name, title):
    v = R["validation"]
    pipes = ["CART classifier", "RF classifier", "QDA on CART features", "QDA on RF features"]
    schemes = [s for s in ("V1", "V3", "V4", "V5") if s in set(v["Scheme"])]
    lab = {"V1": "V1 leaf 10-fold (optimistic)", "V3": "V3 nested plot-grouped", "V4": "V4 30 % plot hold-out",
           "V5": f"V5 {v5_label(F, short=True)}"}
    fig, ax = plt.subplots(figsize=(9, 3.6))
    x = np.arange(len(pipes))
    w = 0.8 / len(schemes)
    for k, s in enumerate(schemes):
        q = v[v.Scheme == s].set_index("Pipeline").reindex(pipes)
        xs = x + (k - (len(schemes) - 1) / 2) * w
        ax.bar(xs, q["BA"] * 100, w * 0.92, color=SEQ[k], label=lab[s])
        for xi, b in zip(xs, q["BA"] * 100):
            ax.text(xi, b + 0.8, f"{b:.1f}", ha="center", fontsize=6.5, color=INK)
    ax.set_xticks(x, pipes)
    ax.set(ylabel="Balanced accuracy (%)", ylim=(40, 100))
    ax.set_title(title)
    ax.legend(loc="upper left", fontsize=7.5, ncol=2)
    save(fig, name)


def f14_stability(R, name, title):
    rc, rr = R["stability"]["reselect_CART"], R["stability"]["reselect_RF"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.2), sharey=True)
    for ax, t, col, ttl in ((a1, rc, CART_COL, f"{R['cart_name']}: re-selected by CART"),
                            (a2, rr, RF_COL, f"{R['rf_name']}: re-selected by RF")):
        k = [c for c in t.columns if c.startswith("Re-selected by " + ("CART" if t is rc else "RF"))][0]
        ax.bar(np.arange(len(t)), t[k] * 100, color=col)
        ax.set_xticks(np.arange(len(t)), [str(v).replace("WV", "") for v in t["Feature"]], rotation=90, fontsize=7)
        ax.set_title(ttl)
    a1.set_ylabel("Training sets (%)")
    fig.suptitle(title, fontsize=10, fontweight="bold", y=1.04)
    save(fig, name)


# ------------------------------------------------------------- K figures
def f15_k0():
    k0 = K["k0"]
    wf = k0["wl_full"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.4))
    m = (wf >= 980) & (wf <= 1020)
    m2 = (wf >= 1770) & (wf <= 1850)
    for k, d in enumerate(PD):
        col = SEQ[k % len(SEQ)]
        a1.plot(wf[m], k0["date_means"][d][m], color=col, label=d)
        a1.plot(wf[m], k0["date_means_sc"][d][m], color=col, ls="--", lw=0.9)
        a2.plot(wf[m2], k0["date_means_sc"][d][m2], color=col, label=d)
    a1.axvline(1000.5, color=INK2, lw=0.6)
    a2.axvline(1800.5, color=INK2, lw=0.6)
    a2.axvspan(1795, 1835, color=GUARD, lw=0, zorder=0)
    a1.set(xlabel="Wavelength (nm)", ylabel="Mean reflectance", title="(a) 1000/1001 nm join\nraw (solid) vs splice-corrected (dashed)")
    a2.set(xlabel="Wavelength (nm)", title="(b) 1800/1801 nm join after correction\n(grey = guard zone)")
    a1.legend(fontsize=7)
    save(fig, "F15_K0_detector_joins")


def f16_k1_auc():
    fig, ax = plt.subplots(figsize=(8, 3.4))
    shade_guard(ax, "D1")
    ax.plot(wl, K["k1_all"]["AUC"], color=INK, lw=1, label="K1 smoothed reflectance")
    ax.plot(wl, K["d1_all"]["AUC"], color=CART_COL, lw=0.9, label="K4 first derivative")
    ax.axhline(0.7, color=INK2, lw=0.6, ls="--")
    ax.set(xlabel="Wavelength (nm)", ylabel="AUC (direction-free)", xlim=(400, 2500), ylim=(0.5, 1))
    ax.set_title("Single-band sensitivity: AUC of every band (grey = detector guard zones, excluded)")
    ax.legend(loc="upper left")
    save(fig, "F16_K1_K4_band_auc")


def f17_cr():
    cur = K["cr_curves"]
    fig, axs = plt.subplots(2, 3, figsize=(10, 5))
    for ax, (nm, (x, h, d)) in zip(axs.ravel(), cur.items()):
        ax.plot(x, h, color=H_COL, label="Healthy")
        ax.plot(x, d, color=D_COL, label="Diseased")
        ax.set_title(nm, fontsize=9)
        ax.set_xlabel("Wavelength (nm)")
    axs[0, 0].set_ylabel("Continuum-removed reflectance")
    axs[1, 0].set_ylabel("Continuum-removed reflectance")
    axs[0, 0].legend(fontsize=7)
    fig.suptitle("K2: mean continuum-removed absorption features", fontweight="bold", y=1.0)
    fig.tight_layout()
    save(fig, "F17_K2_continuum")


def f18_vi():
    t = K["k3"].sort_values("AUC")
    fig, ax = plt.subplots(figsize=(6, 6.5))
    col = [D_COL if d == "D > H" else H_COL for d in t["Direction"]]
    ax.barh(t["name"], t["AUC"], color=col)
    for yv, (a, b) in enumerate(zip(t["AUC"], t["BA plot-grouped CV"])):
        ax.text(a + 0.003, yv, f"{a:.3f}", va="center", fontsize=6.5, color=INK)
    ax.set(xlim=(0.5, max(0.9, t["AUC"].max() + 0.05)), xlabel="AUC (direction-free)")
    ax.set_title("K3: the 31 vegetation indices ranked by AUC\n(orange: higher in diseased, aqua: lower in diseased)")
    ax.grid(axis="y", visible=False)
    save(fig, "F18_K3_indices")


def f19_ndsi():
    w, H = K["k3b_heat"]
    fig, ax = plt.subplots(figsize=(6.4, 5.4))
    edges = np.r_[w[0] - 2.5, (w[:-1] + w[1:]) / 2, w[-1] + 2.5]
    im = ax.pcolormesh(edges, edges, H, cmap="Blues", vmin=0.5, vmax=np.nanmax(H), shading="flat")
    best = K["k3b_top"].iloc[0]
    ax.plot(best["Band j (nm)"], best["Band i (nm)"], marker="o", ls="none", mfc="none", mec=D_COL, ms=11, mew=1.6,
            label=f"best pair ({best['Band i (nm)']:.0f}, {best['Band j (nm)']:.0f}) — straddles 1800 nm join")
    if "k3b_jf" in K:
        b2 = K["k3b_jf"]["top"].iloc[0]
        ax.plot(b2["Band j (nm)"], b2["Band i (nm)"], marker="s", ls="none", mfc="none", mec=INK, ms=10, mew=1.6,
                label=f"best join-free pair ({b2['Band i (nm)']:.0f}, {b2['Band j (nm)']:.0f})")
    for j in (1000.5, 1800.5):
        ax.axvline(j, color=INK2, lw=0.5, ls=":")
        ax.axhline(j, color=INK2, lw=0.5, ls=":")
    ax.set(xlabel="Band j (nm)", ylabel="Band i (nm)", aspect="equal")
    ax.set_title("K3b: AUC of NDSI(i, j) for every band pair\n(5 nm grid; guard zones excluded; dotted = detector joins)")
    ax.grid(False)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.13), fontsize=7.5)
    fig.colorbar(im, ax=ax, label="AUC", shrink=0.8)
    save(fig, "F19_K3b_ndsi_heatmap")


def f20_d1():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.4), gridspec_kw={"width_ratios": [2, 1]})
    for ax, rng in ((a1, (400, 2500)), (a2, (650, 780))):
        shade_guard(ax, "D1")
        m = (wl >= rng[0]) & (wl <= rng[1])
        ax.plot(wl[m], spec.D1[y == 0][:, m].mean(0) * 1000, color=H_COL, label="Healthy")
        ax.plot(wl[m], spec.D1[y == 1][:, m].mean(0) * 1000, color=D_COL, label="Diseased")
        ax.set(xlim=rng, xlabel="Wavelength (nm)")
    a1.set(ylabel="First derivative (× 10⁻³ nm⁻¹)", title="Mean first-derivative spectra")
    a2.set(title="Red edge (650–780 nm)")
    a1.legend()
    save(fig, "F20_K4_first_derivative")


def f21_reip():
    X = K["reip_X"]
    names = ["Max. first derivative", "Linear 4-point", "Lagrangian", "Linear extrapolation"]
    fig, axs = plt.subplots(1, 2, figsize=(10, 3.6))
    ax = axs[0]
    data, pos, cols = [], [], []
    for k in range(4):
        data += [X[y == 0, k], X[y == 1, k]]
        pos += [3 * k, 3 * k + 1]
        cols += [H_COL, D_COL]
    bp = ax.boxplot(data, positions=pos, widths=0.8, patch_artist=True, showfliers=False)
    for p, c in zip(bp["boxes"], cols):
        p.set(facecolor=c, alpha=0.55, edgecolor=INK2)
    for med in bp["medians"]:
        med.set(color=INK)
    ax.set_xticks([3 * k + 0.5 for k in range(4)], names, fontsize=7.5)
    ax.set(ylabel="REIP (nm)", title="REIP by method (aqua healthy, orange diseased)")
    st = K["reip_strata"]
    q = st[(st.Stratum == "Date") & (st.Method.str.contains("Lagrangian"))]
    ax2 = axs[1]
    x = np.arange(len(q))
    ax2.plot(x, q["Mean REIP healthy (nm)"], color=H_COL, marker="o", label="Healthy")
    ax2.plot(x, q["Mean REIP diseased (nm)"], color=D_COL, marker="o", label="Diseased")
    order = PD
    q = q.set_index("Level").reindex(order).reset_index()
    ax2.cla()
    ax2.plot(x, q["Mean REIP healthy (nm)"], color=H_COL, marker="o", label="Healthy")
    ax2.plot(x, q["Mean REIP diseased (nm)"], color=D_COL, marker="o", label="Diseased")
    ax2.set_xticks(x, q["Level"])
    ax2.set(ylabel="Mean REIP (nm), Lagrangian", title="REIP by measurement date")
    ax2.legend()
    save(fig, "F21_K4_REIP")


def f22_corr():
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(8, 5.2), sharex=True)
    for ax, tag, ttl in ((a1, "R", "Reflectance"), (a2, "D1", "First derivative")):
        t = K["corr"][tag]
        shade_guard(ax, "D1" if tag == "D1" else "R")
        for k, c in enumerate([c for c in t.columns if c.startswith("r ") and c[2].isdigit()]):
            ax.plot(t["Wavelength (nm)"], t[c], color=SEQ[k], lw=0.6, alpha=0.8, label=c.replace("r ", ""))
        ax.plot(t["Wavelength (nm)"], t["r (point-biserial)"], color=INK, lw=1.3, label="all leaves")
        ax.axhline(0, color=INK2, lw=0.6)
        ax.set(ylabel="r with disease status", title=ttl)
    a2.set(xlabel="Wavelength (nm)", xlim=(400, 2500))
    h, l = a1.get_legend_handles_labels()
    fig.suptitle("K6: correlation spectra (point-biserial r, diseased = 1)", fontweight="bold", y=1.0)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.legend(h, l, ncol=5, fontsize=8, loc="lower center", bbox_to_anchor=(0.5, 0.0))
    save(fig, "F22_K6_correlation")


def f23_k5():
    t = K["k5"]
    groups = list(dict.fromkeys(t["Group"]))
    lab = {"G0": "Full spectrum", "G1": "K1 reflectance", "G2": "K2 continuum", "G3": "K3 indices",
           "G4": "K4 derivatives", "G5": "K1–K4 combined", "G6": "K4 + guard\n(artefact)", "GS": "K-selected 15"}
    fig, axs = plt.subplots(1, 2, figsize=(11, 3.6), sharey=True)
    for ax, sch in zip(axs, ("CV", "Hold-out")):
        x = np.arange(len(groups))
        for k, (clf, col) in enumerate((("CART", CART_COL), ("RF", RF_COL))):
            q = t[(t.Classifier == clf) & (t.Scheme == sch)].set_index("Group").reindex(groups)
            ax.bar(x + (k - 0.5) * 0.38, q["BA"] * 100, 0.36, color=col, label=clf)
            for xi, b in zip(x + (k - 0.5) * 0.38, q["BA"] * 100):
                ax.text(xi, b + 0.8, f"{b:.0f}", ha="center", fontsize=6.5, color=INK)
        ax.set_xticks(x, [lab[g] for g in groups], rotation=45, ha="right", fontsize=7.5)
        ax.set(ylim=(40, 100), title="Plot-grouped CV (V3)" if sch == "CV" else "30 % plot hold-out (V4)")
    axs[0].set_ylabel("Balanced accuracy (%)")
    axs[0].legend(loc="upper left")
    fig.suptitle("K5: CART vs Random Forest on each feature group", fontweight="bold", y=1.03)
    save(fig, "F23_K5_cart_vs_rf")


def f24_composition(R=None, name="F24_C_composition", title="Part C: which feature families the selectors pick from the combined pool"):
    R = Cc if R is None else R
    comp = R["composition"].set_index("Feature type")
    sets = [c for c in comp.columns if c.startswith(("CART", "RF"))]
    fig, ax = plt.subplots(figsize=(8, 3.4))
    x = np.arange(len(comp))
    w = 0.8 / len(sets)
    cols = [CART_COL, "#86b6ef", RF_COL, "#f6cf73", "#c98500"]
    for k, s in enumerate(sets):
        ax.bar(x + (k - (len(sets) - 1) / 2) * w, comp[s], w * 0.92, color=cols[k % len(cols)], label=s)
    ax.set_xticks(x, comp.index, rotation=15, fontsize=8)
    ax.set(ylabel="Features selected")
    ax.set_title(title)
    ax.legend(fontsize=7.5)
    save(fig, name)


def f25_c_top(R=None, name="F25_C_top_importance", title="Part C: 30 most important features of the combined pool (Balanced RF)"):
    R = Cc if R is None else R
    imp = R["rf_importance"].nlargest(30, "importance").iloc[::-1]
    tcol = {"K1 band reflectance": "#9a998f", "Raw reflectance band": "#52514e", "K2 continuum removal": "#1baf7a", "K3 vegetation index": "#e87ba4",
            "K4 first-derivative band": CART_COL, "K4 edge parameter": RF_COL}
    fig, ax = plt.subplots(figsize=(7, 6.5))
    ax.barh(imp["name"], imp["importance"] * 1000, color=[tcol.get(t, INK2) for t in imp["type"]])
    from matplotlib.patches import Patch
    present = [t for t in tcol if t in set(imp["type"])]
    ax.legend(handles=[Patch(color=tcol[t], label=t) for t in present], fontsize=8, loc="lower right")
    ax.set(xlabel="Mean decrease in Gini × 1000")
    ax.set_title(title)
    ax.grid(axis="y", visible=False)
    ax.tick_params(axis="y", labelsize=7)
    save(fig, name)


def f38_compare(CR):
    """Balanced accuracy of the four pipelines: Part A (raw reflectance), Part C′ (raw + K2–K4), Part C (K1 + K2–K4)."""
    pipes = ["CART classifier", "RF classifier", "QDA on CART features", "QDA on RF features"]
    sets = (("Part A · raw reflectance", A, "#9a998f"), ("Part C′ · raw + K2–K4", CR, "#52514e"), ("Part C · K1 + K2–K4", Cc, CART_COL))
    fig, axs = plt.subplots(1, 3, figsize=(12, 3.6), sharey=True)
    for ax, sch, ttl in zip(axs, ("V3", "V4", "V5"), ("V3 nested plot-grouped CV", "V4 30 % plot hold-out", "V5 new date + new plots")):
        x = np.arange(len(pipes))
        w = 0.8 / len(sets)
        for k, (lab, R, col) in enumerate(sets):
            v = R["validation"]
            q = v[v.Scheme == sch].set_index("Pipeline").reindex(pipes)
            xs = x + (k - 1) * w
            ax.bar(xs, q["BA"] * 100, w * 0.92, color=col, label=lab, yerr=q["BA_SD"] * 100 if sch != "V5" else None,
                   error_kw=dict(lw=0.6, capsize=1.5, ecolor=INK2))
            for xi, b in zip(xs, q["BA"] * 100):
                ax.text(xi, 41, f"{b:.0f}", ha="center", fontsize=6, color="white", rotation=90, va="bottom")
        ax.set_xticks(x, [p.replace(" features", "").replace(" classifier", "\nclassifier") for p in pipes], fontsize=7)
        ax.set_title(ttl)
        ax.set_ylim(40, 100)
    axs[0].set_ylabel("Balanced accuracy (%)")
    axs[0].legend(fontsize=7, loc="upper left")
    fig.suptitle("Does the combined pool need K1 or raw reflectance? Same folds, same settings", fontsize=10, fontweight="bold", y=1.03)
    save(fig, "F38_A_CR_C_comparison")


def f29_synthesis():
    rows = []
    CR = _try("partCR")
    labs = {"A": "Reflectance", "C": "Combined pool", "CR": "Raw + K2–K4 pool"}
    for lab, R in (("A", A), ("C", Cc)) + ((("CR", CR),) if CR is not None else ()):
        v = R["validation"]
        for p in ["CART classifier", "RF classifier", "QDA on CART features", "QDA on RF features"]:
            s = v[(v.Pipeline == p)].set_index("Scheme")
            rows.append((f"{labs[lab]} · {p}", s.loc["V3", "BA"], s.loc["V3", "BA_SD"],
                         s.loc["V4", "BA"], s.loc["V4", "BA_SD"]))
    t = K["k5"]
    for g, nm in (("G2", "K2 continuum"), ("G3", "K3 indices"), ("G4", "K4 derivatives"), ("G5", "K1–K4 combined")):
        for clf in ("RF",):
            a = t[(t.Group == g) & (t.Classifier == clf) & (t.Scheme == "CV")].iloc[0]
            b = t[(t.Group == g) & (t.Classifier == clf) & (t.Scheme == "Hold-out")].iloc[0]
            rows.append((f"K5 {nm} · RF classifier", a["BA"], a["BA_SD"], b["BA"], b["BA_SD"]))
    df = pd.DataFrame(rows, columns=["Approach", "V3", "V3sd", "V4", "V4sd"]).sort_values("V3")
    fig, ax = plt.subplots(figsize=(8, 5.4 + 0.25 * max(0, len(df) - 12)))
    yv = np.arange(len(df))
    ax.errorbar(df["V3"] * 100, yv + 0.12, xerr=df["V3sd"] * 100, fmt="o", color=CART_COL, ms=5, capsize=2, label="V3 nested plot-grouped CV (± SD over repeats)")
    ax.errorbar(df["V4"] * 100, yv - 0.12, xerr=df["V4sd"] * 100, fmt="s", color=RF_COL, mec=INK, mew=0.4, ms=5, capsize=2, label="V4 30 % plot hold-out (± SD over splits)")
    ax.set_yticks(yv, df["Approach"], fontsize=7.5)
    ax.set(xlabel="Balanced accuracy (%)")
    ax.set_title("All approaches on new plots (ranked by V3)")
    ax.legend(fontsize=7.5, loc="lower right")
    save(fig, "F29_synthesis")


def f30_lodo():
    rows = []
    dates = F["V5_dates"]
    for lab, R in (("Reflectance", A), ("Combined pool", Cc)):
        for p in ["RF classifier", "QDA on CART features", "QDA on RF features"]:
            lst = R["preds"][(p, "V5")]
            for te, pp, ss, rep, i in lst:
                d = D["folds"]["V5"][i]["date"]
                rows.append((f"{lab} · {p}", d, rep, te, pp))
    df = pd.DataFrame(rows, columns=["Pipeline", "Date", "rep", "te", "pp"])
    out = []
    for (p, d), g in df.groupby(["Pipeline", "Date"]):
        bas = []
        for _, r in g.iterrows():
            yt = y[r["te"]]
            if len(np.unique(yt)) < 2:          # BA needs both classes
                continue
            bas.append(0.5 * ((r["pp"][yt == 1] == 1).mean() + (r["pp"][yt == 0] == 0).mean()))
        out.append((p, d, np.mean(bas) if bas else np.nan))
    o = pd.DataFrame(out, columns=["Pipeline", "Date", "BA"])
    fig, ax = plt.subplots(figsize=(8, 3.6))
    pipes = list(dict.fromkeys(o["Pipeline"]))
    x = np.arange(len(dates))
    w = 0.8 / len(pipes)
    pal = [CART_COL, "#86b6ef", "#0d366b", RF_COL, "#f6cf73", "#c98500"]
    for k, p in enumerate(pipes):
        q = o[o.Pipeline == p].set_index("Date").reindex(dates)
        ax.bar(x + (k - (len(pipes) - 1) / 2) * w, q["BA"] * 100, w * 0.92, color=pal[k], label=p)
    unit = "date" if F.get("V5_by", "Date") == "Date" else "variety"
    ax.set_xticks(x, [f"held-out {unit}\n{d}" for d in dates], fontsize=8)
    ax.set(ylabel="Balanced accuracy (%)", ylim=(40, 100))
    ax.set_title("V5: trained on the other dates, tested on the held-out date in new plots" if unit == "date"
                 else "V5: trained on the other varieties, tested on the held-out variety")
    ax.legend(fontsize=7, ncol=2, loc="upper left")
    save(fig, "F30_V5_leave_one_date_out")
    return o


if __name__ == "__main__":
    import sys
    only = sys.argv[1] if len(sys.argv) > 1 else "all"
    if only in ("all", "A"):
        f01_workflow()
        f02_mean_spectra()
        f03_sig_regions()
        f04_frequency()
        f05_log10p()
        tree_diagram(A["cart_full"]["frame"], "F06_cart_tree", f"Tier 2: CART tree on the Tier-1 bands ({A['cart_name']})")
        if "frame_1se" in A["cart_full"]:
            tree_diagram(A["cart_full"]["frame_1se"], "F06b_cart_tree_1se", "Tier 2: 1-SE pruned CART tree")
        f07_cp()
        f08_reselection()
        f09_incremental(A, "F09_tier3_tier4_incremental", "Part A: CART vs RF band order (reflectance)")
        f11_validation_qda()
        f12_rf_importance(A, "F12_A1_rf_importance", "A1: Balanced RF importance spectrum with the RF peaks and CART bands")
        pipelines_chart(A, "F13_A3_pipelines", "A3: CART and RF as classifiers and as band selectors for QDA (reflectance)")
        f14_stability(A, "F14_A4_stability", f"A4: re-selection in the {NSETS} nested training sets (± 10 nm)")
    if only in ("all", "K"):
        f15_k0()
        f16_k1_auc()
        f17_cr()
        f18_vi()
        f19_ndsi()
        f20_d1()
        f21_reip()
        f22_corr()
        f23_k5()
    if only in ("all", "C"):
        tree_diagram(Cc["cart_full"]["frame"], "F26_C_cart_tree", f"Part C, Tier 2: CART tree on the combined pool ({Cc['cart_name']})")
        f24_composition()
        f25_c_top()
        f09_incremental(Cc, "F27_C_incremental", "Part C: CART vs RF feature order (combined pool)")
        pipelines_chart(Cc, "F28_C_pipelines", "Part C: four pipelines on the combined pool")
        f14_stability(Cc, "F28b_C_stability", f"Part C: re-selection in the {NSETS} nested training sets")
        f29_synthesis()
        lodo = f30_lodo()
        lodo.to_pickle(WORK / "lodo_by_date.pkl")
    if only in ("all", "CR"):
        CR = load("partCR")
        tree_diagram(CR["cart_full"]["frame"], "F32_CR_cart_tree", f"Part C′, Tier 2: CART tree on raw + K2 + K3 + K4 ({CR['cart_name']})")
        f25_c_top(CR, "F33_CR_top_importance", "Part C′: 30 most important features of raw + K2 + K3 + K4 (Balanced RF)")
        f24_composition(CR, "F34_CR_composition", "Part C′: which feature families the selectors pick from raw + K2 + K3 + K4")
        f09_incremental(CR, "F35_CR_incremental", "Part C′: CART vs RF feature order (raw + K2 + K3 + K4)")
        pipelines_chart(CR, "F36_CR_pipelines", "Part C′: four pipelines on raw + K2 + K3 + K4")
        f14_stability(CR, "F37_CR_stability", f"Part C′: re-selection in the {NSETS} nested training sets")
        f38_compare(CR)
    print(len(done), "figures:", done)
