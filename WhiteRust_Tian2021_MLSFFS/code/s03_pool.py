import sys, pickle, time, numpy as np, pandas as pd
sys.path.insert(0, '.')
from mlsffs import *
feats, y, _ = pickle.load(open(sys.argv[1], 'rb'))
P = build_pool(feats, y)
print('pre-VIF', len(P['pool_pre_vif']), 'post-VIF', len(P['pool']), 'plain', len(P['pool_plain_vif']))
r = P['reps'].set_index('feature')
for n in P['pool']: print(f"{n[:50]:52s} {r.loc[n,'family']:4s} BA={r.loc[n,'mean_BA']:.3f} VIF={P['vif_log'][-1]['vif'][n]:.2f}")
pickle.dump(P, open(sys.argv[2], 'wb'))
# timing of SFFS for one repetition
d = DATES[2]; X = date_matrix(feats, d, P['pool']).values; yy = y[d]
for clf in ['LDA', 'kNN', 'SVM']:
    t = time.time(); r_ = sffs(X, yy, [strat_folds(yy, 4, 0)], clf, 'OA', False, 8)
    print(clf, round(time.time() - t, 1), 's', r_['subset'], round(r_['score'], 3), r_['metrics'], r_['n_eval'])
