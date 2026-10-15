"""Shared functions for the mustard white-rust hyperspectral analysis.

Every step that learns from labels (MSC reference, date normalisation, OSC, feature
selection, NDSI search, hyper-parameter tuning) is fitted on training plots only.
"""
import os
import numpy as np
import pandas as pd
import pywt
from scipy.signal import savgol_filter
from scipy.spatial import ConvexHull
from sklearn.metrics import (accuracy_score, balanced_accuracy_score, f1_score, cohen_kappa_score,
                             matthews_corrcoef, roc_auc_score, average_precision_score, confusion_matrix,
                             precision_score, recall_score)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, 'cache')
TAB = os.path.join(ROOT, 'outputs', 'tables')
FIG = os.path.join(ROOT, 'outputs', 'figures')
os.makedirs(TAB, exist_ok=True)
os.makedirs(FIG, exist_ok=True)

WL_MIN, WL_MAX = 400, 2400
WL10 = np.arange(400, 2401, 10)
DATE_ORDER = ['2026-02-11', '2026-02-24', '2026-03-03', '2026-03-13']
DATE_LABEL = {'2026-02-11': '11 Feb', '2026-02-24': '24 Feb', '2026-03-03': '03 Mar', '2026-03-13': '13 Mar'}
STAGE_ORDER = ['Vegetative', 'Flowering', 'Pod formation']
VARIETIES = ['V1', 'V2', 'V3']


# ----------------------------------------------------------------------------- loading / QC
def load_raw():
    d = np.load(os.path.join(CACHE, 'raw.npz'))
    return d['X'], d['wl'], pd.read_csv(os.path.join(CACHE, 'meta.csv'))


def splice_correct(X, wl):
    """Additive splice correction at the ASD detector joins (1000/1001 and 1800/1801 nm).
    SWIR segments are shifted so the first SWIR value matches the linear extrapolation of the
    preceding detector (Hueni & Bialek, 2017)."""
    X = X.copy()
    for edge in (1000, 1800):
        i = int(np.where(wl == edge)[0][0])
        target = 2 * X[:, i] - X[:, i - 1]
        off = target - X[:, i + 1]
        X[:, i + 1:] += off[:, None]
    return X


def trim(X, wl, lo=WL_MIN, hi=WL_MAX):
    m = (wl >= lo) & (wl <= hi)
    return X[:, m], wl[m]


def sg(X, window=11, poly=2, deriv=0):
    return savgol_filter(X, window, poly, deriv=deriv, axis=1)


def resample10(X, wl, centres=WL10):
    out = np.empty((X.shape[0], len(centres)))
    for k, c in enumerate(centres):
        m = (wl >= c - 5) & (wl <= c + 4)
        out[:, k] = X[:, m].mean(1)
    return out


def snv(X):
    return (X - X.mean(1, keepdims=True)) / X.std(1, keepdims=True)


class MSC:
    def fit(self, X):
        self.ref = X.mean(0)
        return self

    def transform(self, X):
        out = np.empty_like(X)
        for i, s in enumerate(X):
            b, a = np.polyfit(self.ref, s, 1)
            out[i] = (s - a) / b
        return out


class DateNorm:
    """Lv et al. (2023): multiply every spectrum of a date by (baseline / healthy-mean of that date).
    Baseline = healthy mean of the first date. Fitted on training plots only."""
    def fit(self, X, dates, y):
        self.base = X[(y == 0) & (dates == DATE_ORDER[0])].mean(0)
        self.ratio = {d: self.base / X[(y == 0) & (dates == d)].mean(0) for d in np.unique(dates)}
        return self

    def transform(self, X, dates):
        out = X.copy()
        for d, r in self.ratio.items():
            out[dates == d] *= r
        return out


# ----------------------------------------------------------------------------- feature families
def R(X1, wl1, w):
    return X1[:, int(w - wl1[0])]


def vegetation_indices(X1, wl1):
    """Published indices on smoothed 1-nm reflectance (400-2400 nm). Returns DataFrame + citation map."""
    r = lambda w: R(X1, wl1, w)
    fd = sg(X1, 11, 2, deriv=1)
    d = lambda w: fd[:, int(w - wl1[0])]
    ix = lambda a, b: (wl1 >= a) & (wl1 <= b)
    rre = (r(670) + r(780)) / 2
    vi = {}
    cite = {}
    def add(name, val, ref, trait):
        vi[name] = val
        cite[name] = (ref, trait)
    add('NDVI', (r(800) - r(670)) / (r(800) + r(670)), 'Rouse et al., 1974', 'Chlorophyll/biomass')
    add('GNDVI', (r(800) - r(550)) / (r(800) + r(550)), 'Gitelson et al., 1996', 'Chlorophyll')
    add('SR', r(800) / r(670), 'Jordan, 1969', 'Chlorophyll/biomass')
    add('mND705', (r(750) - r(705)) / (r(750) + r(705) - 2 * r(445)), 'Sims & Gamon, 2002', 'Chlorophyll')
    add('mSR705', (r(750) - r(445)) / (r(705) - r(445)), 'Sims & Gamon, 2002', 'Chlorophyll')
    mcari = ((r(700) - r(670)) - 0.2 * (r(700) - r(550))) * (r(700) / r(670))
    add('MCARI', mcari, 'Daughtry et al., 2000', 'Chlorophyll')
    tcari = 3 * ((r(700) - r(670)) - 0.2 * (r(700) - r(550)) * (r(700) / r(670)))
    osavi = 1.16 * (r(800) - r(670)) / (r(800) + r(670) + 0.16)
    add('TCARI', tcari, 'Haboudane et al., 2002', 'Chlorophyll')
    add('OSAVI', osavi, 'Rondeaux et al., 1996', 'Structure/biomass')
    add('TCARI/OSAVI', tcari / osavi, 'Haboudane et al., 2002', 'Chlorophyll')
    add('MTCI', (r(754) - r(709)) / (r(709) - r(681)), 'Dash & Curran, 2004', 'Chlorophyll (red edge)')
    add('Datt', (r(850) - r(710)) / (r(850) - r(680)), 'Datt, 1999', 'Chlorophyll')
    add('PSSRa', r(800) / r(675), 'Blackburn, 1998', 'Chlorophyll a')
    add('PSSRb', r(800) / r(650), 'Blackburn, 1998', 'Chlorophyll b')
    add('CIred-edge', r(800) / r(720) - 1, 'Gitelson et al., 2003', 'Chlorophyll (red edge)')
    add('NDRE', (r(790) - r(720)) / (r(790) + r(720)), 'Barnes et al., 2000', 'Chlorophyll (red edge)')
    add('TVI', 0.5 * (120 * (r(750) - r(550)) - 200 * (r(670) - r(550))), 'Broge & Leblanc, 2001', 'Chlorophyll/LAI')
    add('NRI', (r(570) - r(670)) / (r(570) + r(670)), 'Filella et al., 1995', 'Nitrogen/chlorophyll')
    add('CCI', (r(531) - r(645)) / (r(531) + r(645)), 'Gamon et al., 2016', 'Carotenoid/chlorophyll')
    add('PRI', (r(531) - r(570)) / (r(531) + r(570)), 'Gamon et al., 1992', 'Xanthophyll/photosynthesis')
    add('SIPI', (r(800) - r(445)) / (r(800) - r(680)), 'Penuelas et al., 1995', 'Carotenoid/chlorophyll')
    add('PSRI', (r(680) - r(500)) / r(750), 'Merzlyak et al., 1999', 'Senescence (Car/Chl)')
    add('CRI1', 1 / r(510) - 1 / r(550), 'Gitelson et al., 2002', 'Carotenoid')
    add('CRI2', 1 / r(510) - 1 / r(700), 'Gitelson et al., 2002', 'Carotenoid')
    add('ARI1', 1 / r(550) - 1 / r(700), 'Gitelson et al., 2001', 'Anthocyanin')
    add('ARI2', r(800) * (1 / r(550) - 1 / r(700)), 'Gitelson et al., 2001', 'Anthocyanin')
    add('RGR', r(690) / r(550), 'Gamon & Surfus, 1999', 'Anthocyanin/chlorophyll')
    add('REP_LI', 700 + 40 * (rre - r(700)) / (r(740) - r(700)), 'Guyot & Baret, 1988', 'Red-edge position')
    add('Vog1', r(740) / r(720), 'Vogelmann et al., 1993', 'Red edge')
    add('Vog2', (r(734) - r(747)) / (r(715) + r(726)), 'Vogelmann et al., 1993', 'Red edge')
    add('RVSI', (r(712) + r(752)) / 2 - r(732), 'Merton & Huntington, 1999', 'Red-edge stress')
    add('WI', r(900) / r(970), 'Penuelas et al., 1997', 'Water')
    add('NDWI', (r(860) - r(1240)) / (r(860) + r(1240)), 'Gao, 1996', 'Water')
    add('MSI', r(1600) / r(820), 'Hunt & Rock, 1989', 'Water stress')
    add('NDII', (r(820) - r(1650)) / (r(820) + r(1650)), 'Hardisky et al., 1983', 'Water')
    add('LWVI1', (r(1094) - r(983)) / (r(1094) + r(983)), 'Galvao et al., 2005', 'Water')
    add('DWSI', (r(802) + r(547)) / (r(1657) + r(682)), 'Apan et al., 2004', 'Disease-water stress')
    l1, l2, l3 = np.log(1 / r(1510)), np.log(1 / r(1680)), np.log(1 / r(1754))
    add('NDNI', (l1 - l2) / (l1 + l2), 'Serrano et al., 2002', 'Nitrogen')
    add('NDLI', (l3 - l2) / (l3 + l2), 'Serrano et al., 2002', 'Lignin')
    add('CAI', 0.5 * (r(2000) + r(2200)) - r(2100), 'Nagler et al., 2000', 'Cellulose/dry matter')
    add('HI', (r(534) - r(698)) / (r(534) + r(698)) - 0.5 * r(704), 'Mahlein et al., 2013', 'Disease-specific (Healthy index)')
    add('PMI', (r(520) - r(584)) / (r(520) + r(584)) + r(724), 'Mahlein et al., 2013', 'Disease-specific (powdery mildew)')
    add('LRDSI', 6.9 * (r(605) / r(455)) - 1.2, 'Ashourloo et al., 2014', 'Disease-specific (leaf rust)')
    add('RBI', (r(1068) - r(1560)) / (r(1068) + r(1560)), 'Selvaprakash et al., 2026', 'Disease-specific (rice blast)')
    add('BI_ratio', r(1148) / r(1301), 'Mandal et al., 2023', 'Disease-specific (rice blast)')
    # red-edge / derivative parameters (Mandal et al., 2022; Zhang et al., 2012)
    m = ix(680, 750)
    add('REP_FD', wl1[m][np.argmax(fd[:, m], 1)].astype(float), 'Mandal et al., 2022', 'Red-edge position (derivative)')
    add('REV', fd[:, m].max(1), 'Mandal et al., 2022', 'Red-edge value (max derivative)')
    return pd.DataFrame(vi), cite


def derivative_features(X1, wl1):
    """First-derivative indices of Lv et al. (2023, Table 1) and edge parameters of Zhang et al. (2012)."""
    fd = sg(X1, 11, 2, deriv=1)
    d = lambda w: fd[:, int(w - wl1[0])]
    ix = lambda a, b: (wl1 >= a) & (wl1 <= b)
    f = {}
    f['Boochs_D703'] = d(703)
    f['Boochs2_D720'] = d(720)
    f['D1_D730/D706'] = d(730) / d(706)
    f['D2_D705/D722'] = d(705) / d(722)
    f['DPI'] = d(688) * d(710) / d(697) ** 2
    f['Datt3_D754/D704'] = d(754) / d(704)
    mx_r, mx_g = fd[:, ix(650, 750)].max(1), fd[:, ix(500, 550)].max(1)
    f['EGFN'] = (mx_r - mx_g) / (mx_r + mx_g)
    f['EGFR'] = mx_r / mx_g
    f['Vog3_D715/D705'] = d(715) / d(705)
    f['Sum_Dr1_626-795'] = fd[:, ix(626, 795)].sum(1)
    f['Sum_Dr2_680-780'] = fd[:, ix(680, 780)].sum(1)
    for nm, (a, b) in {'b': (490, 530), 'y': (550, 582), 'r': (670, 737)}.items():
        m = ix(a, b)
        if nm == 'y':  # yellow edge: most negative slope
            f['Dy'] = fd[:, m].min(1)
            f['lambda_y'] = wl1[m][np.argmin(fd[:, m], 1)].astype(float)
            f['SDy'] = fd[:, m].sum(1)
        else:
            f['D' + nm] = fd[:, m].max(1)
            f['lambda_' + nm] = wl1[m][np.argmax(fd[:, m], 1)].astype(float)
            f['SD' + nm] = fd[:, m].sum(1)
    df = pd.DataFrame(f)
    fd10 = resample10(fd, wl1)
    bands = pd.DataFrame(fd10, columns=[f'FD{w}' for w in WL10])
    return pd.concat([df, bands], axis=1)


CR_REGIONS = {'CR550-750': (550, 750), 'CR920-1060': (920, 1060), 'CR1100-1290': (1100, 1290),
              'CR1300-1650': (1300, 1650), 'CR1800-2100': (1800, 2100), 'CR2100-2350': (2100, 2350)}


def _hull(x, y):
    """Upper convex hull (monotone chain) interpolated onto x = the continuum."""
    hull = []
    for i in range(len(x)):
        while len(hull) >= 2:
            i1, i2 = hull[-2], hull[-1]
            if (x[i2] - x[i1]) * (y[i] - y[i1]) - (y[i2] - y[i1]) * (x[i] - x[i1]) >= 0:
                hull.pop()
            else:
                break
        hull.append(i)
    return np.interp(x, x[hull], y[hull])


def continuum_features(X1, wl1):
    """Band depth, width, area and position of max depth after continuum removal
    (Clark & Roush, 1984; Kokaly & Clark, 1999; Zhang et al., 2012)."""
    f = {}
    for nm, (a, b) in CR_REGIONS.items():
        m = (wl1 >= a) & (wl1 <= b)
        x = wl1[m].astype(float)
        dep, wid, area, pos = [], [], [], []
        for s in X1[:, m]:
            c = _hull(x, s)
            bd = 1 - s / c
            k = np.argmax(bd)
            dep.append(bd[k]); pos.append(x[k]); area.append(bd.sum())
            wid.append(float((bd >= bd[k] / 2).sum()))
        f[nm + '_depth'] = dep; f[nm + '_width'] = wid; f[nm + '_area'] = area; f[nm + '_pos'] = pos
    return pd.DataFrame(f)


CWT_SCALES = [2 ** k for k in range(1, 9)]


def cwt_features(X1, wl1):
    """Continuous wavelet transform, Mexican-hat mother wavelet, dyadic scales 2^1..2^8
    (Cheng et al., 2011; Tian et al., 2021; Lv et al., 2023); coefficients sampled every 10 nm."""
    idx = np.searchsorted(wl1, WL10)
    cols, blocks = [], []
    for k, s in enumerate(CWT_SCALES, start=1):
        coef, _ = pywt.cwt(X1, [s], 'mexh', axis=1)
        blocks.append(coef[0][:, idx])
        cols += [f'WF{w}_s{k}' for w in WL10]
    return pd.DataFrame(np.hstack(blocks), columns=cols)


def ndsi_scores(B, y, dates):
    """|Cohen d| of every normalised-difference index (b_i - b_j)/(b_i + b_j) on 10-nm bands.
    Score = mean |d| across dates with a sign-consistency requirement (stable across dates)."""
    nb = B.shape[1]
    I, J = np.triu_indices(nb, 1)
    scores, signs = [], []
    for d in np.unique(dates):
        m = dates == d
        Bi, Bj = B[m][:, I], B[m][:, J]
        nd = (Bi - Bj) / (Bi + Bj)
        a, b = nd[y[m] == 1], nd[y[m] == 0]
        sp = np.sqrt((a.var(0, ddof=1) * (len(a) - 1) + b.var(0, ddof=1) * (len(b) - 1)) / (len(a) + len(b) - 2))
        dd = (a.mean(0) - b.mean(0)) / sp
        scores.append(np.abs(dd)); signs.append(np.sign(dd))
    scores, signs = np.array(scores), np.array(signs)
    consistent = np.abs(signs.sum(0)) == len(signs)
    return I, J, np.where(consistent, scores.mean(0), 0.0), scores.min(0) * consistent


# ----------------------------------------------------------------------------- metrics
def metrics(y, pred, score=None):
    cm = confusion_matrix(y, pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()
    out = dict(OA=accuracy_score(y, pred), BA=balanced_accuracy_score(y, pred),
               Sensitivity=recall_score(y, pred, zero_division=0), Specificity=tn / (tn + fp) if tn + fp else np.nan,
               Precision=precision_score(y, pred, zero_division=0),
               F1_Diseased=f1_score(y, pred, pos_label=1, zero_division=0),
               F1_Healthy=f1_score(y, pred, pos_label=0, zero_division=0),
               MacroF1=f1_score(y, pred, average='macro', zero_division=0),
               Kappa=cohen_kappa_score(y, pred), MCC=matthews_corrcoef(y, pred),
               TN=tn, FP=fp, FN=fn, TP=tp)
    if score is not None and len(np.unique(y)) == 2:
        out['ROC_AUC'] = roc_auc_score(y, score)
        out['PR_AUC_Healthy'] = average_precision_score(1 - y, -score)
    return out


# ----------------------------------------------------------------------------- CV design
def plot_folds(meta_plots, k, seed):
    """Plot-grouped, class- and variety-stratified folds.
    meta_plots: DataFrame with columns plot, y, variety (one row per plot). Returns {plot: fold}."""
    rng = np.random.default_rng(seed)
    assign = {}
    for (v, yy), g in meta_plots.groupby(['variety', 'y']):
        p = g['plot'].to_numpy().copy()
        rng.shuffle(p)
        start = rng.integers(k)
        for i, pl in enumerate(p):
            assign[pl] = (start + i) % k
    return assign


def plot_table(M):
    return M.groupby('plot').agg(y=('y', 'first'), variety=('variety', 'first')).reset_index()
