"""QA of the subset workbooks: formula errors after LibreOffice recalculation, sheets, images,
missing figures, and the PASS / FLAG / FAIL counts of the cross-check sheet."""
from __future__ import annotations

import glob
import sys
from pathlib import Path

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[1]
OUT = (ROOT / ".." / "deliverables" / "WhiteRust_Subsets").resolve()
ERRS = ("#REF!", "#DIV/0!", "#VALUE!", "#NAME?", "#N/A", "#NUM!", "#NULL!")
rows = []
for p in sorted(glob.glob(str(OUT / "*.xlsx"))):
    wb = load_workbook(p, data_only=True)
    nerr, nimg, empty_formula = 0, 0, 0
    for ws in wb.worksheets:
        nimg += len(ws._images)
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, str) and c.value.strip() in ERRS:
                    nerr += 1
    wbf = load_workbook(p)
    nform = sum(1 for ws in wbf.worksheets for row in ws.iter_rows() for c in row
                if isinstance(c.value, str) and c.value.startswith("="))
    ws = wb["33_CrossChecks"]
    st = [r[5] for r in ws.iter_rows(values_only=True) if r and len(r) > 5 and r[5] in ("PASS", "FLAG", "FAIL")]
    rows.append((Path(p).name, len(wb.sheetnames), nimg, nform, nerr, st.count("PASS"), st.count("FLAG"), st.count("FAIL")))
print(f"{'workbook':70s} sheets images formulas errors PASS FLAG FAIL")
for r in rows:
    print(f"{r[0]:70s} {r[1]:6d} {r[2]:6d} {r[3]:8d} {r[4]:6d} {r[5]:4d} {r[6]:4d} {r[7]:4d}")
sys.exit(1 if any(r[4] or r[7] for r in rows) else 0)
