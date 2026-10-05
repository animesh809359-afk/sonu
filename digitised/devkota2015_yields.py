"""Devkota et al. 2015 Agric. For. Meteorol. 214-215:266-280 - Fig. 3A (rice) and Fig. 4 (wheat) MEASURED grain yields,
read exactly from the vector scatter markers (y = measured, x = simulated). Marker key from the legend:
filled circle WSRF-R0-FI, open circle DSRB-R0, filled down-triangle DSRB-R50, open up-triangle DSRB-R100,
filled square DSRF-R0, open square DSRF-R50, filled diamond DSRF-R100, open diamond WSRF-R0-AWD (2009 only).
Usage: python digitised/devkota2015_yields.py <pdf>  -> devkota2015_yields.json"""
import json
import sys

import pdfplumber

pdf = pdfplumber.open(sys.argv[1])


def black(c):
    return c is not None and len(c) == 4 and c[3] > 0.5


def markers(page, box):
    x0, x1, ytop, ybot = box
    out = []
    for o in page.curves:
        pts = o["pts"]
        if not o.get("fill") or len(pts) not in (4, 5):
            continue
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        if not (x0 + 3 < cx < x1 and ytop < cy < ybot - 1):
            continue
        filled = black(o.get("non_stroking_color"))
        if len(pts) == 4:   # triangle
            apex = pts[0]
            shape = "tri_down" if apex[1] > cy else "tri_up"
        else:
            half = (max(xs) - min(xs)) / 2
            shape = "diamond" if half > 2.2 else "circle"
        out.append((shape, filled, cx, cy))
    for o in page.rects:
        w, h = o["x1"] - o["x0"], o["bottom"] - o["top"]
        if not o.get("fill") or not (2.5 < w < 4.5 and 2.5 < h < 4.5):
            continue
        cx, cy = (o["x0"] + o["x1"]) / 2, (o["top"] + o["bottom"]) / 2
        if x0 + 3 < cx < x1 and ytop < cy < ybot - 1:
            out.append(("square", black(o.get("non_stroking_color")), cx, cy))
    return out


KEY = {("circle", True): "WSRF-R0-FI", ("circle", False): "DSRB-R0-AWD", ("tri_down", True): "DSRB-R50-AWD", ("tri_up", False): "DSRB-R100-AWD",
       ("square", True): "DSRF-R0-AWD", ("square", False): "DSRF-R50-AWD", ("diamond", True): "DSRF-R100-AWD", ("diamond", False): "WSRF-R0-AWD"}
# (page index, panel, plot box x0, x1, y(7500), y(0)), legend excluded by x > legend column + 40
PANELS = [(6, "rice 2008", (191.4, 311.2, 29.6, 128.3), 222), (6, "rice 2009", (365.6, 491.8, 30.1, 132.7), 400),
          (7, "wheat 2008", None, None), (7, "wheat 2009", None, None)]
res = {}
for pi, name, box, legx in PANELS:
    page = pdf.pages[pi]
    if box is None:  # wheat panels on p. 8: find the two plot frames (largest rects near the top)
        fr = sorted([r for r in page.rects if r["top"] < 120 and (r["x1"] - r["x0"]) > 100], key=lambda r: r["x0"])
        fr = [fr[0], fr[-1]] if name == "wheat 2008" else [fr[-1]]
        r = fr[0] if name == "wheat 2008" else fr[-1]
        box = (r["x0"], r["x1"], r["top"], r["bottom"])
        legx = r["x0"] + 30
    x0, x1, ytop, ybot = box
    ms = [m for m in markers(page, box) if m[2] > legx]
    vals = {}
    for shape, filled, cx, cy in ms:
        k = KEY.get((shape, filled))
        y = (ybot - cy) / (ybot - ytop) * 7500
        x = (cx - x0) / (x1 - x0) * 7500
        vals.setdefault(k, []).append((round(y), round(x)))
    res[name] = {"box": [round(v, 1) for v in box], "points": vals}
    print(name, [round(v, 1) for v in box], vals)
json.dump(res, open(sys.argv[1].replace(".pdf", "") and "digitised/devkota2015_yields.json", "w"), indent=1)
