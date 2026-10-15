# Spectral four-tier pipeline (healthy vs diseased leaf spectra)

Reusable implementation of the four-tier hierarchical method of Das et al. (2020,
*Geocarto International* 35:64–77) with imbalance / pseudo-replication / selection-bias
corrections, CART vs Random Forest, disease-sensitive feature extraction (Part K) and the
four-tier analysis of the combined feature pool (Part C: K1 + K2–K4; Part C′: raw reflectance + K2–K4).

First application: white rust (*Albugo candida*) in mustard leaves, four dates, three growth
stages, three varieties pooled (`configs/whiterust_all_dates.yaml`). Results are in
`../deliverables/WhiteRust_AllDates/` (Excel workbook, PowerPoint deck, Word report).

## Steps

| Stage | Script | What it does |
|---|---|---|
| 0–1 | `analysis/stage_data.py` | read the ASD export workbooks (one column per spectrum), drop plot-average formula columns and exact duplicate spectra, audit, noise by region, SAM outlier screen, splice correction + Savitzky–Golay smoothing/derivatives + guard zones, build the folds (V1, V3, V4, V5) |
| A | `analysis/stage_A.py` | Tier 1 (Welch + BH-FDR, ANOVA, Levene, mixed model, 1000 balanced subsets), Tier 2 (rpart with prior 0.5/0.5; Balanced RF importance peaks), Tier 3 (J–M), Tier 4 (QDA equal priors), validation V1–V5 + RUS, CART vs RF classifiers, Wilcoxon tests, stability, sensitivity (band range, duplicates), R cross-checks (MASS::qda, randomForest) |
| K | `analysis/stage_K.py` | K0 denoising checks, K1 band reflectance, K2 continuum removal, K3 31 vegetation indices, K3b optimised NDSI/DI (nested), K4 first/second derivative + 20 edge parameters, K4b REIP (4 methods), K6 correlation spectra, K5 CART vs RF on every feature group + nested top-15 |
| K3b-JF | `analysis/stage_K3b_joinfree.py` | optimised two-band index repeated without band pairs that straddle a detector join (run after stage K) |
| C | `analysis/stage_C.py` | the four tiers on the combined K1–K4 pool (CART and RF selection, J–M, QDA, V1–V5, stability) |
| C′ | `analysis/stage_CR.py` | variant of C: the four tiers on raw reflectance (all bands, as in Part A) + K2 + K3 + K4 — same engine, seeds and folds |
| compare | `analysis/stage_compare.py` | C vs A vs K5 paired tests, V5 by date, stratified checks, guard-edge check, synthesis |
| compare C′ | `analysis/stage_compare_CR.py` | C′ vs C vs A side by side, paired Wilcoxon on identical folds, feature-type composition, overlap, raw bands near joins / noisy ends, V5 by date; adds C′ rows to the synthesis (run after `stage_compare.py`) |
| FS | `analysis/stage_FS.py` (+ `sp/fs_methods.py`) | 23 feature-selection methods (filter: r, ANOVA F, Fisher, χ², MI, ReliefF, J–M, mRMR, SPA, MC-UVE, CWT scalogram; wrapper: SVM-RFE, RF-RFE, CARS, SFFS-QDA, SFFS-J–M, GA; embedded: RF, CART, Boruta, PLS-VIP, LASSO, gradient boosting) run on all leaves and inside 20 training sets (V3 repeat 1 + V4); cached per unit in `work/fs_units/` |
| FS eval | `analysis/stage_FS_eval.py` | top-k (5–20, plain / redundancy-controlled) → QDA, LDA, RF on held-out plots; stability (Kuncheva, Jaccard ±10 nm); Friedman–Nemenyi, Wilcoxon–Holm; composite ranking; consensus features; detector-join check |
| FS features | `analysis/stage_FS_features.py`, `make_fs_features.py`, `build_fs_features_ppt.js` | disease-specific features across methods: spectral-region map, agreement tiers, consistency across dates/stages/varieties, accuracy of fixed stable feature sets; presentation |
| (history) | `analysis/patch_mixed.py`, `analysis/patch_cond.py` | one-off fixes applied to the first white-rust run (statsmodels mixed model → R nlme; scale-free condition numbers); both are now built into the stage scripts and are not needed for new runs |
| report | `make_figures.py`, `build_excel.py`, `export_json.py`, `build_ppt.js`, `build_docx.js` | figures, workbook (formulas recalculated by LibreOffice), deck, Word report |

Mixed models use R `nlme::lme` (REML; t-test with between-plot df). CART uses R `rpart`.

## Running on a new dataset

1. Put the raw files in `raw_data/` and copy `configs/whiterust_all_dates.yaml`; edit
   `data.files` (file, date label), the class labels, `spectra.keep_range`, `spectra.canopy`
   (true = mask atmospheric water bands for canopy data), guard zones and `cr_windows` if the
   sensor or range differs. Settings, seeds and the validation design are defaults in
   `sp/config.py` and normally stay unchanged.
2. If the files are not the transposed ASD export layout, use `sp/data.py` (one row per
   spectrum, wavelength columns) instead of `sp/load_asd.py` in `stage_data.py`.
3. Run, from `analysis/`:
   ```
   python stage_data.py && python stage_A.py && python stage_K.py && python stage_K3b_joinfree.py && python stage_C.py && python stage_CR.py
   python stage_compare.py && python stage_compare_CR.py && python make_figures.py
   OMP_NUM_THREADS=1 python stage_FS.py 4 && python stage_FS_eval.py && python make_fs_figures.py   # feature-selection comparison (≈ 1.5 h on 4 cores)
   python build_excel.py && python <xlsx-skill>/scripts/recalc.py <workbook>
   python export_json.py
   PPTX_SKILL=<pptx-skill> node build_ppt.js ../work <deck.pptx>
   DOCX_MODULE=<path to docx> node build_docx.js ../work <report.docx>
   python build_fs_excel.py && python export_fs_json.py && PPTX_SKILL=<pptx-skill> node build_fs_ppt.js ../work <fs_deck.pptx>
   ```
   Stages A and K can run in parallel (≈ 30 and ≈ 60 min for 2264 spectra on 4 cores).
4. Write `work/conclusions.json` (interpretation text used by the summary sheet, the deck and
   the report) after reading the results — `analysis/conclusions_whiterust_all_dates.json` is the
   white-rust example. Every number in it must be checked against the workbook. The feature-selection deliverables read
   `work/fs_conclusions.json` in the same way (example: `analysis/fs_conclusions_whiterust.json`; references in
   `analysis/fs_references.json`).

Requirements: Python ≥ 3.11 (numpy, scipy, pandas, statsmodels, scikit-learn,
imbalanced-learn, matplotlib, openpyxl, pyyaml), R ≥ 4.3 with rpart, nlme, MASS,
randomForest, jsonlite; Node with pptxgenjs and docx; LibreOffice for the formula recalculation.
