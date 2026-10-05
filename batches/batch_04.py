"""Batch 04 (2026-10-05): uploaded files 114.pdf, 115_rep.pdf, 116_real.pdf, 116_rep.pdf, 114_reqal.pdf.

  169               Singh V.K. et al. 2005 (Field Crops Res. 92:85-105)           - EXCLUDED (rice vs pigeonpea x N x P; no tillage/residue contrast)
  23 (companion 3)  Jat H.S. et al. 2019 (Soil Tillage Res. 190:128-138)        - CSSRI Karnal scenarios: Sc1 CT, Sc2 pCA, Sc3 CA (red rows)
  165 (companion)   Meena A.L. et al. 2020 (Commun. Soil Sci. Plant Anal.)      - IARI organic project (same as 165): FYM/VC (CT) vs +CR (CTR) (red soil rows)
  23 (companion 4)  Jat H.S. et al. 2019 (Catena, accepted manuscript)          - same trial: C pools, stocks, biology (red rows)
  131 (companion)   Zhang Y.-P. et al. 2023 (Sustainability 15:474)             - re-entry of old-master 131: CN = CA, PR = pCA (rule 68)

Usage: python batches/batch_04.py <in.xlsx> <out.xlsx>
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


def dur_class(y):
    return "0-3 Y" if y <= 3 else ("4-10 Y" if y <= 10 else ">10 Y")


def put(sheet, base, vals, prefix, red=False, **extra):
    d = dict(base)
    for code, v in vals.items():
        d[prefix + code] = v
    d.update(extra)
    return B.add(sheet, d, red=red)


# =====================================================================================
# 131 (companion)  ZHANG et al. 2023  (CN = CA, PR = pCA)
# =====================================================================================
ZH_TRT = ("TREATMENTS IN PAPER (one 960 m2 strip per pattern, 2017-2019 rice seasons, Taoluo, Rizhao): RT = rotational tillage before rice "
          "(no-till 2017 and 2018, plough 2019; no-till dry direct-seeded rice) -> EXCLUDED (alternate tillage); CN = continuous no-till dry "
          "direct-seeded rice (wide-belt stubble seeder) 2017-2019 -> CA ; PR = plough + rotary tillage, irrigation, puddling and transplanting "
          "(30 x 12 cm) every year -> pCA. In ALL treatments wheat (Yannong 21, 187.5 kg/ha, 14 Oct) is sown WITHOUT tillage with the same seeder, "
          "and the crushed straw (<=10 cm) of the previous crop is fully returned. Before the trial: ploughing + rotary 15-18 cm, transplanting, straw removed.")
ZH = {"No.": "131 (companion)", "SERIAL NO": "131 (companion)", "Authors": "Zhang Y.-P., Li X., He H.-J., Zhou H., Geng D.-Y. & Zhang Y.-Z.", "Year": 2023,
      "Journal": "Sustainability", "Country": "China (Shandong)", "Site/Location": "Taoluo Town, Donggang District, Rizhao, Shandong",
      "latitude": 35.27, "longitude": 119.38, "CLIMATE": "TEMP", "Rep": 3, "RAIN FALL": 916, "LATT": 35.27, "AVG T": 12.6,
      "ph (initial)": 6.8, "soc (initial)": 5.75, "Bdi": 1.423,
      "Treatment mapping (paper's name -> code)": "CN (NT dry DSR + NT wheat, straw returned) -> CA ; PR (plough + rotary + puddled transplanted rice, NT wheat, straw returned) -> pCA ; RT -> EXCLUDED",
      "Fertilizer dose & other management": ("Rice: 600 kg/ha slow-release 25-10-10 (deep-placed at sowing in CN; at ploughing in PR) + 300 kg/ha compound 53-10-30 later; "
                                             "KH2PO4 0.3% foliar x2. Wheat: N 225, P2O5 180, K2O 25 kg/ha deep-placed at sowing (all). Rice Linhan 1 (125 d), 127.5 kg seed/ha in 12 cm "
                                             "wide belts (CN); PR transplanted 10 July. CN: intermittent / alternate wet-dry irrigation; PR: traditional flooding. Paddy soil; "
                                             "initial TN 0.95 g/kg, alkali-N 82.43, Olsen P 34.30, K 73.10 mg/kg (0-30 cm), BD 1.423."),
      "Treatment details (from paper)": ZH_TRT}
ZH_NOTE = ("RE-ENTRY of old-master study 131 (excluded there 2026-10-04 as a rotation mismatch); re-evaluated under the PARTIAL-CA rule (rule 68): "
           "PR = puddled transplanted rice + no-till wheat with straw -> pCA, CN -> CA. FLAG: UNREPLICATED (one strip per pattern, multi-point sampling) - Rep kept 3 by rule. "
           "Coordinates approximate (Taoluo town centre; paper gives none). Texture not stated (paddy soil). Supplementary: none found. Source file 114_reqal.pdf.")
ZLAY = [("0-15 CM", "0-10 cm", 1, 10, 0), ("15-30 CM", "10-20 cm", 2, 10, 1), ("15-30 CM", "20-30 cm", 2, 10, 2)]
# Fig. 3 BD (digitised): [depth][year] = (CN, PR)
ZBD = {0: {2018: (1.374, 1.395), 2019: (1.376, 1.397), 2020: (1.382, 1.408)},
       1: {2018: (1.421, 1.434), 2019: (1.418, 1.435), 2020: (1.455, 1.441)},
       2: {2018: (1.490, 1.501), 2019: (1.480, 1.517), 2020: (1.483, 1.533)}}
zbd_row = {}
for depth, rep, D, th, k in ZLAY:
    for yr in (2018, 2019, 2020):
        cn, pr = ZBD[k][yr]
        base = {**ZH, "year of data collection/experiment": yr, "DURATION": "0-3 Y", "YEAR OF DATA (duration)": yr - 2017,
                "DEPTH": depth, "DEPTH (as reported in paper)": rep, "Obs": D,
                "Crop/season of sampling": f"Wheat season - after the {yr} wheat harvest (ring knife 100 cm3)"}
        r = put("BD", base, dict(CA=cn, pCA=pr), "BD_", UNIT="Mg/m3", **{"Data source": "Fig. 3 (digitised)",
                "Method used (from paper)": "Ring-knife (100 cm3) drying-weighing method",
                "Notes/Doubts": (f"Year-wise (rule 37). DIGITISED from Fig. 3{'abc'[k]}; 2020 values reproduce the printed differences (0-10 cm RT 0.037/0.064 below CN/PR; 20-30 cm 0.056/0.051). "
                                 "2017 point = before the first treated rice (all ~equal), not entered. RT (excluded) 2018-2020: "
                                 + {0: "1.377/1.378/1.345", 1: "1.420/1.416/1.412", 2: "1.492/1.476/1.478"}[k] + ". " + ZH_NOTE)})
        zbd_row[(k, yr)] = r
        put("POROSITY", base, {c: f"=ROUND((1-{B.ref('BD', 'BD_' + c, r)}/2.65)*100,2)" for c in ("CA", "pCA")}, "POROSITY_", UNIT="% v/v",
            **{"Data source": "DERIVED from Fig. 3 BD", "Method used (from paper)": "Porosity = (1 - BD/PD) x 100",
               "Notes/Doubts": "DERIVED (rule 73): no PD in the paper -> 2.65 Mg/m3 (flag). " + ZH_NOTE})
# Table 2 aggregates (after 3 years), Table 3 nutrients
AGG = {0: (31.44, 22.38, 0.54, 0.38, 3.24, 2.21, 77.41, 64.53, 59.39, 65.32),
       1: (26.26, 27.88, 0.32, 0.38, 2.59, 2.76, 68.62, 70.12, 61.73, 60.24),
       2: (22.23, 18.82, 0.27, 0.21, 2.17, 2.11, 63.86, 55.76, 65.19, 66.25)}
NUT = {0: (1.18, 0.96, 93.21, 91.42, 36.28, 32.54, 106.36, 102.55, 6.98, 6.32),
       1: (0.82, 0.97, 87.05, 88.00, 32.60, 35.68, 90.56, 99.47, 6.25, 6.92),
       2: (0.78, 0.68, 75.05, 60.00, 26.40, 23.68, 80.56, 69.47, 5.92, 5.65)}
soc_r = {}
for depth, rep, D, th, k in ZLAY:
    base = {**ZH, "year of data collection/experiment": 2020, "DURATION": "0-3 Y", "YEAR OF DATA (duration)": 3,
            "DEPTH": depth, "DEPTH (as reported in paper)": rep, "Obs": D,
            "Crop/season of sampling": "Wheat season - after three years of the tillage patterns (2020 wheat harvest assumed)"}
    w0, w1, m0, m1, d0, d1, ms0, ms1, k0, k1 = AGG[k]
    nt = (f"Mechanically (dry) stable R>0.25: CN {ms0}, PR {ms1} %; aggregate disruption K: CN {k0}, PR {k1} %. Sampling year assumed 2020 (paper: 'after three years'). " + ZH_NOTE)
    put("MACRO", base, dict(CA=w0, pCA=w1), "MACRO_", UNIT="% (water-stable aggregates >0.25 mm)", **{"Data source": "Table 2",
        "Method used (from paper)": "Wet sieving in deionised water (R>0.25 water stability)",
        "Notes/Doubts": "WSA (>0.053 mm) cannot be derived - only the >0.25 mm fraction is printed. " + nt}, **{})
    put("MWD 1", base, dict(CA=m0, pCA=m1), "MWD_", UNIT="mm (wet sieving)", **{"Data source": "Table 2", "Method used (from paper)": "Wet sieving; MWD", "Notes/Doubts": nt})
    put("MWDA", base, dict(CA=d0, pCA=d1), "MWDA_", UNIT="mm (dry sieving, mechanically stable aggregates)", **{"Data source": "Table 2",
        "Method used (from paper)": "Dry sieving (mechanical stability); MWD", "Notes/Doubts": nt})
    tn0, tn1, an0, an1, p0, p1, kk0, kk1, oc0, oc1 = NUT[k]
    nn = "Table 3 (after three years). " + ZH_NOTE
    soc_r[k] = put("SOC(active C pool)", base, dict(CA=oc0, pCA=oc1), "SOC_", UNIT="g/kg", **{"Data source": "Table 3",
                   "Method used (from paper)": "K2Cr2O7 volumetric (external heating) method", "Notes/Doubts": nn})
    put("total N", base, dict(CA=f"=ROUND({tn0}*1000,0)", pCA=f"=ROUND({tn1}*1000,0)"), "TN_", UNIT="mg/kg (printed g/kg x 1000)",
        **{"Data source": "Table 3 - converted", "Method used (from paper)": "Total N", "Notes/Doubts": nn})
    bdr = zbd_row[(k, 2020)]
    for sheet, pre, v0, v1, lab, meth in [("N", "N_", an0, an1, "alkali-hydrolysable N", "Alkali-hydrolysis diffusion"),
                                          ("P", "P_", p0, p1, "available P", "Available P (Olsen-type)"),
                                          ("K", "K_", kk0, kk1, "available K", "Available (rapidly available) K")]:
        put(sheet, base, {c: f"=ROUND({v}*{B.ref('BD', 'BD_' + c, bdr)}*{th}*0.1,1)" for c, v in (("CA", v0), ("pCA", v1))}, pre,
            UNIT=f"kg/ha ({lab}: printed mg/kg x treatment BD x {th} cm x 0.1)",
            **{"Data source": "Table 3 - converted", "Method used (from paper)": meth,
               "Notes/Doubts": f"CONVERTED with the same treatment's 2020 BD of this layer (live link): printed CN {v0}, PR {v1} mg/kg. " + nn})
# SOC stock (cumulative) and sequestration
stock = {}
for cum, ks in (("0-10 CM", [0]), ("0-20 CM", [0, 1]), ("0-30 CM", [0, 1, 2])):
    vals = {}
    for c in ("CA", "pCA"):
        terms = [f"{B.ref('SOC(active C pool)', 'SOC_' + c, soc_r[k])}*{B.ref('BD', 'BD_' + c, zbd_row[(k, 2020)])}*10*0.1" for k in ks]
        vals[c] = "=ROUND(" + "+".join(terms) + ",2)"
    stock[cum] = put("stock-SOC", {**ZH, "year of data collection/experiment": 2020, "DURATION": "0-3 Y", "YEAR OF DATA (duration)": 3},
                     vals, "SOCs_", **{"DEPTH": cum, "DEPTH (as reported in paper)": " + ".join(["0-10", "10-20", "20-30"][:len(ks)]) + " cm summed",
                                       "Obs": 1, "UNIT": "Mg C/ha", "initial": "=ROUND(5.75*1.423*%d*0.1,2)" % (10 * len(ks)),
                                       "Data source": "DERIVED (Table 3 SOC x Fig. 3 BD)", "Method used (from paper)": "Stock = SOC x BD x thickness x 0.1",
                                       "Crop/season of sampling": "Wheat season - after three years",
                                       "Notes/Doubts": "DERIVED (rule 48): SOC (g/kg) x same-layer 2020 BD x 10 cm x 0.1, summed cumulatively; 'initial' = paper's 0-30 cm mean OC 5.75 g/kg x BD 1.423. " + ZH_NOTE})
r30 = stock["0-30 CM"]
put("c sequestration rate", {**ZH, "year of data collection/experiment": 2020, "DURATION": "0-3 Y", "YEAR OF DATA (duration)": 3},
    {c: f"=ROUND(({B.ref('stock-SOC', 'SOCs_' + c, r30)}-{B.ref('stock-SOC', 'initial', r30)})/3,3)" for c in ("CA", "pCA")}, "SSOC_",
    **{"DEPTH": "0-30 CM", "DEPTH (as reported in paper)": "0-30 cm", "Obs": 1, "UNIT": "Mg C/ha/yr",
       "Data source": "DERIVED", "Method used (from paper)": "(stock 0-30 cm - initial stock)/3 yr",
       "Notes/Doubts": "DERIVED (rule 48) from the 0-30 cm stock row and the initial stock (5.75 g/kg x 1.423 Mg/m3 x 30 cm); 3 years. Initial OC is a 0-30 cm mean, not layer-wise (flag). " + ZH_NOTE})
# Yield and components (Tables 4-5)
yb = {**ZH, "year of data collection/experiment": "2019-20 (assumed)", "DURATION": "0-3 Y", "YEAR OF DATA (duration)": 3, "Obs": 1,
      "Crop/season of sampling": "Rice and wheat (year not stated; final cycle assumed)"}
yn = ("Year not stated (paper reports one set of yields after the 3-year comparison) - assumed final cycle. RT (excluded): rice 8.970, wheat 7.818 t/ha. "
      "Rice spike length CN 12.8 / PR 13.9 cm, seed setting 92 / 96 %. Wheat basic seedlings 1.63 / 1.62 x10^6/ha, tillers per plant 3.59 / 3.42. " + ZH_NOTE)
B.add("YIELD", {**yb, "RICE YIELD_CA": "=7866/1000", "RICE YIELD_pCA": "=9020/1000", "WYIELD_CA": "=7073/1000", "WYIELD_pCA": "=6898/1000",
                "UNIT": "t/ha (printed kg/ha / 1000)", "Data source": "Tables 4-5", "Method used (from paper)": "5 x 1 m2 quadrats; yield from components", "Notes/Doubts": yn})
put("PANICLE-SPIKE DENSITY", yb, {"WCA": "=5.87*100", "WpCA": "=5.78*100", "RCA": "=4.41*100", "RpCA": "=3.81*100"}, "PSD_",
    UNIT="no./m2 (printed 10^6/ha x 100)", **{"Data source": "Tables 4-5 - converted", "Method used (from paper)": "Effective panicles in 1 m2 quadrats", "Notes/Doubts": yn})
put("GRAINS PER PANICLE", yb, {"WCA": 32.5, "WpCA": 32.3, "RCA": 88, "RpCA": 98}, "GPP_", UNIT="no. grains per panicle / spike",
    **{"Data source": "Tables 4-5", "Method used (from paper)": "Primary x 5.5 + secondary branches x 3 (rice); effective grains per spike (wheat)", "Notes/Doubts": yn})
put("1000-GRAIN WEIGHT", yb, {"WCA": 43.6, "WpCA": 42.8, "RCA": 24.6, "RpCA": 27.3}, "TGW_", UNIT="g",
    **{"Data source": "Tables 4-5", "Method used (from paper)": "1000 seeds counted, 2 repeats", "Notes/Doubts": yn})

# =====================================================================================
# 23 (companion 3)  JAT et al. 2019 Soil Tillage Res.
# =====================================================================================
JT_TRT = ("TREATMENTS IN PAPER (CSISA scenario trial, ICAR-CSSRI Karnal, est. 2009, RBD 3 reps, 100 x 20 m plots): Sc1 conventional rice-wheat "
          "(puddled manually transplanted rice, broadcast CT wheat, residues removed; farmers' practice) -> CT ; Sc2 partial CA rice-wheat-mungbean "
          "(puddled transplanted rice; ZT drill-seeded wheat and mungbean; anchored rice stubble 4.1-12.7 t/ha retained at wheat sowing, mungbean residue "
          "incorporated during puddling) -> pCA ; Sc3 full CA rice-wheat-mungbean (ZT DSR, ZT wheat, ZT mungbean, residues retained on the surface) -> CA ; "
          "Sc4 full CA maize-wheat-mungbean -> EXCLUDED (maize). Residue added 2009-15: Sc2 78.5, Sc3 74.5 t/ha.")
JT = {"No.": "23 (companion 3)", "SERIAL NO": "23 (companion 3)", "Authors": "Jat H.S., Datta A., Choudhary M., Yadav A.K., Choudhary V., Sharma P.C., Gathala M.K., Jat M.L. & McDonald A.",
      "Year": 2019, "Journal": "Soil & Tillage Research", "Country": "India (Haryana)", "Site/Location": "ICAR-CSSRI research farm, Karnal (CSISA scenario trial, est. 2009)",
      "latitude": 29.70, "longitude": 76.96, "CLIMATE": "ST", "SOIL": "LOAMY", "Rep": 3, "RAIN FALL": 700, "MIN TEMP": 2, "MAX TEMP": 42.5, "LATT": 29.70,
      "Treatment mapping (paper's name -> code)": "Sc1 -> CT ; Sc2 (puddled TPR + ZT wheat + ZT mungbean, residue) -> pCA ; Sc3 (ZT DSR + ZT wheat + ZT mungbean, residue) -> CA ; Sc4 maize -> EXCLUDED",
      "Fertilizer dose & other management": ("Sc1: rice 175-58-0, wheat 150-58-0 kg N-P-K/ha (farmers' practice, continuous flooding). Sc2/Sc3: wheat 151-64-32; rice 151-58-60 (Sc2), 162-64-62 (Sc3); "
                                             "tensiometer-based irrigation (Sc2 TPR -40/-50 kPa after 15-20 d flooding; Sc3 DSR -20/-30 kPa). Mungbean unfertilised. Reclaimed alkali loam (Typic Natrustalf)."),
      "Treatment details (from paper)": JT_TRT}
JT_NOTE = ("GREEN MANURE / 3rd CROP: ZT mungbean in Sc2 and Sc3, not in Sc1 (rule 71). pCA (Sc2) was EXCLUDED in old-master study 23 (rotation mismatch) and is now coded pCA (rule 68). "
           "COMPANION of old-master study 23 (same CSSRI trial). Supplementary: none found. Source file 115_rep.pdf.")
RED_NOTE = "RICE-SEASON DATA (RED ROW): soil sampled only after rice harvest (October). "
for yr, dur in ((2013, 4), (2015, 6)):
    for depth, rep in (("0-15 CM", "0-15 cm"), ("15-30 CM", "15-30 cm")):
        base = {**JT, "year of data collection/experiment": yr, "DURATION": dur_class(dur), "YEAR OF DATA (duration)": dur,
                "DEPTH": depth, "DEPTH (as reported in paper)": rep, "Obs": 1,
                "Crop/season of sampling": f"RICE SEASON - after rice harvest, October {yr} ({dur} years)"}
        dupe = ("DUPLICATE SEASON: old-master 23 (companion 2) (Jat et al. 2018, Oct 2013) printed the same WB-C for Sc1/Sc3 - keep one when merging. " if yr == 2013 else "")
        wb_ = {2013: {"0-15 CM": (4.5, 5.5, 7.5), "15-30 CM": (3.5, 4.9, 3.6)}, 2015: {"0-15 CM": (4.9, 6.8, 8.1), "15-30 CM": (4.4, 5.5, 4.0)}}[yr][depth]
        toc = {2013: {"0-15 CM": (6.5, 8.1, 10.9), "15-30 CM": (3.8, 5.4, 3.6)}, 2015: {"0-15 CM": (6.3, 8.7, 11.4), "15-30 CM": (5.6, 7.0, 5.2)}}[yr][depth]
        put("SOC(active C pool)", base, dict(CT=wb_[0], pCA=wb_[1], CA=wb_[2]), "SOC_", red=True, UNIT="g/kg (Walkley-Black)",
            **{"Data source": "Table 2", "Method used (from paper)": "Walkley & Black (1934)", "Notes/Doubts": RED_NOTE + dupe + "Sc4 (excluded): " + {2013: "7.7 / 3.6", 2015: "8.2 / 3.4"}[yr] + ". " + JT_NOTE})
        tr = put("TOC", base, dict(CT=toc[0], pCA=toc[1], CA=toc[2]), "TOC_", red=True, UNIT="g/kg (Elementar Vario TOC cube)",
                 **{"Data source": "Table 2", "Method used (from paper)": "Dry combustion, Elementar Vario TOC Cube", "Notes/Doubts": RED_NOTE + JT_NOTE})
        if yr == 2013:
            B_TOC13 = globals().setdefault("B_TOC13", {})
            B_TOC13[depth] = tr
        # aggregates Table 3
        A = {(2013, "0-15 CM"): ((21.93, 8.91, 30.84, 1.48, 0.76), (32.34, 9.10, 41.44, 2.06, 0.98), (40.33, 3.44, 43.77, 2.44, 1.28)),
             (2015, "0-15 CM"): ((23.46, 9.82, 33.29, 1.67, 0.79), (42.57, 6.63, 49.20, 2.20, 1.15), (44.40, 6.91, 51.32, 2.65, 1.29)),
             (2013, "15-30 CM"): ((17.95, 10.85, 28.80, 1.27, 0.62), (17.54, 12.95, 30.50, 1.31, 0.56), (13.90, 12.49, 26.39, 1.34, 0.49)),
             (2015, "15-30 CM"): ((20.28, 8.79, 29.07, 1.12, 0.66), (30.99, 8.43, 39.41, 1.56, 0.66), (24.80, 7.11, 31.91, 1.53, 0.63))}[(yr, depth)]
        AS = {(2013, "0-15 CM"): "AS 22.42/32.61/41.54 %, AR 0.79/1.83/4.62", (2015, "0-15 CM"): "AS 24.00/42.92/45.74 %, AR 0.89/6.00/7.97",
              (2013, "15-30 CM"): "AS 18.49/17.69/14.32 %, AR 0.56/0.55/0.39", (2015, "15-30 CM"): "AS 20.88/31.24/25.55 %, AR 0.69/1.64/0.99"}[(yr, depth)]
        an = RED_NOTE + f"Not on a sheet (Sc1/Sc2/Sc3): {AS}. " + JT_NOTE
        meth = "Wet sieving (Yoder 1936), 100 g of 5-8 mm aggregates, 2 min slaking, 30 min at 50 cycles/min; sand-corrected"
        put("MACRO", base, dict(CT=A[0][0], pCA=A[1][0], CA=A[2][0]), "MACRO_", red=True, UNIT="% (water-stable macro-aggregates >0.25 mm)",
            **{"Data source": "Table 3", "Method used (from paper)": meth, "Notes/Doubts": an})
        put("MICRO", base, dict(CT=A[0][1], pCA=A[1][1], CA=A[2][1]), "MICRO_", red=True, UNIT="% (water-stable micro-aggregates 0.05-0.25 mm)",
            **{"Data source": "Table 3", "Method used (from paper)": meth, "Notes/Doubts": an})
        put("WSA", base, {c: f"=ROUND({v}/100,4)" for c, v in (("CT", A[0][2]), ("pCA", A[1][2]), ("CA", A[2][2]))}, "WSA_", red=True,
            UNIT="g/g soil (printed total WSA % / 100; macro + micro >0.05 mm)", **{"Data source": "Table 3 - converted", "Method used (from paper)": meth, "Notes/Doubts": an})
        put("MWD 1", base, dict(CT=A[0][3], pCA=A[1][3], CA=A[2][3]), "MWD_", red=True, UNIT="mm (wet sieving)", **{"Data source": "Table 3", "Method used (from paper)": meth, "Notes/Doubts": an})
        put("GMD 1", base, dict(CT=A[0][4], pCA=A[1][4], CA=A[2][4]), "GMD_", red=True, UNIT="mm", **{"Data source": "Table 3", "Method used (from paper)": meth, "Notes/Doubts": an})

agg = json.load(open(os.path.join(DIG, "jat2019_aggC.json")))
poc = json.load(open(os.path.join(DIG, "jat2019_POC.json")))
MAC = [">2", "2-1", "1-0.5", "0.5-0.25"]
MIC = ["0.25-0.1", "0.1-0.05"]
for key, yr, dur, depth, rep, pockey in [("Fig2a_0-15_2013", 2013, 4, "0-15 CM", "0-15 cm", "a0-15"), ("Fig2b_0-15_2015", 2015, 6, "0-15 CM", "0-15 cm", "b0-15"),
                                         ("Fig3a_15-30_2013", 2013, 4, "15-30 CM", "15-30 cm", "a15-30"), ("Fig3b_15-30_2015", 2015, 6, "15-30 CM", "15-30 cm", "b15-30")]:
    base = {**JT, "year of data collection/experiment": yr, "DURATION": dur_class(dur), "YEAR OF DATA (duration)": dur,
            "DEPTH": depth, "DEPTH (as reported in paper)": rep, "Obs": 1, "Crop/season of sampling": f"RICE SEASON - after rice harvest, October {yr}"}
    d = agg[key]
    cls = {sc: ", ".join(f"{c} {d[c][sc]}" for c in MAC + MIC + ["silt+clay"]) for sc in ("Sc1", "Sc2", "Sc3")}
    note = (RED_NOTE + "Aggregate-associated C (TOC analyser) READ FROM THE VECTOR Fig. " + key[3:5] + " (exact bar geometry; 2015 Sc2 1-0.5 mm = 8.94 as printed in text). "
            f"Class values g/kg - Sc1: {cls['Sc1']}; Sc2: {cls['Sc2']}; Sc3: {cls['Sc3']}. " + JT_NOTE)
    sc = {"CT": "Sc1", "pCA": "Sc2", "CA": "Sc3"}
    put("macro c", base, {c: "=ROUND(AVERAGE(" + ",".join(str(d[k][s]) for k in MAC) + "),2)" for c, s in sc.items()}, "MACRO c_", red=True,
        UNIT="g/kg (C in >0.25 mm aggregates; UNWEIGHTED mean of 4 classes)", **{"Data source": f"Fig. {key[3:5]} (vector) - DERIVED",
        "Method used (from paper)": "Aggregate-associated C by Elementar Vario TOC Cube", "Notes/Doubts": "DERIVED: unweighted mean of the >2, 2-1, 1-0.5, 0.5-0.25 mm classes (class masses not printed - flag). " + note})
    put("micro c", base, {c: "=ROUND(AVERAGE(" + ",".join(str(d[k][s]) for k in MIC) + "),2)" for c, s in sc.items()}, "MICRO c_", red=True,
        UNIT="g/kg (C in 0.05-0.25 mm aggregates; UNWEIGHTED mean of 2 classes)", **{"Data source": f"Fig. {key[3:5]} (vector) - DERIVED",
        "Method used (from paper)": "Aggregate-associated C by Elementar Vario TOC Cube", "Notes/Doubts": "DERIVED: unweighted mean of the 0.25-0.1 and 0.1-0.05 mm classes. " + note})
    p = poc[pockey]
    put("PSOC", base, dict(CT=p[0], pCA=p[1], CA=p[2]), "PSOC_", red=True, UNIT="g/kg (particulate organic C, >53 um)", **{"Data source": f"Fig. 4{pockey[0]} (digitised)",
        "Method used (from paper)": "Cambardella & Elliott (1992)", "Notes/Doubts": RED_NOTE + f"DIGITISED from raster Fig. 4; 2015 0-15 cm increases over Sc1 (Sc3 +83%, Sc2 +68%) match the text. Sc4 (excl.) {p[3]}. " + JT_NOTE})
rey = json.load(open(os.path.join(DIG, "jat2019_REY.json")))
for i, (yr, v) in enumerate(rey.items(), 1):
    B.add("YIELD", {**JT, "year of data collection/experiment": yr, "DURATION": dur_class(i), "YEAR OF DATA (duration)": i, "Obs": 1,
                    "SYS YIELD_CT": v["Sc1"], "SYS YIELD_pCA": v["Sc2"], "SYS YIELD_CA": v["Sc3"],
                    "UNIT": "t/ha rice-equivalent system yield (incl. mungbean in Sc2/Sc3)", "Crop/season of sampling": f"System {yr}",
                    "Data source": "Fig. 6 (digitised)", "Method used (from paper)": "REY = sum(yield x MSP)/MSP rice; grain at 14% moisture",
                    "Notes/Doubts": (f"Year-wise (rule 37). DIGITISED from raster Fig. 6 (2009-10 Sc2 16.77 vs 16.76 in text). SYS value INCLUDES MUNGBEAN in Sc2/Sc3 (flag, rule 54). "
                                     f"Sc4 (excl.) {v['Sc4']}. 4-yr mean in 23 (companion 4): Sc1 12.39, Sc2 14.87, Sc3 13.73. " + JT_NOTE)})

# =====================================================================================
# 23 (companion 4)  JAT et al. 2019 Catena (accepted manuscript)
# =====================================================================================
JC = {**JT, "No.": "23 (companion 4)", "SERIAL NO": "23 (companion 4)",
      "Authors": "Jat H.S., Datta A., Choudhary M., Sharma P.C., Yadav A.K., Choudhary V., Gathala M.K., Jat M.L. & McDonald A.", "Journal": "Catena (accepted manuscript)",
      "year of data collection/experiment": 2013, "DURATION": "4-10 Y", "YEAR OF DATA (duration)": 4, "RAIN FALL": 670, "MAX TEMP": 31.68, "MIN TEMP": 11.62,
      "Crop/season of sampling": "RICE SEASON - after rice harvest, October 2013 (4 cycles)", "soc (initial)": 4.5,
      "Treatment details (from paper)": JT_TRT.replace("Residue added 2009-15: Sc2 78.5, Sc3 74.5 t/ha.", "Residue added 2009-13: Sc2 47.9, Sc3 56.1 t/ha.")}
JC_NOTE = ("RICE-SEASON DATA (RED ROW). SAME SAMPLING (Oct 2013) as 23 (companion 3); parameters split between the two papers (no duplicates): concentrations of WB-C/TOC from companion 3, "
           "stocks, C pools and biology from this paper. GREEN MANURE / 3rd CROP: mungbean in Sc2 and Sc3 (rule 71). Supplementary: none found. Source file 116_rep.pdf.")
cp = json.load(open(os.path.join(DIG, "jatCSA_Cpools_stock.json")))
F = {"0-15": 0.989, "15-30": 1.0}   # scale correction (0-15 cm panel reads ~1.1% high against 8 printed values)
sc = {"CT": "Sc1", "pCA": "Sc2", "CA": "Sc3"}
st = {}
for dk, depth, rep in (("0-15", "0-20 CM", "0-15 cm (cumulative class 0-20 CM)"),):
    st[dk] = put("stock-SOC", JC, {c: round(cp[dk][s]["SOC"] * F[dk], 2) for c, s in sc.items()}, "SOCs_", red=True,
                 **{"DEPTH": depth, "DEPTH (as reported in paper)": rep, "Obs": 1, "UNIT": "Mg C/ha", "Data source": "Fig. 1 (vector, scale-corrected)",
                    "Method used (from paper)": "Total C by CHNS analyser (Elementar vario EL III) x BD x depth",
                    "Notes/Doubts": "READ FROM VECTOR Fig. 1, x0.989 so that Sc1 = 16.2 Mg/ha (printed). 15-30 cm stocks Sc1/Sc2/Sc3: "
                    + ", ".join(str(cp['15-30'][s]['SOC']) for s in ('Sc1', 'Sc2', 'Sc3')) + ". Sc4 (excl.) " + str(cp['0-15']['Sc4']['SOC']) + ". " + JC_NOTE})
put("stock-SOC", JC, {c: f"=ROUND({B.ref('stock-SOC', 'SOCs_' + c, st['0-15'])}+{cp['15-30'][s]['SOC']},2)" for c, s in sc.items()}, "SOCs_", red=True,
    **{"DEPTH": "0-30 CM", "DEPTH (as reported in paper)": "0-15 + 15-30 cm summed", "Obs": 1, "UNIT": "Mg C/ha", "Data source": "Figs 1-2 (vector) - summed",
       "Method used (from paper)": "Total C x BD x depth", "Notes/Doubts": "DERIVED: 0-15 cm stock (live link) + 15-30 cm stock from Fig. 2. " + JC_NOTE})
POOLS = [("VLC(Cfrac1)", "VLC_", "VL", "very labile C (12 N H2SO4)"), ("LC(Cfrac2)", "LC_", "L", "labile C (18-12 N)"),
         ("LLC(Cfrac3)", "LLC_", "LL", "less labile C (24-18 N)"), ("NLC(Cfrac4)", "NLC_", "NL", "non-labile C (TOC - 24 N)")]
for dk, depth, rep in (("0-15", "0-15 CM", "0-15 cm"), ("15-30", "15-30 CM", "15-30 cm")):
    tr = B_TOC13[depth]
    for sheet, pre, key, lab in POOLS:
        vals = {c: f"=ROUND({cp[dk][s][key]}/{cp[dk][s]['SOC']}*{B.ref('TOC', 'TOC_' + c, tr)},2)" for c, s in sc.items()}
        put(sheet, {**JC, "DEPTH": depth, "DEPTH (as reported in paper)": rep, "Obs": 1}, vals, pre, red=True,
            UNIT=f"g/kg ({lab}; DERIVED from printed stocks)", **{"Data source": f"Fig. {1 if dk == '0-15' else 2} (vector) - DERIVED",
            "Method used (from paper)": "Modified Walkley-Black with 5, 10, 20 ml H2SO4 (Chan et al. 2001; Datta et al. 2015)",
            "Notes/Doubts": (f"DERIVED (rule 53): pool concentration = pool stock / SOC stock (Fig. {1 if dk == '0-15' else 2}, Mg C/ha) x TOC concentration of the same Oct-2013 sampling "
                             "(23 (companion 3) TOC row, live link) - the paper prints only stocks and no BD for Sc2. Stocks Sc1/Sc2/Sc3: "
                             + ", ".join(f"{cp[dk][s][key]}/{cp[dk][s]['SOC']}" for s in ('Sc1', 'Sc2', 'Sc3')) + " (pool/SOC). "
                             + ("Lability index (Datta) 1.79/1.66/2.19, RI1 1.54/1.19/2.53, RI2 0.25/0.29/0.21. " if dk == "0-15" else "LI 1.76/1.76/1.89, RI1 3.07/2.23/2.36, RI2 0.11/0.14/0.13. ")
                             + JC_NOTE)})
BIO = {"0-15 CM": dict(dha=(467, 843, 539), apa=(127, 181, 146), mbc=(441, 1054, 626), mbn=(45, 145, 63), fun=(6.1, 7.4, 6.2), bac=(11.4, 14.9, 12.3), act=(4.4, 7.3, 7.2)),
       "15-30 CM": dict(dha=(202.0, 309.6, 212.8), apa=(98, 120, 144), mbc=(387, 551, 409), mbn=(13, 46, 21), fun=(4.3, 7.0, 2.6), bac=(5.5, 6.3, 5.8), act=(2.1, 1.7, 2.9))}
for depth, v in BIO.items():
    base = {**JC, "DEPTH": depth, "DEPTH (as reported in paper)": depth.replace(" CM", " cm"), "Obs": 1}
    codes = ("CT", "pCA", "CA")
    put("DHA", base, {c: f"=ROUND({x}/24,2)" for c, x in zip(codes, v["dha"])}, "DHA_", red=True, UNIT="ug TPF/g soil/h (printed per 24 h / 24)",
        **{"Data source": "Table 3 - converted", "Method used (from paper)": "TTC reduction to TPF over 24 h (Dick et al. 1996)", "Notes/Doubts": f"CONVERTED: printed {v['dha']} ug TPF/g/24 h. " + JC_NOTE})
    put("ALKP", base, dict(zip(codes, v["apa"])), "ALP_", red=True, UNIT="ug PNP/g soil/h", **{"Data source": "Table 3", "Method used (from paper)": "Dick et al. (1996)", "Notes/Doubts": JC_NOTE})
    put("MBC", base, dict(zip(codes, v["mbc"])), "MBC_", red=True, UNIT="ug C/g soil", **{"Data source": "Table 3", "Method used (from paper)": "Fumigation-extraction (Vance et al. 1987), kEC 0.38", "Notes/Doubts": JC_NOTE})
    put("MBN", base, dict(zip(codes, v["mbn"])), "MBN_", red=True, UNIT="ug N/g soil", **{"Data source": "Table 3", "Method used (from paper)": "Fumigation-extraction (Jenkinson et al. 1988), kEN 0.45", "Notes/Doubts": JC_NOTE})
    put("Fungal count", base, dict(zip(codes, v["fun"])), "FUN_", red=True, UNIT="x10^3 CFU/g soil", **{"Data source": "Table 6", "Method used (from paper)": "Rose bengal agar + streptomycin, 5 d at 30 C", "Notes/Doubts": JC_NOTE})
    put("Soil microbial count", base, {c: f"=ROUND({x}/100,3)" for c, x in zip(codes, v["bac"])}, "SMC_", red=True, UNIT="10^7 cfu/g soil (printed bacteria x10^5 / 100)",
        **{"Data source": "Table 6 - converted", "Method used (from paper)": "Nutrient agar, 3 d at 32 C", "Notes/Doubts": f"BACTERIA. CONVERTED: printed {v['bac']} x10^5 CFU/g. " + JC_NOTE})
    put("Actinomycetes", base, dict(zip(codes, v["act"])), "AM_", red=True, UNIT="10^5 cfu/g soil", **{"Data source": "Table 6", "Method used (from paper)": "Actinomycetes isolation agar + nalidixic acid, 7 d at 28 C", "Notes/Doubts": JC_NOTE})
put("RESP", {**JC, "DEPTH": "0-15 CM", "DEPTH (as reported in paper)": "0-15 cm", "Obs": 1}, dict(CT=0.73, pCA=1.01, CA=0.83), "RESP_", red=True,
    UNIT="mg CO2-C/kg soil/day (printed ug CO2(-C)/g/day)", **{"Data source": "Table 5", "Method used (from paper)": "Linear CO2-C evolution rate, days 10-23 of incubation (alkali trap)",
    "Notes/Doubts": "FLAG: expressed as CO2-C (methods) - sheet unit is CO2. Mineralisable C 0-23 d: 61.4/91.5/70.7 ug C/g; MQ x100 0.07/0.13/0.06; qCO2 0.0061/0.0038/0.0049. " + JC_NOTE})

# =====================================================================================
# 165 (companion)  MEENA et al. 2020
# =====================================================================================
ME_TRT = ("TREATMENTS IN PAPER (IARI long-term organic project 'Nutrient management in rice-wheat cropping system under organic conditions', since kharif 2003, "
          "organic from 2006; strip plot, 3 reps): main strips RWCS (basmati rice-wheat) and RWMCS (rice-wheat-mungbean); rows: Control (no organics), FYM, VC "
          "(each = 60 kg N/ha), FYM + CR, VC + CR (crop residue of the preceding crop 3 t/ha to each crop), FYM + CR + BF, VC + CR + BF (BF = BGA + PSB + "
          "cellulolytic culture in rice; Azotobacter + PSB + cellulolytic in wheat; Rhizobium + PSB in mungbean). FYM -> CT, FYM + CR -> CTR (row a), "
          "FYM + CR + BF -> CTR (row b, BF flag); VC -> CT, VC + CR -> CTR (row a), VC + CR + BF -> CTR (row b); Control EXCLUDED (no organics).")
ME = {"No.": "165 (companion)", "SERIAL NO": "165 (companion)",
      "Authors": "Meena A.L., Pandey R.N., Kumar D., Dotaniya M.L., Sharma V.K., Singh G., Meena B.P., Kumar A. & Bhanu C.", "Year": 2020,
      "Journal": "Communications in Soil Science and Plant Analysis", "Country": "India (Delhi)", "Site/Location": "IARI research farm, New Delhi (long-term organic rice-based project, since 2003)",
      "latitude": 28.4, "longitude": 77.1, "CLIMATE": "ST", "year of data collection/experiment": "2015-16", "DURATION": ">10 Y", "SOIL": "LOAMY", "Rep": 3,
      "CLAY": 25.4, "MIN TEMP": 18, "MAX TEMP": 35.2, "RAIN FALL": 750, "LATT": 28.4, "YEAR OF DATA (duration)": 12, "ph (initial)": 8.45, "soc (initial)": 5.10,
      "Bdi": 1.50, "sand": 52.1, "silt": 22.5,
      "Fertilizer dose & other management": ("ORGANIC: FYM or vermicompost equivalent to 60 kg N/ha to rice and to wheat; CR = preceding-crop residue 3 t/ha to each crop; mungbean on residual "
                                             "fertility (RWMCS), its residue to the next rice. Varieties: Pusa Basmati 1121, HD 2967, Pusa Vishal. Initial soil SCL, BD 1.50, WHC 36.4%, MWD 0.472, "
                                             "pH 8.45, EC 0.79, CEC 14.7, OC 5.10 g/kg, avail. N 163.7 kg/ha, Olsen P 8.42 mg/kg."),
      "Treatment details (from paper)": ME_TRT}
ME_NOTE = ("SAME IARI ORGANIC PROJECT as serial 165 (Davari et al. 2012: identical initial soil, rotations and strip-plot layout) -> filed as 165 (companion); the CR rate (3 t/ha) and "
           "treatment set differ from Davari's 2006-08 RR/RI comparison - check. Tillage not described in this paper; from the same project (Davari 2012): puddled transplanted rice, "
           "disc-ploughed wheat -> conventional (flag). Supplementary: none found. Source file 116_real.pdf.")
SYSM = {"RWMCS": "GREEN MANURE / 3rd CROP: mungbean in BOTH treatments of this row (residue to rice). ", "RWCS": ""}
PAIRS = [("FYM", "FYM+CR", "a", "FYM -> CT ; FYM + CR -> CTR (row a)"), ("FYM", "FYM+CR+BF", "b", "FYM -> CT ; FYM + CR + BF -> CTR (row b, biofertiliser flag)"),
         ("VC", "VC+CR", "a", "VC -> CT ; VC + CR -> CTR (row a)"), ("VC", "VC+CR+BF", "b", "VC -> CT ; VC + CR + BF -> CTR (row b, biofertiliser flag)")]
TRT = ["Control", "FYM", "VC", "FYM+CR", "VC+CR", "FYM+CR+BF", "VC+CR+BF"]
MT = {  # sheet: (prefix, unit, src, method, {sys: values in TRT order}, conv)
    "BD": ("BD_", "Mg/m3", "Table 4", "Core method (Veihmeyer & Hendrickson 1948)", {"RWMCS": [1.58, 1.53, 1.51, 1.48, 1.46, 1.43, 1.40], "RWCS": [1.60, 1.57, 1.53, 1.49, 1.46, 1.44, 1.41]}, None),
    "WHC": ("WHC_", "% (Keen-Raczkowski box)", "Table 4", "Keen & Raczkowski (1921) box", {"RWMCS": [47.62, 52.41, 55.27, 54.51, 56.30, 53.24, 54.74], "RWCS": [44.78, 51.10, 52.22, 54.86, 55.90, 53.61, 55.98]}, None),
    "MWD 1": ("MWD_", "mm (wet sieving)", "Table 4", "Wet sieving, Yoder (1936)", {"RWMCS": [0.52, 0.79, 0.81, 0.83, 0.84, 0.86, 0.88], "RWCS": [0.49, 0.76, 0.78, 0.80, 0.81, 0.83, 0.85]}, None),
    "GMD 1": ("GMD_", "mm", "Table 4", "Wet sieving, Yoder (1936)", {"RWMCS": [1.62, 1.64, 1.67, 1.87, 1.91, 2.07, 2.18], "RWCS": [1.57, 1.59, 1.62, 1.82, 1.86, 2.02, 2.13]}, None),
    "HC": ("HC_", "cm/hr (saturated, constant head)", "Table 4", "Constant head (Klute & Dirksen 1986)", {"RWMCS": [0.21, 0.38, 0.41, 0.50, 0.53, 0.55, 0.57], "RWCS": [0.19, 0.36, 0.39, 0.48, 0.51, 0.53, 0.55]}, None),
    "PH": ("PH_", "pH (1:2.5 soil:water)", "Table 5", "Jackson (1973)", {"RWMCS": [8.29, 8.25, 8.17, 8.22, 8.19, 8.00, 8.03], "RWCS": [8.24, 8.27, 8.26, 8.21, 8.29, 8.26, 8.15]}, None),
    "EC": ("EC_", "dS/m (1:2.5)", "Table 5", "Jackson (1973)", {"RWMCS": [0.470, 0.477, 0.493, 0.517, 0.470, 0.473, 0.463], "RWCS": [0.483, 0.457, 0.447, 0.453, 0.490, 0.453, 0.453]}, None),
    "SOC(active C pool)": ("SOC_", "g/kg", "Table 5", "Walkley & Black (1934) rapid titration", {"RWMCS": [4.11, 5.04, 4.88, 6.37, 5.87, 7.70, 7.10], "RWCS": [3.68, 4.72, 4.42, 6.15, 5.52, 7.26, 6.75]}, None),
    "N": ("N_", "kg/ha (available N, alkaline KMnO4, as printed)", "Table 5", "Subbiah & Asija (1956)", {"RWMCS": [217, 231, 247, 236, 238, 243, 242], "RWCS": [226, 234, 226, 221, 243, 238, 226]}, None),
    "P": ("P_", "kg/ha (Olsen P mg/kg x treatment BD x 15 cm x 0.1)", "Table 5 - converted", "Olsen et al. (1954)", {"RWMCS": [14.7, 16.7, 17.9, 19.2, 20.0, 20.6, 23.2], "RWCS": [12.7, 15.7, 17.1, 18.3, 19.2, 20.2, 22.4]}, "bd"),
    "Cu(ppm)": ("Cu_", "ppm (DTPA)", "Table 6", "DTPA (Lindsay & Norvell 1978)", {"RWMCS": [4.18, 4.00, 4.09, 3.85, 3.96, 4.11, 4.22], "RWCS": [3.91, 3.96, 4.30, 3.99, 4.03, 3.91, 4.30]}, None),
    "Zn(ppm)": ("Zn_", "ppm (DTPA)", "Table 6", "DTPA (Lindsay & Norvell 1978)", {"RWMCS": [1.75, 1.70, 1.69, 1.68, 1.69, 1.81, 1.74], "RWCS": [1.53, 1.84, 1.88, 1.66, 1.69, 1.66, 1.82]}, None),
    "Mn": ("Mn_", "ppm (DTPA)", "Table 6", "DTPA (Lindsay & Norvell 1978)", {"RWMCS": [12.15, 12.08, 12.87, 11.56, 11.93, 11.80, 12.06], "RWCS": [13.42, 14.33, 12.73, 15.84, 12.98, 12.63, 13.24]}, None),
    "Fe(ppm)": ("Fe_", "ppm (DTPA)", "Table 6", "DTPA (Lindsay & Norvell 1978)", {"RWMCS": [31.2, 29.6, 30.3, 27.8, 30.6, 33.5, 32.4], "RWCS": [26.1, 30.0, 34.3, 29.5, 28.9, 28.4, 32.4]}, None),
}
STOCK = {"RWMCS": [17.8, 18.9, 21.4, 23.8, 26.5, 28.8, 32.0], "RWCS": [15.7, 17.2, 20.1, 21.9, 24.9, 27.5, 30.9]}
YLD = {"RWMCS": ([2.92, 4.57, 4.78, 4.95, 4.87, 5.05, 5.25], [6.50, 7.37, 8.20, 9.33, 8.50, 9.20, 8.67]),
       "RWCS": ([2.80, 3.87, 4.08, 4.02, 4.15, 4.12, 4.23], [6.07, 6.10, 7.10, 6.77, 7.50, 7.00, 7.37])}
idx = {t: i for i, t in enumerate(TRT)}
for sysn in ("RWMCS", "RWCS"):
    bd_rows = {}
    for ct, ctr, rowl, mapping in PAIRS:
        base = {**ME, "DEPTH": "0-15 CM", "DEPTH (as reported in paper)": "0-15 cm", "Obs": 2,
                "Treatment mapping (paper's name -> code)": f"{sysn}: {mapping}",
                "Crop/season of sampling": "RICE SEASON - surface soil after rice harvest, after the 12th cropping cycle (2015-16)"}
        rn = (f"ROW {rowl}: {sysn} {ct} (CT) vs {ctr} (CTR). Obs = 2 (T=2 paper treatments under CTR: {ct}+CR and {ct}+CR+BF). "
              + ("FLAG: biofertiliser inoculation confounded with residue. " if rowl == "b" else "") + SYSM[sysn])
        for sheet, (pre, unit, src, meth, data, conv) in MT.items():
            v0, v1 = data[sysn][idx[ct]], data[sysn][idx[ctr]]
            vals = {"CT": v0, "CTR": v1}
            nt = RED_NOTE.replace("(October)", "") + rn + f"Control (excluded): {data[sysn][0]}. " + ME_NOTE
            if conv == "bd":
                vals = {c: f"=ROUND({v}*{B.ref('BD', 'BD_' + c, bd_rows[(ct, ctr)])}*15*0.1,1)" for c, v in vals.items()}
                nt = f"CONVERTED with the same treatment's BD (live link): printed {v0} / {v1} mg/kg. " + nt
            r = put(sheet, base, vals, pre, red=True, UNIT=unit, **{"Data source": src, "Method used (from paper)": meth, "Notes/Doubts": nt})
            if sheet == "BD":
                bd_rows[(ct, ctr)] = r
                put("POROSITY", base, {c: f"=ROUND((1-{B.ref('BD', 'BD_' + c, r)}/2.65)*100,2)" for c in ("CT", "CTR")}, "POROSITY_", red=True, UNIT="% v/v",
                    **{"Data source": "DERIVED from Table 4 BD", "Method used (from paper)": "Porosity = (1 - BD/PD) x 100",
                       "Notes/Doubts": "DERIVED (rule 73): PD not reported -> 2.65 (flag). " + rn + ME_NOTE})
        put("stock-SOC", {k: v for k, v in base.items() if k not in ("DEPTH", "DEPTH (as reported in paper)")},
            {"CT": STOCK[sysn][idx[ct]], "CTR": STOCK[sysn][idx[ctr]]}, "SOCs_", red=True,
            **{"DEPTH": "0-20 CM", "DEPTH (as reported in paper)": "0-15 cm (cumulative class 0-20 CM)", "UNIT": "Mg C/ha", "Data source": "Table 5",
               "Method used (from paper)": "SOC x BD x depth", "Notes/Doubts": RED_NOTE + rn + "Printed carbon stock (0-15 cm). " + ME_NOTE})
        gy, sy = YLD[sysn]
        yb = {k: v for k, v in base.items() if k not in ("DEPTH", "DEPTH (as reported in paper)", "Crop/season of sampling")}
        yb["Obs"] = 9
        B.add("YIELD", {**yb, "RICE YIELD_CT": gy[idx[ct]], "RICE YIELD_CTR": gy[idx[ctr]], "RSTRAW_CT": sy[idx[ct]], "RSTRAW_CTR": sy[idx[ctr]],
                        "year of data collection/experiment": "2009-2015 (mean)", "UNIT": "t/ha (rice grain and straw)",
                        "Crop/season of sampling": "Rice, long-term mean (Table 8: 2009-2015)", "Data source": "Table 7",
                        "Method used (from paper)": "Rice grain and straw yield",
                        "Notes/Doubts": (f"MEAN of 2009-2015 (7 seasons; year-wise values not printed) -> Obs = 7 (Y) + 2 (T) = 9. {rn}Wheat yield not reported. "
                                         f"Control (excl.) grain {gy[0]}, straw {sy[0]}. " + ME_NOTE)})

# =====================================================================================
# Study_Info, LAT_LONG, Treatment_Mapping, EXCLUDED_rows
# =====================================================================================
B.add("Study_Info", {"No.": 169, "SERIAL NO": 169, "Authors": "Singh V.K., Dwivedi B.S., Shukla A.K., Chauhan Y.S. & Yadav R.L.", "Year": 2005, "Journal": "Field Crops Research",
                     "Full reference": "Singh VK et al. (2005) Diversification of rice with pigeonpea in a rice-wheat cropping system on a Typic Ustochrept: effect on soil fertility, yield and nutrient use efficiency. Field Crops Res 92:85-105",
                     "DOI / link": "https://doi.org/10.1016/j.fcr.2004.09.002", "Country": "India (Uttar Pradesh)", "Site/Location": "PDCSR Modipuram, Meerut + farmers' survey (Upper Gangetic Plain)",
                     "Crop rotation": "Rice-wheat vs pigeonpea-wheat", "Treatments in paper": "Cropping system (rice-wheat vs pigeonpea-wheat) x N (0/120) x P (0/26) to wheat",
                     "Parameters extracted": "NONE (excluded)", "Supplementary data?": SUPP,
                     "Notes/Doubts": "EXCLUDED: crop-diversification x fertiliser trial (rice replaced by pigeonpea); no tillage or crop-residue contrast within rice-wheat (rule 34). Source file 114.pdf."})
B.add("Study_Info", {"No.": "23 (companion 3)", "SERIAL NO": "23 (companion 3)", "Authors": JT["Authors"], "Year": 2019, "Journal": "Soil & Tillage Research",
                     "Full reference": "Jat HS et al. (2019) Effects of tillage, crop establishment and diversification on soil organic carbon, aggregation, aggregate associated carbon and productivity in cereal systems of semi-arid Northwest India. Soil Tillage Res 190:128-138",
                     "DOI / link": "https://doi.org/10.1016/j.still.2019.03.005", "Country": "India (Haryana)", "Site/Location": JT["Site/Location"], "latitude": 29.70, "longitude": 76.96,
                     "latitude (as reported)": "29 deg 70'N (as printed)", "longitude (as reported)": "76 deg 96'E (as printed)", "Coordinates source": "Paper (non-standard minutes, read as decimals)",
                     "CLIMATE": "ST", "Experiment established (year)": 2009, "year of data collection/experiment": "2013, 2015 (soil); 2009-10 to 2014-15 (yield)", "Years of data reported": "2 soil samplings; 6 yield years",
                     "DURATION": "4-10 Y", "SOIL": "LOAMY", "Texture as reported": "Loam, reclaimed alkali (Typic Natrustalf)", "MIN TEMP": 2, "MAX TEMP": 42.5, "RAIN FALL": 700,
                     "Crop rotation": "Rice-wheat (Sc1); rice-wheat-mungbean (Sc2, Sc3)", "Residue type & rate (t/ha)": "Sc2 78.5, Sc3 74.5 t/ha over 6 yr", "Treatments in paper": JT_TRT,
                     "Parameters extracted": "WB-C, TOC, macro/micro WSA, WSA, MWD, GMD, macro-C, micro-C, POC (2013, 2015, 2 depths); REY 6 years",
                     "Supplementary data?": SUPP, "Notes/Doubts": "INCLUDED: Sc1 CT, Sc2 pCA, Sc3 CA. Soil rows RED (after rice harvest). " + JT_NOTE})
B.add("Study_Info", {"No.": "23 (companion 4)", "SERIAL NO": "23 (companion 4)", "Authors": JC["Authors"], "Year": 2019, "Journal": "Catena (accepted manuscript; version of record S0341816219301936)",
                     "Full reference": "Jat HS et al. (2019) Climate Smart Agriculture practices improve soil organic carbon pools, biological properties and crop productivity in cereal-based systems of North-West India. Catena",
                     "DOI / link": "https://www.sciencedirect.com/science/article/pii/S0341816219301936", "Country": "India (Haryana)", "Site/Location": JT["Site/Location"], "latitude": 29.70, "longitude": 76.95,
                     "Coordinates source": "Paper", "CLIMATE": "ST", "Experiment established (year)": 2009, "year of data collection/experiment": 2013, "Years of data reported": 1, "DURATION": "4-10 Y",
                     "SOIL": "LOAMY", "Texture as reported": "Loam (Typic Natrustalf), OC 0.45%", "soc (initial)": 4.5, "MIN TEMP": 11.62, "MAX TEMP": 31.68, "RAIN FALL": 670,
                     "Crop rotation": "Rice-wheat (Sc1); rice-wheat-mungbean (Sc2, Sc3)", "Residue type & rate (t/ha)": "Sc2 47.9, Sc3 56.1 t/ha over 4 yr", "Treatments in paper": JC["Treatment details (from paper)"],
                     "Parameters extracted": "SOC stock; VL/L/LL/NL C (derived g/kg); DHA, ALP, MBC, MBN, BSR, fungi, bacteria, actinomycetes (2 depths)",
                     "Supplementary data?": SUPP, "Notes/Doubts": "INCLUDED: Sc1 CT, Sc2 pCA, Sc3 CA. All rows RED. " + JC_NOTE})
B.add("Study_Info", {"No.": "165 (companion)", "SERIAL NO": "165 (companion)", "Authors": ME["Authors"], "Year": 2020, "Journal": ME["Journal"],
                     "Full reference": "Meena AL et al. (2020) Impact of 12-year-long rice based organic farming on soil quality in terms of soil physical properties, available micronutrients and rice yield in a typic Ustochrept soil of India. Commun Soil Sci Plant Anal",
                     "DOI / link": "https://doi.org/10.1080/00103624.2020.1822386", "Country": "India (Delhi)", "Site/Location": ME["Site/Location"], "latitude": 28.4, "longitude": 77.1,
                     "latitude (as reported)": "28.4 N", "longitude (as reported)": "77.1 E", "Coordinates source": "Paper", "CLIMATE": "ST", "Experiment established (year)": 2003,
                     "year of data collection/experiment": "2015-16 (soil); 2009-2015 (rice yield mean)", "DURATION": ">10 Y", "SOIL": "LOAMY", "Texture as reported": "Sandy clay loam",
                     "sand": 52.1, "silt": 22.5, "CLAY": 25.4, "ph (initial)": 8.45, "soc (initial)": 5.10, "Bdi": 1.50, "MIN TEMP": 18, "MAX TEMP": 35.2, "RAIN FALL": 750,
                     "Crop rotation": "Organic basmati rice-wheat and rice-wheat-mungbean", "Rice variety": "Pusa Basmati 1121", "Wheat variety": "HD 2967",
                     "N dose (kg/ha)": "60 (FYM or VC N)", "Residue type & rate (t/ha)": "3 t/ha preceding-crop residue to each crop (CR treatments)", "Treatments in paper": ME_TRT,
                     "Parameters extracted": "BD, porosity (derived), WHC, MWD, GMD, Ks, pH, EC, SOC, C stock, available N, P, DTPA Cu/Zn/Mn/Fe, rice grain and straw yield",
                     "Supplementary data?": SUPP, "Notes/Doubts": "INCLUDED: FYM/VC (CT) vs +CR (CTR), rows a/b (+BF). Soil rows RED (after rice harvest). " + ME_NOTE})
B.add("Study_Info", {"No.": "131 (companion)", "SERIAL NO": "131 (companion)", "Authors": ZH["Authors"], "Year": 2023, "Journal": "Sustainability",
                     "Full reference": "Zhang Y-P et al. (2023) Effects of rotational tillage on soil physicochemical properties and crop yield in a rice-wheat double cropping area. Sustainability 15:474",
                     "DOI / link": "https://doi.org/10.3390/su15010474", "Country": "China (Shandong)", "Site/Location": ZH["Site/Location"], "latitude": 35.27, "longitude": 119.38,
                     "Coordinates source": "Approximate - Taoluo town centre (paper gives none; Donggang district 35.425 N, 119.462 E)", "CLIMATE": "TEMP", "Experiment established (year)": 2017,
                     "year of data collection/experiment": "2018-2020", "Years of data reported": "BD 2018-2020; other soil after 3 yr", "DURATION": "0-3 Y", "Texture as reported": "Paddy soil (texture not stated)",
                     "ph (initial)": 6.8, "soc (initial)": 5.75, "Bdi": 1.423, "AVG T": 12.6, "RAIN FALL": 916, "Crop rotation": "Rice-wheat (double cropping)",
                     "Wheat variety": "Yannong 21", "Rice variety": "Linhan 1", "N dose (kg/ha)": "Wheat 225; rice slow-release 25-10-10 600 kg + compound", "Residue type & rate (t/ha)": "Full straw return (crushed) in all",
                     "Treatments in paper": ZH_TRT, "Parameters extracted": "BD (2018-20, 3 layers), porosity (derived), water-stable macro-aggregates, MWD (wet, dry), SOC, total N, alkali-N, P, K, SOC stock and sequestration (derived), rice/wheat yield and components",
                     "Supplementary data?": SUPP, "Notes/Doubts": "INCLUDED: CN = CA, PR = pCA (RT excluded). " + ZH_NOTE})
for no, au, yr, ctry, site, la, lo, lar, lor, src, cl, note in [
        (169, "Singh V.K. et al.", 2005, "India (Uttar Pradesh)", "PDCSR Modipuram, Meerut", None, None, None, None, "Not entered (study excluded)", None, "EXCLUDED study"),
        ("23 (companion 3)", "Jat H.S. et al.", 2019, "India (Haryana)", "ICAR-CSSRI, Karnal", 29.70, 76.96, "29 deg 70'N", "76 deg 96'E", "Paper", "ST", "Printed minutes > 59 - read as decimals (as old-master 23)"),
        ("23 (companion 4)", "Jat H.S. et al.", 2019, "India (Haryana)", "ICAR-CSSRI, Karnal", 29.70, 76.95, "29 deg 70'N", "76 deg 95'E", "Paper", "ST", None),
        ("165 (companion)", "Meena A.L. et al.", 2020, "India (Delhi)", "IARI, New Delhi", 28.4, 77.1, "28.4 N", "77.1 E", "Paper", "ST", None),
        ("131 (companion)", "Zhang Y.-P. et al.", 2023, "China (Shandong)", "Taoluo Town, Rizhao", 35.27, 119.38, "-", "-", "Approximate (town centre)", "TEMP", "Paper gives no coordinates")]:
    B.add("LAT_LONG", {"No.": no, "SERIAL NO": no, "Authors": au, "Year": yr, "Country": ctry, "Site/Location": site, "latitude (as reported)": lar,
                       "longitude (as reported)": lor, "latitude": la, "longitude": lo, "Coordinates source": src, "CLIMATE": cl, "Notes": note})
TM = [
    (169, "Singh V.K. et al.", 2005, "RW / PW x N x P", "Rice-wheat vs pigeonpea-wheat with 0/120 kg N and 0/26 kg P to wheat", "Puddled TPR / pigeonpea", "Conventional", "No", None, "EXCLUDED", "Crop substitution + fertiliser; no tillage/residue contrast", "High", "EXCLUDED"),
    ("23 (companion 3)", "Jat H.S. et al.", 2019, "Sc1", "Conventional rice-wheat, residues removed", "Puddled TPR", "CT (broadcast)", "No", None, "CT", "Conventional both phases", "High", "INCLUDED"),
    ("23 (companion 3)", "Jat H.S. et al.", 2019, "Sc2", "Partial CA: puddled TPR + ZT wheat + ZT mungbean, rice stubble retained", "Puddled TPR", "ZT (drill)", "Yes (anchored stubble 4.1-12.7)", "4.1-12.7", "pCA", "Puddled rice + ZT wheat with residue (rule 68); mungbean flag", "High", "INCLUDED"),
    ("23 (companion 3)", "Jat H.S. et al.", 2019, "Sc3", "Full CA: ZT DSR + ZT wheat + ZT mungbean, residues retained", "ZT DSR", "ZT", "Yes (surface)", "3.7-10.2 rice", "CA", "Zero till both phases + residue; mungbean flag", "High", "INCLUDED"),
    ("23 (companion 3)", "Jat H.S. et al.", 2019, "Sc4", "CA maize-wheat-mungbean", "-", "ZT", "Yes", None, "EXCLUDED", "Maize-wheat system", "High", "EXCLUDED"),
    ("23 (companion 4)", "Jat H.S. et al.", 2019, "Sc1 / Sc2 / Sc3 / Sc4", "As 23 (companion 3)", "-", "-", "-", None, "CT / pCA / CA / EXCLUDED", "Same trial", "High", "INCLUDED"),
    ("165 (companion)", "Meena A.L. et al.", 2020, "FYM / VC", "Organic manure only (60 kg N/ha)", "Puddled TPR (project)", "Conventional (project)", "No", None, "CT", "Conventional, no residue", "Medium (tillage from Davari 2012)", "INCLUDED"),
    ("165 (companion)", "Meena A.L. et al.", 2020, "FYM + CR / VC + CR", "Manure + 3 t/ha preceding-crop residue", "Puddled TPR (project)", "Conventional (project)", "Yes (incorporated)", 3, "CTR", "Conventional + residue (row a)", "Medium", "INCLUDED"),
    ("165 (companion)", "Meena A.L. et al.", 2020, "FYM + CR + BF / VC + CR + BF", "As above + biofertilisers (BGA, PSB, Azotobacter, cellulolytic culture)", "Puddled TPR (project)", "Conventional (project)", "Yes (incorporated)", 3, "CTR", "Row b, biofertiliser flag (rule 20)", "Medium", "INCLUDED - FLAGGED"),
    ("165 (companion)", "Meena A.L. et al.", 2020, "Control", "No organics", "Puddled TPR", "Conventional", "No", None, "EXCLUDED", "Unfertilised control", "High", "EXCLUDED"),
    ("131 (companion)", "Zhang Y.-P. et al.", 2023, "CN", "Continuous no-till dry direct-seeded rice + no-till wheat, full straw return", "ZT DSR", "ZT", "Yes", "full", "CA", "Zero till both phases + residue", "High", "INCLUDED"),
    ("131 (companion)", "Zhang Y.-P. et al.", 2023, "PR", "Plough + rotary + puddled transplanted rice; no-till wheat; full straw return", "Puddled TPR (plough + rotary)", "ZT", "Yes", "full", "pCA", "Puddled rice + ZT wheat with residue (rule 68)", "High", "INCLUDED"),
    ("131 (companion)", "Zhang Y.-P. et al.", 2023, "RT", "No-till 2017-18, plough 2019 before rice; no-till wheat", "Rotational", "ZT", "Yes", "full", "EXCLUDED", "Alternate / rotational tillage", "High", "EXCLUDED"),
]
th = ["SERIAL NO", "Authors", "Year", "Paper's treatment label (verbatim)", "Full description from paper", "Rice-phase tillage", "Wheat-phase tillage",
      "Residue retained?", "Residue rate (t/ha)", "ASSIGNED CODE", "Rationale", "Confidence", "Status"]
for row in TM:
    d = dict(zip(th, row))
    d["No."] = row[0]
    B.add("Treatment_Mapping", d)
B.add("EXCLUDED_rows", {"Sheet": "(whole study)", "SERIAL NO": 169, "Authors": "Singh V.K. et al.", "Year": 2005,
                        "Reason for exclusion": "Rice vs pigeonpea substitution x N x P to wheat - no tillage or residue contrast. No rows entered.",
                        "Full row (header = value)": "Parameters in paper: wheat yield, N/P uptake and use efficiency, soil OC, NO3-N profile, BD, economics."})
B.add("EXCLUDED_rows", {"Sheet": "(treatments)", "SERIAL NO": "23 (companion 3) / 23 (companion 4)", "Authors": "Jat H.S. et al.", "Year": 2019,
                        "Reason for exclusion": "Sc4 (maize-wheat-mungbean) not entered; its values are in the Notes of each row.", "Full row (header = value)": "-"})
B.add("EXCLUDED_rows", {"Sheet": "(treatments)", "SERIAL NO": "131 (companion)", "Authors": "Zhang Y.-P. et al.", "Year": 2023,
                        "Reason for exclusion": "RT (rotational no-till / plough) not entered; values in Notes.", "Full row (header = value)": "-"})
B.save(OUT)
print("saved", OUT)
