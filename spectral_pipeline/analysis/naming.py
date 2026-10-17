"""Full names instead of codes (V1-V5 validation schemes, K0-K6 feature steps, A1-A4 / C0-C7 parts) for workbook
text, sheet names and figure text. Variety labels V1, V2, V3 of this data set are protected: a cell that is just
'V1' is never expanded, 'variety V1' / 'varieties V1, V2, V3' keep their codes, and validation codes in tables are
expanded only in validation-scheme columns."""
from __future__ import annotations

import re

V5_BY = {"Date": "leave-one-date-out validation on new plots", "Variety": "leave-one-variety-out validation"}
VNAME = {"1": "leaf-level 10-fold cross-validation", "2": "plot-grouped cross-validation",
         "3": "nested plot-grouped cross-validation", "4": "30 % plot hold-out validation", "5": None}
KNAME = {"K0": "smoothing and detector-join correction", "K1": "band reflectance", "K2": "continuum-removal features",
         "K3": "vegetation indices", "K3b": "optimised two-band index", "K4": "derivative and edge features",
         "K4b": "red-edge inflection point", "K5": "CART vs Random Forest on each feature group",
         "K6": "correlation spectra"}
PART = {"A1": "Random Forest band importance", "A2": "Tiers 3 and 4 on the CART and Random Forest bands",
        "A3": "CART vs Random Forest as classifiers and band selectors", "A4": "stability of the selected bands"}
TABNUM = {"Z": "1", "A1": "10", "A2": "11", "A3": "12", "A4": "13", "K0": "14", "K1": "15", "K2": "16", "K3": "17",
          "K3b": "18", "K4": "19", "K4b": "20", "K6": "21", "K5": "22", "C0": "23", "C1": "24", "C2": "25", "C3": "26",
          "C4": "27", "C5": "28", "C6": "29", "C7": "30", "V5": "31", "S": "32"}
SHEETS = {"10_A1_RF_Importance": "10_RF_Band_Importance", "11_A2_RF_Tier3_Tier4": "11_RF_Bands_Tier3_Tier4",
          "12_A3_CART_vs_RF": "12_CART_vs_RF_Validation", "13_A4_Band_Stability": "13_Band_Stability",
          "14_K0_Denoising": "14_Smoothing_Detector_Joins", "15_K1_Band_Reflectance": "15_Band_Reflectance",
          "16_K2_Continuum_Removal": "16_Continuum_Removal", "17_K3_Vegetation_Indices": "17_Vegetation_Indices",
          "18_K3b_Optimised_Index": "18_Optimised_TwoBand_Index", "19_K4_Derivatives": "19_Derivatives_Edge_Features",
          "20_K4b_REIP": "20_RedEdge_Inflection_Point", "21_K6_Correlation": "21_Correlation_Spectra",
          "22_K5_CART_vs_RF": "22_Feature_Groups_CART_RF", "23_C0_Feature_Pool": "23_Combined_Feature_Pool",
          "24_C1_Tier1": "24_Pool_Tier1_Ttest", "25_C2_Tier2": "25_Pool_Tier2_CART_RF", "26_C3_Tier3_JM": "26_Pool_Tier3_JM",
          "27_C4_Tier4_QDA": "27_Pool_Tier4_QDA", "28_C5_Validation": "28_Pool_Validation", "29_C6_Stability": "29_Pool_Stability",
          "30_C7_Comparison": "30_Pool_vs_Reflectance", "31_V5_Transfer": "31_Transfer_New_Date",
          "32_Extra_Strata": "32_Within_Strata_Checks", "34_K_AllBands": "34_Features_AllBands",
          "35_C_AllFeatures": "35_Pool_AllFeatures"}
SCHEME_COLS = ("Scheme", "Units", "Validation")
PROTECT_COLS = ("Variety", "Level", "Held-out variety")


class Namer:
    def __init__(self, v5_by="Date"):
        self.v = dict(VNAME)
        self.v["5"] = V5_BY.get(v5_by, V5_BY["Date"])
        K = KNAME
        allk = f"{K['K1']} + {K['K2']} + {K['K3']} + {K['K4']}"
        # ordered phrase rules (applied before the generic code rules)
        v = self.v
        MET = {"BA": "Balanced accuracy", "SD": "SD", "AUC": "AUC", "κ": "κ", "OA": "Overall accuracy"}
        self.rules = [
            (r"\bV1[–-]V5\b", "the five validation schemes (leaf-level 10-fold, plot-grouped, nested plot-grouped, 30 % plot hold-out, leave-one-date-out)"),
            (r"\bPart A1[–-]A4\b", "the Random Forest steps"),
            (r"\bV([1-5]) = ", ""),
            (r"\bV5 \((leave-one-[^)]*)\)", v["5"]), (r"\bV5, leave-one-(?:date|variety)-out[^)]*", v["5"]),
            (r"\bV3 nested, plot-grouped\b", v["3"]),
            (r"\bV3-RUS\s*·\s*nested \+ random under-sampling", "nested plot-grouped cross-validation with random under-sampling"),
            (r"\bV3 \(nested plot-grouped CV, ", v["3"] + " ("), (r"\bV4 \(independent hold-out plots, ", v["4"] + " ("),
            (r"\bV4 (training|test) plots\b", lambda m: f"{m.group(1)} plots of the 30 % plot hold-out"),
            (r"\bPart A \(raw reflectance\)", "raw reflectance"), (r"\bPart C \(combined pool\)", "combined feature pool"),
            (r"\b[Dd]isease-sensitive features \(Part K\)", lambda m: m.group(0)[:-9].rstrip()),
            (r"\b([Nn])ested-CV\b", lambda m: m.group(1) + "ested cross-validation"),
            # prefixes in front of an already descriptive title are dropped
            (r"\bPart A[1-4]\s*·\s*", ""), (r"\bStep (?:K3b|K4b|K\d)\s*\(extra\)\s*·\s*", "Additional step · "),
            (r"\bStep (?:K3b|K4b|K\d)\s*·\s*", ""), (r"\bPart C′?\d\s*·\s*", ""), (r"(?<![\w-])C′?[0-7]\s*·\s*", ""),
            (r"\bPart A · reflectance four-tier\b", "Raw reflectance · four tiers"),
            (r"\bPart C · combined-pool four-tier\b", "Combined feature pool · four tiers"),
            (r"\bK5 · ", "Feature group · "),
            # feature-step phrases
            (r"\bK1\s*\+\s*K2\s*\+\s*K3\s*\+\s*K4\b", allk), (r"\bK1\s*\+\s*K2[–-]K4\b", allk),
            (r"\bK1[–-]K4 combined\b", "all disease-sensitive features combined"),
            (r"\bK1[–-]K4\b", "the disease-sensitive features (" + allk + ")"),
            (r"\bK2[–-]K4\b", f"{K['K2']} + {K['K3']} + {K['K4']}"), (r"\bK2\s*\+\s*K3\s*\+\s*K4\b", f"{K['K2']} + {K['K3']} + {K['K4']}"),
            (r"\bK0[–-]K[56]\b", "all disease-sensitive feature steps"),
            (r"\bPart K\b", "disease-sensitive feature extraction"),
            (r"\bPart C′", "raw reflectance + other features"),
            (r"\bPart C\b", "combined feature pool"), (r"\bPart A\b", "raw-reflectance four tiers"),
            (r"\bTable (K3b|K4b|K\d|A\d|C′?\d|V5|S|Z|CC)\.(\d+)", lambda m: f"Table {TABNUM.get(m.group(1), m.group(1))}.{m.group(2)}"),
            (r"\bK3b optimised\b", "optimised"), (r"\bK2 best single parameter\b", "best single continuum-removal parameter"),
            (r"\bK3 best single index\b", "best single vegetation index"), (r"\bK4 best edge parameter\b", "best edge parameter"),
            (r"\bK1 smoothed reflectance\b", "smoothed band reflectance"), (r"\bK4 first derivative\b", "first derivative"),
            (r"\bK1 (?:band )?reflectance\b", "band reflectance"), (r"\bK2 continuum removal\b", "continuum removal"),
            (r"\bK3 vegetation ind(ex|ices)\b", lambda m: "vegetation ind" + m.group(1)), (r"\bK3 indices\b", "vegetation indices"),
            (r"\bK4 derivatives \+ edge(?: parameters)?\b", "derivatives + edge parameters"), (r"\bK4 edge parameter\b", "edge parameter"),
            (r"\bK4 first-derivative band\b", "first-derivative band"), (r"\bK4 incl\. guard", "derivatives incl. guard"),
            (r"\bK-selected\b", "selected"),
            (r"\b(K3b|K4b|K\d)\s*[·:—–]\s*", lambda m: K[m.group(1)][0].upper() + K[m.group(1)][1:] + " — "),
            (r"\b(K3b|K4b|K\d)\b", lambda m: K[m.group(1)]),
            (r"\b(A[1-4])\s*[·:]\s*", lambda m: PART[m.group(1)][0].upper() + PART[m.group(1)][1:] + ": "),
            # validation schemes: a code followed by its own description collapses to the full name
            (r"\b(BA|SD|AUC|κ|OA) V([1-5])(?: \([^)]*\))?", lambda m: f"{MET[m.group(1)]}, {v[m.group(2)]}"),
            (r"\bV([1-5])\s*·\s*", ""),
            (r"\bV1 leaf(?:-level)?[- ]10-fold(?: CV)?(?: \(optimistic\))?", v["1"] + " (optimistic)"),
            (r"\bV2 plot-grouped(?: \d+-fold)?(?: CV)?", v["2"]),
            (r"\bV3 nested(?: plot-grouped)?(?: CV)?", v["3"]), (r"\bV4 (?:30 % )?(?:plot )?hold-out(?: plots)?", v["4"]),
            (r"\bV5 (?:new date(?: \+| and) new plots|new variety|transfer)", v["5"]),
            (r"\bnested V3\b", v["3"]), (r"\bleaf-level V1\b", v["1"]),
            (r"\bV3-RUS\b", "nested plot-grouped cross-validation with random under-sampling"),
            (r"\bV([1-5])\b", lambda m: v[m.group(1)]),
            (r"\bCV\b", "cross-validation"),
        ]
        def capwrap(rep):
            def f(m):
                out = rep(m) if callable(rep) else m.expand(rep) if "\\" in rep else rep
                before = m.string[:m.start()]
                if out and out[0].islower() and (before.strip() == "" or re.search(r"(?:^|[.!?]\s|\d\.\s)$", before)):
                    out = out[0].upper() + out[1:]
                return out
            return f
        self.rx = [(re.compile(p), capwrap(r)) for p, r in self.rules]

    def text(self, s):
        if not isinstance(s, str) or not s or s.startswith("="):
            return s
        for old, new in SHEETS.items():
            if old in s:
                s = s.replace(old, new)
        if re.fullmatch(r"\s*V[1-5]\s*", s):            # a bare code is a variety label
            return s
        # protect variety mentions
        prot = {}

        def keep(m):
            k = f"\x00{len(prot)}\x00"
            prot[k] = m.group(0)
            return k
        s2 = re.sub(r"[Vv]ariet(?:y|ies)\s*:?\s*V[1-3](?:(?:\s*,\s*|\s+and\s+|\s*/\s*)V[1-3])*", keep, s)
        s2 = re.sub(r"\bV[1-3]\s*(?:,|and)\s*V[1-3](?:\s*,\s*V[1-3])*", keep, s2)
        for rx, rep in self.rx:
            s2 = rx.sub(rep, s2)
        for k, v in prot.items():
            s2 = s2.replace(k, v)
        if s2[:1].islower() and (s[:1].isupper() or re.match(r"V[1-5]\b|K\d|Part ", s)):
            s2 = s2[0].upper() + s2[1:]
        return s2

    def cell(self, value, column=None):
        if not isinstance(value, str):
            return value
        if column is not None and str(column) in PROTECT_COLS:
            return value
        if column is not None and any(str(column).startswith(c) for c in SCHEME_COLS) and re.fullmatch(r"V[1-5]", value.strip()):
            return self.v[value.strip()[1]]
        return self.text(value)

    @staticmethod
    def sheet(name):
        return SHEETS.get(name, name)
