"""Step-by-step Excel workbook of the four-tier analysis + RF comparison (reads results/results.pkl)."""
import pickle, sys
import numpy as np
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter as CL
from openpyxl.comments import Comment

OUT = sys.argv[1]
R = pickle.load(open("results/results.pkl", "rb"))
raw = pd.read_csv("endmembers.csv")
wl, X, y, SEL, data = R["wl"], R["X"], R["y"], R["SEL"], R["data"]
N, P = X.shape
nH, nD = int((y == "healthy").sum()), int((y == "diseased").sum())
assert all(y[:nH] == "healthy") and all(y[nH:] == "diseased"), "analysis data must be sorted healthy first"

FONT = "Arial"
F_IN = Font(name=FONT, size=10, color="0000FF")         # values from Python / data (inputs)
F_FX = Font(name=FONT, size=10, color="000000")         # formulas
F_LINK = Font(name=FONT, size=10, color="008000")       # links to other sheets
F_B = Font(name=FONT, size=10, bold=True)
F_H = Font(name=FONT, size=10, bold=True, color="FFFFFF")
F_T = Font(name=FONT, size=14, bold=True, color="1F3864")
F_S = Font(name=FONT, size=10, italic=True, color="404040")
FILL_H = PatternFill("solid", fgColor="1F4E5A")
FILL_K = PatternFill("solid", fgColor="FFF2CC")
FILL_G = PatternFill("solid", fgColor="E2EFDA")
thin = Side(style="thin", color="BFBFBF")
BOX = Border(left=thin, right=thin, top=thin, bottom=thin)

wb = Workbook()
wb.remove(wb.active)

def sheet(name, title, subtitle):
    ws = wb.create_sheet(name)
    ws["A1"] = title; ws["A1"].font = F_T
    ws["A2"] = subtitle; ws["A2"].font = F_S
    ws.sheet_view.showGridLines = False
    return ws

def put(ws, r, c, v, font=None, fmt=None, fill=None, bold=False, wrap=False, align=None):
    cell = ws.cell(r, c, v)
    if font is None:
        font = F_FX if isinstance(v, str) and v.startswith("=") and "!" not in v else (F_LINK if isinstance(v, str) and v.startswith("=") else F_IN)
        if isinstance(v, str) and not v.startswith("="):
            font = Font(name=FONT, size=10, bold=bold)
    cell.font = font
    if fmt: cell.number_format = fmt
    if fill: cell.fill = fill
    if wrap or align:
        cell.alignment = Alignment(wrap_text=wrap, horizontal=align, vertical="top")
    return cell

def header(ws, r, c, names, widths=None):
    for k, n in enumerate(names):
        cell = ws.cell(r, c + k, n); cell.font = F_H; cell.fill = FILL_H; cell.border = BOX
        cell.alignment = Alignment(wrap_text=True, horizontal="center", vertical="center")
    if widths:
        for k, w in enumerate(widths):
            ws.column_dimensions[CL(c + k)].width = w

def note(ws, r, c, text, width_cols=10):
    cell = ws.cell(r, c, text); cell.font = F_S
    cell.alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(start_row=r, start_column=c, end_row=r, end_column=c + width_cols - 1)
    ws.row_dimensions[r].height = max(15, 15 * (1 + len(text) // (11 * width_cols)))

def q(name): return f"'{name}'"

S_RAW, S_DQ, S_AD, S_T1, S_T2, S_T3, S_T4, S_RF, S_CMP, S_VAL, S_CHK = (
    "1_Raw_Data", "2_Data_Quality", "3_Analysis_Data", "4_Tier1_ANOVA", "5_Tier2_CART", "6_Tier3_JM",
    "7_Tier4_QDA", "8_RandomForest", "9_Comparison", "10_Validation", "11_Cross_Checks")

# ================================================================ README
ws = sheet("README", "Four-tier hierarchical analysis (Das et al. 2020) + Random Forest — healthy vs diseased SMACC endmembers",
           "Input: smacc_endmembers_healthy_diseased.csv (300 healthy + 300 diseased SMACC endmembers, 483 reflectance bands). Analysis on reflectance values only.")
ws.column_dimensions["A"].width = 6; ws.column_dimensions["B"].width = 22; ws.column_dimensions["C"].width = 110
header(ws, 4, 1, ["Step", "Sheet", "What it contains"])
steps = [
    ("0", S_RAW, "The input file exactly as received (600 spectra × 483 bands + class, SMACC order, pixel row/column, lon/lat)."),
    ("1", S_DQ, "Data-quality screening: vegetation rules per spectrum (NDVI, R800/R670, NDWI, R800), negative-reflectance counts, bands used. 3 non-vegetation spectra removed; noisy detector edges (<420 nm, >2350 nm) excluded."),
    ("2", S_AD, "The analysis data set: 597 spectra (298 healthy, 299 diseased) × 463 bands (420–2350 nm), sorted healthy first. All Excel formulas in later sheets read from here."),
    ("3", S_T1, "TIER 1 — one-way ANOVA at every band, computed with live Excel formulas (means, SDs, sums of squares, F, p = FDIST), plus Tukey HSD, Welch, Levene, FDR, Cohen's d and single-band JM; Python values alongside for cross-checking."),
    ("4", S_T2, "TIER 2 — CART (rpart settings: Gini, minsplit 20, minbucket 7, cp 0.01) on the ANOVA-significant bands: cp table, tree nodes, selected bands, importance."),
    ("5", S_T3, "TIER 3 — Jeffries–Matusita distance on the CART bands, rebuilt in Excel from COVAR / MINVERSE / MMULT / MDETERM; single-band and cumulative JM."),
    ("6", S_T4, "TIER 4 — Quadratic Discriminant Analysis with 10-fold cross-validation (as in the paper): fold accuracies, confusion matrix, OA / PA / UA / kappa as formulas, 10× repeated CV."),
    ("7", S_RF, "Random Forest comparison (500 trees, mtry = √p) on three band sets, same folds: confusion matrices, OOB accuracy, band importance."),
    ("8", S_CMP, "Side-by-side comparison of QDA and RF under every validation scheme."),
    ("9", S_VAL, "Validation cross-checks: nested CV (band selection inside folds), spatial-block CV, location-only control, permutation test, sensitivity analyses."),
    ("10", S_CHK, "All cross-checks (Python and live Excel) with PASS/FAIL."),
]
for i, (a, b, c) in enumerate(steps):
    r = 5 + i
    put(ws, r, 1, a); put(ws, r, 2, b, font=Font(name=FONT, size=10, bold=True)); put(ws, r, 3, c, wrap=True)
    ws.row_dimensions[r].height = 30
r = 5 + len(steps) + 1
put(ws, r, 1, "Colour code", font=F_B)
put(ws, r + 1, 2, "Blue text", font=F_IN); put(ws, r + 1, 3, "Values: input data, or results computed in Python (scipy / scikit-learn / statsmodels) where Excel has no equivalent (CART, QDA, RF, Tukey, Levene, FDR).")
put(ws, r + 2, 2, "Black text", font=F_FX); put(ws, r + 2, 3, "Live Excel formulas within the sheet.")
put(ws, r + 3, 2, "Green text", font=F_LINK); put(ws, r + 3, 3, "Live Excel formulas that link to another sheet.")
put(ws, r + 4, 2, "Yellow fill", fill=FILL_K); put(ws, r + 4, 3, "Key results.")
r += 6
put(ws, r, 1, "Software", font=F_B)
put(ws, r + 1, 3, "Python 3.13 · numpy · pandas · scipy 1.18 (ANOVA, t-tests, Levene) · statsmodels 0.15 (Tukey HSD, FDR) · scikit-learn 1.9 (CART, QDA, Random Forest, cross-validation). CART pruning re-implemented to match R rpart's cp (misclassification-based cost-complexity). Random seed 42 throughout.", wrap=True)
ws.row_dimensions[r + 1].height = 30
put(ws, r + 2, 3, "Reference: Das B, Sahoo RN, Biswas A, et al. (2020) Discrimination of rice genotypes using field spectroradiometry. Geocarto International 35(1):64–77.", wrap=True)

# ================================================================ 1 RAW
ws = sheet(S_RAW, "Step 0 — Input data (as received)", "smacc_endmembers_healthy_diseased.csv — one row per SMACC endmember; reflectance columns named by wavelength (nm).")
cols = list(raw.columns)
header(ws, 4, 1, cols)
for i, row in enumerate(raw.itertuples(index=False)):
    for j, v in enumerate(row):
        ws.cell(5 + i, 1 + j, v).font = F_IN
ws.freeze_panes = "G5"

# ================================================================ 2 DATA QUALITY
ws = sheet(S_DQ, "Step 1 — Data-quality screening", "Rules applied to every spectrum; a spectrum failing any REMOVE rule is excluded from the analysis. Index values computed from band means (Python).")
fl = R["flags"]
hdr = ["class", "endmember_no", "row_0based", "col_0based", "NDVI", "R800/R670", "NDWI", "R800", "Mean VIS", "Bands < 0", "Min reflectance", "Remove reason", "Kept"]
header(ws, 12, 1, hdr, [10, 11, 10, 10, 9, 10, 9, 9, 9, 9, 11, 26, 7])
for i, r_ in enumerate(fl.itertuples(index=False)):
    rr = 13 + i
    vals = [r_[0], r_[1], r_[2], r_[3], r_[4], r_[5], r_[6], r_[7], r_[8], int(r_[9]), r_[10], r_[11]]
    for j, v in enumerate(vals):
        c = put(ws, rr, 1 + j, v, font=F_IN, fmt="0.000" if 4 <= j <= 10 and j != 9 else None)
    put(ws, rr, 13, f'=IF(L{rr}="","yes","no")')
last = 12 + len(fl)
put(ws, 4, 1, "Rules (REMOVE): NDVI < 0.30; R800/R670 < 2; NDWI = (R560 − R860)/(R560 + R860) > 0; R800 < 0.10.", font=F_B)
header(ws, 6, 1, ["", "Healthy", "Diseased", "Total"])
put(ws, 7, 1, "Spectra in file", bold=True)
put(ws, 7, 2, f'=COUNTIF(A13:A{last},"healthy")'); put(ws, 7, 3, f'=COUNTIF(A13:A{last},"diseased")'); put(ws, 7, 4, "=B7+C7")
put(ws, 8, 1, "Removed (non-vegetation)", bold=True)
put(ws, 8, 2, f'=COUNTIFS(A13:A{last},"healthy",M13:M{last},"no")'); put(ws, 8, 3, f'=COUNTIFS(A13:A{last},"diseased",M13:M{last},"no")'); put(ws, 8, 4, "=B8+C8")
put(ws, 9, 1, "Kept for analysis", bold=True)
for c in "BCD":
    put(ws, 9, " BCD".index(c) + 1, f"={c}7-{c}8", fill=FILL_K)
put(ws, 10, 1, "Spectra with any negative reflectance", bold=True)
put(ws, 10, 2, f'=COUNTIFS(A13:A{last},"healthy",J13:J{last},">0")'); put(ws, 10, 3, f'=COUNTIFS(A13:A{last},"diseased",J13:J{last},">0")'); put(ws, 10, 4, "=B10+C10")
# negatives by band + band usage
nb = R["neg_by_band"]; bt = R["band_table"]
c0 = 16
header(ws, 12, c0, ["Wavelength (nm)", "Healthy spectra < 0", "Diseased spectra < 0", "Used in analysis"], [12, 12, 12, 24])
for i in range(len(nb)):
    put(ws, 13 + i, c0, float(nb.wavelength_nm[i]), font=F_IN, fmt="0.00")
    put(ws, 13 + i, c0 + 1, int(nb.neg_healthy[i]), font=F_IN); put(ws, 13 + i, c0 + 2, int(nb.neg_diseased[i]), font=F_IN)
    put(ws, 13 + i, c0 + 3, bt.used[i], font=F_IN)
put(ws, 4, c0, "Bands in file", bold=True); put(ws, 4, c0 + 2, f"=COUNTA({CL(c0)}13:{CL(c0)}{12+len(nb)})")
put(ws, 5, c0, "Bands used (420–2350 nm)", bold=True); put(ws, 5, c0 + 2, f'=COUNTIF({CL(c0+3)}13:{CL(c0+3)}{12+len(nb)},"yes")', fill=FILL_K)
put(ws, 6, c0, "Bands excluded (noisy edges)", bold=True); put(ws, 6, c0 + 2, f"={CL(c0+2)}4-{CL(c0+2)}5")
note(ws, 8, c0, "Negative reflectance is physically impossible. It is concentrated in SWIR-2 (1970–2350 nm) and in the diseased class; see the SWIR-2-excluded sensitivity analysis in sheet 10_Validation.", 4)
ws.freeze_panes = "A13"

# ================================================================ 3 ANALYSIS DATA
ws = sheet(S_AD, "Step 2 — Analysis data set", f"{N} spectra ({nH} healthy in rows 5–{4+nH}, {nD} diseased in rows {5+nH}–{4+N}) × {P} bands (420–2350 nm). Later formulas read these ranges.")
meta = ["class", "endmember_no", "row_0based", "col_0based"]
header(ws, 4, 1, meta + [f"{w:.2f}" for w in wl])
for i in range(N):
    put(ws, 5 + i, 1, y[i], font=F_IN); put(ws, 5 + i, 2, int(data.endmember_no[i]), font=F_IN)
    put(ws, 5 + i, 3, int(data.row_0based[i]), font=F_IN); put(ws, 5 + i, 4, int(data.col_0based[i]), font=F_IN)
    for j in range(P):
        ws.cell(5 + i, 5 + j, float(X[i, j])).font = F_IN
ws.freeze_panes = "E5"
H0, H1, D0, D1 = 5, 4 + nH, 5 + nH, 4 + N
def col_of_band(j): return CL(5 + j)
def rngH(j): return f"{q(S_AD)}!{col_of_band(j)}${H0}:{col_of_band(j)}${H1}"
def rngD(j): return f"{q(S_AD)}!{col_of_band(j)}${D0}:{col_of_band(j)}${D1}"
def rngA(j): return f"{q(S_AD)}!{col_of_band(j)}${H0}:{col_of_band(j)}${D1}"

# ================================================================ 4 TIER 1
ws = sheet(S_T1, "Tier 1 — One-way ANOVA at every band (healthy vs diseased)",
           "H0: μ_healthy(λ) = μ_diseased(λ). Columns C–Q are live Excel formulas on sheet 3_Analysis_Data; R–Z are Python results for cross-checking.")
t1 = R["tier1"]
hdr = ["Band #", "Wavelength (nm)", "n healthy", "n diseased", "Mean healthy", "Mean diseased", "SD healthy", "SD diseased",
       "SS between", "SS within", "df between", "df within", "F", "p (ANOVA)", "Significant (p<0.05)", "Cohen's d (D−H)",
       "Bhattacharyya B (1 band)", "JM (0–2, 1 band)",
       "Tukey HSD p (Python)", "Welch t p (Python)", "Levene p (Python)", "FDR q, BH (Python)", "Bonferroni p (Python)",
       "F (Python scipy)", "|F Excel − F Python| / F", "p (Python scipy)", "|p Excel − p Python|"]
TR0 = 12
header(ws, TR0, 1, hdr, [7, 11, 8, 8, 10, 10, 10, 10, 11, 11, 7, 7, 10, 11, 10, 10, 11, 10, 11, 11, 11, 11, 11, 10, 12, 11, 12])
for j in range(P):
    r = TR0 + 1 + j
    put(ws, r, 1, j + 1, font=F_IN); put(ws, r, 2, float(wl[j]), font=F_IN, fmt="0.00")
    put(ws, r, 3, f"=COUNT({rngH(j)})"); put(ws, r, 4, f"=COUNT({rngD(j)})")
    put(ws, r, 5, f"=AVERAGE({rngH(j)})", fmt="0.00000"); put(ws, r, 6, f"=AVERAGE({rngD(j)})", fmt="0.00000")
    put(ws, r, 7, f"=STDEV({rngH(j)})", fmt="0.00000"); put(ws, r, 8, f"=STDEV({rngD(j)})", fmt="0.00000")
    put(ws, r, 10, f"=DEVSQ({rngH(j)})+DEVSQ({rngD(j)})", fmt="0.000000")
    put(ws, r, 9, f"=DEVSQ({rngA(j)})-J{r}", fmt="0.000000")
    put(ws, r, 11, 1, font=F_IN); put(ws, r, 12, f"=C{r}+D{r}-2")
    put(ws, r, 13, f"=(I{r}/K{r})/(J{r}/L{r})", fmt="0.000")
    put(ws, r, 14, f"=FDIST(M{r},K{r},L{r})", fmt="0.00E+00")
    put(ws, r, 15, f'=IF(N{r}<0.05,"yes","no")')
    put(ws, r, 16, f"=(F{r}-E{r})/SQRT(((C{r}-1)*G{r}^2+(D{r}-1)*H{r}^2)/L{r})", fmt="0.000")
    put(ws, r, 17, f"=(F{r}-E{r})^2/(4*(G{r}^2+H{r}^2))+0.5*LN((G{r}^2+H{r}^2)/(2*G{r}*H{r}))", fmt="0.0000")
    put(ws, r, 18, f"=2*(1-EXP(-Q{r}))", fmt="0.0000")
    put(ws, r, 19, float(t1.Tukey_HSD_p[j]), font=F_IN, fmt="0.00E+00")
    put(ws, r, 20, float(t1.Welch_t_p[j]), font=F_IN, fmt="0.00E+00")
    put(ws, r, 21, float(t1.Levene_p[j]), font=F_IN, fmt="0.00E+00")
    put(ws, r, 22, float(t1.FDR_q_BH[j]), font=F_IN, fmt="0.00E+00")
    put(ws, r, 23, float(t1.Bonferroni_p[j]), font=F_IN, fmt="0.00E+00")
    put(ws, r, 24, float(t1.F[j]), font=F_IN, fmt="0.000")
    put(ws, r, 25, f"=ABS(M{r}-X{r})/X{r}", fmt="0.0E+00")
    put(ws, r, 26, float(t1.p_ANOVA[j]), font=F_IN, fmt="0.00E+00")
    put(ws, r, 27, f"=ABS(N{r}-Z{r})", fmt="0.0E+00")
TL = TR0 + P
ws.freeze_panes = f"C{TR0+1}"
# summary
put(ws, 4, 1, "Summary", font=F_B)
put(ws, 5, 1, "Bands tested"); put(ws, 5, 4, f"=COUNT(B{TR0+1}:B{TL})")
put(ws, 6, 1, "Significant at p < 0.05 (paper criterion)"); put(ws, 6, 4, f'=COUNTIF(O{TR0+1}:O{TL},"yes")', fill=FILL_K)
put(ws, 7, 1, "Significant after FDR (q < 0.05)"); put(ws, 7, 4, f'=COUNTIF(V{TR0+1}:V{TL},"<0.05")')
put(ws, 8, 1, "Significant after Bonferroni (p < 0.05)"); put(ws, 8, 4, f'=COUNTIF(W{TR0+1}:W{TL},"<0.05")')
put(ws, 9, 1, "Bands with |Cohen's d| ≥ 0.8 (large effect)"); put(ws, 9, 4, f'=COUNTIF(P{TR0+1}:P{TL},">=0.8")+COUNTIF(P{TR0+1}:P{TL},"<=-0.8")')
put(ws, 10, 1, "Max F (band)"); put(ws, 10, 4, f"=MAX(M{TR0+1}:M{TL})", fmt="0.0")
put(ws, 10, 5, f"=INDEX(B{TR0+1}:B{TL},MATCH(D10,M{TR0+1}:M{TL},0))", fmt="0.0 \"nm\"")
# region table
put(ws, 4, 7, "By spectral region", font=F_B)
header(ws, 5, 7, ["Region", "From (nm)", "To (nm)", "Bands", "Significant p<0.05", "Significant FDR", "Max F"])
regions = [("VIS", 420, 700), ("Red-edge", 700, 750), ("NIR", 750, 1330), ("SWIR-1", 1460, 1780), ("SWIR-2", 1970, 2350.1)]
for i, (nm, lo, hi) in enumerate(regions):
    r = 6 + i
    put(ws, r, 7, nm); put(ws, r, 8, lo, font=F_IN); put(ws, r, 9, hi, font=F_IN)
    B_ = f"$B${TR0+1}:$B${TL}"
    put(ws, r, 10, f'=COUNTIFS({B_},">="&H{r},{B_},"<"&I{r})')
    put(ws, r, 11, f'=COUNTIFS({B_},">="&H{r},{B_},"<"&I{r},$O${TR0+1}:$O${TL},"yes")')
    put(ws, r, 12, f'=COUNTIFS({B_},">="&H{r},{B_},"<"&I{r},$V${TR0+1}:$V${TL},"<0.05")')
    put(ws, r, 13, f'=SUMPRODUCT(MAX(({B_}>=H{r})*({B_}<I{r})*$M${TR0+1}:$M${TL}))', fmt="0.0")
put(ws, 11, 7, "Total"); put(ws, 11, 10, "=SUM(J6:J10)"); put(ws, 11, 11, "=SUM(K6:K10)"); put(ws, 11, 12, "=SUM(L6:L10)")
note(ws, 4, 15, "With two classes there is only one pair, so Tukey HSD gives the same decision as the ANOVA (column S); the paper's 'number of significant genotype pairs per band' becomes 0 or 1. FDR and Bonferroni are shown because 463 tests are made.", 9)

# ================================================================ 5 TIER 2
ws = sheet(S_T2, "Tier 2 — Classification and Regression Tree (CART) for band reduction",
           "Input: the ANOVA-significant bands (sheet 4). Settings as R rpart defaults used by Das et al.: Gini split, minsplit 20, minbucket 7, cp 0.01, 10-fold CV.")
cs = R["cart_summary"]
put(ws, 4, 1, "Settings and summary", font=F_B)
rows = [("Input bands (ANOVA p < 0.05)", f"={q(S_T1)}!D6"), ("Splitting rule", "Gini index"), ("minsplit / minbucket", "20 / 7"),
        ("Complexity parameter used (cp)", 0.01), ("Splits in cp = 0.01 tree", cs["nsplitA"]),
        ("Bands used in the tree (selected)", len(cs["bandsA"])),
        ("Resubstitution accuracy of the tree", cs["train_acc_A"]), ("10-fold CV accuracy of the tree as a classifier", cs["cv_acc_cart_A"]),
        ("1-SE rule cp (for comparison)", cs["cp_1se"]), ("Splits / bands in 1-SE tree", f"{cs['nsplitB']} / {len(cs['bandsB'])}")]
for i, (a, b) in enumerate(rows):
    put(ws, 5 + i, 1, a); c = put(ws, 5 + i, 4, b, fmt="0.0%" if "accuracy" in a else ("0.0000" if "cp" in a.lower() and isinstance(b, float) else None))
ws["D10"].fill = FILL_K
ws.column_dimensions["A"].width = 14; ws.column_dimensions["B"].width = 14; ws.column_dimensions["C"].width = 14; ws.column_dimensions["D"].width = 16
# cp table
put(ws, 17, 1, "Complexity table (rpart printcp equivalent; errors relative to the root node error)", font=F_B)
cpt = R["cp_table"]
header(ws, 18, 1, ["CP", "nsplit", "rel error", "xerror", "xstd"])
for i, r_ in enumerate(cpt.itertuples(index=False)):
    for j, v in enumerate(r_):
        put(ws, 19 + i, 1 + j, float(v) if j != 1 else int(v), font=F_IN, fmt="0.0000" if j != 1 else None)
# selected bands + importance
imp = R["treeA_importance"]
c0 = 7
put(ws, 4, c0, "Bands selected by CART (cp = 0.01 tree), by importance", font=F_B)
header(ws, 5, c0, ["Rank", "Wavelength (nm)", "Region", "Gini decrease", "Importance (%)"], [7, 13, 11, 13, 13])
def region_of(w):
    for nm, lo, hi in regions:
        if lo <= w < hi: return nm
    return ""
for i, r_ in enumerate(imp.itertuples(index=False)):
    rr = 6 + i
    put(ws, rr, c0, i + 1, font=F_IN); put(ws, rr, c0 + 1, float(r_.wavelength_nm), font=F_IN, fmt="0.0")
    put(ws, rr, c0 + 2, region_of(float(r_.wavelength_nm))); put(ws, rr, c0 + 3, float(r_.gini_decrease), font=F_IN, fmt="0.000")
    put(ws, rr, c0 + 4, f"={CL(c0+3)}{rr}/SUM(${CL(c0+3)}$6:${CL(c0+3)}${5+len(imp)})", fmt="0.0%")
# node table
nd = R["treeA_nodes"]
r0 = max(19 + len(cpt), 7 + len(imp)) + 2
put(ws, r0, 1, "Tree structure (cp = 0.01 tree, depth-first; left branch = condition true)", font=F_B)
cols_nd = ["node_id", "depth", "rule_from_parent", "type", "split", "n", "n_healthy", "n_diseased", "predicted", "purity_pct"]
header(ws, r0 + 1, 1, ["Node", "Depth", "From parent", "Type", "Split rule", "n", "n healthy", "n diseased", "Predicted class", "Purity (%)"])
for i, r_ in enumerate(nd[cols_nd].itertuples(index=False)):
    for j, v in enumerate(r_):
        put(ws, r0 + 2 + i, 1 + j, v if not isinstance(v, (np.integer, np.floating)) else float(v) if isinstance(v, np.floating) else int(v), font=F_IN)
ws.column_dimensions["E"].width = 26

# ================================================================ 6 TIER 3
ws = sheet(S_T3, "Tier 3 — Jeffries–Matusita (J–M) distance on the CART bands",
           "B = (1/8)(μD−μH)ᵀ[(CH+CD)/2]⁻¹(μD−μH) + ½ ln(|(CH+CD)/2| / √(|CH||CD|));   JM = 2(1 − e^(−B)) on a 0–2 scale (threshold 1.94, Das et al.); √JM form ranges 0–1.414.")
k = len(SEL)
sel_sorted = sorted(SEL)
put(ws, 4, 1, "Selected bands", font=F_B)
header(ws, 5, 1, ["#", "Wavelength (nm)", "Mean healthy", "Mean diseased", "d = μD − μH"], [6, 13, 13, 13, 13])
for i, j in enumerate(sel_sorted):
    r = 6 + i; tr = TR0 + 1 + j
    put(ws, r, 1, i + 1, font=F_IN); put(ws, r, 2, f"={q(S_T1)}!B{tr}", fmt="0.0")
    put(ws, r, 3, f"={q(S_T1)}!E{tr}", fmt="0.00000"); put(ws, r, 4, f"={q(S_T1)}!F{tr}", fmt="0.00000")
    put(ws, r, 5, f"=D{r}-C{r}", fmt="0.00000")
dcol0, dcol1 = 6, 5 + k
# row vector of d
put(ws, 4, 8, "d as a row vector", font=F_B)
for i in range(k):
    put(ws, 5, 8 + i, f"=INDEX($E${dcol0}:$E${dcol1},{i+1})", fmt="0.00000")
drow = f"$H$5:${CL(7+k)}$5"
def cov_block(r0, title, rH, label):
    put(ws, r0, 1, title, font=F_B)
    for i in range(k):
        put(ws, r0 + 1, 2 + i, f"=B{6+i}", fmt="0.0"); put(ws, r0 + 2 + i, 1, f"=B{6+i}", fmt="0.0")
    for a in range(k):
        for b in range(k):
            ja, jb = sel_sorted[a], sel_sorted[b]
            if rH == "H":
                f = f"=COVAR({rngH(ja)},{rngH(jb)})*{nH}/{nH-1}"
            else:
                f = f"=COVAR({rngD(ja)},{rngD(jb)})*{nD}/{nD-1}"
            put(ws, r0 + 2 + a, 2 + b, f, fmt="0.00E+00")
    return f"${CL(2)}${r0+2}:${CL(1+k)}${r0+1+k}"
rH0 = 8 + k
CHr = cov_block(rH0, "Covariance matrix — healthy (COVAR × n/(n−1))", "H", "H")
rD0 = rH0 + k + 3
CDr = cov_block(rD0, "Covariance matrix — diseased", "D", "D")
rM0 = rD0 + k + 3
put(ws, rM0, 1, "Average covariance (CH + CD)/2", font=F_B)
for a in range(k):
    for b in range(k):
        put(ws, rM0 + 2 + a, 2 + b, f"=({CL(2+b)}{rH0+2+a}+{CL(2+b)}{rD0+2+a})/2", fmt="0.00E+00")
CMr = f"$B${rM0+2}:${CL(1+k)}${rM0+1+k}"
rR = rM0 + k + 3
jm = R["tier3"]
put(ws, rR, 1, "Result", font=F_B)
header(ws, rR + 1, 1, ["Quantity", "", "Excel (live)", "Python", "|difference|"])
res = [("Mahalanobis term (1/8)dᵀC⁻¹d", f"=SUMPRODUCT(MMULT({drow},MINVERSE({CMr})),{drow})/8", jm["mahalanobis_term"]),
       ("Covariance term ½ln(|C|/√(|CH||CD|))", f"=0.5*LN(MDETERM({CMr})/SQRT(MDETERM({CHr})*MDETERM({CDr})))", jm["covariance_term"]),
       ("Bhattacharyya distance B", f"=C{rR+2}+C{rR+3}", jm["B"]),
       ("JM distance (0–2 scale)", f"=2*(1-EXP(-C{rR+4}))", jm["JM_0to2"]),
       ("JM distance (√ form, 0–1.414)", f"=SQRT(C{rR+5})", jm["JM_sqrt"])]
for i, (a, f, v) in enumerate(res):
    r = rR + 2 + i
    put(ws, r, 1, a); put(ws, r, 3, f, fmt="0.0000"); put(ws, r, 4, float(v), font=F_IN, fmt="0.0000"); put(ws, r, 5, f"=ABS(C{r}-D{r})", fmt="0.0E+00")
ws.cell(rR + 5, 3).fill = FILL_K
put(ws, rR + 8, 1, "Threshold (0–2 scale, Das et al.)"); put(ws, rR + 8, 3, 1.94, font=F_IN)
put(ws, rR + 9, 1, "Classes separable at this threshold?"); put(ws, rR + 9, 3, f'=IF(C{rR+5}>=C{rR+8},"yes","no")', fill=FILL_K)
note(ws, rR + 11, 1, f"Why only the CART bands: with all {jm['n_sig']} significant bands the class covariance matrix has rank {jm['cov_rank_all_sig']} < {jm['n_sig']} (only {jm['n_per_class']} spectra per class), so it cannot be inverted and J–M cannot be computed — the same reason given by Das et al.", 9)
# cumulative + per band JM
jc = R["jm_cumulative"]
c0 = 9 + k
put(ws, rH0, c0, "Cumulative JM (bands added in CART importance order)", font=F_B)
header(ws, rH0 + 1, c0, ["Bands", "Band added (nm)", "JM (0–2)", "√JM"], [8, 13, 10, 10])
for i, r_ in enumerate(jc.itertuples(index=False)):
    rr = rH0 + 2 + i
    put(ws, rr, c0, int(r_.n_bands), font=F_IN); put(ws, rr, c0 + 1, float(r_.added_band_nm), font=F_IN, fmt="0.0")
    put(ws, rr, c0 + 2, float(r_.JM_0to2), font=F_IN, fmt="0.0000"); put(ws, rr, c0 + 3, float(r_.JM_sqrt_form), font=F_IN, fmt="0.0000")
put(ws, rD0 + 2, c0, "Single-band JM: column R of sheet 4 (live formula).", font=F_S)
put(ws, rD0 + 3, c0, "Highest single-band JM"); put(ws, rD0 + 3, c0 + 2, f"=MAX({q(S_T1)}!R{TR0+1}:R{TL})", fmt="0.0000")
put(ws, rD0 + 4, c0, "at wavelength (nm)"); put(ws, rD0 + 4, c0 + 2, f"=INDEX({q(S_T1)}!B{TR0+1}:B{TL},MATCH({CL(c0+2)}{rD0+3},{q(S_T1)}!R{TR0+1}:R{TL},0))", fmt="0.0")

# ================================================================ confusion-matrix block helper
def cm_block(ws, r0, c0, title, cm, note_txt=None):
    """2x2 confusion matrix with formula metrics. Returns dict of metric cell refs (sheet-qualified)."""
    put(ws, r0, c0, title, font=F_B)
    header(ws, r0 + 1, c0, ["Reference \\ Predicted", "Healthy", "Diseased", "Total", "Producer's acc."])
    labels = ["Healthy", "Diseased"]
    for i in range(2):
        r = r0 + 2 + i
        put(ws, r, c0, labels[i], bold=True)
        put(ws, r, c0 + 1, int(cm[i, 0]), font=F_IN); put(ws, r, c0 + 2, int(cm[i, 1]), font=F_IN)
        put(ws, r, c0 + 3, f"=SUM({CL(c0+1)}{r}:{CL(c0+2)}{r})")
        put(ws, r, c0 + 4, f"={CL(c0+1+i)}{r}/{CL(c0+3)}{r}", fmt="0.0%")
    rt = r0 + 4
    put(ws, rt, c0, "Total", bold=True)
    for j in range(3):
        put(ws, rt, c0 + 1 + j, f"=SUM({CL(c0+1+j)}{r0+2}:{CL(c0+1+j)}{r0+3})")
    put(ws, rt + 1, c0, "User's acc.", bold=True)
    for j in range(2):
        put(ws, rt + 1, c0 + 1 + j, f"={CL(c0+1+j)}{r0+2+j}/{CL(c0+1+j)}{rt}", fmt="0.0%")
    a, b, c, d, n = (f"{CL(c0+1)}{r0+2}", f"{CL(c0+2)}{r0+2}", f"{CL(c0+1)}{r0+3}", f"{CL(c0+2)}{r0+3}", f"{CL(c0+3)}{rt}")
    m = rt + 2
    put(ws, m, c0, "Overall accuracy", bold=True); put(ws, m, c0 + 1, f"=({a}+{d})/{n}", fmt="0.00%", fill=FILL_K)
    put(ws, m + 1, c0, "Kappa", bold=True)
    put(ws, m + 1, c0 + 1, f"=(({a}+{d})/{n}-(({a}+{b})*({a}+{c})+({c}+{d})*({b}+{d}))/{n}^2)/(1-(({a}+{b})*({a}+{c})+({c}+{d})*({b}+{d}))/{n}^2)", fmt="0.000")
    put(ws, m + 2, c0, "Balanced accuracy", bold=True); put(ws, m + 2, c0 + 1, f"=({CL(c0+4)}{r0+2}+{CL(c0+4)}{r0+3})/2", fmt="0.00%")
    if note_txt:
        put(ws, m + 3, c0, note_txt, font=F_S)
    return dict(OA=f"{q(ws.title)}!{CL(c0+1)}{m}", kappa=f"{q(ws.title)}!{CL(c0+1)}{m+1}", BA=f"{q(ws.title)}!{CL(c0+1)}{m+2}",
                PA_H=f"{q(ws.title)}!{CL(c0+4)}{r0+2}", PA_D=f"{q(ws.title)}!{CL(c0+4)}{r0+3}",
                UA_H=f"{q(ws.title)}!{CL(c0+1)}{rt+1}", UA_D=f"{q(ws.title)}!{CL(c0+2)}{rt+1}", N=f"{q(ws.title)}!{n}")

REF = {}
# ================================================================ 7 TIER 4 QDA
ws = sheet(S_T4, "Tier 4 — Quadratic Discriminant Analysis (QDA), 10-fold cross-validation",
           "As in Das et al.: CART bands → QDA, 10-fold CV, confusion matrix, overall / producer's / user's accuracy. Equal priors; stratified folds; seed 42.")
for c, w in zip("ABCDEFGHIJ", [24, 12, 12, 10, 16, 4, 10, 14, 4, 12]):
    ws.column_dimensions[c].width = w
qd = R["qda"]
put(ws, 4, 1, "Input bands (nm):", bold=True)
put(ws, 4, 2, ", ".join(f"{wl[b]:.1f}" for b in sorted(SEL)), font=F_IN)
REF["qda_paper"] = cm_block(ws, 6, 1, "Confusion matrix — out-of-fold predictions, 10-fold CV (repetition 1)", qd["metrics"]["cm"])
put(ws, 6, 7, "Accuracy per fold (rep. 1)", font=F_B)
header(ws, 7, 7, ["Fold", "Accuracy"])
for i, a in enumerate(qd["fold_acc_rep1"]):
    put(ws, 8 + i, 7, i + 1, font=F_IN); put(ws, 8 + i, 8, float(a), font=F_IN, fmt="0.0%")
put(ws, 18, 7, "Mean", bold=True); put(ws, 18, 8, "=AVERAGE(H8:H17)", fmt="0.0%")
put(ws, 19, 7, "SD", bold=True); put(ws, 19, 8, "=STDEV(H8:H17)", fmt="0.0%")
put(ws, 6, 10, "10 × repeated 10-fold CV", font=F_B)
header(ws, 7, 10, ["Repetition", "OA"])
ws.column_dimensions["K"].width = 10
for i, a in enumerate(qd["rep_acc"]):
    put(ws, 8 + i, 10, i + 1, font=F_IN); put(ws, 8 + i, 11, float(a), font=F_IN, fmt="0.00%")
put(ws, 18, 10, "Mean", bold=True); put(ws, 18, 11, "=AVERAGE(K8:K17)", fmt="0.00%", fill=FILL_K)
put(ws, 19, 10, "SD", bold=True); put(ws, 19, 11, "=STDEV(K8:K17)", fmt="0.00%")
REF["qda_rep_mean"] = f"{q(S_T4)}!K18"; REF["qda_rep_sd"] = f"{q(S_T4)}!K19"
put(ws, 17, 1, "Python check: OA (sklearn accuracy_score)", bold=True); put(ws, 17, 2, float(qd["metrics"]["OA"]), font=F_IN, fmt="0.00%")
put(ws, 18, 1, "Python check: kappa (sklearn)", bold=True); put(ws, 18, 2, float(qd["metrics"]["kappa"]), font=F_IN, fmt="0.000")
note(ws, 21, 1, "These folds are random over pixels and the bands were selected on all data before CV — this reproduces the paper's procedure. Sheet 10_Validation repeats the analysis with band selection inside the folds (nested) and with spatial blocks, which give the realistic accuracy.", 11)

# ================================================================ 8 RANDOM FOREST
ws = sheet(S_RF, "Random Forest comparison — same 10 folds as QDA",
           "RandomForestClassifier: 500 trees, mtry = √(number of bands), Gini, bootstrap; seed 42. OOB = out-of-bag accuracy of a forest fitted to all data.")
for c, w in zip("ABCDEFGHIJKLMNOPQR", [24, 11, 11, 9, 15, 3, 24, 11, 11, 9, 15, 3, 24, 11, 11, 9, 15, 3]):
    ws.column_dimensions[c].width = w
rfr = R["rf"]
for i, (name, v) in enumerate(rfr.items()):
    c0 = 1 + 6 * i
    put(ws, 4, c0, name, font=F_B); put(ws, 5, c0, "Bands"); put(ws, 5, c0 + 1, v["n_bands"], font=F_IN)
    put(ws, 6, c0, "OOB accuracy"); put(ws, 6, c0 + 1, float(v["oob"]), font=F_IN, fmt="0.00%")
    REF[f"rf_{i}"] = cm_block(ws, 8, c0, "10-fold CV confusion matrix", v["metrics"]["cm"])
    REF[f"rf_{i}_oob"] = f"{q(S_RF)}!{CL(c0+1)}6"
imp = R["rf_importance"].sort_values("MDI_importance", ascending=False).reset_index(drop=True)
put(ws, 20, 1, "Band importance (forest on all 463 bands) — top 30", font=F_B)
header(ws, 21, 1, ["Rank", "Wavelength (nm)", "Region", "Mean decrease Gini", "Selected by CART?"])
selset = {round(float(wl[b]), 2) for b in SEL}
for i, r_ in enumerate(imp.head(30).itertuples(index=False)):
    rr = 22 + i
    put(ws, rr, 1, i + 1, font=F_IN); put(ws, rr, 2, float(r_.wavelength_nm), font=F_IN, fmt="0.0")
    put(ws, rr, 3, region_of(float(r_.wavelength_nm))); put(ws, rr, 4, float(r_.MDI_importance), font=F_IN, fmt="0.0000")
    put(ws, rr, 5, "yes" if round(float(r_.wavelength_nm), 2) in selset else "")
put(ws, 20, 7, "Importance summed by region (all 463 bands)", font=F_B)
header(ws, 21, 7, ["Region", "Bands", "Total importance", "Share"])
imp_all = R["rf_importance"]
for i, (nm, lo, hi) in enumerate(regions):
    m = (imp_all.wavelength_nm >= lo) & (imp_all.wavelength_nm < hi)
    rr = 22 + i
    put(ws, rr, 7, nm); put(ws, rr, 8, int(m.sum()), font=F_IN); put(ws, rr, 9, float(imp_all.MDI_importance[m].sum()), font=F_IN, fmt="0.000")
    put(ws, rr, 10, f"=I{rr}/SUM($I$22:$I$26)", fmt="0.0%")

# ================================================================ 10 VALIDATION
ws = sheet(S_VAL, "Validation cross-checks",
           "(a) nested CV: ANOVA + CART repeated inside each training fold; (b) spatial-block CV: 5 spatial blocks per class from k-means on pixel position, nested; (c) location-only control; (d) permutation test; (e) sensitivity.")
for c, w in zip("ABCDEFGHIJKLMNOPQR", [24, 11, 11, 9, 15, 3, 24, 11, 11, 9, 15, 3, 24, 11, 11, 9, 15, 3]):
    ws.column_dimensions[c].width = w
nest, spat = R["nested"], R["spatial"]
put(ws, 4, 1, "(a) Nested random 10-fold CV (band selection inside each training fold)", font=F_B)
REF["n_qda"] = cm_block(ws, 5, 1, "QDA on fold-selected CART bands", nest["qda"]["cm"])
REF["n_rf"] = cm_block(ws, 5, 7, "RF on fold-selected CART bands", nest["rf_sel"]["cm"])
REF["n_rfall"] = cm_block(ws, 5, 13, "RF on all 463 bands", nest["rf_all"]["cm"])
put(ws, 17, 1, "Bands selected per fold:"); put(ws, 17, 2, ", ".join(str(v) for v in nest["n_bands_per_fold"]), font=F_IN)
put(ws, 18, 1, "Most frequently selected bands (nm : folds)");
put(ws, 18, 2, "; ".join(f"{k}: {v}" for k, v in nest["band_frequency"].head(12).items()), font=F_IN)
put(ws, 20, 1, "(b) Spatial-block CV (nested; each fold = one healthy block + one diseased block)", font=F_B)
REF["s_qda"] = cm_block(ws, 21, 1, "QDA on fold-selected CART bands", spat["qda"]["cm"])
REF["s_rf"] = cm_block(ws, 21, 7, "RF on fold-selected CART bands", spat["rf_sel"]["cm"])
REF["s_rfall"] = cm_block(ws, 21, 13, "RF on all 463 bands", spat["rf_all"]["cm"])
header(ws, 33, 1, ["Spatial fold", "Test spectra", "QDA", "RF (sel.)", "RF (all)", "", "Bands selected in fold (nm)"])
for i, f in enumerate(spat["per_fold"]):
    rr = 34 + i
    put(ws, rr, 1, f["fold"], font=F_IN); put(ws, rr, 2, f["n_test"], font=F_IN)
    put(ws, rr, 3, f["qda"], font=F_IN, fmt="0.0%"); put(ws, rr, 4, f["rf_sel"], font=F_IN, fmt="0.0%"); put(ws, rr, 5, f["rf_all"], font=F_IN, fmt="0.0%")
    put(ws, rr, 7, f["bands"], font=F_IN)
put(ws, 39, 1, "Mean of folds", bold=True)
for c in "CDE":
    put(ws, 39, "ABCDE".index(c) + 1, f"=AVERAGE({c}34:{c}38)", fmt="0.0%")
lc = R["location_control"]
put(ws, 41, 1, "(c) Location-only control: can two halves of the SAME class be told apart?", font=F_B)
header(ws, 42, 1, ["Control", "n", "QDA paper-style", "QDA nested", "", "", "Bands selected (nm)"])
for i, r_ in enumerate(lc.itertuples(index=False)):
    rr = 43 + i
    put(ws, rr, 1, r_.control); put(ws, rr, 2, r_.n, font=F_IN); put(ws, rr, 3, float(r_.paper_style_QDA_OA), font=F_IN, fmt="0.0%")
    put(ws, rr, 4, float(r_.nested_QDA_OA), font=F_IN, fmt="0.0%"); put(ws, rr, 7, r_.bands, font=F_IN)
note(ws, 45, 1, "If halves of one class separate about as well as healthy vs diseased, the classifier is largely learning position (illumination, soil, view angle) rather than disease.", 12)
pm = R["permutation"]
put(ws, 47, 1, "(d) Permutation test — nested QDA pipeline with shuffled class labels", font=F_B)
put(ws, 48, 1, "Permutations"); put(ws, 48, 2, f"=COUNT(M49:M{48+pm['n']})")
put(ws, 49, 1, "Observed nested QDA accuracy"); put(ws, 49, 2, f"={REF['n_qda']['OA'].split('!')[1]}", fmt="0.00%")
put(ws, 50, 1, "Null mean"); put(ws, 50, 2, f"=AVERAGE(M49:M{48+pm['n']})", fmt="0.00%")
put(ws, 51, 1, "Null maximum"); put(ws, 51, 2, f"=MAX(M49:M{48+pm['n']})", fmt="0.00%")
put(ws, 52, 1, "p-value = (1 + #null ≥ observed)/(n + 1)"); put(ws, 52, 2, f'=(1+COUNTIF(M49:M{48+pm["n"]},">="&B49))/(B48+1)', fmt="0.0000", fill=FILL_K)
header(ws, 48, 13, ["Null accuracies"])
for i, a in enumerate(pm["acc"]):
    put(ws, 49 + i, 13, float(a), font=F_IN, fmt="0.00%")
sens = R["sensitivity"]
put(ws, 54, 1, "(e) Sensitivity analyses (paper-style pipeline: ANOVA → CART → JM → QDA 10-fold; RF on all bands)", font=F_B)
header(ws, 55, 1, ["Case", "Significant bands", "CART bands", "JM (0–2)", "QDA OA", "RF OA (all bands)", "Bands selected (nm)"])
for i, r_ in enumerate(sens.itertuples(index=False)):
    rr = 56 + i
    put(ws, rr, 1, r_.case); put(ws, rr, 2, int(r_.n_sig), font=F_IN); put(ws, rr, 3, int(r_.n_sel), font=F_IN)
    put(ws, rr, 4, float(r_.JM), font=F_IN, fmt="0.000"); put(ws, rr, 5, float(r_.QDA_OA), font=F_IN, fmt="0.0%")
    put(ws, rr, 6, float(r_.RF_all_OA), font=F_IN, fmt="0.0%"); put(ws, rr, 7, r_.bands, font=F_IN)
ws.column_dimensions["A"].width = 40

# ================================================================ 9 COMPARISON (links)
ws = sheet(S_CMP, "Comparison — QDA (four-tier) vs Random Forest",
           "Every number links to the sheet where it is computed (green). Paper-style = bands chosen on all data, random 10-fold CV.")
for c, w in zip("ABCDEFGHIJ", [30, 30, 14, 12, 12, 12, 12, 12, 12, 12]):
    ws.column_dimensions[c].width = w
header(ws, 4, 1, ["Classifier / bands", "Validation", "Overall acc.", "Kappa", "Balanced acc.", "PA healthy", "PA diseased", "UA healthy", "UA diseased"])
rows = [("QDA — CART bands (four-tier)", "Paper-style 10-fold", REF["qda_paper"]),
        ("RF — CART bands", "Paper-style 10-fold", REF["rf_0"]),
        ("RF — all ANOVA-significant bands", "Paper-style 10-fold", REF["rf_1"]),
        ("RF — all 463 bands", "Paper-style 10-fold", REF["rf_2"]),
        ("QDA — CART bands (four-tier)", "Nested 10-fold", REF["n_qda"]),
        ("RF — CART bands", "Nested 10-fold", REF["n_rf"]),
        ("RF — all 463 bands", "Nested 10-fold", REF["n_rfall"]),
        ("QDA — CART bands (four-tier)", "Spatial-block (nested)", REF["s_qda"]),
        ("RF — CART bands", "Spatial-block (nested)", REF["s_rf"]),
        ("RF — all 463 bands", "Spatial-block (nested)", REF["s_rfall"])]
for i, (a, b, ref) in enumerate(rows):
    r = 5 + i
    put(ws, r, 1, a); put(ws, r, 2, b)
    for j, kk in enumerate(["OA", "kappa", "BA", "PA_H", "PA_D", "UA_H", "UA_D"]):
        put(ws, r, 3 + j, f"={ref[kk]}", fmt="0.000" if kk == "kappa" else "0.0%")
put(ws, 16, 1, "QDA 10 × repeated CV: mean (col C), SD (col D)", bold=True)
put(ws, 16, 3, f"={REF['qda_rep_mean']}", fmt="0.00%"); put(ws, 16, 4, f"={REF['qda_rep_sd']}", fmt="0.00%")
put(ws, 17, 1, "RF out-of-bag accuracy (CART / significant / all bands)", bold=True)
for j in range(3):
    put(ws, 17, 3 + j, f"={REF[f'rf_{j}_oob']}", fmt="0.0%")
put(ws, 18, 1, "JM distance, CART bands (0–2)", bold=True); put(ws, 18, 3, f"={q(S_T3)}!C{rR+5}", fmt="0.000")

# ================================================================ 11 CROSS CHECKS
ws = sheet(S_CHK, "Cross-checks of every step", "Part A: checks run in Python during the analysis. Part B: live Excel checks comparing workbook formulas with the Python results.")
for c, w in zip("ABCDE", [14, 62, 30, 44, 9]):
    ws.column_dimensions[c].width = w
header(ws, 4, 1, ["Step", "Check", "Expected", "Obtained", "Result"])
ck = R["checks"]
for i, r_ in enumerate(ck.itertuples(index=False)):
    rr = 5 + i
    put(ws, rr, 1, r_.step); put(ws, rr, 2, r_.check, wrap=True); put(ws, rr, 3, r_.expected, font=F_IN); put(ws, rr, 4, r_.obtained, font=F_IN, wrap=True)
    put(ws, rr, 5, r_.result, font=Font(name=FONT, size=10, bold=True, color="008000" if r_.result == "PASS" else "C00000"))
rb = 5 + len(ck) + 2
put(ws, rb, 1, "Part B — live Excel checks", font=F_B)
header(ws, rb + 1, 1, ["Step", "Check", "Value", "Tolerance", "Result"])
live = [("Tier 1", "Max relative |F(Excel) − F(Python)| over all bands", f"=MAX({q(S_T1)}!Y{TR0+1}:Y{TL})", 1e-6),
        ("Tier 1", "Max |p(Excel FDIST) − p(Python)| over all bands", f"=MAX({q(S_T1)}!AA{TR0+1}:AA{TL})", 1e-6),
        ("Tier 1", "Significant-band count: Excel minus Python", f"=ABS({q(S_T1)}!D6-{int(R['sig'].sum())})", 0.5),
        ("Tier 3", "|JM(Excel matrix formulas) − JM(Python)|", f"={q(S_T3)}!E{rR+5}", 1e-6),
        ("Tier 3", "|Bhattacharyya B (Excel) − B (Python)|", f"={q(S_T3)}!E{rR+4}", 1e-6),
        ("Tier 4", "|QDA OA (Excel formula) − OA (Python)|", f"=ABS({REF['qda_paper']['OA']}-{q(S_T4)}!B17)", 1e-9),
        ("Tier 4", "|QDA kappa (Excel formula) − kappa (Python)|", f"=ABS({REF['qda_paper']['kappa']}-{q(S_T4)}!B18)", 1e-9),
        ("Tier 4", "Confusion-matrix total − analysis spectra", f"=ABS({REF['qda_paper']['N']}-{N})", 0.5),
        ("RF", "|RF OA (Excel, all bands) − OA (Python)|", f"=ABS({REF['rf_2']['OA']}-{float(R['rf']['All 463 bands']['metrics']['OA'])})", 1e-9),
        ("Data", "Kept spectra (sheet 2) − rows in analysis data", f"=ABS({q(S_DQ)}!D9-{N})", 0.5)]
for i, (a, b, f, tol) in enumerate(live):
    rr = rb + 2 + i
    put(ws, rr, 1, a); put(ws, rr, 2, b); put(ws, rr, 3, f, fmt="0.0E+00"); put(ws, rr, 4, tol, font=F_IN, fmt="0.0E+00")
    put(ws, rr, 5, f'=IF(C{rr}<=D{rr},"PASS","FAIL")', font=Font(name=FONT, size=10, bold=True))
put(ws, rb + 3 + len(live), 1, "All checks", font=F_B)
put(ws, rb + 3 + len(live), 5, f'=IF(AND(COUNTIF(E5:E{4+len(ck)},"FAIL")=0,COUNTIF(E{rb+2}:E{rb+1+len(live)},"FAIL")=0),"ALL PASS","CHECK")', fill=FILL_K,
    font=Font(name=FONT, size=10, bold=True))

order = ["README", S_RAW, S_DQ, S_AD, S_T1, S_T2, S_T3, S_T4, S_RF, S_CMP, S_VAL, S_CHK]
wb._sheets = [wb[n] for n in order]
wb.save(OUT)
print("saved", OUT)
