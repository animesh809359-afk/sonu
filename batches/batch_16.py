"""Batch 16 (2026-10-05): uploaded files 127_real.pdf, 126.pdf, 127.docx, 128.pdf, 128_real.pdf.

  179                Ahmad N. et al. (supplementary material only, 127.docx)          - Sukheki farm, Hafizabad (Punjab, Pakistan): CT0 CT, CTR CTR, NT0 ZT, NTR CA;
                                                                                        SOC (Table S3), aggregate C mineralisation (Figs S4-S5), C input (Figs S8-S9)
  180                Mann R.A., Ramzan M. & Munir A. 2008 (Int. J. Agric. Biol. 10:249-254) - Punjab (Pakistan) farmers' fields: ZT vs CT wheat (rice tillage not
                                                                                        stated, rule 23); yields, soil chemistry, microbial counts, irrigation WUE
  24 (companion 2)   Choudhary M. et al. 2018 (Appl. Soil Ecol. 126:189-198)           - RE-SUBMISSION of old-master 24 (rule 6): row a = old-master set (T1 CT, T4 CTR,
                                                                                        T5 ZT, T9 CA); rows b-d = treatments the old entry excluded (T2/T6 RDF, T8, T3/T7/T10
                                                                                        mungbean) under rules 20 / 33 / 71 (flagged)
  159 (companion)    Dutta A. et al. 2023 (IJERPH 20:810)                              - IIFSR Modipuram tillage x residue trial (est. 1998) = old-master 159 (Gangwar 2006):
                                                                                        CT-NR / CT-RB CT, CT-R CTR, ZT-NR / ZT-RB pZT, ZT-R pCA, ST-NR / ST-RB pMT, ST-R pMTR
  173 (companion)    Biswakarma N. et al. 2023 (127_real.pdf) = study 173 (121_now.pdf) - DUPLICATE RE-SUBMISSION (rule 6): every 173 row copied (live formulas re-pointed)

Obs on every row = Y + T + D (rule 101). Every row records the paper's method in 'Method used (from paper)'.
Usage: python batches/batch_16.py <in.xlsx> <out.xlsx>
"""
import json
import os
import re
import sys
from copy import copy

sys.path.insert(0, os.path.dirname(__file__))
from lib import Book  # noqa: E402

SRC, OUT = sys.argv[1], sys.argv[2]
DIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "digitised")
B = Book(SRC)
SUPP = "None found - web search 2026-10-05 (publisher pages not reachable from this environment)"
dj = lambda f: json.load(open(os.path.join(DIG, f)))
NODEPTH = ("DEPTH", "DEPTH (as reported in paper)")


def obs(Y, T=1, D=1):
    o = sum(f for f in (Y, T, D) if f > 1) or 1
    return o, f" [OBS (rule 101): Y={Y} + T={T} + D={D} -> {o}; factors of 1 add nothing.]"


def put(sheet, base, vals, prefix, note, Y=1, T=1, D=1, red=False, **extra):
    h = B.headers(sheet)
    d = {k: v for k, v in base.items() if k in h or k not in NODEPTH}
    for code, v in vals.items():
        if v is not None:
            d[prefix + code] = v
    d.update(extra)
    o, why = obs(Y, T, D)
    d["Obs"] = o
    d["Notes/Doubts"] = note + why
    return B.add(sheet, d, red=red)


# =====================================================================================
# 179  AHMAD N. et al. - supplementary material (127.docx)
# =====================================================================================
A_TRT = ("TREATMENTS (supplement Table S1 / figure captions; main paper NOT supplied): CT0 = puddled transplanted rice (1 disc harrowing + 3 cultivations + 2 plankings, "
         "puddling, manual transplanting) + conventional wheat (1 disc harrowing + 2 cultivations + 2 plankings, then drilled with the zero-till drill), residue removed; "
         "CTR = CT0 with residue retention; NT0 = no-till direct-seeded rice (multi-crop inclined-plate drill) + zero-till wheat (Happy Seeder), residue removed; NTR = NT0 "
         "with residue retention. Rice cv. Super Kainat 1121 (DSR 30 kg/ha; nursery 40 g/m2 for TPR), sown 25 June, harvested 10 Nov; wheat Akbar-2019 125 kg/ha, sown "
         "22 Nov, harvested 26 Apr. Fertiliser rice 140-85-62-25 kg N-P-K-Zn/ha, wheat 115-75-62.5 kg N-P-K/ha. Irrigation: 16 (NT/DSR) vs 20 (CT/TPR) in rice, 4 in wheat.")
A_MAP = "CT0 -> CT ; CTR -> CTR ; NT0 -> ZT ; NTR -> CA (rice and wheat tillage matched in every treatment)"
A = {"No.": 179, "SERIAL NO": 179, "Authors": "Ahmad N., Virk A.L., Hafeez M.B., Kan Z.-R., Shi Z., Wang R., Iqbal H.M.W., Rehmani M.I.A., Wang X., Lal R. & Li J.",
     "Year": None, "Journal": "Supplementary material only (main paper not supplied)", "Country": "Pakistan",
     "Site/Location": "Sukheki Agricultural Farm, Hafizabad, Punjab", "latitude": 31.86, "longitude": 73.51, "CLIMATE": "TEMP", "Rep": 3, "LATT": 31.86,
     "Treatment mapping (paper's name -> code)": A_MAP,
     "Fertilizer dose & other management": "Rice 140-85-62-25 kg N-P-K-Zn/ha; wheat 115-75-62.5 kg N-P-K/ha; 16 (DSR) / 20 (TPR) rice irrigations, 4 wheat irrigations.",
     "Treatment details (from paper)": A_TRT}
A_NOTE = ("SUPPLEMENT ONLY (127.docx: Fig. S1 map, Figs S2-S9, Tables S1-S3) - the main paper (Ahmad et al., 'Soil carbon mineralization and aggregate distribution in "
          "various tillage practices of rice-wheat cropping system: A field and laboratory study') was NOT uploaded: year, journal, establishment year, duration, soil "
          "texture, BD and methods are unknown - please supply it. Coordinates approximate (Sukheki, Hafizabad; map in Fig. S1). Wheat-season rows entered; rice-season "
          "values of the same parameters kept in the Notes (rule 35). Source file 127.docx.")
SOC3 = {"Wheat 2020": [(3.23, 3.92, 3.95, 4.74), (2.84, 3.62, 3.04, 3.22), (1.61, 2.13, 1.83, 2.00)],
        "Wheat 2021": [(3.32, 4.04, 4.12, 4.94), (2.99, 3.70, 3.11, 3.37), (1.77, 2.26, 2.05, 2.15)],
        "Rice 2020": [(2.99, 3.62, 3.54, 4.27), (2.61, 3.41, 3.03, 3.19), (1.11, 1.26, 1.41, 1.54)],
        "Rice 2021": [(3.28, 3.91, 3.81, 4.51), (2.96, 3.56, 3.16, 3.35), (1.60, 1.79, 1.92, 2.07)]}
SOCSE = {"Wheat 2020": (0.24, 0.27, 0.25), "Wheat 2021": (0.22, 0.33, 0.28), "Rice 2020": (0.26, 0.30, 0.27), "Rice 2021": (0.25, 0.35, 0.28)}
AC = ("CT", "CTR", "ZT", "CA")   # CT0, CTR, NT0, NTR
DEP = [("0-15 CM", "0-15 cm"), ("15-30 CM", "15-30 cm"), ("30-45 CM", "30-45 cm")]
for yi, sea in enumerate(("Wheat 2020", "Wheat 2021")):
    rsea = sea.replace("Wheat", "Rice")
    for di, (dc, dr) in enumerate(DEP):
        put("SOC(active C pool)", {**A, "year of data collection/experiment": sea + " (as labelled; presumably the wheat after rice of that year)", "DEPTH": dc,
                                   "DEPTH (as reported in paper)": dr, "Crop/season of sampling": f"{sea} season (wheat harvest)"},
            dict(zip(AC, SOC3[sea][di])), "SOC_",
            f"Table S3 (S.E. of means {SOCSE[sea][di]}; letters in Table S3). {rsea} values CT0 / CTR / NT0 / NTR: {' / '.join(map(str, SOC3[rsea][di]))} g/kg (rule 35, not "
            "entered). " + A_NOTE, Y=2, UNIT="g/kg (SOC concentration, g C/kg; method in the main paper - not supplied)",
            **{"Data source": "Supplementary Table S3", "Method used (from paper)": "Not stated in the supplement (main paper not supplied); SOC concentration g C/kg"})
am = dj("ahmad_min.json")
for yi, (fig, sea) in enumerate((("S4 wheat 2020", "Wheat 2020"), ("S5 wheat 2021", "Wheat 2021"))):
    rfig = fig.replace("S4 wheat", "S2 rice").replace("S5 wheat", "S3 rice")
    for pn, frac, dc, dr in (("a >2mm 0-15", ">2 mm", "0-15 CM", "0-15 cm"), ("b <2mm 0-15", "<2 mm", "0-15 CM", "0-15 cm"),
                             ("c >2mm 15-30", ">2 mm", "15-30 CM", "15-30 cm"), ("d <2mm 15-30", "<2 mm", "15-30 CM", "15-30 cm")):
        v = am[fig]["values"][pn]
        d60 = {t: v["60"][t][0] for t in ("CT0", "CTR", "NT0", "NTR")}
        series = "; ".join(f"{t}: " + ", ".join(f"d{d}={v[d][t][0]:.0f}" if v[d][t] else f"d{d}=n.r." for d in ("15", "30", "45", "60"))
                           for t in ("CT0", "CTR", "NT0", "NTR"))
        rv = am[rfig]["values"][pn]["60"]
        rice60 = " / ".join(f"{rv[t][0]:.0f}" if rv[t] else "n.r." for t in ("CT0", "CTR", "NT0", "NTR"))
        put("RESP", {**A, "year of data collection/experiment": sea, "DEPTH": dc, "DEPTH (as reported in paper)": dr,
                     "Crop/season of sampling": f"{sea} season - {frac} AGGREGATES, 60-day laboratory incubation"},
            {c: f"=ROUND({d60[t]:.0f}/60,2)" for c, t in zip(AC, ("CT0", "CTR", "NT0", "NTR"))}, "RESP_",
            f"AGGREGATE FRACTION {frac} (not bulk soil - flag; rule 114). Fig. {fig.split()[0]} DIGITISED (raster; markers located by template matching with the "
            "figure's own legend symbols, panel frame = 0-70 d x 0-700 mg CO2/kg): cumulative CO2 at day 60 / 60 d = mean daily rate. Cumulative series (mg CO2/kg; "
            f"n.r. = marker not resolved): {series}. Days 3-7 not digitised (overlapping markers). {rfig.split()[1].title()} {rfig.split()[2]} day-60 CT0 / CTR / NT0 / "
            f"NTR: {rice60} mg CO2/kg (Fig. {rfig.split()[0]}; rule 35, not entered). C mineralizability (Table S2, g CO2/g SOC) in the Notes of the SOC rows / "
            "Study_Info. " + A_NOTE, Y=2, UNIT="mg CO2/kg aggregate soil/day (DERIVED mean over a 60-day incubation = cumulative / 60)",
            **{"Data source": f"Supplementary Fig. {fig.split()[0]} (digitised) - DERIVED",
               "Method used (from paper)": "Laboratory incubation of >2 mm and <2 mm aggregates for 60 days (CO2 trapped; method details in the main paper - not supplied)"})
ac_ = dj("ahmad_cinput.json")
for fig, sname in (("S8 rice season", "Rice"), ("S9 wheat season", "Wheat")):
    for yr in ("2020", "2021"):
        lay = {d: ac_[fig][f"{d} {yr}"] for d in ("0-15 cm", "15-30 cm", "30-45 cm")}
        det = "; ".join(f"{d}: " + ", ".join(f"{t} {lay[d][t]['total']:.2f}" for t in ("CT0", "CTR", "NT0", "NTR")) for d in lay)
        put("C input", {**A, "year of data collection/experiment": f"{sname} {yr}", "Crop/season of sampling": f"{sname} season {yr} - C input to 0-45 cm"},
            {c: "=ROUND(" + "+".join(f"{lay[d][t]['total']:.3f}" for d in lay) + ",2)" for c, t in zip(AC, ("CT0", "CTR", "NT0", "NTR"))}, "CIN_",
            f"Fig. {fig.split()[0]} DIGITISED (raster stacked bars: straw C + root C + rhizodeposition C; panel frame = 0-8 Mg/ha at 0-15 cm, 0-1.0 at 15-30 / 30-45 cm). "
            f"Total over the three layers (sheet has no depth column; rule 120). Layer totals (Mg C/ha): {det}. Straw C only in CTR / NTR (residue treatments). "
            f"{sname}-season crop input - a separate season row, not a soil sampling (rule 120). " + A_NOTE, Y=2,
            UNIT="Mg C/ha per season (straw + root + rhizodeposition C, 0-45 cm)",
            **{"Data source": f"Supplementary Fig. {fig.split()[0]} (digitised) - summed",
               "Method used (from paper)": "C input = straw C + root C + rhizodeposition C by layer (allocation coefficients in the main paper - not supplied)"})

# =====================================================================================
# 180  MANN R.A., RAMZAN M. & MUNIR A. 2008 Int. J. Agric. Biol. 10:249-254
# =====================================================================================
U_TRT = ("TREATMENTS IN PAPER (farmers' fields, irrigated rice-wheat Punjab, July 1999-2002; 5 farms, one zero-till and one conventional field per farm): zero tillage = "
         "wheat drilled directly without tillage (zero-till drill) into combine-harvested rice stubble ('rice straw or stubbles left over in field by the combine served "
         "as mulch'); conventional = broadcast after rototiller (1 pass) + cultivator (4 passes) + planking (2 passes) (Table IX: 5 ploughings, 3 diskings, 3 plankings). "
         "Experiment 2 (3 farms, 2001-02): zero tillage (flat), beds with two rows, beds with three rows, farmers' practice (conventional). Rice phase: Basmati, "
         "establishment not described for the trial (introduction: transplanted into puddled soil).")
U_MAP = "Zero tillage -> ZT ; Conventional (rototiller + 4 cultivator + 2 planking) -> CT (rule 23: rice tillage not stated; no deliberate residue treatment)"
U = {"No.": 180, "SERIAL NO": 180, "Authors": "Mann R.A., Ramzan M. & Munir A.", "Year": 2008, "Journal": "International Journal of Agriculture and Biology",
     "Country": "Pakistan", "Site/Location": "Farmers' fields, irrigated rice-wheat area, Punjab (5 farms)", "latitude": 31.7, "longitude": 74.0, "CLIMATE": "TEMP",
     "SOIL": "LOAMY", "Rep": 5, "LATT": 31.7, "DURATION": "0-3 Y", "Treatment mapping (paper's name -> code)": U_MAP,
     "Fertilizer dose & other management": "Not stated. Seed 87.5 (ZT) vs 125 kg/ha (CT); irrigation 35 vs 43 hectare-inches; herbicide after first irrigation.",
     "Treatment details (from paper)": U_TRT}
U_NOTE = ("ON-FARM PAIRED FIELDS (rule 117): five farms (Rizwan, Imran, Shahbaz, Asghar, Bashir) each with one ZT and one CT field = 5 replicates; farm values in Notes. "
          "Rice tillage not stated for the trial (rule 23 -> classified on the wheat phase). ZT fields kept the combine-harvested rice stubble as mulch (no deliberate "
          "residue treatment) - coded ZT, not CA (rule 104; ask: CA / CTR under rule 18?). Coordinates APPROXIMATE (Punjab rice tract; farms not located). Soil 'mixed "
          "calcareous silty alluvium, moderately fine textured', Typic Camborthids. Supplementary: none referenced. Source file 126.pdf.")
UY = {"ZT": {"Rizwan": (4.92, 4.80, 4.32), "Shahbaz": (4.87, 4.52, 4.42), "Imran": (4.47, 4.12, 3.82), "Asghar": (4.72, 3.95, 4.10), "Bashir": (5.07, 4.30, 4.02)},
      "CT": {"Rizwan": (4.72, 4.62, 4.15), "Shahbaz": (4.50, 4.07, 3.87), "Imran": (4.15, 3.67, 4.10), "Asghar": (4.25, 3.95, 4.22), "Bashir": (4.65, 4.15, 3.97)}}
UTXT = {"ZT": (4.82, 4.35, 4.15), "CT": (4.45, 4.02, 4.07)}
for yi, yr in enumerate(("2000", "2001", "2002")):
    farms = "; ".join(f"{f} ZT {UY['ZT'][f][yi]} / CT {UY['CT'][f][yi]}" for f in UY["ZT"])
    put("YIELD", {**U, "year of data collection/experiment": f"{int(yr) - 1}-{yr[2:]} (wheat harvest {yr})", "YEAR OF DATA (duration)": yi + 1,
                  "Crop/season of sampling": f"Wheat harvest {yr}"},
        {c: UTXT[c][yi] for c in ("ZT", "CT")}, "WYIELD_",
        f"Text means of the 5 farms (Table VII 'Average' row is misprinted: 4.82 / 3.75 / 1.90 / 2.02 / 1.85 / 1.87). Means recomputed from the farm values: ZT "
        f"{sum(UY['ZT'][f][yi] for f in UY['ZT']) / 5:.2f}, CT {sum(UY['CT'][f][yi] for f in UY['CT']) / 5:.2f} t/ha. Farm values (t/ha): {farms}. " + U_NOTE,
        Y=3, D=0, UNIT="t/ha (wheat grain; 8 m2 harvest, moisture basis not stated)",
        **{"Data source": "Text (Results) + Table VII", "Method used (from paper)": "8 m2 harvested at maturity, threshed manually, grain yield t/ha; ANOVA 5 %"})
put("YIELD", {**U, "Site/Location": "Farmers' fields (M.K., Zaidi and Dogar farms), Punjab - Experiment 2", "Rep": 3, "year of data collection/experiment": "2001-02",
              "YEAR OF DATA (duration)": 3, "Crop/season of sampling": "Wheat harvest 2002 - Experiment 2 (establishment methods)"},
    {"ZT": 4.43, "CT": 3.95}, "WYIELD_",
    "EXPERIMENT 2 (Table VIII, 3 farms, 2001-02): printed means (farm values ZT flat 4.02 / 4.95 / 4.15, conventional 3.45 / 4.25 / 4.05; recomputed means 4.37 / 3.92). "
    "Beds with two rows (4.60) and three rows (4.42) NOT entered - bed formation not described (ask: MT under rule 15 or CT under rule 98?). " + U_NOTE,
    D=0, UNIT="t/ha (wheat grain)", **{"Data source": "Table VIII", "Method used (from paper)": "8 m2 harvested at maturity, threshed manually; ANOVA 5 %"})
put("WUE", {**U, "year of data collection/experiment": "2000-2002 (average)", "Crop/season of sampling": "Wheat seasons 2000-2002"},
    {"ZT": "=ROUND(4970/(35*25.4),2)", "CT": "=ROUND(4820/(43*25.4),2)"}, "WUE_W",
    "DERIVED IRRIGATION water productivity (rule 9 flag): Table IX grain yield (ZT 4.97, CT 4.82 t/ha - note Table IX lists these against the other columns' "
    "order: 'Conventional 4.82, Zero 4.97') / irrigation water (ZT 35, CT 43 hectare-inches x 25.4 mm); rainfall not included. Table IX also: seed 87.5 vs 125 kg/ha, "
    "land preparation Rs 450 vs 3400/ha, diesel 15.2 vs 68.5 L/ha, herbicide Rs 1000 vs 1500, labour 0 vs 5 man-days; saving Rs 5725/ha (no gross / cost -> no B:C). "
    + U_NOTE, Y=3, UNIT="kg grain/ha/mm irrigation (DERIVED, irrigation only)",
    **{"Data source": "DERIVED from Table IX", "Method used (from paper)": "Irrigation water recorded per field (hectare-inches); yield from 8 m2 harvests"})
ub = {**U, "year of data collection/experiment": "2002 (end of study)", "DEPTH": "0-15 CM", "DEPTH (as reported in paper)": "0-10 cm",
      "Crop/season of sampling": "End of the 3-year study (2002; after wheat)"}
UI = "Initial (1999) values: pH 8.10, EC 0.35 dS/m, OM 1.23 %, NO3-N 0.96, P 4.56, K 98, Zn 1.52, Cu 3.82, Mn 5.16 mg/kg."
for sh, pre, zt, ct, unit, meth, extra in (
        ("PH", "PH_", 8.18, 8.09, "pH (soil:water ratio not stated)", "pH (method not stated); ranges ZT 7.81-8.47, CT 7.90-8.54", ""),
        ("EC", "EC_", 0.68, 0.44, "dS/m (EC 1:1)", "EC in 1:1 soil:water extract; ranges ZT 0.51-1.84, CT 0.23-0.95", ""),
        ("SOC(active C pool)", "SOC_", "=ROUND(1.56*10/1.724,2)", "=ROUND(1.21*10/1.724,2)", "g/kg (DERIVED: OM % x 10 / 1.724)", "Organic matter (method not stated); SOC = OM / 1.724",
         "OM printed 1.56 % (ZT) vs 1.21 % (CT); converted (rule 47). "),
        ("no3,nh4,PMN", "NO3_", 1.66, 1.36, "mg/kg (NO3-N, AB-DTPA; kept as printed - no BD, rule 58)", "AB-DTPA extraction (Soltanpour) of NO3-N", ""),
        ("P", "P_", 6.83, 4.44, "mg/kg (AB-DTPA P; kept as printed - no BD, rule 58)", "AB-DTPA extractable P", ""),
        ("K", "K_", 116, 106, "mg/kg (AB-DTPA K; kept as printed - no BD, rule 58)", "AB-DTPA extractable K", ""),
        ("Zn(ppm)", "Zn_", 2.53, 1.42, "mg/kg", "Extractant not stated (AB-DTPA used for P, NO3-N, K)", ""),
        ("Cu(ppm)", "Cu_", 4.37, 3.78, "mg/kg", "Extractant not stated (AB-DTPA used for P, NO3-N, K)", ""),
        ("Mn", "Mn_", 7.02, 6.86, "mg/kg", "Extractant not stated (AB-DTPA used for P, NO3-N, K)", "")):
    put(sh, ub, {"ZT": zt, "CT": ct}, pre, f"Table V (means of the ZT / CT fields; no SD). {extra}{UI} " + U_NOTE, UNIT=unit,
        **{"Data source": "Table V", "Method used (from paper)": f"{meth}; soil 0-10 cm from each field at the start and end of the study"})
UM = {"ZT": {"Rizwan": ((2.2e6, 4.5e5, 5.5e4), (2.7e6, 4.9e5, 7.7e4)), "Imran": ((1.4e6, 2.0e5, 5.4e4), (2.4e6, 3.5e5, 5.9e4)),
             "Shahbaz": ((1.6e6, 3.5e5, 6.5e4), (3.7e6, 4.1e5, 6.1e4)), "Asghar": ((3.5e6, 2.0e5, 0.0), (4.0e6, 3.0e5, 2.6e4)),
             "Bashir": ((5.5e6, 3.6e5, 2.6e4), (3.8e6, 3.9e5, 4.6e4))},
      "CT": {"Rizwan": ((1.9e6, 6.0e5, 1.5e4), (1.9e6, 4.5e5, 1.2e4)), "Imran": ((6.2e6, 3.5e5, 3.0e4), (2.1e6, 3.2e5, 2.5e4)),
             "Shahbaz": ((1.0e6, 1.5e5, 2.0e4), (1.1e6, 1.8e5, 1.7e4)), "Asghar": ((2.9e6, 3.5e5, 1.5e4), (2.5e6, 2.3e5, 1.8e4)),
             "Bashir": ((3.9e6, 2.1e5, 2.4e4), (2.0e6, 3.2e5, 2.8e4))}}
for yi, yr in enumerate(("2000-01", "2001-02")):
    mb = {**ub, "year of data collection/experiment": yr, "YEAR OF DATA (duration)": yi + 1, "Crop/season of sampling": f"Wheat season {yr}"}
    for k, (sh, pre, div, unit, nm) in enumerate((("Soil microbial count", "SMC_", 1e7, "10^7 cfu/g soil (bacteria; printed x 10^6 per g)", "bacteria"),
                                                  ("Actinomycetes", "AM_", 1e5, "10^5 cfu/g soil", "actinomyces"),
                                                  ("Fungal count", "FUN_", 1e4, "CFU x 10^4 /g soil (fungi)", "fungi"))):
        vals = {c: "=ROUND(AVERAGE(" + ",".join(f"{UM[c][f][yi][k] / div:g}" for f in UM[c]) + "),3)" for c in ("ZT", "CT")}
        farms = "; ".join(f"{f} ZT {UM['ZT'][f][yi][k]:.1e} / CT {UM['CT'][f][yi][k]:.1e}" for f in UM["ZT"])
        put(sh, mb, vals, pre, f"Table VI {nm}, mean of the 5 farms (live AVERAGE of the farm values in sheet units; Asghar ZT fungi 2000-01 printed 'Nil' = 0). Farm values "
            f"(cfu/g): {farms}. " + U_NOTE, Y=2, UNIT=unit,
            **{"Data source": "Table VI - mean of farms (DERIVED)", "Method used (from paper)": "Plate counts on selective media (bacteria, actinomyces, fungi), 0-10 cm soil"})

# =====================================================================================
# 24 (companion 2)  CHOUDHARY M. et al. 2018 Appl. Soil Ecol. 126:189-198 (re-submission of old-master 24)
# =====================================================================================
C_TRT = ("TREATMENTS IN PAPER (CIMMYT farmer-participatory trial, Taraori, Karnal, est. 2012; RBD 3 reps, 20 x 5.4 m; Table 1): T1 CTR-CTW (FP) puddled TPR (2 disc + 2 "
         "cross harrow puddling + planking) + CT wheat (2 harrow + 3 cultivator + planking, broadcast), residue removed; T2 = T1 at RDF; T3 CTR-CTW-CTMb (Mb Ri) + "
         "mungbean, mungbean residue incorporated (5.52 t/ha over 3 yr); T4 CTR-CTW (RW Ri) 100 % rice + 33 % wheat residue incorporated (26.50 t/ha); T5 ZTDSR-ZTW (FP) "
         "residue removed; T6 = T5 at RDF; T7 ZTDSR-ZTW-ZTMb (Mb Rr) relay mungbean, mungbean residue retained (4.56 t/ha); T8 ZTDSR-ZTW (R Rr) turbo Happy Seeder, 100 % "
         "rice residue (18.39 t/ha); T9 ZTDSR-ZTW (RW Rr) 100 % rice + 33 % wheat residue (24.53 t/ha); T10 T9 + relay mungbean + 100 % mungbean residue (30.95 t/ha); "
         "T11-T14 maize-wheat (excluded).")
C_MAP = ("row a (= old-master 24): CT T1, CTR T4, ZT T5, CA T9 ; row b (fertiliser RDF / rice-residue-only CA): CT T2, CTR T4, ZT T6, CA T8 ; row c (mungbean, mungbean "
         "residue only): CT T1, CTR T3, ZT T5, CA T7 ; row d: CT T1, CTR T4, ZT T5, CA T10 (rice + wheat + mungbean residue)")
C = {"No.": "24 (companion 2)", "SERIAL NO": "24 (companion 2)", "Authors": "Choudhary M., Jat H.S., Datta A., Yadav A.K., Sapkota T.B., Mondal S., Meena R.P., Sharma P.C. & Jat M.L.",
     "Year": 2018, "Journal": "Applied Soil Ecology", "Country": "India (Haryana)", "Site/Location": "Farmer participatory trial, Taraori, Karnal", "latitude": 29.8,
     "longitude": 76.917, "CLIMATE": "ST", "SOIL": "LOAMY", "Rep": 3, "LATT": 29.8, "CLAY": 38.28, "sand": 32.08, "silt": 29.64, "ph (initial)": 7.94, "soc (initial)": 4.7,
     "RAIN FALL": 670, "AVG T": 24, "DURATION": "0-3 Y", "YEAR OF DATA (duration)": 3, "year of data collection/experiment": "April 2015 (3rd year)",
     "DEPTH": "0-15 CM", "DEPTH (as reported in paper)": "0-10 cm", "Crop/season of sampling": "After wheat harvest, April 2015",
     "Treatment mapping (paper's name -> code)": C_MAP, "Treatment details (from paper)": C_TRT}
CR = [("a", ("T1", "T4", "T5", "T9")), ("b", ("T2", "T4", "T6", "T8")), ("c", ("T1", "T3", "T5", "T7")), ("d", ("T1", "T4", "T5", "T10"))]
CRN = {"a": "row a = OLD-MASTER 24 SET (T1 CT, T4 CTR, T5 ZT, T9 CA)", "b": "row b (NEW, rules 20 / 33): CT = T2 and ZT = T6 at the recommended dose (RDF), CA = T8 "
       "(100 % rice residue only); CTR = T4 repeated", "c": "row c (NEW, rules 20 / 71 - MUNGBEAN flag): CTR = T3 (CT + mungbean, mungbean residue incorporated), CA = T7 "
       "(ZT + relay mungbean, mungbean residue retained); CT = T1, ZT = T5 repeated", "d": "row d (NEW, rules 20 / 71 - MUNGBEAN flag): CA = T10 (T9 + relay mungbean "
       "and its residue); CT, CTR, ZT repeated"}
C_NOTE = ("DUPLICATE RE-SUBMISSION (rule 6): this paper is old-master study 24 (same file content) - row a repeats the old-master 24 values (DUPLICATE FLAG, rule 99); rows "
          "b-d add treatments the old entry excluded (rules 20 / 33 / 71; ask). Maize-wheat T11-T14 excluded (rule 31). Rep 3; values +/- SE printed (SE in Notes, SD "
          "formula kept). Supplementary Tables S1-S4: " + SUPP + ". Source file 128.pdf.")
CT2 = {"T1": (7.83, .05, .52, .01, 1.47, .01, 4.6, .06), "T2": (7.95, .05, .40, .01, 1.46, .01, 5.2, .06), "T3": (8.10, .06, .41, .02, 1.42, .01, 5.8, .07),
       "T4": (7.90, .03, .44, .01, 1.41, .01, 6.6, .06), "T5": (7.90, .07, .53, .01, 1.37, .01, 5.4, .06), "T6": (7.88, .02, .48, .01, 1.37, .01, 6.0, .12),
       "T7": (7.99, .01, .36, .01, 1.37, .01, 6.2, .06), "T8": (7.89, .03, .51, .02, 1.35, .01, 7.6, .06), "T9": (7.66, .06, .47, .01, 1.36, .00, 8.2, .06),
       "T10": (7.64, .04, .54, .02, 1.35, .01, 8.4, .06)}
CT3 = {"T1": (646, 10.33, 201, 1.86, 180, 8.7, 144, 5.4, 74.7, .67, 45.3, .88, 35.5, .76), "T2": (804, 3.31, 221, 1.76, 193, 13.2, 150, 9.8, 76.4, .87, 49.7, 1.67, 37.6, 1.32),
       "T3": (981, 19.86, 269, 13.42, 245, 12.5, 175, 4.5, 82.3, 1.45, 56.0, 1.73, 47.3, .67), "T4": (1110, 33.61, 338, 27.68, 256, 17.4, 176, 4.7, 83.2, 1.61, 57.9, 2.19, 49.0, .17),
       "T5": (887, 33.38, 233, 2.18, 196, 7.4, 153, 8.0, 78.6, 1.33, 52.2, 0.00, 40.2, 1.42), "T6": (907, 7.58, 245, .57, 260, 42.7, 163, 1.2, 81.7, .88, 55.4, 2.23, 46.3, .93),
       "T7": (1158, 72.20, 359, 3.35, 263, 18.1, 183, 3.4, 85.0, .58, 59.3, .33, 50.7, .67), "T8": (1177, 31.76, 359, 14.81, 298, 22.2, 181, 3.6, 85.9, 1.67, 63.7, 1.48, 51.2, 1.01),
       "T9": (1295, 33.38, 475, 5.78, 404, 3.5, 196, 10.4, 91.3, .17, 72.1, 1.46, 54.4, 1.45), "T10": (1404, 29.06, 545, 3.61, 432, 33.6, 204, 5.3, 94.3, .93, 73.1, .07, 68.0, 1.73)}
CT6 = {"T1": (6.53, 4.77, 11.12), "T2": (7.29, 5.00, 12.09), "T3": (7.44, 4.73, 14.47), "T4": (6.91, 5.02, 11.74), "T5": (6.77, 5.47, 12.06), "T6": (7.06, 5.60, 13.34),
       "T7": (7.48, 5.99, 15.92), "T8": (7.18, 5.99, 12.98), "T9": (6.71, 6.23, 13.65), "T10": (6.94, 6.14, 15.50)}
MB = {"T3": 0.78, "T6": 0.27, "T7": 0.83, "T9": 0.28, "T10": 0.82}
sqi = dj("choudhary2018_sqi.json")["sqi"]
CODES = ("CT", "CTR", "ZT", "CA")
bdrow = {}
for rl, ts in CR:
    se = lambda i, tab: " / ".join(f"{t} {tab[t][i]}" for t in ts)
    nn = f"ROW {rl}: {CRN[rl]}. "
    for sh, pre, idx, unit, meth, src in (
            ("PH", "PH_", 0, "pH (1:2 soil:water)", "Soil:water 1:2 suspension (Jackson 1973)", "Table 2"),
            ("EC", "EC_", 2, "dS/m (1:2 soil:water)", "Soil:water 1:2 suspension (Jackson 1973)", "Table 2"),
            ("BD", "BD_", 4, "Mg/m3", "Core sampler (Blake & Hartge 1986)", "Table 2"),
            ("SOC(active C pool)", "SOC_", 6, "g/kg (Walkley-Black oxidisable OC)", "Wet oxidation (Walkley & Black 1934)", "Table 2")):
        r = put(sh, C, {c: CT2[t][idx] for c, t in zip(CODES, ts)}, pre, nn + f"{src} (SE {se(idx + 1, CT2)}). " + C_NOTE, T=4, UNIT=unit,
                **{"Data source": src, "Method used (from paper)": meth + "; 0-10 cm, 3 replicates, composite of 5 auger cores per plot, April 2015"})
        if sh == "BD":
            bdrow[rl] = r
    put("POROSITY", C, {c: f"=ROUND((1-{B.ref('BD', 'BD_' + c, bdrow[rl])}/2.65)*100,1)" for c in CODES}, "POROSITY_",
        nn + "DERIVED total porosity = (1 - BD / 2.65) x 100, live link to the BD row (rule 73; PD not reported -> 2.65 flagged). " + C_NOTE, T=4,
        UNIT="% v/v (DERIVED from BD, PD 2.65)", **{"Data source": "DERIVED from Table 2", "Method used (from paper)": "Porosity = (1 - BD/PD) x 100, PD 2.65 Mg/m3 (default)"})
    for sh, pre, idx, unit, meth, fmt in (
            ("MBC", "MBC_", 0, "ug C/g soil", "Chloroform fumigation-extraction (Vance et al. 1987), fresh soil", None),
            ("MBN", "MBN_", 2, "ug N/g soil", "Chloroform fumigation-extraction (Vance et al. 1987), fresh soil", None),
            ("DHA", "DHA_", 4, "ug TPF/g soil/h (printed per 24 h / 24)", "Dick et al. (1996), TPF per g per 24 h", "=ROUND({}/24,2)"),
            ("ALKP", "ALP_", 6, "ug PNP/g soil/h", "Dick et al. (1996), p-nitrophenol per g per h", None),
            ("Soil microbial count", "SMC_", 8, "10^7 cfu/g soil (bacteria; printed x 10^4 / g)", "Nutrient agar plate count (CFU/g dry soil)", "=ROUND({}*10^4/10^7,4)"),
            ("Fungal count", "FUN_", 10, "CFU x 10^2 /g soil (fungi, as printed)", "Rose Bengal agar + streptomycin plate count", None),
            ("Actinomycetes", "AM_", 12, "10^5 cfu/g soil (printed x 10^4 / g)", "Actinomycetes isolation agar + nalidixic acid plate count", "=ROUND({}*10^4/10^5,2)")):
        vals = {c: (fmt.format(CT3[t][idx]) if fmt else CT3[t][idx]) for c, t in zip(CODES, ts)}
        put(sh, C, vals, pre, nn + f"Table 3 (SE {se(idx + 1, CT3)}). " + C_NOTE, T=4, UNIT=unit,
            **{"Data source": "Table 3" + (" - converted" if fmt else ""), "Method used (from paper)": meth + "; 0-10 cm, April 2015"})
    put("SQI", C, {c: sqi[t] for c, t in zip(CODES, ts)}, "SQI_",
        nn + "Fig. 2 DIGITISED (raster hatched bars, 11 tick stubs 0.00-1.00; text T10 0.82, T6 / T14 0.76 reproduced). SQI from a PCA minimum data set (fungal count 0.685, "
        "pH 0.154, microarthropod population 0.099) with non-linear scoring (Bastida et al. 2006). " + C_NOTE, T=4, UNIT="unitless (0-1; PCA-MDS, non-linear scoring)",
        **{"Data source": "Fig. 2 (digitised)", "Method used (from paper)": "PCA minimum data set (fungi, pH, microarthropods) weighted non-linear scores, Eq. 6-7"})
    yb = {k: v for k, v in C.items() if k not in NODEPTH}
    mbn = "; ".join(f"{t} mungbean {MB[t]} t/ha" for t in ts if t in MB)
    put("YIELD", {**yb, "Crop/season of sampling": "Rice, wheat and system yield (Table 6)"}, {c: CT6[t][1] for c, t in zip(CODES, ts)}, "WYIELD_",
        nn + "Table 6 (years averaged not stated - 3-year trial; Y=1 as in old-master 24). RICE YIELD = Table 6 'rice equivalent yield' (rice systems = rice grain yield). "
        "SYS YIELD = wheat-equivalent system yield (MSP basis) INCLUDING MUNGBEAN where grown (rule 54 flag): " + (mbn or "no mungbean in this row") + ". Table 6 also "
        "prints mungbean yields for T6 / T9 (rice-wheat-fallow in Table 1) - flag. " + C_NOTE, T=4, D=0,
        UNIT="Mg/ha (grain, 14 % moisture; system = wheat-equivalent)",
        **{**{"RICE YIELD_" + c: CT6[t][0] for c, t in zip(CODES, ts)}, **{"SYS YIELD_" + c: CT6[t][2] for c, t in zip(CODES, ts)},
           "Data source": "Table 6", "Method used (from paper)": "Manual harvest of 2 quadrats of 4 x 2.7 m per plot, 14 % moisture; WEY by minimum support prices (Eq. 5)"})

# =====================================================================================
# 159 (companion)  DUTTA A. et al. 2023 IJERPH 20:810 - IIFSR Modipuram tillage x residue trial (old-master 159)
# =====================================================================================
D_TRT = ("TREATMENTS IN PAPER (ICAR-IIFSR Modipuram, Meerut; CA experiment initiated 1998-99, rice-wheat; split plot, 4 replications; sampled after wheat harvest, end "
         "of March 2016 = 18 years): main plots zero tillage (ZT), conventional tillage (CT), strip tillage (ST); sub-plots residue burning (RB), no residue (NR), 40 % "
         "crop residue retention (R). 'Standard package of practices' (rice establishment not described).")
D_MAP = ("row a (no residue): CT = CT-NR, pZT = ZT-NR, pMT = ST-NR ; row b (residue burnt): CT = CT-RB, pZT = ZT-RB, pMT = ST-RB ; both rows: CTR = CT-R, pCA = ZT-R, "
         "pMTR = ST-R (rice phase puddled TPR per old-master 159 Gangwar 2006, rule 89; strip tillage = MT / MTR, rule 16)")
DU = {"No.": "159 (companion)", "SERIAL NO": "159 (companion)", "Authors": "Dutta A., Bhattacharyya R., Jimenez-Ballesta R., Dey A., Das Saha N., Kumar S., Nath C.P., Prakash V., Jatav S.S. & Patra A.",
      "Year": 2023, "Journal": "International Journal of Environmental Research and Public Health", "Country": "India (Uttar Pradesh)",
      "Site/Location": "ICAR-IIFSR (formerly PDCSR), Modipuram, Meerut", "latitude": 28.99, "longitude": 77.70, "CLIMATE": "ST", "SOIL": "LOAMY", "Rep": 3, "LATT": 28.99,
      "AVG T": 24.1, "MIN TEMP": 7.2, "MAX TEMP": 39.1, "RAIN FALL": 860, "DURATION": ">10 Y", "YEAR OF DATA (duration)": 18,
      "year of data collection/experiment": "March 2016 (18 years)", "Crop/season of sampling": "After wheat harvest, end of March 2016",
      "Treatment mapping (paper's name -> code)": D_MAP,
      "Fertilizer dose & other management": "Standard package of practices (not detailed). Residue: 40 % retention (R), burnt (RB) or removed (NR).",
      "Treatment details (from paper)": D_TRT}
D_NOTE = ("COMPANION of old-master 159 (Gangwar et al. 2006, PDCSR Modipuram tillage x residue trial est. 1998; rule 5 - flag: same institute, start year and 3 tillage x 3 "
          "residue design). Rice phase not described here: puddled TPR taken from 159 (rule 89) -> ZT / ST after puddled rice = partial codes (rules 68 / 85). Residue "
          "burning = no residue retained -> row b (rule 116). Strip tillage -> pMT / pMTR (rule 16). Rep 3 (means of three replicates). Supplementary Table S1 (basic "
          "soil properties): " + SUPP + ". Source file 128_real.pdf.")
DR = [("a", "NR"), ("b", "RB")]
DT1 = {"ZT-NR": (5.7, 4.4, 5.5, 4.3, 494.2, 249), "ZT-RB": (6.3, 4.5, 5.7, 4.6, 478.2, 208.6), "ZT-R": (7.7, 4.8, 7.3, 4.8, 599.7, 417.6),
       "CT-NR": (5.5, 4.3, 5.1, 4.1, 327.6, 188.7), "CT-RB": (5.8, 4.4, 5.6, 4.35, 319.3, 133.9), "CT-R": (7.2, 4.6, 7.0, 4.6, 463.1, 190.7),
       "ST-NR": (5.5, 4.3, 5.4, 4.2, 481.6, 290), "ST-RB": (5.8, 4.4, 5.7, 4.45, 368, 197.1), "ST-R": (7.4, 4.7, 7.2, 4.65, 567.9, 394)}
DT4 = {"ZT-NR": (271.1, 166.8, 93.82, 44.54), "ZT-RB": (146, 104.8, 53.12, 17.60), "ZT-R": (274.4, 191.9, 119.2, 98.37), "CT-NR": (147.3, 84.16, 48.08, 18.53),
       "CT-RB": (109.9, 56.36, 47.32, 19.30), "CT-R": (199.9, 133.4, 67.17, 77.34), "ST-NR": (253.7, 167.2, 105.1, 35.20), "ST-RB": (140.6, 86.95, 42.97, 53.57),
       "ST-R": (350.4, 176.2, 105.6, 113.37)}
DT5 = {"ZT-NR": (223.9, 129.6, 629.36, 151.2), "ZT-RB": (115.7, 91.76, 337.48, 117.2), "ZT-R": (188.6, 133.5, 644.32, 206.6), "CT-NR": (94.91, 58.31, 451.57, 103.9),
       "CT-RB": (68.04, 44.72, 171.89, 72.78), "CT-R": (105.2, 70.97, 472.01, 184.9), "ST-NR": (162.4, 123.5, 618.47, 193.9), "ST-RB": (133.6, 96.05, 317.60, 148.5),
       "ST-R": (204.5, 126.4, 661.42, 227.6)}
DT2 = ("Table 2 (0-5 cm; Ea kJ/mol bulk / macro / micro; Q10 bulk / macro / micro): ZT-NR 8.48 / 13.30 / 12.50, 1.12 / 1.18 / 1.17; ZT-RB 5.90 / 7.69 / 6.18, 1.07 / 1.10 / "
       "1.08; ZT-R 8.94 / 12.99 / 15.03, 1.12 / 1.18 / 1.21; CT-NR 8.21 / 8.17 / 10.33, 1.11 / 1.11 / 1.14; CT-RB 4.39 / 5.97 / 5.89, 1.05 / 1.07 / 1.07; CT-R 8.86 / "
       "11.14 / 12.35, 1.12 / 1.15 / 1.17. Table 3 decay constant Kc (mg C/week; 37 C bulk / macro / micro, 27 C bulk / macro / micro): ZT-NR 0.003999 / 0.003256 / "
       "0.004198, 0.003598 / 0.002931 / 0.003780; ZT-RB 0.003625 / 0.003443 / 0.004093, 0.003358 / 0.003188 / 0.003675; ZT-R 0.003934 / 0.003395 / 0.005248, 0.003506 / "
       "0.002872 / 0.004328; CT-NR 0.005848 / 0.003604 / 0.003962, 0.005243 / 0.003037 / 0.003373; CT-RB 0.004382 / 0.003785 / 0.004519, 0.004141 / 0.003248 / 0.004189; "
       "CT-R 0.005259 / 0.004063 / 0.005917, 0.004692 / 0.003520 / 0.005093 (no sheet - Notes only).")
TRI = ("CT", "pZT", "pMT")
RES = ("CTR", "pCA", "pMTR")
for rl, rk in DR:
    trs = (f"CT-{rk}", f"ZT-{rk}", f"ST-{rk}")
    nn = f"ROW {rl} ({'no residue' if rk == 'NR' else 'residue BURNT'}): CT / pZT / pMT = {' / '.join(trs)}; CTR / pCA / pMTR = CT-R / ZT-R / ST-R. "
    for di, (dr, ix) in enumerate((("0-5 cm", 0), ("5-15 cm", 1))):
        db = {**DU, "DEPTH": "0-15 CM", "DEPTH (as reported in paper)": dr}
        def v9(tab, i):
            d = {c: tab[t][i] for c, t in zip(TRI, trs)}
            d.update({c: tab[t][i] for c, t in zip(RES, ("CT-R", "ZT-R", "ST-R"))})
            return d
        put("macro c", db, v9(DT1, 0 + 2 * ix), "MACRO c_", nn + "Table 1 total SOC in macro-aggregates (TC by IRMS - TIC, wet sieving). Residue main-effect rows of Table "
            "1 at 0-5 cm (NR 7.43, R 5.56) contradict the cell means (flag; cells entered). " + D_NOTE, T=2, D=2, UNIT="g/kg (SOC in macro-aggregates, TC - TIC)",
            **{"Data source": "Table 1", "Method used (from paper)": "Wet sieving (8-mm sieved moist soil); total C by isotope-ratio mass spectrometer minus titrimetric TIC"})
        put("micro c", db, v9(DT1, 1 + 2 * ix), "MICRO c_", nn + "Table 1 total SOC in micro-aggregates. " + D_NOTE, T=2, D=2,
            UNIT="g/kg (SOC in micro-aggregates, TC - TIC)",
            **{"Data source": "Table 1", "Method used (from paper)": "Wet sieving; total C by IRMS minus titrimetric TIC"})
        put("MBC", db, v9(DT1, 4 + ix), "MBC_", nn + "Table 1 SMBC (header prints 'ug kg-1'; text 'ug C g-1' - entered as ug/g, typo flag). " + D_NOTE, T=2, D=2,
            UNIT="ug C/g soil", **{"Data source": "Table 1", "Method used (from paper)": "Chloroform fumigation-extraction (Jenkinson & Ladd), KEC 0.45; refrigerated soil"})
        for sh, pre, tab, i0, nm, meth in (("B-GLU", "BGL_", DT4, 0, "beta-D-glucosidase", "Eivazi & Tabatabai, colorimetric (p-nitrophenol)"),
                                           ("B-galactosidase", "BGAL_", DT4, 2, "beta-D-galactosidase", "Eivazi & Tabatabai, colorimetric (p-nitrophenol)"),
                                           ("PEROX", "PEROX_", DT5, 0, "peroxidase", "Colorimetric at 450 nm, tetramethylbenzidine substrate"),
                                           ("PPO", "PPO_", DT5, 2, "polyphenol oxidase", "Colorimetric at 525 nm, 0.2 M catechol substrate")):
            put(sh, db, v9(tab, i0 + ix), pre, nn + f"Table {4 if tab is DT4 else 5} {nm}. "
                + ("Tillage main-effect PPO at 5-15 cm (CT 416.5, ST 479.3) does not match the cell means (flag; cells entered). " if sh == "PPO" else "") + D_NOTE,
                T=2, D=2, UNIT="ug/g soil/h", **{"Data source": f"Table {4 if tab is DT4 else 5}", "Method used (from paper)": meth})
gl = dj("dutta2023_glomalin.json")["glomalin_mg_g"]
for rl, rk in DR:
    trs = (f"CT-{rk}", f"ZT-{rk}", f"ST-{rk}")
    nn = f"ROW {rl} ({'no residue' if rk == 'NR' else 'residue BURNT'}). "
    for dr, ser_ma, ser_mi in (("0-5 cm", "0-5 MA", "0-5 MI"), ("5-15 cm", "5-15 MA", "5-15 MI")):
        for ser, frac in ((ser_ma, "MACRO-AGGREGATES"), (ser_mi, "MICRO-AGGREGATES")):
            vals = {c: gl[t][ser] for c, t in zip(TRI, trs)}
            vals.update({c: gl[t][ser] for c, t in zip(RES, ("CT-R", "ZT-R", "ST-R"))})
            put("GLOMALIN", {**DU, "DEPTH": "0-15 CM", "DEPTH (as reported in paper)": dr,
                             "Crop/season of sampling": f"After wheat harvest, March 2016 - glomalin WITHIN {frac}"}, vals, "GLO_",
                nn + f"GLOMALIN IN {frac} (not bulk soil - flag; rule 115). Fig. 7 DIGITISED (raster coloured bars; text ZT-R 5-15 cm 1.41 and CT-NR 0.33 mg/g reproduced "
                "as 1.40 / 0.31). LSD in the caption. Easily extractable glomalin (EEG). " + D_NOTE, T=2, D=2, UNIT="mg/g aggregate (easily extractable glomalin)",
                **{"Data source": "Fig. 7 (digitised)", "Method used (from paper)": "EEG: 1 g soil autoclaved with 8 mL 20 mM citrate pH 7.0 for 30 min (Wright & Upadhyaya)"})
ct = dj("dutta2023_ct.json")
for fig, frac, temp in (("Fig1", "BULK SOIL", 37), ("Fig2", "BULK SOIL", 27), ("Fig3", "MACRO-AGGREGATES", 37), ("Fig4", "MACRO-AGGREGATES", 27),
                        ("Fig5", "MICRO-AGGREGATES", 37), ("Fig6", "MICRO-AGGREGATES", 27)):
    s = ct[fig]["series"]
    for rl, rk in DR:
        ser = "; ".join(f"{t}: " + ", ".join(f"d{d}={s[t][d]}" if s[t][d] is not None else f"d{d}=hidden" for d in ("1", "3", "7", "14", "29", "44", "59"))
                        for t in s)
        vals = {"CT": f"=ROUND({s['CT-' + rk]['59']}*10*44/12/59,2)", "pZT": f"=ROUND({s['ZT-' + rk]['59']}*10*44/12/59,2)",
                "CTR": f"=ROUND({s['CT-R']['59']}*10*44/12/59,2)", "pCA": f"=ROUND({s['ZT-R']['59']}*10*44/12/59,2)"}
        put("RESP", {**DU, "DEPTH": "0-15 CM", "DEPTH (as reported in paper)": "0-5 cm",
                     "Crop/season of sampling": f"After wheat harvest, March 2016 - {frac}, 59-day incubation at {temp} C"}, vals, "RESP_",
            f"ROW {rl} ({'no residue' if rk == 'NR' else 'residue BURNT'}). {frac}" + (" (not bulk soil - flag; rule 114)" if frac != "BULK SOIL" else "")
            + f", {temp} C. {fig.replace('Fig', 'Fig. ')} DIGITISED (raster line+marker plot; colour masks, calibrated on the y ticks; day-59 values reproduce the text: "
            "Fig. 1 CT-R 120.6 vs 120.5, ZT-R 112.6 vs 112.7; Fig. 2 CT-R 106.4 vs 106.2, CT-NR 71.1 vs 71.5; Fig. 3 CT-R 125.4 vs 125.5). Mean daily rate = cumulative C "
            "at day 59 (mg C/100 g) x 10 x 44/12 / 59 (rule 100). Strip tillage not incubated. Cumulative series (mg C/100 g; 'hidden' = marker under another series): "
            + ser + ". " + (DT2 if fig == "Fig1" and rl == "a" else "Q10 / Ea / Kc (Tables 2-3) in the Notes of the Fig. 1 row a. ") + D_NOTE, T=2,
            UNIT="mg CO2/kg soil/day (DERIVED mean over a 59-day incubation)",
            **{"Data source": f"{fig.replace('Fig', 'Fig. ')} (digitised) - DERIVED",
               "Method used (from paper)": (f"25 g soil at 75 % FC (-33 kPa), 15-d pre-incubation at 25 C, incubated at {temp} C with 0.5 N NaOH traps, back-titrated "
                                            "with 0.5 M HCl (BaCl2), days 1-59; Ct = Co(1 - e^-kt) (Sanford & Smith)")})

# =====================================================================================
# 173 (companion)  BISWAKARMA et al. 2023 - duplicate re-submission (127_real.pdf): copy every 173 row
# =====================================================================================
DUP = ("DUPLICATE RE-SUBMISSION (rule 6, 2026-10-05): 127_real.pdf is the same paper as study 173 (Biswakarma et al. 2023 AEE 357:108675, entered from 121_now.pdf); "
       "row copied unchanged from 173 (live formulas re-pointed to the copied rows). Do NOT pool with 173 - filter on this flag. ")
names = B.wb.sheetnames
DATA = [n for n in names[names.index("BD"):] if n != "EXCLUDED_rows"]
REF = re.compile(r"(?:(?P<sh>'[^']+'|[A-Za-z_][A-Za-z0-9_.]*)!)?(?P<col>\$?[A-Z]{1,3})(?P<row>\$?\d+)(?![\d(])")
rowmap, plan = {}, []
for n in DATA:
    ws = B.wb[n]
    src = [r for r in range(2, ws.max_row + 1) if ws.cell(r, 2).value == 173]
    if not src:
        continue
    r0 = B.next_row(n)
    for i, r in enumerate(src):
        rowmap[(n, r)] = r0 + i
        plan.append((n, r, r0 + i))


def repoint(f, sheet):
    def sub(m):
        sh = m.group("sh")
        tgt = sheet if sh is None else sh.strip("'")
        row = int(m.group("row").lstrip("$"))
        if (tgt, row) in rowmap:
            return (sh + "!" if sh else "") + m.group("col") + str(rowmap[(tgt, row)])
        return m.group(0)
    return REF.sub(sub, f)


for n, r, nr in plan:
    ws = B.wb[n]
    h = B.headers(n)
    for ci in range(1, ws.max_column + 1):
        c = ws.cell(r, ci)
        v = c.value
        if ci in (h.get("No."), h.get("SERIAL NO")):
            v = "173 (companion)"
        elif ci == h.get("Notes/Doubts"):
            v = DUP + (v or "")
        elif isinstance(v, str) and v.startswith("="):
            v = repoint(v, n)
        if ws.cell(1, ci).value == "UNIT FOR THIS SHEET:" or (v is None and not c.has_style):
            continue
        t = ws.cell(nr, ci)
        t.value = v
        t._style = copy(c._style)
print("173 (companion): copied", len(plan), "rows")

# =====================================================================================
# Study_Info, LAT_LONG, Treatment_Mapping, EXCLUDED_rows
# =====================================================================================
TS2 = ("Table S2 C mineralizability (g CO2/g SOC; >2 mm | <2 mm; 0-15 / 15-30 cm; CT0, CTR, NT0, NTR): Rice 2020 >2 0.109/0.111, 0.127/0.103, 0.109/0.108, "
       "0.124/0.110 | <2 0.116/0.115, 0.131/0.118, 0.123/0.118, 0.131/0.112; Rice 2021 >2 0.135/0.110, 0.129/0.101, 0.130/0.108, 0.126/0.106 | <2 0.134/0.116, "
       "0.135/0.111, 0.129/0.113, 0.133/0.115; Wheat 2020 >2 0.113/0.110, 0.128/0.130, 0.120/0.113, 0.127/0.110 | <2 0.122/0.123, 0.141/0.140, 0.129/0.135, "
       "0.137/0.141; Wheat 2021 >2 0.110/0.101, 0.126/0.122, 0.118/0.110, 0.130/0.117 | <2 0.116/0.118, 0.138/0.137, 0.124/0.126, 0.137/0.139 (all ns; no sheet).")
B.add("Study_Info", {"No.": 179, "SERIAL NO": 179, "Authors": A["Authors"], "Year": None, "Journal": "Main paper not supplied (supplementary material only)",
                     "Full reference": ("Ahmad N, Virk AL, Hafeez MB, Kan Z-R, Shi Z, Wang R, Iqbal HMW, Rehmani MIA, Wang X, Lal R, Li J. Soil carbon mineralization and "
                                        "aggregate distribution in various tillage practices of rice-wheat cropping system: A field and laboratory study. (Supplementary "
                                        "material; journal / year not given in the supplement)"),
                     "DOI / link": "Not given (supplement only)", "Country": "Pakistan", "Site/Location": A["Site/Location"], "latitude": 31.86, "longitude": 73.51,
                     "latitude (as reported)": "Map only (Fig. S1)", "longitude (as reported)": "Map only (Fig. S1)", "Coordinates source": "Approximate (Sukheki, Hafizabad)",
                     "CLIMATE": "TEMP", "year of data collection/experiment": "Rice 2020 - wheat 2021", "Years of data reported": "2 (year-wise)",
                     "Crop rotation": "Rice-wheat", "Wheat variety": "Akbar-2019", "Rice variety": "Super Kainat 1121 (fine aromatic)", "N dose (kg/ha)": "140 rice / 115 wheat",
                     "P dose (kg/ha)": "85 / 75", "K dose (kg/ha)": "62 / 62.5", "Residue type & rate (t/ha)": "Residue retained in CTR / NTR (rate in the main paper)",
                     "Irrigation / water management": "Rice 16 (DSR) / 20 (TPR) irrigations; wheat 4", "Treatments in paper": A_TRT,
                     "Parameters extracted": ("SOC 0-15 / 15-30 / 30-45 cm wheat 2020 and 2021 (Table S3); aggregate (>2 / <2 mm) C mineralisation rate 0-15 / 15-30 cm "
                                              "(Figs S4-S5, digitised); C input per season (Figs S8-S9, digitised). Rice-season values in Notes."),
                     "Supplementary data?": "YES - this upload IS the supplement (127.docx); main paper missing",
                     "Notes/Doubts": ("INCLUDED (supplement data): CT, CTR, ZT, CA. MWD / GMD (Figs S6-S7) are box plots pooled over treatments (rice vs wheat) - not "
                                      "entered (rule 119). " + TS2 + " " + A_NOTE)})
B.add("Study_Info", {"No.": 180, "SERIAL NO": 180, "Authors": U["Authors"], "Year": 2008, "Journal": "International Journal of Agriculture and Biology",
                     "Full reference": ("Mann RA, Ramzan M & Munir A (2008) Improving the sustainability of wheat production in irrigated areas of Punjab, Pakistan through "
                                        "conservation tillage technology. Int J Agric Biol 10(3):249-254"),
                     "DOI / link": "Int. J. Agric. Biol. 10(3):249-254 (07-182/AKA/2008/10-3-249-254)", "Country": "Pakistan", "Site/Location": U["Site/Location"],
                     "latitude": 31.7, "longitude": 74.0, "latitude (as reported)": "Not given", "longitude (as reported)": "Not given",
                     "Coordinates source": "APPROXIMATE (Punjab rice tract)", "CLIMATE": "TEMP", "Experiment established (year)": 1999,
                     "year of data collection/experiment": "1999-2000 to 2001-02", "Years of data reported": "3 (yields), 2 (microbes), 1 (soil chemistry)",
                     "DURATION": "0-3 Y", "SOIL": "LOAMY", "Texture as reported": "Mixed calcareous silty alluvium, moderately fine textured (Typic Camborthids)",
                     "ph (initial)": 8.10, "soc (initial)": 7.13, "Crop rotation": "Rice (Basmati)-wheat", "Treatments in paper": U_TRT,
                     "Parameters extracted": ("Wheat yield (3 years + experiment 2), irrigation WUE (derived), pH, EC, SOC (from OM), NO3-N, P, K, Zn, Cu, Mn (0-10 cm, end), "
                                              "bacteria / actinomycetes / fungi (2 years)"),
                     "Supplementary data?": "None referenced",
                     "Notes/Doubts": ("INCLUDED: ZT vs CT. Not entered (no sheet): weed density and species (Tables I-II), stem-borer larvae (Table III), predators "
                                      "(Table IV). Initial SOC = OM 1.23 % / 1.724. " + U_NOTE)})
B.add("Study_Info", {"No.": "24 (companion 2)", "SERIAL NO": "24 (companion 2)", "Authors": C["Authors"], "Year": 2018, "Journal": "Applied Soil Ecology",
                     "Full reference": ("Choudhary M, Jat HS, Datta A, Yadav AK, Sapkota TB, Mondal S, Meena RP, Sharma PC & Jat ML (2018) Sustainable intensification "
                                        "influences soil quality, biota, and productivity in cereal-based agroecosystems. Appl Soil Ecol 126:189-198"),
                     "DOI / link": "https://doi.org/10.1016/j.apsoil.2018.02.027", "Country": "India (Haryana)", "Site/Location": C["Site/Location"], "latitude": 29.8,
                     "longitude": 76.917, "latitude (as reported)": "29 deg 48' N", "longitude (as reported)": "76 deg 55' E", "Coordinates source": "Paper", "CLIMATE": "ST",
                     "Experiment established (year)": 2012, "year of data collection/experiment": "April 2015", "Years of data reported": "1 soil sampling; yields (3-yr trial)",
                     "DURATION": "0-3 Y", "SOIL": "LOAMY", "Texture as reported": "Clay loam (sand 32.08, silt 29.64, clay 38.28 %), Typic Ustocrept", "sand": 32.08,
                     "silt": 29.64, "CLAY": 38.28, "ph (initial)": 7.94, "soc (initial)": 4.7, "AVG T": 24, "RAIN FALL": 670,
                     "Crop rotation": "Rice-wheat (T1-T10; mungbean in T3, T7, T10); maize-wheat T11-T14 excluded", "Residue type & rate (t/ha)": "T3 5.52, T4 26.50, "
                     "T7 4.56, T8 18.39, T9 24.53, T10 30.95 t/ha over 3 years", "Treatments in paper": C_TRT,
                     "Parameters extracted": ("pH, EC, BD (+ porosity), OC, MBC, MBN, DHA, APA, bacteria, fungi, actinomycetes (0-10 cm), SQI (Fig. 2, digitised), rice / "
                                              "wheat / system yield - rows a-d"),
                     "Supplementary data?": "Tables S1-S4 / Fig. S1 referenced - " + SUPP,
                     "Notes/Doubts": ("RE-SUBMISSION of old-master 24 (rule 6) - entered again as 24 (companion 2); 24 (companion) = Choudhary 2018 Geoderma (old master). "
                                      "Not entered (no sheet): microarthropods (Table 4), EMI / QBS (Table 5). " + C_NOTE)})
B.add("Study_Info", {"No.": "159 (companion)", "SERIAL NO": "159 (companion)", "Authors": DU["Authors"], "Year": 2023,
                     "Journal": "International Journal of Environmental Research and Public Health",
                     "Full reference": ("Dutta A, Bhattacharyya R, Jimenez-Ballesta R, Dey A, Das Saha N, Kumar S, Nath CP, Prakash V, Jatav SS & Patra A (2023) Conventional "
                                        "and zero tillage with residue management in rice-wheat system in the Indo-Gangetic Plains: impact on thermal sensitivity of soil "
                                        "organic carbon respiration and enzyme activity. Int J Environ Res Public Health 20:810"),
                     "DOI / link": "https://doi.org/10.3390/ijerph20010810", "Country": "India (Uttar Pradesh)", "Site/Location": DU["Site/Location"], "latitude": 28.99,
                     "longitude": 77.70, "latitude (as reported)": "28.99 N", "longitude (as reported)": "77.70 E", "Coordinates source": "Paper", "CLIMATE": "ST",
                     "Experiment established (year)": 1998, "year of data collection/experiment": "March 2016 (after wheat)", "Years of data reported": "1 soil sampling",
                     "DURATION": ">10 Y", "SOIL": "LOAMY", "Texture as reported": "Inceptisol (Typic Haplustept); texture in Table S1 (sandy loam per 159)",
                     "MIN TEMP": 7.2, "MAX TEMP": 39.1, "AVG T": 24.1, "RAIN FALL": 860, "Crop rotation": "Rice-wheat",
                     "Residue type & rate (t/ha)": "40 % crop residue retained (R); burnt (RB); removed (NR)", "Treatments in paper": D_TRT,
                     "Parameters extracted": ("0-5 and 5-15 cm: macro / micro-aggregate SOC, MBC (Table 1), beta-glucosidase, beta-galactosidase (Table 4), peroxidase, "
                                              "polyphenol oxidase (Table 5), aggregate glomalin (Fig. 7); 0-5 cm C mineralisation rate bulk / macro / micro at 27 and 37 C "
                                              "(Figs 1-6, digitised); Q10, Ea, Kc in Notes"),
                     "Supplementary data?": "Table S1 (basic soil properties) - " + SUPP,
                     "Notes/Doubts": "INCLUDED as companion of old-master 159: CT, CTR, pZT, pCA, pMT, pMTR; rows a (NR) / b (RB). " + D_NOTE})
B.add("Study_Info", {"No.": "173 (companion)", "SERIAL NO": "173 (companion)", "Authors": ("Biswakarma N., Pooniya V., Zhiipao R.R., Kumar D., Shivay Y.S., Das T.K., Roy D., "
                     "Das B., Choudhary A.K., Swarnalakshmi K., Govindasamy P., Lakhena K.K., Das K., Lama A., Jat R.D., Babu S., Khan S.A. & Behera B."), "Year": 2023,
                     "Journal": "Agriculture, Ecosystems and Environment",
                     "Full reference": ("Biswakarma N et al. (2023) Identification of a resource-efficient integrated crop management practice for the rice-wheat rotations "
                                        "in south Asian Indo-Gangetic Plains. Agric Ecosyst Environ 357:108675"),
                     "DOI / link": "https://doi.org/10.1016/j.agee.2023.108675", "Country": "India (Delhi)", "Site/Location": "ICAR-IARI research farm, New Delhi (ICM trial, est. 2015)",
                     "latitude": 28.633, "longitude": 77.15, "Coordinates source": "Paper", "CLIMATE": "ST", "Experiment established (year)": 2015,
                     "Parameters extracted": "As study 173 (every row copied)", "Supplementary data?": "As study 173",
                     "Notes/Doubts": (DUP + "Upload 127_real.pdf sat beside 127.docx (the supplement of Ahmad et al.) - possibly the Ahmad main paper was intended; "
                                      "ask the author whether to keep or delete these duplicate rows.")})
for no, au, yr, ctry, site, la, lo, lar, lor, src, cl, note in [
        (179, "Ahmad N. et al.", None, "Pakistan", "Sukheki Agricultural Farm, Hafizabad", 31.86, 73.51, "Map (Fig. S1)", "Map (Fig. S1)", "Approximate", "TEMP", "Supplement only"),
        (180, "Mann R.A. et al.", 2008, "Pakistan", "Farmers' fields, Punjab rice tract", 31.7, 74.0, "Not given", "Not given", "Approximate", "TEMP", "Farms not located"),
        ("24 (companion 2)", "Choudhary M. et al.", 2018, "India (Haryana)", "Taraori, Karnal", 29.8, 76.917, "29 deg 48' N", "76 deg 55' E", "Paper", "ST", "Re-submission of 24"),
        ("159 (companion)", "Dutta A. et al.", 2023, "India (Uttar Pradesh)", "ICAR-IIFSR, Modipuram", 28.99, 77.70, "28.99 N", "77.70 E", "Paper", "ST", "Same trial as 159"),
        ("173 (companion)", "Biswakarma N. et al.", 2023, "India (Delhi)", "ICAR-IARI, New Delhi", 28.633, 77.15, "28 deg 38' N", "77 deg 09' E", "Paper", "ST", "Duplicate of 173")]:
    B.add("LAT_LONG", {"No.": no, "SERIAL NO": no, "Authors": au, "Year": yr, "Country": ctry, "Site/Location": site, "latitude (as reported)": lar,
                       "longitude (as reported)": lor, "latitude": la, "longitude": lo, "Coordinates source": src, "CLIMATE": cl, "Notes": note})
TM = [
    (179, "Ahmad N. et al.", None, "CT0", "Puddled TPR + conventional wheat (disc + 2 cultivations + 2 plankings), residue removed", "Puddled TPR", "Conventional", "No", None, "CT", "Conventional both phases", "High", "INCLUDED"),
    (179, "Ahmad N. et al.", None, "CTR", "As CT0 with residue retention", "Puddled TPR", "Conventional", "Yes", None, "CTR", "Conventional + residue", "High", "INCLUDED"),
    (179, "Ahmad N. et al.", None, "NT0", "No-till DSR (inclined-plate drill) + zero-till wheat (Happy Seeder), residue removed", "No-till DSR", "Zero till", "No", None, "ZT", "Zero till both phases", "High", "INCLUDED"),
    (179, "Ahmad N. et al.", None, "NTR", "As NT0 with residue retention", "No-till DSR", "Zero till", "Yes", None, "CA", "ZT + residue", "High", "INCLUDED"),
    (180, "Mann R.A. et al.", 2008, "Zero tillage", "Wheat drilled with zero-till drill into combine-harvested rice stubble (stubble left as mulch)", "Not stated", "Zero till", "Stubble only (not a treatment)", None, "ZT", "Rule 23; stubble not coded (rule 104) - ask (rule 18?)", "Medium", "INCLUDED - FLAG"),
    (180, "Mann R.A. et al.", 2008, "Conventional", "Rototiller 1 pass + cultivator 4 passes + planking 2 passes, broadcast", "Not stated", "Conventional", "No", None, "CT", "Rule 23", "High", "INCLUDED"),
    (180, "Mann R.A. et al.", 2008, "Beds (two rows) / Beds (three rows)", "Wheat on raised beds (exp. 2); bed formation not described", "Not stated", "Raised beds", "Not stated", None, "EXCLUDED (pending)", "Fresh beds MT (rule 15) or CT (rule 98)? - ask", "Low", "PENDING AUTHOR"),
    ("24 (companion 2)", "Choudhary M. et al.", 2018, "T1 / T2", "Puddled TPR + CT wheat, residue removed; FP / RDF", "Puddled", "Conventional", "No", None, "CT", "T1 row a (old-master 24); T2 row b (rule 33)", "High", "INCLUDED"),
    ("24 (companion 2)", "Choudhary M. et al.", 2018, "T4 / T3", "CT + 100 % rice + 33 % wheat residue incorporated / CT + mungbean, mungbean residue incorporated", "Puddled", "Conventional", "Yes - incorporated", "26.50 / 5.52", "CTR", "T4 rows a, b, d; T3 row c (mungbean flag)", "High", "INCLUDED"),
    ("24 (companion 2)", "Choudhary M. et al.", 2018, "T5 / T6", "ZT DSR + ZT wheat, residue removed; FP / RDF", "Zero till DSR", "Zero till", "No", None, "ZT", "T5 row a; T6 row b (rule 33)", "High", "INCLUDED"),
    ("24 (companion 2)", "Choudhary M. et al.", 2018, "T9 / T8 / T7 / T10", "ZT DSR + ZT wheat: rice + wheat residue / rice residue only / relay mungbean + its residue / all residues + mungbean", "Zero till DSR", "Zero till", "Yes - surface", "24.53 / 18.39 / 4.56 / 30.95", "CA", "T9 row a (old-master 24); T8 row b; T7 row c; T10 row d (rules 20 / 71; mungbean flag)", "High", "INCLUDED - FLAG (rows b-d new)"),
    ("24 (companion 2)", "Choudhary M. et al.", 2018, "T11-T14", "Maize-wheat (-mungbean), CT or ZT / permanent beds", "n/a (maize)", "CT / ZT", "Varies", None, "EXCLUDED", "Not rice-wheat (rule 31)", "High", "EXCLUDED"),
    ("159 (companion)", "Dutta A. et al.", 2023, "CT-NR / CT-RB", "Conventional tillage, residue removed / burnt", "Puddled TPR (per 159)", "Conventional", "No (removed / burnt)", None, "CT", "Rows a / b", "High", "INCLUDED"),
    ("159 (companion)", "Dutta A. et al.", 2023, "CT-R", "Conventional tillage + 40 % residue retention", "Puddled TPR (per 159)", "Conventional", "Yes (40 %)", None, "CTR", "Both rows", "High", "INCLUDED"),
    ("159 (companion)", "Dutta A. et al.", 2023, "ZT-NR / ZT-RB", "Zero tillage, residue removed / burnt", "Puddled TPR (per 159)", "Zero till", "No", None, "pZT", "Partial code (rules 68 / 85 / 89)", "Medium", "INCLUDED - FLAG"),
    ("159 (companion)", "Dutta A. et al.", 2023, "ZT-R", "Zero tillage + 40 % residue retention", "Puddled TPR (per 159)", "Zero till", "Yes (40 %)", None, "pCA", "Partial code", "Medium", "INCLUDED - FLAG"),
    ("159 (companion)", "Dutta A. et al.", 2023, "ST-NR / ST-RB", "Strip tillage, residue removed / burnt", "Puddled TPR (per 159)", "Strip till", "No", None, "pMT", "Strip = MT (rule 16), partial", "Medium", "INCLUDED - FLAG"),
    ("159 (companion)", "Dutta A. et al.", 2023, "ST-R", "Strip tillage + 40 % residue retention", "Puddled TPR (per 159)", "Strip till", "Yes (40 %)", None, "pMTR", "Strip + residue = MTR (rule 16), partial", "Medium", "INCLUDED - FLAG"),
    ("173 (companion)", "Biswakarma N. et al.", 2023, "ICM1-ICM8", "As study 173", "As 173", "As 173", "As 173", None, "DT / CT / CA", "Duplicate re-submission (rule 6) - coding of 173", "High", "INCLUDED - DUPLICATE FLAG"),
]
th = ["SERIAL NO", "Authors", "Year", "Paper's treatment label (verbatim)", "Full description from paper", "Rice-phase tillage", "Wheat-phase tillage",
      "Residue retained?", "Residue rate (t/ha)", "ASSIGNED CODE", "Rationale", "Confidence", "Status"]
for row in TM:
    d = dict(zip(th, row))
    d["No."] = row[0]
    B.add("Treatment_Mapping", d)
for ser, au, yr, why in (
        (179, "Ahmad N. et al.", None, "Figs S6-S7 MWD / GMD: box plots pooled over all treatments (rice vs wheat season only) - no treatment means (rule 119). Rice-season SOC and "
         "mineralisation values in Notes (rule 35). Table S2 mineralizability (no sheet) in Study_Info Notes."),
        (180, "Mann R.A. et al.", 2008, "Experiment 2 bed treatments (beds two rows 3.92 / 5.27 / 4.60, mean 4.60 t/ha; beds three rows 4.25 / 4.70 / 4.37, mean 4.42) - "
         "bed formation not described; pending author (MT rule 15 vs CT rule 98). Weeds, stem borer, predators: no sheet."),
        ("24 (companion 2)", "Choudhary M. et al.", 2018, "T11-T14 maize-wheat (rule 31). Microarthropods / QBS (Tables 4-5): no sheet."),
        ("173 (companion)", "Biswakarma N. et al.", 2023, "Whole study duplicated from 173 (rule 6) - delete these rows if the upload was a mistake (127_real.pdf vs 127.docx).")):
    B.add("EXCLUDED_rows", {"Sheet": "(treatments)", "SERIAL NO": ser, "Authors": au, "Year": yr, "Reason for exclusion": why, "Full row (header = value)": "-"})
B.save(OUT)
print("batch 16 written to", OUT)
