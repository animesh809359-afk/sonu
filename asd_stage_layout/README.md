# Stage-wise plot arrangement of the ASD leaf-spectra dataset (IARI 2025-26)

| File | Content |
|---|---|
| `White_Rust_ASD_Stagewise_Plot_Arrangement.pptx` | 14-slide deck: field layout, stage calendar, stage map for each assessment date, the three stage datasets, spectra counts, diseased − healthy spectra, date offset, modelling workflow, data issues. |
| `Stage_wise_plot_index.xlsx` | All 192 plot-dates by stage with treatment, replication, spectra count and file range; yellow column to enter plot DI, with DI class computed automatically. |
| `deck_data.json` | Summary values derived from the four ASD files and `treatment_detail.xlsx` (no raw spectra). |
| `build_deck.js`, `build_index.py` | Rebuild: `node build_deck.js deck_data.json out.pptx <pptx-skill>/scripts/apply_theme.js`; `python build_index.py deck_data.json out.xlsx`. |
