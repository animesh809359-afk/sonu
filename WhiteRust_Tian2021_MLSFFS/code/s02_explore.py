import sys, pickle, numpy as np, pandas as pd, time
sys.path.insert(0, '.')
from mlsffs import *
c = pickle.load(open(sys.argv[1], 'rb'))
t = time.time()
feats = {d: build_features(c[d]) for d in DATES}
y = {d: (c[d]['meta'].Class == 'Diseased').astype(int).values for d in DATES}
print('build', time.time() - t, {f: feats[DATES[0]][f].shape[1] for f in feats[DATES[0]]})
sep = {}
for d in DATES:
    for f in feats[d]:
        X = feats[d][f]
        X = X.loc[:, X.std() > 0]
        s = threshold_separability(X.values, y[d]); s.index = X.columns
        sep[(d, f)] = s
print('sep', time.time() - t)
for f in SPECTRAL_FAMS:
    cnt = sum(top_fraction(sep[(d, f)].BA.values, 0.05).astype(int) for d in DATES)
    cnt = pd.Series(cnt, index=sep[(DATES[0], f)].index)
    print(f, 'n', len(cnt), 'in all 4:', (cnt == 4).sum(), '>=3:', (cnt >= 3).sum(), '>=2', (cnt >= 2).sum(),
          [round(sep[(d, f)].BA.quantile(.95), 3) for d in DATES])
    if (cnt == 4).sum(): print('   all4', list(cnt[cnt == 4].index)[:40])
    print('   >=3', list(cnt[cnt >= 3].index)[:60])
for f in SCALAR_FAMS:
    for d in DATES:
        s = sep[(d, f)].sort_values('BA', ascending=False)
        print(f, d, [(n[:28], round(v, 3)) for n, v in s.BA.head(8).items()])
pickle.dump((feats, y, sep), open(sys.argv[2], 'wb'))
