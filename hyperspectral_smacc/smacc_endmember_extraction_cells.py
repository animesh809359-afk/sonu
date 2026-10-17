# %% ===== CELL 1: Settings and imports =====
# ===================== USER SETTINGS =====================
IMG_HDR = r"D:\Coalighned\24_02_2026\subset_200526.hdr"
ROI_FILES = {
    "healthy":  r"D:\Coalighned\24_02_2026\ROI(TRIAL)\healthy.xml",
    "diseased": r"D:\Coalighned\24_02_2026\ROI(TRIAL)\diseased.xml",
}
OUT_DIR = r"D:\Coalighned\24_02_2026\ROI(TRIAL)\TRIAL_h_d_combined"

N_ENDMEMBERS = 300        # endmembers to extract per class
MAX_PIXELS   = 100_000    # ROI pixels randomly drawn per class and given to SMACC (None = every ROI pixel; needs a lot of RAM)
NDVI_MIN     = 0.3        # pixels with NDVI below this are dropped (soil, water, shadow). None = keep everything
SMACC_EXCLUDE_NM = [(0, 420), (2350, 3000)]   # noisy band edges that SMACC ignores when searching.
                                              # The saved spectra still contain ALL bands.
RANDOM_SEED  = 42

import os
import time
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.path import Path
import spectral.io.envi as envi

os.makedirs(OUT_DIR, exist_ok=True)
rng = np.random.default_rng(RANDOM_SEED)


# %% ===== CELL 2: Open image, georeferencing, ROIs, quick-look =====
img = envi.open(IMG_HDR)          # finds the data file next to the .hdr automatically
n_rows, n_cols, n_bands = img.shape
wl = np.array([float(w) for w in img.metadata["wavelength"]])
interleave = img.metadata.get("interleave", "bil").lower()

# Memory map: nothing is read from disk until a pixel is accessed.
# Shape follows the file layout: BIL -> (rows, bands, cols), BIP -> (rows, cols, bands), BSQ -> (bands, rows, cols)
mm = img.open_memmap(interleave="source", writable=False)

def read_pixels(r, cols):
    """Spectra (len(cols), bands) of the given columns of image row r."""
    if interleave == "bil":
        return np.asarray(mm[r][:, cols]).T
    if interleave == "bip":
        return np.asarray(mm[r][cols, :])
    return np.asarray(mm[:, r, cols]).T          # bsq

def band_index(nm):
    return int(np.argmin(np.abs(wl - nm)))

print(f"Image: {n_rows} rows x {n_cols} cols x {n_bands} bands, interleave={interleave}, dtype={img.dtype}")
print(f"Wavelengths: {wl.min():.1f} - {wl.max():.1f} nm")

mi = [s.strip() for s in img.metadata["map info"]]
ref_x, ref_y = float(mi[1]), float(mi[2])
x0, y0 = float(mi[3]), float(mi[4])
dx, dy = float(mi[5]), float(mi[6])
print("Projection:", mi[0], "| pixel size:", dx, "x", dy)

def map_to_pix(x, y):
    """lon/lat -> continuous pixel coordinates (col, row), 0 = upper-left corner of the first pixel."""
    col = (np.asarray(x) - x0) / dx + ref_x - 1.0
    row = (y0 - np.asarray(y)) / dy + ref_y - 1.0
    return col, row

def pix_to_map(row, col):
    """0-based pixel index -> lon/lat of the pixel centre."""
    x = x0 + (np.asarray(col) + 1.5 - ref_x) * dx
    y = y0 - (np.asarray(row) + 1.5 - ref_y) * dy
    return x, y

def read_envi_roi_xml(path):
    """List of (exterior_xy, [hole_xy, ...]) polygons from an ENVI ROI .xml file (all regions merged)."""
    def to_xy(text):
        v = np.array(text.split(), dtype=float)
        return v.reshape(-1, 2)
    root = ET.parse(path).getroot()
    polys = []
    for reg in root.iter("Region"):
        crs = (reg.findtext(".//CoordSysStr") or "").strip()
        if "GEOGCS" not in crs and "PROJCS" not in crs:
            raise ValueError(f"{path}: ROI '{reg.get('name')}' is not in map coordinates (CoordSysStr={crs!r}). "
                             "Export the ROI from ENVI with the image's map coordinates.")
        for poly in reg.iter("Polygon"):
            ext = to_xy(poly.find("./Exterior/LinearRing/Coordinates").text)
            holes = [to_xy(h.text) for h in poly.findall("./Interior/LinearRing/Coordinates")]
            polys.append((ext, holes))
        print(f"  {os.path.basename(path)}: region '{reg.get('name')}', {len(polys)} polygon(s)")
    return polys

def roi_pixels(polys):
    """0-based (rows, cols) of all pixels whose centre lies inside the polygons (holes removed)."""
    lin = []
    for ext, holes in polys:
        cf, rf = map_to_pix(ext[:, 0], ext[:, 1])
        c0, c1 = max(int(np.floor(cf.min())), 0), min(int(np.ceil(cf.max())), n_cols)
        r0, r1 = max(int(np.floor(rf.min())), 0), min(int(np.ceil(rf.max())), n_rows)
        if c1 <= c0 or r1 <= r0:
            print("  WARNING: a polygon lies completely outside the image")
            continue
        cc, rr = np.meshgrid(np.arange(c0, c1), np.arange(r0, r1))
        centres = np.column_stack([cc.ravel() + 0.5, rr.ravel() + 0.5])
        inside = Path(np.column_stack([cf, rf])).contains_points(centres)
        for h in holes:
            hc, hr = map_to_pix(h[:, 0], h[:, 1])
            inside &= ~Path(np.column_stack([hc, hr])).contains_points(centres)
        lin.append(rr.ravel()[inside] * n_cols + cc.ravel()[inside])
    lin = np.unique(np.concatenate(lin)) if lin else np.array([], dtype=int)
    return lin // n_cols, lin % n_cols

rois = {}
for cls, path in ROI_FILES.items():
    polys = read_envi_roi_xml(path)
    rows, cols = roi_pixels(polys)
    rois[cls] = dict(polys=polys, rows=rows, cols=cols)
    print(f"{cls:>9}: {len(rows):,} pixels inside ROI")

# Pixels claimed by both ROIs would get both labels: drop them from both
lin_h = rois["healthy"]["rows"] * n_cols + rois["healthy"]["cols"]
lin_d = rois["diseased"]["rows"] * n_cols + rois["diseased"]["cols"]
overlap = np.intersect1d(lin_h, lin_d)
if overlap.size:
    print(f"{overlap.size:,} pixels fall in both ROIs and are removed from both")
    for cls, lin in (("healthy", lin_h), ("diseased", lin_d)):
        keep = ~np.isin(lin, overlap)
        rois[cls]["rows"], rois[cls]["cols"] = rois[cls]["rows"][keep], rois[cls]["cols"][keep]

step = max(1, max(n_rows, n_cols) // 900)       # down-sample for display only
def quicklook(nm):
    b = band_index(nm)
    if interleave == "bil":
        a = np.asarray(mm[::step, b, ::step], dtype=float)
    elif interleave == "bip":
        a = np.asarray(mm[::step, ::step, b], dtype=float)
    else:
        a = np.asarray(mm[b, ::step, ::step], dtype=float)
    valid = np.isfinite(a) & (a != 0)
    lo, hi = np.percentile(a[valid], [2, 98]) if valid.any() else (0, 1)
    return np.clip((a - lo) / (hi - lo + 1e-12), 0, 1)

rgb = np.dstack([quicklook(650), quicklook(550), quicklook(470)])
roi_colours = {"healthy": "lime", "diseased": "red"}

def show_rois(ax):
    ax.imshow(rgb, extent=(0, n_cols, n_rows, 0))
    for cls, roi in rois.items():
        for i, (ext, _) in enumerate(roi["polys"]):
            cf, rf = map_to_pix(ext[:, 0], ext[:, 1])
            ax.plot(cf, rf, color=roi_colours.get(cls, "yellow"), lw=1.5, label=cls if i == 0 else None)
    ax.set_xlabel("column"); ax.set_ylabel("row")

fig, ax = plt.subplots(figsize=(8, 8))
show_rois(ax); ax.legend(); ax.set_title("True-colour quick-look with ROIs")
plt.show()


# %% ===== CELL 3: Extract ROI spectra =====
i_red, i_nir = band_index(670), band_index(800)

def extract_roi_spectra(rows, cols, max_pixels, ndvi_min):
    n_roi = len(rows)
    keep_p = 1.0 if (max_pixels is None or n_roi <= max_pixels) else max_pixels / n_roi
    order = np.argsort(rows, kind="stable")
    rows, cols = rows[order], cols[order]
    uniq, start = np.unique(rows, return_index=True)
    stop = np.append(start[1:], len(rows))

    spec, rr, cc = [], [], []
    n_nodata = n_lowndvi = 0
    t0 = time.time()
    for k, r in enumerate(uniq):
        c = cols[start[k]:stop[k]]
        if keep_p < 1.0:
            c = c[rng.random(c.size) < keep_p]
            if c.size == 0:
                continue
        s = read_pixels(int(r), c).astype(np.float32)
        ok = np.isfinite(s).all(axis=1) & (np.abs(s).sum(axis=1) > 0)
        n_nodata += int((~ok).sum())
        if ndvi_min is not None:
            nir, red = s[:, i_nir], s[:, i_red]
            with np.errstate(divide="ignore", invalid="ignore"):
                ndvi = (nir - red) / (nir + red)
            veg = ndvi >= ndvi_min
            n_lowndvi += int((ok & ~veg).sum())
            ok &= veg
        spec.append(s[ok]); rr.append(np.full(int(ok.sum()), r)); cc.append(c[ok])
        if k % 300 == 0:
            print(f"   row {k+1}/{len(uniq)}  ({time.time()-t0:.0f} s)", end="\r")
    spec = np.concatenate(spec) if spec else np.empty((0, n_bands), np.float32)
    print(f"\n   ROI pixels: {n_roi:,} | sampled: {len(spec) + n_nodata + n_lowndvi:,} | "
          f"no-data dropped: {n_nodata:,} | NDVI<{ndvi_min} dropped: {n_lowndvi:,} | kept: {len(spec):,}")
    return spec, np.concatenate(rr).astype(int), np.concatenate(cc).astype(int)

pool = {}
for cls, roi in rois.items():
    print(f"{cls}:")
    s, r, c = extract_roi_spectra(roi["rows"], roi["cols"], MAX_PIXELS, NDVI_MIN)
    if len(s) < N_ENDMEMBERS:
        raise ValueError(f"{cls}: only {len(s)} usable pixels, fewer than N_ENDMEMBERS={N_ENDMEMBERS}. "
                         "Lower NDVI_MIN or check the ROI.")
    pool[cls] = dict(spec=s, rows=r, cols=c)


# %% ===== CELL 4: SMACC =====
def smacc(H, n_end, verbose=True):
    """SMACC endmember extraction.
    H     : (N, B) pixel spectra
    n_end : number of endmembers
    Returns idx (row indices of H chosen as endmembers, in SMACC order),
            F   (N, n_end) non-negative abundances, and the max residual norm after each step."""
    H = np.asarray(H, dtype=np.float64)
    N = H.shape[0]
    R = H.copy()
    F = np.zeros((N, n_end))
    norms = np.einsum("ij,ij->i", R, R)
    first = norms.max()
    idx, max_res = [], []
    t0 = time.time()
    for n in range(n_end):
        q = int(np.argmax(norms))
        if norms[q] <= 1e-12 * first:
            print(f"\n   stopped at {n} endmembers: residual is zero (data fully explained)")
            break
        w = R[q].copy()
        On = R @ w / (w @ w)                      # projection coefficients onto the new direction
        alpha = np.ones(N)
        Fq = F[q, :n].copy()
        for k in np.nonzero(Fq > 0)[0]:           # keep earlier abundances >= 0
            t = On * Fq[k]
            with np.errstate(divide="ignore", invalid="ignore"):
                np.minimum(alpha, np.where(t > 0, F[:, k] / t, np.inf), out=alpha)
        alpha[On <= 0] = 0.0                      # positivity
        alpha[q] = 1.0                            # the selected pixel is removed completely
        Fn = np.clip(alpha * On, 0.0, None)
        R -= np.outer(Fn, w)
        if n:
            F[:, :n] -= np.outer(Fn, Fq)
            np.maximum(F[:, :n], 0.0, out=F[:, :n])
        F[:, n] = Fn
        idx.append(q)
        norms = np.einsum("ij,ij->i", R, R)
        max_res.append(float(np.sqrt(norms.max())))
        if verbose and ((n + 1) % 25 == 0 or n + 1 == n_end):
            print(f"   {n+1}/{n_end} endmembers, max residual norm {max_res[-1]:.4g}  ({time.time()-t0:.0f} s)", end="\r")
    idx = np.array(idx, dtype=int)
    m = len(idx)
    F = F[:, :m]
    F[idx, :] = 0.0                               # correction from the SMACC paper
    F[idx, np.arange(m)] = 1.0
    if verbose:
        print()
    return idx, F, np.array(max_res)

smacc_bands = np.ones(n_bands, bool)
for lo, hi in SMACC_EXCLUDE_NM:
    smacc_bands &= ~((wl >= lo) & (wl <= hi))
print(f"SMACC uses {smacc_bands.sum()} of {n_bands} bands")

results = {}
for cls, p in pool.items():
    print(f"SMACC on {cls} ({len(p['spec']):,} pixels):")
    idx, F, max_res = smacc(p["spec"][:, smacc_bands], N_ENDMEMBERS)
    results[cls] = dict(idx=idx, F=F, max_res=max_res)
    if len(idx) < N_ENDMEMBERS:
        print(f"   NOTE: only {len(idx)} endmembers could be found for {cls}")


# %% ===== CELL 5: Save CSV and ENVI spectral libraries =====
band_cols = [f"{w:.2f}" for w in wl]
tables = []
for cls, res in results.items():
    p, idx = pool[cls], res["idx"]
    lon, lat = pix_to_map(p["rows"][idx], p["cols"][idx])
    meta = pd.DataFrame({
        "class": cls,
        "endmember_no": np.arange(1, len(idx) + 1),     # SMACC order (1 = first extracted)
        "row_0based": p["rows"][idx],
        "col_0based": p["cols"][idx],
        "lon": lon,
        "lat": lat,
    })
    spectra = pd.DataFrame(p["spec"][idx], columns=band_cols)
    tables.append(pd.concat([meta, spectra], axis=1))

    # ENVI spectral library, one per class (opens in ENVI's Spectral Library Viewer)
    names = [f"{cls}_EM{i:03d}" for i in range(1, len(idx) + 1)]
    hdr = {"wavelength": list(wl), "wavelength units": "Nanometers", "spectra names": names}
    envi.SpectralLibrary(p["spec"][idx].astype(np.float32), hdr, None).save(
        os.path.join(OUT_DIR, f"smacc_{cls}_endmembers"), description=f"SMACC endmembers, {cls} ROI")

em = pd.concat(tables, ignore_index=True)
csv_path = os.path.join(OUT_DIR, "smacc_endmembers_healthy_diseased.csv")
em.to_csv(csv_path, index=False)
print("Saved:", csv_path, em.shape)
print("Saved ENVI libraries:", [f"smacc_{c}_endmembers.sli" for c in results])
em.iloc[:5, :10]


# %% ===== CELL 6: Plots =====
def gapped(y):
    """Insert NaN where the wavelength jumps (removed water bands) so lines are not drawn across gaps."""
    d = np.diff(wl)
    neighbour = np.maximum(np.r_[d[1], d[:-1]], np.r_[d[1:], d[-2]])   # spacing of the bands either side
    gap = np.where(d > 2.5 * neighbour)[0] + 1
    return np.insert(wl.astype(float), gap, np.nan), np.insert(np.asarray(y, float), gap, np.nan, axis=-1)

fig, axes = plt.subplots(1, 3, figsize=(18, 5))
for ax, cls in zip(axes[:2], results):
    S = pool[cls]["spec"][results[cls]["idx"]]
    for s in S:
        ax.plot(*gapped(s), color=roi_colours[cls], alpha=0.08, lw=0.7)
    ax.plot(*gapped(S.mean(0)), color="k", lw=2, label="mean of endmembers")
    ax.plot(*gapped(pool[cls]["spec"].mean(0)), color="k", ls="--", lw=1.5, label="mean of all ROI pixels")
    ax.set_title(f"{cls}: {len(S)} SMACC endmembers"); ax.set_xlabel("Wavelength (nm)"); ax.set_ylabel("Reflectance")
    ax.legend()

ax = axes[2]
for cls in results:
    S = pool[cls]["spec"][results[cls]["idx"]]
    x, m = gapped(S.mean(0)); _, sd = gapped(S.std(0))
    ax.plot(x, m, color=roi_colours[cls], lw=2, label=f"{cls} (mean ± SD)")
    ax.fill_between(x, m - sd, m + sd, color=roi_colours[cls], alpha=0.2)
ax.set_title("Healthy vs diseased endmembers"); ax.set_xlabel("Wavelength (nm)"); ax.legend()
plt.tight_layout(); plt.show()

fig, axes = plt.subplots(1, 2, figsize=(16, 7))
show_rois(axes[0])
for cls in results:
    p, idx = pool[cls], results[cls]["idx"]
    axes[0].scatter(p["cols"][idx], p["rows"][idx], s=8, c=roi_colours[cls], edgecolors="k", linewidths=0.3)
axes[0].set_title("Locations of the SMACC endmembers")
for cls in results:
    axes[1].plot(np.arange(1, len(results[cls]["max_res"]) + 1), results[cls]["max_res"], color=roi_colours[cls], label=cls)
axes[1].set_xlabel("Number of endmembers"); axes[1].set_ylabel("Max residual norm"); axes[1].set_yscale("log")
axes[1].set_title("SMACC convergence"); axes[1].legend()
plt.tight_layout(); plt.show()


# %% ===== CELL 7: Random samples for comparison (optional) =====
rand_tables = []
for cls, p in pool.items():
    pick = rng.choice(len(p["spec"]), size=N_ENDMEMBERS, replace=False)
    lon, lat = pix_to_map(p["rows"][pick], p["cols"][pick])
    meta = pd.DataFrame({"class": cls, "sample_no": np.arange(1, N_ENDMEMBERS + 1),
                         "row_0based": p["rows"][pick], "col_0based": p["cols"][pick], "lon": lon, "lat": lat})
    rand_tables.append(pd.concat([meta, pd.DataFrame(p["spec"][pick], columns=band_cols)], axis=1))
rand = pd.concat(rand_tables, ignore_index=True)
rand_path = os.path.join(OUT_DIR, "random_samples_healthy_diseased.csv")
rand.to_csv(rand_path, index=False)
print("Saved:", rand_path, rand.shape)

fig, ax = plt.subplots(figsize=(8, 5))
for cls in results:
    ax.plot(*gapped(pool[cls]["spec"][results[cls]["idx"]].mean(0)), color=roi_colours[cls], lw=2, label=f"{cls} - SMACC mean")
    ax.plot(*gapped(rand.loc[rand["class"] == cls, band_cols].mean().values), color=roi_colours[cls], ls="--", lw=2,
            label=f"{cls} - random-sample mean")
ax.set_xlabel("Wavelength (nm)"); ax.set_ylabel("Reflectance"); ax.legend(); plt.show()
