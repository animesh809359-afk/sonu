"""Digitise Dutta et al. 2023 IJERPH Figs 1-6 (cumulative C mineralisation, raster line+marker plots, 6 coloured series).
Axis: longest vertical dark run = y axis; y ticks = short dark stubs left of the axis; tick values supplied. Markers: per-series colour mask,
eroded (radius 4) to drop the 3-4 px lines, connected components -> centroids; x categories = days 0,1,3,7,14,29,44,59 (equally spaced)."""
import json, sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

D = "/tmp/claude-0/-home-user-sonu/2fb4e6fa-f356-5f43-b5d3-cf878a7db82d/scratchpad/b16/dimg/"
FIGS = {"Fig1": ("d-006-000.png", [0, 40, 80, 120, 160]), "Fig2": ("d-006-001.png", [0, 20, 40, 60, 80, 100, 120, 140]),
        "Fig3": ("d-007-004.png", [0, 20, 40, 60, 80, 100, 120, 140]), "Fig4": ("d-007-005.png", [0, 20, 40, 60, 80, 100, 120, 140]),
        "Fig5": ("d-008-008.png", [0, 20, 40, 60, 80, 100, 120, 140]), "Fig6": ("d-008-009.png", [0, 20, 40, 60, 80, 100, 120, 140])}
DAYS = [0, 1, 3, 7, 14, 29, 44, 59]
SER = ["CT-RB", "CT-NR", "CT-R", "ZT-RB", "ZT-NR", "ZT-R"]


def longest_run(col):
    best = cur = 0
    for v in col:
        cur = cur + 1 if v else 0
        best = max(best, cur)
    return best


def axis(a):
    g = a.mean(2)
    dark = np.abs(g - 135) < 30
    H, W = g.shape
    runs = [longest_run(dark[:, x]) for x in range(W // 3)]
    runs = [r if r > 0.6 * H else 0 for r in runs]
    ax = int(np.argmax(runs))
    col = dark[:, ax]
    ys = np.where(col)[0]
    # longest run bounds
    best, s, e, cur, st = 0, 0, 0, 0, 0
    for y in range(H):
        if col[y]:
            if cur == 0:
                st = y
            cur += 1
            if cur > best:
                best, s, e = cur, st, y
        else:
            cur = 0
    ticks = [y for y in range(s, e + 1) if dark[y, ax - 7:ax - 2].sum() >= 4]
    # merge consecutive
    tk = []
    for y in ticks:
        if tk and y - tk[-1][-1] <= 1:
            tk[-1].append(y)
        else:
            tk.append([y])
    tk = [float(np.mean(t)) for t in tk]
    # x axis row = bottom of the y axis
    cnt = dark.sum(1)
    xr = int(np.argmax(cnt))
    xs = np.where(dark[xr])[0]
    return ax, s, e, tk, int(xs.max())


def legend_colours(a, ytop):
    top = a[:ytop]
    sat = (top.max(2) - top.min(2)) > 50
    lab, n = ndi.label(sat)
    out = []
    for i in range(1, n + 1):
        ys, xs = np.where(lab == i)
        if len(ys) > 120:
            out.append((xs.min(), np.median(top[ys, xs], axis=0)))
    out.sort(key=lambda t: t[0])
    # legend has a line + marker per entry -> one component each
    return [c for _, c in out]


res = {}
for fig, (fn, tv) in FIGS.items():
    a = np.asarray(Image.open(D + fn).convert("RGB")).astype(int)
    ax, s, e, tk, xmax = axis(a)
    tk = tk[-len(tv):] if len(tk) >= len(tv) else tk
    if len(tk) != len(tv):
        print(fig, "tick mismatch", tk, tv)
    ypix = np.array(sorted(tk, reverse=True))  # bottom first
    k, b = np.polyfit(ypix, tv, 1)
    legend_bottom = int(0.13 * a.shape[0])
    cols = legend_colours(a, max(legend_bottom, 30))
    if len(cols) != 6:
        print(fig, "legend colours", len(cols))
    H, W = a.shape[:2]
    cat_w = (xmax - ax) / len(DAYS)
    xc = [ax + cat_w * (i + 0.5) for i in range(len(DAYS))]
    series, how = {}, {}
    for nm, c in zip(SER, cols):
        d = np.sqrt(((a - c) ** 2).sum(2))
        m0 = d < 24
        m0[:legend_bottom + 5] = False
        pts = {}
        for it in (4, 2, 1):   # fallback: smaller erosion for markers partly hidden under later-drawn series
            m = ndi.binary_erosion(m0, iterations=it)
            lab, n = ndi.label(m)
            cand = {}
            for i in range(1, n + 1):
                ys, xs = np.where(lab == i)
                if len(ys) < (15 if it == 4 else 8):
                    continue
                cx = xs.mean()
                j = int(np.argmin([abs(cx - x) for x in xc]))
                sel = np.abs(xs - xc[j]) < 12
                if abs(cx - xc[j]) < cat_w * 0.3 and sel.sum() >= 5 and DAYS[j] not in pts:
                    if DAYS[j] not in cand or sel.sum() > cand[DAYS[j]][1]:
                        cand[DAYS[j]] = (round(float(k * ys[sel].mean() + b), 1), int(sel.sum()))
            for dd, (v, _) in cand.items():
                pts[dd] = (v, it)
        series[nm] = {str(dd): (pts[dd][0] if dd in pts else None) for dd in DAYS}
        how[nm] = {str(dd): (pts[dd][1] if dd in pts else "hidden") for dd in DAYS}
    res[fig] = {"file": fn, "y_axis_x": ax, "ticks_px": tk, "slope": k, "series": series, "erosion_used": how}
    print(fig, fn, "ax", ax, "ticks", [round(t) for t in tk], "xmax", xmax)
    for nm in SER:
        print("  ", nm, series[nm], how[nm])
json.dump(res, open(sys.argv[1] if len(sys.argv) > 1 else "/home/user/sonu/digitised/dutta2023_ct.json", "w"), indent=1)
