"""Digitise Kader et al. 2022 FCR 287:108636 Fig. 1 (vector PDF): rows = rice / wheat / mungbean, columns = 2018-19 / 2019-20 / 2020-21.
Filled circle = CT, open = ST; five points per series = N1..N5 (60-140 % RFD)."""
import json, sys
import pdfplumber
pdf = sys.argv[1]
p = pdfplumber.open(pdf).pages[6]
cv = p.curves
axes = [c for c in cv if (c['x1'] - c['x0']) < 0.8 and (c['bottom'] - c['top']) > 60 and c['top'] > 300]
axes.sort(key=lambda c: (round(c['top'] / 50), c['x0']))
out = {}
YMAX = None
for ax in axes:
    ax_x = ax['x1']
    ticks = sorted({round((t['top'] + t['bottom']) / 2, 2) for t in cv if abs(t['x1'] - ax_x) < 0.6 and (t['x1'] - t['x0']) < 2 and (t['bottom'] - t['top']) < 0.6
                    and ax['top'] - 1 < t['top'] < ax['bottom'] + 1})
    n = len(ticks) - 1
    ymax = {5: 5.0 if n == 5 else 2.0, 7: 7.0, 4: 2.0}.get(n)
    if n == 5:
        pass
    y0, y1 = ticks[-1], ticks[0]
    mk = [c for c in cv if 2.5 < (c['x1'] - c['x0']) < 3.1 and len(c['pts']) in (15, 16) and ax_x + 25 < c['x0'] < ax_x + 160 and y1 - 3 < c['top'] < y0 + 2]
    pts = []
    for m in mk:
        cx, cy = (m['x0'] + m['x1']) / 2, (m['top'] + m['bottom']) / 2
        filled = any(len(c['pts']) == 5 and abs((c['x0'] + c['x1']) / 2 - cx) < 0.3 and abs((c['top'] + c['bottom']) / 2 - cy) < 0.3 for c in cv)
        pts.append((round(cx, 1), cy, 'CT' if filled else 'ST'))
    out[f"{round(ax['top'])}_{round(ax_x)}"] = {"ticks": n, "y0": y0, "y1": y1, "pts": [(x, round(y, 2), s) for x, y, s in sorted(pts)]}
for k, v in out.items():
    print(k, v['ticks'], v['y0'], v['y1'], len(v['pts']))
    for x, y, s in v['pts']:
        print('   ', x, s, round((v['y0'] - y) / (v['y0'] - v['y1']), 4))

# top-left panel (rice 2018-19): its y-axis is drawn as separate segments; ticks found manually at y=456.32 (0) and 374.92 (7.0)
tl = []
for m in cv:
    if 2.5 < (m['x1'] - m['x0']) < 3.1 and len(m['pts']) in (15, 16) and 110 < m['x0'] < 200 and 370 < m['top'] < 457:
        cx, cy = (m['x0'] + m['x1']) / 2, (m['top'] + m['bottom']) / 2
        filled = any(len(c['pts']) == 5 and abs((c['x0'] + c['x1']) / 2 - cx) < 0.3 and abs((c['top'] + c['bottom']) / 2 - cy) < 0.3 for c in cv)
        tl.append((round(cx, 1), round(cy, 2), 'CT' if filled else 'ST'))
out["375_78"] = {"ticks": 7, "y0": 456.32, "y1": 374.92, "pts": sorted(tl)}
MAP = {"375_78": ("rice", "2018-19"), "375_243": ("rice", "2019-20"), "375_405": ("rice", "2020-21"),
       "491_78": ("wheat", "2018-19"), "492_243": ("wheat", "2019-20"), "492_405": ("wheat", "2020-21"),
       "608_78": ("mungbean", "2018-19"), "609_243": ("mungbean", "2019-20"), "609_405": ("mungbean", "2020-21")}
YM = {7: 7.0, 5: 5.0, 4: 2.0}
res = {}
for k, v in out.items():
    crop, yr = MAP[k]
    for s in ("CT", "ST"):
        xs = [(x, y) for x, y, ss in v['pts'] if ss == s]
        assert len(xs) == 5, (k, s, xs)
        res.setdefault(crop, {}).setdefault(yr, {})[s] = [round((v['y0'] - y) / (v['y0'] - v['y1']) * YM[v['ticks']], 2) for x, y in sorted(xs)]
json.dump(res, open(__file__.replace('kader_fig1.py', 'kader_fig1.json'), 'w'), indent=1)
for c in res:
    for y in res[c]:
        print(c, y, res[c][y])
