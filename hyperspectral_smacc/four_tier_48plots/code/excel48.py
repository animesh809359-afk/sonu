"""Step-by-step workbook for the 48-plot analysis (reads results/r48.pkl)."""
import pickle, sys
import numpy as np, pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter as CL
from refs48 import REFS

OUT = sys.argv[1]
R = pickle.load(open("results/r48.pkl", "rb"))
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

S = dict(raw="1_Data", summ="2_Data_Summary", t1="3_Tier1_ANOVA", imb="4_Imbalance", cart="5_Tier2_CART", rf="6_Tier2_RF", jm="7_Tier3_JM",
         v1="8_Tier4_PaperStyle", v2="9_Validation_PlotGrouped", v3="10_Validation_LOPO", cmp="11_Comparison", perm="12_Permutation",
         refs="13_References", chk="14_Cross_Checks")

# ============================================================ README
ws = sheet("README", "Four-tier analysis (Das et al. 2020) of 48-plot SMACC endmembers — CART vs Random Forest in Tier 2, with class-imbalance handling",
           f"{N} endmember spectra (healthy plots 1–12: {nH}; diseased plots 13–48: {nD}) × {P} reflectance bands (399–2398 nm). Every endmember and every band is used; spectra are not averaged.")
ws.column_dimensions["A"].width = 6; ws.column_dimensions["B"].width = 26; ws.column_dimensions["C"].width = 120
header(ws, 4, 1, ["Step", "Sheet", "Content"])
rows = [("0", S["raw"], "All 1417 endmember spectra exactly as in SMACC_EM_spectra_48plots_rearranged.xlsx (all 483 bands), with plot, EM number and class; sorted healthy first. All live formulas read from here."),
        ("1", S["summ"], "Spectra per plot and per class (COUNTIFS), imbalance ratio, negative-reflectance counts."),
        ("2", S["t1"], "TIER 1 — one-way ANOVA at every band with live Excel formulas (means, SDs, sums of squares, F, p); Tukey HSD, Welch, Levene, FDR, Bonferroni, Cohen's d, single-band J–M; ANOVA of the 48 plot means (pseudo-replication check)."),
        ("3", S["imb"], "Class imbalance (1 : 2.96) and the four strategies compared: none, class weighting, random under-sampling, SMOTE — applied to training data only."),
        ("4", S["cart"], "TIER 2 (CART, rpart settings) — bands selected under each imbalance strategy; class-weighted tree structure."),
        ("5", S["rf"], "TIER 2 alternative (Random Forest) — importance ranking, redundancy filter |r| < 0.95, same number of bands as CART."),
        ("6", S["jm"], "TIER 3 — Jeffries–Matusita distance of every selected set; single-band J–M of every selected band; live matrix J–M for the best CART and RF sets."),
        ("7", S["v1"], "TIER 4 — QDA, paper-style random 10-fold CV (bands chosen on all data; optimistic, for comparison with Das et al.)."),
        ("8", S["v2"], "VALIDATION (main) — plot-grouped nested 4-fold CV × 10 repetitions: every step (ANOVA, CART/RF, re-balancing, QDA) redone on training plots only; spectrum- and plot-level metrics."),
        ("9", S["v3"], "VALIDATION — leave-one-plot-out (48 folds), nested; prediction for every plot."),
        ("10", S["cmp"], "Comparison of all configurations under the three validation schemes, plus the RF classifier benchmark."),
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
# single-band JM of every selected band (union)
union = sorted({b for v in full.values() for b in v["bands"]})
put(ws, 15, 1, f"Single-band J–M of every band selected in any configuration ({len(union)} bands) — live link to sheet 3", font=F_B)
header(ws, 16, 1, ["Band (nm)", "Region", "JM 0–2 (live)", "JM (Python)", "|Δ|"] + [f"{t2}-{s}" for t2, s in CFG])
T1B, T1R = f"{q(S['t1'])}!$B${TR0+1}:$B${TL}", f"{q(S['t1'])}!$R${TR0+1}:$R${TL}"
for i, b in enumerate(union):
    rr = 17 + i
    put(ws, rr, 1, float(wl[b]), fmt="0.000"); put(ws, rr, 2, region(wl[b])); put(ws, rr, 3, f"=INDEX({T1R},MATCH(A{rr},{T1B},0))", fmt="0.0000")
    put(ws, rr, 4, float(R["jm_band"][b]), fmt="0.0000"); put(ws, rr, 5, f"=ABS(C{rr}-D{rr})", fmt="0.0E+00")
    for k, (t2, s) in enumerate(CFG): put(ws, rr, 6 + k, "✓" if b in full[(t2, s)]["bands"] else "")
JM_LAST = 16 + len(union)
put(ws, JM_LAST + 1, 1, "Maximum", bold=True); put(ws, JM_LAST + 1, 3, f"=MAX(C17:C{JM_LAST})", fmt="0.0000", fill=FILL_K)
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

# ============================================================ 8 V1
ws = sheet(S["v1"], "Tier 4 — QDA with paper-style random 10-fold CV (5 repetitions)", "Bands chosen on all data (as in Das et al.); folds random over spectra; re-balancing on training folds only. Spectra of one plot fall on both sides of a split, so these numbers are optimistic.")
end = summary_table(ws, 4, lambda t2, s: {k: mean_of(V[(t2, s)]["v1"], k) for k, _, _ in MKEYS}, "Mean over 5 repetitions")
REF["v1"] = {}
for i, t2 in enumerate(("CART", "RF")):
    REF["v1"][t2] = cm_block(ws, end + 2, 1 + 7 * i, f"{lab(t2, best[t2])} — repetition 1", V[(t2, best[t2])]["v1"][0]["cm"])
    put(ws, end + 14, 1 + 7 * i, "Python BA (rep. 1)"); put(ws, end + 14, 2 + 7 * i, float(V[(t2, best[t2])]["v1"][0]["BA"]), fmt="0.0%")
    REF["v1"][t2]["py"] = f"{q(S['v1'])}!{CL(2+7*i)}{end+14}"

# ============================================================ 9 V2
ws = sheet(S["v2"], "Validation (main) — plot-grouped, nested 4-fold CV × 10 repetitions", "Each fold: 3 healthy + 9 diseased plots held out; ANOVA, CART/RF selection, re-balancing and QDA fitted on the other 36 plots only (Ambroise & McLachlan 2002; Roberts et al. 2017).")
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

# ============================================================ 10 V3 LOPO
ws = sheet(S["v3"], "Validation — leave-one-plot-out (48 folds, nested)", "Each plot is predicted by a model trained on the other 47 plots. Plot label = majority of its spectra.")
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

# ============================================================ 11 COMPARISON
ws = sheet(S["cmp"], "Comparison — balanced accuracy of every configuration under the three validation schemes", "Bold = best imbalance strategy per Tier-2 method (highest plot-grouped balanced accuracy).")
header(ws, 4, 1, ["Configuration", "Paper-style 10-fold", "Plot-grouped nested (mean)", "Plot-grouped SD", "Leave-one-plot-out", "Plot-grouped, plot level", "LOPO plots correct", "J–M (0–2)", "Bands", "LOPO plot-level BA"],
       [40, 14, 14, 12, 14, 14, 12, 10, 8, 14])
for i, (t2, s) in enumerate(CFG):
    rr = 5 + i
    put(ws, rr, 1, f"{t2} · {STRATS[s]}", bold=(s == best[t2]))
    put(ws, rr, 2, f"={q(S['v1'])}!B{6+i}", fmt="0.0%"); put(ws, rr, 3, f"={q(S['v2'])}!B{6+i}", fmt="0.0%")
    put(ws, rr, 4, f"={q(S['v2'])}!{CL(2+len(MKEYS))}{6+i}", fmt="0.0%"); put(ws, rr, 5, f"={q(S['v3'])}!B{6+i}", fmt="0.0%")
    put(ws, rr, 6, f"={q(S['v2'])}!B{6+len(CFG)+4+i}", fmt="0.0%"); put(ws, rr, 7, f"={q(S['v3'])}!{CL(3+len(CFG)+i)}{LOPO_ROW}")
    put(ws, rr, 8, f"={q(S['jm'])}!D{5+i}", fmt="0.000"); put(ws, rr, 9, len(full[(t2, s)]["bands"])); put(ws, rr, 10, float(V[(t2, s)]["v3"]["plot"]["BA"]), fmt="0.0%")
put(ws, 14, 1, "Benchmark: RF on all 483 bands (class-weighted)", bold=True); put(ws, 14, 3, mean_of(bm, "BA"), fmt="0.0%"); put(ws, 14, 6, mean_of([m["plot"] for m in bm], "BA"), fmt="0.0%")
put(ws, 15, 1, "Chance level", bold=True); put(ws, 15, 2, 0.5, fmt="0.0%"); put(ws, 15, 3, 0.5, fmt="0.0%"); put(ws, 15, 5, 0.5, fmt="0.0%")

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
ck = R["checks"]
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
        ("Tier 3", "Max |single-band JM (Excel) − Python| over selected bands", f"=MAX({q(S['jm'])}!E17:E{JM_LAST})", 1e-9),
        ("Tier 3", "|JM best CART set (Excel matrix) − Python|", f"=ABS({REF['jm_CART']})", 1e-6),
        ("Tier 3", "|JM best RF set (Excel matrix) − Python|", f"=ABS({REF['jm_RF']})", 1e-6),
        ("Imbalance", "Class weights give equal total weight", f'=IF({q(S["imb"])}!B9="yes",0,1)', 0.5)]
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
