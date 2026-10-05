"""Digitise Ahmad et al. (supplement, docx) Figs S2-S5: cumulative C mineralisation (mg CO2/kg soil) of >2 mm and <2 mm aggregates, 0-15 / 15-30 cm,
days 3, 5, 7, 15, 30, 45, 60; 4 treatments (CT0 filled circle, CTR open circle, NT0 filled down-triangle, NTR open up-triangle). Raster PNGs.
Calibration: each panel frame = axis box (x 0-70 d left-right, y 0-700 bottom-top). Markers located by normalised cross-correlation with templates
cut from the figure's own legend (search band +/-10 px around each day's x); best NCC peak per template, peaks of other templates suppressed."""
import json
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

M = "/tmp/claude-0/-home-user-sonu/2fb4e6fa-f356-5f43-b5d3-cf878a7db82d/scratchpad/b16/dx/word/media/"
FIG = {"S2 rice 2020": "image2.png", "S3 rice 2021": "image3.png", "S4 wheat 2020": "image4.png", "S5 wheat 2021": "image5.png"}
# legend marker centres (x, [y CT0, CTR, NT0, NTR]) from the legend line+marker components of panel (a) (bbox centres; checked by eye)
LEG = {"image2.png": (604, [491, 525, 561, 590]), "image3.png": (593.5, [535.5, 570, 604.5, 633]),
       "image4.png": (627, [574.5, 605, 646, 676]), "image5.png": (573.5, [471, 502, 532.5, 556.5])}
DAYS = [3, 5, 7, 15, 30, 45, 60]
TRT = ["CT0", "CTR", "NT0", "NTR"]


def runs(mask, axis):
    m = mask if axis == 0 else mask.T
    out = []
    for i in range(m.shape[1]):
        c = b = 0
        for v in m[:, i]:
            c = c + 1 if v else 0
            b = max(b, c)
        out.append(b)
    return np.array(out)


def clusters(idx):
    g = []
    for i in idx:
        if g and i - g[-1][-1] <= 6:
            g[-1].append(i)
        else:
            g.append([i])
    return [float(np.mean(x)) for x in g]


def ncc_best(img, tpl, x0, x1, y0, y1):
    th, tw = tpl.shape
    t = tpl - tpl.mean()
    tn = np.sqrt((t * t).sum())
    best = []
    for y in range(y0, y1 - th):
        for x in range(x0, x1 - tw):
            w = img[y:y + th, x:x + tw]
            w = w - w.mean()
            d = np.sqrt((w * w).sum()) * tn
            best.append(((w * t).sum() / d if d > 0 else 0, y + th / 2, x + tw / 2))
    return best


res = {}
for fig, fn in FIG.items():
    a = np.asarray(Image.open(M + fn).convert("L")).astype(float)
    H, W = a.shape
    dark = a < 128
    vx = clusters([x for x, r in enumerate(runs(dark, 0)) if r > 0.3 * H])
    hy = clusters([y for y, r in enumerate(runs(dark, 1)) if r > 0.3 * W])
    L, R1, L2, R = vx[0], vx[1], vx[-2], vx[-1]
    T, B1, T2, B = hy[0], hy[1], hy[-2], hy[-1]
    panels = {"a >2mm 0-15": (L, R1, T, B1), "b <2mm 0-15": (L, R1, T2, B), "c >2mm 15-30": (L2, R, T, B1), "d <2mm 15-30": (L2, R, T2, B)}
    lx, lys = LEG[fn]
    tpls = {t: a[int(round(y)) - 13:int(round(y)) + 13, int(round(lx)) - 13:int(round(lx)) + 13] for t, y in zip(TRT, lys)}
    out = {}
    for pn, (x0, x1, y0, y1) in panels.items():
        sx = (x1 - x0) / 70.0
        sy = (y1 - y0) / 700.0
        out[pn] = {}
        for d in DAYS:
            px = x0 + d * sx
            cand = {}
            for t, tp in tpls.items():
                sc = ncc_best(a, tp, int(px - 23), int(px + 23), int(y0 + 5), int(y1 - 5))
                sc.sort(reverse=True)
                cand[t] = sc[:40]
            # greedy assignment: highest score first, no two treatments within 8 px of each other
            taken, val = [], {}
            allc = sorted(((s, t, y, x) for t, l in cand.items() for (s, y, x) in l), reverse=True)
            for s, t, y, x in allc:
                if t in val or s < 0.55:
                    continue
                if any(abs(y - yy) < 8 for yy in taken):
                    continue
                val[t] = (round((y1 - y) / sy, 0), round(float(s), 2))
                taken.append(y)
            out[pn][str(d)] = {t: val.get(t) for t in TRT}
        print(fig, pn, {d: {t: (v[0] if v else None) for t, v in out[pn][str(d)].items()} for d in ("15", "30", "45", "60")})
    res[fig] = {"file": fn, "frames": panels, "legend_px": LEG[fn], "values": out}
json.dump(res, open("/home/user/sonu/digitised/ahmad_min.json", "w"), indent=1)
