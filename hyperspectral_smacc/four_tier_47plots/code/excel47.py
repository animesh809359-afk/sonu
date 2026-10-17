"""Step-by-step workbook for the 47-plot four-tier analysis (reads results/r47.pkl).  Usage: python excel47.py OUT.xlsx"""
import os, pickle, sys
import numpy as np, pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter as CL
from refs47 import REFS
from abbrev47 import ABBR

OUT = sys.argv[1]
R = pickle.load(open(os.environ.get("R47", "results/r47.pkl"), "rb"))
meta, wl, X, y, groups, V, full, td = R["meta"], R["wl"], R["X"], R["y"], R["groups"], R["V"], R["full"], R["design"]
PH, PD = R["PH"], R["PD"]
N, P = X.shape; nH, nD = int((y == 0).sum()), int((y == 1).sum())
assert all(y[:nH] == 0) and all(y[nH:] == 1)
T2 = ("CART", "RF"); CVK = ("CV1", "CV2", "CV3", "CV4", "CV5", "CV6")
CVN = {"CV1": "Das et al. (2020): random 10-fold CV of QDA (×10)", "CV2": "Plot-grouped nested 4-fold CV (×10) — main", "CV3": "Leave-one-plot-out (47 folds)",
       "CV4": "Leave-one-treatment-combination-out (12 folds)", "CV5": "Leave-one-variety-out (3 folds)", "CV6": "Leave-one-inoculation-date-out (4 folds)"}
def Vt(t2, k): return V[(t2, "S0")][k]
FONT = "Arial"
F_IN, F_FX, F_LINK = Font(name=FONT, size=10, color="0000FF"), Font(name=FONT, size=10, color="000000"), Font(name=FONT, size=10, color="008000")
F_B, F_H, F_T, F_S = Font(name=FONT, size=10, bold=True), Font(name=FONT, size=10, bold=True, color="FFFFFF"), Font(name=FONT, size=14, bold=True, color="1F3864"), Font(name=FONT, size=10, italic=True, color="404040")
FILL_H, FILL_K = PatternFill("solid", fgColor="1F4E5A"), PatternFill("solid", fgColor="FFF2CC")
thin = Side(style="thin", color="BFBFBF"); BOX = Border(left=thin, right=thin, top=thin, bottom=thin)
wb = Workbook(); wb.remove(wb.active)
def q(n): return f"'{n}'"
def sheet(name, title, sub, why=None):
    ws = wb.create_sheet(name); ws["A1"] = title; ws["A1"].font = F_T; ws["A2"] = sub; ws["A2"].font = F_S; ws.sheet_view.showGridLines = False
    if why: ws["A3"] = "Why: " + why; ws["A3"].font = Font(name=FONT, size=10, italic=True, color="7F3F00")
    return ws
def put(ws, r, c, v, font=None, fmt=None, fill=None, bold=False, wrap=False):
    cell = ws.cell(r, c, v)
    if font is None:
        if isinstance(v, str) and v.startswith("="): font = F_LINK if "!" in v else F_FX
        elif isinstance(v, str): font = Font(name=FONT, size=10, bold=bold)
        else: font = F_IN
    cell.font = font
    if fmt: cell.number_format = fmt
    if fill: cell.fill = fill
    if wrap: cell.alignment = Alignment(wrap_text=True, vertical="top")
    return cell
def header(ws, r, c, names, widths=None):
    for k, n in enumerate(names):
        cell = ws.cell(r, c + k, n); cell.font = F_H; cell.fill = FILL_H; cell.border = BOX
        cell.alignment = Alignment(wrap_text=True, horizontal="center", vertical="center")
    if widths:
        for k, w in enumerate(widths): ws.column_dimensions[CL(c + k)].width = w
def note(ws, r, c, text, ncols=10):
    cell = ws.cell(r, c, text); cell.font = F_S; cell.alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells(start_row=r, start_column=c, end_row=r, end_column=c + ncols - 1); ws.row_dimensions[r].height = max(15, 15 * (1 + len(text) // (11 * ncols)))
def region(w): return "VIS" if w < 700 else "Red-edge" if w < 750 else "NIR" if w < 1350 else "SWIR-1" if w < 1800 else "SWIR-2"
LIVE = []          # (step, description, formula returning a deviation, tolerance)

S = dict(raw="1_Data", summ="2_Data_Summary", des="3_Design", t1="4_Tier1_ANOVA", cart="5_Tier2_CART", rf="6_Tier2_RF", jm="7_Tier3_JM",
         cv1="8_Tier4_CV1_Das", cv2="9_CV2_PlotGrouped", cv3="10_CV3_LOPO", cvd="11_CV4-6_Design", nc="12_Negative_Control",
         acc="13_Accuracy", perm="14_Permutation", sens="15_Sensitivity", cmp="16_Comparison", refs="17_References", chk="18_Cross_Checks")

# ============================================================ README
ws = sheet("README", "Four-tier analysis (Das et al. 2020) of SMACC endmembers from 47 plots — CART vs Random Forest in Tier 2",
           f"{N} endmember spectra kept separately (healthy plots 1–3, 5–12: {nH} = 11 × 98; diseased plots 13–48: {nD} = 36 × 30) × {P} reflectance bands (399–2398 nm). Plot 4 is excluded.")
ws.column_dimensions["A"].width = 6; ws.column_dimensions["B"].width = 24; ws.column_dimensions["C"].width = 95; ws.column_dimensions["D"].width = 70
header(ws, 4, 1, ["Step", "Sheet", "What is done", "Why it is done"])
rows = [("–", "Abbreviations", "Every abbreviation used in the workbook and the slides.", "So that every table can be read without the slides."),
        ("0", S["raw"], "All endmember spectra as supplied (one row each), healthy first. Every live formula reads from here.", "Reflectance values only, no transformation, as requested."),
        ("1", S["summ"], "Spectra per plot and class (COUNTIF), class balance, out-of-range reflectance.", "Check the input before any statistics."),
        ("2", S["des"], "Treatment design: control block C and inoculated blocks R3, R2, R1; 3 varieties × 4 inoculation dates.", "Plots are the experimental units; the layout decides how validation must be done (Hurlbert 1984)."),
        ("3", S["t1"], "TIER 1: one-way ANOVA at every band (live formulas), Tukey HSD, Welch, Levene, FDR, Bonferroni, Cohen's d, single-band J–M, ANOVA on plot means.", "Keeps only bands whose class means differ (Das et al. 2020); the extra tests show how robust that band list is."),
        ("4", S["cart"], "TIER 2: CART (rpart settings) on the ANOVA-significant bands; tree, bands and their single-band J–M.", "CART picks a small set of complementary bands (Das et al. 2020; Breiman et al. 1984)."),
        ("5", S["rf"], "TIER 2 alternative: Random Forest importance ranking, |r| < 0.95 redundancy filter, same number of bands as CART.", "Comparison requested: an ensemble ranking that is less sensitive to one tree (Breiman 2001; Strobl et al. 2008)."),
        ("6", S["jm"], "TIER 3: J–M distance of each band selected by CART and by RF, cumulative J–M and J–M of the whole set (live matrix formula).", "Separability of the classes on the selected bands; 1.94 threshold of Das et al. (2020)."),
        ("7", S["cv1"], "TIER 4 as in Das et al.: QDA with random 10-fold CV on the Tier-2 bands; error matrix with OA, PA, UA, kappa (live).", "Reproduces the paper's validation for direct comparison."),
        ("8", S["cv2"], "CV2: plot-grouped nested 4-fold CV × 10 (all tiers refitted inside each training fold).", "Spectra of one plot are not independent: whole plots must be held out (Roberts et al. 2017; Ambroise & McLachlan 2002)."),
        ("9", S["cv3"], "CV3: leave-one-plot-out; prediction for every plot.", "Shows which plots are misclassified."),
        ("10", S["cvd"], "CV4–CV6: leave-one-treatment-combination / variety / inoculation-date-out.", "Tests transfer to treatment levels the model has never seen (Meyer et al. 2018)."),
        ("11", S["nc"], "Negative control (block vs block), restricted block permutation, detection by block/variety/date.", "All healthy plots form one block: measures how much of the separation is location (Lipsitch et al. 2010; Anderson & ter Braak 2003)."),
        ("12", S["acc"], "Accuracy assessment: error matrices (live formulas) and OA, BA, kappa, PA, UA, F1, MCC, quantity/allocation disagreement with 95% plot-bootstrap CIs.", "Complete and correctly computed accuracy (Congalton 1991; Story & Congalton 1986; Olofsson et al. 2014; Pontius & Millones 2011)."),
        ("13", S["perm"], "Permutation test with shuffled plot labels (live p).", "Is the accuracy better than chance? (Ojala & Garriga 2010)."),
        ("14", S["sens"], "Sensitivity analysis with the band removal of Das et al. (no bands ≥ 2350 nm).", "Checks that conclusions do not depend on the noisy detector edge."),
        ("15", S["cmp"], "CART vs RF under every validation scheme (live links).", "The comparison requested."),
        ("16", S["refs"], "References: what each is used for and how the citation was checked.", ""),
        ("17", S["chk"], "Cross-checks (Python and live Excel) with PASS/FAIL.", "Every step verified twice.")]
for i, (a, b, c, d_) in enumerate(rows):
    put(ws, 5 + i, 1, a); put(ws, 5 + i, 2, b, font=F_B); put(ws, 5 + i, 3, c, wrap=True); put(ws, 5 + i, 4, d_, wrap=True); ws.row_dimensions[5 + i].height = 30
r = 6 + len(rows)
put(ws, r, 1, "Colour code", font=F_B)
put(ws, r + 1, 2, "Blue", font=F_IN); put(ws, r + 1, 3, "Input data, or results computed in Python (scipy, statsmodels, scikit-learn)")
put(ws, r + 2, 2, "Black", font=F_FX); put(ws, r + 2, 3, "Live Excel formulas"); put(ws, r + 3, 2, "Green", font=F_LINK); put(ws, r + 3, 3, "Live formulas linking to another sheet")
put(ws, r + 4, 2, "Yellow fill", fill=FILL_K); put(ws, r + 4, 3, "Key results")
put(ws, r + 6, 1, "Software", font=F_B); put(ws, r + 7, 3, "Python 3.13; numpy; pandas; scipy; statsmodels; scikit-learn 1.9 (Pedregosa et al. 2011). CART pruning re-implemented to match R rpart's cp (Therneau & Atkinson). Random seed 42.", wrap=True)

# ============================================================ ABBREVIATIONS
ws = sheet("Abbreviations", "Abbreviations", "V1–V3 = varieties; CV1–CV6 = validation schemes. 'D' alone = diseased, D1–D4 = inoculation dates; 'R' + wavelength = reflectance, R1–R3 = inoculated blocks.")
header(ws, 4, 1, ["Abbreviation", "Meaning"], [22, 110])
for i, (a_, m_) in enumerate(ABBR): put(ws, 5 + i, 1, a_, bold=True); put(ws, 5 + i, 2, m_)

# ============================================================ 1 DATA
ws = sheet(S["raw"], "Step 0 — all endmember spectra (one row per endmember)", f"Rows 5–{4+nH}: healthy (plots 1–3, 5–12); rows {5+nH}–{4+N}: diseased (plots 13–48). Columns E onward: reflectance at each of the {P} bands.")
header(ws, 4, 1, ["plot", "EM", "spectrum_id", "class"] + [f"{w:.3f}" for w in wl])
for i in range(N):
    put(ws, 5 + i, 1, int(meta["plot"][i])); put(ws, 5 + i, 2, int(meta["em"][i])); put(ws, 5 + i, 3, meta["spectrum_id"][i]); put(ws, 5 + i, 4, meta["class"][i])
    for j in range(P): ws.cell(5 + i, 5 + j, float(X[i, j])).font = F_IN
ws.freeze_panes = "E5"
H0, H1, D0, D1 = 5, 4 + nH, 5 + nH, 4 + N
def col(j): return CL(5 + j)
def rH(j): return f"{q(S['raw'])}!{col(j)}${H0}:{col(j)}${H1}"
def rD(j): return f"{q(S['raw'])}!{col(j)}${D0}:{col(j)}${D1}"
def rA(j): return f"{q(S['raw'])}!{col(j)}${H0}:{col(j)}${D1}"

# ============================================================ 2 SUMMARY
ws = sheet(S["summ"], "Step 1 — data summary", "Live COUNTIF on sheet 1_Data. No spectrum and no band is removed.",
           "The class balance decides whether imbalance handling is needed; out-of-range reflectance is a data-quality warning.")
header(ws, 5, 1, ["Plot", "Class", "Spectra (live)"], [8, 10, 13])
plots_all = PH + PD
for i, k in enumerate(plots_all):
    rr = 6 + i; put(ws, rr, 1, k); put(ws, rr, 2, "healthy" if k in PH else "diseased"); put(ws, rr, 3, f"=COUNTIF({q(S['raw'])}!$A$5:$A${D1},A{rr})")
RL = 5 + len(plots_all)
put(ws, RL + 1, 1, "Total", bold=True); put(ws, RL + 1, 3, f"=SUM(C6:C{RL})", fill=FILL_K)
LIVE.append(("Data", "Spectra counted per plot = all spectra", f"=ABS({q(S['summ'])}!C{RL+1}-{N})", 0.5))
header(ws, 5, 5, ["Class", "Plots", "Spectra", "Share", "Per plot"], [12, 8, 10, 10, 10])
for i, cl in enumerate(("healthy", "diseased")):
    rr = 6 + i; put(ws, rr, 5, cl); put(ws, rr, 6, f'=COUNTIF($B$6:$B${RL},"{cl}")'); put(ws, rr, 7, f'=SUMIF($B$6:$B${RL},"{cl}",$C$6:$C${RL})')
    put(ws, rr, 8, f"=G{rr}/G8", fmt="0.0%"); put(ws, rr, 9, f"=G{rr}/F{rr}", fmt="0.0")
put(ws, 8, 5, "Total", bold=True); put(ws, 8, 6, "=F6+F7"); put(ws, 8, 7, "=G6+G7")
put(ws, 10, 5, "Spectra ratio diseased : healthy", bold=True); put(ws, 10, 8, "=G7/G6", fmt='"1 : "0.000', fill=FILL_K)
put(ws, 11, 5, "Plot ratio diseased : healthy", bold=True); put(ws, 11, 8, "=F7/F6", fmt='"1 : "0.00', fill=FILL_K)
note(ws, 12, 5, "Spectra are balanced (1078 vs 1080) by the extraction design (98 vs 30 endmembers per plot), so no re-sampling or class weighting is applied in the main analysis. Plots are not balanced (11 vs 36), so balanced accuracy is reported next to overall accuracy (Brodersen et al. 2010).", 7)
ng, ns = R["neg"], R["neg_spectra"]
put(ws, 15, 5, "Spectra with any reflectance < 0 (healthy / diseased)", bold=True); put(ws, 15, 9, f"{ns['healthy']} / {ns['diseased']}")
put(ws, 16, 5, "Spectra with any reflectance > 1 (healthy / diseased)", bold=True); put(ws, 16, 9, f"{ns['gt1_healthy']} / {ns['gt1_diseased']}")
header(ws, 18, 5, ["Wavelength (nm)", "Healthy < 0", "Diseased < 0", "Healthy > 1", "Diseased > 1"])
for i in range(P):
    put(ws, 19 + i, 5, float(wl[i]), fmt="0.000"); put(ws, 19 + i, 6, int(ng.neg_healthy[i])); put(ws, 19 + i, 7, int(ng.neg_diseased[i]))
    put(ws, 19 + i, 8, int(ng.gt1_healthy[i])); put(ws, 19 + i, 9, int(ng.gt1_diseased[i]))

# ============================================================ 3 DESIGN
ws = sheet(S["des"], "Step 2 — treatment design (treatment_detail.xlsx) and plot positions (EXCEPTPLOT4.xml)",
           "Block C = control (healthy); R3, R2, R1 = inoculated (diseased). Every block contains each variety (V1–V3) × inoculation date (D1–D4) once; plot 4 (C, V1·D3) is excluded.",
           "The experimental unit is the plot. Validation must hold out whole plots, and the spatial layout shows whether class and location are confounded (Hurlbert 1984).")
header(ws, 5, 1, ["Plot", "Block", "Variety", "Inoculation (DAS code)", "Class", "Spectra (live)", "East (m)", "North (m)"], [7, 8, 9, 14, 10, 10, 10, 10])
for i, k in enumerate(td.index):
    rr = 6 + i
    for j, v in enumerate([int(k), td.block[k], td.variety[k], td.date[k], td["class"][k]]): put(ws, rr, 1 + j, v)
    put(ws, rr, 6, f"=COUNTIF({q(S['raw'])}!$A$5:$A${D1},A{rr})"); put(ws, rr, 7, float(td.x_m[k]), fmt="0.0"); put(ws, rr, 8, float(td.y_m[k]), fmt="0.0")
DL = 5 + len(td)
DATES, VARS, BLOCKS = sorted(td.date.unique()), sorted(td.variety.unique()), ["C", "R3", "R2", "R1"]
put(ws, 5, 10, "Plots per block × variety × date (live COUNTIFS)", font=F_B)
for bi, b in enumerate(BLOCKS):
    r0 = 6 + bi * 6; put(ws, r0, 10, f"Block {b}", bold=True)
    for j, d_ in enumerate(DATES): put(ws, r0, 11 + j, d_, bold=True)
    for i, v in enumerate(VARS):
        put(ws, r0 + 1 + i, 10, v, bold=True)
        for j, d_ in enumerate(DATES): put(ws, r0 + 1 + i, 11 + j, f'=COUNTIFS($B$6:$B${DL},"{b}",$C$6:$C${DL},"{v}",$D$6:$D${DL},"{d_}")')
put(ws, 31, 10, "Cells = 1 (47 expected; the empty cell is plot 4)", bold=True); put(ws, 31, 15, "=COUNTIF(K7:N9,1)+COUNTIF(K13:N15,1)+COUNTIF(K19:N21,1)+COUNTIF(K25:N27,1)", fill=FILL_K)
LIVE.append(("Design", "Block × variety × date cells holding one plot = 47", f"=ABS({q(S['des'])}!O31-47)", 0.5))
put(ws, 33, 10, "Block centres (live) and distances (m)", font=F_B)
header(ws, 34, 10, ["Block", "East", "North"] + [f"to {b}" for b in BLOCKS])
for i, b in enumerate(BLOCKS):
    rr = 35 + i; put(ws, rr, 10, b, bold=True)
    put(ws, rr, 11, f'=AVERAGEIF($B$6:$B${DL},J{rr},$G$6:$G${DL})', fmt="0.0"); put(ws, rr, 12, f'=AVERAGEIF($B$6:$B${DL},J{rr},$H$6:$H${DL})', fmt="0.0")
    for j in range(4): put(ws, rr, 13 + j, f"=SQRT((K{rr}-K{35+j})^2+(L{rr}-L{35+j})^2)", fmt="0.0")
note(ws, 40, 10, "All healthy plots lie in one contiguous block (C) at the west end; healthy vs diseased is therefore partly confounded with location. Sheets 11 and 12 test this.", 7)

# ============================================================ 4 TIER 1
t1 = R["tier1"]; TR0 = 14
ws = sheet(S["t1"], "Step 3 — TIER 1: one-way ANOVA at every band (healthy vs diseased)",
           "Columns C–R are live formulas on 1_Data; S onward are Python results and cross-checks. H0: mean reflectance of healthy = diseased at band i; reject if p < 0.05 (Das et al. 2020).",
           "Removes bands where the class means do not differ, so Tier 2 only chooses among informative bands. With 2 classes Tukey HSD tests one pair and gives the ANOVA decision.")
hdr = ["Band #", "Wavelength (nm)", "n healthy", "n diseased", "Mean healthy", "Mean diseased", "SD healthy", "SD diseased", "SS between", "SS within",
       "df between", "df within", "F", "p", "Significant (p<0.05)", "Cohen's d (D−H)", "Bhattacharyya B (1 band)", "JM 0–2 (1 band)",
       "Tukey HSD p", "Welch p", "Levene p", "FDR q", "Bonferroni p", "F plot means (n=47)", "p plot means", "F (Python)", "|ΔF|/F", "p (Python)", "|Δp|", "JM (Python)", "|ΔJM|"]
header(ws, TR0, 1, hdr, [7, 11, 8, 8, 10, 10, 10, 10, 11, 11, 7, 7, 10, 11, 10, 10, 11, 10, 11, 11, 11, 11, 11, 11, 11, 10, 10, 11, 10, 10, 10])
for j in range(P):
    r = TR0 + 1 + j
    put(ws, r, 1, j + 1); put(ws, r, 2, float(wl[j]), fmt="0.000")
    put(ws, r, 3, f"=COUNT({rH(j)})"); put(ws, r, 4, f"=COUNT({rD(j)})")
    put(ws, r, 5, f"=AVERAGE({rH(j)})", fmt="0.00000"); put(ws, r, 6, f"=AVERAGE({rD(j)})", fmt="0.00000")
    put(ws, r, 7, f"=STDEV({rH(j)})", fmt="0.00000"); put(ws, r, 8, f"=STDEV({rD(j)})", fmt="0.00000")
    put(ws, r, 10, f"=DEVSQ({rH(j)})+DEVSQ({rD(j)})", fmt="0.000000"); put(ws, r, 9, f"=DEVSQ({rA(j)})-J{r}", fmt="0.000000")
    put(ws, r, 11, 1); put(ws, r, 12, f"=C{r}+D{r}-2"); put(ws, r, 13, f"=(I{r}/K{r})/(J{r}/L{r})", fmt="0.000")
    put(ws, r, 14, f"=FDIST(M{r},K{r},L{r})", fmt="0.00E+00"); put(ws, r, 15, f'=IF(N{r}<0.05,"yes","no")')
    put(ws, r, 16, f"=(F{r}-E{r})/SQRT(((C{r}-1)*G{r}^2+(D{r}-1)*H{r}^2)/L{r})", fmt="0.000")
    put(ws, r, 17, f"=(F{r}-E{r})^2/(4*(G{r}^2+H{r}^2))+0.5*LN((G{r}^2+H{r}^2)/(2*G{r}*H{r}))", fmt="0.0000")
    put(ws, r, 18, f"=2*(1-EXP(-Q{r}))", fmt="0.0000")
    for c, key in zip(range(19, 26), ["Tukey_p", "Welch_p", "Levene_p", "FDR_q", "Bonferroni_p", "F_plot_means", "p_plot_means"]):
        put(ws, r, c, float(t1[key][j]), fmt="0.000" if key == "F_plot_means" else "0.00E+00")
    put(ws, r, 26, float(t1.F[j]), fmt="0.000"); put(ws, r, 27, f"=ABS(M{r}-Z{r})/Z{r}", fmt="0.0E+00")
    put(ws, r, 28, float(t1.p_ANOVA[j]), fmt="0.00E+00"); put(ws, r, 29, f"=ABS(N{r}-AB{r})", fmt="0.0E+00")
    put(ws, r, 30, float(t1.JM_band[j]), fmt="0.0000"); put(ws, r, 31, f"=ABS(R{r}-AD{r})", fmt="0.0E+00")
TL = TR0 + P; ws.freeze_panes = f"C{TR0+1}"
B_, rng = f"$B${TR0+1}:$B${TL}", lambda c: f"${c}${TR0+1}:${c}${TL}"
put(ws, 5, 1, "Summary (live)", font=F_B)
items = [("Bands tested", f"=COUNT({rng('B')})"), ("Significant, p < 0.05 (criterion of Das et al.) → passed to Tier 2", f'=COUNTIF({rng("O")},"yes")'),
         ("Significant after FDR (Benjamini–Hochberg)", f'=COUNTIF({rng("V")},"<0.05")'), ("Significant after Bonferroni", f'=COUNTIF({rng("W")},"<0.05")'),
         ("Significant by Welch test", f'=COUNTIF({rng("T")},"<0.05")'), ("Significant with the 47 plot means as replicates", f'=COUNTIF({rng("Y")},"<0.05")'),
         ("Largest |Cohen's d|", f"=MAX(MAX({rng('P')}),-MIN({rng('P')}))"), ("Largest single-band J–M", f"=MAX({rng('R')})")]
for i, (a, f) in enumerate(items): put(ws, 6 + i, 1, a); put(ws, 6 + i, 6, f, fill=FILL_K if i in (1, 5) else None, fmt="0.000" if i >= 6 else None)
LIVE += [("Tier 1", "max relative |F(Excel) − F(Python)|", f"=MAX({q(S['t1'])}!AA{TR0+1}:AA{TL})", 1e-6),
         ("Tier 1", "max |p(Excel) − p(Python)|", f"=MAX({q(S['t1'])}!AC{TR0+1}:AC{TL})", 1e-6),
         ("Tier 1", "significant bands: Excel − Python", f"=ABS({q(S['t1'])}!F7-{int((t1.p_ANOVA<0.05).sum())})", 0.5),
         ("Tier 3", "max |single-band JM(Excel) − Python| over all bands", f"=MAX({q(S['t1'])}!AE{TR0+1}:AE{TL})", 1e-9)]
put(ws, 5, 9, "By spectral region (live)", font=F_B)
header(ws, 6, 9, ["Region", "From", "To", "Bands", "p<0.05", "FDR", "Plot means"])
for i, (nm, lo, hi) in enumerate([("VIS", 0, 700), ("Red-edge", 700, 750), ("NIR", 750, 1350), ("SWIR-1", 1350, 1800), ("SWIR-2", 1800, 3000)]):
    rr = 7 + i; put(ws, rr, 9, nm); put(ws, rr, 10, lo); put(ws, rr, 11, hi)
    put(ws, rr, 12, f'=COUNTIFS({B_},">="&J{rr},{B_},"<"&K{rr})'); put(ws, rr, 13, f'=COUNTIFS({B_},">="&J{rr},{B_},"<"&K{rr},{rng("O")},"yes")')
    put(ws, rr, 14, f'=COUNTIFS({B_},">="&J{rr},{B_},"<"&K{rr},{rng("V")},"<0.05")'); put(ws, rr, 15, f'=COUNTIFS({B_},">="&J{rr},{B_},"<"&K{rr},{rng("Y")},"<0.05")')
T1B, T1R = f"{q(S['t1'])}!$B${TR0+1}:$B${TL}", f"{q(S['t1'])}!$R${TR0+1}:$R${TL}"
def jm_live(cell): return f"=INDEX({T1R},MATCH({cell},{T1B},0))"

# ============================================================ 5 CART / 6 RF
for key, t2, title, why in (("cart", "CART", "Step 4 — TIER 2: CART on the ANOVA-significant bands (rpart settings: Gini, minsplit 20, minbucket 7, maxdepth 30, cp 0.01)",
                             "Das et al. used rpart to reduce the significant bands to a small subset that separates the classes; the bands used in the pruned tree are kept."),
                            ("rf", "RF", "Step 5 — TIER 2 alternative: Random Forest band selection (500 trees, mtry = √p, mean decrease in Gini)",
                             "Requested comparison. RF ranks bands by importance over many trees; neighbouring bands with |r| ≥ 0.95 are skipped (Strobl et al. 2008) and as many bands as CART are kept.")):
    ws = sheet(S[key], title, "Bands selected on ALL spectra (for reporting and Tier 3). In CV2–CV6 the selection is repeated inside every training fold.", why)
    v = full[t2]
    header(ws, 5, 1, ["Order", "Band (nm)", "Region", "Single-band J–M (live)", "J–M of first k bands", "Excel − Python"], [8, 11, 11, 14, 14, 12])
    for i, (b, wv) in enumerate(zip(v["bands"], v["wl"])):
        rr = 6 + i; put(ws, rr, 1, i + 1); put(ws, rr, 2, float(wv), fmt="0.000"); put(ws, rr, 3, region(wv))
        put(ws, rr, 4, jm_live(f"B{rr}"), fmt="0.0000"); put(ws, rr, 5, float(v["cum"][i]), fmt="0.0000"); put(ws, rr, 6, f"=ABS(D{rr}-{float(v['jm_single'][i])})", fmt="0.0E+00")
    re_ = 6 + len(v["bands"])
    put(ws, re_, 1, "Set", bold=True); put(ws, re_, 4, f"=MAX(D6:D{re_-1})", fmt="0.0000"); put(ws, re_, 5, float(v["JM"]), fmt="0.0000", fill=FILL_K)
    put(ws, re_ + 1, 1, "(row 'Set': column D = largest single-band J–M, column E = J–M of all bands together)")
    LIVE.append(("Tier 3", f"{t2}: single-band J–M (live) − Python, max", f"=MAX({q(S[key])}!F6:F{re_-1})", 1e-9))
    if t2 == "CART":
        put(ws, 4, 1, f"{len(v['bands'])} bands, in the order of first use in the pruned tree (root first). Tree: {v['nodes']} splits; resubstitution accuracy {v['train_acc']*100:.1f}%.", font=F_B)
        tr = v["tree"]; L_, R_, f_, th, cnt, fidx, pr = tr["L"], tr["Rr"], tr["f"], tr["thr"], tr["counts"], tr["feat_idx"], tr["pr"]
        r0 = re_ + 4; put(ws, r0, 1, "Pruned tree, depth-first (left branch = condition true)", font=F_B)
        header(ws, r0 + 1, 1, ["Node", "Type", "Split", "Healthy spectra", "Diseased spectra", "Predicted"])
        rr = r0 + 2; st = [(0, 0)]
        while st:
            nd, dd = st.pop(); leaf = L_[nd] == -1 or pr[nd]
            put(ws, rr, 1, int(nd)); put(ws, rr, 2, ("  " * dd) + ("leaf" if leaf else "split"))
            put(ws, rr, 3, "" if leaf else f"R({wl[fidx[f_[nd]]]:.1f} nm) ≤ {th[nd]:.4f}"); put(ws, rr, 4, float(cnt[nd, 0]), fmt="0"); put(ws, rr, 5, float(cnt[nd, 1]), fmt="0")
            put(ws, rr, 6, "diseased" if cnt[nd, 1] > cnt[nd, 0] else "healthy"); rr += 1
            if not leaf: st += [(R_[nd], dd + 1), (L_[nd], dd + 1)]
        rr += 2; put(ws, rr, 1, "Cost-complexity sequence (rpart cp, relative to root error) → number of splits", font=F_B)
        header(ws, rr + 1, 1, ["cp", "Splits"])
        for i, (cp, ns_) in enumerate(v["seq"]): put(ws, rr + 2 + i, 1, cp, fmt="0.0000"); put(ws, rr + 2 + i, 2, ns_)
    else:
        put(ws, 4, 1, f"{len(v['bands'])} bands (= number of CART bands), in order of importance after the |r| < 0.95 filter.", font=F_B)
        imp = v["importance"].sort_values("importance", ascending=False).head(50); kept = set(v["bands"])
        r0 = re_ + 4; put(ws, r0, 1, "Importance ranking (top 50 of the ANOVA-significant bands)", font=F_B)
        header(ws, r0 + 1, 1, ["Rank", "Band (nm)", "Importance", "Kept?"])
        for i, rw in enumerate(imp.itertuples(index=False)):
            put(ws, r0 + 2 + i, 1, i + 1); put(ws, r0 + 2 + i, 2, float(wl[int(rw.band)]), fmt="0.0"); put(ws, r0 + 2 + i, 3, float(rw.importance), fmt="0.00000")
            put(ws, r0 + 2 + i, 4, "yes" if int(rw.band) in kept else "skipped (|r| ≥ 0.95 with a kept band) or beyond K")

# ============================================================ 7 TIER 3
ws = sheet(S["jm"], "Step 6 — TIER 3: Jeffries–Matusita distance",
           "JM = 2(1 − e^(−B)), B = Bhattacharyya distance; 0–2 scale ('square of J–M' in Das et al.); threshold 1.94. Computed on all spectra.",
           "Tells how separable healthy and diseased are on the bands chosen in Tier 2 — for every single band and for the set.")
KM = max(len(full[t]["bands"]) for t in T2)
for k_, t2 in enumerate(T2):
    c0 = 1 + 6 * k_; v = full[t2]
    put(ws, 5, c0, f"{t2} bands", font=F_B)
    header(ws, 6, c0, ["#", "Band (nm)", "J–M single band (live)", "J–M cumulative", "Region"], [6, 11, 14, 13, 10])
    for i, (b, wv) in enumerate(zip(v["bands"], v["wl"])):
        rr = 7 + i; put(ws, rr, c0, i + 1); put(ws, rr, c0 + 1, float(wv), fmt="0.000"); put(ws, rr, c0 + 2, jm_live(f"{CL(c0+1)}{rr}"), fmt="0.0000")
        put(ws, rr, c0 + 3, float(v["cum"][i]), fmt="0.0000"); put(ws, rr, c0 + 4, region(wv))
    rr = 7 + KM
    put(ws, rr, c0, "Mean single", bold=True); put(ws, rr, c0 + 2, f"=AVERAGE({CL(c0+2)}7:{CL(c0+2)}{6+len(v['bands'])})", fmt="0.0000")
    put(ws, rr + 1, c0, "Max single", bold=True); put(ws, rr + 1, c0 + 2, f"=MAX({CL(c0+2)}7:{CL(c0+2)}{6+len(v['bands'])})", fmt="0.0000")
    put(ws, rr + 2, c0, "Whole set", bold=True); put(ws, rr + 2, c0 + 3, float(v["JM"]), fmt="0.0000", fill=FILL_K)
    put(ws, rr + 3, c0, "≥ 1.94?", bold=True); put(ws, rr + 3, c0 + 3, f'=IF({CL(c0+3)}{rr+2}>=1.94,"yes","no")')
REF = {}
rL = 7 + KM + 6
for t2 in T2:
    bands = full[t2]["bands"]; k = len(bands)
    put(ws, rL, 1, f"Live matrix J–M of the whole {t2} set ({k} bands): Bhattacharyya B = (1/8) dᵀ C⁻¹ d + ½ ln(|C| / √(|C_H||C_D|)), C = (C_H + C_D)/2", font=F_B)
    put(ws, rL + 1, 1, "d = μD − μH", bold=True)
    for i, j in enumerate(bands):
        put(ws, rL, 2 + i, float(wl[j]), fmt="0.0"); put(ws, rL + 1, 2 + i, f"=AVERAGE({rD(j)})-AVERAGE({rH(j)})", fmt="0.00000")
    dR = f"$B${rL+1}:${CL(1+k)}${rL+1}"
    def block(r0, which):
        put(ws, r0, 1, {"H": "Covariance healthy", "D": "Covariance diseased", "M": "Average covariance"}[which], bold=True)
        for a in range(k):
            for bb in range(k):
                ja, jb = bands[a], bands[bb]
                f = (f"=COVAR({rH(ja)},{rH(jb)})*{nH}/{nH-1}" if which == "H" else f"=COVAR({rD(ja)},{rD(jb)})*{nD}/{nD-1}" if which == "D"
                     else f"=({CL(2+bb)}{rh+1+a}+{CL(2+bb)}{rd+1+a})/2")
                put(ws, r0 + 1 + a, 2 + bb, f, fmt="0.00E+00")
        return f"$B${r0+1}:${CL(1+k)}${r0+k}"
    rh = rL + 3; CH_ = block(rh, "H"); rd = rh + k + 2; CD_ = block(rd, "D"); rm = rd + k + 2; CM_ = block(rm, "M")
    rr = rm + k + 2
    header(ws, rr, 1, ["Quantity", "Excel (live)", "Python", "|Δ|"])
    put(ws, rr + 1, 1, "Bhattacharyya B"); put(ws, rr + 1, 2, f"=SUMPRODUCT(MMULT({dR},MINVERSE({CM_})),{dR})/8+0.5*LN(MDETERM({CM_})/SQRT(MDETERM({CH_})*MDETERM({CD_})))", fmt="0.0000")
    put(ws, rr + 1, 3, float(full[t2]["B"]), fmt="0.0000"); put(ws, rr + 1, 4, f"=ABS(B{rr+1}-C{rr+1})", fmt="0.0E+00")
    put(ws, rr + 2, 1, "J–M (0–2)"); put(ws, rr + 2, 2, f"=2*(1-EXP(-B{rr+1}))", fmt="0.0000", fill=FILL_K); put(ws, rr + 2, 3, float(full[t2]["JM"]), fmt="0.0000")
    put(ws, rr + 2, 4, f"=ABS(B{rr+2}-C{rr+2})", fmt="0.0E+00")
    LIVE.append(("Tier 3", f"|J–M of the {t2} set: Excel matrix formula − Python|", f"={q(S['jm'])}!D{rr+2}", 1e-6))
    rL = rr + 5

# ============================================================ accuracy block helper
AK = [("OA", "Overall accuracy"), ("BA", "Balanced accuracy"), ("kappa", "Kappa"), ("PA_H", "PA healthy"), ("UA_H", "UA healthy"), ("PA_D", "PA diseased"),
      ("UA_D", "UA diseased"), ("F1_H", "F1 healthy"), ("F1_D", "F1 diseased"), ("MCC", "MCC"), ("QD", "Quantity disagreement"), ("AD", "Allocation disagreement")]
ACC_DELTA = []
def acc_block(ws, r0, c0, title, cm, py):
    put(ws, r0, c0, title, font=F_B)
    header(ws, r0 + 1, c0, ["Reference \\ Predicted", "Healthy", "Diseased", "Total", "PA"])
    for i, nm in enumerate(["Healthy", "Diseased"]):
        r = r0 + 2 + i; put(ws, r, c0, nm, bold=True); put(ws, r, c0 + 1, int(cm[i, 0])); put(ws, r, c0 + 2, int(cm[i, 1]))
        put(ws, r, c0 + 3, f"=SUM({CL(c0+1)}{r}:{CL(c0+2)}{r})"); put(ws, r, c0 + 4, f"={CL(c0+1+i)}{r}/{CL(c0+3)}{r}", fmt="0.0%")
    rt = r0 + 4; put(ws, rt, c0, "Total", bold=True)
    for j in range(3): put(ws, rt, c0 + 1 + j, f"=SUM({CL(c0+1+j)}{r0+2}:{CL(c0+1+j)}{r0+3})")
    put(ws, rt + 1, c0, "UA", bold=True)
    for j in range(2): put(ws, rt + 1, c0 + 1 + j, f"={CL(c0+1+j)}{r0+2+j}/{CL(c0+1+j)}{rt}", fmt="0.0%")
    a, b, c, d, n = f"{CL(c0+1)}{r0+2}", f"{CL(c0+2)}{r0+2}", f"{CL(c0+1)}{r0+3}", f"{CL(c0+2)}{r0+3}", f"{CL(c0+3)}{rt}"
    PAH, PAD, UAH, UAD = f"{CL(c0+4)}{r0+2}", f"{CL(c0+4)}{r0+3}", f"{CL(c0+1)}{rt+1}", f"{CL(c0+2)}{rt+1}"
    pe = f"(({a}+{b})*({a}+{c})+({c}+{d})*({b}+{d}))/{n}^2"
    m0 = r0 + 1; mc = c0 + 6
    header(ws, m0, mc, ["Measure", "Excel (live)", "Python", "|Δ|"])
    forms = [("OA", f"=({a}+{d})/{n}"), ("BA", f"=({PAH}+{PAD})/2"), ("kappa", f"=(({a}+{d})/{n}-{pe})/(1-{pe})"),
             ("PA_H", f"={PAH}"), ("UA_H", f"={UAH}"), ("PA_D", f"={PAD}"), ("UA_D", f"={UAD}"),
             ("F1_H", f"=2*{PAH}*{UAH}/({PAH}+{UAH})"), ("F1_D", f"=2*{PAD}*{UAD}/({PAD}+{UAD})"),
             ("MCC", f"=({d}*{a}-{b}*{c})/SQRT(({d}+{b})*({d}+{c})*({a}+{b})*({a}+{c}))"),
             ("QD", f"=(ABS(({a}+{b})-({a}+{c}))+ABS(({c}+{d})-({b}+{d})))/(2*{n})"), ("AD", f"=1-({a}+{d})/{n}-{CL(mc+1)}{m0+11}")]
    for i, (key, f) in enumerate(forms):
        r = m0 + 1 + i; put(ws, r, mc, dict(AK)[key], bold=True); put(ws, r, mc + 1, f, fmt="0.0000", fill=FILL_K if key in ("OA", "BA") else None)
        pv = py.get(key); put(ws, r, mc + 2, None if pv is None or np.isnan(pv) else float(pv), fmt="0.0000")
        put(ws, r, mc + 3, f'=IF(ISNUMBER({CL(mc+2)}{r}),ABS({CL(mc+1)}{r}-{CL(mc+2)}{r}),0)', fmt="0.0E+00")
    ACC_DELTA.append(f"{q(ws.title)}!{CL(mc+3)}{m0+1}:{CL(mc+3)}{m0+12}")
    return {"OA": f"{q(ws.title)}!{CL(mc+1)}{m0+1}", "BA": f"{q(ws.title)}!{CL(mc+1)}{m0+2}"}
MK = [("BA", "Balanced acc.", "0.0%"), ("OA", "Overall acc.", "0.0%"), ("kappa", "Kappa", "0.000"), ("MCC", "MCC", "0.000"), ("sens_D", "PA diseased (sensitivity)", "0.0%"),
      ("spec_H", "PA healthy (specificity)", "0.0%"), ("UA_D", "UA diseased", "0.0%"), ("UA_H", "UA healthy", "0.0%"), ("AUC", "ROC-AUC", "0.000")]
def rep_table(ws, r0, k, title):
    put(ws, r0, 1, title, font=F_B)
    header(ws, r0 + 1, 1, ["Tier 2", "Repetition"] + [m[1] for m in MK] + ["Plot-level BA"], [10, 11] + [12] * (len(MK) + 1))
    rr = r0 + 2; out = {}
    for t2 in T2:
        reps = Vt(t2, k)["reps"]; r_first = rr
        for i, m in enumerate(reps):
            put(ws, rr, 1, t2); put(ws, rr, 2, i + 1)
            for j, (key, _, fmt) in enumerate(MK):
                v = m.get(key, np.nan); put(ws, rr, 3 + j, None if v is None or (isinstance(v, float) and np.isnan(v)) else float(v), fmt=fmt)
            put(ws, rr, 3 + len(MK), float(m["plot"]["BA"]), fmt="0.0%"); rr += 1
        put(ws, rr, 1, t2, bold=True); put(ws, rr, 2, "mean (live)", bold=True)
        for j in range(len(MK) + 1):
            c = CL(3 + j); put(ws, rr, 3 + j, f"=AVERAGE({c}{r_first}:{c}{rr-1})", fmt=(MK[j][2] if j < len(MK) else "0.0%"), fill=FILL_K)
        put(ws, rr + 1, 2, "SD (live)")
        for j in range(len(MK) + 1):
            c = CL(3 + j); put(ws, rr + 1, 3 + j, f"=STDEV({c}{r_first}:{c}{rr-1})" if len(reps) > 1 else "—", fmt=(MK[j][2] if j < len(MK) else "0.0%"))
        out[t2] = f"{q(ws.title)}!C{rr}"; rr += 3
    return rr, out
for t2 in T2:
    for k in CVK:
        for lev in ("spectra", "plots"):
            m = Vt(t2, k)["acc"][lev]
            for key in ("UA_D", "UA_H"):
                pass
for t2 in T2:                                         # per-repetition user's accuracies for the repetition tables
    for k in CVK:
        for m in Vt(t2, k)["reps"]:
            cm = m["cm"]; m["UA_D"] = cm[1, 1] / max(cm[:, 1].sum(), 1); m["UA_H"] = cm[0, 0] / max(cm[:, 0].sum(), 1)

# ============================================================ 8 CV1 (Das et al.)
ws = sheet(S["cv1"], "Step 7 — TIER 4 with the validation of Das et al. (2020): QDA, random stratified 10-fold cross-validation",
           "Bands from Tier 2 (chosen on all spectra), QDA with empirical priors; folds drawn at random over spectra. Repeated 10 times with different random folds (repetition 1 = the single run of the paper).",
           "Reproduces the paper's Tier 4 for a like-for-like comparison. Because spectra of the same plot fall in both training and test, and the bands were chosen with the test spectra, the result is optimistic (Ambroise & McLachlan 2002; Roberts et al. 2017).")
end, MEAN_CV1 = rep_table(ws, 5, "CV1", "Accuracy of every repetition (spectrum level)")
REF_CV1 = {}
for i, t2 in enumerate(T2):
    m1 = Vt(t2, "CV1")["acc_rep1"]["spectra"]
    REF_CV1[t2] = acc_block(ws, end + 1, 1 + 11 * i, f"{t2} + QDA — error matrix of repetition 1 (as reported in Das et al.)", m1["cm"], m1)
    LIVE.append(("Tier 4", f"CV1 {t2}: OA from live error matrix − Python", f"=ABS({REF_CV1[t2]['OA']}-{float(Vt(t2, 'CV1')['reps'][0]['OA'])})", 1e-9))
for i, t2 in enumerate(T2):
    m = Vt(t2, "CV1")["acc"]["spectra"]
    acc_block(ws, end + 17, 1 + 11 * i, f"{t2} + QDA — error matrix summed over the 10 repetitions ({int(m['cm'].sum())} predictions)", m["cm"], m)

# ============================================================ 9 CV2
ws = sheet(S["cv2"], "Step 8 — CV2 (main result): plot-grouped, nested 4-fold cross-validation × 10 repetitions",
           "Each fold holds out whole plots (≈3 healthy + 9 diseased). Tier 1 (ANOVA), Tier 2 (CART/RF), and Tier 4 (QDA) are refitted on the training plots only.",
           "Spectra of one plot share soil, illumination and treatment, so they are not independent (Hurlbert 1984). Holding out whole plots and repeating the band selection inside each fold gives an honest accuracy (Roberts et al. 2017; Ambroise & McLachlan 2002).")
end, MEAN_CV2 = rep_table(ws, 5, "CV2", "Accuracy of every repetition (spectrum level; plot level = majority vote of each held-out plot)")
for i, t2 in enumerate(T2):
    m = Vt(t2, "CV2")["acc"]["spectra"]
    acc_block(ws, end + 1, 1 + 11 * i, f"{t2} + QDA — error matrix summed over 10 repetitions ({int(m['cm'].sum())} predictions)", m["cm"], m)
put(ws, end + 17, 1, "Bands selected in the 40 training folds (share of folds)", font=F_B)
for i, t2 in enumerate(T2):
    from collections import Counter
    cnt_ = Counter(b for m in Vt(t2, "CV2")["reps"] for fb in m["bands"] for b in fb); nf = sum(len(m["bands"]) for m in Vt(t2, "CV2")["reps"])
    header(ws, end + 18, 1 + 4 * i, [f"{t2} band (nm)", "Share of folds", "In full-data set?"])
    for j, (b, c) in enumerate(cnt_.most_common(25)):
        put(ws, end + 19 + j, 1 + 4 * i, float(wl[b]), fmt="0.0"); put(ws, end + 19 + j, 2 + 4 * i, c / nf, fmt="0%"); put(ws, end + 19 + j, 3 + 4 * i, "yes" if b in full[t2]["bands"] else "")

# ============================================================ 10 CV3
ws = sheet(S["cv3"], "Step 9 — CV3: leave-one-plot-out (47 folds, nested)", "Each plot is predicted by a model built on the other 46 plots; plot label = majority of its spectra.",
           "Shows, plot by plot, where the model fails — useful for field checking.")
header(ws, 5, 1, ["Plot", "Block", "Variety", "Inoculation", "True class"] + [f"{t2} % predicted diseased" for t2 in T2] + [f"{t2} correct? (live)" for t2 in T2], [7, 8, 9, 11, 10, 14, 14, 13, 13])
for i, k in enumerate(plots_all):
    rr = 6 + i
    for j, v in enumerate([k, td.block[k], td.variety[k], td.date[k], "healthy" if k in PH else "diseased"]): put(ws, rr, 1 + j, v)
    for j, t2 in enumerate(T2):
        put(ws, rr, 6 + j, float(Vt(t2, "CV3")["reps"][0]["plot"]["table"].frac[k]), fmt="0%")
        cp = CL(6 + j); put(ws, rr, 8 + j, f'=IF(OR(AND(E{rr}="diseased",{cp}{rr}>0.5),AND(E{rr}="healthy",{cp}{rr}<=0.5)),1,0)')
RE = 5 + len(plots_all)
for j, (lab_, crit) in enumerate((("Plots correct (of 47)", None), ("Healthy plots correct (of 11)", "healthy"), ("Diseased plots correct (of 36)", "diseased"))):
    put(ws, RE + 2 + j, 1, lab_, bold=True)
    for jj in range(2):
        c = CL(8 + jj)
        put(ws, RE + 2 + j, 8 + jj, f"=SUM({c}6:{c}{RE})" if crit is None else f'=SUMIF($E$6:$E${RE},"{crit}",{c}6:{c}{RE})', fill=FILL_K if crit is None else None)
put(ws, RE + 5, 1, "Plot-level balanced accuracy (live)", bold=True)
for jj in range(2):
    c = CL(8 + jj); put(ws, RE + 5, 8 + jj, f"=({c}{RE+3}/11+{c}{RE+4}/36)/2", fmt="0.0%", fill=FILL_K)
    LIVE.append(("Validation", f"CV3 {T2[jj]}: plot-level BA (live) − Python", f"=ABS({q(S['cv3'])}!{c}{RE+5}-{float(Vt(T2[jj], 'CV3')['reps'][0]['plot']['BA'])})", 1e-9))
for i, t2 in enumerate(T2):
    m = Vt(t2, "CV3")["acc"]["spectra"]; acc_block(ws, RE + 8, 1 + 11 * i, f"{t2} + QDA — error matrix (spectra)", m["cm"], m)
    m = Vt(t2, "CV3")["acc"]["plots"]; acc_block(ws, RE + 24, 1 + 11 * i, f"{t2} + QDA — error matrix (plots)", m["cm"], m)

# ============================================================ 11 CV4-6
ws = sheet(S["cvd"], "Step 10 — CV4–CV6: validation using the treatment design (nested)",
           "CV4 holds out the plots sharing one variety × inoculation date (1 control + 3 inoculated; the V1×D3 fold has no control because plot 4 is excluded); CV5 one variety; CV6 one inoculation date.",
           "Leave-location/group-out validation tests transfer to treatment levels the model never saw (Meyer et al. 2018; Roberts et al. 2017).")
r0 = 5; CVD_ROWS = {}
for k in ("CV4", "CV5", "CV6"):
    nm, labels = R["SCHEMES"][k]
    put(ws, r0, 1, f"{k} — {nm}: {len(labels)} folds ({', '.join(labels)})", font=F_B)
    header(ws, r0 + 1, 1, ["Tier 2"] + [m[1] for m in MK] + ["BA 95% CI low", "BA 95% CI high", "Plot-level BA", "Plots correct", "Folds without bands"], [12] + [12] * (len(MK) + 5))
    for i, t2 in enumerate(T2):
        rr = r0 + 2 + i; m = Vt(t2, k)["reps"][0]; a = Vt(t2, k)["acc"]["spectra"]; CVD_ROWS[(k, t2)] = rr
        put(ws, rr, 1, t2, bold=True)
        for j, (key, _, fmt) in enumerate(MK):
            v = m.get(key, np.nan); put(ws, rr, 2 + j, None if v is None or (isinstance(v, float) and np.isnan(v)) else float(v), fmt=fmt)
        c = 2 + len(MK); put(ws, rr, c, a["ci"]["BA"][0], fmt="0.0%"); put(ws, rr, c + 1, a["ci"]["BA"][1], fmt="0.0%"); put(ws, rr, c + 2, float(m["plot"]["BA"]), fmt="0.0%")
        tb = m["plot"]["table"]; put(ws, rr, c + 3, int((tb.pred == tb.t).sum())); put(ws, rr, c + 4, int(m["no_band_folds"]))
    header(ws, r0 + 5, 1, ["Held-out level", "Test plots", "Healthy plots"] + [f"{t2} accuracy" for t2 in T2] + [f"{t2} BA" for t2 in T2])
    for i, lab_ in enumerate(labels):
        rr = r0 + 6 + i; pf = [Vt(t2, k)["reps"][0]["per_fold"][i] for t2 in T2]
        put(ws, rr, 1, lab_); put(ws, rr, 2, pf[0]["plots"]); put(ws, rr, 3, pf[0]["healthy_plots"])
        for j in range(2): put(ws, rr, 4 + j, pf[j]["acc"], fmt="0.0%"); put(ws, rr, 6 + j, pf[j]["BA"] if pf[j]["BA"] is not None else "— (one class)", fmt="0.0%")
    r0 += 6 + len(labels) + 2

# ============================================================ 12 NEGATIVE CONTROL
NC, RP, DET = R["NC"], R["RP"], R["DET"]
ws = sheet(S["nc"], "Step 11 — negative control, restricted permutation and detection by treatment",
           "Block pairs classified with the same plot-grouped nested pipeline (4-fold × 5 repetitions) with class weights, because the control block has 98 spectra per plot and the inoculated blocks 30.",
           "Two INOCULATED blocks cannot differ by disease, so their accuracy measures the block/location effect (negative control; Lipsitch et al. 2010). Treatments were assigned to whole blocks, so blocks are the units to permute (Anderson & ter Braak 2003).")
header(ws, 5, 1, ["Pair", "Type", "Distance (m)", "Spectra", "Plots", "Tier-1 bands p<0.05", "Tier-1 bands, plot means", "Max single-band JM",
                  "CART BA", "CART SD", "RF BA", "RF SD", "CART plot BA", "RF plot BA"], [11, 36, 11, 12, 9, 12, 12, 12, 10, 10, 10, 10, 11, 11])
for i, r in enumerate(NC.values()):
    rr = 6 + i
    vals = [r["pair"], r["kind"], r["distance_m"], f"{r['n'][0]} / {r['n'][1]}", f"{r['plots'][0]} / {r['plots'][1]}", r["sig"], r["sig_plot"], r["jm_band_max"],
            r["CART"]["BA"][0], r["CART"]["BA"][1], r["RF"]["BA"][0], r["RF"]["BA"][1], r["CART"]["plotBA"][0], r["RF"]["plotBA"][0]]
    fm = [None, None, "0.0", None, None, "0", "0", "0.0000", "0.0%", "0.0%", "0.0%", "0.0%", "0.0%", "0.0%"]
    for j, (v, f_) in enumerate(zip(vals, fm)): put(ws, rr, 1 + j, float(v) if isinstance(v, (float, np.floating)) else v, fmt=f_)
put(ws, 13, 1, "Mean BA, control vs inoculated (live)", bold=True); put(ws, 13, 9, "=AVERAGE(I6:I8)", fmt="0.0%", fill=FILL_K); put(ws, 13, 11, "=AVERAGE(K6:K8)", fmt="0.0%", fill=FILL_K)
put(ws, 14, 1, "Mean BA, inoculated vs inoculated (live)", bold=True); put(ws, 14, 9, "=AVERAGE(I9:I11)", fmt="0.0%", fill=FILL_K); put(ws, 14, 11, "=AVERAGE(K9:K11)", fmt="0.0%", fill=FILL_K)
put(ws, 15, 1, "Difference = separation beyond the block effect", bold=True); put(ws, 15, 9, "=I13-I14", fmt="0.0%"); put(ws, 15, 11, "=K13-K14", fmt="0.0%")
put(ws, 16, 1, "Same distance (≈27 m): C vs R2 minus R3 vs R1", bold=True); put(ws, 16, 9, "=I7-I11", fmt="0.0%"); put(ws, 16, 11, "=K7-K11", fmt="0.0%")
put(ws, 19, 1, "Restricted (block-level) permutation: each block in turn labelled 'healthy' (class weights, 5 repetitions)", font=F_B)
header(ws, 20, 1, ["Block labelled healthy", "CART BA", "RF BA"])
for i, b in enumerate(BLOCKS):
    put(ws, 21 + i, 1, b + (" (true)" if b == "C" else ""), bold=(b == "C"))
    for j, t2 in enumerate(T2): put(ws, 21 + i, 2 + j, RP[t2]["ba"][b], fmt="0.0%")
put(ws, 25, 1, "p = share of labellings with BA ≥ true (live; minimum possible 0.25)", bold=True)
for j in range(2): c = CL(2 + j); put(ws, 25, 2 + j, f'=COUNTIF({c}21:{c}24,">="&{c}21)/4', fmt="0.00", fill=FILL_K)
put(ws, 28, 1, "Detection per plot: share of the plot's spectra predicted diseased (CV2 = mean of 10 repetitions; CV3 = leave-one-plot-out)", font=F_B)
tabC, tabR = DET["CART"]["table"], DET["RF"]["table"]
header(ws, 29, 1, ["Plot", "Block", "Variety", "Inoculation", "Class", "CART CV2", "RF CV2", "CART CV3", "RF CV3"])
for i, k in enumerate(tabC.index):
    rr = 30 + i
    for j, v in enumerate([int(k), tabC.block[k], tabC.variety[k], tabC.date[k], tabC["class"][k]]): put(ws, rr, 1 + j, v)
    for j, v in enumerate([tabC.pD_CV2[k], tabR.pD_CV2[k], tabC.pD_CV3[k], tabR.pD_CV3[k]]): put(ws, rr, 6 + j, float(v), fmt="0.0%")
DL2 = 29 + len(tabC)
put(ws, 28, 11, "Mean share predicted diseased (live AVERAGEIFS)", font=F_B)
header(ws, 29, 11, ["Group", "Level", "CART CV2", "RF CV2", "CART CV3", "RF CV3"], [16, 10, 10, 10, 10, 10])
rr = 30
for lv in BLOCKS:
    put(ws, rr, 11, "Block"); put(ws, rr, 12, lv)
    for j, c in enumerate("FGHI"): put(ws, rr, 13 + j, f'=AVERAGEIF($B$30:$B${DL2},L{rr},{c}$30:{c}${DL2})', fmt="0.0%")
    rr += 1
for fac, col_, levels in (("Variety", "C", VARS), ("Inoculation", "D", DATES)):
    for cl in ("healthy", "diseased"):
        for lv in levels:
            put(ws, rr, 11, f"{fac} ({cl})"); put(ws, rr, 12, lv)
            for j, c in enumerate("FGHI"): put(ws, rr, 13 + j, f'=AVERAGEIFS({c}$30:{c}${DL2},${col_}$30:${col_}${DL2},L{rr},$E$30:$E${DL2},"{cl}")', fmt="0.0%")
            rr += 1
rr += 1; put(ws, rr, 11, "Kruskal–Wallis on CV2 shares (Kruskal & Wallis 1952)", font=F_B); rr += 1
header(ws, rr, 11, ["Factor | class", "", "CART H", "CART p", "RF H", "RF p"]); rr += 1
for key in DET["CART"]["kw"]:
    put(ws, rr, 11, key)
    for j, t2 in enumerate(T2): h_, p_ = DET[t2]["kw"][key]; put(ws, rr, 13 + 2 * j, h_, fmt="0.00"); put(ws, rr, 14 + 2 * j, p_, fmt="0.000")
    rr += 1
put(ws, rr, 11, "block | diseased (R3, R2, R1)")
for j, t2 in enumerate(T2): h_, p_ = DET[t2]["kw_block"]; put(ws, rr, 13 + 2 * j, h_, fmt="0.00"); put(ws, rr, 14 + 2 * j, p_, fmt="0.000")

# ============================================================ 13 ACCURACY
ws = sheet(S["acc"], "Step 12 — accuracy assessment: error matrices and accuracy measures with 95% confidence intervals",
           "Rows = reference class, columns = predicted (Story & Congalton 1986; Congalton 1991). PA = correct / reference total (1 − omission error); UA = correct / predicted total (1 − commission error). 95% CI: plots resampled with replacement within each class, 2000 times (Field & Welsh 2007; Olofsson et al. 2014).",
           "Overall accuracy alone hides which class fails; PA/UA per class, balanced accuracy, MCC and the two disagreement components (Pontius & Millones 2011) give the full picture.")
put(ws, 5, 1, "A. Summary (Python values; CI = 95% stratified cluster bootstrap over plots)", font=F_B)
header(ws, 6, 1, ["Tier 2", "Validation", "Level", "Predictions"] + [a[1] for a in AK] + ["OA CI low", "OA CI high", "BA CI low", "BA CI high", "Kappa CI low", "Kappa CI high"],
       [10, 44, 9, 11] + [10] * (len(AK) + 6))
rr = 7
for t2 in T2:
    for k in CVK:
        for lev in ("spectra", "plots"):
            m = Vt(t2, k)["acc"][lev]
            put(ws, rr, 1, t2, bold=True); put(ws, rr, 2, f"{k} {CVN[k]}"); put(ws, rr, 3, lev); put(ws, rr, 4, int(m["cm"].sum()))
            for j, (key, _) in enumerate(AK):
                v = m[key]; put(ws, rr, 5 + j, None if np.isnan(v) else float(v), fmt="0.000" if key in ("kappa", "MCC", "F1_H", "F1_D") else "0.0%")
            if "ci" in m:
                for j, key in enumerate(("OA", "BA", "kappa")):
                    lo, hi = m["ci"][key]; fm = "0.000" if key == "kappa" else "0.0%"
                    put(ws, rr, 5 + len(AK) + 2 * j, lo, fmt=fm); put(ws, rr, 6 + len(AK) + 2 * j, hi, fmt=fm)
            rr += 1
ws.freeze_panes = "E7"
note(ws, rr + 1, 1, "CV1 (Das et al.) has no CI: its random folds put spectra of the same plot in training and test, so its error is not independent of training. CV1 values are summed over 10 repetitions (sheet 8 shows repetition 1 alone). Kappa is given for comparison with the literature; its use is debated (Pontius & Millones 2011).", 14)
note(ws, rr + 2, 1, "Asymmetry: producer's accuracy is much higher for healthy than for diseased. The class means are almost equal, but diseased endmembers are more variable; QDA therefore assigns spectra near the common mean to the tighter healthy class and labels only outlying spectra as diseased (large quantity disagreement = too many 'healthy' predictions).", 14)
rB = rr + 5
put(ws, rB, 1, "B. Error matrices with live formulas — spectrum level (all schemes; CV1, CV2 summed over 10 repetitions)", font=F_B)
for i, k in enumerate(CVK):
    for j, t2 in enumerate(T2):
        m = Vt(t2, k)["acc"]["spectra"]
        acc_block(ws, rB + 2 + i * 16, 1 + j * 11, f"{t2} + QDA — {k}: {CVN[k]} ({int(m['cm'].sum())} predictions)", m["cm"], m)
rP = rB + 2 + len(CVK) * 16 + 1
put(ws, rP, 1, "C. Error matrices — plot level (majority vote of each plot's spectra)", font=F_B)
for i, k in enumerate(("CV2", "CV3")):
    for j, t2 in enumerate(T2):
        m = Vt(t2, k)["acc"]["plots"]
        acc_block(ws, rP + 2 + i * 16, 1 + j * 11, f"{t2} + QDA — {k}, plots ({int(m['cm'].sum())} plot predictions)", m["cm"], m)

# ============================================================ 14 PERMUTATION
ws = sheet(S["perm"], "Step 13 — permutation test: plot labels shuffled (11 healthy / 36 diseased kept), CV2 pipeline re-run (1 repetition)",
           "p = (1 + number of shuffles with BA ≥ observed) / (shuffles + 1) (Ojala & Garriga 2010).", "Shows whether the accuracy is better than chance when plots, not spectra, are exchanged.")
for i, t2 in enumerate(T2):
    pmn = R["perm"][t2]; c0 = 1 + 4 * i; nn = len(pmn["null"])
    put(ws, 5, c0, f"{t2} + QDA", font=F_B)
    put(ws, 6, c0, "Observed BA (CV2 rep. 1)"); put(ws, 6, c0 + 1, float(pmn["observed"]), fmt="0.0%")
    put(ws, 7, c0, "Shuffles"); put(ws, 7, c0 + 1, f"=COUNT({CL(c0+1)}13:{CL(c0+1)}{12+nn})")
    put(ws, 8, c0, "Null mean"); put(ws, 8, c0 + 1, f"=AVERAGE({CL(c0+1)}13:{CL(c0+1)}{12+nn})", fmt="0.0%")
    put(ws, 9, c0, "Null max"); put(ws, 9, c0 + 1, f"=MAX({CL(c0+1)}13:{CL(c0+1)}{12+nn})", fmt="0.0%")
    put(ws, 10, c0, "p-value (live)"); put(ws, 10, c0 + 1, f'=(1+COUNTIF({CL(c0+1)}13:{CL(c0+1)}{12+nn},">="&{CL(c0+1)}6))/({CL(c0+1)}7+1)', fmt="0.000", fill=FILL_K)
    LIVE.append(("Validation", f"permutation p ({t2}): Excel − Python", f"=ABS({q(S['perm'])}!{CL(c0+1)}10-{float(pmn['p'])})", 1e-9))
    header(ws, 12, c0, ["Shuffle", "BA"])
    for k, v in enumerate(pmn["null"]): put(ws, 13 + k, c0, k + 1); put(ws, 13 + k, c0 + 1, float(v), fmt="0.0%")
    ws.column_dimensions[CL(c0)].width = 26

# ============================================================ 15 SENSITIVITY
SE = R["SENS"]
ws = sheet(S["sens"], "Step 14 — sensitivity analysis: band removal of Das et al. (bands ≥ 2350 nm removed)",
           f"Das et al. removed 1350–1430, 1800–1950 and 2350–2500 nm (water absorption / noise). The first two ranges are already absent from the image; here the {P - SE['bands_used']} bands ≥ 2350 nm are also removed and Tiers 1–4 are repeated.",
           "Checks that the conclusions do not depend on the noisy end of the sensor, where most negative reflectance values occur.")
header(ws, 5, 1, ["Tier 2", "Bands used", "ANOVA-significant", "Selected bands", "Selected wavelengths (nm)", "J–M set", "CV1 OA", "CV1 BA", "CV2 BA", "CV2 BA SD", "CV2 plot BA"],
       [10, 10, 12, 10, 70, 10, 10, 10, 10, 10, 10])
for i, t2 in enumerate(T2):
    s_ = SE[t2]; rr = 6 + i
    vals = [t2, SE["bands_used"], SE["sig"], len(s_["bands"]), ", ".join(f"{b:.0f}" for b in s_["bands"]), s_["JM"], s_["CV1_OA"], s_["CV1_BA"], s_["CV2_BA"][0], s_["CV2_BA"][1], s_["CV2_plotBA"]]
    fm = [None, None, None, None, None, "0.000", "0.0%", "0.0%", "0.0%", "0.0%", "0.0%"]
    for j, (v, f_) in enumerate(zip(vals, fm)): put(ws, rr, 1 + j, v, fmt=f_)
header(ws, 9, 1, ["Tier 2", "All bands: J–M set", "CV1 OA", "CV2 BA"])
for i, t2 in enumerate(T2):
    rr = 10 + i; put(ws, rr, 1, t2); put(ws, rr, 2, float(full[t2]["JM"]), fmt="0.000")
    put(ws, rr, 3, float(np.mean([m["OA"] for m in Vt(t2, "CV1")["reps"]])), fmt="0.0%"); put(ws, rr, 4, float(np.mean([m["BA"] for m in Vt(t2, "CV2")["reps"]])), fmt="0.0%")

# ============================================================ 16 COMPARISON
ws = sheet(S["cmp"], "Step 15 — comparison: CART vs Random Forest in Tier 2", "Spectrum-level balanced accuracy unless stated; live links to the step sheets.",
           "Answers the requested comparison under every validation scheme.")
header(ws, 4, 1, ["Measure", "CART", "RF", "RF − CART"], [62, 14, 14, 12])
rows_ = [("Bands selected (Tier 2)", len(full["CART"]["bands"]), len(full["RF"]["bands"]), "0"),
         ("J–M of the set (Tier 3)", f"={q(S['cart'])}!E{6+len(full['CART']['bands'])}", f"={q(S['rf'])}!E{6+len(full['RF']['bands'])}", "0.000"),
         ("CV1 (Das et al.) overall accuracy, mean of 10 repetitions", f"={MEAN_CV1['CART'].replace('!C', '!D')}", f"={MEAN_CV1['RF'].replace('!C', '!D')}", "0.0%"),
         ("CV1 (Das et al.) balanced accuracy, mean", f"={MEAN_CV1['CART']}", f"={MEAN_CV1['RF']}", "0.0%"),
         ("CV2 plot-grouped balanced accuracy, mean (main result)", f"={MEAN_CV2['CART']}", f"={MEAN_CV2['RF']}", "0.0%"),
         ("CV3 leave-one-plot-out plot-level BA", f"={q(S['cv3'])}!H{RE+5}", f"={q(S['cv3'])}!I{RE+5}", "0.0%")]
for k in ("CV4", "CV5", "CV6"):
    rows_.append((f"{k} {CVN[k]}", f"={q(S['cvd'])}!B{CVD_ROWS[(k, 'CART')]}", f"={q(S['cvd'])}!B{CVD_ROWS[(k, 'RF')]}", "0.0%"))
rows_.append(("Permutation p (CV2)", f"={q(S['perm'])}!B10", f"={q(S['perm'])}!F10", "0.000"))
rows_.append(("Restricted block permutation p", f"={q(S['nc'])}!B25", f"={q(S['nc'])}!C25", "0.00"))
rows_.append(("Sensitivity (no bands ≥ 2350 nm): CV2 BA", f"={q(S['sens'])}!I6", f"={q(S['sens'])}!I7", "0.0%"))
for i, (a, b, c, fm) in enumerate(rows_):
    rr = 5 + i; put(ws, rr, 1, a); put(ws, rr, 2, b, fmt=fm); put(ws, rr, 3, c, fmt=fm); put(ws, rr, 4, f"=C{rr}-B{rr}", fmt=fm)
put(ws, 6 + len(rows_), 1, "Chance level of balanced accuracy", bold=True); put(ws, 6 + len(rows_), 2, 0.5, fmt="0.0%")

# ============================================================ 17 REFERENCES
ws = sheet(S["refs"], "References — what each is used for and how the citation was checked", "Each citation was checked against the journal, publisher, repository or library record (October 2026).")
header(ws, 4, 1, ["Short citation", "Full reference", "Used for", "Checked against"], [26, 90, 60, 36])
for i, (a, b, c, d_) in enumerate(REFS):
    for j, v in enumerate((a, b, c, d_)): put(ws, 5 + i, 1 + j, v, wrap=True, bold=(j == 0))
    ws.row_dimensions[5 + i].height = 42

# ============================================================ 18 CHECKS
ws = sheet(S["chk"], "Cross-checks of every step", "Part A: Python checks during the analysis. Part B: live Excel formulas compared with the Python results.")
for c, w in zip("ABCDE", [14, 70, 30, 46, 9]): ws.column_dimensions[c].width = w
header(ws, 4, 1, ["Step", "Check", "Expected", "Obtained", "Result"])
ck = R["checks"]
for i, rw in enumerate(ck.itertuples(index=False)):
    rr = 5 + i
    put(ws, rr, 1, rw.step); put(ws, rr, 2, rw.check, wrap=True); put(ws, rr, 3, rw.expected); put(ws, rr, 4, rw.obtained, wrap=True)
    put(ws, rr, 5, rw.result, font=Font(name=FONT, size=10, bold=True, color="008000" if rw.result == "PASS" else "C00000"))
LIVE.append(("Accuracy", "max |accuracy measure (Excel formula) − Python| over all error matrices", "=MAX(" + ",".join(ACC_DELTA) + ")", 1e-9))
rb = 5 + len(ck) + 2
put(ws, rb, 1, "Part B — live Excel checks", font=F_B); header(ws, rb + 1, 1, ["Step", "Check", "Value", "Tolerance", "Result"])
for i, (a, b, f, tol) in enumerate(LIVE):
    rr = rb + 2 + i
    put(ws, rr, 1, a); put(ws, rr, 2, b); put(ws, rr, 3, f, fmt="0.0E+00"); put(ws, rr, 4, tol, fmt="0.0E+00")
    put(ws, rr, 5, f'=IF(C{rr}<=D{rr},"PASS","FAIL")', font=Font(name=FONT, size=10, bold=True))
put(ws, rb + 3 + len(LIVE), 1, "All checks", font=F_B)
put(ws, rb + 3 + len(LIVE), 5, f'=IF(AND(COUNTIF(E5:E{4+len(ck)},"FAIL")=0,COUNTIF(E{rb+2}:E{rb+1+len(LIVE)},"FAIL")=0),"ALL PASS","CHECK")', fill=FILL_K, font=F_B)
wb.save(OUT); print("saved", OUT, "sheets", len(wb.sheetnames), "live checks", len(LIVE), "error matrices", len(ACC_DELTA))
