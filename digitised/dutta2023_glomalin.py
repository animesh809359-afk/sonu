"""Digitise Dutta et al. 2023 Fig. 7 (glomalin mg/g in macro / micro aggregates, 0-5 and 5-15 cm; 9 treatments x 4 coloured bars; raster).
Y axis = longest dark vertical run; ticks 0-2.5 (step 0.5) read as dark stubs left of the axis. Each bar = connected component of its fill colour;
top = first row of the component (error bars are black and drawn over the top, so the coloured fill top is the bar value)."""
import json
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

F = "/tmp/claude-0/-home-user-sonu/2fb4e6fa-f356-5f43-b5d3-cf878a7db82d/scratchpad/b16/dimg/d-010-012.png"
a = np.asarray(Image.open(F).convert("RGB")).astype(int)
g = a.mean(2)
H, W = g.shape
dark = g < 200
runs = []
for x in range(W // 4):
    c, best = 0, 0
    for v in dark[:, x]:
        c = c + 1 if v else 0
        best = max(best, c)
    runs.append(best)
ax = int(np.argmax(runs))
col = dark[:, ax]
ys = np.where(col)[0]
tk = [y for y in range(ys.min(), ys.max() + 1) if dark[y, ax - 6:ax - 1].sum() >= 4]
grp = []
for y in tk:
    if grp and y - grp[-1][-1] <= 1:
        grp[-1].append(y)
    else:
        grp.append([y])
tk = [float(np.mean(t)) for t in grp]
TV = [0, 0.5, 1, 1.5, 2, 2.5]
tk = sorted(tk)[-len(TV):]
k, b = np.polyfit(sorted(tk, reverse=True), TV, 1)
SER = {"0-5 MA": (31, 119, 180), "0-5 MI": (227, 26, 28), "5-15 MA": (51, 160, 44), "5-15 MI": (106, 61, 154)}
# legend colours sampled from the legend squares (top 12 % of the image)
top = a[:int(0.12 * H)]
sat = (top.max(2) - top.min(2)) > 60
lab, n = ndi.label(sat)
leg = []
for i in range(1, n + 1):
    yy, xx = np.where(lab == i)
    if len(yy) > 60:
        leg.append((xx.min(), np.median(top[yy, xx], axis=0)))
leg.sort(key=lambda t: t[0])
cols = dict(zip(SER, [c for _, c in leg]))
bars = []
for nm, c in cols.items():
    d = np.sqrt(((a - c) ** 2).sum(2))
    m = d < 40
    m[:int(0.12 * H)] = False
    m = ndi.binary_opening(m, iterations=2)
    lab, n = ndi.label(m)
    for i in range(1, n + 1):
        yy, xx = np.where(lab == i)
        if len(yy) < 60 or (xx.max() - xx.min()) < 8:
            continue
        # bar top: median over the bar's columns of the first coloured row
        tops = [yy[xx == x].min() for x in range(xx.min() + 2, xx.max() - 1)]
        bars.append((float(xx.mean()), nm, round(float(k * np.median(tops) + b), 3)))
bars.sort()
TRT = ["ZT-NR", "ZT-RB", "ZT-R", "CT-NR", "CT-RB", "CT-R", "ST-NR", "ST-RB", "ST-R"]
out = {t: {} for t in TRT}
per = {}
for x, nm, v in bars:
    per.setdefault(nm, []).append((x, v))
for nm, lst in per.items():
    lst.sort()
    if len(lst) != 9:
        print("WARNING", nm, len(lst), lst)
    for t, (x, v) in zip(TRT, lst):
        out[t][nm] = v
for t in TRT:
    print(t, out[t])
json.dump({"ticks_px": tk, "axis_x": ax, "colours": {k2: list(map(float, v)) for k2, v in cols.items()}, "glomalin_mg_g": out},
          open("/home/user/sonu/digitised/dutta2023_glomalin.json", "w"), indent=1)
