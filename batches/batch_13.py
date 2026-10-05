"""Batch 13 (2026-10-05) = batch 12 re-entered with the author decisions of 2026-10-05 (updated 12 superseded).
Uploaded files 123_real.pdf, 123.pdf, 122_real.pdf, 124_real.pdf, 124.pdf.

  115 (companion)   Pokharel D. et al. 2018 (Cogent Food Agric. 4:1557582)              - SRFSI Sunsari (Nepal) node trials = SRFSI programme of old-master 115:
                                                                                         CTTPR-CTW CT, CTTPR-ZTW pZT, ZTDSR-ZTW / UPTPR-ZTW ZT rows a/b (no residue stated - author)
  174               Gathala M.K. et al. 2017 (J. Ecosys. Ecograph 7:246)                - Modipuram 2005-07: T1/T3 pZT rows a/b, T2/T4 pCA rows a/b, T5 ZT, T6 CA (author)
  175               Hossain M.M., Begum M. & Bell R.W. 2022 (Res. World Agric. Econ.)   - Mymensingh on-farm: TA (plough, puddled) CT vs CA (VMP strip + 50 % residue) MTR
  176               Devkota K.P. et al. 2015 (Eur. J. Agron. 62:98-109)                 - Khorezm (Uzbekistan): ZT (R0) vs CA (R50 / R100), beds and flats, rows a-d;
                                                                                         WSRF-FI (CT water-seeded rice + surface-seeded wheat) = pZT (author); WSRF-AWD row e (2009)
  176 (companion)   Devkota K.P. et al. 2015 (Agric. For. Meteorol. 214-215:266-280)    - same trial: measured yields (Figs 3A / 4, vector) + DSSAT MODEL OUTPUT (Tables 6-7)

Obs on every row = Y + T + D (rule 101). Every row records the paper's method in 'Method used (from paper)'.
Usage: python batches/batch_12.py <in.xlsx> <out.xlsx>
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from lib import Book  # noqa: E402

SRC, OUT = sys.argv[1], sys.argv[2]
DIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "digitised")
B = Book(SRC)
SUPP = "None found - web search 2026-10-05 (publisher pages not reachable from this environment)"


def obs(Y, T=1, D=1):
    o = sum(f for f in (Y, T, D) if f > 1) or 1
    return o, f" [OBS (rule 101): Y={Y} + T={T} + D={D} -> {o}; factors of 1 add nothing.]"


def put(sheet, base, vals, prefix, note, Y=1, T=1, D=1, red=False, **extra):
    d = dict(base)
    for code, v in vals.items():
        d[prefix + code] = v
    d.update(extra)
    o, why = obs(Y, T, D)
    d["Obs"] = o
    d["Notes/Doubts"] = note + why
    return B.add(sheet, d, red=red)


# =====================================================================================
# 174  GATHALA et al. 2017 J Ecosys Ecograph 7:246  (Modipuram, 2005-06 / 2006-07)
# =====================================================================================
G_TRT = ("TREATMENTS IN PAPER (IIFSR Modipuram, RCBD 3 reps, 6 x 20 m plots, 2 rice-wheat cycles 2005-06 and 2006-07; wheat ZERO-TILL drill-seeded (DSW) in ALL plots): "
         "T1 CT-TPR (-S,-WR)/ZT-DSW (-RR): puddled TPR (2 cross harrowings + 2 tyne passes, puddled twice by disc harrow + planking), no Sesbania, wheat stubble removed, rice residue removed; "
         "T2 CT-TPR (+S,+WR)/ZT-DSW (+RR): as T1 + Sesbania intercrop 30 d (brown manure), 15-cm wheat stubble incorporated at puddling, ~8 Mg/ha rice residue retained as mulch "
         "(Turbo Happy Seeder); T3 CT-DSR (-S,-WR)/ZT-DSW (-RR): dry tillage (2 harrowings 12-15 cm + 2 tyne passes + planking), drill-seeded rice, no residue; "
         "T4 CT-DSR (+S,+WR)/ZT-DSW (+RR): as T3 + Sesbania + wheat stubble incorporated by dry tillage + rice residue mulch; T5 ZT-DSR (-S,-WR)/ZT-DSW (-RR); "
         "T6 ZT-DSR (+S,+WR)/ZT-DSW (+RR): wheat stubble left on surface + rice residue mulch. Rice 150-26-50 kg N-P-K + 8.75 Zn; wheat 120-26-50.")
G_MAP = ("row a: pZT = T1 CT-TPR/ZTW (puddled, no residue), pCA = T2 CT-TPR/ZTW + residue ; row b: pZT = T3 CT-DSR/ZTW (conventionally dry-tilled unpuddled DSR, no residue), "
         "pCA = T4 CT-DSR/ZTW + residue (author 2026-10-05) ; ZT = T5 ZT-DSR/ZTW and CA = T6 ZT-DSR/ZTW + residue in both rows")
G = {"No.": 174, "SERIAL NO": 174, "Authors": "Gathala M.K., Jat M.L., Saharawat Y.S., Sharma S.K., Yadvinder-Singh & Ladha J.K.", "Year": 2017,
     "Journal": "Journal of Ecosystem & Ecography", "Country": "India (Uttar Pradesh)", "Site/Location": "IIFSR (PDCSR) research farm, Modipuram, Meerut",
     "latitude": 29.067, "longitude": 77.767, "CLIMATE": "ST", "SOIL": "LOAMY", "Rep": 3, "RAIN FALL": 863, "LATT": 29.067, "MIN TEMP": 5, "MAX TEMP": 46,
     "ph (initial)": 8.1, "soc (initial)": 8.3, "sand": 62, "silt": 20.5, "CLAY": 16.5, "year of data collection/experiment": "2006-07", "DURATION": "0-3 Y",
     "YEAR OF DATA (duration)": 2, "Treatment mapping (paper's name -> code)": G_MAP,
     "Fertilizer dose & other management": ("Rice PHB-71 (TPR last week June / DSR first week June, 25 kg/ha), 150-26-50 kg N-P-K + 8.75 Zn/ha; wheat PBW 343 (100 kg/ha, first week Nov), "
                                            "120-26-50 kg N-P-K/ha, 5 irrigations x 60 mm. SESBANIA brown manure (50 kg/ha seed, 30 d, ~1 Mg/ha DM, killed with 2,4-D) in T2/T4/T6 only "
                                            "(GREEN MANURE - rule 71). Rice irrigated at -20 kPa (15-18 cm). Sandy loam Typic Ustochrept."),
     "Crop/season of sampling": "Wheat season - after wheat harvest, April 2007 (2 cycles)", "Treatment details (from paper)": G_TRT}
G_NOTE = ("AUTHOR CODING 2026-10-05: conventional rice + ZT wheat = partial codes - T1 / T3 pZT, T2 / T4 pCA; T5 ZT, T6 CA. Rows a/b pair the conventional rice establishment of "
          "the partial treatments (a = puddled TPR T1/T2, b = conventionally dry-tilled DSR T3/T4); ZT / CA repeated in both rows (rule 20, T = 2). "
          "FLAG: residue treatments T2/T4/T6 also carry Sesbania brown manure (rule 71) and incorporated wheat stubble (T2/T4). Supplementary: " + SUPP + ". Source file 123.pdf.")
GR = [("a", "T1", "T2"), ("b", "T3", "T4")]  # (row, pZT, pCA); ZT = T5, CA = T6
dig = json.load(open(os.path.join(DIG, "gathala2017_figs.json")))
T2 = {"T1": 0, "T2": 1, "T3": 2, "T4": 3, "T5": 4, "T6": 5}


def gvals(seq_or_map, pzt, pca):
    g = (lambda t: seq_or_map[T2[t]]) if isinstance(seq_or_map, (list, tuple)) else (lambda t: seq_or_map[t])
    return {"pZT": g(pzt), "pCA": g(pca), "ZT": g("T5"), "CA": g("T6")}


def g6(v):
    return "All treatments T1-T6: " + " / ".join(str(x) for x in v) + ". "


# Table 2 (0-15 cm, after 2 cycles)
EC = (0.146, 0.124, 0.127, 0.127, 0.134, 0.128)
OC = (5.72, 5.88, 5.78, 5.97, 5.78, 6.25)
KK = (110.5, 126.2, 111.3, 125.4, 109.4, 129.2)
C84 = (9.5, 10.6, 9.2, 10.5, 11.3, 16.0)
C42 = (8.4, 10.1, 10.7, 11.1, 10.9, 12.5)
C01 = (22.13, 16.93, 20.47, 20.13, 20.67, 16.20)
G0 = {**G, "DEPTH": "0-15 CM", "DEPTH (as reported in paper)": "0-15 cm"}
GMETH_CHEM = "Soil cores (7.6 cm diam.) in triplicate per plot, 0-15 / 15-30 cm, after wheat harvest April 2007, composited, air-dried, <2 mm"
for row, zt, ca in GR:
    lab = f"ROW {row}. "
    put("EC", G0, gvals(EC, zt, ca), "EC_", lab + "Table 2 (letters: T1 a, T2-T4 b, T5 ab, T6 b). Main effects: no residue 0.135, residue 0.126 dS/m. 15-30 cm not different (not printed). "
        + g6(EC) + G_NOTE, T=2, UNIT="dS/m (ratio not stated for treatment samples; initial EC/pH in 1:2 soil:water)", **{"Data source": "Table 2",
        "Method used (from paper)": GMETH_CHEM + "; EC method not stated (initial soil pH/EC in 1:2 soil:water)"})
    put("SOC(active C pool)", G0, gvals(OC, zt, ca), "SOC_", lab + "Table 2 (T6 6.25a highest). Main effects: no residue 5.76, residue 6.03 g/kg. Initial 8.3 g/kg (2005). "
        + g6(OC) + G_NOTE, T=2, UNIT="g/kg (Walkley-Black)", **{"Data source": "Table 2", "Method used (from paper)": GMETH_CHEM + "; organic C by Walkley & Black (1934) [ref. 28]"})
    put("K", G0, gvals(KK, zt, ca), "K_", lab + "Table 2 (residue plots a, no-residue b). Main effects: 110.4 vs 126.9 kg/ha. Olsen-P 14.7-14.9 kg/ha (0-15) and 10.4-11.6 (15-30) "
        "unchanged (data not shown - not entered); pH 7.72-7.80 unchanged. " + g6(KK) + G_NOTE, T=2, UNIT="kg/ha (available K, as printed)",
        **{"Data source": "Table 2", "Method used (from paper)": GMETH_CHEM + "; 1 N neutral NH4OAc-extractable K by flame emission spectrophotometry [ref. 30]"})
GMETH_AGG = ("Wet sieving (Yoder apparatus; Kemper & Rosenau): duplicate undisturbed 0-15 cm samples, air-dried 4.75-8 mm aggregates, 50 g on a nest of 4.75, 2.0, 1.0, 0.5, 0.25 "
             "and 0.106 mm sieves, 10 min pre-wetting, 20 min at 30-35 cycles/min (4 cm stroke), oven-dried 105 C 48 h; MWD = sum(xi wi); after wheat harvest April 2007")
for row, zt, ca in GR:
    lab = f"ROW {row}. "
    classes = "; ".join(f"{t}: 8.00-4.75 mm {C84[i]} %, 4.00-2.00 mm {C42[i]} %, 0.106-0.25 mm {C01[i]} %" for t, i in T2.items())
    agg = dig["AGG>0.25"]
    mrow = put("MACRO", G0, gvals(agg, zt, ca), "MACRO_", lab + "Fig. 2 bars DIGITISED exactly from the vector chart (residue main-effect bars reproduce the treatment means "
               f"within 0.05 %). Initial {agg['Initial']} %; main effects no residue {agg['No residue']}, residue {agg['Residue']} %. Table 2 size classes (not all classes printed): {classes}. "
               + G_NOTE, T=2, UNIT="% (water-stable aggregates >0.25 mm)", **{"Data source": "Fig. 2 (digitised, vector)", "Method used (from paper)": GMETH_AGG})
    irow = put("MICRO", G0, gvals(C01, zt, ca), "MICRO_", lab + "Table 2 class 0.106-0.25 mm (rule 102: water-stable class <0.25 mm). FLAG: the 0.053-0.106 mm part of the "
               "micro-aggregates was not sieved, so MICRO (and WSA) is incomplete. Residue main effect 21.09 vs 17.76 % (P = 0.027). " + G_NOTE, T=2,
               UNIT="% (water-stable micro-aggregates 0.106-0.25 mm)", **{"Data source": "Table 2", "Method used (from paper)": GMETH_AGG})
    put("WSA", G0, {c: f"=ROUND(({B.ref('MACRO', 'MACRO_' + c, mrow)}+{B.ref('MICRO', 'MICRO_' + c, irow)})/100,4)" for c in ("pZT", "pCA", "ZT", "CA")}, "WSA_",
        lab + "DERIVED (rule 102): WSA = MACRO (>0.25 mm, Fig. 2) + MICRO (0.106-0.25 mm, Table 2), live links, % / 100. FLAG: 0.053-0.106 mm class not measured. " + G_NOTE, T=2,
        UNIT="g/g soil (MACRO >0.25 mm + MICRO 0.106-0.25 mm, % / 100)", **{"Data source": "DERIVED (Fig. 2 MACRO + Table 2 MICRO)",
                                                                             "Method used (from paper)": GMETH_AGG + "; WSA = macro + micro (live links)"})
    put("MWD 1", G0, gvals(dig["MWD"], zt, ca), "MWD_", lab + f"Fig. 2 MWD line DIGITISED exactly (vector). Initial {dig['MWD']['Initial']} mm; main effects no residue "
        f"{dig['MWD']['No residue']}, residue {dig['MWD']['Residue']} mm (abstract: +11.9 % for T6 vs T1 - the plotted values give a larger gap; plotted values entered). " + G_NOTE,
        T=2, UNIT="mm (wet sieving)", **{"Data source": "Fig. 2 (digitised, vector)", "Method used (from paper)": GMETH_AGG})
# Fig. 1 BD - 4 layers
GBD = [("0-5 cm", "0-15 CM", 3), ("6-10 cm", "0-15 CM", 3), ("11-15 cm", "0-15 CM", 3), ("16-20 cm", "15-30 CM", 1)]
GMETH_BD = ("Core method: 3 cm long x 5 cm diam. metal cores placed in the middle of the 0-5, 6-10, 11-15 and 16-20 cm layers, oven-dried; after wheat harvest April 2007 "
            "(plotted at layer mid-points 2.5 / 7.5 / 12.5 / 17.5 cm)")
for i, (rep, cls, D) in enumerate(GBD):
    for row, zt, ca in GR:
        base = {**G, "DEPTH": cls, "DEPTH (as reported in paper)": rep}
        v = {t: dig["BD"][t][i] for t in dig["BD"]}
        r = put("BD", base, gvals(v, zt, ca), "BD_", f"ROW {row}. Fig. 1 DIGITISED exactly from the vector polylines (x 1.45-1.80 Mg/m3). Initial {v['Initial']} Mg/m3. "
                "Residue main effect (right panel) not entered. " + G_NOTE, T=2, D=D, UNIT="Mg/m3", **{"Data source": "Fig. 1 (digitised, vector)", "Method used (from paper)": GMETH_BD})
        put("POROSITY", base, {c: f"=ROUND((1-{B.ref('BD', 'BD_' + c, r)}/2.65)*100,2)" for c in ("pZT", "pCA", "ZT", "CA")}, "POROSITY_",
            f"ROW {row}. DERIVED (rule 73): porosity = (1 - BD / 2.65) x 100 from the Fig. 1 BD row (live link); PD not reported - 2.65 Mg/m3 assumed (flag). " + G_NOTE,
            T=2, D=D, UNIT="% v/v (DERIVED, PD 2.65)", **{"Data source": "DERIVED from Fig. 1 BD", "Method used (from paper)": "Porosity = (1 - BD/PD) x 100; BD by core method"})
# Fig. 3 SPR - 9 readings
GPR = [("5 cm", "0-10 CM", 2), ("10 cm", "0-10 CM", 2), ("15 cm", "10-20 CM", 2), ("20 cm", "10-20 CM", 2), ("25 cm", "20-30 CM", 2), ("30 cm", "20-30 CM", 2),
       ("35 cm", "30-40 CM", 2), ("40 cm", "30-40 CM", 2), ("45 cm", "40-50 CM", 1)]
GMETH_PR = ("Manual cone penetrometer (Eijkelkamp; 30 deg cone, 1 cm2 base) at every 5 cm to 45 cm near field capacity (moisture 15.9-16.4, 16.4-16.9, 14.1-14.6, 14.4-14.9 % "
            "at 0-5 / 6-10 / 11-15 / 16-20 cm); after wheat harvest April 2007")
for i, (rep, cls, D) in enumerate(GPR):
    for row, zt, ca in GR:
        put("PR", {**G, "DEPTH": cls, "DEPTH (as reported in paper)": rep}, {k: v[i] for k, v in gvals(dig["SPR"], zt, ca).items()},
            "PR_", f"ROW {row}. Fig. 3 DIGITISED exactly from the vector polylines (x 0-3.5 MPa). Each 5-cm reading its own row (rule 96). Residue main effect not entered. " + G_NOTE,
            T=2, D=D, UNIT="MPa (cone index)", **{"Data source": "Fig. 3 (digitised, vector)", "Method used (from paper)": GMETH_PR})
for row, zt, ca in GR:
    v = gvals(dig["IR_mm_h"], zt, ca)
    put("IR", {**G, "DEPTH": "0-15 CM", "DEPTH (as reported in paper)": "surface (rings 10 cm deep)"}, {c: f"=ROUND({x}/10,4)" for c, x in v.items()}, "IR_",
        f"ROW {row}. Fig. 4 bars DIGITISED exactly (vector), printed mm/h / 10 = cm/hr. Initial {dig['IR_mm_h']['Initial']} mm/h; main effects no residue {dig['IR_mm_h']['No residue']}, "
        f"residue {dig['IR_mm_h']['Residue']} mm/h (bars reproduce the abstract ranges: ZT-DSR 2.97-3.34, CT-PTR 2.41-2.62 mm/h). STEADY-STATE rate (IR_). " + G_NOTE, T=2,
        UNIT="cm/hr (steady-state; printed mm/h / 10)", **{"Data source": "Fig. 4 (digitised, vector) - converted",
                                                            "Method used (from paper)": "Double-ring infiltrometer pushed 10 cm, constant 20 cm head in both rings, run to steady state, 2 points per plot, at wheat harvest"})

# =====================================================================================
# 175  HOSSAIN, BEGUM & BELL 2022 Res. World Agric. Econ. 3(2)
# =====================================================================================
H_TRT = ("TREATMENTS IN PAPER (on-farm, Bhungnamary village, Gouripur, Mymensingh; RCBD 4 reps, 9 x 5 m plots; 2016-17 and 2017-18): crop establishment TA = traditional "
         "agriculture: plough tillage (4 ploughings + cross ploughings by two-wheel tractor), puddled manual transplanting of rice, manual line sowing of wheat / mungbean, "
         "three hand weedings, previous crop residue removed; CA = pre-plant glyphosate + SINGLE (strip) tillage by Versatile Multi-crop Planter (6 x 5 cm strips at row spacing; "
         "rice transplanted into the strips after 24 h flooding - unpuddled), pre- and post-emergence herbicides, 50 % anchored residue of the previous crop; "
         "x cropping system R-W vs R-W-M (summer mungbean after wheat).")
H_MAP = "TA (plough tillage, puddled, no residue) -> CT ; CA (VMP strip / single tillage + 50 % anchored residue) -> MTR (rule 16: strip tillage + residue = MTR even when called CA)"
H = {"No.": 175, "SERIAL NO": 175, "Authors": "Hossain M.M., Begum M. & Bell R.W.", "Year": 2022, "Journal": "Research on World Agricultural Economy",
     "Country": "Bangladesh", "Site/Location": "Farmers' field, Bhungnamary village, Gouripur, Mymensingh", "latitude": 24.4514, "longitude": 90.2411, "CLIMATE": "ST",
     "SOIL": "LOAMY", "Rep": 4, "RAIN FALL": 1720, "LATT": 24.4514, "MIN TEMP": 12, "MAX TEMP": 33, "ph (initial)": 6.81, "sand": 52, "silt": 20, "CLAY": 28,
     "year of data collection/experiment": "2016-17 & 2017-18 (2-yr mean)", "DURATION": "0-3 Y", "YEAR OF DATA (duration)": 2,
     "Treatment mapping (paper's name -> code)": H_MAP,
     "Fertilizer dose & other management": ("N-P-K-S-Zn kg/ha: rice 120-22-35-11-3, wheat 90-26-33-20-2, mungbean 20-20-15-10-1. Rice BRRI hybrid dhan6 (rainfed), wheat BARI Gom 26 "
                                            "(3 irrigations), mungbean BARI Mung 6. CA herbicides: glyphosate 3.7 L + pendimethalin 2.5 L; POH ethoxysulfuron-ethyl (rice), "
                                            "carfentrazone-ethyl + isoproturon (wheat). Sandy clay loam, pH 6.81."),
     "Treatment details (from paper)": H_TRT}
H_NOTE = ("CA strip tillage + 50 % anchored residue -> MTR (rule 16); TA plough + puddling, no residue -> CT. Paper prints 'average annual rainfall 172 mm' - corrected to 1720 mm "
          "(author 2026-10-05). Supplementary: " + SUPP + ". Source file 122_real.pdf.")
H_POOL = ("FLAG: crop values (Tables 2-3) are pooled over the R-W and R-W-M cropping systems and the 2 years (no cell means printed; rule 33 main effect, flagged; "
          "T = 2 paper treatments pooled under each code). MUNGBEAN third crop in the R-W-M half of both codes. ")
HMETH_Y = "Three 3 x 1 m harvest areas per plot, grain yield at 14 % moisture; yield attributes from 10 random plants at 80 % maturity"
HB = {**H, "Crop/season of sampling": "Rice (aman) and wheat, 2016-17 & 2017-18 (pooled)"}
put("YIELD", HB, {"CT": 5.41, "MTR": 6.23}, "RICE YIELD_", "Tables 2-3 (LSD 0.17 / 0.14). " + H_POOL + H_NOTE, Y=2, T=2,
    UNIT="t/ha grain (14 % moisture)", **{"WYIELD_CT": 3.61, "WYIELD_MTR": 4.74, "Data source": "Tables 2-3", "Method used (from paper)": HMETH_Y})
for sysn, ct, mtr, tc in (("R-W", 9.91, 12.76, "R-W system"), ("R-W-M", 13.57, 17.81, "R-W-M system (MUNGBEAN third crop - flag)")):
    put("YIELD", {**H, "Crop/season of sampling": f"{tc}, 2016-17 & 2017-18"}, {"CT": ct, "MTR": mtr}, "SYS YIELD_",
        f"Table 5 cell means for the {sysn} system (rule 33: one row per cropping-system level). REY includes mungbean in R-W-M (rule 54 flag). LUE TA / CA {('81.91 / 76.71' if sysn == 'R-W' else '99.45 / 92.05')} %, "
        f"PE {('33.14 / 45.57' if sysn == 'R-W' else '37.38 / 53.00')} kg/ha/day (no sheet). " + H_NOTE, Y=2,
        UNIT="t/ha system rice-equivalent yield (REY)", **{"Data source": "Table 5",
                                                            "Method used (from paper)": "REY = sum of crop yields converted to rice equivalent at market prices (US$/t wheat 271.14, mungbean 589.71, rice 209.50)"})
put("BC ratio", HB, {"CT": "=ROUND(1.12-1,2)", "MTR": "=ROUND(1.52-1,2)"}, "BC_W",
    "Tables 2-3 printed BCR rice TA 1.07 / CA 1.33, wheat 1.12 / 1.52. CONVERTED to net/cost (printed - 1, rule 57): the paper does not define BCR, but gross/cost is implied - "
    "rice TA gross = 5.41 t x 209.5 US$/t = 1133 US$/ha, so BCR 1.07 as net/cost would give a total cost (547 US$) below the tillage + weeding costs printed in Table 6 alone "
    "(455 US$) plus fertiliser (conversion confirmed by the author 2026-10-05). " + H_POOL + H_NOTE, Y=2, T=2,
    UNIT="ratio (net return / cost; printed gross/cost BCR - 1)", **{"BC_RCT": "=ROUND(1.07-1,2)", "BC_RMTR": "=ROUND(1.33-1,2)", "Data source": "Tables 2-3 - converted",
                                                                       "Method used (from paper)": "Partial budgeting (gross return, gross margin, BCR); 1 US$ = 86.42 BDT"})
put("PANICLE-SPIKE DENSITY", {**HB, "DEPTH": None}, {"CT": 293, "MTR": 324}, "PSD_W",
    "Wheat heads m-2 (Table 3) and rice TILLERS m-2 (Table 2 - effective panicles not printed; tillers entered, flag). Hills m-2 26 / 26, wheat plants m-2 164 / 167 (no sheet). "
    + H_POOL + H_NOTE, Y=2, T=2, UNIT="no. m-2 (wheat spikes; rice tillers)", **{"PSD_RCT": 239, "PSD_RMTR": 288, "Data source": "Tables 2-3", "Method used (from paper)": HMETH_Y})
put("GRAINS PER PANICLE", HB, {"CT": 31, "MTR": 39}, "GPP_W", "Grains head-1 (wheat) and grains panicle-1 (rice). Sterile spikelets panicle-1 rice 35 / 26 (no sheet). "
    + H_POOL + H_NOTE, Y=2, T=2, UNIT="no. grains per panicle / spike", **{"GPP_RCT": 145, "GPP_RMTR": 199, "Data source": "Tables 2-3", "Method used (from paper)": HMETH_Y})
put("1000-GRAIN WEIGHT", HB, {"CT": 44.87, "MTR": 46.13}, "TGW_W", "1000-grain weight (not significant). Mungbean 1000-seed 40.6 / 41.3 g (no column). " + H_POOL + H_NOTE,
    Y=2, T=2, UNIT="g", **{"TGW_RCT": 29.60, "TGW_RMTR": 32.48, "Data source": "Tables 2-3", "Method used (from paper)": HMETH_Y})
for sysn, w_ct, w_ca in (("R-W", 146, 139), ("R-W-M", 150, 139)):
    put("DAYS TO MATURITY", {**H, "Crop/season of sampling": f"{sysn} system, 2016-17 & 2017-18"}, {"CT": w_ct, "MTR": w_ca}, "DTM_W",
        f"Table 5 'growth duration (days)' per crop in the {sysn} system (sowing / transplanting to harvest - flag: definition of the start date not stated; TPR duration may "
        "exclude the nursery). " + ("Mungbean 60 / 54 d. " if sysn == "R-W-M" else "") + H_NOTE, Y=2,
        UNIT="days (crop growth duration, Table 5)", **{"DTM_RCT": 153, "DTM_RMTR": 142, "Data source": "Table 5", "Method used (from paper)": "Growth duration of each crop (days) recorded per plot"})

# =====================================================================================
# 176  DEVKOTA et al. 2015 Eur. J. Agron. 62:98-109  (+ 176 (companion) Agric. For. Meteorol.)
# =====================================================================================
D_TRT = ("TREATMENTS IN PAPER (ZEF/UNESCO Khorezm project, Urgench, Uzbekistan; 2008-2010; laser-levelled, deep-ploughed once before the trial (May 2008); 400 m2 DSR plots, "
         "2000 m2 WSR plots, 4 reps; DSR treatments 70 m from the flooded WSR): DSRB-SSW-R0 / R50 / R100: zero-till dry-seeded rice on PERMANENT raised beds (67 cm, made once "
         "in 2008), AWD irrigation (20 kPa at 20 cm), followed by wheat surface-seeded / zero-till drilled on the same beds; residue R0 = farmer harvest (3-5 cm stubble, ~95 % "
         "removed), R50 = 15-20 cm standing straw, R100 = 35-40 cm standing straw (R50 1.5-4.1, R100 3.0-6.7 t/ha); DSRF-SSW-R0 / R50 / R100: the same on the flat; "
         "WSRF-SSW-FI: conventional (dry) tillage, water-seeded rice continuously flooded (5-15 cm), wheat surface-seeded into the standing rice 17-22 d before harvest, no residue; "
         "WSRF-SSW-AWD (2009 only): as WSRF with AWD, CT non-puddled.")
D_MAP = ("AUTHOR CODING 2026-10-05: WSRF-SSW-FI (conventional dry tillage, water-seeded non-puddled rice + surface-seeded ZT wheat) -> pZT. Rows pair the establishment method: "
         "a: pZT = WSRF-FI, ZT = DSRB-R0, CA = DSRB-R50 ; b: pZT = WSRF-FI, ZT = DSRB-R0, CA = DSRB-R100 ; c: pZT = WSRF-FI, ZT = DSRF-R0, CA = DSRF-R50 ; "
         "d: pZT = WSRF-FI, ZT = DSRF-R0, CA = DSRF-R100 ; e (2009 only): pZT = WSRF-AWD (second pZT treatment), ZT = DSRF-R0, CA = DSRF-R100 (all flat, AWD)")
D = {"No.": 176, "SERIAL NO": 176, "Authors": "Devkota K.P., Lamers J.P.A., Manschadi A.M., Devkota M., McDonald A.J. & Vlek P.L.G.", "Year": 2015,
     "Journal": "European Journal of Agronomy", "Country": "Uzbekistan", "Site/Location": "Khorezm region, Urgench (ZEF/UNESCO experimental station)",
     "latitude": 41.55, "longitude": 60.63, "CLIMATE": "TEMP", "SOIL": "LOAMY", "Rep": 4, "RAIN FALL": 100, "LATT": 41.55, "MIN TEMP": -7, "MAX TEMP": 40, "AVG T": 13.4,
     "soc (initial)": 3.6, "Bdi": 1.35, "sand": 23, "silt": 58, "CLAY": 19, "DURATION": "0-3 Y", "Treatment mapping (paper's name -> code)": D_MAP,
     "Fertilizer dose & other management": ("Rice Nukus-2 (140 kg/ha, drill-seeded 18-21 June), N-P2O5-K2O 257:120:80 (2008) / 250:120:80 (2009); wheat Krasnodar-99 (200 kg/ha, "
                                            "surface-seeded into standing rice), 124:100:70 (2008) / 233:140:70 (2009). Glyphosate pre-plant; azimsulfuron (rice), tribenuron (wheat). "
                                            "DSR on AWD at 20 kPa (1-5 d intervals); WSRF-FI continuously flooded (5-15 cm), WSRF-AWD on AWD; shallow saline groundwater (0.5-2 m); "
                                            "calcaric gleysol, silt loam topsoil."),
     "Treatment details (from paper)": D_TRT}
D_NOTE = ("AUTHOR CODING 2026-10-05: WSRF (conventional dry-tilled water-seeded rice + surface-seeded ZT wheat) = pZT. Rows a-d (rule 20: T = 4 CA treatments; pZT WSRF-FI and ZT "
          "bed / flat repeated) + row e in 2009 for the second pZT treatment WSRF-AWD (T = 5 in 2009). FLAG: WSRF-FI is continuously flooded while the ZT / CA plots are on AWD "
          "(irrigation differs with the code); row e pairs AWD with AWD. Permanent beds without / with residue -> ZT / CA (rule 15). Arid irrigated drylands (<100 mm rain). "
          "Supplementary: " + SUPP + ". Source file 124.pdf.")
DROWS = [("a", "WFI", "B0", "B50"), ("b", "WFI", "B0", "B100"), ("c", "WFI", "F0", "F50"), ("d", "WFI", "F0", "F100"), ("e", "WAWD", "F0", "F100")]
TRT8 = ("B0", "B50", "B100", "F0", "F50", "F100", "WFI", "WAWD")
# Table 5 (gross margin, B:C) - order DSRB R0 R50 R100, DSRF R0 R50 R100, WSRF-FI, WSRF-AWD
GM = {"R2008": (1455, 1318, 894, 1340, 1051, 844, 2066, None), "W2008": (1550, 1270, 1188, 1253, 1294, 1237, 1264, None),
      "R2009": (1251, 898, 58, 1437, 698, -134, 2366, 1378), "W2009": (1190, 1118, 945, 1263, 1054, 814, 1392, 1117),
      "S2008": (3005, 2589, 2082, 2592, 2346, 2080, 3330, None), "S2009": (2441, 2015, 1003, 2700, 1751, 679, 3759, 2496)}
BCR = {"R2008": (1.87, 1.39, 0.80, 1.70, 1.10, 0.75, 2.22, None), "W2008": (3.66, 2.29, 1.85, 2.94, 2.37, 1.91, 2.95, None),
       "R2009": (1.68, 1.06, 0.06, 1.90, 0.80, -0.14, 2.68, 1.76), "W2009": (2.43, 1.84, 1.53, 2.56, 1.73, 1.27, 2.82, 2.26),
       "S2008": (2.50, 1.72, 1.18, 2.14, 1.56, 1.17, 2.45, None), "S2009": (1.98, 1.38, 0.65, 2.16, 1.18, 0.42, 2.73, 1.96)}
DMETH_EC = ("Partial budget from plot records extrapolated to 1 ha: gross revenue (grain + straw x market price, Table 3) - total variable cost (seed, fertiliser, herbicide, "
            "machinery fuel and rental, labour, irrigation pumping at US$ 0.0038 m-3, residue retained valued as purchase cost); BCR = gross margin / total variable cost")


def d8(v):
    return "DSRB R0/R50/R100, DSRF R0/R50/R100, WSRF-FI, WSRF-AWD: " + " / ".join("-" if x is None else str(x) for x in v) + ". "


def dyrows(yi):
    """rows present in year index yi (row e only in 2009), with Y (years in the row's series) and T (rows in that year)"""
    rows = DROWS if yi == 1 else DROWS[:4]
    return [(r, p, z, c, 1 if r == "e" else 2, len(rows)) for r, p, z, c in rows]


for yi, (yr, rk, wk, sk) in enumerate((("2008-09", "R2008", "W2008", "S2008"), ("2009-10", "R2009", "W2009", "S2009"))):
    for row, pz, zt, ca, Yr, Tr in dyrows(yi):
        pi, zi, ci = TRT8.index(pz), TRT8.index(zt), TRT8.index(ca)
        base = {**D, "year of data collection/experiment": yr, "YEAR OF DATA (duration)": yi + 1, "Crop/season of sampling": f"Rice {yr[:4]}, wheat {yr}, rice-wheat system {yr}"}
        put("NET RETURN", base, {"pZT": GM[wk][pi], "ZT": GM[wk][zi], "CA": GM[wk][ci]}, "NR_W", f"ROW {row}. Table 5 GROSS MARGIN (gross revenue - total variable cost). Rice: "
            f"{d8(GM[rk])}Wheat: {d8(GM[wk])}System: {d8(GM[sk])}Overall R-W means (2 yr) in Table 5 not entered (year-wise rows). " + D_NOTE, Y=Yr, T=Tr,
            UNIT="US$/ha GROSS MARGIN (gross revenue - total variable cost)",
            **{"NR_RpZT": GM[rk][pi], "NR_RZT": GM[rk][zi], "NR_RCA": GM[rk][ci], "NR_SYSpZT": GM[sk][pi], "NR_SYSZT": GM[sk][zi], "NR_SYSCA": GM[sk][ci],
               "Data source": "Table 5", "Method used (from paper)": DMETH_EC})
        put("BC ratio", base, {"pZT": BCR[wk][pi], "ZT": BCR[wk][zi], "CA": BCR[wk][ci]}, "BC_W", f"ROW {row}. Table 5 B:C = gross margin / total variable cost (already net/cost - "
            f"entered as printed). Rice: {d8(BCR[rk])}Wheat: {d8(BCR[wk])}System: {d8(BCR[sk])}" + D_NOTE, Y=Yr, T=Tr, UNIT="ratio (gross margin / total variable cost)",
            **{"BC_RpZT": BCR[rk][pi], "BC_RZT": BCR[rk][zi], "BC_RCA": BCR[rk][ci], "BC_SYSpZT": BCR[sk][pi], "BC_SYSZT": BCR[sk][zi], "BC_SYSCA": BCR[sk][ci],
               "Data source": "Table 5", "Method used (from paper)": DMETH_EC})
# Fig. 3 wheat-season ECe (R0, R100 and WSRF-R0 plotted; season 2008-09, before WSRF-AWD existed)
ece = json.load(open(os.path.join(DIG, "devkota2015_ece.json")))
DEC = [("0-10 cm", "0-15 CM", 1), ("10-20 cm", "15-30 CM", 2), ("20-30 cm", "15-30 CM", 2), ("30-50 cm", "30-45 CM", 1), ("50-80 cm", ">60 CM", 1)]
for i, (rep, cls, Dd) in enumerate(DEC):
    for row, zt, ca in (("b", "DSRB-R0", "DSRB-R100"), ("d", "DSRF-R0", "DSRF-R100")):
        put("EC", {**D, "year of data collection/experiment": "2008-09", "YEAR OF DATA (duration)": 1, "DEPTH": cls, "DEPTH (as reported in paper)": rep,
                   "Crop/season of sampling": "Wheat season 2008-09 (mean of 15 sampling dates; panel 'Wheat 2009')"},
            {"pZT": ece["WSRF-R0-FI"][i], "ZT": ece[zt][i], "CA": ece[ca][i]}, "EC_",
            f"ROW {row} (pZT = WSRF-SSW-R0, ZT = R0, CA = R100; R50 not plotted, so T = 2). Fig. 3 'Wheat 2009' panel DIGITISED exactly from the vector markers. "
            "ECe from EC 1:1 paste (flag: saturated-paste basis, saline soil). " + ("Depth class by maximum overlap (50-80 cm -> >60 CM; sequential alternative 45-60 CM - flag). "
            if cls == ">60 CM" else "") + "Rice-season panels (rice 2008, rice 2009) duplicate this parameter -> not entered (rule 35); text: top-30 cm salinity fell 48 % (DSR) and 61 % (WSR) "
            "in rice 2008. " + D_NOTE, T=2, D=Dd, UNIT="dS/m (ECe, saturated-paste equivalent: ECe = 2.02 x EC1:1 + 0.14)",
            **{"Data source": "Fig. 3 (digitised, vector)",
               "Method used (from paper)": ("Tube-auger samples at 0-10, 10-20, 20-30, 30-50, 50-80 cm before irrigation, 15 dates in wheat 2008/09, 5-12 replicates; beds sampled at "
                                            "bed top and furrow centre; EC of 1:1 water:soil paste (Forkutsa 2006) converted to ECe = 2.02 ECp + 0.14 (Akramkhanov et al. 2010)")})

# ---- 176 (companion) Agric. For. Meteorol.
DA = {**D, "No.": "176 (companion)", "SERIAL NO": "176 (companion)", "Journal": "Agricultural and Forest Meteorology",
      "Authors": "Devkota K.P., Hoogenboom G., Boote K.J., Singh U., Lamers J.P.A., Devkota M. & Vlek P.L.G."}
DA_NOTE = ("COMPANION of 176 (same Khorezm trial, 2008-2010; rule 5). " + D_NOTE.replace("Source file 124.pdf", "Source file 124_real.pdf"))
yld = json.load(open(os.path.join(DIG, "devkota2015_yields.json")))
KMAP = {"B0": "DSRB-R0-AWD", "B50": "DSRB-R50-AWD", "B100": "DSRB-R100-AWD", "F0": "DSRF-R0-AWD", "F50": "DSRF-R50-AWD", "F100": "DSRF-R100-AWD",
        "WFI": "WSRF-R0-FI", "WAWD": "WSRF-R0-AWD"}
TABMEAN = {"rice 2008": 4916, "rice 2009": 3293, "wheat 2008": 5366, "wheat 2009": 5411}
for yi, (yr, rk, wk) in enumerate((("2008-09", "rice 2008", "wheat 2008"), ("2009-10", "rice 2009", "wheat 2009"))):
    for row, pz, zt, ca, Yr, Tr in dyrows(yi):
        rv = {k: yld[rk]["points"][KMAP[k]][0][0] for k in (pz, zt, ca)}
        wv = {k: yld[wk]["points"][KMAP[k]][0][0] for k in (pz, zt, ca)}
        put("YIELD", {**DA, "year of data collection/experiment": yr, "YEAR OF DATA (duration)": yi + 1, "Crop/season of sampling": f"Rice {yr[:4]}, wheat {yr} - at harvest"},
            {c: f"=ROUND({rv[k]}/1000,2)" for c, k in (("pZT", pz), ("ZT", zt), ("CA", ca))}, "RICE YIELD_",
            f"ROW {row}. MEASURED grain yields read EXACTLY from the vector scatter of Fig. 3A (rice) / Fig. 4{'A' if yi == 0 else 'B'} (wheat) - y axis = measured, kg/ha / 1000. "
            f"Check: the digitised means reproduce the printed measured means of Tables 4-5 ({rk} {TABMEAN[rk]}, {wk} {TABMEAN[wk]} kg/ha) within 3 kg/ha. " + DA_NOTE,
            Y=Yr, T=Tr, UNIT="t/ha grain (measured; printed kg/ha / 1000; moisture basis not stated)",
            **{**{"WYIELD_" + c: f"=ROUND({wv[k]}/1000,2)" for c, k in (("pZT", pz), ("ZT", zt), ("CA", ca))},
               "Data source": f"Fig. 3A / Fig. 4{'A' if yi == 0 else 'B'} (digitised, vector - measured axis)",
               "Method used (from paper)": "Grain yield measured by standard methods (Devkota et al. 2013c) in 4 replicate plots; used for DSSAT calibration (2008) and evaluation (2009)"})
# Tables 6-7 MODEL OUTPUT (1971-2010 simulations, 39 seasons)
T6 = {"WFI": (5617, 6859), "B0": (3624, 5658), "B50": (3714, 6107), "B100": (3890, 6298), "F0": (3817, 5590), "F50": (3958, 6119), "F100": (4113, 6307), "WAWD": (3429, 5656)}
SOC6 = {"WFI": (44755, 43740), "B0": (36040, 35933), "B50": (46998, 47192), "B100": (54248, 54706), "F0": (36079, 35999), "F50": (47513, 47738), "F100": (55022, 55521), "WAWD": (34057, 33965)}
NUP = {"WFI": (166, 265), "B0": (130, 186), "B50": (137, 199), "B100": (143, 211), "F0": (132, 183), "F50": (143, 199), "F100": (149, 213), "WAWD": (116, 189)}
NLE = {"WFI": (34, 49), "B0": (73, 22), "B50": (90, 35), "B100": (98, 42), "F0": (75, 21), "F50": (93, 33), "F100": (104, 40), "WAWD": (83, 20)}
MO = "MODEL OUTPUT (DSSAT v4.6 CERES-Rice / CERES-Wheat, 1971-2010 weather, mean of 39 simulated seasons; rule 55 - filter on 'MODEL OUTPUT'). "
MMETH = ("DSSAT v4.6 CERES-Rice and CERES-Wheat (cultivar coefficients calibrated on 2008, evaluated on 2009 data), long-term simulation 1971-2010 with measured soil profile "
         "(Table 2) and management; relay sowing of wheat replaced by sowing the day after rice harvest")
MBASE = {**DA, "year of data collection/experiment": "1971-2010 (39-season simulated mean)", "YEAR OF DATA (duration)": 39}
for row, pz, zt, ca in DROWS:
    side = ("Sensitivity runs 9-11 (WSRF puddled, CT-DSR, CT-DSR + deep urea) are hypothetical scenarios - not entered (Table 6). Simulated SOC (kg/ha, 0-80 cm profile, end of rice / "
            "wheat season): " + "; ".join(f"{k} {v[0]}/{v[1]}" for k, v in SOC6.items()) + " - not entered (no depth class for a 0-80 cm model profile stock). ")
    trio = (("pZT", pz), ("ZT", zt), ("CA", ca))
    put("YIELD", {**MBASE, "Crop/season of sampling": "Rice and wheat - simulated"}, {c: f"=ROUND({T6[k][0]}/1000,2)" for c, k in trio}, "RICE YIELD_",
        f"ROW {row}. " + MO + side + DA_NOTE, Y=39, T=5, UNIT="t/ha grain (MODEL OUTPUT; printed kg/ha / 1000)",
        **{**{"WYIELD_" + c: f"=ROUND({T6[k][1]}/1000,2)" for c, k in trio}, "Data source": "MODEL OUTPUT - Table 6", "Method used (from paper)": MMETH})
    for ci, crop in enumerate(("Rice", "Wheat")):
        put("N uptake", {**MBASE, "Crop/season of sampling": f"{crop} - simulated", "N APPLIED (kg/ha)": (250, 233)[ci]}, {c: NUP[k][ci] for c, k in trio}, "NU_",
            f"ROW {row}. {crop} N uptake. " + MO + "Measured N uptake: only the 2009 rice means across treatments (Table 5: grain N 51, TAGB N 96 kg/ha) - not entered. " + DA_NOTE,
            Y=39, T=5, UNIT="kg N/ha (MODEL OUTPUT)", **{"Data source": "MODEL OUTPUT - Table 7", "Method used (from paper)": MMETH})
        put("NO3 leaching", {**MBASE, "DEPTH": ">60 CM", "DEPTH (as reported in paper)": "below the 80-cm profile", "Crop/season of sampling": f"{crop} season - simulated"},
            {c: NLE[k][ci] for c, k in trio}, "NO3L_",
            f"ROW {row}. {crop}-season N LEACHED below 80 cm (DSSAT total N leached, NO3 dominant - flag). " + MO + "Other simulated N losses (immobilised, NH3 volatilised, "
            "denitrified, mineralised) have no sheet. " + DA_NOTE, Y=39, T=5,
            UNIT="kg N/ha per season (MODEL OUTPUT)", **{"Data source": "MODEL OUTPUT - Table 7", "Method used (from paper)": MMETH})

# =====================================================================================
# 115 (companion)  POKHAREL et al. 2018 Cogent Food & Agriculture 4:1557582
# =====================================================================================
P_TRT = ("TREATMENTS IN PAPER (SRFSI project, Sunsari district, Nepal; 5 nodes; 2015-2016; rice-wheat on lowland): CTTPR+CTW = conventional tillage with massive puddling and "
         "manual transplanting of rice + conventional (multiple-tillage) wheat; CTTPR+ZTW = puddled TPR + zero-till drilled wheat; ZTDSR+ZTW = zero-till direct-seeded rice + "
         "ZT wheat; UPTPR+ZTW = unpuddled mechanically (or manually) transplanted rice + ZT wheat. Residue not described in this paper (SRFSI protocol in Islam et al. 2019, "
         "old-master 115: ZT crops into 15-20 cm anchored stubble). Rice-maize system (upland) with the same rice treatments + CTM / ZTM.")
P_MAP = ("CTTPR+CTW -> CT ; CTTPR+ZTW -> pZT ; row a: ZT = ZTDSR+ZTW ; row b: ZT = UPTPR+ZTW (unpuddled = ZT, puddling rule) - residue not described in this paper, so no "
         "residue codes (author 2026-10-05)")
P = {"No.": "115 (companion)", "SERIAL NO": "115 (companion)", "Authors": "Pokharel D., Jha R.K., Tiwari T.P., Gathala M.K., Shrestha H.K. & Panday D.", "Year": 2018,
     "Journal": "Cogent Food & Agriculture", "Country": "Nepal", "Site/Location": "Sunsari district (SRFSI nodes Mahendranagar, Bhokraha, Kaptanjung, Simariya, Bhaluwa)",
     "latitude": 26.67, "longitude": 87.13, "CLIMATE": "ST", "SOIL": "LOAMY", "Rep": 3, "RAIN FALL": 1943, "LATT": 26.67, "MIN TEMP": 10, "MAX TEMP": 43,
     "year of data collection/experiment": "2015-16", "DURATION": "0-3 Y", "YEAR OF DATA (duration)": 2, "Treatment mapping (paper's name -> code)": P_MAP,
     "Fertilizer dose & other management": ("Farmers' fields, SRFSI node trials (long-term trial plots n = 18 rice-wheat; out-scaling blocks 400 m2, n = 162 rice / 153 wheat). "
                                            "Inputs (seed, DAP, urea, MOP) varied by system (Fig. 2, not entered); herbicide weed control in ZT / DSR. Clay loam to silty clay loam "
                                            "(sandy loam at Kaptanjung)."),
     "Treatment details (from paper)": P_TRT}
P_NOTE = ("COMPANION of old-master 115 (Islam S. et al. 2019, SRFSI on-farm trials incl. Sunsari, same four treatments; rule 5) - Sunsari subset, different data set "
          "(DUPLICATE FLAG for the 2015-16 seasons). AUTHOR CODING 2026-10-05: residue retention is not stated in this paper, so the treatments are coded WITHOUT residue - "
          "CTTPR+CTW CT, CTTPR+ZTW pZT, ZTDSR+ZTW / UPTPR+ZTW ZT (rows a/b; T = 2) - although old-master 115 coded the same treatments as CA (residue from its own text). "
          "Rice-maize system excluded (rule 31). Supplementary: " + SUPP + ". Source file 123_real.pdf.")
PROWS = [("a", "ZTDSR+ZTW", 2), ("b", "UPTPR+ZTW", 3)]
RICE1 = (3.02, 3.20, 3.21, 3.14)
SYS3 = {"grain": (8.08, 8.19, 7.15, 8.11), "bio": (15.91, 16.09, 14.42, 15.72), "hi": (0.51, 0.51, 0.50, 0.52), "est": (43508, 33759, 14180, 18853),
        "tvc": (102727, 94267, 78395, 80409), "gross": (232767, 237923, 217781, 237923), "net": (130040, 143656, 139386, 157514), "bc": (2.27, 2.52, 2.78, 2.96), "lab": (100, 89, 57, 71)}
PMETH3 = ("Long-term SRFSI trial plots (rice-wheat n = 18) 2015/2016: grain and biomass yield (t/ha) recorded; costs of seed, fertiliser, manure, irrigation, labour and herbicide "
          "at 2015-16 market prices; gross return = yield x harvest-time price; net profit = gross return - total variable cost")
for row, lab, i in PROWS:
    put("YIELD", {**P, "year of data collection/experiment": "2015 & 2016 (2-yr mean)", "Crop/season of sampling": "Rice (out-scaling blocks), 2015 & 2016"},
        {"CT": RICE1[0], "pZT": RICE1[1], "ZT": RICE1[i]}, "RICE YIELD_",
        f"ROW {row} (ZT = {lab}). Table 1 out-scaling blocks (n = 162 rice plots across treatments), mean +/- SE: 3.02 +/- 0.05, 3.20 +/- 0.04, 3.21 +/- 0.04, 3.14 +/- 0.04 t/ha "
        "(SE kept here; per-treatment n not given, so the SD formula is kept). Wheat (n = 153) printed only as CT 3.15 +/- 0.04 vs ZT 3.06 +/- 0.04 t/ha - ZT pooled over the pZT "
        "and ZT treatments -> not entered. " + P_NOTE, Y=2, T=2, UNIT="t/ha rice grain (moisture basis not stated)",
        **{"Data source": "Table 1", "Method used (from paper)": "Farmers' out-scaling blocks (400 m2): grain yield recorded per plot; two-way ANOVA"})
    yr = put("YIELD", {**P, "Crop/season of sampling": "Rice-wheat system 2015/2016 (long-term trial plots)"},
             {"CT": SYS3["grain"][0], "pZT": SYS3["grain"][1], "ZT": SYS3["grain"][i]}, "SYS YIELD_",
             f"ROW {row} (ZT = {lab}). Table 3 system grain yield (rice + wheat, t/ha). System HI {SYS3['hi'][0]} / {SYS3['hi'][1]} / {SYS3['hi'][2]} / {SYS3['hi'][3]} "
             "(no system HI column). Labour use 100 / 89 / 57 / 71 person-days/ha. " + P_NOTE, T=2, UNIT="t/ha system grain yield (rice + wheat, as printed)",
             **{"Data source": "Table 3", "Method used (from paper)": PMETH3})
    put("SYS STRAW", {**P, "Crop/season of sampling": "Rice-wheat system 2015/2016 (long-term trial plots)"},
        {c: f"=ROUND({SYS3['bio'][j]}-{B.ref('YIELD', 'SYS YIELD_' + c, yr)},2)" for c, j in (("CT", 0), ("pZT", 1), ("ZT", i))}, "SSTRAW_",
        f"ROW {row}. DERIVED (rule 52): system straw = printed system biomass (Table 3: {SYS3['bio'][0]} / {SYS3['bio'][1]} / {SYS3['bio'][2]} / {SYS3['bio'][3]} t/ha) - "
        "system grain (live link to the YIELD row). " + P_NOTE, T=2, UNIT="t/ha system straw (DERIVED: biomass - grain)",
        **{"Data source": "DERIVED from Table 3", "Method used (from paper)": PMETH3 + "; straw = biomass - grain"})
    put("NET RETURN", {**P, "Crop/season of sampling": "Rice-wheat system 2015/2016 (long-term trial plots)"},
        {"CT": SYS3["net"][0], "pZT": SYS3["net"][1], "ZT": SYS3["net"][i]}, "NR_SYS",
        f"ROW {row}. Table 3 net profit (gross return - total variable cost), NRs/ha (NRs 103 = 1 US$). Gross return {SYS3['gross']}; total variable cost {SYS3['tvc']}; crop "
        f"establishment cost {SYS3['est']} NRs/ha. " + P_NOTE, T=2, UNIT="NRs/ha (net profit = gross return - total variable cost)",
        **{"Data source": "Table 3", "Method used (from paper)": PMETH3})
    put("BC ratio", {**P, "Crop/season of sampling": "Rice-wheat system 2015/2016 (long-term trial plots)"},
        {c: f"=ROUND({SYS3['net'][j]}/{SYS3['tvc'][j]},2)" for c, j in (("CT", 0), ("pZT", 1), ("ZT", i))}, "BC_SYS",
        f"ROW {row}. Printed B:C {SYS3['bc']} = gross return / total variable cost (232767 / 102727 = 2.27) -> CONVERTED to net / cost (rule 57) as net profit / TVC from Table 3. "
        + P_NOTE, T=2, UNIT="ratio (net profit / total variable cost; DERIVED from Table 3)",
        **{"Data source": "Table 3 - converted", "Method used (from paper)": PMETH3 + "; B:C = gross return / total variable cost (converted)"})

# =====================================================================================
# Study_Info, LAT_LONG, Treatment_Mapping, EXCLUDED_rows
# =====================================================================================
B.add("Study_Info", {"No.": 174, "SERIAL NO": 174, "Authors": G["Authors"], "Year": 2017, "Journal": "Journal of Ecosystem & Ecography",
                     "Full reference": "Gathala MK, Jat ML, Saharawat YS, Sharma SK, Yadvinder-Singh & Ladha JK (2017) Physical and chemical properties of a sandy loam soil under irrigated rice-wheat sequence in the Indo-Gangetic Plains of South Asia. J Ecosys Ecograph 7(3):246",
                     "DOI / link": "https://doi.org/10.4172/2157-7625.1000246", "Country": "India (Uttar Pradesh)", "Site/Location": G["Site/Location"], "latitude": 29.067, "longitude": 77.767,
                     "latitude (as reported)": "29 deg 4' N", "longitude (as reported)": "77 deg 46' E", "Coordinates source": "Paper", "CLIMATE": "ST",
                     "Experiment established (year)": 2005, "year of data collection/experiment": "2005-06, 2006-07; soil April 2007", "Years of data reported": "1 soil sampling (after 2 cycles)",
                     "DURATION": "0-3 Y", "SOIL": "LOAMY", "Texture as reported": "Sandy loam (sand 620, silt 205, clay 165 g/kg), Typic Ustochrept", "sand": 62, "silt": 20.5, "CLAY": 16.5,
                     "ph (initial)": 8.1, "soc (initial)": 8.3, "MIN TEMP": 5, "MAX TEMP": 46, "RAIN FALL": 863, "Crop rotation": "Rice-wheat (+ Sesbania brown manure in T2/T4/T6)",
                     "Wheat variety": "PBW 343", "Rice variety": "PHB-71", "N dose (kg/ha)": "rice 150, wheat 120", "P dose (kg/ha)": "26 / 26", "K dose (kg/ha)": "50 / 50",
                     "Residue type & rate (t/ha)": "Rice residue ~8 Mg/ha mulch in wheat; 2.25 Mg/ha wheat stubble (T2/T4 incorporated, T6 surface)",
                     "Irrigation / water management": "Rice irrigated at -20 kPa (15-18 cm); wheat 5 x 60 mm", "Treatments in paper": G_TRT,
                     "Parameters extracted": ("0-15 cm EC, SOC, NH4OAc-K, MACRO (Fig. 2), MICRO (0.106-0.25 mm), WSA (derived), MWD; BD 4 layers (Fig. 1) + porosity (derived); "
                                              "SPR 5-45 cm (Fig. 3); steady IR (Fig. 4) - all figures digitised exactly from vector objects"),
                     "Supplementary data?": SUPP,
                     "Notes/Doubts": ("INCLUDED (author coding): pZT (T1 / T3) and pCA (T2 / T4) rows a/b, ZT (T5), CA (T6). Soil temperature (Figs 6-7) and matric potential (Fig. 5) printed only "
                                      "as residue main effects pooled over pZT/ZT or pCA/CA treatments -> not entered (rule 65). Text: minimum soil temperature 1.12-2.21 C higher and maximum "
                                      "2.2-2.8 C lower with residue in early wheat. " + G_NOTE)})
B.add("Study_Info", {"No.": 175, "SERIAL NO": 175, "Authors": H["Authors"], "Year": 2022, "Journal": "Research on World Agricultural Economy",
                     "Full reference": "Hossain MM, Begum M & Bell RW (2022) Land use, productivity, and profitability of traditional rice-wheat system could be improved by conservation agriculture. Res World Agric Econ 3(2):48-58 (article 516)",
                     "DOI / link": "https://doi.org/10.36956/rwae.v3i2.516", "Country": "Bangladesh", "Site/Location": H["Site/Location"], "latitude": 24.4514, "longitude": 90.2411,
                     "latitude (as reported)": "24.4514 N", "longitude (as reported)": "90.2411 E", "Coordinates source": "Paper", "CLIMATE": "ST",
                     "Experiment established (year)": 2016, "year of data collection/experiment": "2016-17, 2017-18", "Years of data reported": "2 (pooled)", "DURATION": "0-3 Y",
                     "SOIL": "LOAMY", "Texture as reported": "Sandy clay loam (sand 52, silt 20, clay 28 %)", "sand": 52, "silt": 20, "CLAY": 28, "ph (initial)": 6.81,
                     "MIN TEMP": 12, "MAX TEMP": 33, "RAIN FALL": 1720, "Crop rotation": "Rice-wheat and rice-wheat-mungbean (cropping-system factor)", "Wheat variety": "BARI Gom 26",
                     "Rice variety": "BRRI hybrid dhan6", "N dose (kg/ha)": "rice 120, wheat 90, mungbean 20", "P dose (kg/ha)": "22 / 26 / 20", "K dose (kg/ha)": "35 / 33 / 15",
                     "Residue type & rate (t/ha)": "CA: 50 % anchored residue of the previous crop (height basis); TA: none",
                     "Irrigation / water management": "Rice rainfed; wheat 3 irrigations; mungbean 2", "Treatments in paper": H_TRT,
                     "Parameters extracted": "Rice / wheat grain yield, B:C (converted), tillers / spikes m-2, grains per panicle, 1000-grain weight (pooled); REY per system; growth duration",
                     "Supplementary data?": SUPP,
                     "Notes/Doubts": "INCLUDED: CT (TA) vs MTR (CA, strip / single tillage + residue). B:C conversion confirmed by the author. No soil data in the paper. Mungbean yields, LUE, PE and Table 6 input costs not entered (no sheets). " + H_NOTE})
B.add("Study_Info", {"No.": 176, "SERIAL NO": 176, "Authors": D["Authors"], "Year": 2015, "Journal": "European Journal of Agronomy",
                     "Full reference": "Devkota KP, Lamers JPA, Manschadi AM, Devkota M, McDonald AJ & Vlek PLG (2015) Comparative advantages of conservation agriculture based rice-wheat rotation systems under water and salt dynamics typical for the irrigated arid drylands in Central Asia. Eur J Agron 62:98-109",
                     "DOI / link": "https://doi.org/10.1016/j.eja.2014.10.002", "Country": "Uzbekistan", "Site/Location": D["Site/Location"], "latitude": 41.55, "longitude": 60.63,
                     "latitude (as reported)": "60.050-61.390 N (printed; coordinates swapped in the paper)", "longitude (as reported)": "41.130-42.020 E (printed)",
                     "Coordinates source": "Approximate (Urgench, Khorezm; paper swaps lat / long)", "CLIMATE": "TEMP", "Experiment established (year)": 2008,
                     "year of data collection/experiment": "2008-2010", "Years of data reported": "2 (year-wise)", "DURATION": "0-3 Y", "SOIL": "LOAMY",
                     "Texture as reported": "Calcaric gleysol; 0-10 cm sand 23, silt 58, clay 19 % (silt loam; Table 2 of the companion)", "sand": 23, "silt": 58, "CLAY": 19,
                     "ph (initial)": 5.6, "soc (initial)": 3.6, "Bdi": 1.35, "MIN TEMP": -7, "MAX TEMP": 40, "AVG T": 13.4, "RAIN FALL": 100,
                     "Crop rotation": "Rice-wheat (fallow between wheat harvest and rice)", "Wheat variety": "Krasnodar-99", "Rice variety": "Nukus-2",
                     "N dose (kg/ha)": "rice 250-257, wheat 124-233", "P dose (kg/ha)": "120 / 100-140 P2O5", "K dose (kg/ha)": "80 / 70 K2O",
                     "Residue type & rate (t/ha)": "R50 1.5-4.1, R100 3.0-6.7 t/ha standing straw (Table 2)",
                     "Irrigation / water management": "DSR AWD (20 kPa at 20 cm); WSR continuous flooding; wheat furrow / flood irrigated", "Treatments in paper": D_TRT,
                     "Parameters extracted": "Gross margin and B:C (rice, wheat, system; 2 years), wheat-season ECe at 5 layers (Fig. 3: WSRF-R0, R0, R100)",
                     "Supplementary data?": SUPP,
                     "Notes/Doubts": ("INCLUDED (author coding): pZT (WSRF-FI rows a-d; WSRF-AWD row e, 2009), ZT (R0) and CA (R50 / R100). Irrigation water (Fig. 1, bed vs flat pooled over residue), "
                                      "infiltration (Fig. 2, DSR vs fallow) and groundwater (Figs 4-5, DSR vs WSR) not entered (no code contrast). " + D_NOTE)})
B.add("Study_Info", {"No.": "176 (companion)", "SERIAL NO": "176 (companion)", "Authors": DA["Authors"], "Year": 2015, "Journal": "Agricultural and Forest Meteorology",
                     "Full reference": "Devkota KP, Hoogenboom G, Boote KJ, Singh U, Lamers JPA, Devkota M & Vlek PLG (2015) Simulating the impact of water saving irrigation and conservation agriculture practices for rice-wheat systems in the irrigated semi-arid drylands of Central Asia. Agric For Meteorol 214-215:266-280",
                     "DOI / link": "https://doi.org/10.1016/j.agrformet.2015.08.264", "Country": "Uzbekistan", "Site/Location": D["Site/Location"], "latitude": 41.55, "longitude": 60.63,
                     "Coordinates source": "As 176", "CLIMATE": "TEMP", "Experiment established (year)": 2008, "year of data collection/experiment": "2008-2010 (measured); 1971-2010 (simulated)",
                     "Years of data reported": "2 measured; 39 simulated", "DURATION": "0-3 Y", "SOIL": "LOAMY", "sand": 23, "silt": 58, "CLAY": 19, "soc (initial)": 3.6, "Bdi": 1.35,
                     "Crop rotation": "Rice-wheat", "Wheat variety": "Krasnodar-99", "Rice variety": "Nukus-2", "Treatments in paper": D_TRT + " Simulation-only scenarios 9-11 (WSRF puddled, CT-DSR, CT-DSR + DPUS).",
                     "Parameters extracted": "Measured rice and wheat grain yields 2008 and 2009 (Figs 3A / 4, vector); MODEL OUTPUT (DSSAT 1971-2010): yields, N uptake, N leached",
                     "Supplementary data?": SUPP,
                     "Notes/Doubts": ("COMPANION of 176. Biomass / LAI dynamics (Figs 2-3), mineral N (Fig. 5, WSR vs pooled DSR) and soil moisture (Fig. 6, one treatment) not entered "
                                      "(no sheet or no code contrast). Initial soil profile (Table 2): BD 1.35-1.57, SOC 0.36-0.19 %, NH4-N 5.2-6.5, NO3-N 3.9-5.3 mg/kg, Olsen P 17.6-27.9, "
                                      "Ex-K 76.8-98.5 mg/kg. " + DA_NOTE)})
B.add("Study_Info", {"No.": "115 (companion)", "SERIAL NO": "115 (companion)", "Authors": P["Authors"], "Year": 2018, "Journal": "Cogent Food & Agriculture",
                     "Full reference": "Pokharel D, Jha RK, Tiwari TP, Gathala MK, Shrestha HK & Panday D (2018) Is conservation agriculture a potential option for cereal-based sustainable farming system in the Eastern Indo-Gangetic Plains of Nepal? Cogent Food Agric 4:1557582",
                     "DOI / link": "https://doi.org/10.1080/23311932.2018.1557582", "Country": "Nepal", "Site/Location": P["Site/Location"], "latitude": 26.67, "longitude": 87.13,
                     "latitude (as reported)": "26 deg 25' to 26 deg 55' N", "longitude (as reported)": "86 deg 55' to 87 deg 21' E", "Coordinates source": "Paper (district range; centre used)",
                     "CLIMATE": "ST", "Experiment established (year)": 2014, "year of data collection/experiment": "2015-2016", "Years of data reported": "2 (pooled)", "DURATION": "0-3 Y",
                     "SOIL": "LOAMY", "Texture as reported": "Clay loam to silty clay loam (sandy loam at Kaptanjung)", "MIN TEMP": 10, "MAX TEMP": 43, "RAIN FALL": 1943,
                     "Crop rotation": "Rice-wheat (lowland); rice-maize (upland, excluded)", "Treatments in paper": P_TRT,
                     "Parameters extracted": "Rice yield (Table 1); system grain yield, straw (derived), net profit, B:C (converted) (Table 3)",
                     "Supplementary data?": SUPP,
                     "Notes/Doubts": "INCLUDED as companion of 115 (author coding): CT, pZT, ZT rows a/b. Survey data (Table 4), input rates (Fig. 2) and weed-control costs (Fig. 3) not entered (no sheets). " + P_NOTE})
for no, au, yr, ctry, site, la, lo, lar, lor, src, cl, note in [
        (174, "Gathala M.K. et al.", 2017, "India (Uttar Pradesh)", "IIFSR Modipuram, Meerut", 29.067, 77.767, "29 deg 4' N", "77 deg 46' E", "Paper", "ST", None),
        (175, "Hossain M.M. et al.", 2022, "Bangladesh", "Bhungnamary, Gouripur, Mymensingh", 24.4514, 90.2411, "24.4514 N", "90.2411 E", "Paper", "ST", None),
        (176, "Devkota K.P. et al.", 2015, "Uzbekistan", "Urgench, Khorezm", 41.55, 60.63, "60.050-61.390 N (swapped)", "41.130-42.020 E (swapped)", "Approximate (Urgench)", "TEMP",
         "Paper prints latitude and longitude swapped"),
        ("176 (companion)", "Devkota K.P. et al.", 2015, "Uzbekistan", "Urgench, Khorezm", 41.55, 60.63, "-", "-", "As 176", "TEMP", "Same trial as 176"),
        ("115 (companion)", "Pokharel D. et al.", 2018, "Nepal", "Sunsari district", 26.67, 87.13, "26 deg 25'-26 deg 55' N", "86 deg 55'-87 deg 21' E", "Paper (range centre)", "ST", None)]:
    B.add("LAT_LONG", {"No.": no, "SERIAL NO": no, "Authors": au, "Year": yr, "Country": ctry, "Site/Location": site, "latitude (as reported)": lar,
                       "longitude (as reported)": lor, "latitude": la, "longitude": lo, "Coordinates source": src, "CLIMATE": cl, "Notes": note})
TM = [
    (174, "Gathala M.K. et al.", 2017, "T1 CT-TPR (-S,-WR)/ZT-DSW (-RR)", "Puddled TPR, no Sesbania, no residue; ZT wheat", "Puddled", "Zero till", "No", None, "pZT", "Row a; puddled rice + ZT wheat, no residue (rule 68)", "High", "INCLUDED"),
    (174, "Gathala M.K. et al.", 2017, "T2 CT-TPR (+S,+WR)/ZT-DSW (+RR)", "Puddled TPR + Sesbania + wheat stubble incorporated; ZT wheat (Turbo Happy Seeder) into ~8 Mg/ha rice residue", "Puddled", "Zero till", "Yes", 8, "pCA", "Row a; puddled rice + ZT wheat + residue (rule 68); Sesbania flag", "High", "INCLUDED - FLAG"),
    (174, "Gathala M.K. et al.", 2017, "T3 CT-DSR (-S,-WR)/ZT-DSW (-RR)", "Dry tillage (2 harrowings + 2 tyne passes + planking), drill-seeded rice; ZT wheat; no residue", "Dry-tilled, unpuddled DSR", "Zero till", "No", None, "pZT", "Row b; author 2026-10-05: conventional dry-tilled rice + ZT wheat = partial code", "High", "INCLUDED (author)"),
    (174, "Gathala M.K. et al.", 2017, "T4 CT-DSR (+S,+WR)/ZT-DSW (+RR)", "As T3 + Sesbania + wheat stubble incorporated + rice residue mulch", "Dry-tilled, unpuddled DSR", "Zero till", "Yes", 8, "pCA", "Row b; author 2026-10-05; Sesbania flag", "High", "INCLUDED (author) - FLAG"),
    (174, "Gathala M.K. et al.", 2017, "T5 ZT-DSR (-S,-WR)/ZT-DSW (-RR)", "Zero-till DSR + ZT wheat, no residue", "Zero till", "Zero till", "No", None, "ZT", "Rows a and b (repeated)", "High", "INCLUDED"),
    (174, "Gathala M.K. et al.", 2017, "T6 ZT-DSR (+S,+WR)/ZT-DSW (+RR)", "Zero-till DSR + Sesbania + surface wheat stubble; ZT wheat into rice residue mulch", "Zero till", "Zero till", "Yes", 8, "CA", "Rows a and b (repeated); Sesbania flag (rule 71)", "High", "INCLUDED"),
    (175, "Hossain M.M. et al.", 2022, "TA (Traditional Agriculture)", "Plough tillage (4 ploughings + cross ploughings, 2WT), puddled TPR, 3 hand weedings, residue removed", "Puddled", "Conventional", "No", None, "CT", "Conventional both phases", "High", "INCLUDED"),
    (175, "Hossain M.M. et al.", 2022, "CA (Conservation Agriculture)", "Glyphosate + single (strip) tillage by VMP, unpuddled strip transplanting, PEH + POH, 50 % anchored residue", "Strip tillage, unpuddled", "Strip tillage (VMP)", "Yes (50 % anchored)", None, "MTR", "Rule 16: strip tillage + residue = MTR even when called CA", "High", "INCLUDED"),
    (176, "Devkota K.P. et al.", 2015, "DSRB-SSW-R0", "ZT dry-seeded rice on permanent beds (AWD) + surface-seeded wheat, farmer harvest (3-5 cm stubble)", "Zero till (permanent beds)", "Zero till / surface seeded", "No (~95 % removed)", None, "ZT", "Rows a/b; permanent beds without residue = ZT (rule 15)", "High", "INCLUDED"),
    (176, "Devkota K.P. et al.", 2015, "DSRB-SSW-R50 / R100", "As DSRB-R0 with 15-20 cm / 35-40 cm standing straw", "Zero till (permanent beds)", "Zero till / surface seeded", "Yes", "1.5-6.7", "CA", "Rows a (R50) / b (R100); permanent beds + residue = CA", "High", "INCLUDED"),
    (176, "Devkota K.P. et al.", 2015, "DSRF-SSW-R0", "ZT dry-seeded rice on the flat (AWD) + surface-seeded wheat, farmer harvest", "Zero till", "Zero till / surface seeded", "No", None, "ZT", "Rows c/d", "High", "INCLUDED"),
    (176, "Devkota K.P. et al.", 2015, "DSRF-SSW-R50 / R100", "As DSRF-R0 with 15-20 / 35-40 cm standing straw", "Zero till", "Zero till / surface seeded", "Yes", "1.5-6.7", "CA", "Rows c (R50) / d (R100)", "High", "INCLUDED"),
    (176, "Devkota K.P. et al.", 2015, "WSRF-SSW-FI / WSRF-SSW-AWD", "Conventional dry tillage, water-seeded rice (flooded / AWD, non-puddled) + wheat surface-seeded into standing rice, no residue", "Conventional dry tillage (non-puddled)", "Zero till / surface seeded", "No", None, "pZT", "Author 2026-10-05: WSRF-FI pZT in rows a-d; WSRF-AWD (2009) second pZT treatment, row e", "High", "INCLUDED (author) - FLAG irrigation"),
    ("176 (companion)", "Devkota K.P. et al.", 2015, "Treatments 2-7 (DSRB / DSRF x R0 / R50 / R100)", "As 176", "Zero till", "Zero till", "R0 no / R50, R100 yes", None, "ZT / CA", "As 176 rows a-d", "High", "INCLUDED"),
    ("176 (companion)", "Devkota K.P. et al.", 2015, "1 WSRF-R0-FI / 8 WSRF-R0-AWD", "As 176", "Conventional dry tillage", "Zero till", "No", None, "pZT", "As 176 (rows a-d / row e)", "High", "INCLUDED (author)"),
    ("176 (companion)", "Devkota K.P. et al.", 2015, "9-11 (simulation only)", "WSRF puddled; CT-DSR; CT-DSR + deep-placed urea", "-", "-", "No", None, "EXCLUDED", "Hypothetical model scenarios, never field-tested", "High", "EXCLUDED"),
    ("115 (companion)", "Pokharel D. et al.", 2018, "CTTPR+CTW", "Conventional tillage, puddled manual TPR + multiple-tillage wheat", "Puddled", "Conventional", "No", None, "CT", "As old-master 115 T1", "High", "INCLUDED"),
    ("115 (companion)", "Pokharel D. et al.", 2018, "CTTPR+ZTW", "Puddled TPR + zero-till drilled wheat", "Puddled", "Zero till", "Not stated", None, "pZT", "Excluded in 115 (mismatch); partial code now (rules 68/85); no residue stated (author 2026-10-05)", "High", "INCLUDED (author)"),
    ("115 (companion)", "Pokharel D. et al.", 2018, "ZTDSR+ZTW", "Zero-till DSR + ZT wheat", "Zero till", "Zero till", "Not stated", None, "ZT", "Row a; residue not stated -> ZT (author 2026-10-05; 115 coded CA)", "High", "INCLUDED (author)"),
    ("115 (companion)", "Pokharel D. et al.", 2018, "UPTPR+ZTW", "Unpuddled mechanical / manual transplanting + ZT wheat", "Unpuddled (zero till)", "Zero till", "Not stated", None, "ZT", "Row b; unpuddled = ZT; residue not stated (author 2026-10-05)", "High", "INCLUDED (author)"),
    ("115 (companion)", "Pokharel D. et al.", 2018, "Rice-maize: CTTPR+CTM / CTTPR+ZTM / ZTDSR+ZTM / UPTPR+ZTM", "Upland rice-maize system", "-", "-", "-", None, "EXCLUDED", "Rice-maize system (rule 31)", "High", "EXCLUDED"),
]
th = ["SERIAL NO", "Authors", "Year", "Paper's treatment label (verbatim)", "Full description from paper", "Rice-phase tillage", "Wheat-phase tillage",
      "Residue retained?", "Residue rate (t/ha)", "ASSIGNED CODE", "Rationale", "Confidence", "Status"]
for row in TM:
    d = dict(zip(th, row))
    d["No."] = row[0]
    B.add("Treatment_Mapping", d)
B.add("EXCLUDED_rows", {"Sheet": "(treatments)", "SERIAL NO": "176 (companion)", "Authors": "Devkota K.P. et al.", "Year": 2015,
                        "Reason for exclusion": "Simulation-only scenarios 9-11 (WSRF-R0-AWD puddled, CT-DSR-AWD, CT-DSR-AWD-DPUS; Table 6-7) - never field-tested, not entered (rule 106).",
                        "Full row (header = value)": "-"})
B.add("EXCLUDED_rows", {"Sheet": "(treatments)", "SERIAL NO": "115 (companion)", "Authors": "Pokharel D. et al.", "Year": 2018,
                        "Reason for exclusion": ("Rice-maize system (rule 31): yields 11.75 / 11.07 / 11.06 / 13.1 t/ha, net profit 179510 / 177576 / 175320 / 237440 NRs/ha, "
                                                 "B:C 2.69 / 2.88 / 2.84 / 3.47 (CTTPR+CTM / CTTPR+ZTM / ZTDSR+ZTM / UPTPR+ZTM); maize Table 1 6.49 / 5.81 / 5.86 / 6.86 t/ha."),
                        "Full row (header = value)": "-"})
B.save(OUT)
print("batch 13 written to", OUT)
