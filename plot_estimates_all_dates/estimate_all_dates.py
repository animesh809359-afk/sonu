"""Plot-wise estimates of biophysical and biochemical parameters for all four assessment dates.

Usage:
    python estimate_all_dates.py <scored_110226.xlsx> <scored_240226.xlsx> <scored_030326.xlsx> \
        <scored_130326.xlsx> <scores_03_03_26.xlsx> <treatment_detail.xlsx> <model_workbook.xlsx> \
        <prospect_d_spectra.txt> <output.xlsx>

For every plot and date the estimate combines
  1. the expected healthy value of its treatment on that date (Simulation sheet of the model workbook),
  2. its leaf scores -> pustule leaf area A -> effective severity s_eff = kappa x A (kappa fitted to the
     chlorophyll drop seen in the plot-average spectra, all dates pooled),
  3. its plot-average ASD spectrum (chlorophyll from MTCI through PROSPECT-D),
  4. the RWC and MSI measured on 03/03/2026 (sheet MSI of the 03/03 score file): they set the assay
     level and the disease effect for RWC and MSI on every date, and are reported as measured on 03/03.
The combination step is written as live formulas so weights and couplings stay editable.
"""
import sys

import numpy as np
import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter as CL
from scipy.optimize import brentq, minimize_scalar
from scipy.signal import savgol_filter
from scipy.special import expi

SCORED = dict(zip(["11/02/2026", "24/02/2026", "03/03/2026", "13/03/2026"], sys.argv[1:5]))
MEAS, LAYOUT, MODEL, SPEC, OUT = sys.argv[5:10]
DATES = list(SCORED)
DAI = {"11/02/2026": 6, "24/02/2026": 19, "03/03/2026": 26, "13/03/2026": 36}
MDATE = "03/03/2026"
AREA = {0: 0.0, 1: 2.5, 3: 7.5, 5: 18.0, 7: 38.0, 9: 75.0}   # leaf area (%) at each Bisht grade (mid-points)
LMA = {"V": 0.0038, "F": 0.0042, "P": 0.0046}               # g cm-2, as in the simulated dataset
N_LEAF = {"V": 1.50, "F": 1.60, "P": 1.75}
BROWN0 = {"V": 0.0, "F": 0.02, "P": 0.08}
WATER_SAT = 6.0
TOL = {"V1": 1.0, "V2": 1.1, "V3": 0.85}
STAGE = {"Vegetative": "V", "Flowering": "F", "Pod formation": "P"}
K_WATER = 15.0          # RWC/MSI disease response saturates early: R = -Rmax (1 - exp(-15 s))
DEV_CLIP = 0.5          # plot deviations from 03/03 are clipped to +/-50% before use

# ---------------------------------------------------------------- read the scored workbooks
P = {}                  # (date, plot) -> record
WL = None
for d, path in SCORED.items():
    rows = list(openpyxl.load_workbook(path, read_only=True, data_only=True).worksheets[0].iter_rows(values_only=True))
    hdr, data = rows[:7], rows[7:]
    if WL is None:
        WL = np.array([r[0] for r in data], float)
    block = []
    for j in range(1, len(hdr[0])):
        name = hdr[0][j]
        if name == "Wavelength":          # second copy of plots 13/34/38/41/42 on 13/03: not used
            break
        if name is None:                  # unnamed copies of spectra (plot 27 on 11/02): not used
            continue
        if isinstance(name, str) and name.endswith(".sco"):
            block.append(j)
            continue
        if block and isinstance(hdr[1][j], int):
            p = hdr[1][j]
            avg = np.array([r[j] for r in data], float)
            leafmean = np.array([[r[k] for k in block] for r in data], float).mean(1)
            assert np.nanmax(np.abs(avg - leafmean)) < 1e-9, (d, p)
            sc = [hdr[6][k] for k in block]
            P[(d, p)] = dict(date=d, plot=p, stage=hdr[3][j], hd=hdr[4][j], spectrum=avg, n=len(block),
                             scores=sc, leaves=[hdr[5][k] for k in block],
                             di=sum(sc) / (9 * len(sc)) * 100, area=float(np.mean([AREA[int(s)] for s in sc])))
        block = []
assert len(P) == 192

lay = {r[0]: dict(t=r[1] + r[2], sow=r[1], var=r[2], rep="Control" if r[3] not in ("R1", "R2", "R3") else r[3])
       for r in openpyxl.load_workbook(LAYOUT).active.iter_rows(min_row=2, values_only=True)}
for (d, p), e in P.items():
    e.update(lay[p])

mws = openpyxl.load_workbook(MODEL, data_only=True, read_only=True)["Simulation"]
mit = mws.iter_rows(min_row=2, values_only=True)
mh = next(mit)
H = {}
for r in mit:
    x = dict(zip(mh, r))
    if x["Severity class"] == "Healthy":
        H[(x["Date code"], x["Treatment"])] = x
for e in P.values():
    assert STAGE[e["stage"]] == H[(e["date"], e["t"])]["Stage"], (e["date"], e["plot"])

# measured 03/03 (one sampled leaf per plot)
mw = openpyxl.load_workbook(MEAS, data_only=True)["MSI"]
MRAW = {}
for r in mw.iter_rows(min_row=4, max_row=51, values_only=True):
    MRAW[r[0]] = dict(ec40=r[1], ec100=r[2], fw=r[8], tw=r[9], dw=r[10])
for p, m in MRAW.items():
    m["msi"] = (1 - m["ec40"] / m["ec100"]) * 100
    m["rwc"] = 100 * (m["fw"] - m["dw"]) / (m["tw"] - m["dw"])

# ---------------------------------------------------------------- PROSPECT-D (Feret et al. 2017)
spec = np.loadtxt(SPEC, comments="#")
_, NR, KAB, KCAR, KANT, KBROWN, KW, KM = spec.T


def tav(alpha, nr):
    n2 = nr * nr
    npx, nm = n2 + 1, n2 - 1
    a = (nr + 1) ** 2 / 2.0
    k = -(n2 - 1) ** 2 / 4.0
    sa = np.sin(np.deg2rad(alpha))
    b1 = np.sqrt((sa * sa - npx / 2) ** 2 + k) if alpha != 90 else 0.0
    b = b1 - (sa * sa - npx / 2)
    ts = (k ** 2 / (6 * b ** 3) + k / b - b / 2) - (k ** 2 / (6 * a ** 3) + k / a - a / 2)
    tp = (-2 * n2 * (b - a) / npx ** 2 - 2 * n2 * npx * np.log(b / a) / nm ** 2 + n2 * (1 / b - 1 / a) / 2
          + 16 * n2 ** 2 * (n2 ** 2 + 1) * np.log((2 * npx * b - nm ** 2) / (2 * npx * a - nm ** 2)) / (npx ** 3 * nm ** 2)
          + 16 * n2 ** 3 * (1 / (2 * npx * b - nm ** 2) - 1 / (2 * npx * a - nm ** 2)) / npx ** 3)
    return (ts + tp) / (2 * sa ** 2)


T40, T90 = tav(40.0, NR), tav(90.0, NR)


def prospect(N, cab, car, ant, brown, cw, cm):
    k = (cab * KAB + car * KCAR + ant * KANT + brown * KBROWN + cw * KW + cm * KM) / N
    tau = np.where(k > 0, (1 - k) * np.exp(-k) + k ** 2 * (-expi(-np.maximum(k, 1e-12))), 1.0)
    talf, ralf, t12, r12 = T40, 1 - T40, T90, 1 - T90
    t21 = t12 / NR ** 2
    r21 = 1 - t21
    den = 1 - r21 ** 2 * tau ** 2
    Ta = talf * tau * t21 / den
    Ra = ralf + r21 * tau * Ta
    t = t12 * tau * t21 / den
    r = r12 + r21 * tau * t
    D = np.sqrt((1 + r + t) * (1 + r - t) * (1 - r + t) * (1 - r - t))
    a = (1 + r * r - t * t + D) / (2 * r)
    b = (1 - r * r + t * t + D) / (2 * t)
    bN1 = b ** (N - 1)
    d2 = a * a * bN1 * bN1 - 1
    Rs = a * (bN1 * bN1 - 1) / d2
    return Ra + Ta * Rs * t / (1 - Rs * r)


def mtci(S, w0):
    R = lambda w: S[..., int(w - w0)]
    return (R(754) - R(709)) / (R(709) - R(681))


def cab_from_mtci(m, st, s_eff, cw, cm):
    f = lambda cab: mtci(savgol_filter(prospect(N_LEAF[st] * (1 - 0.15 * s_eff), cab, cab / 5.5, 0.4,
                                                 BROWN0[st] + 0.6 * s_eff, cw, cm), 21, 2), 400) - m
    return brentq(f, 2, 150)


# ---------------------------------------------------------------- spectral features
Rw = lambda S, w: S[int(w - WL[0])]
for e in P.values():
    S = savgol_filter(e["spectrum"], 21, 2)
    d1 = np.gradient(S)
    e.update(
        MTCI=float(mtci(S, WL[0])),
        NDVI=float((Rw(S, 800) - Rw(S, 670)) / (Rw(S, 800) + Rw(S, 670))),
        CIre=float(Rw(S, 780) / Rw(S, 710) - 1),
        REIP=float(680 + np.argmax(d1[int(680 - WL[0]):int(760 - WL[0])])),
        ARI=float(1 / Rw(S, 550) - 1 / Rw(S, 700)),
        NDWI=float((Rw(S, 860) - Rw(S, 1240)) / (Rw(S, 860) + Rw(S, 1240))),
        R800=float(Rw(S, 800)), R670=float(Rw(S, 670)),
    )

# ---------------------------------------------------------------- kappa: model chlorophyll response vs spectral drop
ELAST = 1.13             # d ln MTCI / d ln Cab from PROSPECT-D at 35-45 ug cm-2
hplot = {(d, lay[p]["t"]): p for d in DATES for p in range(1, 13)}
for e in P.values():
    ref = P[(e["date"], hplot[(e["date"], e["t"])])]
    e["chl_rel"] = (e["MTCI"] / ref["MTCI"]) ** (1 / ELAST) if e["rep"] != "Control" else 1.0


def model_tot(s, t):
    ra = -0.65 * (1 - np.exp(-3.2 * s))
    rb = -0.55 * (1 - np.exp(-3.0 * s))
    return (1.25 * (1 + ra * t) + 0.45 * (1 + rb * t)) / 1.70


def fit_kappa(es):
    A = np.array([e["area"] / 100 for e in es])
    tl = np.array([TOL[e["var"]] for e in es])
    cr = np.array([e["chl_rel"] for e in es])
    res = minimize_scalar(lambda kp: np.sum((np.log(model_tot(kp * A, tl)) - np.log(cr)) ** 2), bounds=(0.01, 3), method="bounded")
    return float(res.x), float(np.sqrt(res.fun / len(es))), float(np.mean(cr)), float(np.mean(A))


inoc = [e for e in P.values() if e["rep"] != "Control"]
KFIT = {d: fit_kappa([e for e in inoc if e["date"] == d]) for d in DATES}
KFIT["All dates"] = fit_kappa(inoc)
KAPPA = round(KFIT["All dates"][0], 2)
for e in P.values():
    e["s_eff"] = KAPPA * e["area"] / 100


# ---------------------------------------------------------------- model priors (model workbook equations)
def R(code, s):
    if code in ("RWC", "MSI"):
        return -1.0 * (1 - np.exp(-K_WATER * s))          # amplitude set by calibration below
    if code == "Car":
        return -0.40 * (1 - np.exp(-3 * s)) + 0.10 * (s / 0.10) * np.exp(1 - s / 0.10)
    sign, rmax, k = {"Pn": (-1, 0.75, 4.4), "gs": (-1, 0.65, 3.0), "Ci": (1, 0.30, 4.0), "LAI": (-1, 0.45, 2.5),
                     "ChlA": (-1, 0.65, 3.2), "ChlB": (-1, 0.55, 3.0), "Anth": (1, 0.60, 3.0),
                     "Prot": (-1, 0.15, 3.0)}[code]
    return sign * rmax * (1 - np.exp(-k * s))


# RWC and MSI calibration on 03/03: assay level from healthy plots, disease amplitude from inoculated plots
CAL = {}
m_e = [P[(MDATE, p)] for p in range(1, 49)]
for code, key in (("RWC", "rwc"), ("MSI", "msi")):
    hm = np.mean([MRAW[e["plot"]][key] for e in m_e if e["rep"] == "Control"])
    hmod = np.mean([H[(MDATE, e["t"])][f"{code} healthy"] for e in m_e if e["rep"] == "Control"])
    level = hm / hmod
    im = np.mean([MRAW[e["plot"]][key] for e in m_e if e["rep"] != "Control"])
    ratio = im / hm
    shape = np.mean([-R(code, e["s_eff"]) * TOL[e["var"]] for e in m_e if e["rep"] != "Control"])
    rmax = (1 - ratio) / shape
    CAL[code] = dict(meas_h=hm, model_h=hmod, level=level, meas_i=im, ratio=ratio, rmax=rmax)

CODES = ["RWC", "MSI", "Pn", "gs", "Ci", "LAI", "ChlA", "ChlB", "Car", "Anth", "Prot"]
for e in P.values():
    h, s, tl = H[(e["date"], e["t"])], e["s_eff"], TOL[e["var"]]
    pri = {}
    for c in CODES:
        base = h[f"{c} healthy"]
        if c in CAL:
            pri[c] = base * CAL[c]["level"] * (1 + CAL[c]["rmax"] * R(c, s) * tl)
        else:
            pri[c] = base * (1 + R(c, s) * tl)
    pri["E"] = h["E healthy"] * pri["gs"] / h["gs healthy"] * (1 + 0.25 * s)
    e["prior"], e["E_H"], e["gs_H"] = pri, h["E healthy"], h["gs healthy"]

# plot deviation from the calibrated expectation on 03/03 (used, shrunk, as a persistent plot effect)
for p in range(1, 49):
    e = P[(MDATE, p)]
    for code, key in (("RWC", "rwc"), ("MSI", "msi")):
        dev = MRAW[p][key] / e["prior"][code] - 1
        for d in DATES:
            P[(d, p)][f"{code}_dev"] = float(np.clip(dev, -DEV_CLIP, DEV_CLIP))

# spectral chlorophyll (mg g-1 FW)
for e in P.values():
    st, s = STAGE[e["stage"]], e["s_eff"]
    rwc = MRAW[e["plot"]]["rwc"] if e["date"] == MDATE else e["prior"]["RWC"]
    cw = WATER_SAT * LMA[st] * rwc / 100
    cm = LMA[st] * (1 - 0.10 * s)
    e["Cab_area"] = cab_from_mtci(e["MTCI"], st, s, cw, cm)
    e["FW_area"] = cw + cm
    e["chl_spec"] = e["Cab_area"] / (e["FW_area"] * 1000)

# ---------------------------------------------------------------- workbook
F = Font(name="Arial", size=10)
FB = Font(name="Arial", size=10, bold=True)
FW = Font(name="Arial", size=10, bold=True, color="FFFFFF")
FT = Font(name="Arial", size=12, bold=True, color="1F4D2B")
FR = Font(name="Arial", size=10, bold=True, color="C00000")
FIN = Font(name="Arial", size=10, color="0000FF")
HDR = PatternFill("solid", fgColor="1F4D2B")
SUB = PatternFill("solid", fgColor="D9E1DA")
YEL = PatternFill("solid", fgColor="FFFF00")
MEASF = PatternFill("solid", fgColor="DDEBF7")
THIN = Side(style="thin", color="BFBFBF")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical="center", horizontal="center")


def put(ws, r, c, v, font=F, fill=None, fmt=None, align=None):
    cell = ws.cell(row=r, column=c, value=v)
    cell.font, cell.border = font, BOX
    if fill:
        cell.fill = fill
    if fmt:
        cell.number_format = fmt
    if align:
        cell.alignment = align
    return cell


def header(ws, r, cols, widths=None, fill=HDR, font=FW):
    for j, h in enumerate(cols, start=1):
        put(ws, r, j, h, font, fill, align=WRAP)
    ws.row_dimensions[r].height = 42
    if widths:
        for j, w in enumerate(widths, start=1):
            ws.column_dimensions[CL(j)].width = w


wb = openpyxl.Workbook()
rd = wb.active
rd.title = "README"
kf = KFIT["All dates"]
lines = [
    ("PLOT-WISE ESTIMATES OF BIOPHYSICAL AND BIOCHEMICAL PARAMETERS - 11/02, 24/02, 03/03 AND 13/03/2026", FT),
    ("ESTIMATED VALUES, NOT LABORATORY MEASUREMENTS - except RWC and MSI on 03/03/2026, which are your measured values (blue cells). "
     "Use the estimates as expected plot values, to check lab data, as priors and to test spectra-to-trait models; report them as estimates.", FR),
    ("", F),
    ("HOW EACH PLOT-DATE VALUE IS BUILT", FB),
    ("1. Healthy baseline: expected healthy value of the plot's treatment on that date from the model workbook (stage, sampled leaf, "
     "variety, weekly heat and VPD of that date included).", F),
    ("2. Severity: leaf scores of the scanned leaves -> pustule leaf area (grade mid-points 0, 2.5, 7.5, 18, 38, 75%) -> plot mean A -> "
     f"s_eff = kappa x A. kappa = {KAPPA} was fitted, all dates pooled, so that the model's chlorophyll response matches the "
     "chlorophyll drop in your plot-average spectra (MTCI of each inoculated plot / MTCI of the healthy plot of the same treatment and "
     "date). Per-date fits are in the Calibration sheet.", F),
    ("3. Spectral chlorophyll: plot-average spectrum (your average column) -> MTCI (insensitive to offset and gain) -> chlorophyll a+b "
     "per leaf area by PROSPECT-D -> divided by fresh mass per area -> mg g-1 FW.", F),
    (f"4. RWC and MSI: your 03/03 measurements set the assay level (healthy measured / model = {CAL['RWC']['level']:.3f} for RWC, "
     f"{CAL['MSI']['level']:.3f} for MSI) and the disease effect (inoculated / healthy = {CAL['RWC']['ratio']:.3f} for RWC, "
     f"{CAL['MSI']['ratio']:.3f} for MSI) on every date. On 03/03 the measured values are reported; on other dates each plot keeps "
     "a share (Settings: plot_shrink) of its own 03/03 deviation as a persistent plot effect.", F),
    ("5. Final values (Estimates sheet, live formulas): total chlorophyll = weighted geometric mean of prior and spectral values; the "
     "ratio delta = final / prior chlorophyll adjusts Pn, gs (and E), Ci, protein and anthocyanin through the exponents in Settings. "
     "Chl a, Chl b and carotenoids keep the model's a/b and Car/Chl ratios.", F),
    ("6. Ranges: estimate x (1 -/+ 1.645 x CV) (about 90%).", F),
    ("", F),
    ("NOTES", FB),
    ("- Measured MSI is low on your assay scale (healthy mean "
     f"{CAL['MSI']['meas_h']:.1f}%); estimates for the other dates are on the same scale. Plots 2, 19 and 27 read 0-1.2% on 03/03 - "
     "check those assays.", F),
    ("- Measured RWC and MSI on 03/03 come from one sampled leaf per plot; within the inoculated plots they did not follow plot DI, "
     "so the disease effect is applied as a near-constant step for infected plots.", F),
    ("- Plot-average spectra mix the leaves you scanned (L3/L5/LL); estimates refer to that plot-average leaf.", F),
    ("- LAI is a canopy trait that leaf spectra cannot see; it follows the model prior.", F),
    ("- On 13/03 the duplicated copy of plots 13, 34, 38, 41, 42 is not used (main table only).", F),
    ("", F),
    ("SHEETS: Estimates | one sheet per parameter (plots x dates) | Ranges | Treatment_Summary | Inputs | Settings | Calibration | "
     "Measured_0303 | Spectral_Features", F),
]
for i, (t, f) in enumerate(lines, start=1):
    c = rd.cell(row=i, column=1, value=t)
    c.font = f
    c.alignment = Alignment(wrap_text=True, vertical="top")
    rd.row_dimensions[i].height = 15 * max(1, len(t) // 150 + 1)
rd.column_dimensions["A"].width = 160

# Settings
se = wb.create_sheet("Settings")
se.cell(row=1, column=1, value="Combination settings (yellow = editable)").font = FT
SET = [
    ("w_spec", "Weight of spectral chlorophyll in total chlorophyll (0-1)", 0.5),
    ("e_Pn", "Exponent of chlorophyll ratio on Pn", 0.5),
    ("e_gs", "Exponent of chlorophyll ratio on gs (E follows gs)", 0.4),
    ("e_Ci", "Exponent of chlorophyll ratio on Ci", -0.15),
    ("e_Prot", "Exponent of chlorophyll ratio on protein", 0.3),
    ("e_Anth", "Exponent of chlorophyll ratio on anthocyanin", -0.5),
    ("plot_shrink", "Share of a plot's 03/03 RWC/MSI deviation carried to other dates (0-1)", 0.3),
]
header(se, 2, ["Name", "Meaning", "Value"], [12, 70, 10])
SREF = {}
for i, (n, mtxt, v) in enumerate(SET, start=3):
    put(se, i, 1, n, FB)
    put(se, i, 2, mtxt)
    put(se, i, 3, v, FIN, YEL, "0.00")
    SREF[n] = f"Settings!$C${i}"
CV = {"RWC": 0.04, "MSI": 0.15, "Pn": 0.12, "gs": 0.18, "E": 0.18, "Ci": 0.06, "LAI": 0.12, "ChlA": 0.10,
      "ChlB": 0.12, "TotChl": 0.10, "Car": 0.12, "Anth": 0.30, "Prot": 0.12, "WUE": 0.15}
r0 = len(SET) + 5
se.cell(row=r0 - 1, column=1, value="Coefficients of variation for ranges (MSI widened to 0.15 for the measured spread)").font = FB
header(se, r0, ["Code", "", "CV"])
for i, (c, v) in enumerate(CV.items(), start=r0 + 1):
    put(se, i, 1, c, FB)
    put(se, i, 2, "")
    put(se, i, 3, v, FIN, YEL, "0.00")
    SREF["CV_" + c] = f"Settings!$C${i}"

# Calibration
ca = wb.create_sheet("Calibration")
ca.cell(row=1, column=1, value="Calibration of severity (kappa) and of RWC / MSI").font = FT
header(ca, 3, ["Dataset", "kappa fitted", "RMSE of ln(chl ratio)", "Mean spectral chl ratio (inoculated / own healthy)", "Mean pustule area A (%)"],
       [16, 12, 14, 22, 14])
for i, (k, (kp, rm, cr, a)) in enumerate(KFIT.items(), start=4):
    put(ca, i, 1, k, FB)
    put(ca, i, 2, kp, fmt="0.000")
    put(ca, i, 3, rm, fmt="0.000")
    put(ca, i, 4, cr, fmt="0.000")
    put(ca, i, 5, a * 100, fmt="0.0")
ca.cell(row=9, column=1, value=f"Used: kappa = {KAPPA} (all dates). s_eff = kappa x A.").font = FB
header(ca, 11, ["Trait", "Measured healthy mean 03/03", "Model healthy mean 03/03", "Assay level factor", "Measured inoculated mean",
                "Inoculated / healthy", "Fitted response amplitude"])
for i, c in enumerate(("RWC", "MSI"), start=12):
    x = CAL[c]
    for k, v in enumerate([c, x["meas_h"], x["model_h"], x["level"], x["meas_i"], x["ratio"], x["rmax"]], start=1):
        put(ca, i, k, v, FB if k == 1 else F, fmt=None if k == 1 else "0.000")
ca.cell(row=15, column=1, value=f"RWC and MSI response: R(s) = -amplitude x (1 - exp(-{K_WATER:g} s_eff)) x variety tolerance; amplitude chosen "
        "so the mean inoculated/healthy ratio on 03/03 equals the measured ratio.").font = F

# Measured 03/03 (formulas from the raw readings)
me = wb.create_sheet("Measured_0303")
me.cell(row=1, column=1, value="Measured on 03/03/2026 (your file 03_03_26.xlsx, sheet MSI; one sampled leaf per plot)").font = FT
header(me, 3, ["Plot", "EC 40 C (mS/cm)", "EC 100 C (mS/cm)", "MSI (%) = (1 - C1/C2) x 100", "FW (g)", "TW (g)", "DW (g)",
               "RWC (%) = (FW-DW)/(TW-DW) x 100"], [6, 11, 11, 14, 8, 8, 8, 16])
MROW = {}
for i, p in enumerate(range(1, 49), start=4):
    m = MRAW[p]
    for k, v in enumerate([p, m["ec40"], m["ec100"], f"=(1-B{i}/C{i})*100", m["fw"], m["tw"], m["dw"], f"=(E{i}-G{i})/(F{i}-G{i})*100"], start=1):
        put(me, i, k, v, FB if k in (1, 4, 8) else F, fmt="0.0" if k in (4, 8) else None)
    MROW[p] = i

ORDER = sorted(P, key=lambda k: (DATES.index(k[0]), 0 if P[k]["rep"] == "Control" else 1, P[k]["sow"], P[k]["var"], P[k]["rep"]))
ID = ["Assessment date", "DAI", "Plot", "Treatment", "Sowing", "Variety", "Replication", "Growth stage", "Plot DI (%)"]
IDW = [12, 5, 6, 10, 7, 7, 11, 13, 9]


def id_cells(ws, r, e):
    vals = [e["date"], DAI[e["date"]], e["plot"], e["t"], e["sow"], e["var"], e["rep"], e["stage"], round(e["di"], 4)]
    for j, v in enumerate(vals, start=1):
        put(ws, r, j, v, FB if j in (3, 4) else F, fmt="0.0" if j == 9 else None)


# Inputs
ip = wb.create_sheet("Inputs")
PRI = ["RWC", "MSI", "Pn", "gs", "E", "Ci", "LAI", "ChlA", "ChlB", "Car", "Anth", "Prot"]
ICOL = ID + ["Spectra (n)", "Mean leaf score", "Pustule leaf area A (%)", "s_eff", "MTCI", "Chl rel. to own healthy plot",
             "Cab spectral (ug cm-2)", "Fresh mass per area (g cm-2)", "Total chl spectral (mg g-1 FW)"] + \
           [f"{c} prior" for c in PRI] + ["RWC measured (03/03)", "MSI measured (03/03)", "RWC plot deviation 03/03",
                                          "MSI plot deviation 03/03"]
header(ip, 1, ICOL, IDW + [8, 9, 10, 8, 8, 10, 10, 10, 11] + [9] * len(PRI) + [11, 11, 11, 11])
IC = {h: j for j, h in enumerate(ICOL, start=1)}
INR = {}
for i, k in enumerate(ORDER, start=2):
    e = P[k]
    INR[k] = i
    id_cells(ip, i, e)
    vals = [e["n"], float(np.mean(e["scores"])), e["area"], e["s_eff"], e["MTCI"], e["chl_rel"], e["Cab_area"], e["FW_area"], e["chl_spec"]]
    fm = ["0", "0.00", "0.0", "0.000", "0.000", "0.000", "0.0", "0.0000", "0.000"]
    for j, (v, f_) in enumerate(zip(vals, fm), start=len(ID) + 1):
        put(ip, i, j, v, fmt=f_)
    for c in PRI:
        put(ip, i, IC[f"{c} prior"], e["prior"][c], fmt="0.000")
    if e["date"] == MDATE:
        put(ip, i, IC["RWC measured (03/03)"], f"=Measured_0303!H{MROW[e['plot']]}", fill=MEASF, fmt="0.0")
        put(ip, i, IC["MSI measured (03/03)"], f"=Measured_0303!D{MROW[e['plot']]}", fill=MEASF, fmt="0.0")
    else:
        put(ip, i, IC["RWC measured (03/03)"], "")
        put(ip, i, IC["MSI measured (03/03)"], "")
    put(ip, i, IC["RWC plot deviation 03/03"], e["RWC_dev"], fmt="+0.000;-0.000;0.000")
    put(ip, i, IC["MSI plot deviation 03/03"], e["MSI_dev"], fmt="+0.000;-0.000;0.000")
ip.freeze_panes = "D2"
ia = lambda col, r: f"Inputs!${CL(IC[col])}{r}"

# Estimates (formulas)
es = wb.create_sheet("Estimates")
EST = [
    ("RWC", "RWC (%)", "0.0"), ("MSI", "MSI (%)", "0.0"), ("Pn", "Pn (umol CO2 m-2 s-1)", "0.00"),
    ("gs", "gs (mol H2O m-2 s-1)", "0.000"), ("E", "E (mmol H2O m-2 s-1)", "0.00"), ("Ci", "Ci (umol mol-1)", "0"),
    ("LAI", "LAI (m2 m-2)", "0.00"), ("ChlA", "Chl a (ug mg-1 FW)", "0.000"), ("ChlB", "Chl b (ug mg-1 FW)", "0.000"),
    ("TotChl", "Total chl (ug mg-1 FW)", "0.000"), ("AB", "Chl a/b", "0.00"), ("Car", "Carotenoids (mg g-1 FW)", "0.000"),
    ("CarChl", "Car / total chl", "0.000"), ("Anth", "Anthocyanin (ug g-1 FW)", "0.0"), ("Prot", "Total protein (ug mg-1 FW)", "0.00"),
    ("WUE", "WUE Pn/E (umol mmol-1)", "0.00"), ("delta", "Chl final / prior (delta)", "0.000"), ("src", "RWC & MSI source", None),
]
header(es, 1, ID + [x[1] for x in EST], IDW + [10] * (len(EST) - 1) + [12])
EC = {x[0]: len(ID) + 1 + j for j, x in enumerate(EST)}
ec = lambda code, r: f"{CL(EC[code])}{r}"
ESR = {}
for i, k in enumerate(ORDER, start=2):
    e, r = P[k], INR[k]
    ESR[k] = i
    id_cells(es, i, e)
    pri_tot = f"({ia('ChlA prior', r)}+{ia('ChlB prior', r)})"
    meas_r, meas_m = ia("RWC measured (03/03)", r), ia("MSI measured (03/03)", r)
    f = {
        "TotChl": f"=EXP((1-{SREF['w_spec']})*LN({pri_tot})+{SREF['w_spec']}*LN({ia('Total chl spectral (mg g-1 FW)', r)}))",
        "delta": f"={ec('TotChl', i)}/{pri_tot}",
        "ChlA": f"={ec('TotChl', i)}*{ia('ChlA prior', r)}/{pri_tot}",
        "ChlB": f"={ec('TotChl', i)}*{ia('ChlB prior', r)}/{pri_tot}",
        "AB": f"={ec('ChlA', i)}/{ec('ChlB', i)}",
        "Car": f"={ec('TotChl', i)}*{ia('Car prior', r)}/{pri_tot}",
        "CarChl": f"={ec('Car', i)}/{ec('TotChl', i)}",
        "RWC": f'=IF({meas_r}<>"",{meas_r},{ia("RWC prior", r)}*(1+{SREF["plot_shrink"]}*{ia("RWC plot deviation 03/03", r)}))',
        "MSI": f'=IF({meas_m}<>"",{meas_m},{ia("MSI prior", r)}*(1+{SREF["plot_shrink"]}*{ia("MSI plot deviation 03/03", r)}))',
        "Pn": f"={ia('Pn prior', r)}*{ec('delta', i)}^{SREF['e_Pn']}",
        "gs": f"={ia('gs prior', r)}*{ec('delta', i)}^{SREF['e_gs']}",
        "E": f"={ia('E prior', r)}*{ec('gs', i)}/{ia('gs prior', r)}",
        "Ci": f"={ia('Ci prior', r)}*{ec('delta', i)}^{SREF['e_Ci']}",
        "LAI": f"={ia('LAI prior', r)}",
        "Anth": f"={ia('Anth prior', r)}*{ec('delta', i)}^{SREF['e_Anth']}",
        "Prot": f"={ia('Prot prior', r)}*{ec('delta', i)}^{SREF['e_Prot']}",
        "WUE": f"={ec('Pn', i)}/{ec('E', i)}",
        "src": f'=IF({meas_r}<>"","Measured","Estimated")',
    }
    for code, _, fm in EST:
        fill = MEASF if code in ("RWC", "MSI") and e["date"] == MDATE else None
        put(es, i, EC[code], f[code], FB if code in ("Pn", "TotChl", "RWC") else F, fill, fm)
es.freeze_panes = "E2"
LASTE = len(ORDER) + 1
es.auto_filter.ref = f"A1:{CL(len(ID) + len(EST))}{LASTE}"

# One sheet per parameter: plots x dates
PSHEETS = [x for x in EST if x[0] not in ("delta", "src")]
for code, name, fm in PSHEETS:
    ps = wb.create_sheet(code if code not in ("AB", "CarChl", "TotChl") else {"AB": "Chl_ab", "CarChl": "Car_Chl", "TotChl": "Total_Chl"}[code])
    ps.cell(row=1, column=1, value=name + " - plot x date (from Estimates)").font = FT
    header(ps, 3, ["Plot", "Treatment", "Replication"] + [f"{d} ({DAI[d]} DAI)" for d in DATES] + ["Mean"], [6, 10, 11, 14, 14, 14, 14, 10])
    for i, p in enumerate(range(1, 49), start=4):
        e0 = P[(DATES[0], p)]
        put(ps, i, 1, p, FB)
        put(ps, i, 2, e0["t"], FB)
        put(ps, i, 3, e0["rep"])
        for j, d in enumerate(DATES, start=4):
            fill = MEASF if code in ("RWC", "MSI") and d == MDATE else None
            put(ps, i, j, f"=Estimates!{ec(code, ESR[(d, p)])}", fill=fill, fmt=fm)
        put(ps, i, 8, f"=AVERAGE(D{i}:G{i})", FB, fmt=fm)
    ps.freeze_panes = "D4"

# Ranges
rg = wb.create_sheet("Ranges")
RC = [x for x in EST if x[0] not in ("AB", "CarChl", "delta", "src")]
rh = ["Assessment date", "Plot", "Treatment"]
for _, nm, _ in RC:
    rh += [f"{nm} low", f"{nm} high"]
header(rg, 1, rh, [12, 6, 10] + [10] * (2 * len(RC)))
for i, k in enumerate(ORDER, start=2):
    put(rg, i, 1, k[0])
    put(rg, i, 2, k[1], FB)
    put(rg, i, 3, P[k]["t"], FB)
    for j, (code, _, fm) in enumerate(RC):
        src = f"Estimates!{ec(code, ESR[k])}"
        cv = SREF["CV_" + code]
        put(rg, i, 4 + 2 * j, f"={src}*(1-1.645*{cv})", fmt=fm)
        put(rg, i, 5 + 2 * j, f"={src}*(1+1.645*{cv})", fmt=fm)
rg.freeze_panes = "D2"

# Treatment summary (formulas)
ts = wb.create_sheet("Treatment_Summary")
ts.cell(row=1, column=1, value="Healthy control plot vs mean of inoculated R1-R3, by date (formulas on Estimates)").font = FT
SC = ["RWC", "MSI", "Pn", "gs", "E", "Ci", "LAI", "TotChl", "Car", "Anth", "Prot"]
th = ["Assessment date", "Treatment", "Growth stage", "Mean DI R1-R3 (%)"]
for c in SC:
    nm = next(x[1] for x in EST if x[0] == c)
    th += [f"{nm} healthy", f"{nm} R1-R3", "% change"]
header(ts, 2, th, [12, 10, 12, 10] + [9] * (3 * len(SC)))
rng = lambda col: f"Estimates!${col}$2:${col}${LASTE}"
TRE = [f"D{a}V{b}" for a in range(1, 5) for b in range(1, 4)]
r = 3
for d in DATES:
    for t in TRE:
        put(ts, r, 1, d)
        put(ts, r, 2, t, FB)
        put(ts, r, 3, P[(d, hplot[(d, t)])]["stage"])
        crit = f'{rng("A")},$A{r},{rng("D")},$B{r}'
        put(ts, r, 4, f'=AVERAGEIFS({rng("I")},{crit},{rng("G")},"<>Control")', fmt="0.0")
        for j, c in enumerate(SC):
            col = CL(EC[c])
            fm = next(x[2] for x in EST if x[0] == c)
            hc, dc, pc = 5 + 3 * j, 6 + 3 * j, 7 + 3 * j
            put(ts, r, hc, f'=AVERAGEIFS({rng(col)},{crit},{rng("G")},"Control")', fmt=fm)
            put(ts, r, dc, f'=AVERAGEIFS({rng(col)},{crit},{rng("G")},"<>Control")', fmt=fm)
            put(ts, r, pc, f"={CL(dc)}{r}/{CL(hc)}{r}-1", fmt="+0.0%;-0.0%;0.0%")
        r += 1
ts.freeze_panes = "C3"

# Spectral features
sf = wb.create_sheet("Spectral_Features")
FEATS = [("MTCI", "MTCI (R754-R709)/(R709-R681)", "0.000"), ("CIre", "CI red-edge R780/R710-1", "0.000"),
         ("NDVI", "NDVI (R800,R670)", "0.000"), ("REIP", "Red-edge position, max 1st derivative (nm)", "0"),
         ("ARI", "ARI 1/R550-1/R700", "0.000"), ("NDWI", "NDWI (R860,R1240)", "0.000"),
         ("R670", "R670", "0.000"), ("R800", "R800", "0.000")]
header(sf, 1, ID + [x[1] for x in FEATS], IDW + [13] * len(FEATS))
for i, k in enumerate(ORDER, start=2):
    id_cells(sf, i, P[k])
    for j, (key, _, fm) in enumerate(FEATS, start=len(ID) + 1):
        put(sf, i, j, P[k][key], fmt=fm)
sf.freeze_panes = "D2"

order = ["README", "Estimates"] + [s.title for s in wb.worksheets if s.title not in
                                   ("README", "Estimates", "Ranges", "Treatment_Summary", "Inputs", "Settings", "Calibration",
                                    "Measured_0303", "Spectral_Features")] + \
        ["Ranges", "Treatment_Summary", "Inputs", "Settings", "Calibration", "Measured_0303", "Spectral_Features"]
wb._sheets = [wb[n] for n in order]
wb.save(OUT)
print("kappa per date", {k: round(v[0], 3) for k, v in KFIT.items()})
print("RWC cal", {k: round(v, 3) for k, v in CAL["RWC"].items()})
print("MSI cal", {k: round(v, 3) for k, v in CAL["MSI"].items()})
print("saved", OUT)
