"""Append the batch-02 decision log to RULES (status PENDING CONFIRMATION)."""
import sys
from copy import copy
import openpyxl
p = sys.argv[1]
wb = openpyxl.load_workbook(p)
ws = wb["RULES"]
style = [copy(c._style) for c in ws[ws.max_row]]
n0 = max(v for v in (ws.cell(i, 1).value for i in range(1, ws.max_row + 1)) if isinstance(v, int))
rows = [
    ("Treatment codes", "INM papers with a crop-residue treatment: 100% NPK (CT) vs reduced NPK + straw substituting the cut N (CTR), FLAGGED under rule 62.",
     "Applied to Yadav 2000 (164: 100F vs 50F+CR, 50% NPK + wheat straw to rice only) and Das 2014 (166: T2 vs T8, 25% N via straw to both crops). FYM / press mud / green manure / unfertilised tiers excluded.", "Default 2026-10-05", "PENDING CONFIRMATION"),
    ("Seasons, years & rows", "Soil sampled only after rice harvest -> rice-season fallback, whole rows red (rule 36).", "Dhaliwal 2020 (168): all soil rows red.", "Default 2026-10-05", "IN FORCE (rule 36)"),
    ("Parameter-specific", "Enzymes printed only as tillage and residue MAIN effects (no cell means): tillage main effect entered as _CT vs _ZT (each pooled over +/- residue), flagged; residue main effect kept in Notes.",
     "Dhaliwal 2020 (168) DHA, urease, ALP, ACP (Figs 1-2).", "Default 2026-10-05 (rule 33)", "PENDING CONFIRMATION"),
    ("Parameter-specific", "Aggregate-scale water retention (pressure plate on packed aggregates) entered on FC / PWP / AWC sheets, flagged AGGREGATE-SCALE; AWCv uses the paper's initial BD.",
     "Das 2014 (166) Table 3, 2-5 mm and 5-8 mm aggregates (separate rows).", "Default 2026-10-05 (rule 9)", "PENDING CONFIRMATION"),
    ("Parameter-specific", "Two MWD pre-treatments (slaked and capillary-rewetted) both entered on MWD 1 as separate rows, flagged by pre-treatment.",
     "Das 2014 (166) Fig. 2a/2b.", "Default 2026-10-05", "PENDING CONFIRMATION"),
    ("Seasons, years & rows", "Year-wise yields digitised from multi-site trend figures; where a treatment's panel plots fewer seasons, seasons are paired by matching the series and checked against the printed site means.",
     "Yadav 2000 (164) Fig. 2: Faizabad wheat (12 CR seasons), Jabalpur wheat (12 seasons, one of 1988-89/1989-90 unlabelled), Sabour (one unlabelled season 1993-96).", "Default 2026-10-05 (rule 37)", "IN FORCE"),
]
r = ws.max_row + 1
for k, (cat, rule, det, src, st) in enumerate(rows):
    for j, v in enumerate((n0 + 1 + k, cat, rule, det, src, st), 1):
        ws.cell(r + k, j, v)._style = copy(style[j - 1])
wb.calculation.fullCalcOnLoad = True
wb.save(p)
print("rules", n0 + 1, "-", n0 + len(rows))
