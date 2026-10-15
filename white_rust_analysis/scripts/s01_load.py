"""Step 1: assemble the four ASD contact-probe workbooks into one long table.
Excel AVERAGE columns (integer headers) are ignored; only raw .asd.sco spectra are used."""
import openpyxl, glob, sys, numpy as np, pandas as pd, os
SRC = sys.argv[1]; OUT = sys.argv[2]
DATES = {'110226': '2026-02-11', '240226': '2026-02-24', '030326': '2026-03-03', '130326': '2026-03-13'}
meta_rows, spectra = [], []
for f in sorted(glob.glob(os.path.join(SRC, '*asd__data*.xlsx'))):
    code = f.split('_')[-1][:6]
    rows = list(openpyxl.load_workbook(f, read_only=True).worksheets[0].iter_rows(values_only=True))
    first_wl = [i for i, r in enumerate(rows) if r[0] == 350][0]
    meta = {str(rows[i][0]).strip().lower(): rows[i] for i in range(1, first_wl)}
    wl = np.array([r[0] for r in rows[first_wl:]], dtype=int)
    X = rows[first_wl:]
    hdr = rows[0]
    for j, h in enumerate(hdr):
        if isinstance(h, str) and h.endswith('.sco'):
            spec = np.array([X[k][j] for k in range(len(X))], dtype=float)
            meta_rows.append(dict(file_id=h, date_code=code, date=DATES[code], plot=int(meta['plot no.'][j]),
                                  variety=meta['variety'][j], stage=meta['growth stage'][j],
                                  label=meta['healthy/diseased'][j]))
            spectra.append(spec)
M = pd.DataFrame(meta_rows); S = np.vstack(spectra)
M['spec_uid'] = M['date_code'] + '_' + M['file_id'].str.replace('.asd.sco', '', regex=False)
M['y'] = (M['label'] == 'Diseased').astype(int)
M['plot_date'] = M['plot'].astype(str) + '_' + M['date_code']
# within plot-date order index (scan sequence)
M['scan_in_group'] = M.groupby('plot_date').cumcount() + 1
np.savez_compressed(os.path.join(OUT, 'raw.npz'), X=S, wl=wl)
M.to_csv(os.path.join(OUT, 'meta.csv'), index=False)
print(M.shape, S.shape, wl[0], wl[-1], np.isnan(S).sum())
print(M.groupby(['date', 'label']).size().unstack())
