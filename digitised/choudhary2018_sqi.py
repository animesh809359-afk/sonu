"""Digitise Choudhary et al. 2018 ASE Fig. 2 (SQI, T1-T14). Raster image (pdfimages p.8, 1271 x 578): y axis = grey line at the left with tick stubs
every 0.10 (0.00 at the x axis ... 1.00 at the top stub, labels on the vector layer); hatched bars - bar top = first row whose hatch-ink
fraction across the bar's columns exceeds 0.25 (error bars and letters are on the vector layer, not in the image)."""
import json
import numpy as np
from PIL import Image

F = "/tmp/claude-0/-home-user-sonu/2fb4e6fa-f356-5f43-b5d3-cf878a7db82d/scratchpad/b16/cimg/c-000.png"
a = np.asarray(Image.open(F).convert("L")).astype(float)
H, W = a.shape
ink = a < 200
ax = 14
tk = [y for y in range(H) if ink[y, 2:11].mean() > 0.7]
grp = []
for y in tk:
    if grp and y - grp[-1][-1] <= 2:
        grp[-1].append(y)
    else:
        grp.append([y])
tk = [float(np.mean(t)) for t in grp]
xa = int(np.argmax(ink[:, 20:].sum(1)))   # x axis row
ticks = sorted(tk)
vals = [round(1.0 - 0.1 * i, 2) for i in range(len(ticks))]
k, b = np.polyfit(ticks, vals, 1)
colink = ink[xa - 30:xa - 6, ax + 12:].mean(0)
xs = np.where(colink > 0.25)[0] + ax + 12
bars = []
for x in xs:
    if bars and x - bars[-1][-1] <= 3:
        bars[-1].append(x)
    else:
        bars.append([x])
bars = [bb for bb in bars if len(bb) > 15]
out = {}
for i, bb in enumerate(bars):
    c0, c1 = bb[0] + 2, bb[-1] - 1
    frac = ink[:xa - 6, c0:c1].mean(1)
    top = int(np.where(frac > 0.25)[0].min())
    out[f"T{i + 1}"] = round(float(k * top + b), 3)
print(len(ticks), "ticks", [round(t) for t in ticks], "bars", len(bars))
print(out)
json.dump({"ticks_px": ticks, "sqi": out}, open("/home/user/sonu/digitised/choudhary2018_sqi.json", "w"), indent=1)
