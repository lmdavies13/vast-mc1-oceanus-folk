"""Shared graph-loading/extraction utilities for the VAST 2025 MC1 dataset.

Covers the data-prep step everyone needs before building their own
visualization (ego network, genre diffusion, or rising-star comparison):
load the graph, pull basic stats, and carve out bounded subgraphs so nobody
hands Tableau/Gephi a 17k-node hairball.
"""

import json
from pathlib import Path

import networkx as nx
import pandas as pd

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "MC1_graph.json"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"


def load_graph(path: Path = DATA_PATH) -> nx.MultiDiGraph:
    with open(path, "r") as f:
        data = json.load(f)
    return nx.node_link_graph(data, directed=True, multigraph=True, edges="links")


def node_counts_by_type(g: nx.MultiDiGraph) -> pd.Series:
    types = [attrs.get("Node Type") for _, attrs in g.nodes(data=True)]
    return pd.Series(types).value_counts()


def edge_counts_by_type(g: nx.MultiDiGraph) -> pd.Series:
    types = [attrs.get("Edge Type") for _, _, attrs in g.edges(data=True)]
    return pd.Series(types).value_counts()


def find_node_by_name(g: nx.MultiDiGraph, name: str) -> int | None:
    """Node ids in MC1_graph.json are ints, not the display name - look it up."""
    for node_id, attrs in g.nodes(data=True):
        if attrs.get("name") == name:
            return node_id
    return None


def ego_subgraph(g: nx.MultiDiGraph, node_id: int, radius: int = 1) -> nx.MultiDiGraph:
    """Bounded subgraph around a node - direct connections at radius=1,
    multi-hop at radius>1. Use this instead of ever laying out the full graph."""
    return nx.ego_graph(g.to_undirected(as_view=True), node_id, radius=radius)


INFLUENCE_EDGE_TYPES = {"InStyleOf", "InterpolatesFrom", "CoverOf", "LyricalReferenceTo", "DirectlySamples"}


def genre_flow_edges(g: nx.MultiDiGraph, genre_attr: str = "genre") -> pd.DataFrame:
    """Genre-to-genre influence counts, oriented in the direction influence FLOWS.

    In MC1 the influence edges point from the newer, borrowing work (source)
    to the work it borrows from (target) - e.g. "Song A -InStyleOf-> Song B"
    means B influenced A. So influence flows target -> source, and this
    function reverses each edge: `from_genre` is the influencing genre,
    `to_genre` the genre that borrowed from it. (An earlier version reported
    the raw source -> target direction, which reads backwards.)

    Only the five influence edge types are counted, and only between
    Song/Album nodes (the only nodes with a genre). For flows that also
    include artist/band nodes, see scripts/rq1_diffusion.py.
    """
    rows = []
    for u, v, attrs in g.edges(data=True):
        if attrs.get("Edge Type") not in INFLUENCE_EDGE_TYPES:
            continue
        borrower_genre = g.nodes[u].get(genre_attr)
        original_genre = g.nodes[v].get(genre_attr)
        if borrower_genre and original_genre and borrower_genre != original_genre:
            rows.append({"from_genre": original_genre, "to_genre": borrower_genre, "edge_type": attrs.get("Edge Type")})
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.groupby(["from_genre", "to_genre"]).size().reset_index(name="count").sort_values("count", ascending=False)


def node_table(g: nx.MultiDiGraph) -> pd.DataFrame:
    """Flat node table - one row per node, every attribute as a column.
    This is the generic 'throw it in Tableau' export: filter/join on
    Node Type, genre, release_date, notable, notoriety_date, etc."""
    rows = []
    for node_id, attrs in g.nodes(data=True):
        rows.append({"id": node_id, **attrs})
    return pd.DataFrame(rows)


def edge_table(g: nx.MultiDiGraph) -> pd.DataFrame:
    """Flat edge table with source/target name + type joined in, so Tableau
    doesn't need a separate join to the node table for basic filtering."""
    rows = []
    for u, v, attrs in g.edges(data=True):
        u_attrs, v_attrs = g.nodes[u], g.nodes[v]
        rows.append({
            "source_id": u,
            "source_name": u_attrs.get("name"),
            "source_type": u_attrs.get("Node Type"),
            "source_genre": u_attrs.get("genre"),
            "target_id": v,
            "target_name": v_attrs.get("name"),
            "target_type": v_attrs.get("Node Type"),
            "target_genre": v_attrs.get("genre"),
            "edge_type": attrs.get("Edge Type"),
        })
    return pd.DataFrame(rows)


def oceanus_folk_by_decade(g: nx.MultiDiGraph, genre: str = "Oceanus Folk") -> pd.DataFrame:
    """Release count by decade for a given genre - the RQ1b line chart data."""
    rows = []
    for _, attrs in g.nodes(data=True):
        if attrs.get("genre") != genre:
            continue
        release_date = attrs.get("release_date")
        if not release_date:
            continue
        year = int(str(release_date)[:4])
        rows.append({"decade": f"{year // 10 * 10}s"})
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.groupby("decade").size().reset_index(name="count").sort_values("decade")


def export_ego_graphml(g: nx.MultiDiGraph, node_id: int, radius: int, path: Path) -> None:
    """Gephi (not Tableau) reads GraphML directly - Tableau has no native
    graph/node-link layout, so the ego-network visual belongs in Gephi."""
    ego = ego_subgraph(g, node_id, radius=radius)
    nx.write_graphml(ego, path)


def centrality_table(g: nx.MultiDiGraph) -> pd.DataFrame:
    """Degree + betweenness centrality for the RQ2 'bridge ties' metric.
    Betweenness on the full graph is slow - this flattens to a simple
    DiGraph first since centrality algorithms don't support multigraphs."""
    flat = nx.DiGraph(g)
    degree = dict(flat.degree())
    betweenness = nx.betweenness_centrality(flat)
    node_ids = list(degree.keys())
    return pd.DataFrame({
        "node_id": node_ids,
        "name": [g.nodes[n].get("name") for n in node_ids],
        "node_type": [g.nodes[n].get("Node Type") for n in node_ids],
        "degree": list(degree.values()),
        "betweenness": [betweenness[n] for n in node_ids],
    }).sort_values("degree", ascending=False)


if __name__ == "__main__":
    g = load_graph()
    print(f"Loaded graph: {g.number_of_nodes()} nodes, {g.number_of_edges()} edges")
    print("\nNode types:\n", node_counts_by_type(g))
    print("\nEdge types:\n", edge_counts_by_type(g))

    OUTPUT_DIR.mkdir(exist_ok=True)

    node_table(g).to_csv(OUTPUT_DIR / "nodes.csv", index=False)
    edge_table(g).to_csv(OUTPUT_DIR / "edges.csv", index=False)
    genre_flow_edges(g).to_csv(OUTPUT_DIR / "genre_flow.csv", index=False)
    oceanus_folk_by_decade(g).to_csv(OUTPUT_DIR / "oceanus_folk_by_decade.csv", index=False)
    centrality_table(g).to_csv(OUTPUT_DIR / "centrality.csv", index=False)
    print(f"\nWrote Tableau-ready CSVs to {OUTPUT_DIR}/")

    sailor_id = find_node_by_name(g, "Sailor Shift")
    if sailor_id:
        ego = ego_subgraph(g, sailor_id, radius=1)
        print(f"Sailor Shift ego network (radius=1): {ego.number_of_nodes()} nodes, {ego.number_of_edges()} edges")
        export_ego_graphml(g, sailor_id, radius=1, path=OUTPUT_DIR / "sailor_shift_ego.graphml")
        print(f"Wrote Gephi-ready {OUTPUT_DIR / 'sailor_shift_ego.graphml'}")
