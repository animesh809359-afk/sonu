"""Tier 2 - CART (R rpart) band/feature selection and CART classification.

All trees of a step are fitted in one R process: Python writes the feature
matrix once (binary) plus a list of jobs (training rows, test rows, columns).
Settings follow Das et al. (2020) with the imbalance correction:
method = "class", prior = c(0.5, 0.5), split = "gini", minsplit = 20,
minbucket = 7, cp = 0.01, maxcompete = 0, maxsurrogate = 0.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

RUNNER = Path(__file__).with_name("rpart_runner.R")


def r_available() -> bool:
    return shutil.which("Rscript") is not None


def grouped_xval(y, groups, k=10, seed=42):
    """Plot-grouped fold assignment (1..k) for rpart's internal CV; k is capped at the number of
    plots of the smaller class so that every fold holds both classes."""
    from .folds import group_folds, n_group_folds
    k = n_group_folds(y, groups, k)
    xv = np.zeros(len(y), int)
    splits, _ = group_folds(y, groups, k, seed)
    for f, (_, te) in enumerate(splits):
        xv[te] = f + 1
    return xv


def run_jobs(X, y, names, jobs, cfg):
    """jobs: list of dict(train=idx, test=idx or [], cols=idx or None,
    full=bool, xval=fold vector or None). Returns one result dict per job
    with selected feature names in order of first use."""
    if not r_available():
        raise RuntimeError("Rscript not found: install R with packages rpart and jsonlite")
    X = np.asarray(X, float)
    n, p = X.shape
    c = cfg["cart"]
    with tempfile.TemporaryDirectory(prefix="rpart_") as td:
        td = Path(td)
        X.T.astype("<f8").tofile(td / "X.bin")      # column-major for R
        meta = {"n": n, "p": p, "y": [int(v) for v in y],
                "settings": {"minsplit": c["minsplit"], "minbucket": c["minbucket"],
                             "cp": c["cp"], "maxcompete": c["maxcompete"],
                             "maxsurrogate": c["maxsurrogate"], "split": c["split"],
                             "prior": c["prior"], "xval_folds": c["xval_folds"]}}
        (td / "meta.json").write_text(json.dumps(meta))
        js = []
        for jb in jobs:
            js.append({"train": [int(i) + 1 for i in jb["train"]],
                       "test": [int(i) + 1 for i in jb.get("test", [])],
                       "cols": [int(i) + 1 for i in (jb.get("cols") if jb.get("cols") is not None else [])],
                       "full": bool(jb.get("full", False)),
                       "xval": [int(v) for v in (jb.get("xval") if jb.get("xval") is not None else [])]})
        (td / "jobs.json").write_text(json.dumps(js))
        r = subprocess.run(["Rscript", str(RUNNER), str(td)], capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError("rpart failed:\n" + r.stderr[-3000:])
        res = json.loads((td / "result.json").read_text())
    names = np.asarray(names)

    def fmap(v):
        if isinstance(v, str):
            v = [v]
        return [str(names[int(s[1:]) - 1]) for s in (v or [])]

    out = []
    for jb, rr in zip(jobs, res):
        o = {"vars": fmap(rr.get("vars"))}
        if jb.get("test") is not None and len(jb.get("test", [])):
            o["prob"] = np.atleast_1d(np.asarray(rr["prob"], float))
            o["pred"] = np.atleast_1d(np.asarray(rr["pred"], int))
        if jb.get("full"):
            fr = pd.DataFrame(rr["frame"])
            fr["var"] = [(str(names[int(v[1:]) - 1]) if v != "<leaf>" else "leaf") for v in fr["var"]]
            fr["label"] = [_relabel(lbl, names) for lbl in fr["label"]]
            o["frame"] = fr
            o["cptable"] = pd.DataFrame(rr["cptable"])
            if "vars_1se" in rr:
                o["vars_1se"] = fmap(rr["vars_1se"])
                o["nsplit_1se"] = rr["nsplit_1se"]
                fr1 = pd.DataFrame(rr["frame_1se"])
                fr1["var"] = [(str(names[int(v[1:]) - 1]) if v != "<leaf>" else "leaf") for v in fr1["var"]]
                fr1["label"] = [_relabel(lbl, names) for lbl in fr1["label"]]
                o["frame_1se"] = fr1
            o["prob_train"] = np.asarray(rr["prob_train"], float)
        out.append(o)
    return out


def _relabel(lbl, names):
    import re
    return re.sub(r"\bf(\d+)\b", lambda m: str(names[int(m.group(1)) - 1]), str(lbl))
