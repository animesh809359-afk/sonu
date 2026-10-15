# Hyperspectral detection of white rust in Indian mustard (ASD contact probe)

Pooled prediction model for healthy vs white-rust (*Albugo candida*) mustard leaves, whatever the date,
variety or growth stage. The methodology combines the ten reviewed papers (Tian et al. 2021; Lv et al. 2023;
Mandal et al. 2022, 2023; Selvaprakash et al. 2026; Terentev et al. 2023; Zhang et al. 2012; Zhu et al. 2017;
Huang et al. 2020; Nguyen et al. 2023).

## Deliverables (`outputs/`)

| File | Content |
|---|---|
| `WhiteRust_Mustard_Hyperspectral_Analysis.xlsx` | One sheet per analysis step: tables, native (editable) Excel charts, formula-driven summaries, cleaned 10-nm data, references |
| `WhiteRust_Mustard_PhD_Seminar.pptx` | PhD seminar deck (introduction, literature, objectives, methods, results, discussion, conclusions, references) with native editable charts and tables |
| `figures/*.png` | 300-dpi publication-style figures for the thesis |
| `tables/*.csv` | Every result table produced by the scripts |

## Pipeline (`scripts/`)

| Script | Step |
|---|---|
| `s01_load.py` | Assemble the four ASD workbooks (raw `.asd.sco` columns only; Excel AVERAGE columns ignored) |
| `s02_qc_preprocess.py` | Splice correction, 400-2400 nm trimming, noise/SNR, consensus outlier screening, SG smoothing, 10-nm resampling, feature families F1, F2, F4, F5, F6 |
| `s03_explore.py` | Mean/difference/ratio/derivative spectra, band-wise tests (FDR), J-M distance, red-edge parameters, PCA/t-SNE, PERMANOVA, mixed models, VI ranking, NDSI search (MWRI), CWT sensitivity |
| `s04_cv.py` | Main experiment: 10 feature scenarios x 10 classifiers, nested plot-grouped stratified 4-fold CV x 25 repeats |
| `s05_experiments.py` | E1 preprocessing, E2 transfer (unseen date/variety/stage), E3 metadata, E4 learning curve, E5 simulated sensors, E6 outlier sensitivity |
| `s06_summarise.py` | Summaries, Friedman/Nemenyi, corrected t-tests, confusion matrices, ROC, sub-groups, selection stability, final model and interpretation |
| `s11_ofc.py` | E7: optimal feature combinations (OFC-LDA/kNN/SVM) from wrapper SFFS after Tian et al. (2021) |
| `s07_figures.py`, `s08_excel.py`, `s09_export_ppt_data.py`, `s10_narrative.py`, `build_ppt.js` | Figures, workbook, slide data, slide text, deck |
| `common.py`, `models.py` | Shared preprocessing, features, metrics, CV design, classifiers, feature selection |

Run order: `s01 -> s02 -> s03 -> s04 (25 main) -> s06 -> s11 (25) -> s05 -> s07 -> s08 -> s09/s10 -> build_ppt.js`.
`s01_load.py` takes the folder holding the four source workbooks and the cache folder as arguments.

## Key design decisions

* **Unit of independence = plot.** Spectra from the same plot never appear in both training and test data.
* **No leakage.** MSC reference, date normalisation, NDSI search, feature selection and hyper-parameter tuning are fitted on training plots only (nested CV).
* **Imbalance (1 : 5.2).** Class weights or random oversampling inside training folds; balanced accuracy, MCC, kappa and macro-F1 reported.
* **Labels.** The plot label in the source workbooks (plots 1-12 healthy, 13-48 diseased). Severity and leaf-layer fields were empty, so severity models were not fitted.
