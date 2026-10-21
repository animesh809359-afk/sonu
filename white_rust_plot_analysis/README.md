# White rust of Indian mustard - plot-level discrimination

Healthy (12 control) vs diseased (36 inoculated) plots from plot-average ASD contact-probe spectra
(48 plots x 4 dates = 192 plot-dates) and the features derived from them.

## Run order
```
python -I scripts/p01_load.py <treatment_detail.xlsx> <PlotAverage_Features_11-02-2026.xlsx> ... <..._13-03-2026.xlsx>
python scripts/p02_explore.py            # QC, characterisation, screening, LMM, design checks, PCA, PERMANOVA, index search
python scripts/p03_cv.py 20 main         # main nested cell-grouped CV (12 scenarios x 10 classifiers)
python scripts/p05_summarise.py          # summary, statistics, best models, final features
python scripts/p04_experiments.py E1 E2 E3 E4 E5 E6 E7 E8 E9
python scripts/p06_figures.py
python scripts/p07_excel.py              # outputs/WhiteRust_Mustard_PlotLevel_Analysis.xlsx
python scripts/p08_export.py && python scripts/p09_narrative.py
NODE_PATH=$(npm root -g) node scripts/build_ppt.js   # outputs/WhiteRust_Mustard_PlotLevel_PhD_Seminar.pptx
```
Classifiers, selection procedures and metrics are imported from `../white_rust_analysis/scripts` (leaf-level chapter);
E9 re-uses its cached leaf spectra. `cache/` is not versioned.
