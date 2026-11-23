# VAST 2025 MC1 — Oceanus Folk Network Analysis

ISTE-782 (Visual Analytics) final project. Python data-prep layer: load the
graph, compute metrics, carve out subgraphs — then hand off to Tableau/Gephi
for the actual visualizations.

## Setup

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Dataset

`data/MC1_graph.json` — VAST Challenge 2025 Mini-Challenge 1 synthetic
music-industry knowledge graph. 17,412 nodes / 37,857 edges.

- **Node types** (`Node Type` attr): Person (11,361), Song (3,615),
  RecordLabel (1,217), Album (996), MusicalGroup (223)
- **Edge types** (`Edge Type` attr): PerformerOf, RecordedBy, ComposerOf,
  ProducerOf, DistributedBy, LyricistOf, InStyleOf, InterpolatesFrom,
  LyricalReferenceTo, CoverOf, DirectlySamples, MemberOf
- `genre` is a string attribute on Song/Album nodes only — not its own node
  type. `notable` (bool) and `notoriety_date` sit on Song/Album nodes too.
- Node ids are ints; look nodes up by the `name` attribute
  (`scripts/load_graph.py::find_node_by_name`).

## Research questions

1. **Diffusion** — how did Sailor Shift's ego network + cross-genre
   collaborations drive Oceanus Folk's spread into mainstream genres?
2. **Career trajectory** — which network-topology features distinguish
   sustained rising stars from viral spikes, and who's next for Oceanus
   Folk?

## scripts/load_graph.py

Shared loading/extraction helpers so nobody re-writes the same graph-load
code or hands Tableau/Gephi the full 17k-node graph:

- `load_graph()` — loads `data/MC1_graph.json` as an `nx.MultiDiGraph`
- `node_counts_by_type` / `edge_counts_by_type` — quick schema sanity check
- `find_node_by_name(g, name)` — look up a node id by display name
- `ego_subgraph(g, node_id, radius)` — bounded subgraph around a node
  (radius=1 for direct connections, higher for multi-hop)
- `genre_flow_edges(g)` — genre→genre influence-edge counts, direction
  preserved (feeds the Sankey-vs-chord-diagram decision)
- `centrality_table(g)` — degree + betweenness centrality (RQ2's "bridge
  ties" metric)

Run `python3 scripts/load_graph.py` directly for a schema printout, and it
also writes everything below to `output/` (gitignored — regenerate locally
with the same command rather than committing it):

- `nodes.csv` / `edges.csv` — full flat tables, every node/edge attribute as
  a column, source/target name+type joined into the edge table. The generic
  **drag-into-Tableau** export — filter by `Node Type`, `genre`,
  `release_date`, etc. once it's in.
- `genre_flow.csv` — genre→genre influence-edge counts, direction preserved.
  Feeds either a Sankey or chord diagram once that decision is made.
- `oceanus_folk_by_decade.csv` — release counts by decade, for the RQ1b line
  chart. (Matches the meeting-prep numbers through the 2030s, plus 3 more
  releases that land in the 2040s that weren't in the original note.)
- `centrality.csv` — degree + betweenness per node, with name/type joined
  in, for the RQ2 scatterplot.
- `sailor_shift_ego.graphml` — Sailor Shift's radius-1 ego network, for
  **Gephi**, not Tableau — Tableau has no native node-link/graph layout, so
  the ego-network visual belongs in Gephi (or a from-scratch D3/NetworkX
  plot), not a Tableau sheet.

## Analysis (RQ1 / RQ2)

Results, methods and caveats are written up in **[FINDINGS.md](FINDINGS.md)**.
Slide-ready charts are in `figures/`.

| Script | What it does | Writes |
|---|---|---|
| `scripts/analysis_common.py` | Tabular loader (pandas) + edge-type groups | — |
| `scripts/rq1_diffusion.py` | Sailor Shift's ego network (incl. Ivy Echos + collaborators via shared works), direction-corrected genre flows, attribution of Oceanus Folk's outward spread | `results/rq1.json`, `results/*.csv`, `output/sailor_shift_collab_ego.graphml` (Gephi), `output/influence_edges_resolved.csv` |
| `scripts/rq2_features.py` | Per-artist career + collaboration-network metrics (degree, betweenness, clustering, k-core, major-producer ties) | `results/artist_features.csv` (Tableau-ready) |
| `scripts/rq2_trajectories.py` | Sustained vs viral groups, significance tests, logistic model, next-star candidates | `results/rq2.json`, `results/rq2_groups.csv`, `results/of_candidates.csv` |
| `scripts/make_figures.py` | 7 PNG figures | `figures/` |

Run them in that order after `pip install -r requirements.txt`.

**Influence direction:** influence edges point borrower -> original, so
influence flows target -> source. `genre_flow_edges()` now returns
`from_genre` (influencer) -> `to_genre` (borrower), restricted to the five
influence edge types. Before this change it returned the raw edge direction,
which read backwards.

## Open items

- Sankey vs. chord diagram for the genre-flow visualization (`figures/02_genre_influence_flows.png` is a diverging bar stand-in; `results/genre_flow_matrix.csv` feeds either) — meeting notes
  leaned Sankey (direction matters), final proposal deck said chord. Pick
  one before building it.
- Confirm work split (who owns ego-network vs. genre-diffusion vs.
  rising-star) and "influence" definition (direct edges vs. derived) with
  the group.
