"""Slide-ready PNG figures for RQ1 / RQ2. Run after rq1_diffusion.py, rq2_features.py, rq2_trajectories.py."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np, pandas as pd, networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from analysis_common import RESULTS, FIGURES

FIGURES.mkdir(exist_ok=True)
BLUE, ORANGE, AQUA, GRAY, LIGHT = '#2a78d6', '#eb6834', '#1baf7a', '#8a8984', '#d9d8d4'
INK, INK2 = '#0b0b0b', '#52514e'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11, 'axes.edgecolor': LIGHT, 'axes.labelcolor': INK2,
                     'xtick.color': INK2, 'ytick.color': INK2, 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.grid': True, 'grid.color': '#eeedea', 'grid.linewidth': 0.8, 'axes.axisbelow': True,
                     'figure.dpi': 150, 'savefig.bbox': 'tight', 'axes.titleweight': 'bold', 'axes.titlesize': 13,
                     'axes.titlelocation': 'left', 'figure.facecolor': 'white'})
rq1 = json.load(open(RESULTS / 'rq1.json')); rq2 = json.load(open(RESULTS / 'rq2.json'))
SS0, SS1 = rq1['ss']['first_year'], rq1['ss']['last_year']

def save(fig, name):
    fig.savefig(FIGURES / name); plt.close(fig)

# 1. Oceanus Folk releases and share of all releases, by year (two panels: no dual axis)
s = pd.read_csv(RESULTS / 'of_share_by_year.csv').set_index('year')
s = s[s.index >= 1990]
fig, (a, b) = plt.subplots(2, 1, figsize=(10, 6), sharex=True, gridspec_kw={'hspace': 0.25})
a.bar(s.index, s['of'], color=BLUE, width=0.8)
a.set_title('Oceanus Folk releases per year'); a.set_ylabel('Songs + albums')
roll = s['of'].rolling(5, center=True, min_periods=3).sum() / s['total'].rolling(5, center=True, min_periods=3).sum()
b.plot(s.index, roll * 100, color=BLUE, lw=2)
b.set_title('Oceanus Folk share of all releases (5-yr rolling)'); b.set_ylabel('% of releases')
for ax in (a, b):
    ax.axvspan(SS0 - 0.5, SS1 + 0.5, color=AQUA, alpha=0.10, lw=0)
a.text(SS0, a.get_ylim()[1] * 0.92, f" Sailor Shift active {SS0}-{SS1}", color=INK2, fontsize=9)
b.text(1990, -12, 'Note: total releases in the data fall sharply after 2030, so the 2030s share rests on fewer works.', fontsize=8, color=INK2,
       transform=b.transData)
save(fig, '01_oceanus_folk_over_time.png')

# 2. Who Oceanus Folk influenced vs. who influenced it (direction-corrected)
out = pd.Series(rq1['flows']['outward_by_genre']); inn = pd.Series(rq1['flows']['inward_by_genre'])
g = pd.concat([out.rename('out'), inn.rename('in')], axis=1).fillna(0)
g = g.loc[(g.out + g['in']).sort_values(ascending=True).index[-12:]]
fig, ax = plt.subplots(figsize=(10, 6))
y = np.arange(len(g))
ax.barh(y, g.out, color=BLUE, height=0.7, label='Oceanus Folk -> genre (OF influenced it)')
ax.barh(y, -g['in'], color=ORANGE, height=0.7, label='Genre -> Oceanus Folk (it influenced OF)')
ax.set_yticks(y, g.index); ax.axvline(0, color=INK2, lw=0.8)
ax.set_xlabel('Influence edges (covers, samples, interpolations, style, lyrical references)')
ax.set_title('Oceanus Folk influence flows, top 12 genres')
ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f'{abs(int(v))}'))
ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.12), ncol=2, frameon=False, fontsize=9)
for i, (o, n) in enumerate(zip(g.out, g['in'])):
    ax.text(o + 1, i, f'{int(o)}', va='center', fontsize=8, color=INK2)
    ax.text(-n - 1, i, f'{int(n)}', va='center', ha='right', fontsize=8, color=INK2)
save(fig, '02_genre_influence_flows.png')

# 3. Outward spread over time, by whether it traces back to Sailor Shift
ts = pd.read_csv(RESULTS / 'of_outward_by_year_via.csv').set_index('year')
ts = ts.reindex(range(2000, 2041), fill_value=0)
cols = [c for c in ['Sailor Shift / Ivy Echos', 'Her collaborators', 'Independent of her network'] if c in ts]
colors = {'Sailor Shift / Ivy Echos': ORANGE, 'Her collaborators': AQUA, 'Independent of her network': BLUE}
fig, ax = plt.subplots(figsize=(10, 4.8))
bottom = np.zeros(len(ts))
for c in reversed(cols):
    ax.bar(ts.index, ts[c], bottom=bottom, color=colors[c], width=0.8, label=c, edgecolor='white', linewidth=1)
    bottom += ts[c].values
ax.axvspan(SS0 - 0.5, SS1 + 0.5, color=AQUA, alpha=0.08, lw=0)
ax.set_title('New works borrowing from Oceanus Folk outside the genre, per year')
ax.set_ylabel('Influence edges'); ax.legend(frameon=False, fontsize=9, loc='upper left')
f = rq1['flows']
n_ss = f['outward_by_via'].get('Sailor Shift / Ivy Echos', 0)
n_ss_dated = int(ts.get('Sailor Shift / Ivy Echos', pd.Series(dtype=int)).sum())
ax.set_ylim(0, ax.get_ylim()[1] * 1.15)
fig.text(0.01, -0.04, f"Only {n_ss} of {f['of_outward_total']} outward edges trace to Sailor Shift / Ivy Echos. {n_ss - n_ss_dated} of those link artist or band "
         "nodes rather than dated works, so they can't be placed on the timeline.", fontsize=9, color=INK2)
save(fig, '03_outward_spread_attribution.png')

# 4. Sailor Shift ego network (collaborators via shared works)
ego = json.load(open(RESULTS / 'ss_ego.json'))
G = nx.Graph()
for n in ego['nodes']: G.add_node(n['id'], **n)
for l in ego['links']: G.add_edge(l['s'], l['t'], w=l.get('w', 1), kind=l['type'])
fa = pd.read_csv(RESULTS / 'artist_features.csv').set_index('id')
pos = nx.spring_layout(G, seed=4, k=0.55, weight='w')
fig, ax = plt.subplots(figsize=(9, 8)); ax.axis('off'); ax.grid(False)
cc = [(u, v) for u, v, d in G.edges(data=True) if d['kind'] == 'CoCredited']
sp = [(u, v) for u, v, d in G.edges(data=True) if d['kind'] != 'CoCredited']
nx.draw_networkx_edges(G, pos, edgelist=cc, ax=ax, edge_color='#9fc3ee', width=0.5, alpha=0.6)
nx.draw_networkx_edges(G, pos, edgelist=sp, ax=ax, edge_color=LIGHT, width=[0.6 + G[u][v]['w'] * 0.7 for u, v in sp])
role_c = {'center': ORANGE, 'group': AQUA, 'collaborator': BLUE, 'label': GRAY}
for role, c in role_c.items():
    ns = [n for n, d in G.nodes(data=True) if d['role'] == role]
    if not ns: continue
    sz = [900 if role == 'center' else 260 if role == 'group' else 40 + 45 * G[ego['nodes'][0]['id']][n].get('w', 1) for n in ns]
    nx.draw_networkx_nodes(G, pos, nodelist=ns, node_color=c, node_size=sz, ax=ax, edgecolors='white', linewidths=1,
                           label={'center': 'Sailor Shift', 'group': 'Her band (Ivy Echos)', 'collaborator': 'Collaborator', 'label': 'Record label'}[role])
top = sorted([(G[ego['nodes'][0]['id']][n]['w'], n) for n in G.neighbors(ego['nodes'][0]['id'])], reverse=True)[:9]
labels = {n: G.nodes[n]['name'] for _, n in top}; labels[ego['nodes'][0]['id']] = 'Sailor Shift'
for gid in [n for n, d in G.nodes(data=True) if d['role'] == 'group']: labels[gid] = G.nodes[gid]['name']
nx.draw_networkx_labels(G, pos, labels, font_size=8, ax=ax, font_color=INK)
ax.set_title(f"Sailor Shift's collaboration network: {rq1['ss']['n_collaborators']} collaborators on {rq1['ss']['n_works_incl_group']} works\n(blue lines = collaborators credited together)", fontsize=12)
ax.legend(frameon=False, loc='lower left', fontsize=9, markerscale=0.6)
save(fig, '04_sailor_shift_ego_network.png')

# 5. Sailor Shift's output by year
sy = pd.read_csv(RESULTS / 'ss_works_by_year.csv').astype({'year': int}).set_index('year').reindex(range(SS0, SS1 + 1), fill_value=0)
fig, ax = plt.subplots(figsize=(10, 3.8))
ax.bar(sy.index, sy.notable, color=BLUE, width=0.8, label='Notable', edgecolor='white', linewidth=1)
ax.bar(sy.index, sy.works - sy.notable, bottom=sy.notable, color=LIGHT, width=0.8, label='Not notable', edgecolor='white', linewidth=1)
ax.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(2)); ax.set_title('Sailor Shift releases per year (solo + Ivy Echos)'); ax.set_ylabel('Works'); ax.legend(frameon=False, fontsize=9)
save(fig, '05_sailor_shift_career.png')

# 6. RQ2: sustained stars vs viral spikes, small multiples
gr = pd.read_csv(RESULTS / 'rq2_groups.csv')
panels = [('degree', 'Collaborators (degree)', False), ('betweenness', 'Betweenness (log scale)', True),
          ('clustering', 'Clustering coefficient', False), ('major_producer_ties', 'Ties to major producers', False)]
fig, axs = plt.subplots(1, 4, figsize=(13, 4.2))
rng = np.random.default_rng(0)
for ax, (col, title, log) in zip(axs, panels):
    for i, (grp, c) in enumerate([('Sustained star', BLUE), ('Viral spike', ORANGE)]):
        v = gr[gr.group == grp][col].astype(float)
        if log: v = np.log10(v + 1e-7)
        ax.scatter(i + rng.uniform(-0.18, 0.18, len(v)), v, s=8, color=c, alpha=0.35, lw=0)
        ax.hlines(v.median(), i - 0.3, i + 0.3, color=INK, lw=2)
    ax.set_xticks([0, 1], ['Sustained', 'Viral']); ax.set_title(title, fontsize=11)
    if log: ax.set_yticks([-7, -6, -5, -4, -3, -2], ['0', '1e-6', '1e-5', '1e-4', '1e-3', '1e-2'])
fig.suptitle(f"Network position: sustained stars (n={rq2['n_sustained']}) vs viral spikes (n={rq2['n_viral']})  -  black line = median",
             x=0.01, ha='left', fontweight='bold', fontsize=13)
fig.tight_layout()
save(fig, '06_sustained_vs_viral.png')

# 7. Candidate next Oceanus Folk stars
cd = pd.DataFrame(rq2['top_candidates']).iloc[::-1]
fig, ax = plt.subplots(figsize=(9, 4.6))
ax.barh(cd.name, cd.score, color=BLUE, height=0.6)
for i, r in enumerate(cd.itertuples()):
    ax.text(r.score + 0.01, i, f"{int(r.first_year)}-{int(r.last_year)} · {int(r.n_works)} works · {int(r.degree)} collaborators", va='center', fontsize=8, color=INK2)
ax.set_xlim(0, 1.35); ax.set_xlabel('Rising-star score (sustained-profile probability x momentum x influence)')
ax.set_title('Early-career Oceanus Folk artists with a "sustained star" network profile')
save(fig, '07_next_oceanus_folk_stars.png')
print('figures ->', FIGURES)
