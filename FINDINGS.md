# Findings — RQ1 & RQ2

Results produced by the analysis scripts in `scripts/` (see "Reproduce" at the
bottom). Every number below comes from `results/rq1.json`, `results/rq2.json`
or the CSVs next to them. Figures are in `figures/`.

> **Key correction — influence direction.** For the five influence edge types
> (InStyleOf, InterpolatesFrom, CoverOf, LyricalReferenceTo, DirectlySamples)
> the data description defines *source = the newer work that borrows* and
> *target = the work it borrows from*. Influence therefore flows
> **target → source**. All analysis here reverses those edges. The proposal
> deck's "100 edges from Oceanus Folk into Indie Folk" actually means
> **Indie Folk influenced Oceanus Folk** 100 times. `genre_flow_edges()` in
> `load_graph.py` has been fixed to output the corrected direction.

---

## 1. Data exploration (for the presentation's exploration section)

| | |
|---|---|
| Nodes / edges | 17,412 / 37,857 (directed multigraph) |
| Works | 4,611 (3,615 songs, 996 albums), released 1975–2040 |
| Genres | 26; largest: Dream Pop (742), Indie Folk (450), Synthwave (382), Doom Metal (348), **Oceanus Folk (305)** |
| `notable` flag | True on 93% of works, so it barely separates anything |
| `notoriety_date` | Present on only 649 works; median lag after release = 0 years |
| Artists (people + bands with ≥1 credit) | 11,581; 74% have exactly one work |
| Collaboration network (artists linked by shared credits) | 11,581 nodes, 31,695 links; the largest connected component holds 42% of artists |
| Release volume | Peaks in the 2020s (2,169 works), then falls to 269 in the 2030s, so treat 2030s trends with care |

**Oceanus Folk over time** (`figures/01_oceanus_folk_over_time.png`): the genre
was a steady ~4–6% of releases from the 1990s to the 2010s. It reached 6.7%
in the 2020s, then 23% in the 2030s (61 of 269 works). The 2030s jump is
partly a shrinking denominator.

---

## 2. RQ1 — Did Sailor Shift's network drive Oceanus Folk's diffusion?

### Her ego network
- 60 direct edges to 51 distinct nodes: 26 PerformerOf, 21 LyricistOf, and a
  handful of influence edges. She is a member of **Ivy Echos** (with Maya
  Jensen, Lila "Lilly" Hartman, Jade Thompson and Sophie Ramirez).
- 46 works across her solo output and Ivy Echos, released 2024–2040. 44 of
  the 46 are Oceanus Folk; the other two are Synthwave and Americana.
- **47 collaborators** share credits with her. They form small, tight
  clusters (80 collaborator-to-collaborator pairs). 32 of the 47 are mainly
  Oceanus Folk; the rest are Americana, Synthwave, Sea Shanties, Celtic Folk
  and Acoustic Folk. Her collaborators barely cross genres
  (`figures/04_sailor_shift_ego_network.png`).
- Her collaboration cluster is **not connected to the main collaboration
  network**. It is an island.
- Influence: 36 influence edges point *into* her (from 18 genres; The
  Saltwater Weavers and The Fiddle & The Fjord appear most). 21 edges point
  *out* from her to later works (Oceanus Folk, Post-Apocalyptic Folk, Lo-Fi
  Electronica and others).

### Genre-level diffusion (direction-corrected)
- 267 influence edges run from Oceanus Folk into other genres; 230 run the
  other way (counts include artist/band nodes, which get their dominant
  genre). Work-to-work only: 230 outward.
- **Oceanus Folk spread most into** Desert Rock (51), Dream Pop (44), Indie
  Folk (43) and Space Rock (36).
- **Oceanus Folk drew most from** Indie Folk (100), then Synthwave (19) and
  Dream Pop (15) (`figures/02_genre_influence_flows.png`).
- Reach grew over time. Oceanus Folk had influenced 10 genres before 2023 and
  16 from 2023 on. First year each genre was reached: Doom Metal 2007, Indie
  Folk 2010, Dream Pop 2017, Desert Rock 2020, Synthwave 2021, Indie Rock
  2027, Speed Metal 2034.
- Outward borrowing peaks from 2023 to 2029, which overlaps the start of
  Sailor Shift's career (`figures/03_outward_spread_attribution.png`).

### Attribution: how much runs through her?
- Only **14 of 267** outward edges (5%) start at Sailor Shift, Ivy Echos or
  their works. Her collaborators' own works account for none.
- Since 2023, **1 of 190** dated outward edges traces to her network.
- The single biggest carrier is the 2017 song *Destiny's Call* (25 outward
  edges), which predates her career.

**Answer to RQ1.** The hypothesis is only partly supported. Sailor Shift's
rise coincides with Oceanus Folk's peak in releases and in cross-genre
borrowing. But the explicit graph links show most of the spread running
*independently* of her ego network. Her network is a dense, genre-pure island
rather than a bridge between genres. A defensible story: she is the face of
the genre's boom, but the cross-genre diffusion was carried by earlier
Oceanus Folk works and other artists.

---

## 3. RQ2 — Sustained stars vs. viral spikes

### How the groups are defined
- **Population:** artists whose works were borrowed from at least 10 times
  (681 artists).
- **Sustained star (n = 304):** 3 or more influential works, and a career of
  6 years or more.
- **Viral spike (n = 217):** at least 80% of their influence comes from one
  work, and a career of 3 years or less.

Network features come from the artist collaboration network, so they are
measured separately from the influence counts that define the groups.

| Feature | Sustained (median) | Viral (median) | Mann–Whitney p |
|---|---|---|---|
| Collaborators (degree) | 13 | 5 | 1e-28 |
| Betweenness > 0 (acts as a bridge) | 81% of artists | 1% of artists | 1e-63 |
| Clustering coefficient | 0.38 | 1.00 | 6e-51 |
| k-core | 5 (mean 6.2) | 5 (mean 7.5) | 0.004 (viral higher) |
| Has a tie to a top-2% producer | 45% of artists | 15% of artists | 6e-14 |
| In main network component | 68% | 39% | 6e-11 |

See `figures/06_sustained_vs_viral.png`.

**Interpretation**
- **Supported:** sustained stars have more collaborators, act as bridges
  (betweenness), and are about 3× more likely to be tied to a major producer.
- **Not supported:** being "embedded in core clusters." Viral spikes sit in
  *closed* cliques (clustering 1.0, and an equal or higher k-core). That is
  the single-song credit team. Sustained careers come from **brokerage**
  across groups, not density.
- A logistic regression using only network-position features (log
  betweenness, clustering, producer ties, main component, degree) separates
  the groups with **78.5% cross-validated accuracy**, against a 58% baseline.
  Betweenness is the strongest predictor.

### Who's next for Oceanus Folk? (`figures/07_next_oceanus_folk_stars.png`)
Candidates are Oceanus Folk-majority artists who debuted in 2020 or later,
were still active in 2028 or later, and have at least 2 works (69 in the
pool). Each was scored by:

- the model's sustained-profile probability,
- release momentum (works per year), and
- influence received.

Top candidates:

1. **Donna Ryan** (2029; 15 collaborators, the most in the pool)
2. **Ping Sun** (2023–29; 4 works, borrowed from 7 times)
3. **Lei Jin** (2021–32; 5 works across lyricist, performer and producer roles)
4. **Cosmic Drift** (band: Xia Cui, Xiuying Li, Lei Shen; 2022–30; borrowed from 11 times)
5. Also: Ping Xu (highest betweenness in the pool), Yoko Fujita, Guiying Tang, Chao Sun

Sailor Shift herself scores a 0.99 sustained-profile probability, which is
consistent with the model.

Caveat: the data thins out after 2030, and most Oceanus Folk artists active
in the late 2030s are Sailor Shift's own collaborators (inside her island
cluster). Treat these as **network-based hypotheses**, not forecasts.

---

## 4. Limitations / future work
- "Influence" is limited to the five explicit edge types. Shared labels or
  producers might carry influence that never shows up as an edge.
- A few influence edges connect person/band nodes directly, even though the
  data description says they link works. These are kept and assigned each
  artist's dominant genre.
- Group thresholds (≥10 influence received, 6-year/3-year spans, 80%
  concentration) are judgment calls; results should be re-run with
  alternatives.
- `notable` is too common to be useful, and `notoriety_date` is sparse.
- Collaboration-network betweenness uses sampling (k = 1500) for speed.

## Reproduce
```
pip install -r requirements.txt
python3 scripts/rq1_diffusion.py      # RQ1 -> results/rq1.json + CSVs, output/*.graphml
python3 scripts/rq2_features.py       # per-artist metrics -> results/artist_features.csv (~30 s)
python3 scripts/rq2_trajectories.py   # RQ2 groups, tests, model, candidates -> results/rq2.json
python3 scripts/make_figures.py       # figures/*.png
```
