"""Digitise Roy et al. 2022 Geoderma 405:115391 Fig. 1 (soil penetration resistance, vector PDF page 5).
x: tick labels 0.4 (centre x=72.35) ... 3.4 (275.55) MPa; nine markers per series at 5-cm layer mid-depths 0-5 ... 40-45 cm."""
import json, sys
import pdfplumber
p = pdfplumber.open(sys.argv[1]).pages[4]
X = lambda x: round(0.4 + (x - 72.35) / ((275.55 - 72.35) / 3.0), 2)
def curves(col, n):
    s = sorted({(round((c['x0'] + c['x1']) / 2, 2), round((c['top'] + c['bottom']) / 2, 2)) for c in p.curves if c['top'] < 240 and c.get('stroking_color') == col and len(c['pts']) == n}, key=lambda t: t[1])
    return s
sc1 = curves((0.255, 0.435, 0.651), 13)
sc3 = curves((0.525, 0.643, 0.29), 8)
sc2 = sorted({(round((r['x0'] + r['x1']) / 2, 2), round((r['top'] + r['bottom']) / 2, 2)) for r in p.rects if r.get('non_stroking_color') == (0.667, 0.275, 0.263) and r['x0'] > 100}, key=lambda t: t[1])
res = {}
for name, s in (("Sc1", sc1), ("Sc2", sc2), ("Sc3", sc3)):
    assert len(s) == 9, (name, s)
    res[name] = [X(x) for x, y in s]
    print(name, res[name], [round((y - 93.7) / 15.84 * 5, 1) for x, y in s])
json.dump(res, open(__file__.replace('.py', '.json'), 'w'), indent=1)
