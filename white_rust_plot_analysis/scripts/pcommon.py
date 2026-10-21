"""Shared paths, constants and helpers for the plot-level white-rust analysis.

The leaf-level pipeline (../../white_rust_analysis/scripts) supplies the classifiers, the
feature-selection procedures and the metric function; they are imported, not copied.
"""
import os, sys
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEAF = os.path.join(os.path.dirname(ROOT), 'white_rust_analysis')
sys.path.insert(0, os.path.join(LEAF, 'scripts'))
CACHE = os.path.join(ROOT, 'cache')
TAB = os.path.join(ROOT, 'outputs', 'tables')
FIG = os.path.join(ROOT, 'outputs', 'figures')
for d in (CACHE, TAB, FIG):
    os.makedirs(d, exist_ok=True)

DATE_ORDER = ['2026-02-11', '2026-02-24', '2026-03-03', '2026-03-13']
DATE_LABEL = {'2026-02-11': '11 Feb', '2026-02-24': '24 Feb', '2026-03-03': '03 Mar', '2026-03-13': '13 Mar'}
WL1 = np.arange(400, 2401)
WL10 = np.arange(400, 2401, 10)
JOINS = (1000, 1800)
BRANCHES = ('raw', 'smooth')
FAMILY_LABEL = {'REF': 'Reflectance (10 nm)', 'FD1': 'First derivative', 'FD2': 'Second derivative',
                'FD3': 'Third derivative', 'CR': 'Continuum-removal parameters', 'VI': 'Vegetation indices',
                'RE': 'Red-edge parameters', 'CWT': 'Wavelet (CWT) coefficients', 'NDSI': 'Optimised two-band indices'}


def load_meta():
    return pd.read_csv(os.path.join(CACHE, 'meta.csv'))


def load_family(branch, fam):
    return pd.read_pickle(os.path.join(CACHE, f'{branch}_{fam}.pkl'))


def load_spectra(branch):
    d = np.load(os.path.join(CACHE, f'{branch}_spectra.npz'))
    return d['R1'], d['wl']


def bin10(X1, wl1, centres=WL10):
    """Mean of the 1-nm values within +/-5 nm of each 10-nm centre (Mandal et al., 2023)."""
    out = np.empty((X1.shape[0], len(centres)))
    for k, c in enumerate(centres):
        m = (wl1 >= c - 5) & (wl1 <= c + 4)
        out[:, k] = np.nanmean(X1[:, m], axis=1)
    return out


def cell_folds(P, k, seed):
    """Folds made of whole variety x inoculation cells (1 control + 3 inoculated plots each),
    one cell per variety in every fold when k = 4. P: one row per plot with plot, variety, cell."""
    rng = np.random.default_rng(seed)
    assign = {}
    for v, g in P.groupby('variety'):
        cells = np.array(sorted(g['cell'].unique()))
        rng.shuffle(cells)
        for i, c in enumerate(cells):
            for pl in g.loc[g['cell'] == c, 'plot']:
                assign[pl] = i % k
    return assign


def plot_table(M):
    return M.groupby('plot').agg(y=('y', 'first'), variety=('variety', 'first'), cell=('cell', 'first'),
                                 inoc=('inoc', 'first'), block=('block', 'first')).reset_index()


def rep_metrics(res, keys, y, extra=()):
    """Pool the out-of-fold predictions of every repeat (each sample predicted once per repeat) and compute
    the metrics per repeat; res rows carry te (indices), score, pred and the grouping keys."""
    from common import metrics
    df = pd.DataFrame(res)
    rows = []
    for k, g in df.groupby(list(keys) + ['rep'], sort=False):
        te = np.concatenate(g['te'].to_numpy()); s = np.concatenate(g['score'].to_numpy()); p = np.concatenate(g['pred'].to_numpy())
        yt = y[te] if not isinstance(y, dict) else y[k[0]][te]
        r = dict(zip(list(keys) + ['rep'], k if isinstance(k, tuple) else (k,)))
        r.update(metrics(yt, p, s))
        for e in extra:
            r[e] = np.median([len(f) for f in g[e]]) if e == 'features' else g[e].iloc[0]
        rows.append(r)
    return pd.DataFrame(rows)
