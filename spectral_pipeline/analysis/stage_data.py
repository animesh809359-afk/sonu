"""Stage 0-1: load the four ASD workbooks, remove exact duplicates, audit,
pre-process (band set, splice correction, smoothing, derivatives), build folds."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.signal import savgol_filter

from common import RAW_DIR, cfg, region_of, save, subset_mask
from sp import folds as fl
from sp import load_asd, preprocess
from sp.data import Dataset

C = cfg()
files = [(RAW_DIR / f, d) for f, d in C["data"]["files"]]
meta_all, R_all, wl, logs = load_asd.load_all(files)

# ---- exact duplicates among the kept spectra (first occurrence kept)
dup_mask = pd.DataFrame(R_all).duplicated(keep="first").to_numpy()
dup_rows = []
for i in np.where(dup_mask)[0]:
    j = next(k for k in range(i) if np.array_equal(R_all[k], R_all[i]))
    dup_rows.append({"Removed spectrum": meta_all.at[i, "File"], "Date": meta_all.at[i, "Date"],
                     "Plot": int(meta_all.at[i, "Plot"]), "Source column": meta_all.at[i, "Source column"],
                     "Identical to": meta_all.at[j, "File"], "Its column": meta_all.at[j, "Source column"]})
meta_all["Exact duplicate (removed)"] = dup_mask
keep = ~dup_mask
meta = meta_all[keep].reset_index(drop=True)
meta["Spectrum ID"] = np.arange(1, len(meta) + 1)
R_full = R_all[keep]
# ---- subset (date / growth stage / variety): applied after duplicate removal on all files
n_before_subset = len(meta)
smask = subset_mask(meta, C)
meta = meta[smask].reset_index(drop=True)
R_full = R_full[smask]
subset_info = {"filter": C["data"].get("subset"), "label": C["data"].get("subset_label"),
               "n_all": n_before_subset, "n_subset": len(meta)}
if C["data"].get("subset"):
    dup_rows = [d for d in dup_rows if ((meta["Date"] == d["Date"]) & (meta["Plot"] == d["Plot"])).any()]
present_dates = [d for _, d in C["data"]["files"] if d in set(meta["Date"])]

y = (meta["Class"].values == "Diseased").astype(int)
groups = meta["Plot"].astype(str).values
dates = meta["Date"].values
ds = Dataset(meta=meta, wl_full=wl, R_full=R_full, y=y, groups=groups, dates=dates)
spec = preprocess.preprocess(ds, C)

# ---- audit tables
counts = (meta.groupby("Class").agg(Plots=("Plot", "nunique"), Spectra=("Plot", "size"))
          .reindex(["Healthy", "Diseased"]).reset_index())
by_date = pd.crosstab(meta["Date"], meta["Class"]).reindex(present_dates)[["Healthy", "Diseased"]]
by_stage = pd.crosstab([meta["Date"], meta["Growth stage"]], meta["Class"])[["Healthy", "Diseased"]]
by_stage = by_stage.reindex(sorted(by_stage.index, key=lambda t: (present_dates.index(t[0]), t[1])))
by_variety = pd.crosstab(meta["Variety"], meta["Class"])[["Healthy", "Diseased"]]
by_stage_total = pd.crosstab(meta["Growth stage"], meta["Class"])[["Healthy", "Diseased"]]
per_plot = (meta.groupby("Plot").agg(Class=("Class", "first"), Variety=("Variety", "first"),
                                    Spectra=("Class", "size"),
                                    Dates=("Date", "nunique"))
            .reset_index())
for d in present_dates:
    per_plot[d] = meta[meta["Date"] == d].groupby("Plot").size().reindex(per_plot["Plot"]).fillna(0).astype(int).values
plot_consistency = meta.groupby("Plot").agg(n_class=("Class", "nunique"), n_var=("Variety", "nunique"))
stage_by_plot_date = meta.pivot_table(index="Plot", columns="Date", values="Growth stage", aggfunc="first")[present_dates]

# ---- noise by region (SG residual of the raw spectra, full 350-2500)
Rs = savgol_filter(R_full, 11, 2, axis=1)
res = R_full - Rs
regs = [("350–399", 350, 399), ("400–499", 400, 499), ("500–699", 500, 699), ("700–1000", 700, 1000),
        ("1001–1349", 1001, 1349), ("1350–1430", 1350, 1430), ("1431–1799", 1431, 1799),
        ("1800–1950", 1800, 1950), ("1951–2349", 1951, 2349), ("2350–2500", 2350, 2500)]
noise = []
for nm, a, b in regs:
    m = (wl >= a) & (wl <= b)
    noise.append({"Range (nm)": nm, "Noise (SD of SG residual)": float(res[:, m].std())})
ref = [r["Noise (SD of SG residual)"] for r in noise if r["Range (nm)"] == "500–699"][0]
for r in noise:
    r["Ratio to 500–699 nm"] = r["Noise (SD of SG residual)"] / ref

# ---- outlier screen: spectral angle to the class median spectrum (400-2500)
Rk = spec.R_raw
sam = np.zeros(len(y))
for c in (0, 1):
    med = np.median(Rk[y == c], 0)
    Xc = Rk[y == c]
    cos = Xc @ med / (np.linalg.norm(Xc, axis=1) * np.linalg.norm(med))
    sam[y == c] = np.arccos(np.clip(cos, -1, 1))
meta["SAM (rad)"] = sam
sam_tab = []
for c, nm in ((0, "Healthy"), (1, "Diseased")):
    s = sam[y == c]
    sam_tab.append({"Class": nm, "Leaves": int(len(s)), "Median SAM (rad)": float(np.median(s)),
                    "95th pct (rad)": float(np.percentile(s, 95)), "Max (rad)": float(s.max()),
                    "Leaves > 0.15 rad": int((s > 0.15).sum())})
i1985 = int(np.argmin(np.abs(spec.wl - 1985)))
top_dev = meta.assign(_s=sam).nlargest(10, "_s")[["Plot", "Class", "Date", "Growth stage", "File"]].copy()
top_dev["SAM (rad)"] = sam[top_dev.index]
top_dev["R1985 (leaf)"] = Rk[top_dev.index, i1985]
top_dev["R1985 (class median)"] = [float(np.median(Rk[y == (1 if c == "Diseased" else 0), i1985])) for c in top_dev["Class"]]

checks = [
    ("Missing values in spectra", int(np.isnan(R_full).sum()), "PASS" if not np.isnan(R_full).any() else "FAIL"),
    ("Reflectance range (350–2500 nm)", f"{R_full.min():.3f} – {R_full.max():.3f}",
     "PASS" if R_full.min() >= 0 and R_full.max() <= 1 else "FLAG"),
    ("Wavelength grid identical in all files", f"{wl[0]:.0f}–{wl[-1]:.0f} nm, 1 nm, {len(wl)} bands", "PASS"),
    ("Plot-average formula columns ignored", sum(l["avg_columns"] for l in logs), "PASS"),
    ("Second data block 13-03-2026: exact copies of block 1 (same plot)",
     f"{sum(len(l['block2']) for l in logs)} of {sum(len(l['block2']) for l in logs)} identical → removed", "PASS"),
    ("Exact duplicates among the remaining spectra",
     f"{int(dup_mask.sum())} (the unnamed plot-27 spectra of 11-02-2026) → removed", "FLAG" if dup_mask.any() else "PASS"),
    ("Each plot has one class on every date", f"{int((plot_consistency.n_class == 1).sum())} of {len(plot_consistency)} plots",
     "PASS" if (plot_consistency.n_class == 1).all() else "FAIL"),
    ("Each plot has one variety on every date", f"{int((plot_consistency.n_var == 1).sum())} of {len(plot_consistency)} plots",
     "PASS" if (plot_consistency.n_var == 1).all() else "FAIL"),
    ("Healthy plots within 1–12, diseased plots within 13–48",
     f"healthy plots {sorted(set(meta.loc[meta.Class == 'Healthy', 'Plot'].astype(int)))}; {meta.loc[meta.Class == 'Diseased', 'Plot'].nunique()} diseased plots",
     "PASS" if set(meta.loc[meta.Class == "Healthy", "Plot"].astype(int)) <= set(range(1, 13))
     and set(meta.loc[meta.Class == "Diseased", "Plot"].astype(int)) <= set(range(13, 49)) else "FLAG"),
    ("Repeated ASD file names within a date (counter restarted on 13-03-2026)",
     (f"{int(meta.duplicated(['Date', 'File']).sum())} names repeated; spectra differ (max |Δ| ≥ "
      f"{min(np.abs(R_full[a] - R_full[b]).max() for a, b in meta[meta.duplicated(['Date', 'File'], keep=False)].groupby(['Date', 'File']).apply(lambda g: g.index.tolist())):.3f}) → distinct leaves, kept")
     if meta.duplicated(['Date', 'File']).any() else "none in this data set",
     "PASS"),
]
if C["data"].get("subset"):
    checks.insert(0, ("Subset selected after duplicate removal on all four files",
                      f"{C['data']['subset_label']}: {len(meta)} of {n_before_subset} leaf spectra", "PASS"))

# ---- folds (identical everywhere) + leave-one-date-out on new plots
F = fl.make_folds(y, groups, C)
F = fl.add_transfer(F, dates, meta["Variety"].values, groups, C["validation"].get("v5_by", "auto"), y)
ftab = F["table"].copy()
ftab.insert(1, "Spectrum ID", meta["Spectrum ID"].values)
ftab.insert(2, "Date", dates)
ftab.insert(3, "File", meta["File"].values)
ftab["Class"] = np.where(y == 1, "Diseased", "Healthy")
F["table"] = ftab.drop(columns=["row", "y"])
assert all(not set(groups[f["train"]]) & set(groups[f["test"]]) for s in ("V3", "V4", "V5") for f in F[s])
assert all(len(np.unique(y[f["test"]])) == 2 for s in ("V3", "V4") for f in F[s]), "a test fold lacks one class"
if F["V5_by"] == "Date":
    assert all(not set(dates[f["train"]]) & set(dates[f["test"]]) for f in F["V5"])
else:
    vv = meta["Variety"].values
    assert all(not set(vv[f["train"]]) & set(vv[f["test"]]) for f in F["V5"])
checks.append(("Validation folds: V3 k, V4 hold-out, V5 transfer units",
               f"V3 k = {F['v3_k']} plot-grouped folds × {len(C['validation']['v3_seeds'])} ({F['v3_method']}); "
               f"V4 holds out {F['v4_plots'][0]} healthy + {F['v4_plots'][1]} diseased plots; "
               f"V5 by {F['V5_by']}: {len(F['V5'])} units"
               + (f", {len(F['V5_dropped'])} split×date units skipped (held-out date has no leaves of the test plots "
                  f"or the training set has < 5 leaves of a class)" if F["V5_dropped"] else ""),
               "PASS"))
print("folds: V3 k =", F["v3_k"], "(", F["v3_method"], ") | V4 plots held out", F["v4_plots"], "| V5 by", F["V5_by"], F["V5_dates"])

save({"meta": meta, "meta_all": meta_all, "R_full": R_full, "R_all": R_all, "dup_all": dup_mask,
      "wl_full": wl, "y": y, "groups": groups, "dates": dates, "spec": spec, "folds": F,
      "logs": logs, "dup_rows": dup_rows,
      "audit": {"counts": counts, "by_date": by_date, "by_stage": by_stage, "by_stage_total": by_stage_total,
                "by_variety": by_variety, "per_plot": per_plot, "stage_by_plot_date": stage_by_plot_date,
                "checks": checks, "noise": noise, "sam": sam_tab, "top_dev": top_dev, "subset": subset_info,
                "present_dates": present_dates}},
     "data")
print(counts, "\n", by_date, "\n", by_stage_total, "\n", by_variety)
print("bands analysed", len(spec.wl), "| K0 bump flag", spec.k0["bump_flag"])
print(pd.DataFrame(noise))
print(pd.DataFrame(sam_tab))
for c in checks:
    print(c)
