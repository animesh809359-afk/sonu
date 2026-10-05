"""Batch 14 (2026-10-05). Uploaded files 126_2.pdf, 126_real_f2f.pdf (byte-identical duplicate), 126_real.pdf, 125_real.pdf, 125.pdf.

  177                Zhao Z. et al. 2021 (Soil Tillage Res. 212:105071)               - Pingdingshan (Henan, China): CTFR / CTOM -> CT, RTFR / RTOM (rice tilled, wheat
                                                                                        not tilled) -> pZT; rows a (chemical fertiliser) / b (organic manure); RED (after rice)
  178                Mittal R. et al. 2020 (Plant Archives 20(1):2629-2635)           - Taraori, Karnal farmer's field: T1 CT, T2 DSR + ZTW + R -> CA (rule 23, flag),
                                                                                        T3 TPR + ZTW -> pZT, T4 TPR + ZTW + R -> pCA
  59 (companion 3)   Singh G. et al. 2022 (Soil Tillage Res. 217:105272)              - IARI CA trial of old-master 59: TPR-CTW CT, TPR-ZTW pZT, DSR-ZTW (+BM / +MBR) ZT,
                                                                                        + rice residue CA, rows a/b/c (coding of the confirmed 59 companions - ask)
  48 (companion)     Mondal S. et al. 2021 (Eur. J. Soil Sci. 72:1742-1761)          - ICAR-RCER Patna CSISA trial of old-master 48: TA CT, fCA CA; pCA1 left out (residue
                                                                                        contradiction - ask); pCA2 no wheat (excluded); soil RED (sampled after rice)

Obs on every row = Y + T + D (rule 101). Every row records the paper's method in 'Method used (from paper)'.
Usage: python batches/batch_14.py <in.xlsx> <out.xlsx>
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
dj = lambda f: json.load(open(os.path.join(DIG, f)))


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
# 177  ZHAO et al. 2021 Soil Tillage Res. 212:105071
# =====================================================================================
Z_TRT = ("TREATMENTS IN PAPER (demonstration field since Oct 2010, Pingdingshan, Henan; 5 blocks of 300 m2, three 10 x 10 m subplots each; rice Jun-Oct, wheat Oct-May): "
         "CT = conventional tillage (20 cm, every crop), NO fertiliser; CTFR = CT + chemical fertiliser (225 kg N + 90 P2O5 + 90 K2O /ha); RTFR = reduced tillage (20 cm tillage in the "
         "rice season, NO tillage in the wheat season) + chemical fertiliser; CTOM = CT + organic manure (swine compost replacing the fertiliser N; P and K topped up to FR); "
         "RTOM = RT + organic manure. Residue management not described.")
Z_MAP = ("row a (chemical fertiliser): CT = CTFR, pZT = RTFR ; row b (organic manure): CT = CTOM, pZT = RTOM (RT = tilled rice + untilled wheat = partial ZT, rule 103; "
         "no residue described). Unfertilised CT excluded (rule 78).")
Z = {"No.": 177, "SERIAL NO": 177, "Authors": "Zhao Z., Gao S., Lu C., Li X., Li F. & Wang T.", "Year": 2021, "Journal": "Soil & Tillage Research", "Country": "China",
     "Site/Location": "Demonstration experimental field, Pingdingshan, Henan", "latitude": 33.70, "longitude": 113.17, "CLIMATE": "TEMP", "SOIL": "LOAMY", "Rep": 3,
     "RAIN FALL": 1000, "LATT": 33.70, "AVG T": 15, "ph (initial)": 6.8, "soc (initial)": 9.28, "Bdi": 1.33, "sand": 43.4, "silt": 29.5, "CLAY": 27.1,
     "year of data collection/experiment": 2019, "DURATION": "4-10 Y", "YEAR OF DATA (duration)": 9, "Treatment mapping (paper's name -> code)": Z_MAP,
     "DEPTH": "0-15 CM", "DEPTH (as reported in paper)": "0-20 cm",
     "Crop/season of sampling": "RICE SEASON - after rice harvest, 30 Oct 2019 (9th year)",
     "Treatment details (from paper)": Z_TRT}
Z_NOTE = ("RICE-SEASON FALLBACK (rule 79): the only soil sampling (30 Oct 2019) followed the rice harvest - whole row red. Rows a / b = fertiliser level (rule 33; OM = swine compost "
          "replacing fertiliser N - organic-manure tier as rule 89, flag). RT tilled the rice season and left the wheat season untilled -> pZT (rule 103). Unfertilised CT (excluded, "
          "rule 78) values are in the Notes. Mean +/- SD printed (SDs in Notes; SD formula kept). Duplicate upload 126_real_f2f.pdf = 126_2.pdf (entered once). Supplementary: "
          + SUPP + ". Source file 126_2.pdf.")
ZR = [("a", "CTFR", "RTFR", "chemical fertiliser 225-90-90"), ("b", "CTOM", "RTOM", "organic manure (swine compost) + P/K top-up")]
T1Z = {"SOC": {"CT": (6.78, .38), "CTFR": (9.52, .36), "RTFR": (10.02, .28), "CTOM": (13.05, .48), "RTOM": (15.08, .33)},
       "AOC": {"CT": 2.46, "CTFR": 5.61, "RTFR": 6.74, "CTOM": 8.41, "RTOM": 10.24},
       "LOC": {"CT": (4.31, .09), "CTFR": (3.90, .04), "RTFR": (3.28, .07), "CTOM": (4.64, .06), "RTOM": (4.83, .14)},
       "PAOC": {"CT": 36.6, "CTFR": 58.95, "RTFR": 67.3, "CTOM": 64.43, "RTOM": 67.93},
       "DOC": {"CT": (90.46, .19), "CTFR": (106.6, 1.91), "RTFR": (125.13, .43), "CTOM": (134.29, 1.49), "RTOM": (150.6, 4.98)},
       "MBC": {"CT": (101.21, 3.85), "CTFR": (181.42, 5.95), "RTFR": (200.6, 3.97), "CTOM": (316.12, 8.46), "RTOM": (337.95, 9.51)}}
# Table 2 aggregate-associated amounts (g C / kg soil): silt+clay, micro, small macro, large macro
T2Z = {"SOC": {"CT": (2.28, 1.12, 2.65, 1.26), "CTFR": (1.86, 1.41, 3.23, 1.75), "RTFR": (1.72, 1.47, 3.46, 2.26), "CTOM": (1.84, 1.04, 4.48, 3.83), "RTOM": (1.78, .82, 5.48, 5.42)},
       "AOC": {"CT": (1.39, .71, 1.84, .91), "CTFR": (.79, .79, 2.00, 1.19), "RTFR": (.77, .79, 1.97, 1.47), "CTOM": (.62, .51, 2.52, 2.48), "RTOM": (.56, .37, 3.30, 3.74)},
       "LOC": {"CT": (.89, .41, .82, .35), "CTFR": (1.07, .62, 1.23, .56), "RTFR": (.95, .68, 1.49, .80), "CTOM": (1.21, .53, 1.96, 1.35), "RTOM": (1.22, .45, 2.18, 1.69)},
       "DOC": {"CT": (30.04, 16.25, 40.87, 17.6), "CTFR": (28.95, 20.32, 56.71, 26.76), "RTFR": (23.13, 21.68, 75.06, 36.47), "CTOM": (39.6, 23.05, 107.07, 68.21),
               "RTOM": (36.77, 17.68, 122.95, 84.76)},
       "PAOC": {"CT": (60.72, 63.62, 69.17, 72.11), "CTFR": (42.66, 56.23, 61.81, 68.11), "RTFR": (45.18, 53.85, 56.8, 64.84), "CTOM": (34.01, 48.96, 56.15, 64.56),
                "RTOM": (30.97, 45.85, 60.18, 68.82)}}
f1 = dj("zhao2021_fig1.json")   # g/kg soil per class
ZM_SOC = ("Wet redox titration: 250 mg soil (<0.15 mm) digested with 5 ml 0.8 M K2Cr2O7 + 5 ml H2SO4, 5 min at 185 C (graphite digester), back-titrated with 0.2 M FeSO4 "
          "(o-phenanthroline) (Carter & Gregorich 2007); 3 intact cores (0-20 cm, 12-cm shovel) per subplot composited")
ZM_AGG = ("Wet sieving (Elliott 1986): 100 g air-dried <10-mm soil slaked on a 2000-um sieve 5 min, sieve moved up and down 60 times (3 cm) in 2 min; <2000-um soil passed "
          "through 250- and 53-um sieves; <53 um settled / centrifuged; fractions dried at 40 C")
zcls = lambda t: f"{t}: >2000 {f1[t]['large macro']}, 250-2000 {f1[t]['small macro']}, 53-250 {f1[t]['micro']}, <53 {f1[t]['silt+clay']} g/kg"
Z_UNF = "Unfertilised CT (excluded): SOC 6.78, LOC 4.31 g/kg, DOC 90.46, MBC 101.21 mg/kg; aggregates " + zcls("CT") + ". "
for row, ct, pz, lab in ZR:
    lb = f"ROW {row} ({lab}; CT = {ct}, pZT = {pz}). "
    sd = lambda k: f"Paper SD: {ct} {T1Z[k][ct][1]}, {pz} {T1Z[k][pz][1]}. "
    put("SOC(active C pool)", Z, {"CT": T1Z["SOC"][ct][0], "pZT": T1Z["SOC"][pz][0]}, "SOC_", lb + "Table 1. " + sd("SOC") +
        f"Slow + passive C (AOC = SOC - LOC) {T1Z['AOC'][ct]} / {T1Z['AOC'][pz]} g/kg; PAOC {T1Z['PAOC'][ct]} / {T1Z['PAOC'][pz]} % (no sheets). " + Z_UNF + Z_NOTE, red=True,
        UNIT="g/kg (K2Cr2O7 wet oxidation)", **{"Data source": "Table 1", "Method used (from paper)": ZM_SOC})
    put("POXC(KMnO4-C)", Z, {"CT": f"=ROUND({T1Z['LOC'][ct][0]}*1000,0)", "pZT": f"=ROUND({T1Z['LOC'][pz][0]}*1000,0)"}, "POXC_",
        lb + "Table 1 LOC (labile organic C) printed in g/kg x 1000. " + sd("LOC") + Z_UNF + Z_NOTE, red=True, UNIT="mg/kg (333 mM KMnO4-oxidisable C; printed g/kg x 1000)",
        **{"Data source": "Table 1 - converted", "Method used (from paper)": "2.5 g soil + 25 ml 333 mM KMnO4 shaken 30 min (180 rpm), centrifuged 10 min (2500 rpm), A565 (Loginow et al. 1987)"})
    put("DOC", Z, {"CT": T1Z["DOC"][ct][0], "pZT": T1Z["DOC"][pz][0]}, "DOC_", lb + "Table 1. " + sd("DOC") + Z_UNF + Z_NOTE, red=True,
        UNIT="mg/kg soil (water-extractable, 2:1 water:soil)", **{"Data source": "Table 1",
        "Method used (from paper)": "Fresh soil shaken 30 min with double-distilled water (2:1 v/w), centrifuged 10 min at 4000 rpm, 0.45-um filtered, Vario Max elemental analyser (Hao et al. 2013)"})
    put("MBC", Z, {"CT": T1Z["MBC"][ct][0], "pZT": T1Z["MBC"][pz][0]}, "MBC_", lb + "Table 1. " + sd("MBC") + "Aggregate-associated MBC (Fig. 2) has no sheet - not entered. "
        + Z_UNF + Z_NOTE, red=True, UNIT="mg/kg (ug C/g soil)", **{"Data source": "Table 1",
        "Method used (from paper)": "Chloroform fumigation-extraction (Vance et al. 1987): 20 g moist soil, 24 h CHCl3 at 25 C, 0.5 M K2SO4 (1:4), TOC analyser, kEC 0.45"})
    mrow = put("MACRO", Z, {c: f"=ROUND(({f1[t]['large macro']}+{f1[t]['small macro']})/10,2)" for c, t in (("CT", ct), ("pZT", pz))}, "MACRO_",
               lb + "Fig. 1 DIGITISED exactly from the vector bars (the four classes sum to 1000 +/- 2 g/kg in every treatment). MACRO = >2000 + 250-2000 um, g/kg / 10. "
               + zcls(ct) + "; " + zcls(pz) + ". " + Z_UNF + Z_NOTE, red=True, UNIT="% (water-stable aggregates >0.25 mm; printed g/kg / 10)",
               **{"Data source": "Fig. 1 (digitised, vector)", "Method used (from paper)": ZM_AGG})
    irow = put("MICRO", Z, {c: f"=ROUND({f1[t]['micro']}/10,2)" for c, t in (("CT", ct), ("pZT", pz))}, "MICRO_",
               lb + "Fig. 1 53-250 um class (digitised exactly, vector), g/kg / 10. " + Z_NOTE, red=True, UNIT="% (water-stable micro-aggregates 0.053-0.25 mm)",
               **{"Data source": "Fig. 1 (digitised, vector)", "Method used (from paper)": ZM_AGG})
    put("WSA", Z, {c: f"=ROUND(({B.ref('MACRO', 'MACRO_' + c, mrow)}+{B.ref('MICRO', 'MICRO_' + c, irow)})/100,4)" for c in ("CT", "pZT")}, "WSA_",
        lb + "DERIVED (rule 102): WSA = MACRO + MICRO (all fractions >0.053 mm), live links, % / 100. " + Z_NOTE, red=True,
        UNIT="g/g soil (MACRO >0.25 mm + MICRO 0.053-0.25 mm, % / 100)", **{"Data source": "DERIVED (Fig. 1)", "Method used (from paper)": ZM_AGG + "; WSA = macro + micro"})
    for sh, pre, key, unit, conv in (("macro c", "MACRO c_", "SOC", "g/kg aggregate (DERIVED: printed C amount g/kg soil / class mass fraction)", 1),
                                     ("macro c", "MACRO c_", "LOC", "g/kg aggregate (KMnO4-oxidisable labile C in macroaggregates; DERIVED from amount / mass fraction)", 1)):
        put(sh, Z, {c: f"=ROUND(({T2Z[key][t][2]}+{T2Z[key][t][3]})/(({f1[t]['small macro']}+{f1[t]['large macro']})/1000),2)" for c, t in (("CT", ct), ("pZT", pz))}, pre,
            lb + f"DERIVED (rule 110 default): Table 2 prints aggregate-associated {key} as AMOUNTS (g C / kg bulk soil = concentration x mass fraction); concentration in "
            f">0.25 mm aggregates = (small + large macro amount) / (small + large mass fraction, Fig. 1). Amounts {ct}: {T2Z[key][ct]}, {pz}: {T2Z[key][pz]} "
            "(silt+clay, micro, small macro, large macro). " + Z_NOTE, red=True, UNIT=unit, **{"Data source": "DERIVED (Table 2 + Fig. 1)",
            "Method used (from paper)": ZM_AGG + ("; SOC by K2Cr2O7 wet oxidation" if key == "SOC" else "; LOC by 333 mM KMnO4") + "; C amount = C concentration x mass fraction"})
    for key, unit in (("SOC", "g/kg aggregate (DERIVED: printed C amount g/kg soil / class mass fraction)"),
                      ("LOC", "g/kg aggregate (KMnO4-oxidisable labile C in microaggregates; DERIVED from amount / mass fraction)")):
        put("micro c", Z, {c: f"=ROUND({T2Z[key][t][1]}/({f1[t]['micro']}/1000),2)" for c, t in (("CT", ct), ("pZT", pz))}, "MICRO c_",
            lb + f"DERIVED: 53-250 um {key} amount / 53-250 um mass fraction (Fig. 1); silt+clay (<53 um) left out. DOC and PAOC per class (Table 2) have no sheet: DOC {ct} "
            f"{T2Z['DOC'][ct]}, {pz} {T2Z['DOC'][pz]} mg/kg; PAOC {ct} {T2Z['PAOC'][ct]}, {pz} {T2Z['PAOC'][pz]} %. " + Z_NOTE, red=True, UNIT=unit,
            **{"Data source": "DERIVED (Table 2 + Fig. 1)", "Method used (from paper)": ZM_AGG + "; C amount = C concentration x mass fraction"})

# =====================================================================================
# 178  MITTAL et al. 2020 Plant Archives 20(1):2629-2635
# =====================================================================================
M_TRT = ("TREATMENTS IN PAPER (farmer's field, Taraori, Karnal, Haryana; rice-wheat >10 yr; RBD, 5 reps, 7.5 x 6 m; 2015-16 and 2016-17): T1 transplanted rice + conventionally "
         "tilled wheat; T2 direct-seeded rice + zero-tilled wheat with residue retention (DSR tillage not described); T3 transplanted rice + ZT wheat; T4 transplanted rice + ZT wheat "
         "with residue retention (rice residue retained / incorporated in the wheat field). 120-60-60 kg N-P2O5-K2O to both crops; Pusa 1121 rice, HD 2967 wheat.")
M_MAP = ("T1 -> CT ; T2 DSR + ZTW + R -> CA (DSR tillage not stated: rule 23, classified on the ZT wheat phase; flag) ; T3 TPR + ZTW -> pZT ; T4 TPR + ZTW + R -> pCA")
M = {"No.": 178, "SERIAL NO": 178, "Authors": "Mittal R., Chakrabarti B., Rawat M., Jatav R.S. & Dhupper R.", "Year": 2020, "Journal": "Plant Archives", "Country": "India (Haryana)",
     "Site/Location": "Farmer's field, Taraori village, Karnal", "latitude": 29.7, "longitude": 76.9, "CLIMATE": "ST", "SOIL": "LOAMY", "Rep": 5, "RAIN FALL": 700,
     "LATT": 29.7, "MIN TEMP": 18, "MAX TEMP": 35, "ph (initial)": 8.1, "soc (initial)": 4.6, "DURATION": "0-3 Y", "Treatment mapping (paper's name -> code)": M_MAP,
     "Fertilizer dose & other management": ("120-60-60 kg N-P2O5-K2O/ha to both crops (N in 3 splits); TPR flooded 6 cm (alternate-day irrigation), DSR at field capacity (4-5 d), "
                                            "wheat 5 irrigations; herbicides as needed. Sandy clay loam, pH 8.1, SOC 0.46 %."),
     "Treatment details (from paper)": M_TRT}
M_NOTE = ("T2 coded CA under rule 23 (direct-seeded rice, tillage not described; ZT wheat + residue) - flag (if the DSR was dry-tilled it would be pCA under rule 103). "
          "Rice-season values of the same parameters are kept in the Notes (rule 35). Supplementary: " + SUPP + ". Source file 126_real.pdf.")
MG = {"2015-16": {"R": (4.01, 3.51, 4.09, 4.16), "W": (4.39, 4.42, 4.40, 4.89)}, "2016-17": {"R": (4.10, 3.73, 4.20, 4.36), "W": (4.98, 5.03, 5.08, 5.27)}}
MS = {"2015-16": {"R": (6.26, 6.34, 6.11, 6.38), "W": (6.23, 6.51, 6.23, 6.63)}, "2016-17": {"R": (6.87, 6.36, 6.53, 6.81), "W": (6.74, 6.81, 6.74, 7.21)}}
MN = {"2015-16": {"R": (378.0, 397.5, 400.6, 485.9), "W": (409.4, 462.7, 420.5, 531.9)}, "2016-17": {"R": (354.8, 374.6, 448.7, 491.5), "W": (390.0, 480.7, 457.1, 525.5)}}
MC = ("CT", "CA", "pZT", "pCA")   # T1, T2, T3, T4
mb = dj("mittal2020_bars.json")
for yi, yr in enumerate(("2015-16", "2016-17")):
    base = {**M, "year of data collection/experiment": yr, "YEAR OF DATA (duration)": yi + 1}
    yrow = put("YIELD", {**base, "Crop/season of sampling": f"Rice {yr[:4]} and wheat {yr} - harvest"}, dict(zip(MC, MG[yr]["W"])), "WYIELD_",
               f"Tables 1-2 (LSD grain rice / wheat {('0.25 / 0.20' if yi == 0 else '0.20 / 0.29')}). " + M_NOTE, Y=2, UNIT="Mg/ha = t/ha (grain and straw, dry weight; 1 m2 harvest)",
               **{**{"RICE YIELD_" + c: v for c, v in zip(MC, MG[yr]["R"])}, **{"W STRAW_" + c: v for c, v in zip(MC, MS[yr]["W"])},
                  **{"RSTRAW_" + c: v for c, v in zip(MC, MS[yr]["R"])}, "Data source": "Tables 1-2",
                  "Method used (from paper)": "Rice and wheat harvested and threshed manually from 1 m2 per plot; dried straw and grain weighed"})
    put("HARVEST INDEX", {**base, "Crop/season of sampling": f"Rice {yr[:4]} and wheat {yr} - harvest"},
        {c: f"=ROUND({B.ref('YIELD', 'WYIELD_' + c, yrow)}/({B.ref('YIELD', 'WYIELD_' + c, yrow)}+{B.ref('YIELD', 'W STRAW_' + c, yrow)}),3)" for c in MC}, "HI_W",
        "DERIVED (rule 52): HI = grain / (grain + straw), live links to the YIELD row. " + M_NOTE, Y=2, UNIT="ratio (DERIVED grain / (grain + straw))",
        **{**{"HI_R" + c: f"=ROUND({B.ref('YIELD', 'RICE YIELD_' + c, yrow)}/({B.ref('YIELD', 'RICE YIELD_' + c, yrow)}+{B.ref('YIELD', 'RSTRAW_' + c, yrow)}),3)" for c in MC},
           "Data source": "DERIVED from Tables 1-2", "Method used (from paper)": "HI = grain / (grain + straw); 1-m2 harvest"})
    sb = {**base, "DEPTH": "0-15 CM", "DEPTH (as reported in paper)": "0-15 cm", "Crop/season of sampling": f"Wheat {yr} - flowering stage"}
    rk, wk = f"Rice {yr[:4]}", f"Wheat {yr}"
    put("N", sb, dict(zip(MC, MN[yr]["W"])), "N_", f"Table 3 (LSD {('19.6' if yi == 0 else '26.6')}). Rice-season (flowering) values T1-T4: {MN[yr]['R']} kg/ha (rule 35, not entered). "
        + M_NOTE, Y=2, UNIT="kg/ha (available N, alkaline KMnO4)", **{"Data source": "Table 3",
        "Method used (from paper)": "Alkaline KMnO4 (Subbiah & Asija 1956) on fresh 0-15 cm soil at crop flowering"})
    for sh, pre, key, unit, meth in (("MBC", "MBC_", "MBC", "mg/kg (ug C/g soil)", "Chloroform fumigation-extraction (Jenkinson & Powlson 1976), fresh 0-15 cm soil at flowering"),
                                     ("MBN", "MBN_", "MBN", "mg/kg (ug N/g soil)", "Chloroform fumigation-extraction (Jenkinson & Powlson 1976), fresh 0-15 cm soil at flowering"),
                                     ("DHA", "DHA_", "DHA", "ug TPF/g soil/h (axis label; text says 'mg TPF' - flag)", "Klein et al. (1971), TTC reduction, fresh soil at flowering")):
        put(sh, sb, dict(zip(MC, mb[key][wk])), pre, f"Fig. {({'MBC': 1, 'MBN': 2, 'DHA': 3}[key])} DIGITISED (raster bars, pixel scan calibrated on the axis ticks; text values reproduced "
            "within ~3: MBC wheat T4 538 / T2 507.9 (yr 1), T2 555.6 / T4 548.2 (yr 2); MBN 41.9-56.9 rice, 53.4-73.5 wheat; DHA T4 1.57). "
            f"Rice-season values T1-T4: {mb[key][rk]} (rule 35, not entered). " + M_NOTE, Y=2, UNIT=unit,
            **{"Data source": f"Fig. {({'MBC': 1, 'MBN': 2, 'DHA': 3}[key])} (digitised)", "Method used (from paper)": meth})
fb = {**M, "year of data collection/experiment": "2016-17 (after 2 cycles)", "YEAR OF DATA (duration)": 2, "DEPTH": "0-15 CM", "DEPTH (as reported in paper)": "0-15 cm",
      "Crop/season of sampling": "Wheat season - end of the 2-year experiment ('final', 2017)"}
put("TOC", fb, {c: f"=ROUND({v[1]}*10,2)" for c, v in zip(MC, (mb["TOC"][t] for t in ("T1", "T2", "T3", "T4")))}, "TOC_",
    "Fig. 5 'Final' bars DIGITISED (raster; text: T4 1.36 %, T3 0.97 %, T1 0.91 % reproduced), % x 10. Initial (2015) T1-T4: "
    + " / ".join(str(mb["TOC"][t][0]) for t in ("T1", "T2", "T3", "T4")) + " %. " + M_NOTE, UNIT="g/kg (dry combustion total C, printed % x 10)",
    **{"Data source": "Fig. 5 (digitised) - converted", "Method used (from paper)": "Dry combustion at 950 C, Vario TOC select (Elementar), NDIR detection (Nelson & Sommers 1982)"})
put("total N", fb, {c: f"=ROUND({v[1]}*10000,0)" for c, v in zip(MC, (mb["TN"][t] for t in ("T1", "T2", "T3", "T4")))}, "TN_",
    "Fig. 4 'Final' bars DIGITISED (raster; text range 0.11-0.16 %), % x 10000. Initial (2015) T1-T4: " + " / ".join(str(mb["TN"][t][0]) for t in ("T1", "T2", "T3", "T4"))
    + " %. " + M_NOTE, UNIT="mg/kg (printed % x 10000)", **{"Data source": "Fig. 4 (digitised) - converted", "Method used (from paper)": "Total N (method not stated)"})

# =====================================================================================
# 59 (companion 3)  SINGH G. et al. 2022 Soil Tillage Res. 217:105272
# =====================================================================================
S_TRT = ("TREATMENTS IN PAPER (ICAR-IARI CA trial est. June 2010, New Delhi; RCBD 3 reps, ~14 x 9 m; tilled DSR in years 1-3, zero-till DSR from year 4; details in Table S1 and "
         "Bhattacharyya et al. 2015): TPR-CTW (puddled TPR + conventional-till wheat); TPR-ZTW; DSR-ZTW; DSR-ZTW + RR (rice residue); DSR + BM-ZTW (Sesbania brown manure); "
         "DSR + BM-ZTW + RR (CA module 1); DSR + MBR-ZTW-ZTMB (mungbean residue + ZT summer mungbean); DSR + MBR-ZTW + RR-ZTMB + WR (CA module 2; rice + wheat residue).")
S_MAP = ("CT = TPR-CTW and pZT = TPR-ZTW in every row ; row a: ZT = DSR-ZTW, CA = DSR-ZTW + RR ; row b: ZT = DSR + BM-ZTW, CA = DSR + BM-ZTW + RR (CA module 1) ; "
         "row c: ZT = DSR + MBR-ZTW-ZTMB, CA = DSR + MBR-ZTW + RR-ZTMB + WR (CA module 2) - coding of the author-confirmed 59 companions")
S = {"No.": "59 (companion 3)", "SERIAL NO": "59 (companion 3)", "Authors": "Singh G., Bhattacharyya R., Dhaked B.S. & Das T.K.", "Year": 2022, "Journal": "Soil & Tillage Research",
     "Country": "India (Delhi)", "Site/Location": "ICAR-IARI research farm, New Delhi (CA trial of study 59)", "latitude": 28.583, "longitude": 77.2, "CLIMATE": "ST",
     "SOIL": "LOAMY", "Rep": 3, "LATT": 28.583, "ph (initial)": 8.3, "soc (initial)": 6.0, "year of data collection/experiment": "June 2014", "DURATION": "4-10 Y",
     "YEAR OF DATA (duration)": 4, "Treatment mapping (paper's name -> code)": S_MAP,
     "Fertilizer dose & other management": ("Rice hybrid PRH 10, wheat HD 2895; ~15 irrigations DSR vs 17 TPR (5 cm each). BROWN MANURE (Sesbania) in row b, MUNGBEAN residue + ZT summer "
                                            "mungbean in row c (rule 71 / 59-family flag). Sandy clay loam, pH 8.3, OC 6.0 g/kg, EC 0.69 dS/m."),
     "Crop/season of sampling": "After the 4th wheat + summer mungbean (harvest of mungbean, June 2014)", "Treatment details (from paper)": S_TRT}
S_NOTE = ("COMPANION of old-master 59 (IARI CA trial est. 2010; same 8 treatments; rule 5). Coded as the author-confirmed 59 companions (DSR-ZTW -> ZT, + rice residue -> CA; "
          "BM row b and mungbean row c flagged); TPR-ZTW -> pZT now (excluded in 59, rules 85 / 68). FLAG (question to author): DSR was dry-tilled in years 1-3 and zero-tilled in "
          "year 4 - under rule 103 the tilled-DSR years would make it pZT / pCA. Sampled after the summer mungbean harvest (post-wheat; not rice season). "
          "Treatment numbers T1-T8 of Fig. 3 decoded through the glomalin values of Table 1 (Table S1 not reachable). Supplementary: Tables S1-S6 - " + SUPP + ". Source file 125_real.pdf.")
SR = [("a", "DSR-ZTW", "DSR-ZTW + RR"), ("b", "DSR + BM-ZTW", "DSR + BM-ZTW + RR (CA module 1)"), ("c", "DSR + MBR-ZTW-ZTMB", "DSR + MBR-ZTW + RR-ZTMB + WR (CA module 2)")]
ST = ["DSR-ZTW", "DSR-ZTW + RR", "DSR + BM-ZTW", "DSR + BM-ZTW + RR (CA module 1)", "DSR + MBR-ZTW-ZTMB", "DSR + MBR-ZTW + RR-ZTMB + WR (CA module 2)", "TPR-ZTW", "TPR-CTW"]
# Table 1 (0-5, 5-15 cm) in the order of ST
T1S = {"ERG": ((4.27, 3.91), (3.00, 3.75), (5.41, 3.30), (2.53, 2.98), (5.08, 6.09), (3.91, 3.65), (5.34, 5.52), (5.95, 4.62)),
       "BGL": ((56.5, 70.7), (46.2, 67.9), (57.7, 71.4), (56.5, 65.1), (69.9, 57.3), (50.4, 39.5), (38.8, 48.3), (53.3, 48.9)),
       "GLO": ((18.0, 27.0), (13.4, 13.6), (24.1, 30.7), (17.2, 19.9), (30.3, 20.6), (35.6, 31.5), (14.1, 29.3), (5.80, 35.2)),
       "CMC": ((192.9, 200.5), (291.5, 271.1), (205.4, 257.8), (315.1, 306.8), (168.7, 198.3), (251.7, 355.1), (189.6, 286.5), (159.3, 272.5)),
       "ALP": ((81.8, 57.8), (85.6, 65.7), (86.3, 63.9), (56.0, 59.3), (101.0, 70.3), (98.1, 85.5), (82.0, 107.7), (66.7, 94.0)),
       "MBC": ((56.3, 68.9), (61.9, 71.8), (78.8, 72.5), (53.3, 79.8), (75.0, 77.1), (69.8, 69.2), (49.6, 63.2), (49.3, 68.3))}
# Fig. 3A spore counts per g soil (filled circles 0-5 cm, open 5-15 cm); T1-T8 = TPR-CTW, TPR-ZTW, CA2, MBR-ZTMB, BM-ZTW, DSR-ZTW+RR, CA1, DSR-ZTW
SPO = {"TPR-CTW": (10.15, 37.67), "TPR-ZTW": (15.44, 24.3), "DSR + MBR-ZTW + RR-ZTMB + WR (CA module 2)": (38.48, 25.09), "DSR + MBR-ZTW-ZTMB": (27.82, 18.28),
       "DSR + BM-ZTW": (25.3, 27.0), "DSR-ZTW + RR": (14.6, 11.6), "DSR + BM-ZTW + RR (CA module 1)": (20.13, 15.72), "DSR-ZTW": (20.64, 20.3)}
SPO_VIS = {("TPR-ZTW", 1), ("DSR + BM-ZTW", 0), ("DSR-ZTW", 1)}
sag = dj("singh2022_aggr.json")
SKEY = {"DSR-ZTW": "DSR-ZTW", "DSR-ZTW + RR": "DSR-ZTW+RR", "DSR + BM-ZTW": "DSR+BM-ZTW", "DSR + BM-ZTW + RR (CA module 1)": "DSR+BM-ZTW+RR",
        "DSR + MBR-ZTW-ZTMB": "DSR+MBR-ZTW-ZTMB", "DSR + MBR-ZTW + RR-ZTMB + WR (CA module 2)": "DSR+MBR-ZTW+RR-ZTMB+WR", "TPR-ZTW": "TPR-ZTW", "TPR-CTW": "TPR-CTW"}
SMETH = {"BGL": "beta-glucosidase (Eivazi & Tabatabai 1988), p-nitrophenol release", "GLO": "Glomalin (Wright & Upadhyaya 1996), ug/g dry soil",
         "CMC": "Carboxymethyl cellulase: glucose released (Miller 1959 DNS), glucose standard", "ALP": "Alkaline phosphatase (Tabatabai 1994), p-nitrophenol release",
         "MBC": "Chloroform fumigation-extraction (Vance et al. 1987)", "SPO": "Wet sieving and decanting (Gerdemann & Nicolson 1963)",
         "AGG": "Wet sieving adapted from Elliott (1986) (procedure in Singh et al. 2018) of <8-mm field-moist samples: >2000, 250-2000, 53-250, <53 um"}
SDEP = [(0, "0-5 cm"), (1, "5-15 cm")]
for di, rep in SDEP:
    sb = {**S, "DEPTH": "0-15 CM", "DEPTH (as reported in paper)": rep}
    for row, zt, ca in SR:
        lb = f"ROW {row} (ZT = {zt}; CA = {ca}). "
        ix = lambda t: ST.index(t)
        cod = {"CT": "TPR-CTW", "pZT": "TPR-ZTW", "ZT": zt, "CA": ca}
        ergs = "Ergosterol (ug/g, no sheet): " + ", ".join(f"{t} {T1S['ERG'][ix(t)][di]}" for t in cod.values()) + ". "
        for sh, pre, key, unit, conv in (("B-GLU", "BGL_", "BGL", "ug PNP/g soil/h", None), ("GLOMALIN", "GLO_", "GLO", "mg/g soil (printed ug/g / 1000; total glomalin)", 1000),
                                         ("CELL", "CELL_", "CMC", "IU/g soil AS PRINTED (Cmcase; not convertible to ug glucose/g/h without the assay time - flag)", None),
                                         ("ALKP", "ALP_", "ALP", "ug PNP/g soil/h (table unit; text says umol - flag)", None), ("MBC", "MBC_", "MBC", "mg/kg (ug C/g soil)", None)):
            vals = {c: (f"=ROUND({T1S[key][ix(t)][di]}/{conv},4)" if conv else T1S[key][ix(t)][di]) for c, t in cod.items()}
            put(sh, sb, vals, pre, lb + f"Table 1, {rep}. " + (ergs if key == "MBC" else "") + S_NOTE, T=3, D=2, UNIT=unit,
                **{"Data source": "Table 1" + (" - converted" if conv else ""), "Method used (from paper)": SMETH[key]})
        put("MYCORRHIZAL SPORES", sb, {c: f"=ROUND({SPO[t][di]}*100,0)" for c, t in cod.items()}, "SPORE_",
            lb + f"Fig. 3A ({rep}: {'filled' if di == 0 else 'open'} circles) DIGITISED from the raster (marker blobs, axis-tick calibration; "
            + ("values marked * read visually where the marker merged with a line: " + ", ".join(f"{t}*" for t in cod.values() if (t, di) in SPO_VIS) + "; " if any((t, di) in SPO_VIS for t in cod.values()) else "")
            + "text: CA module 2 37 spores/g). Spores per g x 100. " + S_NOTE, T=3, D=2, UNIT="spores per 100 g soil (printed per g x 100)",
            **{"Data source": "Fig. 3A (digitised) - converted", "Method used (from paper)": SMETH["SPO"]})
        ag = {c: sag[rep][SKEY[t]] for c, t in cod.items()}
        mrow = put("MACRO", sb, {c: round(v["0.25-2"] + v[">2"], 1) for c, v in ag.items()}, "MACRO_",
                   lb + f"Fig. {1 if di == 0 else 2} stacked bars DIGITISED (hatch layer is raster, the >2 mm segment vector: >2 mm = bar top minus the patterned segments; "
                   "10 % gridlines calibration). Classes: " + "; ".join(f"{t}: >2 {sag[rep][SKEY[t]]['>2']}, 0.25-2 {sag[rep][SKEY[t]]['0.25-2']}, 0.053-0.25 "
                   f"{sag[rep][SKEY[t]]['0.053-0.25']}, <0.053 {sag[rep][SKEY[t]]['<0.053']} %" for t in cod.values()) + ". " + S_NOTE, T=3, D=2,
                   UNIT="% (water-stable aggregates >0.25 mm = >2 + 0.25-2 mm)", **{"Data source": f"Fig. {1 if di == 0 else 2} (digitised)", "Method used (from paper)": SMETH["AGG"]})
        irow = put("MICRO", sb, {c: v["0.053-0.25"] for c, v in ag.items()}, "MICRO_", lb + f"Fig. {1 if di == 0 else 2} 0.053-0.25 mm class (digitised). " + S_NOTE,
                   T=3, D=2, UNIT="% (water-stable micro-aggregates 0.053-0.25 mm)", **{"Data source": f"Fig. {1 if di == 0 else 2} (digitised)", "Method used (from paper)": SMETH["AGG"]})
        put("WSA", sb, {c: f"=ROUND(({B.ref('MACRO', 'MACRO_' + c, mrow)}+{B.ref('MICRO', 'MICRO_' + c, irow)})/100,4)" for c in cod}, "WSA_",
            lb + "DERIVED (rule 102): MACRO + MICRO, % / 100. " + S_NOTE, T=3, D=2, UNIT="g/g soil (MACRO + MICRO >0.053 mm, % / 100)",
            **{"Data source": f"DERIVED (Fig. {1 if di == 0 else 2})", "Method used (from paper)": SMETH["AGG"] + "; WSA = macro + micro"})

# =====================================================================================
# 48 (companion)  MONDAL et al. 2021 Eur. J. Soil Sci. 72:1742-1761
# =====================================================================================
N_TRT = ("TREATMENTS IN PAPER (CSISA long-term trial, ICAR-RCER Patna, est. Nov 2009; 2000 m2 plots, 3 reps; soil sampled 2019 after rice): TA = CT wheat - fallow - puddled TPR, "
         "residues removed; pCA1 = NT wheat - NT greengram - rice CT (puddled 2009-14; CT + unpuddled machine transplanting 2014-19), wheat and rice residue REMOVED and greengram "
         "residue incorporated (Table 1) BUT Table 5 lists 2.1 / 2.0 Mg/ha rice and 2.1 / 2.4 Mg/ha wheat residue retained in pCA1; fCA = NT wheat - NT greengram (cowpea "
         "2009-14) - NT DSR, one-third wheat and rice residue retained, legume residue retained; pCA2 = potato+maize / mustard - maize - rice (no wheat).")
N_MAP = "TA -> CT ; fCA -> CA (greengram third crop not in TA - flag, as old-master 48) ; pCA1 NOT ENTERED (residue contradiction, ask the author) ; pCA2 excluded (no wheat)"
N = {"No.": "48 (companion)", "SERIAL NO": "48 (companion)", "Authors": ("Mondal S., Mishra J.S., Poonia S.P., Kumar R., Dubey R., Kumar S., Verma M., Rao K.K., Ahmed A., Dwivedi S., "
                                                                         "Bhatt B.P., Malik R.K., Kumar V. & McDonald A."), "Year": 2021,
     "Journal": "European Journal of Soil Science", "Country": "India (Bihar)", "Site/Location": "ICAR Research Complex for Eastern Region, Patna (CSISA trial of study 48)",
     "latitude": 25.58, "longitude": 85.06, "CLIMATE": "ST", "SOIL": "CLAYEY", "Rep": 3, "RAIN FALL": 1130, "LATT": 25.58, "MIN TEMP": 15.6, "MAX TEMP": 31.2,
     "soc (initial)": 8.0, "DURATION": "4-10 Y", "Treatment mapping (paper's name -> code)": N_MAP,
     "Fertilizer dose & other management": ("Greengram (cowpea 2009-14) third crop in fCA only (TA summer fallow) - flag (rule 30, as old-master 48). fCA one-third rice and wheat "
                                            "residue retained; TA residues removed at ground level. Silty clay, TOC 8 g/kg at start."),
     "Treatment details (from paper)": N_TRT}
N_NOTE = ("COMPANION of old-master 48 (Samal et al. 2017; same CSISA trial est. 2009; rule 5): TA -> CT, fCA -> CA as in 48. pCA1 (NT wheat after CT rice) not entered - Table 1 says "
          "rice / wheat residue removed (-> pZT) but Table 5 lists 2.0-2.4 Mg/ha retained (-> pCA): author decision pending; pCA1 values in the Notes. pCA2 (no wheat) excluded. "
          "Supplementary: Fig. S1 only - " + SUPP + ". Source file 125.pdf.")
N_RED = "RICE-SEASON FALLBACK (rule 79): soil sampled once, in 2019 AFTER THE RICE HARVEST (10th year) - whole row red. "
fig = dj("mondal2021_figs.json")
NLAY = [("0-7.5", "0-15 CM", 2, 7.5), ("7.5-15", "0-15 CM", 2, 7.5), ("15-30", "15-30 CM", 1, 15), ("30-45", "30-45 CM", 1, 15), ("45-60", "45-60 CM", 1, 15)]
T2N = {"TA": (7.12, 5.06, 8.08, 7.86, 8.58, 36.70), "pCA1": (8.93, 5.60, 8.66, 8.97, 7.49, 39.66), "fCA": (9.99, 6.86, 10.32, 7.76, 8.74, 43.67), "pCA2": (9.36, 5.77, 8.78, 8.11, 9.32, 41.34)}
T2M = {"TA": (7.02, 5.14, 7.83, 7.75, 8.50, 36.25), "pCA1": (8.99, 5.72, 8.62, 8.93, 7.53, 39.79), "fCA": (10.22, 6.82, 10.56, 7.82, 8.79, 44.22), "pCA2": (9.19, 5.62, 8.90, 8.17, 9.30, 41.18)}
T3N = {  # MacA, MicA, WSA, AR, MWD, GMD, FD per layer: TA, pCA1, fCA, pCA2
    "0-7.5": ((58.0, 27.3, 85.2, 2.13, .77, .80, 3.20), (67.2, 18.8, 86.0, 3.59, 1.29, .96, 3.18), (73.4, 18.8, 92.2, 3.91, 1.68, 1.05, 3.20), (65.9, 20.2, 86.1, 3.27, 1.45, .99, 3.18)),
    "7.5-15": ((63.5, 25.3, 88.8, 2.53, .73, .76, 3.21), (67.2, 21.0, 88.2, 3.22, 1.11, .91, 3.20), (71.2, 18.3, 89.5, 3.93, 1.25, .94, 3.20), (69.5, 20.3, 89.8, 3.45, .95, .85, 3.19)),
    "15-30": ((62.0, 25.5, 87.4, 2.44, .95, .86, 3.21), (69.5, 24.4, 93.9, 2.86, .93, .83, 3.21), (71.5, 20.1, 91.6, 3.67, .92, .85, 3.20), (62.7, 25.0, 87.7, 2.53, .84, .81, 3.18)),
    "30-45": ((65.2, 20.3, 85.5, 3.26, .79, .83, 3.19), (69.4, 22.3, 91.7, 3.24, .88, .83, 3.20), (65.2, 21.7, 86.9, 3.16, .88, .86, 3.19), (63.5, 20.5, 84.0, 3.13, .82, .84, 3.19)),
    "45-60": ((61.3, 23.2, 84.5, 2.71, .80, .83, 3.19), (62.4, 25.3, 87.7, 2.48, .85, .81, 3.18), (66.5, 21.9, 88.4, 3.08, .89, .84, 3.19), (66.2, 23.6, 89.7, 2.86, .81, .81, 3.20))}
T4N = {  # MacP, MicP, TotP, FC, PWP, AWC (% v/v): TA, pCA1, fCA, pCA2
    "0-7.5": ((8.6, 33.3, 41.9, 44.6, 26.8, 17.8), (9.0, 34.0, 43.0, 38.4, 24.3, 14.1), (10.9, 33.2, 44.1, 41.1, 25.7, 15.4), (8.9, 34.7, 43.6, 42.7, 25.7, 17.0)),
    "7.5-15": ((9.1, 32.9, 42.0, 38.3, 22.9, 15.4), (9.0, 33.1, 42.2, 39.1, 22.6, 16.4), (10.1, 32.3, 42.4, 44.8, 24.9, 19.9), (8.6, 33.5, 43.2, 44.8, 25.7, 19.1)),
    "15-30": ((8.1, 33.6, 41.6, 43.6, 24.5, 19.1), (7.7, 33.5, 41.2, 40.7, 24.3, 16.3), (11.0, 33.2, 44.2, 39.5, 24.2, 15.3), (8.0, 33.4, 41.4, 40.1, 23.5, 16.6)),
    "30-45": ((9.1, 32.3, 41.4, 44.0, 23.6, 20.4), (8.0, 31.4, 39.4, 45.8, 24.5, 21.3), (7.9, 31.6, 39.5, 43.8, 25.7, 18.0), (7.3, 34.7, 42.0, 42.8, 25.4, 17.4)),
    "45-60": ((9.2, 34.1, 43.3, 45.9, 23.7, 22.2), (8.3, 33.6, 41.9, 46.9, 25.0, 21.9), (6.6, 34.1, 40.8, 47.2, 22.9, 24.2), (7.0, 34.1, 41.1, 46.6, 22.8, 23.8))}
TI = {"TA": 0, "pCA1": 1, "fCA": 2, "pCA2": 3}
NC = {"CT": "TA", "CA": "fCA"}
NB = {**N, "year of data collection/experiment": 2019, "YEAR OF DATA (duration)": 10, "Crop/season of sampling": "RICE SEASON - after rice harvest, 2019 (10th year)"}
NM_BD = "Core method: 5.3 cm diam. x 5 cm cores, oven-dried at 100 C; 0-7.5, 7.5-15, 15-30, 30-45, 45-60 cm"
NM_AGG = ("Wet sieving (Yoder 1936): 100 g air-dried 2-4 mm aggregates capillary-wetted 10 min, shaken 5 min at 35 cycles/min on 2, 0.5, 0.25, 0.12, 0.053 mm sieves, sand-corrected; "
          "MWD / GMD by eqs 1-2")
NM_C = "Walkley & Black (1934) dichromate oxidation; composite of 8 auger points per plot and depth"
NM_W = ("Undisturbed cores saturated by capillarity; macropores = water drained at 60-cm hanging water column; micropores = total - macro; FC / PWP at 33 / 1500 kPa on a "
        "pressure plate, gravimetric x BD = volumetric; AWC = FC - PWP")
pc = lambda d: ", ".join(f"{t} {d[t]}" for t in ("pCA1", "pCA2"))
bdrow = {}
for li, (lay, cls, D, th) in enumerate(NLAY):
    nb = {**NB, "DEPTH": cls, "DEPTH (as reported in paper)": f"{lay} cm"}
    bd = fig["BD"][lay]
    bdrow[lay] = put("BD", nb, {c: bd[t] for c, t in NC.items()}, "BD_", N_RED + f"Fig. 1 DIGITISED (raster bars, tick-calibrated; text: 0-7.5 cm highest pCA2 1.55 / lowest fCA 1.49; "
                     "15-30 cm TA 4.7-5.6 % above fCA / pCA2 - reproduced). Not entered: " + pc(bd) + ". " + N_NOTE, D=D, red=True, UNIT="Mg/m3",
                     **{"Data source": "Fig. 1 (digitised)", "Method used (from paper)": NM_BD})
    soc = fig["SOC"][lay]
    put("SOC(active C pool)", nb, {c: soc[t] for c, t in NC.items()}, "SOC_", N_RED + "Fig. 2 DIGITISED (raster bars; text +46 / +33 % fCA vs TA at 0-7.5 / 7.5-15 cm "
        "reproduced). Not entered: " + pc(soc) + ". " + N_NOTE, D=D, red=True, UNIT="g/kg (Walkley-Black)", **{"Data source": "Fig. 2 (digitised)", "Method used (from paper)": NM_C})
    t3 = T3N[lay]
    mac = put("MACRO", nb, {c: t3[TI[t]][0] for c, t in NC.items()}, "MACRO_", N_RED + f"Table 3 MacA (>0.25 mm). Aggregate ratio TA / fCA {t3[0][3]} / {t3[2][3]}, fractal dimension "
              f"{t3[0][6]} / {t3[2][6]} (no sheets). Not entered pCA1 / pCA2 MacA {t3[1][0]} / {t3[3][0]}. " + N_NOTE, D=D, red=True, UNIT="% (water-stable aggregates >0.25 mm)",
              **{"Data source": "Table 3", "Method used (from paper)": NM_AGG})
    mic = put("MICRO", nb, {c: t3[TI[t]][1] for c, t in NC.items()}, "MICRO_", N_RED + f"Table 3 MicA (0.053-0.25 mm). Not entered pCA1 / pCA2 {t3[1][1]} / {t3[3][1]}. " + N_NOTE,
              D=D, red=True, UNIT="% (water-stable micro-aggregates 0.053-0.25 mm)", **{"Data source": "Table 3", "Method used (from paper)": NM_AGG})
    put("WSA", nb, {c: f"=ROUND({t3[TI[t]][2]}/100,4)" for c, t in NC.items()}, "WSA_", N_RED + "Table 3 WSA printed (MacA + MicA) % / 100. " + N_NOTE, D=D, red=True,
        UNIT="g/g soil (printed WSA % / 100)", **{"Data source": "Table 3 - converted", "Method used (from paper)": NM_AGG})
    put("MWD 1", nb, {c: t3[TI[t]][4] for c, t in NC.items()}, "MWD_", N_RED + f"Table 3. Not entered pCA1 / pCA2 {t3[1][4]} / {t3[3][4]}. " + N_NOTE, D=D, red=True,
        UNIT="mm (wet sieving)", **{"Data source": "Table 3", "Method used (from paper)": NM_AGG})
    put("GMD 1", nb, {c: t3[TI[t]][5] for c, t in NC.items()}, "GMD_", N_RED + f"Table 3. Not entered pCA1 / pCA2 {t3[1][5]} / {t3[3][5]}. " + N_NOTE, D=D, red=True,
        UNIT="mm", **{"Data source": "Table 3", "Method used (from paper)": NM_AGG})
    a = fig["ASOC"]
    put("macro c", nb, {c: f"=ROUND(({a['2-4 mm'][lay][t]}+{a['0.5-2 mm'][lay][t]}+{a['0.25-0.5 mm'][lay][t]})/3,2)" for c, t in NC.items()}, "MACRO c_",
        N_RED + "DERIVED (rule 88): unweighted mean of the Fig. 3 classes 2-4, 0.5-2 and 0.25-0.5 mm (digitised raster; text checks fCA +45 % vs TA in 2-4 mm at 0-7.5 cm, "
        "+26-29 % fCA / pCA2 in 0.25-0.5 mm). Classes TA: " + ", ".join(f"{k} {a[k][lay]['TA']}" for k in a) + "; fCA: " + ", ".join(f"{k} {a[k][lay]['fCA']}" for k in a) + ". "
        + N_NOTE, D=D, red=True, UNIT="g/kg (C in >0.25 mm aggregates; unweighted mean of 3 classes)",
        **{"Data source": "DERIVED (Fig. 3, digitised)", "Method used (from paper)": NM_AGG + "; aggregate SOC by Walkley-Black, sand-corrected"})
    put("micro c", nb, {c: f"=ROUND(({a['0.12-0.25 mm'][lay][t]}+{a['0.053-0.12 mm'][lay][t]})/2,2)" for c, t in NC.items()}, "MICRO c_",
        N_RED + "DERIVED (rule 88): unweighted mean of the Fig. 3 classes 0.12-0.25 and 0.053-0.12 mm (digitised). " + N_NOTE, D=D, red=True,
        UNIT="g/kg (C in 0.053-0.25 mm aggregates; unweighted mean of 2 classes)",
        **{"Data source": "DERIVED (Fig. 3, digitised)", "Method used (from paper)": NM_AGG + "; aggregate SOC by Walkley-Black, sand-corrected"})
    t4 = T4N[lay]
    for sh, pre, k, unit in (("macro pore", "MACROPORE_", 0, "% v/v (drained at 60-cm water column)"), ("micro pore", "MICROPORE_", 1, "% v/v (total - macro)"),
                             ("POROSITY", "POROSITY_", 2, "% v/v (printed total porosity, saturation)")):
        put(sh, nb, {c: t4[TI[t]][k] for c, t in NC.items()}, pre, N_RED + f"Table 4. Not entered pCA1 / pCA2 {t4[1][k]} / {t4[3][k]}. " + N_NOTE, D=D, red=True, UNIT=unit,
            **{"Data source": "Table 4", "Method used (from paper)": NM_W})
    wc = "WATER-QUANTITY CHECK: Methods - FC and PWP = water held at 33 and 1500 kPa (pressure plate), printed % v/v; AWC = FC - PWP (available water). "
    for sh, pre, k, unit, name in (("FC (weight basis)", "FC_", 3, "% w/w (DERIVED: printed % v/v / BD)", "FC"), ("PWP (weight basis)", "PWP_", 4, "% w/w (DERIVED: printed % v/v / BD)", "PWP"),
                                   ("AWC (weight basis)", "AWCW_", 5, "% w/w (DERIVED: printed AWC % v/v / BD)", "AWC")):
        put(sh, nb, {c: f"=ROUND({t4[TI[t]][k]}/{B.ref('BD', 'BD_' + c, bdrow[lay])},2)" for c, t in NC.items()}, pre,
            N_RED + wc + f"Table 4 {name} printed v/v (TA {t4[0][k]}, fCA {t4[2][k]}) / treatment BD of the same layer (Fig. 1 row, live link). " + N_NOTE, D=D, red=True, UNIT=unit,
            **{"Data source": "Table 4 + Fig. 1 - DERIVED", "Method used (from paper)": NM_W})
    put("AWC (volume basis)", nb, {c: t4[TI[t]][5] for c, t in NC.items()}, "AWCV_", N_RED + wc + f"Table 4 as printed. Not entered pCA1 / pCA2 {t4[1][5]} / {t4[3][5]}. " + N_NOTE,
        D=D, red=True, UNIT="% v/v (printed AWC = FC - PWP)", **{"Data source": "Table 4", "Method used (from paper)": NM_W})
# Table 2 SOC stock (equivalent soil volume) -> cumulative classes
CUM = [("0-10 CM", "0-7.5 cm", 1), ("0-20 CM", "0-15 cm", 2), ("0-30 CM", "0-30 cm", 3), ("0-50 CM", "0-45 cm", 4), ("0-60 CM", "0-60 cm (sum of layers)", 5)]
for cls, rep, n in CUM:
    put("stock-SOC", {**NB, "DEPTH": cls, "DEPTH (as reported in paper)": rep}, {c: "=ROUND(" + "+".join(str(x) for x in T2N[t][:n]) + ",2)" for c, t in NC.items()}, "SOCs_",
        N_RED + f"Table 2 equivalent-soil-VOLUME stocks summed to the cumulative depth (live sum of printed layers; printed 0-60 total TA 36.70, fCA 43.67). Equivalent-soil-MASS "
        f"stocks (TA {T2M['TA']}, fCA {T2M['fCA']}; ~1143 / 1136 / 2228 / 2282 / 2346 Mg soil/ha per layer) in Notes only. Not entered pCA1 {T2N['pCA1']}, pCA2 {T2N['pCA2']}. "
        + N_NOTE, red=True, UNIT="Mg C/ha (equivalent soil volume; SOC x BD x depth)", **{"Data source": "Table 2 (cumulative sum)",
        "Method used (from paper)": "SOC stock = SOC (g/kg) x BD x depth (cm) x 0.1 per layer (eq. 5); Walkley-Black SOC"})
# Table 5 yields / economics (crop year = wheat (winter) then rice (rainy))
T5 = {"wheat": {"TA": (5.15, 5.93), "pCA1": (5.56, 6.14), "fCA": (5.48, 6.30)}, "rice": {"TA": (6.72, 5.72), "pCA1": (7.23, 6.71), "fCA": (7.28, 6.78)},
      "gg": {"pCA1": (1.10, 1.21), "fCA": (1.21, 0.90)},
      "net_w": {"TA": (41414, 61239), "pCA1": (58705, 75288), "fCA": (57356, 78139)}, "net_r": {"TA": (57084, 43308), "pCA1": (67209, 62547), "fCA": (85038, 80863)},
      "cost_w": {"TA": 47905, "pCA1": 37761, "fCA": 37761}, "cost_r": {"TA": 60440, "pCA1": 59240, "fCA": 42275},
      "res": {"TA": "0", "pCA1": "rice 2.11 / 1.96, wheat 2.09 / 2.38, greengram 2.62 / 2.84", "fCA": "rice 2.46 / 2.14, wheat 2.07 / 2.53, greengram 2.49 / 2.58"}}
NYM = "Crops harvested at maturity, grain yield at appropriate moisture (Table 5); REY (2 crops) = rice + wheat converted to rice at MSP (Fig. 6, eq. 8)"
for yi, (yr, ry) in enumerate((("2017-18", "2018"), ("2018-19", "2019"))):
    yb = {**N, "year of data collection/experiment": yr, "YEAR OF DATA (duration)": 9 + yi, "Crop/season of sampling": f"Wheat {yr} and rice {ry}"}
    put("YIELD", yb, {c: T5["wheat"][t][yi] for c, t in NC.items()}, "WYIELD_",
        f"Table 5 crop yields (wheat {yr}, rice {ry}); SYS = Fig. 6 'REY (2 crops)' DIGITISED (rice bars of Fig. 6 reproduce Table 5 within 0.05 Mg/ha). SREY incl. greengram "
        f"(TA {fig['Fig6']['SREY ' + yr]['TA']}, fCA {fig['Fig6']['SREY ' + yr]['fCA']}) and greengram yield fCA {T5['gg']['fCA'][yi]} Mg/ha in Notes (third crop). Residue retained "
        f"(Mg/ha, 2 yr): TA 0, fCA {T5['res']['fCA']}. Not entered pCA1: wheat {T5['wheat']['pCA1'][yi]}, rice {T5['rice']['pCA1'][yi]}, REY {fig['Fig6']['REY (2 crops) ' + yr]['pCA1']}. "
        + N_NOTE, Y=2, UNIT="t/ha grain (Table 5); SYS = rice-equivalent yield of rice + wheat (digitised)",
        **{"RICE YIELD_CT": T5["rice"]["TA"][yi], "RICE YIELD_CA": T5["rice"]["fCA"][yi], "SYS YIELD_CT": fig["Fig6"]["REY (2 crops) " + yr]["TA"],
           "SYS YIELD_CA": fig["Fig6"]["REY (2 crops) " + yr]["fCA"], "Data source": "Table 5; SYS Fig. 6 (digitised)", "Method used (from paper)": NYM})
    put("NET RETURN", yb, {c: T5["net_w"][t][yi] for c, t in NC.items()}, "NR_W",
        f"Table 5 net income (income from grain at MSP - cost of cultivation), INR/ha. Greengram net income fCA {(30157, 25618)[yi]} INR/ha (third crop, not in the columns). "
        f"Not entered pCA1: wheat {T5['net_w']['pCA1'][yi]}, rice {T5['net_r']['pCA1'][yi]}. " + N_NOTE, Y=2, UNIT="INR/ha (net income; 1 US$ = 68.41 INR, 2018)",
        **{"NR_RCT": T5["net_r"]["TA"][yi], "NR_RCA": T5["net_r"]["fCA"][yi], "Data source": "Table 5",
           "Method used (from paper)": "Net income = grain yield x MSP - total cost of cultivation (all inputs of the crop year)"})
yb = {**N, "year of data collection/experiment": "2017-18 & 2018-19 (2-yr mean)", "YEAR OF DATA (duration)": 10, "Crop/season of sampling": "Crop years 2017-18 and 2018-19"}
put("NET RETURN", yb, {"CT": 101523, "CA": 178586}, "NR_SYS", "Table 5 system net income (avg of 2 years; INR/ha; US$ 1484 / 2610). fCA INCLUDES greengram (third crop, rule 54 "
    "flag). Not entered pCA1 167415, pCA2 178618 INR/ha. " + N_NOTE, Y=2, UNIT="INR/ha (system net income incl. greengram in fCA - flag)",
    **{"Data source": "Table 5", "Method used (from paper)": "Sum of crop-wise net income per crop year (MSP-based income - cost of cultivation), mean of 2 years"})
put("BC ratio", {**yb, "Crop/season of sampling": "Wheat 2017-18 and rice 2018; system 2-yr mean"},
    {c: f"=ROUND({T5['net_w'][t][0]}/{T5['cost_w'][t]},2)" for c, t in NC.items()}, "BC_W",
    "DERIVED (rule 57: net / cost) from Table 5: crop costs printed only for wheat 2017-18 and rice 2018 (INR/ha: wheat TA 47905, fCA 37761; rice TA 60440, fCA 42275); system "
    "= 2-yr net income / 2-yr cost (TA 101523 / 108345; fCA 178586 / 117355, incl. greengram - flag). " + N_NOTE, Y=2, UNIT="ratio (DERIVED net income / cost of cultivation)",
    **{"BC_RCT": f"=ROUND({T5['net_r']['TA'][0]}/{T5['cost_r']['TA']},2)", "BC_RCA": f"=ROUND({T5['net_r']['fCA'][0]}/{T5['cost_r']['fCA']},2)",
       "BC_SYSCT": "=ROUND(101523/108345,2)", "BC_SYSCA": "=ROUND(178586/117355,2)", "Data source": "DERIVED from Table 5",
       "Method used (from paper)": "Net income / total cost of cultivation (MSP-based)"})

# =====================================================================================
# Study_Info, LAT_LONG, Treatment_Mapping, EXCLUDED_rows
# =====================================================================================
B.add("Study_Info", {"No.": 177, "SERIAL NO": 177, "Authors": Z["Authors"], "Year": 2021, "Journal": "Soil & Tillage Research",
                     "Full reference": "Zhao Z, Gao S, Lu C, Li X, Li F & Wang T (2021) Effects of different tillage and fertilization management practices on soil organic carbon and aggregates under the rice-wheat rotation system. Soil Tillage Res 212:105071",
                     "DOI / link": "https://doi.org/10.1016/j.still.2021.105071", "Country": "China", "Site/Location": Z["Site/Location"], "latitude": 33.70, "longitude": 113.17,
                     "latitude (as reported)": "33.70 N", "longitude (as reported)": "113.17 E", "Coordinates source": "Paper", "CLIMATE": "TEMP", "Experiment established (year)": 2010,
                     "year of data collection/experiment": "30 Oct 2019 (after rice)", "Years of data reported": "1 soil sampling", "DURATION": "4-10 Y", "SOIL": "LOAMY",
                     "Texture as reported": "Clay 27.1, silt 29.5, sand 43.4 % (clay loam by USDA triangle)", "sand": 43.4, "silt": 29.5, "CLAY": 27.1, "ph (initial)": 6.8,
                     "soc (initial)": 9.28, "Bdi": 1.33, "AVG T": 15, "RAIN FALL": 1000, "Crop rotation": "Rice-wheat", "N dose (kg/ha)": "225 (FR) / manure-N (OM)",
                     "P dose (kg/ha)": "90 P2O5", "K dose (kg/ha)": "90 K2O", "Residue type & rate (t/ha)": "Not described", "Treatments in paper": Z_TRT,
                     "Parameters extracted": "RED (after rice) 0-20 cm: SOC, LOC (POXC), DOC, MBC, MACRO / MICRO (Fig. 1, vector) + WSA, macro / micro aggregate SOC and LOC (derived)",
                     "Supplementary data?": SUPP,
                     "Notes/Doubts": "INCLUDED: CT vs pZT at two fertiliser tiers (rows a FR / b OM). Duplicate upload 126_real_f2f.pdf (same file) entered once (rule 6). " + Z_NOTE})
B.add("Study_Info", {"No.": 178, "SERIAL NO": 178, "Authors": M["Authors"], "Year": 2020, "Journal": "Plant Archives",
                     "Full reference": "Mittal R, Chakrabarti B, Rawat M, Jatav RS & Dhupper R (2020) Availability of soil nitrogen and soil biological activity in rice-wheat cropping system under conventional and conservation agricultural practice. Plant Archives 20(1):2629-2635",
                     "DOI / link": "Plant Archives 20(1):2629-2635 (e-ISSN 2581-6063)", "Country": "India (Haryana)", "Site/Location": M["Site/Location"], "latitude": 29.7, "longitude": 76.9,
                     "latitude (as reported)": "29.7 N", "longitude (as reported)": "76.9 E", "Coordinates source": "Paper", "CLIMATE": "ST", "Experiment established (year)": 2015,
                     "year of data collection/experiment": "2015-16, 2016-17", "Years of data reported": "2 (year-wise)", "DURATION": "0-3 Y", "SOIL": "LOAMY",
                     "Texture as reported": "Sandy clay loam", "ph (initial)": 8.1, "soc (initial)": 4.6, "MIN TEMP": 18, "MAX TEMP": 35, "RAIN FALL": 700,
                     "Crop rotation": "Rice-wheat", "Wheat variety": "HD 2967", "Rice variety": "Pusa 1121", "N dose (kg/ha)": "120 / 120", "P dose (kg/ha)": "60 P2O5",
                     "K dose (kg/ha)": "60 K2O", "Residue type & rate (t/ha)": "Rice residue retained in T2 / T4 (rate not stated)", "Treatments in paper": M_TRT,
                     "Parameters extracted": "Rice / wheat grain and straw yields (+ HI derived), available N, MBC, MBN, DHA (wheat flowering, year-wise; figures digitised), TOC and total N (final)",
                     "Supplementary data?": SUPP, "Notes/Doubts": "INCLUDED: CT, CA (T2, rule 23 flag), pZT, pCA. " + M_NOTE})
B.add("Study_Info", {"No.": "59 (companion 3)", "SERIAL NO": "59 (companion 3)", "Authors": S["Authors"], "Year": 2022, "Journal": "Soil & Tillage Research",
                     "Full reference": "Singh G, Bhattacharyya R, Dhaked BS & Das TK (2022) Soil aggregation, glomalin and enzyme activities under conservation tilled rice-wheat system in the Indo-Gangetic Plains. Soil Tillage Res 217:105272",
                     "DOI / link": "https://doi.org/10.1016/j.still.2021.105272", "Country": "India (Delhi)", "Site/Location": S["Site/Location"], "latitude": 28.583, "longitude": 77.2,
                     "latitude (as reported)": "28 deg 35' N", "longitude (as reported)": "77 deg 12' E", "Coordinates source": "Paper", "CLIMATE": "ST",
                     "Experiment established (year)": 2010, "year of data collection/experiment": "June 2014 (after 4 years)", "Years of data reported": "1 soil sampling",
                     "DURATION": "4-10 Y", "SOIL": "LOAMY", "Texture as reported": "Sandy clay loam", "ph (initial)": 8.3, "soc (initial)": 6.0,
                     "Crop rotation": "Rice-wheat (+ Sesbania BM / summer mungbean in some treatments)", "Wheat variety": "HD 2895", "Rice variety": "PRH 10 (hybrid)",
                     "Residue type & rate (t/ha)": "Rice residue (RR), mungbean residue (MBR), wheat residue (WR) as per Bhattacharyya et al. 2015", "Treatments in paper": S_TRT,
                     "Parameters extracted": "0-5 and 5-15 cm: beta-glucosidase, glomalin, Cmcase, alkaline phosphatase, MBC (Table 1); AM spores (Fig. 3A); MACRO / MICRO / WSA (Figs 1-2, digitised)",
                     "Supplementary data?": "Tables S1-S6 - not reachable", "Notes/Doubts": "INCLUDED as companion of 59: CT, pZT, ZT / CA rows a-c. Ergosterol (no sheet) in MBC Notes. " + S_NOTE})
B.add("Study_Info", {"No.": "48 (companion)", "SERIAL NO": "48 (companion)", "Authors": N["Authors"], "Year": 2021, "Journal": "European Journal of Soil Science",
                     "Full reference": "Mondal S, Mishra JS, Poonia SP, Kumar R, Dubey R, Kumar S, Verma M, Rao KK, Ahmed A, Dwivedi S, Bhatt BP, Malik RK, Kumar V & McDonald A (2021) Can yield, soil C and aggregation be improved under long-term conservation agriculture in the eastern Indo-Gangetic plain of India? Eur J Soil Sci 72:1742-1761",
                     "DOI / link": "https://doi.org/10.1111/ejss.13092", "Country": "India (Bihar)", "Site/Location": N["Site/Location"], "latitude": 25.58, "longitude": 85.06,
                     "latitude (as reported)": "25.58 N", "longitude (as reported)": "85.06 E", "Coordinates source": "Paper", "CLIMATE": "ST", "Experiment established (year)": 2009,
                     "year of data collection/experiment": "Soil 2019 (after rice); yields 2017-18, 2018-19", "Years of data reported": "1 soil sampling; 2 yield years",
                     "DURATION": "4-10 Y", "SOIL": "CLAYEY", "Texture as reported": "Silty clay", "soc (initial)": 8.0, "MIN TEMP": 15.6, "MAX TEMP": 31.2, "RAIN FALL": 1130,
                     "Crop rotation": "Rice-wheat (TA, fallow summer); rice-wheat-greengram (fCA)", "Residue type & rate (t/ha)": "fCA one-third rice / wheat residue (2.1-2.5 t/ha) + legume",
                     "Treatments in paper": N_TRT,
                     "Parameters extracted": ("RED soil rows at 5 layers: BD (Fig. 1), SOC (Fig. 2), SOC stock cumulative (Table 2), MACRO / MICRO / WSA / MWD / GMD (Table 3), aggregate C "
                                              "(Fig. 3, derived macro / micro), macro / micro / total pores, FC / PWP / AWC (Table 4); yields, REY, net income, B:C (Table 5, Fig. 6)"),
                     "Supplementary data?": "Fig. S1 (site map) - not needed", "Notes/Doubts": "INCLUDED as companion of 48: CT vs CA; pCA1 pending (ask); pCA2 excluded. " + N_NOTE})
for no, au, yr, ctry, site, la, lo, lar, lor, src, cl, note in [
        (177, "Zhao Z. et al.", 2021, "China", "Pingdingshan, Henan", 33.70, 113.17, "33.70 N", "113.17 E", "Paper", "TEMP", None),
        (178, "Mittal R. et al.", 2020, "India (Haryana)", "Taraori, Karnal", 29.7, 76.9, "29.7 N", "76.9 E", "Paper", "ST", None),
        ("59 (companion 3)", "Singh G. et al.", 2022, "India (Delhi)", "ICAR-IARI, New Delhi", 28.583, 77.2, "28 deg 35' N", "77 deg 12' E", "Paper", "ST", "Same trial as 59"),
        ("48 (companion)", "Mondal S. et al.", 2021, "India (Bihar)", "ICAR-RCER, Patna", 25.58, 85.06, "25.58 N", "85.06 E", "Paper", "ST", "Same trial as 48")]:
    B.add("LAT_LONG", {"No.": no, "SERIAL NO": no, "Authors": au, "Year": yr, "Country": ctry, "Site/Location": site, "latitude (as reported)": lar,
                       "longitude (as reported)": lor, "latitude": la, "longitude": lo, "Coordinates source": src, "CLIMATE": cl, "Notes": note})
TM = [
    (177, "Zhao Z. et al.", 2021, "CTFR", "Conventional tillage (20 cm) every crop + chemical fertiliser", "Tilled (20 cm)", "Conventional (20 cm)", "Not described", None, "CT", "Row a", "High", "INCLUDED"),
    (177, "Zhao Z. et al.", 2021, "RTFR", "Tillage 20 cm in the rice season, no tillage in the wheat season + chemical fertiliser", "Tilled (20 cm)", "Zero till", "Not described", None, "pZT", "Row a; conventional rice + ZT wheat (rule 103)", "High", "INCLUDED"),
    (177, "Zhao Z. et al.", 2021, "CTOM", "CT + organic manure (swine compost replacing fertiliser N)", "Tilled", "Conventional", "Not described", None, "CT", "Row b (organic-manure tier, rule 89 flag)", "Medium", "INCLUDED - FLAG"),
    (177, "Zhao Z. et al.", 2021, "RTOM", "RT + organic manure", "Tilled", "Zero till", "Not described", None, "pZT", "Row b", "Medium", "INCLUDED - FLAG"),
    (177, "Zhao Z. et al.", 2021, "CT (no fertiliser)", "Conventional tillage, unfertilised", "Tilled", "Conventional", "-", None, "EXCLUDED", "Unfertilised control (rule 78); values in Notes", "High", "EXCLUDED"),
    (178, "Mittal R. et al.", 2020, "T1 TPR + CTW", "Transplanted rice + conventionally tilled wheat", "Puddled TPR", "Conventional", "No", None, "CT", "Conventional both phases", "High", "INCLUDED"),
    (178, "Mittal R. et al.", 2020, "T2 DSR + ZTW + R", "Direct-seeded rice + zero-tilled wheat with residue retention", "DSR (tillage not stated)", "Zero till", "Yes", None, "CA", "Rule 23: rice tillage not stated -> wheat phase (flag)", "Medium", "INCLUDED - FLAG"),
    (178, "Mittal R. et al.", 2020, "T3 TPR + ZTW", "Transplanted rice + zero-tilled wheat", "Puddled TPR", "Zero till", "No", None, "pZT", "Partial code (rule 68)", "High", "INCLUDED"),
    (178, "Mittal R. et al.", 2020, "T4 TPR + ZTW + R", "Transplanted rice + zero-tilled wheat with residue retention", "Puddled TPR", "Zero till", "Yes", None, "pCA", "Partial code (rule 68)", "High", "INCLUDED"),
    ("59 (companion 3)", "Singh G. et al.", 2022, "TPR-CTW", "Puddled TPR + conventional-till wheat", "Puddled", "Conventional", "No", None, "CT", "As 59", "High", "INCLUDED"),
    ("59 (companion 3)", "Singh G. et al.", 2022, "TPR-ZTW", "Puddled TPR + zero-till wheat", "Puddled", "Zero till", "No", None, "pZT", "Excluded in 59; partial code now (rules 68 / 85)", "High", "INCLUDED"),
    ("59 (companion 3)", "Singh G. et al.", 2022, "DSR-ZTW / DSR + BM-ZTW / DSR + MBR-ZTW-ZTMB", "DSR (tilled yrs 1-3, ZT yr 4) + ZT wheat, no rice residue (+ Sesbania BM / + mungbean)", "Dry-tilled DSR (yrs 1-3), ZT (yr 4)", "Zero till", "No (BM / mungbean residue only)", None, "ZT", "Rows a / b / c; as author-confirmed 59 companions (rule 103 question)", "Medium", "INCLUDED - FLAG / ASK"),
    ("59 (companion 3)", "Singh G. et al.", 2022, "... + RR (CA modules 1 and 2)", "As above + rice residue retention (CA module 2 also wheat residue + ZT mungbean)", "Dry-tilled DSR (yrs 1-3), ZT (yr 4)", "Zero till", "Yes", None, "CA", "Rows a / b / c", "Medium", "INCLUDED - FLAG / ASK"),
    ("48 (companion)", "Mondal S. et al.", 2021, "TA", "CT wheat - fallow - puddled TPR, residues removed", "Puddled", "Conventional", "No", None, "CT", "As old-master 48 S1", "High", "INCLUDED"),
    ("48 (companion)", "Mondal S. et al.", 2021, "fCA", "NT wheat - NT greengram - NT DSR, one-third rice / wheat residue + legume residue", "Zero till", "Zero till", "Yes", "2.1-2.5", "CA", "As old-master 48 S3 (greengram third crop flag)", "High", "INCLUDED - FLAG"),
    ("48 (companion)", "Mondal S. et al.", 2021, "pCA1", "NT wheat - NT greengram - CT rice (puddled 2009-14; unpuddled machine TPR 2014-19)", "Conventional tillage", "Zero till", "CONTRADICTORY: Table 1 removed, Table 5 2.0-2.4 t/ha retained", None, "PENDING", "pZT or pCA (rule 103)? Author decision; values in Notes", "Low", "NOT ENTERED - ASK AUTHOR"),
    ("48 (companion)", "Mondal S. et al.", 2021, "pCA2", "Potato+maize / mustard - maize - rice", "-", "No wheat", "-", None, "EXCLUDED", "Not a rice-wheat system (rule 31)", "High", "EXCLUDED"),
]
th = ["SERIAL NO", "Authors", "Year", "Paper's treatment label (verbatim)", "Full description from paper", "Rice-phase tillage", "Wheat-phase tillage",
      "Residue retained?", "Residue rate (t/ha)", "ASSIGNED CODE", "Rationale", "Confidence", "Status"]
for row in TM:
    d = dict(zip(th, row))
    d["No."] = row[0]
    B.add("Treatment_Mapping", d)
for ser, au, yr, why in (
        (177, "Zhao Z. et al.", 2021, "Unfertilised CT (rule 78) - values in the Notes of every 177 row. Duplicate upload 126_real_f2f.pdf is byte-identical to 126_2.pdf (entered once, rule 6)."),
        ("48 (companion)", "Mondal S. et al.", 2021, "pCA1 NOT ENTERED pending the author (residue contradiction between Tables 1 and 5); pCA2 excluded (no wheat). Values in the Notes of the 48 (companion) rows.")):
    B.add("EXCLUDED_rows", {"Sheet": "(treatments)", "SERIAL NO": ser, "Authors": au, "Year": yr, "Reason for exclusion": why, "Full row (header = value)": "-"})
B.save(OUT)
print("batch 14 written to", OUT)
