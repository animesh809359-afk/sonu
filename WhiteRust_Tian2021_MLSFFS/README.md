# White rust of mustard – ML-SFFS after Tian et al. (2021)

Step-by-step application and critical re-evaluation of the methodology of
Tian, L. et al. (2021) *Spectroscopic detection of rice leaf blast infection from asymptomatic to mild stages with
integrated machine learning and feature selection*, Remote Sensing of Environment 257, 112350,
on the plot-average raw reflectance (and the continuum-removal, vegetation-index, derivative and red-edge features derived from it)
of 48 mustard plots measured on 4 dates (T1 = 11 Feb, T2 = 24 Feb, T3 = 3 Mar, T4 = 13 Mar 2026).

## Files

| File | Content |
|---|---|
| `WhiteRust_ML-SFFS_TianMethod_Analysis.xlsx` | 25 sheets, one per step (S00 contents … S24 references). Green cells are live Excel formulas that recompute class means, threshold accuracies and summary accuracies (0 formula errors; identical to the Python values). |
| `WhiteRust_ML-SFFS_TianMethod_Thesis_Chapter.docx` | Thesis chapter: introduction, materials, methods (concept, equations, procedure for every step), results with 17 tables and 16 figures, discussion, limitations, conclusions, verified references. Update the table of contents in Word (right-click → Update field). |
| `WhiteRust_ML-SFFS_TianMethod_Slides.pptx` | 26 slides following the same steps. |
| `figures/` | All figures (PNG, 200 dpi). |
| `code/` | Python / JavaScript that reproduce every number (run order below). |

## Steps

| Step | Tian et al. (2021) | This study | Excel sheets |
|---|---|---|---|
| 1 | Data preparation | QC, guard zones (C1), CWT, treatment design and confounds (C9) | S04–S05 |
| 2 | Biochemistry tests | Index proxies (C8), same test rule + BH-FDR (C7) | S06–S07 |
| 3 | Thresholding separability, scalograms | Same, balanced accuracy (C2) | S08–S11 |
| 4 | Top 5 % → intersection → representatives; SI top-10 union | Same with explicit consistency level k* (C3) | S12 |
| 5 | VIF < 10 | Relevance-aware iterative VIF (C5) | S13–S14 |
| 6A | ML-SFFS (LDA, k-NN, SVM), 4-fold CV × 100 | Identical replication | S15–S17 |
| 6B | – | Nested CV (whole pipeline inside outer folds) (C4) | S18 |
| 6C | – | Label-permutation null | S19 |
| 6D | OA per infection stage (DAI) | Controls vs each inoculation timing D1–D4 per date | S20 |
| 7 | – | Formula checks, independent recomputation, reference verification | S21–S24 |

## Key results

* 19,548 candidate features per date → 16 disease-specific spectral features (DSSFs) with VIF < 10.
* Paper-faithful ML-SFFS (procedure A): 1–4 features, mean OA 94.9–100 %; SVM-SFFS best.
* Nested cross-validation (procedure B, to be reported as the accuracy of the method): balanced accuracy 83.5–98.8 %, OA 86.0–99.0 %.
* Optimism of procedure A: 1.2–14.1 percentage points (BA); with shuffled labels procedure A still reports 85.1–91.7 % OA.
* Cross-checks: 18 PASS, 3 FLAG (control block measured first; duplicated indices in the source workbooks; optimism of procedure A).

## Reproduce

Input: the four `WhiteRust_Mustard_PlotAverage_Features_<date>.xlsx` workbooks and `treatment_detail.xlsx` (not stored here).
Python 3.13 with numpy, pandas, scipy, statsmodels, scikit-learn 1.9, PyWavelets 1.10, matplotlib, openpyxl; Node 22 with `docx` and `pptxgenjs`.

```
python s01_load.py <data_dir> <scratch>/out/cache.pkl
python s02_explore.py <scratch>/out/cache.pkl <scratch>/out/feats.pkl
python s03_pool.py <scratch>/out/feats.pkl <scratch>/out/pool_full.pkl
python s04_run.py feats.pkl pool_full.pkl res_faithful.pkl faithful 100
python s04_run.py feats.pkl pool_full.pkl res_nested.pkl nested 10
python s04_run.py feats.pkl pool_full.pkl res_perm_ldaknn.pkl perm 5 20 LDA,kNN 0
python s04_run.py feats.pkl pool_full.pkl res_perm_svm.pkl perm 2 4 SVM 100
python s05_physio.py cache.pkl physio.pkl
python s00_treatment.py treatment_detail.xlsx <scratch>/out/treatment.pkl
python s08_stage.py <scratch> 100
python s06_figs_a.py <scratch>; python s07_summarize.py <scratch>; python s10_crosscheck.py <scratch>; python s09_figs_b.py <scratch>
python s11_excel.py <scratch> Analysis.xlsx; python s12_doc.py <scratch> doc.json; node render_docx.js doc.json Chapter.docx
python s13_pptdata.py <scratch>; node s14_pptx.js <scratch> Slides.pptx <pptx-skill-dir>
```
(The treatment table is read from `treatment_detail.xlsx` into `out/treatment.pkl`; columns Plot, Inoculation, Variety_t, Replication.)
