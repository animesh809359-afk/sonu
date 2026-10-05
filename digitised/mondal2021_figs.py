"""Mondal et al. 2021 Eur. J. Soil Sci. 72:1742-1761 - raster figures (pdfimages -png -p): Fig. 1 BD (m-004-005), Fig. 2 SOC (m-008-010),
Fig. 3 aggregate-associated SOC, panels a-e (m-010-013), Fig. 6 yields (m-013-019).
Horizontal bars read with digitised/hbar.py (tick-calibrated, bar-end = right outline), every bar checked on an overlay image; the few bars
whose outline merged with an error-bar cap / significance letter were set from the column profile (MANUAL, listed below).
Checks: Fig. 6 rice bars reproduce Table 5 rice yields within 0.05 Mg/ha; Fig. 1 15-30 cm TA 4.7 / 5.6 % above pCA2 / fCA (text 4.7-5.6 %); Fig. 2 fCA +45.5 % / +32.5 % vs TA at 0-7.5 / 7.5-15 cm (text 46 / 33 %);
stock check 6.147 g/kg x 1.546 x 7.5 cm x 0.1 = 7.13 Mg/ha (Table 2: 7.12); Fig. 3a fCA +45.3 % vs TA at 0-7.5 (text 45.2 %).
Usage: python digitised/mondal2021_figs.py <image dir> -> digitised/mondal2021_figs.json"""
import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hbar import groups, read, right_end  # noqa: E402

D = sys.argv[1]
TRT = ["TA", "pCA1", "fCA", "pCA2"]
LAY = ["0-7.5", "7.5-15", "15-30", "30-45", "45-60"]
img = lambda f: np.array(Image.open(os.path.join(D, f)).convert("L")).astype(int)


def tab(out):
    return {LAY[i]: dict(zip(TRT, row)) for i, row in enumerate(out)}


res = {}
_, o = read(img("m-004-005.png"), 100, 156, 1.30, 0.05, 102, 871)
res["BD"] = tab(o)
res["BD"]["15-30"]["pCA2"] = 1.503      # MANUAL: outline at x 901 px (dotted bar; automatic read stopped on an inner dot column)
_, o = read(img("m-008-010.png"), 101, 158, 0, 2, 103, 878)
res["SOC"] = tab(o)
g = img("m-010-013.png")
PAN = {"2-4 mm": (104, 164, 106, 868, 1000), "0.5-2 mm": (105, 1051, 107, 868, 1771), "0.25-0.5 mm": (873, 164, 875, 1655, 1000),
       "0.12-0.25 mm": (871, 1051, 873, 1655, 1771), "0.053-0.12 mm": (1658, 164, 1660, 2396, 1000)}
res["ASOC"] = {}
for k, (ar, ac, y0, y1, xb) in PAN.items():
    _, o = read(g, ar, ac, 0, 2, y0, y1, x1=xb, nticks=7)
    res["ASOC"][k] = tab(o)
MAN = {("2-4 mm", "15-30", "TA"): 4.356, ("0.25-0.5 mm", "15-30", "pCA2"): 4.79, ("0.25-0.5 mm", "30-45", "TA"): 3.633,
       ("0.12-0.25 mm", "0-7.5", "TA"): 6.877, ("0.053-0.12 mm", "30-45", "TA"): 3.644, ("0.053-0.12 mm", "45-60", "TA"): 3.778}
for (p, l, t), v in MAN.items():   # MANUAL: end of the solid black run / outline from the column profile
    res["ASOC"][p][l][t] = v
# Fig. 6 vertical bars: image flipped/transposed so the baseline (y 702 px = 0) becomes a left axis; 20 Mg/ha at y 14 px
g6 = img("m-013-019.png")
gt = g6[::-1, :].T.copy()
base = g6.shape[0] - 1 - 702
G6 = groups(gt, base, 125, gt.shape[0] - 5)
lab6 = ["Rice 2018", "Rice 2019", "REY (2 crops) 2017-18", "REY (2 crops) 2018-19", "SREY 2017-18", "SREY 2018-19"]
res["Fig6"] = {lab: dict(zip(TRT, [round((right_end(gt, e[k], e[k + 1], base) - base) / ((702 - 14) / 20), 2) for k in range(4)]))
               for lab, e in zip(lab6, G6)}
res["manual"] = [f"{p} {l} {t}" for (p, l, t) in MAN] + ["BD 15-30 pCA2"]
json.dump(res, open("digitised/mondal2021_figs.json", "w"), indent=1, default=float)
for k in ("BD", "SOC"):
    for l, v in res[k].items():
        print(k, l, v)
for p, d in res["ASOC"].items():
    for l, v in d.items():
        print("ASOC", p, l, v)
