"""Step 1 - load the raw-branch plot-average features of the four dates into one cache.

Reads (raw branch only, as requested):
  02 raw reflectance, 04 continuum-removal parameters, 06 vegetation indices,
  07/08/09 first-third derivatives, 10 red-edge parameters.
Writes cache.pkl with one dict per date.
"""
import sys, pickle, re
import numpy as np, pandas as pd, openpyxl

DATA = sys.argv[1]
OUT = sys.argv[2]
DATES = ["11-02-2026", "24-02-2026", "03-03-2026", "13-03-2026"]

def spectral_sheet(ws):
    rows = list(ws.iter_rows(values_only=True))
    hdr = next(i for i, r in enumerate(rows) if r[0] == "Plot")
    plots = [int(x) for x in rows[hdr][1:49]]
    meta = {"Variety": rows[hdr + 1][1:49], "Stage": rows[hdr + 2][1:49],
            "Class": rows[hdr + 3][1:49], "Nleaf": rows[hdr + 4][1:49]}
    assert rows[hdr + 5][0].startswith("Wavelength")
    wl, vals = [], []
    for r in rows[hdr + 6:]:
        if not isinstance(r[0], (int, float)):
            break
        wl.append(int(r[0]))
        vals.append([np.nan if v is None else float(v) for v in r[1:49]])
    df = pd.DataFrame(np.array(vals).T, index=plots, columns=wl)
    return df, pd.DataFrame(meta, index=plots)

def feature_sheet(ws):
    rows = list(ws.iter_rows(values_only=True))
    hdr = next(i for i, r in enumerate(rows) if r[0] == "Plot")
    names = [c for c in rows[hdr][5:] if c is not None]
    data = rows[hdr + 1: hdr + 49]
    plots = [int(r[0]) for r in data]
    vals = [[np.nan if v is None else float(v) for v in r[5:5 + len(names)]] for r in data]
    return pd.DataFrame(vals, index=plots, columns=names), data

cache = {}
for d in DATES:
    wb = openpyxl.load_workbook(f"{DATA}/WhiteRust_Mustard_PlotAverage_Features_{d}.xlsx", read_only=True)
    R, meta = spectral_sheet(wb["02_Raw_PlotAverage_Reflectance"])
    D1, _ = spectral_sheet(wb["07_Raw_First_Derivative"])
    D2, _ = spectral_sheet(wb["08_Raw_Second_Derivative"])
    D3, _ = spectral_sheet(wb["09_Raw_Third_Derivative"])
    CR, crrows = feature_sheet(wb["04_Raw_Continuum_Removal"])
    VI, virows = feature_sheet(wb["06_Raw_Vegetation_Indices"])
    RE, rerows = feature_sheet(wb["10_Raw_RedEdge_Parameters"])
    # file order of the leaf spectra (measurement sequence) from sheet 01
    info = list(wb["01_Plot_Information"].iter_rows(min_row=5, max_row=52, values_only=True))
    first_file = {}
    for r in info:
        m = re.findall(r"(\d{3,6})\.asd", str(r[5]))
        first_file[int(r[0])] = int(m[0]) if m else np.nan
    meta["FirstSpectrumNo"] = pd.Series(first_file)
    # consistency of metadata between sheets
    for rows_ in (crrows, virows, rerows):
        for r in rows_:
            assert meta.loc[int(r[0]), "Class"] == r[3], ("class mismatch", d, r[0])
    cache[d] = dict(R=R, D1=D1, D2=D2, D3=D3, CR=CR, VI=VI, RE=RE, meta=meta)
    print(d, R.shape, D1.shape, CR.shape, VI.shape, RE.shape, meta["Class"].value_counts().to_dict())

pickle.dump(cache, open(OUT, "wb"))
