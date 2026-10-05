"""Author decisions 2026-10-05 on batch 02 -> updated_03.
1 keep Yadav/Das CT-CTR (flagged) | 2 Dhaliwal red rows | 3 enzyme main effects | 4 Das aggregate water retention on BULK-SOIL basis
5 both MWD pre-treatments | 6 urease x60 and Ludhiana 50F+CR SOC kept as read."""
import sys
import openpyxl
p_in, p_out = sys.argv[1], sys.argv[2]
wb = openpyxl.load_workbook(p_in)
OLD = "FLAG: AGGREGATE-SCALE retention, not bulk-soil FC/PWP. "
NEW = ("BULK-SOIL BASIS (author decision 2026-10-05): the aggregate-core retention is entered as the bulk-soil value - gravimetric water content "
       "is the same per unit dry soil, and every volumetric conversion uses the bulk-soil BD (paper's initial 1.55 Mg/m3), not aggregate density. ")
n = 0
for sh in ("FC (weight basis)", "PWP (weight basis)", "AWC (weight basis)", "AWC (volume basis)"):
    ws = wb[sh]
    h = {c.value: c.column for c in ws[1]}
    for r in range(2, ws.max_row + 1):
        if ws.cell(r, 2).value != 166:
            continue
        c = ws.cell(r, h["Notes/Doubts"])
        c.value = "DECIDED 2026-10-05: bulk-soil basis. " + str(c.value).replace(OLD, NEW).replace(
            "AWCv = AWCw x 1.55 Mg/m3 (paper's initial BD; no treatment bulk density printed - aggregate densities in notes)",
            "AWCv = AWCw x bulk-soil BD 1.55 Mg/m3 (paper's initial BD; no treatment bulk density printed)")
        u = ws.cell(r, h["UNIT"])
        u.value = str(u.value).replace(" aggregates", " aggregates, bulk-soil basis").replace("initial BD 1.55", "bulk-soil BD 1.55")
        n += 1
print("Das soil-water rows updated:", n)

ws = wb["RULES"]
upd = {78: "IN FORCE (author confirmed 2026-10-05)", 80: "IN FORCE (author confirmed 2026-10-05)",
       81: "IN FORCE (author 2026-10-05: BULK-SOIL basis)", 82: "IN FORCE (author confirmed 2026-10-05)"}
for r in range(1, ws.max_row + 1):
    k = ws.cell(r, 1).value
    if k in upd:
        ws.cell(r, 6).value = upd[k]
        if k == 81:
            ws.cell(r, 3).value = ("Water retention measured on packed aggregates (pressure plate) is entered on the FC / PWP / AWC sheets on a BULK-SOIL basis: "
                                   "gravimetric values as printed, all volumetric conversions with the bulk-soil BD (not aggregate density).")
    if k == 79:
        ws.cell(r, 6).value = "IN FORCE (rule 36; author confirmed 2026-10-05)"
n0 = max(v for v in (ws.cell(i, 1).value for i in range(1, ws.max_row + 1)) if isinstance(v, int))
from copy import copy
style = [copy(c._style) for c in ws[ws.max_row]]
r = ws.max_row + 1
for j, v in enumerate((n0 + 1, "Parameter-specific", "Values read from figures that look odd (axis unit 'per min' on a 5-h assay; a treatment bar below the unfertilised control) are kept as read, converted to the sheet unit and flagged.",
                       "Dhaliwal 2020 urease (x 60 to per hour); Yadav 2000 Ludhiana 50F+CR SOC 1.51 g/kg.", "Author 2026-10-05", "IN FORCE"), 1):
    ws.cell(r, j, v)._style = copy(style[j - 1])

rd = wb["README"]
r = rd.max_row + 1
rd.cell(r, 1, "Decisions on batch 111-113 (2026-10-05)").font = openpyxl.styles.Font(name="Arial", size=10, bold=True)
c = rd.cell(r, 2, "updated 03: author confirmed rules 78-82 (INM straw treatments CT/CTR flagged; rice-season red rows; enzyme main effects; both MWD pre-treatments; "
                  "odd figure readings kept and flagged). Das 2014 aggregate water retention now on BULK-SOIL basis (rule 81). No data values changed.")
c.font = openpyxl.styles.Font(name="Arial", size=10)
c.alignment = openpyxl.styles.Alignment(wrap_text=True, vertical="top")
wb.calculation.fullCalcOnLoad = True
wb.save(p_out)
print("saved", p_out)
