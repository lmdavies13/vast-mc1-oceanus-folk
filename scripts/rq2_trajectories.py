"""RQ2: what separates sustained stars from viral spikes, and who is next for Oceanus Folk."""
import json
import numpy as np, pandas as pd
from scipy.stats import mannwhitneyu
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score

import sys; sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
from analysis_common import RESULTS
OUT = str(RESULTS) + '/'
df = pd.read_csv(OUT + 'artist_features.csv')
df['log_btw'] = np.log10(df.betweenness + 1e-7)
df['in_main_component'] = df.in_main_component.astype(int)

# Population: artists whose work others borrowed from at least 10 times ("successful")
pop = df[df.infl_received >= 10].copy()
sustained = (pop.influential_works >= 3) & (pop.span >= 6)
viral = (pop.top_work_share >= 0.8) & (pop.span <= 3)
pop['group'] = np.where(sustained, 'Sustained star', np.where(viral, 'Viral spike', 'Other'))
grp = pop[pop.group != 'Other']
grp.to_csv(OUT + 'rq2_groups.csv', index=False)

FEATS = {'degree': 'Collaborators (degree)', 'betweenness': 'Betweenness (bridging)', 'clustering': 'Clustering (closed clique)',
         'core': 'k-core (embeddedness)', 'major_producer_ties': 'Ties to major producers', 'in_main_component': 'In main network component'}
cmp = []
for f, label in FEATS.items():
    s, v = grp[grp.group == 'Sustained star'][f], grp[grp.group == 'Viral spike'][f]
    cmp.append({'feature': label, 'sustained_median': float(s.median()), 'sustained_mean': float(s.mean()),
                'viral_median': float(v.median()), 'viral_mean': float(v.mean()), 'p_value': float(mannwhitneyu(s, v).pvalue)})
res = {'population': int(len(pop)), 'n_sustained': int(sustained.sum()), 'n_viral': int(viral.sum()), 'comparison': cmp,
       'share_btw_positive': {'sustained': float((grp[grp.group == 'Sustained star'].betweenness > 0).mean()),
                              'viral': float((grp[grp.group == 'Viral spike'].betweenness > 0).mean())},
       'share_major_producer': {'sustained': float((grp[grp.group == 'Sustained star'].major_producer_ties > 0).mean()),
                                'viral': float((grp[grp.group == 'Viral spike'].major_producer_ties > 0).mean())}}

# Classifier on network-position features only (not span / works, which define the groups)
X_cols = ['log_btw', 'clustering', 'major_producer_ties', 'in_main_component', 'degree']
X = grp[X_cols].values; y = (grp.group == 'Sustained star').astype(int).values
sc = StandardScaler().fit(X)
clf = LogisticRegression(max_iter=1000).fit(sc.transform(X), y)
res['model'] = {'cv_accuracy': float(cross_val_score(LogisticRegression(max_iter=1000), sc.transform(X), y, cv=5).mean()),
                'baseline_accuracy': float(max(y.mean(), 1 - y.mean())),
                'std_coefficients': dict(zip(X_cols, map(float, clf.coef_[0])))}

# Prediction: early-career Oceanus Folk artists, scored by how "sustained-like" their network position is
of = df[(df.of_share >= 0.5) & (df.first_year >= 2020) & (df.last_year >= 2028) & (df.n_works >= 2) & (df.name != 'Sailor Shift')].copy()
of['sustained_prob'] = clf.predict_proba(sc.transform(of[X_cols].values))[:, 1]
of['momentum'] = of.n_works / of.span
of['score'] = of.sustained_prob * (0.5 + 0.5 * of.momentum.clip(upper=2) / 2) * (1 + np.log1p(of.infl_received) / 5)
cand = of.sort_values('score', ascending=False)
# Members of one band share identical credits, so they score identically: collapse them into one row
sig = ['n_works', 'first_year', 'last_year', 'degree', 'infl_received']
cand['members'] = cand.groupby(sig)['name'].transform(lambda s: ', '.join(s))
cand['is_group'] = cand.type.eq('MusicalGroup')
cand = cand.sort_values(['score', 'is_group'], ascending=False).drop_duplicates(sig)
cand.to_csv(OUT + 'of_candidates.csv', index=False)
res['n_candidates_pool'] = int(len(of))
res['top_candidates'] = cand.head(8)[['name', 'type', 'n_works', 'n_notable', 'first_year', 'last_year', 'infl_received', 'degree',
                                      'betweenness', 'clustering', 'major_producer_ties', 'in_main_component', 'roles', 'members', 'sustained_prob', 'score']].to_dict('records')
ss = df[df.name == 'Sailor Shift'].iloc[0]
res['sailor_shift_profile'] = {k: (float(ss[k]) if isinstance(ss[k], (int, float, np.number)) else ss[k]) for k in
                               ['degree', 'betweenness', 'clustering', 'core', 'major_producer_ties', 'in_main_component', 'infl_received', 'n_works', 'span']}
res['sailor_shift_profile']['sustained_prob'] = float(clf.predict_proba(sc.transform(df[df.name == 'Sailor Shift'][X_cols].values))[0, 1])
json.dump(res, open(OUT + 'rq2.json', 'w'), indent=1, default=str)
print(json.dumps(res, indent=1, default=str))
