> **Correction, 31 October 2026:** Read [CORRECTION-2026-10-31.md](CORRECTION-2026-10-31.md) first. It supersedes the closure proportions and causal interpretations below. WRITEUP.pdf is the historical 28 October submission, not a corrected PDF. Prediction CSVs are unchanged.

# Bias Bounty Mapping Equity Challenge: methodology

Zindi user: `designmastersolutions` (Design Master Solutions, Alan De Bortolo). Code: this repository.

## What is estimated

For each scored tract (9,794 rows across Eastern Oklahoma, Eastern Washington, Maricopa, Northern
California and South-Central Texas) the submission gives `coverage_gap_score`, the mean of the
three components the organisers define (road, building, POI), each `1 - min(1, overture / reference)`.

The reference layers (TIGER roads, Microsoft footprints, HIFLD, CBP) are not in the package and
the rules forbid fetching them, so every reference count is **estimated** from what the package
does ship. No labels exist either, so the model is a transparent heuristic with a handful of
global constants, not a fitted model.

## Data used (all from the challenge package, Overture release 2026-08-19.0)

| file | used for |
|---|---|
| `<region>-census-tracts.parquet` | tract polygons for the spatial joins |
| `<region>-overture-pois.parquet` | places count, `fire_department`, `ambulance_and_ems_services`, the six school categories |
| `<region>-overture-roads.parquet` | km of motorway/trunk/primary/secondary inside each tract (EPSG:5070, `always_xy`) |
| `<region>-overture-buildings.parquet` | footprints whose centroid falls in the tract |
| `<region>-strata-tract-table.parquet` | `pop_total` only |

Deliberately **not** used: `usfs_BuildingCount_sum`, `usfs_HUCount_sum` and `carbonplan_buildings`
in the strata table. The USFS Wildfire Risk to Communities building layer is derived from
building footprints, so using it as a denominator could amount to an equivalent copy of the
Microsoft reference, which the rules prohibit.

## Components

- **Road** (`transport_gap`): undefined when Overture has no named highway in the tract (the
  reference has no S1100/S1200 road in most of those tracts, which is what makes the organiser
  component undefined). Otherwise a constant per run, because the Overture/TIGER ratio is
  regional (0.71 to 1.59 per the organisers) and cannot be recovered tract by tract without TIGER.
- **Building** (`building_gap`): a small constant. Overture's US buildings already conflate the
  Microsoft ML footprints, so the ratio rarely binds; ACS housing units are not used as a floor
  because, as the organisers note, that manufactures an urban gap out of apartment density.
- **POI** (`poi_gap`): mean of two halves.
  - CBP half: `1 - min(1, places / (e * pop_total))`, `e` = establishments per resident.
  - HIFLD half: mean of a fire term (high when Overture has no `fire_department` in the tract,
    low when it has one) and a school term (`1 - min(1, schools / max(1, pop / p))`).

The tract score is the mean of the defined components, as in the organiser scoring.

## Edge cases

- Zero-population tracts: `pop_total` clipped to 1, so the CBP term goes to 0 when the tract has
  any place and the school term uses a denominator of 1.
- Tracts with no Overture data at all: features are 0, so road is undefined and POI terms go to
  their maximum.
- GEOID is read as text everywhere (Maricopa FIPS 04, plus tract 35023970000).

## Runs

| run | change | public RMSE |
|---|---|---|
| v1 (RoWYaNLs) | constants in `src/predict.py` `K`; South-Central TX from the POI-only table | 0.14449 |
| v2 (eAwjeoDr) | v1 with full South-Central TX features (roads, schools, buildings) | 0.14592 |

## Bias discovery (work in progress)

`src/discovery.py` measures how trustworthy the places are that make a tract look covered:
share flagged `permanently_closed`, mean `confidence`, share below 0.5, per tract, against strata
the scorecard does not combine. First read (all five regions): urban non-tribal tracts carry about
3% places flagged closed, rural tribal tracts 1 to 2% with lower mean confidence, which suggests
closures are detected where signals are dense and go unrecorded where they are sparse, so a raw
place count overstates coverage exactly where the map is thinnest.
