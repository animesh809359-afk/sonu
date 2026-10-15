"""Part FS: comparison of feature-selection methods on the combined K1-K4 pool.

Every method is run (i) once on all leaves (reported feature sets) and (ii) inside each of
20 training sets - the 10 plot-grouped folds of the first V3 repeat and the 10 V4 30 %-plot
hold-out splits - so that the selected features can be evaluated on leaves of plots that the
selection never saw. Results are cached per unit in work/fs_units/ (re-running resumes).

usage: python stage_FS.py [n_jobs] [unit ...]       units: ALL, V3_0..V3_9, V4_0..V4_9
"""
from __future__ import annotations

import os
import pickle
import sys
import time
import traceback
import zlib

import numpy as np
import pandas as pd

from common import WORK, cfg, load
from sp import features
from sp import fs_methods as fm

C = cfg()
OUT = WORK / "fs_units"
OUT.mkdir(exist_ok=True)
SCALES = [2, 4, 8, 16, 32, 64, 128, 256]


def build_pool():
    """K1-K4 pool exactly as in Part C (same duplicate removal), plus CWT wavelet features."""
    D = load("data")
    spec = D["spec"]
    FE = features.build_all(spec, C)
    pool = FE["groups"]["G5"][1]
    Z = (pool.X - pool.X.mean(0)) / pool.X.std(0)
    scalar = np.where(pool.meta["position"].isna())[0]
    drop = set()
    for a_i, a in enumerate(scalar):
        for b in scalar[a_i + 1:]:
            if b not in drop and abs(float(Z[:, a] @ Z[:, b] / len(Z))) >= C["combined"]["dedupe_abs_r"]:
                drop.add(b)
    keep = np.array([j not in drop for j in range(pool.X.shape[1])])
    P = pool.subset(keep)
    P.meta["type"] = P.meta["type"].replace({"K1 band": "K1 band reflectance", "K2 continuum": "K2 continuum removal",
                                             "K3 index": "K3 vegetation index", "K4 D1 band": "K4 first-derivative band",
                                             "K4 edge": "K4 edge parameter"}).values
    ref = load("partC")["pool_meta"]["name"].tolist()
    assert P.meta["name"].tolist() == ref, "pool differs from Part C"
    # CWT (Mexican hat) of the K0-processed reflectance, 400-2500 nm
    m = ~spec.excluded
    wl = spec.wl[m]
    W = fm.cwt_mexh(spec.R[:, m], wl, SCALES)                          # n x 8 x nwl
    valid = np.ones(W.shape[1:], bool)
    for i, a in enumerate(SCALES):
        valid[i] &= (wl - wl.min() >= 2 * a) & (wl.max() - wl >= 2 * a)        # cone of influence
        for lo, hi in C["spectra"]["guard"]["R"]:
            valid[i] &= ~((wl >= lo - a) & (wl <= hi + a))                    # detector joins
    step = 5                                                                  # 5-nm grid keeps the matrix small
    keepw = (np.arange(len(wl)) % step) == 0
    Wk = W[:, :, keepw]
    vk = valid[:, keepw]
    wk = wl[keepw]
    names = [f"CWT s{a} {int(w)}" for a in SCALES for w in wk]
    cw = {"X": Wk.reshape(len(Wk), -1), "valid": vk.ravel(), "names": np.array(names), "scales": SCALES, "wl": wk,
          "shape": vk.shape}
    return D, P, cw


def units(F):
    u = {"ALL": None}
    for i, f in enumerate(F["V3"]):
        if f["rep"] == 0:
            u[f"V3_{f['fold']}"] = f
    for i, f in enumerate(F["V4"]):
        u[f"V4_{f['rep']}"] = f
    return u


def timed(res, key, fn):
    t = time.time()
    try:
        res[key] = fn()
        res[key]["sec"] = time.time() - t
    except Exception:  # keep the other methods going; the error is reported
        res[key] = {"error": traceback.format_exc(), "sec": time.time() - t}
    if os.environ.get("FS_VERBOSE"):
        print(f"  {key}: {res[key]['sec']:.1f}s" + (" ERROR " + res[key]["error"].splitlines()[-1] if "error" in res[key] else ""), flush=True)


def run_unit(name, tr, X, y, g, cw, n_cand=100):
    rng = lambda s: np.random.default_rng(zlib.crc32(f"{name}|{s}".encode()))  # noqa: E731
    X, y, g = X[tr], y[tr], g[tr]
    Xz = fm.zs(X)
    R = {"unit": name, "train": tr}
    U = fm.univariate(X, y)
    R["univariate"] = U
    for key, sc in (("Pearson r", U["abs_r"]), ("ANOVA F", U["F"]), ("Fisher score", U["fisher"]), ("J–M (univariate)", U["jm"])):
        R[key] = {"rank": np.argsort(-sc), "score": sc}
    timed(R, "Chi-square", lambda: {"score": (s := fm.chi2_binned(X, y)), "rank": np.argsort(-s)})
    timed(R, "Mutual information", lambda: {"score": (s := fm.mutual_info(X, y)), "rank": np.argsort(-s)})
    timed(R, "ReliefF", lambda: {"score": (s := fm.relieff(X, y, 10, rng("relief"))), "rank": np.argsort(-s)})
    timed(R, "mRMR", lambda: {"rank": np.array(fm.mrmr_fcq(X, y, U["F"], 30))})

    def _spa():
        ch, nat, info = fm.spa(X, y, g, U["F"])
        return {"rank": np.array(ch), "native": nat, "info": info}
    timed(R, "SPA", _spa)

    def _uve():
        s, nat, info = fm.mc_uve(X, y, 10, 100, rng("uve"))
        return {"score": s, "rank": np.argsort(-s), "native": nat, "info": info}
    timed(R, "MC-UVE", _uve)

    def _cars():
        o, nat, info = fm.cars(X, y, g, 10, 50, rng("cars"))
        return {"rank": o, "native": nat, "info": info}
    timed(R, "CARS", _cars)
    timed(R, "SVM-RFE", lambda: {"rank": fm.svm_rfe(X, y)})
    timed(R, "RF-RFE", lambda: {"rank": fm.rf_rfe(X, y, C)})

    # candidate pool for SFFS / GA: top features by ANOVA F with the |r| < 0.95 guard
    cands = fm.guard_topk(np.argsort(-U["F"]), Xz, n_cand)
    R["candidates"] = cands
    folds = fm.inner_folds(y, g, 3)
    qcrit = fm._Crit(lambda S: fm.cv_score(Xz[:, S], y, folds, fm.qda_fast))
    jcrit = fm._Crit(lambda S: fm.jm_multi(Xz[:, S], y))

    def _sffs(crit):
        sets, vals = fm.sffs(cands, crit, 20)
        kbest = max(vals, key=lambda k: (round(vals[k], 3), -k))
        return {"sets": sets, "crit": vals, "native": sets[kbest], "rank": np.array(sets[20]), "info": {"evaluations": crit.calls}}
    timed(R, "SFFS (QDA)", lambda: _sffs(qcrit))
    timed(R, "SFFS (J–M)", lambda: _sffs(jcrit))

    def _ga():
        order, nat, info = fm.ga_select(cands, qcrit, rng("ga"))
        return {"rank": np.array(order), "native": nat, "info": info}
    timed(R, "Genetic algorithm", _ga)

    timed(R, "RF importance", lambda: {"score": (s := fm.rf_mdi(X, y, C)), "rank": np.argsort(-s)})

    def _cart():
        imp, info = fm.cart_importance(X, y, g)
        o = np.argsort(-imp)
        return {"score": imp, "rank": o[imp[o] > 0], "native": np.where(imp > 0)[0], "info": info}
    timed(R, "CART importance", _cart)

    def _bor():
        o, nat, info = fm.boruta(X, y, C, 100 if name == "ALL" else 60, 200, 0.01, rng("boruta"))
        return {"rank": o, "native": nat, "score": info.pop("mean_imp"), "info": info}
    timed(R, "Boruta", _bor)

    def _vip():
        v, nat, info = fm.pls_vip(X, y, g)
        return {"score": v, "rank": np.argsort(-v), "native": nat, "info": info}
    timed(R, "PLS-VIP", _vip)

    def _lasso():
        o, nat, info = fm.lasso_path(X, y, g)
        return {"rank": o, "native": nat, "info": info}
    timed(R, "LASSO", _lasso)
    timed(R, "Gradient boosting", lambda: {"score": (s := fm.gbm_importance(X, y)), "rank": np.argsort(-s)})

    # CWT separability scalogram (Cheng et al. 2010) on the wavelet features
    def _cwt():
        Wtr = cw["X"][tr]
        sep = fm.jm_1d(Wtr, y)
        sep[~cw["valid"]] = 0
        pk = fm.scalogram_peaks(sep.reshape(cw["shape"]), cw["valid"].reshape(cw["shape"])).ravel()
        o = np.argsort(-sep)
        o = o[pk[o]]
        return {"score": sep, "rank": o, "space": "cwt"}
    timed(R, "CWT scalogram", _cwt)
    return R


def main():
    n_jobs = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    D, P, cw = build_pool()
    y, g, F = D["y"], D["groups"], D["folds"]
    U = units(F)
    todo = sys.argv[2:] or list(U)
    todo = [u for u in todo if not (OUT / f"{u}.pkl").exists()]
    with open(WORK / "fs_pool.pkl", "wb") as fh:
        pickle.dump({"meta": P.meta, "cwt_names": cw["names"], "cwt_valid": cw["valid"], "cwt_shape": cw["shape"],
                     "cwt_wl": cw["wl"], "cwt_scales": cw["scales"]}, fh)
    print(f"pool {P.X.shape}, CWT {cw['X'].shape}, units to run: {todo}", flush=True)

    def job(u):
        t = time.time()
        f = U[u]
        tr = np.arange(len(y)) if f is None else f["train"]
        R = run_unit(u, tr, P.X, y, g, cw)
        R["test"] = None if f is None else f["test"]
        R["sec"] = time.time() - t
        with open(OUT / f"{u}.pkl", "wb") as fh:
            pickle.dump(R, fh)
        errs = [k for k, v in R.items() if isinstance(v, dict) and "error" in v]
        return f"{u} done in {R['sec'] / 60:.1f} min; errors: {errs}"
    from joblib import Parallel, delayed
    for msg in Parallel(n_jobs=n_jobs, verbose=0, return_as="generator_unordered")(delayed(job)(u) for u in todo):
        print(time.strftime("[%H:%M:%S] ") + msg, flush=True)


if __name__ == "__main__":
    main()
