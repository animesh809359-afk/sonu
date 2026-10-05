"""Mittal et al. 2020 Plant Archives 20(1):2629-2635 - Figs 1-5 (raster bar charts, extracted with pdfimages -png).
Calibration from the y-axis tick marks found in each image; each bar = contiguous non-white run from the baseline upward, read at
columns 25-75 % across the bar (avoids the centred error bar), median top. Groups split into equal-width bars.
Usage: python digitised/mittal2020_bars.py <dir with m-000..m-004.png>  -> digitised/mittal2020_bars.json"""
import json
import sys

import numpy as np
from PIL import Image

D = sys.argv[1]
# file, y pixel of zero, y pixel of top tick, top tick value, bars per group, group labels
FIG = {"MBC": ("m-000.png", 313, 26, 700.0, 4, ["Rice 2015", "Wheat 2015-16", "Rice 2016", "Wheat 2016-17"]),
       "MBN": ("m-001.png", 303, 39, 90.0, 4, ["Rice 2015", "Wheat 2015-16", "Rice 2016", "Wheat 2016-17"]),
       "DHA": ("m-002.png", 295, 23, 1.80, 4, ["Rice 2015", "Wheat 2015-16", "Rice 2016", "Wheat 2016-17"]),
       "TN": ("m-003.png", 308, 20, 0.20, 2, ["T1", "T2", "T3", "T4"]),
       "TOC": ("m-004.png", 297, 26, 1.6, 2, ["T1", "T2", "T3", "T4"])}
res = {}
for key, (f, y0, yt, vt, nb, labs) in FIG.items():
    im = np.array(Image.open(f"{D}/{f}").convert("L")).astype(int)
    base = y0 - 4
    dark = im[base] < 252
    runs, x = [], 0
    while x < im.shape[1]:
        if dark[x]:
            s = x
            while x < im.shape[1] and dark[x]:
                x += 1
            if x - s > 30:
                runs.append((s, x))
        x += 1
    runs = [r for r in runs if r[0] > 110 or key in ("DHA",) and r[0] > 100][:len(labs)]
    out = {}
    for lab, (s, e) in zip(labs, runs):
        w = (e - s) / nb
        vals = []
        for b in range(nb):
            tops = []
            for c in range(int(s + b * w + 0.25 * w), int(s + b * w + 0.75 * w) + 1):
                if abs(c - (s + (b + 0.5) * w)) < 3:
                    continue  # skip error-bar line
                y = base
                while y > 0 and im[y, c] < 252:
                    y -= 1
                tops.append(y + 1)
            top = float(np.median(tops))
            vals.append(round((y0 - top) / (y0 - yt) * vt, 3 if vt < 5 else 1))
        out[lab] = vals
    res[key] = out
    print(key, out)
json.dump(res, open("digitised/mittal2020_bars.json", "w"), indent=1)
