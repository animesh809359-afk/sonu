"""Zhao et al. 2021 Soil Tillage Res. 212:105071 - Fig. 1 water-stable aggregate mass (g/kg soil, 0-20 cm) read exactly from the vector bars
(page 4). Axis: tick 0 at y 658.62, 600 at 526.58 pt. Fill colours from the legend: white = silt + clay (<53 um), grey 0.749 = microaggregate
(53-250 um), grey 0.498 = small macroaggregate (250-2000 um), black = large macroaggregate (>2000 um).
Usage: python digitised/zhao2021_fig1.py <pdf> -> digitised/zhao2021_fig1.json"""
import json
import sys

import pdfplumber

p = pdfplumber.open(sys.argv[1]).pages[3]
Y0, Y600 = 658.62, 526.58
COL = {(1.0, 1.0, 1.0): "silt+clay", (0.749, 0.749, 0.749): "micro", (0.498, 0.498, 0.498): "small macro", (0.0, 0.0, 0.0): "large macro"}
bars = [r for r in p.rects if r["top"] > 520 and r["x0"] > 85 and r["x0"] < 300 and 4.5 < r["x1"] - r["x0"] < 6 and abs(r["bottom"] - 658.54) < 0.1]
bars.sort(key=lambda r: r["x0"])
TRT = ["CT", "CTFR", "RTFR", "CTOM", "RTOM"]
res = {}
for i, r in enumerate(bars):
    t = TRT[i // 4]
    res.setdefault(t, {})[COL[tuple(r["non_stroking_color"])]] = round((Y0 - r["top"]) / (Y0 - Y600) * 600, 1)
json.dump(res, open("digitised/zhao2021_fig1.json", "w"), indent=1)
for t, v in res.items():
    print(t, v, "sum", round(sum(v.values()), 1))
