"""Kukal & Aggarwal 2003 STR 72:1-8, Figs 1-2 (600-dpi 1-bit page bitmaps, pdfimages pages 5-6).
Marker centroids found by hole-filling + 17x17 opening (filled square = shallow / normal, diamond = unpuddled / shallow, open triangle = normal).
Fig. 1 x-scale fitted on the unpuddled markers against Table 3 footnote values (exact check); Fig. 2 x-scale from the axis tick marks."""
import json
import numpy as np

# ---- Fig. 1 BD (a = before wheat seedbed cultivation = after rice harvest 1996; b = after cultivation for wheat 1996-97)
F1 = {
    "a": {"layers": ["0-5", "5-10", "10-12", "12-14", "14-16", "16-18", "18-20", "20-22", "22-24"],
          "U": [1060.6, 1226.9, 1360.0, 1294.4, 1294.5, 1294.9, 1261.5, 1228.5, 1326.4],
          "S": [1290.8, 1457.1, 1690.0, 1790.0, 1723.1, 1458.6, 1425.0, 1359.4, 1326.4],
          "N": [1192.5, 1358.5, 1524.0, 1658.7, 2091.3, 2058.9, 1992.0, 1824.2, 1492.7],
          "known_U": [1.44, 1.49, 1.53, 1.51, 1.51, 1.51, 1.50, 1.49, 1.52]},
    "b": {"layers": ["0-5", "5-10", "10-12", "12-14", "14-16", "16-18", "18-20"],
          "U": [460.0, None, 1201.6, 1334.1, None, None, 1299.6],
          "S": [697.0, 988.5, 1368.5, 1401.5, 1368.0, 1401.2, 1467.5],
          "N": [594.6, 988.5, 1436.2, 1470.6, 2111.3, 2078.1, 2009.5],
          "known_U": [1.27, 1.42, 1.49, 1.53, 1.54, 1.55, 1.52]},
}
out = {"fig1": {}, "fig2": {}}
for p, d in F1.items():
    xs = [x for x, k in zip(d["U"], d["known_U"]) if x is not None and not (p == "a" and x == 1326.4)]
    ks = [k for x, k in zip(d["U"], d["known_U"]) if x is not None and not (p == "a" and x == 1326.4)]
    m, c = np.polyfit(xs, ks, 1)
    conv = lambda x: None if x is None else round(m * x + c, 3)
    res = [round(conv(x) - k, 3) for x, k in zip(xs, ks)]
    out["fig1"][p] = {"layers": d["layers"], "shallow": [conv(x) for x in d["S"]], "normal": [conv(x) for x in d["N"]],
                      "unpuddled_table3": d["known_U"], "fit_residuals_on_unpuddled": res,
                      "flags": {"a": "22-24 cm shallow marker merged with unpuddled (1.52)", "b": "5-10 cm all three markers merged (blob centre); 14-16/16-18 unpuddled hidden under shallow"}[p]}
# ---- Fig. 2 SPR (a = before cultivation, rice harvest; b = after wheat seedbed), layers 0-5 ... 25-30
T = {"a": [252.0, 467.0, 682.5, 897.0, 1109.5, 1322.0, 1535.0, 1749.0, 1964.0, 2178.5], "b": [243.5, 460.0, 677.5, 893.0, 1106.5, 1321.0]}
F2 = {"a": {"N": [517.7, 775.0, 1001.5, 1907.1, 2104.4, 1994.9], "S": [576.0, 888.9, 1063.5, 1487.2, 1750.9, 1892.5]},
      "b": {"N": [267.7, 485.9, 678.9, 1626.1, 1874.4, 1993.1], "S": [267.7, 485.9, 678.9, 1437.7, 1672.2, 1924.5]}}
for p, d in F2.items():
    m, c = np.polyfit(T[p], [0.5 * i for i in range(len(T[p]))], 1)
    out["fig2"][p] = {"layers": ["0-5", "5-10", "10-15", "15-20", "20-25", "25-30"],
                      "normal": [round(m * x + c, 2) for x in d["N"]], "shallow": [round(m * x + c, 2) for x in d["S"]],
                      "flags": "b: 0-15 cm shallow and normal markers coincide (one blob)" if p == "b" else ""}
json.dump(out, open(__file__.replace(".py", ".json"), "w"), indent=1)
print(json.dumps(out, indent=1))
