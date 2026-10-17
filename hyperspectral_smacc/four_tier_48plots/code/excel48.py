"""Step-by-step workbook for the 48-plot analysis (reads results/r48.pkl)."""
import pickle, sys
import numpy as np, pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter as CL
from refs48 import REFS
from abbrev48 import ABBR

OUT = sys.argv[1]
R = pickle.load(open("results/r48.pkl", "rb"))
DZ = pickle.load(open("results/d48.pkl", "rb"))          # design-based validation and accuracy assessment (design48.py)
meta, wl, X, y, groups, V, full, STRATS, CFG = R["meta"], R["wl"], R["X"], R["y"], R["groups"], R["V"], R["full"], R["STRATS"], R["CONFIGS"]
N, P = X.shape; nH, nD = int((y == 0).sum()), int((y == 1).sum())
assert all(y[:nH] == 0) and all(y[nH:] == 1)
best = R["best"]
FONT = "Arial"
F_IN, F_FX, F_LINK = Font(name=FONT, size=10, color="0000FF"), Font(name=FONT, size=10, color="000000"), Font(name=FONT, size=10, color="008000")
F_B, F_H, F_T, F_S = Font(name=FONT, size=10, bold=True), Font(name=FONT, size=10, bold=True, color="FFFFFF"), Font(name=FONT, size=14, bold=True, color="1F3864"), Font(name=FONT, size=10, italic=True, color="404040")
FILL_H, FILL_K = PatternFill("solid", fgColor="1F4E5A"), PatternFill("solid", fgColor="FFF2CC")
thin = Side(style="thin", color="BFBFBF"); BOX = Border(left=thin, right=thin, top=thin, bottom=thin)
wb = Workbook(); wb.remove(wb.active)
def q(n): return f"'{n}'"
def sheet(name, title, sub):
    ws = wb.create_sheet(name); ws["A1"] = title; ws["A1"].font = F_T; ws["A2"] = sub; ws["A2"].font = F_S; ws.sheet_view.showGridLines = False; return ws
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
def region(w):
    return "VIS" if w < 700 else "Red-edge" if w < 750 else "NIR" if w < 1350 else "SWIR-1" if w < 1800 else "SWIR-2"
def lab(t2, s): return f"{t2} + QDA · {STRATS[s]}"

S = dict(raw="1_Data", summ="2_Data_Summary", des="3_Design", t1="4_Tier1_ANOVA", imb="5_Imbalance", cart="6_Tier2_CART", rf="7_Tier2_RF",
         jm="8_Tier3_JM", v1="9_Tier4_PaperStyle", v2="10_Valid_PlotGrouped", v3="11_Valid_LOPO", vd="12_Valid_Design",
         nc="13_Negative_Control", acc="14_Accuracy", cmp="15_Comparison", perm="16_Permutation", refs="17_References", chk="18_Cross_Checks")

# ============================================================ README
ws = sheet("README", "Four-tier analysis (Das et al. 2020) of 48-plot SMACC endmembers — CART vs Random Forest in Tier 2, with class-imbalance handling",
           f"{N} endmember spectra (healthy plots 1–12: {nH}; diseased plots 13–48: {nD}) × {P} reflectance bands (399–2398 nm). Every endmember and every band is used; spectra are not averaged.")
ws.column_dimensions["A"].width = 6; ws.column_dimensions["B"].width = 26; ws.column_dimensions["C"].width = 120
header(ws, 4, 1, ["Step", "Sheet", "Content"])
rows = [("–", "Abbreviations", "Every abbreviation used in the workbook and the slides, with its meaning."),
        ("0", S["raw"], "All 1417 endmember spectra exactly as in SMACC_EM_spectra_48plots_rearranged.xlsx (all 483 bands), with plot, EM number and class; sorted healthy first. All live formulas read from here."),
        ("1", S["summ"], "Spectra per plot and per class (COUNTIFS), imbalance ratio, negative-reflectance counts."),
        ("1b", S["des"], "Treatment design (treatment_detail.xlsx): control block C (plots 1–12) and inoculated blocks R3, R2, R1; each block = 3 varieties × 4 inoculation dates."),
        ("2", S["t1"], "TIER 1 — one-way ANOVA at every band with live Excel formulas (means, SDs, sums of squares, F, p); Tukey HSD, Welch, Levene, FDR, Bonferroni, Cohen's d, single-band J–M; ANOVA of the 48 plot means (pseudo-replication check)."),
        ("3", S["imb"], "Class imbalance (1 : 2.96) and the four strategies compared: none, class weighting, random under-sampling, SMOTE — applied to training data only."),
        ("4", S["cart"], "TIER 2 (CART, rpart settings) — bands selected under each imbalance strategy; class-weighted tree structure."),
        ("5", S["rf"], "TIER 2 alternative (Random Forest) — importance ranking, redundancy filter |r| < 0.95, same number of bands as CART."),
        ("6", S["jm"], "TIER 3 — Jeffries–Matusita distance of every selected set; single-band J–M of EACH band selected by CART and by RF (every strategy; CART in wavelength order, RF in importance order); live matrix J–M for the best CART and RF sets."),
        ("7", S["v1"], "TIER 4 — QDA, paper-style random 10-fold CV (bands chosen on all data; optimistic, for comparison with Das et al.)."),
        ("8", S["v2"], "VALIDATION (main) — plot-grouped nested 4-fold CV × 10 repetitions: every step (ANOVA, CART/RF, re-balancing, QDA) redone on training plots only; spectrum- and plot-level metrics."),
        ("9", S["v3"], "VALIDATION — leave-one-plot-out (48 folds), nested; prediction for every plot."),
        ("9b", S["vd"], "VALIDATION using the treatment design — leave-one-treatment-combination-out (12 folds), leave-one-variety-out (3), leave-one-inoculation-date-out (4); all nested."),
        ("9c", S["nc"], "NEGATIVE CONTROL — block vs block (inoculated vs inoculated) next to control vs inoculated; restricted (block-level) permutation; detection by block, variety and date."),
        ("9d", S["acc"], "ACCURACY ASSESSMENT — error matrices (live formulas) with producer's/user's/overall accuracy, kappa, balanced accuracy, F1, MCC, quantity and allocation disagreement, and 95% CIs by plot (cluster) bootstrap."),
        ("10", S["cmp"], "Comparison of all configurations under all six validation schemes, plus the RF classifier benchmark and the restricted permutation p."),
        ("11", S["perm"], "Permutation test: plot labels shuffled (12 healthy / 36 diseased kept), full pipeline re-run."),
        ("12", S["refs"], "References: what each method is used for and how the citation was checked."),
        ("13", S["chk"], "Cross-checks (Python and live Excel) with PASS/FAIL.")]
for i, (a, b, c) in enumerate(rows):
    put(ws, 5 + i, 1, a); put(ws, 5 + i, 2, b, font=F_B); put(ws, 5 + i, 3, c, wrap=True); ws.row_dimensions[5 + i].height = 30
r = 6 + len(rows)
put(ws, r, 1, "Colour code", font=F_B)
put(ws, r + 1, 2, "Blue", font=F_IN); put(ws, r + 1, 3, "Input data, or results computed in Python (scipy, statsmodels, scikit-learn, imbalanced-learn)")
put(ws, r + 2, 2, "Black", font=F_FX); put(ws, r + 2, 3, "Live Excel formulas"); put(ws, r + 3, 2, "Green", font=F_LINK); put(ws, r + 3, 3, "Live formulas linking to another sheet")
put(ws, r + 4, 2, "Yellow fill", fill=FILL_K); put(ws, r + 4, 3, "Key results")
put(ws, r + 6, 1, "Software", font=F_B); put(ws, r + 7, 3, "Python 3.13; numpy; pandas; scipy 1.18; statsmodels 0.15; scikit-learn 1.9; imbalanced-learn 0.14. CART pruning re-implemented to match R rpart's cp. Random seed 42.", wrap=True)

# ============================================================ ABBREVIATIONS
ws = sheet("Abbreviations", "Abbreviations used in this workbook and in the slide deck", "Note: V1–V3 are varieties; the validation schemes are called CV1–CV6. 'D' alone = diseased, D1–D4 = inoculation dates; 'R' + wavelength = reflectance, R1–R3 = inoculated blocks.")
header(ws, 4, 1, ["Abbreviation", "Meaning"], [22, 110])
for i, (a_, m_) in enumerate(ABBR):
    put(ws, 5 + i, 1, a_, bold=True); put(ws, 5 + i, 2, m_)

# ============================================================ 1 DATA
ws = sheet(S["raw"], "Step 0 — All endmember spectra (one row per endmember)", f"Rows 5–{4+nH}: healthy (plots 1–12); rows {5+nH}–{4+N}: diseased (plots 13–48). Columns E onward: reflectance at each of the {P} bands.")
header(ws, 4, 1, ["plot", "EM", "spectrum_id", "class"] + [f"{w:.3f}" for w in wl])
for i in range(N):
    put(ws, 5 + i, 1, int(meta["plot"][i])); put(ws, 5 + i, 2, meta.em[i]); put(ws, 5 + i, 3, meta.spectrum_id[i]); put(ws, 5 + i, 4, meta["class"][i])
    for j in range(P): ws.cell(5 + i, 5 + j, float(X[i, j])).font = F_IN
ws.freeze_panes = "E5"
H0, H1, D0, D1 = 5, 4 + nH, 5 + nH, 4 + N
def col(j): return CL(5 + j)
def rH(j): return f"{q(S['raw'])}!{col(j)}${H0}:{col(j)}${H1}"
def rD(j): return f"{q(S['raw'])}!{col(j)}${D0}:{col(j)}${D1}"
def rA(j): return f"{q(S['raw'])}!{col(j)}${H0}:{col(j)}${D1}"

# ============================================================ 2 SUMMARY
ws = sheet(S["summ"], "Step 1 — Data summary", "Counts are live COUNTIFS on sheet 1_Data. No spectrum and no band is removed.")
header(ws, 4, 1, ["Plot", "Class", "Spectra (live)"], [8, 10, 13])
for k in range(1, 49):
    rr = 4 + k; put(ws, rr, 1, k); put(ws, rr, 2, "healthy" if k <= 12 else "diseased")
    put(ws, rr, 3, f"=COUNTIF({q(S['raw'])}!$A$5:$A${D1},A{rr})")
put(ws, 53, 1, "Total", bold=True); put(ws, 53, 3, "=SUM(C5:C52)", fill=FILL_K)
header(ws, 4, 5, ["Class", "Plots", "Spectra", "Share"], [12, 8, 10, 10])
put(ws, 5, 5, "healthy"); put(ws, 5, 6, '=COUNTIF(B5:B52,"healthy")'); put(ws, 5, 7, '=SUMIF(B5:B52,"healthy",C5:C52)'); put(ws, 5, 8, "=G5/G7", fmt="0.0%")
put(ws, 6, 5, "diseased"); put(ws, 6, 6, '=COUNTIF(B5:B52,"diseased")'); put(ws, 6, 7, '=SUMIF(B5:B52,"diseased",C5:C52)'); put(ws, 6, 8, "=G6/G7", fmt="0.0%")
put(ws, 7, 5, "Total", bold=True); put(ws, 7, 7, "=G5+G6")
put(ws, 9, 5, "Imbalance ratio (diseased : healthy)", bold=True); put(ws, 9, 8, "=G6/G5", fmt='"1 : "0.00', fill=FILL_K)
put(ws, 10, 5, "Bands", bold=True); put(ws, 10, 8, P)
put(ws, 11, 5, "Spectra with any negative reflectance (healthy / diseased)", bold=True); put(ws, 11, 8, f"{R['neg_spectra']['healthy']} / {R['neg_spectra']['diseased']}")
ng = R["neg"]
header(ws, 13, 5, ["Wavelength (nm)", "Healthy spectra < 0", "Diseased spectra < 0"])
for i in range(P):
    put(ws, 14 + i, 5, float(wl[i]), fmt="0.000"); put(ws, 14 + i, 6, int(ng.neg_healthy[i])); put(ws, 14 + i, 7, int(ng.neg_diseased[i]))

# ============================================================ 2b DESIGN
td = DZ["design"]
ws = sheet(S["des"], "Treatment design (from treatment_detail.xlsx)", "Block C = control (healthy, plots 1–12); R3, R2, R1 = inoculated (diseased). Each block contains every variety (V1–V3) × inoculation date (D1–D4, days after sowing) once.")
header(ws, 4, 1, ["Plot", "Block", "Variety", "Inoculation (DAS code)", "Class", "Spectra (live)", "East (m)", "North (m)"], [7, 8, 9, 14, 10, 10, 10, 10])
for i, k in enumerate(td.index):
    rr = 5 + i
    put(ws, rr, 1, int(k)); put(ws, rr, 2, td.block[k]); put(ws, rr, 3, td.variety[k]); put(ws, rr, 4, td.date[k]); put(ws, rr, 5, td["class"][k])
    put(ws, rr, 6, f"=COUNTIF({q(S['raw'])}!$A$5:$A${4+N},A{rr})"); put(ws, rr, 7, float(td.x_m[k]), fmt="0.0"); put(ws, rr, 8, float(td.y_m[k]), fmt="0.0")
put(ws, 4, 10, "Check: plots per block × variety × date (live COUNTIFS; every cell must be 1)", font=F_B)
DATES, VARS, BLOCKS = sorted(td.date.unique()), sorted(td.variety.unique()), ["C", "R3", "R2", "R1"]
for bi, b in enumerate(BLOCKS):
    r0 = 5 + bi * 6
    put(ws, r0, 10, f"Block {b}", bold=True)
    for j, d_ in enumerate(DATES): put(ws, r0, 11 + j, d_, bold=True)
    for i, v in enumerate(VARS):
        put(ws, r0 + 1 + i, 10, v, bold=True)
        for j, d_ in enumerate(DATES):
            put(ws, r0 + 1 + i, 11 + j, f'=COUNTIFS($B$5:$B$52,"{b}",$C$5:$C$52,"{v}",$D$5:$D$52,"{d_}")')
DES_CHECK = f"{q(S['des'])}!$K$6:$N$27"
put(ws, 30, 10, "All cells = 1?", bold=True); put(ws, 30, 11, f'=IF(AND(COUNTIF(K6:N8,1)=12,COUNTIF(K12:N14,1)=12,COUNTIF(K18:N20,1)=12,COUNTIF(K24:N26,1)=12),"yes","no")', fill=FILL_K)
put(ws, 32, 10, "Block centres (m) and distances", font=F_B)
header(ws, 33, 10, ["Block", "East (live)", "North (live)"] + [f"to {b}" for b in BLOCKS])
for i, b in enumerate(BLOCKS):
    rr = 34 + i; put(ws, rr, 10, b, bold=True)
    put(ws, rr, 11, f'=AVERAGEIF($B$5:$B$52,J{rr},$G$5:$G$52)', fmt="0.0"); put(ws, rr, 12, f'=AVERAGEIF($B$5:$B$52,J{rr},$H$5:$H$52)', fmt="0.0")
    for j in range(4): put(ws, rr, 13 + j, f"=SQRT((K{rr}-K{34+j})^2+(L{rr}-L{34+j})^2)", fmt="0.0")
note(ws, 39, 10, "Consequence for validation: all healthy plots form ONE contiguous block at the west end, so 'healthy vs diseased' is confounded with 'block C vs blocks R1–R3' (spatially segregated treatments; Hurlbert 1984). Sheets 12 and 13 test how much of the separation can be explained by block/location.", 8)

# ============================================================ 3 TIER 1
ws = sheet(S["t1"], "Tier 1 — One-way ANOVA at every band (healthy vs diseased)", "Columns C–R are live formulas on sheet 1_Data; S onward are Python results (and cross-checks). Unequal group sizes are allowed in one-way ANOVA; Welch's test is shown because variances may differ.")
t1 = R["tier1"]; TR0 = 13
hdr = ["Band #", "Wavelength (nm)", "n healthy", "n diseased", "Mean healthy", "Mean diseased", "SD healthy", "SD diseased", "SS between", "SS within",
       "df between", "df within", "F", "p", "Significant (p<0.05)", "Cohen's d (D−H)", "Bhattacharyya B (1 band)", "JM 0–2 (1 band)",
       "Tukey HSD p", "Welch p", "Levene p", "FDR q", "Bonferroni p", "F plot means (n=48)", "p plot means", "F (Python)", "|ΔF|/F", "p (Python)", "|Δp|"]
header(ws, TR0, 1, hdr, [7, 11, 8, 8, 10, 10, 10, 10, 11, 11, 7, 7, 10, 11, 10, 10, 11, 10, 11, 11, 11, 11, 11, 11, 11, 10, 10, 11, 10])
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
TL = TR0 + P; ws.freeze_panes = f"C{TR0+1}"
B_, rng = f"$B${TR0+1}:$B${TL}", lambda c: f"${c}${TR0+1}:${c}${TL}"
put(ws, 4, 1, "Summary", font=F_B)
items = [("Bands tested", f"=COUNT({rng('B')})"), ("Significant, p < 0.05 (paper criterion)", f'=COUNTIF({rng("O")},"yes")'),
         ("Significant after FDR", f'=COUNTIF({rng("V")},"<0.05")'), ("Significant after Bonferroni", f'=COUNTIF({rng("W")},"<0.05")'),
         ("Significant by Welch test", f'=COUNTIF({rng("T")},"<0.05")'), ("Significant using the 48 plot means", f'=COUNTIF({rng("Y")},"<0.05")'),
         ("Bands with |d| ≥ 0.8", f'=COUNTIF({rng("P")},">=0.8")+COUNTIF({rng("P")},"<=-0.8")')]
for i, (a, f) in enumerate(items):
    put(ws, 5 + i, 1, a); put(ws, 5 + i, 5, f, fill=FILL_K if i in (1, 5) else None)
put(ws, 4, 8, "By spectral region", font=F_B)
header(ws, 5, 8, ["Region", "From", "To", "Bands", "p<0.05", "FDR", "Plot means p<0.05"])
for i, (nm, lo, hi) in enumerate([("VIS", 0, 700), ("Red-edge", 700, 750), ("NIR", 750, 1350), ("SWIR-1", 1350, 1800), ("SWIR-2", 1800, 3000)]):
    rr = 6 + i; put(ws, rr, 8, nm); put(ws, rr, 9, lo); put(ws, rr, 10, hi)
    put(ws, rr, 11, f'=COUNTIFS({B_},">="&I{rr},{B_},"<"&J{rr})'); put(ws, rr, 12, f'=COUNTIFS({B_},">="&I{rr},{B_},"<"&J{rr},{rng("O")},"yes")')
    put(ws, rr, 13, f'=COUNTIFS({B_},">="&I{rr},{B_},"<"&J{rr},{rng("V")},"<0.05")'); put(ws, rr, 14, f'=COUNTIFS({B_},">="&I{rr},{B_},"<"&J{rr},{rng("Y")},"<0.05")')
note(ws, 12, 8, "Spectra from the same plot are not independent (Hurlbert 1984). The plot-mean ANOVA (n = 48) is the conservative check; Tier 2 uses the paper's spectrum-level criterion.", 8)

# ============================================================ 4 IMBALANCE
ws = sheet(S["imb"], "Class imbalance and how it is handled", "All four strategies are applied to the TRAINING data only, inside every cross-validation fold (Santos et al. 2018). Test spectra are never re-sampled.")
for c, w in zip("ABCDEF", [30, 16, 16, 16, 60, 30]): ws.column_dimensions[c].width = w
put(ws, 4, 1, "Healthy spectra"); put(ws, 4, 2, f"={q(S['summ'])}!G5"); put(ws, 5, 1, "Diseased spectra"); put(ws, 5, 2, f"={q(S['summ'])}!G6")
put(ws, 6, 1, "Imbalance ratio"); put(ws, 6, 2, "=B5/B4", fmt='"1 : "0.00', fill=FILL_K)
put(ws, 7, 1, "Class weight healthy = N / (2 · n_H)"); put(ws, 7, 2, "=(B4+B5)/(2*B4)", fmt="0.000")
put(ws, 8, 1, "Class weight diseased = N / (2 · n_D)"); put(ws, 8, 2, "=(B4+B5)/(2*B5)", fmt="0.000")
put(ws, 9, 1, "Check: weighted totals equal"); put(ws, 9, 2, '=IF(ABS(B4*B7-B5*B8)<1E-9,"yes","no")')
header(ws, 11, 1, ["Strategy", "Healthy (all data)", "Diseased (all data)", "Ratio", "What it does", "Reference"])
desc = {"S0": ("Baseline: classifiers learn from the imbalanced data; QDA uses empirical priors.", "—"),
        "S1": ("Cost-sensitive: each class gets total weight 0.5 (rpart 'prior', RF class_weight='balanced', QDA equal priors).", "Breiman et al. 1984; Chen et al. 2004; He & Garcia 2009"),
        "S2": ("Random under-sampling: diseased training spectra randomly reduced to the number of healthy ones.", "He & Garcia 2009; Chen et al. 2004 (balanced RF)"),
        "S3": ("SMOTE: synthetic healthy spectra interpolated between each healthy spectrum and its 5 nearest healthy neighbours.", "Chawla et al. 2002; Douzas et al. 2019; Cuenca-Romero et al. 2024")}
for i, s in enumerate(STRATS):
    rr = 12 + i; nt = full[("CART", s)]["n_train"]
    put(ws, rr, 1, STRATS[s], bold=True); put(ws, rr, 2, nt[0]); put(ws, rr, 3, nt[1]); put(ws, rr, 4, f"=C{rr}/B{rr}", fmt='"1 : "0.00')
    put(ws, rr, 5, desc[s][0], wrap=True); put(ws, rr, 6, desc[s][1], wrap=True); ws.row_dimensions[rr].height = 30
note(ws, 17, 1, "Accuracy measures used for imbalanced data: balanced accuracy (Brodersen et al. 2010), Matthews correlation coefficient (Chicco & Jurman 2020), kappa (Cohen 1960), F1 per class and ROC-AUC (He & Garcia 2009). Overall accuracy alone is misleading: predicting every spectrum 'diseased' already gives 74.7%.", 6)
put(ws, 19, 1, "Accuracy of 'always diseased'"); put(ws, 19, 2, "=B5/(B4+B5)", fmt="0.0%"); put(ws, 20, 1, "Balanced accuracy of 'always diseased'"); put(ws, 20, 2, 0.5, fmt="0.0%")

# ============================================================ 5 CART / 6 RF
for key, t2, title in (("cart", "CART", "Tier 2 — CART (rpart-equivalent: Gini, minsplit 20, minbucket 7, cp 0.01) on the ANOVA-significant bands"),
                       ("rf", "RF", "Tier 2 alternative — Random Forest band selection (500 trees, mtry = √p; importance = mean decrease in Gini; |r| < 0.95 filter; as many bands as CART)")):
    ws = sheet(S[key], title, "Bands selected on ALL data for each imbalance strategy (for reporting and J–M). In the validation sheets the selection is repeated inside every training fold.")
    header(ws, 4, 1, ["Strategy", "Bands", "J–M (0–2)", "Selected bands (nm)"], [32, 8, 11, 150])
    for i, s in enumerate(STRATS):
        v = full[(t2, s)]; rr = 5 + i
        put(ws, rr, 1, STRATS[s], bold=True); put(ws, rr, 2, len(v["bands"])); put(ws, rr, 3, float(v["JM"]), fmt="0.000")
        put(ws, rr, 4, ", ".join(f"{w:.1f}" for w in sorted(v["wl"])))
    put(ws, 10, 1, "Bands by region (count)", font=F_B)
    header(ws, 11, 1, ["Strategy", "VIS", "Red-edge", "NIR", "SWIR-1", "SWIR-2"])
    for i, s in enumerate(STRATS):
        rr = 12 + i; put(ws, rr, 1, STRATS[s])
        regs = [region(w) for w in full[(t2, s)]["wl"]]
        for j, nm in enumerate(["VIS", "Red-edge", "NIR", "SWIR-1", "SWIR-2"]): put(ws, rr, 2 + j, regs.count(nm))
    if t2 == "CART":
        tr = R["tree_S1"]; L_, R_, f_, th, cnt, fidx, pr = tr["L"], tr["Rr"], tr["f"], tr["thr"], tr["counts"], tr["feat_idx"], tr["pr"]
        put(ws, 18, 1, "Class-weighted tree (strategy: class weighting) — nodes, depth-first; counts are class-weighted", font=F_B)
        header(ws, 19, 1, ["Node", "Type", "Split (left branch = true)", "Weighted healthy", "Weighted diseased", "Predicted"])
        rr = 20; st = [(0, 0)]
        while st:
            nd, dd = st.pop()
            leaf = L_[nd] == -1 or pr[nd]
            put(ws, rr, 1, int(nd)); put(ws, rr, 2, ("  " * dd) + ("leaf" if leaf else "split"))
            put(ws, rr, 3, "" if leaf else f"R({wl[fidx[f_[nd]]]:.1f} nm) ≤ {th[nd]:.4f}"); put(ws, rr, 4, float(cnt[nd, 0]), fmt="0.0")
            put(ws, rr, 5, float(cnt[nd, 1]), fmt="0.0"); put(ws, rr, 6, "diseased" if cnt[nd, 1] > cnt[nd, 0] else "healthy"); rr += 1
            if not leaf: st += [(R_[nd], dd + 1), (L_[nd], dd + 1)]
    else:
        imp = full[("RF", "S1")]["importance"].sort_values("importance", ascending=False).head(40)
        put(ws, 18, 1, "Importance ranking, class-weighted RF (top 40 of the significant bands)", font=F_B)
        header(ws, 19, 1, ["Rank", "Band (nm)", "Importance", "Kept?"])
        kept = set(full[("RF", "S1")]["bands"])
        for i, rw in enumerate(imp.itertuples(index=False)):
            put(ws, 20 + i, 1, i + 1); put(ws, 20 + i, 2, float(wl[int(rw.band)]), fmt="0.0"); put(ws, 20 + i, 3, float(rw.importance), fmt="0.0000")
            put(ws, 20 + i, 4, "yes" if int(rw.band) in kept else "skipped (|r| ≥ 0.95 with a kept band)" if i < 60 else "")

# ============================================================ 7 JM
ws = sheet(S["jm"], "Tier 3 — Jeffries–Matusita distance", "JM = 2(1 − e^(−B)) on a 0–2 scale; threshold 1.94 as in Das et al. 2020. Computed on all spectra with their natural class sizes.")
header(ws, 4, 1, ["Configuration", "Bands", "B", "JM 0–2", "√JM", "≥ 1.94?"], [40, 8, 10, 10, 10, 10])
for i, (t2, s) in enumerate(CFG):
    rr = 5 + i; v = full[(t2, s)]
    put(ws, rr, 1, f"{t2} · {STRATS[s]}"); put(ws, rr, 2, len(v["bands"])); put(ws, rr, 3, float(v["B"]), fmt="0.0000")
    put(ws, rr, 4, float(v["JM"]), fmt="0.0000"); put(ws, rr, 5, f"=SQRT(D{rr})", fmt="0.0000"); put(ws, rr, 6, f'=IF(D{rr}>=1.94,"yes","no")')
# single-band JM of EACH band selected by each configuration (live link to the Tier 1 sheet)
T1B, T1R = f"{q(S['t1'])}!$B${TR0+1}:$B${TL}", f"{q(S['t1'])}!$R${TR0+1}:$R${TL}"
KMAX = max(len(v["bands"]) for v in full.values())
put(ws, 15, 1, "J–M distance of each individual band selected in Tier 2 (CART and RF, every imbalance strategy) — CART bands in wavelength order, RF bands in importance order; JM of the single band (live, from sheet 4) and cumulative JM of the first k bands (Python)", font=F_B)
for k_, (t2, s) in enumerate(CFG):
    c0 = 1 + 4 * k_; v = full[(t2, s)]
    put(ws, 16, c0, f"{t2}-{s}", bold=True, fill=FILL_K); put(ws, 16, c0 + 1, STRATS[s])
    header(ws, 17, c0, ["#", "Band (nm)", "JM band (live)", "JM cumul."])
    for i, (b, cu) in enumerate(zip(v["bands"], v["cum"])):
        rr = 18 + i
        put(ws, rr, c0, i + 1); put(ws, rr, c0 + 1, float(wl[b]), fmt="0.000")
        put(ws, rr, c0 + 2, f"=INDEX({T1R},MATCH({CL(c0+1)}{rr},{T1B},0))", fmt="0.0000"); put(ws, rr, c0 + 3, float(cu), fmt="0.0000")
    re_ = 18 + KMAX
    put(ws, re_, c0, "mean", bold=True); put(ws, re_, c0 + 2, f"=AVERAGE({CL(c0+2)}18:{CL(c0+2)}{17+len(v['bands'])})", fmt="0.0000")
    put(ws, re_ + 1, c0, "max", bold=True); put(ws, re_ + 1, c0 + 2, f"=MAX({CL(c0+2)}18:{CL(c0+2)}{17+len(v['bands'])})", fmt="0.0000")
    put(ws, re_ + 2, c0, "set", bold=True); put(ws, re_ + 2, c0 + 2, f"=D{5+k_}", fmt="0.0000", fill=FILL_K)
for k_ in range(len(CFG)): ws.column_dimensions[CL(1 + 4 * k_)].width = max(ws.column_dimensions[CL(1 + 4 * k_)].width or 0, 9)
note(ws, 21 + KMAX, 1, "Every individual band has JM ≤ 0.07 (0–2 scale): no single band separates healthy and diseased endmembers; the set values in row 'set' show how far combining bands raises J–M. 'JM cumul.' = J–M of the first k bands together.", 16)
U0 = 24 + KMAX
# single-band JM of every selected band (union)
union = sorted({b for v in full.values() for b in v["bands"]})
put(ws, U0, 1, f"Single-band J–M of every band selected in any configuration ({len(union)} bands) — live link to sheet 4", font=F_B)
header(ws, U0 + 1, 1, ["Band (nm)", "Region", "JM 0–2 (live)", "JM (Python)", "|Δ|"] + [f"{t2}-{s}" for t2, s in CFG])
for i, b in enumerate(union):
    rr = U0 + 2 + i
    put(ws, rr, 1, float(wl[b]), fmt="0.000"); put(ws, rr, 2, region(wl[b])); put(ws, rr, 3, f"=INDEX({T1R},MATCH(A{rr},{T1B},0))", fmt="0.0000")
    put(ws, rr, 4, float(R["jm_band"][b]), fmt="0.0000"); put(ws, rr, 5, f"=ABS(C{rr}-D{rr})", fmt="0.0E+00")
    for k, (t2, s) in enumerate(CFG): put(ws, rr, 6 + k, "✓" if b in full[(t2, s)]["bands"] else "")
JM_LAST = U0 + 1 + len(union)
put(ws, JM_LAST + 1, 1, "Maximum", bold=True); put(ws, JM_LAST + 1, 3, f"=MAX(C{U0+2}:C{JM_LAST})", fmt="0.0000", fill=FILL_K)
# live matrix JM for the two best configurations
REF = {}
rL = JM_LAST + 4
for t2 in ("CART", "RF"):
    s = best[t2]; bands = sorted(full[(t2, s)]["bands"]); k = len(bands)
    put(ws, rL, 1, f"Live matrix J–M: {t2} · {STRATS[s]} ({k} bands)", font=F_B)
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
    put(ws, rr + 1, 3, float(full[(t2, s)]["B"]), fmt="0.0000"); put(ws, rr + 1, 4, f"=ABS(B{rr+1}-C{rr+1})", fmt="0.0E+00")
    put(ws, rr + 2, 1, "JM (0–2)"); put(ws, rr + 2, 2, f"=2*(1-EXP(-B{rr+1}))", fmt="0.0000", fill=FILL_K); put(ws, rr + 2, 3, float(full[(t2, s)]["JM"]), fmt="0.0000")
    put(ws, rr + 2, 4, f"=ABS(B{rr+2}-C{rr+2})", fmt="0.0E+00"); REF[f"jm_{t2}"] = f"{q(S['jm'])}!D{rr+2}"
    rL = rr + 5

# ============================================================ metric helpers
MKEYS = [("BA", "Balanced acc.", "0.0%"), ("OA", "Overall acc.", "0.0%"), ("kappa", "Kappa", "0.000"), ("MCC", "MCC", "0.000"), ("F1_H", "F1 healthy", "0.000"),
         ("F1_D", "F1 diseased", "0.000"), ("sens_D", "Sensitivity (diseased)", "0.0%"), ("spec_H", "Specificity (healthy)", "0.0%"), ("AUC", "ROC-AUC", "0.000")]
def cm_block(ws, r0, c0, title, cm):
    put(ws, r0, c0, title, font=F_B)
    header(ws, r0 + 1, c0, ["Reference \\ Predicted", "Healthy", "Diseased", "Total", "Producer's acc."])
    for i, nm in enumerate(["Healthy", "Diseased"]):
        r = r0 + 2 + i; put(ws, r, c0, nm, bold=True); put(ws, r, c0 + 1, int(cm[i, 0])); put(ws, r, c0 + 2, int(cm[i, 1]))
        put(ws, r, c0 + 3, f"=SUM({CL(c0+1)}{r}:{CL(c0+2)}{r})"); put(ws, r, c0 + 4, f"={CL(c0+1+i)}{r}/{CL(c0+3)}{r}", fmt="0.0%")
    rt = r0 + 4; put(ws, rt, c0, "Total", bold=True)
    for j in range(3): put(ws, rt, c0 + 1 + j, f"=SUM({CL(c0+1+j)}{r0+2}:{CL(c0+1+j)}{r0+3})")
    put(ws, rt + 1, c0, "User's acc.", bold=True)
    for j in range(2): put(ws, rt + 1, c0 + 1 + j, f"={CL(c0+1+j)}{r0+2+j}/{CL(c0+1+j)}{rt}", fmt="0.0%")
    a, b, c, d, n = f"{CL(c0+1)}{r0+2}", f"{CL(c0+2)}{r0+2}", f"{CL(c0+1)}{r0+3}", f"{CL(c0+2)}{r0+3}", f"{CL(c0+3)}{rt}"
    m = rt + 2
    put(ws, m, c0, "Overall accuracy", bold=True); put(ws, m, c0 + 1, f"=({a}+{d})/{n}", fmt="0.0%")
    put(ws, m + 1, c0, "Balanced accuracy", bold=True); put(ws, m + 1, c0 + 1, f"=({CL(c0+4)}{r0+2}+{CL(c0+4)}{r0+3})/2", fmt="0.0%", fill=FILL_K)
    pe = f"(({a}+{b})*({a}+{c})+({c}+{d})*({b}+{d}))/{n}^2"
    put(ws, m + 2, c0, "Kappa", bold=True); put(ws, m + 2, c0 + 1, f"=(({a}+{d})/{n}-{pe})/(1-{pe})", fmt="0.000")
    put(ws, m + 3, c0, "MCC", bold=True); put(ws, m + 3, c0 + 1, f"=({d}*{a}-{b}*{c})/SQRT(({d}+{b})*({d}+{c})*({a}+{b})*({a}+{c}))", fmt="0.000")
    return {"BA": f"{q(ws.title)}!{CL(c0+1)}{m+1}", "kappa": f"{q(ws.title)}!{CL(c0+1)}{m+2}", "MCC": f"{q(ws.title)}!{CL(c0+1)}{m+3}", "N": f"{q(ws.title)}!{n}"}
def summary_table(ws, r0, getter, title, extra_cols=()):
    put(ws, r0, 1, title, font=F_B)
    header(ws, r0 + 1, 1, ["Configuration"] + [m[1] for m in MKEYS] + [e[0] for e in extra_cols], [40] + [12] * (len(MKEYS) + len(extra_cols)))
    for i, (t2, s) in enumerate(CFG):
        rr = r0 + 2 + i; put(ws, rr, 1, f"{t2} · {STRATS[s]}", bold=(s == best[t2]))
        vals = getter(t2, s)
        for j, (k, _, fmt) in enumerate(MKEYS):
            v = float(vals.get(k, np.nan)); put(ws, rr, 2 + j, "—" if np.isnan(v) else v, fmt=fmt)
        for j, e in enumerate(extra_cols): put(ws, rr, 2 + len(MKEYS) + j, float(e[1](t2, s)), fmt=e[2])
    return r0 + 2 + len(CFG)
def mean_of(lst, k): return float(np.mean([m[k] for m in lst if k in m]))

# ============================================================ 8 CV1
ws = sheet(S["v1"], "Tier 4 — QDA with paper-style random 10-fold CV (CV1; 5 repetitions)", "Bands chosen on all data (as in Das et al.); folds random over spectra; re-balancing on training folds only. Spectra of one plot fall on both sides of a split, so these numbers are optimistic.")
end = summary_table(ws, 4, lambda t2, s: {k: mean_of(V[(t2, s)]["v1"], k) for k, _, _ in MKEYS}, "Mean over 5 repetitions")
REF["v1"] = {}
for i, t2 in enumerate(("CART", "RF")):
    REF["v1"][t2] = cm_block(ws, end + 2, 1 + 7 * i, f"{lab(t2, best[t2])} — repetition 1", V[(t2, best[t2])]["v1"][0]["cm"])
    put(ws, end + 14, 1 + 7 * i, "Python BA (rep. 1)"); put(ws, end + 14, 2 + 7 * i, float(V[(t2, best[t2])]["v1"][0]["BA"]), fmt="0.0%")
    REF["v1"][t2]["py"] = f"{q(S['v1'])}!{CL(2+7*i)}{end+14}"

# ============================================================ 9 CV2
ws = sheet(S["v2"], "Validation (main, CV2) — plot-grouped, nested 4-fold CV × 10 repetitions", "Each fold: 3 healthy + 9 diseased plots held out; ANOVA, CART/RF selection, re-balancing and QDA fitted on the other 36 plots only (Ambroise & McLachlan 2002; Roberts et al. 2017).")
end = summary_table(ws, 4, lambda t2, s: {k: mean_of(V[(t2, s)]["v2"], k) for k, _, _ in MKEYS}, "Spectrum level — mean over 10 repetitions",
                    extra_cols=[("SD of balanced acc.", lambda t2, s: np.std([m["BA"] for m in V[(t2, s)]["v2"]], ddof=1), "0.0%")])
end2 = summary_table(ws, end + 2, lambda t2, s: {k: mean_of([m["plot"] for m in V[(t2, s)]["v2"]], k) for k, _, _ in MKEYS if k != "AUC"},
                     "Plot level (majority vote of each held-out plot's spectra) — mean over 10 repetitions")
REF["v2"] = {}
for i, t2 in enumerate(("CART", "RF")):
    REF["v2"][t2] = cm_block(ws, end2 + 2, 1 + 7 * i, f"{lab(t2, best[t2])} — repetition 1 (spectra)", V[(t2, best[t2])]["v2"][0]["cm"])
    put(ws, end2 + 14, 1 + 7 * i, "Python BA (rep. 1)"); put(ws, end2 + 14, 2 + 7 * i, float(V[(t2, best[t2])]["v2"][0]["BA"]), fmt="0.0%")
    REF["v2"][t2]["py"] = f"{q(S['v2'])}!{CL(2+7*i)}{end2+14}"
r0 = end2 + 17
put(ws, r0, 1, "Balanced accuracy of every repetition", font=F_B)
header(ws, r0 + 1, 1, ["Configuration"] + [f"Rep {k+1}" for k in range(len(V[CFG[0]]["v2"]))] + ["Mean (live)", "SD (live)"])
for i, (t2, s) in enumerate(CFG):
    rr = r0 + 2 + i; put(ws, rr, 1, f"{t2} · {STRATS[s]}")
    reps = V[(t2, s)]["v2"]
    for k, m in enumerate(reps): put(ws, rr, 2 + k, float(m["BA"]), fmt="0.0%")
    put(ws, rr, 2 + len(reps), f"=AVERAGE(B{rr}:{CL(1+len(reps))}{rr})", fmt="0.0%"); put(ws, rr, 3 + len(reps), f"=STDEV(B{rr}:{CL(1+len(reps))}{rr})", fmt="0.0%")
bm = R["bench_rf_v2"]
rr = r0 + 3 + len(CFG)
put(ws, rr, 1, "Benchmark: RF classifier on all 483 bands (class-weighted), same folds", font=F_B)
for j, (k, nm, fmt) in enumerate(MKEYS): put(ws, rr + 1, 2 + j, nm, bold=True); put(ws, rr + 2, 2 + j, mean_of(bm, k), fmt=fmt)
put(ws, rr + 2, 1, "spectrum level"); put(ws, rr + 3, 1, "plot level")
for j, (k, nm, fmt) in enumerate(MKEYS):
    if k != "AUC": put(ws, rr + 3, 2 + j, mean_of([m["plot"] for m in bm], k), fmt=fmt)

# ============================================================ 10 CV3 LOPO
ws = sheet(S["v3"], "Validation (CV3) — leave-one-plot-out (48 folds, nested)", "Each plot is predicted by a model trained on the other 47 plots. Plot label = majority of its spectra.")
end = summary_table(ws, 4, lambda t2, s: {k: V[(t2, s)]["v3"].get(k, np.nan) for k, _, _ in MKEYS}, "Spectrum level (pooled predictions)",
                    extra_cols=[("Plots correct (of 48)", lambda t2, s: int((V[(t2, s)]["v3"]["plot"]["table"].pred == V[(t2, s)]["v3"]["plot"]["table"].t).sum()), "0"),
                                ("Plot-level BA", lambda t2, s: float(V[(t2, s)]["v3"]["plot"]["BA"]), "0.0%")])
r0 = end + 2
put(ws, r0, 1, "Per plot: % of spectra predicted diseased (prediction = diseased if > 50%)", font=F_B)
header(ws, r0 + 1, 1, ["Plot", "True class"] + [f"{t2}-{s} %D" for t2, s in CFG] + [f"{t2}-{s} correct?" for t2, s in CFG])
for k in range(1, 49):
    rr = r0 + 1 + k; put(ws, rr, 1, k); put(ws, rr, 2, "healthy" if k <= 12 else "diseased")
    for i, (t2, s) in enumerate(CFG):
        put(ws, rr, 3 + i, float(V[(t2, s)]["v3"]["plot"]["table"].loc[k, "frac"]), fmt="0%")
        cpos = CL(3 + i)
        put(ws, rr, 3 + len(CFG) + i, f'=IF(OR(AND(B{rr}="diseased",{cpos}{rr}>0.5),AND(B{rr}="healthy",{cpos}{rr}<=0.5)),1,0)')
put(ws, r0 + 50, 1, "Plots correct (live)", bold=True)
for i in range(len(CFG)):
    c = CL(3 + len(CFG) + i); put(ws, r0 + 50, 3 + len(CFG) + i, f"=SUM({c}{r0+2}:{c}{r0+49})", fill=FILL_K)
put(ws, r0 + 51, 1, "Healthy plots correct (of 12)", bold=True); put(ws, r0 + 52, 1, "Diseased plots correct (of 36)", bold=True)
for i in range(len(CFG)):
    c = CL(3 + len(CFG) + i)
    put(ws, r0 + 51, 3 + len(CFG) + i, f"=SUM({c}{r0+2}:{c}{r0+13})"); put(ws, r0 + 52, 3 + len(CFG) + i, f"=SUM({c}{r0+14}:{c}{r0+49})")
LOPO_ROW = r0 + 50

# ============================================================ 12 VALIDATION WITH THE DESIGN
DV, SCH = DZ["DV"], DZ["SCHEMES"]
ws = sheet(S["vd"], "Validation using the treatment design (nested: Tier 1, Tier 2, re-balancing and QDA refitted without the test plots)",
           "Leave-location/group-out validation (Roberts et al. 2017; Meyer et al. 2018): the test plots share a treatment level that the model never saw. Every test fold keeps the 1 healthy : 3 diseased plot ratio.")
r0 = 4
VKEYS = [("BA", "Balanced acc.", "0.0%"), ("OA", "Overall acc.", "0.0%"), ("kappa", "Kappa", "0.000"), ("MCC", "MCC", "0.000"),
         ("sens_D", "Sensitivity (D)", "0.0%"), ("spec_H", "Specificity (H)", "0.0%"), ("AUC", "ROC-AUC", "0.000")]
VD_ROWS = {}
for k in ("V4", "V5", "V6"):
    nm, labels = SCH[k]
    put(ws, r0, 1, f"C{k} — {nm} ({len(labels)} folds: {', '.join(labels)})", font=F_B)
    header(ws, r0 + 1, 1, ["Configuration"] + [x[1] for x in VKEYS] + ["BA 95% CI low", "BA 95% CI high", "Plot-level BA", "Plots correct", "Folds without bands"],
           [40] + [12] * (len(VKEYS) + 5))
    for i, (t2, s_) in enumerate(CFG):
        rr = r0 + 2 + i; mm = DV[(k, t2, s_)]; VD_ROWS[(k, t2, s_)] = rr
        put(ws, rr, 1, f"{t2} · {STRATS[s_]}", bold=(s_ == best[t2]))
        for j, (key, _, fmt) in enumerate(VKEYS): put(ws, rr, 2 + j, float(mm.get(key, np.nan)), fmt=fmt)
        ci = mm["acc"]["spectra"]["ci"]["BA"]; c = 2 + len(VKEYS)
        put(ws, rr, c, ci[0], fmt="0.0%"); put(ws, rr, c + 1, ci[1], fmt="0.0%"); put(ws, rr, c + 2, float(mm["plot"]["BA"]), fmt="0.0%")
        tb = mm["plot"]["table"]; put(ws, rr, c + 3, int((tb.pred == tb.t).sum())); put(ws, rr, c + 4, int(mm["no_band_folds"]))
    r0 += 2 + len(CFG) + 2
put(ws, r0, 1, "Balanced accuracy of every fold (best configuration of each Tier-2 method)", font=F_B)
for k in ("V4", "V5", "V6"):
    nm, labels = SCH[k]
    header(ws, r0 + 1, 1, [f"C{k} fold (held-out level)"] + [f"{t2}-{best[t2]}" for t2 in ("CART", "RF")] + ["Test plots"])
    for i, lab_ in enumerate(labels):
        rr = r0 + 2 + i; put(ws, rr, 1, lab_)
        for j, t2 in enumerate(("CART", "RF")): put(ws, rr, 2 + j, DV[(k, t2, best[t2])]["per_fold"][i]["BA"], fmt="0.0%")
        put(ws, rr, 4, DV[(k, "CART", best["CART"])]["per_fold"][i]["plots"])
    r0 += 2 + len(labels) + 1

# ============================================================ 13 NEGATIVE CONTROL
NC, RP, DET = DZ["NC"], DZ["RP"], DZ["DET"]
ws = sheet(S["nc"], "Negative control — does the separation reflect disease or block/location?",
           "Same nested plot-grouped pipeline (4-fold × 10 repetitions, no imbalance correction because each pair has 12 vs 12 plots). Pairs of two INOCULATED blocks cannot differ by disease, so their accuracy measures the block/location effect (negative control; Lipsitch et al. 2010).")
header(ws, 4, 1, ["Pair", "Type", "Distance between block centres (m)", "Spectra (first / second)", "Tier-1 bands p<0.05", "Tier-1 bands, plot means",
                  "Max single-band JM", "CART BA", "CART BA SD", "RF BA", "RF BA SD", "CART plot BA", "RF plot BA"], [12, 36, 14, 14, 12, 12, 12, 11, 11, 11, 11, 11, 11])
for i, (pr_, r) in enumerate(NC.items()):
    rr = 5 + i
    vals = [r["pair"], r["kind"], r["distance_m"], f"{r['n'][0]} / {r['n'][1]}", r["sig"], r["sig_plot"], r["jm_band_max"],
            r["CART"]["BA"][0], r["CART"]["BA"][1], r["RF"]["BA"][0], r["RF"]["BA"][1], r["CART"]["plotBA"][0], r["RF"]["plotBA"][0]]
    fm = [None, None, "0.0", None, "0", "0", "0.0000", "0.0%", "0.0%", "0.0%", "0.0%", "0.0%", "0.0%"]
    for j, (v, f_) in enumerate(zip(vals, fm)): put(ws, rr, 1 + j, v if not isinstance(v, (np.floating, float)) else float(v), fmt=f_)
put(ws, 12, 1, "Mean BA, control vs inoculated", bold=True); put(ws, 12, 8, "=AVERAGE(H5:H7)", fmt="0.0%", fill=FILL_K); put(ws, 12, 10, "=AVERAGE(J5:J7)", fmt="0.0%", fill=FILL_K)
put(ws, 13, 1, "Mean BA, inoculated vs inoculated", bold=True); put(ws, 13, 8, "=AVERAGE(H8:H10)", fmt="0.0%", fill=FILL_K); put(ws, 13, 10, "=AVERAGE(J8:J10)", fmt="0.0%", fill=FILL_K)
put(ws, 14, 1, "Difference (disease signal beyond block effect)", bold=True); put(ws, 14, 8, "=H12-H13", fmt="0.0%"); put(ws, 14, 10, "=J12-J13", fmt="0.0%")
put(ws, 15, 1, "Pairs at the same distance (≈27 m): C vs R2 minus R3 vs R1", bold=True); put(ws, 15, 8, "=H6-H10", fmt="0.0%"); put(ws, 15, 10, "=J6-J10", fmt="0.0%")

put(ws, 18, 1, "Restricted (block-level) permutation: each block in turn labelled 'healthy', full CV2 pipeline (10 repetitions)", font=F_B)
note(ws, 19, 1, "Treatments were assigned to whole blocks, so the only exchangeable units are the 4 blocks (Anderson & ter Braak 2003). With 4 possible labellings the smallest attainable p-value is 1/4 = 0.25: the design cannot separate disease from block effect statistically (Hurlbert 1984).", 10)
header(ws, 20, 1, ["Block labelled healthy"] + [f"{t2}-{RP[t2]['strategy']} BA" for t2 in ("CART", "RF")])
for i, b in enumerate(["C", "R3", "R2", "R1"]):
    put(ws, 21 + i, 1, b + (" (true)" if b == "C" else ""), bold=(b == "C"))
    for j, t2 in enumerate(("CART", "RF")): put(ws, 21 + i, 2 + j, RP[t2]["ba"][b], fmt="0.0%")
put(ws, 25, 1, "p = share of labellings with BA ≥ true (live)", bold=True)
for j in range(2):
    c = CL(2 + j); put(ws, 25, 2 + j, f'=COUNTIF({c}21:{c}24,">="&{c}21)/4', fmt="0.00", fill=FILL_K)

put(ws, 28, 1, "Detection per plot (share of the plot's spectra predicted diseased; CV2 = mean of 10 repetitions, CV3 = leave-one-plot-out)", font=F_B)
tabC, tabR = DET["CART"]["table"], DET["RF"]["table"]
header(ws, 29, 1, ["Plot", "Block", "Variety", "Inoculation", "Class", f"CART-{DET['CART']['strategy']} CV2", f"RF-{DET['RF']['strategy']} CV2", f"CART CV3", "RF CV3"])
for i, k in enumerate(tabC.index):
    rr = 30 + i
    for j, v in enumerate([int(k), tabC.block[k], tabC.variety[k], tabC.date[k], tabC["class"][k]]): put(ws, rr, 1 + j, v)
    for j, v in enumerate([tabC.pD_V2[k], tabR.pD_V2[k], tabC.pD_V3[k], tabR.pD_V3[k]]): put(ws, rr, 6 + j, float(v), fmt="0.0%")
DL = 29 + len(tabC)
put(ws, 28, 11, "Mean share predicted diseased (live AVERAGEIFS)", font=F_B)
header(ws, 29, 11, ["Group", "Level", f"CART CV2", "RF CV2", "CART CV3", "RF CV3"], [12, 12, 10, 10, 10, 10])
rr = 30
for fac, col_, levels in (("Block", "B", ["C", "R3", "R2", "R1"]),):
    for lv in levels:
        put(ws, rr, 11, fac); put(ws, rr, 12, lv)
        for j, c in enumerate("FGHI"): put(ws, rr, 13 + j, f'=AVERAGEIF(${col_}$30:${col_}${DL},L{rr},{c}$30:{c}${DL})', fmt="0.0%")
        rr += 1
for fac, col_, levels in (("Variety", "C", VARS), ("Inoculation", "D", DATES)):
    for cl in ("healthy", "diseased"):
        for lv in levels:
            put(ws, rr, 11, f"{fac} ({cl})"); put(ws, rr, 12, lv)
            for j, c in enumerate("FGHI"): put(ws, rr, 13 + j, f'=AVERAGEIFS({c}$30:{c}${DL},${col_}$30:${col_}${DL},L{rr},$E$30:$E${DL},"{cl}")', fmt="0.0%")
            rr += 1
rr += 1
put(ws, rr, 11, "Kruskal–Wallis (CV2 shares; Kruskal & Wallis 1952)", font=F_B); rr += 1
header(ws, rr, 11, ["Factor | class", "", "CART H", "CART p", "RF H", "RF p"]); rr += 1
for key in DET["CART"]["kw"]:
    put(ws, rr, 11, key)
    for j, t2 in enumerate(("CART", "RF")):
        h_, p_ = DET[t2]["kw"][key]; put(ws, rr, 13 + 2 * j, h_, fmt="0.00"); put(ws, rr, 14 + 2 * j, p_, fmt="0.000")
    rr += 1
put(ws, rr, 11, "block | diseased (R3, R2, R1)")
for j, t2 in enumerate(("CART", "RF")):
    h_, p_ = DET[t2]["kw_block"]; put(ws, rr, 13 + 2 * j, h_, fmt="0.00"); put(ws, rr, 14 + 2 * j, p_, fmt="0.000")

# ============================================================ 14 ACCURACY
ACC = DZ["ACC"]
ws = sheet(S["acc"], "Accuracy assessment — error matrices and accuracy measures",
           "Rows = reference class, columns = predicted class (Story & Congalton 1986; Congalton 1991). Producer's accuracy (PA) = correct / reference total (= sensitivity or specificity); user's accuracy (UA) = correct / predicted total. 95% CI by stratified cluster bootstrap over plots (2000 resamples; Field & Welsh 2007; Olofsson et al. 2014).")
AK = [("OA", "OA"), ("BA", "BA"), ("kappa", "Kappa"), ("PA_H", "PA healthy"), ("UA_H", "UA healthy"), ("PA_D", "PA diseased"), ("UA_D", "UA diseased"),
      ("F1_H", "F1 healthy"), ("F1_D", "F1 diseased"), ("MCC", "MCC"), ("QD", "Quantity disagr."), ("AD", "Allocation disagr.")]
put(ws, 4, 1, "A. Summary of accuracy measures (Python), with 95% cluster-bootstrap CI for OA, BA and kappa", font=F_B)
header(ws, 5, 1, ["Configuration", "Validation", "Level", "Predictions"] + [a[1] for a in AK] + ["OA CI low", "OA CI high", "BA CI low", "BA CI high", "Kappa CI low", "Kappa CI high"],
       [32, 30, 9, 11] + [10] * (len(AK) + 6))
rr = 6
SCHEME_LIST = [("V1", "Paper-style random 10-fold (×5)"), ("V2", "Plot-grouped nested 4-fold (×10)"), ("V3", "Leave-one-plot-out"),
               ("V4", "Leave-one-treatment-combination-out"), ("V5", "Leave-one-variety-out"), ("V6", "Leave-one-inoculation-date-out")]
ACC_ROWS = {}
for (t2, s_) in CFG:
    for k, nm in SCHEME_LIST:
        src = ACC[(t2, s_)].get(k) if k in ("V1", "V2", "V3") else DV[(k, t2, s_)]["acc"]
        for lev in ("spectra", "plots"):
            if lev not in src: continue
            m_ = src[lev]
            put(ws, rr, 1, f"{t2} · {STRATS[s_]}", bold=(s_ == best[t2])); put(ws, rr, 2, f"C{k} {nm}"); put(ws, rr, 3, lev); put(ws, rr, 4, int(m_["cm"].sum()))
            for j, (key, _) in enumerate(AK): put(ws, rr, 5 + j, float(m_[key]), fmt="0.000" if key in ("kappa", "MCC", "F1_H", "F1_D") else "0.0%")
            if "ci" in m_:
                for j, key in enumerate(("OA", "BA", "kappa")):
                    lo, hi = m_["ci"][key]; put(ws, rr, 5 + len(AK) + 2 * j, lo, fmt="0.000" if key == "kappa" else "0.0%"); put(ws, rr, 6 + len(AK) + 2 * j, hi, fmt="0.000" if key == "kappa" else "0.0%")
            ACC_ROWS[(t2, s_, k, lev)] = rr; rr += 1
ws.freeze_panes = "E6"
note(ws, rr + 1, 1, "CV1 has no confidence interval: its folds split spectra of the same plot, so its errors are not independent of the training data. Kappa is reported for comparison with Das et al. (2020), but its use is debated (Pontius & Millones 2011): quantity disagreement (wrong class proportions) and allocation disagreement (wrong placement) add up to 1 − OA.", 14)

def acc_block(ws, r0, c0, title, cm, py):
    """Error matrix with live accuracy formulas and the Python values next to them; returns the cell of the largest |Δ|."""
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
        r = m0 + 1 + i; put(ws, r, mc, dict(AK)[key], bold=True); put(ws, r, mc + 1, f, fmt="0.0000", fill=FILL_K if key == "BA" else None)
        put(ws, r, mc + 2, float(py[key]), fmt="0.0000"); put(ws, r, mc + 3, f"=ABS({CL(mc+1)}{r}-{CL(mc+2)}{r})", fmt="0.0E+00")
    return f"{q(ws.title)}!{CL(mc+3)}{m0+1}:{CL(mc+3)}{m0+12}"
rB = rr + 4
put(ws, rB, 1, "B. Error matrices with live formulas — spectrum level (left: plot-grouped CV2, summed over 10 repetitions; right: leave-one-plot-out CV3)", font=F_B)
ACC_DELTA = []
for i, (t2, s_) in enumerate(CFG):
    r0 = rB + 2 + i * 16
    for j, k in enumerate(("V2", "V3")):
        m_ = ACC[(t2, s_)][k]["spectra"]
        ACC_DELTA.append(acc_block(ws, r0, 1 + j * 11, f"{t2} · {STRATS[s_]} — C{k} ({int(m_['cm'].sum())} predictions)", m_["cm"], m_))
rP = rB + 2 + len(CFG) * 16 + 1
put(ws, rP, 1, "C. Error matrices — plot level (majority vote of each plot's spectra; CV2 summed over 10 repetitions = 480 plot predictions)", font=F_B)
for i, t2 in enumerate(("CART", "RF")):
    for j, k in enumerate(("V2", "V3")):
        m_ = ACC[(t2, best[t2])][k]["plots"]
        ACC_DELTA.append(acc_block(ws, rP + 2 + i * 16, 1 + j * 11, f"{t2} · {STRATS[best[t2]]} — C{k}, plots", m_["cm"], m_))

# ============================================================ 15 COMPARISON
ws = sheet(S["cmp"], "Comparison — balanced accuracy of every configuration under every validation scheme", "Bold = best imbalance strategy per Tier-2 method (highest plot-grouped balanced accuracy).")
header(ws, 4, 1, ["Configuration", "CV1 paper-style 10-fold", "CV2 plot-grouped nested (mean)", "CV2 SD", "CV3 leave-one-plot-out", "CV2 plot level", "CV3 plots correct", "J–M (0–2)", "Bands", "CV3 plot-level BA", "CV4 leave-one-treatment-combination-out", "CV5 leave-one-variety-out", "CV6 leave-one-inoculation-date-out"],
       [40, 14, 14, 12, 14, 14, 12, 10, 8, 14, 16, 14, 14])
for i, (t2, s) in enumerate(CFG):
    rr = 5 + i
    put(ws, rr, 1, f"{t2} · {STRATS[s]}", bold=(s == best[t2]))
    put(ws, rr, 2, f"={q(S['v1'])}!B{6+i}", fmt="0.0%"); put(ws, rr, 3, f"={q(S['v2'])}!B{6+i}", fmt="0.0%")
    put(ws, rr, 4, f"={q(S['v2'])}!{CL(2+len(MKEYS))}{6+i}", fmt="0.0%"); put(ws, rr, 5, f"={q(S['v3'])}!B{6+i}", fmt="0.0%")
    put(ws, rr, 6, f"={q(S['v2'])}!B{6+len(CFG)+4+i}", fmt="0.0%"); put(ws, rr, 7, f"={q(S['v3'])}!{CL(3+len(CFG)+i)}{LOPO_ROW}")
    put(ws, rr, 8, f"={q(S['jm'])}!D{5+i}", fmt="0.000"); put(ws, rr, 9, len(full[(t2, s)]["bands"])); put(ws, rr, 10, float(V[(t2, s)]["v3"]["plot"]["BA"]), fmt="0.0%")
    for j, k in enumerate(("V4", "V5", "V6")): put(ws, rr, 11 + j, f"={q(S['vd'])}!B{VD_ROWS[(k, t2, s)]}", fmt="0.0%")
put(ws, 14, 1, "Benchmark: RF on all 483 bands (class-weighted)", bold=True); put(ws, 14, 3, mean_of(bm, "BA"), fmt="0.0%"); put(ws, 14, 6, mean_of([m["plot"] for m in bm], "BA"), fmt="0.0%")
put(ws, 15, 1, "Chance level", bold=True); put(ws, 15, 2, 0.5, fmt="0.0%"); put(ws, 15, 3, 0.5, fmt="0.0%"); put(ws, 15, 5, 0.5, fmt="0.0%")
put(ws, 16, 1, "Restricted (block-level) permutation p (sheet 13)", bold=True); put(ws, 16, 3, f"={q(S['nc'])}!B25", fmt="0.00")

# ============================================================ 12 PERMUTATION
ws = sheet(S["perm"], "Permutation test — plot labels shuffled (12 healthy / 36 diseased kept), full plot-grouped pipeline re-run", "p = (1 + number of shuffles with balanced accuracy ≥ observed) / (shuffles + 1)  (Ojala & Garriga 2010).")
for i, t2 in enumerate(("CART", "RF")):
    pm = R["perm"][t2]; c0 = 1 + 4 * i; nn = len(pm["null"])
    put(ws, 4, c0, lab(t2, pm["strategy"]), font=F_B)
    put(ws, 5, c0, "Observed BA"); put(ws, 5, c0 + 1, float(pm["observed"]), fmt="0.0%")
    put(ws, 6, c0, "Shuffles"); put(ws, 6, c0 + 1, f"=COUNT({CL(c0+1)}12:{CL(c0+1)}{11+nn})")
    put(ws, 7, c0, "Null mean"); put(ws, 7, c0 + 1, f"=AVERAGE({CL(c0+1)}12:{CL(c0+1)}{11+nn})", fmt="0.0%")
    put(ws, 8, c0, "Null max"); put(ws, 8, c0 + 1, f"=MAX({CL(c0+1)}12:{CL(c0+1)}{11+nn})", fmt="0.0%")
    put(ws, 9, c0, "p-value"); put(ws, 9, c0 + 1, f'=(1+COUNTIF({CL(c0+1)}12:{CL(c0+1)}{11+nn},">="&{CL(c0+1)}5))/({CL(c0+1)}6+1)', fmt="0.000", fill=FILL_K)
    header(ws, 11, c0, ["Shuffle", "BA"])
    for k, v in enumerate(pm["null"]): put(ws, 12 + k, c0, k + 1); put(ws, 12 + k, c0 + 1, float(v), fmt="0.0%")
    ws.column_dimensions[CL(c0)].width = 34

# ============================================================ 13 REFERENCES
ws = sheet(S["refs"], "References — what each is used for and how the citation was checked", "Each citation was checked against the journal, publisher, repository or index record (October 2026).")
header(ws, 4, 1, ["Short citation", "Full reference", "Used for", "Checked against"], [26, 90, 60, 36])
for i, (a, b, c, d) in enumerate(REFS):
    for j, v in enumerate((a, b, c, d)): put(ws, 5 + i, 1 + j, v, wrap=True, bold=(j == 0))
    ws.row_dimensions[5 + i].height = 42

# ============================================================ 14 CHECKS
ws = sheet(S["chk"], "Cross-checks of every step", "Part A: Python checks during the analysis. Part B: live Excel formulas compared with the Python results.")
for c, w in zip("ABCDE", [14, 64, 30, 46, 9]): ws.column_dimensions[c].width = w
header(ws, 4, 1, ["Step", "Check", "Expected", "Obtained", "Result"])
ck = pd.concat([R["checks"], DZ["checks"]], ignore_index=True)
for i, rw in enumerate(ck.itertuples(index=False)):
    rr = 5 + i
    put(ws, rr, 1, rw.step); put(ws, rr, 2, rw.check, wrap=True); put(ws, rr, 3, rw.expected); put(ws, rr, 4, rw.obtained, wrap=True)
    put(ws, rr, 5, rw.result, font=Font(name=FONT, size=10, bold=True, color="008000" if rw.result == "PASS" else "C00000"))
rb = 5 + len(ck) + 2
put(ws, rb, 1, "Part B — live Excel checks", font=F_B); header(ws, rb + 1, 1, ["Step", "Check", "Value", "Tolerance", "Result"])
live = [("Data", "Spectra counted per plot (sheet 2) = total spectra", f"=ABS({q(S['summ'])}!C53-{N})", 0.5),
        ("Tier 1", "Max relative |F(Excel) − F(Python)|", f"=MAX({q(S['t1'])}!AA{TR0+1}:AA{TL})", 1e-6),
        ("Tier 1", "Max |p(Excel) − p(Python)|", f"=MAX({q(S['t1'])}!AC{TR0+1}:AC{TL})", 1e-6),
        ("Tier 1", "Significant bands: Excel − Python", f"=ABS({q(S['t1'])}!E6-{int((R['tier1'].p_ANOVA<0.05).sum())})", 0.5),
        ("Tier 3", "Max |single-band JM (Excel) − Python| over selected bands", f"=MAX({q(S['jm'])}!E{U0+2}:E{JM_LAST})", 1e-9),
        ("Tier 3", "|JM best CART set (Excel matrix) − Python|", f"=ABS({REF['jm_CART']})", 1e-6),
        ("Tier 3", "|JM best RF set (Excel matrix) − Python|", f"=ABS({REF['jm_RF']})", 1e-6),
        ("Imbalance", "Class weights give equal total weight", f'=IF({q(S["imb"])}!B9="yes",0,1)', 0.5),
        ("Design", "Every block holds each variety × date once (live COUNTIFS)", f'=IF({q(S["des"])}!K30="yes",0,1)', 0.5),
        ("Design", "Spectra per plot (design sheet) sum to all spectra", f"=ABS(SUM({q(S['des'])}!F5:F52)-{N})", 0.5),
        ("Accuracy", "Max |accuracy measure (Excel formula) − Python| over all error matrices", "=MAX(" + ",".join(ACC_DELTA) + ")", 1e-9)]
for t2 in ("CART", "RF"):
    live.append(("Tier 4", f"|BA paper-style {t2} (Excel formula) − Python|", f"=ABS({REF['v1'][t2]['BA']}-{REF['v1'][t2]['py']})", 1e-9))
    live.append(("Validation", f"|BA plot-grouped {t2} (Excel formula) − Python|", f"=ABS({REF['v2'][t2]['BA']}-{REF['v2'][t2]['py']})", 1e-9))
    live.append(("Validation", f"Confusion-matrix total ({t2}, plot-grouped) − spectra", f"=ABS({REF['v2'][t2]['N']}-{N})", 0.5))
for i, (a, b, f, tol) in enumerate(live):
    rr = rb + 2 + i
    put(ws, rr, 1, a); put(ws, rr, 2, b); put(ws, rr, 3, f, fmt="0.0E+00"); put(ws, rr, 4, tol, fmt="0.0E+00")
    put(ws, rr, 5, f'=IF(C{rr}<=D{rr},"PASS","FAIL")', font=Font(name=FONT, size=10, bold=True))
put(ws, rb + 3 + len(live), 1, "All checks", font=F_B)
put(ws, rb + 3 + len(live), 5, f'=IF(AND(COUNTIF(E5:E{4+len(ck)},"FAIL")=0,COUNTIF(E{rb+2}:E{rb+1+len(live)},"FAIL")=0),"ALL PASS","CHECK")', fill=FILL_K, font=F_B)
wb.save(OUT); print("saved", OUT, "live checks:", len(live))
