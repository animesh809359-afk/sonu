"""Digitise Ahmad et al. (supplement) Figs S8 (rice season) and S9 (wheat season): total C input (Mg C/ha) = straw C (blue) + root C (red) +
rhizodeposition C (green), stacked bars, 0-15 / 15-30 / 30-45 cm (panel columns), 2020 (top row) / 2021 (bottom row), CT0, CTR, NT0, NTR. Raster PNG.
Calibration: each panel frame = axis box (bottom = 0; top = 8 Mg/ha for the 0-15 cm panels, 1.0 for the 15-30 / 30-45 cm panels; tick labels at
the frame top). Panel frames: long dark vertical runs (left / right) and, within each column, long dark horizontal runs (top / bottom).
Per bar: in the bar's central columns, rows of each fill colour -> segment top / bottom; total = top of the highest segment."""
import json
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

M = "/tmp/claude-0/-home-user-sonu/2fb4e6fa-f356-5f43-b5d3-cf878a7db82d/scratchpad/b16/dx/word/media/"
TRT = ["CT0", "CTR", "NT0", "NTR"]
COL = {"straw": (128, 160, 255), "root": (255, 0, 0), "rhizo": (0, 255, 0)}
PCOLS = {"image8.png": [(104, 486), (552, 934), (1001, 1383)], "image9.png": [(105, 487), (548, 930), (990, 1373)]}
DEP = ["0-15 cm", "15-30 cm", "30-45 cm"]
TOPV = [8.0, 1.0, 1.0]


def cl(idx, gap=4):
    gg = []
    for i in idx:
        if gg and i - gg[-1][-1] <= gap:
            gg[-1].append(i)
        else:
            gg.append([i])
    return [float(np.mean(x)) for x in gg]


res = {}
for fig, fn in (("S8 rice season", "image8.png"), ("S9 wheat season", "image9.png")):
    a = np.asarray(Image.open(M + fn).convert("RGB")).astype(int)
    g = a.mean(2)
    H, W = g.shape
    dark = g < 100
    masks = {k: np.sqrt(((a - np.array(c)) ** 2).sum(2)) < 80 for k, c in COL.items()}
    out = {}
    for ci, (xl, xr) in enumerate(PCOLS[fn]):
        frac = dark[:, int(xl) + 3:int(xr) - 3].mean(1)
        hy = cl([y for y in range(H) if frac[y] > 0.9])
        # pair frames: rows (top, bottom) for the two panels
        rows = [(hy[0], hy[1]), (hy[2], hy[3])] if len(hy) >= 4 else None
        for ri, (yt, yb) in enumerate(rows):
            yr = "2020" if ri == 0 else "2021"
            k = TOPV[ci] / (yb - yt)
            y0 = int(yt + 0.2 * (yb - yt))   # skip the legend swatches (top 20 % of panel a; no bar reaches it)
            anyc = (masks["straw"] | masks["root"] | masks["rhizo"])[y0:int(yb) - 1, int(xl) + 2:int(xr) - 1]
            colhas = anyc.sum(0) > 3
            xs = np.where(colhas)[0]
            segs = []
            for x in xs:
                if segs and x - segs[-1][-1] <= 2:
                    segs[-1].append(x)
                else:
                    segs.append([x])
            segs = [s for s in segs if len(s) > 20]
            if len(segs) != 4:
                print(fig, DEP[ci], yr, "bars found", len(segs))
            vals = {}
            for t, s in zip(TRT, segs):
                cx = range(int(xl) + 2 + s[0] + 4, int(xl) + 2 + s[-1] - 3)
                seg = {}
                for nm, m in masks.items():
                    rr = [y for y in range(y0, int(yb) - 1) if m[y, list(cx)].mean() > 0.6]
                    seg[nm] = round((max(rr) + 1 - min(rr)) * k, 3) if rr else 0.0
                    seg[nm + "_top"] = round((yb - min(rr)) * k, 3) if rr else None
                tops = [seg[nm + "_top"] for nm in COL if seg[nm + "_top"] is not None]
                vals[t] = {"total": round(max(tops), 3), "straw": seg["straw"], "root": seg["root"], "rhizo": seg["rhizo"]}
            out[f"{DEP[ci]} {yr}"] = vals
            print(fig, DEP[ci], yr, {t: v["total"] for t, v in vals.items()})
    res[fig] = out
json.dump(res, open("/home/user/sonu/digitised/ahmad_cinput.json", "w"), indent=1)
