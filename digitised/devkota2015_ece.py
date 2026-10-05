"""Devkota et al. 2015 Eur. J. Agron. 62:98-109 - Fig. 3 lower-left panel ('Wheat 2009' = wheat season 2008/09): season-averaged ECe (dS/m) at
10 / 20 / 30 / 50 / 80 cm (bottoms of the 0-10, 10-20, 20-30, 30-50, 50-80 cm layers), read exactly from the vector markers.
Markers: filled circle DSRB-R0, open circle DSRB-R100, filled triangle DSRF-R0, open triangle DSRF-R100, filled square WSRF-R0 (legend of the rice-2008 panel).
x axis 0 at 188.8 pt, 5 dS/m at 334.1 pt. Usage: python digitised/devkota2015_ece.py <pdf> -> digitised/devkota2015_ece.json"""
import json
import sys

import pdfplumber

p = pdfplumber.open(sys.argv[1]).pages[5]
X0, X5 = 188.8, 334.1
out = {}
for o in p.curves + p.rects:
    pts = o["pts"]
    if not (565 < o["top"] < 672 and 186 < o["x0"] < 340) or not o.get("fill"):
        continue
    w, h = o["x1"] - o["x0"], o["bottom"] - o["top"]
    if not (3.5 < w < 4.7 and 3.5 < h < 4.2) or len(pts) not in (4, 5):
        continue
    nsc = o.get("non_stroking_color")
    filled = nsc is not None and len(nsc) == 4 and nsc[3] > 0.5
    shape = "circle" if len(pts) == 5 else ("square" if abs(w - h) < 0.2 else "triangle")
    key = {("circle", True): "DSRB-R0", ("circle", False): "DSRB-R100", ("triangle", True): "DSRF-R0", ("triangle", False): "DSRF-R100", ("square", True): "WSRF-R0-FI"}[(shape, filled)]
    out.setdefault(key, []).append((round((o["top"] + o["bottom"]) / 2, 1), round(((o["x0"] + o["x1"]) / 2 - X0) / (X5 - X0) * 5, 2)))
res = {k: [v for _, v in sorted(set(vs))] for k, vs in out.items()}
json.dump(res, open("digitised/devkota2015_ece.json", "w"), indent=1)
print(res)
