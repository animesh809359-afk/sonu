"""Build the one-sheet-per-parameter dataset workbook, including simulated ASD leaf spectra.

Usage:
    python build_dataset.py <model.xlsx> <prospect_d_spectra.txt> <output.xlsx>

<model.xlsx> is the recalculated White_Rust_Simulated_Parameters_IARI_2025-26.xlsx
(its Simulation sheet supplies all parameter values). <prospect_d_spectra.txt> is the
PROSPECT-D specific absorption file (dataSpec_PDB, Feret et al. 2017), e.g. the copy
shipped in the `prosail` Python package. Recalculate the output afterwards so the
Spectral_Indices formulas carry cached values.
"""
import sys

import numpy as np
import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter as CL
from scipy.special import expi

MODEL, SPEC, OUT = sys.argv[1:4]

# ---------------------------------------------------------------- styles
F = Font(name="Arial", size=9)
F_B = Font(name="Arial", size=9, bold=True)
F_T = Font(name="Arial", size=11, bold=True, color="1F4E79")
F_W = Font(name="Arial", size=9, bold=True, color="FFFFFF")
F_RED = Font(name="Arial", size=9, bold=True, color="C00000")
HDR = PatternFill("solid", fgColor="1F4E79")
THIN = Side(style="thin", color="BFBFBF")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
CLASSES = ["Healthy", "Very low", "Low", "Moderate", "High", "Very high"]
FILL = {c: PatternFill("solid", fgColor=x) for c, x in zip(
    CLASSES, ["E2EFDA", "F2F7E8", "FFF8E1", "FFE9C7", "FCD5C0", "F4B6B6"])}
DATE_ORDER = ["11/02/2026", "24/02/2026", "03/03/2026", "13/03/2026"]
TREAT_ORDER = [f"D{d}V{v}" for d in range(1, 5) for v in range(1, 4)]
STAGE_NAME = {"V": "Vegetative", "F": "Flowering", "P": "Pod formation"}
STATUS = "SIMULATED (EXPECTED) VALUES - NOT MEASURED DATA"

# ---------------------------------------------------------------- read model
wb_in = openpyxl.load_workbook(MODEL, data_only=True, read_only=True)
ws_in = wb_in["Simulation"]
it = ws_in.iter_rows(min_row=2, values_only=True)
head = next(it)
COL = {h: i for i, h in enumerate(head)}
recs = [dict(zip(head, r)) for r in it if r[0]]
key = lambda r: (DATE_ORDER.index(r["Date code"]), TREAT_ORDER.index(r["Treatment"]), CLASSES.index(r["Severity class"]))
recs.sort(key=key)
assert len(recs) == 288, len(recs)
for r in recs:
    if r[f"Tc (C)"] is None:
        raise SystemExit("Model workbook has no cached values - recalculate it first.")
healthy = {(r["Date code"], r["Treatment"]): r for r in recs if r["Severity class"] == "Healthy"}

# ---------------------------------------------------------------- parameter definitions
# (sheet, title, unit, method, getter -> (mean, low, high), decimals, range note)
def g(code):
    return lambda r: (r[f"{code} mean"], r[f"{code} low"], r[f"{code} high"])


def ratio(fn, cv):
    def f(r):
        m = fn(r)
        return m, m * (1 - 1.645 * cv), m * (1 + 1.645 * cv)
    return f


def tc_rng(r):
    return r["Tc low (C)"], r["Tc high (C)"]


def clip_cwsi(r, tc):
    return min(max((tc - r["Twet (C)"]) / (r["Tdry (C)"] - r["Twet (C)"]), 0.02), 0.98)


def thermal(fn):
    """Apply fn(r, Tc) to mean Tc and the Tc range bounds."""
    def f(r):
        lo, hi = tc_rng(r)
        vals = [fn(r, lo), fn(r, hi)]
        return fn(r, r["Tc (C)"]), min(vals), max(vals)
    return f


def sd_rng(r):
    s_lo, s_hi = r["s low"], r["s high"]
    m = r["Tc SD within plot (C)"]
    return m, (0.6 + 2.0 * s_lo) * 0.85, (0.6 + 2.0 * s_hi) * 1.15


def ig_rng(r):
    """Ig is proportional to gs, so its range follows the relative gs range."""
    m = r["IG = (Tdry-Tc)/(Tc-Twet)"]
    return m, m * r["gs low"] / r["gs mean"], m * r["gs high"] / r["gs mean"]


PARAMS = [
    ("RWC", "Relative water content", "%", "Dehydration & imbibition (Barrs & Weatherley 1962)", g("RWC"), 1),
    ("MSI", "Membrane stability index", "%", "Electrolyte leakage (Sairam 1994)", g("MSI"), 1),
    ("Pn", "Net photosynthetic rate", "umol CO2 m-2 s-1", "LI-6400 IRGA", g("Pn"), 2),
    ("gs", "Stomatal conductance", "mol H2O m-2 s-1", "LI-6400 IRGA", g("gs"), 3),
    ("E", "Transpiration rate", "mmol H2O m-2 s-1", "LI-6400 IRGA", g("E"), 2),
    ("Ci", "Intercellular CO2 concentration", "umol mol-1", "LI-6400 IRGA", g("Ci"), 0),
    ("LAI", "Leaf area index", "m2 m-2", "Plant canopy analyser", g("LAI"), 2),
    ("Chl_a", "Chlorophyll a", "ug mg-1 FW", "DMSO extraction (Wellburn 1994)", g("ChlA"), 3),
    ("Chl_b", "Chlorophyll b", "ug mg-1 FW", "DMSO extraction (Wellburn 1994)", g("ChlB"), 3),
    ("Total_Chl", "Total chlorophyll (a + b)", "ug mg-1 FW", "Sum of Chl a and Chl b",
     lambda r: (r["ChlA mean"] + r["ChlB mean"], r["ChlA low"] + r["ChlB low"], r["ChlA high"] + r["ChlB high"]), 3),
    ("Chl_ab_ratio", "Chlorophyll a/b ratio", "-", "Chl a / Chl b", ratio(lambda r: r["Chl a/b"], 0.06), 2),
    ("Carotenoid", "Total carotenoids", "mg g-1 FW", "DMSO extraction (Wellburn 1994)", g("Car"), 3),
    ("Car_Chl_ratio", "Carotenoid / total chlorophyll", "-", "Car / (Chl a + b)", ratio(lambda r: r["Car/Total chl"], 0.08), 3),
    ("Anthocyanin", "Total monomeric anthocyanin", "ug g-1 FW (cyanidin-3-glucoside eq.)", "pH differential (Lee et al. 2005)", g("Anth"), 1),
    ("Protein", "Total soluble protein", "ug mg-1 FW", "Bradford (1976)", g("Prot"), 2),
    ("WUE", "Instantaneous water-use efficiency Pn/E", "umol CO2 mmol-1 H2O", "Pn / E", ratio(lambda r: r["WUE Pn/E (umol/mmol)"], 0.15), 2),
    ("iWUE", "Intrinsic water-use efficiency Pn/gs", "umol CO2 mol-1 H2O", "Pn / gs", ratio(lambda r: r["iWUE Pn/gs (umol/mol)"], 0.15), 1),
    ("Tc", "Canopy temperature", "C", "UAV thermal (FLIR), canopy pixels", thermal(lambda r, tc: tc), 2),
    ("CTD", "Canopy temperature depression (Tc - Ta)", "C", "Tc - Ta at flight time", thermal(lambda r, tc: tc - r["Ta flight (C)"]), 2),
    ("dTc", "Tc difference vs healthy plot (same treatment, date)", "C", "Tc - Tc(healthy)",
     thermal(lambda r, tc: tc - healthy[(r["Date code"], r["Treatment"])]["Tc (C)"]), 2),
    ("CTR", "Canopy temperature ratio (Tc / Ta)", "-", "Tc / Ta", thermal(lambda r, tc: tc / r["Ta flight (C)"]), 3),
    ("CWSI", "Crop water stress index", "0-1", "(Tc - Twet) / (Tdry - Twet)", thermal(clip_cwsi), 3),
    ("Ig", "Stomatal conductance index Ig", "-", "(Tdry - Tc) / (Tc - Twet)", ig_rng, 2),
    ("I3", "Thermal index I3", "-", "(Tc - Twet) / (Tdry - Tc)",
     lambda r: (lambda m, lo, hi: (1 / m, 1 / hi, 1 / lo))(*ig_rng(r)), 3),
    ("Tc_SD", "Within-plot canopy temperature SD", "C", "SD of canopy pixels", sd_rng, 2),
    ("MTD", "Maximum temperature difference (P95 - P5)", "C", "P95 - P5 of canopy pixels",
     lambda r: tuple(3.29 * v for v in sd_rng(r)), 2),
]
RANGE_NOTE = {
    "Chl_ab_ratio": "Range = mean x (1 -/+ 1.645 x CV), CV 0.06.",
    "Car_Chl_ratio": "Range = mean x (1 -/+ 1.645 x CV), CV 0.08.",
    "WUE": "Range = mean x (1 -/+ 1.645 x CV), CV 0.15.",
    "iWUE": "Range = mean x (1 -/+ 1.645 x CV), CV 0.15.",
    "Total_Chl": "Range = sum of the Chl a and Chl b range limits.",
    "Tc_SD": "SD = 0.6 + 2.0 x DI fraction; range from class DI limits, -/+15%.",
    "MTD": "MTD = 3.29 x SD (P95 - P5 of a normal distribution).",
}
THERMAL = {"Tc", "CTD", "dTc", "CTR", "CWSI", "Ig", "I3", "Tc_SD", "MTD"}
for c in THERMAL - {"Tc_SD", "MTD", "Ig", "I3"}:
    RANGE_NOTE[c] = ("Range from the Tc range (class DI limits and +/-1.645 CV of E); "
                     "CWSI clipped to 0.02-0.98.")
RANGE_NOTE["Ig"] = "Ig is proportional to gs: range = mean x (gs low / gs mean, gs high / gs mean)."
RANGE_NOTE["I3"] = "I3 = 1 / Ig; range is the inverse of the Ig range."

# ---------------------------------------------------------------- PROSPECT-D leaf model
spec = np.loadtxt(SPEC, comments="#")
WL, NR, KAB, KCAR, KANT, KBROWN, KW, KM = spec.T
assert WL[0] == 400 and WL[-1] == 2500 and len(WL) == 2101


def tav(alpha, nr):
    """Stern (1964) / Allen (1973) average transmissivity of a dielectric interface."""
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


def prospect_d(N, cab, car, ant, brown, cw, cm):
    """Directional-hemispherical reflectance of a leaf (Feret et al. 2017)."""
    k = (cab * KAB + car * KCAR + ant * KANT + brown * KBROWN + cw * KW + cm * KM) / N
    tau = np.where(k > 0, (1 - k) * np.exp(-k) + k ** 2 * (-expi(-np.maximum(k, 1e-12))), 1.0)
    talf, ralf = T40, 1 - T40
    t12, r12 = T90, 1 - T90
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
    den2 = a * a * bN1 * bN1 - 1
    Rsub = a * (bN1 * bN1 - 1) / den2
    Tsub = bN1 * (a * a - 1) / den2
    return Ra + Ta * Rsub * t / (1 - Rsub * r)


def gauss(c, w):
    return np.exp(-0.5 * ((WL - c) / w) ** 2)


# Reflectance of a dense white Albugo sporangial mass (dry, highly scattering; weak water,
# protein and cellulose features). Shape assumption, not a measured library spectrum.
R_PUST = (0.40 + 0.18 * (1 - np.exp(-(WL - 400) / 120.0)) - 0.06 * np.clip((WL - 1300) / 1200.0, 0, 1)
          - 0.08 * gauss(1450, 45) - 0.14 * gauss(1940, 60) - 0.05 * gauss(2100, 50) - 0.04 * gauss(2300, 40))

LMA = {"V": 0.0038, "F": 0.0042, "P": 0.0046}      # dry mass per area, g cm-2
N_LEAF = {"V": 1.50, "F": 1.60, "P": 1.75}         # PROSPECT structure parameter
BROWN0 = {"V": 0.0, "F": 0.02, "P": 0.08}          # senescence pigment in healthy leaf
WATER_SAT = 6.0                                     # water at full turgor / dry mass (g g-1)
SPORE_AGE = {"11/02/2026": 0.5}                     # sporulation still young at 6 DAI


def leaf_inputs(r):
    st, s = r["Stage"], r["s mid"]
    lma = LMA[st] * (1 - 0.10 * s)
    cw = WATER_SAT * LMA[st] * r["RWC mean"] / 100.0
    fw = lma + cw
    return {
        "N": N_LEAF[st] * (1 - 0.15 * s),
        "Cab": (r["ChlA mean"] + r["ChlB mean"]) * fw * 1000.0,
        "Car": r["Car mean"] * fw * 1000.0,
        "Anth": r["Anth mean"] * fw,
        "Cbrown": BROWN0[st] + 0.60 * s,
        "Cw": cw,
        "Cm": lma,
        "FW": fw,
        "f_pust": 0.15 * s * SPORE_AGE.get(r["Date code"], 1.0),
    }


def spectrum(p):
    leaf = prospect_d(p["N"], p["Cab"], p["Car"], p["Anth"], p["Cbrown"], p["Cw"], p["Cm"])
    return (1 - p["f_pust"]) * leaf + p["f_pust"] * R_PUST


INP = [leaf_inputs(r) for r in recs]
SPECTRA = np.array([spectrum(p) for p in INP])
assert np.all((SPECTRA > 0) & (SPECTRA < 1))

# ---------------------------------------------------------------- workbook
wb = openpyxl.Workbook()
wb.remove(wb.active)


def put(ws, row, col, val, font=F, fill=None, fmt=None, align=None, border=True):
    c = ws.cell(row=row, column=col, value=val)
    c.font = font
    if fill:
        c.fill = fill
    if fmt:
        c.number_format = fmt
    if align:
        c.alignment = align
    if border:
        c.border = BOX
    return c


WRAP = Alignment(wrap_text=True, vertical="center", horizontal="center")

# README
rd = wb.create_sheet("README")
lines = [
    ("WHITE RUST OF MUSTARD - SIMULATED DATASET, ONE SHEET PER PARAMETER", F_T),
    ("ICAR-IARI New Delhi, rabi 2025-26 | 4 sowing dates x 3 varieties | assessments 11/02, 24/02, 03/03 and 13/03/2026", F_B),
    (STATUS + ". Use as expected values, sanity-check ranges, priors and synthetic data for testing analysis/ML pipelines. "
     "Do not report them as observations.", F_RED),
    ("", F),
    ("LAYOUT OF EVERY PARAMETER SHEET", F_B),
    ("288 rows = 4 assessment dates x 12 treatments (D1V1 ... D4V3) x 6 severity classes "
     "(Healthy, Very low 1-5%, Low 6-10%, Moderate 11-25%, High 26-50%, Very high >50% DI).", F),
    ("Columns: date, DAS, DAI, stage, sampled leaf, treatment, sowing, variety, severity class, DI range, "
     "mean, low, high (approx. 90% range), % change vs the healthy plot of the same treatment and date, plausibility of the class.", F),
    ("Mean = value at the class mid-DI; low/high = values at the class DI limits widened by +/-1.645 x CV "
     "(plant-to-plant and assay variability).", F),
    ("Sampled leaf: 3rd fully expanded leaf from top at vegetative stage; 5th fully expanded leaf from top at flowering and pod formation.", F),
    ("", F),
    ("SOURCE OF THE VALUES", F_B),
    ("All biophysical, biochemical and thermal values are exported from the Simulation sheet of "
     "White_Rust_Simulated_Parameters_IARI_2025-26.xlsx (model equations, inputs, evidence and references are there "
     "and in the Word report). Ratios, thermal ranges and indices derived here are documented on each sheet.", F),
    ("", F),
    ("ASD SPECTRA (sheets ASD_Reflectance, ASD_Model_Inputs, Spectral_Indices)", F_B),
    ("Leaf reflectance 400-2500 nm at 1 nm, as from an ASD FieldSpec with leaf clip / contact probe on the adaxial "
     "(upper) surface of the sampled leaf, simulated with the PROSPECT-D leaf model (Feret et al. 2017).", F),
    ("PROSPECT-D inputs per spectrum are converted from the simulated values: Cab = total chl (mg g-1 FW) x FW per area x 1000; "
     "Car likewise; Anth = anthocyanin (ug g-1 FW) x FW per area; EWT Cw = 6.0 x LMA x RWC/100; LMA (Cm) = 0.0038 / 0.0042 / "
     "0.0046 g cm-2 at V / F / P, reduced by 10% x DI; N = 1.50 / 1.60 / 1.75 at V / F / P, reduced by 15% x DI; "
     "brown pigment = 0 / 0.02 / 0.08 at V / F / P + 0.6 x DI.", F),
    ("White pustules: a fraction f = 0.15 x DI (x0.5 on 11/02, 6 DAI) of the measured area takes the reflectance of a "
     "dry white sporangial mass (assumed shape). Pustules are mainly abaxial, so on the adaxial surface their direct "
     "effect is small; an abaxial measurement would show much brighter VIS and a flatter red edge.", F),
    ("Spectra are noise-free class means. Real ASD data add detector noise (largest beyond 2350 nm and at the 1000 and "
     "1800 nm detector joins) and leaf-to-leaf scatter of roughly 5-10% in NIR and 10-20% in VIS.", F),
    ("Spectral_Indices are live formulas on the ASD_Reflectance sheet. PROSPECT-D has no xanthophyll cycle, so PRI is "
     "not given; ARI and CRI follow the simulated pigment pools only.", F),
    ("", F),
    ("SHEETS", F_B),
]
for i, (t, f) in enumerate(lines, start=1):
    c = rd.cell(row=i, column=1, value=t)
    c.font = f
    c.alignment = Alignment(wrap_text=True, vertical="top")
row = len(lines) + 1
put(rd, row, 1, "Sheet", F_W, HDR)
put(rd, row, 2, "Parameter", F_W, HDR)
put(rd, row, 3, "Unit", F_W, HDR)
put(rd, row, 4, "Method / definition", F_W, HDR)
for sheet, title, unit, method, _, _ in PARAMS:
    row += 1
    for j, v in enumerate([sheet, title, unit, method], start=1):
        put(rd, row, j, v)
for sheet, title, unit, method in [
    ("ASD_Reflectance", "Leaf reflectance spectra, 400-2500 nm (288 spectra)", "fraction (0-1)", "PROSPECT-D + pustule mixing"),
    ("ASD_Model_Inputs", "PROSPECT-D inputs for each spectrum", "various", "Converted from simulated parameters"),
    ("Spectral_Indices", "Narrow-band indices from the simulated spectra", "-", "Formulas on ASD_Reflectance"),
]:
    row += 1
    for j, v in enumerate([sheet, title, unit, method], start=1):
        put(rd, row, j, v)
rd.column_dimensions["A"].width = 120
for col, w in zip("BCD", [48, 34, 44]):
    rd.column_dimensions[col].width = w
# Long text sits in column A; keep table readable by widening A only for text rows.
rd.column_dimensions["A"].width = 22
for i in range(1, len(lines) + 1):
    rd.merge_cells(start_row=i, start_column=1, end_row=i, end_column=4)
    rd.row_dimensions[i].height = 15 if len(lines[i - 1][0]) < 140 else 15 * (1 + len(lines[i - 1][0]) // 140)

# Parameter sheets
COLS = ["Assessment date", "DAS", "DAI", "Growth stage", "Sampled leaf", "Treatment", "Sowing", "Variety",
        "Severity class", "DI range (%)", "Mean", "Low", "High", "% change vs healthy", "Plausibility of class"]
WIDTHS = [12, 6, 6, 13, 30, 10, 8, 8, 12, 10, 10, 10, 10, 12, 44]
for sheet, title, unit, method, getter, dec in PARAMS:
    ws = wb.create_sheet(sheet)
    ws.cell(row=1, column=1, value=f"{title} ({unit})").font = F_T
    ws.cell(row=2, column=1, value=f"{STATUS} | Method: {method}"
            + (f" | {RANGE_NOTE[sheet]}" if sheet in RANGE_NOTE else "")).font = F_RED
    for j, h in enumerate(COLS, start=1):
        put(ws, 3, j, h if j < 11 or j > 13 else f"{h} ({unit})", F_W, HDR, align=WRAP)
    ws.row_dimensions[3].height = 30
    fmt = "0" if dec == 0 else "0." + "0" * dec
    for i, r in enumerate(recs):
        rr = 4 + i
        m, lo, hi = getter(r)
        hm = getter(healthy[(r["Date code"], r["Treatment"])])[0]
        if r["Severity class"] == "Healthy":
            p = 0.0
        elif sheet in {"CTD", "dTc"}:
            p = None  # % change is not meaningful for differences around zero
        else:
            p = (m / hm - 1) if hm else None
        vals = [r["Date code"], r["DAS"], r["DAI"], f'{r["Stage"]} - {STAGE_NAME[r["Stage"]]}', r["Leaf sampled"],
                r["Treatment"], r["Sowing"], r["Variety"], r["Severity class"], r["DI range (%)"],
                m, lo, hi, p if p is not None else "n.a.", r["Plausibility of class"]]
        fill = FILL[r["Severity class"]]
        for j, v in enumerate(vals, start=1):
            put(ws, rr, j, v, F_B if j == 11 else F, fill if j in (9, 10, 11) else None,
                fmt if j in (11, 12, 13) else ("+0.0%;-0.0%;0.0%" if j == 14 and isinstance(v, float) else None))
        if r["Severity class"] == "Very high":
            for j in range(1, len(COLS) + 1):
                ws.cell(row=rr, column=j).border = Border(left=THIN, right=THIN, top=THIN,
                                                          bottom=Side(style="medium", color="1F4E79"))
    for j, w in enumerate(WIDTHS, start=1):
        ws.column_dimensions[CL(j)].width = w
    ws.freeze_panes = "A4"
    ws.auto_filter.ref = f"A3:{CL(len(COLS))}{3 + len(recs)}"

# ASD reflectance
asd = wb.create_sheet("ASD_Reflectance")
HROWS = ["Spectrum ID", "Assessment date", "Treatment", "Severity class", "DI range (%)", "Growth stage", "Sampled leaf"]
FIRST = len(HROWS) + 3  # first wavelength row
asd.cell(row=1, column=1, value="Simulated ASD leaf reflectance (fraction), adaxial surface, 400-2500 nm at 1 nm. "
         + STATUS + ". PROSPECT-D + white-pustule mixing; inputs in ASD_Model_Inputs.").font = F_RED
for i, h in enumerate(HROWS):
    put(asd, 2 + i, 1, h, F_W, HDR)
put(asd, FIRST - 1, 1, "Wavelength (nm)", F_W, HDR)
for k, r in enumerate(recs):
    col = 2 + k
    meta = [f"S{k + 1:03d}", r["Date code"], r["Treatment"], r["Severity class"], r["DI range (%)"],
            STAGE_NAME[r["Stage"]], r["Leaf sampled"].replace(" fully expanded leaf from top", " leaf")]
    for i, v in enumerate(meta):
        put(asd, 2 + i, col, v, F_B if i == 0 else F, FILL[r["Severity class"]] if i == 3 else None, align=WRAP)
    put(asd, FIRST - 1, col, f"{r['Treatment']} {r['Date code'][:5]} {r['Severity class']}", F_B, align=WRAP)
    asd.column_dimensions[CL(col)].width = 11
for w_i, wl in enumerate(WL.astype(int)):
    rr = FIRST + w_i
    asd.cell(row=rr, column=1, value=int(wl)).font = F_B
    for k in range(len(recs)):
        asd.cell(row=rr, column=2 + k, value=round(float(SPECTRA[k, w_i]), 5)).number_format = "0.0000"
asd.column_dimensions["A"].width = 16
asd.row_dimensions[FIRST - 1].height = 36
asd.freeze_panes = asd.cell(row=FIRST, column=2)
ROW_OF = lambda wl: FIRST + (wl - 400)

# Model inputs
mi = wb.create_sheet("ASD_Model_Inputs")
mi.cell(row=1, column=1, value="PROSPECT-D inputs behind each simulated spectrum. " + STATUS).font = F_RED
ih = ["Spectrum ID", "Assessment date", "Treatment", "Severity class", "DI range (%)", "Growth stage",
      "N (structure)", "Cab (ug cm-2)", "Car (ug cm-2)", "Anth (ug cm-2)", "Cbrown (a.u.)", "Cw = EWT (g cm-2)",
      "Cm = LMA (g cm-2)", "FW per area (g cm-2)", "White pustule area fraction"]
ifmt = [None] * 6 + ["0.000", "0.0", "0.00", "0.000", "0.000", "0.0000", "0.0000", "0.0000", "0.000"]
for j, h in enumerate(ih, start=1):
    put(mi, 2, j, h, F_W, HDR, align=WRAP)
mi.row_dimensions[2].height = 30
for k, (r, p) in enumerate(zip(recs, INP)):
    vals = [f"S{k + 1:03d}", r["Date code"], r["Treatment"], r["Severity class"], r["DI range (%)"],
            STAGE_NAME[r["Stage"]], p["N"], p["Cab"], p["Car"], p["Anth"], p["Cbrown"], p["Cw"], p["Cm"], p["FW"], p["f_pust"]]
    for j, v in enumerate(vals, start=1):
        put(mi, 3 + k, j, v, F, FILL[r["Severity class"]] if j == 4 else None, ifmt[j - 1])
for j in range(1, len(ih) + 1):
    mi.column_dimensions[CL(j)].width = 13
mi.freeze_panes = "B3"

# Spectral indices (live formulas on ASD_Reflectance)
IDX = [
    ("NDVI", "(R800-R670)/(R800+R670)", "Rouse et al. 1974", lambda R: f"({R(800)}-{R(670)})/({R(800)}+{R(670)})"),
    ("GNDVI", "(R800-R550)/(R800+R550)", "Gitelson et al. 1996", lambda R: f"({R(800)}-{R(550)})/({R(800)}+{R(550)})"),
    ("NDRE", "(R790-R720)/(R790+R720)", "Barnes et al. 2000", lambda R: f"({R(790)}-{R(720)})/({R(790)}+{R(720)})"),
    ("CI red-edge", "R780/R710 - 1", "Gitelson et al. 2003", lambda R: f"{R(780)}/{R(710)}-1"),
    ("REIP (nm)", "700 + 40 x ((R670+R780)/2 - R700)/(R740-R700)", "Guyot & Baret 1988",
     lambda R: f"700+40*(({R(670)}+{R(780)})/2-{R(700)})/({R(740)}-{R(700)})"),
    ("MCARI", "((R700-R670) - 0.2(R700-R550)) x R700/R670", "Daughtry et al. 2000",
     lambda R: f"(({R(700)}-{R(670)})-0.2*({R(700)}-{R(550)}))*({R(700)}/{R(670)})"),
    ("ARI", "1/R550 - 1/R700", "Gitelson et al. 2001", lambda R: f"1/{R(550)}-1/{R(700)}"),
    ("CRI1", "1/R510 - 1/R550", "Gitelson et al. 2002", lambda R: f"1/{R(510)}-1/{R(550)}"),
    ("PSRI", "(R680-R500)/R750", "Merzlyak et al. 1999", lambda R: f"({R(680)}-{R(500)})/{R(750)}"),
    ("WI", "R900/R970", "Penuelas et al. 1997", lambda R: f"{R(900)}/{R(970)}"),
    ("NDWI", "(R860-R1240)/(R860+R1240)", "Gao 1996", lambda R: f"({R(860)}-{R(1240)})/({R(860)}+{R(1240)})"),
    ("NDII", "(R819-R1649)/(R819+R1649)", "Hardisky et al. 1983", lambda R: f"({R(819)}-{R(1649)})/({R(819)}+{R(1649)})"),
    ("SWIR moisture stress index", "R1600/R820", "Hunt & Rock 1989", lambda R: f"{R(1600)}/{R(820)}"),
    ("CAI", "0.5(R2000+R2200) - R2100", "Nagler et al. 2003", lambda R: f"0.5*({R(2000)}+{R(2200)})-{R(2100)}"),
]
si = wb.create_sheet("Spectral_Indices")
si.cell(row=1, column=1, value="Narrow-band indices computed by formula from ASD_Reflectance. " + STATUS).font = F_RED
sh = ["Spectrum ID", "Assessment date", "Treatment", "Severity class", "DI range (%)", "Growth stage"] + [x[0] for x in IDX]
for j, h in enumerate(sh, start=1):
    put(si, 2, j, h, F_W, HDR, align=WRAP)
put(si, 3, 1, "Formula", F_B)
put(si, 4, 1, "Reference", F_B)
for j, (_, form, ref, _) in enumerate(IDX, start=7):
    put(si, 3, j, form, F, align=WRAP)
    put(si, 4, j, ref, F, align=WRAP)
si.row_dimensions[2].height = 30
si.row_dimensions[3].height = 45
for k, r in enumerate(recs):
    rr = 5 + k
    col = CL(2 + k)
    R = lambda wl, col=col: f"ASD_Reflectance!${col}${ROW_OF(wl)}"
    for j, v in enumerate([f"S{k + 1:03d}", r["Date code"], r["Treatment"], r["Severity class"],
                           r["DI range (%)"], STAGE_NAME[r["Stage"]]], start=1):
        put(si, rr, j, v, F, FILL[r["Severity class"]] if j == 4 else None)
    for j, (name, _, _, fn) in enumerate(IDX, start=7):
        put(si, rr, j, "=" + fn(R), F, fmt="0.0" if name.startswith("REIP") else "0.0000")
for j in range(1, len(sh) + 1):
    si.column_dimensions[CL(j)].width = 14
si.freeze_panes = "G5"

wb.save(OUT)
print("saved", OUT, "spectra", SPECTRA.shape)
