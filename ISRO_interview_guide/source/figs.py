import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Rectangle, Polygon, Ellipse
import os
OUT = os.path.join(os.path.dirname(__file__), "figs")
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False,
                     "axes.spines.right": False, "savefig.dpi": 200, "savefig.bbox": "tight"})
C = dict(blue="#2563eb", green="#16a34a", orange="#ea580c", red="#dc2626", purple="#7c3aed",
         teal="#0d9488", gray="#6b7280", yellow="#ca8a04", brown="#92400e", navy="#1e3a8a")
FILL = dict(blue="#dbeafe", green="#dcfce7", orange="#ffedd5", red="#fee2e2", purple="#ede9fe",
            teal="#ccfbf1", gray="#f3f4f6", yellow="#fef9c3", brown="#fde68a", navy="#e0e7ff")

def save(name):
    plt.savefig(f"{OUT}/{name}.png", facecolor="white"); plt.close()

def box(ax, x, y, w, h, text, col="blue", fs=9, bold=False):
    ax.add_patch(FancyBboxPatch((x - w/2, y - h/2), w, h, boxstyle="round,pad=0.02,rounding_size=0.03",
                                fc=FILL[col], ec=C[col], lw=1.4))
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, wrap=True,
            fontweight="bold" if bold else "normal", color="#111827")

def arr(ax, x1, y1, x2, y2, col="gray", text=None, fs=8, style="-|>", rad=0.0):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, mutation_scale=12,
                                 color=C[col], lw=1.3, connectionstyle=f"arc3,rad={rad}"))
    if text:
        ax.text((x1+x2)/2, (y1+y2)/2, text, fontsize=fs, ha="center", va="bottom", color=C[col],
                bbox=dict(fc="white", ec="none", pad=0.5))

def canvas(w=10, h=6, xl=(0, 10), yl=(0, 6)):
    fig, ax = plt.subplots(figsize=(w, h)); ax.set_xlim(*xl); ax.set_ylim(*yl); ax.axis("off")
    return fig, ax

# 1 Spectral reflectance with Sentinel-2 bands
def f_reflectance():
    wl = np.linspace(400, 2500, 800)
    def g(c, s, a): return a*np.exp(-((wl-c)/s)**2)
    ax_ = [400, 450, 500, 550, 600, 650, 680, 700, 720, 750, 800, 900, 970, 1050, 1200, 1300, 1400, 1450, 1500, 1650, 1800, 1900, 1950, 2000, 2200, 2400, 2500]
    vy_ = [.04, .04, .05, .11, .07, .045, .035, .09, .25, .44, .47, .48, .45, .48, .44, .40, .25, .17, .22, .30, .24, .10, .07, .09, .16, .07, .05]
    sy_ = [.05, .05, .07, .12, .11, .10, .10, .14, .22, .30, .33, .34, .33, .34, .33, .31, .26, .22, .26, .36, .33, .20, .16, .19, .27, .17, .14]
    veg = np.interp(wl, ax_, vy_); stress = np.interp(wl, ax_, sy_)
    soil = 0.08 + 0.25*(wl-400)/2100 - g(1450, 50, 0.04) - g(1940, 50, 0.06) - g(2200, 40, 0.03)
    residue = 0.12 + 0.28*(wl-400)/2100 - g(2100, 70, 0.1) - g(1450, 50, 0.05) - g(1940, 50, 0.07) + g(1700, 150, 0.05)
    water = 0.06*np.exp(-(wl-450)/150); water[wl > 900] = 0.003
    fig, ax = plt.subplots(figsize=(10, 5))
    bands = [("B2", 490, 65), ("B3", 560, 35), ("B4", 665, 30), ("B5", 705, 15), ("B6", 740, 15), ("B7", 783, 20),
             ("B8", 842, 115), ("B8A", 865, 20), ("B11", 1610, 90), ("B12", 2190, 180)]
    for n, c, w in bands:
        ax.axvspan(c-w/2, c+w/2, color="#e5e7eb", alpha=0.8, zorder=0)
        ax.text(c, 0.62, n, ha="center", fontsize=7, rotation=90, color="#374151")
    ax.plot(wl, veg, color=C["green"], lw=2, label="Healthy crop canopy")
    ax.plot(wl, stress, color=C["yellow"], lw=2, ls="--", label="Stressed / senescent crop")
    ax.plot(wl, soil, color=C["brown"], lw=2, label="Bare soil (dry)")
    ax.plot(wl, residue, color=C["orange"], lw=1.6, ls="-.", label="Crop residue (cellulose/lignin dip ~2100 nm)")
    ax.plot(wl, water, color=C["blue"], lw=2, label="Clear water")
    for x, t in [(480, "Chlorophyll\nabsorption"), (680, "Red\nwell"), (720, "Red edge"), (1450, "Leaf water"), (1940, "Leaf water")]:
        ax.annotate(t, (x, 0.05 if x < 800 else 0.09), fontsize=7, ha="center", color="#4b5563")
    ax.set_xlabel("Wavelength (nm)"); ax.set_ylabel("Reflectance (fraction)"); ax.set_ylim(0, 0.68)
    ax.set_title("Spectral signatures of crop, soil, residue and water, with Sentinel-2 MSI bands (grey)")
    ax.legend(fontsize=8, loc="center right", bbox_to_anchor=(1.0, 0.72)); save("reflectance")

# 2 SIF spectrum and absorption bands
def f_sif():
    wl = np.linspace(640, 800, 600)
    sif = 1.2*np.exp(-((wl-685)/11)**2) + 1.8*np.exp(-((wl-740)/24)**2)
    irr = 1.4 - 0.002*(wl-640)
    irr = irr - 0.9*np.exp(-((wl-760.5)/1.6)**2) - 0.5*np.exp(-((wl-687)/1.2)**2) - 0.3*np.exp(-((wl-656.3)/0.6)**2) \
          - 0.3*np.exp(-((wl-719)/2.5)**2)
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    a1.plot(wl, irr, color=C["orange"], lw=1.6); a1.set_ylabel("Solar irradiance\n(relative)")
    for x, t in [(656.3, "Hα Fraunhofer\n656.3"), (687, "O₂-B\n687"), (719, "H₂O\n719"), (760.5, "O₂-A\n760")]:
        a1.annotate(t, (x, 0.35), ha="center", fontsize=8, color=C["red"])
    a1.set_title("Top: incoming solar spectrum with dark absorption lines used for in-filling retrieval")
    a2.fill_between(wl, sif, color=FILL["red"]); a2.plot(wl, sif, color=C["red"], lw=2)
    a2.annotate("Red peak ~685 nm\n(PSII, re-absorbed in canopy)", (685, 1.25), (650, 1.7), fontsize=8,
                arrowprops=dict(arrowstyle="->", color=C["gray"]))
    a2.annotate("Far-red peak ~740 nm\n(PSI+PSII, escapes canopy)", (740, 1.85), (760, 2.1), fontsize=8,
                arrowprops=dict(arrowstyle="->", color=C["gray"]))
    a2.set_ylabel("SIF (mW m⁻² sr⁻¹ nm⁻¹)"); a2.set_xlabel("Wavelength (nm)"); a2.set_ylim(0, 2.5)
    a2.set_title("Bottom: chlorophyll fluorescence emission spectrum (650–800 nm), typically 1–5 % of reflected radiance")
    save("sif_spectrum")

# 3 Fate of absorbed photons
def f_fate():
    fig, ax = canvas(10, 4.6, (0, 10), (0, 4.6))
    box(ax, 1.4, 2.3, 2.3, 1.2, "Absorbed PAR\n(APAR = fAPAR × PAR)", "yellow", 10, True)
    box(ax, 5, 3.8, 2.8, 0.9, "Photochemistry (ΦP)\nCO₂ fixation → GPP", "green", 9)
    box(ax, 5, 2.3, 2.8, 0.9, "Heat dissipation (ΦN)\nNPQ / xanthophyll cycle", "orange", 9)
    box(ax, 5, 0.8, 2.8, 0.9, "Fluorescence (ΦF)\n~1–2 % re-emitted 650–800 nm", "red", 9)
    for y in (3.8, 2.3, 0.8): arr(ax, 2.6, 2.3, 3.55, y)
    box(ax, 8.4, 2.3, 2.8, 2.6, "ΦP + ΦN + ΦF = 1\n\nSIF = PAR · fAPAR · ΦF · fesc\nGPP = PAR · fAPAR · LUE\n\n⇒ GPP ≈ (LUE/ΦF·fesc) · SIF", "navy", 9)
    arr(ax, 6.45, 0.8, 7.0, 1.6, "red"); arr(ax, 6.45, 3.8, 7.0, 3.1, "green")
    ax.set_title("Fate of light absorbed by chlorophyll: why SIF is a direct proxy for photosynthesis", fontsize=11)
    save("sif_fate")

# 4 FLEX tandem
def f_flex():
    fig, ax = canvas(10, 5, (0, 10), (0, 5))
    ax.add_patch(Ellipse((5, -2.2), 16, 5, fc="#bbf7d0", ec=C["green"]))
    ax.text(5, 0.25, "Vegetated land surface — 150 km swath, 300 m pixels", ha="center", fontsize=9)
    for x, n, col, d in [(3.2, "FLEX\nFLORIS spectrometer\n500–780 nm\n0.3 nm (O₂ bands) / 2 nm", "red", "Earth Explorer 8 (ESA)"),
                         (6.8, "Sentinel-3\nOLCI + SLSTR\nreflectance, LST,\ncloud, aerosol", "blue", "Copernicus")]:
        ax.add_patch(Rectangle((x-0.5, 3.6), 1.0, 0.6, fc=FILL[col], ec=C[col], lw=1.5))
        ax.add_patch(Rectangle((x-1.3, 3.8), 0.75, 0.2, fc="#93c5fd", ec=C["navy"]))
        ax.add_patch(Rectangle((x+0.55, 3.8), 0.75, 0.2, fc="#93c5fd", ec=C["navy"]))
        ax.text(x, 2.6, n, ha="center", fontsize=8.5); ax.text(x, 4.45, d, ha="center", fontsize=8, color=C[col])
        ax.add_patch(Polygon([[x-0.2, 3.6], [x+0.2, 3.6], [x+1.6, 0.6], [x-1.6, 0.6]], fc=FILL[col], ec="none", alpha=0.45))
    arr(ax, 4.0, 3.9, 6.0, 3.9, "gray", "≈ 6–15 s apart\nsame orbit", 8, "<|-|>")
    ax.text(5, 1.7, "Sun-synchronous ~815 km, 10:00 descending node,\n27-day repeat; launched 15 Sep 2026 on Vega-C (VV30) with Sentinel-3C",
            ha="center", fontsize=8.5, bbox=dict(fc="white", ec=C["gray"]))
    ax.set_title("FLEX–Sentinel-3 tandem concept", fontsize=11); save("flex_tandem")

# 5 Ground SIF set-up
def f_sif_ground():
    fig, ax = canvas(10, 5.2, (0, 10), (0, 5.2))
    ax.add_patch(Rectangle((0, 0), 10, 0.6, fc="#fde68a", ec="none"))
    for x in np.arange(0.3, 10, 0.45):
        ax.plot([x, x], [0.6, 1.4], color=C["green"], lw=2); ax.plot([x, x+0.15], [1.2, 1.5], color=C["green"], lw=1.5)
    ax.plot([3, 3], [0.6, 4.4], color="#374151", lw=3)
    ax.plot([3, 4.2], [4.2, 4.2], color="#374151", lw=2)
    ax.add_patch(Rectangle((2.6, 1.8), 0.8, 0.8, fc=FILL["navy"], ec=C["navy"])); ax.text(3, 2.2, "FloX /\nQEPro", ha="center", va="center", fontsize=7)
    ax.add_patch(Polygon([[4.2, 4.2], [3.6, 1.45], [4.8, 1.45]], fc=FILL["red"], ec=C["red"], alpha=0.6))
    ax.annotate("", (4.2, 4.9), (4.2, 4.25), arrowprops=dict(arrowstyle="-|>", color=C["orange"]))
    ax.text(4.35, 4.6, "Upward-looking cosine\ndiffuser: E(λ) irradiance", fontsize=8)
    ax.text(4.9, 2.8, "Downward bare fibre (25° FOV):\nL(λ) canopy radiance", fontsize=8)
    ax.text(7.0, 3.2, "Retrieval: FLD / 3FLD / iFLD /\nSFM / SVD at O₂-A & O₂-B\n\nF = [Ein·Lout − Eout·Lin] /\n       [Ein − Eout]   (FLD)",
            fontsize=8.5, bbox=dict(fc=FILL["gray"], ec=C["gray"]))
    ax.text(0.2, 3.3, "Spectral resolution ≤ 0.3 nm\nSNR > 1000\nTemp-stabilised housing\nAlternate E & L every few s", fontsize=8,
            bbox=dict(fc=FILL["yellow"], ec=C["yellow"]))
    ax.set_title("Ground (tower) measurement of SIF — passive dual-channel spectrometer", fontsize=11); save("sif_ground")

# 6 SAR scattering
def f_sar():
    fig, axs = plt.subplots(1, 3, figsize=(10, 3.6))
    titles = ["Surface scattering\n(bare/smooth soil; VV>HH; ∝ moisture, roughness)",
              "Volume scattering\n(canopy; strong cross-pol VH/HV)", "Double bounce\n(stalk–ground, flooded rice; HH≫VV)"]
    for ax, t in zip(axs, titles):
        ax.set_xlim(0, 4); ax.set_ylim(0, 4); ax.axis("off"); ax.set_title(t, fontsize=8.5)
        ax.add_patch(Rectangle((0, 0), 4, 0.6, fc="#d6b98c" if "Surface" in t else ("#93c5fd" if "Double" in t else "#d6b98c"), ec="none"))
        ax.annotate("", (1.8, 0.65), (0.3, 3.5), arrowprops=dict(arrowstyle="-|>", color=C["red"], lw=1.5))
    a = axs[0]; a.annotate("", (3.7, 3.5), (2.0, 0.65), arrowprops=dict(arrowstyle="-|>", color=C["blue"], lw=1.5))
    a.annotate("", (0.6, 3.0), (1.9, 0.7), arrowprops=dict(arrowstyle="-|>", color=C["blue"], lw=0.8, ls="--"))
    a = axs[1]
    for x in np.linspace(0.4, 3.6, 9):
        a.plot([x, x], [0.6, 2.2], color=C["green"], lw=1.5); a.plot([x-0.2, x+0.2], [1.8, 2.1], color=C["green"]); a.plot([x+0.2, x-0.2], [1.4, 1.7], color=C["green"])
    for dx, dy in [(-1, 1.2), (0.2, 1.6), (1.2, 1.0)]:
        a.annotate("", (1.8+dx*0.8, 1.6+dy), (1.8, 1.6), arrowprops=dict(arrowstyle="-|>", color=C["blue"], lw=1))
    a = axs[2]
    for x in np.linspace(0.6, 3.4, 6): a.plot([x, x], [0.6, 2.6], color=C["green"], lw=2)
    a.annotate("", (2.4, 2.0), (1.8, 0.65), arrowprops=dict(arrowstyle="-|>", color=C["blue"], lw=1.5))
    a.annotate("", (0.6, 3.4), (2.4, 2.0), arrowprops=dict(arrowstyle="-|>", color=C["blue"], lw=1.5))
    fig.suptitle("Radar scattering mechanisms over agricultural surfaces", fontsize=11, y=1.1); save("sar_scatter")

# 7 Backscatter time-series
def f_sar_ts():
    d = np.arange(0, 150, 6)
    rice_vh = -24 + 10/(1+np.exp(-(d-60)/10)) - 3/(1+np.exp(-(d-125)/6)); rice_vh[d < 25] = -26 + np.random.default_rng(1).normal(0, .4, (d < 25).sum())
    wheat_vh = -21 + 7/(1+np.exp(-(d-55)/12)) - 2.5/(1+np.exp(-(d-115)/8))
    wheat_vv = -11 + 1.5*np.sin(d/40) - 2/(1+np.exp(-(d-60)/10))
    fig, ax = plt.subplots(figsize=(10, 4.2))
    ax.plot(d, rice_vh, "o-", color=C["blue"], ms=3, label="Rice VH (flooding dip at transplanting → rise)")
    ax.plot(d, wheat_vh, "s-", color=C["green"], ms=3, label="Wheat VH")
    ax.plot(d, wheat_vv, "^-", color=C["orange"], ms=3, label="Wheat VV (attenuated by vertical stems)")
    ax.axvspan(0, 25, color=FILL["blue"], alpha=0.7); ax.text(1, -27.8, "Puddling /\nflooded field", fontsize=8)
    ax.axvspan(110, 150, color=FILL["yellow"], alpha=0.7); ax.text(112, -12.5, "Maturity /\nharvest", fontsize=8)
    ax.set_xlabel("Days after sowing / transplanting"); ax.set_ylabel("σ⁰ (dB)")
    ax.set_title("Typical C/L-band backscatter temporal signatures used for crop classification"); ax.legend(fontsize=8, loc="lower right")
    save("sar_timeseries")

# 8 NISAR
def f_nisar():
    fig, ax = canvas(10, 5, (0, 10), (0, 5))
    ax.add_patch(Rectangle((0, 0), 10, 1.0, fc="#d6b98c", ec="none"))
    for x in np.linspace(5.4, 9.8, 14): ax.plot([x, x], [1.0, 2.2], color=C["green"], lw=2)
    for x in np.linspace(0.3, 4.6, 14): ax.plot([x, x], [1.0, 2.2], color=C["green"], lw=2)
    ax.annotate("", (2.3, 0.35), (1.2, 4.3), arrowprops=dict(arrowstyle="-|>", color=C["purple"], lw=2.5))
    ax.text(0.2, 4.5, "L-band 24 cm (1.257 GHz, NASA)\npenetrates canopy → soil (top ~5 cm)", fontsize=8.5, color=C["purple"])
    ax.annotate("", (7.6, 1.8), (6.5, 4.3), arrowprops=dict(arrowstyle="-|>", color=C["teal"], lw=2.5))
    ax.text(5.4, 4.5, "S-band 9.4 cm (3.2 GHz, ISRO)\ninteracts with leaves/upper canopy", fontsize=8.5, color=C["teal"])
    ax.text(5, 3.2, "NISAR: 12 m deployable reflector, SweepSAR, 242 km swath, 3–10 m res,\n12-day repeat (6-day with asc+desc), full/quad-pol modes, 747 km SSO,\nlaunched 30 Jul 2025 GSLV-F16 from Sriharikota", ha="center", fontsize=8.5, bbox=dict(fc="white", ec=C["gray"]))
    ax.text(5, 2.45, "Soil moisture products: 100 m L4 (L & S-band), 200 m global (L-band); crop area every 12 days", ha="center", fontsize=8.5)
    ax.set_title("NISAR dual-frequency SAR — penetration and agricultural use", fontsize=11); save("nisar")

# 9 Soil moisture retrieval flow
def f_sm_flow():
    fig, ax = canvas(10, 5.4, (0, 10), (0, 5.4))
    box(ax, 1.4, 4.6, 2.3, 0.8, "NISAR L/S σ⁰\n(HH, HV, VV)", "purple")
    box(ax, 1.4, 3.2, 2.3, 0.8, "Ancillary: NDVI/LAI,\nsoil texture, DEM", "green")
    box(ax, 1.4, 1.8, 2.3, 0.8, "In-situ SM probes\n(cal/val sites)", "orange")
    box(ax, 5, 4.6, 3.1, 0.8, "Radiometric/terrain correction,\nspeckle filter, incidence norm.", "blue")
    box(ax, 5, 3.2, 3.1, 1.0, "Vegetation correction\nWater Cloud Model:\nσ⁰ = σ⁰veg + γ²·σ⁰soil", "teal")
    box(ax, 5, 1.6, 3.1, 1.2, "Soil inversion:\n• Change detection (time series)\n• IEM/Oh/Dubois models\n• ML (RF/ANN) on features", "navy", 8.5)
    box(ax, 8.6, 3.2, 2.3, 1.2, "Soil moisture map\n(m³ m⁻³), 100–200 m\n→ irrigation, drought,\ncrop models", "red")
    arr(ax, 2.55, 4.6, 3.45, 4.6); arr(ax, 5, 4.2, 5, 3.7); arr(ax, 5, 2.7, 5, 2.2); arr(ax, 2.55, 3.2, 3.45, 3.2)
    arr(ax, 6.55, 1.6, 7.45, 3.0); arr(ax, 2.55, 1.8, 3.45, 1.6, "orange", "train/validate")
    ax.set_title("SAR soil-moisture retrieval chain", fontsize=11); save("sm_flow")

# 10 Digital twin vs crop model
def f_dt():
    fig, ax = canvas(10, 5.6, (0, 10), (0, 5.6))
    ax.text(2.2, 5.3, "Crop simulation model (open loop)", ha="center", fontweight="bold")
    box(ax, 2.2, 4.4, 3.2, 0.7, "Inputs: weather, soil, cultivar,\nmanagement (static/at start)", "gray", 8.5)
    box(ax, 2.2, 3.0, 3.2, 0.9, "Process equations\n(DSSAT, APSIM, InfoCrop, WOFOST)", "blue", 8.5)
    box(ax, 2.2, 1.6, 3.2, 0.7, "Output: yield, phenology, water use\n(what-if scenarios)", "green", 8.5)
    arr(ax, 2.2, 4.05, 2.2, 3.45); arr(ax, 2.2, 2.55, 2.2, 1.95)
    ax.text(7.4, 5.3, "Digital twin (closed loop)", ha="center", fontweight="bold")
    box(ax, 7.4, 4.4, 3.4, 0.7, "Physical field: IoT sensors, drones,\nsatellite (SAR, optical, SIF), farmer logs", "orange", 8.5)
    box(ax, 7.4, 3.0, 3.4, 0.9, "Virtual replica: crop model + ML\n+ data assimilation (EnKF/4D-Var)", "purple", 8.5)
    box(ax, 7.4, 1.6, 3.4, 0.7, "Decision engine: irrigation, N, pest\nalerts, insurance trigger", "red", 8.5)
    arr(ax, 7.4, 4.05, 7.4, 3.45, "orange", "real-time data"); arr(ax, 7.4, 2.55, 7.4, 1.95)
    arr(ax, 9.1, 1.6, 9.2, 4.2, "red", None, rad=0.5); ax.text(9.55, 2.9, "actuate /\nadvise", fontsize=8, color=C["red"])
    box(ax, 5, 0.45, 8.5, 0.6, "Twin = model that is continuously updated by observations, bidirectional, persistent through the season", "yellow", 8.5)
    save("digital_twin")

# 11 Energy balance
def f_seb():
    fig, ax = canvas(10, 5, (0, 10), (0, 5))
    ax.add_patch(Rectangle((0, 0), 10, 1.0, fc="#d6b98c", ec="none"))
    for x in np.linspace(0.3, 9.7, 30): ax.plot([x, x], [1.0, 1.9], color=C["green"], lw=2)
    def a(x1, y1, x2, y2, t, c):
        ax.annotate("", (x2, y2), (x1, y1), arrowprops=dict(arrowstyle="-|>", color=C[c], lw=2.5)); ax.text(x1+0.1, (y1+y2)/2, t, fontsize=8.5, color=C[c])
    a(0.8, 4.8, 1.3, 2.0, "Rs↓", "orange"); a(1.9, 2.0, 2.4, 4.4, "αRs↑", "yellow"); a(3.1, 4.8, 3.1, 2.0, "RL↓", "red"); a(3.9, 2.0, 3.9, 4.4, "εσTs⁴↑", "red")
    a(5.6, 2.0, 5.6, 4.4, "H (sensible)", "orange"); a(7.4, 2.0, 7.4, 4.4, "λET (latent)", "blue"); a(8.8, 1.2, 8.8, 0.2, "G", "brown")
    ax.text(5, 0.45, "Rn = (1−α)Rs↓ + RL↓ − RL↑ − (1−ε)RL↓      and      λET = Rn − G − H", ha="center", fontsize=10,
            bbox=dict(fc="white", ec=C["gray"]))
    ax.text(5.9, 3.0, "H = ρ cp dT / rah", fontsize=8.5, color=C["orange"])
    ax.set_title("Surface energy balance: ET computed as the residual", fontsize=11); save("energy_balance")

# 12 Hot/cold pixel triangle
def f_triangle():
    rng = np.random.default_rng(3); n = 1500
    ndvi = rng.uniform(0.05, 0.9, n); wet = rng.uniform(0, 1, n)
    tmax = 325 - 18*ndvi; tmin = 298 + 1*ndvi
    ts = tmin + (tmax-tmin)*(1-wet)**1.3 + rng.normal(0, 0.6, n)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(ndvi, ts, s=4, c=wet, cmap="RdYlBu", alpha=0.8)
    x = np.linspace(0.05, 0.9); ax.plot(x, 325-18*x, color=C["red"], lw=2, label="Dry edge (ET→0)")
    ax.plot(x, 298+1*x, color=C["blue"], lw=2, label="Wet edge (ET→ET max)")
    ax.scatter([0.1], [323.5], s=120, marker="*", color=C["red"], zorder=5); ax.text(0.12, 324, "HOT pixel: dry bare\nfield, λET≈0, H=Rn−G", fontsize=8)
    ax.scatter([0.82], [298.5], s=120, marker="*", color=C["blue"], zorder=5); ax.text(0.55, 300.5, "COLD pixel: well-watered\nfull crop, H≈0 (SEBAL)\nET=1.05 ETr (METRIC)", fontsize=8)
    ax.set_xlabel("NDVI"); ax.set_ylabel("Land surface temperature Ts (K)"); ax.legend(fontsize=8)
    ax.set_title("Ts–NDVI space: anchor pixels for SEBAL/METRIC and triangle methods"); save("ts_ndvi")

# 13 SEBAL/METRIC workflow
def f_sebal():
    fig, ax = canvas(10, 6.4, (0, 10), (0, 6.4))
    steps = [("Landsat 8/9 / MODIS / Sentinel-2+3:\nVNIR → albedo, NDVI, LAI; TIR → Ts", "blue"),
             ("Net radiation Rn = (1−α)Rs↓ + RL↓ − RL↑ − (1−ε)RL↓", "orange"),
             ("Soil heat flux G/Rn = (Ts/α)(0.0038α+0.0074α²)(1−0.98NDVI⁴)", "brown"),
             ("Select hot & cold anchor pixels; dT = a + b·Ts (linear)", "red"),
             ("Iterate H = ρcp dT / rah with Monin–Obukhov stability correction", "purple"),
             ("Instantaneous λET = Rn − G − H  → EF or ETrF", "teal"),
             ("Scale to daily ET24 (EF or ETrF constant) → seasonal ET", "green")]
    for i, (t, c) in enumerate(steps):
        y = 5.9 - i*0.85; box(ax, 3.8, y, 6.8, 0.62, t, c, 8.5)
        if i: arr(ax, 3.8, y+0.54, 3.8, y+0.32)
    box(ax, 8.6, 3.4, 2.4, 2.6, "Weather data needed:\nSEBAL: minimal\n(wind at 200 m blend)\n\nMETRIC: hourly ETr\n(ASCE alfalfa) to\ncalibrate cold pixel\nand scale ETrF", "yellow", 8.2)
    ax.set_title("SEBAL / METRIC processing chain", fontsize=11); save("sebal_flow")

# 14 ALEXI
def f_alexi():
    fig, ax = canvas(10, 5.4, (0, 10), (0, 5.4))
    t = np.linspace(1.2, 8.8, 100); h = 1.4 + 2.6*np.sin((t-1.2)/7.6*np.pi/2)
    ax.plot(t, h, color=C["purple"], lw=2); ax.fill_between(t, 1.2, h, color=FILL["purple"], alpha=0.6)
    ax.text(3.0, 2.0, "Atmospheric boundary layer grows\nas H heats it (slab model)", fontsize=8.5)
    ax.text(1.0, 0.85, "t₁ ≈ 1.5 h after sunrise\nTs(t₁) from GEO", fontsize=8); ax.text(7.6, 0.85, "t₂ ≈ 1.5 h before noon\nTs(t₂) from GEO", fontsize=8)
    ax.plot([1.2, 1.2], [1.2, 4.3], "k:"); ax.plot([8.8, 8.8], [1.2, 4.3], "k:")
    box(ax, 5, 4.6, 6.0, 1.0, "Two-source (TSEB) partitioning: Ts⁴ = fc·Tc⁴ + (1−fc)·Tsoil⁴\nPriestley–Taylor initial canopy transpiration λEc = 1.26·fG·Δ/(Δ+γ)·Rnc", "navy", 8.5)
    ax.text(5, 0.25, "ALEXI uses the time-rate of Ts rise (not absolute Ts) → robust to emissivity/atmospheric errors.  DisALEXI → 30 m with Landsat/MODIS.", ha="center", fontsize=8.5)
    ax.set_title("ALEXI: Atmosphere–Land Exchange Inverse model", fontsize=11); save("alexi")

# 15 Diurnal scaling
def f_diurnal():
    h = np.linspace(6, 18, 200); rn = np.clip(600*np.sin((h-6)/12*np.pi), 0, None)
    le = 0.7*rn*(1+0.06*np.sin((h-12)/6*np.pi/2)**2); g = 0.1*rn; H = rn - le - g
    ef = le/(rn-g+1e-9); etr = 0.85*rn; frac = le/(etr+1e-9)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4))
    a1.plot(h, rn, label="Rn", color=C["orange"]); a1.plot(h, le, label="λET", color=C["blue"]); a1.plot(h, H, label="H", color=C["red"]); a1.plot(h, g, label="G", color=C["brown"])
    a1.axvline(10.5, color=C["gray"], ls="--"); a1.text(10.6, 520, "Landsat/S2\noverpass\n~10:30", fontsize=8)
    a1.set_xlabel("Local time (h)"); a1.set_ylabel("W m⁻²"); a1.legend(fontsize=8); a1.set_title("Diurnal energy fluxes (clear day)", fontsize=10)
    m = (h > 8) & (h < 16.5)
    a2.plot(h[m], ef[m], color=C["teal"], lw=2, label="EF = λET/(Rn−G)"); a2.plot(h[m], frac[m], color=C["purple"], lw=2, label="ETrF = ET/ETr (=AET/ET₀)")
    a2.set_ylim(0.4, 1.2); a2.axvline(10.5, color=C["gray"], ls="--"); a2.legend(fontsize=8); a2.set_xlabel("Local time (h)")
    a2.set_title("Ratios stay nearly constant → self-preservation", fontsize=10)
    fig.suptitle("Instantaneous-to-daily scaling: ET24 = ETrF_inst × ET₀,24   or   ET24 = EF × (Rn24 − G24)/λ", fontsize=10.5)
    save("diurnal_scaling")

# 16 Eddy covariance
def f_ec():
    fig, ax = canvas(10, 5, (0, 10), (0, 5))
    ax.add_patch(Rectangle((0, 0), 10, 0.5, fc="#d6b98c", ec="none"))
    for x in np.linspace(0.2, 9.8, 40): ax.plot([x, x], [0.5, 1.1], color=C["green"], lw=1.5)
    ax.plot([2, 2], [0.5, 3.8], color="#374151", lw=3); ax.plot([2, 2.9], [3.6, 3.6], color="#374151", lw=2)
    ax.add_patch(Circle((3.05, 3.6), 0.18, fc=FILL["blue"], ec=C["blue"])); ax.text(3.3, 3.9, "3-D sonic anemometer\n(u, v, w, Ts) 10–20 Hz", fontsize=8)
    ax.add_patch(Rectangle((2.9, 3.0), 0.4, 0.25, fc=FILL["orange"], ec=C["orange"])); ax.text(3.4, 2.9, "Open-path IRGA (CO₂, H₂O)", fontsize=8)
    for cx, cy, r in [(5, 2.2, 0.4), (6.0, 2.7, 0.3), (7.2, 2.0, 0.5), (4.3, 1.6, 0.3)]:
        ax.add_patch(Circle((cx, cy), r, fc="none", ec=C["purple"], ls="--"))
    ax.text(5.6, 1.35, "turbulent eddies carry w′ and c′", fontsize=8, color=C["purple"])
    ax.add_patch(Ellipse((-0.5+7.5, 0.8), 6, 0.5, fc=FILL["yellow"], ec=C["yellow"], alpha=0.7)); ax.text(7.2, 0.15, "upwind flux footprint (≈100×z)", fontsize=8)
    ax.text(0.2, 4.6, "Fc = ρa·⟨w′c′⟩     LE = λ·ρa·⟨w′q′⟩     H = ρa·cp·⟨w′T′⟩", fontsize=10, bbox=dict(fc="white", ec=C["gray"]))
    ax.text(6.3, 4.2, "Corrections: coordinate rotation,\nWPL density, spectral, despiking,\nu* filtering, gap-filling (MDS),\nenergy-balance closure ~70–90 %", fontsize=8, bbox=dict(fc=FILL["gray"], ec=C["gray"]))
    ax.set_title("Eddy covariance flux tower", fontsize=11); save("eddy")

# 17 ML pipeline
def f_ml():
    fig, ax = canvas(10, 4.2, (0, 10), (0, 4.2))
    items = [("Data\nCCE yields, S1/S2,\nweather, soil", "orange"), ("Features\nVIs, σ⁰, GDD,\nrain, SM, SIF", "yellow"),
             ("Split\nspatial/temporal\nblock CV", "gray"), ("Models\nRF, XGBoost,\nSVR, LSTM, CNN", "blue"),
             ("Evaluate\nRMSE, MAPE, R²,\nbias, SHAP", "purple"), ("Deploy\nGP-level yield\n+ uncertainty", "green")]
    for i, (t, c) in enumerate(items):
        box(ax, 0.85+i*1.66, 2.4, 1.45, 1.5, t, c, 8.2)
        if i: arr(ax, 0.85+(i-1)*1.66+0.73, 2.4, 0.85+i*1.66-0.73, 2.4)
    ax.text(5, 0.8, "Pitfall: random k-fold leaks spatial/temporal autocorrelation → over-optimistic R². Use leave-one-year-out / leave-district-out.",
            ha="center", fontsize=8.5, bbox=dict(fc=FILL["red"], ec=C["red"]))
    ax.set_title("Machine-learning workflow for crop yield estimation", fontsize=11); save("ml_pipeline")

# 18 Planck / fire
def f_planck():
    wl = np.linspace(0.5, 16, 600)*1e-6; h = 6.626e-34; c = 3e8; k = 1.381e-23
    def B(T): return 2*h*c**2/wl**5/(np.exp(h*c/(wl*k*T))-1)/1e6
    fig, ax = plt.subplots(figsize=(10, 4.4))
    for T, col in [(300, C["blue"]), (600, C["orange"]), (1000, C["red"])]:
        ax.semilogy(wl*1e6, B(T), color=col, lw=2, label=f"{T} K" + (" (background soil/crop)" if T == 300 else " (smouldering)" if T == 600 else " (flaming)"))
    ax.axvspan(3.5, 4.1, color=FILL["red"]); ax.text(3.55, 1e-2, "MIR 3.9 µm\nMODIS B21/22,\nVIIRS I4/M13", fontsize=8)
    ax.axvspan(10.5, 12.0, color=FILL["blue"]); ax.text(10.6, 1e-2, "TIR 11 µm\nB31 / I5", fontsize=8)
    ax.set_ylim(1e-3, 1e6); ax.set_xlabel("Wavelength (µm)"); ax.set_ylabel("Spectral radiance (W m⁻² sr⁻¹ µm⁻¹)")
    ax.set_title("Planck curves: a sub-pixel fire raises 4 µm radiance far more than 11 µm radiance → fire detection & FRP"); ax.legend(fontsize=8)
    save("planck_fire")

# 19 NBR
def f_nbr():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4))
    bands = ["B2", "B3", "B4", "B8\nNIR", "B11\nSWIR1", "B12\nSWIR2"]; pre = [0.05, 0.08, 0.06, 0.38, 0.22, 0.12]; post = [0.05, 0.06, 0.07, 0.13, 0.20, 0.21]
    x = np.arange(6); a1.bar(x-0.2, pre, 0.4, color=C["green"], label="Before burning (standing stubble)"); a1.bar(x+0.2, post, 0.4, color="#374151", label="After burning (char/ash)")
    a1.set_xticks(x); a1.set_xticklabels(bands, fontsize=8); a1.set_ylabel("Reflectance"); a1.legend(fontsize=7.5, loc="upper left"); a1.set_ylim(0, 0.5); a1.set_title("Spectral change on burning", fontsize=10)
    cls = [("Enhanced regrowth", -0.25, -0.1, "#4ade80"), ("Unburned", -0.1, 0.1, "#d1d5db"), ("Low severity", 0.1, 0.27, "#fde047"),
           ("Moderate-low", 0.27, 0.44, "#fb923c"), ("Moderate-high", 0.44, 0.66, "#ef4444"), ("High severity", 0.66, 1.3, "#7f1d1d")]
    for i, (n, lo, hi, col) in enumerate(cls):
        a2.barh(i, hi-lo, left=lo, color=col); a2.text(hi+0.02, i, f"{n} ({lo}–{hi})", va="center", fontsize=8)
    a2.set_yticks([]); a2.set_xlim(-0.3, 2.0); a2.set_xlabel("dNBR = NBRpre − NBRpost"); a2.set_title("USGS dNBR severity classes (Key & Benson)", fontsize=10)
    fig.suptitle("NBR = (NIR − SWIR2)/(NIR + SWIR2), Sentinel-2: (B8 − B12)/(B8 + B12)", fontsize=10.5); save("nbr")

# 20 Residue management tree
def f_residue():
    fig, ax = canvas(10, 5.6, (0, 10), (0, 5.6))
    box(ax, 5, 5.1, 3.4, 0.7, "Paddy straw (~20+ Mt surplus in Punjab–Haryana)", "orange", 9, True)
    box(ax, 2.5, 3.9, 3.4, 0.7, "IN-SITU (in the field)", "green", 9, True); box(ax, 7.5, 3.9, 3.4, 0.7, "EX-SITU (removed from field)", "blue", 9, True)
    arr(ax, 4.2, 4.8, 2.9, 4.25); arr(ax, 5.8, 4.8, 7.1, 4.25)
    ins = ["Retention/mulch: Happy Seeder,\nSuper Seeder, Smart Seeder", "Incorporation: MB plough,\nrotavator, mulcher + disc", "PUSA bio-decomposer spray\n(fungal consortium, 20–25 d)", "Composting / vermicompost;\nbiochar (pyrolysis) back to soil"]
    exs = ["Biomass power &\nco-firing in thermal plants", "Compressed biogas (CBG,\nSATAT); biogas plants", "2G bioethanol (Panipat\nIOCL refinery)", "Pellets/briquettes, paper/board,\ncattle feed, mushroom, packaging"]
    for i, t in enumerate(ins): box(ax, 2.5, 3.0-i*0.75, 3.6, 0.62, t, "green", 7.8)
    for i, t in enumerate(exs): box(ax, 7.5, 3.0-i*0.75, 3.6, 0.62, t, "blue", 7.8)
    ax.text(5, 0.1, "Supply-chain: baler/rake → aggregation depot → industry. CRM scheme subsidy 50 % (individual), 80 % (CHC/FPO).", ha="center", fontsize=8.3)
    ax.set_title("Crop residue management options", fontsize=11); save("residue_tree")

# 21 Carbon cycle
def f_ccycle():
    fig, ax = canvas(10, 6, (0, 10), (0, 6))
    box(ax, 5, 5.4, 3.2, 0.7, "Atmosphere CO₂ (~425 ppm)", "gray", 9, True)
    box(ax, 1.7, 3.4, 2.6, 0.9, "Crop biomass\n(NPP = GPP − Ra)", "green", 9)
    box(ax, 5.0, 2.0, 2.6, 0.9, "Residue & roots\n→ litter, POM", "yellow", 9)
    box(ax, 8.3, 3.4, 2.6, 0.9, "Soil organic carbon\n(MAOM, stable)", "brown", 9)
    box(ax, 5.0, 0.5, 3.6, 0.7, "Burning: CO₂, CH₄, CO, N₂O, PM2.5", "red", 8.5)
    arr(ax, 3.6, 5.2, 1.5, 3.9, "green"); ax.text(1.2, 4.7, "Photosynthesis\n(GPP)", fontsize=8, color=C["green"])
    arr(ax, 2.3, 3.9, 4.0, 5.05, "orange"); ax.text(2.9, 4.2, "Ra", fontsize=8, color=C["orange"])
    arr(ax, 2.4, 2.95, 3.7, 2.2); ax.text(2.4, 2.35, "residue\nreturn", fontsize=8, color=C["gray"])
    arr(ax, 6.3, 2.2, 7.6, 2.95, "brown"); ax.text(6.7, 2.2, "humification\n(microbial\nnecromass)", fontsize=8, color=C["brown"])
    arr(ax, 8.3, 3.85, 6.2, 5.05, "red"); ax.text(7.8, 4.6, "Rh (decomposition)", fontsize=8, color=C["red"])
    arr(ax, 5.0, 1.55, 5.0, 0.85, "red")
    arr(ax, 6.8, 0.5, 9.4, 1.0, "red"); ax.text(8.2, 0.35, "to atmosphere", fontsize=8, color=C["red"])
    ax.text(0.1, 0.9, "Management levers:\n↑ inputs (cover crops, residue,\n   manure, biochar, roots)\n↓ losses (zero/min tillage,\n   no burning, AWD rice)", fontsize=8.3, bbox=dict(fc=FILL["green"], ec=C["green"]))
    ax.set_title("Agro-ecosystem carbon cycle", fontsize=11); save("carbon_cycle")

# 22 MRV
def f_mrv():
    fig, ax = canvas(10, 5.4, (0, 10), (0, 5.4))
    cyc = [("1. Project design\n(PDD), baseline,\nadditionality", "blue"), ("2. Validation\nby VVB", "purple"), ("3. Monitoring\nsoil samples +\nRS + models", "green"),
           ("4. Reporting\nmonitoring report,\nuncertainty", "orange"), ("5. Verification\nVVB audit", "purple"), ("6. Issuance\n(VCU/ICC) to\nregistry", "teal"), ("7. Sale/retire\nbuyer offsets", "red")]
    n = len(cyc); R = 2.0
    pts = [(5+R*1.6*np.cos(np.pi/2-2*np.pi*i/n), 2.75+R*np.sin(np.pi/2-2*np.pi*i/n)) for i in range(n)]
    for (x, y), (t, c) in zip(pts, cyc): box(ax, x, y, 1.75, 0.9, t, c, 7.8)
    for i in range(n):
        x1, y1 = pts[i]; x2, y2 = pts[(i+1) % n]; arr(ax, x1+(x2-x1)*0.3, y1+(y2-y1)*0.3, x1+(x2-x1)*0.7, y1+(y2-y1)*0.7, rad=-0.15)
    ax.text(5, 2.75, "Measure-Model-\nRemote-sense-\nVerify (MMRV)\nVM0042 · CCTS", ha="center", va="center", fontsize=9, fontweight="bold", color=C["navy"])
    ax.set_title("Carbon-credit project cycle with MRV", fontsize=11); save("mrv_cycle")

# 23 CA detection
def f_ca():
    d = np.arange(0, 160, 5)
    ndvi_ct = np.where(d < 35, 0.15, 0.15+0.65/(1+np.exp(-(d-70)/10))-0.6/(1+np.exp(-(d-135)/6)))
    ndvi_zt = np.where(d < 15, 0.22, 0.22+0.6/(1+np.exp(-(d-60)/10))-0.55/(1+np.exp(-(d-138)/6)))
    ndti_ct = np.where(d < 30, 0.05, 0.05 - 0.02*np.exp(-(d-30)/40)); ndti_zt = np.where(d < 40, 0.14 - 0.0005*d, 0.12)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4))
    a1.plot(d, ndvi_ct, "o-", ms=3, color=C["orange"], label="Conventional tillage (late sown)"); a1.plot(d, ndvi_zt, "s-", ms=3, color=C["green"], label="Zero-till / Happy Seeder (early)")
    a1.set_xlabel("Days from 1 Nov"); a1.set_ylabel("NDVI"); a1.legend(fontsize=8); a1.set_title("Wheat NDVI: earlier green-up in ZT", fontsize=10)
    a2.bar([0, 1], [ndti_ct[:8].mean(), ndti_zt[:8].mean()], color=[C["orange"], C["green"]])
    a2.set_xticks([0, 1]); a2.set_xticklabels(["Conventional\n(bare soil)", "Zero-till\n(residue mulch)"]); a2.set_ylabel("NDTI = (B11−B12)/(B11+B12)")
    a2.set_title("Early-season tillage index: residue cover", fontsize=10)
    fig.suptitle("Remote-sensing cues to separate conservation-agriculture wheat fields", fontsize=11); save("ca_detect")

# 24 RTM inversion
def f_rtm():
    fig, ax = canvas(10, 5, (0, 10), (0, 5))
    box(ax, 1.5, 4.2, 2.6, 1.1, "Leaf RTM: PROSPECT\nN, Cab, Car, Cw, Cm, Cbrown", "green", 8.5)
    box(ax, 1.5, 2.5, 2.6, 1.1, "Canopy RTM: SAIL / 4SAIL\nLAI, ALA, hot-spot, soil,\nsun-view geometry", "teal", 8.5)
    box(ax, 1.5, 0.8, 2.6, 0.9, "SIF: SCOPE, FluorSAIL\nEnergy+fluorescence", "red", 8.5)
    arr(ax, 1.5, 3.65, 1.5, 3.05, "green", "ρ, τ leaf")
    box(ax, 5.0, 2.5, 2.8, 1.4, "Forward simulations\n→ Look-up table (LUT)\n(10⁴–10⁶ spectra)\n+ noise", "purple", 8.5)
    arr(ax, 2.8, 2.5, 3.6, 2.5)
    box(ax, 8.4, 4.0, 2.8, 1.2, "Inversion:\n• LUT cost-function\n• Hybrid ML (GPR, ANN)\n• Optimisation", "navy", 8.5)
    box(ax, 8.4, 1.6, 2.8, 1.2, "Retrieved: LAI, CCC,\nCab, CWC, fAPAR, fCover\n(+ uncertainty)", "orange", 8.5)
    arr(ax, 6.4, 2.8, 7.0, 3.7); arr(ax, 8.4, 3.4, 8.4, 2.2)
    box(ax, 5.0, 0.6, 2.8, 0.8, "Satellite/UAV/hyperspectral\nreflectance (S2, PRISMA, EnMAP)", "yellow", 8)
    arr(ax, 6.4, 0.6, 7.6, 3.4, "yellow", None, rad=0.3)
    ax.set_title("Radiative transfer model (PROSAIL) inversion for crop biophysical parameters", fontsize=11); save("rtm")

# 25 Precision agriculture cycle
def f_pa():
    fig, ax = canvas(10, 5.2, (0, 10), (0, 5.2))
    steps = [("Data acquisition\nGNSS, yield monitor,\nsoil EC, UAV, satellite", "blue"), ("Mapping & analysis\nGIS, kriging,\nmanagement zones", "purple"),
             ("Decision support\nN/irrigation model,\nprescription map", "orange"), ("Variable-rate\napplication (VRT)\nmap- / sensor-based", "green"), ("Evaluation\nyield map, profit,\nenvironment", "teal")]
    n = 5
    pts = [(5+3.3*np.cos(np.pi/2-2*np.pi*i/n), 2.6+1.85*np.sin(np.pi/2-2*np.pi*i/n)) for i in range(n)]
    for (x, y), (t, c) in zip(pts, steps): box(ax, x, y, 2.3, 0.95, t, c, 8.2)
    for i in range(n):
        x1, y1 = pts[i]; x2, y2 = pts[(i+1) % n]; arr(ax, x1+(x2-x1)*0.32, y1+(y2-y1)*0.32, x1+(x2-x1)*0.68, y1+(y2-y1)*0.68, rad=-0.2)
    ax.text(5, 2.6, "Right input\nright place\nright time\nright amount", ha="center", va="center", fontsize=9.5, fontweight="bold", color=C["navy"])
    ax.set_title("Precision-agriculture cycle", fontsize=11); save("pa_cycle")

# 26 FASAL
def f_fasal():
    fig, ax = canvas(10, 5.4, (0, 10), (0, 5.4))
    box(ax, 5, 4.9, 6, 0.6, "FASAL (MNCFC, DA&FW) — multiple in-season forecasts", "navy", 9.5, True)
    cols = [("Econometric\n(F0, pre-season)\narea/production trends", "gray"), ("Agro-meteorology\nweather-indices,\nregression (IMD/SAUs)", "yellow"), ("Remote sensing\nS1 SAR + S2/AWiFS\narea & condition", "blue"), ("Land observations\nCCEs, crop surveys,\nstate reports", "orange")]
    for i, (t, c) in enumerate(cols): box(ax, 1.4+i*2.4, 3.7, 2.2, 1.0, t, c, 8.2); arr(ax, 1.4+i*2.4, 3.2, 5, 2.6)
    box(ax, 5, 2.2, 9.6, 0.75, "Yield models: semi-physical (Monteith LUE) • crop simulation (WOFOST/InfoCrop/DSSAT) • statistical & ML • ensemble", "purple", 8.3)
    box(ax, 5, 1.0, 8.6, 0.75, "District/State/National production forecasts: F1 (mid-season), F2 (pre-harvest), F3 (harvest)", "green", 8.5)
    arr(ax, 5, 1.8, 5, 1.4)
    ax.text(5, 0.2, "Crops: rice (kharif/rabi), wheat, jute, mustard, cotton, sugarcane, sorghum, pulses; CHAMAN for 7 horticultural crops", ha="center", fontsize=8.2)
    ax.set_title("FASAL: Forecasting Agricultural output using Space, Agro-meteorology and Land observations", fontsize=10.5); save("fasal")

# 27 Semi-physical
def f_semi():
    fig, ax = canvas(10, 4.0, (0, 10), (0, 4.0))
    items = [("PAR\n(0.48·Rs, INSAT)", "yellow"), ("fAPAR\n(from NDVI/LAI)", "green"), ("ε LUE\n(g MJ⁻¹)", "blue"), ("Stress scalars\nTscalar·Wscalar\n(LST, LSWI/ET)", "red"), ("Σ daily GPP/NPP\n→ biomass", "purple"), ("× HI\n→ yield", "orange")]
    for i, (t, c) in enumerate(items):
        box(ax, 0.85+i*1.66, 2.3, 1.45, 1.2, t, c, 8.2)
        if i: arr(ax, 0.85+(i-1)*1.66+0.73, 2.3, 0.85+i*1.66-0.73, 2.3)
    ax.text(5, 0.7, "Yield = HI × Σ (ε × fAPAR × PAR × Ts × Ws)   (Monteith 1972; used in FASAL & YES-TECH)", ha="center", fontsize=9.5, bbox=dict(fc="white", ec=C["gray"]))
    ax.set_title("Semi-physical (light-use-efficiency) yield model", fontsize=11); save("semi_physical")

# 28 YES-TECH
def f_yestech():
    fig, ax = canvas(10, 6, (0, 10), (0, 6))
    box(ax, 5, 5.5, 8.8, 0.6, "YES-TECH (Yield Estimation System based on Technology), PMFBY — from Kharif 2023", "navy", 9.5, True)
    box(ax, 2.0, 4.3, 3.4, 1.2, "Approach 1: Smart sampling of CCEs\nstratify GP by RS crop-vigour\n→ optimum CCE locations\n→ fewer, better-placed CCEs", "orange", 8.2)
    box(ax, 7.6, 4.3, 4.0, 1.2, "Approach 2: Direct yield estimation\nsemi-physical / crop-model / ML / ensemble\ncalibrated with CCE yields", "blue", 8.2)
    box(ax, 5, 2.75, 7.5, 0.8, "Final GP/IU yield = 30 % (min) YES-TECH + 70 % CCE  (MP: 100 % tech for paddy/wheat/soybean)", "purple", 8.5)
    arr(ax, 2.0, 3.7, 3.6, 3.15); arr(ax, 7.6, 3.7, 6.4, 3.15)
    box(ax, 5, 1.6, 7.5, 0.8, "Shortfall = (Threshold yield − Actual yield)/Threshold yield × Sum insured", "red", 8.5)
    arr(ax, 5, 2.35, 5, 2.0)
    box(ax, 5, 0.5, 7.5, 0.8, "Threshold yield = average of best 5 of last 7 years × indemnity level (70/80/90 %)", "green", 8.5)
    save("yestech")

# 29 Ensemble GP level
def f_ensemble():
    fig, ax = canvas(10, 5, (0, 10), (0, 5))
    ms = [("Semi-physical\nLUE", "green"), ("Crop model\n+ assimilation", "teal"), ("ML (RF/XGB)\nS1+S2+weather", "blue"), ("Deep learning\nLSTM/CNN", "purple"), ("Weather-index\nregression", "yellow")]
    for i, (t, c) in enumerate(ms): box(ax, 1.1+i*1.95, 4.0, 1.7, 0.9, t, c, 8.3); arr(ax, 1.1+i*1.95, 3.55, 5, 2.85)
    box(ax, 5, 2.4, 8.4, 0.85, "Ensemble: inverse-RMSE weights / Bayesian model averaging / stacking meta-learner", "navy", 8.5)
    box(ax, 5, 1.1, 5.4, 0.9, "GP-level yield + prediction interval;\nflag GPs with high model disagreement for extra CCEs", "red", 8.5)
    arr(ax, 5, 1.95, 5, 1.55)
    ax.set_title("Insurance-unit (gram panchayat) yield ensemble", fontsize=11); save("ensemble")

# 30 Insurance chart
def f_ins():
    yrs = np.arange(2018, 2025); y = np.array([3.9, 4.2, 3.6, 4.4, 4.1, 4.5, 4.3])
    best5 = np.sort(y)[-5:].mean(); ty = best5*0.8
    fig, ax = plt.subplots(figsize=(9, 3.8))
    ax.bar(yrs, y, color=C["blue"], alpha=0.8, label="Past GP yields (t/ha)")
    ax.axhline(best5, color=C["green"], ls="--", label=f"Avg of best 5 of 7 = {best5:.2f}")
    ax.axhline(ty, color=C["red"], lw=2, label=f"Threshold yield @80 % = {ty:.2f}")
    ax.bar([2025], [2.8], color=C["orange"], label="2025 actual = 2.80 (loss year)")
    ax.text(2021.5, 1.0, f"Shortfall = ({ty:.2f}−2.80)/{ty:.2f} = {(ty-2.8)/ty*100:.1f} % of sum insured", fontsize=9, ha="center", bbox=dict(fc="white", ec=C["gray"]))
    ax.set_ylim(0, 5.3); ax.legend(fontsize=8, loc="upper left", ncol=2); ax.set_ylabel("Yield (t/ha)"); ax.set_title("Area-yield index insurance: threshold yield and claim (worked example)")
    save("insurance")

# 31 Fire bulletin workflow
def f_firewf():
    fig, ax = canvas(10, 4.0, (0, 10), (0, 4.0))
    items = [("VIIRS 375 m (S-NPP,\nNOAA-20/21) +\nMODIS 1 km", "red"), ("Contextual fire\nalgorithm on\nMIR/TIR (ΔT)", "orange"), ("Mask: crop land\n(LULC), remove\nindustry/flare", "yellow"),
             ("Attribute to state,\ndistrict, village;\nFRP (MW)", "purple"), ("Daily bulletin\nCREAMS-IARI /\nNRSC → CAQM", "blue"), ("Season burnt-area\nfrom S2 dNBR\n(ground-truth)", "green")]
    for i, (t, c) in enumerate(items):
        box(ax, 0.85+i*1.66, 2.3, 1.5, 1.3, t, c, 8)
        if i: arr(ax, 0.85+(i-1)*1.66+0.75, 2.3, 0.85+i*1.66-0.75, 2.3)
    ax.text(5, 0.6, "Protocol (ISRO-ICAR standard, 2021): Punjab, Haryana, UP, Delhi, Rajasthan, MP; 15 Sep – 30 Nov (paddy), Apr–May (wheat)", ha="center", fontsize=8.5)
    ax.set_title("Active-fire monitoring and bulletin workflow", fontsize=11); save("fire_workflow")

# 32 Ag Physics organogram
def f_org():
    fig, ax = canvas(10, 4.6, (0, 10), (0, 4.6))
    box(ax, 5, 4.0, 4.6, 0.7, "Division of Agricultural Physics, ICAR-IARI, New Delhi", "navy", 9.5, True)
    units = [("Remote sensing\n& GIS (CREAMS\nlab)", "blue"), ("Agricultural\nmeteorology &\ncrop modelling", "yellow"), ("Soil physics &\nwater mgmt.", "brown"),
             ("Biophysics &\nplant physics\n(hyperspectral)", "green"), ("Nanotech, sensors\n& AI/IoT", "purple")]
    for i, (t, c) in enumerate(units): box(ax, 1.1+i*1.95, 2.4, 1.75, 1.2, t, c, 8.2); arr(ax, 5, 3.65, 1.1+i*1.95, 3.0)
    ax.text(5, 0.8, "Products: fire bulletins • drought/crop health • ZT mapper • PUSA soil-moisture & hyperspectral libraries • agromet advisories (GKMS) • M.Sc./PhD teaching",
            ha="center", fontsize=8.2, bbox=dict(fc=FILL["gray"], ec=C["gray"]))
    save("agphysics")

# 33 Confusion / accuracy
def f_cm():
    cm = np.array([[412, 18, 6, 4], [21, 356, 12, 9], [5, 14, 288, 11], [3, 7, 10, 224]])
    labs = ["Rice", "Cotton", "Maize", "Other"]
    fig, ax = plt.subplots(figsize=(6.5, 4.8)); im = ax.imshow(cm, cmap="Blues")
    for i in range(4):
        for j in range(4): ax.text(j, i, cm[i, j], ha="center", va="center", color="white" if cm[i, j] > 200 else "black")
    ax.set_xticks(range(4)); ax.set_xticklabels(labs); ax.set_yticks(range(4)); ax.set_yticklabels(labs)
    ax.set_xlabel("Predicted (classified)"); ax.set_ylabel("Reference (ground truth)")
    oa = np.trace(cm)/cm.sum(); pe = (cm.sum(0)*cm.sum(1)).sum()/cm.sum()**2; k = (oa-pe)/(1-pe)
    ax.set_title(f"Confusion matrix: OA = {oa*100:.1f} %, Kappa = {k:.2f}"); save("confusion")

# 34 precision VRT
def f_vrt():
    rng = np.random.default_rng(7); x = np.linspace(0, 1, 40); X, Y = np.meshgrid(x, x)
    z = 0.6+0.25*np.sin(3*X)*np.cos(2*Y)+0.025*rng.normal(size=X.shape)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4))
    i1 = a1.imshow(z, cmap="RdYlGn", origin="lower"); a1.set_title("NDVI / GreenSeeker sensor map", fontsize=10); plt.colorbar(i1, ax=a1, fraction=0.046)
    zone = np.digitize(z, [0.5, 0.7]); rate = np.choose(zone, [45, 30, 15])
    i2 = a2.imshow(rate, cmap="Purples", origin="lower"); a2.set_title("Top-dress N prescription (kg N/ha) by zone", fontsize=10); plt.colorbar(i2, ax=a2, fraction=0.046)
    for a in (a1, a2): a.set_xticks([]); a.set_yticks([])
    fig.suptitle("Sensor-based VRT: low-vigour zones receive more N (NDVI-based algorithm, e.g. Raun et al.)", fontsize=10.5); save("vrt")

for f in list(globals().values()):
    if callable(f) and getattr(f, "__name__", "").startswith("f_"): f()
print(sorted(os.listdir(OUT)))

def f_timeline():
    ev = [(1988, "IRS-1A launched;\nCAPE crop forecasting\n(SAC)"), (1996, "IRS-1C/1D WiFS;\nmulti-crop forecasts"), (2003, "Resourcesat-1\nAWiFS/LISS-IV"),
          (2006, "FASAL concept\n(DAC & ISRO)"), (2012, "MNCFC set up;\nRISAT-1 C-SAR"), (2014, "CHAMAN\n(horticulture)"), (2016, "PMFBY launched;\nKISAN pilots (2015–16)"),
          (2021, "ISRO–ICAR fire protocol;\nNePPA; CAQM Act"), (2022, "EOS-04 SAR;\nCCTS law (EC Act)"), (2023, "YES-TECH (Kharif);\nWINDS, CROPIC"), (2025, "NISAR launch\n(30 Jul); BharatFS"), (2026, "IAIRO (Jan); FLEX +\nSentinel-3C (15 Sep)")]
    fig, ax = plt.subplots(figsize=(12, 5.4)); ax.axis("off"); ax.set_xlim(1985, 2028.5); ax.set_ylim(-3.6, 3.6)
    ax.plot([1986, 2027.5], [0, 0], color=C["navy"], lw=2.5)
    for i, (y, t) in enumerate(ev):
        up = 1 if i % 2 == 0 else -1; lvl = [0.5, 1.6][(i//2) % 2]
        ax.plot([y, y], [0, lvl*up], color=C["gray"], lw=1); ax.scatter([y], [0], color=C["orange"], zorder=3, s=40)
        xl = {2021: 2019.4, 2022: 2021.2, 2023: 2023.0, 2025: 2025.0, 2026: 2027.0}.get(y, y)
        ax.plot([y, xl], [lvl*up, lvl*up], color=C["gray"], lw=1)
        ax.text(xl, (lvl+0.05)*up, f"{y}\n{t}" if up > 0 else f"{t}\n{y}", ha="center", va="bottom" if up > 0 else "top", fontsize=7.2,
                bbox=dict(fc=FILL["blue"] if up > 0 else FILL["green"], ec="none", pad=2))
    ax.set_title("Milestones of space technology for Indian agriculture", fontsize=11); save("timeline")

def f_smart():
    rng = np.random.default_rng(11); x = np.linspace(0, 1, 60); X, Y = np.meshgrid(x, x)
    z = 0.55 + 0.2*np.sin(4*X+1)*np.cos(3*Y) + 0.03*rng.normal(size=X.shape)
    st = np.digitize(z, [0.48, 0.62])
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4.2))
    i1 = a1.imshow(z, cmap="RdYlGn", origin="lower"); a1.set_title("Peak-season NDVI over a GP (crop mask)", fontsize=10); plt.colorbar(i1, ax=a1, fraction=0.046)
    from matplotlib.colors import ListedColormap
    a2.imshow(st, cmap=ListedColormap(["#fca5a5", "#fde68a", "#86efac"]), origin="lower")
    for s, col in [(0, C["red"]), (1, C["yellow"]), (2, C["green"])]:
        ys, xs = np.where(st == s); k = rng.choice(len(xs), 4, replace=False)
        a2.scatter(xs[k], ys[k], marker="X", s=90, color="black", edgecolor="white")
    a2.set_title("Vigour strata (low/medium/high) + CCE plots (X)", fontsize=10)
    for a in (a1, a2): a.set_xticks([]); a.set_yticks([])
    fig.suptitle("Smart sampling: RS-based stratification and allocation of crop-cutting experiments", fontsize=10.5); save("smart_sampling")

def f_cce():
    fig, ax = canvas(10, 3.6, (0, 10), (0, 3.6))
    items = [("Random selection\nof survey no. &\nfield (by app)", "blue"), ("Mark plot\n5 m × 5 m\n(or as notified)", "orange"), ("Harvest, thresh,\nweigh fresh grain", "yellow"),
             ("Driage: dry and\nre-weigh (moisture\ncorrection)", "brown"), ("Yield (kg/ha) =\nweight × 10000/25\n× driage factor", "green"), ("Upload: geotag,\nphotos, video\n(CCE-Agri app)", "purple")]
    for i, (t, c) in enumerate(items):
        box(ax, 0.85+i*1.66, 2.0, 1.5, 1.4, t, c, 8)
        if i: arr(ax, 0.85+(i-1)*1.66+0.75, 2.0, 0.85+i*1.66-0.75, 2.0)
    ax.text(5, 0.5, "Errors: non-random plot choice, measurement & driage errors, delays, manipulation → motivation for YES-TECH", ha="center", fontsize=8.5,
            bbox=dict(fc=FILL["red"], ec=C["red"]))
    ax.set_title("Crop-cutting experiment (CCE) procedure", fontsize=11); save("cce")

for f in (f_timeline, f_smart, f_cce): f()

def f_walker():
    fig, axs = plt.subplots(2, 1, figsize=(10, 5.6))
    for ax, title, el in zip(axs, ["Normal / La Niña: strong Walker circulation, rising air over Indo-Pacific → good monsoon",
                                  "El Niño: weak/shifted Walker cell, rising air over central-east Pacific, subsidence over India → weak monsoon"], [False, True]):
        ax.set_xlim(0, 10); ax.set_ylim(0, 4); ax.axis("off"); ax.set_title(title, fontsize=9.5)
        ax.add_patch(Rectangle((0, 0), 10, 1.0, fc="#bfdbfe", ec="none"))
        ax.add_patch(Rectangle((0, 0), 1.3, 1.2, fc="#a3e635", ec="none")); ax.text(0.65, 0.4, "India", ha="center", fontsize=8)
        ax.add_patch(Rectangle((2.2, 0), 1.0, 1.15, fc="#a3e635", ec="none")); ax.text(2.7, 0.4, "Indonesia", ha="center", fontsize=7)
        ax.add_patch(Rectangle((9.2, 0), 0.8, 1.2, fc="#a3e635", ec="none")); ax.text(9.6, 0.4, "Peru", ha="center", fontsize=7)
        warm_x = 6.5 if el else 3.6
        ax.add_patch(Ellipse((warm_x, 0.75), 3.2, 0.4, fc="#fca5a5", ec=C["red"])); ax.text(warm_x, 0.68, "warm pool", ha="center", fontsize=7.5, color=C["red"])
        rise = 6.5 if el else 2.7; sink = 9.3 if not el else 1.0
        ax.annotate("", (rise, 3.2), (rise, 1.3), arrowprops=dict(arrowstyle="-|>", lw=2.2, color=C["red"])); ax.text(rise+0.1, 2.2, "convection\n& rain", fontsize=7.5, color=C["red"])
        ax.annotate("", (sink, 1.3), (sink, 3.2), arrowprops=dict(arrowstyle="-|>", lw=2.2, color=C["blue"])); ax.text(sink+0.1, 2.2, "sinking,\ndry", fontsize=7.5, color=C["blue"])
        ax.annotate("", (sink-0.2 if sink > rise else sink+0.2, 3.4), (rise, 3.4), arrowprops=dict(arrowstyle="-|>", lw=1.5, color=C["gray"]))
        ax.annotate("", (rise, 1.2), (sink-0.2 if sink > rise else sink+0.2, 1.2), arrowprops=dict(arrowstyle="-|>", lw=1.5, color=C["gray"]))
        ax.text(5, 1.25 if not el else 1.25, "trade winds" if not el else "weakened trades / westerly bursts", fontsize=7.5, ha="center", color=C["gray"], va="bottom")
        if el: ax.text(0.2, 3.5, "Niño-3.4 SST anomaly ≥ +0.5 °C (El Niño), ≥ +2.0 °C ('super')", fontsize=8, bbox=dict(fc=FILL["yellow"], ec=C["yellow"]))
    plt.tight_layout(); save("walker")

def f_pheno():
    d = np.arange(0, 181, 4); ndvi = 0.18 + 0.62/(1+np.exp(-(d-55)/9)) - 0.6/(1+np.exp(-(d-140)/8))
    rng = np.random.default_rng(5); obs = ndvi + rng.normal(0, 0.03, d.size); obs[[8, 9, 20, 31]] -= 0.25
    fig, ax = plt.subplots(figsize=(10, 4.2))
    ax.scatter(d, obs, s=14, color=C["gray"], label="Raw NDVI (clouds → dips)"); ax.plot(d, ndvi, color=C["green"], lw=2.2, label="Double-logistic / S-G fit")
    amp = ndvi.max()-ndvi.min(); thr = ndvi.min()+0.2*amp
    sos = d[np.argmax(ndvi > thr)]; eos = d[len(d)-1-np.argmax(ndvi[::-1] > thr)]; pk = d[np.argmax(ndvi)]
    for x, t in [(sos, "SOS"), (pk, "Peak"), (eos, "EOS")]:
        ax.axvline(x, color=C["purple"], ls="--"); ax.text(x+1, 0.86, t, color=C["purple"], fontsize=9)
    ax.axhline(thr, color=C["orange"], ls=":"); ax.text(150, thr+0.01, "20 % amplitude threshold", fontsize=8, color=C["orange"])
    ax.annotate("", (eos, 0.1), (sos, 0.1), arrowprops=dict(arrowstyle="<->")); ax.text((sos+eos)/2, 0.11, "Length of season (LOS)", ha="center", fontsize=8)
    ax.fill_between(d, ndvi.min(), ndvi, where=(d >= sos) & (d <= eos), color=FILL["green"], alpha=0.5); ax.text(pk-20, 0.45, "Seasonal integral\n(Σ NDVI ∝ productivity)", fontsize=8)
    ax.set_ylim(0.05, 0.95); ax.set_xlabel("Days after 1 November"); ax.set_ylabel("NDVI"); ax.legend(fontsize=8, loc="upper left")
    ax.set_title("Phenology metrics from a smoothed NDVI time series (TIMESAT-style)"); save("phenology")

def f_vario():
    h = np.linspace(0, 1000, 200); nug, sill, rng_ = 0.05, 0.45, 600
    g = np.where(h < rng_, nug + (sill-nug)*(1.5*h/rng_ - 0.5*(h/rng_)**3), sill)
    r = np.random.default_rng(2); hx = np.linspace(30, 1000, 22); gy = np.interp(hx, h, g) + r.normal(0, 0.025, hx.size)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.scatter(hx, gy, color=C["blue"], label="Experimental semivariogram"); ax.plot(h, g, color=C["red"], lw=2, label="Spherical model")
    ax.axhline(sill, color=C["gray"], ls=":"); ax.text(20, sill+0.01, "Sill", fontsize=9); ax.axvline(rng_, color=C["gray"], ls=":"); ax.text(rng_+10, 0.1, "Range (600 m)", fontsize=9)
    ax.annotate("Nugget", (0, nug), (80, 0.02), fontsize=9, arrowprops=dict(arrowstyle="->"))
    ax.set_xlabel("Lag distance h (m)"); ax.set_ylabel("γ(h)"); ax.legend(fontsize=8, loc="lower right")
    ax.set_title("Semivariogram for kriging / digital soil mapping (e.g. SOC)"); save("variogram")

def f_biasvar():
    c = np.linspace(1, 10, 100); bias = 3/c; var = 0.04*c**1.8; tot = bias + var + 0.3
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.8))
    a1.plot(c, bias, color=C["blue"], label="Bias²"); a1.plot(c, var, color=C["orange"], label="Variance"); a1.plot(c, tot, color=C["red"], lw=2.2, label="Total test error")
    a1.axvline(c[np.argmin(tot)], ls="--", color=C["gray"]); a1.text(c[np.argmin(tot)]+0.2, 3, "optimum\ncomplexity", fontsize=8)
    a1.set_xlabel("Model complexity (e.g. tree depth)"); a1.set_ylabel("Error"); a1.legend(fontsize=8); a1.set_title("Bias–variance trade-off", fontsize=10)
    yrs = np.arange(2016, 2026); a2.set_xlim(2015.5, 2025.5); a2.set_ylim(0, 3); a2.set_yticks([0.5, 1.5, 2.5]); a2.set_yticklabels(["Fold 3", "Fold 2", "Fold 1"])
    for i, test in enumerate([2025, 2022, 2019]):
        for y in yrs: a2.add_patch(Rectangle((y-0.45, 2.1-i+0.0), 0.9, 0.8, fc=C["red"] if y == test else C["blue"], alpha=0.8))
    a2.set_title("Leave-one-year-out CV (red = test year)", fontsize=10); a2.set_xlabel("Season")
    save("bias_variance")

def f_rf():
    fig, ax = canvas(10, 4.4, (0, 10), (0, 4.4))
    box(ax, 5, 4.0, 4.2, 0.55, "Training data (CCE yield + features)", "orange", 9)
    for i in range(4):
        x = 1.4+i*2.4; box(ax, x, 3.0, 1.9, 0.55, f"Bootstrap sample {i+1}", "yellow", 8); arr(ax, 5, 3.72, x, 3.3)
        ax.plot([x, x-0.5, x+0.5, x], [2.55, 1.9, 1.9, 2.55], color=C["green"], lw=1.4)
        for xx in (x-0.5, x+0.5): ax.plot([xx, xx-0.25, xx+0.25, xx], [1.9, 1.4, 1.4, 1.9], color=C["green"], lw=1.2)
        ax.text(x, 1.05, f"Tree {i+1}\n(random m features\nat each split)", ha="center", fontsize=7.5)
    box(ax, 5, 0.3, 5.6, 0.45, "Prediction = mean (regression) / majority vote (classification); OOB error", "navy", 8.5)
    ax.set_title("Random Forest: bagging + random feature subsets", fontsize=11); save("random_forest")

def f_enkf():
    rng = np.random.default_rng(9); t = np.arange(0, 121); truth = 5.5/(1+np.exp(-(t-55)/10)) * (1 - 1/(1+np.exp(-(t-105)/6)))
    fig, ax = plt.subplots(figsize=(10, 4.2))
    ol = 4.3/(1+np.exp(-(t-62)/10)) * (1 - 1/(1+np.exp(-(t-105)/6)))
    ax.plot(t, truth, color="black", lw=2, label="True LAI (field)"); ax.plot(t, ol, color=C["orange"], lw=2, ls="--", label="Open-loop crop model")
    obs_t = np.array([30, 45, 60, 75, 90]); obs = np.interp(obs_t, t, truth) + rng.normal(0, 0.25, obs_t.size)
    ens = []; state = ol.copy()
    for k in range(20):
        m = ol + rng.normal(0, 0.35, t.size).cumsum()*0.02
        ens.append(m)
    da = ol.copy()
    for ot, ov in zip(obs_t, obs):
        da[ot:] += (ov - da[ot])*0.75*np.exp(-(t[ot:]-ot)/40)
    for m in ens: ax.plot(t, m + (da-ol), color=C["blue"], alpha=0.12)
    ax.plot(t, da, color=C["blue"], lw=2.2, label="Assimilated (EnKF analysis mean)")
    ax.errorbar(obs_t, obs, yerr=0.3, fmt="o", color=C["green"], ms=7, label="Sentinel-2 LAI observations ± σ")
    ax.set_xlabel("Days after sowing"); ax.set_ylabel("LAI (m² m⁻²)"); ax.legend(fontsize=8, loc="upper left")
    ax.set_title("Data assimilation: observations pull the model trajectory toward reality (digital-twin engine)"); save("enkf")

def f_cropmodel():
    fig, ax = canvas(10, 5, (0, 10), (0, 5))
    box(ax, 1.3, 4.3, 2.2, 0.8, "Weather (daily)\nRs, Tmax, Tmin, rain", "yellow", 8.3); box(ax, 1.3, 3.0, 2.2, 0.8, "Soil\ntexture, water, N", "brown", 8.3)
    box(ax, 1.3, 1.7, 2.2, 0.8, "Genotype\ncoefficients", "green", 8.3); box(ax, 1.3, 0.5, 2.2, 0.8, "Management\nsowing, irrigation, N", "orange", 8.3)
    box(ax, 4.8, 4.3, 2.6, 0.75, "Phenology (GDD,\nphotoperiod)", "purple", 8.3); box(ax, 4.8, 3.1, 2.6, 0.75, "Light interception\nfAPAR = 1−e^(−k·LAI)", "teal", 8.3)
    box(ax, 4.8, 1.9, 2.6, 0.75, "Biomass = RUE × IPAR\n× stress factors", "blue", 8.3); box(ax, 4.8, 0.7, 2.6, 0.75, "Water & N balance\n→ stress (0–1)", "red", 8.3)
    box(ax, 8.4, 2.5, 2.4, 1.6, "Partitioning →\nLAI, stem, root,\ngrain\n\nYield = HI × biomass", "navy", 8.5)
    for y in (4.3, 3.0, 1.7, 0.5): arr(ax, 2.4, y, 3.5, min(max(y, 0.7), 4.3))
    arr(ax, 4.8, 3.92, 4.8, 3.48); arr(ax, 4.8, 2.72, 4.8, 2.28); arr(ax, 4.8, 1.08, 4.8, 1.52); arr(ax, 6.1, 1.9, 7.2, 2.4); arr(ax, 7.2, 3.0, 6.1, 3.1, "green", "LAI feedback")
    ax.set_title("Generic structure of a crop simulation model (DSSAT / InfoCrop / WOFOST)", fontsize=11); save("crop_model")

for f in (f_walker, f_pheno, f_vario, f_biasvar, f_rf, f_enkf, f_cropmodel): f()


# ---------- generic vertical flowcharts ----------
def flow(name, title, steps, side=None, h=None, w=7.0, inv=()):
    """steps: list of (text, colour, kind) kind in {'box','dec','io','term'}; decisions get a 'no' side note."""
    import textwrap
    steps = [("\n".join(textwrap.wrap(t, 34 if k == "dec" else 70)), c, k) for t, c, k in steps]
    n = len(steps); H = h or (1.0*n + 0.8)
    fig, ax = canvas(10, H*0.62, (0, 10), (0, H)); ax.set_title(title, fontsize=11)
    ys = [H - 0.7 - i*1.0 for i in range(n)]
    for i, ((t, c, k), y) in enumerate(zip(steps, ys)):
        x = 4.2
        if k == "dec":
            ax.add_patch(Polygon([[x-3.0, y], [x, y+0.46], [x+3.0, y], [x, y-0.46]], fc=FILL[c], ec=C[c], lw=1.4))
            ax.text(x, y, t, ha="center", va="center", fontsize=7.8)
        elif k == "term":
            ax.add_patch(FancyBboxPatch((x-w/2+0.6, y-0.3), w-1.2, 0.6, boxstyle="round,pad=0.02,rounding_size=0.28", fc=FILL[c], ec=C[c], lw=1.6))
            ax.text(x, y, t, ha="center", va="center", fontsize=8.2, fontweight="bold")
        elif k == "io":
            ax.add_patch(Polygon([[x-w/2+0.3, y-0.32], [x+w/2-0.1, y-0.32], [x+w/2+0.1, y+0.32], [x-w/2+0.5, y+0.32]], fc=FILL[c], ec=C[c], lw=1.4))
            ax.text(x, y, t, ha="center", va="center", fontsize=8.4)
        else:
            box(ax, x, y, w, 0.64, t, c, 8.4)
        if i: arr(ax, x, ys[i-1]-0.34 if steps[i-1][2] != "dec" else ys[i-1]-0.46, x, y+(0.46 if k == "dec" else 0.33), "gray", ("no" if (i-1) in inv else "yes") if steps[i-1][2] == "dec" else None)
    if side:
        for (i, t, c) in side:
            y = ys[i]; box(ax, 9.0, y, 1.9, 0.75, t, c, 7.6); arr(ax, 7.2 if steps[i][2] == "dec" else 7.7, y, 8.05, y, c, ("yes" if i in inv else "no") if steps[i][2] == "dec" else None)
    save(name)

flow("fc_cropmap", "Flowchart: crop-type mapping and area estimation (FASAL / NISAR)", [
    ("Start: define crop season, region, crop calendar", "navy", "term"),
    ("Acquire S1/EOS-04/NISAR SAR stack + Sentinel-2/LISS-III optical", "blue", "io"),
    ("Pre-process: calibration, terrain correction, speckle filter; cloud mask, BOA reflectance", "gray", "box"),
    ("Feature stack: σ⁰ VV/VH/HH/HV, ratios, RVI, coherence; NDVI/NDRE/LSWI time series; phenology", "purple", "box"),
    ("Ground truth: field survey, Digital Crop Survey, CROPIC (train 70 % / test 30 %)", "orange", "io"),
    ("Classifier: Random Forest / SVM / LSTM-Transformer", "teal", "box"),
    ("Accuracy OK?  (OA > 85–90 %, class F1)", "yellow", "dec"),
    ("Area estimation: stratified sample, error-adjusted area ± CI (Olofsson)", "green", "box"),
    ("Output: crop map + acreage → yield model → production", "navy", "term")],
    side=[(6, "Add samples,\nfeatures,\ntune model", "red")])

flow("fc_sif", "Flowchart: SIF retrieval and use (FLEX / ground)", [
    ("Start: FLORIS L1b radiance + Sentinel-3 OLCI/SLSTR (tandem)", "navy", "term"),
    ("Cloud screening & co-registration (SLSTR, OLCI)", "gray", "box"),
    ("Atmospheric correction in O₂-A/O₂-B (aerosol, pressure, water vapour)", "blue", "box"),
    ("Spectral fitting (SFM / SVD / FLD family) → apparent reflectance + SIF", "purple", "box"),
    ("Valid retrieval?  (residuals, SZA, fit quality)", "yellow", "dec"),
    ("L2: SIF 687 & 740 nm, full spectrum, fAPAR, PRI/NPQ, LST", "red", "box"),
    ("Normalise: SIF yield = SIF/APAR; structural correction (NIRv, fesc)", "teal", "box"),
    ("Validate vs ground FloX + eddy-covariance GPP", "orange", "io"),
    ("Uses: GPP, early stress alert, yield, insurance trigger", "green", "term")],
    side=[(4, "Flag / discard\npixel", "red")])

flow("fc_burnt", "Flowchart: paddy-residue burnt-area mapping with Sentinel-2", [
    ("Start: season 1 Oct – 30 Nov; AOI Punjab/Haryana", "navy", "term"),
    ("Paddy mask from Sentinel-1 VH (flooding signature)", "blue", "box"),
    ("Sentinel-2 L2A, s2cloudless masking, 5–10-day composites", "gray", "io"),
    ("Indices: NBR (B8,B12), NBR2 (B11,B12), MIRBI, BAIS2", "purple", "box"),
    ("Harvested stubble detected?  (NDVI drop, NBR ~0)", "yellow", "dec"),
    ("dNBR = NBR(stubble) − NBR(post); NBR2/MIRBI change", "orange", "box"),
    ("Classify burnt / unburnt / sown (RF + VIIRS-guided samples)", "teal", "box"),
    ("Validate: field photos, PlanetScope, active-fire points", "red", "io"),
    ("Output: burnt area by village/district + emissions", "green", "term")],
    side=[(4, "Wait for next\ncomposite\n(still standing)", "gray")])

flow("fc_zt", "Flowchart: identifying zero-till (CA) wheat fields", [
    ("Start: field boundaries + rice–wheat mask", "navy", "term"),
    ("Burn event after harvest?  (VIIRS / dNBR)", "yellow", "dec"),
    ("Residue on surface at sowing?  (NDTI / CAI high)", "yellow", "dec"),
    ("Tillage detected?  (SAR coherence loss)", "yellow", "dec"),
    ("Early green-up?  (NDVI rise 7–15 d earlier than CT)", "yellow", "dec"),
    ("Label: Zero-till / CA wheat (RF probability)", "green", "term")],
    side=[(1, "Burnt →\nnon-CA", "red"), (2, "Bare soil →\nCT or baled", "orange"), (3, "Ploughed →\nconventional", "red"), (4, "Check Super\nSeeder / mixed", "gray")], inv=(1, 3))

flow("fc_dsm", "Flowchart: digital soil mapping (scorpan + ML)", [
    ("Start: target property (SOC, pH, EC, texture) and depth", "navy", "term"),
    ("Sampling design: cLHS / stratified; lab or VNIR-SWIR spectral prediction", "orange", "io"),
    ("Covariates: S2 bare-soil composite, DEM (slope, TWI), climate, geology, LULC", "blue", "box"),
    ("Model: RF / QRF / Cubist / regression kriging", "purple", "box"),
    ("Spatial CV good?  (RMSE, R², CCC, PICP)", "yellow", "dec"),
    ("Predict map + 90 % prediction interval at GlobalSoilMap depths", "teal", "box"),
    ("Use: Soil Health Cards, salinity, carbon MRV", "green", "term")],
    side=[(4, "Add samples /\ncovariates", "red")])

flow("fc_drought", "Flowchart: drought declaration (Manual for Drought Management 2016/2020)", [
    ("Start: monsoon season monitoring (district/taluk)", "navy", "term"),
    ("Mandatory trigger: rainfall deviation / SPI ≤ −1 or dry spell ≥ 3–4 weeks?", "yellow", "dec"),
    ("Impact indicators: RS (NDVI/VCI, NDWI), sown area, soil moisture (MAI), hydrology", "blue", "box"),
    ("≥ 3 impact indicators show moderate/severe?", "yellow", "dec"),
    ("Ground truthing: sample villages, crop-loss survey", "orange", "io"),
    ("Declare drought → relief (SDRF/NDRF), PMFBY on-account", "red", "term")],
    side=[(1, "No drought;\ncontinue\nmonitoring", "green"), (3, "Watch /\nadvisory", "gray")])

flow("fc_pmfby", "Flowchart: PMFBY claim pathways", [
    ("Start: notified crop, insurance unit (GP), sum insured, TY", "navy", "term"),
    ("Sowing prevented (> 75 % area)?", "yellow", "dec"),
    ("Mid-season adversity (< 50 % normal yield)?", "yellow", "dec"),
    ("Localised calamity or post-harvest loss?", "yellow", "dec"),
    ("Harvest: AY = 70 % CCE + 30 % YES-TECH (MP 100 %)", "blue", "box"),
    ("AY < TY?", "yellow", "dec"),
    ("Claim = (TY − AY)/TY × SI → DigiClaim → bank", "green", "term")],
    side=[(1, "Pay up to 25 %\nSI; policy ends", "red"), (2, "On-account\n25 % of claim", "orange"), (3, "Farm-level\nsurvey (72 h)", "purple"), (5, "No claim", "gray")], h=8.0, inv=(1, 2, 3))

flow("fc_vrt", "Flowchart: sensor-based variable-rate nitrogen (GreenSeeker / satellite)", [
    ("Start: N-rich reference strip established at sowing", "navy", "term"),
    ("Measure NDVI in field and N-rich strip (Feekes 5 / CRI+30 d)", "blue", "io"),
    ("INSEY = NDVI / days from sowing → YP₀; RI = NDVI(Nrich)/NDVI(field)", "purple", "box"),
    ("RI > 1.1 ?  (crop responsive to N)", "yellow", "dec"),
    ("N rate = (YP₀·RI − YP₀) × %N grain / NUE (by zone / on-the-go)", "teal", "box"),
    ("Variable-rate applicator / drone applies prescription", "green", "box"),
    ("Evaluate: yield map, NUE, profit", "navy", "term")],
    side=[(3, "Apply little\nor no N", "gray")])

flow("fc_yestech", "Flowchart: YES-TECH GP-level yield pipeline (technology provider)", [
    ("Start: notified crop & GPs; historical CCEs (5+ yrs)", "navy", "term"),
    ("Crop mask & sowing date (SAR + optical); field boundaries", "blue", "box"),
    ("Features: VI/SAR time series, SIF, ET/SM, weather, soil", "purple", "box"),
    ("Base models: semi-physical, crop model+DA, ML, DL, agromet", "teal", "box"),
    ("Ensemble (stacking/BMA) + uncertainty", "orange", "box"),
    ("Holdout CCE validation within tolerance?", "yellow", "dec"),
    ("Blend: ≥ 30 % YES-TECH + CCE → AY per GP", "green", "box"),
    ("Upload to NCIP → claims (DigiClaim)", "navy", "term")],
    side=[(5, "Extra CCEs in\nhigh-uncertainty\nGPs; recalibrate", "red")])

flow("fc_mrv", "Flowchart: remote-sensing-enabled MRV for an agricultural carbon project", [
    ("Start: enrol farms (GIS polygons, land records, consent)", "navy", "term"),
    ("Baseline: 5-yr history of burning, tillage, crop rotation (RS)", "blue", "io"),
    ("Practice change verified each season?  (no fire, ZT, cover crop, AWD)", "yellow", "dec"),
    ("Stratified soil sampling (RS strata) + model (DayCent/RothC)", "purple", "box"),
    ("ΔSOC + avoided CH₄/N₂O − leakage − uncertainty − buffer", "teal", "box"),
    ("VVB verification passed?", "yellow", "dec"),
    ("Issue credits (VCU / CCC) → sell → farmer share", "green", "term")],
    side=[(2, "Field not\neligible this\nseason", "red"), (5, "Corrective\naction /\nre-sample", "orange")])

for f in (f_timeline,): f()
