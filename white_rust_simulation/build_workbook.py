"""Build the white-rust expected-value (simulation) workbook.

Every simulated value is an Excel formula driven by input sheets, so any
assumption can be changed (or replaced with measured data) and the whole
workbook recalculates. Run scripts/recalc.py on the output afterwards.

Usage: python build_workbook.py <weather.xlsx> <output.xlsx>
"""
import sys
import datetime as dt

import openpyxl
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter as CL
from openpyxl.worksheet.datavalidation import DataValidation

WEATHER_SRC, OUT = sys.argv[1], sys.argv[2]

FONT = "Arial"
F_NORMAL = Font(name=FONT, size=10)
F_BOLD = Font(name=FONT, size=10, bold=True)
F_INPUT = Font(name=FONT, size=10, color="0000FF")
F_LINK = Font(name=FONT, size=10, color="008000")
F_TITLE = Font(name=FONT, size=14, bold=True)
F_WARN = Font(name=FONT, size=11, bold=True, color="C00000")
FILL_HEAD = PatternFill("solid", fgColor="D9E1F2")
FILL_INPUT = PatternFill("solid", fgColor="FFF2CC")
FILL_HEALTHY = PatternFill("solid", fgColor="E2EFDA")
FILL_WARN = PatternFill("solid", fgColor="FCE4D6")
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical="top")
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)

wb = openpyxl.Workbook()


def style_header(ws, row, c1, c2):
    for c in range(c1, c2 + 1):
        cell = ws.cell(row=row, column=c)
        cell.font = F_BOLD
        cell.fill = FILL_HEAD
        cell.alignment = CENTER
        cell.border = BORDER


def put(ws, ref, value, font=F_NORMAL, fill=None, fmt=None, comment=None, align=None):
    cell = ws[ref]
    cell.value = value
    cell.font = font
    if fill:
        cell.fill = fill
    if fmt:
        cell.number_format = fmt
    if comment:
        cell.comment = Comment(comment, "model")
    if align:
        cell.alignment = align
    return cell


DATES = [("11/02/2026", dt.date(2026, 2, 11)), ("24/02/2026", dt.date(2026, 2, 24)),
         ("03/03/2026", dt.date(2026, 3, 3)), ("13/03/2026", dt.date(2026, 3, 13))]
SOWINGS = ["D1", "D2", "D3", "D4"]
VARIETIES = ["V1", "V2", "V3"]
TREATMENTS = [d + v for d in SOWINGS for v in VARIETIES]
CLASSES = [  # name, DI range text, s_low, s_mid, s_high (fraction of leaf area / DI)
    ("Healthy", "0", 0.0, 0.0, 0.0),
    ("Very low", "1-5", 0.01, 0.03, 0.05),
    ("Low", "6-10", 0.06, 0.08, 0.10),
    ("Moderate", "11-25", 0.11, 0.18, 0.25),
    ("High", "26-50", 0.26, 0.38, 0.50),
    ("Very high", ">50", 0.51, 0.65, 0.85),
]
# Growth stage recorded by the user (V vegetative, F flowering, P pod formation)
STAGE = {
    "D1V1": ["F", "F", "P", "P"], "D1V2": ["V", "F", "F", "P"], "D1V3": ["V", "F", "F", "P"],
    "D2V1": ["V", "F", "F", "P"], "D2V2": ["V", "F", "F", "P"], "D2V3": ["V", "F", "F", "P"],
    "D3V1": ["V", "F", "F", "P"], "D3V2": ["V", "V", "F", "P"], "D3V3": ["V", "V", "F", "P"],
    "D4V1": ["V", "V", "F", "F"], "D4V2": ["V", "V", "F", "F"], "D4V3": ["V", "V", "F", "F"],
}

# ---------------------------------------------------------------- README
ws = wb.active
ws.title = "README"
readme = [
    ("WHITE RUST OF MUSTARD - EXPECTED-VALUE (SIMULATION) MODEL", F_TITLE),
    ("IARI New Delhi, rabi 2025-26 | 4 sowing dates x 3 varieties | assessments 11/02, 24/02, 03/03, 13/03/2026", F_BOLD),
    ("", None),
    ("STATUS OF THESE NUMBERS: SIMULATED / EXPECTED VALUES - NOT MEASURED DATA", F_WARN),
    ("All values are model outputs built from published baselines, white-rust and analogous-disease effect sizes, "
     "the IARI 2025-26 daily weather, your DAS/GDD/phenology and your sampling leaf. Use them as hypotheses, "
     "expected ranges, priors for sanity-checking field data, synthetic data for testing analysis/ML pipelines, "
     "and as the 'expected' column when you discuss your results. Do NOT report them in the thesis as observations. "
     "Where your measured data exist, they replace these values.", None),
    ("", None),
    ("HOW THE MODEL WORKS", F_BOLD),
    ("1. Healthy value (same treatment, date, stage, leaf) = reference value x stage factor x (1 - heat sensitivity x heat index h) "
     "x variety factor [x cold-legacy factor for anthocyanin]. LAI uses a GDD-driven canopy curve.", None),
    ("2. Diseased value = Healthy x (1 + R(s) x variety tolerance x lesion-age factor), where s = disease index (fraction) "
     "and R(s) is the parameter's severity-response curve (Response_Table).", None),
    ("3. Range = values at the lower and upper DI limit of the class, widened by +/- 1.645 x CV (approx. 90% interval) "
     "for plant-to-plant and assay variability.", None),
    ("4. E (transpiration) = gs x leaf-to-air VPD / P, using the measurement-time VPD from the weather of the 7 days to the "
     "assessment date, plus extra cuticular loss through ruptured pustules.", None),
    ("5. Thermal parameters come from an energy-balance CWSI logic: CWSI = 1 - (1 - CWSI_healthy) x E_diseased / E_healthy, "
     "Tc = Twet + CWSI x (Tdry - Twet), with Twet/Tdry baselines from flight-time air temperature and VPD.", None),
    ("", None),
    ("SHEETS", F_BOLD),
    ("Inputs_General - all global assumptions (blue = editable input).", None),
    ("Inputs_Treatments - sowing dates, variety reactions, LAI maxima, expected-DI drivers, anthocyanin cold legacy.", None),
    ("Parameters - reference values, CV, stage factors, heat sensitivity, variety factors, severity-response coefficients, sources.", None),
    ("Severity_Classes - your 6 DI classes and the DI fractions used.", None),
    ("Response_Table - relative change R(s) of each parameter at each class (low / mid / high DI).", None),
    ("Weather - IARI daily weather 31/10/2025-06/04/2026 (your file) + GDD and Chattopadhyay et al. (2011) favourability flags.", None),
    ("Context - per treatment x date: DAS, DAI, GDD, stage, sampled leaf, weekly weather, VPD, heat index, thermal baselines, "
     "healthy LAI, expected DI and the plausibility of each severity class.", None),
    ("Simulation - 288 rows (12 treatments x 4 dates x 6 classes): mean, low, high, % change vs healthy for 12 parameters, "
     "derived ratios and thermal parameters.", None),
    ("Stage_Comparison - healthy vs each severity class at each growth stage (V/F/P), pooled and by date.", None),
    ("Quick_View - choose a treatment and date to see healthy vs all severity classes side by side.", None),
    ("Thermal_Parameters - definitions and formulas of thermal indices. Texture_Colour - expected GLCM and colour-index changes.", None),
    ("Sources - references and evidence level behind each number.", None),
    ("", None),
    ("SAMPLED LEAF: 3rd fully expanded leaf from top at vegetative stage; 5th fully expanded leaf from top at flowering and "
     "pod formation (as specified by you). The model applies stage factors for this.", None),
    ("", None),
    ("KEY CAVEATS", F_BOLD),
    ("- Only chlorophyll, carotenoids and total protein have any direct white-rust data in B. juncea; RWC, MSI, Pn, E, gs, LAI "
     "and anthocyanin responses are built from mechanism and analogous pathosystems (evidence level shown in Parameters).", None),
    ("- Classes flagged 'Unlikely' in the Context / Simulation sheets are not expected under your 2025-26 weather and timing; their "
     "values are still given so every class can be compared at every stage.", None),
    ("- The resistance labels of V3 (PM 37) are unverified in the literature you supplied; V1 (PM 26, susceptible) and V2 "
     "(Pusa Vijay, highly susceptible) follow Shrivastava et al. (2023).", None),
    ("- The 11/02 assessment is 6 days after inoculation; any visible disease then most likely comes from natural infection "
     "during the favourable spell of 18 Dec-4 Feb (see Weather flags).", None),
]
for i, (text, font) in enumerate(readme, start=1):
    c = ws.cell(row=i, column=1, value=text)
    c.font = font or F_NORMAL
    c.alignment = Alignment(wrap_text=True, vertical="top")
ws.column_dimensions["A"].width = 150

# ------------------------------------------------------------ Inputs_General
ig = wb.create_sheet("Inputs_General")
put(ig, "A1", "GLOBAL INPUTS (blue cells on yellow are editable assumptions)", F_TITLE)
general = [
    # key, label, value, unit, note
    ("Tbase", "Base temperature for GDD", 5.0, "deg C", "Rana et al. 2017 (Nanda et al. 1996) base 5 C for B. juncea"),
    ("EmergGDD", "GDD from sowing to emergence", 110.0, "deg C d", "Rana et al. 2017: 100-125 GDD"),
    ("Inoc", "Inoculation date", dt.date(2026, 2, 5), "date", "User: all treatments inoculated on 05/02/2026"),
    ("HeatThr", "Heat-index threshold (weekly mean Tmax)", 27.0, "deg C", "Assumption: above ~27 C Tmax late-sown mustard shows heat stress"),
    ("HeatSpan", "Heat-index span (Tmax rise giving h = 1)", 8.0, "deg C", "Assumption: h = (Tmax_wk - 27)/8, so h ~ 1 at 35 C"),
    ("fMeas", "Fraction of diurnal T range at IRGA time (~10:30-11:30 h)", 0.80, "-", "Assumption for leaf-to-air VPD at gas-exchange time"),
    ("gMeas", "Weight of morning RH at IRGA time", 0.30, "-", "RH_meas = RH II + g x (RH I - RH II)"),
    ("fFlight", "Fraction of diurnal T range at UAV thermal flight (~12:30 h)", 0.90, "-", "Flights 11:00-14:00 per review draft"),
    ("gFlight", "Weight of morning RH at flight time", 0.15, "-", ""),
    ("Patm", "Atmospheric pressure, New Delhi (~216 m asl)", 99.3, "kPa", "Standard atmosphere at 216 m"),
    ("a_wet", "Non-water-stressed baseline intercept (Tc - Ta at VPD = 0)", 1.0, "deg C", "Idso-type NWSB: Tc - Ta = a - b x VPD"),
    ("b_wet", "Non-water-stressed baseline slope", 1.9, "deg C/kPa", "Typical crop NWSB slopes 1.5-2.2 C/kPa"),
    ("dT_dry", "Upper (non-transpiring) baseline: Tdry - Ta", 4.0, "deg C", "Typical 3-5 C under midday radiation"),
    ("CWSI_V", "Healthy-canopy CWSI, vegetative", 0.12, "-", "Irrigated, transpiring canopy"),
    ("CWSI_F", "Healthy-canopy CWSI, flowering", 0.20, "-", "Yellow petals raise canopy temperature"),
    ("CWSI_P", "Healthy-canopy CWSI, pod formation", 0.30, "-", "Senescing lower canopy, pods"),
    ("CWSI_heat", "Extra healthy CWSI per unit heat index h", 0.05, "-", ""),
    ("Cuticle", "Extra water loss through ruptured pustules (fraction per unit s)", 0.25, "-", "Field-crop review: rust pustule rupture can raise cuticular loss"),
    ("z", "z for range (90% interval)", 1.645, "-", ""),
    ("TcSD0", "Within-plot canopy-temperature SD, healthy", 0.6, "deg C", "Assumption for 2-cm FLIR pixels"),
    ("TcSDslope", "Increase of within-plot Tc SD per unit s", 2.0, "deg C", "Patchy lesions raise thermal heterogeneity"),
    ("gsVPDm", "Stomatal sensitivity to VPD: gs = gs_ref x (VPD/VPDref)^-m", 0.5, "-", "Leuning/Oren-type response; m ~0.5 for C3 crops"),
    ("VPDref", "Reference VPD for gs reference value", 1.0, "kPa", "gs reference value applies at ~1 kPa"),
    ("G50", "LAI curve: GDD (from emergence) at half of LAImax", 330.0, "deg C d", "Calibrated so canopy closes near flowering"),
    ("Gscale", "LAI curve: logistic scale", 100.0, "deg C d", ""),
    ("Gdecl", "LAI decline starts (GDD from emergence)", 800.0, "deg C d", "Around pod initiation (Rana et al. 2017: 685-816)"),
    ("Gdeclsc", "LAI decline scale", 300.0, "deg C d", ""),
]
ig["A3"], ig["B3"], ig["C3"], ig["D3"], ig["E3"] = "Key", "Assumption", "Value", "Unit", "Basis / source"
style_header(ig, 3, 1, 5)
GEN = {}
for i, (k, label, val, unit, note) in enumerate(general, start=4):
    put(ig, f"A{i}", k, F_BOLD)
    put(ig, f"B{i}", label, align=WRAP)
    put(ig, f"C{i}", val, F_INPUT, FILL_INPUT, "dd/mm/yyyy" if isinstance(val, dt.date) else "0.000")
    put(ig, f"D{i}", unit)
    put(ig, f"E{i}", note, align=WRAP)
    GEN[k] = f"Inputs_General!$C${i}"
for col, w in zip("ABCDE", (12, 55, 12, 12, 70)):
    ig.column_dimensions[col].width = w

# ---------------------------------------------------------- Inputs_Treatments
it = wb.create_sheet("Inputs_Treatments")
put(it, "A1", "TREATMENT INPUTS (blue on yellow = editable)", F_TITLE)
# Sowing table
hdr = ["Sowing", "Sowing date", "LAImax healthy", "Exposure factor (expected DI)",
       "Anth cold factor 11/02", "Anth cold factor 24/02", "Anth cold factor 03/03", "Anth cold factor 13/03", "Note"]
for j, h in enumerate(hdr, start=1):
    it.cell(row=3, column=j, value=h)
style_header(it, 3, 1, len(hdr))
sow_rows = {
    "D1": (dt.date(2025, 12, 9), 3.4, 1.00, [1.00, 1.00, 1.00, 1.00],
           "Sown 09/12/2025 (ORW slide 11 says 08/12 - DAS table fits 09/12). Inoculated at 58 DAS; >=36 DAS from 14 Jan inside the favourable spell"),
    "D2": (dt.date(2025, 12, 18), 3.2, 0.90, [1.05, 1.00, 1.00, 1.00], "Inoculated at 49 DAS; >=36 DAS from 23 Jan"),
    "D3": (dt.date(2025, 12, 27), 2.9, 0.75, [1.20, 1.05, 1.00, 1.00], "Inoculated at 40 DAS; leaves formed in Jan cold spell"),
    "D4": (dt.date(2026, 1, 9), 2.5, 0.60, [1.40, 1.15, 1.00, 1.00],
           "Inoculated at 27 DAS; emerged during 10-17 Jan cold (Tmin 1.6-4 C) -> cold-induced anthocyanin in young leaves"),
}
SOW = {}
for i, d in enumerate(SOWINGS, start=4):
    sd, lmax, expo, anth, note = sow_rows[d]
    put(it, f"A{i}", d, F_BOLD)
    put(it, f"B{i}", sd, F_INPUT, FILL_INPUT, "dd/mm/yyyy")
    put(it, f"C{i}", lmax, F_INPUT, FILL_INPUT, "0.00")
    put(it, f"D{i}", expo, F_INPUT, FILL_INPUT, "0.00")
    for j, a in enumerate(anth):
        put(it, f"{CL(5 + j)}{i}", a, F_INPUT, FILL_INPUT, "0.00")
    put(it, f"I{i}", note, align=WRAP)
    SOW[d] = i
it["C3"].comment = Comment("Healthy peak LAI assumed lower with later sowing (Jain & Sandhu, PAU: LAI highest in 10 Oct sowing, "
                           "lowest in 1 Dec). Your Dec-Jan sowings are later still. LOW confidence - replace with canopy-analyser data.", "model")
it["D3"].comment = Comment("Relative disease exposure used only for the EXPECTED DI scenario: earlier-sown crops reached the "
                           ">=36 DAS susceptible window during the 18 Dec-4 Feb favourable spell (Chattopadhyay et al. 2011 criteria).", "model")

# Variety table
put(it, "A10", "Variety", F_BOLD)
vh = ["Variety", "Name", "Reported reaction", "Tolerance factor on R(s)", "Susceptibility (expected DI)",
      "LAI factor", "Basis"]
for j, h in enumerate(vh, start=1):
    it.cell(row=11, column=j, value=h)
style_header(it, 11, 1, len(vh))
var_rows = {
    "V1": ("Pusa Mustard 26", "Susceptible (PDI 44.4)", 1.00, 0.80, 0.95,
           "Shrivastava et al. 2023. Early-maturing: flowered first in your phenology table"),
    "V2": ("Pusa Vijay", "Highly susceptible (PDI 55.6)", 1.10, 1.00, 1.00, "Shrivastava et al. 2023"),
    "V3": ("Pusa Mustard 37", "Moderately resistant (UNVERIFIED)", 0.85, 0.50, 1.00,
           "Label from ORW slide 27; no verified source yet - treat as assumption"),
}
VAR = {}
for i, v in enumerate(VARIETIES, start=12):
    name, react, tol, susc, laif, basis = var_rows[v]
    put(it, f"A{i}", v, F_BOLD)
    put(it, f"B{i}", name)
    put(it, f"C{i}", react)
    put(it, f"D{i}", tol, F_INPUT, FILL_INPUT, "0.00")
    put(it, f"E{i}", susc, F_INPUT, FILL_INPUT, "0.00")
    put(it, f"F{i}", laif, F_INPUT, FILL_INPUT, "0.00")
    put(it, f"G{i}", basis, align=WRAP)
    VAR[v] = i
it["D11"].comment = Comment("Multiplies the severity-response R(s): at the same DI a more tolerant genotype loses slightly less "
                            "(similar-experiment slides; Rai et al. 2024 pigment retention in resistant NIL).", "model")

# Date table
put(it, "A17", "Assessment dates", F_BOLD)
dh = ["Date code", "Date", "Reference expected DI (V2 x D1)", "Basis"]
for j, h in enumerate(dh, start=1):
    it.cell(row=18, column=j, value=h)
style_header(it, 18, 1, len(dh))
di_ref = [3.0, 18.0, 28.0, 35.0]
di_note = [
    "6 DAI: before the 8-13 d incubation of inoculated infections; only natural pre-inoculation infection visible",
    "19 DAI: first inoculated cycle sporulated; borderline-favourable week after inoculation",
    "26 DAI: secondary cycle limited by dry, warm weather (no favourable days after 5 Feb)",
    "36 DAI: near plateau; onset-to-peak ~40 d (Singh M. et al. 2024); heat (Tmax ~35 C) halts spread",
]
DATEROW = {}
for i, ((code, d), ref, note) in enumerate(zip(DATES, di_ref, di_note), start=19):
    put(it, f"A{i}", code, F_BOLD)
    put(it, f"B{i}", d, F_INPUT, FILL_INPUT, "dd/mm/yyyy")
    put(it, f"C{i}", ref, F_INPUT, FILL_INPUT, "0.0")
    put(it, f"D{i}", note, align=WRAP)
    DATEROW[code] = i
put(it, "A24", "Expected DI = reference DI (date) x variety susceptibility x sowing exposure. "
    "It is a scenario only; overwrite column C or the factors with your observed plot DI when available.", F_BOLD)
for col, w in zip("ABCDEFGHI", (12, 22, 26, 26, 20, 18, 22, 20, 80)):
    it.column_dimensions[col].width = w

# ---------------------------------------------------------------- Parameters
pa = wb.create_sheet("Parameters")
put(pa, "A1", "PARAMETER BASELINES, MODIFIERS AND SEVERITY-RESPONSE COEFFICIENTS (blue on yellow = editable)", F_TITLE)
phead = ["Code", "Parameter", "Unit", "Method", "Reference healthy value", "CV", "Ref range low", "Ref range high",
         "Stage factor V (3rd leaf)", "Stage factor F (5th leaf)", "Stage factor P (5th leaf)", "Heat sensitivity",
         "Variety factor V1", "Variety factor V2", "Variety factor V3", "Response type", "Sign", "Rmax", "k",
         "Logistic centre", "Logistic scale", "Hump amplitude", "Hump peak s",
         DATES[0][0], DATES[1][0], DATES[2][0], DATES[3][0], "Evidence level", "Basis / sources"]
for j, h in enumerate(phead, start=1):
    pa.cell(row=3, column=j, value=h)
style_header(pa, 3, 1, len(phead))
pa.cell(row=2, column=24, value="Lesion-age factor by date (damage lag behind sporulation; Chou et al. 2000)").font = F_BOLD
pa.cell(row=2, column=9, value="Healthy-value modifiers").font = F_BOLD
pa.cell(row=2, column=16, value="Severity-response curve R(s)").font = F_BOLD

AGE_DMG = [0.5, 1, 1, 1]
AGE_GAS = [0.8, 1, 1, 1]
params = [
    # code, name, unit, method, ref, cv, lo, hi, stV, stF, stP, heat, v1, v2, v3, type, sign, rmax, k, c, sc, hA, hP, age, evid, basis, numfmt
    ("RWC", "Relative water content", "%", "Dehydration & imbibition (Barrs & Weatherley 1962)", 86.0, 0.04, 82, 90,
     1.00, 0.99, 0.95, 0.05, 1.00, 1.00, 1.00, "logistic", -1, 0.30, 0, 0.35, 0.12, 0, 0, AGE_DMG, "E4 + E3",
     "Healthy 86% at flowering (Jobner field study, RGN-229); 85% max (PLOS ONE 2021 K study). Threshold decline once "
     "pustules rupture epidermis (mechanism); your ASD SWIR spectra showed lower water in diseased leaves on 03/03 and 13/03.", "0.0"),
    ("MSI", "Membrane stability index", "%", "Electrolyte leakage (Sairam 1994)", 72.0, 0.07, 62, 78,
     1.00, 0.98, 0.92, 0.12, 1.00, 1.00, 1.00, "logistic", -1, 0.70, 0, 0.28, 0.10, 0, 0, AGE_DMG, "E4 + E3",
     "Healthy ~72% (similar-experiment HR class; PLOS ONE 2021: 57-73%). Late, steep collapse at high severity "
     "(similar-experiment S class 66 -> 31 -> 14%); heat lowers MSI independently.", "0.0"),
    ("Pn", "Net photosynthetic rate", "umol CO2 m-2 s-1", "LI-6400", 19.0, 0.12, 15, 24,
     1.00, 1.00, 0.85, 0.12, 1.00, 1.00, 1.03, "exp", -1, 0.75, 4.4, 0, 0, 0, 0, AGE_GAS, "E2 + E3",
     "Healthy 15-20 (similar-experiment HR), 18-31 (Plants 2025, green B. juncea). Chou et al. 2000: whole-leaf A "
     "fell to 30% of control by 14 DAI (~30% leaf colonised); decline is non-stomatal.", "0.0"),
    ("gs", "Stomatal conductance", "mol H2O m-2 s-1", "LI-6400", 0.45, 0.18, 0.30, 0.65,
     1.00, 1.00, 0.85, 0.0, 1.00, 1.00, 1.00, "exp", -1, 0.65, 3.0, 0, 0, 0, 0, AGE_GAS, "E2(indirect) + E3",
     "Healthy 0.38-0.52 (similar-experiment HR); 0.62-0.85 in pots (Plants 2025). Healthy gs declines with VPD (gs_ref x (VPD/1 kPa)^-0.5, Inputs_General). Chou et al. 2000: transpiration "
     "unchanged at 8 DAI, so gs declines later and less steeply than Pn.", "0.000"),
    ("E", "Transpiration rate", "mmol H2O m-2 s-1", "LI-6400 (derived: gs x VPD / P)", 0, 0.18, 2, 7,
     1, 1, 1, 0, 1, 1, 1, "derived", 0, 0, 0, 0, 0, 0, 0, AGE_GAS, "Physics + E3",
     "E = gs x leaf-to-air VPD / P (LI-6400 relation); extra cuticular loss through ruptured pustules. Similar-experiment "
     "HR values 4.0-6.6 rising with VPD through the season.", "0.00"),
    ("Ci", "Intercellular CO2 (extra, from LI-6400)", "umol mol-1", "LI-6400", 285.0, 0.06, 270, 320,
     1.00, 1.00, 1.03, 0.0, 1.00, 1.00, 1.00, "exp", 1, 0.30, 4.0, 0, 0, 0, 0, AGE_GAS, "E3",
     "Healthy ~285 (similar-experiment HR). Ci rises while gs falls = non-stomatal limitation (Tatagiba et al. 2015; "
     "similar-experiment S class +27%). Not in your list but recorded by the LI-6400 - report it.", "0"),
    ("LAI", "Leaf area index", "m2 m-2", "Canopy analyser", 0, 0.12, 0.3, 4.0,
     1, 1, 1, 0, 1, 1, 1, "exp", -1, 0.45, 2.5, 0, 0, 0, 0, AGE_DMG, "E4",
     "Healthy LAI from GDD canopy curve and LAImax per sowing (Inputs_Treatments). Disease: premature senescence and "
     "defoliation (Bal & Kumar 2014: total defoliation in unsprayed plots at PDI ~70).", "0.00"),
    ("ChlA", "Chlorophyll a", "ug mg-1 FW (= mg g-1 FW)", "DMSO (Wellburn 1994)", 1.25, 0.10, 1.00, 1.60,
     0.95, 1.00, 0.85, 0.06, 1.00, 1.00, 1.03, "exp", -1, 0.65, 3.2, 0, 0, 0, 0, AGE_DMG, "E1(qual) + E2",
     "Total chl 0.86-1.75 mg g-1 FW in B. juncea leaves at 45-65 DAS (phytojournal 2019). Chou et al. 2000: chl stable "
     "to 12 DAI then -60% in invaded tissue by 14 DAI. Rai et al. 2024: higher in resistant NIL.", "0.000"),
    ("ChlB", "Chlorophyll b", "ug mg-1 FW (= mg g-1 FW)", "DMSO (Wellburn 1994)", 0.45, 0.12, 0.35, 0.60,
     0.95, 1.00, 0.88, 0.06, 1.00, 1.00, 1.03, "exp", -1, 0.55, 3.0, 0, 0, 0, 0, AGE_DMG, "E1(indirect) + E2",
     "a:b ~2.8 in healthy leaves. Chou et al. 2000: both a and b lost. DMSO can overestimate chl b (Quercus study) - "
     "use one extraction protocol throughout.", "0.000"),
    ("Car", "Carotenoids", "mg g-1 FW", "Spectrophotometric (Wellburn 1994 DMSO eq.)", 0.30, 0.12, 0.22, 0.45,
     0.95, 1.00, 0.90, 0.03, 1.00, 1.00, 1.03, "hump", -1, 0.40, 3.0, 0, 0, 0.10, 0.10, AGE_DMG, "E1(qual) + E3",
     "Rai et al. 2024: carotenoids ROSE continuously 0-96 hpi in the susceptible line; field-crop review: Car/Chl rises "
     "at intermediate severity. Modelled as small early rise then decline.", "0.000"),
    ("Anth", "Anthocyanin", "ug g-1 FW (cyanidin-3-glucoside eq.)", "pH differential (Lee et al. 2005)", 15.0, 0.30, 5, 35,
     1.10, 1.00, 1.15, 0.0, 1.00, 1.00, 1.00, "exp", 1, 0.60, 3.0, 0, 0, 0, 0, AGE_DMG, "E4 (speculative)",
     "No white-rust data at any level. Green B. juncea leaves: anthocyanins near detection limit (PMC4992693). Rise "
     "assumed from stress/phenylpropanoid induction (field-crop review); cold (Jan) and senescence also raise it.", "0.0"),
    ("Prot", "Total soluble protein", "ug mg-1 FW", "Bradford (1976), colorimetric", 10.0, 0.12, 6, 15,
     1.08, 1.00, 0.82, 0.06, 1.04, 1.08, 1.00, "exp", -1, 0.15, 3.0, 0, 0, 0, 0, AGE_DMG, "E1",
     "Mishra et al. 2009: inoculated leaves 4-10% lower than uninoculated in all 6 genotypes; susceptible genotypes have "
     "higher constitutive protein (variety factors). Conversion from %DW (Lowry) to Bradford FW basis is approximate.", "0.00"),
]
PROW = {}
NUMFMT = {}
for i, p in enumerate(params, start=4):
    (code, name, unit, meth, ref, cv, lo, hi, sv, sf, sp, heat, f1, f2, f3, rtype, sign, rmax, k, c, sc, hA, hP,
     age, evid, basis, nf) = p
    vals = [code, name, unit, meth, ref, cv, lo, hi, sv, sf, sp, heat, f1, f2, f3, rtype, sign, rmax, k, c, sc, hA, hP,
            *age, evid, basis]
    for j, v in enumerate(vals, start=1):
        cell = pa.cell(row=i, column=j, value=v)
        cell.border = BORDER
        if 5 <= j <= 27 and j not in (16,):
            cell.font = F_INPUT
            cell.fill = FILL_INPUT
        else:
            cell.font = F_NORMAL
        if j in (28, 29, 2, 4):
            cell.alignment = WRAP
    PROW[code] = i
    NUMFMT[code] = nf
pa.cell(row=17, column=1, value="Response types: exp: R = sign x Rmax x (1 - exp(-k s)); logistic: R = sign x Rmax x "
        "(L(s) - L(0)) / (1 - L(0)), L(s) = 1/(1 + exp(-(s - centre)/scale)); hump: exp decline plus "
        "A x (s/peak) x exp(1 - s/peak). s = disease index as a fraction (0.18 = 18%).").font = F_BOLD
pa.cell(row=18, column=1, value="Evidence levels: E1 direct white rust on B. juncea; E2 A. candida on another host "
        "(Arabidopsis); E3 other Brassica / foliar pathogen; E4 mechanism or abiotic analogue only.").font = F_BOLD
pa.cell(row=19, column=1, value="Units: ug mg-1 FW is numerically identical to mg g-1 FW (chlorophyll, protein).").font = F_BOLD
widths = [8, 26, 18, 26, 11, 7, 9, 9, 10, 10, 10, 9, 9, 9, 9, 10, 6, 7, 6, 9, 9, 9, 9, 10, 10, 10, 10, 16, 90]
for j, w in enumerate(widths, start=1):
    pa.column_dimensions[CL(j)].width = w
pa.freeze_panes = "C4"

# ---------------------------------------------------------- Severity_Classes
sc_ws = wb.create_sheet("Severity_Classes")
put(sc_ws, "A1", "DISEASE-INDEX CLASSES (plot DI = sum(x f) / (n sum f) x 100, n = 9, Bisht/AICRP 0-9 scale)", F_TITLE)
for j, h in enumerate(["Class", "DI range (%)", "s low", "s mid", "s high", "Class index"], start=1):
    sc_ws.cell(row=3, column=j, value=h)
style_header(sc_ws, 3, 1, 6)
CLSROW = {}
for i, (name, rng, lo, mid, hi) in enumerate(CLASSES, start=4):
    put(sc_ws, f"A{i}", name, F_BOLD)
    put(sc_ws, f"B{i}", rng)
    for col, v in zip("CDE", (lo, mid, hi)):
        put(sc_ws, f"{col}{i}", v, F_INPUT, FILL_INPUT, "0.00")
    put(sc_ws, f"F{i}", i - 3)
    CLSROW[name] = i
sc_ws["A11"] = ("s = DI as a fraction. Mid values are used for the mean; low/high values bound the range. The sampled leaf "
                "is assumed to carry the plot-mean severity (ORW slide 23: leaves closest to plot-mean DI). The 'Very high' "
                "upper limit is capped at 85% because leaves beyond that are usually shed.")
sc_ws["A11"].alignment = WRAP
sc_ws.merge_cells("A11:F14")
for col, w in zip("ABCDEF", (14, 14, 9, 9, 9, 11)):
    sc_ws.column_dimensions[col].width = w

# ------------------------------------------------------------ Response_Table
rt = wb.create_sheet("Response_Table")
put(rt, "A1", "RELATIVE CHANGE R(s) vs HEALTHY (before variety tolerance and lesion-age factors). -0.25 = 25% lower than healthy.",
    F_TITLE)
RCODES = [p[0] for p in params if p[0] != "E"]
heads = ["Key", "Class", "Point", "s"] + RCODES
for j, h in enumerate(heads, start=1):
    rt.cell(row=3, column=j, value=h)
style_header(rt, 3, 1, len(heads))
RCOL = {}
r = 4
for name, *_ in CLASSES:
    for pt, scol in (("low", "C"), ("mid", "D"), ("high", "E")):
        rt.cell(row=r, column=1, value=f'=B{r}&"|"&C{r}')
        rt.cell(row=r, column=2, value=name)
        rt.cell(row=r, column=3, value=pt)
        rt.cell(row=r, column=4, value=f"=Severity_Classes!${scol}${CLSROW[name]}").font = F_LINK
        for j, code in enumerate(RCODES, start=5):
            pr = PROW[code]
            P = lambda col: f"Parameters!${col}${pr}"
            s = f"$D{r}"
            f = (f'=IF({P("P")}="logistic",'
                 f'{P("Q")}*{P("R")}*((1/(1+EXP(-({s}-{P("T")})/{P("U")})))-(1/(1+EXP({P("T")}/{P("U")}))))'
                 f'/(1-(1/(1+EXP({P("T")}/{P("U")})))),'
                 f'{P("Q")}*{P("R")}*(1-EXP(-{P("S")}*{s}))'
                 f'+IF({P("P")}="hump",{P("V")}*({s}/{P("W")})*EXP(1-{s}/{P("W")}),0))')
            cell = rt.cell(row=r, column=j, value=f)
            cell.number_format = "0.0%"
            RCOL[code] = CL(j)
        for c in range(1, len(heads) + 1):
            rt.cell(row=r, column=c).border = BORDER
            if name == "Healthy":
                rt.cell(row=r, column=c).fill = FILL_HEALTHY
        r += 1
RT_LAST = r - 1
rt.column_dimensions["A"].width = 18
rt.column_dimensions["B"].width = 12
rt.freeze_panes = "E4"

# ------------------------------------------------------------------- Weather
we = wb.create_sheet("Weather")
src = openpyxl.load_workbook(WEATHER_SRC, data_only=True).active
wh = ["Date", "Tmax (C)", "Tmin (C)", "Rainfall (mm)", "RH I morning (%)", "RH II afternoon (%)", "Sunshine (h)",
      "GDD (base Tbase)", "Mean T (C)", "Mean RH (%)", "Leaf-WR favourable (1/0)", "Staghead favourable (1/0)"]
for j, h in enumerate(wh, start=1):
    we.cell(row=1, column=j, value=h)
style_header(we, 1, 1, len(wh))
wrow = 2
for row in src.iter_rows(values_only=True):
    if row[0] is None:
        continue
    d = row[0].date() if hasattr(row[0], "date") else row[0]
    vals = [d, row[1], row[2], row[3], row[9], row[10], row[11]]
    for j, v in enumerate(vals, start=1):
        c = we.cell(row=wrow, column=j, value=v)
        c.font = F_INPUT
        if j == 1:
            c.number_format = "dd/mm/yyyy"
    we.cell(row=wrow, column=8, value=f"=MAX(0,(B{wrow}+C{wrow})/2-{GEN['Tbase']})").number_format = "0.0"
    we.cell(row=wrow, column=9, value=f"=(B{wrow}+C{wrow})/2").number_format = "0.0"
    we.cell(row=wrow, column=10, value=f"=(E{wrow}+F{wrow})/2").number_format = "0.0"
    we.cell(row=wrow, column=11,
            value=f"=IF(AND(F{wrow}>40,E{wrow}>97,B{wrow}>=16,B{wrow}<=24,J{wrow}>72,I{wrow}>10),1,0)")
    we.cell(row=wrow, column=12,
            value=f"=IF(AND(B{wrow}>=20,B{wrow}<=29,C{wrow}>12,E{wrow}>97,J{wrow}>72),1,0)")
    wrow += 1
W_LAST = wrow - 1
we["K1"].comment = Comment("Chattopadhyay et al. 2011 leaf criteria: RH II >40%, RH I >97%, Tmax 16-24 C, mean RH >72%, mean T >10 C.", "model")
we["L1"].comment = Comment("Chattopadhyay et al. 2011 staghead criteria: Tmax 20-29 C, Tmin >12 C, RH I >97%, mean RH >72%.", "model")
we["F38"].comment = Comment("06/12/2025 RH II = 3.1 in source file: likely a typing error for 31 (before any sowing; does not affect results).", "model")
for j in range(1, len(wh) + 1):
    we.column_dimensions[CL(j)].width = 14
we.freeze_panes = "B2"
WR = lambda col: f"Weather!${col}$2:${col}${W_LAST}"

# ------------------------------------------------------------------- Context
cx = wb.create_sheet("Context")
put(cx, "A1", "TREATMENT x DATE CONTEXT (formulas; Stage column is your field observation)", F_TITLE)
chead = ["Key", "Treatment", "Sowing", "Variety", "Date code", "Date", "Sowing date", "DAS", "DAI",
         "GDD from sowing", "GDD from emergence", "Stage (obs.)", "Leaf sampled", "Tmax wk", "Tmin wk", "RH I wk", "RH II wk",
         "Heat index h", "T at IRGA", "RH at IRGA", "VPD at IRGA (kPa)", "Ta at flight", "RH at flight",
         "VPD at flight (kPa)", "Twet (C)", "Tdry (C)", "Healthy CWSI", "Healthy LAI", "Anth cold factor",
         "Tolerance factor", "Leaf-favourable days from 36 DAS", "Expected DI (%)", "Expected class",
         "Expected class index"] + [f"Plausibility: {c[0]}" for c in CLASSES]
for j, h in enumerate(chead, start=1):
    cx.cell(row=3, column=j, value=h)
style_header(cx, 3, 1, len(chead))
CXC = {h: CL(j) for j, h in enumerate(chead, start=1)}
r = 4
for t in TREATMENTS:
    d, v = t[:2], t[2:]
    for di, (code, date) in enumerate(DATES):
        drow = DATEROW[code]
        put(cx, f"A{r}", f'=B{r}&"|"&E{r}')
        put(cx, f"B{r}", t, F_BOLD)
        put(cx, f"C{r}", d)
        put(cx, f"D{r}", v)
        put(cx, f"E{r}", code)
        put(cx, f"F{r}", f"=Inputs_Treatments!$B${drow}", F_LINK, fmt="dd/mm/yyyy")
        put(cx, f"G{r}", f"=Inputs_Treatments!$B${SOW[d]}", F_LINK, fmt="dd/mm/yyyy")
        put(cx, f"H{r}", f"=F{r}-G{r}", fmt="0")
        put(cx, f"I{r}", f"=F{r}-{GEN['Inoc']}", fmt="0")
        put(cx, f"J{r}", f'=SUMIFS({WR("H")},{WR("A")},">="&G{r},{WR("A")},"<="&F{r})', fmt="0")
        put(cx, f"K{r}", f"=J{r}-{GEN['EmergGDD']}", fmt="0")
        put(cx, f"L{r}", STAGE[t][di], F_INPUT, FILL_INPUT)
        put(cx, f"M{r}", f'=IF(L{r}="V","3rd fully expanded leaf from top","5th fully expanded leaf from top")')
        for col, wcol in zip("NOPQ", "BCEF"):
            put(cx, f"{col}{r}", f'=AVERAGEIFS({WR(wcol)},{WR("A")},">="&(F{r}-6),{WR("A")},"<="&F{r})', fmt="0.0")
        put(cx, f"R{r}", f"=MAX(0,(N{r}-{GEN['HeatThr']})/{GEN['HeatSpan']})", fmt="0.00")
        put(cx, f"S{r}", f"=O{r}+{GEN['fMeas']}*(N{r}-O{r})", fmt="0.0")
        put(cx, f"T{r}", f"=Q{r}+{GEN['gMeas']}*(P{r}-Q{r})", fmt="0.0")
        put(cx, f"U{r}", f"=0.6108*EXP(17.27*S{r}/(S{r}+237.3))*(1-T{r}/100)", fmt="0.00")
        put(cx, f"V{r}", f"=O{r}+{GEN['fFlight']}*(N{r}-O{r})", fmt="0.0")
        put(cx, f"W{r}", f"=Q{r}+{GEN['gFlight']}*(P{r}-Q{r})", fmt="0.0")
        put(cx, f"X{r}", f"=0.6108*EXP(17.27*V{r}/(V{r}+237.3))*(1-W{r}/100)", fmt="0.00")
        put(cx, f"Y{r}", f"=V{r}+{GEN['a_wet']}-{GEN['b_wet']}*X{r}", fmt="0.0")
        put(cx, f"Z{r}", f"=V{r}+{GEN['dT_dry']}", fmt="0.0")
        put(cx, f"AA{r}", f'=IF(L{r}="V",{GEN["CWSI_V"]},IF(L{r}="F",{GEN["CWSI_F"]},{GEN["CWSI_P"]}))+{GEN["CWSI_heat"]}*R{r}',
            fmt="0.00")
        put(cx, f"AB{r}", (f"=Inputs_Treatments!$C${SOW[d]}*Inputs_Treatments!$F${VAR[v]}"
                           f"*(1/(1+EXP(-(K{r}-{GEN['G50']})/{GEN['Gscale']})))"
                           f"*EXP(-((MAX(0,K{r}-{GEN['Gdecl']})/{GEN['Gdeclsc']})^2))"), fmt="0.00")
        put(cx, f"AC{r}", f"=Inputs_Treatments!${CL(5 + di)}${SOW[d]}", F_LINK, fmt="0.00")
        put(cx, f"AD{r}", f"=Inputs_Treatments!$D${VAR[v]}", F_LINK, fmt="0.00")
        put(cx, f"AE{r}", f'=COUNTIFS({WR("K")},1,{WR("A")},">="&(G{r}+36),{WR("A")},"<="&F{r})', fmt="0")
        put(cx, f"AF{r}", f"=Inputs_Treatments!$C${drow}*Inputs_Treatments!$E${VAR[v]}*Inputs_Treatments!$D${SOW[d]}",
            fmt="0.0")
        put(cx, f"AG{r}", (f'=IF(AF{r}<=0,"Healthy",IF(AF{r}<=5,"Very low",IF(AF{r}<=10,"Low",'
                           f'IF(AF{r}<=25,"Moderate",IF(AF{r}<=50,"High","Very high")))))'))
        put(cx, f"AH{r}", f"=MATCH(AG{r},Severity_Classes!$A$4:$A$9,0)", fmt="0")
        for ci in range(1, 7):
            col = CL(34 + ci)
            if ci == 1:
                f = '="Reference: healthy (uninoculated) control plot"'
            else:
                f = (f'=IF(AND(I{r}<8,{ci}>=4),"Unlikely (only via pre-inoculation natural infection)",'
                     f'IF(ABS({ci}-AH{r})<=1,"Likely",IF(ABS({ci}-AH{r})=2,"Possible","Unlikely")))')
            put(cx, f"{col}{r}", f)
        for c in range(1, len(chead) + 1):
            cx.cell(row=r, column=c).border = BORDER
        r += 1
CX_LAST = r - 1
cx.freeze_panes = "C4"
for j in range(1, len(chead) + 1):
    cx.column_dimensions[CL(j)].width = 12
cx.column_dimensions["A"].width = 18
cx.column_dimensions["M"].width = 30
for j in range(35, 41):
    cx.column_dimensions[CL(j)].width = 30
CXR = lambda col: f"Context!${col}$4:${col}${CX_LAST}"

# ---------------------------------------------------------------- Simulation
sm = wb.create_sheet("Simulation")
put(sm, "A1", "SIMULATED (EXPECTED) VALUES - NOT MEASURED DATA. Mean = class mid-DI; Low-High = approx. 90% range; "
    "'% vs H' = change relative to the healthy plot of the same treatment, date, stage and leaf.", F_WARN)
base_cols = ["Key", "Treatment", "Sowing", "Variety", "Date code", "Severity class", "DI range (%)", "s low", "s mid",
             "s high", "Context row", "DAS", "DAI", "Stage", "Leaf sampled", "Heat index h", "VPD at IRGA (kPa)",
             "Tolerance", "Plausibility of class"]
PCODES = ["RWC", "MSI", "Pn", "gs", "E", "Ci", "LAI", "ChlA", "ChlB", "Car", "Anth", "Prot"]
cols = list(base_cols)
for code in PCODES:
    cols += [f"{code} healthy", f"{code} mean", f"{code} low", f"{code} high", f"{code} % vs H"]
derived = ["Total chl mean", "Chl a/b", "Car/Total chl", "WUE Pn/E (umol/mmol)", "iWUE Pn/gs (umol/mol)"]
thermal = ["Ta flight (C)", "Twet (C)", "Tdry (C)", "CWSI healthy", "CWSI", "Tc (C)", "Tc low (C)", "Tc high (C)",
           "CTD = Tc - Ta (C)", "dTc vs healthy (C)", "CTR = Tc/Ta", "IG = (Tdry-Tc)/(Tc-Twet)", "I3 = (Tc-Twet)/(Tdry-Tc)",
           "Tc SD within plot (C)", "Tc P95-P5 spread / MTD proxy (C)"]
cols += derived + thermal
for j, h in enumerate(cols, start=1):
    sm.cell(row=2, column=j, value=h)
style_header(sm, 2, 1, len(cols))
SC = {h: CL(j) for j, h in enumerate(cols, start=1)}

r = 3
for t in TREATMENTS:
    d, v = t[:2], t[2:]
    for code, _ in DATES:
        for cname, rng, *_ in CLASSES:
            put(sm, f"A{r}", f'=B{r}&"|"&E{r}&"|"&F{r}')
            put(sm, f"B{r}", t, F_BOLD)
            put(sm, f"C{r}", d)
            put(sm, f"D{r}", v)
            put(sm, f"E{r}", code)
            put(sm, f"F{r}", cname, F_BOLD)
            put(sm, f"G{r}", rng)
            for col, scol in zip("HIJ", "CDE"):
                put(sm, f"{col}{r}", f"=INDEX(Severity_Classes!${scol}$4:${scol}$9,MATCH(F{r},Severity_Classes!$A$4:$A$9,0))",
                    F_LINK, fmt="0.00")
            put(sm, f"K{r}", f'=MATCH(B{r}&"|"&E{r},{CXR("A")},0)', fmt="0")
            put(sm, f"L{r}", f'=INDEX({CXR("H")},K{r})', fmt="0")
            put(sm, f"M{r}", f'=INDEX({CXR("I")},K{r})', fmt="0")
            put(sm, f"N{r}", f'=INDEX({CXR("L")},K{r})')
            put(sm, f"O{r}", f'=INDEX({CXR("M")},K{r})')
            put(sm, f"P{r}", f'=INDEX({CXR("R")},K{r})', fmt="0.00")
            put(sm, f"Q{r}", f'=INDEX({CXR("U")},K{r})', fmt="0.00")
            put(sm, f"R{r}", f'=INDEX({CXR("AD")},K{r})', fmt="0.00")
            put(sm, f"S{r}", f'=INDEX(Context!$AI$4:$AN${CX_LAST},K{r},MATCH(F{r},Severity_Classes!$A$4:$A$9,0))')
            stage_sel = lambda pr: (f'IF($N{r}="V",Parameters!$I${pr},IF($N{r}="F",Parameters!$J${pr},Parameters!$K${pr}))')
            var_sel = lambda pr: (f'IF($D{r}="V1",Parameters!$M${pr},IF($D{r}="V2",Parameters!$N${pr},Parameters!$O${pr}))')
            age_sel = lambda pr: f"INDEX(Parameters!$X${pr}:$AA${pr},1,MATCH($E{r},Parameters!$X$3:$AA$3,0))"
            rsel = lambda code, pt: (f'INDEX(Response_Table!${RCOL[code]}$4:${RCOL[code]}${RT_LAST},'
                                     f'MATCH($F{r}&"|{pt}",Response_Table!$A$4:$A${RT_LAST},0))')
            for pcode in PCODES:
                pr = PROW[pcode]
                hc, mc, lc, xc, pc = (SC[f"{pcode} healthy"], SC[f"{pcode} mean"], SC[f"{pcode} low"], SC[f"{pcode} high"],
                                      SC[f"{pcode} % vs H"])
                cv = f"Parameters!$F${pr}"
                z = GEN["z"]
                fmt = NUMFMT[pcode]
                if pcode == "E":
                    gsH, gsM, gsL, gsX = (SC["gs healthy"], SC["gs mean"], SC["gs low"], SC["gs high"])
                    k = f"$Q{r}/{GEN['Patm']}*1000"
                    put(sm, f"{hc}{r}", f"={gsH}{r}*{k}", fmt=fmt)
                    put(sm, f"{mc}{r}", f"={gsM}{r}*{k}*(1+{GEN['Cuticle']}*$I{r})", fmt=fmt)
                    put(sm, f"{lc}{r}", f"={gsL}{r}*{k}*(1+{GEN['Cuticle']}*$H{r})", fmt=fmt)
                    put(sm, f"{xc}{r}", f"={gsX}{r}*{k}*(1+{GEN['Cuticle']}*$J{r})", fmt=fmt)
                else:
                    if pcode == "LAI":
                        hf = f'=INDEX({CXR("AB")},$K{r})'
                    else:
                        hf = (f"=Parameters!$E${pr}*{stage_sel(pr)}*(1-Parameters!$L${pr}*$P{r})*{var_sel(pr)}"
                              + (f'*INDEX({CXR("AC")},$K{r})' if pcode == "Anth" else "")
                              + (f"*POWER($Q{r}/{GEN['VPDref']},-{GEN['gsVPDm']})" if pcode == "gs" else ""))
                    put(sm, f"{hc}{r}", hf, fmt=fmt)
                    mult = f"$R{r}*{age_sel(pr)}"
                    vmid = f"{hc}{r}*(1+{rsel(pcode, 'mid')}*{mult})"
                    vlo = f"{hc}{r}*(1+{rsel(pcode, 'low')}*{mult})"
                    vhi = f"{hc}{r}*(1+{rsel(pcode, 'high')}*{mult})"
                    cap = pcode in ("RWC", "MSI")
                    put(sm, f"{mc}{r}", f"=MIN(100,{vmid})" if cap else f"={vmid}", fmt=fmt)
                    lo_f = f"MIN({vlo},{vhi})*(1-{z}*{cv})"
                    hi_f = f"MAX({vlo},{vhi})*(1+{z}*{cv})"
                    put(sm, f"{lc}{r}", f"=MAX(0,{lo_f})", fmt=fmt)
                    put(sm, f"{xc}{r}", f"=MIN(100,{hi_f})" if cap else f"={hi_f}", fmt=fmt)
                put(sm, f"{pc}{r}", f"=IF({hc}{r}=0,0,{mc}{r}/{hc}{r}-1)", fmt="0.0%")
            # derived
            put(sm, f"{SC['Total chl mean']}{r}", f"={SC['ChlA mean']}{r}+{SC['ChlB mean']}{r}", fmt="0.000")
            put(sm, f"{SC['Chl a/b']}{r}", f"={SC['ChlA mean']}{r}/{SC['ChlB mean']}{r}", fmt="0.00")
            put(sm, f"{SC['Car/Total chl']}{r}", f"={SC['Car mean']}{r}/{SC['Total chl mean']}{r}", fmt="0.000")
            put(sm, f"{SC['WUE Pn/E (umol/mmol)']}{r}", f"={SC['Pn mean']}{r}/{SC['E mean']}{r}", fmt="0.00")
            put(sm, f"{SC['iWUE Pn/gs (umol/mol)']}{r}", f"={SC['Pn mean']}{r}/{SC['gs mean']}{r}", fmt="0.0")
            # thermal
            ta, tw, td, chh, cw, tc = (SC["Ta flight (C)"], SC["Twet (C)"], SC["Tdry (C)"], SC["CWSI healthy"],
                                       SC["CWSI"], SC["Tc (C)"])
            put(sm, f"{ta}{r}", f'=INDEX({CXR("V")},$K{r})', fmt="0.0")
            put(sm, f"{tw}{r}", f'=INDEX({CXR("Y")},$K{r})', fmt="0.0")
            put(sm, f"{td}{r}", f'=INDEX({CXR("Z")},$K{r})', fmt="0.0")
            put(sm, f"{chh}{r}", f'=INDEX({CXR("AA")},$K{r})', fmt="0.00")
            eh, em, el, ex = SC["E healthy"], SC["E mean"], SC["E low"], SC["E high"]
            put(sm, f"{cw}{r}", f"=MAX(0,MIN(1,1-(1-{chh}{r})*{em}{r}/{eh}{r}))", fmt="0.00")
            put(sm, f"{tc}{r}", f"={tw}{r}+{cw}{r}*({td}{r}-{tw}{r})", fmt="0.0")
            put(sm, f"{SC['Tc low (C)']}{r}",
                f"={tw}{r}+MAX(0,MIN(1,1-(1-{chh}{r})*{ex}{r}/{eh}{r}))*({td}{r}-{tw}{r})", fmt="0.0")
            put(sm, f"{SC['Tc high (C)']}{r}",
                f"={tw}{r}+MAX(0,MIN(1,1-(1-{chh}{r})*{el}{r}/{eh}{r}))*({td}{r}-{tw}{r})", fmt="0.0")
            put(sm, f"{SC['CTD = Tc - Ta (C)']}{r}", f"={tc}{r}-{ta}{r}", fmt="0.0")
            put(sm, f"{SC['dTc vs healthy (C)']}{r}", f"={tc}{r}-({tw}{r}+{chh}{r}*({td}{r}-{tw}{r}))", fmt="0.0")
            put(sm, f"{SC['CTR = Tc/Ta']}{r}", f"={tc}{r}/{ta}{r}", fmt="0.000")
            put(sm, f"{SC['IG = (Tdry-Tc)/(Tc-Twet)']}{r}", f"=IF({tc}{r}-{tw}{r}<=0,\"n/a\",({td}{r}-{tc}{r})/({tc}{r}-{tw}{r}))",
                fmt="0.00")
            put(sm, f"{SC['I3 = (Tc-Twet)/(Tdry-Tc)']}{r}", f"=IF({td}{r}-{tc}{r}<=0,\"n/a\",({tc}{r}-{tw}{r})/({td}{r}-{tc}{r}))",
                fmt="0.00")
            put(sm, f"{SC['Tc SD within plot (C)']}{r}", f"={GEN['TcSD0']}+{GEN['TcSDslope']}*$I{r}", fmt="0.00")
            put(sm, f"{SC['Tc P95-P5 spread / MTD proxy (C)']}{r}", f"=3.29*{SC['Tc SD within plot (C)']}{r}", fmt="0.0")
            if cname == "Healthy":
                for c in range(1, len(cols) + 1):
                    sm.cell(row=r, column=c).fill = FILL_HEALTHY
            r += 1
SM_LAST = r - 1
sm.freeze_panes = "H3"
for j in range(1, len(cols) + 1):
    sm.column_dimensions[CL(j)].width = 11
sm.column_dimensions["A"].width = 26
sm.column_dimensions["O"].width = 28
sm.column_dimensions["S"].width = 34
SMR = lambda col: f"Simulation!${SC[col]}$3:${SC[col]}${SM_LAST}"

# ----------------------------------------------------------- Stage_Comparison
sg = wb.create_sheet("Stage_Comparison")
put(sg, "A1", "HEALTHY vs EACH SEVERITY CLASS AT EACH GROWTH STAGE (simulated means; averages over all treatment-dates at that stage)",
    F_TITLE)
put(sg, "A2", "Upper block: absolute values. Lower block: % change vs the healthy value of the same stage. Third block: "
    "stage x date. V = vegetative (3rd leaf), F = flowering (5th leaf), P = pod formation (5th leaf).", F_BOLD)
SHOW = [("RWC", "RWC (%)"), ("MSI", "MSI (%)"), ("Pn", "Pn (umol m-2 s-1)"), ("gs", "gs (mol m-2 s-1)"),
        ("E", "E (mmol m-2 s-1)"), ("Ci", "Ci (umol mol-1)"), ("LAI", "LAI"), ("ChlA", "Chl a (ug mg-1 FW)"),
        ("ChlB", "Chl b (ug mg-1 FW)"), ("Car", "Carotenoid (mg g-1 FW)"), ("Anth", "Anthocyanin (ug g-1 FW)"),
        ("Prot", "Protein (ug mg-1 FW)")]
STAGES = [("V", "Vegetative"), ("F", "Flowering"), ("P", "Pod formation")]


def stage_block(top, pct, by_date):
    heads = ["Stage", "Date", "Severity class", "n treatment-dates"] + [s[1] for s in SHOW] + ["Tc (C)", "CTD (C)", "CWSI"]
    for j, h in enumerate(heads, start=1):
        sg.cell(row=top, column=j, value=h)
    style_header(sg, top, 1, len(heads))
    rr = top + 1
    groups = []
    for st, stname in STAGES:
        if by_date:
            for code, _ in DATES:
                groups.append((st, stname, code))
        else:
            groups.append((st, stname, None))
    for st, stname, code in groups:
        healthy_row = rr
        for cname, *_ in CLASSES:
            sg.cell(row=rr, column=1, value=stname).font = F_BOLD
            sg.cell(row=rr, column=2, value=code if code else "All dates")
            sg.cell(row=rr, column=3, value=cname)
            crit = f'{SMR("Stage")},"{st}",{SMR("Severity class")},$C{rr}'
            if code:
                crit += f',{SMR("Date code")},"{code}"'
            sg.cell(row=rr, column=4, value=f"=COUNTIFS({crit})").number_format = "0"
            for j, (pc, _) in enumerate(SHOW + [("Tc", ""), ("CTD", ""), ("CWSI", "")], start=5):
                colname = {"Tc": "Tc (C)", "CTD": "CTD = Tc - Ta (C)", "CWSI": "CWSI"}.get(pc, f"{pc} mean")
                avg = f"AVERAGEIFS({SMR(colname)},{crit})"
                if pct and pc not in ("Tc", "CTD", "CWSI"):
                    hcell = f"{CL(j)}{healthy_row}"
                    # healthy row in the pct block is itself an average; compute ratio of averages
                    hav = avg.replace(f"$C{rr}", f"$C{healthy_row}")
                    f = f"=IF($D{rr}=0,\"\",{avg}/{hav}-1)"
                    fmt = "0.0%"
                elif pct:
                    hav = avg.replace(f"$C{rr}", f"$C{healthy_row}")
                    f = f"=IF($D{rr}=0,\"\",{avg}-{hav})"
                    fmt = "+0.0;-0.0;0.0"
                else:
                    f = f"=IF($D{rr}=0,\"\",{avg})"
                    fmt = {"gs": "0.000", "ChlA": "0.000", "ChlB": "0.000", "Car": "0.000", "Prot": "0.00", "E": "0.00",
                           "LAI": "0.00", "CWSI": "0.00", "Ci": "0"}.get(pc, "0.0")
                c = sg.cell(row=rr, column=j, value=f)
                c.number_format = fmt
            for c in range(1, len(heads) + 1):
                sg.cell(row=rr, column=c).border = BORDER
                if cname == "Healthy":
                    sg.cell(row=rr, column=c).fill = FILL_HEALTHY
            rr += 1
    return rr


nxt = stage_block(4, False, False)
put(sg, f"A{nxt + 1}", "% CHANGE vs HEALTHY AT THE SAME STAGE (thermal columns: difference in C or CWSI units)", F_BOLD)
nxt = stage_block(nxt + 2, True, False)
put(sg, f"A{nxt + 1}", "STAGE x DATE: absolute simulated means (empty rows = that stage does not occur on that date)", F_BOLD)
stage_block(nxt + 2, False, True)
sg.column_dimensions["A"].width = 14
sg.column_dimensions["B"].width = 11
sg.column_dimensions["C"].width = 12
for j in range(4, 22):
    sg.column_dimensions[CL(j)].width = 12
sg.freeze_panes = "D5"

# ---------------------------------------------------------------- Quick_View
qv = wb.create_sheet("Quick_View")
put(qv, "A1", "QUICK VIEW - healthy vs every severity class for one treatment and date (simulated)", F_TITLE)
put(qv, "A3", "Treatment", F_BOLD)
put(qv, "B3", "D2V2", F_INPUT, FILL_INPUT)
put(qv, "A4", "Date code", F_BOLD)
put(qv, "B4", "24/02/2026", F_INPUT, FILL_INPUT)
dv1 = DataValidation(type="list", formula1='"' + ",".join(TREATMENTS) + '"', allow_blank=False)
dv2 = DataValidation(type="list", formula1='"' + ",".join(c for c, _ in DATES) + '"', allow_blank=False)
qv.add_data_validation(dv1)
qv.add_data_validation(dv2)
dv1.add("B3")
dv2.add("B4")
put(qv, "D3", "Stage", F_BOLD)
put(qv, "E3", f'=INDEX({SMR("Stage")},MATCH($B$3&"|"&$B$4&"|Healthy",{SMR("Key")},0))')
put(qv, "D4", "Leaf", F_BOLD)
put(qv, "E4", f'=INDEX({SMR("Leaf sampled")},MATCH($B$3&"|"&$B$4&"|Healthy",{SMR("Key")},0))')
put(qv, "G3", "DAS / DAI", F_BOLD)
put(qv, "H3", f'=INDEX({SMR("DAS")},MATCH($B$3&"|"&$B$4&"|Healthy",{SMR("Key")},0))&" / "&'
    f'INDEX({SMR("DAI")},MATCH($B$3&"|"&$B$4&"|Healthy",{SMR("Key")},0))')
put(qv, "A6", "Edit the yellow cells (drop-down lists). Each parameter shows mean, then range, then % change vs healthy.", F_BOLD)
qh = ["Severity class", "Plausibility"]
for _, lab in SHOW:
    qh += [f"{lab} mean", "range", "% vs H"]
qh += ["Tc (C)", "dTc vs healthy (C)", "CWSI"]
for j, h in enumerate(qh, start=1):
    qv.cell(row=8, column=j, value=h)
style_header(qv, 8, 1, len(qh))
for i, (cname, *_) in enumerate(CLASSES, start=9):
    key = f'$B$3&"|"&$B$4&"|"&$A{i}'
    qv.cell(row=i, column=1, value=cname).font = F_BOLD
    qv.cell(row=i, column=2, value=f'=INDEX({SMR("Plausibility of class")},MATCH({key},{SMR("Key")},0))')
    j = 3
    for code, lab in SHOW:
        fmt = {"gs": "0.000", "ChlA": "0.000", "ChlB": "0.000", "Car": "0.000", "Prot": "0.00", "E": "0.00",
               "LAI": "0.00", "Ci": "0"}.get(code, "0.0")
        tf = fmt.replace("0.0%", "0.0")
        m = f'INDEX({SMR(code + " mean")},MATCH({key},{SMR("Key")},0))'
        lo = f'INDEX({SMR(code + " low")},MATCH({key},{SMR("Key")},0))'
        hi = f'INDEX({SMR(code + " high")},MATCH({key},{SMR("Key")},0))'
        pcf = f'INDEX({SMR(code + " % vs H")},MATCH({key},{SMR("Key")},0))'
        qv.cell(row=i, column=j, value=f"={m}").number_format = fmt
        qv.cell(row=i, column=j + 1, value=f'=TEXT({lo},"{tf}")&" - "&TEXT({hi},"{tf}")')
        qv.cell(row=i, column=j + 2, value=f"={pcf}").number_format = "0.0%"
        j += 3
    for colname, fmt in (("Tc (C)", "0.0"), ("dTc vs healthy (C)", "+0.0;-0.0;0.0"), ("CWSI", "0.00")):
        qv.cell(row=i, column=j, value=f'=INDEX({SMR(colname)},MATCH({key},{SMR("Key")},0))').number_format = fmt
        j += 1
    for c in range(1, len(qh) + 1):
        qv.cell(row=i, column=c).border = BORDER
        if cname == "Healthy":
            qv.cell(row=i, column=c).fill = FILL_HEALTHY
qv.column_dimensions["A"].width = 13
qv.column_dimensions["B"].width = 34
for j in range(3, len(qh) + 1):
    qv.column_dimensions[CL(j)].width = 12
qv.freeze_panes = "C9"

# -------------------------------------------------------- Thermal_Parameters
tp = wb.create_sheet("Thermal_Parameters")
put(tp, "A1", "THERMAL PARAMETERS FOR UAV (FLIR Vue Pro R) AND HANDHELD THERMAL DATA", F_TITLE)
th = ["Parameter", "Formula", "Unit", "Expected direction with white rust", "Notes for your field (IARI, Feb-Mar 2026)"]
for j, h in enumerate(th, start=1):
    tp.cell(row=3, column=j, value=h)
style_header(tp, 3, 1, len(th))
trows = [
    ("Canopy temperature Tc", "Mean of canopy pixels after soil/shadow masking (K-means or NDVI mask)", "C",
     "Increases (less transpirational cooling)", "Fly 11:00-14:00 under clear sky; record Ta and RH at flight time."),
    ("Canopy temperature depression CTD", "Tc - Ta (your ORW definition; many papers use Ta - Tc)", "C",
     "Becomes less negative / positive", "State the sign convention explicitly in the thesis."),
    ("Canopy temperature ratio CTR", "Tc / Ta", "-", "Increases", "Use K if comparing across dates with very different Ta."),
    ("Normalised relative canopy temperature NRCT", "(Tc - Tc,min field) / (Tc,max field - Tc,min field)", "0-1",
     "Increases", "Computed within each flight across all 48 plots."),
    ("Crop water stress index CWSI", "(Tc - Twet) / (Tdry - Twet); Twet = Ta + a - b VPD, Tdry = Ta + 3-5 C", "0-1",
     "Increases", "Empirical baselines; wet/dry reference surfaces (wet cloth, petroleum-jelly leaf) improve it."),
    ("Stomatal conductance index IG", "(Tdry - Tc) / (Tc - Twet)", "-", "Decreases (proportional to gs)",
     "Validate against LI-6400 gs on the same plots."),
    ("Index I3", "(Tc - Twet) / (Tdry - Tc)", "-", "Increases (proportional to 1/gs)", ""),
    ("Within-plot Tc SD", "SD of canopy pixels", "C", "Increases (patchy lesions)", "Sensitive to pixel size (2 cm at 30 m)."),
    ("Maximum temperature difference MTD", "P95 - P5 (or max - min) of canopy pixels", "C", "Increases", ""),
    ("Thermal percentiles", "P10, P50, P90 of canopy Tc", "C", "Upper percentiles rise first", "Liu et al. 2024 used percentile features."),
    ("Thermal GLCM texture", "Contrast, homogeneity, entropy, ASM, correlation, dissimilarity of the thermal image (0, 45, 90, 135 deg; d = 1-5 px)",
     "-", "Contrast/entropy up, homogeneity/ASM down", "As in ORW slide 21."),
]
for i, row in enumerate(trows, start=4):
    for j, v in enumerate(row, start=1):
        c = tp.cell(row=i, column=j, value=v)
        c.alignment = WRAP
        c.border = BORDER
put(tp, "A17", "CAVEATS", F_BOLD)
cav = [
    "1. Pustules form on the LOWER leaf surface; a nadir camera sees the upper surface. Thermal change before 8-11 DAI is not expected "
    "(Chou et al. 2000: transpiration unchanged at 8 DAI while photosynthesis already fell).",
    "2. White pustules may change surface emissivity; rupture can raise cuticular water loss and partly cancel warming.",
    "3. At flowering, yellow petals dominate the canopy view and are warmer than leaves - mask flowers or compare within stage only.",
    "4. Late-season heat (Tmax 30-35 C from 28 Feb) and VPD 2-3 kPa raise Tc of healthy plots too; always use the healthy plot of the "
    "same variety and sowing date as reference (your design allows this).",
    "5. Simulated Tc values (Simulation sheet) use flight-time Ta and VPD estimated from daily data; replace with logged values.",
]
for i, t in enumerate(cav, start=18):
    c = tp.cell(row=i, column=1, value=t)
    c.alignment = WRAP
    tp.merge_cells(start_row=i, start_column=1, end_row=i, end_column=5)
    tp.row_dimensions[i].height = 30
for col, w in zip("ABCDE", (34, 60, 8, 34, 60)):
    tp.column_dimensions[col].width = w

# ------------------------------------------------------------ Texture_Colour
tx = wb.create_sheet("Texture_Colour")
put(tx, "A1", "RGB TEXTURE (GLCM) AND COLOUR INDICES - EXPECTED % CHANGE vs HEALTHY (simulated; LOW confidence)", F_TITLE)
put(tx, "A2", "Change = sign x Rmax x (1 - exp(-k s)) x stage damping. Leaf-level = abaxial (lower) surface photographed at fixed "
    "exposure with colour card; canopy = UAV nadir view (upper surface). Absolute GLCM values depend on grey-level quantisation, "
    "window size, offset and GSD, so only relative changes are given.", F_BOLD)
txh = ["Feature", "Group", "Definition", "Sign", "Rmax leaf (abaxial)", "Rmax canopy (nadir)", "k", "Rationale"]
for j, h in enumerate(txh, start=1):
    tx.cell(row=4, column=j, value=h)
style_header(tx, 4, 1, len(txh))
feats = [
    ("GLCM mean", "GLCM", "sum_i sum_j i P(i,j)", 1, 0.35, 0.08, 3.0, "White pustules brighten the abaxial surface; slight canopy yellowing"),
    ("GLCM variance", "GLCM", "sum (i - mu)^2 P(i,j)", 1, 1.20, 0.25, 3.0, "Bright pustules on green tissue"),
    ("GLCM contrast", "GLCM", "sum (i - j)^2 P(i,j)", 1, 2.50, 0.30, 3.0, "Local grey-level jumps at pustule edges"),
    ("GLCM dissimilarity", "GLCM", "sum |i - j| P(i,j)", 1, 1.20, 0.18, 3.0, "As contrast, linear weighting"),
    ("GLCM homogeneity", "GLCM", "sum P(i,j) / (1 + (i - j)^2)", -1, 0.30, 0.08, 3.0, "Uniform healthy lamina becomes patchy"),
    ("GLCM entropy", "GLCM", "-sum P(i,j) log P(i,j)", 1, 0.22, 0.06, 3.0, "More grey-level randomness"),
    ("GLCM second moment (ASM)", "GLCM", "sum P(i,j)^2", -1, 0.55, 0.15, 3.0, "Less uniformity"),
    ("GLCM correlation", "GLCM", "sum (i - mu_i)(j - mu_j) P(i,j) / (sd_i sd_j)", -1, 0.20, 0.05, 3.0, "Random pustule pattern breaks linear structure"),
    ("NGRDI (G-R)/(G+R)", "Colour", "(G - R)/(G + R)", -1, 0.60, 0.45, 3.0, "Chlorosis lowers green relative to red"),
    ("ExG 2g-r-b (chromatic)", "Colour", "2g - r - b, with r,g,b chromatic coordinates", -1, 0.50, 0.40, 3.0, "Loss of greenness"),
    ("VARI", "Colour", "(G - R)/(G + R - B)", -1, 0.60, 0.50, 3.0, "Loss of greenness"),
    ("GLI", "Colour", "(2G - R - B)/(2G + R + B)", -1, 0.50, 0.40, 3.0, "Loss of greenness"),
    ("RGRI R/G", "Colour", "R / G", 1, 0.40, 0.25, 3.0, "Yellowing"),
    ("Brightness / whiteness (abaxial)", "Colour", "(R + G + B)/3 or HSV value", 1, 0.40, 0.05, 3.0, "Pustule area fraction; best objective severity proxy"),
]
TXROW = {}
for i, f in enumerate(feats, start=5):
    for j, v in enumerate(f, start=1):
        c = tx.cell(row=i, column=j, value=v)
        c.border = BORDER
        if j in (4, 5, 6, 7):
            c.font = F_INPUT
            c.fill = FILL_INPUT
        if j in (3, 8):
            c.alignment = WRAP
    TXROW[f[0]] = i
TX_LAST = 4 + len(feats)
put(tx, f"A{TX_LAST + 2}", "Canopy stage damping (flowers mask leaves at F)", F_BOLD)
damp = [("V", 1.0), ("F", 0.6), ("P", 0.8)]
DAMP = {}
for i, (st, val) in enumerate(damp, start=TX_LAST + 3):
    put(tx, f"A{i}", st)
    put(tx, f"B{i}", val, F_INPUT, FILL_INPUT, "0.00")
    DAMP[st] = f"$B${i}"
blocks = [("LEAF LEVEL (abaxial surface, any stage)", "E", None),
          ("CANOPY - vegetative (UAV nadir)", "F", "V"),
          ("CANOPY - flowering (UAV nadir; petals mask leaves)", "F", "F"),
          ("CANOPY - pod formation (UAV nadir)", "F", "P")]
top = TX_LAST + 8
for title, rcol, st in blocks:
    put(tx, f"A{top}", title, F_BOLD)
    tx.cell(row=top + 1, column=1, value="Severity class")
    for j, f in enumerate(feats, start=2):
        tx.cell(row=top + 1, column=j, value=f[0])
    style_header(tx, top + 1, 1, len(feats) + 1)
    for i, (cname, *_) in enumerate(CLASSES, start=top + 2):
        tx.cell(row=i, column=1, value=cname).font = F_BOLD
        for j, f in enumerate(feats, start=2):
            fr = TXROW[f[0]]
            dmp = f"*{DAMP[st]}" if st else ""
            frm = (f"=$D${fr}*${rcol}${fr}*(1-EXP(-$G${fr}*INDEX(Severity_Classes!$D$4:$D$9,"
                   f"MATCH($A{i},Severity_Classes!$A$4:$A$9,0)))){dmp}")
            c = tx.cell(row=i, column=j, value=frm)
            c.number_format = "0.0%"
            c.border = BORDER
            if cname == "Healthy":
                c.fill = FILL_HEALTHY
    top += 10
tx.column_dimensions["A"].width = 30
tx.column_dimensions["C"].width = 30
tx.column_dimensions["H"].width = 50
for j in range(2, 16):
    if CL(j) not in ("C", "H"):
        tx.column_dimensions[CL(j)].width = 13

# ------------------------------------------------------------------- Sources
so = wb.create_sheet("Sources")
put(so, "A1", "SOURCES AND EVIDENCE BEHIND THE INPUTS", F_TITLE)
sh = ["#", "Reference", "Used for", "Link / note"]
for j, h in enumerate(sh, start=1):
    so.cell(row=3, column=j, value=h)
style_header(so, 3, 1, 4)
srcs = [
    ("Chattopadhyay C. et al. (2011) Epidemiology and development of forecasting models for white rust of Brassica juncea in India. "
     "Archives of Phytopathology and Plant Protection 44(8): 751-763.", "Leaf and staghead weather criteria; later sowing = more disease; onset >=36 DAS",
     "https://doi.org/10.1080/03235400903458571"),
    ("Chou H.-M. et al. (2000) Infection of Arabidopsis thaliana leaves with Albugo candida causes a reprogramming of host metabolism. "
     "Molecular Plant Pathology 1(2): 99-113.", "Timeline: no change at 6 DAI, Pn decline from 8 DAI, A 30% of control at 14 DAI; chl stable to 12 DAI then 40% of control; "
     "Fv/Fm unchanged; transpiration unchanged at 8 DAI", "https://doi.org/10.1046/j.1364-3703.2000.00013.x"),
    ("Mishra K.K. et al. (2009) Pathological and biochemical changes in Brassica juncea infected with Albugo candida. Plant Pathology 58: 80-86.",
     "Protein 4-10% lower in inoculated leaves; incubation 10-13 d; sugars and phenols lower", "https://doi.org/10.1111/j.1365-3059.2008.01939.x"),
    ("Pandey P., Tewari A.K., Awasthi R.P. (2013) Morphological and pathogenic variability of Albugo candida isolates. The Bioscan 8(3): 835-838.",
     "Incubation 4-9 d, latent 9-12 d (cotyledons); Delhi isolate least virulent, small pustules", "User-supplied PDF"),
    ("Rai P. et al. (2024) Transcriptional, biochemical and histochemical response of resistant and susceptible B. juncea to A. candida. "
     "Frontiers in Plant Science 15: 1426302.", "Chl and carotenoids higher in resistant NIL; carotenoids rise in susceptible line early; protein",
     "https://doi.org/10.3389/fpls.2024.1426302"),
    ("Shrivastava A. et al. (2023) Screening of Indian mustard genotypes against white rust based on disease indexing. Biological Forum 15(4): 268-272.",
     "PM-26 susceptible (PDI 44.4); Pusa Vijay highly susceptible (PDI 55.6)", "User-supplied PDF"),
    ("Singh M. et al. (2024) Multivariate analysis of the effects of weather variables on white rust epidemics. Plant Pathology 73: 791-809.",
     "Onset-to-peak ~40 d; maximum severity 40-46%; later sowing earlier onset", "https://doi.org/10.1111/ppa.13851"),
    ("Rana R.S. et al. (2017) Forecasting phenology of mustard crop in North-western Himalayas. J. Appl. Nat. Sci. 9(1): 230-236.",
     "GDD (base 5 C) stage thresholds; emergence 100-125 GDD", "User-supplied PDF"),
    ("Bal R.S., Kumar A. (2014) Studies on the epidemiology of white rust and Alternaria leaf blight. African J. Agric. Res. 9(2): 302-306.",
     "Defoliation at high PDI; lagged weather effect", "https://doi.org/10.5897/AJAR2013.7352"),
    ("Ram L., Awasthi R.P. (2018) Comparative assessment of white rust disease in improved varieties of Indian mustard. IJCMAS 7(5): 1431-1438.",
     "Staghead incidence and severity formulas", "https://doi.org/10.20546/ijcmas.2018.705.170"),
    ("Similar-experiment slides (HR/MR/MS/S classes, 45-85 DAS; unpublished)",
     "Magnitude anchors for Pn, gs, E, Ci, MSI only. Data-integrity concerns noted (duplicated seasons, tables not matching bars).",
     "User-supplied slides"),
    ("Effect of sowing time, varieties and salicylic acid on physiological parameters of Indian mustard (Jobner).",
     "Healthy RWC ~86% at flowering", "https://www.microbiologyjournal.org/influence-of-sowing-time-varieties-and-salicylic-acid-application-on-different-physiological-parameters-of-indian-mustard-brassica-juncea-l/"),
    ("Effect of potassium fertilizer on growth, physiology and water status of Brassica juncea cultivars (PLOS ONE 2021).",
     "MSI 57-73%, RWC up to 85%, chlorophyll and carotenoid ranges", "https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0257023"),
    ("The photosynthetic characteristics of leaves in different-colored Brassica juncea. Plants 14(20): 3197 (2025).",
     "Pn 18-31 umol m-2 s-1 and gs 0.62-0.85 mol m-2 s-1 in green lines", "https://doi.org/10.3390/plants14203197"),
    ("Chlorophyll content of B. juncea M4 mutants (J. Pharmacogn. Phytochem. 2019).", "Total chl 0.86-1.75 mg g-1 FW at 45-65 DAS",
     "https://phytojournal.com/archives/2019/vol8issue3/PartAB/8-2-592-868.pdf"),
    ("Anthocyanins in purple vs green B. juncea leaves (PMC4992693, Table 1).", "Green leaves near detection limit; purple ~22-25 ug g-1 FW per compound",
     "https://pmc.ncbi.nlm.nih.gov/articles/PMC4992693/table/T1"),
    ("Tripathi S.K. et al. (2020) Late-sown Indian mustard, Kanpur (IJCMAS 9(1)).", "CTD ~3.5-3.7 C post-flowering in tolerant genotypes",
     "https://www.ijcmas.com/9-1-2020/Sanjay Kumar Tripathi, et al.pdf"),
    ("JIRCAS JARQ 25(1): remote sensing of physiological depression with thermal imagery.", "Stressed canopy up to 3.1-4.2 C warmer",
     "https://www.jircas.go.jp/en/publication/jarq/25/1/1"),
    ("Jain G., Sandhu S.K. (PAU) Mustard under different dates of sowing.", "LAI highest in early sowing, lowest in 1 Dec sowing",
     "https://phytojournal.com/archives/2018/vol7issue3/PartAI/7-3-493-188.pdf"),
    ("Methods: Barrs & Weatherley 1962 (RWC); Sairam 1994 (MSI); Wellburn 1994 (DMSO pigments); Lee, Durst & Wrolstad 2005 "
     "(pH differential); Bradford 1976 (protein); Haralick et al. 1973 (GLCM); Idso et al. 1981 / Jackson et al. 1981 (CWSI).",
     "Assay definitions, units and index formulas", "Standard method papers"),
    ("IARI weather 31/10/2025-06/04/2026 (user file WEATHER_DATA_Jan_2024_to_tilldate.xlsx).", "All weather-driven terms", "User-supplied"),
]
for i, (ref, use, link) in enumerate(srcs, start=4):
    for j, v in enumerate((i - 3, ref, use, link), start=1):
        c = so.cell(row=i, column=j, value=v)
        c.alignment = WRAP
        c.border = BORDER
for col, w in zip("ABCD", (5, 70, 60, 55)):
    so.column_dimensions[col].width = w

# default font for any unstyled cells
for wsx in wb.worksheets:
    for row in wsx.iter_rows():
        for cell in row:
            if cell.value is not None and (cell.font is None or cell.font.name != FONT):
                cell.font = Font(name=FONT, size=cell.font.size or 10, bold=cell.font.bold, color=cell.font.color)

wb.save(OUT)
print("saved", OUT, "simulation rows", SM_LAST - 2)
