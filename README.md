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

Run `python3 scripts/load_graph.py` directly for a quick schema printout.

## Open items

- Sankey vs. chord diagram for the genre-flow visualization — meeting notes
  leaned Sankey (direction matters), final proposal deck said chord. Pick
  one before building it.
- Confirm work split (who owns ego-network vs. genre-diffusion vs.
  rising-star) and "influence" definition (direct edges vs. derived) with
  the group.
