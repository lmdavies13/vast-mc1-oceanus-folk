"""RQ2: per-artist career and network features."""
import sys, json, collections, itertools
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
import numpy as np, pandas as pd, networkx as nx
from analysis_common import load, works_of, INFLUENCE, RESULTS

OUT = str(RESULTS) + '/'
g, nodes, edges = load()
W = nodes[nodes['Node Type'].isin(['Song', 'Album'])]
aw, cre = works_of(nodes, edges)
artists = [a for a in aw if nodes.loc[a, 'Node Type'] in ('Person', 'MusicalGroup')]

# Influence received: influence flows target -> source, so an artist "receives" when their work/self is a target
inf = edges[edges['Edge Type'].isin(INFLUENCE)]
recv = inf.groupby('target').size()
recv_years = inf.assign(y=inf.source.map(W['year'])).groupby('target')['y'].apply(list)

# Collaboration graph: artists linked when credited on the same work
work_artists = cre.groupby('target')['source'].apply(lambda s: sorted(set(s)))
C = nx.Graph()
C.add_nodes_from(artists)
first_collab_year = {}
for w, arts in work_artists.items():
    y = W.year.get(w)
    for a, b in itertools.combinations(arts, 2):
        if C.has_edge(a, b):
            C[a][b]['w'] += 1
        else:
            C.add_edge(a, b, w=1)
            first_collab_year[(a, b)] = y
        first_collab_year[(a, b)] = min(first_collab_year.get((a, b), y) or y, y or 9999)

print('collab graph', C.number_of_nodes(), C.number_of_edges())
deg = dict(C.degree())
btw = nx.betweenness_centrality(C, k=1500, seed=7)
core = nx.core_number(C)
clust = nx.clustering(C)
comp = {n: i for i, cc in enumerate(sorted(nx.connected_components(C), key=len, reverse=True)) for n in cc}

# "Major producers": top 2% of producers by number of works produced
prod = cre[cre['Edge Type'] == 'ProducerOf'].groupby('source').target.nunique()
major = set(prod[prod >= prod.quantile(0.98)].index)

rows = []
for a in artists:
    ws = list(aw[a])
    wy = W.loc[ws]
    ys = wy.year.dropna().astype(int)
    rec_by_work = recv.reindex(ws).fillna(0)
    total_recv = rec_by_work.sum() + recv.get(a, 0)
    nbrs = set(C.neighbors(a))
    # degree growth: new collaborators per active year
    cy = [first_collab_year.get((min(a, b), max(a, b))) or first_collab_year.get((a, b)) or first_collab_year.get((b, a)) for b in nbrs]
    cy = [y for y in cy if y and y < 9999]
    rows.append({
        'id': a, 'name': nodes.loc[a, 'name'], 'type': nodes.loc[a, 'Node Type'],
        'n_works': len(ws), 'n_notable': int(wy.notable.sum()), 'n_charted': int(wy.notoriety_year.notna().sum()),
        'first_year': ys.min() if len(ys) else np.nan, 'last_year': ys.max() if len(ys) else np.nan,
        'active_years': ys.nunique(), 'main_genre': wy.genre.mode().iloc[0] if len(wy) else None,
        'of_share': (wy.genre == 'Oceanus Folk').mean() if len(wy) else 0,
        'infl_received': int(total_recv),
        'top_work_share': float(rec_by_work.max() / total_recv) if total_recv else np.nan,
        'influential_works': int((rec_by_work > 0).sum()),
        'influential_span': (int(wy.loc[rec_by_work[rec_by_work > 0].index].year.max() - wy.loc[rec_by_work[rec_by_work > 0].index].year.min())
                             if (rec_by_work > 0).sum() else np.nan),
        'degree': deg.get(a, 0), 'betweenness': btw.get(a, 0), 'core': core.get(a, 0), 'clustering': clust.get(a, 0),
        'in_main_component': comp.get(a) == 0,
        'major_producer_ties': len(nbrs & major), 'roles': ','.join(sorted(cre[cre.source == a]['Edge Type'].str.replace('Of', '').unique())),
        'collab_first_years': cy,
    })
df = pd.DataFrame(rows)
df['span'] = df.last_year - df.first_year + 1
df['works_per_year'] = df.n_works / df.span
# Rate of new collaborators: in first half vs second half of career
def growth(r):
    if r.span < 4 or not r.collab_first_years:
        return np.nan
    mid = r.first_year + r.span / 2
    a = sum(1 for y in r.collab_first_years if y < mid); b = len(r.collab_first_years) - a
    return (b - a) / max(a + b, 1)
df['collab_growth'] = df.apply(growth, axis=1)
df.drop(columns='collab_first_years').to_csv(OUT + 'artist_features.csv', index=False)
print(df.describe().T.to_string())
print('major producers', len(major))
