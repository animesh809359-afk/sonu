"""Plot-wise disease index for all four assessment dates, with 4- and 3-class schemes.

Usage: python build_di_table.py <alldi.json> <output.xlsx>

alldi.json holds, per plot and date, the values of the Plot_DI sheets of the four scored ASD
workbooks (asd_scores_110226, _240226, _030326, _130326). Classes are live formulas on editable
limits in the Classes sheet.
"""
import json
import sys

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter as CL

SRC, OUT = sys.argv[1:3]
D = {int(k): v for k, v in json.load(open(SRC)).items()}
DATES = ["11/02/2026", "24/02/2026", "03/03/2026", "13/03/2026"]
DAI = {"11/02/2026": 6, "24/02/2026": 19, "03/03/2026": 26, "13/03/2026": 36}
NOTE = {"24/02/2026": "spectra 24/02, leaves scored 26/02"}

F = Font(name="Arial", size=10)
FB = Font(name="Arial", size=10, bold=True)
FW = Font(name="Arial", size=10, bold=True, color="FFFFFF")
FT = Font(name="Arial", size=12, bold=True, color="1F4D2B")
FIN = Font(name="Arial", size=10, color="0000FF")
HDR = PatternFill("solid", fgColor="1F4D2B")
SUB = PatternFill("solid", fgColor="D9E1DA")
YEL = PatternFill("solid", fgColor="FFFF00")
THIN = Side(style="thin", color="BFBFBF")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, horizontal="center", vertical="center")


def put(ws, r, c, v, font=F, fill=None, fmt=None, align=None):
    cell = ws.cell(row=r, column=c, value=v)
    cell.font, cell.border = font, BOX
    if fill:
        cell.fill = fill
    if fmt:
        cell.number_format = fmt
    if align:
        cell.alignment = align
    return cell


wb = openpyxl.Workbook()
rd = wb.active
rd.title = "README"
lines = [
    ("PLOT-WISE WHITE RUST DISEASE INDEX, ALL FOUR DATES - IARI 2025-26", FT),
    ("DI = sum(x f) / (9 x sum f) x 100 from the leaf scores of the scanned leaves (x = 0,1,3,5,7,9). Values come from the "
     "Plot_DI sheets of the four scored ASD workbooks.", F),
    ("Classes are numbered only (Class 0-3); limits are editable in the Classes sheet (yellow cells) and every class column, "
     "count and summary follows them.", F),
    ("", F),
    ("4-CLASS SCHEME: Class 0 = DI 0; Class 1 = 0 < DI <= 25; Class 2 = 25 < DI <= 50; Class 3 = DI > 50.", FB),
    ("3-CLASS SCHEME: Class 0 = DI 0; Class 1 = 0 < DI <= 50; Class 2 = DI > 50 (Classes 1 and 2 of the 4-class scheme merged).", FB),
    ("Why these limits: natural breaks (Jenks) of the 144 inoculated plot-dates fall at DI 23.7 and 49.6, close to the 25 and 50 "
     "limits of your DI table, and the four classes are well filled (51 / 36 / 50 / 55 plot-dates).", F),
    ("Class 0 holds the 48 healthy-control plot-dates and 3 inoculated plots that showed no symptoms on 11/02 (plots 20, 45, 46); "
     "the H/D column keeps them apart.", F),
    ("", F),
    ("SHEETS: DI_Wide (one row per plot, four dates side by side, AUDPC) | DI_Long (one row per plot-date, for joining to spectra) | "
     "Classes (limits) | Summary (counts by date, stage and treatment).", F),
]
for i, (t, f) in enumerate(lines, start=1):
    c = rd.cell(row=i, column=1, value=t)
    c.font = f
    c.alignment = Alignment(wrap_text=True, vertical="top")
rd.column_dimensions["A"].width = 150

# Classes (limits)
cs = wb.create_sheet("Classes")
cs.cell(row=1, column=1, value="Class limits (yellow = editable)").font = FT
for k, h in enumerate(["Scheme", "Class", "DI from (>)", "DI to (<=)", "Rule"], start=1):
    put(cs, 3, k, h, FW, HDR, align=WRAP)
C4 = [("4-class", "Class 0", None, 0, "DI = 0"), ("4-class", "Class 1", 0, 25, "0 < DI <= limit"),
      ("4-class", "Class 2", 25, 50, "limit 1 < DI <= limit 2"), ("4-class", "Class 3", 50, None, "DI > limit 2")]
C3 = [("3-class", "Class 0", None, 0, "DI = 0"), ("3-class", "Class 1", 0, 50, "0 < DI <= limit"),
      ("3-class", "Class 2", 50, None, "DI > limit")]
for i, row in enumerate(C4 + C3, start=4):
    for k, v in enumerate(row, start=1):
        put(cs, i, k, v)
# editable limits
cs.cell(row=4 + 1, column=4).fill = YEL
cs.cell(row=4 + 1, column=4).font = FIN
cs.cell(row=4 + 2, column=4).fill = YEL
cs.cell(row=4 + 2, column=4).font = FIN
cs.cell(row=4 + 2, column=3).value = "=D5"
cs.cell(row=4 + 3, column=3).value = "=D6"
cs.cell(row=9, column=4).fill = YEL
cs.cell(row=9, column=4).font = FIN
cs.cell(row=10, column=3).value = "=D9"
L4A, L4B, L3A = "Classes!$D$5", "Classes!$D$6", "Classes!$D$9"
for k, w in enumerate([10, 10, 12, 12, 26], start=1):
    cs.column_dimensions[CL(k)].width = w
cs.cell(row=12, column=1, value="Natural breaks (Jenks) of inoculated plot-dates: 2 groups -> 33.3; 3 groups -> 23.7 and 49.6.").font = F


def cls4(ref):
    return f'=IF({ref}="","",IF({ref}<=0,"Class 0",IF({ref}<={L4A},"Class 1",IF({ref}<={L4B},"Class 2","Class 3"))))'


def cls3(ref):
    return f'=IF({ref}="","",IF({ref}<=0,"Class 0",IF({ref}<={L3A},"Class 1","Class 2")))'


plots = sorted(D)
first = D[1][DATES[0]]

# DI_Wide
wd = wb.create_sheet("DI_Wide")
base = ["Plot", "Treatment", "Sowing", "Variety", "Replication", "Healthy/Diseased"]
per = ["Stage", "Leaves scored", "DI (%)", "Class (4)", "Class (3)"]
col = 1
for h in base:
    put(wd, 2, col, h, FW, HDR, align=WRAP)
    col += 1
DCOL = {}
for d in DATES:
    put(wd, 1, col, f"{d} ({DAI[d]} DAI)" + (f" - {NOTE[d]}" if d in NOTE else ""), FW, HDR, align=WRAP)
    wd.merge_cells(start_row=1, start_column=col, end_row=1, end_column=col + len(per) - 1)
    DCOL[d] = col
    for h in per:
        put(wd, 2, col, h, FB, SUB, align=WRAP)
        col += 1
EXTRA = ["Mean DI (4 dates)", "AUDPC (DI x days)"]
for h in EXTRA:
    put(wd, 2, col, h, FW, HDR, align=WRAP)
    col += 1
wd.row_dimensions[1].height = 30
wd.row_dimensions[2].height = 30
for i, p in enumerate(plots, start=3):
    v = D[p][DATES[0]]
    sow, var = v["t"][:2], v["t"][2:]
    for k, x in enumerate([p, v["t"], sow, var, v["rep"], v["hd"]], start=1):
        put(wd, i, k, x, FB if k <= 2 else F)
    for d in DATES:
        c0 = DCOL[d]
        e = D[p][d]
        put(wd, i, c0, e["stage"])
        put(wd, i, c0 + 1, e["n"])
        put(wd, i, c0 + 2, round(e["di"], 4), FB, fmt="0.0")
        di = f"{CL(c0 + 2)}{i}"
        put(wd, i, c0 + 3, cls4(di))
        put(wd, i, c0 + 4, cls3(di))
    dis = [f"{CL(DCOL[d] + 2)}{i}" for d in DATES]
    put(wd, i, col - 2, f"=AVERAGE({','.join(dis)})", fmt="0.0")
    # trapezoid AUDPC over 11/02-24/02 (13 d), 24/02-03/03 (7 d), 03/03-13/03 (10 d)
    put(wd, i, col - 1, f"=({dis[0]}+{dis[1]})/2*13+({dis[1]}+{dis[2]})/2*7+({dis[2]}+{dis[3]})/2*10", fmt="0")
widths = [6, 10, 8, 8, 11, 12] + [12, 8, 8, 9, 9] * 4 + [10, 11]
for k, w in enumerate(widths, start=1):
    wd.column_dimensions[CL(k)].width = w
wd.freeze_panes = "C3"

# DI_Long
lg = wb.create_sheet("DI_Long")
LH = ["Assessment date", "DAI", "Plot", "Treatment", "Sowing", "Variety", "Replication", "Healthy/Diseased", "Growth stage",
      "Leaves scored", "f(0)", "f(1)", "f(3)", "f(5)", "f(7)", "f(9)", "Sum (x f)", "Mean leaf score", "DI (%)", "Class (4)", "Class (3)"]
for k, h in enumerate(LH, start=1):
    put(lg, 1, k, h, FW, HDR, align=WRAP)
lg.row_dimensions[1].height = 30
r = 2
for d in DATES:
    for p in plots:
        e = D[p][d]
        vals = [d, DAI[d], p, e["t"], e["t"][:2], e["t"][2:], e["rep"], e["hd"], e["stage"], e["n"]] + e["f"] + \
               [e["sx"], round(e["mean"], 4), round(e["di"], 4)]
        for k, x in enumerate(vals, start=1):
            put(lg, r, k, x, FB if k == 19 else F, fmt={18: "0.00", 19: "0.0"}.get(k))
        put(lg, r, 20, cls4(f"S{r}"))
        put(lg, r, 21, cls3(f"S{r}"))
        r += 1
LAST = r - 1
for k, w in enumerate([12, 5, 6, 10, 8, 8, 11, 12, 13, 8] + [6] * 6 + [8, 9, 8, 9, 9], start=1):
    lg.column_dimensions[CL(k)].width = w
lg.freeze_panes = "D2"
lg.auto_filter.ref = f"A1:U{LAST}"

# Summary (formulas)
sm = wb.create_sheet("Summary")
sm.cell(row=1, column=1, value="Plot-dates per class (formulas on DI_Long)").font = FT
rng = lambda c: f"DI_Long!${c}$2:${c}${LAST}"


def table(r0, title, keys, keycol, classes, clscol):
    sm.cell(row=r0, column=1, value=title).font = FB
    put(sm, r0 + 1, 1, "Group", FW, HDR)
    for k, c in enumerate(classes, start=2):
        put(sm, r0 + 1, k, c, FW, HDR, align=WRAP)
    put(sm, r0 + 1, len(classes) + 2, "Total", FW, HDR)
    put(sm, r0 + 1, len(classes) + 3, "Mean DI (%)", FW, HDR, align=WRAP)
    for i, key in enumerate(keys, start=r0 + 2):
        put(sm, i, 1, key, FB)
        crit = f'"{key}"' if isinstance(key, str) else key
        for k, c in enumerate(classes, start=2):
            put(sm, i, k, f'=COUNTIFS({rng(keycol)},{crit},{rng(clscol)},"{c}")')
        put(sm, i, len(classes) + 2, f"=SUM(B{i}:{CL(len(classes) + 1)}{i})", FB)
        put(sm, i, len(classes) + 3, f"=AVERAGEIFS({rng('S')},{rng(keycol)},{crit})", fmt="0.0")
    i = r0 + 2 + len(keys)
    put(sm, i, 1, "All", FB)
    for k in range(2, len(classes) + 3):
        put(sm, i, k, f"=SUM({CL(k)}{r0 + 2}:{CL(k)}{i - 1})", FB)
    put(sm, i, len(classes) + 3, f"=AVERAGE({rng('S')})", fmt="0.0")
    return i + 2


C4N, C3N = ["Class 0", "Class 1", "Class 2", "Class 3"], ["Class 0", "Class 1", "Class 2"]
r0 = 3
r0 = table(r0, "4-class scheme by assessment date", DATES, "A", C4N, "T")
r0 = table(r0, "4-class scheme by growth stage", ["Vegetative", "Flowering", "Pod formation"], "I", C4N, "T")
r0 = table(r0, "4-class scheme, healthy control vs inoculated", ["Healthy", "Diseased"], "H", C4N, "T")
r0 = table(r0, "3-class scheme by assessment date", DATES, "A", C3N, "U")
r0 = table(r0, "3-class scheme by growth stage", ["Vegetative", "Flowering", "Pod formation"], "I", C3N, "U")
r0 = table(r0, "4-class scheme by treatment (inoculated and control together)",
           [f"D{a}V{b}" for a in range(1, 5) for b in range(1, 4)], "D", C4N, "T")
for k, w in enumerate([22, 10, 10, 10, 10, 8, 11], start=1):
    sm.column_dimensions[CL(k)].width = w

wb.move_sheet("DI_Wide", offset=1 - wb.sheetnames.index("DI_Wide"))
wb.save(OUT)
print("saved", OUT)
