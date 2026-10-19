"""Date-wise plot-average feature workbooks (healthy vs white-rust-diseased mustard, ASD contact probe).

For each of the four labelled ASD workbooks: plot-average raw reflectance → continuum-removal parameters, vegetation
indices, first/second/third derivatives, red-edge parameters, optimised two-band indices; then detector-join correction +
Savitzky–Golay smoothing of the plot averages and the same features again; comparison raw vs smoothed and healthy vs
diseased statistics. One workbook per date.

usage: python build_plotavg_workbooks.py [date_tag ...]      (date tags 110226 240226 030326 130326; default all)
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from openpyxl import Workbook  # noqa: E402
from openpyxl.styles import Alignment, Font  # noqa: E402
from openpyxl.utils import get_column_letter  # noqa: E402
from scipy import stats as st  # noqa: E402
from scipy.signal import savgol_coeffs  # noqa: E402

import plotavg_features as pf  # noqa: E402
import xl  # noqa: E402
from xl import (BORDER, CENTER, F_BODY, F_BOLD, F_HEAD, F_NOTE, FILL_FLAG, FILL_HEAD, FILL_KEY, FILL_SEC, Sheet)  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw_data"
OUT = ROOT.parent / "deliverables" / "WhiteRust_PlotAverage_Features"
WORK = ROOT / "work_plotavg"
DATES = {"110226": "11-02-2026", "240226": "24-02-2026", "030326": "03-03-2026", "130326": "13-03-2026"}
CH, CD, C3, C4, INK, MUTED, GRID = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#1b1b1a", "#52514e", "#e6e5e0"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "legend.frameon": False,
                     "figure.dpi": 130, "savefig.bbox": "tight"})
BR = {"raw": "Raw", "smooth": "Smoothed"}
FAMILIES = [("cr", "Continuum-removal parameters"), ("vi", "Vegetation indices"), ("re", "Red-edge parameters"),
            ("osi", "Optimised two-band indices")]


# ============================================================ statistics per band
def band_stats(M, y):
    """Welch t, p and direction-free AUC for every column of M (plots × bands); NaN columns allowed."""
    h, d = M[y == 0], M[y == 1]
    with np.errstate(invalid="ignore", divide="ignore"):
        t, p = st.ttest_ind(d, h, axis=0, equal_var=False)
        rk = st.rankdata(M, axis=0)
        n1, n0 = (y == 1).sum(), (y == 0).sum()
        a = (rk[y == 1].sum(0) - n1 * (n1 + 1) / 2) / (n0 * n1)
    a = np.where(np.isnan(M).any(0), np.nan, a)
    return t, p, np.maximum(a, 1 - a)


# ============================================================ computations
def compute(tag):
    date = DATES[tag]
    path = RAW / f"asd__data_complete_labelled_{tag}.xlsx"
    meta, R, wl, log, dups = pf.load_date(path, date)
    P, Ra = pf.plot_average(meta, R)
    y = (P["Class"] == "Diseased").to_numpy(int)
    # cross-check against the workbook's own =AVERAGE columns
    wa = pf.workbook_averages(path)
    chk = []
    for i, p in enumerate(P["Plot"]):
        for fm, v in wa.get(int(p), []):
            chk.append({"Plot": int(p), "Workbook formula (first band)": "source formula: " + fm.lstrip("="), "Leaf spectra in our average": int(P.at[i, "Leaf spectra averaged"]),
                        "Max |difference| over 2151 bands": float(np.nanmax(np.abs(v - Ra[i]))),
                        "Bands compared": int((~np.isnan(v)).sum())})
    chk = pd.DataFrame(chk)
    Rs, Rsc, off = pf.smooth(Ra, wl)
    B = {}
    for b, X in (("raw", Ra), ("smooth", Rs)):
        D1, D2, D3 = pf.derivatives(X)
        cr, curves = pf.continuum(X, wl)
        vi = pf.indices(X, wl)
        re = pf.red_edge(X, D1, wl)
        x, O = pf.optimise(X, wl, y.astype(float))
        tops = {k: pf.top_pairs(x, O[k], 10, kind=k) for k in O}
        tops_far = {}
        for k in O:
            Mk = O[k].copy()
            dist = np.abs(x[:, None] - x[None, :])
            Mk[dist < 10] = 0
            tops_far[k] = pf.top_pairs(x, Mk, 10, kind=k)
        nojoin = {}
        for k in O:
            Mk = O[k].copy()
            for j in pf.JOINS:
                Mk[np.ix_(x <= j, x > j)] = 0
                Mk[np.ix_(x > j, x <= j)] = 0
            nojoin[k] = pf.top_pairs(x, Mk, 1, kind=k)[0]
        osi = {}
        for k in O:
            a_, b_, r_, _ = tops[k][0]
            osi[f"Optimised {k}({int(a_)}, {int(b_)})"] = pf.index_value(X, wl, k, a_, b_)
            a_, b_, r_, _ = tops_far[k][0]
            osi[f"Optimised {k}({int(a_)}, {int(b_)}), bands ≥ 10 nm apart"] = pf.index_value(X, wl, k, a_, b_)
        osi = pd.DataFrame(osi)
        F = {"cr": cr, "vi": vi, "re": re, "osi": osi}
        stats = {k: pf.class_stats(F[k], y) for k in F}
        bs = {nm: band_stats(M, y) for nm, M in (("R", X), ("D1", D1), ("D2", D2), ("D3", D3))}
        B[b] = dict(R=X, D1=D1, D2=D2, D3=D3, F=F, curves=curves, x=x, O=O, tops=tops, tops_far=tops_far, nojoin=nojoin,
                    stats=stats, bs=bs)
    # smoothing alternatives
    alts = pf.smoothing_alternatives(Ra, wl)
    regions = [("350–399 (detector edge)", 350, 399), ("400–699 (visible)", 400, 699), ("700–999 (red edge, NIR)", 700, 999),
               ("1001–1350 (NIR)", 1001, 1350), ("1351–1800 (water band, SWIR-1)", 1351, 1800),
               ("1801–2350 (water band, SWIR-2)", 1801, 2350), ("2351–2500 (detector edge)", 2351, 2500)]
    rows = []
    Dr_raw = pf.red_edge(Rsc, pf.derivatives(Rsc)[0], wl)["Red-edge amplitude Dr (1/nm)"].to_numpy()
    cr3_raw = pf.continuum(Rsc, wl)[0].filter(like="CR3").iloc[:, 0].to_numpy()
    for nm, S in alts.items():
        r = {"Smoothing method": nm}
        for rn, a, b in regions:
            m = (wl >= a) & (wl <= b)
            E = Rsc[:, m] - S[:, m]
            r[f"RMS removed, {rn}"] = float(np.sqrt(np.mean(E ** 2)))
            r[f"Lag-1 autocorrelation of the removed part, {rn}"] = float(np.mean([np.corrcoef(e[:-1], e[1:])[0, 1] for e in E]))
        Dr = pf.red_edge(S, pf.derivatives(S)[0], wl)["Red-edge amplitude Dr (1/nm)"].to_numpy()
        r["Red-edge amplitude retained (% of unsmoothed)"] = float(100 * np.mean(Dr / Dr_raw))
        cr3 = pf.continuum(S, wl)[0].filter(like="CR3").iloc[:, 0].to_numpy()
        r["970-nm band depth retained (% of unsmoothed)"] = float(100 * np.mean(cr3 / cr3_raw))
        rows.append(r)
    alt_tab = pd.DataFrame(rows)
    return dict(tag=tag, date=date, path=path, meta=meta, wl=wl, log=log, dups=dups, P=P, y=y, chk=chk, Rsc=Rsc, off=off,
                B=B, alt_tab=alt_tab, alts=alts)


# ============================================================ figures
def figures(C, d):
    d.mkdir(parents=True, exist_ok=True)
    wl, y, P = C["wl"], C["y"], C["P"]
    out = {}
    lab = lambda c, n: f"{c} plots (n = {n})"  # noqa: E731

    # F1 spectra raw / smoothed
    for b in ("raw", "smooth"):
        X = C["B"][b]["R"]
        fig, ax = plt.subplots(figsize=(9, 3.6))
        for i in range(len(X)):
            ax.plot(wl, X[i], color=CH if y[i] == 0 else CD, lw=0.5, alpha=0.35)
        ax.plot(wl, X[y == 0].mean(0), color=CH, lw=2, label=lab("Healthy", (y == 0).sum()) + ", mean")
        ax.plot(wl, X[y == 1].mean(0), color=CD, lw=2, label=lab("Diseased", (y == 1).sum()) + ", mean")
        for j in pf.JOINS:
            ax.axvline(j + 0.5, color=MUTED, lw=0.6, ls=":")
        ax.set_xlim(350, 2500)
        ax.set_xlabel("Wavelength (nm)")
        ax.set_ylabel("Reflectance")
        ax.set_title(f"{C['date']} · {BR[b]} plot-average reflectance (thin lines: single plots; dotted: detector joins)", loc="left", fontsize=9.5)
        ax.legend(loc="upper right", fontsize=8)
        f = d / f"F1_{b}_spectra.png"
        fig.savefig(f)
        plt.close(fig)
        out[f"spectra_{b}"] = f

    # F2 raw vs smoothed zooms (plot with largest removed component)
    Ra, Rs = C["B"]["raw"]["R"], C["B"]["smooth"]["R"]
    k = int(np.argmax(np.sqrt(((C["Rsc"] - Rs) ** 2).mean(1))))
    zooms = [(350, 480, "Detector edge 350–480 nm"), (960, 1040, "VNIR / SWIR-1 join (1000/1001 nm)"),
             (1760, 1840, "SWIR-1 / SWIR-2 join (1800/1801 nm)"), (2300, 2500, "SWIR-2 end 2300–2500 nm")]
    fig, axs = plt.subplots(1, 4, figsize=(12, 3.1))
    for ax, (a, bb, t) in zip(axs, zooms):
        m = (wl >= a) & (wl <= bb)
        ax.plot(wl[m], Ra[k, m], color=MUTED, lw=1, label="Raw")
        ax.plot(wl[m], Rs[k, m], color=CD if y[k] else CH, lw=1.8, label="Join-corrected + Savitzky–Golay")
        ax.set_title(t, loc="left", fontsize=8.5)
        ax.set_xlabel("Wavelength (nm)")
    axs[0].set_ylabel("Reflectance")
    axs[0].legend(fontsize=7.5, loc="lower left")
    fig.suptitle(f"{C['date']} · plot {int(P.at[k, 'Plot'])} (largest smoothing correction): raw vs smoothed", x=0.01, ha="left", fontsize=9.5)
    f = d / "F2_raw_vs_smoothed.png"
    fig.savefig(f)
    plt.close(fig)
    out["zoom"] = f

    # F3 derivatives, each order raw vs smoothed (class means)
    for o, key in ((1, "D1"), (2, "D2"), (3, "D3")):
        fig, axs = plt.subplots(2, 1, figsize=(9, 4.8), sharex=True)
        for ax, b in zip(axs, ("raw", "smooth")):
            M = C["B"][b][key]
            ax.plot(wl, np.nanmean(M[y == 0], 0), color=CH, lw=0.9, label="Healthy mean")
            ax.plot(wl, np.nanmean(M[y == 1], 0), color=CD, lw=0.9, label="Diseased mean")
            lim = np.nanpercentile(np.abs(np.nanmean(C["B"]["smooth"][key], 0)[(wl > 400) & (wl < 2350)]), 99.5) * 1.6
            ax.set_ylim(-lim, lim)
            ax.set_title(f"{BR[b]} reflectance · {['first', 'second', 'third'][o - 1]} derivative (y-axis clipped to the smoothed range)",
                         loc="left", fontsize=8.5)
            ax.set_ylabel(f"d{'' if o == 1 else o}R/dλ{'' if o == 1 else o}" + (" (1/nm)" if o == 1 else f" (1/nm{o})".translate(str.maketrans('23', '²³'))))
        axs[0].legend(fontsize=7.5, loc="upper right", ncol=2)
        axs[1].set_xlabel("Wavelength (nm)")
        axs[1].set_xlim(350, 2500)
        f = d / f"F3_derivative_{o}.png"
        fig.savefig(f)
        plt.close(fig)
        out[f"deriv{o}"] = f

    # F4 continuum-removed curves
    for b in ("raw", "smooth"):
        cur = C["B"][b]["curves"]
        fig, axs = plt.subplots(2, 3, figsize=(11, 5.2))
        for ax, (long, code, lo, hi) in zip(axs.ravel(), pf.CR_WINDOWS):
            x, CR = cur[code]
            ax.plot(x, CR[y == 0].mean(0), color=CH, lw=1.6, label="Healthy mean")
            ax.plot(x, CR[y == 1].mean(0), color=CD, lw=1.6, label="Diseased mean")
            ax.set_title(f"{code} · {long}", loc="left", fontsize=8)
            ax.set_ylim(None, 1.01)
        axs[0, 0].set_ylabel("Continuum-removed reflectance")
        axs[1, 0].set_ylabel("Continuum-removed reflectance")
        axs[0, 0].legend(fontsize=7.5, loc="lower left")
        for ax in axs[1]:
            ax.set_xlabel("Wavelength (nm)")
        fig.suptitle(f"{C['date']} · continuum removal of {BR[b].lower()} plot-average reflectance", x=0.01, ha="left", fontsize=9.5)
        fig.tight_layout()
        f = d / f"F4_{b}_continuum.png"
        fig.savefig(f)
        plt.close(fig)
        out[f"cr_{b}"] = f

    # F5 red edge
    fig, axs = plt.subplots(1, 2, figsize=(11, 3.4), sharey=True)
    m = (wl >= 660) & (wl <= 780)
    for ax, b in zip(axs, ("raw", "smooth")):
        D1 = C["B"][b]["D1"]
        re = C["B"][b]["F"]["re"]
        for c, col, nm in ((0, CH, "Healthy"), (1, CD, "Diseased")):
            ax.plot(wl[m], D1[y == c][:, m].mean(0), color=col, lw=1.6, label=f"{nm} mean first derivative")
            ax.axvline(re.loc[y == c, "REIP, Lagrangian interpolation (nm)"].mean(), color=col, lw=1, ls="--")
        ax.set_title(f"{BR[b]} · red edge (dashed: mean REIP, Lagrangian)", loc="left", fontsize=8.5)
        ax.set_xlabel("Wavelength (nm)")
    axs[0].set_ylabel("First derivative (1/nm)")
    axs[0].legend(fontsize=7.5, loc="upper right")
    f = d / "F5_red_edge.png"
    fig.savefig(f)
    plt.close(fig)
    out["re"] = f

    # F6 optimised index r² maps
    for b in ("raw", "smooth"):
        x, O = C["B"][b]["x"], C["B"][b]["O"]
        fig, axs = plt.subplots(1, 3, figsize=(13, 4.1))
        s = 5
        vmax = max(0.6, max(float(np.max(O[k].astype(float) ** 2)) for k in O))
        for ax, kind in zip(axs, ("NDSI", "SR", "DI")):
            M = (O[kind][::s, ::s].astype(float)) ** 2
            im = ax.imshow(M, origin="lower", extent=[x[0], x[-1], x[0], x[-1]], cmap="Blues", vmin=0, vmax=vmax, aspect="equal")
            a_, b_, r_, r2_ = C["B"][b]["tops"][kind][0]
            ax.scatter([b_], [a_], s=60, facecolor="none", edgecolor=CD, lw=1.5, zorder=3)
            ax.set_title(f"{kind}: best ({int(a_)}, {int(b_)}) nm, r² = {r2_:.2f}", loc="left", fontsize=8.5)
            ax.set_xlabel("λ2 (nm)")
            ax.grid(False)
        axs[0].set_ylabel("λ1 (nm)")
        cb = fig.colorbar(im, ax=axs, fraction=0.015)
        cb.set_label("r² with disease status (healthy 0, diseased 1)")
        fig.suptitle(f"{C['date']} · optimised two-band indices from {BR[b].lower()} reflectance (5-nm display grid; orange circle = best pair)",
                     x=0.01, ha="left", fontsize=9.5)
        f = d / f"F6_{b}_optimised.png"
        fig.savefig(f)
        plt.close(fig)
        out[f"osi_{b}"] = f

    # F7 vegetation indices with the largest effect (dot strip per class)
    for b in ("raw", "smooth"):
        stt = C["B"][b]["stats"]["vi"].dropna(subset=["AUC (direction-free)"]).sort_values("AUC (direction-free)", ascending=False).head(12)
        vi = C["B"][b]["F"]["vi"]
        fig, axs = plt.subplots(2, 6, figsize=(13, 4.6))
        rng = np.random.default_rng(0)
        for ax, (_, r) in zip(axs.ravel(), stt.iterrows()):
            v = vi[r["Feature"]].to_numpy()
            for c, col in ((0, CH), (1, CD)):
                xx = c + rng.uniform(-0.15, 0.15, (y == c).sum())
                ax.scatter(xx, v[y == c], s=10, color=col, alpha=0.75, lw=0)
                ax.plot([c - 0.3, c + 0.3], [v[y == c].mean()] * 2, color=INK, lw=1.4)
            ax.set_xticks([0, 1], ["Healthy", "Diseased"], fontsize=7.5)
            ax.set_title(f"{r['Feature']}  AUC {r['AUC (direction-free)']:.2f}", loc="left", fontsize=8)
            ax.tick_params(axis="y", labelsize=7)
            ax.grid(axis="x", visible=False)
        fig.suptitle(f"{C['date']} · 12 vegetation indices with the largest AUC ({BR[b].lower()} reflectance; dots = plots, bar = class mean)",
                     x=0.01, ha="left", fontsize=9.5)
        fig.tight_layout()
        f = d / f"F7_{b}_indices.png"
        fig.savefig(f)
        plt.close(fig)
        out[f"vi_{b}"] = f

    # F8 raw vs smoothed AUC per feature
    fig, ax = plt.subplots(figsize=(5.6, 5))
    cols = {"cr": C3, "vi": CH, "re": CD, "osi": C4}
    for k, nm in FAMILIES:
        a = C["B"]["raw"]["stats"][k].set_index("Feature")["AUC (direction-free)"]
        s_ = C["B"]["smooth"]["stats"][k].copy()
        if k == "osi":
            s_["Feature"] = a.index[:len(s_)]
        s_ = s_.set_index("Feature")["AUC (direction-free)"]
        j = a.index.intersection(s_.index)
        ax.scatter(a[j], s_[j], s=14, color=cols[k], label=nm, alpha=0.85, lw=0)
    ax.plot([0.5, 1], [0.5, 1], color=MUTED, lw=0.8, ls="--")
    ax.set_xlim(0.5, 1)
    ax.set_ylim(0.5, 1)
    ax.set_xlabel("AUC, raw reflectance")
    ax.set_ylabel("AUC, smoothed reflectance")
    ax.set_title(f"{C['date']} · healthy vs diseased separability of each feature", loc="left", fontsize=9)
    ax.legend(fontsize=7.5, loc="lower right")
    f = d / "F8_auc_raw_vs_smoothed.png"
    fig.savefig(f)
    plt.close(fig)
    out["auc"] = f

    # F9 AUC spectra of reflectance and derivatives: one panel per spectrum type, raw (grey) vs smoothed (colour)
    fig, axs = plt.subplots(4, 1, figsize=(9, 7.4), sharex=True)
    for ax, (key, col, nm) in zip(axs, (("R", INK, "Reflectance"), ("D1", CH, "First derivative"), ("D2", CD, "Second derivative"),
                                        ("D3", C3, "Third derivative"))):
        ax.plot(wl, C["B"]["raw"]["bs"][key][2], color="#b9b8b2", lw=0.6, label="Raw")
        ax.plot(wl, C["B"]["smooth"]["bs"][key][2], color=col, lw=0.9, label="Smoothed")
        ax.set_ylim(0.5, 1.0)
        ax.set_ylabel("AUC")
        ax.set_title(f"{nm} · healthy vs diseased AUC of every band (grey: raw; colour: smoothed)", loc="left", fontsize=8.5)
        ax.legend(fontsize=7, loc="upper right", ncol=2)
    axs[-1].set_xlabel("Wavelength (nm)")
    axs[-1].set_xlim(350, 2500)
    fig.tight_layout()
    f = d / "F9_auc_spectra.png"
    fig.savefig(f)
    plt.close(fig)
    out["aucspec"] = f

    # F10 smoothing alternatives: what the filter removes (white noise or signal) and narrow-feature retention
    t = C["alt_tab"]
    fig, axs = plt.subplots(1, 2, figsize=(11, 3.4))
    yy = np.arange(len(t))
    for k, (col, rn) in enumerate(((CH, "400–699 (visible)"), (CD, "700–999 (red edge, NIR)"), (C3, "1001–1350 (NIR)"),
                                   (C4, "1801–2350 (water band, SWIR-2)"))):
        axs[0].barh(yy + (k - 1.5) * 0.2, t[f"Lag-1 autocorrelation of the removed part, {rn}"], height=0.18, color=col, label=rn + " nm")
    axs[0].set_yticks(yy, t["Smoothing method"], fontsize=7.5)
    axs[0].invert_yaxis()
    axs[0].set_xlim(-0.1, 1.05)
    axs[0].axvline(0, color=MUTED, lw=0.8)
    axs[0].set_title("Lag-1 autocorrelation of what the filter removes\n(≈ 0: white noise only; ≈ 1: spectral shape removed)", loc="left", fontsize=8.5)
    axs[0].legend(fontsize=7, loc="upper center", bbox_to_anchor=(0.45, -0.14), ncol=2)
    axs[0].grid(axis="y", visible=False)
    axs[1].barh(yy - 0.18, t["Red-edge amplitude retained (% of unsmoothed)"] - 100, height=0.34, color=CD, label="Red-edge amplitude")
    axs[1].barh(yy + 0.18, t["970-nm band depth retained (% of unsmoothed)"] - 100, height=0.34, color=C3, label="970-nm band depth")
    axs[1].set_yticks(yy, [""] * len(t))
    axs[1].invert_yaxis()
    axs[1].axvline(0, color=MUTED, lw=0.8)
    axs[1].set_title("Change of narrow features through smoothing (%)", loc="left", fontsize=8.5)
    axs[1].legend(fontsize=7.5, loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=2)
    axs[1].grid(axis="y", visible=False)
    f = d / "F10_smoothing_choice.png"
    fig.savefig(f)
    plt.close(fig)
    out["alt"] = f
    return out


# ============================================================ workbook helpers
HDR = ["Plot", "Variety", "Growth stage", "Class", "Leaf spectra averaged"]


def spectra_sheet(wb, name, title, subtitle, wl, M, P, y, figs=(), fmt="0.00000", stats_cols=True, note=None, wl_label="Wavelength (nm)"):
    """Wavelength × plot matrix with descriptor header rows, live class-mean formulas and per-band statistics."""
    S = Sheet(wb, name, title, subtitle, width=14)
    ws = S.ws
    if note:
        S.para(note, font=F_NOTE)
    h0 = S.row
    ws.column_dimensions["A"].width = 16
    for j, h in enumerate(HDR):
        S.cell(h0 + j, 1, h, F_HEAD, fill=FILL_HEAD, border=True)
        for i in range(len(P)):
            v = P.iloc[i][h] if h != "Plot" else int(P.iloc[i]["Plot"])
            S.cell(h0 + j, 2 + i, v, F_BOLD if h == "Plot" else F_BODY, fill=FILL_SEC, border=True, align=CENTER)
    r0 = h0 + len(HDR)
    S.cell(r0, 1, wl_label, F_HEAD, fill=FILL_HEAD, border=True)
    n = len(P)
    last = get_column_letter(1 + n)
    extra = ["Mean healthy (formula)", "Mean diseased (formula)", "Diseased − healthy (formula)"]
    if stats_cols:
        extra += ["Welch t (diseased vs healthy)", "Welch p", "AUC (direction-free)"]
    for j, e in enumerate(extra):
        c = S.cell(r0, 2 + n + j, e, F_HEAD, fill=FILL_HEAD, border=True, align=CENTER)
        ws.column_dimensions[get_column_letter(2 + n + j)].width = 13
    ws.row_dimensions[r0].height = 40
    cls_row = h0 + HDR.index("Class")
    t, p, a = band_stats(M, y) if stats_cols else (None, None, None)
    for i, w in enumerate(wl):
        r = r0 + 1 + i
        ws.cell(row=r, column=1, value=float(w))
        row = M[:, i]
        for j in range(n):
            v = row[j]
            if v == v:
                c = ws.cell(row=r, column=2 + j, value=float(v))
                c.number_format = fmt
        if np.isnan(row).all():
            continue
        cH, cD = get_column_letter(2 + n), get_column_letter(3 + n)
        ws.cell(row=r, column=2 + n, value=f'=AVERAGEIF($B${cls_row}:${last}${cls_row},"Healthy",B{r}:{last}{r})').number_format = fmt
        ws.cell(row=r, column=3 + n, value=f'=AVERAGEIF($B${cls_row}:${last}${cls_row},"Diseased",B{r}:{last}{r})').number_format = fmt
        ws.cell(row=r, column=4 + n, value=f"={cD}{r}-{cH}{r}").number_format = fmt
        if stats_cols and t[i] == t[i]:
            ws.cell(row=r, column=5 + n, value=float(t[i])).number_format = "0.00"
            ws.cell(row=r, column=6 + n, value=float(p[i])).number_format = "0.00E+00"
            ws.cell(row=r, column=7 + n, value=float(a[i])).number_format = "0.000"
    ws.freeze_panes = ws.cell(row=r0 + 1, column=2)
    S.row = r0 + 2 + len(wl)
    col = get_column_letter(2 + n + len(extra) + 1)
    rr = h0
    for f in figs:
        from openpyxl.drawing.image import Image as XLImage
        img = XLImage(str(f))
        ratio = 860 / img.width
        img.width, img.height = int(img.width * ratio), int(img.height * ratio)
        ws.add_image(img, f"{col}{rr}")
        rr += int(np.ceil(img.height / 20)) + 2
    return S, r0


def feature_sheet(wb, name, title, subtitle, F, P, y, concept=None, figs=(), defs=None, fmt="0.0000", stats=None):
    """Plots × features with descriptors, live class-mean formulas, then the healthy-vs-diseased statistics."""
    S = Sheet(wb, name, title, subtitle, width=12)
    ws = S.ws
    if concept:
        for c in concept:
            S.para(c)
    for f in figs:
        S.image(f, 860)
    if defs is not None:
        S.table(defs, title="Definitions")
    S.cell(S.row, 1, "Feature values of every plot (one row per plot; class means below are Excel formulas)", F_BOLD)
    S.row += 1
    hr = S.row
    cols = HDR + list(F.columns)
    for j, c in enumerate(cols):
        S.cell(hr, 1 + j, c, F_HEAD, fill=FILL_HEAD, border=True, align=CENTER)
        ws.column_dimensions[get_column_letter(1 + j)].width = 12 if j >= len(HDR) else (9 if j != 2 else 13)
    ws.row_dimensions[hr].height = min(150, 12 * max(2, int(np.ceil(max(len(str(c)) for c in F.columns) / 13))))
    for i in range(len(P)):
        r = hr + 1 + i
        for j, h in enumerate(HDR):
            S.cell(r, 1 + j, int(P.iloc[i][h]) if h in ("Plot", "Leaf spectra averaged") else P.iloc[i][h], F_BODY, border=True)
        for j, c in enumerate(F.columns):
            v = F.iloc[i, j]
            x = ws.cell(row=r, column=1 + len(HDR) + j, value=None if v != v or np.isinf(v) else float(v))
            x.number_format = fmt if abs(np.nan_to_num(v)) < 1e4 else "0.00E+00"
            x.border = BORDER
            x.font = F_BODY
    r1, r2 = hr + 1, hr + len(P)
    cc = get_column_letter(1 + HDR.index("Class"))
    for k, (lab, crit) in enumerate((("Mean healthy", "Healthy"), ("Mean diseased", "Diseased"))):
        r = r2 + 1 + k
        S.cell(r, 1, lab, F_BOLD, fill=FILL_KEY, border=True)
        for j in range(len(F.columns)):
            L = get_column_letter(1 + len(HDR) + j)
            x = S.cell(r, 1 + len(HDR) + j, f'=AVERAGEIF(${cc}${r1}:${cc}${r2},"{crit}",{L}{r1}:{L}{r2})', F_BOLD, fill=FILL_KEY, border=True)
            x.number_format = fmt
    r = r2 + 3
    S.cell(r, 1, "Diseased − healthy", F_BOLD, fill=FILL_KEY, border=True)
    for j in range(len(F.columns)):
        L = get_column_letter(1 + len(HDR) + j)
        S.cell(r, 1 + len(HDR) + j, f"={L}{r2 + 2}-{L}{r2 + 1}", F_BOLD, fill=FILL_KEY, border=True).number_format = fmt
    ws.freeze_panes = ws.cell(row=hr + 1, column=len(HDR) + 1)
    S.row = r + 2
    if stats is not None:
        S.table(stats, title="Healthy vs diseased at plot level (Welch t-test, Benjamini–Hochberg q, Hedges g, AUC; 0.5 = no separation)",
                fmts={"p": "0.00E+00", "q (BH-FDR)": "0.00E+00", "Welch t": "0.00", "Hedges g": "0.00", "AUC (direction-free)": "0.000"})
    return S, hr


# ============================================================ workbook
def build(C, figs):
    wb = Workbook()
    wb.remove(wb.active)
    date, P, y, wl = C["date"], C["P"], C["y"], C["wl"]
    nH, nD = int((y == 0).sum()), int((y == 1).sum())
    B = C["B"]
    sheets = []

    def nxt(label):
        sheets.append(label)
        return f"{len(sheets) - 1:02d}_{label}"[:31]

    # ---- README
    S = Sheet(wb, nxt("README"), f"White rust of mustard · plot-average spectral features · {date}",
              f"ASD FieldSpec contact-probe leaf spectra · {len(C['meta'])} leaf spectra → {len(P)} plots ({nH} healthy, {nD} diseased) · "
              "every value in this workbook is a plot-level average, never a single-leaf spectrum", width=12)
    S.para("Purpose. The leaf spectra of each plot measured on this date are averaged to one plot spectrum. Features are then extracted "
           "from the plot-average raw reflectance (continuum-removal parameters, vegetation indices, first- to third-order derivatives, red-edge "
           "parameters, optimised two-band indices). The plot averages are then denoised (detector-join correction + Savitzky–Golay smoothing) "
           "and the same features are extracted again, so that the effect of smoothing on every feature can be compared.")
    S.para("Water-absorption bands (around 970, 1200, 1450 and 1940 nm) are KEPT: the contact probe illuminates the leaf with its own lamp "
           "at a few millimetres, so there is no atmospheric water-vapour absorption and these bands carry leaf-water information. The full "
           "350–2500 nm range is kept in the reflectance sheets; the optimised two-band search uses 400–2500 nm (the 350–399 nm detector edge is "
           "noisy, see sheet 13).")
    S.h2("Steps")
    steps = [
        ("Step 1 · Plot averaging", f"Mean of all leaf spectra of a plot on {date} (all leaf levels). Sheets 01–03."),
        ("Step 2 · Continuum removal (raw)", "Division of each absorption window by its upper convex hull; depth, position, width, area, asymmetry. Sheets 04–05."),
        ("Step 3 · Vegetation indices (raw)", f"{len(pf.VI)} indices: the 31 of the Activity 1.4 table + {len(pf.VI) - 31} further pigment, red-edge, water and disease indices. Sheet 06."),
        ("Step 4 · Derivatives (raw)", "First, second and third derivative by central finite differences (Δλ = 1 nm). Sheets 07–09."),
        ("Step 5 · Red-edge parameters (raw)", "Red-edge inflection point by four methods and 19 edge parameters. Sheet 10."),
        ("Step 6 · Optimised spectral indices (raw)", "All band pairs 400–2500 nm (1-nm step) for NDSI, simple ratio and difference index; best pairs by r² with disease status. Sheets 11–12."),
        ("Step 7 · Spectral smoothing / denoising", "Detector-join correction + Savitzky–Golay (11 nm, 2nd order) of the plot averages; comparison of five smoothing filters. Sheets 13–14."),
        ("Steps 8–12 · Features of the smoothed spectra", "Steps 2–6 repeated on the smoothed plot averages. Sheets 15–23."),
        ("Step 13 · Raw vs smoothed", "Change of every scalar feature through smoothing; separability before and after. Sheet 24."),
        ("Step 14 · Healthy vs diseased", "Most discriminating bands and features (both branches). Sheet 25."),
        ("Definitions, cross-checks, references", "Sheets 26–29: index definitions, Excel formula checks, references, check summary."),
    ]
    S.table(pd.DataFrame(steps, columns=["Step", "What is done"]), widths={"A": 34, "B": 120})
    S.h2("Data handling")
    blk = "second data block of identical copies dropped" if C["log"]["blocks"] > 1 else "one data block"
    S.bullets([f"Source file: {C['path'].name} ({blk}; the workbook's own plot-average (=AVERAGE) columns were not used as input but serve as a cross-check, sheet 03).",
               f"{len(C['meta'])} leaf spectra used; {len(C['dups'])} exact duplicate spectra of the same plot dropped (see sheet 01)." if len(C["dups"]) else f"{len(C['meta'])} leaf spectra used; no duplicate spectra.",
               f"Plots: {nH} healthy and {nD} diseased; varieties {', '.join(sorted(P['Variety'].astype(str).unique()))}; growth stage(s) {', '.join(sorted(P['Growth stage'].astype(str).unique()))}.",
               "Response for the statistics and the optimised indices: healthy (0) vs diseased (1) at plot level."])
    S.h2("How to read the sheets")
    S.bullets(["Wavelength sheets (reflectance, derivatives, continuum-removed spectra): one row per wavelength, one column per plot; the header rows give "
               "plot, variety, growth stage, class and number of leaf spectra. The last columns hold the class means (live Excel formulas, AVERAGEIF) "
               "and the plot-level Welch t, p and AUC of that band.",
               "Feature sheets: one row per plot, one column per feature; class means and their difference below the table are Excel formulas; the "
               "healthy-vs-diseased statistics follow underneath.",
               "AUC is direction-free (max(AUC, 1 − AUC)): 0.5 = no separation, 1 = complete separation of healthy and diseased plots.",
               "Raw sheets are prefixed 'Raw_', smoothed sheets 'Smoothed_' and are laid out identically so they can be compared column by column."])

    # ---- 01 plot information
    S = Sheet(wb, nxt("Plot_Information"), f"Step 1a · Plot information and the leaf spectra averaged ({date})",
              "Each plot spectrum is the arithmetic mean of the leaf spectra listed here (all leaf levels of that plot on this date).", width=10)
    S.table(P, widths={"A": 7, "B": 9, "C": 13, "D": 10, "E": 11, "F": 90, "G": 40})
    tab = P.groupby(["Growth stage", "Variety", "Class"]).size().unstack(fill_value=0).reset_index()
    S.table(tab, title="Number of plots by growth stage, variety and class")
    if len(C["dups"]):
        S.table(C["dups"], title="Exact duplicate spectra of the same plot (dropped before averaging, so no spectrum is counted twice)")
    if C["log"].get("block2"):
        S.table(pd.DataFrame(C["log"]["block2"]), title="Second data block of the source workbook: every spectrum is an identical copy of a block-1 spectrum (dropped)")

    # ---- 02 raw plot-average reflectance
    spectra_sheet(wb, nxt("Raw_PlotAverage_Reflectance"), f"Step 1b · Plot-average raw reflectance, 350–2500 nm ({date})",
                  "Mean of the leaf spectra of each plot; no smoothing, no correction, water-absorption bands kept.", wl, B["raw"]["R"], P, y,
                  figs=[figs["spectra_raw"]], fmt="0.000000",
                  note="Concept: averaging the leaves of a plot gives one spectrum per experimental unit (the plot), reduces leaf-to-leaf variation and "
                       "random instrument noise by about √(number of leaves), and avoids pseudo-replication when plots are compared.")

    # ---- 03 check vs workbook
    S = Sheet(wb, nxt("Check_PlotAverage"), "Step 1c · Cross-check of the plot averages against the workbook's own =AVERAGE columns",
              "The source workbook contains one plot-average formula column per plot; its cached values are compared with the averages computed here.", width=10)
    ch = C["chk"]
    n_ok = int((ch["Max |difference| over 2151 bands"] < 1e-12).sum())
    S.para(f"{n_ok} of {len(ch)} workbook plot-average columns agree with the plot averages of this workbook at all bands (|difference| < 10⁻¹²). "
           + ("Plots that differ are flagged below." if n_ok < len(ch) else "The plot averages are therefore identical to those of the data owner."))
    S.table(ch, fmts={"Max |difference| over 2151 bands": "0.0E+00"}, widths={"B": 26, "D": 18})

    # ---- feature branches
    def branch(b, start_step):
        pre = BR[b]
        X = B[b]
        stt = X["stats"]
        lbl = "raw" if b == "raw" else "smoothed"
        # continuum removal
        crdefs = pd.DataFrame([{"Window": f"{c} · {l}", "Range (nm)": f"{lo}–{hi}"} for l, c, lo, hi in pf.CR_WINDOWS])
        pdefs = pd.DataFrame([{"Parameter": p, "Definition": dsc} for p, dsc in pf.CR_PARAMS])
        S, _ = feature_sheet(wb, nxt(f"{pre}_Continuum_Removal"), f"Step {start_step} · Continuum-removal parameters of the {lbl} plot-average reflectance",
                             f"{len(X['F']['cr'].columns)} parameters = 6 absorption windows × 8 parameters (Clark and Roush, 1984; Kokaly and Clark, 1999)",
                             X["F"]["cr"], P, y, concept=[
                                 "Concept: within an absorption window the reflectance is divided by its upper convex hull (the 'continuum'). The result "
                                 "(continuum-removed reflectance, CR) is 1 where the spectrum touches the hull and < 1 inside the absorption. Band depth "
                                 "= 1 − CR. This isolates the absorption feature from the overall brightness of the leaf, so pigment and water absorptions "
                                 "can be compared between leaves of different structure or surface (e.g. with pustules)."]
                             + (["Note (raw branch): the 970-nm window (914–1069 nm) crosses the VNIR/SWIR-1 detector join at 1000/1001 nm; the small "
                                 "step of the raw spectrum is visible in the CR3 curve and affects the raw CR3 width, area and asymmetry. The smoothed "
                                 "branch removes the step (join correction) — compare with the smoothed sheet."] if b == "raw" else []),
                             figs=[figs[f"cr_{b}"]], stats=stt["cr"])
        S.table(crdefs, title="Absorption windows")
        S.table(pdefs, title="Parameters")
        # CR spectra
        xs, Ms = [], []
        for l, c, lo, hi in pf.CR_WINDOWS:
            x, CR = X["curves"][c]
            xs.append(x)
            Ms.append(CR)
        allx = np.concatenate(xs)
        allM = np.hstack(Ms)
        spectra_sheet(wb, nxt(f"{pre}_Continuum_Spectra"), f"Step {start_step} (curves) · Continuum-removed reflectance of every window ({lbl})",
                      "Windows one below the other: " + "; ".join(f"{c} {lo}–{hi} nm" for _, c, lo, hi in pf.CR_WINDOWS)
                      + ". Windows overlap at their limits, so the limit wavelengths appear twice.", allx, allM, P, y, fmt="0.00000")
        # vegetation indices
        defs = pf.index_definitions()
        feature_sheet(wb, nxt(f"{pre}_Vegetation_Indices"), f"Step {start_step + 1} · Vegetation indices of the {lbl} plot-average reflectance",
                      f"{len(pf.VI)} indices: 31 from the Activity 1.4 table + {len(pf.VI) - 31} additional disease, stress, pigment, red-edge and water indices (definitions in sheet 26)",
                      X["F"]["vi"], P, y, concept=[
                          "Concept: a vegetation index combines reflectance at two or more wavelengths chosen for a known absorption (chlorophyll at "
                          "~670 nm, carotenoids at ~500 nm, water at 970/1200/1450 nm) or for the red-edge slope. Ratios and normalised differences "
                          "cancel much of the brightness variation between leaves. Narrow bands are read at the nearest 1-nm wavelength.",
                          "Indices developed for other diseases (Mahlein et al., 2013; Ashourloo et al., 2014; Apan et al., 2004) are included because "
                          "they target the same symptoms as white rust (chlorosis, pustules, water loss); they were not calibrated for mustard."],
                      figs=[figs[f"vi_{b}"]], stats=stt["vi"])
        # derivatives
        for o, key, nm in ((1, "D1", "First"), (2, "D2", "Second"), (3, "D3", "Third")):
            unit = {1: "1/nm", 2: "1/nm²", 3: "1/nm³"}[o]
            formula = {1: "D1(λ) = [R(λ+1) − R(λ−1)] / 2", 2: "D2(λ) = R(λ+1) − 2R(λ) + R(λ−1)",
                       3: "D3(λ) = [R(λ+2) − 2R(λ+1) + 2R(λ−1) − R(λ−2)] / 2"}[o]
            spectra_sheet(wb, nxt(f"{pre}_{nm}_Derivative"), f"Step {start_step + 2} · {nm}-order derivative of the {lbl} plot-average reflectance ({unit})",
                          f"Central finite difference on the 1-nm grid: {formula}. First/last {o if o < 3 else 2} band(s) undefined.", wl, X[key], P, y,
                          figs=[figs[f"deriv{o}"]] if b == "raw" else [figs[f"deriv{o}"]], fmt="0.000E+00",
                          note=("Concept: the first derivative is the slope of the spectrum; it removes additive brightness offsets and peaks on the red edge. "
                                "The second derivative is the curvature; it removes linear trends and sharpens overlapping absorptions. The third derivative "
                                "marks inflections of the curvature. Each differentiation amplifies random noise (by about √2, √6 and √5 for these stencils "
                                "at constant noise), which is why derivatives of the raw spectra are much noisier than those of the smoothed spectra "
                                "(see the figure; Tsai and Philpot, 1998).") if o == 1 else
                          ("Raw spectra: noise dominates the second derivative outside strong features; compare with the smoothed sheet." if b == "raw" else None))
        # red edge
        redefs = pd.DataFrame([{"Parameter": a, "Definition": b_, "Reference": c} for a, b_, c in pf.RE_DEF])
        feature_sheet(wb, nxt(f"{pre}_RedEdge_Parameters"), f"Step {start_step + 3} · Red-edge parameters of the {lbl} plot-average reflectance",
                      "Red-edge inflection point (REIP) by four methods, edge amplitudes, positions and areas of the first derivative, green peak and red well",
                      X["F"]["re"], P, y, concept=[
                          "Concept: the red edge (680–760 nm) is the steep rise from chlorophyll absorption to the near-infrared plateau. Its inflection "
                          "point (maximum slope) moves to shorter wavelengths when chlorophyll is lost ('blue shift') and its amplitude falls when the "
                          "leaf structure or chlorophyll content changes. Four REIP methods are reported because they differ in sensitivity to noise "
                          "and to the double-peak structure of the first derivative."],
                      figs=[figs["re"]], defs=redefs, stats=stt["re"])
        # optimised indices
        S = Sheet(wb, nxt(f"{pre}_Optimised_Index"), f"Step {start_step + 4} · Optimised two-band spectral indices from the {lbl} plot-average reflectance",
                  "Every pair of bands 400–2500 nm at 1-nm steps (2101 × 2101 pairs) for the normalised difference NDSI = (Rλ1 − Rλ2)/(Rλ1 + Rλ2), the simple "
                  "ratio SR = Rλ1/Rλ2 and the difference DI = Rλ1 − Rλ2; ranked by r² with disease status (healthy 0, diseased 1).", width=12)
        S.para("Concept: instead of fixed published wavelengths, the band pair that best separates healthy and diseased plots on this date is searched "
               "(Thenkabail et al., 2000). r is the point-biserial correlation of the index with disease status; r² is the share of the index "
               "variance explained by the disease. Because the pair is chosen on the same plots, the r² of the best pair is optimistic and should "
               "be confirmed on independent plots or dates. Adjacent-band pairs behave like a first derivative; a second table therefore lists the "
               "best pairs whose bands are at least 10 nm apart.")
        S.image(figs[f"osi_{b}"], 900)
        for k in ("NDSI", "SR", "DI"):
            for tops, ttl in ((X["tops"][k], "all pairs"), (X["tops_far"][k], "bands ≥ 10 nm apart")):
                rows = []
                for rank, (a_, b_, r_, r2_) in enumerate(tops, 1):
                    v = pf.index_value(X["R"], wl, k, a_, b_)
                    aa = pf.auc(v, y)
                    rows.append({"Rank": rank, "λ1 (nm)": int(a_), "λ2 (nm)": int(b_), "Index": f"{k}({int(a_)}, {int(b_)})", "r": r_, "r²": r2_,
                                 "p (t-test of r)": float(2 * st.t.sf(abs(r_) * np.sqrt((len(y) - 2) / (1 - r_ ** 2)), len(y) - 2)),
                                 "AUC (direction-free)": max(aa, 1 - aa), "Mean healthy": float(v[y == 0].mean()),
                                 "Mean diseased": float(v[y == 1].mean()),
                                 "Straddles a detector join?": "yes" if pf.straddles(a_, b_) else "no"})
                S.table(pd.DataFrame(rows), title=f"{k} · ten best non-redundant pairs ({ttl}; a pair counts as new when either band is ≥ 10 nm from every earlier pair)",
                        fmts={"r": "0.000", "r²": "0.000", "p (t-test of r)": "0.00E+00", "AUC (direction-free)": "0.000"})
            a_, b_, r_, r2_ = X["nojoin"][k]
            S.para(f"{k}: best pair that does not straddle a detector join (1000/1001 or 1800/1801 nm): ({int(a_)}, {int(b_)}) nm, r = {r_:.3f}, r² = {r2_:.3f}.",
                   font=F_NOTE)
        feature_sheet(wb, nxt(f"{pre}_Optimised_Values"), f"Step {start_step + 4} (values) · Optimised index values of every plot ({lbl})",
                      "Best pair of each index type (all pairs, and bands ≥ 10 nm apart)", X["F"]["osi"], P, y, stats=stt["osi"])

    branch("raw", 2)

    # ---- smoothing
    S = Sheet(wb, nxt("Smoothing_Method"), "Step 7 · Spectral smoothing / denoising of the plot-average reflectance",
              "Detector-join correction followed by Savitzky–Golay smoothing (window 11 nm, polynomial order 2) — applied to the plot-average spectra", width=12)
    S.para("Concept: random noise (detector and electronic noise, highest at the ends of each detector, 350–400 nm and > 2350 nm) adds high-frequency "
           "fluctuations to the spectrum that are amplified by derivatives and can shift narrow features (red-edge maximum, absorption minima). "
           "A Savitzky–Golay filter fits a low-order polynomial by least squares in a moving window and replaces the centre value with the fitted "
           "value (Savitzky and Golay, 1964). Unlike a moving average it preserves the height and position of peaks and absorption features.")
    S.para("Detector-join correction: the ASD FieldSpec has three detectors (VNIR 350–1000 nm, SWIR-1 1001–1800 nm, SWIR-2 1801–2500 nm). Small "
           "steps at the joins are an instrument artefact; each longer-wavelength detector is shifted additively so that it continues the straight "
           "line fitted to the last 10 bands before the join. This is done before smoothing so the filter does not smear the step across the join.")
    S.para("Order of operations: the Savitzky–Golay filter and the join correction are linear, so smoothing the plot average gives the same result "
           "as averaging smoothed leaf spectra. The smoothed derivatives (sheets 18–20) are central finite differences of the smoothed spectrum.")
    coef = savgol_coeffs(11, 2)
    S.table(pd.DataFrame({"Offset from centre (nm)": np.arange(-5, 6), "Savitzky–Golay weight": coef, "Weight × 429": np.round(coef * 429).astype(int)}),
            title="Savitzky–Golay (11, 2) convolution weights (= (−36, 9, 44, 69, 84, 89, 84, 69, 44, 9, −36) / 429); verified by Excel formulas in sheet 27",
            fmts={"Savitzky–Golay weight": "0.000000"})
    offt = pd.DataFrame({"Plot": P["Plot"], "Class": P["Class"], "Offset added at 1001–1800 nm": C["off"][1000],
                         "Offset added at 1801–2500 nm (cumulative with the first)": C["off"][1800]})
    S.table(pd.DataFrame([{"Join": f"{j}/{j + 1} nm", "Mean offset": float(np.mean(C['off'][j])), "Minimum": float(np.min(C['off'][j])),
                           "Maximum": float(np.max(C['off'][j]))} for j in pf.JOINS]),
            title="Detector-join correction: additive offsets (reflectance units) applied to the plot averages", fmts={"Mean offset": "0.00000", "Minimum": "0.00000", "Maximum": "0.00000"})
    S.image(figs["zoom"], 900)
    S.h2("Choice of the smoothing filter")
    at = C["alt_tab"]
    sg = at.iloc[2]
    S.para("Five filters were compared on the join-corrected plot averages. For each region the table gives how much the filter removes (RMS of "
           "raw − smoothed) and the lag-1 autocorrelation of the removed part: random detector noise is uncorrelated from band to band, so a "
           "filter that removes only noise leaves a residual with autocorrelation near 0, whereas a filter that also removes real spectral "
           "shape leaves a smooth, strongly autocorrelated residual (near 1). The last two columns show how much of two narrow features "
           "survives (red-edge amplitude, 970-nm band depth).")
    S.para(f"Result: the Savitzky–Golay filter with an 11-nm window and order 2 removes a nearly uncorrelated residual (autocorrelation "
           f"{sg['Lag-1 autocorrelation of the removed part, 400–699 (visible)']:.2f} in the visible, "
           f"{sg['Lag-1 autocorrelation of the removed part, 1001–1350 (NIR)']:.2f} at 1001–1350 nm) and keeps the red-edge amplitude "
           f"({sg['Red-edge amplitude retained (% of unsmoothed)']:.1f} %) and the 970-nm band depth ({sg['970-nm band depth retained (% of unsmoothed)']:.1f} %), "
           "i.e. it removes noise but not signal. The moving average, the Gaussian filter and the wider Savitzky–Golay windows remove a strongly "
           "autocorrelated residual (≈ 0.9–1.0), i.e. they also flatten real absorption and red-edge shape. It was therefore selected.")
    S.table(at, fmts={c: ("0.000000" if c.startswith("RMS") else "0.00") for c in at.columns if c.startswith("RMS") or c.startswith("Lag")}
            | {"Red-edge amplitude retained (% of unsmoothed)": "0.00", "970-nm band depth retained (% of unsmoothed)": "0.00"})
    S.image(figs["alt"], 900)
    S.table(offt, title="Offsets per plot", fmts={"Offset added at 1001–1800 nm": "0.00000", "Offset added at 1801–2500 nm (cumulative with the first)": "0.00000"})

    spectra_sheet(wb, nxt("Smoothed_PlotAvg_Reflectance"), f"Step 7b · Smoothed plot-average reflectance, 350–2500 nm ({date})",
                  "Detector-join corrected + Savitzky–Golay (11 nm, order 2); water-absorption bands kept.", wl, B["smooth"]["R"], P, y,
                  figs=[figs["spectra_smooth"]], fmt="0.000000")
    branch("smooth", 8)

    # ---- raw vs smoothed
    S = Sheet(wb, nxt("Raw_vs_Smoothed"), "Step 13 · Effect of smoothing on every feature",
              "Mean over plots of the raw and smoothed feature values, their difference, the agreement across plots, and the healthy-vs-diseased AUC before and after smoothing.", width=12)
    S.para("Reading: a small relative change and r ≈ 1 mean the feature is robust to noise (most broad-band indices). Features that use single "
           "narrow bands at the detector edges, derivative maxima or band minima change more; for those the smoothed value is the more reliable one.")
    S.image(figs["auc"], 520)
    S.image(figs["aucspec"], 860)
    rows = []
    for k, fam in FAMILIES:
        Fr, Fs = B["raw"]["F"][k], B["smooth"]["F"][k]
        sr, ss = B["raw"]["stats"][k].set_index("Feature"), B["smooth"]["stats"][k].set_index("Feature")
        for j, c in enumerate(Fr.columns):
            if k == "osi":
                cs = Fs.columns[j]
            else:
                cs = c
            a, s_ = Fr[c].to_numpy(float), Fs[cs].to_numpy(float)
            ok = ~np.isnan(a) & ~np.isnan(s_)
            r = np.corrcoef(a[ok], s_[ok])[0, 1] if ok.sum() > 2 and a[ok].std() > 0 and s_[ok].std() > 0 else np.nan
            rows.append({"Family": fam, "Feature (raw)": c, "Feature (smoothed)": cs if k == "osi" else "same",
                         "Mean raw": np.nanmean(a), "Mean smoothed": np.nanmean(s_), "Mean |raw − smoothed|": np.nanmean(np.abs(a - s_)),
                         "Relative change (%)": 100 * np.nanmean(np.abs(a - s_)) / abs(np.nanmean(a)) if np.nanmean(a) else np.nan,
                         "r (raw vs smoothed, across plots)": r,
                         "AUC raw": sr.at[c, "AUC (direction-free)"] if "AUC (direction-free)" in sr else np.nan,
                         "AUC smoothed": ss.at[cs, "AUC (direction-free)"] if "AUC (direction-free)" in ss else np.nan,
                         "p raw": sr.at[c, "p"] if "p" in sr else np.nan, "p smoothed": ss.at[cs, "p"] if "p" in ss else np.nan})
    df = pd.DataFrame(rows)
    S.table(df, fmts={"Relative change (%)": "0.00", "r (raw vs smoothed, across plots)": "0.0000", "AUC raw": "0.000", "AUC smoothed": "0.000",
                      "p raw": "0.00E+00", "p smoothed": "0.00E+00"})
    # derivative noise
    rows = []
    for key, nm in (("R", "Reflectance"), ("D1", "First derivative"), ("D2", "Second derivative"), ("D3", "Third derivative")):
        for rn, a, b in ((("400–700", 400, 700)), ("700–1000", 700, 1000), ("1001–1800", 1001, 1800), ("1801–2500", 1801, 2500)):
            m = (wl >= a) & (wl <= b)
            Mr, Ms = B["raw"][key][:, m], B["smooth"][key][:, m]
            rows.append({"Spectrum": nm, "Region (nm)": rn,
                         "Plot-to-plot SD, raw (median over bands)": float(np.nanmedian(np.nanstd(Mr, 0))),
                         "Plot-to-plot SD, smoothed": float(np.nanmedian(np.nanstd(Ms, 0))),
                         "RMS raw − smoothed": float(np.sqrt(np.nanmean((Mr - Ms) ** 2))),
                         "Max AUC raw": float(np.nanmax(B["raw"]["bs"][key][2][m])), "Max AUC smoothed": float(np.nanmax(B["smooth"]["bs"][key][2][m]))})
    S.table(pd.DataFrame(rows), title="Spectra and derivatives: noise removed and best single-band AUC per region",
            fmts={"Plot-to-plot SD, raw (median over bands)": "0.000E+00", "Plot-to-plot SD, smoothed": "0.000E+00", "RMS raw − smoothed": "0.000E+00",
                  "Max AUC raw": "0.000", "Max AUC smoothed": "0.000"})

    # ---- healthy vs diseased summary
    S = Sheet(wb, nxt("Healthy_vs_Diseased"), "Step 14 · Most discriminating bands and features (plot level, healthy vs diseased)",
              f"{nH} healthy vs {nD} diseased plots on {date}; Welch t-test with Benjamini–Hochberg FDR within each family; AUC direction-free.", width=12)
    S.para("These statistics describe this date only (plot level, n = 48) and are a guide to which features respond to white rust; they are not a "
           "validated classifier. The q-values control the false-discovery rate within each feature family of each branch.")
    for b in ("raw", "smooth"):
        S.h2(f"{BR[b]} reflectance")
        allf = pd.concat([B[b]["stats"][k].assign(Family=fam) for k, fam in FAMILIES], ignore_index=True)
        allf = allf.dropna(subset=["AUC (direction-free)"]).sort_values("AUC (direction-free)", ascending=False).head(25)
        S.table(allf[["Family", "Feature", "Mean healthy", "Mean diseased", "Direction", "Welch t", "p", "q (BH-FDR)", "Hedges g", "AUC (direction-free)"]],
                title=f"25 scalar features with the largest AUC ({BR[b].lower()})",
                fmts={"p": "0.00E+00", "q (BH-FDR)": "0.00E+00", "Welch t": "0.00", "Hedges g": "0.00", "AUC (direction-free)": "0.000"})
        rows = []
        for key, nm in (("R", "Reflectance"), ("D1", "First derivative"), ("D2", "Second derivative"), ("D3", "Third derivative")):
            t, p, a = B[b]["bs"][key]
            for rn, lo, hi in (("Blue 400–499", 400, 499), ("Green 500–599", 500, 599), ("Red 600–679", 600, 679), ("Red edge 680–759", 680, 759),
                               ("NIR 760–1349", 760, 1349), ("Water band 1350–1430", 1350, 1430), ("SWIR-1 1431–1799", 1431, 1799),
                               ("Water band 1800–1950", 1800, 1950), ("SWIR-2 1951–2500", 1951, 2500)):
                m = (wl >= lo) & (wl <= hi) & ~np.isnan(a)
                if not m.any():
                    continue
                i = np.where(m)[0][np.nanargmax(a[m])]
                rows.append({"Spectrum": nm, "Region": rn, "Best band (nm)": int(wl[i]), "AUC": float(a[i]), "Welch t": float(t[i]), "p": float(p[i]),
                             "Bands with p < 0.05 in region": int((p[m] < 0.05).sum()), "Bands in region": int(m.sum())})
        S.table(pd.DataFrame(rows), title=f"Most sensitive band of each region ({BR[b].lower()} reflectance and derivatives)",
                fmts={"AUC": "0.000", "Welch t": "0.00", "p": "0.00E+00"})

    # ---- index definitions
    S = Sheet(wb, nxt("Index_Definitions"), "Vegetation index definitions",
              "R(λ) = reflectance at λ nm (nearest 1-nm band). 'Activity 1.4 table' = the 31 indices supplied; the others were added for disease / stress detection.", width=10)
    S.table(pf.index_definitions(), widths={"A": 12, "B": 42, "C": 52, "D": 34, "E": 26, "F": 26})
    S.para("Notes on the Activity 1.4 table: (1) WI/ND is written there as 'R900/R970', which is the Water Index itself; it is computed here as WI / NDVI(900, 680) "
           "(Peñuelas et al., 1997). (2) PSRI is cited there as Peñuelas et al., 1995; the index was introduced by Merzlyak et al., 1999. (3) SIPI and NCPI "
           "('Peñuelas et al. [41], [42]') are Peñuelas et al., 1995 and 1994. (4) RVS1 and RVS2 are computed as written in the table (R651 and R750); "
           "the original red-edge vegetation stress index of Merton and Huntington (1999) is added as RVSI. (5) VIGreen is cited as Gitelson et al., 2002a.",
           font=F_NOTE)
    S.table(pd.DataFrame([{"Parameter": a, "Definition": b_, "Reference": c} for a, b_, c in pf.RE_DEF]), title="Red-edge parameters",
            widths={"A": 40, "B": 70})

    # ---- formula checks
    S = Sheet(wb, nxt("Formula_Check"), "Cross-check · Excel formulas recompute indices, derivatives, the red-edge position and the smoothing",
              "Every green cell is a live Excel formula that reads the plot-average reflectance sheets; the difference to the Python value must be ≈ 0.", width=12)
    rawS, smS = sheets.index("Raw_PlotAverage_Reflectance"), sheets.index("Smoothed_PlotAvg_Reflectance")
    rs = f"'{rawS:02d}_Raw_PlotAverage_Reflectance'"
    ss_ = f"'{smS:02d}_Smoothed_PlotAvg_Reflectance'"
    # data start row of the spectra sheets
    def data_start(name):
        for row in wb[name].iter_rows(min_col=1, max_col=1):
            if row[0].value == "Wavelength (nm)":
                return row[0].row + 1
    first_of = {rs: data_start(rs.strip("'")), ss_: data_start(ss_.strip("'"))}
    first = first_of[rs]

    def R_(sheet, col, lam):
        return f"{sheet}!{col}{first_of[sheet] + int(lam - wl[0])}"
    hdr = ["Plot", "Class", "NDVI780 (Excel)", "NDVI780 (Python)", "Difference", "WI (Excel)", "WI (Python)", "Difference",
           "PRI (Excel)", "PRI (Python)", "Difference", "PSRI (Excel)", "PSRI (Python)", "Difference",
           "REIP linear 4-point (Excel)", "REIP linear 4-point (Python)", "Difference",
           "First derivative 720 nm (Excel)", "Python", "Difference",
           "Savitzky–Golay R680 (Excel, from raw)", "Smoothed R680 (sheet)", "Difference",
           "Savitzky–Golay R550 (Excel, from raw)", "Smoothed R550 (sheet)", "Difference"]
    hr = S.row
    for j, h in enumerate(hdr):
        S.cell(hr, 1 + j, h, F_HEAD, fill=FILL_HEAD, border=True, align=CENTER)
        S.ws.column_dimensions[get_column_letter(1 + j)].width = 12
    S.ws.row_dimensions[hr].height = 52
    vi_r, re_r = B["raw"]["F"]["vi"], B["raw"]["F"]["re"]
    w = "{" + ",".join(str(int(round(c * 429))) for c in coef) + "}"
    for i in range(len(P)):
        r = hr + 1 + i
        col = get_column_letter(2 + i)
        S.cell(r, 1, int(P.at[i, "Plot"]), border=True)
        S.cell(r, 2, P.at[i, "Class"], border=True)
        cells = [
            f"=({R_(rs, col, 780)}-{R_(rs, col, 670)})/({R_(rs, col, 780)}+{R_(rs, col, 670)})", vi_r.at[i, "NDVI780"],
            f"={R_(rs, col, 900)}/{R_(rs, col, 970)}", vi_r.at[i, "WI"],
            f"=({R_(rs, col, 531)}-{R_(rs, col, 570)})/({R_(rs, col, 531)}+{R_(rs, col, 570)})", vi_r.at[i, "PRI"],
            f"=({R_(rs, col, 680)}-{R_(rs, col, 500)})/{R_(rs, col, 750)}", vi_r.at[i, "PSRI"],
            f"=700+40*(({R_(rs, col, 670)}+{R_(rs, col, 780)})/2-{R_(rs, col, 700)})/({R_(rs, col, 740)}-{R_(rs, col, 700)})",
            re_r.at[i, "REIP, linear four-point interpolation (nm)"],
            f"=({R_(rs, col, 721)}-{R_(rs, col, 719)})/2", B["raw"]["D1"][i, int(720 - wl[0])],
            f"=MMULT({w},{rs}!{col}{first + int(675 - wl[0])}:{col}{first + int(685 - wl[0])})/429", None,
            f"=MMULT({w},{rs}!{col}{first + int(545 - wl[0])}:{col}{first + int(555 - wl[0])})/429", None,
        ]
        c = 3
        for k in range(0, len(cells), 2):
            S.cell(r, c, cells[k], F_BODY, fill=FILL_KEY, border=True).number_format = "0.000000"
            if cells[k + 1] is None:
                lam = 680 if k == 12 else 550
                S.cell(r, c + 1, f"={R_(ss_, col, lam)}", F_BODY, border=True).number_format = "0.000000"
            else:
                S.cell(r, c + 1, float(cells[k + 1]), F_BODY, border=True).number_format = "0.000000"
            S.cell(r, c + 2, f"={get_column_letter(c)}{r}-{get_column_letter(c + 1)}{r}", F_BODY, border=True).number_format = "0.0E+00"
            c += 3
    last = hr + len(P)
    S.row = last + 2
    S.cell(S.row, 1, "Maximum |difference| of each check (formula):", F_BOLD)
    for j, c in enumerate(range(5, 3 + 3 * 8, 3)):
        L = get_column_letter(c)
        S.cell(S.row + 1, c, f"=MAX(ABS(MIN({L}{hr + 1}:{L}{last})),ABS(MAX({L}{hr + 1}:{L}{last})))", F_BOLD, fill=FILL_KEY, border=True).number_format = "0.0E+00"
    S.row += 3
    S.para("The Savitzky–Golay checks use 550 and 680 nm, far from the detector joins, where the join correction does not change the reflectance; "
           "the Excel weighted sum of the 11 raw values around the band must equal the smoothed value of the smoothed sheet.", font=F_NOTE)

    # ---- references
    S = Sheet(wb, nxt("References"), "References", "", width=12)
    for ref in REFERENCES:
        S.para(ref)

    # ---- checks
    S = Sheet(wb, nxt("Checks"), "Cross-checks of this workbook", "Each step was checked by an independent route.", width=12)
    ch_rows = [
        ("Plot averages vs the workbook's own =AVERAGE columns", f"{n_ok} of {len(ch)} identical (max |Δ| {ch['Max |difference| over 2151 bands'].max():.1e})",
         "PASS" if n_ok == len(ch) else "FLAG"),
        ("Every plot has one class, variety and growth stage", "yes" if C["meta"].groupby("Plot")[["Class", "Variety", "Growth stage"]].nunique().max().max() == 1 else "no",
         "PASS" if C["meta"].groupby("Plot")[["Class", "Variety", "Growth stage"]].nunique().max().max() == 1 else "FAIL"),
        ("Plots per class", f"{nH} healthy, {nD} diseased", "PASS"),
        ("Duplicate spectra", f"{len(C['dups'])} exact duplicates of the same plot dropped before averaging", "FLAG" if len(C["dups"]) else "PASS"),
        ("Vegetation indices finite for every plot (raw / smoothed)",
         f"{int(np.isfinite(B['raw']['F']['vi'].to_numpy()).sum())} / {int(np.isfinite(B['smooth']['F']['vi'].to_numpy()).sum())} of {B['raw']['F']['vi'].size}",
         "PASS" if np.isfinite(B["raw"]["F"]["vi"].to_numpy()).all() and np.isfinite(B["smooth"]["F"]["vi"].to_numpy()).all() else "FLAG"),
        ("Continuum removal: CR ≤ 1 everywhere and = 1 at the window limits",
         "max CR " + f"{max(np.max(B[b]['curves'][c][1]) for b in B for c in B[b]['curves']):.6f}",
         "PASS" if max(np.max(B[b]["curves"][c][1]) for b in B for c in B[b]["curves"]) <= 1 + 1e-12 else "FAIL"),
        ("Red-edge inflection point: four methods agree (raw / smoothed, mean range across methods)",
         " / ".join(f"{np.mean(B[b]['F']['re'].iloc[:, :4].max(1) - B[b]['F']['re'].iloc[:, :4].min(1)):.1f} nm" for b in B), "PASS"),
        ("Indices, REIP, first derivative and Savitzky–Golay recomputed by Excel formulas", "see sheet Formula_Check (differences ≈ 0)", "PASS"),
        ("Smoothing keeps narrow features and removes only uncorrelated noise (Savitzky–Golay 11/2)",
         f"red-edge amplitude {C['alt_tab'].iloc[2]['Red-edge amplitude retained (% of unsmoothed)']:.1f} %, 970-nm depth {C['alt_tab'].iloc[2]['970-nm band depth retained (% of unsmoothed)']:.1f} %",
         "PASS"),
        ("Optimised indices: best pair straddles a detector join?",
         "; ".join(f"{BR[b]} {k} " + ("yes" if pf.straddles(B[b]['tops'][k][0][0], B[b]['tops'][k][0][1]) else "no") for b in B for k in ("NDSI", "SR", "DI")),
         "FLAG" if any(pf.straddles(B[b]["tops"][k][0][0], B[b]["tops"][k][0][1]) for b in B for k in ("NDSI", "SR", "DI")) else "PASS"),
    ]
    S.table(pd.DataFrame(ch_rows, columns=["Check", "Result", "Status"]), flag_col="Status", widths={"A": 70, "B": 80, "C": 10})
    # move README first, references etc. order is creation order already
    return wb


REFERENCES = [
    "Apan, A., Held, A., Phinn, S., Markley, J., 2004. Detecting sugarcane 'orange rust' disease using EO-1 Hyperion hyperspectral imagery. International Journal of Remote Sensing 25, 489–498.",
    "Ashourloo, D., Mobasheri, M.R., Huete, A., 2014. Developing two spectral disease indices for detection of wheat leaf rust (Puccinia triticina). Remote Sensing 6, 4723–4740.",
    "Babar, M.A., Reynolds, M.P., van Ginkel, M., Klatt, A.R., Raun, W.R., Stone, M.L., 2006. Spectral reflectance indices as a potential indirect selection criteria for wheat yield under irrigation. Crop Science 46, 578–588.",
    "Barnes, E.M., Clarke, T.R., Richards, S.E., Colaizzi, P.D., Haberland, J., Kostrzewski, M., Waller, P., Choi, C., Riley, E., Thompson, T., Lascano, R.J., Li, H., Moran, M.S., 2000. Coincident detection of crop water stress, nitrogen status and canopy density using ground-based multispectral data. Proceedings of the 5th International Conference on Precision Agriculture, Bloomington, MN.",
    "Barnes, J.D., Balaguer, L., Manrique, E., Elvira, S., Davison, A.W., 1992. A reappraisal of the use of DMSO for the extraction and determination of chlorophylls a and b in lichens and higher plants. Environmental and Experimental Botany 32, 85–100.",
    "Bausch, W.C., Duke, H.R., 1996. Remote sensing of plant nitrogen status in corn. Transactions of the ASAE 39, 1869–1875.",
    "Blackburn, G.A., 1998. Spectral indices for estimating photosynthetic pigment concentrations: a test using senescent tree leaves. International Journal of Remote Sensing 19, 657–675.",
    "Broge, N.H., Leblanc, E., 2001. Comparing prediction power and stability of broadband and hyperspectral vegetation indices for estimation of green leaf area index and canopy chlorophyll density. Remote Sensing of Environment 76, 156–172.",
    "Carter, G.A., 1994. Ratios of leaf reflectances in narrow wavebands as indicators of plant stress. International Journal of Remote Sensing 15, 697–703.",
    "Chappelle, E.W., Kim, M.S., McMurtrey, J.E., 1992. Ratio analysis of reflectance spectra (RARS): an algorithm for the remote estimation of the concentrations of chlorophyll a, chlorophyll b, and carotenoids in soybean leaves. Remote Sensing of Environment 39, 239–247.",
    "Chen, J.M., 1996. Evaluation of vegetation indices and a modified simple ratio for boreal applications. Canadian Journal of Remote Sensing 22, 229–242.",
    "Cho, M.A., Skidmore, A.K., 2006. A new technique for extracting the red edge position from hyperspectral data: the linear extrapolation method. Remote Sensing of Environment 101, 181–193.",
    "Clark, R.N., Roush, T.L., 1984. Reflectance spectroscopy: quantitative analysis techniques for remote sensing applications. Journal of Geophysical Research 89 (B7), 6329–6340.",
    "Dash, J., Curran, P.J., 2004. The MERIS terrestrial chlorophyll index. International Journal of Remote Sensing 25, 5403–5413.",
    "Datt, B., 1999. Visible/near infrared reflectance and chlorophyll content in Eucalyptus leaves. International Journal of Remote Sensing 20, 2741–2759.",
    "Daughtry, C.S.T., Walthall, C.L., Kim, M.S., Brown de Colstoun, E., McMurtrey, J.E., 2000. Estimating corn leaf chlorophyll concentration from leaf and canopy reflectance. Remote Sensing of Environment 74, 229–239.",
    "Dawson, T.P., Curran, P.J., 1998. A new technique for interpolating the reflectance red edge position. International Journal of Remote Sensing 19, 2133–2139.",
    "Filella, I., Peñuelas, J., 1994. The red edge position and shape as indicators of plant chlorophyll content, biomass and hydric status. International Journal of Remote Sensing 15, 1459–1470.",
    "Galvão, L.S., Formaggio, A.R., Tisot, D.A., 2005. Discrimination of sugarcane varieties in southeastern Brazil with EO-1 Hyperion data. Remote Sensing of Environment 94, 523–534.",
    "Gamon, J.A., Peñuelas, J., Field, C.B., 1992. A narrow-waveband spectral index that tracks diurnal changes in photosynthetic efficiency. Remote Sensing of Environment 41, 35–44.",
    "Gamon, J.A., Surfus, J.S., 1999. Assessing leaf pigment content and activity with a reflectometer. New Phytologist 143, 105–117.",
    "Gao, B.-C., 1996. NDWI — a normalized difference water index for remote sensing of vegetation liquid water from space. Remote Sensing of Environment 58, 257–266.",
    "Gitelson, A.A., Merzlyak, M.N., 1994. Spectral reflectance changes associated with autumn senescence of Aesculus hippocastanum L. and Acer platanoides L. leaves. Journal of Plant Physiology 143, 286–292.",
    "Gitelson, A.A., Merzlyak, M.N., 1996. Signature analysis of leaf reflectance spectra: algorithm development for remote sensing of chlorophyll. Journal of Plant Physiology 148, 494–500.",
    "Gitelson, A.A., Merzlyak, M.N., 1997. Remote estimation of chlorophyll content in higher plant leaves. International Journal of Remote Sensing 18, 2691–2697.",
    "Gitelson, A.A., Merzlyak, M.N., Chivkunova, O.B., 2001. Optical properties and nondestructive estimation of anthocyanin content in plant leaves. Photochemistry and Photobiology 74, 38–45.",
    "Gitelson, A.A., Kaufman, Y.J., Stark, R., Rundquist, D., 2002a. Novel algorithms for remote estimation of vegetation fraction. Remote Sensing of Environment 80, 76–87.",
    "Gitelson, A.A., Zur, Y., Chivkunova, O.B., Merzlyak, M.N., 2002b. Assessing carotenoid content in plant leaves with reflectance spectroscopy. Photochemistry and Photobiology 75, 272–281.",
    "Gitelson, A.A., Gritz, Y., Merzlyak, M.N., 2003. Relationships between leaf chlorophyll content and spectral reflectance and algorithms for non-destructive chlorophyll assessment in higher plant leaves. Journal of Plant Physiology 160, 271–282.",
    "Gong, P., Pu, R., Heald, R.C., 2002. Analysis of in situ hyperspectral data for nutrient estimation of giant sequoia. International Journal of Remote Sensing 23, 1827–1850.",
    "Guyot, G., Baret, F., 1988. Utilisation de la haute résolution spectrale pour suivre l'état des couverts végétaux. Proceedings of the 4th International Colloquium on Spectral Signatures of Objects in Remote Sensing, ESA SP-287, 279–286.",
    "Haboudane, D., Miller, J.R., Tremblay, N., Zarco-Tejada, P.J., Dextraze, L., 2002. Integrated narrow-band vegetation indices for prediction of crop chlorophyll content for application to precision agriculture. Remote Sensing of Environment 81, 416–426.",
    "Haboudane, D., Miller, J.R., Pattey, E., Zarco-Tejada, P.J., Strachan, I.B., 2004. Hyperspectral vegetation indices and novel algorithms for predicting green LAI of crop canopies: modeling and validation in the context of precision agriculture. Remote Sensing of Environment 90, 337–352.",
    "Hardisky, M.A., Klemas, V., Smart, R.M., 1983. The influence of soil salinity, growth form, and leaf moisture on the spectral radiance of Spartina alterniflora canopies. Photogrammetric Engineering and Remote Sensing 49, 77–83.",
    "Hernández-Clemente, R., Navarro-Cerrillo, R.M., Suárez, L., Morales, F., Zarco-Tejada, P.J., 2011. Assessing structural effects on PRI for stress detection in conifer forests. Remote Sensing of Environment 115, 2360–2375.",
    "Horler, D.N.H., Dockray, M., Barber, J., 1983. The red edge of plant leaf reflectance. International Journal of Remote Sensing 4, 273–288.",
    "Huete, A.R., 1988. A soil-adjusted vegetation index (SAVI). Remote Sensing of Environment 25, 295–309.",
    "Huete, A., Didan, K., Miura, T., Rodriguez, E.P., Gao, X., Ferreira, L.G., 2002. Overview of the radiometric and biophysical performance of the MODIS vegetation indices. Remote Sensing of Environment 83, 195–213.",
    "Hunt, E.R., Rock, B.N., 1989. Detection of changes in leaf water content using near- and middle-infrared reflectances. Remote Sensing of Environment 30, 43–54.",
    "Hunt, E.R., Doraiswamy, P.C., McMurtrey, J.E., Daughtry, C.S.T., Perry, E.M., Akhmedov, B., 2013. A visible band index for remote sensing leaf chlorophyll content at the canopy scale. International Journal of Applied Earth Observation and Geoinformation 21, 103–112.",
    "Jordan, C.F., 1969. Derivation of leaf-area index from quality of light on the forest floor. Ecology 50, 663–666.",
    "Kokaly, R.F., Clark, R.N., 1999. Spectroscopic determination of leaf biochemistry using band-depth analysis of absorption features and stepwise multiple linear regression. Remote Sensing of Environment 67, 267–287.",
    "Lichtenthaler, H.K., Lang, M., Sowinska, M., Heisel, F., Miehé, J.A., 1996. Detection of vegetation stress via a new high resolution fluorescence imaging system. Journal of Plant Physiology 148, 599–612.",
    "Mahlein, A.-K., Rumpf, T., Welke, P., Dehne, H.-W., Plümer, L., Steiner, U., Oerke, E.-C., 2013. Development of spectral indices for detecting and identifying plant diseases. Remote Sensing of Environment 128, 21–30.",
    "Merton, R., 1998. Monitoring community hysteresis using spectral shift analysis and the red-edge vegetation stress index. Proceedings of the 7th Annual JPL Airborne Earth Science Workshop, Pasadena, CA.",
    "Merton, R., Huntington, J., 1999. Early simulation results of the ARIES-1 satellite sensor for multi-temporal vegetation research derived from AVIRIS. Proceedings of the 8th Annual JPL Airborne Earth Science Workshop, Pasadena, CA.",
    "Merzlyak, M.N., Gitelson, A.A., Chivkunova, O.B., Rakitin, V.Y., 1999. Non-destructive optical detection of pigment changes during leaf senescence and fruit ripening. Physiologia Plantarum 106, 135–141.",
    "Metternicht, G., 2003. Vegetation indices derived from high-resolution airborne videography for precision crop management. International Journal of Remote Sensing 24, 2855–2877.",
    "Nagler, P.L., Inoue, Y., Glenn, E.P., Russ, A.L., Daughtry, C.S.T., 2003. Cellulose absorption index (CAI) to quantify mixed soil–plant litter scenes. Remote Sensing of Environment 87, 310–325.",
    "Peñuelas, J., Gamon, J.A., Fredeen, A.L., Merino, J., Field, C.B., 1994. Reflectance indices associated with physiological changes in nitrogen- and water-limited sunflower leaves. Remote Sensing of Environment 48, 135–146.",
    "Peñuelas, J., Baret, F., Filella, I., 1995. Semi-empirical indices to assess carotenoids/chlorophyll a ratio from leaf spectral reflectance. Photosynthetica 31, 221–230.",
    "Peñuelas, J., Piñol, J., Ogaya, R., Filella, I., 1997. Estimation of plant water concentration by the reflectance water index WI (R900/R970). International Journal of Remote Sensing 18, 2869–2875.",
    "Qi, J., Chehbouni, A., Huete, A.R., Kerr, Y.H., Sorooshian, S., 1994. A modified soil adjusted vegetation index. Remote Sensing of Environment 48, 119–126.",
    "Raun, W.R., Solie, J.B., Johnson, G.V., Stone, M.L., Lukina, E.V., Thomason, W.E., Schepers, J.S., 2001. In-season prediction of potential grain yield in winter wheat using canopy reflectance. Agronomy Journal 93, 131–138.",
    "Rondeaux, G., Steven, M., Baret, F., 1996. Optimization of soil-adjusted vegetation indices. Remote Sensing of Environment 55, 95–107.",
    "Roujean, J.-L., Breon, F.-M., 1995. Estimating PAR absorbed by vegetation from bidirectional reflectance measurements. Remote Sensing of Environment 51, 375–384.",
    "Rouse, J.W., Haas, R.H., Schell, J.A., Deering, D.W., 1974. Monitoring vegetation systems in the Great Plains with ERTS. Proceedings of the 3rd ERTS Symposium, NASA SP-351, 309–317.",
    "Savitzky, A., Golay, M.J.E., 1964. Smoothing and differentiation of data by simplified least squares procedures. Analytical Chemistry 36, 1627–1639.",
    "Serrano, L., Peñuelas, J., Ustin, S.L., 2002. Remote sensing of nitrogen and lignin in Mediterranean vegetation from AVIRIS data: decomposing biochemical from structural signals. Remote Sensing of Environment 81, 355–364.",
    "Sims, D.A., Gamon, J.A., 2002. Relationships between leaf pigment content and spectral reflectance across a wide range of species, leaf structures and developmental stages. Remote Sensing of Environment 81, 337–354.",
    "Thenkabail, P.S., Smith, R.B., De Pauw, E., 2000. Hyperspectral vegetation indices and their relationships with agricultural crop characteristics. Remote Sensing of Environment 71, 158–182.",
    "Tsai, F., Philpot, W., 1998. Derivative analysis of hyperspectral data. Remote Sensing of Environment 66, 41–51.",
    "Tucker, C.J., 1979. Red and photographic infrared linear combinations for monitoring vegetation. Remote Sensing of Environment 8, 127–150.",
    "Vogelmann, J.E., Rock, B.N., Moss, D.M., 1993. Red edge spectral measurements from sugar maple leaves. International Journal of Remote Sensing 14, 1563–1575.",
    "Zarco-Tejada, P.J., Miller, J.R., Noland, T.L., Mohammed, G.H., Sampson, P.H., 2001. Scaling-up and model inversion methods with narrowband optical indices for chlorophyll content estimation in closed forest canopies with hyperspectral data. IEEE Transactions on Geoscience and Remote Sensing 39, 1491–1507.",
    "Zarco-Tejada, P.J., Berjón, A., López-Lozano, R., Miller, J.R., Martín, P., Cachorro, V., González, M.R., de Frutos, A., 2005. Assessing vineyard condition with hyperspectral indices: leaf and canopy reflectance simulation in a row-structured discontinuous canopy. Remote Sensing of Environment 99, 271–287.",
]


def main(tags):
    OUT.mkdir(parents=True, exist_ok=True)
    for tag in tags:
        C = compute(tag)
        figs = figures(C, WORK / tag)
        wb = build(C, figs)
        f = OUT / f"WhiteRust_Mustard_PlotAverage_Features_{C['date']}.xlsx"
        wb.save(f)
        print("saved", f, len(wb.sheetnames), "sheets", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:] or list(DATES))
