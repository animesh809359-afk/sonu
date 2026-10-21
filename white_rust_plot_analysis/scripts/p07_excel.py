"""Build the plot-level analysis workbook: one sheet per step, editable native Excel charts, formula-driven checks."""
import os, sys, json
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pcommon import *
from p03_cv import SCENARIOS
from models import CLF_NAMES
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.chart import ScatterChart, BarChart, LineChart, Reference, Series
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.drawing.image import Image as XLImage

OUT = os.path.join(ROOT, 'outputs', 'WhiteRust_Mustard_PlotLevel_Analysis.xlsx')
T = lambda n: pd.read_csv(os.path.join(TAB, n))
have = lambda n: os.path.exists(os.path.join(TAB, n))
FONT = 'Arial'
HDR_FILL = PatternFill('solid', fgColor='1F4E2C')
HDR_FONT = Font(name=FONT, bold=True, color='FFFFFF', size=10)
TITLE_FONT = Font(name=FONT, bold=True, size=13, color='1F4E2C')
NOTE_FONT = Font(name=FONT, italic=True, size=9, color='555555')
BOLD = Font(name=FONT, bold=True, size=10)
BODY = Font(name=FONT, size=10)
INPUT = Font(name=FONT, size=10, color='0000FF')
THIN = Side(style='thin', color='D0D0D0')
COL_H, COL_D, COL_3, COL_4 = '2E7D32', 'D08A00', '2A6FB0', 'B03A2E'
DATEC = [COL_3, COL_H, COL_D, COL_4]
DL = [DATE_LABEL[d] for d in DATE_ORDER]
METS = ['BA', 'OA', 'Sensitivity', 'Specificity', 'MacroF1', 'Kappa', 'MCC', 'ROC_AUC']

wb = Workbook(); wb.remove(wb.active)
INDEX = []


def sheet(name, title, note, ref=''):
    ws = wb.create_sheet(name)
    ws['A1'] = title; ws['A1'].font = TITLE_FONT
    ws['A2'] = note; ws['A2'].font = NOTE_FONT
    if ref:
        ws['A3'] = 'Method reference(s): ' + ref; ws['A3'].font = NOTE_FONT
    INDEX.append((name, title, note, ref))
    ws.sheet_view.showGridLines = False
    return ws


def write_df(ws, df, r0=5, c0=1, fmt=None, widths=None, freeze=True):
    for j, col in enumerate(df.columns):
        c = ws.cell(r0, c0 + j, str(col)); c.font = HDR_FONT; c.fill = HDR_FILL
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    for i, row in enumerate(df.itertuples(index=False), start=1):
        for j, v in enumerate(row):
            if isinstance(v, (np.floating, float)) and not np.isfinite(v):
                v = None
            elif isinstance(v, np.generic):
                v = v.item()
            c = ws.cell(r0 + i, c0 + j, v); c.font = BODY; c.border = Border(bottom=THIN)
            if isinstance(v, float):
                c.number_format = (fmt or {}).get(df.columns[j], '0.000')
    for j, col in enumerate(df.columns):
        w = (widths or {}).get(col, min(max(len(str(col)) + 2, 10), 30))
        cur = ws.column_dimensions[get_column_letter(c0 + j)].width or 0
        ws.column_dimensions[get_column_letter(c0 + j)].width = max(w, cur if cur < 40 else 0)
    if freeze:
        ws.freeze_panes = ws.cell(r0 + 1, 1)
    return r0, c0, r0 + len(df), c0 + len(df.columns) - 1


def label(ws, r, c, text):
    ws.cell(r, c, text).font = BOLD


def scatter_lines(ws, anchor, title, xcol, ycols, r0, r1, colors, xt='Wavelength (nm)', yt='', w=22, h=10, dashes=None, xmin=400, xmax=2400, markers=False):
    ch = ScatterChart(); ch.title = title; ch.style = 13; ch.x_axis.title = xt; ch.y_axis.title = yt
    ch.width, ch.height = w, h
    xs = Reference(ws, min_col=xcol, min_row=r0 + 1, max_row=r1)
    for k, yc in enumerate(ycols):
        s = Series(Reference(ws, min_col=yc, min_row=r0, max_row=r1), xs, title_from_data=True)
        if markers:
            s.marker.symbol = 'circle'; s.marker.size = 5; s.graphicalProperties.line.noFill = True
            s.marker.graphicalProperties.solidFill = colors[k % len(colors)]; s.marker.graphicalProperties.line.solidFill = colors[k % len(colors)]
        else:
            s.marker.symbol = 'none'
            s.graphicalProperties.line.solidFill = colors[k % len(colors)]; s.graphicalProperties.line.width = 20000
            if dashes and dashes[k]:
                s.graphicalProperties.line.dashStyle = 'dash'
        s.smooth = False
        ch.series.append(s)
    if xmin is not None:
        ch.x_axis.scaling.min = xmin; ch.x_axis.scaling.max = xmax
    ch.x_axis.delete = False; ch.y_axis.delete = False; ch.legend.position = 'b'
    ws.add_chart(ch, anchor)


def bar(ws, anchor, title, catcol, valcols, r0, r1, colors, yt='', horizontal=False, w=18, h=9, ymin=None, ymax=None):
    ch = BarChart(); ch.type = 'bar' if horizontal else 'col'; ch.title = title; ch.style = 10
    ch.width, ch.height = w, h; ch.y_axis.title = yt
    ch.add_data(Reference(ws, min_col=valcols[0], max_col=valcols[-1], min_row=r0, max_row=r1), titles_from_data=True)
    ch.set_categories(Reference(ws, min_col=catcol, min_row=r0 + 1, max_row=r1))
    for k, s in enumerate(ch.series):
        s.graphicalProperties.solidFill = colors[k % len(colors)]; s.graphicalProperties.line.noFill = True
    if ymin is not None: ch.y_axis.scaling.min = ymin
    if ymax is not None: ch.y_axis.scaling.max = ymax
    ch.x_axis.delete = False; ch.y_axis.delete = False
    if len(valcols) == 1: ch.legend = None
    else: ch.legend.position = 'b'
    ws.add_chart(ch, anchor)


def heat(ws, rng, lo='FFFFE5', mid='78C679', hi='004529', mn=None, mx=None):
    if mn is None:
        ws.conditional_formatting.add(rng, ColorScaleRule(start_type='min', start_color=lo, mid_type='percentile', mid_value=50, mid_color=mid, end_type='max', end_color=hi))
    else:
        ws.conditional_formatting.add(rng, ColorScaleRule(start_type='num', start_value=mn, start_color=lo, mid_type='num', mid_value=(mn + mx) / 2, mid_color=mid, end_type='num', end_value=mx, end_color=hi))


def diverge(ws, rng, v=2.5):
    ws.conditional_formatting.add(rng, ColorScaleRule(start_type='num', start_value=-v, start_color='2A6FB0', mid_type='num', mid_value=0, mid_color='FFFFFF', end_type='num', end_value=v, end_color='B03A2E'))


def image(ws, fig, anchor, width=None):
    p = os.path.join(FIG, fig)
    if os.path.exists(p):
        im = XLImage(p)
        if width:
            r = width / im.width; im.width = width; im.height = im.height * r
        ws.add_image(im, anchor)


def summ(df, keys, extra=()):
    g = df.groupby(keys, sort=False)
    s = g[METS].mean()
    s.insert(1, 'BA_SD', g['BA'].std())
    for e in extra:
        s[e] = g[e].median()
    return s.reset_index()


readme = wb.create_sheet('00_README')
M = load_meta()

# ============================================================ 01 Methodology
ws = sheet('01_Methodology', 'Analysis framework - step by step (plot level)', 'Each step, what was done, why, the source papers and the sheet holding the result. Steps not useful for plot-average data are listed at the bottom with the reason.')
steps = [
    ('1', 'Data assembly', '4 PlotAverage_Features workbooks (48 plots x 4 dates = 192 plot-date samples) merged with the treatment layout (variety, inoculation timing D1-D4, control / replicate block).', 'Lv et al. 2023; Tian et al. 2021', '02_Data_Design'),
    ('2', 'Quality control', 'Noise of every plot average, detector-join steps, leaf-number confound, PCA T2/Q screening per date (flag only).', 'Hueni & Bialek 2017; Selvaprakash et al. 2026', '03_QC'),
    ('3', 'Spectral characterisation', 'Mean, difference and ratio spectra of healthy vs diseased plots for every date.', 'Zhang et al. 2012; Mandal et al. 2022', '04_Mean_Spectra'),
    ('4', 'Band-wise statistics', 'Welch t + BH-FDR, Hedges g, AUC, J-M distance, point-biserial r for reflectance and derivatives; sensitive regions stable on >= 3 dates.', 'Mandal et al. 2022, 2023; Lv et al. 2023', '05_Bandwise_Stats'),
    ('5', 'Feature families', 'Reflectance (10 nm), 1st/2nd/3rd derivatives, 48 continuum-removal parameters, 87 vegetation indices, 23 red-edge parameters, CWT (Mexican hat, 8 scales), optimised NDSI/SR/DI.', 'Zhang 2012; Mandal 2022, 2023; Tian 2021; Lv 2023; Zhu 2017', '06_Feature_Screening'),
    ('6', 'Univariate screening', 'Every feature on every date: AUC, Hedges g, FDR q; stability = significant and same sign on >= 3 of 4 dates.', 'Tian et al. 2021; Lv et al. 2023', '06_Feature_Screening .. 09_Optimised_Index'),
    ('7', 'Repeated-measures models', 'Linear mixed model per feature: z ~ disease + date + variety + (1 | plot); disease x date likelihood-ratio test.', 'Bates et al. 2015', '10_Mixed_Models'),
    ('8', 'Design-based controls', 'Matched control (inoculated minus its own control in the same variety x inoculation cell), block-to-block contrast among inoculated plots, inoculation-timing effect.', 'Hurlbert 1984', '11_Design_Controls'),
    ('9', 'Multivariate structure', 'PCA (raw and date-centred), eta2 of factors, PERMANOVA with design-restricted permutations.', 'Anderson 2001; Selvaprakash et al. 2026', '12_PCA_PERMANOVA'),
    ('10', 'Raw vs smoothed branch', 'Separability of every feature computed from raw and from SG-smoothed plot averages; CV on both branches.', 'Savitzky & Golay 1964; Mandal et al. 2023', '13_Raw_vs_Smoothed'),
    ('11', 'Classification (main CV)', '12 feature scenarios x 10 classifiers; nested, cell-grouped, repeated (20 x 4-fold) CV; selection and tuning inside the training folds.', 'Varma & Simon 2006; Roberts et al. 2017; Tian 2021; Zhu 2017; Huang 2020', '14_CV_Design, 15_CV_Results'),
    ('12', 'Model comparison', 'Friedman + Nemenyi, Nadeau-Bengio corrected t-test, Wilcoxon-Holm.', 'Demsar 2006; Nadeau & Bengio 2003', '17_Model_Comparison'),
    ('13', 'Best models', 'Confusion matrices, ROC, per-date / variety / inoculation performance, disease-call progression.', 'Fawcett 2006; Chicco & Jurman 2020', '18_Best_Models, 19_Progression'),
    ('14', 'Supporting experiments', 'E1 branch, E2 single date, E3 transfer (LODO/LOVO), E4 date normalisation, E5 permutation test, E6 block controls, E7 OFC, E8 selector comparison, E9 equal leaf numbers, E10 leaf vs plot level.', 'see each sheet', '20_..29_'),
    ('15', 'Final feature set', 'Robust selection on all data; correlation, VIF, J-M distance, permutation importance.', 'Tian et al. 2021; Dormann et al. 2013', '30_Final_Features'),
]
write_df(ws, pd.DataFrame(steps, columns=['Step', 'Name', 'What was done', 'Main references', 'Result sheet']), 5, 1,
         widths={'What was done': 90, 'Main references': 45, 'Result sheet': 28, 'Name': 26})
skipped = [('Outlier removal', 'Plot means already average 3-15 leaves; T2/Q flags reported only (1-2 plots per date, removal would unbalance the 12 control plots).'),
           ('SNV / MSC / OSC pre-treatment of classifier inputs', 'Plot averaging removes most leaf-to-leaf scatter; SNV used only for PCA/PERMANOVA. The leaf-level chapter compared them.'),
           ('t-SNE / UMAP', '48 points per date: PCA is sufficient and reproducible.'),
           ('Severity regression (Mandal et al. 2022, 2023)', 'No severity score per plot - the response is healthy vs diseased.'),
           ('Image texture / colour features (Huang et al. 2020)', 'Point spectra, no images.'),
           ('3D-CNN / UAV multispectral (Nguyen et al. 2023)', 'n = 192 plot-dates is too small for deep learning; the target here is contact-probe spectra.'),
           ('Learning curve, sensor simulation', 'Already done at leaf level; at plot level the training set has only 36 plots.')]
r = 5 + len(steps) + 3
label(ws, r - 1, 1, 'Steps left out and why')
write_df(ws, pd.DataFrame(skipped, columns=['Step', 'Reason']), r, 1, widths={'Reason': 90}, freeze=False)

# ============================================================ 02 data design
ws = sheet('02_Data_Design', 'Step 1 - Data assembly and experimental design',
           'Each sample is one plot-average spectrum on one date. Controls (block C) are healthy; inoculated plots (R1-R3) are diseased. Cells = variety x inoculation timing (1 control + 3 inoculated plots).',
           'Treatment file; PlotAverage_Features workbooks')
Dd = T('design_by_date.csv')
tab = Dd[['Date', 'Healthy', 'Diseased']].copy()
_, _, r1, _ = write_df(ws, tab, 5, 1)
ws.cell(5, 4, 'Total plots').font = HDR_FONT; ws.cell(5, 4).fill = HDR_FILL
ws.cell(5, 5, 'Healthy : Diseased').font = HDR_FONT; ws.cell(5, 5).fill = HDR_FILL
for rr in range(6, r1 + 1):
    ws.cell(rr, 4, f'=B{rr}+C{rr}'); ws.cell(rr, 5, f'="1 : "&TEXT(C{rr}/B{rr},"0.0")')
ws.cell(r1 + 1, 1, 'Total').font = BOLD
for col in 'BCD':
    ws[f'{col}{r1 + 1}'] = f'=SUM({col}6:{col}{r1})'; ws[f'{col}{r1 + 1}'].font = BOLD
lv = Dd[['Date', 'median_Healthy', 'median_Diseased', 'sum_Healthy', 'sum_Diseased']].rename(columns={'median_Healthy': 'Median leaves / healthy plot', 'median_Diseased': 'Median leaves / diseased plot', 'sum_Healthy': 'Leaf spectra healthy', 'sum_Diseased': 'Leaf spectra diseased'})
label(ws, r1 + 3, 1, 'Leaf spectra averaged per plot')
_, _, r2, _ = write_df(ws, lv, r1 + 4, 1, freeze=False)
bar(ws, 'H5', 'Median leaves averaged per plot', 1, [2, 3], r1 + 4, r2, [COL_H, COL_D], 'Leaves per plot', w=14, h=8)
label(ws, r2 + 3, 1, 'Treatment layout (plot numbers)')
_, _, r3, _ = write_df(ws, T('design_layout.csv'), r2 + 4, 1, freeze=False)
image(ws, 'Fig01_treatment_layout.png', f'H{r2 + 4}', width=760)
pl = M.assign(Date=M['date'].map(DATE_LABEL), v=M['stage'].str[:3] + ' (' + M['n_leaves'].astype(str) + ')').pivot(index=['plot', 'variety', 'inoc', 'block', 'label'], columns='Date', values='v')[DL].reset_index()
label(ws, r3 + 3, 1, 'Plot x date: growth stage (leaves averaged)')
write_df(ws, pl, r3 + 4, 1, freeze=False)
ws.freeze_panes = None

# ============================================================ 03 QC
ws = sheet('03_QC', 'Step 2 - Quality control of the plot averages',
           'Noise = SD of (raw - SG(11,2)) in 450-900 and 1050-1300 nm. Diseased plots average more leaves (5-15 vs 3-9), so their raw averages are expected to be smoother by sqrt(n_H/n_D); this confound is tested in E9.',
           'Hueni & Bialek 2017; Savitzky & Golay 1964')
NS = T('qc_noise_summary.csv')
_, _, r1, _ = write_df(ws, NS, 5, 1, fmt={c: '0.00000' for c in NS.columns if 'Noise_' in c and 'ratio' not in c} | {c: '0.0000' for c in NS.columns if 'Join' in c})
bar(ws, f'A{r1 + 3}', 'Diseased / healthy noise ratio (raw branch rows 1-4)', 2, [7, 8], 5, 9, [COL_4, '9E9E9E'], 'Ratio', w=16, h=8, ymin=0.6, ymax=1.1)
QC = T('qc_plot_noise.csv'); QC = QC[QC.branch == 'raw']
qq = pd.DataFrame({'Leaves (healthy)': np.where(QC.label == 'Healthy', QC.n_leaves, np.nan), 'Noise healthy': np.where(QC.label == 'Healthy', QC.noise_sd, np.nan),
                   'Leaves (diseased)': np.where(QC.label == 'Diseased', QC.n_leaves, np.nan), 'Noise diseased': np.where(QC.label == 'Diseased', QC.noise_sd, np.nan)})
label(ws, r1 + 21, 1, 'Noise of each raw plot average vs leaves averaged')
rq0 = r1 + 22
write_df(ws, pd.concat([QC[['date', 'plot', 'label', 'n_leaves', 'noise_sd', 'join1000_step', 'join1800_step']].reset_index(drop=True), qq.reset_index(drop=True)], axis=1), rq0, 1,
         fmt={'noise_sd': '0.000000', 'Noise healthy': '0.000000', 'Noise diseased': '0.000000', 'join1000_step': '0.00000', 'join1800_step': '0.00000'}, freeze=False)
ch = ScatterChart(); ch.title = 'Noise vs leaves averaged'; ch.style = 13; ch.x_axis.title = 'Leaves per plot'; ch.y_axis.title = 'Noise SD'
for xc, yc, col in ((8, 9, COL_H), (10, 11, COL_D)):
    s = Series(Reference(ws, min_col=yc, min_row=rq0, max_row=rq0 + len(QC)), Reference(ws, min_col=xc, min_row=rq0 + 1, max_row=rq0 + len(QC)), title_from_data=True)
    s.marker.symbol = 'circle'; s.marker.size = 5; s.graphicalProperties.line.noFill = True
    s.marker.graphicalProperties.solidFill = col; s.marker.graphicalProperties.line.solidFill = col
    ch.series.append(s)
ch.x_axis.delete = False; ch.y_axis.delete = False; ch.width, ch.height = 16, 8
ws.add_chart(ch, f'K{r1 + 3}')
OU = T('qc_outliers_plot.csv'); OU['Date'] = OU['date'].map(DATE_LABEL)
label(ws, 5, 18, 'PCA T2 / Q screening per date (99 % limits) - flagged plot averages')
write_df(ws, OU[OU.flag][['Date', 'plot', 'label', 'T2', 'T2_limit99', 'Q', 'Q_limit99']], 6, 18, freeze=False)
ws.freeze_panes = None

# ============================================================ 04 mean spectra
ws = sheet('04_Mean_Spectra', 'Step 3 - Mean plot-average spectra of healthy and diseased plots',
           'Raw plot-average reflectance resampled to 10 nm (mean of the 1-nm values within +/-5 nm). Difference = diseased - healthy. Columns R onward are Excel formulas.', 'Zhang et al. 2012; Mandal et al. 2022')
S = T('spectra_mean_by_date_class.csv')
cols = ['Wavelength_nm'] + [f'raw_{d}_{c}_mean' for d in DL for c in ('H', 'D')]
SD_ = S[cols].copy(); SD_.columns = ['Wavelength_nm'] + [f'{d} {c}' for d in DL for c in ('Healthy', 'Diseased')]
_, _, r1, c1 = write_df(ws, SD_, 5, 1, fmt={c: '0.0000' for c in SD_.columns[1:]})
for k, d in enumerate(DL):
    col = c1 + 1 + k
    ws.cell(5, col, f'{d} D-H').font = HDR_FONT; ws.cell(5, col).fill = HDR_FILL
    hcol, dcol = get_column_letter(2 + 2 * k), get_column_letter(3 + 2 * k)
    for rr in range(6, r1 + 1):
        ws.cell(rr, col, f'={dcol}{rr}-{hcol}{rr}').number_format = '0.0000'
for k, d in enumerate(DL):
    scatter_lines(ws, f'{get_column_letter(c1 + 6)}{5 + 21 * k}', f'Mean reflectance, {d}', 1, [2 + 2 * k, 3 + 2 * k], 5, r1, [COL_H, COL_D], yt='Reflectance', w=17, h=10)
scatter_lines(ws, f'{get_column_letter(c1 + 16)}5', 'Difference spectra (D - H) by date', 1, list(range(c1 + 1, c1 + 5)), 5, r1, DATEC, yt='Reflectance difference', w=17, h=10)
F1m = T('bandwise_by_date.csv'); F1m = F1m[(F1m.branch == 'raw') & (F1m.family == 'FD1') & (F1m.date == 'All')]
r2 = r1 + 4
label(ws, r2 - 1, 1, 'First-derivative mean spectra (all dates)')
write_df(ws, F1m[['wl', 'mean_H', 'mean_D', 'diff']].rename(columns={'wl': 'Wavelength_nm', 'mean_H': 'FD1 Healthy', 'mean_D': 'FD1 Diseased', 'diff': 'FD1 D-H'}), r2, 1, fmt={'FD1 Healthy': '0.000000', 'FD1 Diseased': '0.000000', 'FD1 D-H': '0.000000'}, freeze=False)
scatter_lines(ws, f'{get_column_letter(c1 + 16)}27', 'First-derivative spectra', 1, [2, 3], r2, r2 + len(F1m), [COL_H, COL_D], yt='dR/dλ', w=17, h=10)

# ============================================================ 05 band-wise
ws = sheet('05_Bandwise_Stats', 'Step 4 - Band-wise statistics per date (raw reflectance and first derivative)',
           "Hedges' g > 0: diseased higher. q = BH-FDR within date. Sensitive regions: >= 2 adjacent 10-nm bands with q < 0.05 and the same sign on >= 3 of 4 dates.",
           'Mandal et al. 2022, 2023; Benjamini & Hochberg 1995; Hedges 1981; Richards & Jia 2006')
BW = T('bandwise_by_date.csv'); BW = BW[BW.branch == 'raw']
wide = {'Wavelength_nm': WL10}
for fam in ('REF', 'FD1'):
    for met in ('g', 'AUC', 'q'):
        for d in DL:
            wide[f'{fam} {met} {d}'] = BW[(BW.family == fam) & (BW.date == d)][met].to_numpy()
    wide[f'{fam} JM all dates'] = BW[(BW.family == fam) & (BW.date == 'All')]['JM'].to_numpy()
    wide[f'{fam} r_pb all dates'] = BW[(BW.family == fam) & (BW.date == 'All')]['r_pb'].to_numpy()
W = pd.DataFrame(wide)
_, _, r1, c1 = write_df(ws, W, 5, 1, fmt={c: '0.0E+00' for c in W.columns if ' q ' in c})
for k, fam in enumerate(('REF', 'FD1')):
    base = 2 + k * 14
    diverge(ws, f'{get_column_letter(base)}6:{get_column_letter(base + 3)}{r1}')
    heat(ws, f'{get_column_letter(base + 4)}6:{get_column_letter(base + 7)}{r1}', mn=0.5, mx=1.0)
    scatter_lines(ws, f'{get_column_letter(c1 + 2)}{5 + 21 * k}', f'AUC by date - {FAMILY_LABEL[fam]}', 1, list(range(base + 4, base + 8)), 5, r1, DATEC, yt='AUC', w=18, h=10)
REG = T('sensitive_regions.csv')
label(ws, 48, c1 + 2, 'Sensitive regions (stable on >= 3 dates)')
write_df(ws, REG, 49, c1 + 2, freeze=False)
ws.freeze_panes = 'B6'

# ============================================================ 06 feature screening
SCR = T('feature_screening_all.csv')
ws = sheet('06_Feature_Screening', 'Step 6 - Screening of every feature of every family (raw branch)',
           'Mean AUC over the 4 dates (direction-free); score = mean AUC if the direction is the same on all dates, else 0. n_dates_q05 = dates with FDR q < 0.05.',
           'Tian et al. 2021; Lv et al. 2023; Hanley & McNeil 1982')
FS = T('feature_screening_family_summary.csv'); FS = FS[FS.branch == 'raw'].drop(columns='branch')
FS.insert(1, 'Family name', FS['family'].map(FAMILY_LABEL))
_, _, r1, _ = write_df(ws, FS, 5, 1)
bar(ws, 'J5', 'Best stable feature per family (mean AUC)', 2, [6], 5, r1, [COL_4], 'Mean AUC', w=16, h=8, ymin=0.5, ymax=1.0)
TP = T('feature_screening_top10.csv')
cols = ['family', 'feature', 'direction', 'n_dates_q05', 'mean_AUC', 'min_AUC'] + [f'AUC_{d}' for d in DL] + [f'g_{d}' for d in DL]
label(ws, r1 + 3, 1, 'Top-10 features per family')
_, _, r2, _ = write_df(ws, TP[cols], r1 + 4, 1, widths={'feature': 40}, freeze=False)
heat(ws, f'E{r1 + 5}:J{r2}', mn=0.5, mx=1.0); diverge(ws, f'K{r1 + 5}:N{r2}')
label(ws, r2 + 3, 1, 'All features (raw branch)')
ALL = SCR[SCR.branch == 'raw'][cols + ['score', 'pooled_AUC', 'pooled_JM', 'sign_consistent']].sort_values('score', ascending=False)
write_df(ws, ALL, r2 + 4, 1, widths={'feature': 40}, freeze=False)
ws.freeze_panes = None

# ============================================================ 07 VI
ws = sheet('07_Vegetation_Indices', 'Step 6a - 87 vegetation indices: definitions and separability',
           'Definitions from sheet 26 of the source workbooks. Disease-specific indices (HI, PMI, LRDSI, CLSI, SBRI) were developed for other pathogens with similar symptoms.',
           'Mahlein et al. 2013; Ashourloo et al. 2014; Apan et al. 2004; see 33_References')
VD = pd.read_csv(os.path.join(CACHE, 'vi_definitions.csv'))
VD.columns = ['Index', 'Full name', 'Equation', 'Reference', 'Group', 'Source']
V = SCR[(SCR.branch == 'raw') & (SCR.family == 'VI')][['feature', 'direction', 'n_dates_q05', 'mean_AUC', 'min_AUC'] + [f'AUC_{d}' for d in DL] + ['score']].rename(columns={'feature': 'Index'})
V = V.merge(VD[['Index', 'Full name', 'Equation', 'Reference', 'Group']], on='Index', how='left').sort_values('score', ascending=False)
_, _, r1, _ = write_df(ws, V, 5, 1, widths={'Full name': 34, 'Equation': 40, 'Reference': 26})
heat(ws, f'D6:I{r1}', mn=0.5, mx=1.0)
bar(ws, 'Q5', 'Top-15 vegetation indices (mean AUC)', 1, [4], 5, 20, [COL_3], 'Mean AUC', horizontal=True, w=14, h=11, ymin=0.5, ymax=1.0)

# ============================================================ 08 CR, red edge, derivatives, CWT
ws = sheet('08_CR_RedEdge_Deriv', 'Step 6b - Continuum removal, red-edge parameters, derivatives and CWT',
           'Red-edge parameters by date (Mandal et al. 2022 style table) and the CWT mean-AUC scalogram (scale x wavelength).',
           'Clark & Roush 1984; Kokaly & Clark 1999; Horler et al. 1983; Guyot & Baret 1988; Dawson & Curran 1998; Cho & Skidmore 2006; Gong et al. 2002; Cheng et al. 2011')
RE = T('red_edge_by_date.csv')
_, _, r1, _ = write_df(ws, RE, 5, 1, widths={'Parameter': 40}, fmt={'p_Welch': '0.0E+00'})
cr = SCR[(SCR.branch == 'raw') & (SCR.family == 'CR')].sort_values('score', ascending=False)[['feature', 'direction', 'n_dates_q05', 'mean_AUC', 'min_AUC'] + [f'AUC_{d}' for d in DL]]
label(ws, 5, 11, 'Continuum-removal parameters ranked')
_, _, rc, _ = write_df(ws, cr, 6, 11, widths={'feature': 40}, freeze=False)
heat(ws, f'N7:S{rc}', mn=0.5, mx=1.0)
cw = SCR[(SCR.branch == 'raw') & (SCR.family == 'CWT')].copy()
cw['wl'] = cw.feature.str.extract(r'WF(\d+)_').astype(int); cw['scale'] = cw.feature.str.extract(r'_s(\d)').astype(int)
P = cw.pivot(index='wl', columns='scale', values='mean_AUC'); P.columns = [f'scale 2^{c}' for c in P.columns]
P = P.reset_index().rename(columns={'wl': 'Wavelength_nm'})
label(ws, 5, 21, 'CWT mean AUC (rows = wavelength, columns = scale)')
_, _, rcw, _ = write_df(ws, P, 6, 21, freeze=False)
heat(ws, f'V7:AC{rcw}', mn=0.5, mx=1.0)
image(ws, 'Fig09_CWT_scalogram.png', 'AE6', width=760)
image(ws, 'Fig07_feature_screening.png', 'AE24', width=900)
ws.freeze_panes = None

# ============================================================ 09 optimised index
ws = sheet('09_Optimised_Index', 'Step 6c - Exhaustive two-band index search (NDSI, SR, DI) on 10-nm bands',
           'Score = mean r2 with disease status over the 4 dates, kept only when the sign agrees on every date. Join-free: bands within 10 nm of the 1000/1800 nm detector joins excluded. In CV this search is repeated inside every training fold.',
           'Mandal et al. 2023; Tian et al. 2021; Zhu et al. 2017; Lv et al. 2023')
IX = T('optimised_index_top_pairs.csv'); IX = IX[IX.branch == 'raw'].drop(columns='branch')
_, _, r1, _ = write_df(ws, IX, 5, 1)
heat(ws, f'F6:J{r1}', mn=0, mx=0.7)
WO = T('workbook_optimised_indices.csv').pivot(index='Index', columns='Date', values='AUC').reset_index()
label(ws, 5, 13, "Source workbooks' own optimised indices (1-nm pairs chosen on all plots of the date - descriptive only, optimistic)")
write_df(ws, WO, 6, 13, widths={'Index': 46}, freeze=False)
image(ws, 'Fig08_optimised_index_map.png', f'A{r1 + 3}', width=520)
MX = T('ndsi_sr_r2_matrix_20nm.csv').rename(columns={'Unnamed: 0': 'nm'})
label(ws, r1 + 32, 1, 'r2 matrix at 20-nm spacing (upper triangle NDSI, lower triangle SR)')
_, _, rm, cm = write_df(ws, MX, r1 + 33, 1, freeze=False)
heat(ws, f'B{r1 + 34}:{get_column_letter(cm)}{rm}', lo='000004', mid='B73779', hi='FCFDBF', mn=0, mx=0.6)
ws.freeze_panes = None

# ============================================================ 10 mixed models
ws = sheet('10_Mixed_Models', 'Step 7 - Linear mixed models (repeated measures of the same plots over 4 dates)',
           'z(feature) ~ disease + date + variety + (1 | plot), REML; disease x date tested by a likelihood-ratio test (ML fits, 3 df). Effect in SD units. ICC = between-plot share of the residual variance.',
           'Bates et al. 2015; Benjamini & Hochberg 1995')
LM = T('mixed_models.csv')
_, _, r1, _ = write_df(ws, LM, 5, 1, widths={'Feature': 40}, fmt={'p_disease': '0.0E+00', 'q_disease': '0.0E+00', 'p_disease_x_date': '0.0E+00', 'q_interaction': '0.0E+00'})
diverge(ws, f'C6:C{r1}', 2)
r = 5
for txt, f in (('Features tested', f'=COUNTA(B6:B{r1})'), ('Disease effect q < 0.05', f'=COUNTIF(I6:I{r1},"<0.05")'), ('Disease x date q < 0.05', f'=COUNTIF(J6:J{r1},"<0.05")')):
    ws.cell(r, 13, txt).font = BOLD; ws.cell(r, 14, f); r += 1

# ============================================================ 11 design controls
ws = sheet('11_Design_Controls', 'Step 8 - Design-based checks of the disease effect',
           'Controls occupy one block (plots 1-12), so disease is confounded with field position. (a) matched control: inoculated minus its own control in the same cell; (b) block contrast: the largest difference between the three inoculated blocks, used as a yardstick for field-position effects; (c) inoculation timing among diseased plots.',
           'Hurlbert 1984; Kruskal & Wallis 1952')
BC = T('block_control.csv'); MC = T('matched_control_effects.csv'); IT = T('inoculation_timing.csv')
bs = BC.groupby('family').agg(median_abs_d_control_vs_inoculated=('abs_d_control_vs_inoculated', 'median'), median_max_abs_d_between_blocks=('max_abs_d_between_blocks', 'median'),
                              median_ratio=('ratio', 'median'), share_ratio_above_1=('ratio', lambda s: (s > 1).mean())).reset_index()
_, _, r1, _ = write_df(ws, bs, 5, 1)
ws.cell(5, 6, 'Formula: ratio of medians').font = HDR_FONT; ws.cell(5, 6).fill = HDR_FILL
for rr in range(6, r1 + 1):
    ws.cell(rr, 6, f'=B{rr}/C{rr}').number_format = '0.00'
bar(ws, 'H5', 'Control vs inoculated, compared with block-to-block', 1, [2, 3], 5, r1, [COL_4, '9E9E9E'], '|d|', w=16, h=8)
mcs = MC.groupby(['family', 'date']).apply(lambda g: pd.Series(dict(features=len(g), share_p05=(g.p < 0.05).mean(), median_delta_SD=g.mean_delta_SD.median(), median_cells_same_sign=g.cells_same_sign.median()))).reset_index()
label(ws, r1 + 3, 1, 'Matched-control test (12 cells per date) - top-ranked features of each family')
_, _, r2, _ = write_df(ws, mcs, r1 + 4, 1, freeze=False)
its = IT.groupby(['family', 'date']).apply(lambda g: pd.Series(dict(share_KW_p05=(g.p_KW_inoc < 0.05).mean(), median_spearman=g.spearman_inoc.median()))).reset_index()
label(ws, r2 + 3, 1, 'Inoculation timing (D1-D4) among diseased plots: matched-control effect by timing')
write_df(ws, its, r2 + 4, 1, freeze=False)
label(ws, 5, 16, 'Feature-level detail')
write_df(ws, BC.merge(MC, on=['family', 'feature', 'date']), 6, 16, widths={'feature': 36}, fmt={'p': '0.0E+00', 'p_KW_blocks': '0.000'}, freeze=False)
image(ws, 'Fig10_design_controls_features.png', f'A{r2 + 40}', width=880)
ws.freeze_panes = None

# ============================================================ 12 PCA & PERMANOVA
ws = sheet('12_PCA_PERMANOVA', 'Step 9 - Multivariate structure: PCA, eta-squared and PERMANOVA',
           'PCA of SNV reflectance (pooled and after removing the date means). PERMANOVA: Euclidean distance, marginal sums of squares; disease permuted as whole plots within variety x inoculation cells (999 permutations).',
           'Anderson 2001; Barnes et al. 1989; Selvaprakash et al. 2026')
PV = T('pca_variance.csv')
_, _, r1, _ = write_df(ws, PV, 5, 1, fmt={c: '0.0' for c in PV.columns[1:]})
E2 = T('pca_eta2.csv')
label(ws, r1 + 2, 1, 'Eta-squared of each factor on the first five PCs')
_, _, r2, c2 = write_df(ws, E2, r1 + 3, 1, freeze=False)
heat(ws, f'C{r1 + 4}:{get_column_letter(c2)}{r2}', mn=0, mx=1)
PM = T('permanova.csv')
label(ws, r2 + 2, 1, 'PERMANOVA')
_, _, r3, _ = write_df(ws, PM, r2 + 3, 1, widths={'Response': 40}, fmt={'R2_pct': '0.00', 'p_perm': '0.000', 'SS': '0.00', 'Pseudo_F': '0.00'}, freeze=False)
bar(ws, f'J{r2 + 3}', 'PERMANOVA R2 (%) - SNV reflectance', 2, [6], r2 + 3, r2 + 3 + 7, [COL_4], 'R2 (%)', horizontal=True, w=15, h=8)
P = T('pca_scores.csv')
sc = pd.DataFrame({'PC1 healthy': np.where(P.label == 'Healthy', P.PC1, np.nan), 'PC2 healthy': np.where(P.label == 'Healthy', P.PC2, np.nan),
                   'PC1 diseased': np.where(P.label == 'Diseased', P.PC1, np.nan), 'PC2 diseased': np.where(P.label == 'Diseased', P.PC2, np.nan),
                   'dcPC1 healthy': np.where(P.label == 'Healthy', P.dcPC1, np.nan), 'dcPC2 healthy': np.where(P.label == 'Healthy', P.dcPC2, np.nan),
                   'dcPC1 diseased': np.where(P.label == 'Diseased', P.dcPC1, np.nan), 'dcPC2 diseased': np.where(P.label == 'Diseased', P.dcPC2, np.nan)})
sc = pd.concat([P[['plot', 'date', 'label', 'variety', 'inoc']], sc], axis=1)
rs = r3 + 3
label(ws, rs - 1, 1, 'PCA scores (plot-date)')
write_df(ws, sc, rs, 1, freeze=False)
for k, (nm, c0) in enumerate((('PCA (SNV reflectance)', 6), ('PCA after removing date means', 10))):
    ch = ScatterChart(); ch.title = nm; ch.style = 13; ch.x_axis.title = 'PC1'; ch.y_axis.title = 'PC2'
    for xc, yc, col in ((c0, c0 + 1, COL_H), (c0 + 2, c0 + 3, COL_D)):
        s = Series(Reference(ws, min_col=yc, min_row=rs, max_row=rs + len(sc)), Reference(ws, min_col=xc, min_row=rs + 1, max_row=rs + len(sc)), title_from_data=True)
        s.marker.symbol = 'circle'; s.marker.size = 5; s.graphicalProperties.line.noFill = True
        s.marker.graphicalProperties.solidFill = col; s.marker.graphicalProperties.line.solidFill = col
        ch.series.append(s)
    ch.x_axis.delete = False; ch.y_axis.delete = False; ch.width, ch.height = 15, 9
    ws.add_chart(ch, f'{get_column_letter(16 + 9 * k)}{rs}')
ws.freeze_panes = None

# ============================================================ 13 raw vs smoothed
ws = sheet('13_Raw_vs_Smoothed', 'Step 10 - Raw vs smoothed branch',
           'Separability (mean AUC) of each family computed from the raw and from the detector-join corrected + SG(11,2) smoothed plot averages; E1 repeats the CV on the smoothed branch (same folds, 10 repeats).',
           'Savitzky & Golay 1964; Hueni & Bialek 2017; Mandal et al. 2023')
RV = T('raw_vs_smooth_separability.csv')
_, _, r1, _ = write_df(ws, RV, 5, 1)
bar(ws, 'J5', 'Mean AUC per family: raw vs smoothed', 1, [2, 3], 5, r1, [COL_4, COL_3], 'Mean AUC', w=16, h=8, ymin=0.5)
if have('E1_branch_reps.csv') and have('cv_main_reps.csv'):
    E1 = summ(T('E1_branch_reps.csv'), ['scenario', 'clf'])
    MR = T('cv_main_reps.csv'); MR = MR[MR.rep < 10]
    Rw = summ(MR[MR.scenario.isin(E1.scenario.unique()) & MR.clf.isin(E1.clf.unique())], ['scenario', 'clf'])
    cmp_ = Rw[['scenario', 'clf', 'BA']].rename(columns={'BA': 'BA raw'}).merge(E1[['scenario', 'clf', 'BA']].rename(columns={'BA': 'BA smoothed'}), on=['scenario', 'clf'])
    cmp_.insert(1, 'Scenario', cmp_.scenario.map(SCENARIOS))
    label(ws, r1 + 18, 1, 'E1 - CV balanced accuracy, raw vs smoothed branch (same 10 x 4 folds)')
    _, _, r2, _ = write_df(ws, cmp_, r1 + 19, 1, widths={'Scenario': 40}, freeze=False)
    ws.cell(r1 + 19, 6, 'Smoothed - raw').font = HDR_FONT; ws.cell(r1 + 19, 6).fill = HDR_FILL
    for rr in range(r1 + 20, r2 + 1):
        ws.cell(rr, 6, f'=E{rr}-D{rr}').number_format = '0.000'
    diverge(ws, f'F{r1 + 20}:F{r2}', 0.05)
ws.freeze_panes = None

# ============================================================ 14 CV design
ws = sheet('14_CV_Design', 'Step 11 - Validation design, feature scenarios and classifiers',
           'Outer: 4 folds of whole variety x inoculation cells (each test fold = 3 control + 9 inoculated plots on all 4 dates, never seen in training), 20 repeats. Inner: 3 cell-folds of the training plots for selection and tuning.',
           'Varma & Simon 2006; Roberts et al. 2017; Ambroise & McLachlan 2002')
sc_tab = pd.DataFrame([(k, v) for k, v in SCENARIOS.items()], columns=['Scenario', 'Feature set'])
refs = {'S1': 'Zhang 2012; Terentev 2023', 'S2': 'Mandal 2022; Lv 2023', 'S3': 'Tsai & Philpot 1998', 'S4': 'Tsai & Philpot 1998', 'S5': 'Zhang 2012; Kokaly & Clark 1999',
        'S6': 'Mandal 2023; Mahlein 2013', 'S7': 'Mandal 2022; Gong 2002', 'S8': 'Mandal 2023; Tian 2021; Zhu 2017', 'S9': 'Lv 2023; Cheng 2011',
        'S10': 'Tian 2021; Lv 2023', 'S11': 'Huang 2020; Zhu 2017; Araujo 2001', 'S12': 'Mandal 2023; Leardi 1998'}
sc_tab['Source papers'] = sc_tab['Scenario'].map(refs)
_, _, r1, _ = write_df(ws, sc_tab, 5, 1, widths={'Feature set': 46, 'Source papers': 36})
clf_tab = pd.DataFrame([('LDA', 'Linear discriminant (shrinkage), equal priors', 'Zhang 2012; Tian 2021'), ('PLS-DA', 'PLS discriminant analysis, 1-16 LVs', 'Barker & Rayens 2003; Zhu 2017'),
                        ('LR', 'L2 logistic regression, class-balanced', 'Terentev 2023'), ('kNN', 'k-nearest neighbours (5/15/35), oversampled', 'Tian 2021'),
                        ('SVM', 'RBF support vector machine, class-balanced', 'Cortes & Vapnik 1995; Huang 2020'), ('LS-SVM', 'Least-squares SVM (kernel ridge form)', 'Suykens & Vandewalle 1999; Zhu 2017'),
                        ('RF', 'Random forest, 200 trees', 'Breiman 2001; Mandal 2023'), ('XGBoost', 'Gradient boosting, 300 trees', 'Chen & Guestrin 2016'),
                        ('ELM', 'Extreme learning machine', 'Huang et al. 2006; Zhu 2017'), ('MLP', 'Multilayer perceptron', 'Nguyen 2023')], columns=['Classifier', 'Description', 'Source'])
label(ws, r1 + 2, 1, 'Classifiers (hyper-parameters tuned in the inner CV by balanced accuracy)')
_, _, r2, _ = write_df(ws, clf_tab, r1 + 3, 1, widths={'Description': 46, 'Source': 36}, freeze=False)
P0 = plot_table(M); a0 = cell_folds(P0, 4, 1000); P0['Outer fold (repeat 1)'] = P0['plot'].map(a0) + 1
fc = P0.groupby('Outer fold (repeat 1)').agg(Plots=('plot', 'size'), Healthy=('y', lambda s: int((s == 0).sum())), Diseased=('y', 'sum'),
                                              Cells=('cell', lambda s: ', '.join(sorted(s.unique())))).reset_index()
label(ws, r2 + 2, 1, 'Composition of the outer folds in repeat 1')
write_df(ws, fc, r2 + 3, 1, widths={'Cells': 40}, freeze=False)
ws.freeze_panes = None

# ============================================================ 15 / 16 CV results
if have('cv_main_summary.csv'):
    SUM = T('cv_main_summary.csv'); REP = T('cv_main_reps.csv')
    ws16 = sheet('16_CV_Reps', 'Main CV - metrics of every repeat (20 repeats x 120 pipelines)', 'Each row pools the four outer test folds of one repeat (every plot-date predicted once). Source for the formulas in 15_CV_Results.')
    _, _, rr1, _ = write_df(ws16, REP[['scenario', 'clf', 'rep'] + METS + ['PR_AUC_Healthy', 'TN', 'FP', 'FN', 'TP']], 5, 1)
    ws = sheet('15_CV_Results', 'Step 11 - Main CV results: 12 feature scenarios x 10 classifiers',
               'Mean of 20 repeats of cell-grouped 4-fold CV (192 plot-dates). The yellow block recomputes the best pipeline from 16_CV_Reps with AVERAGEIFS / COUNTIFS and a t-based 95 % CI.',
               'Tian et al. 2021; Zhu et al. 2017; Huang et al. 2020; Mandal et al. 2023; Chicco & Jurman 2020')
    BA = SUM.pivot(index='scenario', columns='clf', values='BA_mean').loc[list(SCENARIOS), CLF_NAMES].reset_index()
    BA.insert(1, 'Feature set', BA['scenario'].map(SCENARIOS))
    _, _, r1, c1 = write_df(ws, BA, 5, 1, widths={'Feature set': 40})
    heat(ws, f'C6:{get_column_letter(c1)}{r1}', lo='F7FCF5', mid='74C476', hi='00441B')
    ws.cell(5, c1 + 1, 'Row max (formula)').font = HDR_FONT; ws.cell(5, c1 + 1).fill = HDR_FILL
    ws.cell(5, c1 + 2, 'Best classifier (formula)').font = HDR_FONT; ws.cell(5, c1 + 2).fill = HDR_FILL
    for rr in range(6, r1 + 1):
        ws.cell(rr, c1 + 1, f'=MAX(C{rr}:{get_column_letter(c1)}{rr})').number_format = '0.000'
        ws.cell(rr, c1 + 2, f'=INDEX($C$5:${get_column_letter(c1)}$5,MATCH({get_column_letter(c1 + 1)}{rr},C{rr}:{get_column_letter(c1)}{rr},0))')
    MCC = SUM.pivot(index='scenario', columns='clf', values='MCC_mean').loc[list(SCENARIOS), CLF_NAMES].reset_index()
    label(ws, r1 + 2, 1, 'MCC matrix')
    _, _, r2, _ = write_df(ws, MCC, r1 + 3, 1, freeze=False)
    heat(ws, f'B{r1 + 4}:{get_column_letter(len(CLF_NAMES) + 1)}{r2}', lo='F7FBFF', mid='6BAED6', hi='08306B')
    BS = T('cv_best_per_scenario.csv')
    bs = BS[['scenario', 'clf', 'BA_mean', 'BA_SD', 'BA_CI95_low', 'BA_CI95_high', 'Sensitivity_mean', 'Specificity_mean', 'MacroF1_mean', 'Kappa_mean', 'MCC_mean', 'ROC_AUC_mean']].copy()
    bs.insert(1, 'Feature set', bs['scenario'].map(SCENARIOS))
    label(ws, r2 + 2, 1, 'Best classifier of every feature scenario')
    _, _, r3, _ = write_df(ws, bs, r2 + 3, 1, widths={'Feature set': 40}, freeze=False)
    bar(ws, f'O{r2 + 3}', 'Best balanced accuracy per feature scenario', 1, [4], r2 + 3, r3, [COL_4], 'BA', w=17, h=9, ymin=0.6, ymax=1.0)
    B = T('best_pipelines.csv')
    label(ws, r3 + 2, 1, 'Selected pipelines')
    _, _, r4, _ = write_df(ws, B, r3 + 3, 1, widths={'Scenario_name': 40}, freeze=False)
    rr = r4 + 3
    from openpyxl.styles import PatternFill as PF
    Y = PF('solid', fgColor='FFF2CC')
    sc0, c0 = B['scenario'][0], B['clf'][0]
    ws.cell(rr, 1, 'Formula check of the best pipeline').font = BOLD
    for i, (k, v) in enumerate((('Scenario', sc0), ('Classifier', c0))):
        ws.cell(rr + 1 + i, 1, k).font = BOLD; c = ws.cell(rr + 1 + i, 2, v); c.font = INPUT; c.fill = Y
    lines = [('Repeats', f"=COUNTIFS('16_CV_Reps'!A:A,B{rr + 1},'16_CV_Reps'!B:B,B{rr + 2})"),
             ('Mean BA', f"=AVERAGEIFS('16_CV_Reps'!D:D,'16_CV_Reps'!A:A,B{rr + 1},'16_CV_Reps'!B:B,B{rr + 2})"),
             ('Mean MCC', f"=AVERAGEIFS('16_CV_Reps'!J:J,'16_CV_Reps'!A:A,B{rr + 1},'16_CV_Reps'!B:B,B{rr + 2})"),
             ('Mean AUC', f"=AVERAGEIFS('16_CV_Reps'!K:K,'16_CV_Reps'!A:A,B{rr + 1},'16_CV_Reps'!B:B,B{rr + 2})"),
             ('SD of BA (from summary)', float(B['BA'][0] * 0 + SUM[(SUM.scenario == sc0) & (SUM.clf == c0)]['BA_SD'].iloc[0])),
             ('95 % CI low', f'=B{rr + 4}-TINV(0.05,B{rr + 3}-1)*B{rr + 7}/SQRT(B{rr + 3})'),
             ('95 % CI high', f'=B{rr + 4}+TINV(0.05,B{rr + 3}-1)*B{rr + 7}/SQRT(B{rr + 3})')]
    for i, (k, f) in enumerate(lines):
        ws.cell(rr + 3 + i, 1, k).font = BOLD; c = ws.cell(rr + 3 + i, 2, f); c.number_format = '0.000'; c.fill = Y
    full = SUM[['scenario', 'clf'] + [f'{m}_mean' for m in METS] + ['BA_SD', 'BA_CI95_low', 'BA_CI95_high', 'PR_AUC_Healthy_mean']]
    label(ws, rr + 12, 1, 'All 120 pipelines')
    write_df(ws, full, rr + 13, 1, freeze=False)
    ws.freeze_panes = 'C6'

    # 17 comparison
    ws = sheet('17_Model_Comparison', 'Step 12 - Statistical comparison of classifiers and feature scenarios',
               'Friedman test on BA (blocks = scenario x repeat for classifiers; classifier x repeat for scenarios) with Nemenyi critical difference; best pipeline vs best of every other scenario: corrected resampled t-test on the 80 fold BAs and Wilcoxon signed-rank on the 20 repeat BAs (Holm).',
               'Demsar 2006; Nadeau & Bengio 2003; Wilcoxon 1945; Holm 1979')
    FT = T('friedman_tests.csv')
    _, _, r1, _ = write_df(ws, FT, 5, 1, fmt={'p': '0.0E+00'}, widths={'Comparison': 46})
    FC = T('friedman_classifiers.csv'); FSn = T('friedman_scenarios.csv')
    label(ws, r1 + 2, 1, 'Classifiers - average rank (1 = best)')
    _, _, r2, _ = write_df(ws, FC, r1 + 3, 1, freeze=False)
    bar(ws, f'H{r1 + 3}', 'Average Friedman rank of classifiers', 1, [2], r1 + 3, r2, [COL_3], 'Average rank', horizontal=True, w=14, h=8)
    label(ws, r2 + 2, 1, 'Feature scenarios - average rank')
    _, _, r3, _ = write_df(ws, FSn, r2 + 3, 1, widths={'Scenario_name': 40}, freeze=False)
    bar(ws, f'H{r2 + 3}', 'Average Friedman rank of feature scenarios', 4, [2], r2 + 3, r3, [COL_4], 'Average rank', horizontal=True, w=14, h=10)
    PT = T('pairwise_tests.csv')
    label(ws, r3 + 2, 1, 'Best pipeline vs best of every other scenario')
    write_df(ws, PT, r3 + 3, 1, widths={'Comparison': 30, 'Other': 40}, fmt={'p_corrected_t': '0.0E+00', 'p_Wilcoxon': '0.0E+00', 'p_Wilcoxon_Holm': '0.0E+00'}, freeze=False)

    # 18 best models
    ws = sheet('18_Best_Models', 'Step 13 - Best pipelines: confusion matrices, ROC and sub-group performance',
               'Confusion matrix of the repeat with the median BA (192 plot-dates). Metrics in yellow are Excel formulas of the counts. Sub-group metrics are averaged over the 20 repeats.',
               'Fawcett 2006; Cohen 1960; Chicco & Jurman 2020')
    CM = T('confusion_matrices.csv')
    _, _, r1, _ = write_df(ws, CM, 5, 1, widths={'Pipeline': 46})
    from openpyxl.styles import PatternFill as PF
    Y = PF('solid', fgColor='FFF2CC')
    heads = ['BA (formula)', 'OA (formula)', 'Sensitivity (formula)', 'Specificity (formula)', 'Kappa (formula)']
    for j, h in enumerate(heads):
        c = ws.cell(5, 13 + j, h); c.font = HDR_FONT; c.fill = HDR_FILL
    for rr in range(6, r1 + 1):
        tn, fp, fn, tp = f'D{rr}', f'E{rr}', f'F{rr}', f'G{rr}'
        n = f'({tn}+{fp}+{fn}+{tp})'
        po = f'(({tn}+{tp})/{n})'; pe = f'((({tn}+{fp})*({tn}+{fn})+({fn}+{tp})*({fp}+{tp}))/{n}^2)'
        for j, f in enumerate([f'=({tp}/({tp}+{fn})+{tn}/({tn}+{fp}))/2', f'={po}', f'={tp}/({tp}+{fn})', f'={tn}/({tn}+{fp})', f'=({po}-{pe})/(1-{pe})']):
            c = ws.cell(rr, 13 + j, f); c.number_format = '0.000'; c.fill = Y
    RC = T('roc_curves.csv')
    label(ws, r1 + 2, 1, 'Mean ROC curves (20 repeats)')
    _, _, r2, _ = write_df(ws, RC, r1 + 3, 1, freeze=False)
    tcols = [j + 1 for j, c in enumerate(RC.columns) if c.startswith('TPR_')]
    scatter_lines(ws, f'J{r1 + 3}', 'ROC curves (mean over repeats)', 1, tcols, r1 + 3, r2, [COL_4, COL_3, COL_H], xt='False-positive rate', yt='True-positive rate', w=15, h=10, xmin=0, xmax=1)
    SG = T('subgroup_performance.csv')
    label(ws, r2 + 2, 1, 'Performance by date, variety, inoculation timing and growth stage')
    _, _, r3, _ = write_df(ws, SG, r2 + 3, 1, freeze=False)
    sub = SG[(SG.Role == 'Best overall') & (SG.Factor == 'Date')]
    label(ws, r2 + 2, 14, 'Best overall - BA by date')
    _, _, r4, _ = write_df(ws, sub[['Level', 'BA', 'Sensitivity', 'Specificity']], r2 + 3, 14, freeze=False)
    bar(ws, f'T{r2 + 3}', 'Best pipeline: BA, sensitivity and specificity by date', 14, [15, 16, 17], r2 + 3, r4, [COL_4, COL_D, COL_H], ymin=0.5, ymax=1.0, w=16, h=8)
    LD = T('plot_level_decision.csv')
    label(ws, r3 + 2, 1, 'Plot decision across the 4 dates (mean vote of each plot)')
    write_df(ws, LD, r3 + 3, 1, freeze=False)
    ws.freeze_panes = None

    # 19 progression
    ws = sheet('19_Progression', 'Step 13b - Disease call through the season and by inoculation timing',
               'Share of the 20 repeats in which each plot-date was called diseased by the best pipeline, averaged by class, date and inoculation timing. Spearman / Kruskal-Wallis on the decision scores of the diseased plots.',
               'Kruskal & Wallis 1952')
    PG = T('oof_vote_by_date_inoc.csv')
    PG = PG[['label', 'Date', 'D1', 'D2', 'D3', 'D4']]
    _, _, r1, _ = write_df(ws, PG, 5, 1)
    ws.cell(5, 7, 'Mean (formula)').font = HDR_FONT; ws.cell(5, 7).fill = HDR_FILL
    for rr in range(6, r1 + 1):
        ws.cell(rr, 7, f'=AVERAGE(C{rr}:F{rr})').number_format = '0.000'
    dd_rows = [i for i, l in enumerate(PG.label) if l == 'Diseased']
    ch = LineChart(); ch.title = 'Diseased plots called diseased, by inoculation timing'; ch.y_axis.title = 'Share called diseased'; ch.style = 12
    r_lo, r_hi = 6 + dd_rows[0], 6 + dd_rows[-1]
    for j in range(3, 7):
        s = Series(Reference(ws, min_col=j, min_row=r_lo, max_row=r_hi), title=PG.columns[j - 1]); ch.series.append(s)
    ch.set_categories(Reference(ws, min_col=2, min_row=r_lo, max_row=r_hi)); ch.width, ch.height = 16, 8
    ch.x_axis.delete = False; ch.y_axis.delete = False
    ws.add_chart(ch, 'I5')
    label(ws, r1 + 2, 1, 'Tests')
    write_df(ws, T('oof_progression_tests.csv'), r1 + 3, 1, freeze=False)
    OP = T('oof_predictions.csv')
    label(ws, r1 + 10, 1, 'Out-of-fold predictions of every plot-date (mean over 20 repeats)')
    write_df(ws, OP, r1 + 11, 1, freeze=False)
    image(ws, 'Fig16_oof_progression.png', 'I23', width=820)
    ws.freeze_panes = None


def exp_sheet(name, title, note, ref, df, keys, chart=None, extra_tables=()):
    ws = sheet(name, title, note, ref)
    _, _, r1, c1 = write_df(ws, df, 5, 1, widths={k: 34 for k in df.columns if df[k].dtype == object})
    if chart:
        cat, vals, ttl = chart
        bar(ws, f'{get_column_letter(c1 + 2)}5', ttl, cat, vals, 5, r1, [COL_4, COL_3, COL_H, COL_D], 'BA', w=18, h=10, ymin=0.4, ymax=1.0)
    r = r1 + 3
    for lab, t in extra_tables:
        label(ws, r, 1, lab)
        _, _, r, _ = write_df(ws, t, r + 1, 1, freeze=False); r += 3
    ws.freeze_panes = None
    return ws


if have('E2_single_date_reps.csv'):
    E2 = summ(T('E2_single_date_reps.csv'), ['date', 'scenario', 'clf']); E2.insert(2, 'Feature set', E2['scenario'].map(SCENARIOS))
    best = E2.loc[E2.groupby(['date', 'scenario'])['BA'].idxmax()]
    wide = best.pivot(index='Feature set', columns='date', values='BA')[DL].reset_index()
    ws = exp_sheet('20_E2_Single_Date', 'E2 - Models trained and tested within one date (48 plots, cell-grouped 4-fold x 10)',
                   'Shows how early the plots can be separated and whether one date alone is enough. Top table: best classifier per scenario and date.', 'Tian et al. 2021; Lv et al. 2023',
                   wide, [], chart=(1, [2, 3, 4, 5], 'Best BA per feature set and date'), extra_tables=[('All results', E2)])
if have('E3_transfer.csv'):
    E3 = T('E3_transfer.csv'); E3['Feature set'] = E3['scenario'].map(SCENARIOS)
    b3 = E3.loc[E3.groupby(['kind', 'held_out', 'date_norm', 'scenario'])['BA'].idxmax()]
    lodo = b3[b3.kind == 'LODO'].pivot_table(index=['Feature set', 'date_norm'], columns='held_out', values='BA')[DL].reset_index()
    lovo = b3[b3.kind == 'LOVO'].pivot_table(index='Feature set', columns='held_out', values='BA').reset_index()
    exp_sheet('21_E3_Transfer', 'E3 - Transfer to an unseen date (LODO) or an unseen variety (LOVO)',
              'Train on 3 dates and predict the 4th, with or without per-date standardisation (Lv et al. 2023); train on 2 varieties and predict the 3rd. Best classifier per cell.', 'Terentev et al. 2023; Lv et al. 2023',
              lodo, [], chart=(1, [3, 4, 5, 6], 'LODO balanced accuracy by held-out date'), extra_tables=[('Leave-one-variety-out', lovo), ('All transfer results', E3)])
if have('E4_datenorm_reps.csv') and have('cv_main_reps.csv'):
    E4 = summ(T('E4_datenorm_reps.csv'), ['scenario', 'clf']); MR = T('cv_main_reps.csv'); MR = MR[MR.rep < 10]
    base = summ(MR[MR.scenario.isin(E4.scenario.unique()) & MR.clf.isin(E4.clf.unique())], ['scenario', 'clf'])
    c4 = base[['scenario', 'clf', 'BA']].rename(columns={'BA': 'BA without'}).merge(E4[['scenario', 'clf', 'BA']].rename(columns={'BA': 'BA with date normalisation'}), on=['scenario', 'clf'])
    c4.insert(1, 'Feature set', c4.scenario.map(SCENARIOS))
    c4['Label'] = c4['scenario'] + ' ' + c4['clf']
    exp_sheet('22_E4_Date_Norm', 'E4 - Per-date standardisation inside the main CV (same 10 x 4 folds)',
              'Every date is centred and scaled with all of its plots (labels unused) before the classifier.', 'Lv et al. 2023',
              c4[['Label', 'Feature set', 'BA without', 'BA with date normalisation']], [], chart=(1, [3, 4], 'Without vs with date normalisation'))
if have('E5_permutation_summary.csv'):
    E5s = T('E5_permutation_summary.csv'); E5 = T('E5_permutation.csv')
    ws = sheet('23_E5_Permutation', 'E5 - Label-permutation test of the classifiers',
               'Labels permuted as whole plots within variety x inoculation cells; the full CV is repeated for every permutation. p = (1 + #null BA >= observed) / (1 + #permutations). Yellow cells recompute p with COUNTIFS.',
               'Ojala & Garriga 2010')
    _, _, r1, _ = write_df(ws, E5s, 5, 1, fmt={'p_value': '0.0000'})
    rp = r1 + 4
    label(ws, rp - 1, 1, 'Null distribution (perm = 0 is the observed labelling)')
    _, _, r2, _ = write_df(ws, E5, rp, 1, freeze=False)
    from openpyxl.styles import PatternFill as PF
    ws.cell(5, 11, 'p (formula)').font = HDR_FONT; ws.cell(5, 11).fill = HDR_FILL
    for i in range(len(E5s)):
        rr = 6 + i
        f = (f"=(1+COUNTIFS($B${rp + 1}:$B${r2},A{rr},$C${rp + 1}:$C${r2},B{rr},$A${rp + 1}:$A${r2},\">0\",$D${rp + 1}:$D${r2},\">=\"&C{rr}))"
             f"/(1+COUNTIFS($B${rp + 1}:$B${r2},A{rr},$C${rp + 1}:$C${r2},B{rr},$A${rp + 1}:$A${r2},\">0\"))")
        c = ws.cell(rr, 11, f); c.number_format = '0.0000'; c.fill = PF('solid', fgColor='FFF2CC')
    image(ws, 'Fig19_permutation_test.png', 'M5', width=800)
    ws.freeze_panes = None
if have('E6_design_controls_reps.csv'):
    E6 = summ(T('E6_design_controls_reps.csv'), ['contrast', 'type', 'scenario', 'clf'])
    b6 = E6.loc[E6.groupby(['contrast', 'scenario'])['BA'].idxmax()]
    w6 = b6.pivot(index='contrast', columns='scenario', values='BA').reset_index()
    w6.columns = ['Contrast'] + [f'{c} {SCENARIOS[c][:22]}' for c in w6.columns[1:]]
    exp_sheet('24_E6_Block_Controls', 'E6 - Negative / positive controls of the field design',
              'Control vs each inoculated block (C vs R1/R2/R3) should be separable if the signal is disease; inoculated block vs block (R1 vs R2 ...) measures how much a classifier can learn from field position alone (both sides diseased). 12 vs 12 plots x 4 dates, cell-grouped CV x 10.',
              'Hurlbert 1984; Roberts et al. 2017', w6, [], chart=(1, [2, 3, 4], 'Balanced accuracy of each contrast (best classifier)'), extra_tables=[('All results', E6)])
if have('E7_ofc_reps.csv'):
    E7 = summ(T('E7_ofc_reps.csv'), ['feature_set', 'clf'], extra=('features',))
    w7 = E7.pivot(index='feature_set', columns='clf', values='BA').reset_index()
    exp_sheet('25_E7_OFC', 'E7 - Optimal feature combinations (OFC) from SFFS with LDA, kNN and SVM wrappers',
              'Disease-sensitive features (DSF) = top 5 % by ReliefF on >= 3 of 4 dates, |r| < 0.98, VIF < 10; SFFS with each wrapper gives an OFC that is then classified by 5 learners (Tian et al. 2021). Fully inside the training folds.',
              'Tian et al. 2021; Pudil et al. 1994', w7, [], chart=(1, [2, 3, 4, 5, 6], 'OFC balanced accuracy by classifier'), extra_tables=[('All results (features = median subset size)', E7)])
if have('E8_fs_reps.csv'):
    E8 = summ(T('E8_fs_reps.csv'), ['method', 'k', 'clf'])
    w8 = E8[E8.k == 10].pivot(index='method', columns='clf', values='BA').reset_index()
    exp_sheet('26_E8_FS_Methods', 'E8 - Best feature-selection methods of the researcher\'s filter / wrapper / embedded comparison',
              'SVM-RFE, LASSO path, CARS, ReliefF, SFFS (QDA criterion) and their Borda consensus applied to the combined plot-level pool (k = 5, 10, 15 non-redundant features, |r| < 0.95).',
              'Panda 2026 (R1); Guyon et al. 2002; Tibshirani 1996; Li et al. 2009; Kononenko 1994; Saeys et al. 2008', w8, [], chart=(1, [2, 3, 4, 5, 6], 'k = 10: balanced accuracy by classifier'), extra_tables=[('All results', E8)])
if have('E9_equal_leaves_reps.csv'):
    E9 = T('E9_equal_leaves_reps.csv')
    s9 = summ(E9, ['averaging', 'scenario', 'clf']); s9.insert(2, 'Feature set', s9.scenario.map(SCENARIOS).str.replace('Vegetation indices (87)', 'Vegetation indices (46, leaf pipeline)'))
    w9 = s9.loc[s9.groupby(['averaging', 'scenario'])['BA'].idxmax()].pivot(index='Feature set', columns='averaging', values='BA').reset_index()
    exp_sheet('27_E9_Equal_Leaves', 'E9 - Equal leaf-number check: plot means rebuilt from 3 random leaves per plot',
              f"Diseased plots average more leaves than controls, which lowers random noise. Plot means were rebuilt from the leaf spectra (re-built all-leaf means equal the workbook values; max |diff| = {E9['check_max_abs_diff'].iloc[0]:.1e}) and from 3 random leaves per plot-date (5 draws). If BA holds with 3 leaves, the separation is not a leaf-number artefact.",
              'Design check (this study)', w9, [], chart=(1, [2, 3], 'Best BA: all leaves vs 3 leaves per plot'), extra_tables=[('All results', s9)])
if have('leaf_vs_plot_comparison.csv'):
    LP = T('leaf_vs_plot_comparison.csv')
    exp_sheet('28_E10_Leaf_vs_Plot', 'E10 - Leaf-level vs plot-level discrimination', 'Leaf-level results from the previous chapter (same plots and dates; plot-grouped CV). Plot-date row of the leaf models = majority vote of the leaf predictions of each plot-date.',
              'Panda 2026 (R2)', LP, [], chart=(1, [4], 'Balanced accuracy by approach'))

# ============================================================ final features, selection, hyper-parameters
if have('final_features.csv'):
    ws = sheet('30_Final_Features', 'Step 15 - Final feature set (S10 robust selection on all 192 plot-dates)',
               'Selection: ReliefF top 10 % on >= 3 of 4 dates -> |r| < 0.98 -> VIF < 10 -> SFFS-LDA. Importance = drop in BA when a feature is permuted (SVM, cell-grouped 4-fold). VIF and r show no multicollinearity left.',
               'Tian et al. 2021; Lv et al. 2023; Dormann et al. 2013; Richards & Jia 2006')
    FIN = T('final_features.csv')
    _, _, r1, _ = write_df(ws, FIN, 5, 1, widths={'Feature': 40, 'Family': 28})
    bar(ws, 'P5', 'Permutation importance of the final features', 1, [12], 5, r1, [COL_4], 'Drop in BA', horizontal=True, w=16, h=9)
    C = T('final_features_corr.csv').rename(columns={'Unnamed: 0': 'Feature'})
    label(ws, r1 + 2, 1, 'Correlation matrix')
    _, _, r2, c2 = write_df(ws, C, r1 + 3, 1, freeze=False)
    diverge(ws, f'B{r1 + 4}:{get_column_letter(c2)}{r2}', 1)
    JM = T('final_features_JM.csv')
    label(ws, r2 + 2, 1, 'Multivariate J-M distance (0-2) and collinearity diagnostics')
    write_df(ws, JM, r2 + 3, 1, freeze=False)
    ws.freeze_panes = None
if have('selection_frequency.csv'):
    ws = sheet('31_Selection_Frequency', 'Feature-selection stability across the 80 outer training sets',
               'How often each feature was chosen inside the outer folds (LDA rows; selection does not depend on the classifier). S10 family shares show which families the combined selection relies on.',
               'Kuncheva 2007; Nogueira et al. 2018')
    FS10 = T('S10_family_share.csv')
    _, _, r1, _ = write_df(ws, FS10, 5, 1)
    bar(ws, 'F5', 'Families selected in S10 (% of selected features)', 3, [2], 5, r1, [COL_3], '%', horizontal=True, w=14, h=8)
    label(ws, r1 + 12, 1, 'Selection frequency')
    write_df(ws, T('selection_frequency.csv'), r1 + 13, 1, widths={'Feature': 40, 'Scenario_name': 36}, freeze=False)
    BF = T('band_selection_frequency.csv')
    write_df(ws, BF, 5, 14, freeze=False)
    scatter_lines(ws, 'R5', 'Band selection frequency (SPA, GA-PLS)', 14, [15, 16], 5, 5 + len(BF), [COL_4, COL_3], yt='% of folds', w=17, h=9)
    ws.freeze_panes = None
if have('hyperparameters.csv'):
    ws = sheet('32_Hyperparameters', 'Hyper-parameters chosen in the inner CV (most frequent) and median feature numbers', '')
    write_df(ws, T('hyperparameters.csv'), 5, 1, widths={'Most_frequent_params': 50})

# ============================================================ references
ws = sheet('33_References', 'References', '[P] = paper supplied for this thesis; [R] = the researcher\'s own work; others = methods and index sources.')
RF = pd.read_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'references.csv'))
write_df(ws, RF, 5, 1, widths={'Reference': 140, 'Used for': 50})
for rr in range(6, 6 + len(RF)):
    ws.cell(rr, 2).alignment = Alignment(wrap_text=True, vertical='top')

# ============================================================ README
ws = readme
ws['A1'] = 'White rust of Indian mustard - plot-level hyperspectral discrimination of healthy and diseased plots'; ws['A1'].font = TITLE_FONT
inp = json.load(open(os.path.join(CACHE, 'inputs.json')))
ws['A2'] = f"Inputs: {', '.join(inp['books'])}; treatment layout: {inp['treatment']}. 48 plots (12 control, 36 inoculated) x 4 dates = 192 plot-average spectra."; ws['A2'].font = NOTE_FONT
ws['A3'] = 'Every sheet is one analysis step; tables are plain cells and charts are native Excel charts (editable). Blue text = input cells; yellow cells = live formulas.'; ws['A3'].font = NOTE_FONT
ws['A5'] = 'Sheet'; ws['B5'] = 'Content'; ws['C5'] = 'Note'
for c in ('A5', 'B5', 'C5'):
    ws[c].font = HDR_FONT; ws[c].fill = HDR_FILL
for i, (n, t, no, _) in enumerate(INDEX, start=6):
    c = ws.cell(i, 1, n); c.hyperlink = f"#'{n}'!A1"; c.font = Font(name=FONT, color='0563C1', underline='single')
    ws.cell(i, 2, t).font = BODY; ws.cell(i, 3, no).font = NOTE_FONT
ws.column_dimensions['A'].width = 26; ws.column_dimensions['B'].width = 80; ws.column_dimensions['C'].width = 120
ws.sheet_view.showGridLines = False
order = ['00_README'] + sorted([s for s in wb.sheetnames if s != '00_README'])
wb._sheets = [wb[s] for s in order]
wb.save(OUT)
print('saved', OUT, len(wb.sheetnames), 'sheets')
