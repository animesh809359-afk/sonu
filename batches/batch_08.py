"""Batch 08 (2026-10-05) = batch 07 papers re-entered with the author decisions of 2026-10-05 (118.pdf, 119_real.pdf, 117_real.pdf, 117.pdf).

  15 (companion 2)  Gathala M.K. et al. 2011 (Soil Sci. Soc. Am. J. 75:1851-1862)   - Modipuram trial of old-master 15: T1 CT, T2 pZT, ZT T5/T6 and MT T3/T4 (rows a/b)
  40 (companion)    Kader M.A. et al. 2022 (Field Crops Res. 287:108636)            - BAU Mymensingh trial of old-master 40: CT -> CTR, ST -> MTR (rows a LR / b HR)
  23 (companion 5)  Roy D. et al. 2022 (Geoderma 405:115391)                        - CSSRI Karnal scenario trial: Sc1 CT, Sc2 pCA, Sc3 CA (Sc4-Sc6 excluded)
  170               Kukal S.S. & Aggarwal G.C. 2003 (Soil Tillage Res. 72:1-8)       - INCLUDED (author): unpuddled ZT, shallow puddling MT, normal puddling CT

Every row carries the paper's method in 'Method used (from paper)' (author instruction 2026-10-05).

New sheets (run batches/add_sheets_08.py first): LLWR, SOIL TEMP, AGG SIZE CLASS.

Usage: python batches/batch_08.py <in.xlsx> <out.xlsx>
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


def put(sheet, base, vals, prefix, red=False, **extra):
    d = dict(base)
    for code, v in vals.items():
        d[prefix + code] = v
    d.update(extra)
    return B.add(sheet, d, red=red)


RED_NOTE_K = "RICE-SEASON DATA (RED ROW): measured at rice harvest / before wheat seedbed preparation (stage row, rule 90). "

# =====================================================================================
# 15 (companion 2)  GATHALA et al. 2011 SSSAJ  (author coding 2026-10-05: T1 CT, T2 pZT, T3/T4 MT, T5/T6 ZT)
# =====================================================================================
GA_TRT = ("TREATMENTS IN PAPER (Modipuram, est. kharif 2002, RCBD 3 reps, 15.0 x 6.7 m plots; ~1 Mg/ha anchored stubble after every crop in ALL plots, "
          "incorporated in CT/puddled plots, standing in ZT plots): T1 CT-TPR/CT-DSW (puddled TPR; wheat after conventional tillage, drill-seeded) -> CT ; "
          "T2 CTAWD-TPR/ZT-DSW (puddled TPR with mid-season AWD; ZT drill-seeded wheat) -> pZT ; T3 Bed-DSR/Bed-DSW (permanent raised beds, DSR; beds reshaped "
          "in one tractor pass at wheat sowing) -> MT row a ; T4 Bed-TPR/Bed-DSW (permanent beds, transplanted rice, reshaped for wheat) -> MT row b ; "
          "T5 ZT-DSR/ZT-DSW -> ZT row a ; T6 ZT-TPR/ZT-DSW (zero-till plots flooded 1 d before transplanting, not puddled) -> ZT row b.")
GA = {"No.": "15 (companion 2)", "SERIAL NO": "15 (companion 2)",
      "Authors": "Gathala M.K., Ladha J.K., Saharawat Y.S., Kumar V., Kumar V. & Sharma P.K.", "Year": 2011,
      "Journal": "Soil Science Society of America Journal", "Country": "India (Uttar Pradesh)",
      "Site/Location": "SVBPUAT research farm, Modipuram, Meerut (IRRI-India trial of old-master 15)",
      "latitude": 29.017, "longitude": 77.75, "CLIMATE": "ST", "SOIL": "LOAMY", "Rep": 3, "RAIN FALL": 800, "LATT": 29.017,
      "MIN TEMP": 2, "MAX TEMP": 43, "ph (initial)": 8.1, "sand": 55, "silt": 26, "CLAY": 19,
      "Treatment mapping (paper's name -> code)": ("T1 -> CT ; T2 (puddled TPR-AWD + ZT wheat) -> pZT ; row a: ZT = T5 ZT-DSR/ZT-DSW, MT = T3 Bed-DSR/Bed-DSW ; "
                                                   "row b: ZT = T6 ZT-TPR/ZT-DSW, MT = T4 Bed-TPR/Bed-DSW (rows pair the rice establishment: a = DSR, b = TPR)"),
      "Fertilizer dose & other management": ("Rice NDR 359: 150 N (+22.5 kg N at 20 DAS in DSR), 26 P, 50 K, 8.75 Zn kg/ha; wheat PBW 343: 150 N, 26 P, 50 K kg/ha. "
                                             "TPR flooded 2 wk then irrigated at hairline cracks (T2: 10-15 d interval 20-70 DAT, AWD); DSR irrigated every 3-4 d for 4 wk then at hairline cracks; "
                                             "wheat 6 irrigations (furrows filled on beds). ~1 Mg/ha stubble left after each crop in all plots. Sandy loam, pH 8.1, ESP 13.5, total C 8.3 g/kg (2002)."),
      "Treatment details (from paper)": GA_TRT}
GA_NOTE = ("COMPANION of old-master 15 (Gathala et al. 2011 Agron. J., same trial; old-master 15 used T1 CT vs T5 ZT only). AUTHOR CODING 2026-10-05: T1 CT, T2 pZT "
           "(puddled AWD rice + ZT wheat; FLAG AWD), T3 and T4 (permanent beds reshaped at every wheat sowing) MT, T5 and T6 ZT. Rows a/b pair the rice establishment "
           "(a: T5 ZT-DSR + T3 bed-DSR; b: T6 ZT-TPR + T4 bed-TPR); CT and pZT repeated in both rows (rule 20, T = 2 in Obs). Residue is not a treatment factor (~1 Mg/ha "
           "stubble in all) -> no R codes. Supplementary: " + SUPP + ". Source file 118.pdf (scanned).")
GROWS = [("a", "T5", "T3"), ("b", "T6", "T4")]
T_R = 2


def gv(src, zt, mt, k=None):
    pick = (lambda t: src[t]) if k is None else (lambda t: src[t][k])
    return {"CT": pick("T1"), "pZT": pick("T2"), "ZT": pick(zt), "MT": pick(mt)}


GC = ("CT", "pZT", "ZT", "MT")
# Table 2 BD (4-yr average 2005-06 to 2008-09, after wheat harvest)
GBD = {"T1": (1.48, 1.58, 1.74, 1.76), "T2": (1.50, 1.59, 1.75, 1.77), "T3": (1.47, 1.60, 1.66, 1.70),
       "T4": (1.50, 1.59, 1.67, 1.71), "T5": (1.55, 1.60, 1.67, 1.71), "T6": (1.55, 1.61, 1.67, 1.71)}
GLAY = [("0-15 CM", "0-5 cm", 3), ("0-15 CM", "6-10 cm", 3), ("0-15 CM", "11-15 cm", 3), ("15-30 CM", "16-20 cm", 1)]
BD_M = "Core method: 3-cm long x 5-cm i.d. metal cores placed in the middle of each layer (0-5, 6-10, 11-15, 16-20 cm), after wheat harvest"
gbd_row = {}
for k, (depth, rep, D) in enumerate(GLAY):
    for row, zt, mt in GROWS:
        obs = 4 + T_R + (D if D > 1 else 0)
        base = {**GA, "year of data collection/experiment": "2005-06 to 2008-09 (4-yr mean)", "DURATION": "4-10 Y", "YEAR OF DATA (duration)": "4-7 (mean)",
                "DEPTH": depth, "DEPTH (as reported in paper)": rep, "Obs": obs,
                "Crop/season of sampling": "Wheat season - after wheat harvest, 2005-06 to 2008-09 (pooled; no T x Y interaction)"}
        nt = (f"ROW {row} (ZT = {zt}, MT = {mt}). 4-YEAR MEAN (no treatment x year interaction; year-wise values not printed). Obs = Y4 + T2" + (f" + D{D}" if D > 1 else "")
              + f" = {obs}. " + GA_NOTE)
        r = put("BD", base, gv(GBD, zt, mt, k), "BD_", UNIT="Mg/m3", **{"Data source": "Table 2", "Method used (from paper)": BD_M, "Notes/Doubts": nt})
        gbd_row[(k, row)] = r
        put("POROSITY", base, {c: f"=ROUND((1-{B.ref('BD', 'BD_' + c, r)}/2.65)*100,2)" for c in GC}, "POROSITY_", UNIT="% v/v",
            **{"Data source": "DERIVED from Table 2 BD", "Method used (from paper)": "Porosity = (1 - BD/PD) x 100 (PD measured by pycnometer in the paper but not printed)",
               "Notes/Doubts": f"ROW {row}. DERIVED (rule 73): PD values not printed -> 2.65 Mg/m3 (flag). Live link to the BD row. " + GA_NOTE})

# Fig. 1 SPR (4-yr average; digitised) - every 5-cm reading its own row
spr = json.load(open(os.path.join(DIG, "gathala2011_SPR.json")))
SPR_CLS = [("0-10 CM", [5, 10]), ("10-20 CM", [15, 20]), ("20-30 CM", [25, 30]), ("30-40 CM", [35, 40]), ("40-50 CM", [45])]
for cls, depths in SPR_CLS:
    for dcm in depths:
        i = spr["depth_cm"].index(dcm)
        D = len(depths)
        for row, zt, mt in GROWS:
            obs = 4 + T_R + (D if D > 1 else 0)
            hid = [t for t in ("T1", "T2", zt, mt) if dcm in spr["hidden"].get(t, [])]
            base = {**GA, "year of data collection/experiment": "2005-06 to 2008-09 (4-yr mean)", "DURATION": "4-10 Y", "YEAR OF DATA (duration)": "4-7 (mean)",
                    "DEPTH": cls, "DEPTH (as reported in paper)": f"{dcm} cm (point reading, 5-cm steps to 45 cm)", "Obs": obs,
                    "Crop/season of sampling": "Wheat season - after wheat harvest, 2005-06 to 2008-09 (pooled)"}
            put("PR", base, {c: spr[t][i] for c, t in zip(GC, ("T1", "T2", zt, mt))}, "PR_", UNIT="MPa (cone index)",
                **{"Data source": "Fig. 1 (digitised, scanned figure)",
                   "Method used (from paper)": "Manual cone penetrometer (Eijkelkamp), 1-cm2 cone base, every 5 cm to 45 cm; gravimetric moisture sampled simultaneously (22-28 % v/v up to 30 cm)",
                   "Notes/Doubts": (f"ROW {row} (ZT = {zt}, MT = {mt}). DIGITISED by hand from the scanned Fig. 1 (6 overlapping black series; +/-0.05 MPa). "
                                    + (f"Marker hidden for {', '.join(hid)} at {dcm} cm - read from the series line (flag). " if hid else "")
                                    + "Checks: 20 cm puddled 3.46/3.72 and ZT/bed 2.51-2.83 vs text 3.46-3.72 / 2.51-2.82. "
                                    f"4-YEAR MEAN. Obs = Y4 + T2" + (f" + D{D}" if D > 1 else "") + f" = {obs}. " + GA_NOTE)})

# Table 3 WSA >0.25 mm (year-wise, after wheat harvest, 0-15 cm)
GWSA = {"T1": (54.33, 53.90, 54.07, 53.67, 50.07, 49.93), "T2": (54.20, 53.10, 55.27, 55.53, 52.20, 51.27),
        "T3": (57.67, 56.33, 63.87, 69.60, 70.07, 70.13), "T4": (54.93, 55.33, 60.93, 68.00, 69.07, 68.60),
        "T5": (61.47, 55.27, 64.20, 72.67, 74.67, 75.20), "T6": (56.27, 53.40, 63.67, 69.40, 71.67, 72.27)}
GYRS = ["2003-04", "2004-05", "2005-06", "2006-07", "2007-08", "2008-09"]
WSA_M = "Wet sieving (Yoder 1936) of 4.75-8 mm air-dried aggregates through 8.00, 4.75, 2.00, 1.00, 0.50, 0.25 and 0.11 mm sieves; % aggregation >0.25 mm"
for j, yr in enumerate(GYRS):
    dur = j + 2
    for row, zt, mt in GROWS:
        base = {**GA, "year of data collection/experiment": yr, "DURATION": "0-3 Y" if dur <= 3 else "4-10 Y", "YEAR OF DATA (duration)": dur,
                "DEPTH": "0-15 CM", "DEPTH (as reported in paper)": "0-15 cm", "Obs": T_R, "Crop/season of sampling": f"Wheat season - after wheat harvest {yr}"}
        put("MACRO", base, gv(GWSA, zt, mt, j), "MACRO_", UNIT="% (water-stable aggregates >0.25 mm)",
            **{"Data source": "Table 3", "Method used (from paper)": WSA_M,
               "Notes/Doubts": (f"ROW {row} (ZT = {zt}, MT = {mt}). Year-wise (rule 37); 2002-03 not measured. WSA (>0.053 mm) cannot be derived - the finest sieve is 0.11 mm. "
                                "Overall MANOVA means T1 52.66, T2 53.59, T3 64.61, T4 62.81, T5 67.24, T6 64.44 %. Size classes after 7 yr: AGG SIZE CLASS sheet. " + GA_NOTE)})

# Fig. 2 water-stable aggregate size classes after 7 cycles (digitised) -> AGG SIZE CLASS + derived MWD
f235 = json.load(open(os.path.join(DIG, "gathala2011_figs235.json")))
agg = f235["fig2_aggregate_classes_pct"]
MID = [6.375, 3.375, 1.5, 0.75, 0.375, 0.18, 0.055]
for row, zt, mt in GROWS:
    base = {**GA, "year of data collection/experiment": "2008-09", "DURATION": "4-10 Y", "YEAR OF DATA (duration)": 7,
            "DEPTH": "0-15 CM", "DEPTH (as reported in paper)": "0-15 cm", "Obs": T_R, "Crop/season of sampling": "Wheat season - after the 7th rice-wheat cycle (2008-09 wheat harvest)"}
    crow = []
    for ci, cl in enumerate(agg["classes"]):
        crow.append(put("AGG SIZE CLASS", base, gv(agg, zt, mt, ci), "AGGC_", UNIT="% of soil (water-stable aggregates in the class)",
                        **{"Aggregate size class (mm)": cl, "Data source": "Fig. 2 (digitised, scanned figure)", "Method used (from paper)": WSA_M.replace("; % aggregation >0.25 mm", "; mass in each sieve class"),
                           "Notes/Doubts": (f"ROW {row} (ZT = {zt}, MT = {mt}). DIGITISED by hand from the scanned Fig. 2 (+/-0.5 %; classes 2-4 of T3-T6 overlap and were read from the lines). "
                                            "Check: classes >0.25 mm sum to Table 3 2008-09 within ~1 %. " + GA_NOTE)}))
    put("MWD 1", base, {c: "=ROUND(" + "+".join(f"{m}*{B.ref('AGG SIZE CLASS', 'AGGC_' + c, rr)}/100" for m, rr in zip(MID, crow)) + ",2)" for c in GC}, "MWD_",
        UNIT="mm (wet sieving; DERIVED from size classes)",
        **{"Data source": "DERIVED from Fig. 2 size classes", "Method used (from paper)": "MWD = sum(class mean diameter x mass fraction); class means 6.375, 3.375, 1.5, 0.75, 0.375, 0.18, 0.055 mm",
           "Notes/Doubts": (f"ROW {row}. DERIVED (flag): the paper says MWD 'followed a trend similar to WSA (data not shown)'; computed here from the digitised classes "
                            "(live links to AGG SIZE CLASS), fractions of whole soil not re-normalised (classes sum to 88-96 %). " + GA_NOTE)})

# Table 5 steady-state infiltration (cm/h) at wheat harvest
GIR = {"T1": (0.24, 0.25, 0.18, 0.14, 0.14, 0.13), "T2": (0.26, 0.25, 0.18, 0.12, 0.13, 0.13), "T3": (0.31, 0.31, 0.43, 0.46, 0.44, 0.44),
       "T4": (0.27, 0.30, 0.32, 0.32, 0.29, 0.32), "T5": (0.21, 0.33, 0.34, 0.35, 0.35, 0.39), "T6": (0.18, 0.30, 0.28, 0.31, 0.32, 0.34)}
IYRS = [("2002-03", 1), ("2003-04", 2), ("2005-06", 4), ("2006-07", 5), ("2007-08", 6), ("2008-09", 7)]
for j, (yr, dur) in enumerate(IYRS):
    for row, zt, mt in GROWS:
        base = {**GA, "year of data collection/experiment": yr, "DURATION": "0-3 Y" if dur <= 3 else "4-10 Y", "YEAR OF DATA (duration)": dur,
                "DEPTH": "0-15 CM", "DEPTH (as reported in paper)": "soil surface (rings pushed to 10 cm)", "Obs": T_R,
                "Crop/season of sampling": f"Wheat season - at wheat harvest {yr}"}
        put("IR", base, gv(GIR, zt, mt, j), "IR_", UNIT="cm/hr (steady-state)",
            **{"Data source": "Table 5",
               "Method used (from paper)": "Double-ring infiltrometer, 2 per plot pushed to 10 cm (bed centre on raised beds), constant 5-cm head, run to steady state",
               "Notes/Doubts": f"ROW {row} (ZT = {zt}, MT = {mt}). Year-wise; 2004-05 not recorded. Overall MANOVA means T1 0.18, T2 0.18, T3 0.40, T4 0.30, T5 0.33, T6 0.29 cm/h. " + GA_NOTE})

# SOC 0-15 cm after 7 cycles (text) + derived stock
GSOC = {"T1": 0.55, "T2": 0.55, "T3": 0.59, "T4": 0.57, "T5": 0.67, "T6": 0.62}
for row, zt, mt in GROWS:
    base = {**GA, "year of data collection/experiment": "2008-09", "DURATION": "4-10 Y", "YEAR OF DATA (duration)": 7,
            "DEPTH": "0-15 CM", "DEPTH (as reported in paper)": "0-15 cm", "Obs": T_R, "Crop/season of sampling": "Wheat season - after the 7th rice-wheat cycle (2008-09)"}
    sr = put("SOC(active C pool)", base, {c: f"={v}*10" for c, v in gv(GSOC, zt, mt).items()}, "SOC_", UNIT="g/kg (printed % x 10)",
             **{"Data source": "Text (Soil Aggregation section)", "Method used (from paper)": "Walkley & Black wet oxidation (method stated for soil OC analysis)",
                "Notes/Doubts": f"ROW {row} (ZT = {zt}, MT = {mt}). Printed in % (T1-T6 0.55, 0.55, 0.59, 0.57, 0.67, 0.62). Initial (2002) total C 8.3 g/kg (not SOC). " + GA_NOTE})
    bds = {c: [B.ref("BD", "BD_" + c, gbd_row[(k, row)]) for k in range(3)] for c in GC}
    put("stock-SOC", base, {c: f"=ROUND({B.ref('SOC(active C pool)', 'SOC_' + c, sr)}*AVERAGE({','.join(bds[c])})*15*0.1,2)" for c in GC}, "SOCs_",
        **{"DEPTH": "0-20 CM", "DEPTH (as reported in paper)": "0-15 cm (cumulative class 0-20 CM, rule 43)", "UNIT": "Mg C/ha",
           "Data source": "DERIVED (text SOC x Table 2 BD)", "Method used (from paper)": "Stock = SOC x mean BD(0-5, 6-10, 11-15 cm) x 15 cm x 0.1",
           "Notes/Doubts": f"ROW {row}. DERIVED (rule 48): 2008-09 SOC x the 4-yr mean BD of the three 0-15 cm layers (live links). No initial SOC (only total C). " + GA_NOTE})

# Fig. 5 LLWR (2008-09 wheat season) -> LLWR sheet
ll = f235["fig5_LLWR_pct_vv"]
for rep_ in ("0-5", "6-10"):
    for row, zt, mt in GROWS:
        put("LLWR", {**GA, "year of data collection/experiment": "2008-09", "DURATION": "4-10 Y", "YEAR OF DATA (duration)": 7,
                     "DEPTH": "0-15 CM", "DEPTH (as reported in paper)": f"{rep_} cm", "Obs": 1 + T_R + 2,
                     "Crop/season of sampling": "Wheat season 2008-09 - repeated readings from the first irrigation (~3 wk) onward"},
            gv(ll[rep_], zt, mt), "LLWR_", UNIT="% v/v",
            **{"Data source": "Fig. 5 (bars measured on the scan)",
               "Method used (from paper)": ("LLWR (Sharma & Bhushan 2001; Verma & Sharma 2008) = volumetric water content at 10 % air-filled porosity minus water content at SPR 1.75 MPa; "
                                            "gravimetric water x core BD; total porosity from BD and pycnometer PD; SPR by cone penetrometer"),
               "Notes/Doubts": (f"ROW {row} (ZT = {zt}, MT = {mt}). Obs = Y1 + T2 + D2 = 5 (0-5 and 6-10 cm separate rows). Bars measured on the scan (+/-0.05); T2 3.0/3.1 and T5 6.2/5.8 "
                                "are the printed text values. LLWR vs wheat yield: y = 0.249x + 3.71 (5 cm, R2 0.52), y = 0.287x + 3.59 (10 cm, R2 0.45). Initial AWC 15.6 % v/v. " + GA_NOTE)})

# Fig. 3 weekly soil temperature at 5 cm (only T1, T3, T5 plotted) -> SOIL TEMP sheet (one row per week and time of day)
st = f235["fig3_soil_temp_5cm"]
for key, lab in (("morning_0700", "0700 h (morning)"), ("afternoon_1500", "1500 h (afternoon)")):
    for w in range(20):
        put("SOIL TEMP", {**GA, "year of data collection/experiment": "2006-07 to 2008-09 (3-season mean)", "DURATION": "4-10 Y", "YEAR OF DATA (duration)": "5-7 (mean)",
                          "DEPTH": "0-15 CM", "DEPTH (as reported in paper)": "5 cm", "Obs": 3,
                          "Crop/season of sampling": f"Wheat season week {w + 1} - {lab}"},
            {"CT": st[key]["T1"][w], "MT": st[key]["T3"][w], "ZT": st[key]["T5"][w]}, "STEMP_", UNIT="deg C (weekly mean of daily readings)",
            **{"Data source": "Fig. 3 (digitised, scanned figure)",
               "Method used (from paper)": "Digital soil thermometer (Hanna HI 93510 thermistor) at 5 cm, daily at 0700 (minimum) and 1500 h (maximum); weekly means averaged over 2006-07, 2007-08, 2008-09",
               "Notes/Doubts": ("Stage-wise row per week (rule 90). Only T1 (CT), T3 (MT, row a) and T5 (ZT, row a) are plotted - no pZT / row b. Obs = Y3. DIGITISED by hand from "
                                "the scanned Fig. 3 (+/-0.15 C). " + GA_NOTE)})

# Table 6 yields (7-yr average) - kept (author 2026-10-05) with the duplicate flag
GY = {"T1": (8.10, 4.76, 12.86), "T2": (7.81, 4.97, 12.77), "T3": (4.62, 4.71, 9.33), "T4": (6.16, 4.24, 10.40), "T5": (6.80, 5.37, 12.19), "T6": (6.87, 5.22, 12.09)}
for row, zt, mt in GROWS:
    d = {**GA, "year of data collection/experiment": "2002-03 to 2008-09 (7-yr mean)", "DURATION": "4-10 Y", "YEAR OF DATA (duration)": "1-7 (mean)", "Obs": 7 + T_R,
         "UNIT": "t/ha grain (Mg/ha)", "Crop/season of sampling": "Rice and wheat, 7-yr mean 2002-2009", "Data source": "Table 6",
         "Method used (from paper)": "Crops harvested manually at 15 cm above ground; 7-yr mean (MANOVA for repeated measures)",
         "Notes/Doubts": (f"ROW {row} (ZT = {zt}, MT = {mt}). KEPT on author instruction 2026-10-05; DUPLICATE FLAG: the year-wise yields behind the T1 and T5 means are in "
                          "old-master 15 (Agron. J. 2011). Obs = Y7 + T2 = 9. Time-trend slopes (Mg/ha/yr) rice T1 0.134, T2 0.262, T3 -0.446, T4 -0.139, T5 0.013, T6 -0.083; "
                          "wheat 0.106, 0.080, 0.074, 0.048, 0.230, 0.227. " + GA_NOTE)}
    for col, k in (("RICE YIELD_", 0), ("WYIELD_", 1), ("SYS YIELD_", 2)):
        for c, v in gv(GY, zt, mt, k).items():
            d[col + c] = v
    B.add("YIELD", d)


# =====================================================================================
# 40 (companion)  KADER et al. 2022 Field Crops Res.
# =====================================================================================
KA_TRT = ("TREATMENTS IN PAPER (BAU farm, Mymensingh, est. monsoon rice 2012, split-split plot, 3 reps, 7 x 7 m sub-sub plots; rice-wheat-mungbean every year): "
          "main plot tillage - CT = conventional (rice: soil flooded 5-6 cm and puddled with 4 rotary passes of a 2-wheel-tractor rotary tiller; wheat and mungbean: "
          "4 full cross rotary passes) -> CTR ; ST = strip tillage (Versatile Multi-crop Planter, 4-6 cm wide x 5-6 cm deep strips, 75-80 % of soil untilled; rice "
          "transplanted unpuddled into strips softened overnight) -> MTR. Sub-plot residue - LR = 15 % of crop height retained (farmers' practice) / HR = 30 % of rice "
          "and wheat + 100 % mungbean residue -> both residue-retained (rows a = LR, b = HR). Sub-sub plot N - 60, 80, 100, 120, 140 % of RFD (RFD 75 / 100 / 20 kg N/ha "
          "rice / wheat / mungbean).")
KA = {"No.": "40 (companion)", "SERIAL NO": "40 (companion)",
      "Authors": "Kader M.A., Jahangir M.M.R., Islam M.R., Begum R., Nasreen S.S., Islam Md.R., Mahmud A.Al., Haque M.E., Bell R.W. & Jahiruddin M.", "Year": 2022,
      "Journal": "Field Crops Research", "Country": "Bangladesh", "Site/Location": "Bangladesh Agricultural University farm, Mymensingh (Old Brahmaputra Floodplain)",
      "latitude": 24.724, "longitude": 90.437, "CLIMATE": "ST", "SOIL": "LOAMY", "Rep": 3, "RAIN FALL": 2400, "LATT": 24.724,
      "ph (initial)": 6.92, "soc (initial)": 13.2, "Bdi": 1.58, "sand": 11, "silt": 76, "CLAY": 13,
      "Treatment mapping (paper's name -> code)": "CT (puddled rice, 4-pass rotary for wheat) + LR/HR -> CTR ; ST (strip tillage, unpuddled) + LR/HR -> MTR ; row a = LR (15 %), row b = HR (30 %)",
      "Fertilizer dose & other management": ("100 % RFD: rice 75, wheat 100, mungbean 20 kg N/ha (urea; rice 50/25/25 %, wheat 3 equal splits, mungbean basal); rice 10 P, 30 K, 10 S, 2 Zn; "
                                             "wheat 20 P, 60 K, 10 S, 2 Zn, 1.5 B; mungbean 20 P, 30 K, 10 S kg/ha; basal fertiliser in the strips (ST) or broadcast (CT). Glyphosate "
                                             "1.85 kg a.i./ha before every crop (both tillage). Rice BRRI dhan49 rainfed (Jul-Nov); wheat BARI Gom 25 (2 irrigations, 35-40 mm); "
                                             "mungbean Binamung 8 rainfed. Silt loam Aeric Haplaquept, initial OC 13.2 g/kg, BD 1.58, pH 6.92."),
      "Treatment details (from paper)": KA_TRT}
KA_NOTE = ("COMPANION of old-master 40 (Mumu et al. 2024 SSRN; same BAU trial est. 2012, same coordinates; coded CT-LR/HR -> CTR, ST-LR/HR -> MTR there). "
           "THIRD CROP: mungbean every year in both tillage systems (rule 71). CT here is 4-pass rotary (CT under the rotary rule) with puddling for rice. "
           "Supplementary Tables S1-S4 (year-wise main-effect yields) not reachable - " + SUPP + ". Source file 119_real.pdf.")
# Table 6 tillage x residue (pooled over N), 0-15 cm after 23rd crop (wheat 2019-20)
KS = {"LR": {"CT": (1.30, 1.1, 1.1, 21.5, 156), "ST": (1.30, 1.5, 1.4, 27.3, 198)},
      "HR": {"CT": (1.28, 1.1, 1.4, 26.9, 175), "ST": (1.27, 1.5, 1.6, 30.5, 240)}}
KTN = ("Tillage x N cells (pooled over residue; BD, TN g/kg, OC %, stock t/ha, MBC mg/kg): CT N1-N5 1.30/1.1/1.2/23.4/155, 1.29/1.1/1.2/23.2/163, 1.28/1.3/1.2/23.0/158, "
       "1.29/1.3/1.3/25.1/151, 1.30/1.5/1.3/25.4/199; ST N1-N5 1.29/1.3/1.4/27.1/197, 1.29/1.3/1.4/27.1/223, 1.28/1.4/1.5/28.8/227, 1.28/1.4/1.6/30.7/242, 1.29/1.5/1.6/31.0/205. ")
for row, lev in (("a", "LR"), ("b", "HR")):
    ct, st = KS[lev]["CT"], KS[lev]["ST"]
    base = {**KA, "year of data collection/experiment": "2019-20 (after 23rd crop, wheat)", "DURATION": "4-10 Y", "YEAR OF DATA (duration)": 8,
            "DEPTH": "0-15 CM", "DEPTH (as reported in paper)": "0-15 cm", "Obs": 2,
            "Crop/season of sampling": "Wheat season - after harvest of the 23rd crop (wheat, 2019-20)"}
    nt = (f"ROW {row} = {lev} ({'15' if lev == 'LR' else '30'} % residue) in both codes. TILLAGE x RESIDUE cell means POOLED OVER THE 5 N RATES (no 3-way cell means printed; flag, rule 33). "
          "Obs = T2 (rows a/b). " + KTN + KA_NOTE)
    br = put("BD", base, {"CTR": ct[0], "MTR": st[0]}, "BD_", UNIT="Mg/m3",
             **{"Data source": "Table 6", "Method used (from paper)": "Core sampler method (Blake & Hartge 1986), cores from 15 spots per plot", "Notes/Doubts": nt})
    put("POROSITY", base, {c: f"=ROUND((1-{B.ref('BD', 'BD_' + c, br)}/2.65)*100,2)" for c in ("CTR", "MTR")}, "POROSITY_", UNIT="% v/v",
        **{"Data source": "DERIVED from Table 6 BD", "Method used (from paper)": "Porosity = (1 - BD/PD) x 100",
           "Notes/Doubts": f"ROW {row}. DERIVED (rule 73): no PD in the paper -> 2.65 Mg/m3 (flag). " + KA_NOTE})
    put("total N", base, {"CTR": f"=ROUND({ct[1]}*1000,0)", "MTR": f"=ROUND({st[1]}*1000,0)"}, "TN_", UNIT="mg/kg (printed g/kg x 1000)",
        **{"Data source": "Table 6 - converted", "Method used (from paper)": "Total N, Kjeldahl (Page et al. 1982); auger samples (2.5 cm), 15 cores per plot (4 in strip/row, rest between)",
           "Notes/Doubts": nt})
    sr = put("SOC(active C pool)", base, {"CTR": f"={ct[2]}*10", "MTR": f"={st[2]}*10"}, "SOC_", UNIT="g/kg (printed % x 10)",
             **{"Data source": "Table 6 - converted", "Method used (from paper)": "Walkley & Black (1934) wet oxidation", "Notes/Doubts": nt})
    put("MBC", base, {"CTR": ct[4], "MTR": st[4]}, "MBC_", UNIT="ug C/g soil (printed mg/kg)",
        **{"Data source": "Table 6", "Method used (from paper)": "CHCl3 fumigation-extraction (Wu et al. 1990), kEC = 0.45", "Notes/Doubts": nt})
    kr = put("stock-SOC", base, {"CTR": ct[3], "MTR": st[3]}, "SOCs_",
             **{"DEPTH": "0-20 CM", "DEPTH (as reported in paper)": "0-15 cm (cumulative class 0-20 CM, rule 43)", "UNIT": "Mg C/ha", "initial": "=ROUND(13.2*1.58*15*0.1,2)",
                "Data source": "Table 6", "Method used (from paper)": "SOC stock = SOC x BD x layer depth (paper's calculation)",
                "Notes/Doubts": "'initial' DERIVED from the paper's initial OC 13.2 g/kg x BD 1.58 x 15 cm (flag: BD fell from 1.58 to 1.27-1.30, so the initial stock is on a larger soil mass). " + nt})
    put("c sequestration rate", base, {c: f"=ROUND(({B.ref('stock-SOC', 'SOCs_' + c, kr)}-{B.ref('stock-SOC', 'initial', kr)})/8,3)" for c in ("CTR", "MTR")}, "SSOC_",
        **{"DEPTH": "0-20 CM", "DEPTH (as reported in paper)": "0-15 cm", "Obs": 2, "UNIT": "Mg C/ha/yr",
           "Data source": "DERIVED", "Method used (from paper)": "(stock 0-15 cm - initial stock)/8 yr",
           "Notes/Doubts": f"ROW {row}. DERIVED (rule 48). NEGATIVE in all treatments because the initial stock uses the initial BD 1.58 (no equivalent-soil-mass correction) - compare codes within the row only (flag). " + KA_NOTE})

# Fig. 1 yields: tillage x N (pooled over residue), 2018-19 to 2020-21 (digitised from the vector figure)
kf = json.load(open(os.path.join(DIG, "kader_fig1.json")))
NRATE = [("N1", 60), ("N2", 80), ("N3", 100), ("N4", 120), ("N5", 140)]
for yi, yr in enumerate(("2018-19", "2019-20", "2020-21")):
    for ni, (nl, pct) in enumerate(NRATE):
        r_, w_, m_ = kf["rice"][yr], kf["wheat"][yr], kf["mungbean"][yr]
        B.add("YIELD", {**KA, "year of data collection/experiment": yr, "DURATION": "4-10 Y", "YEAR OF DATA (duration)": 7 + yi, "Obs": 2,
                        "RICE YIELD_CTR": r_["CT"][ni], "RICE YIELD_MTR": r_["ST"][ni], "WYIELD_CTR": w_["CT"][ni], "WYIELD_MTR": w_["ST"][ni],
                        "UNIT": "t/ha grain (rice 14 %, wheat 12 % moisture)",
                        "Fertilizer dose & other management": f"{nl} = {pct} % RFD: rice {round(75 * pct / 100)}, wheat {round(100 * pct / 100)}, mungbean {round(20 * pct / 100)} kg N/ha. " + KA["Fertilizer dose & other management"],
                        "Crop/season of sampling": f"Rice (aman) and wheat (rabi) {yr} - N rate {nl} ({pct} % RFD)",
                        "Data source": "Fig. 1 (digitised, vector PDF)",
                        "Method used (from paper)": "Three 1-m2 quadrats per plot harvested manually at maturity; grain at 14 % (rice) / 12 % (wheat) moisture",
                        "Notes/Doubts": (f"One row per N rate (rule 33). TILLAGE x N means POOLED OVER LR/HR residue (flag) -> Obs = T2. DIGITISED from the vector Fig. 1 (exact marker "
                                         "positions); rows/columns of the figure are crops x years (panel labels a-c are mislabelled) - check: 3-yr mean at 100 % RFD reproduces "
                                         f"Table 4 PFP (rice CT 62.4, ST 69.1). Mungbean seed (third crop) CT {m_['CT'][ni]}, ST {m_['ST'][ni]} t/ha. " + KA_NOTE)})
# Table 4 NUE (3-yr mean 2018-2021), tillage x N pooled over residue
AE = {"N2": ((20.2, 16.2), (20.7, 18.1)), "N3": ((20.3, 22.5), (22.0, 17.7)), "N4": ((19.3, 17.6), (27.5, 18.7)), "N5": ((11.7, 13.3), (16.7, 11.5))}
PFP = {"N1": ((90.5, 37.8), (100.5, 48.8)), "N2": ((73.0, 32.4), (80.6, 41.1)), "N3": ((62.4, 31.7), (69.1, 36.4)),
       "N4": ((54.9, 27.7), (64.0, 33.7)), "N5": ((45.5, 23.8), (52.6, 27.5))}
for nl, pct in NRATE:
    for metric, tab, meth, unit in (("PFP", PFP, "PFPN = grain yield / N applied (Dobermann 2005)", "kg grain/kg N applied (PARTIAL FACTOR PRODUCTIVITY of N)"),
                                    ("AE", AE, "Relative AEN = (GY at N rate - GY at 60 % RFD) / N applied (modified after Dobermann 2005)", "kg grain increase/kg N applied (relative AGRONOMIC EFFICIENCY vs 60 % RFD)")):
        if nl not in tab:
            continue
        (rc, wc), (rs, ws_) = tab[nl]
        B.add("NUE", {**KA, "year of data collection/experiment": "2018-19 to 2020-21 (3-yr mean)", "DURATION": "4-10 Y", "YEAR OF DATA (duration)": "7-9 (mean)",
                      "Obs": 5, "INPUT (kg N/ha)": f"rice {round(75 * pct / 100)} / wheat {pct}", "NUE_RCTR": rc, "NUE_RMTR": rs, "NUE_WCTR": wc, "NUE_WMTR": ws_,
                      "UNIT": unit, "Crop/season of sampling": f"Rice and wheat, 3-yr mean 2018-2021 - N rate {nl} ({pct} % RFD)",
                      "Fertilizer dose & other management": f"{nl} = {pct} % RFD. " + KA["Fertilizer dose & other management"],
                      "Data source": f"Table 4{'b' if metric == 'PFP' else 'a'}", "Method used (from paper)": meth,
                      "Notes/Doubts": (f"{metric} row, one row per N rate (rule 33). Tillage x N POOLED OVER RESIDUE (flag). Obs = Y3 + T2 = 5. Mungbean "
                                       f"{metric} CT/ST: " + {"PFP": {"N1": "34.6/66.9", "N2": "38.4/63.0", "N3": "37.6/58.5", "N4": "36.4/61.6", "N5": "28.1/46.5"},
                                                              "AE": {"N2": "49.8/51.3", "N3": "42.1/45.9", "N4": "38.3/56.4", "N5": "23.2/31.3"}}[metric][nl] + ". " + KA_NOTE)})
# Table 3 gross margin (tillage main effect, pooled over residue and N)
GR = {"CT": (3.03, 2.9, 2.81, 3.46, 3.63, 3.22, 3.11, 3.32, 2.89), "ST": (3.36, 3.15, 2.97, 4.11, 4.11, 4.11, 3.87, 3.93, 3.94)}
GM = {"CT": (1.48, 1.35, 1.26, 1.83, 2.00, 1.59, 1.40, 1.61, 1.18), "ST": (2.09, 1.88, 1.70, 2.78, 2.78, 2.78, 2.47, 2.53, 2.54)}
KYRS = ["2012-13", "2013-14", "2014-15", "2015-16", "2016-17", "2017-18", "2018-19", "2019-20", "2020-21"]
for j, yr in enumerate(KYRS):
    B.add("NET RETURN", {**KA, "year of data collection/experiment": yr, "DURATION": "0-3 Y" if j < 3 else "4-10 Y", "YEAR OF DATA (duration)": j + 1, "Obs": 2,
                         "NR_SYSCTR": f"={GM['CT'][j]}*1000", "NR_SYSMTR": f"={GM['ST'][j]}*1000",
                         "UNIT": "US$/ha/yr GROSS MARGIN (printed 1000 US$ x 1000; variable-cost basis)", "Crop/season of sampling": f"Rice-wheat-mungbean system {yr}",
                         "Data source": "Table 3 - converted",
                         "Method used (from paper)": "Gross margin = gross return - total variable cost (land preparation, labour at Tk 400/person-day, seed, fertiliser, irrigation, herbicide, threshing fuel); 1 US$ = 85 Tk",
                         "Notes/Doubts": (f"GROSS MARGIN, not net return (flag). TILLAGE MAIN EFFECT pooled over residue and N (flag, rule 33) -> Obs = T2. Includes MUNGBEAN income. "
                                          f"Gross return CT {GR['CT'][j]}, ST {GR['ST'][j]} (1000 US$/ha); variable cost CT 1.55/1.63/1.71, ST 1.27/1.33/1.40 (1000 US$/ha) for 2012-15/2015-18/2018-21. "
                                          "Land equivalent ratio (Table 1, ST/CT): 1.21, 1.17, 1.07, 1.20, 1.14, 1.23, 1.28, 1.21, 1.79 (2012-13 ... 2020-21). " + KA_NOTE)})

# =====================================================================================
# 23 (companion 5)  ROY et al. 2022 Geoderma
# =====================================================================================
RO_TRT = ("TREATMENTS IN PAPER (CIMMYT-ICAR-CSSRI platform, Karnal, est. kharif 2009, RCBD 3 reps): Sc1 TPR-CTW (puddled transplanted rice; wheat broadcast after 2 harrowings + "
          "2 cultivator passes; no residue) -> CT ; Sc2 TPR-ZTWMb (puddled TPR; ZT wheat and mungbean by Happy Seeder; 100 % rice + mungbean and 30 % wheat residue retained) -> pCA ; "
          "Sc3 ZTDSR-ZTWMb (ZT DSR, ZT wheat, ZT mungbean, same residue) -> CA ; Sc4 ZT maize-wheat-mungbean -> EXCLUDED (maize) ; Sc5 = Sc3 + sub-surface drip irrigation "
          "(from 2016, 25 % less N) -> NOT ENTERED (irrigation/fertigation contrast, as old-master 23) ; Sc6 = Sc4 + SDI -> EXCLUDED.")
RO = {"No.": "23 (companion 5)", "SERIAL NO": "23 (companion 5)",
      "Authors": "Roy D., Datta A., Jat H.S., Choudhary M., Sharma P.C., Singh P.K. & Jat M.L.", "Year": 2022, "Journal": "Geoderma",
      "Country": "India (Haryana)", "Site/Location": "ICAR-CSSRI research farm, Karnal (CSISA scenario trial, est. 2009)",
      "latitude": 29.706, "longitude": 76.956, "CLIMATE": "ST", "SOIL": "LOAMY", "Rep": 3, "RAIN FALL": 670, "LATT": 29.706,
      "year of data collection/experiment": 2019, "DURATION": "4-10 Y", "YEAR OF DATA (duration)": 10,
      "Treatment mapping (paper's name -> code)": "Sc1 -> CT ; Sc2 (puddled TPR + ZT wheat + ZT mungbean, residue) -> pCA ; Sc3 (ZT DSR + ZT wheat + ZT mungbean, residue) -> CA ; Sc4-Sc6 not entered",
      "Fertilizer dose & other management": ("Rice and wheat 150-60-60 kg N-P2O5-K2O/ha in the CA scenarios (Sc2-Sc4); Sc1 farmers' practice (details in Jat et al. 2019a). "
                                             "Residue: 100 % rice and mungbean + 30 % wheat (20-25 cm anchored stubble) in Sc2/Sc3; none in Sc1. Haplic Solonetz (siltic), loam."),
      "Crop/season of sampling": "Wheat season - after wheat harvest 2019 (10 years)",
      "Treatment details (from paper)": RO_TRT}
RO_NOTE = ("COMPANION of old-master 23 (same CSSRI scenario trial; Sc2 was excluded there and is now pCA, rule 68 - see 23 (companion 3/4)). THIRD CROP: ZT mungbean in Sc2/Sc3 "
           "only (rule 71). Sc5 (Sc3 + SDI) not entered (same tillage/residue as Sc3; values in Notes, as old-master 23). Supplementary: " + SUPP + ". Source file 117.pdf.")
RLAY = [("0-15 CM", "0-5 cm", 2, 5), ("0-15 CM", "5-15 cm", 2, 10), ("15-30 CM", "15-30 cm", 1, 15)]
R = {  # Sc1, Sc2, Sc3, Sc5 per layer
    "BD": [(1.50, 1.41, 1.39, 1.54), (1.66, 1.61, 1.58, 1.65), (1.72, 1.68, 1.71, 1.68)],
    "VMC": [(28, 28, 36, 31), (28, 27, 33, 29), (26, 30, 24, 25.6)],
    "PH": [(7.57, 7.13, 7.29, 7.26), (7.70, 7.05, 7.46, 7.56), (7.84, 7.68, 7.75, 7.68)],
    "EC": [(0.31, 0.35, 0.33, 0.34), (0.26, 0.32, 0.29, 0.31), (0.29, 0.32, 0.29, 0.23)],
    "SOC": [(6.30, 8.40, 9.90, 9.60), (6.80, 6.60, 7.90, 5.40), (6.30, 4.20, 3.70, 3.15)],
    "STK": [(3.80, 5.91, 7.33, 7.39), (11.34, 10.60, 12.52, 8.80), (16.26, 10.61, 12.33, 7.87)],
    "N": [(127, 133, 123, 156), (123, 127, 139, 158), (101, 111, 118, 101)],
    "P": [(14.48, 23.66, 35.10, 36.79), (13.46, 20.72, 31.30, 20.70), (5.03, 3.38, 6.06, 8.04)],
    "K": [(193, 279, 381, 375), (181, 227, 331, 288), (140, 147, 190, 240)],
    "Fe": [(27.52, 36.30, 8.09, 9.26), (26.79, 31.30, 19.75, 19.13), (6.79, 7.97, 5.05, 6.13)],
    "Zn": [(4.07, 4.86, 7.25, 4.96), (5.30, 7.27, 7.83, 7.93), (1.37, 2.60, 2.46, 3.90)],
    "Cu": [(2.29, 2.10, 1.38, 1.62), (4.09, 2.09, 1.94, 2.33), (3.97, 1.96, 2.90, 2.19)],
    "Mn": [(14.08, 9.42, 14.05, 8.60), (10.60, 22.62, 11.72, 12.20), (10.94, 11.99, 12.61, 7.70)],
    "MBC": [(136.56, 150.22, 398.46, 401.69), (146.65, 183.36, 271.59, 259.98), (64.32, 70.12, 90.08, 146.74)],
    "DHA": [(115.43, 86.16, 223.03, 238.73), (112.07, 76.58, 66.57, 107.27), (54.05, 33.68, 45.21, 46.27)],
    "ACP": [(74.08, 85.77, 65.13, 86.37), (63.37, 81.31, 56.32, 78.98), (43.26, 68.78, 75.03, 54.01)],
    "ALP": [(68.52, 80.06, 39.60, 47.62), (83.2, 41.25, 48.60, 47.44), (53.04, 64.20, 46.14, 44.42)],
    "GLU": [(81.03, 85.18, 87.35, 96.44), (46.84, 94.27, 67.19, 37.15), (23.12, 38.34, 15.22, 17.39)],
    "SQI": [(0.65, 0.75, 0.79, 0.82), (0.69, 0.74, 0.96, 0.78), (0.55, 0.84, 0.67, 0.67)],
}
SCC = {"CT": 0, "pCA": 1, "CA": 2}
RM = {
    "BD": "Core method (Blake & Hartge 1986)",
    "PH": "pH in 1:2 soil:water (Jackson 1973)",
    "EC": "EC in 1:2 soil:water (Jackson 1973)",
    "SOC": "Walkley & Black (1934) wet oxidation",
    "N": "Alkaline permanganate (Subbiah & Asija 1956)",
    "P": "Olsen et al. (1954), ascorbic acid reductant",
    "K": "Neutral 1 N NH4OAc, flame photometer (Jackson 1973)",
    "MIC": "DTPA extraction, atomic absorption spectrophotometer (Lindsay & Norvell 1978)",
    "MBC": "Chloroform fumigation-extraction (Vance et al. 1987)",
    "DHA": "Casida et al. (1964), TPF colorimetric, 24 h incubation",
    "ACP": "Tabatabai & Bremner (1969), p-nitrophenyl phosphate",
    "GLU": "Eivazi & Tabatabai (1988), p-nitrophenyl-beta-D-glucoside",
    "SQI": "Non-linear scoring (Bastida et al. 2006) of a PCA minimum data set, weighted sum; SYI as goal variable",
}
SHEETS = [("BD", "BD", "BD_", "Mg/m3", "Table 2"), ("PH", "PH", "PH_", "pH (1:2 soil:water)", "Table 3"), ("EC", "EC", "EC_", "dS/m (1:2)", "Table 3"),
          ("SOC(active C pool)", "SOC", "SOC_", "g/kg", "Table 3"), ("N", "N", "N_", "kg/ha (available N, as printed)", "Table 4"),
          ("P", "P", "P_", "kg/ha (available P, as printed)", "Table 4"), ("K", "K", "K_", "kg/ha (available K, as printed)", "Table 4"),
          ("Fe(ppm)", "Fe", "Fe_", "mg/kg (DTPA)", "Table 4"), ("Zn(ppm)", "Zn", "Zn_", "mg/kg (DTPA)", "Table 4"), ("Cu(ppm)", "Cu", "Cu_", "mg/kg (DTPA)", "Table 4"),
          ("Mn", "Mn", "Mn_", "mg/kg (DTPA)", "Table 4"), ("MBC", "MBC", "MBC_", "ug C/g dry soil", "Table 5"),
          ("ACP", "ACP", "ACP_", "ug PNP/g soil/h", "Table 5"), ("ALKP", "ALP", "ALP_", "ug PNP/g soil/h", "Table 5"), ("B-GLU", "GLU", "BGL_", "ug PNP/g soil/h", "Table 5"),
          ("SQI", "SQI", "SQI_", "unitless 0-1 (non-linear scoring, Bastida et al. 2006; layer-specific MDS)", "Table 6")]
rbd = {}
for k, (depth, rep, D, th) in enumerate(RLAY):
    base = {**RO, "DEPTH": depth, "DEPTH (as reported in paper)": rep, "Obs": D}
    obsn = f"Obs = {D}" + (" (D=2: 0-5 and 5-15 cm both in the 0-15 CM class, separate rows). " if D == 2 else ". ")
    for sheet, key, pre, unit, src in SHEETS:
        v = R[key][k]
        meth = RM.get(key, RM["MIC"] if key in ("Fe", "Zn", "Cu", "Mn") else RM["ACP"] if key == "ALP" else "")
        r = put(sheet, base, {c: v[i] for c, i in SCC.items()}, pre, UNIT=unit,
                **{"Data source": src, "Method used (from paper)": meth,
                   "Notes/Doubts": f"{obsn}Sc5 (not entered, Sc3 + SDI): {v[3]}. " + ("Initial soil values in Gathala et al. (2013), not this paper. " if key in ("BD", "SOC") else "") + RO_NOTE})
        if key == "BD":
            rbd[k] = r
    put("POROSITY", base, {c: f"=ROUND((1-{B.ref('BD', 'BD_' + c, rbd[k])}/2.65)*100,2)" for c in SCC}, "POROSITY_", UNIT="% v/v",
        **{"Data source": "DERIVED from Table 2 BD", "Method used (from paper)": "Porosity = (1 - BD/PD) x 100", "Notes/Doubts": obsn + "DERIVED (rule 73): no PD in the paper -> 2.65 (flag). " + RO_NOTE})
    vm = R["VMC"][k]
    put("GWC", base, {c: f"=ROUND({vm[i]}/{B.ref('BD', 'BD_' + c, rbd[k])},2)" for c, i in SCC.items()}, "GWC_", UNIT="% w/w (DERIVED: printed volumetric % / BD)",
        **{"Data source": "Table 2 - converted", "Method used (from paper)": "Gravimetric moisture; volumetric content = gravimetric x BD of the layer (paper), back-converted here",
           "Notes/Doubts": (obsn + f"DERIVED: the paper prints volumetric moisture content (Sc1/Sc2/Sc3 {vm[0]}/{vm[1]}/{vm[2]} % v/v, Sc5 {vm[3]}), which it computed as GWC x BD; GWC = VMC / BD "
                            "(live link). Moisture at sampling after wheat harvest. " + RO_NOTE)})
    dh = R["DHA"][k]
    put("DHA", base, {c: f"=ROUND({dh[i]}/24,2)" for c, i in SCC.items()}, "DHA_", UNIT="ug TPF/g soil/h (printed per 24 h / 24)",
        **{"Data source": "Table 5 - converted", "Method used (from paper)": RM["DHA"], "Notes/Doubts": f"{obsn}Printed ug TPF/g/24 h: {dh[0]}/{dh[1]}/{dh[2]}; Sc5 {dh[3]}. " + RO_NOTE})
# SOC stock (printed per layer) -> cumulative classes
STK = R["STK"]
for cum, ks, rep in (("0-10 CM", [0], "0-5 cm (cumulative class 0-10 CM)"), ("0-20 CM", [0, 1], "0-5 + 5-15 cm = 0-15 cm (class 0-20 CM)"), ("0-30 CM", [0, 1, 2], "0-30 cm (3 layers summed)")):
    put("stock-SOC", {**RO, "Obs": 1}, {c: "=" + "+".join(str(STK[k][i]) for k in ks) for c, i in SCC.items()}, "SOCs_",
        **{"DEPTH": cum, "DEPTH (as reported in paper)": rep, "UNIT": "Mg C/ha", "Data source": "Table 3 (layer stocks summed)",
           "Method used (from paper)": "SOC stock = SOC (g/kg) x BD x depth (paper); cumulative sums of the printed layer stocks",
           "Notes/Doubts": ("Printed layer stocks summed (live formula). The printed stocks do not equal SOC x mean BD x depth (computed per replicate - flag); printed values kept. "
                            "Sc5 layer stocks 7.39 / 8.80 / 7.87. Fig. 2 (non-CA / partial / full CA, Sc1 / Sc2 / mean of Sc3-Sc6) not entered. " + RO_NOTE)})
# Fig. 1 SPR (vector, digitised)
rs = json.load(open(os.path.join(DIG, "roy_spr.json")))
RSPR = [("0-10 CM", "0-5 cm", 0, 2), ("0-10 CM", "5-10 cm", 1, 2), ("10-20 CM", "10-15 cm", 2, 2), ("10-20 CM", "15-20 cm", 3, 2), ("20-30 CM", "20-25 cm", 4, 2),
        ("20-30 CM", "25-30 cm", 5, 2), ("30-40 CM", "30-35 cm", 6, 2), ("30-40 CM", "35-40 cm", 7, 2), ("40-50 CM", "40-45 cm", 8, 1)]
for cls, rep, i, D in RSPR:
    put("PR", {**RO, "DEPTH": cls, "DEPTH (as reported in paper)": rep, "Obs": D}, {"CT": rs["Sc1"][i], "pCA": rs["Sc2"][i], "CA": rs["Sc3"][i]}, "PR_", UNIT="MPa (cone index)",
        **{"Data source": "Fig. 1 (digitised, vector PDF)",
           "Method used (from paper)": "Manual cone penetrometer (Eijkelkamp), 1 cm2 base, 60 deg cone, every 5 cm to 45 cm",
           "Notes/Doubts": (f"Obs = {D}. DIGITISED from the vector Fig. 1 (exact marker positions; markers plotted at layer mid-depths). Checks vs text: CA lower than Sc1 by 17 % "
                            "at 15-20 cm and 33 % at 20-25 cm (text 13-21 % and 32-34 %). Sc5 not extracted. " + RO_NOTE)})
# Table 2 infiltration
put("IR", {**RO, "DEPTH": "0-15 CM", "DEPTH (as reported in paper)": "soil surface (rings inserted to 15 cm)", "Obs": 1}, {"CT": 0.44, "pCA": 0.52, "CA": 0.83}, "IR_",
    UNIT="cm/hr (steady-state)", **{"Data source": "Table 2",
    "Method used (from paper)": "Double-ring infiltrometer, falling head (Gathala et al. 2011); inner/outer rings 26/39 cm inserted to 15 cm",
    "Notes/Doubts": "Cumulative infiltration (cm/6 h as printed - implausibly large, units doubtful): Sc1 233, Sc2 257, Sc3 729, Sc5 811. Sc5 steady rate 0.67. "
                    "Sustainable yield index (no sheet): Sc1 0.59, Sc2 0.69, Sc3 0.62, Sc5 0.74. " + RO_NOTE})

# =====================================================================================
# 170  KUKAL & AGGARWAL 2003 Soil Tillage Res.  (author coding 2026-10-05: unpuddled ZT, shallow puddling MT, normal puddling CT)
# =====================================================================================
KU_TRT = ("TREATMENTS IN PAPER (PAU Ludhiana, 1994-1996, RBD, 22 x 1.8 m plots; rice puddled with a 35-HP tractor cultivator in 5-6 cm standing water, then planked): "
          "medium (2 passes) or intensive (4 passes) puddling x shallow (5-6 cm; tines set 4-5 cm) or normal (10-12 cm; full tine length, farmers' practice) depth; "
          "achieved depth medium 5.1 / 10.3 cm, intensive 6.8 / 11.8 cm. Unpuddled plots kept in the same field outside the randomised layout. Wheat after every "
          "treatment: pre-sowing irrigation, 1 disc + 2 cultivator passes + planking (conventional), drilled 22.5 cm rows.")
KU = {"No.": 170, "SERIAL NO": 170, "Authors": "Kukal S.S. & Aggarwal G.C.", "Year": 2003, "Journal": "Soil & Tillage Research",
      "Country": "India (Punjab)", "Site/Location": "Punjab Agricultural University farm, Ludhiana", "latitude": 30.933, "longitude": 75.867,
      "CLIMATE": "TEMP", "SOIL": "SANDY", "Rep": 3, "LATT": 30.933, "soc (initial)": 3.3, "sand": 71, "silt": 17, "CLAY": 12,
      "Treatment mapping (paper's name -> code)": "Normal-depth (10-12 cm) puddling -> CT ; shallow (5-6 cm) puddling -> MT ; unpuddled -> ZT (author 2026-10-05); medium and intensive passes pooled in the figures",
      "Fertilizer dose & other management": ("Rice PR 110, 30-d seedlings at 20 x 15 cm: basal 25 kg ZnSO4, 12 kg superphosphate, 35 kg urea (1/3 N) + 2 N splits at 3 and 6 WAT; "
                                             "flooded 15 d then 7.5-cm irrigations 2 d after ponded water drained. Wheat CPAN 3004 sown 11-13 Nov: 120 kg N (2 splits), 26 kg P; "
                                             "4 irrigations of 7.5 cm (IW/PAN-E 0.9). Fatehpur sandy loam, OC 3.3 g/kg, KMnO4-N 152, Olsen P 13.7, K 145 kg/ha; "
                                             "gravimetric water at -0.03 / -1.5 MPa 13.9 / 7.1 %."),
      "Treatment details (from paper)": KU_TRT}
KU_NOTE = ("AUTHOR CODING 2026-10-05: unpuddled -> ZT, shallow puddling -> MT, normal puddling -> CT. FLAG: the WHEAT phase is conventionally tilled after every treatment "
           "(contrast is the rice-phase puddling only); unpuddled plots were outside the randomised layout (flag). Shallow (MT) and normal (CT) values in the figures are pooled "
           "over medium and intensive puddling (T = 2 in Obs). Supplementary: none (2003). Source file 117_real.pdf.")
kf = json.load(open(os.path.join(DIG, "kukal_figs.json")))
T3B = {"0-5": (1.48, 1.50, 1.34, 1.31), "5-10": (1.53, 1.55, 1.42, 1.44), "10-12": (1.59, 1.61, 1.55, 1.55), "12-14": (1.62, 1.64, 1.54, 1.57),
       "14-16": (1.67, 1.69, 1.66, 1.64), "16-18": (1.63, 1.67, 1.62, 1.67), "18-20": (1.61, 1.66, 1.62, 1.67), "20-22": (1.60, 1.61, None, None), "22-24": (1.54, 1.55, None, None)}
BDK_M = "Core sampler, two sites x three replications per plot (0-5, 5-10, 10-12 ... 22-24 cm)"
for pan, red, season, yr in (("a", True, "RICE SEASON - after rice harvest 1996 (3rd year), before wheat seedbed cultivation", 1996),
                             ("b", False, "Wheat season - after cultivation for wheat seedbed preparation, 1996-97 (3rd year)", "1996-97")):
    f = kf["fig1"][pan]
    n15 = sum(1 for l in f["layers"] if l in ("0-5", "5-10", "10-12", "12-14"))
    n30 = len(f["layers"]) - n15
    for i, lay in enumerate(f["layers"]):
        cls, D = ("0-15 CM", n15) if lay in ("0-5", "5-10", "10-12", "12-14") else ("15-30 CM", n30)
        obs = 2 + D
        t3 = T3B[lay]
        t3n = (f"Table 3 normal-depth plots by intensity ({'before' if pan == 'a' else 'after'} cultivation): medium {t3[0 if pan == 'a' else 2]}, intensive "
               f"{t3[1 if pan == 'a' else 3]} Mg/m3 (not entered as rows - CT split by intensity; NB Table 3 and Fig. 1 disagree at 14-16 cm). ")
        base = {**KU, "year of data collection/experiment": yr, "DURATION": "0-3 Y", "YEAR OF DATA (duration)": 3, "DEPTH": cls, "DEPTH (as reported in paper)": f"{lay} cm",
                "Obs": obs, "Crop/season of sampling": season}
        nt = ((RED_NOTE_K if red else "") + f"Fig. 1{pan} DIGITISED (600-dpi bitmap; x-scale fitted on the unpuddled markers = Table 3 footnote values, residuals <=0.001). "
              + ("14-16 cm assigned to 15-30 CM (1 cm in each class; compaction layer reported as 14-20 cm) - flag. " if lay == "14-16" else "")
              + {"a": "22-24 cm shallow marker merged with unpuddled. " if lay == "22-24" else "", "b": "5-10 cm markers merged (blob centre). " if lay == "5-10" else ""}[pan]
              + t3n + f"Obs = T2 + D{D} = {obs}. " + KU_NOTE)
        r = put("BD", base, {"CT": f["normal"][i], "MT": f["shallow"][i], "ZT": f["unpuddled_table3"][i]}, "BD_", red=red, UNIT="Mg/m3",
                **{"Data source": f"Fig. 1{pan} (digitised) + Table 3 footnote (unpuddled)", "Method used (from paper)": BDK_M, "Notes/Doubts": nt})
        put("POROSITY", base, {c: f"=ROUND((1-{B.ref('BD', 'BD_' + c, r)}/2.65)*100,2)" for c in ("CT", "MT", "ZT")}, "POROSITY_", red=red, UNIT="% v/v",
            **{"Data source": "DERIVED from Fig. 1 BD", "Method used (from paper)": "Porosity = (1 - BD/PD) x 100",
               "Notes/Doubts": (RED_NOTE_K if red else "") + "DERIVED (rule 73): no PD in the paper -> 2.65 (flag). " + KU_NOTE})
SPRK_M = "Proving-ring cone penetrometer (30 deg cone, 1.33 cm2 base) at field-capacity wetness, 5-cm increments to 30 cm, three sites x three replications per plot"
for pan, red, season, yr in (("a", True, "RICE SEASON - at rice harvest 1996 (3rd year), before wheat seedbed cultivation", 1996),
                             ("b", False, "Wheat season - after wheat seedbed preparation, 1996-97 (3rd year)", "1996-97")):
    f = kf["fig2"][pan]
    for i, lay in enumerate(f["layers"]):
        cls = {"0-5": "0-10 CM", "5-10": "0-10 CM", "10-15": "10-20 CM", "15-20": "10-20 CM", "20-25": "20-30 CM", "25-30": "20-30 CM"}[lay]
        put("PR", {**KU, "year of data collection/experiment": yr, "DURATION": "0-3 Y", "YEAR OF DATA (duration)": 3, "DEPTH": cls, "DEPTH (as reported in paper)": f"{lay} cm",
                   "Obs": 4, "Crop/season of sampling": season}, {"CT": f["normal"][i], "MT": f["shallow"][i]}, "PR_", red=red, UNIT="MPa (cone index)",
            **{"Data source": f"Fig. 2{pan} (digitised)", "Method used (from paper)": SPRK_M,
               "Notes/Doubts": ((RED_NOTE_K if red else "") + f"Fig. 2{pan} DIGITISED (600-dpi bitmap, x-scale from the axis ticks). Unpuddled (ZT) not measured for SPR. "
                                + ("0-15 cm shallow and normal markers coincide. " if pan == "b" and i < 3 else "")
                                + ("Table 5 prints 1996 15-20 cm shallow 3.33 / normal 3.87 (figure: shallow 2.89) - inconsistency in the paper (flag). " if lay == "15-20" and pan == "a" else "")
                                + "Obs = T2 + D2 = 4. " + KU_NOTE)})
# Table 4 (BD 14-20 cm) and Table 5 (SPR 15-20 cm) at the end of each rice season - puddling-depth main effects (pooled over intensity)
for yr, (bs, bn), (ps, pn), dur in ((1994, (1.49, 1.56), (3.20, 3.19), 1), (1995, (1.53, 1.71), (3.23, 3.64), 2), (1996, (1.57, 1.74), (3.33, 3.87), 3)):
    base = {**KU, "year of data collection/experiment": yr, "DURATION": "0-3 Y", "YEAR OF DATA (duration)": dur,
            "Crop/season of sampling": f"RICE SEASON - at the end of the {yr} rice season (after rice harvest)"}
    intn = {1994: "medium 1.56 / high 1.57 Mg/m3; SPR 3.16 / 3.20 MPa", 1995: "medium 1.68 / high 1.73; SPR 3.50 / 3.77", 1996: "medium 1.71 / high 1.77; SPR 3.78 / 3.96"}[yr]
    if yr != 1996:
        put("BD", {**base, "DEPTH": "15-30 CM", "DEPTH (as reported in paper)": "14-20 cm (mean of 3 layers)", "Obs": 5}, {"CT": bn, "MT": bs}, "BD_", red=True, UNIT="Mg/m3",
            **{"Data source": "Table 4", "Method used (from paper)": BDK_M + "; mean of the 14-16, 16-18, 18-20 cm layers",
               "Notes/Doubts": (RED_NOTE_K + f"Year-wise (rule 37). Puddling-DEPTH main effect pooled over intensity (flag). Intensity main effect (pooled over depth, not entered): {intn}. "
                                "1996 values (shallow 1.57, normal 1.74) duplicate the 1996 Fig. 1a layers - not entered as a row. Obs = T2 + D3 = 5. " + KU_NOTE)})
    put("PR", {**base, "DEPTH": "10-20 CM", "DEPTH (as reported in paper)": "15-20 cm", "Obs": 2}, {"CT": pn, "MT": ps}, "PR_", red=True, UNIT="MPa (cone index)",
        **{"Data source": "Table 5", "Method used (from paper)": SPRK_M,
           "Notes/Doubts": (RED_NOTE_K + f"Year-wise. Puddling-DEPTH main effect pooled over intensity (flag). Intensity main effect: {intn}. "
                            + ("1996 shallow differs from Fig. 2a (2.89) - kept as printed (flag). " if yr == 1996 else "") + "Obs = T2 = 2. " + KU_NOTE)})


# =====================================================================================
# Study_Info, LAT_LONG, Treatment_Mapping, EXCLUDED_rows
# =====================================================================================
B.add("Study_Info", {"No.": 170, "SERIAL NO": 170, "Authors": "Kukal S.S. & Aggarwal G.C.", "Year": 2003, "Journal": "Soil & Tillage Research",
                     "Full reference": "Kukal SS & Aggarwal GC (2003) Puddling depth and intensity effects in rice-wheat system on a sandy loam soil. I. Development of subsurface compaction. Soil Tillage Res 72:1-8",
                     "DOI / link": "https://doi.org/10.1016/S0167-1987(03)00093-X", "Country": "India (Punjab)", "Site/Location": "Punjab Agricultural University, Ludhiana",
                     "latitude": 30.933, "longitude": 75.867, "latitude (as reported)": "30 deg 56' N", "longitude (as reported)": "75 deg 52' E", "Coordinates source": "Paper",
                     "CLIMATE": "TEMP", "Experiment established (year)": 1994, "year of data collection/experiment": "1994-1996 (rice), 1994-95 to 1996-97 (wheat)",
                     "Years of data reported": 3, "DURATION": "0-3 Y", "SOIL": "SANDY", "Texture as reported": "Fatehpur sandy loam (71 % sand, 17 % silt, 12 % clay), Typic Ustochrept",
                     "sand": 71, "silt": 17, "CLAY": 12, "soc (initial)": 3.3, "Crop rotation": "Rice-wheat", "Wheat variety": "CPAN 3004", "Rice variety": "PR 110",
                     "N dose (kg/ha)": "Wheat 120; rice urea 105 kg (1/3 basal)", "P dose (kg/ha)": "Wheat 26", "Treatments in paper": KU_TRT,
                     "Parameters extracted": ("BD per layer 0-5 ... 22-24 cm at rice harvest (red) and after wheat seedbed preparation 1996 (Fig. 1, digitised; ZT from Table 3), "
                                              "porosity (derived), SPR per 5-cm layer to 30 cm at both stages (Fig. 2, digitised), BD 14-20 cm 1994-95 and SPR 15-20 cm 1994-96 at rice harvest (Tables 4-5, red)"),
                     "Supplementary data?": "None (2003 article)",
                     "Notes/Doubts": ("INCLUDED (author 2026-10-05): normal puddling CT, shallow puddling MT, unpuddled ZT. NOT ON A SHEET: puddling depth achieved (Table 2) and "
                                      "penetrometer calibration (Table 1); Table 3 BD of normal-depth plots by intensity (in the BD rows' Notes). " + KU_NOTE)})
B.add("Study_Info", {"No.": "15 (companion 2)", "SERIAL NO": "15 (companion 2)", "Authors": GA["Authors"], "Year": 2011, "Journal": GA["Journal"],
                     "Full reference": "Gathala MK, Ladha JK, Saharawat YS, Kumar V, Kumar V & Sharma PK (2011) Effect of tillage and crop establishment methods on physical properties of a medium-textured soil under a seven-year rice-wheat rotation. Soil Sci Soc Am J 75:1851-1862",
                     "DOI / link": "https://doi.org/10.2136/sssaj2010.0362", "Country": GA["Country"], "Site/Location": GA["Site/Location"], "latitude": 29.017, "longitude": 77.75,
                     "latitude (as reported)": "29 deg 01' N (old-master 15)", "longitude (as reported)": "77 deg 45' E", "Coordinates source": "Paper / old-master 15", "CLIMATE": "ST",
                     "Experiment established (year)": 2002, "year of data collection/experiment": "2002-03 to 2008-09", "Years of data reported": "WSA 6 yr, IR 6 yr (year-wise); BD and SPR 4-yr mean; SOC after 7 yr",
                     "DURATION": "0-3 Y to 4-10 Y (per row)", "SOIL": "LOAMY", "Texture as reported": "Sandy loam (0-45 cm); 0-15 cm clay 19, silt 26, sand 55 %", "sand": 55, "silt": 26, "CLAY": 19,
                     "ph (initial)": 8.1, "MIN TEMP": 2, "MAX TEMP": 43, "RAIN FALL": 800, "Crop rotation": "Rice-wheat", "Wheat variety": "PBW 343", "Rice variety": "NDR 359",
                     "N dose (kg/ha)": "150 (rice, +22.5 in DSR) / 150 (wheat)", "P dose (kg/ha)": "26 / 26", "K dose (kg/ha)": "50 / 50",
                     "Residue type & rate (t/ha)": "~1 Mg/ha anchored stubble after every crop in all plots (not a treatment)",
                     "Irrigation / water management": "TPR flooded 2 wk then at hairline cracks; T2 AWD 20-70 DAT; DSR every 3-4 d for 4 wk", "Treatments in paper": GA_TRT,
                     "Parameters extracted": ("BD (4 layers), porosity (derived), SPR (every 5 cm to 45 cm, digitised), WSA >0.25 mm (6 yr), water-stable aggregate size classes (7 classes, digitised) "
                                              "and MWD (derived), steady infiltration (6 yr), SOC 0-15 cm, SOC stock (derived), LLWR 0-5 / 6-10 cm (Fig. 5), weekly soil temperature at 5 cm "
                                              "(Fig. 3, 20 weeks x 0700 / 1500 h), 7-yr mean yields (duplicate flag)"),
                     "Supplementary data?": SUPP,
                     "Notes/Doubts": ("INCLUDED: T1 CT, T2 pZT, MT T3 (row a) / T4 (row b), ZT T5 (row a) / T6 (row b). NOT ON A SHEET: initial water retention -30 / -1500 kPa 25.5 / 9.9 % v/v, "
                                      "AWC 15.6 % v/v (initial only); Fig. 4 (LLWR vs wheat yield regression). " + GA_NOTE)})
B.add("Study_Info", {"No.": "40 (companion)", "SERIAL NO": "40 (companion)", "Authors": KA["Authors"], "Year": 2022, "Journal": "Field Crops Research",
                     "Full reference": "Kader MA et al. (2022) Long-term conservation agriculture increases nitrogen use efficiency by crops, land equivalent ratio and soil carbon stock in a subtropical rice-based cropping system. Field Crops Res 287:108636",
                     "DOI / link": "https://doi.org/10.1016/j.fcr.2022.108636", "Country": "Bangladesh", "Site/Location": KA["Site/Location"], "latitude": 24.724, "longitude": 90.437,
                     "latitude (as reported)": "24 deg 43.407' N", "longitude (as reported)": "90 deg 26.22' E", "Coordinates source": "Paper", "CLIMATE": "ST",
                     "Experiment established (year)": 2012, "year of data collection/experiment": "2012-13 to 2020-21; soil after 23rd crop (wheat 2019-20)",
                     "Years of data reported": "Economics 9 yr; yields/NUE 2018-2021; soil 1 sampling", "DURATION": "0-3 Y to 4-10 Y (per row)", "SOIL": "LOAMY",
                     "Texture as reported": "Silt loam (110 sand : 760 silt : 130 clay g/kg), Aeric Haplaquept", "sand": 11, "silt": 76, "CLAY": 13, "ph (initial)": 6.92, "soc (initial)": 13.2,
                     "Bdi": 1.58, "RAIN FALL": 2400, "Crop rotation": "Rice (aman) - wheat - mungbean", "Wheat variety": "BARI Gom 25", "Rice variety": "BRRI dhan49",
                     "N dose (kg/ha)": "RFD rice 75, wheat 100, mungbean 20 (60-140 % tiers)", "P dose (kg/ha)": "rice 10, wheat 20, mungbean 20", "K dose (kg/ha)": "rice 30, wheat 60, mungbean 30",
                     "Residue type & rate (t/ha)": "Anchored stubble 15 % (LR) or 30 % (HR) of plant height; mungbean 0 / 100 %", "Irrigation / water management": "Rice rainfed; wheat 2 irrigations",
                     "Treatments in paper": KA_TRT,
                     "Parameters extracted": "BD, porosity (derived), total N, SOC, MBC, SOC stock, C sequestration (derived) - 0-15 cm rows a/b; rice & wheat yields 2018-21 x 5 N rates (digitised); NUE (PFP, AE) x N; gross margin 9 yr",
                     "Supplementary data?": "Supplementary Tables S1-S4 (year-wise main-effect yields, interactions) exist but could not be reached - " + SUPP,
                     "Notes/Doubts": "INCLUDED: CT -> CTR, ST -> MTR (both residue levels retained; rows a LR / b HR). Optimum N (Table 5) and LER (Table 1) not on a sheet. " + KA_NOTE})
B.add("Study_Info", {"No.": "23 (companion 5)", "SERIAL NO": "23 (companion 5)", "Authors": RO["Authors"], "Year": 2022, "Journal": "Geoderma",
                     "Full reference": "Roy D, Datta A, Jat HS, Choudhary M, Sharma PC, Singh PK & Jat ML (2022) Impact of long term conservation agriculture on soil quality under cereal based systems of North West India. Geoderma 405:115391",
                     "DOI / link": "https://doi.org/10.1016/j.geoderma.2021.115391", "Country": "India (Haryana)", "Site/Location": RO["Site/Location"], "latitude": 29.706, "longitude": 76.956,
                     "latitude (as reported)": "29 deg 42' 20.7\" N", "longitude (as reported)": "76 deg 57' 19.79\" E", "Coordinates source": "Paper", "CLIMATE": "ST",
                     "Experiment established (year)": 2009, "year of data collection/experiment": 2019, "Years of data reported": "1 sampling (after wheat 2019)", "DURATION": "4-10 Y",
                     "SOIL": "LOAMY", "Texture as reported": "Loam, Haplic Solonetz (siltic)", "RAIN FALL": 670, "Crop rotation": "Rice-wheat (Sc1); rice-wheat-mungbean (Sc2, Sc3)",
                     "N dose (kg/ha)": "150 (rice and wheat, CA scenarios)", "P dose (kg/ha)": "60 P2O5", "K dose (kg/ha)": "60 K2O",
                     "Residue type & rate (t/ha)": "100 % rice + mungbean, 30 % wheat (Sc2, Sc3)", "Treatments in paper": RO_TRT,
                     "Parameters extracted": "0-5, 5-15, 15-30 cm: BD, porosity (derived), GWC (derived), pH, EC, SOC, SOC stock, available N/P/K, DTPA Fe/Zn/Cu/Mn, MBC, DHA, ACP, ALKP, B-GLU, SQI; SPR x 9 layers (digitised); steady infiltration",
                     "Supplementary data?": SUPP, "Notes/Doubts": "INCLUDED: Sc1 CT, Sc2 pCA, Sc3 CA; wheat-season sampling (not red). " + RO_NOTE})
for no, au, yr, ctry, site, la, lo, lar, lor, src, cl, note in [
        (170, "Kukal S.S. & Aggarwal G.C.", 2003, "India (Punjab)", "PAU, Ludhiana", 30.933, 75.867, "30 deg 56' N", "75 deg 52' E", "Paper", "TEMP", None),
        ("15 (companion 2)", "Gathala M.K. et al.", 2011, "India (Uttar Pradesh)", "SVBPUAT, Modipuram", 29.017, 77.75, "29 deg 01' N", "77 deg 45' E", "Paper / old-master 15", "ST", None),
        ("40 (companion)", "Kader M.A. et al.", 2022, "Bangladesh", "BAU farm, Mymensingh", 24.724, 90.437, "24 deg 43.407' N", "90 deg 26.22' E", "Paper", "ST", "Same as old-master 40"),
        ("23 (companion 5)", "Roy D. et al.", 2022, "India (Haryana)", "ICAR-CSSRI, Karnal", 29.706, 76.956, "29 deg 42' 20.7\" N", "76 deg 57' 19.79\" E", "Paper", "ST", None)]:
    B.add("LAT_LONG", {"No.": no, "SERIAL NO": no, "Authors": au, "Year": yr, "Country": ctry, "Site/Location": site, "latitude (as reported)": lar,
                       "longitude (as reported)": lor, "latitude": la, "longitude": lo, "Coordinates source": src, "CLIMATE": cl, "Notes": note})
TM = [
    (170, "Kukal S.S. & Aggarwal G.C.", 2003, "Medium / intensive puddling, normal depth (10-12 cm)", "2 or 4 cultivator passes in flooded soil, tines fully in; CT wheat (disc + 2 cultivator)", "Puddled (normal depth)", "Conventional", "No", None, "CT", "Author 2026-10-05: normal puddling = CT", "High", "INCLUDED (author)"),
    (170, "Kukal S.S. & Aggarwal G.C.", 2003, "Medium / intensive puddling, shallow depth (5-6 cm)", "Tines set 4-5 cm deep; CT wheat", "Shallow (reduced) puddling", "Conventional", "No", None, "MT", "Author 2026-10-05: shallow puddling = MT (wheat CT in all - flag)", "Medium", "INCLUDED (author) - FLAG"),
    (170, "Kukal S.S. & Aggarwal G.C.", 2003, "Unpuddled", "Unpuddled plots in the same field, outside the randomised layout (BD only)", "Unpuddled (transplanted)", "Conventional", "No", None, "ZT", "Author 2026-10-05: unpuddled = ZT (outside layout, wheat CT - flag)", "Medium", "INCLUDED (author) - FLAG"),
    ("15 (companion 2)", "Gathala M.K. et al.", 2011, "T1 CT-TPR/CT-DSW", "Puddled TPR; conventional tillage + drill-seeded wheat", "Puddled TPR", "Conventional", "Stubble ~1 Mg/ha (incorporated)", 1, "CT", "As old-master 15", "High", "INCLUDED"),
    ("15 (companion 2)", "Gathala M.K. et al.", 2011, "T2 CTAWD-TPR/ZT-DSW", "Puddled TPR with AWD; ZT drill-seeded wheat", "Puddled TPR (AWD)", "Zero tillage", "Stubble ~1 Mg/ha (not a treatment)", 1, "pZT", "Author 2026-10-05; AWD flag", "High", "INCLUDED (author)"),
    ("15 (companion 2)", "Gathala M.K. et al.", 2011, "T5 ZT-DSR/ZT-DSW", "ZT direct drill-seeded rice; ZT wheat", "Zero tillage DSR", "Zero tillage", "Stubble ~1 Mg/ha", 1, "ZT", "Row a (author 2026-10-05)", "High", "INCLUDED (author)"),
    ("15 (companion 2)", "Gathala M.K. et al.", 2011, "T6 ZT-TPR/ZT-DSW", "Zero-till plots flooded 1 d before transplanting (unpuddled); ZT wheat", "Zero till, unpuddled TPR", "Zero tillage", "Stubble ~1 Mg/ha", 1, "ZT", "Row b (author 2026-10-05)", "High", "INCLUDED (author)"),
    ("15 (companion 2)", "Gathala M.K. et al.", 2011, "T3 Bed-DSR/Bed-DSW", "Permanent raised beds, DSR; beds reshaped at wheat sowing", "Permanent beds (DSR)", "Beds reshaped (1 pass)", "Stubble ~1 Mg/ha", 1, "MT", "Row a; author 2026-10-05: beds = MT", "High", "INCLUDED (author)"),
    ("15 (companion 2)", "Gathala M.K. et al.", 2011, "T4 Bed-TPR/Bed-DSW", "Permanent raised beds, transplanted rice; beds reshaped at wheat sowing", "Permanent beds (TPR)", "Beds reshaped (1 pass)", "Stubble ~1 Mg/ha", 1, "MT", "Row b; author 2026-10-05: beds = MT", "High", "INCLUDED (author)"),
    ("40 (companion)", "Kader M.A. et al.", 2022, "CT-LR / CT-HR", "Puddled (4 rotary passes) TPR; 4 cross rotary passes for wheat and mungbean; 15 % / 30 % residue", "Puddled (rotary x4)", "Conventional (rotary x4)", "Yes (anchored)", "15 / 30 % height", "CTR", "Rotary rule (>= 2 passes) + residue; rows a/b (as old-master 40)", "High", "INCLUDED"),
    ("40 (companion)", "Kader M.A. et al.", 2022, "ST-LR / ST-HR", "VMP strip tillage (4-6 cm wide, 5-6 cm deep), unpuddled TPR in strips; 15 % / 30 % residue", "Strip tillage, unpuddled", "Strip tillage", "Yes (anchored)", "15 / 30 % height", "MTR", "Strip tillage + residue = MTR (rows a/b)", "High", "INCLUDED"),
    ("23 (companion 5)", "Roy D. et al.", 2022, "Sc1 TPR-CTW", "Puddled TPR; broadcast CT wheat (2 harrow + 2 cultivator); no residue", "Puddled TPR", "Conventional", "No", None, "CT", "Conventional both phases", "High", "INCLUDED"),
    ("23 (companion 5)", "Roy D. et al.", 2022, "Sc2 TPR-ZTWMb", "Puddled TPR; ZT wheat and mungbean (Happy Seeder); residue retained", "Puddled TPR", "Zero tillage", "Yes", None, "pCA", "Puddled rice + ZT wheat + residue (rule 68); mungbean flag", "High", "INCLUDED"),
    ("23 (companion 5)", "Roy D. et al.", 2022, "Sc3 ZTDSR-ZTWMb", "ZT DSR, ZT wheat, ZT mungbean; residue retained", "Zero tillage DSR", "Zero tillage", "Yes", None, "CA", "ZT both phases + residue; mungbean flag", "High", "INCLUDED"),
    ("23 (companion 5)", "Roy D. et al.", 2022, "Sc5 ZTDSR-ZTWMb + SDI", "As Sc3 with sub-surface drip irrigation (from 2016), 25 % less N", "Zero tillage DSR", "Zero tillage", "Yes", None, "EXCLUDED", "Irrigation/fertigation contrast with the same tillage and residue as Sc3 (old-master 23); values in Notes", "High", "EXCLUDED"),
    ("23 (companion 5)", "Roy D. et al.", 2022, "Sc4 / Sc6", "ZT maize-wheat-mungbean (+ SDI)", "n/a - maize", "Zero tillage", "Yes", None, "EXCLUDED", "Maize-wheat system", "High", "EXCLUDED"),
]
th = ["SERIAL NO", "Authors", "Year", "Paper's treatment label (verbatim)", "Full description from paper", "Rice-phase tillage", "Wheat-phase tillage",
      "Residue retained?", "Residue rate (t/ha)", "ASSIGNED CODE", "Rationale", "Confidence", "Status"]
for row in TM:
    d = dict(zip(th, row))
    d["No."] = row[0]
    B.add("Treatment_Mapping", d)
B.add("EXCLUDED_rows", {"Sheet": "(treatments)", "SERIAL NO": "23 (companion 5)", "Authors": "Roy D. et al.", "Year": 2022,
                        "Reason for exclusion": "Sc5 (Sc3 + SDI) not entered (values in each row's Notes); Sc4 and Sc6 maize-wheat-mungbean excluded.",
                        "Full row (header = value)": "Sc4 / Sc6 0-5 cm: BD 1.48 / 1.54, SOC 9.45 / 8.85 g/kg, MBC 384.60 / 378.32 ug/g, SQI 0.89 / 0.91; SYI 0.67 / 0.78."})
B.add("EXCLUDED_rows", {"Sheet": "(N tiers)", "SERIAL NO": "40 (companion)", "Authors": "Kader M.A. et al.", "Year": 2022,
                        "Reason for exclusion": "None excluded: all five N rates entered as separate rows for yield and NUE (rule 33); soil Table 6 tillage x N cells kept in Notes (tillage x residue cells entered).",
                        "Full row (header = value)": "-"})
B.save(OUT)
print("saved", OUT)
