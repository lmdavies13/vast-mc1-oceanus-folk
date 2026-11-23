"""RQ1: Sailor Shift's ego network and the diffusion of Oceanus Folk."""
import sys, json, collections
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
import pandas as pd
from analysis_common import load, works_of, CREATOR, INFLUENCE, LABEL, RESULTS, OUTPUT

OUT = str(RESULTS) + '/'
g, nodes, edges = load()
W = nodes[nodes['Node Type'].isin(['Song', 'Album'])]
artist_works, cre = works_of(nodes, edges)
OF = 'Oceanus Folk'
SS = int(nodes.index[nodes.name == 'Sailor Shift'][0])

# --- group membership and group-credited works
mem = edges[edges['Edge Type'] == 'MemberOf']
groups_of = mem.groupby('source')['target'].apply(set).to_dict()
members_of = mem.groupby('target')['source'].apply(set).to_dict()

# Dominant genre for person/group nodes (mode of their works' genres)
def dom_genre(aid):
    ws = artist_works.get(aid, set())
    gs = W.loc[list(ws), 'genre'] if ws else pd.Series(dtype=str)
    return gs.mode().iloc[0] if len(gs) else None

genre_of = W['genre'].to_dict()
for aid in nodes.index[nodes['Node Type'].isin(['Person', 'MusicalGroup'])]:
    if aid in artist_works:
        genre_of[aid] = dom_genre(aid)
year_of = W['year'].to_dict()

res = {}

# --- 1. Oceanus Folk share of releases over time
by_year = W.groupby('year').agg(total=('genre', 'size'), of=('genre', lambda s: (s == OF).sum()))
by_year['share'] = by_year['of'] / by_year['total']
by_year.to_csv(OUT + 'of_share_by_year.csv')
dec = W.assign(dec=(W.year // 10 * 10).astype(int)).groupby('dec').agg(total=('genre', 'size'), of=('genre', lambda s: (s == OF).sum()))
dec['share'] = (dec['of'] / dec['total']).round(4)
res['of_by_decade'] = dec.reset_index().to_dict('records')

# --- 2. Sailor Shift ego network
ss_works = set(artist_works[SS])
ss_groups = groups_of.get(SS, set())
ss_group_works = set().union(*[artist_works.get(gid, set()) for gid in ss_groups]) if ss_groups else set()
all_ss_works = ss_works | ss_group_works
collab = collections.Counter()
collab_roles = collections.defaultdict(set)
for w in all_ss_works:
    for s, et in cre[cre.target == w][['source', 'Edge Type']].values:
        if s != SS and s not in ss_groups:
            collab[s] += 1
            collab_roles[s].add(et.replace('Of', ''))
labels = edges[edges.source.isin(all_ss_works) & edges['Edge Type'].isin(LABEL)].target.value_counts()
ss_edges = edges[(edges.source == SS) | (edges.target == SS)]
res['ss'] = {
    'id': SS,
    'direct_edges': int(len(ss_edges)),
    'direct_neighbors': int(len(set(ss_edges.source) | set(ss_edges.target) - {SS})),
    'edge_types': ss_edges['Edge Type'].value_counts().to_dict(),
    'groups': [nodes.loc[x, 'name'] for x in ss_groups],
    'group_members': [nodes.loc[m, 'name'] for gid in ss_groups for m in members_of.get(gid, []) if m != SS],
    'n_works_personal': len(ss_works), 'n_works_incl_group': len(all_ss_works),
    'first_year': int(W.loc[list(all_ss_works), 'year'].min()), 'last_year': int(W.loc[list(all_ss_works), 'year'].max()),
    'genres': W.loc[list(all_ss_works), 'genre'].value_counts().to_dict(),
    'notable_works': int(W.loc[list(all_ss_works), 'notable'].sum()),
    'notoriety_years': W.loc[list(all_ss_works), 'notoriety_year'].dropna().astype(int).value_counts().sort_index().to_dict(),
    'n_collaborators': len(collab),
    'top_collaborators': [{'name': nodes.loc[a, 'name'], 'type': nodes.loc[a, 'Node Type'], 'shared_works': c,
                           'roles': sorted(collab_roles[a]), 'genre': genre_of.get(a)} for a, c in collab.most_common(15)],
    'labels': {nodes.loc[l, 'name']: int(c) for l, c in labels.items()},
}
ss_year = W.loc[list(all_ss_works)].groupby('year').agg(works=('name', 'size'), notable=('notable', lambda s: int(s.astype(bool).sum())))
ss_year.to_csv(OUT + 'ss_works_by_year.csv')

# --- 3. Influence edges, direction-corrected: influence flows TARGET -> SOURCE
inf = edges[edges['Edge Type'].isin(INFLUENCE)].copy()
inf['from_id'], inf['to_id'] = inf['target'], inf['source']          # influencer -> influenced
inf['from_genre'] = inf.from_id.map(genre_of)
inf['to_genre'] = inf.to_id.map(genre_of)
inf['year'] = inf.to_id.map(year_of)                                # when the borrowing work came out
inf['from_year'] = inf.from_id.map(year_of)

# Attribute each influencer node to Sailor Shift / her collaborators / independent
def owners(nid):
    t = nodes.loc[nid, 'Node Type']
    if t in ('Person', 'MusicalGroup'):
        return {nid}
    return set(cre[cre.target == nid].source)
ss_core = {SS} | ss_groups
ss_ring = set(collab)
own_cache = {}
def attribution(nid):
    if nid not in own_cache:
        o = owners(nid)
        own_cache[nid] = 'Sailor Shift / Ivy Echos' if o & ss_core else ('Her collaborators' if o & ss_ring else 'Independent of her network')
    return own_cache[nid]
inf['via'] = inf.from_id.map(attribution)

out_of = inf[(inf.from_genre == OF) & (inf.to_genre != OF) & inf.to_genre.notna()]
in_of = inf[(inf.to_genre == OF) & (inf.from_genre != OF) & inf.from_genre.notna()]
res['flows'] = {
    'of_outward_total': int(len(out_of)), 'of_inward_total': int(len(in_of)),
    'outward_by_genre': out_of.to_genre.value_counts().to_dict(),
    'inward_by_genre': in_of.from_genre.value_counts().to_dict(),
    'outward_by_via': out_of.via.value_counts().to_dict(),
    'outward_by_type': out_of['Edge Type'].value_counts().to_dict(),
}
# Genre-to-genre matrix for chord / heatmap (all cross-genre influence)
cross = inf[inf.from_genre.notna() & inf.to_genre.notna() & (inf.from_genre != inf.to_genre)]
cross.groupby(['from_genre', 'to_genre']).size().rename('n').reset_index().to_csv(OUT + 'genre_flow_matrix.csv', index=False)
# outward OF spread over time, split by attribution
ts = out_of.dropna(subset=['year']).groupby(['year', 'via']).size().unstack(fill_value=0)
ts.to_csv(OUT + 'of_outward_by_year_via.csv')
pre = out_of[out_of.year < 2023]; post = out_of[out_of.year >= 2023]
res['flows']['outward_before_2023'] = int(len(pre)); res['flows']['outward_2023_on'] = int(len(post))
res['flows']['outward_2023_on_by_via'] = post.via.value_counts().to_dict()
res['flows']['outward_genres_before_2023'] = int(pre.to_genre.nunique()); res['flows']['outward_genres_2023_on'] = int(post.to_genre.nunique())
# first year each genre was influenced by Oceanus Folk
first = out_of.dropna(subset=['year']).groupby('to_genre').year.min().sort_values()
res['flows']['first_year_reached'] = {k: int(v) for k, v in first.items()}

# Who Sailor Shift influenced / was influenced by (direct + via her works)
ss_nodes = ss_core | all_ss_works
infl_by_ss = inf[inf.from_id.isin(ss_nodes)]
infl_on_ss = inf[inf.to_id.isin(ss_nodes)]
res['ss_influence'] = {
    'influenced_edges': int(len(infl_by_ss)), 'influenced_genres': infl_by_ss.to_genre.value_counts().to_dict(),
    'influenced_by_edges': int(len(infl_on_ss)), 'influenced_by_genres': infl_on_ss.from_genre.value_counts().to_dict(),
    'top_influences_on_her': infl_on_ss.from_id.map(nodes['name']).value_counts().head(8).to_dict(),
    'top_influenced_by_her': infl_by_ss.to_id.map(lambda x: nodes.loc[x, 'name']).value_counts().head(8).to_dict(),
}
# Share of all OF outward influence 2023+ that carries her name
res['flows']['ss_share_of_outward_2023_on'] = round((post.via == 'Sailor Shift / Ivy Echos').mean(), 4)
res['flows']['network_share_of_outward_2023_on'] = round((post.via != 'Independent of her network').mean(), 4)

# --- 4. Ego graph export (1-hop collaborators, labels, groups; influence links)
ego = {'nodes': [], 'links': []}
def add(nid, role):
    ego['nodes'].append({'id': int(nid), 'name': nodes.loc[nid, 'name'], 'type': nodes.loc[nid, 'Node Type'], 'role': role})
add(SS, 'center')
for gid in ss_groups: add(gid, 'group'); ego['links'].append({'s': SS, 't': int(gid), 'type': 'MemberOf'})
for a, c in collab.items(): add(a, 'collaborator'); ego['links'].append({'s': SS, 't': int(a), 'type': 'Collaborated', 'w': c})
import itertools
pair_w = collections.Counter()
for w in all_ss_works:
    cs = sorted(set(cre[cre.target == w].source) & set(collab))
    for a, b in itertools.combinations(cs, 2):
        pair_w[(a, b)] += 1
for (a, b), c in pair_w.items(): ego['links'].append({'s': int(a), 't': int(b), 'type': 'CoCredited', 'w': c})
res['ss']['collaborator_pairs'] = len(pair_w)
for l, c in labels.items(): add(l, 'label'); ego['links'].append({'s': SS, 't': int(l), 'type': 'Label', 'w': int(c)})
json.dump(ego, open(OUT + 'ss_ego.json', 'w'))
import networkx as nx
OUTPUT.mkdir(exist_ok=True)
G = nx.Graph()
for n in ego['nodes']:
    G.add_node(n['id'], label=n['name'], node_type=n['type'], role=n['role'], genre=str(genre_of.get(n['id']) or ''))
for l in ego['links']:
    G.add_edge(l['s'], l['t'], edge_type=l['type'], weight=l.get('w', 1))
nx.write_graphml(G, OUTPUT / 'sailor_shift_collab_ego.graphml')
OUTPUT.mkdir(exist_ok=True)
inf.to_csv(OUTPUT / 'influence_edges_resolved.csv', index=False)
json.dump(res, open(OUT + 'rq1.json', 'w'), indent=1, default=str)
print(json.dumps(res, indent=1, default=str)[:9000])
