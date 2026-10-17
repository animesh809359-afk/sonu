import pandas as pd, numpy as np
def load(path="em48.xlsx"):
    xl = pd.ExcelFile(path)
    recs, wl0 = [], None
    for sh in [s for s in xl.sheet_names if s.startswith("P") and s[1:].isdigit()]:
        df = pd.read_excel(xl, sh)
        wl = df.iloc[:, 0].to_numpy(float)
        wl0 = wl if wl0 is None else wl0
        assert np.allclose(wl, wl0)
        for c in df.columns[1:]:
            v = df[c].to_numpy(float)
            if np.isnan(v).all(): continue
            recs.append(dict(plot=int(sh[1:]), em=str(c), spectrum_id=f"{sh}_{c}", vals=v))
    X = np.array([r["vals"] for r in recs])
    meta = pd.DataFrame([{k: r[k] for k in ("plot", "em", "spectrum_id")} for r in recs])
    meta["class"] = np.where(meta["plot"] <= 12, "healthy", "diseased")
    return meta, wl0, X
