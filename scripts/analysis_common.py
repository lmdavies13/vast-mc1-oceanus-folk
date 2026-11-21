"""Shared tabular loader + edge-type groups for the RQ1/RQ2 analysis scripts.

load_graph.py builds an nx.MultiDiGraph; these scripts work on flat pandas
tables instead (faster for group-bys over 37k edges).

IMPORTANT - influence direction: for InStyleOf / InterpolatesFrom / CoverOf /
LyricalReferenceTo / DirectlySamples, the data description defines
source = the newer work that borrows, target = the work it borrows from.
So influence flows TARGET -> SOURCE. Every analysis here reverses those edges
before talking about "who influenced whom".
"""
import json
import collections
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PATH = ROOT / "data" / "MC1_graph.json"
RESULTS = ROOT / "results"      # small committed JSON/CSV results
OUTPUT = ROOT / "output"        # bulky regenerable CSVs (gitignored)
FIGURES = ROOT / "figures"

CREATOR = {'PerformerOf', 'ComposerOf', 'ProducerOf', 'LyricistOf'}
INFLUENCE = {'InStyleOf', 'InterpolatesFrom', 'CoverOf', 'LyricalReferenceTo', 'DirectlySamples'}
LABEL = {'RecordedBy', 'DistributedBy'}


def yr(v):
    try:
        return int(str(v)[:4])
    except (TypeError, ValueError):
        return None


def load():
    g = json.load(open(PATH))
    nodes = pd.DataFrame(g['nodes']).set_index('id')
    nodes['year'] = nodes['release_date'].map(yr).astype('Int64')
    nodes['notoriety_year'] = nodes['notoriety_date'].map(yr)
    nodes['written_year'] = nodes['written_date'].map(yr)
    edges = pd.DataFrame(g['links'])
    edges['src_type'] = edges['source'].map(nodes['Node Type'])
    edges['tgt_type'] = edges['target'].map(nodes['Node Type'])
    return g, nodes, edges


def works_of(nodes, edges):
    """Map artist id (Person/MusicalGroup) -> set of work ids, including works credited to groups they belong to."""
    cre = edges[edges['Edge Type'].isin(CREATOR) & edges['tgt_type'].isin(['Song', 'Album'])]
    w = collections.defaultdict(set)
    for s, t in zip(cre.source, cre.target):
        w[s].add(t)
    return w, cre
