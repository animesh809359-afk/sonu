"""Fill leaf level and disease score into the 13/03/2026 ASD workbook and add plot DI.

Usage: python fill_scores.py <asd_130326.xlsx> <scores_13_03_16.xlsx> <treatment_detail.xlsx> <output.xlsx>

Scores are matched to spectra by (plot, SR no.), where SR no. is the number in the spectrum
file name (MustardNNNNN). Existing leaf/score cells are kept and checked, never overwritten.
"""
import sys

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter as CL

ASD, SCORES, LAYOUT, OUT = sys.argv[1:5]
LEAF_ROW, SCORE_ROW = 6, 7
CLASSES = [(0, "Healthy"), (5, "Very low"), (10, "Low"), (25, "Moderate"), (50, "High"), (1e9, "Very high")]

# scores: diseased block A-G (plot, leaf, score, SR no), healthy block I-L (plot, leaf, SR no, score)
sws = openpyxl.load_workbook(SCORES, data_only=True).worksheets[0]
S, dp, hp = {}, None, None
for r in sws.iter_rows(min_row=4, values_only=True):
    if r[0] is not None:
        dp = r[0]
    if r[3] is not None and r[2] is not None:
        S[(dp, int(r[3]))] = (r[1], r[2])
    if isinstance(r[8], int):
        hp = r[8]
    if r[10] is not None and r[11] is not None:
        S[(hp, int(r[10]))] = (r[9], r[11])

lay = {r[0]: (r[1] + r[2], r[3]) for r in openpyxl.load_workbook(LAYOUT).active.iter_rows(min_row=2, values_only=True)}

wb = openpyxl.load_workbook(ASD)
ws = wb.worksheets[0]
ncol = ws.max_column
filled_leaf = filled_score = kept = 0
avg_cols = []          # (column index, plot, first spectrum column, last spectrum column)
block_start = None
for j in range(2, ncol + 1):
    name = ws.cell(row=1, column=j).value
    plot = ws.cell(row=2, column=j).value
    if isinstance(name, str) and name.endswith(".sco"):
        if block_start is None:
            block_start = j
        leaf, score = S[(plot, int(name[7:12]))]
        lc, sc = ws.cell(row=LEAF_ROW, column=j), ws.cell(row=SCORE_ROW, column=j)
        if lc.value is None:
            lc.value = leaf
            filled_leaf += 1
        elif lc.value != leaf:
            raise SystemExit(f"leaf mismatch {CL(j)}: {lc.value} vs {leaf}")
        if sc.value is None:
            sc.value = score
            filled_score += 1
        elif sc.value != score:
            raise SystemExit(f"score mismatch {CL(j)}: {sc.value} vs {score}")
        else:
            kept += 1
    else:
        if block_start is not None and isinstance(plot, int):
            avg_cols.append((j, plot, block_start, j - 1))
        block_start = None

# plot DI in each plot-average column: DI = sum(x) / (9 x n) x 100
BOLD = Font(bold=True)
for j, plot, a, b in avg_cols:
    rng = f"{CL(a)}{SCORE_ROW}:{CL(b)}{SCORE_ROW}"
    ws.cell(row=LEAF_ROW, column=j, value="Plot DI (%)").font = BOLD
    c = ws.cell(row=SCORE_ROW, column=j, value=f"=SUM({rng})/(9*COUNT({rng}))*100")
    c.font = BOLD
    c.number_format = "0.0"

# summary sheet (main table only: the first average column of each plot)
sm = wb.create_sheet("Plot_DI")
HDR = PatternFill("solid", fgColor="1F4D2B")
YEL = PatternFill("solid", fgColor="FFFF00")
THIN = Side(style="thin", color="BFBFBF")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
FW = Font(bold=True, color="FFFFFF")
CF = {"Healthy": "E2EFDA", "Very low": "F2F7E8", "Low": "FFF8E1", "Moderate": "FFE9C7", "High": "FCD5C0", "Very high": "F4B6B6"}
sm.cell(row=1, column=1, value="Plot disease index (DI) - white rust, 13/03/2026").font = Font(bold=True, size=12)
sm.cell(row=2, column=1, value="DI = sum(x x f) / (n x sum f) x 100, x = leaf rating (0,1,3,5,7,9), n = 9. "
        "Counts come from the score row of sheet 130326 for the plot's spectra (main table).")
cols = ["Plot", "Treatment", "Replication", "Variety", "Growth stage", "Healthy/Diseased", "Leaves scored",
        "f(0)", "f(1)", "f(3)", "f(5)", "f(7)", "f(9)", "Sum (x f)", "Mean leaf score", "Plot DI (%)", "Severity class"]
for k, h in enumerate(cols, start=1):
    c = sm.cell(row=4, column=k, value=h)
    c.font, c.fill, c.border = FW, HDR, BOX
    c.alignment = Alignment(wrap_text=True, horizontal="center", vertical="center")
sm.row_dimensions[4].height = 30
# class limits (editable)
sm.cell(row=4, column=19, value="Upper DI limit (%)").font = BOLD
sm.cell(row=4, column=20, value="Class").font = BOLD
for i, (lim, name) in enumerate(CLASSES[:-1], start=5):
    c = sm.cell(row=i, column=19, value=lim)
    c.fill, c.font = YEL, Font(color="0000FF")
    sm.cell(row=i, column=20, value=name)
sm.cell(row=10, column=20, value="Very high")
sm.cell(row=11, column=19, value="A plot takes the first class whose upper limit is >= its DI; edit the yellow limits to change the bands.")

seen, r = set(), 5
SH = "'130326'!"
for j, plot, a, b in sorted(avg_cols, key=lambda x: x[1]):
    if plot in seen:
        continue
    seen.add(plot)
    rng = f"{SH}${CL(a)}${SCORE_ROW}:${CL(b)}${SCORE_ROW}"
    treat, rep = lay[plot]
    vals = [plot, treat, "Control" if rep not in ("R1", "R2", "R3") else rep,
            f"={SH}{CL(j)}3", f"={SH}{CL(j)}4", f"={SH}{CL(j)}5", f"=COUNT({rng})"]
    vals += [f"=COUNTIF({rng},{g})" for g in (0, 1, 3, 5, 7, 9)]
    vals += [f"=SUMPRODUCT({{0,1,3,5,7,9}},H{r}:M{r})", f"=N{r}/G{r}", f"=N{r}/(9*G{r})*100",
             f'=IF(P{r}<=$S$5,$T$5,IF(P{r}<=$S$6,$T$6,IF(P{r}<=$S$7,$T$7,IF(P{r}<=$S$8,$T$8,IF(P{r}<=$S$9,$T$9,$T$10)))))']
    for k, v in enumerate(vals, start=1):
        c = sm.cell(row=r, column=k, value=v)
        c.border = BOX
        if k == 15:
            c.number_format = "0.00"
        if k == 16:
            c.number_format = "0.0"
            c.font = BOLD
    r += 1
for k, w in enumerate([6, 10, 11, 8, 13, 15, 8, 6, 6, 6, 6, 6, 6, 9, 10, 10, 13, 2, 16, 10], start=1):
    sm.column_dimensions[CL(k)].width = w
sm.freeze_panes = "A5"
wb.save(OUT)
print(f"filled leaf {filled_leaf}, filled score {filled_score}, existing scores kept {kept}, avg columns {len(avg_cols)}, plots {len(seen)}")
