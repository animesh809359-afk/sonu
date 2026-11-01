"""Fill leaf level and disease score into the 11/02/2026 ASD workbook and add plot DI.

Usage: python fill_scores.py <asd_110226.xlsx> <11_02_26.xlsx> <treatment_detail.xlsx> <output.xlsx>

The score sheet (header SPR in A1) lists one row per spectrum in scan order (sample no. 1-428 =
spectrum MustardNNNNN). Columns are found by their header names. Sample numbers carry a "(S)" marker on leaves taken for lab assays; the row order is
used as the sample number, and every printed number is checked against it.
"""
import re
import sys

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter as CL

ASD, SCORES, LAYOUT, OUT = sys.argv[1:5]
LEAF_ROW, SCORE_ROW = 6, 7

sws = next(s for s in openpyxl.load_workbook(SCORES, data_only=True).worksheets if s["A1"].value == "SPR")
hdr = [str(c.value or "").upper() for c in sws[1]]
C_PLOT, C_LEAF = hdr.index("PLOT_NO"), hdr.index("LEAVES")
C_SAMPLE = next(k for k, h in enumerate(hdr) if h.startswith("SAMPLE"))
C_SCORE = next(k for k, h in enumerate(hdr) if "SCORE" in h)
S, plot, typos = {}, None, []
for i, r in enumerate(sws.iter_rows(min_row=2, values_only=True), start=1):
    if r[C_LEAF] is None:     # extra rows after the leaf scans (flowers, pods, stagheads)
        break
    if r[C_PLOT] is not None:
        plot = r[C_PLOT]
    printed = int(re.sub(r"\D", "", str(r[C_SAMPLE])))
    if printed != i:
        typos.append((i, r[C_SAMPLE]))
    if r[C_SCORE] is None:
        raise SystemExit(f"missing score for sample {i}")
    S[i] = (plot, r[C_LEAF], r[C_SCORE])

lay = {r[0]: (r[1] + r[2], r[3]) for r in openpyxl.load_workbook(LAYOUT).active.iter_rows(min_row=2, values_only=True)}

wb = openpyxl.load_workbook(ASD)
ws = wb.worksheets[0]
filled_leaf = filled_score = 0
avg_cols, block_start = [], None
for j in range(2, ws.max_column + 1):
    name = ws.cell(row=1, column=j).value
    pl = ws.cell(row=2, column=j).value
    if name is None:          # unnamed copies of spectra (plot 27 on 11/02): neither spectrum nor average
        continue
    if isinstance(name, str) and name.endswith(".sco"):
        if block_start is None:
            block_start = j
        sp, leaf, score = S[int(name[7:12])]
        if sp != pl:
            raise SystemExit(f"plot mismatch {CL(j)}: {pl} vs {sp}")
        for row, val in ((LEAF_ROW, leaf), (SCORE_ROW, score)):
            c = ws.cell(row=row, column=j)
            if c.value is None:
                c.value = val
                filled_leaf += row == LEAF_ROW
                filled_score += row == SCORE_ROW
            elif c.value != val:
                raise SystemExit(f"mismatch {CL(j)}{row}: {c.value} vs {val}")
    else:
        if block_start is not None and isinstance(pl, int):
            avg_cols.append((j, pl, block_start, j - 1))
        block_start = None

BOLD = Font(bold=True)
for j, pl, a, b in avg_cols:
    rng = f"{CL(a)}{SCORE_ROW}:{CL(b)}{SCORE_ROW}"
    ws.cell(row=LEAF_ROW, column=j, value="Plot DI (%)").font = BOLD
    c = ws.cell(row=SCORE_ROW, column=j, value=f"=SUM({rng})/(9*COUNT({rng}))*100")
    c.font, c.number_format = BOLD, "0.0"

sm = wb.create_sheet("Plot_DI")
HDR = PatternFill("solid", fgColor="1F4D2B")
THIN = Side(style="thin", color="BFBFBF")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
sm.cell(row=1, column=1, value="Plot disease index (DI) - white rust, 11/02/2026").font = Font(bold=True, size=12)
sm.cell(row=2, column=1, value="DI = sum(x x f) / (n x sum f) x 100, x = leaf rating (0,1,3,5,7,9), n = 9. "
        f"Counts come from the score row of sheet {ws.title} for the plot's spectra.")
cols = ["Plot", "Treatment", "Replication", "Variety", "Growth stage", "Healthy/Diseased", "Leaves scored",
        "f(0)", "f(1)", "f(3)", "f(5)", "f(7)", "f(9)", "Sum (x f)", "Mean leaf score", "Plot DI (%)"]
for k, h in enumerate(cols, start=1):
    c = sm.cell(row=4, column=k, value=h)
    c.font, c.fill, c.border = Font(bold=True, color="FFFFFF"), HDR, BOX
    c.alignment = Alignment(wrap_text=True, horizontal="center", vertical="center")
sm.row_dimensions[4].height = 30
SH = f"'{ws.title}'!"
for r, (j, pl, a, b) in enumerate(sorted(avg_cols, key=lambda x: x[1]), start=5):
    rng = f"{SH}${CL(a)}${SCORE_ROW}:${CL(b)}${SCORE_ROW}"
    treat, rep = lay[pl]
    vals = [pl, treat, "Control" if rep not in ("R1", "R2", "R3") else rep,
            f"={SH}{CL(j)}3", f"={SH}{CL(j)}4", f"={SH}{CL(j)}5", f"=COUNT({rng})"]
    vals += [f"=COUNTIF({rng},{g})" for g in (0, 1, 3, 5, 7, 9)]
    vals += [f"=SUMPRODUCT({{0,1,3,5,7,9}},H{r}:M{r})", f"=N{r}/G{r}", f"=N{r}/(9*G{r})*100"]
    for k, v in enumerate(vals, start=1):
        c = sm.cell(row=r, column=k, value=v)
        c.border = BOX
        if k == 15:
            c.number_format = "0.00"
        if k == 16:
            c.number_format, c.font = "0.0", BOLD
for k, w in enumerate([6, 10, 11, 8, 13, 15, 8, 6, 6, 6, 6, 6, 6, 9, 10, 10], start=1):
    sm.column_dimensions[CL(k)].width = w
sm.freeze_panes = "A5"
wb.save(OUT)
print(f"filled leaf {filled_leaf}, filled score {filled_score}, avg columns {len(avg_cols)}, sample-no typos {typos}")
