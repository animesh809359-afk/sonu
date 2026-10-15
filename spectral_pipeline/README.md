# Spectral four-tier pipeline (work in progress)

Reusable implementation of the healthy-vs-diseased protocol (Steps 0–17:
Das et al. 2020 four-tier hierarchy + CART vs RF + K1–K5 feature extraction,
plus the four-tier analysis on the combined K1–K4 pool).

**Status:** partial and not yet run on real data. Built modules:
config (`sp/config.py`), data loading/audit (`sp/data.py`), splice correction +
Savitzky–Golay + guard zones (`sp/preprocess.py`), Welch/FDR/AUC/Youden/mixed
model (`sp/stats.py`), V1/V3/V4 folds (`sp/folds.py`), metrics (`sp/metrics.py`),
rpart via R (`sp/cart.py`, `sp/rpart_runner.R`), Balanced RF + MDI peaks + J–M +
QDA (`sp/models.py`), K1–K4 features (`sp/features.py`), four-tier engine
(`sp/fourtier.py`). Not built yet: K3b/K5 drivers, Excel and PPT reports.

Known open item: the mixed model returns NaN p-values when the plot variance
is estimated at 0; a fallback is needed before use.

Requirements: Python (numpy, scipy, pandas, scikit-learn, imbalanced-learn,
statsmodels, openpyxl, pyyaml), R with `rpart` and `jsonlite`.

A new dataset needs only a YAML file (see `configs/synthetic_test.yaml`):
data file, class column + mapping, plot column, date column; defaults in
`sp/config.py` hold the protocol settings and seeds.

`make_synthetic.py` writes simulated spectra for testing only — its numbers
are not results.
