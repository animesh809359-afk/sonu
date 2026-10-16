"""One-line overview of every subset run (for the final summary): leaves, Tier-1 bands, J-M, BA on new plots."""
from __future__ import annotations

import glob
import pickle
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
import sys  # noqa: E402
sys.path.insert(0, str(ROOT))


def L(w, n):
    return pickle.load(open(w / f"{n}.pkl", "rb"))


def ba(R, p, s):
    return float(R["validation"].set_index(["Pipeline", "Scheme"]).loc[(p, s), "BA"])


rows = []
for w in sorted(Path(p) for p in glob.glob(str(ROOT / "work_subsets" / "0*"))):
    if not (w / "compare.pkl").exists():
        continue
    D, A, C = L(w, "data"), L(w, "partA"), L(w, "partC")
    y = D["y"]
    rows.append({"Subset": w.name, "Leaves H/D": f"{(y == 0).sum()}/{(y == 1).sum()}",
                 "Tier-1 bands (FDR)": A["n_sig"],
                 "J-M CART/RF": f"{A['tier3'].set_index('Set').loc[A['cart_name'], 'JM']:.2f}/{A['tier3'].set_index('Set').loc[A['rf_name'], 'JM']:.2f}",
                 "A: QDA-CART V3": ba(A, "QDA on CART features", "V3"), "A: RF clf V3": ba(A, "RF classifier", "V3"),
                 "C: QDA-RF V3": ba(C, "QDA on RF features", "V3"), "C: RF clf V3": ba(C, "RF classifier", "V3"),
                 "C: QDA-RF V4": ba(C, "QDA on RF features", "V4"), "C: RF clf V5": ba(C, "RF classifier", "V5"),
                 "V5 by": D["folds"].get("V5_by", "Date")})
df = pd.DataFrame(rows)
pd.set_option("display.width", 250)
print(df.to_string(index=False, float_format=lambda v: f"{100 * v:.1f}"))
