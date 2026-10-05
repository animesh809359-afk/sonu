"""Gathala et al. 2017 J Ecosys Ecograph 7:246 - Figs 1-4 read exactly from the vector (Excel) chart objects.
Fig. 1 BD (polyline vertices per treatment colour), Fig. 2 aggregates >0.25 mm (bar tops) + MWD (polyline), Fig. 3 SPR (polylines), Fig. 4 steady IR (bar tops).
Usage: python digitised/gathala2017_figs.py <pdf>  -> digitised/gathala2017_figs.json"""
import json
import sys

import pdfplumber

pdf = pdfplumber.open(sys.argv[1])
COL = {(0.753, 0.0, 0.0): "T1", (1.0, 0.0, 0.0): "T2", (0.0, 0.69, 0.941): "T3", (0.0, 0.439, 0.753): "T4", (0.439, 0.188, 0.627): "T5",
       (0.0, 0.69, 0.314): "T6", 0.0: "Initial"}


def series(page, xmin, xmax, ymin, ymax, npts):
    out = {}
    for o in page.curves:
        pts = o["pts"]
        sc = o.get("stroking_color")
        key = tuple(sc) if isinstance(sc, (list, tuple)) else sc
        if len(pts) == npts and key in COL and o.get("fill") is False and xmin < o["x0"] and o["x1"] < xmax and ymin < o["top"] and o["bottom"] < ymax:
            out.setdefault(COL[key], [p[0] for p in pts])
    return out


res = {}
# Fig. 1 BD (page 6): x 140.7 = 1.45, 318.2 = 1.80; depth vertices 2.5 / 7.5 / 12.5 / 17.5 cm (layers 0-5, 6-10, 11-15, 16-20)
s = series(pdf.pages[6], 135, 320, 150, 316, 4)
res["BD"] = {t: [round(1.45 + (x - 140.7) / (318.2 - 140.7) * 0.35, 3) for x in xs] for t, xs in s.items()}
# Fig. 3 SPR (page 7 lower-left): x 137.5 = 0, 311.7 = 3.5 MPa; vertices at 5, 10 ... 45 cm
s = series(pdf.pages[7], 135, 320, 480, 660, 9)
res["SPR"] = {t: [round((x - 137.5) / (311.7 - 137.5) * 3.5, 3) for x in xs] for t, xs in s.items()}
# Fig. 2 (page 7 top): left axis 0 at y 290.4, 70 at 129.9; right axis MWD 0..2.5 on the same span
p = pdf.pages[7]
bars = sorted({round(r["x0"]): round(r["top"], 1) for r in p.rects if str(r.get("non_stroking_color")) == "P0" and r.get("fill")
               and 150 < r["x0"] < 450 and abs(r["bottom"] - 290.4) < 0.5}.items())
lab = ["Initial", "T1", "T2", "T3", "T4", "T5", "T6", "No residue", "Residue"]
res["AGG>0.25"] = {l: round((290.4 - top) / (290.4 - 129.9) * 70, 2) for l, (x, top) in zip(lab, bars)}
mwd = [o for o in p.curves if len(o["pts"]) == 9 and o["top"] > 140 and o["bottom"] < 200][0]
res["MWD"] = {l: round((290.4 - y) / (290.4 - 129.9) * 2.5, 3) for l, (x, y) in zip(lab, mwd["pts"])}
# Fig. 4 (page 8): bars bottom 638.3 = 0, 543.3 = 3.5 mm/h; order Initial, T1-T6, No residue, Residue
p = pdf.pages[8]
bars = sorted({round(r["x0"]): round(r["top"], 1) for r in p.rects if abs(r["bottom"] - 638.3) < 0.3 and 85 < r["x0"] < 285 and r.get("fill")
               and 9 < r["x1"] - r["x0"] < 12}.items())
res["IR_mm_h"] = {l: round((638.3 - top) / (638.3 - 543.3) * 3.5, 3) for l, (x, top) in zip(lab, bars)}
json.dump(res, open("digitised/gathala2017_figs.json", "w"), indent=1)
for k, v in res.items():
    print(k, v)
