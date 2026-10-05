"""Hoque et al. 2023 FCR 291:108791 Fig. 4 (raster, 1500x1441 px): area-centroid of each violin (3-yr x 4-rep distribution) per panel.
Columns left->right: R-M, R-MB, R-M-MB, R-R, R-W, R-W-MB x (AT, CA, CT). y calibrated on the axis tick marks."""
import json, sys
import numpy as np
from PIL import Image
a = np.array(Image.open(sys.argv[1]).convert("RGB")).astype(int)
R, G, B = a[..., 0], a[..., 1], a[..., 2]
panels = {
    "gross_margin": ((40, 470), (B > 90) & (R < 60) & (G < 110), [(52, 1800), (120, 1500), (189, 1200), (257, 900), (328, 600), (465, 0)]),
    "production_cost": ((470, 895), (R > 170) & (G < 90) & (B < 90), [(577.5, 1500), (683, 1200), (785.5, 900), (890, 600)]),
    "labour_use": ((895, 1330), (G > 170) & (B > 140) & (R < 140), [(1003, 250), (1106, 200), (1211, 150), (1314, 100)]),
}
CS = ["R-M", "R-MB", "R-M-MB", "R-R", "R-W", "R-W-MB"]
out = {}
for name, ((y0, y1), mask, ticks) in panels.items():
    m = mask.copy(); m[:y0] = False; m[y1:] = False; m[:, :165] = False
    k, c = np.polyfit([t[0] for t in ticks], [t[1] for t in ticks], 1)
    col = m.sum(0)
    runs, cur = [], None
    for x, v in enumerate(col):
        if v > 2:
            if cur is None: cur = [x, x]
            else: cur[1] = x
        elif cur is not None and x - cur[1] > 6:
            runs.append(cur); cur = None
    if cur: runs.append(cur)
    runs = [r for r in runs if r[1] - r[0] > 8]
    assert len(runs) == 18, (name, runs)
    vals = []
    for x0, x1 in runs:
        sub = m[:, x0:x1 + 1]
        ys, xs = np.nonzero(sub)
        vals.append(round(float(k * ys.mean() + c), 1))
    out[name] = {cs: dict(zip(["AT", "CA", "CT"], vals[3 * i:3 * i + 3])) for i, cs in enumerate(CS)}
json.dump(out, open(__file__.replace(".py", ".json"), "w"), indent=1)
print(json.dumps(out, indent=1))
