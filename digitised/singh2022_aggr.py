"""Singh G. et al. 2022 Soil Tillage Res. 217:105272 - Figs 1 (0-5 cm) and 2 (5-15 cm): stacked water-stable aggregate fractions (% of soil).
The hatch patterns are a raster layer (pdfimages -png, pages 3-4); the solid black '>2 mm' segment and the axes are vector and absent from the raster,
so the >2 mm share = 100 % minus the three patterned segments. Calibration: light-blue 10 % gridlines in each raster (top gridline = 100 %).
Per bar: top of the horizontal-line block (<0.053 mm), top of the vertical-line block (0.053-0.25 mm), top of the diagonal block (0.25-2 mm)
and bottom of the diagonal block (= top of the >2 mm segment), found from row-to-row pattern comparison.
Usage: python digitised/singh2022_aggr.py <dir with s-000.png, s-001.png> -> digitised/singh2022_aggr.json"""
import json
import sys

import numpy as np
from PIL import Image

D = sys.argv[1]
TRT = ["TPR-CTW", "TPR-ZTW", "DSR+MBR-ZTW+RR-ZTMB+WR", "DSR+MBR-ZTW-ZTMB", "DSR+BM-ZTW+RR", "DSR-ZTW+RR", "DSR+BM-ZTW", "DSR-ZTW"]
FIG = {"0-5 cm": ("s-000.png", 43.0, 49.44), "5-15 cm": ("s-001.png", 41.0, 63.95)}   # y of 100 % gridline, px per 10 %
res = {}
for depth, (f, y100, s10) in FIG.items():
    g = np.array(Image.open(f"{D}/{f}").convert("L")).astype(int)
    h, w = g.shape
    dark = g < 128
    cols = dark.sum(0)
    runs, x = [], 0
    while x < w:
        if cols[x] > 20:
            s = x
            while x < w and cols[x] > 20:
                x += 1
            if runs and s - runs[-1][1] < 8:
                runs[-1] = (runs[-1][0], x)
            else:
                runs.append((s, x))
        x += 1
    pct = lambda y: 100 - (y - y100) / s10 * 10
    out = {}
    for t, (s, e) in zip(TRT, runs):
        seg = dark[:, s + 2:e - 2]
        frac = seg.mean(1)
        top = next(y for y in range(h) if frac[y] > 0.8)  # first full horizontal hatch line (letters above bars ignored)
        # vertical block: first row whose dark pattern repeats in the next 2 rows (0.08-0.7 coverage); then extend downwards
        # while each row keeps >= 85 % of that row's dark columns and adds < 15 % new ones (a diagonal hatch shifts every row)
        vtop = next(y for y in range(top, h - 3) if 0.08 < frac[y] < 0.7 and (seg[y] == seg[y + 1]).all() and (seg[y] == seg[y + 2]).all())
        ref = seg[vtop + 3]
        y = vtop
        while y + 1 < h:
            r = seg[y + 1]
            if (r & ref).sum() >= 0.85 * ref.sum() and (r & ~ref).sum() <= 0.15 * ref.sum():
                y += 1
            else:
                break
        vbot = y
        diag = [yy for yy in range(vbot + 1, h) if frac[yy] > 0.05]
        dtop, dbot = diag[0], diag[-1]
        sc, mi, ma = pct(top) - pct(vtop), pct(vtop) - pct(dtop), pct(dtop) - pct(dbot + 1)
        out[t] = {"<0.053": round(sc, 1), "0.053-0.25": round(mi, 1), "0.25-2": round(ma, 1), ">2": round(pct(dbot + 1) - 0, 1),
                  "top_pct": round(pct(top), 1)}
    res[depth] = out
    for t, v in out.items():
        print(depth, t, v)
json.dump(res, open("digitised/singh2022_aggr.json", "w"), indent=1)
