> **Correction, 31 October 2026:** Read [CORRECTION-2026-10-31.md](CORRECTION-2026-10-31.md) first. It supersedes the closure proportions and causal interpretations below. WRITEUP.pdf is the historical 28 October submission, not a corrected PDF. Prediction CSVs are unchanged.

# Bias Bounty Mapping Equity Challenge: methodology and bias discovery

- Zindi username: **designmastersolutions** (Design Master Solutions LLC, Alan De Bortolo, solo)
- Leaderboard submissions tied to this writeup: **RoWYaNLs** (v1, public RMSE 0.14449) and **eAwjeoDr** (v2, 0.14592)
- Considered for: **Best Bias Discovery** and **Best Documentation**
- Code: `src/features.py`, `src/predict.py`, `src/discovery.py`, `src/discovery_sources.py`, `src/discovery_report.py`
  (Python 3, `duckdb` with the `spatial` extension, `pandas`; no network, no paid service). The repository is
  shared with the judges on request and posted to the challenge discussion board after the close, as the
  code-sharing rule requires.

## 1. Best Bias Discovery: "open" is something only one feed can say, and "closed" is something only one other feed can say

### The pattern

The scorecard counts Overture places per tract. It never asks **whether anyone has confirmed that a
place still exists**. Overture's `operating_status` answers that, and in the challenge package it is
not a property of the place but of the upstream feed that supplied it:

| feeds behind the place (5 regions, 2,001,137 places) | places | status NULL (never verified) | flagged closed | share of all closures |
|------------------|------:|------:|------:|------:|
| neither BrightQuery nor Overture-signals | 637,294 | **99.8%** | (n/a) | 0.1% |
| Overture-signals, no BrightQuery | 1,090,855 | 0.0% | 0.11% | 2.7% |
| BrightQuery, no Overture-signals | 182,493 | 0.0% | **23.99%** | **96.8%** |
| both | 90,495 | 0.0% | 0.17% | 0.3% |

So (a) a third of all places carry no status at all, (b) a place is only ever confirmed open when the
Overture-signals feed backs it, and (c) **96.8% of every closure in the package comes from
BrightQuery-only records**. Across tracts with at least 20 places, the closed share correlates
r = 0.72 with the tract's BrightQuery share and only r = 0.34 with `pct_urban`: closures are detected
where BrightQuery happens to have coverage, not where businesses actually close.

### Who it hits (strata the scorecard does not combine)

Tracts with at least 20 places, places weighted:

| stratum | tracts | population | places never verified | BrightQuery share | flagged closed | emergency places never verified |
|-----------|----:|-----:|-----:|-----:|-----:|-----:|
| non-tribal urban | 7,273 | 31.9 M | 30.5% | 15.2% | 3.6% | 36.2% |
| non-tribal rural | 1,427 | 5.0 M | 40.0% | 5.1% | 1.2% | 37.5% |
| tribal urban | 441 | 1.5 M | 29.5% | 11.6% | 2.9% | 31.9% |
| **tribal rural** | **419** | **1.4 M** | **41.2%** | **4.7%** | **1.2%** | **45.1%** |

"Emergency places" = `fire_department`, `ambulance_and_ems_services`, `police_department`, `hospital`,
`emergency_room`. The rural/urban gap in unverified places holds in every region (rural 39.1 to 41.5%,
urban 27.7 to 31.5%). Rural tracts look like they have **a third of the closure rate** of urban tracts
(1.2% vs 3.6%) only because the feed that reports closures barely reaches them (4.7 to 5.1% vs 15.2%).
Applying the urban rate would mean roughly 2 to 3 times more dead entries in the rural place counts
than the data admits, which the coverage gap score reads as coverage.

The extreme case is the one that matters for dispatch: **274 rural tracts (909,369 residents) in which
every emergency facility on the map has `operating_status` NULL**. 92 of them (291,545 residents) are
tribal, a third of the list while tribal tracts are under a quarter of rural tracts. Named examples
(all rural, every emergency facility unverified):

| region | tract | area | population | places | places never verified | BrightQuery share | emergency places |
|--|-----|--------------|----:|---:|----:|----:|----:|
| AZ | 04007940400 | San Carlos Reservation | 5,531 | 134 | 53% | 0.0% | 2 |
| AZ | 04009940500 | San Carlos Reservation | 4,720 | 72 | 54% | 0.0% | 2 |
| AZ | 04021941401 | Maricopa (Ak Chin) Indian Reservation | 4,806 | 115 | 39% | 2.6% | 2 |
| OK | 40145030601 | Creek OTSA | 5,349 | 91 | 45% | 3.3% | 2 |
| OK | 40079040602 | Choctaw OTSA | 5,096 | 142 | 42% | 2.1% | 2 |
| OK | 40031002302 | Kiowa-Comanche-Apache-Fort Sill Apache OTSA | 4,939 | 161 | 39% | 5.0% | 3 |
| OK | 40051000802 | Chickasaw OTSA | 4,876 | 122 | 59% | 1.6% | 3 |
| OK | 40125501104 | Citizen Potawatomi Nation-Absentee Shawnee OTSA | 4,380 | 158 | 34% | 8.9% | 2 |
| WA | 53013960200 | Umatilla Off-Reservation Trust Land | 3,952 | 277 | 32% | 10.8% | 4 |

The San Carlos tracts have zero BrightQuery records: nothing in the package could ever mark a place
there as closed.

### Why it matters

- **Emergency dispatch and mutual aid.** A planner or a routing tool that uses Overture to find the
  nearest fire station or EMS base gets the same answer for a confirmed station and for an entry no
  feed has checked. In the 274 tracts above there is no confirmed one at all. Rural and tribal fire
  and EMS service in Oklahoma and Arizona is often volunteer or shared with the tribe, the county and
  IHS, and stations consolidate or close; a stale entry there sends a mutual-aid request or an
  ambulance-staging plan to a building that is not staffed.
- **Evacuation and relief siting.** After wildfire or flood, relief agencies pick shelters, PODs and
  supply points from "what is around". On reservations such as San Carlos, where the whole tract has
  no feed able to report a closure, every closed store, clinic or church still counts as an option.
- **The gap score itself.** The POI component is `1 - min(1, overture / reference)`. Dead entries in
  rural and tribal tracts inflate `overture`, so the score reports those tracts as better covered than
  they are, and it does so in the direction opposite to the scorecard's own equity concern.

### Reproduce

From the challenge package only (Overture release in the package, 2026-08-19.0):

```
python src/discovery_sources.py   # writes data/poi-sources.parquet and prints every table above
```

Places are joined to tracts with `ST_Intersects` on the package tract polygons; the feed of a place is
`list_transform(sources, s -> s.dataset)`; strata come from the package strata tables (`pct_urban >= 0.5`
= urban, `tribal_any`, `aiannh_name`). No additional dataset is used, so there is nothing to retrieve.

### What would fix it

Weight each place by verification before counting it (for example, count NULL-status places at the
local closure-adjusted rate, or only count signal-backed places for emergency categories), and publish a
"verified emergency facility" layer per tract next to the gap score so dispatch and relief users can see
where the map has never been checked.

## 2. Methodology (Best Documentation)

### What is estimated

For each scored tract (9,794 rows across Eastern Oklahoma, Eastern Washington, Maricopa, Northern
California and South-Central Texas) the submission gives `coverage_gap_score`, the mean of the three
components the organisers define (road, building, POI), each `1 - min(1, overture / reference)`.

The reference layers (TIGER roads, Microsoft footprints, HIFLD, CBP) are not in the package and the
rules forbid fetching them, so every reference count is **estimated** from what the package ships. No
labels exist, so the model is a transparent heuristic with a handful of global constants (`K` in
`src/predict.py`), not a fitted model.

### Data sources (all from the challenge package)

| file | used for |
|---|---|
| `<region>-census-tracts.parquet` | tract polygons for the spatial joins |
| `<region>-overture-pois.parquet` | places count, `fire_department`, `ambulance_and_ems_services`, the six school categories |
| `<region>-overture-roads.parquet` | km of motorway/trunk/primary/secondary inside each tract (EPSG:5070, `always_xy := true`) |
| `<region>-overture-buildings.parquet` | footprints whose centroid falls in the tract |
| `<region>-strata-tract-table.parquet` | `pop_total` only |

Deliberately **not** used: `usfs_BuildingCount_sum`, `usfs_HUCount_sum` and `carbonplan_buildings`. The
USFS building layer is derived from building footprints, so using it as a denominator could amount to
an equivalent copy of the Microsoft reference, which the rules prohibit.

### Components

- **Road**: undefined when Overture has no named highway in the tract (the reference has no S1100/S1200
  road in most of those tracts, which is what makes the organiser component undefined). Otherwise a
  constant per run, because the Overture/TIGER ratio is regional (0.71 to 1.59 per the organisers) and
  cannot be recovered tract by tract without TIGER.
- **Building**: a small constant. Overture's US buildings already conflate the Microsoft ML footprints,
  so the ratio rarely binds; ACS housing units are not used as a floor because, as the organisers note,
  that manufactures an urban gap out of apartment density.
- **POI**: mean of two halves. CBP half: `1 - min(1, places / (e * pop_total))`, `e` = establishments per
  resident. HIFLD half: mean of a fire term (high when Overture has no `fire_department` in the tract,
  low when it has one) and a school term (`1 - min(1, schools / max(1, pop / p))`).

The tract score is the mean of the defined components, as in the organiser scoring.

### Edge cases

- **Zero-population tracts**: `pop_total` clipped to 1, so the CBP term goes to 0 when the tract has any
  place and the school term uses a denominator of 1.
- **Water-dominated tracts**: no special rule. They have few or no roads (road component undefined) and
  few places; the POI terms are population-normalised, so a near-empty water tract does not get a gap
  out of its area.
- **Tracts with no Overture data**: features are 0, so road is undefined and the POI terms go to their
  maximum.
- GEOID is read as text everywhere (Maricopa FIPS 04, and tract 35023970000).

### Weightings and runs

Equal weights across defined components, as the organisers define the score; no alternative weighting
was applied to the scored file, because without labels any reweighting would be a guess. The discovery
above is the argument for a different POI count, not a different weight.

| run | change | public RMSE |
|---|---|---|
| v1 (RoWYaNLs) | constants in `src/predict.py` `K`; South-Central TX from the POI-only table | 0.14449 |
| v2 (eAwjeoDr) | v1 with full South-Central TX features (roads, schools, buildings) | 0.14592 |

### Reproduce the scored file

```
python -m venv .venv && .venv/bin/pip install duckdb pandas pyarrow
.venv/bin/python src/features.py      # data/<region>-features.parquet
.venv/bin/python src/predict.py       # submissions/v2.csv
```

LLM coding assistants were used for drafting code and text; the method, the numbers and every check are
mine and nothing in the pipeline calls a model.
