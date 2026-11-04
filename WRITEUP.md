> **Version 2, 4 November 2026.** This writeup replaces the PDF I submitted on 28 October. It fixes a
> denominator error in the closure-flag shares, updates every number that depended on it and withdraws
> claims the data does not support (see "Correction history" at the end of section 1). The prediction
> CSVs and leaderboard scores are unchanged. The 28 October PDF is kept as `WRITEUP-2026-10-28-original.pdf`.

# Bias Bounty Mapping Equity Challenge: methodology and bias discovery

- Zindi username: **designmastersolutions** (Design Master Solutions LLC, Alan De Bortolo, solo)
- Leaderboard submissions tied to this writeup: **RoWYaNLs** (v1, public RMSE 0.14449) and **eAwjeoDr** (v2, 0.14592)
- Considered for: **Best Bias Discovery** and **Best Documentation**
- Code: https://github.com/DesignMaster-Solutions/bias-bounty-zindi (public since 4 November, after the close,
  and linked on the challenge discussion board as the code-sharing rule requires): `src/features.py`,
  `src/predict.py`, `src/discovery.py`, `src/discovery_sources.py`, `src/discovery_report.py`, `tests/`
  (Python 3, `duckdb` with the `spatial` extension, `pandas`; no network, no paid service).

## 1. Best Bias Discovery: whether a place has any operating status, and where closures get recorded, depends on the upstream feed

### The pattern

The scorecard counts Overture places per tract. It never asks **whether the package knows that a place
is still operating**. Overture's `operating_status` carries that information, and in the challenge
package its presence depends on the upstream feed that supplied the record, not on the place (5 regions,
2,001,137 raw records; "neither feed" = neither BrightQuery nor Overture-signals; closure flag =
`permanently_closed`):

| feed behind the record | records | status NULL | closure flags | share of all flags |
|------------------|------:|------:|------:|------:|
| neither feed | 637,294 | **99.8%** | 32 (0.005%) | 0.07% |
| Overture-signals only | 1,090,855 | 0.0% | 1,240 (0.11%) | 2.74% |
| BrightQuery only | 182,493 | 0.0% | 43,778 (**23.99%**) | **96.84%** |
| both | 90,495 | 0.0% | 157 (0.17%) | 0.35% |

So (a) 31.8% of all records (636,146) carry no status at all, and 99.8% of the records that neither feed
backs are in that group, while every record backed by either feed carries a status; (b) both feeds report
places as open (BrightQuery-only records: 138,715 open); (c) **96.8% of the explicit closure flags in the
package come from BrightQuery-only records**. Across tracts with at least 20 mapped places, the share of
places with an explicit closure flag correlates r = 0.763 with the tract's BrightQuery share and
r = 0.346 with `pct_urban`. This is an association, not a causal estimate: it shows where closures are
recorded, not where businesses close.

### Who it hits (strata the scorecard does not combine)

Tracts with at least 20 mapped places, weighted by mapped places (BrightQuery = share of places with a
BrightQuery record; closure flags = explicit flags over all places, NULL included):

| stratum | tracts | population | status NULL | BrightQuery | closure flags | emergency places, status NULL |
|-----------|----:|-----:|-----:|-----:|-----:|-----:|
| non-tribal urban | 7,273 | 31.9 M | 30.5% | 15.2% | 2.5% | 36.2% |
| non-tribal rural | 1,427 | 5.0 M | 40.0% | 5.1% | 0.7% | 37.5% |
| tribal urban | 441 | 1.5 M | 29.5% | 11.6% | 2.1% | 31.9% |
| **tribal rural** | **419** | **1.4 M** | **41.2%** | **4.7%** | **0.8%** | **45.1%** |

"Emergency places" = `fire_department`, `ambulance_and_ems_services`, `police_department`, `hospital`,
`emergency_room`. The rural/urban gap in missing status holds in every region (rural 39.1 to 41.5%,
urban 27.7 to 31.5%). Tribal rural tracts combine the highest missing-status share, the lowest
BrightQuery share and the highest share of emergency places with no status. Rural places carry explicit
closure flags about a third as often as urban ones (0.7 to 0.8% against 2.1 to 2.5%), and the feed behind
96.8% of all flags reaches rural places far less often (4.7 to 5.1% against 11.6 to 15.2%). I do not
claim that feed coverage alone causes the rural/urban difference in recorded closures, and I make no
estimate of how many mapped places are actually closed: the package has no independent ground truth
for closures.

The extreme case is the one that matters for dispatch: **273 rural tracts (`pct_urban` < 0.5, at least
20 mapped places; summed census population 909,368) where at least one emergency-category place is
mapped and every such record has `operating_status` NULL**. 92 of them (population 291,545) intersect
tribal areas (`tribal_any`): a third of the list, while tribal tracts are under a quarter of rural tracts
(419 of 1,829). These are tract populations, not counts of people proved to lack emergency services, and
a tract can intersect tribal land without every resident being tribal. Named examples (all rural, every
mapped emergency facility with no status; values from the corrected per-tract table):

| tract | area | population | places | status NULL | BrightQuery | emergency places |
|-----|--------------|----:|---:|----:|----:|----:|
| 04007940400 | San Carlos Reservation, AZ | 5,531 | 134 | 53% | 0.0% | 2 |
| 04009940500 | San Carlos Reservation, AZ | 4,720 | 72 | 54% | 0.0% | 2 |
| 04021941401 | Maricopa (Ak Chin) Indian Reservation, AZ | 4,806 | 115 | 39% | 2.6% | 2 |
| 40145030601 | Creek OTSA, OK | 5,349 | 91 | 45% | 3.3% | 2 |
| 40079040602 | Choctaw OTSA, OK | 5,096 | 142 | 42% | 2.1% | 2 |
| 40031002302 | Kiowa-Comanche-Apache-Fort Sill Apache OTSA, OK | 4,939 | 161 | 39% | 5.0% | 3 |
| 40051000802 | Chickasaw OTSA, OK | 4,876 | 122 | 59% | 1.6% | 3 |
| 40125501104 | Citizen Potawatomi Nation-Absentee Shawnee OTSA, OK | 4,380 | 158 | 34% | 8.9% | 2 |
| 53013960200 | Umatilla Off-Reservation Trust Land, WA | 3,952 | 277 | 32% | 10.8% | 4 |

The two San Carlos tracts have no BrightQuery record at all, the feed behind 96.8% of the closure flags
in the package, and none of their 206 mapped places carries a closure flag.

### Why it matters

- **Emergency dispatch and mutual aid.** A planner or a routing tool that uses Overture to find the
  nearest fire station or EMS base gets the same answer for an entry with a recorded status and for an
  entry with none. In the 273 tracts above, no mapped emergency facility has any status. Where a station
  is volunteer-staffed, consolidated or closed, a stale entry could send a mutual-aid request or an
  ambulance-staging plan to a building that is not staffed, and nothing in the package would flag it.
  The package cannot say how many of these entries are stale; that blind spot is the finding.
- **Evacuation and relief siting.** After wildfire or flood, relief agencies pick shelters, PODs and
  supply points from what is on the map. In tracts such as the two San Carlos tracts, where no record
  comes from the feed that carries almost every closure flag, a closed store, clinic or church would
  still look like an option.
- **The gap score itself.** The POI component is `1 - min(1, overture / reference)`. If the NULL-status
  entries in rural and tribal tracts include closed places, they inflate `overture` and the score reports
  those tracts as better covered than they are, in the direction opposite to the scorecard's own equity
  concern. The package gives no way to measure how many there are, which is why the status gap needs to
  be visible next to the score.

### Reproduce

From the challenge package only (Overture release in the package, 2026-08-19.0):

```
python src/discovery_sources.py                 # prints every table in section 1
python -m unittest tests/test_closed_share.py   # 3 denominator regression tests
```

Places are joined to tracts with `ST_Intersects` on the package tract polygons (a boundary point can fall
in more than one tract, so spatially assigned counts are not unique-record counts; the feed table above
is computed on raw records, before any join). The feed of a place is
`list_transform(sources, s -> s.dataset)`. The closure-flag share of a tract is
`count(*) filter (where st = 'permanently_closed') / count(*)`, so NULL statuses stay in the
denominator. Strata come from the package strata tables (`pct_urban >= 0.5` = urban, `< 0.5` = rural,
`tribal_any`, `aiannh_name`). The discovery covers all five supplied regions; it does not claim that
every discovery tract is scored on the leaderboard. No additional dataset is used, so there is nothing
to retrieve.

### What would fix it

Publish a missing-status share and the feed provenance next to every facility count and next to the gap
score, and prioritize independent verification of emergency destinations in tracts like the 273 above,
so dispatch and relief users can see where the map has never confirmed a facility. I do not recommend
discarding NULL-status facilities or treating signal-backed facilities as operationally verified: such
a filter could remove real services exactly where data is sparse.

### Correction history

My 28 October PDF computed the closure share as `AVG(status = 'permanently_closed')`, which drops NULL
statuses from the denominator, and then described and weighted it as a share of all places. For example,
one closed, one open and two NULL records gave 50% instead of 25%. This version uses the full
denominator and replaces: the closure-flag percentages by stratum (urban 3.6% and rural 1.2% became 2.5%
and 0.7%), the correlations (0.72 and 0.34 became 0.763 and 0.346) and the emergency-status count (274
tracts and 909,369 people became 273 and 909,368 under the stated filter). It withdraws four statements:
that only Overture-signals confirms a place as open, that nothing outside BrightQuery can flag a place
closed, that rural areas must hold 2 to 3 times more dead entries, and that the rural/urban difference
occurs only because of BrightQuery coverage. Three regression tests cover mixed NULL, all-NULL and fully
observed statuses; the first two failed on the original code. I posted the same correction on the
challenge discussion board on 31 October.

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
above argues for publishing status and provenance next to the POI count, not for a different weight.

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
