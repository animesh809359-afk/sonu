"""Add parameter sheets LLWR, SOIL TEMP and AGG SIZE CLASS (author 2026-10-05: 'add a LLWR sheet'; all data points extracted).

Each new sheet is a copy of the SQI layout (same identity/site columns, code groups incl. pCA/pZT/pMT/pMTR, Obs/Rep/SD, notes and
method columns) with its own column prefix and unit note. AGG SIZE CLASS gets an extra 'Aggregate size class (mm)' column.
Usage: python batches/add_sheets_08.py <in.xlsx> <out.xlsx>
"""
import sys
from copy import copy
import openpyxl
from openpyxl.styles import Font

p_in, p_out = sys.argv[1], sys.argv[2]
wb = openpyxl.load_workbook(p_in)
NEW = [  # name, prefix, unit note, insert after
    ("LLWR", "LLWR_", "% v/v (least-limiting water range = water content between the limits set by air-filled porosity 10 %, field capacity, "
                      "penetration resistance (e.g. 1.75-2 MPa) and wilting point; state limits in Method column)", "AWC (volume basis)"),
    ("SOIL TEMP", "STEMP_", "deg C (soil temperature; state depth, time of day and averaging period in 'DEPTH (as reported in paper)' / "
                            "'Crop/season of sampling'; one row per reading date or week, rule 90)", "LLWR"),
    ("AGG SIZE CLASS", "AGGC_", "% of soil in each WATER-STABLE aggregate size class (one row per class; class in 'Aggregate size class (mm)'); "
                                "WSA / MACRO / MICRO / MWD sheets hold the summary indices", "MICRO"),
]
tmpl = wb["SQI"]
for name, pre, unit, after in NEW:
    ws = wb.copy_worksheet(tmpl)
    ws.title = name
    for r in range(ws.max_row, 1, -1):
        for c in range(1, ws.max_column + 1):
            ws.cell(r, c).value = None
    for c in ws[1]:
        if isinstance(c.value, str) and c.value.startswith("SQI_"):
            c.value = pre + c.value[4:]
    uc = [c.column for c in ws[1] if c.value == "UNIT FOR THIS SHEET:"][0]
    ws.cell(2, uc).value = unit
    ws.cell(2, uc).font = Font(name="Arial", size=10, bold=True)
    if name == "AGG SIZE CLASS":
        ws.insert_cols(16)
        src = ws.cell(1, 15)
        h = ws.cell(1, 16, "Aggregate size class (mm)")
        h._style = copy(src._style)
        ws.column_dimensions["P"].width = 16
    for r in range(2, ws.max_row + 1):  # drop copied conditional rows beyond header/unit
        pass
    idx = wb.sheetnames.index(after) + 1
    wb.move_sheet(ws, offset=idx - wb.sheetnames.index(name))
# index rows on STUDIES_BY_PARAMETER
sp = wb["STUDIES_BY_PARAMETER"]
last = sp.max_row
style = [copy(c._style) for c in sp[last]]
n = sp.cell(last, 1).value
for i, (name, pre, unit, after) in enumerate(NEW, 1):
    vals = [n + i, name, unit.split(" (")[0], 0, 0, "NO DATA"]
    for j, v in enumerate(vals, 1):
        sp.cell(last + i, j, v)._style = copy(style[j - 1])
wb.calculation.fullCalcOnLoad = True
wb.save(p_out)
print([s for s in wb.sheetnames if s in ("AWC (volume basis)", "LLWR", "SOIL TEMP", "MICRO", "AGG SIZE CLASS")],
      [wb.sheetnames.index(s) for s in ("AWC (volume basis)", "LLWR", "SOIL TEMP", "MICRO", "AGG SIZE CLASS")])
