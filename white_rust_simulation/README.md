# White rust of mustard: simulated parameter set (IARI New Delhi, rabi 2025-26)

**All values are SIMULATED / EXPECTED, not measured data.** Use them as hypotheses, sanity-check ranges, priors and synthetic data. Do not report them as observations.

| File | Content |
|---|---|
| `White_Rust_Simulated_Parameters_IARI_2025-26.xlsx` | Live-formula model. 12 treatments × 4 dates × 6 DI classes, 12 physiological/biochemical parameters, thermal indices, GLCM/colour changes. Start with `Quick_View` and `Stage_Comparison`; blue cells are editable inputs. |
| `White_Rust_Simulated_Parameters_Report_IARI_2025-26.docx` | Detailed report: context, weather, model, healthy-vs-severity comparison by stage and by date, thermal and texture parameters, plausibility, limitations, references, and 48 treatment × date tables. |
| `build_workbook.py` | `python build_workbook.py <weather.xlsx> <out.xlsx>`, then recalculate (LibreOffice) to fill cached values. |
| `White_Rust_Simulated_Dataset_Parameterwise_ASD_IARI_2025-26.xlsx` | One sheet per parameter (26 biophysical, biochemical and thermal parameters), each with 288 rows: date → treatment → severity class, giving mean, low, high and % change vs healthy. Also 288 simulated ASD leaf spectra (400–2500 nm, 1 nm), their PROSPECT-D inputs, and 14 spectral indices as formulas. |
| `build_dataset.py` | `python build_dataset.py <model.xlsx> <prospect_d_spectra.txt> <out.xlsx>`, then recalculate. The PROSPECT-D absorption file (Féret et al. 2017) ships with the `prosail` Python package and is not included here. |
| `ASD_simulated_spectra_preview.png` | Example simulated spectra, healthy to very high severity. |
| `report_data.json`, `build_report.js` | Values exported from the recalculated workbook; `node build_report.js report_data.json <out.docx>`. |
