"""Batch 11 (2026-10-05) = batch 10 re-entered with the author decisions of 2026-10-05 (compost -> CTR; ICM1/2 -> DT, ICM3/4 -> CT).
Uploaded files 120_real.pdf, 120.pdf, 121_real.pdf, 121_now.pdf.

  171               Ghimire R. et al. 2012 (Paddy Water Environ. 10:95-102)          - Chitwan, Nepal: CT / CTR / ZT / CA (tillage x residue, N timing pooled); SOC stock 5 layers
  172               Tirol-Padre A. et al. 2005 (Soil Sci. Plant Nutr. 51:849-860)     - Fukuoka LTE (1963): +N tier CT (urea) vs CTR (rice straw row a / wheat straw row b / rice-straw compost row c); red soil rows
  124 (companion)   Hoque M.A. et al. 2023 (Field Crops Res. 291:108791)             - re-entry of old-master 124: AT (puddled rice + strip-tilled wheat + residue) = pMTR (rules 85/86)
  173               Biswakarma N. et al. 2023 (Agric. Ecosyst. Environ. 357:108675)   - IARI ICM trial: ICM1/2 DT (chisel 30 cm), ICM3/4 CT, ICM5-8 CA (rows a-d); red soil rows

Every row records the paper's method in 'Method used (from paper)'.
Usage: python batches/batch_11.py <in.xlsx> <out.xlsx>
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


# =====================================================================================
# 171  GHIMIRE et al. 2012 Paddy Water Environ.
# =====================================================================================
GH_TRT = ("TREATMENTS IN PAPER (IAAS Rampur, Chitwan; factorial RCBD, 3 reps, 3 x 5 m plots; Nov 2002 - Mar 2006 phase of a trial under no-till since 1999, "
          "split into CT / NT for wheat 2001-02): T0 no-tillage (surface seeding of all crops; rice, wheat and mungbean) vs T1 conventional tillage (mould-board / disc "
          "15-20 cm + cultivation; rice puddled) x M0 no residue (roots only) vs M1 residue 4 Mg/ha per crop (rice straw to wheat and mungbean, wheat straw to rice; "
          "12 Mg/ha/yr) x N1 recommended N timing vs N2 leaf-colour-chart N in rice. Mungbean cover crop between wheat and rice in ALL plots.")
GH = {"No.": 171, "SERIAL NO": 171, "Authors": "Ghimire R., Adhikari K.R., Chen Z.-S., Shah S.C. & Dahal K.R.", "Year": 2012, "Journal": "Paddy and Water Environment",
      "Country": "Nepal", "Site/Location": "IAAS Rampur campus farm, Chitwan Valley (inner Terai)", "latitude": 27.647, "longitude": 84.346, "CLIMATE": "ST",
      "SOIL": "LOAMY", "Rep": 3, "RAIN FALL": 2000, "LATT": 27.647, "ph (initial)": 5.4, "sand": 57, "silt": 19, "CLAY": 24,
      "year of data collection/experiment": 2006, "DURATION": "4-10 Y", "YEAR OF DATA (duration)": "4.5 (CT/NT split 2001-02; factorial from Nov 2002)",
      "Treatment mapping (paper's name -> code)": "T1M0 -> CT ; T1M1 -> CTR ; T0M0 -> ZT ; T0M1 -> CA (N1/N2 pooled in Table 4)",
      "Fertilizer dose & other management": ("Rice (Sabitri) 100-60-40 and wheat (BL 1473) 100-40-40 kg N-P2O5-K2O/ha; N1 = recommended splits (rice 50/25/25, wheat 50/50), "
                                             "N2 = LCC-based N in rice; basal N at puddling (CT) or 12 DAS (NT). Rice 20 x 15 cm, wheat 20-cm rows (seed dipped in cow-dung in NT), "
                                             "mungbean broadcast unfertilised. Sandy clay loam Typic Haplustoll, pH 5.4-6.0, OC 13.4-15.5 g/kg."),
      "Crop/season of sampling": "Wheat season - after wheat harvest, March 2006",
      "Treatment details (from paper)": GH_TRT}
GH_NOTE = ("TILLAGE x RESIDUE cell means POOLED OVER the two N-timing treatments (Table 4; flag). THIRD CROP: mungbean cover crop in every plot (rule 71). BD not different "
           "among treatments - the paper used one mean BD 1.07 Mg/m3 (SD 0.11) for all stocks. Main effects (Table 3, not entered): T0 / T1 0-5 11.8 / 9.20, 5-10 11.2 / 9.94, "
           "10-15 11.8 / 10.5, 15-30 21.6 / 23.7, 30-50 23.6 / 23.2, 0-50 82.2 / 74.8 Mg C/ha; M0 / M1 0-50 77.1 / 79.9; N1 / N2 0-50 76.5 / 80.5. Sequestration rates printed "
           "by the paper are RELATIVE TO CT (not vs initial): NT 0.59 (0-5 cm), NT+R vs CT-R 0.73 / 0.37 / 0.48 Mg C/ha/yr (0-5 / 5-10 / 10-15 cm). Supplementary: " + SUPP +
           ". Source file 120_real.pdf.")
GSTK = {"0-5": (9.50, 9.90, 10.9, 12.7), "5-10": (10.0, 9.87, 10.8, 11.6), "10-15": (10.1, 10.8, 11.3, 12.2), "15-30": (21.3, 21.9, 23.0, 24.3), "30-50": (23.9, 22.3, 21.9, 25.3)}
GCOD = ("CT", "CTR", "ZT", "CA")
GLAY = [("0-5", "0-15 CM", 3, 5), ("5-10", "0-15 CM", 3, 5), ("10-15", "0-15 CM", 3, 5), ("15-30", "15-30 CM", 1, 15), ("30-50", "30-45 CM", 1, 20)]
for lay, cls, D, th in GLAY:
    v = GSTK[lay]
    put("SOC(active C pool)", {**GH, "DEPTH": cls, "DEPTH (as reported in paper)": f"{lay} cm", "Obs": 2 + (D if D > 1 else 0)},
        {c: f"=ROUND({s}/(1.07*{th}*0.1),2)" for c, s in zip(GCOD, v)}, "SOC_", UNIT="g/kg (DERIVED: printed stock / (1.07 x thickness x 0.1))",
        **{"Data source": "Table 4 - DERIVED", "Method used (from paper)": "Graham (1948) colorimetric organic C; tube auger 2.5 cm, 5 cores per plot; stock = BD x C x depth with one mean BD 1.07 Mg/m3",
           "Notes/Doubts": (f"DERIVED concentration: printed layer stock (Mg C/ha) CT {v[0]}, CTR {v[1]}, ZT {v[2]}, CA {v[3]} back-calculated with the paper's single BD 1.07 and "
                            f"{th} cm (exact inverse of the paper's formula). " + ("30-50 cm assigned to 30-45 CM by maximum overlap. " if lay == "30-50" else "")
                            + f"Obs = T2 (N pooled)" + (f" + D{D}" if D > 1 else "") + ". " + GH_NOTE)})
for cum, lays, rep in (("0-10 CM", ["0-5", "5-10"], "0-5 + 5-10 cm"), ("0-20 CM", ["0-5", "5-10", "10-15"], "0-15 cm (3 layers; class 0-20 CM)"),
                       ("0-30 CM", ["0-5", "5-10", "10-15", "15-30"], "0-30 cm (4 layers)")):
    put("stock-SOC", {**GH, "DEPTH": cum, "DEPTH (as reported in paper)": rep, "Obs": 2},
        {c: "=" + "+".join(str(GSTK[l][i]) for l in lays) for i, c in enumerate(GCOD)}, "SOCs_", UNIT="Mg C/ha",
        **{"Data source": "Table 4 (layer stocks summed)", "Method used (from paper)": "Stock = BD x Corg x D x A (Shofiyati et al. 2010) with BD 1.07 Mg/m3; cumulative sums of the printed layer stocks",
           "Notes/Doubts": "Printed layer stocks summed (live formula). 0-5 cm alone (class 0-10 CM): CT 9.50, CTR 9.90, ZT 10.9, CA 12.7. " + GH_NOTE})
put("stock-SOC", {**GH, "DEPTH": "0-50 CM", "DEPTH (as reported in paper)": "0-50 cm (printed total)", "Obs": 2}, dict(zip(GCOD, (76.1, 73.4, 77.9, 86.4))), "SOCs_",
    UNIT="Mg C/ha", **{"Data source": "Table 4", "Method used (from paper)": "Stock = BD x Corg x D x A with BD 1.07 Mg/m3 (0-50 cm as printed)",
                       "Notes/Doubts": "Printed 0-50 cm totals (differ slightly from the sum of the printed layers, e.g. CT 74.8 by summing - per-replicate computation). " + GH_NOTE})

# =====================================================================================
# 172  TIROL-PADRE et al. 2005 Soil Sci. Plant Nutr.
# =====================================================================================
TP_TRT = ("TREATMENTS IN PAPER (Kyushu National Agricultural Experiment Station LTE, Chikugo, Fukuoka; rice-wheat since 1963; residues incorporated at puddling in mid-June): "
          "1 unfertilised control, 2 70 kg N/ha urea, 3 rice straw 10 Mg/ha, 4 rice straw + N, 5 rice-straw compost 20 Mg/ha, 6 compost + N, 7 Italian ryegrass 8 Mg/ha (1963-84) "
          "then wheat straw 10 Mg/ha (1985-93) and 6 Mg/ha (1994-2003), 8 = 7 + N. ENTERED (+N tier): row a CT = urea N only vs CTR = rice straw + N; row b CT = urea N vs "
          "CTR = wheat straw + N; row c CT = urea N vs CTR = rice-straw compost + N (author 2026-10-05). NOT ENTERED: -N tier (unfertilised control as CT, rule 78).")
TP = {"No.": 172, "SERIAL NO": 172, "Authors": "Tirol-Padre A., Tsuchiya K., Inubushi K. & Ladha J.K.", "Year": 2005, "Journal": "Soil Science and Plant Nutrition",
      "Country": "Japan (Fukuoka)", "Site/Location": "Kyushu National Agricultural Experiment Station (NARC/KOR), Chikugo, Fukuoka - long-term rice-wheat experiment",
      "latitude": 33.2, "longitude": 130.5, "CLIMATE": "TEMP", "SOIL": "LOAMY", "Rep": 3, "LATT": 33.2, "sand": 16, "silt": 56, "CLAY": 29,
      "Treatment mapping (paper's name -> code)": "+N tier: urea N only -> CT ; rice straw 10 Mg/ha + N -> CTR (row a) ; ryegrass/wheat straw + N -> CTR (row b) ; rice-straw compost 20 Mg/ha + N -> CTR (row c, author 2026-10-05) ; -N tier not entered",
      "Fertilizer dose & other management": ("70 kg N/ha urea in +N plots; straw / compost incorporated at puddling (mid-June) before transplanted rice; wheat in winter (management "
                                             "not described). Gray Lowland soil (29 % clay, 56 % silt, 16 % sand). Residue C input: rice straw 3,480 kg C/ha/yr; wheat straw "
                                             "2,496 kg C/ha/yr (6 Mg/ha period)."),
      "Treatment details (from paper)": TP_TRT}
TP_NOTE = ("CONVENTIONAL puddled rice in all plots (residue contrast only). Row b CTR = Italian ryegrass 1963-84 then wheat straw (flag). Row c CTR = rice-straw COMPOST "
           "20 Mg/ha (composted residue counted as CTR - author 2026-10-05; flag). NOT ENTERED: -N tier (unfertilised control as CT, rule 78); its values are in each row's Notes. Sampling depth not stated - plough "
           "layer, class 0-15 CM assumed (flag); the paper uses BD = 1 g/cm3 for its own stock calculations. Coordinates approximate (Chikugo city). Supplementary: " + SUPP +
           ". Source file 120.pdf.")
TP_RED = "RICE-SEASON DATA (RED ROW): soil sampled after rice harvest, October 2003 (40th year). "
TROWS = [("a", "RS", "rice straw 10 Mg/ha + N"), ("b", "WS", "ryegrass/wheat straw + N"), ("c", "RSC", "rice-straw compost 20 Mg/ha + N")]
TPBASE = {**TP, "year of data collection/experiment": 2003, "DURATION": ">10 Y", "YEAR OF DATA (duration)": 40,
          "DEPTH": "0-15 CM", "DEPTH (as reported in paper)": "plough layer (depth not stated)", "Obs": 2,
          "Crop/season of sampling": "RICE SEASON - after rice harvest, October 2003"}
# (+N values: control/N, RS, RSC, WS) and (-N values) per parameter
TPD = {
    "pH": ((5.4, 5.3, 5.3, 5.2), (5.7, 5.5, 5.4, 5.5)),
    "OlsenP": ((7.9, 9.1, 8.9, 10.8), (7.9, 8.9, 8.6, 10.7)),
    "ExK": ((10.5, 19.1, 11.7, 16.0), (16.3, 20.9, 16.3, 21.4)),
    "CEC": ((17.4, 18.3, 19.8, 18.2), (17.0, 18.1, 19.8, 18.0)),
    "TC": ((21.43, 25.70, 30.10, 25.80), (19.90, 24.90, 28.50, 25.10)),
    "OC": ((19.07, 23.13, 27.07, 23.70), (18.10, 22.90, 25.93, 23.27)),
    "TN": ((1.93, 2.34, 2.76, 2.36), (1.82, 2.25, 2.59, 2.24)),
    "MBCa": ((0.83, 1.07, 1.20, 1.09), (0.71, 1.08, 1.21, 1.04)),
    "MBCf": ((0.59, 0.74, 0.85, 0.85), (0.64, 0.67, 0.84, 0.79)),
    "RESPa": ((8.6, 11.6, 12.4, 11.4), (9.7, 11.4, 12.4, 11.4)),
    "RESPf": ((13.7, 17.8, 9.1, 14.1), (28.0, 15.6, 26.6, 14.0)),
    "HWEC": ((0.44, 0.58, 0.67, 0.58), (0.38, 0.56, 0.58, 0.59)),
    "PMNa": ((46.9, 66.2, 66.6, 64.1), (50.1, 58.6, 61.1, 58.3)),
    "PMNf": ((53, 101, 121, 80), (51, 105, 103, 99)),
    "POC": ((3.05, 4.03, 5.11, 3.77), (2.92, 3.99, 4.88, 3.91)),
}
TPI = {"RS": 1, "RSC": 2, "WS": 3}


def tpn(key):
    p, m = TPD[key]
    return (f"All cells (+N: N-only / RS / compost / WS = {p[0]} / {p[1]} / {p[2]} / {p[3]}; -N: control / RS / compost / WS = {m[0]} / {m[1]} / {m[2]} / {m[3]}). ")


TPS = [  # sheet, key, prefix, unit, formula(value) , source, method
    ("PH", "pH", "PH_", "pH (1:1 soil:water)", lambda v: v, "Table 2", "pH in 1:1 soil:water suspension"),
    ("P", "OlsenP", "P_", "kg/ha (printed Olsen P mg/100 g x 10 = mg/kg x BD 1.0 x 15 cm x 0.1 - ASSUMED depth/BD)", lambda v: f"=ROUND({v}*10*1.0*15*0.1,1)", "Table 2 - converted", "Olsen et al. (1954) NaHCO3-P"),
    ("EX-K", "ExK", "EXK_", "mg/kg (printed mg/100 g x 10)", lambda v: f"=ROUND({v}*10,1)", "Table 2 - converted", "Exchangeable K (Knudsen et al. 1982), NH4OAc"),
    ("CEC", "CEC", "CEC_", "cmol(+)/kg (printed meq/100 g)", lambda v: v, "Table 2", "NH4OAc at pH 7"),
    ("TC(total c)", "TC", "TC_", "g/kg (printed mg/g)", lambda v: v, "Table 3", "Automated dry combustion, Perkin-Elmer 2400 CHN analyser"),
    ("SOC(active C pool)", "OC", "SOC_", "g/kg (printed mg/g; organic C by dry combustion after HCl removal of carbonates)", lambda v: v, "Table 3",
     "Dry combustion (Perkin-Elmer 2400 CHN) after 15 % HCl in silver capsules (carbonate removal)"),
    ("total N", "TN", "TN_", "mg/kg (printed mg/g x 1000)", lambda v: f"=ROUND({v}*1000,0)", "Table 3 - converted", "Automated dry combustion, Perkin-Elmer 2400 CHN analyser"),
    ("WSC", "HWEC", "WSC_", "mg/kg (HOT-WATER-extractable C; printed mg/g x 1000)", lambda v: f"=ROUND({v}*1000,0)", "Table 8 - converted",
     "Hot-water extractable C: 20 g soil + 100 mL water boiled under reflux 1 h, centrifuged, TOC analyser (OI 1020A)"),
    ("POXC(KMnO4-C)", "POC", "POXC_", "mg/kg (printed mg/g x 1000)", lambda v: f"=ROUND({v}*1000,0)", "Table 10 - converted", "Permanganate-oxidisable C (Tirol-Padre & Ladha 2004)"),
]
for sheet, key, pre, unit, f, src, meth in TPS:
    p = TPD[key][0]
    for row, tr, lab in TROWS:
        put(sheet, TPBASE, {"CT": f(p[0]), "CTR": f(p[TPI[tr]])}, pre, red=True, UNIT=unit,
            **{"Data source": src, "Method used (from paper)": meth + "; air-dried soil after rice harvest 2003",
               "Notes/Doubts": TP_RED + f"ROW {row}: CTR = {lab}. " + tpn(key) + TP_NOTE})
for key, cond in (("MBCa", "aerobic (50 % WFPS)"), ("MBCf", "flooded")):
    p = TPD[key][0]
    for row, tr, lab in TROWS:
        put("MBC", TPBASE, {"CT": f"=ROUND({p[0]}*1000,0)", "CTR": f"=ROUND({p[TPI[tr]]}*1000,0)"}, "MBC_", red=True, UNIT=f"ug C/g soil (printed mg/g x 1000) - after 31-d {cond} incubation",
            **{"Data source": "Table 5 - converted", "Method used (from paper)": f"Fumigation-extraction (Inubushi et al. 1991), K2SO4 extracts on TOC analyser, after 31 d {cond} pre-incubation of air-dried soil at 25 C",
               "Notes/Doubts": TP_RED + f"ROW {row}: CTR = {lab}. Incubation-condition row ({cond}; lab incubation of air-dried soil, flag). " + tpn(key) + TP_NOTE})
for key, cond in (("RESPa", "aerobic (50 % WFPS)"), ("RESPf", "flooded")):
    p = TPD[key][0]
    for row, tr, lab in TROWS:
        put("RESP", TPBASE, {"CT": f"=ROUND({p[0]}*44/12,1)", "CTR": f"=ROUND({p[TPI[tr]]}*44/12,1)"}, "RESP_", red=True,
            UNIT=f"mg CO2/kg soil/day (printed mg C x 44/12) - basal respiration, {cond}",
            **{"Data source": "Table 6 - converted", "Method used (from paper)": f"CO2 trapped in 5 M NaOH for 24 h after 30 d {cond} incubation at 25 C, released with HCl, GC-TCD",
               "Notes/Doubts": (TP_RED + f"ROW {row}: CTR = {lab}. Incubation-condition row ({cond}). " + tpn(key)
                                + "qCO2 (ug CO2-C/mg MBC/h) +N aerobic N 0.36 / RS 0.46 / RSC 0.44 / WS 0.45, flooded 0.99 / 1.08 / 0.46 / 0.69; 3-d CO2 flush after rewetting "
                                  "(mg C/kg) +N aerobic 408 / 444 / 431 / 449, flooded 47.4 / 57.3 / 77.6 / 69.8. " + TP_NOTE)})
for key, cond in (("PMNa", "aerobic (50 % WFPS)"), ("PMNf", "flooded")):
    p = TPD[key][0]
    for row, tr, lab in TROWS:
        put("no3,nh4,PMN", TPBASE, {"CT": f"=ROUND({p[0]}*1.0*15*0.1,1)", "CTR": f"=ROUND({p[TPI[tr]]}*1.0*15*0.1,1)"}, "PMN_", red=True,
            UNIT=f"kg/ha (printed mg/kg x BD 1.0 x 15 cm x 0.1 - ASSUMED) - potentially mineralisable N, 31-d {cond} incubation",
            **{"Data source": "Table 9 - converted", "Method used (from paper)": f"(NH4+ + NO3-) in K2SO4 extract after 31 d {cond} incubation minus initial available N; salicylate (NH4) and Cd-reduction (NO3)",
               "Notes/Doubts": TP_RED + f"ROW {row}: CTR = {lab}. Printed mg/kg: " + tpn(key) + "Conversion uses the paper's BD 1 g/cm3 and an assumed 15 cm layer (flag). " + TP_NOTE})
# Yields: Fig. 1 (+N panel) year-wise, Table 11 mean and N uptake in Notes / N uptake row
tf = json.load(open(os.path.join(DIG, "tirolpadre2005_fig1.json")))
RSC_VIS = {1989: 5.82, 1996: 6.40, 2000: 6.40, 2003: 5.95}  # RSC+N triangles visible in Fig. 1 (others hidden under other markers - not read)
for i, yr in enumerate(tf["years"]):
    for row, tr, lab in TROWS:
        if tr == "RSC" and yr not in RSC_VIS:
            continue
        hid = [s for s in ("C+N", tr + "+N") if yr in tf["hidden"].get(s, [])]
        B.add("YIELD", {**TP, "year of data collection/experiment": yr, "DURATION": ">10 Y", "YEAR OF DATA (duration)": yr - 1963, "Obs": 2,
                        "RICE YIELD_CT": tf["C+N"][i], "RICE YIELD_CTR": RSC_VIS[yr] if tr == "RSC" else tf[tr + "+N"][i], "UNIT": "t/ha rice grain (15 % moisture)",
                        "Crop/season of sampling": f"Rice {yr} (LTE year {yr - 1963})", "Data source": "Fig. 1 upper panel (digitised, scanned)",
                        "Method used (from paper)": "Grain from 60 hills (2.4 m2) per plot, 15 % moisture",
                        "Notes/Doubts": (f"ROW {row}: CTR = {lab}. Year-wise (rule 37). DIGITISED by hand from the scanned Fig. 1 (+/-0.15 t/ha)"
                                         + ("; compost (triangle) entered only for the 4 years where its marker is visible (1989, 1996, 2000, 2003)" if tr == "RSC" else "")
                                         + (f"; marker partly hidden for {', '.join(hid)} (flag)" if hid else "") + ". Means of the digitised years agree with Table 11 "
                                         "(+N: N-only 5.1, RS 5.7, compost 5.7, WS 5.5 t/ha; -N: control 3.5, RS 4.1, compost 4.7, WS 4.2). Wheat yields not reported. " + TP_NOTE)})
for row, tr, lab in TROWS:
    B.add("N uptake", {**TP, "year of data collection/experiment": "multi-year mean (years not stated; Fig. 1 covers 1989-2003)", "DURATION": ">10 Y",
                       "YEAR OF DATA (duration)": "26-40 (mean)", "Obs": 2, "NU_CT": 100, "NU_CTR": {"RS": 118, "WS": 113, "RSC": 120}[tr],
                       "UNIT": "kg N/ha (rice plant N uptake)", "Crop/season of sampling": "Rice, multi-year mean", "Data source": "Table 11",
                       "Method used (from paper)": "Plant N uptake (method not detailed)",
                       "Notes/Doubts": f"ROW {row}: CTR = {lab}. Rice crop only. All cells: +N N-only 100, RS 118, compost 120, WS 113; -N control 58, RS 73, compost 83, WS 77 kg N/ha. " + TP_NOTE})

# =====================================================================================
# 124 (companion)  HOQUE et al. 2023 Field Crops Res. - AT = pMTR
# =====================================================================================
hf = json.load(open(os.path.join(DIG, "hoque_fig4.json")))
HO_TRT = ("TREATMENTS IN PAPER (BARI RARS Jamalpur, 2013-2016, split plot, 4 reps; 6 cropping systems x 3 tillage): CA = monsoon rice transplanted into UNTILLED unpuddled soil, "
          "wheat (and mungbean) strip-tilled into ~25 cm stubble (~3 t/ha) -> MTR (as old-master 124) ; AT = PUDDLED transplanted rice, winter / spring crops strip-tilled into "
          "~25 cm stubble with residue -> pMTR (NEW, rules 68 / 85 / 86) ; CT = puddled rice, 3-5 tillage passes for winter crops, ~0.7 t/ha stubble incorporated -> CT. "
          "R-W = row a, R-W-MB = row b; R-R, R-M, R-MB, R-M-MB not rice-wheat.")
HO = {"No.": "124 (companion)", "SERIAL NO": "124 (companion)", "Authors": "Hoque M.A., Gathala M.K., Timsina J., Ziauddin M.A.T.M., Hossain M. & Krupnik T.J.",
      "Year": 2023, "Journal": "Field Crops Research", "Country": "Bangladesh", "Site/Location": "BARI Regional Agricultural Research Station, Jamalpur (AEZ 9, Old Brahmaputra Floodplain)",
      "latitude": 24.942, "longitude": 89.928, "CLIMATE": "ST", "SOIL": "LOAMY", "Rep": 4, "LATT": 24.942, "ph (initial)": 6.2, "sand": 47.3, "silt": 30, "CLAY": 22.7,
      "year of data collection/experiment": "2013-14 to 2015-16 (3-yr mean)", "DURATION": "0-3 Y", "YEAR OF DATA (duration)": 3, "Obs": 3,
      "Treatment mapping (paper's name -> code)": "CT -> CT ; CA (unpuddled untilled rice + strip-tilled wheat + residue) -> MTR ; AT (puddled rice + strip-tilled wheat + residue) -> pMTR",
      "Fertilizer dose & other management": ("BARC FRG 2018: long-duration aman rice (BR-11) 81-25-30-36, short-duration aman (BINA dhan-7, triple systems) 68-22-25-30, wheat (BARI Gom-26) "
                                             "100-24-50-110 kg N-P-K-S/ha; aman rice rainfed (+180 mm for puddling); wheat up to 4 irrigations (115-189 mm); glyphosate + pretilachlor in CA."),
      "Treatment details (from paper)": HO_TRT}
HO_NOTE = ("RE-ENTRY of old-master 124 (same paper) for the AT treatment, excluded there as a rotation mismatch and now pMTR (rules 85 / 86, author confirmed). DUPLICATE FLAG: "
           "the CT and MTR values repeat old-master 124 exactly (kept so that pMTR has its comparison in the same row) - when merging use these rows for the pMTR contrasts only. "
           "Cell values exist only as violin plots: AT digitised as the violin area-centroid (Fig. 4 raster, this batch: the same procedure reproduces the old-master CT / CA values within "
           "+/-3 US$/ha); AT system yield from the old-master Notes (Fig. 3 vector). Obs = Y3, Rep 4. System calorie and protein yields (Fig. 3) have no sheet. Supplementary Tables S1-S3 "
           "not reachable - " + SUPP + ". Source file 121_real.pdf.")
for row, cs, sy, gm, cost, third in (("a", "R-W", (9.51, 10.2, 10.21), (586, 719), (1097, 1099), ""),
                                     ("b", "R-W-MB", (13.24, 14.69, 14.62), (938, 1174), (1454, 1461), "THIRD CROP: spring mungbean in every tillage treatment (flag). ")):
    at_gm, at_cost = hf["gross_margin"][cs]["AT"], hf["production_cost"][cs]["AT"]
    lab = hf["labour_use"][cs]
    base = {**HO, "Crop/season of sampling": f"{cs} system, 3-yr mean"}
    nt = f"ROW {row}: {cs}. " + third
    B.add("YIELD", {**base, "SYS YIELD_CT": sy[0], "SYS YIELD_MTR": sy[1], "SYS YIELD_pMTR": sy[2], "UNIT": "t/ha system rice-equivalent yield (SREY)",
                    "Data source": "Fig. 3 (violin centroid; old-master 124 digitisation)",
                    "Method used (from paper)": "18-m2 harvest per plot; rice / wheat grain at 14 % moisture, mungbean 12 %; REY = yield x crop price / price of BR-11 rice; SREY = sum of crops",
                    "Notes/Doubts": nt + HO_NOTE})
    B.add("NET RETURN", {**base, "NR_SYSCT": gm[0], "NR_SYSMTR": gm[1], "NR_SYSpMTR": at_gm, "UNIT": "US$/ha (1 US$ = 84 BDT) - GROSS MARGIN (gross return - total variable cost)",
                         "Data source": "Fig. 4 (violin centroid, digitised raster)",
                         "Method used (from paper)": "Gross margin = gross return (grain + straw at local market prices) - total variable cost (land rent, labour, tillage, machinery, seed, fertiliser, agro-chemicals, irrigation, harvest, threshing)",
                         "Notes/Doubts": (nt + f"FLAG: GROSS MARGIN (variable-cost basis). System labour use (person-days/ha, Fig. 4) CT {lab['CT']}, CA {lab['CA']}, AT {lab['AT']} (no sheet). " + HO_NOTE)})
    B.add("BC ratio", {**base, "BC_SYSCT": f"=ROUND({gm[0]}/{cost[0]},3)", "BC_SYSMTR": f"=ROUND({gm[1]}/{cost[1]},3)", "BC_SYSpMTR": f"=ROUND({at_gm}/{at_cost},3)",
                       "UNIT": "ratio (gross margin / total production cost; both digitised)", "Data source": "Fig. 4 (DERIVED)",
                       "Method used (from paper)": "DERIVED: digitised gross margin / digitised production cost (as old-master 124)",
                       "Notes/Doubts": nt + f"Production cost (US$/ha) CT {cost[0]}, MTR {cost[1]}, pMTR {at_cost}. " + HO_NOTE})

# =====================================================================================
# 173  BISWAKARMA et al. 2023 Agric. Ecosyst. Environ.
# =====================================================================================
BI_TRT = ("TREATMENTS IN PAPER (ICAR-IARI New Delhi, est. kharif 2015, RBD 3 reps, 12.5 x 4 m plots; 8 ICM modules): ICM1 puddled TPR + CT wheat (disc + 2 cultivator), 100 % RF, "
          "no residue -> DT (annual chisel ploughing 30 cm; author 2026-10-05) ; ICM2 = ICM1 with 75 % RF + NPK bio-fertiliser + AM fungi -> DT ; ICM3 / ICM4 direct-seeded rice after "
          "chisel ploughing (30 cm) + furrow-irrigated raised-bed wheat (beds made each year after disc + 2 cultivator), 100 % / 75 % RF + bf -> CT (author 2026-10-05) ; ICM5 / ICM6 ZT-DSR with wheat residue + ZT wheat "
          "with rice residue (~3 / ~5 Mg/ha), 100 % / 75 % RF + bf -> CA ; ICM7 / ICM8 = ICM5 / ICM6 + summer mungbean (~3 Mg/ha residue knocked down with paraquat) -> CA. "
          "Chisel ploughing (30 cm, 45-HP) every year before rice in ICM1-4, laser levelling, three puddlings (ICM1-2).")
BI = {"No.": 173, "SERIAL NO": 173, "Authors": ("Biswakarma N., Pooniya V., Zhiipao R.R., Kumar D., Shivay Y.S., Das T.K., Roy D., Das B., Choudhary A.K., Swarnalakshmi K., "
                                                "Govindasamy P., Lakhena K.K., Das K., Lama A., Jat R.D., Babu S., Khan S.A. & Behera B."),
      "Year": 2023, "Journal": "Agriculture, Ecosystems and Environment", "Country": "India (Delhi)", "Site/Location": "ICAR-IARI research farm, New Delhi (ICM trial, est. 2015)",
      "latitude": 28.633, "longitude": 77.15, "CLIMATE": "ST", "SOIL": "LOAMY", "Rep": 3, "RAIN FALL": 642, "LATT": 28.633, "MIN TEMP": 5, "MAX TEMP": 46,
      "soc (initial)": 4.9, "Bdi": 1.52,
      "Treatment mapping (paper's name -> code)": "rows pair the fertiliser level: a DT = ICM1, CT = ICM3, CA = ICM5 ; b DT = ICM2, CT = ICM4, CA = ICM6 ; c as a with CA = ICM7 (+mungbean) ; d as b with CA = ICM8 (+mungbean)",
      "Fertilizer dose & other management": ("RF rice 100-21.8-41.5, wheat 120-26-33 kg N-P-K/ha (ICM1,5,7); ICM2,6,8 75 % RF + liquid NPK bio-fertiliser (Azotobacter, Pseudomonas, "
                                             "Bacillus) + AM fungi 12 kg/ha. Rice Pusa basmati (DSR 3rd wk June; TPR 1st wk July 20 x 10 cm); wheat 20-cm rows. IWM per module (Table 2 footnote). "
                                             "Sandy clay loam; initial BD 1.52, SOC 4.9, TC 7.2 g/kg, N 169.5, P 11.5, K 275.3 kg/ha."),
      "Treatment details (from paper)": BI_TRT}
BI_NOTE = ("AUTHOR CODING 2026-10-05: ICM1/2 (chisel 30 cm every year + puddled TPR + CT wheat) -> DT; ICM3/4 (chisel-ploughed DSR + raised-bed wheat after disc + cultivator) -> CT "
           "(flag: the paper states chisel ploughing for ICM1-4 alike); ICM5-8 -> CA. ICM2/4/6/8 use 75 % RF + bio-fertiliser + AM (rows b / d, matched fertiliser level). "
           "ICM7/8: summer MUNGBEAN third crop + its residue (rows c / d; rule 71). Supplementary Tables S1-S7 not reachable - " + SUPP + ". Source file 121_now.pdf.")
BROWS = [("a", 0, 2, 4, "ICM1 / ICM3 / ICM5"), ("b", 1, 3, 5, "ICM2 / ICM4 / ICM6"), ("c", 0, 2, 6, "ICM1 / ICM3 / ICM7 (+mungbean)"), ("d", 1, 3, 7, "ICM2 / ICM4 / ICM8 (+mungbean)")]
BI_RED = "RICE-SEASON DATA (RED ROW): soil sampled at harvest of the 6th rice crop (2020); biological samples at rice flowering. "


def all8(v):
    return "All modules ICM1-8: " + " / ".join(str(x) for x in v) + ". "


# Table 3 WEY year-wise (with SD)
WEY = [(8.55, 8.52, 9.10, 8.92, 9.40, 9.17, 9.88, 9.52), (8.16, 7.80, 7.61, 7.62, 8.21, 8.39, 9.72, 9.41), (7.99, 7.66, 7.37, 7.36, 8.67, 8.18, 8.17, 9.05),
       (8.98, 8.69, 8.18, 7.22, 8.62, 8.71, 9.67, 9.92), (7.98, 7.92, 7.38, 7.56, 7.41, 7.73, 8.94, 8.72), (8.98, 8.75, 8.64, 8.52, 8.50, 8.67, 9.57, 9.51)]
WSD = [(0.18, 0.14, 0.09, 0.38, 0.27, 0.08, 0.24, 0.29), (0.25, 0.06, 0.22, 1.20, 0.56, 0.47, 0.13, 0.39), (0.25, 0.19, 0.10, 0.45, 0.39, 0.34, 0.22, 0.29),
       (0.33, 0.21, 1.35, 0.43, 0.35, 0.34, 0.33, 0.34), (0.65, 1.05, 0.91, 0.53, 0.78, 0.81, 0.69, 0.47), (0.55, 0.80, 0.85, 0.94, 0.89, 0.95, 0.62, 0.67)]
for j, yr in enumerate(("2015-16", "2016-17", "2017-18", "2018-19", "2019-20", "2020-21")):
    for row, dt, ct, ca, lab in BROWS:
        B.add("YIELD", {**BI, "year of data collection/experiment": yr, "DURATION": "0-3 Y" if j < 3 else "4-10 Y", "YEAR OF DATA (duration)": j + 1, "Obs": 2,
                        "SYS YIELD_DT": WEY[j][dt], "SYS YIELD_CT": WEY[j][ct], "SYS YIELD_CA": WEY[j][ca], "UNIT": "t/ha system WHEAT-EQUIVALENT yield (WEY)",
                        "Crop/season of sampling": f"Rice-wheat system {yr}", "Data source": "Table 3",
                        "Method used (from paper)": "18-m2 net plot harvest; WEY = Yw + (Yr x Pr) / Pw (Pooniya et al. 2021a)",
                        "Notes/Doubts": (f"ROW {row} ({lab}). Year-wise (rule 37). Paper SD: DT {WSD[j][dt]}, CT {WSD[j][ct]}, CA {WSD[j][ca]}. " + all8(WEY[j])
                                         + ("WEY formula includes rice and wheat only - mungbean grain not counted (rows c/d). " if row in "cd" else "") + BI_NOTE)})
# Tables 4-6: soil properties at 3 depths (rice season)
BD3 = [(1.52, 1.53, 1.54, 1.52, 1.50, 1.51, 1.48, 1.49), (1.55, 1.56, 1.56, 1.54, 1.52, 1.54, 1.50, 1.51), (1.59, 1.59, 1.59, 1.58, 1.58, 1.57, 1.56, 1.58)]
WSA3 = [(51.1, 50.8, 48.9, 49.3, 51.3, 50.5, 52.6, 53.5), (49.5, 48.7, 47.4, 47.1, 48.6, 47.7, 51.2, 50.2), (48.7, 48.0, 46.3, 47.2, 47.7, 46.2, 49.7, 49.6)]
VMC3 = [(11.6, 12.0, 11.3, 11.4, 12.1, 12.3, 14.2, 14.0), (12.9, 11.6, 12.9, 12.1, 13.0, 13.4, 15.1, 14.0), (15.1, 14.6, 12.6, 13.9, 14.1, 12.3, 16.1, 15.5)]
PR3 = [(2244, 2048, 1700, 1776, 1297, 1318, 1307, 1384), (2452, 2321, 2528, 2092, 2223, 1939, 1841, 1645), (2767, 2920, 2615, 2288, 2408, 2560, 2005, 1776)]
TC3 = [(9.90, 9.70, 8.76, 8.67, 10.7, 9.97, 10.9, 10.7), (9.31, 9.17, 7.98, 7.80, 9.42, 9.33, 9.79, 9.67), (8.49, 8.33, 7.05, 7.20, 9.00, 9.10, 8.60, 9.33)]
N3 = [(178.0, 172.7, 163.5, 167.5, 176.9, 175.9, 186.0, 179.1), (170.3, 168.0, 161.0, 164.0, 167.1, 162.7, 175.3, 173.4), (153.9, 149.1, 145.3, 140.7, 148.0, 141.7, 158.3, 154.3)]
P3 = [(13.0, 12.9, 12.4, 11.2, 12.7, 13.1, 14.1, 13.3), (11.6, 10.2, 10.2, 10.7, 11.1, 10.6, 12.8, 12.3), (10.8, 10.4, 9.5, 10.4, 10.8, 10.5, 12.0, 12.5)]
K3 = [(276, 268.4, 265.5, 272.1, 254.3, 265.0, 289.5, 277.7), (246.7, 241.3, 238.1, 241.3, 235.5, 239.9, 259.7, 252.7), (226.4, 235.1, 233.5, 231.6, 222.8, 235.7, 241.1, 246.9)]
APA3 = [(61.9, 64.5, 58.9, 62.9, 72.4, 79.7, 88.9, 87.6), (55.5, 52.9, 50.5, 55.0, 64.0, 68.2, 78.2, 81.1), (51.4, 44.8, 43.0, 42.5, 51.5, 48.6, 55.8, 53.3)]
DHA3 = [(21.7, 19.4, 23.5, 23.9, 25.4, 26.3, 32.5, 35.1), (17.7, 17.1, 16.8, 17.7, 21.4, 21.0, 27.3, 30.2), (16.5, 12.3, 12.3, 12.5, 14.4, 11.1, 14.9, 19.5)]
MBC3 = [(173.3, 169.3, 160.8, 166.8, 187.0, 155.2, 180.8, 209.8), (133.1, 116.4, 141.7, 141.6, 133.1, 157.6, 158.2, 157.0), (127.5, 139.0, 123.8, 123.8, 120.1, 135.0, 140.4, 143.4)]
UA3 = [(1.50, 1.43, 1.27, 1.01, 1.58, 1.55, 1.75, 1.61), (1.31, 1.34, 1.09, 1.31, 1.30, 1.16, 1.56, 1.47), (1.26, 1.19, 0.90, 1.13, 1.38, 1.41, 1.39, 1.28)]
SQI3 = [(0.51, 0.43, 0.32, 0.29, 0.69, 0.64, 0.94, 0.83), (0.48, 0.31, 0.25, 0.30, 0.44, 0.47, 0.88, 0.82), (0.66, 0.63, 0.58, 0.55, 0.66, 0.72, 0.79, 0.83)]
SQSD = [(0.02, 0.09, 0.05, 0.07, 0.07, 0.02, 0.06, 0.03), (0.03, 0.12, 0.10, 0.20, 0.06, 0.10, 0.11, 0.06), (0.04, 0.10, 0.06, 0.21, 0.14, 0.11, 0.07, 0.21)]
BLAY = [("0-15 CM", "0-15 cm"), ("15-30 CM", "15-30 cm"), ("30-45 CM", "30-45 cm")]
BSH = [  # sheet, data, prefix, unit, conv, source, method
    ("MACRO", WSA3, "MACRO_", "% (water-stable aggregates >0.20 mm)", lambda v: v, "Table 4", "Wet sieving, 50 g air-dried soil (Kemper & Koch 1966); % WSA >0.20 mm (flag: 0.20 not 0.25 mm)"),
    ("PR", PR3, "PR_", "MPa (printed kPa / 1000)", lambda v: f"=ROUND({v}/1000,3)", "Table 4 - converted", "Cone penetrometer, 1 cm2 base, 60 deg cone (Eijkelkamp)"),
    ("TC(total c)", TC3, "TC_", "g/kg", lambda v: v, "Table 5", "CHNS analyser (Nelson & Sommers 1982)"),
    ("N", N3, "N_", "kg/ha (available N, as printed)", lambda v: v, "Table 5", "Alkaline KMnO4 (Subbiah & Asija 1956)"),
    ("P", P3, "P_", "kg/ha (available P, as printed)", lambda v: v, "Table 5", "0.5 M NaHCO3 (Olsen et al. 1954)"),
    ("K", K3, "K_", "kg/ha (available K, as printed)", lambda v: v, "Table 5", "Neutral 1 N NH4OAc (Hanway & Heidel 1952)"),
    ("ALKP", APA3, "ALP_", "ug PNP/g fresh soil/h", lambda v: v, "Table 6", "Tabatabai & Bremner (1969), fresh soil at rice flowering"),
    ("DHA", DHA3, "DHA_", "ug TPF/g soil/h (printed per 24 h / 24)", lambda v: f"=ROUND({v}/24,3)", "Table 6 - converted", "Casida et al. (1964), TPF colorimetric, 24 h"),
    ("MBC", MBC3, "MBC_", "ug C/g soil", lambda v: v, "Table 6", "Chloroform fumigation-extraction (Vance et al. 1987)"),
    ("UREASE", UA3, "URE_", "ug urea/g soil/h (DERIVED: printed ug NH4-N x 60/28)", lambda v: f"=ROUND({v}*60/28,3)", "Table 6 - converted", "Urease (May & Douglas 1976); NH4-N released converted to urea equivalent"),
    ("SQI", SQI3, "SQI_", "unitless 0-1 (PCA minimum data set, linear scoring, Bastida et al. 2006 / Basak et al. 2016)", lambda v: v, "Table 7",
     "PCA-MDS (eigenvalue >= 1), linear 'more is better' / 'less is better' (PR) scoring, weighted sum"),
]
for k, (cls, rep) in enumerate(BLAY):
    base = {**BI, "year of data collection/experiment": 2020, "DURATION": "4-10 Y", "YEAR OF DATA (duration)": 6, "DEPTH": cls, "DEPTH (as reported in paper)": rep, "Obs": 2,
            "Crop/season of sampling": "RICE SEASON - at harvest of the 6th rice crop (2020); biological properties at rice flowering"}
    for row, dt, ct, ca, lab in BROWS:
        nt0 = BI_RED + f"ROW {row} ({lab}). "
        br = put("BD", base, {"DT": BD3[k][dt], "CT": BD3[k][ct], "CA": BD3[k][ca]}, "BD_", red=True, UNIT="Mg/m3",
                 **{"Data source": "Table 4", "Method used (from paper)": "Core method, 5 x 5 cm core (Blake & Hartge 1986)", "Notes/Doubts": nt0 + all8(BD3[k]) + BI_NOTE})
        put("POROSITY", base, {c: f"=ROUND((1-{B.ref('BD', 'BD_' + c, br)}/2.65)*100,2)" for c in ("DT", "CT", "CA")}, "POROSITY_", red=True, UNIT="% v/v",
            **{"Data source": "DERIVED from Table 4 BD", "Method used (from paper)": "Porosity = (1 - BD/PD) x 100", "Notes/Doubts": nt0 + "DERIVED (rule 73): no PD -> 2.65 (flag). " + BI_NOTE})
        put("GWC", base, {c: f"=ROUND({VMC3[k][i]}/{B.ref('BD', 'BD_' + c, br)},2)" for c, i in (("DT", dt), ("CT", ct), ("CA", ca))}, "GWC_", red=True,
            UNIT="% w/w (DERIVED: printed volumetric % / BD)",
            **{"Data source": "Table 4 - converted", "Method used (from paper)": "Gravimetric moisture x BD = VMC (paper); back-converted here (oven-dry method)",
               "Notes/Doubts": nt0 + "DERIVED GWC = printed VMC / same-row BD (live link). VMC " + all8(VMC3[k]) + BI_NOTE})
        for sheet, data, pre, unit, conv, src, meth in BSH:
            extra = ""
            if sheet == "SQI":
                extra = f"Paper SD: DT {SQSD[k][dt]}, CT {SQSD[k][ct]}, CA {SQSD[k][ca]} (kept in Notes; SD column keeps the formula, rule 46). "
            put(sheet, base, {"DT": conv(data[k][dt]), "CT": conv(data[k][ct]), "CA": conv(data[k][ca])}, pre, red=True, UNIT=unit,
                **{"Data source": src, "Method used (from paper)": meth, "Notes/Doubts": nt0 + extra + all8(data[k]) + BI_NOTE})
# Table 7 carbon budget (no depth)
CI = (1571, 1230, 1556, 1214, 2520, 2179, 3253, 2911)
CO = (9386, 9075, 9174, 8914, 9826, 9739, 10433, 10658)
CE = (5.97, 7.38, 5.9, 7.34, 3.9, 4.47, 3.21, 3.66)
CSI = (4.97, 6.38, 4.9, 6.34, 2.9, 3.47, 2.21, 2.66)
CFY = (0.178, 0.142, 0.180, 0.143, 0.268, 0.236, 0.318, 0.285)
bb = {**BI, "year of data collection/experiment": "6-yr trial (2015-2021)", "DURATION": "4-10 Y", "YEAR OF DATA (duration)": 6, "Obs": 2,
      "Crop/season of sampling": "Rice-wheat system (annual carbon budget)"}
CBM = "Input-based carbon budget: farm inputs x emission coefficients (Table S2) + N2O = (N fertiliser + residue N) x 0.01 x 1.571; GWP = N2O x 265 + CO2"
for row, dt, ct, ca, lab in BROWS:
    nt0 = f"ROW {row} ({lab}). "
    for sheet, pre, data, unit, conv, extra in (
            ("C input", "CIN_", CI, "kg C/ha/yr (printed kg CO2-eq/ha x 12/44)", lambda v: f"=ROUND({v}*12/44,0)", "Printed CI is in kg CO2-eq/ha (paper Eq. 2: C input = CF x 12/44). "),
            ("C output", "COUT_", CO, "kg C/ha/yr (printed kg CO2-eq/ha x 12/44)", lambda v: f"=ROUND({v}*12/44,0)", "Paper SD of CO: ICM1 50, ICM2 71, ICM5 84, ICM6 122, ICM7 128, ICM8 108. "),
            ("CER", "CER_", CE, "ratio (carbon efficiency = C output / C input; printed as 'CE (%)')", lambda v: v, "Printed label '%' but values = CO / CI (e.g. 9386 / 1571 = 5.97). "),
            ("CSI", "CSI_", CSI, "index ((C output - C input) / C input)", lambda v: v, ""),
            ("GHG intensity", "GHGI_", CFY, "kg CO2-eq/kg yield (yield-scaled carbon footprint, CFy)", lambda v: v, "")):
        put(sheet, bb, {"DT": conv(data[dt]), "CT": conv(data[ct]), "CA": conv(data[ca])}, pre, UNIT=unit,
            **{"Data source": "Table 7" + (" - converted" if "12/44" in unit else ""), "Method used (from paper)": CBM + "; carbon output from biomass (Jat et al. 2019; Lal et al. 2020)",
               "Notes/Doubts": nt0 + "MODEL / INVENTORY ESTIMATE (flag). " + extra + all8(data) + BI_NOTE})

# =====================================================================================
# Study_Info, LAT_LONG, Treatment_Mapping, EXCLUDED_rows
# =====================================================================================
B.add("Study_Info", {"No.": 171, "SERIAL NO": 171, "Authors": GH["Authors"], "Year": 2012, "Journal": "Paddy and Water Environment",
                     "Full reference": "Ghimire R, Adhikari KR, Chen Z-S, Shah SC & Dahal KR (2012) Soil organic carbon sequestration as affected by tillage, crop residue, and nitrogen application in rice-wheat rotation system. Paddy Water Environ 10:95-102",
                     "DOI / link": "https://doi.org/10.1007/s10333-011-0268-0", "Country": "Nepal", "Site/Location": GH["Site/Location"], "latitude": 27.647, "longitude": 84.346,
                     "latitude (as reported)": "27 deg 38' 49\" N", "longitude (as reported)": "84 deg 20' 45\" E", "Coordinates source": "Paper", "CLIMATE": "ST",
                     "Experiment established (year)": "1999 (NT); CT/NT split 2001-02; factorial Nov 2002", "year of data collection/experiment": "March 2006", "Years of data reported": 1,
                     "DURATION": "4-10 Y", "SOIL": "LOAMY", "Texture as reported": "Sandy clay loam to 30 cm, sandy loam 30-50 cm (Typic Haplustoll)", "sand": 57, "silt": 19, "CLAY": 24,
                     "ph (initial)": 5.4, "RAIN FALL": 2000, "Crop rotation": "Rice-wheat-mungbean (cover crop)", "Wheat variety": "BL 1473", "Rice variety": "Sabitri",
                     "N dose (kg/ha)": "100 / 100 (N1 recommended vs N2 LCC timing)", "P dose (kg/ha)": "60 / 40 P2O5", "K dose (kg/ha)": "40 / 40 K2O",
                     "Residue type & rate (t/ha)": "4 Mg/ha per crop (12 Mg/ha/yr) in M1", "Treatments in paper": GH_TRT,
                     "Parameters extracted": "SOC stock 0-5, 5-10, 10-15, 15-30, 30-50 cm (Table 4) -> SOC concentration (derived, BD 1.07) and cumulative stocks 0-10 / 0-15 / 0-30 / 0-50 cm",
                     "Supplementary data?": SUPP, "Notes/Doubts": "INCLUDED: CT, CTR, ZT, CA (N timing pooled). " + GH_NOTE})
B.add("Study_Info", {"No.": 172, "SERIAL NO": 172, "Authors": TP["Authors"], "Year": 2005, "Journal": "Soil Science and Plant Nutrition",
                     "Full reference": "Tirol-Padre A, Tsuchiya K, Inubushi K & Ladha JK (2005) Enhancing soil quality through residue management in a rice-wheat system in Fukuoka, Japan. Soil Sci Plant Nutr 51:849-860",
                     "DOI / link": "https://doi.org/10.1111/j.1747-0765.2005.tb00120.x", "Country": "Japan", "Site/Location": TP["Site/Location"], "latitude": 33.2, "longitude": 130.5,
                     "Coordinates source": "Approximate (Chikugo city; paper gives none)", "CLIMATE": "TEMP", "Experiment established (year)": 1963,
                     "year of data collection/experiment": "Soil Oct 2003; rice yields 1989-2003", "Years of data reported": "1 soil sampling; 12 yield years", "DURATION": ">10 Y",
                     "SOIL": "LOAMY", "Texture as reported": "Gray Lowland soil, 29 % clay, 56 % silt, 16 % sand", "sand": 16, "silt": 56, "CLAY": 29, "Crop rotation": "Rice-wheat",
                     "N dose (kg/ha)": "0 or 70 (urea)", "Residue type & rate (t/ha)": "Rice straw 10; compost 20; ryegrass 8 then wheat straw 10 / 6 (incorporated at puddling)",
                     "Treatments in paper": TP_TRT,
                     "Parameters extracted": "RED soil rows (+N tier): pH, Olsen P (kg/ha, assumed depth), Ex-K, CEC, total C, organic C, total N, MBC and basal respiration (aerobic / flooded incubations), hot-water C, POXC, PMN; rice yield 12 years (Fig. 1, digitised); rice N uptake",
                     "Supplementary data?": SUPP, "Notes/Doubts": "INCLUDED (+N tier): CT vs CTR rows a (rice straw) / b (wheat straw) / c (rice-straw compost). " + TP_NOTE})
B.add("Study_Info", {"No.": "124 (companion)", "SERIAL NO": "124 (companion)", "Authors": HO["Authors"], "Year": 2023, "Journal": "Field Crops Research",
                     "Full reference": "Hoque MA, Gathala MK, Timsina J, Ziauddin MATM, Hossain M & Krupnik TJ (2023) Reduced tillage and crop diversification can improve productivity and profitability of rice-based rotations of the Eastern Gangetic Plains. Field Crops Res 291:108791",
                     "DOI / link": "https://doi.org/10.1016/j.fcr.2022.108791", "Country": "Bangladesh", "Site/Location": HO["Site/Location"], "latitude": 24.942, "longitude": 89.928,
                     "latitude (as reported)": "24 deg 56' 30.68\" N", "longitude (as reported)": "89 deg 55' 40.39\" E", "Coordinates source": "Paper", "CLIMATE": "ST",
                     "Experiment established (year)": 2013, "year of data collection/experiment": "2013-2016", "Years of data reported": 3, "DURATION": "0-3 Y", "SOIL": "LOAMY",
                     "Texture as reported": "Loam (sand 47.3, silt 30.0, clay 22.7 %)", "sand": 47.3, "silt": 30, "CLAY": 22.7, "ph (initial)": 6.2,
                     "Crop rotation": "Rice-wheat (row a) and rice-wheat-mungbean (row b)", "Wheat variety": "BARI Gom-26", "Rice variety": "BR-11 / BINA dhan-7",
                     "N dose (kg/ha)": "wheat 100; rice 81 / 68", "Residue type & rate (t/ha)": "CA / AT ~25 cm stubble (~3 t/ha); CT ~0.7 t/ha incorporated", "Treatments in paper": HO_TRT,
                     "Parameters extracted": "SREY, system gross margin, B:C (derived) - R-W and R-W-MB, CT / MTR / pMTR (AT added)",
                     "Supplementary data?": "Tables S1-S3 (management, residue) - not reachable", "Notes/Doubts": "INCLUDED as companion: AT = pMTR. " + HO_NOTE})
B.add("Study_Info", {"No.": 173, "SERIAL NO": 173, "Authors": BI["Authors"], "Year": 2023, "Journal": "Agriculture, Ecosystems and Environment",
                     "Full reference": "Biswakarma N et al. (2023) Identification of a resource-efficient integrated crop management practice for the rice-wheat rotations in south Asian Indo-Gangetic Plains. Agric Ecosyst Environ 357:108675",
                     "DOI / link": "https://doi.org/10.1016/j.agee.2023.108675", "Country": "India (Delhi)", "Site/Location": BI["Site/Location"], "latitude": 28.633, "longitude": 77.15,
                     "latitude (as reported)": "28 deg 38' N", "longitude (as reported)": "77 deg 09' E", "Coordinates source": "Paper", "CLIMATE": "ST",
                     "Experiment established (year)": 2015, "year of data collection/experiment": "2015-16 to 2020-21; soil 2020 (after 6th rice)", "Years of data reported": "6 yield years; 1 soil sampling",
                     "DURATION": "0-3 Y to 4-10 Y (per row)", "SOIL": "LOAMY", "Texture as reported": "Sandy clay loam", "soc (initial)": 4.9, "Bdi": 1.52, "MIN TEMP": 5, "MAX TEMP": 46,
                     "RAIN FALL": 642, "Crop rotation": "Rice-wheat (ICM1-6); rice-wheat-mungbean (ICM7-8)", "Rice variety": "Basmati (not named)",
                     "N dose (kg/ha)": "rice 100, wheat 120 (100 % RF) or 75 % RF + bio-fertiliser", "P dose (kg/ha)": "21.8 / 26", "K dose (kg/ha)": "41.5 / 33",
                     "Residue type & rate (t/ha)": "CA: wheat ~3, rice ~5, mungbean ~3 Mg/ha retained", "Treatments in paper": BI_TRT,
                     "Parameters extracted": ("WEY 6 years; RED soil rows at 0-15 / 15-30 / 30-45 cm: BD, porosity (derived), WSA >0.20 mm, GWC (derived), PR, total C, available N/P/K, "
                                              "ALKP, DHA, MBC, urease, SQI; carbon input / output, CER, CSI, carbon footprint"),
                     "Supplementary data?": "Tables S1-S7, Figs S1-S4 - not reachable", "Notes/Doubts": "INCLUDED (author coding): DT (ICM1/2), CT (ICM3/4), CA (ICM5-8), rows a-d. SYI radar (Fig. 2) not digitised (values not printed). " + BI_NOTE})
for no, au, yr, ctry, site, la, lo, lar, lor, src, cl, note in [
        (171, "Ghimire R. et al.", 2012, "Nepal", "IAAS Rampur, Chitwan", 27.647, 84.346, "27 deg 38' 49\" N", "84 deg 20' 45\" E", "Paper", "ST", None),
        (172, "Tirol-Padre A. et al.", 2005, "Japan", "Chikugo, Fukuoka", 33.2, 130.5, "-", "-", "Approximate (Chikugo city)", "TEMP", "Paper gives no coordinates"),
        ("124 (companion)", "Hoque M.A. et al.", 2023, "Bangladesh", "BARI RARS Jamalpur", 24.942, 89.928, "24 deg 56' 30.68\" N", "89 deg 55' 40.39\" E", "Paper", "ST", "Same as old-master 124"),
        (173, "Biswakarma N. et al.", 2023, "India (Delhi)", "ICAR-IARI, New Delhi", 28.633, 77.15, "28 deg 38' N", "77 deg 09' E", "Paper", "ST", None)]:
    B.add("LAT_LONG", {"No.": no, "SERIAL NO": no, "Authors": au, "Year": yr, "Country": ctry, "Site/Location": site, "latitude (as reported)": lar,
                       "longitude (as reported)": lor, "latitude": la, "longitude": lo, "Coordinates source": src, "CLIMATE": cl, "Notes": note})
TM = [
    (171, "Ghimire R. et al.", 2012, "T1M0", "Conventional tillage (plough 15-20 cm, puddled rice), no residue", "Puddled", "Conventional", "No (roots only)", None, "CT", "Conventional both phases", "High", "INCLUDED"),
    (171, "Ghimire R. et al.", 2012, "T1M1", "Conventional tillage + 4 Mg/ha residue per crop", "Puddled", "Conventional", "Yes (incorporated)", "4 per crop", "CTR", "Conventional + residue", "High", "INCLUDED"),
    (171, "Ghimire R. et al.", 2012, "T0M0", "No-tillage (surface seeding of all crops), no residue", "No-till surface-seeded", "No-till", "No (roots only)", None, "ZT", "No-till both phases", "High", "INCLUDED"),
    (171, "Ghimire R. et al.", 2012, "T0M1", "No-tillage + 4 Mg/ha residue per crop", "No-till surface-seeded", "No-till", "Yes (surface)", "4 per crop", "CA", "No-till + residue", "High", "INCLUDED"),
    (172, "Tirol-Padre A. et al.", 2005, "N (urea 70 kg N/ha)", "Inorganic N only, no organic residue", "Puddled TPR", "Not described (conventional)", "No", None, "CT", "Residue-free reference of the +N tier", "High", "INCLUDED"),
    (172, "Tirol-Padre A. et al.", 2005, "RS + N", "Rice straw 10 Mg/ha incorporated at puddling + N", "Puddled TPR", "Not described", "Yes (incorporated)", 10, "CTR", "Row a", "High", "INCLUDED"),
    (172, "Tirol-Padre A. et al.", 2005, "WS + N", "Italian ryegrass 8 Mg/ha (1963-84) then wheat straw 10 / 6 Mg/ha + N", "Puddled TPR", "Not described", "Yes (incorporated)", "6-10", "CTR", "Row b (ryegrass period flag)", "Medium", "INCLUDED - FLAG"),
    (172, "Tirol-Padre A. et al.", 2005, "RSC + N", "Rice-straw compost 20 Mg/ha + N", "Puddled TPR", "Not described", "Composted straw (incorporated)", 20, "CTR", "Row c; author 2026-10-05: compost = CTR", "Medium", "INCLUDED (author) - FLAG"),
    (172, "Tirol-Padre A. et al.", 2005, "RSC (-N)", "Rice-straw compost without N", "Puddled TPR", "Not described", "Composted straw", 20, "EXCLUDED", "-N tier (rule 78)", "High", "EXCLUDED"),
    (172, "Tirol-Padre A. et al.", 2005, "Control / RS / WS (-N tier)", "No inorganic N", "Puddled TPR", "Not described", "-", None, "EXCLUDED", "Unfertilised control as CT (rule 78); values in Notes", "High", "EXCLUDED"),
    ("124 (companion)", "Hoque M.A. et al.", 2023, "CT", "Puddled TPR; 3-5 tillage passes for wheat; ~0.7 t/ha stubble incorporated", "Puddled", "Conventional", "Minimal (0.7 t/ha)", 0.7, "CT", "As old-master 124", "High", "INCLUDED"),
    ("124 (companion)", "Hoque M.A. et al.", 2023, "CA", "Untilled unpuddled TPR; wheat (+ mungbean) strip-tilled into ~25 cm stubble", "Zero till, unpuddled", "Strip tillage", "Yes", 3, "MTR", "As old-master 124", "High", "INCLUDED"),
    ("124 (companion)", "Hoque M.A. et al.", 2023, "AT", "Puddled TPR; winter / spring crops strip-tilled into ~25 cm stubble with residue", "Puddled", "Strip tillage", "Yes", 3, "pMTR", "Puddled rice + MT (strip) wheat + residue (rules 68 / 85 / 86)", "High", "INCLUDED"),
    (173, "Biswakarma N. et al.", 2023, "ICM1 / ICM2", "Chisel 30 cm + puddled TPR; disc + 2 cultivator wheat; no residue; 100 % RF / 75 % RF + bf + AM", "Puddled (after chisel 30 cm)", "Conventional", "No", None, "DT", "Author 2026-10-05: annual chisel ploughing to 30 cm = deep tillage", "High", "INCLUDED (author)"),
    (173, "Biswakarma N. et al.", 2023, "ICM3 / ICM4", "Chisel 30 cm + DSR; raised-bed wheat after disc + 2 cultivator; no residue", "Tilled DSR (unpuddled)", "Tilled + fresh raised beds", "No", None, "CT", "Author 2026-10-05 (flag: chisel ploughing stated for ICM1-4 alike)", "Medium", "INCLUDED (author) - FLAG"),
    (173, "Biswakarma N. et al.", 2023, "ICM5 / ICM6", "ZT-DSR with wheat residue; ZT wheat with rice residue; 100 % / 75 % RF + bf", "Zero till DSR", "Zero till", "Yes", "3 / 5", "CA", "Rows a / b", "High", "INCLUDED"),
    (173, "Biswakarma N. et al.", 2023, "ICM7 / ICM8", "As ICM5 / ICM6 + summer mungbean (residue retained)", "Zero till DSR", "Zero till", "Yes (+ mungbean)", "3 / 5 / 3", "CA", "Rows c / d; mungbean flag", "High", "INCLUDED - FLAG"),
]
th = ["SERIAL NO", "Authors", "Year", "Paper's treatment label (verbatim)", "Full description from paper", "Rice-phase tillage", "Wheat-phase tillage",
      "Residue retained?", "Residue rate (t/ha)", "ASSIGNED CODE", "Rationale", "Confidence", "Status"]
for row in TM:
    d = dict(zip(th, row))
    d["No."] = row[0]
    B.add("Treatment_Mapping", d)
B.add("EXCLUDED_rows", {"Sheet": "(treatments)", "SERIAL NO": 172, "Authors": "Tirol-Padre A. et al.", "Year": 2005,
                        "Reason for exclusion": "-N tier (unfertilised control as CT, rule 78) excluded. Its values are in the Notes of each 172 row.",
                        "Full row (header = value)": "-"})
B.add("EXCLUDED_rows", {"Sheet": "(treatments)", "SERIAL NO": "124 (companion)", "Authors": "Hoque M.A. et al.", "Year": 2023,
                        "Reason for exclusion": "R-R, R-M, R-MB, R-M-MB rotations (no wheat) not entered, as in old-master 124.", "Full row (header = value)": "-"})
B.save(OUT)
print("saved", OUT)
