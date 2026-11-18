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


def genre_flow_edges(g: nx.MultiDiGraph, genre_attr: str = "genre") -> pd.DataFrame:
    """Genre-to-genre influence edge counts, direction preserved, for the
    Sankey/chord-diagram decision - group by (source genre, target genre).
    Genre only lives on Song/Album nodes, so this naturally only counts the
    derivative-work edges between songs/albums (InStyleOf, CoverOf, etc.) -
    Person/MusicalGroup/RecordLabel nodes have no genre and get filtered out."""
    rows = []
    for u, v, attrs in g.edges(data=True):
        u_genre = g.nodes[u].get(genre_attr)
        v_genre = g.nodes[v].get(genre_attr)
        if u_genre and v_genre and u_genre != v_genre:
            rows.append({"source_genre": u_genre, "target_genre": v_genre, "edge_type": attrs.get("Edge Type")})
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.groupby(["source_genre", "target_genre"]).size().reset_index(name="count").sort_values("count", ascending=False)


def centrality_table(g: nx.MultiDiGraph) -> pd.DataFrame:
    """Degree + betweenness centrality for the RQ2 'bridge ties' metric.
    Betweenness on the full graph is slow - this flattens to a simple
    DiGraph first since centrality algorithms don't support multigraphs."""
    flat = nx.DiGraph(g)
    degree = dict(flat.degree())
    betweenness = nx.betweenness_centrality(flat)
    return pd.DataFrame({
        "node": list(degree.keys()),
        "degree": list(degree.values()),
        "betweenness": [betweenness[n] for n in degree.keys()],
    }).sort_values("degree", ascending=False)


if __name__ == "__main__":
    g = load_graph()
    print(f"Loaded graph: {g.number_of_nodes()} nodes, {g.number_of_edges()} edges")
    print("\nNode types:\n", node_counts_by_type(g))
    print("\nEdge types:\n", edge_counts_by_type(g))

    sailor_id = find_node_by_name(g, "Sailor Shift")
    if sailor_id:
        ego = ego_subgraph(g, sailor_id, radius=1)
        print(f"\nSailor Shift ego network (radius=1): {ego.number_of_nodes()} nodes, {ego.number_of_edges()} edges")
