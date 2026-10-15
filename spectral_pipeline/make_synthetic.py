"""Synthetic leaf spectra with the structure of the white-rust flowering data
(48 plots, 195 healthy / 965 diseased leaves, 4 dates, ASD detector joins).

FOR TESTING THE PIPELINE ONLY - the numbers it produces are not results.
Usage: python make_synthetic.py out.csv
"""
import sys

import numpy as np
import pandas as pd

rng = np.random.default_rng(7)
wl = np.arange(350, 2501, dtype=float)
G = lambda c, w: np.exp(-0.5 * ((wl - c) / w) ** 2)          # noqa: E731
S = lambda c, w: 1 / (1 + np.exp(-(wl - c) / w))              # noqa: E731

# plot design (leaf spectra per plot as in the real data)
healthy = [18, 18, 18, 15, 18, 18, 18, 18, 18, 9, 9, 18]
diseased = [30, 30, 25, 30, 15, 30, 30, 30, 15, 30, 30, 30, 30, 30, 30, 30, 15, 30,
            25, 15, 30, 30, 30, 25, 25, 30, 30, 30, 30, 30, 25, 15, 30, 30, 30, 15]
dates = ["11-02-2026", "24-02-2026", "03-03-2026", "13-03-2026"]
varieties = ["V1", "V2", "V3", "V4"]


def leaf(dis, sev, plot_fx, d_idx):
    chl = np.clip(rng.normal(1.0, 0.16) * plot_fx[0] * (1 - 0.10 * sev * dis), 0.3, 1.6)
    water = np.clip(rng.normal(1.0, 0.06) * plot_fx[1] * (1 - 0.03 * sev * dis), 0.6, 1.3)
    nir = rng.normal(0.60, 0.035) * plot_fx[2] - 0.012 * sev * dis
    pust = 0.012 * sev * dis * rng.uniform(0.3, 1.0)          # white pustules
    vis = (0.05 + 0.20 * G(550, 38) / chl - 0.06 * G(675, 25) * chl + pust * (wl < 750)
           + 0.02 * (wl < 450) * (1 + dis * 0.03 * sev))
    rep = 712 - 2.5 * sev * dis + rng.normal(0, 2.5)
    edge = S(rep, 13 + 2 * dis * sev)
    R = vis * (1 - edge) + nir * edge
    swir = np.where(wl > 1300, np.exp(-(wl - 1300) / 2600), 1.0)
    R = R * (1 - edge * (1 - swir))
    absorb = (0.025 * G(970, 30) + 0.06 * G(1200, 45) + 0.40 * G(1450, 70)
              + 0.55 * G(1940, 90) + 0.25 * G(2500, 150)) * water
    R = R * np.exp(-absorb * 2.2) + 0.004 * dis * sev * (wl > 1400)
    R *= rng.normal(1.0, 0.05)                                  # leaf brightness
    R += rng.normal(0, 1, len(wl)) * np.where(wl < 400, 0.004, np.where(wl > 2350, 6e-5, 3e-5))
    # detector joins: offset of the SWIR detectors and a date-dependent start-up bump
    R[wl >= 1001] += 0.002 + rng.normal(0, 5e-4)
    bump = [0.006, 0.005, 0.0015, 0.0][d_idx] * (1 + 1.5 * dis)
    R[wl >= 1801] += bump * np.exp(-(wl[wl >= 1801] - 1801) / 12)
    return np.clip(R, 0.01, 0.95)


rows, spectra = [], []
plot = 0
for cls, design in ((0, healthy), (1, diseased)):
    for n_leaves in design:
        plot += 1
        fx = rng.normal(1, [0.10, 0.04, 0.04])
        sev_plot = rng.uniform(0.3, 1.0) if cls else 0.0
        rep = "C" if cls == 0 else ["R1", "R2", "R3"][plot % 3]
        var = varieties[plot % 4]
        for k in range(n_leaves):
            d_idx = k % 4
            sev = np.clip(sev_plot + rng.normal(0, 0.25), 0, 1) if cls else 0.0
            spectra.append(leaf(cls, sev, fx, d_idx))
            rows.append({"Plot": plot, "Rep": rep, "Variety": var, "Date": dates[d_idx],
                         "Leaf": k + 1, "File": f"Synthetic{len(rows):05d}.asd"})
meta = pd.DataFrame(rows)
spec = pd.DataFrame(np.round(np.array(spectra), 6), columns=[str(int(w)) for w in wl])
out = pd.concat([meta, spec], axis=1)
out.to_csv(sys.argv[1] if len(sys.argv) > 1 else "synthetic.csv", index=False)
print(out.shape, out.groupby("Rep").size().to_dict())
