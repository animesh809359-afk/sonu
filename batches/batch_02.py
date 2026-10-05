"""Batch 02 (2026-10-05): uploaded files 112.pdf, 113_rqal.pdf, 113.pdf, 111_real.pdf, 112_real.pdf.

Serials (continuing the old master, which ends at 163), in upload order:
  164 Yadav et al. 2000 (Field Crops Res. 68:219-246)   - 7 sites, 100F (CT) vs 50F+CR (CTR, flagged)
  165 Davari et al. 2012 (Biol. Agric. Hortic. 28:206-222) - RW and RWM systems, RR (CT) vs RI (CTR)
  166 Das et al. 2014 (Soil Tillage Res. 136:9-18)       - T2 (CT) vs T8 (CTR, flagged)
  167 Naz et al. 2023 (Land 12:546)                       - EXCLUDED (rice-berseem GM x fertiliser, no tillage/residue contrast)
  168 Dhaliwal et al. 2020 (Soil Research 58:468-477)    - CT, CTR, ZT, CA (rice-season sampling -> red rows)

Usage: python batches/batch_02.py <in.xlsx> <out.xlsx>
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from lib import Book  # noqa: E402

SRC, OUT = sys.argv[1], sys.argv[2]
HERE = os.path.dirname(os.path.abspath(__file__))
DIG = os.path.join(HERE, "..", "digitised")
B = Book(SRC)
TODAY = "2026-10-05"


def dur_class(y):
    return "0-3 Y" if y <= 3 else ("4-10 Y" if y <= 10 else ">10 Y")


def put(sheet, base, vals, prefix, red=False, **extra):
    """vals: {code: value}; prefix: column prefix e.g. 'BD_'."""
    d = dict(base)
    for code, v in vals.items():
        d[prefix + code] = v
    d.update(extra)
    return B.add(sheet, d, red=red)


# =====================================================================================
# 168  DHALIWAL et al. 2020
# =====================================================================================
DH_TRT = ("TREATMENTS IN PAPER (Table 1; three-factor trial est. 2011 - only the 'absolute' CT and ZT rice and wheat "
          "combinations were studied): 1 CTW-CTDSR (-M) = conventionally tilled wheat (1 discing + 1 tyne harrowing + planking) "
          "and conventionally tilled dry-seeded rice, all rice residue removed -> CT ; 2 CTW+M-CTDSR = as 1 with ALL rice residue "
          "(7 t/ha) retained as surface mulch in wheat -> CTR ; 3 ZTW-ZTDSR = zero-till wheat (Turbo Happy Seeder) and zero-till DSR "
          "(inverted-T tyne ZT drill), residue removed -> ZT ; 4 ZTW+M-ZTDSR = as 3 with rice residue mulch -> CA. Wheat straw removed "
          "in every treatment (cut 3-5 cm above ground). RBD 3 reps; plots 9.3 x 6.5 m.")
DH = {"No.": 168, "SERIAL NO": 168, "Authors": "Dhaliwal J.K., Singh M.J., Sharma S., Gupta N. & Kukal S.S.", "Year": 2020,
      "Journal": "Soil Research", "Country": "India (Punjab)",
      "Site/Location": "PAU research farm, Ludhiana (DSR-wheat tillage x mulch trial of Gupta et al. 2016)",
      "latitude": 30.933, "longitude": 75.867, "CLIMATE": "TEMP", "year of data collection/experiment": 2016,
      "DURATION": "4-10 Y", "SOIL": "LOAMY", "Rep": 3, "RAIN FALL": 734, "LATT": 30.933,
      "YEAR OF DATA (duration)": 5, "ph (initial)": 7.4,
      "Treatment mapping (paper's name -> code)": "CTW-CTDSR (-M) -> CT ; CTW+M-CTDSR -> CTR ; ZTW-ZTDSR -> ZT ; ZTW+M-ZTDSR -> CA",
      "Crop/season of sampling": "RICE SEASON - soil sampled in 2016 after rice harvest (no wheat-season sampling in the paper)",
      "Fertilizer dose & other management": ("Fertiliser, water and pest management as PAU recommendations (doses not printed; see Gupta et al. 2016 FCR 196:219). "
                                             "Wheat PBW 621, 113 kg/ha, Turbo Happy Seeder, 20 cm rows; rice PR 115 DSR 40 kg/ha, 20 cm rows. "
                                             "+M: 7 t/ha rice residue spread between rows after wheat sowing (2.5 t/ha left at wheat harvest). "
                                             "Wheat straw removed in all plots. Surface soil pH 7.4 (1:2), EC 0.31 dS/m (1:2); Typic Ustochrept, sandy loam to 120 cm."),
      "Treatment details (from paper)": DH_TRT}
DH_MAP_NOTE = ("RICE-SEASON DATA (RED ROW): the paper samples ONLY after the 2016 rice harvest, so values are entered under the rice-season "
               "fallback rule (rule 36). Rotation-matched: CT rice + CT wheat = CT; ZT rice + ZT wheat = ZT/CA (rice residue is the mulch factor). "
               "Supplementary: none found (web search 2026-10-05; publisher site not reachable from this environment). Source file 112_real.pdf.")
RED = True

# SOC (Table 2)
dh_soc = {}
for depth, rep, v in [("0-15 CM", "0-15 cm", dict(CA=6.20, CT=4.80, ZT=5.37, CTR=5.80)),
                      ("15-30 CM", "15-30 cm", dict(CA=4.00, CT=3.27, ZT=3.67, CTR=2.87))]:
    dh_soc[depth] = put("SOC(active C pool)", DH, v, "SOC_", red=RED, **{
        "DEPTH": depth, "DEPTH (as reported in paper)": rep, "Obs": 1, "UNIT": "g/kg",
        "Data source": "Table 2", "Method used (from paper)": "Walkley & Black (1934) wet oxidation",
        "Notes/Doubts": DH_MAP_NOTE + (" SD printed only for main-effect means (0-15: CT 5.30+/-0.06, ZT 5.78+/-0.05, -M 5.08+/-0.03, +M 6.00+/-0.04). "
                                       "LSD tillage 0.40, residue 0.40 (0-15); tillage 0.50 (15-30); TxM NS.")})
# SOC stock (Table 2, equivalent soil mass)
r1 = put("stock-SOC", DH, dict(CA=14.1, CT=10.3, ZT=11.9, CTR=12.2), "SOCs_", red=RED, **{
    "DEPTH": "0-20 CM", "DEPTH (as reported in paper)": "0-15 cm (cumulative class 0-20 CM, rule 43)", "Obs": 1, "UNIT": "Mg C/ha",
    "Data source": "Table 2", "Method used (from paper)": "SOC stock on equivalent soil mass basis (Ellert & Bettany 1995); SOC by Walkley-Black",
    "Notes/Doubts": DH_MAP_NOTE + " Printed stock (equivalent soil mass), not recomputed. 15-30 cm layer stock: CA 9.60, CT 7.86, ZT 8.80, CTR 6.88 Mg/ha."})
vals = {}
for code, top, sub in [("CA", 14.1, 9.60), ("CT", 10.3, 7.86), ("ZT", 11.9, 8.80), ("CTR", 12.2, 6.88)]:
    vals[code] = f"=ROUND({B.ref('stock-SOC', 'SOCs_' + code, r1)}+{sub},2)"
put("stock-SOC", DH, vals, "SOCs_", red=RED, **{
    "DEPTH": "0-30 CM", "DEPTH (as reported in paper)": "0-15 + 15-30 cm summed", "Obs": 1, "UNIT": "Mg C/ha",
    "Data source": "Table 2 - DERIVED (sum of the two printed layer stocks)",
    "Method used (from paper)": "SOC stock on equivalent soil mass basis (Ellert & Bettany 1995)",
    "Notes/Doubts": "DERIVED: 0-30 cm = printed 0-15 cm stock (row above, live link) + printed 15-30 cm stock. " + DH_MAP_NOTE})

# Aggregates (Tables 3-4)
AGG_M = ("Wet sieving, Yoder apparatus (Kemper & Rosenau 1986): 50 g air-dry 5-8 mm aggregates, capillary pre-wetting 10 min, "
         "sieves 2, 1, 0.5, 0.25, 0.1 mm, 30 min at 30 osc/min; sand-corrected (Na-hexametaphosphate)")
dh_mac, dh_mic = {}, {}
for depth, rep, mac, mic in [("0-15 CM", "0-15 cm", dict(CA=55.5, CT=43.7, ZT=52.4, CTR=56.1), dict(CA=11.9, CT=14.8, ZT=13.1, CTR=14.1)),
                             ("15-30 CM", "15-30 cm", dict(CA=47.8, CT=41.5, ZT=48.8, CTR=47.5), dict(CA=12.0, CT=15.0, ZT=12.1, CTR=13.6))]:
    common = {"DEPTH": depth, "DEPTH (as reported in paper)": rep, "Obs": 1, "Data source": "Table 3", "Method used (from paper)": AGG_M}
    dh_mac[depth] = put("MACRO", DH, mac, "MACRO_", red=RED, UNIT="% (water-stable macro-aggregates >0.25 mm, sand-corrected)",
                        **{"Notes/Doubts": DH_MAP_NOTE + " LSD (0-15) T 2.17, M 2.17, TxM 3.07; (15-30) T 2.40, M 2.40, TxM 3.38."}, **common)
    dh_mic[depth] = put("MICRO", DH, mic, "MICRO_", red=RED, UNIT="% (water-stable micro-aggregates 0.1-0.25 mm, sand-corrected)",
                        **{"Notes/Doubts": DH_MAP_NOTE + " Smallest sieve 0.1 mm, so this fraction is 0.1-0.25 mm (not 0.053-0.25)."}, **common)
    wsa = {c: f"=ROUND(({B.ref('MACRO', 'MACRO_' + c, dh_mac[depth])}+{B.ref('MICRO', 'MICRO_' + c, dh_mic[depth])})/100,3)"
           for c in ("CA", "CT", "ZT", "CTR")}
    common2 = dict(common)
    common2["Data source"] = "Table 3 - DERIVED (WSA = macro + micro)"
    put("WSA", DH, wsa, "WSA_", red=RED, UNIT="g/g soil (sum of water-stable fractions >0.1 mm)",
        **{"Notes/Doubts": "DERIVED (rule 74): WSA = (WSA-mac + WSA-mic)/100, live links to the MACRO and MICRO rows. FLAG: lowest sieve 0.1 mm, so the sum covers >0.1 mm, not >0.053 mm. " + DH_MAP_NOTE}, **common2)
for depth, rep, v in [("0-15 CM", "0-15 cm", dict(CA=1.33, CT=0.46, ZT=0.99, CTR=1.21)),
                      ("15-30 CM", "15-30 cm", dict(CA=0.50, CT=0.35, ZT=0.42, CTR=0.27))]:
    put("MWD 1", DH, v, "MWD_", red=RED, **{"DEPTH": depth, "DEPTH (as reported in paper)": rep, "Obs": 1, "UNIT": "mm (wet sieving)",
        "Data source": "Table 4", "Method used (from paper)": AGG_M + "; MWD = sum(di*wi)/sum(wi) (Youker & McGuinness 1957)",
        "Notes/Doubts": DH_MAP_NOTE + " LSD (0-15) T 0.23, M 0.23, TxM 0.30; (15-30) T 0.09."})

# Bulk density (Table 5) and derived porosity
dh_bd = {}
for depth, rep, v in [("0-15 CM", "0-15 cm", dict(CA=1.60, CT=1.56, ZT=1.60, CTR=1.50)),
                      ("15-30 CM", "15-30 cm", dict(CA=1.65, CT=1.77, ZT=1.67, CTR=1.75))]:
    dh_bd[depth] = put("BD", DH, v, "BD_", red=RED, **{"DEPTH": depth, "DEPTH (as reported in paper)": rep, "Obs": 1, "UNIT": "Mg/m3",
        "Data source": "Table 5", "Method used (from paper)": "Core method (Blake & Hartge 1986), steel core 5 cm high x 5 cm i.d., 3 cores/plot",
        "Notes/Doubts": DH_MAP_NOTE + " LSD (0-15) T 0.02, M 0.02, TxM 0.03; (15-30) T 0.03."})
    por = {c: f"=ROUND((1-{B.ref('BD', 'BD_' + c, dh_bd[depth])}/2.65)*100,2)" for c in ("CA", "CT", "ZT", "CTR")}
    put("POROSITY", DH, por, "POROSITY_", red=RED, **{"DEPTH": depth, "DEPTH (as reported in paper)": rep, "Obs": 1, "UNIT": "% v/v",
        "Data source": "DERIVED from Table 5 BD", "Method used (from paper)": "Porosity = (1 - BD/PD) x 100",
        "Notes/Doubts": "DERIVED (rule 73): porosity = (1 - treatment BD / PD) x 100, live link to the BD row; no treatment or initial PD in the paper -> PD = 2.65 Mg/m3 (default, flag). " + DH_MAP_NOTE})

# Infiltration (Table 6)
put("IR", DH, dict(CA=1.00, CT=0.47, ZT=0.53, CTR=0.80), "IR_", red=RED,
    **{"IIR_CA": 39.0, "IIR_CT": 21.0, "IIR_ZT": 25.0, "IIR_CTR": 33.0,
       "DEPTH": "0-15 CM", "DEPTH (as reported in paper)": "soil surface (double-ring infiltrometer, rings inserted 10 cm)", "Obs": 1,
       "UNIT": "cm/hr (IR_ = steady-state, IIR_ = initial)", "Data source": "Table 6",
       "Method used (from paper)": "Double-ring infiltrometer (Reynolds et al. 2002), 30/60 cm rings, constant head, readings to 372 min",
       "Notes/Doubts": DH_MAP_NOTE + " Surface infiltration entered in the 0-15 CM class as for other surface rows. LSD residue: initial 8.57, steady 0.17; tillage NS."})

# Soil water (Table 7, 0-15 cm, cm3/cm3 x 100)
WQ = ("WATER-QUANTITY CHECK: Table 7 'soil moisture characteristics' = water retained at -33, -100, -500, -1500 kPa on pressure-plate "
      "extractors (Klute & Dirksen 1986), printed in cm3/cm3 x 100 (% v/v). -33 kPa -> FC, -1500 kPa -> PWP; converted to weight basis "
      "with the SAME treatment's 0-15 cm BD (live link). Also printed: -100 kPa CT 27.3, CTR 31.8, ZT 30.4, CA 34.5; -500 kPa CT 20.9, "
      "CTR 24.6, ZT 24.6, CA 29.2 (% v/v). LSD T and M: 3.45 (-33), 2.23 (-1500); TxM NS. ")
fcv = dict(CA=46.7, CT=33.2, ZT=38.4, CTR=42.9)
pwv = dict(CA=15.7, CT=9.0, ZT=13.1, CTR=14.3)
bdr = dh_bd["0-15 CM"]
common = {"DEPTH": "0-15 CM", "DEPTH (as reported in paper)": "0-15 cm", "Obs": 1,
          "Method used (from paper)": "Pressure-plate extractor (Soilmoisture Equipment Corp.), Klute & Dirksen (1986)"}
fc_r = put("FC (weight basis)", DH, {c: f"=ROUND({fcv[c]}/{B.ref('BD', 'BD_' + c, bdr)},2)" for c in fcv}, "FC_", red=RED,
           UNIT="% w/w (printed % v/v at -33 kPa / BD)", **{"Data source": "Table 7 - converted", "Notes/Doubts": WQ + DH_MAP_NOTE}, **common)
pw_r = put("PWP (weight basis)", DH, {c: f"=ROUND({pwv[c]}/{B.ref('BD', 'BD_' + c, bdr)},2)" for c in pwv}, "PWP_", red=RED,
           UNIT="% w/w (printed % v/v at -1500 kPa / BD)", **{"Data source": "Table 7 - converted", "Notes/Doubts": WQ + DH_MAP_NOTE}, **common)
aw_r = put("AWC (weight basis)", DH, {c: f"=ROUND({B.ref('FC (weight basis)', 'FC_' + c, fc_r)}-{B.ref('PWP (weight basis)', 'PWP_' + c, pw_r)},2)" for c in fcv},
           "AWCW_", red=RED, UNIT="% w/w (FC - PWP)", **{"Data source": "Table 7 - DERIVED", "Notes/Doubts": "DERIVED: AWC = FC - PWP (weight basis, live links). " + WQ + DH_MAP_NOTE}, **common)
put("AWC (volume basis)", DH, {c: f"=ROUND({B.ref('AWC (weight basis)', 'AWCW_' + c, aw_r)}*{B.ref('BD', 'BD_' + c, bdr)},2)" for c in fcv},
    "AWCV_", red=RED, UNIT="% v/v (AWCw x BD = printed -33 minus -1500 kPa)", **{"Data source": "Table 7 - DERIVED",
    "Notes/Doubts": "DERIVED: AWCv = AWCw x treatment BD (equals the printed v/v difference). " + WQ + DH_MAP_NOTE}, **common)

# Biology (Table 8, 0-7.5 cm)
BIO_D = {"DEPTH": "0-15 CM", "DEPTH (as reported in paper)": "0-7.5 cm", "Obs": 1}
put("MBC", DH, dict(CA=332.9, CT=83.6, ZT=138.3, CTR=211.3), "MBC_", red=RED, UNIT="ug C/g soil (printed 'mg g-1', mu lost in typesetting)",
    **{"Data source": "Table 8", "Method used (from paper)": "Chloroform fumigation-extraction (Vance et al. 1987), 0.5 M K2SO4, kEC 0.41",
       "Notes/Doubts": DH_MAP_NOTE + " Unit printed as 'mg g-1 soil' - values (84-333) are ug/g; LSD T and M 37.1, TxM NS."}, **BIO_D)
put("RESP", DH, dict(CA=34.8, CT=10.5, ZT=22.3, CTR=24.1), "RESP_", red=RED, UNIT="mg CO2/kg soil/day (printed 'mg CO2 g-1 day-1', read as ug/g/day)",
    **{"Data source": "Table 8", "Method used (from paper)": "Basal soil respiration: 50 g moist soil incubated 7 d at 30 C, CO2 trapped in 0.5 N NaOH, back-titrated with HCl",
       "Notes/Doubts": DH_MAP_NOTE + " FLAG unit: printed 'mg CO2 g-1 day-1'; taken as ug/g/day = mg/kg/day. LSD T and M 4.43."}, **BIO_D)
ENZ_NOTE = ("TILLAGE MAIN-EFFECT MEANS (flagged, rule 33): Figs 1-2 print only CT vs ZT (each pooled over -M and +M) and -M vs +M (pooled over CT and ZT); "
            "interaction NS, no cell means. _CT = CT main effect (CT and CTR plots), _ZT = ZT main effect (ZT and CA plots). Residue main effect in notes. "
            "DIGITISED (approx.) from the embedded raster figures; ALP/ACP/urease values reproduce the paper's printed % differences. ")
for sheet, pre, ct, zt, mm, pm, unit, src, meth, extra in [
    ("DHA", "DHA_", 7.11, 7.76, 6.76, 8.10, "ug TPF/g soil/h", "Fig. 1a (digitised)", "Tabatabai (1982): TTC + 1% glucose, 24 h at 30 C, TPF in methanol at 485 nm",
     "Text: ZT +13% vs CT, +M +24.6% vs -M (digitised gives +9% and +20%)."),
    ("UREASE", "URE_", "=ROUND(4.80*60,1)", "=ROUND(5.04*60,1)", 4.72, 5.17, "ug urea/g soil/h (axis printed ug urea g-1 MIN-1 x 60)", "Fig. 1b (digitised) - converted",
     "Douglas & Bremner (1970): 2000 ppm urea, 5 h at 37 C, KCl-PMA extraction, colour at 527 nm",
     "Digitised per-minute values CT 4.80, ZT 5.04, -M 4.72, +M 5.17 ug urea/g/min; FLAG: the axis label reads 'per min' although the assay is a 5-h incubation - verify unit."),
    ("ALKP", "ALP_", 22.92, 26.71, 22.02, 27.50, "ug PNP/g soil/h", "Fig. 2a (digitised)", "Tabatabai & Bremner (1969), p-nitrophenyl phosphate, pH 11, 1 h at 30 C, 420 nm", "Text: ZT +15.6%, +M +24.4%."),
    ("ACP", "ACP_", 18.09, 22.57, 17.54, 23.05, "ug PNP/g soil/h", "Fig. 2b (digitised)", "Tabatabai & Bremner (1969), p-nitrophenyl phosphate, pH 6.5, 1 h at 30 C, 420 nm", "Text: ZT +24.8%, +M +31.8%."),
]:
    put(sheet, DH, dict(CT=ct, ZT=zt), pre, red=RED, UNIT=unit, **{"Data source": src, "Method used (from paper)": meth,
        "Treatment mapping (paper's name -> code)": "CT main effect (CT -M and CT +M pooled) -> CT ; ZT main effect (ZT -M and ZT +M pooled) -> ZT",
        "Notes/Doubts": ENZ_NOTE + f"Residue main effect: -M {mm}, +M {pm}. {extra} " + DH_MAP_NOTE}, **BIO_D)

# =====================================================================================
# 165  DAVARI et al. 2012
# =====================================================================================
DV_TRT = ("TREATMENTS IN PAPER: strip-plot, 3 reps, 2006-07 and 2007-08, ORGANIC management. Rows = cropping system: RW (rice-wheat, summer fallow) "
          "and RWM (rice-wheat-mungbean, summer mungbean with Rhizobium + PSB); columns = residue: RR (entire above-ground biomass removed) and RI "
          "(all residue of each crop incorporated before the next crop: rice residue for wheat, wheat residue for rice in RW / for mungbean in RWM, "
          "mungbean residue for rice). Rice: field flooded and PUDDLED with tractor-drawn offset disc harrow, Pusa Basmati 1 transplanted 20 x 10 cm. "
          "Wheat: after rice harvest, residue (RI) + FYM incorporated with tractor-drawn heavy disc, then disked and planked twice; HD 2643 sown 3rd week Nov. "
          "RR -> CT, RI -> CTR (in both systems).")
DV = {"No.": 165, "SERIAL NO": 165, "Authors": "Davari M.R., Sharma S.N. & Mirzakhani M.", "Year": 2012,
      "Journal": "Biological Agriculture & Horticulture", "Country": "India (Delhi)",
      "Site/Location": "IARI research farm, New Delhi (organic rice-based cropping systems trial)",
      "latitude": 28.633, "longitude": 77.183, "CLIMATE": "ST", "SOIL": "LOAMY", "Rep": 3, "CLAY": 25.40, "LATT": 28.633,
      "ph (initial)": 8.16, "soc (initial)": 5.20, "Bdi": 1.50, "sand": 52.06, "silt": 22.54,
      "Fertilizer dose & other management": ("ORGANIC: FYM equivalent to 60 kg N/ha to rice and to wheat (FYM ~0.61% N, 22-23 C:N), no mineral fertiliser; "
                                             "BGA 1.5 kg/ha in rice 20 DAT; Azotobacter + PSB seed inoculation of wheat; cellulolytic fungal culture 600 g/t sprayed "
                                             "on residue in RI plots only. RI residue added (Mg DM/ha): RW 14.2 (2006-07), 16.0 (2007-08); RWM 17.8, 19.7. "
                                             "Initial soil: SCL, EC 0.79 dS/m, CEC 14.73 cmol/kg, OC 5.2 g/kg, Kjeldahl N 580 mg/kg, Olsen P 8.42, NH4OAc K 187 mg/kg, BD 1.50, FC 24.57%."),
      "Treatment details (from paper)": DV_TRT}
DV_NOTE = ("Rotation-matched: puddled transplanted rice + disc-tilled wheat = conventional in both phases; residue incorporated by disc -> CTR. "
           "FLAG: RI plots also received a cellulolytic culture spray (confounded with residue). "
           "Supplementary: none found (web search 2026-10-05; publisher site not reachable). Source file 113_rqal.pdf.")
SYS = {"RW": ("RW (rice-wheat, summer fallow)", "RW-RR -> CT ; RW-RI -> CTR", ""),
       "RWM": ("RWM (rice-wheat-mungbean)", "RWM-RR -> CT ; RWM-RI -> CTR", "GREEN MANURE / 3rd CROP: summer mungbean in BOTH treatments of this row (pods picked, residue incorporated in RI only). ")}
YR = {"2006-07": 1, "2007-08": 2}


def dv(sys_, year):
    d = dict(DV)
    d.update({"year of data collection/experiment": year, "DURATION": dur_class(YR[year]), "YEAR OF DATA (duration)": YR[year],
              "Treatment mapping (paper's name -> code)": SYS[sys_][1]})
    return d


# Yield (Table 5)
YLD = {("RW", "2006-07"): (4.2, 4.4, 3.3, 4.1, 7.2, 8.1, None), ("RWM", "2006-07"): (4.3, 4.5, 3.5, 4.1, 8.8, 10.0, (0.7, 1.0)),
       ("RW", "2007-08"): (4.4, 5.2, 4.3, 4.7, 8.3, 9.5, None), ("RWM", "2007-08"): (5.0, 5.8, 4.5, 5.2, 10.6, 12.5, (0.8, 1.1))}
for (s, y), (rr, ri, wr, wi, er, ei, mung) in YLD.items():
    d = dv(s, y)
    note = (SYS[s][2] + f"Cropping system {SYS[s][0]}, year {y}. SYS YIELD = paper's rice-equivalent yield of the system"
            + (" (INCLUDES MUNGBEAN, flagged)" if mung else "") + ". "
            + (f"Mungbean grain RR {mung[0]}, RI {mung[1]} Mg/ha. " if mung else "")
            + "Two-year means (Table 5): RW rice 4.3/4.8, wheat 3.8/4.4, REY 7.8/8.8; RWM rice 4.7/5.2, wheat 4.0/4.7, REY 9.8/11.5 (RR/RI). " + DV_NOTE)
    B.add("YIELD", {**d, "WYIELD_CT": wr, "WYIELD_CTR": wi, "RICE YIELD_CT": rr, "RICE YIELD_CTR": ri, "SYS YIELD_CT": er, "SYS YIELD_CTR": ei,
                    "Obs": 1, "UNIT": "t/ha grain (economic yield, Mg/ha)", "Crop/season of sampling": f"Rice (kharif) and wheat (rabi) {y}",
                    "Data source": "Table 5", "Method used (from paper)": "Grain harvested from plots; rice equivalent = sum(Ya x Pa/Pr)", "Notes/Doubts": note})

# Soil chemistry (Table 6, 0-20 cm, after each cycle)
CHEM = {("RW", "2006-07"): (5.65, 6.28, 635, 702, 8.6, 9.1, 195, 223), ("RWM", "2006-07"): (5.73, 6.45, 698, 780, 8.8, 9.5, 204, 234),
        ("RW", "2007-08"): (6.08, 6.75, 789, 911, 8.8, 9.4, 197, 227), ("RWM", "2007-08"): (6.21, 6.93, 875, 998, 9.1, 9.9, 207, 241)}
for (s, y), (oc0, oc1, n0, n1, p0, p1, k0, k1) in CHEM.items():
    d = dv(s, y)
    season = f"After completion of the {y} cycle (after wheat{' and mungbean' if s == 'RWM' else ' / summer fallow'}, before rice)"
    base = {"DEPTH": "0-15 CM", "DEPTH (as reported in paper)": "0-20 cm", "Obs": 1, "Crop/season of sampling": season, "Data source": "Table 6"}
    put("SOC(active C pool)", d, dict(CT=oc0, CTR=oc1), "SOC_", UNIT="g/kg", **{"Method used (from paper)": "Organic C (Prasad et al. 2006 manual; Walkley-Black type)",
        "Notes/Doubts": SYS[s][2] + "0-20 cm sample -> 0-15 CM class (maximum overlap). LSD residue 0.32 (06-07), 0.44 (07-08); CSxR 0.58/0.66. " + DV_NOTE}, **base)
    put("total N", d, dict(CT=n0, CTR=n1), "TN_", UNIT="mg/kg (Kjeldahl N)", **{"Method used (from paper)": "Total Kjeldahl N",
        "Notes/Doubts": SYS[s][2] + ("Printed RW-RR '6.35' and RI '70.2' in 2006-07 are typesetting errors for 635 and 702 (row mean 669 confirms). " if (s, y) == ("RW", "2006-07") else "")
        + "LSD residue 43.2 (06-07), 46.8 (07-08). " + DV_NOTE}, **base)
    put("P", d, dict(CT=f"=ROUND({p0}*2.24,2)", CTR=f"=ROUND({p1}*2.24,2)"), "P_", UNIT="kg/ha (printed Olsen P mg/kg x 2.24)",
        **{"Method used (from paper)": "0.5 M NaHCO3-extractable P (Olsen)", "Notes/Doubts": SYS[s][2] + f"CONVERTED: printed {p0} (RR) / {p1} (RI) mg/kg x 2.24 (2.24 million kg soil/ha, 0-15 cm convention; sample was 0-20 cm). " + DV_NOTE}, **base)
    put("K", d, dict(CT=f"=ROUND({k0}*2.24,1)", CTR=f"=ROUND({k1}*2.24,1)"), "K_", UNIT="kg/ha (printed NH4OAc-K mg/kg x 2.24)",
        **{"Method used (from paper)": "Neutral 1 N NH4OAc-extractable K", "Notes/Doubts": SYS[s][2] + f"CONVERTED: printed {k0} (RR) / {k1} (RI) mg/kg x 2.24. " + DV_NOTE}, **base)

# Physical (Table 9, 0-15 cm, after two cycles) and biology (Tables 7-8, after two cycles)
for s, bd0, bd1, po0, po1, hc0, hc1, ba0, ba1, fu0, fu1, ac0, ac1, mb0, mb1, dh0, dh1, co0, co1 in [
        ("RW", 1.46, 1.40, 44.9, 47.2, 0.43, 0.48, 4.8, 6.5, 2.3, 2.6, 9.2, 19.2, 205.3, 245.1, 106.2, 124.0, 547.1, 568.8),
        ("RWM", 1.44, 1.38, 45.7, 48.0, 0.45, 0.51, 5.7, 7.1, 2.9, 4.4, 12.4, 21.6, 236.4, 261.4, 114.3, 136.9, 561.3, 585.9)]:
    d = dv(s, "2007-08")
    phys = {"DEPTH": "0-15 CM", "DEPTH (as reported in paper)": "0-15 cm", "Obs": 1, "Data source": "Table 9",
            "Crop/season of sampling": "After completion of two cycles (June 2008, after wheat" + (" and mungbean)" if s == "RWM" else " / fallow)")}
    nt = SYS[s][2] + "15-30 cm values not printed (not significantly different). " + DV_NOTE
    put("BD", d, dict(CT=bd0, CTR=bd1), "BD_", UNIT="Mg/m3", **{"Method used (from paper)": "Core method (Veihmeyer & Hendrickson 1948), oven-dry 105 C 48 h",
        "Notes/Doubts": "LSD residue 0.04. " + nt}, **phys)
    put("POROSITY", d, dict(CT=po0, CTR=po1), "POROSITY_", UNIT="% v/v (printed)", **{"Method used (from paper)": "Porosity = (1 - BD/PD) x 100 (authors' calculation)",
        "Notes/Doubts": "PRINTED porosity (paper derived it from BD and PD; values reproduce PD = 2.65). LSD residue 1.46. " + nt}, **phys)
    put("HC", d, dict(CT=hc0, CTR=hc1), "HC_", UNIT="cm/hr (hydraulic conductivity, method not described)", **{"Method used (from paper)": "Not described (core samples)",
        "Notes/Doubts": "FLAG: 'hydraulic conductivity' - saturated/lab method not stated. LSD residue 0.36. " + nt}, **phys)
    bio = {"DEPTH": "0-15 CM", "DEPTH (as reported in paper)": "0-20 cm", "Obs": 1,
           "Crop/season of sampling": "After completion of two cycles (2007-08)"}
    put("Soil microbial count", d, dict(CT=f"=ROUND({ba0}/10,2)", CTR=f"=ROUND({ba1}/10,2)"), "SMC_", UNIT="10^7 cfu/g soil (printed bacteria x10^6 cells/g / 10)",
        **{"Data source": "Table 7 - converted", "Method used (from paper)": "Serial dilution agar plate, nutrient agar (bacteria)",
           "Notes/Doubts": f"BACTERIA. CONVERTED: printed {ba0} / {ba1} x10^6 cells/g. LSD R 0.5, CSxR 0.8. " + SYS[s][2] + DV_NOTE}, **bio)
    put("Fungal count", d, dict(CT=fu0, CTR=fu1), "FUN_", UNIT="x10^4 CFU/g soil", **{"Data source": "Table 7",
        "Method used (from paper)": "Serial dilution, Rose Bengal agar (Ottow & Glathe 1968)", "Notes/Doubts": "LSD R 0.7, CSxR 1.0. " + SYS[s][2] + DV_NOTE}, **bio)
    put("Actinomycetes", d, dict(CT=f"=ROUND({ac0}/10,2)", CTR=f"=ROUND({ac1}/10,2)"), "AM_", UNIT="10^5 cfu/g soil (printed x10^4 cells/g / 10)",
        **{"Data source": "Table 7 - converted", "Method used (from paper)": "Serial dilution, Ken Knight's medium",
           "Notes/Doubts": f"CONVERTED: printed {ac0} / {ac1} x10^4 cells/g. LSD R 1.7, CSxR 2.5. " + SYS[s][2] + DV_NOTE}, **bio)
    put("MBC", d, dict(CT=mb0, CTR=mb1), "MBC_", UNIT="ug C/g soil (printed 'mg g-1', read as ug/g)", **{"Data source": "Table 8",
        "Method used (from paper)": "Fumigation method (Jenkinson & Ladd 1981)",
        "Notes/Doubts": "FLAG: 'microbial biomass' printed in mg/g; values 205-261 are ug/g; biomass C assumed. LSD R 13.8. " + SYS[s][2] + DV_NOTE}, **bio)
    put("DHA", d, dict(CT=f"=ROUND({dh0}/24,2)", CTR=f"=ROUND({dh1}/24,2)"), "DHA_", UNIT="ug TPF/g soil/h (printed per 24 h / 24)",
        **{"Data source": "Table 8 - converted", "Method used (from paper)": "Dehydrogenase (TPF), 24 h incubation",
           "Notes/Doubts": f"CONVERTED: printed {dh0} / {dh1} 'mg' (read as ug) TPF/g/24 h, divided by 24. LSD R 15.3. " + SYS[s][2] + DV_NOTE}, **bio)
    put("RESP", d, dict(CT=co0, CTR=co1), "RESP_", UNIT="mg CO2/kg soil/day (printed 'mg g-1 soil 24 h-1', read as ug/g/day)",
        **{"Data source": "Table 8", "Method used (from paper)": "CO2 evolution, 24 h",
           "Notes/Doubts": "FLAG unit: printed mg/g/24 h; read as ug/g/day = mg/kg/day; CO2 vs CO2-C not stated. LSD R 7.8. " + SYS[s][2] + DV_NOTE}, **bio)

# =====================================================================================
# 166  DAS et al. 2014
# =====================================================================================
DS_TRT = ("TREATMENTS IN PAPER (Table 1, RBD 3 reps, since 1993, PDFSR Modipuram): T1 unfertilised; T2 recommended NPK (+Zn to rice) through fertilisers; "
          "T3 NPK + Zn + S (rice); T4 75% NPK + 25% N via FYM (rice); T5 75% NPK + 25% N via sulphitation press mud (rice); T6 75% NPK + green gram residue "
          "incorporated before rice; T7 = T6 (rice) + 75% NPK + 25% N via FYM (wheat); T8 75% NPK + 25% N via WHEAT STRAW to rice and 75% NPK + 25% N via "
          "RICE STRAW to wheat (CR). Rice puddled and transplanted (Saket 4, 20 x 10 cm, continuous 5 cm submergence); wheat HD 2338 drilled after dry tillage "
          "('wet tillage followed by dry tillage'); recommended 120-26-33 kg N-P-K/ha to each crop. T2 -> CT ; T8 -> CTR (FLAG fertiliser offset, rule 62); "
          "T1, T3-T7 EXCLUDED (unfertilised / amendments / third crop in some treatments only).")
DS = {"No.": 166, "SERIAL NO": 166, "Authors": "Das B., Chakraborty D., Singh V.K., Aggarwal P., Singh R., Dwivedi B.S. & Mishra R.P.", "Year": 2014,
      "Journal": "Soil & Tillage Research", "Country": "India (Uttar Pradesh)",
      "Site/Location": "PDFSR (now ICAR-IIFSR) long-term INM experiment, Modipuram, Meerut",
      "latitude": 29.067, "longitude": 77.767, "CLIMATE": "ST", "year of data collection/experiment": 2011, "DURATION": ">10 Y",
      "SOIL": "LOAMY", "Rep": 3, "CLAY": 27, "MIN TEMP": 5, "MAX TEMP": 45.5, "RAIN FALL": 863, "LATT": 29.067,
      "YEAR OF DATA (duration)": 18, "ph (initial)": 7.98, "soc (initial)": 4.1, "Bdi": 1.55, "sand": 55, "silt": 18,
      "Treatment mapping (paper's name -> code)": "T2 (100% NPK, residues removed) -> CT ; T8 (75% NPK + 25% N via crop residue, both crops) -> CTR [FLAG: fertiliser offset]",
      "Crop/season of sampling": "Wheat season - sampled 14 May 2011 after wheat harvest (18th year)",
      "Fertilizer dose & other management": ("T2: 120-26-33 kg N-P-K/ha to rice and wheat + Zn 5 kg/ha to rice. T8: 75% of NPK + 25% of N through wheat straw (rice) "
                                             "and rice straw (wheat); 1993-2011 organic C added by CR 61.54 (rice) + 47.72 (wheat) Mg C/ha; total C input T2 40.54, "
                                             "T8 154.36 Mg C/ha. Rice continuous submergence; wheat 5 irrigations. Initial soil: SL, EC 0.4 dS/m, Olsen P 16.4, avail. K 96, S 14.5 kg/ha, WHC 42%."),
      "Treatment details (from paper)": DS_TRT}
DS_NOTE = ("FLAG - FERTILISER OFFSET (rule 62): in T8 crop residue replaces 25% of fertiliser N and 25% of P and K are also cut; drop for a fertiliser-matched "
           "sensitivity check. Wheat tillage not described in detail ('wet tillage followed by dry tillage', residue incorporated) -> conventional. "
           "Supplementary: none found (web search 2026-10-05; publisher site not reachable). Source file 113.pdf.")
LAYERS = [("0-15 CM", "0-7.5 cm", 2), ("0-15 CM", "7.5-15 cm", 2), ("15-30 CM", "15-30 cm", 1)]
FR = "Wet sieving 2, 0.25, 0.053 mm after slaking (Six et al. 2000); macro = LM (>2 mm) + SM (0.25-2 mm); micro = mi (0.053-0.25 mm)"
# Table 4 fractions g/100 g: (LM, SM, mi) for T2, T8
FRAC = {"0-7.5 cm": ((15.33, 55.58, 4.69), (34.15, 57.72, 6.00)), "7.5-15 cm": ((8.20, 66.60, 5.43), (18.50, 64.84, 11.65)),
        "15-30 cm": ((5.30, 54.01, 39.47), (17.40, 65.43, 10.57))}
# Table 5 carbon g/kg: (bulk, LM-C, SM-C, mi-C, cPOM+sand C)
CARB = {"0-7.5 cm": ((7.25, 10.56, 8.02, 5.68, 14.93), (15.11, 14.58, 12.99, 8.91, 22.36)),
        "7.5-15 cm": ((6.53, 9.02, 7.95, 4.85, 6.91), (14.36, 13.65, 9.04, 5.52, 19.85)),
        "15-30 cm": ((5.43, 5.24, 3.63, 3.99, 5.82), (12.38, 13.24, 8.66, 6.17, 7.27))}
MWD_S = {"0-7.5 cm": (1.41, 2.36), "7.5-15 cm": (1.17, 1.64), "15-30 cm": (0.93, 1.62)}
MWD_C = {"0-7.5 cm": (3.86, 4.32), "7.5-15 cm": (3.65, 3.93), "15-30 cm": (3.38, 3.85)}
for depth, rep, D in LAYERS:
    base = {"DEPTH": depth, "DEPTH (as reported in paper)": rep, "Obs": D}
    obsn = f"Obs = {D} (D={D}: {'0-7.5 and 7.5-15 cm both in the 0-15 CM class, separate rows' if D == 2 else 'one layer'}). "
    (b2, l2, s2, m2, c2), (b8, l8, s8, m8, c8) = CARB[rep]
    put("TOC", DS, dict(CT=b2, CTR=b8), "TOC_", UNIT="g/kg (bulk-soil organic C, elemental analyser after HCl)", **{"Data source": "Table 5",
        "Method used (from paper)": "Total organic C by dry combustion, Vario EL elemental analyser, carbonates removed with 15% HCl",
        "Notes/Doubts": obsn + "Bulk-soil organic C measured by DRY COMBUSTION -> TOC sheet (rule 47). Initial Walkley-Black OC 4.1 g/kg in soc (initial). " + DS_NOTE}, **base)
    (L2, S2, M2), (L8, S8, M8) = FRAC[rep]
    mac = put("MACRO", DS, dict(CT=f"=ROUND({L2}+{S2},2)", CTR=f"=ROUND({L8}+{S8},2)"), "MACRO_", UNIT="% (g/100 g soil, LM >2 mm + SM 0.25-2 mm)",
              **{"Data source": "Table 4 - summed", "Method used (from paper)": FR,
                 "Notes/Doubts": obsn + f"Macro = LM + SM (printed LM {L2}/{L8}, SM {S2}/{S8} for T2/T8). Silt+clay (<0.053) T2/T8: "
                 + {"0-7.5 cm": "24.39/2.13", "7.5-15 cm": "19.77/5.01", "15-30 cm": "1.22/6.59"}[rep] + ". " + DS_NOTE}, **base)
    mic = put("MICRO", DS, dict(CT=M2, CTR=M8), "MICRO_", UNIT="% (g/100 g soil, mi 0.053-0.25 mm)", **{"Data source": "Table 4",
              "Method used (from paper)": FR, "Notes/Doubts": obsn + DS_NOTE}, **base)
    put("WSA", DS, {c: f"=ROUND(({B.ref('MACRO', 'MACRO_' + c, mac)}+{B.ref('MICRO', 'MICRO_' + c, mic)})/100,4)" for c in ("CT", "CTR")}, "WSA_",
        UNIT="g/g soil (LM + SM + mi, all fractions >0.053 mm)", **{"Data source": "Table 4 - DERIVED", "Method used (from paper)": FR,
        "Notes/Doubts": "DERIVED (rule 74): WSA = (macro + micro)/100, live links. " + obsn + DS_NOTE}, **base)
    put("macro c", DS, dict(CT=f"=ROUND(({L2}*{l2}+{S2}*{s2})/({L2}+{S2}),2)", CTR=f"=ROUND(({L8}*{l8}+{S8}*{s8})/({L8}+{S8}),2)"), "MACRO c_",
        UNIT="g/kg (C in >0.25 mm aggregates, mass-weighted LM + SM)", **{"Data source": "Tables 4-5 - DERIVED",
        "Method used (from paper)": "C of aggregate fractions by elemental analyser (Vario EL)",
        "Notes/Doubts": f"DERIVED: macro C = (LM x LM-C + SM x SM-C)/(LM + SM); printed LM-C {l2}/{l8}, SM-C {s2}/{s8} g/kg (T2/T8). " + obsn + DS_NOTE}, **base)
    put("micro c", DS, dict(CT=m2, CTR=m8), "MICRO c_", UNIT="g/kg (C in 0.053-0.25 mm aggregates)", **{"Data source": "Table 5",
        "Method used (from paper)": "Elemental analyser (Vario EL)", "Notes/Doubts": obsn + DS_NOTE}, **base)
    put("cPOM-C", DS, dict(CT=c2, CTR=c8), "cPOMC_", UNIT="g/kg (C in cPOM + sand >0.25 mm isolated from macroaggregates)", **{"Data source": "Table 5",
        "Method used (from paper)": "Macroaggregates disrupted with glass beads (Six et al. 2002a); >0.25 mm cPOM + sand retained; C by elemental analyser",
        "Notes/Doubts": "FLAG: C concentration of the cPOM + sand fraction within macroaggregates (Six et al. 2002), not whole-soil cPOM-C. " + obsn + DS_NOTE}, **base)
    put("MWD 1", DS, dict(CT=MWD_S[rep][0], CTR=MWD_S[rep][1]), "MWD_", UNIT="mm (wet sieving, SLAKED pre-treatment)", **{"Data source": "Fig. 2a (digitised)",
        "Method used (from paper)": "Wet sieving after slaking (rapid immersion), Kemper & Rosenau (1986) MWD",
        "Notes/Doubts": "SLAKED aggregates (fast wetting). DIGITISED from the raster Fig. 2a (approx.). " + obsn + DS_NOTE}, **base)
    put("MWD 1", DS, dict(CT=MWD_C[rep][0], CTR=MWD_C[rep][1]), "MWD_", UNIT="mm (wet sieving, CAPILLARY-REWETTED pre-treatment)",
        **{"Data source": "Fig. 2b (digitised)", "Method used (from paper)": "Wet sieving after capillary re-wetting to field capacity (slow wetting)",
           "Notes/Doubts": "CAPILLARY-REWETTED (slow-wetting) pre-treatment - second MWD of the same soil; filter on this flag to keep one MWD per study. DIGITISED from Fig. 2b (approx.). " + obsn + DS_NOTE}, **base)
    # aggregate water retention (Table 3), two aggregate sizes
    WR = {"0-7.5 cm": {"2-5 mm": (22.9, 23.2, 10.0, 10.2), "5-8 mm": (22.3, 25.2, 7.1, 8.1)},
          "7.5-15 cm": {"2-5 mm": (19.7, 20.4, 8.0, 8.5), "5-8 mm": (20.7, 22.2, 9.9, 9.3)},
          "15-30 cm": {"2-5 mm": (19.5, 19.8, 8.8, 6.3), "5-8 mm": (19.8, 20.0, 10.1, 8.3)}}
    for size, (f2, f8, p2, p8) in WR[rep].items():
        wq = (f"WATER-QUANTITY CHECK: water retained by {size} AGGREGATES packed in cylinders and equilibrated at -33 kPa (FC) and -1500 kPa (PWP) on a pressure plate; "
              "oven-dried to determine water -> weight basis assumed (printed '%'). FLAG: AGGREGATE-SCALE retention, not bulk-soil FC/PWP. ")
        mt = {"Method used (from paper)": f"Pressure plate (Soil Moisture Equipment Corp.), {size} aggregates in 5 x 2.5 cm cylinders, 2-3 wet-dry cycles"}
        fr = put("FC (weight basis)", DS, dict(CT=f2, CTR=f8), "FC_", UNIT=f"% w/w ({size} aggregates, -33 kPa)", **{"Data source": "Table 3", "Notes/Doubts": wq + obsn + DS_NOTE}, **mt, **base)
        pr = put("PWP (weight basis)", DS, dict(CT=p2, CTR=p8), "PWP_", UNIT=f"% w/w ({size} aggregates, -1500 kPa)", **{"Data source": "Table 3", "Notes/Doubts": wq + obsn + DS_NOTE}, **mt, **base)
        ar = put("AWC (weight basis)", DS, {c: f"=ROUND({B.ref('FC (weight basis)', 'FC_' + c, fr)}-{B.ref('PWP (weight basis)', 'PWP_' + c, pr)},2)" for c in ("CT", "CTR")},
                 "AWCW_", UNIT=f"% w/w (FC - PWP, {size} aggregates)", **{"Data source": "Table 3 - DERIVED", "Notes/Doubts": "DERIVED: AWC = FC - PWP. " + wq + obsn + DS_NOTE}, **mt, **base)
        put("AWC (volume basis)", DS, {c: f"=ROUND({B.ref('AWC (weight basis)', 'AWCW_' + c, ar)}*1.55,2)" for c in ("CT", "CTR")}, "AWCV_",
            UNIT=f"% v/v (AWCw x initial BD 1.55, {size} aggregates)", **{"Data source": "Table 3 - DERIVED",
            "Notes/Doubts": "DERIVED: AWCv = AWCw x 1.55 Mg/m3 (paper's initial BD; no treatment bulk density printed - aggregate densities in notes). " + wq + obsn + DS_NOTE}, **mt, **base)
# Yield (Fig. 1, 3-year means)
for label, yrs, dur, rice, wheat, src in [
        ("initial 1993-94 to 1995-96", "1993-96", 2, (4.89, 4.61), (4.45, 4.00), "T2 rice 4.89 printed in text; others digitised"),
        ("final 2008-09 to 2010-11", "2008-11", 17, ("=ROUND(4.89-1.47,2)", 5.13), (3.57, 4.23), "T2 rice = 4.89 - 1.47 (printed decline); others digitised")]:
    B.add("YIELD", {**DS, "year of data collection/experiment": yrs, "DURATION": dur_class(dur), "YEAR OF DATA (duration)": dur,
                    "RICE YIELD_CT": rice[0], "RICE YIELD_CTR": rice[1], "WYIELD_CT": wheat[0], "WYIELD_CTR": wheat[1], "Obs": 3,
                    "UNIT": "t/ha grain (3-year moving average)", "Crop/season of sampling": f"Rice and wheat, {label}",
                    "Data source": "Fig. 1 (digitised) + text", "Method used (from paper)": "Grain yield; 3-year moving averages",
                    "Notes/Doubts": (f"3-YEAR MEAN ({label}); year-wise values not printed. {src}. Obs = 3 (Y). Sustainability index T2/T8: rice 0.61/0.72, wheat 0.72/0.83. "
                                     "Aggregate properties not on a sheet (Table 3, T2/T8): density 0-7.5 cm 1.77/1.60, 7.5-15 1.81/1.65, 15-30 1.89/1.73 Mg/m3; tensile strength 113.4/79.6, "
                                     "122.1/81.2, 163.4/117.2 kPa; friability 0.18/0.34, 0.15/0.31, 0.13/0.27. NSI (Fig. 3) not digitised. " + DS_NOTE)})

# =====================================================================================
# 164  YADAV et al. 2000 (7 sites)
# =====================================================================================
YD_TRT = ("TREATMENTS IN PAPER (network long-term experiment, RBD 4 reps, plots 6 x 5 m, since 1983): Control (no fertiliser/manure); 50F (50% NPK rice, "
          "100% wheat); 100F (100% NPK both crops) ; 50F+FYM, 50F+CR, 50F+GM = 50% NPK + 50% of recommended N through FYM, wheat crop residue (CR) or "
          "Sesbania green manure TO RICE ONLY, wheat 100% NPK. Recommended 120-26-33 kg N-P-K/ha each crop. Rice transplanted (puddled) 20 x 10 cm, wheat "
          "sown in 23 cm rows; above-ground biomass of both crops removed (sickle at ground level) except the CR returned in 50F+CR. 100F -> CT ; 50F+CR -> CTR "
          "(FLAG fertiliser offset, rule 62); Control, 50F, 50F+FYM, 50F+GM EXCLUDED.")
YD_NOTE = ("FLAG - FERTILISER OFFSET (rule 62): 50F+CR gets only 50% NPK to rice (wheat straw supplies the other 50% of N; P cut, K over-supplied) and 100% NPK to wheat; "
           "wheat straw is incorporated 1 month before rice transplanting (residue enters before the RICE phase only). Wheat tillage not described -> conventional "
           "(puddled transplanted rice + tilled wheat). Supplementary: none found (web search 2026-10-05; publisher site not reachable). Source file 112.pdf.")
SITES = {
    "Ludhiana": dict(state="Punjab", lat=30.933, lon=75.867, rep=("30 deg 56'N", "75 deg 52'E"), soil="LOAMY", tex="sandy loam (Ustochrepts-Ustipsamments)", rain=500,
                     start=1983, years=[f"{y}-{str(y+1)[2:]}" for y in range(1983, 1998)], ini=(3.1, 65, 5.1, 46), cr=13.0, ph=None),
    "Pantnagar": dict(state="Uttarakhand (then Uttar Pradesh)", lat=29.0, lon=79.083, rep=("29 deg N", "79 deg 5'E"), soil="LOAMY", tex="silt loam (Hapludolls), neutral", rain=1350,
                      start=1983, years=[f"{y}-{str(y+1)[2:]}" for y in range(1983, 1998)], ini=(14.2, 102, 9.1, 65), cr=15.8, ph=None),
    "Kanpur": dict(state="Uttar Pradesh", lat=26.967, lon=80.567, rep=("26 deg 58'N", "80 deg 34'E"), soil=None, tex="alluvial Udic Ustochrepts, pH ~8.0 (texture not stated)", rain=818,
                   start=1985, years=[f"{y}-{str(y+1)[2:]}" for y in range(1985, 1998)], ini=(2.9, 83, 6.3, 82), cr=8.8, ph=8.0),
    "Faizabad": dict(state="Uttar Pradesh", lat=26.067, lon=82.133, rep=("26 deg 4'N", "82 deg 8'E"), soil="LOAMY", tex="silt loam (Udic Fluvents-Fluaquents)", rain=1100,
                     start=1984, years=[f"{y}-{str(y+1)[2:]}" for y in range(1984, 1998)], ini=(3.7, 46, 6.3, 161), cr=10.7, ph=None),
    "Sabour": dict(state="Bihar", lat=25.233, lon=87.067, rep=("25 deg 14'N", "87 deg 4'E"), soil="CLAYEY", tex="clayey (Ustochrepts)", rain=1358,
                   start=1984, years=[f"{y}-{str(y+1)[2:]}" for y in range(1984, 1993)] + ["one season 1993-94 to 1995-96 (unlabelled)", "1996-97", "1997-98"],
                   ini=(4.6, None, 4.5, 58), cr=9.2, ph=None),
    "Kalyani": dict(state="West Bengal", lat=23.0, lon=89.0, rep=("23 deg N", "89 deg E"), soil=None, tex="alluvial Udic Ustochrepts (texture not stated)", rain=None,
                    start=1986, years=[f"{y}-{str(y+1)[2:]}" for y in range(1986, 1999)], ini=(9.2, 45, 7.3, 36), cr=14.1, ph=None),
    "Jabalpur": dict(state="Madhya Pradesh", lat=23.167, lon=79.95, rep=("23 deg 10'N", "79 deg 57'E"), soil="CLAYEY", tex="clayey (Chromusterts)", rain=850,
                     start=1985, years=[f"{y}-{str(y+1)[2:]}" for y in range(1985, 1998)], ini=(6.9, 261, 9.5, 408), cr=12.2, ph=None),
}
SITE_YEARS = {"Ludhiana": 15, "Pantnagar": 15, "Kanpur": 13, "Faizabad": 14, "Sabour": 12, "Kalyani": 13, "Jabalpur": 12}
T3 = {"Ludhiana": (6083, 5059, 4459, 4400), "Pantnagar": (4564, 3841, 3753, 3449), "Kanpur": (4470, 3658, 4532, 4384), "Faizabad": (4205, 3780, 3449, 3310),
      "Sabour": (4111, 3873, 3128, 3154), "Kalyani": (3328, 3467, 2671, 3093), "Jabalpur": (5094, 4371, 2553, 2483)}
yy = json.load(open(os.path.join(DIG, "yadav_yields.json")))
ss = json.load(open(os.path.join(DIG, "yadav_soil.json")))
for site, S in SITES.items():
    YB = {"No.": 164, "SERIAL NO": 164, "Authors": "Yadav R.L., Dwivedi B.S., Prasad K., Tomar O.K., Shurpali N.J. & Pandey P.S.", "Year": 2000,
          "Journal": "Field Crops Research", "Country": f"India ({S['state']})", "Site/Location": f"{site} - PDCSR network long-term experiment",
          "latitude": S["lat"], "longitude": S["lon"], "CLIMATE": "TEMP" if S["lat"] > 30 else "ST", "SOIL": S["soil"], "Rep": 4,
          "RAIN FALL": S["rain"], "LATT": S["lat"], "ph (initial)": S["ph"], "soc (initial)": S["ini"][0],
          "Treatment mapping (paper's name -> code)": "100F -> CT ; 50F+CR -> CTR [FLAG: fertiliser offset]",
          "Fertilizer dose & other management": (f"100F: 120-26-33 kg N-P-K/ha to rice and wheat. 50F+CR: 60-13-16.5 N-P-K + wheat straw {S['cr']} t/ha/yr to rice "
                                                 f"(supplying 60 kg N), wheat 120-26-33. Irrigated; rice 5 cm flooding, wheat 5 irrigations. Initial soil (0-15 cm): OC {S['ini'][0]} g/kg, "
                                                 f"avail. N {S['ini'][1]}, P {S['ini'][2]}, K {S['ini'][3]} mg/kg."),
          "Treatment details (from paper)": YD_TRT}
    tn = f"Site {site}: {S['tex']}; rainfall {S['rain']} mm. Coordinates as printed ({S['rep'][0]}, {S['rep'][1]})."
    if site == "Faizabad":
        tn += " Printed coordinates (26 deg 4'N, 82 deg 8'E) are ~50 km from NDUAT Kumarganj (26.54 N, 81.84 E) - kept as printed, flag."
    if site == "Kalyani":
        tn += " Kalyani printed only to whole degrees (23 N, 89 E; BCKV Kalyani is ~22.98 N, 88.43 E) - kept as printed, flag."
    # ---- year-wise yields
    r = yy[site]["rice"]
    w = yy[site]["wheat"]
    n = len(S["years"])
    for i in range(n):
        yname = S["years"][i]
        rc, rr_ = r["100F"][i], r["CR"][i]
        wi = i
        wnote = ""
        if site == "Jabalpur":
            # wheat panels hold 12 seasons (85-86 .. 97-98 minus one of 88-89 / 89-90; mean of the first 12 100F points = Table 3);
            # the two trailing 100F points are outside that series and are not used
            wi = {3: 3, 4: None}.get(i, i if i < 3 else i - 1)
            if i == 3:
                wnote = "Wheat season attribution uncertain (1988-89 or 1989-90: the Fig. 2g wheat axis has 12 seasons and skips one of them). "
            if i == 4:
                wnote = "No wheat value attributed to this season (see 1988-89 row). "
        wc = w["100F"][wi] if wi is not None and wi < len(w["CR"]) else None
        wr_ = w["CR"][wi] if wi is not None and wi < len(w["CR"]) else None
        if site == "Faizabad" and i >= 12:
            wnote = f"Wheat 50F+CR not plotted for this season (Fig. 2d shows 12 CR points, 14 for 100F); 100F wheat {w['100F'][i]} t/ha kept in notes only. "
        dur = i + 1 if site != "Sabour" else (i + 1 if i < 9 else {9: 11, 10: 13, 11: 14}[i])
        if site == "Jabalpur" and i == 12:
            pass
        B.add("YIELD", {**YB, "year of data collection/experiment": yname, "DURATION": dur_class(dur), "YEAR OF DATA (duration)": dur,
                        "RICE YIELD_CT": rc, "RICE YIELD_CTR": rr_, "WYIELD_CT": wc, "WYIELD_CTR": wr_, "Obs": 1,
                        "UNIT": "t/ha grain", "Crop/season of sampling": f"Rice (kharif) and wheat (rabi) {yname}",
                        "Data source": f"Fig. 2{'abcdefg'[list(SITES).index(site)]} (digitised, year-wise)",
                        "Method used (from paper)": "Grain yield from 5 x 4 m net plot, crops harvested at ground level",
                        "Notes/Doubts": (f"YEAR-WISE (rule 37). DIGITISED from the vector-rasterised Fig. 2 (markers located automatically; site means reproduce Table 3 within ~1-3%). {wnote}"
                                         f"Table 3 site means (kg/ha) 100F/50F+CR: rice {T3[site][0]}/{T3[site][1]}, wheat {T3[site][2]}/{T3[site][3]}. " + tn + " " + YD_NOTE)})
    # ---- soil after the final wheat harvest
    fy = S["years"][-1] if site != "Sabour" else "1997-98"
    nyr = SITE_YEARS[site]
    sb = {**YB, "year of data collection/experiment": fy, "DURATION": dur_class(nyr), "YEAR OF DATA (duration)": nyr,
          "DEPTH": "0-15 CM", "DEPTH (as reported in paper)": "0-15 cm", "Obs": 1,
          "Crop/season of sampling": f"Wheat season - final year, after wheat harvest in April ({fy})"}
    oc = ss["OC"][site]
    put("SOC(active C pool)", sb, dict(CT=oc["100F"], CTR=oc["50F+CR"]), "SOC_", UNIT="g/kg", **{"Data source": "Fig. 4 (digitised)",
        "Method used (from paper)": "Walkley & Black OC (Page et al. 1982)",
        "Notes/Doubts": (f"DIGITISED from Fig. 4 (bar tops; the initial-OC bars reproduce Table 1 within 0.05 g/kg). Initial {oc['Initial']} (fig) / {S['ini'][0]} (Table 1). "
                         + ("FLAG: 50F+CR bar at Ludhiana (1.51) is below the unfertilised control (2.11) as plotted - verify. " if site == "Ludhiana" else "")
                         + ("Fig. 4 initial bar 9.7 vs Table 1 9.2 g/kg. " if site == "Kalyani" else "") + tn + " " + YD_NOTE)}, **sb)
    if site in ss["N"]:
        nn = ss["N"][site]
        put("N", sb, dict(CT=f"=ROUND({nn['100F']}*2.24,1)", CTR=f"=ROUND({nn['50F+CR']}*2.24,1)"), "N_", UNIT="kg/ha (digitised mg/kg x 2.24)",
            **{"Data source": "Fig. 5 (digitised) - converted", "Method used (from paper)": "Alkaline KMnO4 available N",
               "Notes/Doubts": f"DIGITISED from Fig. 5 (mg/kg) and x 2.24 (0-15 cm). Fig. 5 shows only Ludhiana, Faizabad, Kalyani and Jabalpur. " + tn + " " + YD_NOTE}, **sb)
    pp, kk = ss["P"][site], ss["K"][site]
    put("P", sb, dict(CT=f"=ROUND({pp['100F']}*2.24,2)", CTR=f"=ROUND({pp['50F+CR']}*2.24,2)"), "P_", UNIT="kg/ha (digitised Olsen P mg/kg x 2.24)",
        **{"Data source": "Fig. 6 (digitised) - converted", "Method used (from paper)": "0.5 M NaHCO3 (pH 8.5) extractable P",
           "Notes/Doubts": "DIGITISED from Fig. 6 (initial bars reproduce Table 1) and x 2.24. " + tn + " " + YD_NOTE}, **sb)
    put("K", sb, dict(CT=f"=ROUND({kk['100F']}*2.24,1)", CTR=f"=ROUND({kk['50F+CR']}*2.24,1)"), "K_", UNIT="kg/ha (digitised NH4OAc-K mg/kg x 2.24)",
        **{"Data source": "Fig. 7 (digitised) - converted", "Method used (from paper)": "1 N NH4OAc extractable K",
           "Notes/Doubts": "DIGITISED from Fig. 7 (initial bars reproduce Table 1) and x 2.24. " + tn + " " + YD_NOTE}, **sb)

# =====================================================================================
# Study_Info, LAT_LONG, Treatment_Mapping, EXCLUDED_rows
# =====================================================================================
def study(d):
    B.add("Study_Info", d)


common_supp = "None found - web search 2026-10-05 (publisher pages not reachable from this environment)"
study({"No.": 164, "SERIAL NO": 164, "Authors": "Yadav R.L., Dwivedi B.S., Prasad K., Tomar O.K., Shurpali N.J. & Pandey P.S.", "Year": 2000,
       "Journal": "Field Crops Research", "Full reference": "Yadav RL et al. (2000) Yield trends, and changes in soil organic-C and available NPK in a long-term rice-wheat system under integrated use of manures and fertilisers. Field Crops Res 68:219-246",
       "DOI / link": "https://doi.org/10.1016/S0378-4290(00)00126-X", "Country": "India (7 sites)", "Site/Location": "Ludhiana, Pantnagar, Kanpur, Faizabad, Sabour, Kalyani, Jabalpur (one row per site in data sheets)",
       "Coordinates source": "Paper (each site); see LAT_LONG", "CLIMATE": "ST (Ludhiana TEMP)", "Experiment established (year)": "1983-1986 (by site)",
       "year of data collection/experiment": "1983-84 to 1998-99", "Years of data reported": "12-15 seasons per site (year-wise yields); soil after final wheat",
       "DURATION": ">10 Y", "Crop rotation": "Rice-wheat (transplanted rice)", "N dose (kg/ha)": "120 (100F); 60 + CR (50F+CR rice)", "P dose (kg/ha)": 26, "K dose (kg/ha)": 33,
       "Residue type & rate (t/ha)": "Wheat straw to rice: 8.8-15.8 t/ha/yr (by site) in 50F+CR", "Irrigation / water management": "Irrigated; rice 5 cm flooding; wheat 5 irrigations",
       "Treatments in paper": YD_TRT, "Parameters extracted": "YIELD (year-wise rice & wheat, 7 sites); SOC; available N (4 sites), P, K (final year)",
       "Supplementary data?": common_supp,
       "Notes/Doubts": "INCLUDED FLAGGED (rule 62): 100F (CT) vs 50F+CR (CTR) - fertiliser cut offset by straw. Yields digitised year-wise from Fig. 2 and validated against Table 3 means. " + YD_NOTE})
study({"No.": 165, "SERIAL NO": 165, "Authors": "Davari M.R., Sharma S.N. & Mirzakhani M.", "Year": 2012, "Journal": "Biological Agriculture & Horticulture",
       "Full reference": "Davari MR, Sharma SN, Mirzakhani M (2012) Effect of cropping systems and crop residue incorporation on production and properties of soil in an organic agroecosystem. Biol Agric Hortic 28(3):206-222",
       "DOI / link": "https://doi.org/10.1080/01448765.2012.735005", "Country": "India (Delhi)", "Site/Location": DV["Site/Location"],
       "latitude": 28.633, "longitude": 77.183, "latitude (as reported)": "28 deg 38'N", "longitude (as reported)": "77 deg 11'E", "Coordinates source": "Paper",
       "CLIMATE": "ST", "Experiment established (year)": 2006, "year of data collection/experiment": "2006-07, 2007-08", "Years of data reported": 2,
       "DURATION": "0-3 Y", "SOIL": "LOAMY", "Texture as reported": "Sandy clay loam", "sand": 52.06, "silt": 22.54, "CLAY": 25.40, "ph (initial)": 8.16,
       "soc (initial)": 5.20, "Bdi": 1.50, "Crop rotation": "Rice-wheat and rice-wheat-mungbean (organic)", "Wheat variety": "HD 2643", "Rice variety": "Pusa Basmati 1",
       "N dose (kg/ha)": "60 (FYM-N, organic)", "Residue type & rate (t/ha)": "All residues incorporated in RI: 14.2-19.7 Mg DM/ha/yr",
       "Irrigation / water management": "Rice flooded/puddled; mungbean 2 irrigations", "Treatments in paper": DV_TRT,
       "Parameters extracted": "Rice, wheat, rice-equivalent yield (year-wise); SOC, Kjeldahl N, Olsen P, NH4OAc K (year-wise); BD, porosity, HC; bacteria, fungi, actinomycetes, MBC, DHA, CO2 evolution",
       "Supplementary data?": common_supp, "Notes/Doubts": "INCLUDED: RR (CT) vs RI (CTR) in RW and in RWM (mungbean in both treatments of the RWM row, flagged). Protein yield and energy output (Figs 1-2) have no sheet. " + DV_NOTE})
study({"No.": 166, "SERIAL NO": 166, "Authors": DS["Authors"], "Year": 2014, "Journal": "Soil & Tillage Research",
       "Full reference": "Das B et al. (2014) Effect of integrated nutrient management practice on soil aggregate properties, its stability and aggregate-associated carbon content in an intensive rice-wheat system. Soil Tillage Res 136:9-18",
       "DOI / link": "https://doi.org/10.1016/j.still.2013.09.009", "Country": "India (Uttar Pradesh)", "Site/Location": DS["Site/Location"],
       "latitude": 29.067, "longitude": 77.767, "latitude (as reported)": "29 deg 4'N", "longitude (as reported)": "77 deg 46'E", "Coordinates source": "Paper",
       "CLIMATE": "ST", "Experiment established (year)": 1993, "year of data collection/experiment": 2011, "Years of data reported": "Soil 2011; yields as 3-yr means 1993-96 and 2008-11",
       "DURATION": ">10 Y", "SOIL": "LOAMY", "Texture as reported": "Sandy loam", "sand": 55, "silt": 18, "CLAY": 27, "ph (initial)": 7.98, "soc (initial)": 4.1, "Bdi": 1.55,
       "MIN TEMP": 5, "MAX TEMP": 45.5, "RAIN FALL": 863, "Crop rotation": "Rice-wheat", "Wheat variety": "HD 2338", "Rice variety": "Saket 4",
       "N dose (kg/ha)": "120 (T2); 90 + CR (T8)", "P dose (kg/ha)": 26, "K dose (kg/ha)": 33, "Residue type & rate (t/ha)": "T8: rice and wheat straw supplying 25% of N (61.5 + 47.7 Mg C/ha over 18 yr)",
       "Irrigation / water management": "Rice continuous 5 cm submergence; wheat 5 irrigations", "Treatments in paper": DS_TRT,
       "Parameters extracted": "TOC; macro/micro aggregates, WSA (derived), MWD (slaked + capillary), macro-C, micro-C, cPOM-C; aggregate FC/PWP/AWC; yields (3-yr means)",
       "Supplementary data?": common_supp, "Notes/Doubts": "INCLUDED FLAGGED (rule 62): T2 (CT) vs T8 (CTR). " + DS_NOTE})
study({"No.": 167, "SERIAL NO": 167, "Authors": "Naz A., Rebi A., Naz R., Akbar M.U., Aslam A., Kalsom A., Niaz A., Ahmad M.I., Nawaz S., Kausar R., Ali B., Saleem M.H. & Zhou J.",
       "Year": 2023, "Journal": "Land", "Full reference": "Naz A et al. (2023) Impact of green manuring on health of low fertility calcareous soils. Land 12:546",
       "DOI / link": "https://doi.org/10.3390/land12030546", "Country": "Pakistan (Punjab)", "Site/Location": "Khushab / Faisalabad, Punjab (calcareous soil field trial)",
       "Experiment established (year)": 2015, "year of data collection/experiment": "2015-2018", "Crop rotation": "Rice-berseem (green manure)",
       "Treatments in paper": "Control; NPK (100% RDF); GM100, GM75, GM50 = berseem green manure (last cutting rotavated in) + 100/75/50% RDF; rice puddled-transplanted in all",
       "Parameters extracted": "NONE (excluded)", "Supplementary data?": common_supp,
       "Notes/Doubts": "EXCLUDED: rice-berseem green-manure x fertiliser-dose trial - no wheat phase in the treatments, identical (puddled/rotavator) tillage and no crop-residue contrast; green manure is an amendment here, not part of a CA treatment (rule 34; rule 71 lets GM support CA, but there is no CA). Source file 111_real.pdf."})
study({"No.": 168, "SERIAL NO": 168, "Authors": DH["Authors"], "Year": 2020, "Journal": "Soil Research",
       "Full reference": "Dhaliwal JK, Singh MJ, Sharma S, Gupta N, Kukal SS (2020) Medium-term impact of tillage and residue retention on soil physical and biological properties in dry-seeded rice-wheat system in north-west India. Soil Research 58:468-477",
       "DOI / link": "https://doi.org/10.1071/SR19238", "Country": "India (Punjab)", "Site/Location": DH["Site/Location"],
       "latitude": 30.933, "longitude": 75.867, "latitude (as reported)": "30 deg 56'N", "longitude (as reported)": "75 deg 52'E", "Coordinates source": "Paper",
       "CLIMATE": "TEMP", "Experiment established (year)": 2011, "year of data collection/experiment": 2016, "Years of data reported": 1, "DURATION": "4-10 Y",
       "SOIL": "LOAMY", "Texture as reported": "Sandy loam (Typic Ustochrept)", "ph (initial)": 7.4, "RAIN FALL": 734,
       "Crop rotation": "Dry-seeded rice-wheat", "Wheat variety": "PBW 621", "Rice variety": "PR 115", "Residue type & rate (t/ha)": "Rice residue 7 t/ha surface mulch in wheat (+M)",
       "Irrigation / water management": "Irrigated (PAU recommendations)", "Treatments in paper": DH_TRT,
       "Parameters extracted": "SOC, SOC stock, macro/micro WSA, WSA (derived), MWD, BD, porosity (derived), IR (initial + steady), FC/PWP/AWC, MBC, BSR, DHA, urease, ALP, ACP",
       "Supplementary data?": common_supp, "Notes/Doubts": "INCLUDED: CT, CTR, ZT, CA. ALL ROWS RED (rice-season fallback - sampling after 2016 rice harvest only). Enzymes = tillage main effects (flagged). " + DH_MAP_NOTE})

for site, S in SITES.items():
    B.add("LAT_LONG", {"No.": 164, "SERIAL NO": 164, "Authors": "Yadav R.L. et al.", "Year": 2000, "Country": f"India ({S['state']})", "Site/Location": site,
                       "latitude (as reported)": S["rep"][0], "longitude (as reported)": S["rep"][1], "latitude": S["lat"], "longitude": S["lon"],
                       "Coordinates source": "Paper", "CLIMATE": "TEMP" if S["lat"] > 30 else "ST",
                       "Notes": {"Faizabad": "Printed coords ~50 km from NDUAT Kumarganj (26.54 N, 81.84 E) - kept as printed",
                                 "Kalyani": "Printed to whole degrees; BCKV Kalyani ~22.98 N, 88.43 E", "Pantnagar": "GBPUAT Pantnagar ~29.02 N, 79.48 E; printed 79 deg 5'E"}.get(site)})
for no, au, yr, ctry, site, la, lo, lar, lor, src, cl, note in [
        (165, "Davari M.R. et al.", 2012, "India (Delhi)", "IARI, New Delhi", 28.633, 77.183, "28 deg 38'N", "77 deg 11'E", "Paper", "ST", None),
        (166, "Das B. et al.", 2014, "India (Uttar Pradesh)", "PDFSR Modipuram, Meerut", 29.067, 77.767, "29 deg 4'N", "77 deg 46'E", "Paper", "ST", None),
        (167, "Naz A. et al.", 2023, "Pakistan (Punjab)", "Khushab / Faisalabad", None, None, None, None, "Not given (study excluded)", None, "EXCLUDED study"),
        (168, "Dhaliwal J.K. et al.", 2020, "India (Punjab)", "PAU, Ludhiana", 30.933, 75.867, "30 deg 56'N", "75 deg 52'E", "Paper", "TEMP", None)]:
    B.add("LAT_LONG", {"No.": no, "SERIAL NO": no, "Authors": au, "Year": yr, "Country": ctry, "Site/Location": site, "latitude (as reported)": lar,
                       "longitude (as reported)": lor, "latitude": la, "longitude": lo, "Coordinates source": src, "CLIMATE": cl, "Notes": note})

TM = [
    (164, "Yadav R.L. et al.", 2000, "Control", "No fertiliser or manure to either crop", "Puddled TPR", "Conventional (not described)", "No", None, "EXCLUDED", "Unfertilised control (rule 34)", "High", "EXCLUDED"),
    (164, "Yadav R.L. et al.", 2000, "50F", "50% NPK to rice, 100% to wheat", "Puddled TPR", "Conventional", "No", None, "EXCLUDED", "Sub-optimal fertiliser tier, no residue/tillage contrast", "High", "EXCLUDED"),
    (164, "Yadav R.L. et al.", 2000, "100F", "100% recommended NPK (120-26-33) to rice and wheat; all biomass removed", "Puddled TPR", "Conventional", "No", None, "CT", "Conventional rice + wheat, residue removed", "Medium (wheat tillage not described)", "INCLUDED"),
    (164, "Yadav R.L. et al.", 2000, "50F + FYM", "50% NPK + 50% N through FYM to rice; 100% NPK wheat", "Puddled TPR", "Conventional", "No", None, "EXCLUDED", "Amendment (FYM), rule 34", "High", "EXCLUDED"),
    (164, "Yadav R.L. et al.", 2000, "50F + CR", "50% NPK + 50% N through wheat crop residue incorporated 1 month before rice; 100% NPK wheat", "Puddled TPR", "Conventional", "Yes (wheat straw to rice)", "8.8-15.8 by site", "CTR", "Straw return with fertiliser cut to offset -> CTR FLAGGED (rule 62)", "Medium", "INCLUDED - FLAGGED"),
    (164, "Yadav R.L. et al.", 2000, "50F + GM", "50% NPK + 50% N through Sesbania green manure to rice; 100% NPK wheat", "Puddled TPR", "Conventional", "No (GM)", None, "EXCLUDED", "Green manure in a conventional system - amendment; GM only supports CA (rule 71)", "High", "EXCLUDED"),
    (165, "Davari M.R. et al.", 2012, "RW-RR", "Rice-wheat, residue removed (organic, FYM 60 kg N)", "Puddled (offset disc)", "Heavy disc + disk & plank x2", "No", None, "CT", "Conventional in both phases", "High", "INCLUDED"),
    (165, "Davari M.R. et al.", 2012, "RW-RI", "Rice-wheat, all residue incorporated", "Puddled (offset disc)", "Heavy disc + disk & plank x2", "Yes (incorporated)", "14.2-16.0 Mg DM/yr", "CTR", "Conventional + residue incorporation", "High", "INCLUDED"),
    (165, "Davari M.R. et al.", 2012, "RWM-RR", "Rice-wheat-mungbean, residue removed", "Puddled (offset disc)", "Heavy disc + disk & plank x2", "No", None, "CT", "Conventional; summer mungbean in both RWM treatments (flag)", "High", "INCLUDED"),
    (165, "Davari M.R. et al.", 2012, "RWM-RI", "Rice-wheat-mungbean, all residue incorporated", "Puddled (offset disc)", "Heavy disc + disk & plank x2", "Yes (incorporated)", "17.8-19.7 Mg DM/yr", "CTR", "Conventional + residue; mungbean in both (flag)", "High", "INCLUDED"),
    (166, "Das B. et al.", 2014, "T1", "Unfertilised", "Puddled TPR", "Dry tillage", "No", None, "EXCLUDED", "Unfertilised control", "High", "EXCLUDED"),
    (166, "Das B. et al.", 2014, "T2", "Recommended NPK (+Zn rice) through fertilisers", "Puddled TPR", "Dry tillage (conventional)", "No", None, "CT", "Conventional, residue removed", "High", "INCLUDED"),
    (166, "Das B. et al.", 2014, "T3", "NPK + Zn + S", "Puddled TPR", "Dry tillage", "No", None, "EXCLUDED", "Nutrient tier (S), no residue contrast", "High", "EXCLUDED"),
    (166, "Das B. et al.", 2014, "T4", "75% NPK + 25% N via FYM (rice)", "Puddled TPR", "Dry tillage", "No", None, "EXCLUDED", "Amendment (FYM)", "High", "EXCLUDED"),
    (166, "Das B. et al.", 2014, "T5", "75% NPK + 25% N via sulphitation press mud (rice)", "Puddled TPR", "Dry tillage", "No", None, "EXCLUDED", "Amendment (press mud)", "High", "EXCLUDED"),
    (166, "Das B. et al.", 2014, "T6", "75% NPK + green gram residue before rice", "Puddled TPR", "Dry tillage", "Green gram residue", None, "EXCLUDED", "Third crop (green gram) in some treatments only (rule 30); GM only supports CA", "High", "EXCLUDED"),
    (166, "Das B. et al.", 2014, "T7", "T6 + 75% NPK + 25% N via FYM (wheat)", "Puddled TPR", "Dry tillage", "Green gram residue", None, "EXCLUDED", "Third crop + FYM", "High", "EXCLUDED"),
    (166, "Das B. et al.", 2014, "T8", "75% NPK + 25% N via wheat straw (rice) and rice straw (wheat)", "Puddled TPR", "Dry tillage (straw incorporated)", "Yes (both crops)", "N-equivalent (61.5 + 47.7 Mg C over 18 yr)", "CTR", "Straw return with fertiliser cut -> CTR FLAGGED (rule 62)", "Medium", "INCLUDED - FLAGGED"),
    (167, "Naz A. et al.", 2023, "Control / NPK / GM100 / GM75 / GM50", "Rice-berseem; berseem GM with 100/75/50% RDF vs NPK and control", "Puddled TPR", "No wheat (berseem)", "No", None, "EXCLUDED", "Not a rice-wheat tillage/residue study", "High", "EXCLUDED"),
    (168, "Dhaliwal J.K. et al.", 2020, "CTW-CTDSR (-M)", "CT wheat (disc + tyne harrow + plank) after CT dry-seeded rice, residue removed", "CT DSR", "CT", "No", None, "CT", "Conventional both phases", "High", "INCLUDED"),
    (168, "Dhaliwal J.K. et al.", 2020, "CTW+M-CTDSR", "As above + 7 t/ha rice residue mulch in wheat", "CT DSR", "CT", "Yes (surface mulch)", 7, "CTR", "Conventional + residue", "High", "INCLUDED"),
    (168, "Dhaliwal J.K. et al.", 2020, "ZTW-ZTDSR", "ZT wheat (Turbo Happy Seeder) after ZT DSR, residue removed", "ZT DSR", "ZT", "No", None, "ZT", "Zero till both phases, no residue", "High", "INCLUDED"),
    (168, "Dhaliwal J.K. et al.", 2020, "ZTW+M-ZTDSR", "ZT wheat + rice residue mulch after ZT DSR", "ZT DSR", "ZT", "Yes (surface mulch)", 7, "CA", "Zero till both phases + residue", "High", "INCLUDED"),
]
th = ["SERIAL NO", "Authors", "Year", "Paper's treatment label (verbatim)", "Full description from paper", "Rice-phase tillage", "Wheat-phase tillage",
      "Residue retained?", "Residue rate (t/ha)", "ASSIGNED CODE", "Rationale", "Confidence", "Status"]
for row in TM:
    d = dict(zip(th, row))
    d["No."] = row[0]
    B.add("Treatment_Mapping", d)

B.add("EXCLUDED_rows", {"Sheet": "(whole study)", "SERIAL NO": 167, "Authors": "Naz A. et al.", "Year": 2023,
                        "Reason for exclusion": "Rice-berseem green-manure x fertiliser-dose trial: no wheat phase in treatments, no tillage or crop-residue contrast (rule 34). No data rows entered.",
                        "Full row (header = value)": "Treatments: Control, NPK, GM100, GM75, GM50; parameters: rice growth/yield, BD, porosity, OC, N, P, K, micronutrients (2015-2018)."})
for sid, au, yr, why in [(164, "Yadav R.L. et al.", 2000, "Treatments Control, 50F, 50F+FYM, 50F+GM not entered (unfertilised / fertiliser tier / FYM / green-manure amendments). Values in Table 3 and Figs 2-7 of the paper."),
                         (166, "Das B. et al.", 2014, "Treatments T1, T3-T7 not entered (unfertilised, S tier, FYM, press mud, green gram in some treatments only).")]:
    B.add("EXCLUDED_rows", {"Sheet": "(treatments)", "SERIAL NO": sid, "Authors": au, "Year": yr, "Reason for exclusion": why, "Full row (header = value)": "-"})

B.save(OUT)
print("saved", OUT)
