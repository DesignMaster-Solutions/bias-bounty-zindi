# Best Bias Discovery and Documentation: correction to my submitted writeup

Zindi user: designmastersolutions. Submissions: RoWYaNLs (0.14449478) and eAwjeoDr (0.145918577). I submitted my writeup for both special prizes on 28 October. This correction supersedes the closure-rate percentages, correlations and causal interpretations in that PDF. It does not change either prediction CSV or its leaderboard score.

## Finding and correction

My discovery concerns upstream-feed differences in the availability of Overture operating_status, which the automated coverage scorecard does not display. During my final reproducibility audit, I found a denominator error in my discovery code: AVG(status = 'permanently_closed') excludes NULL statuses. I had incorrectly described that result as a proportion of all places, and then weighted the per-tract ratios by all places.

The corrected per-tract expression is:

```sql
COUNT(*) FILTER (WHERE st = 'permanently_closed')::DOUBLE / COUNT(*) AS closed_share
```

This is the proportion of records carrying an explicit closure flag. It is NOT the actual business closure rate. For example, one closed, one open and two NULL records give 25%, not 50%. An all-NULL tract has zero recorded closures, not proof that all businesses are open.

Recomputed from the same five-region package, spatially joined to tracts, retaining tracts with at least 20 mapped places and weighting by mapped-place count:

| Stratum | Tracts | Missing status | BrightQuery-backed | Explicit closure flags / all places |
|---|---:|---:|---:|---:|
| Non-tribal rural | 1,427 | 40.0% | 5.1% | 0.7% |
| Non-tribal urban | 7,273 | 30.5% | 15.2% | 2.5% |
| Tribal rural | 419 | 41.2% | 4.7% | 0.8% |
| Tribal urban | 441 | 29.5% | 11.6% | 2.1% |

Across these tracts, Pearson correlation of the corrected closure-flag proportion with BrightQuery share is 0.763; with pct_urban it is 0.346. These replace 0.72 and 0.34 in my original writeup. The larger association does not establish causation or control for confounding.

The raw feed-cohort counts, before spatial joins, remain independently reproducible: 2,001,137 records; 637,294 have neither BrightQuery nor Overture-signals, of which 636,146 have NULL status. Of 45,207 explicitly closed records, 43,778 (96.84%) are BrightQuery-only. There are also 32 closure flags among records with neither feed. My earlier wording that nothing outside BrightQuery could mark a place closed was too strong and is withdrawn.

## What the evidence does and does not show

NULL means that this package has no operating-status value. It does not establish that a place has never been verified, that it is closed, or that a feed is incapable of reporting closure. I withdraw the extrapolation that rural areas must contain two to three times more dead entries, and the claim that the observed rural/urban difference occurs only because of BrightQuery coverage. There is no independent ground truth here for actual closures or emergency-service staffing.

Under the explicit >=20-place filter above, 273 rural tracts, containing a summed census population of 909,368, have at least one mapped emergency-category place and all such records have NULL status. Of these, 92 tracts have tribal_any=true, with population 291,545. This replaces the earlier 274 / 909,369 figure under this stated filter. These are tract populations, not counts of people proved to lack emergency services; a tract can intersect tribal land without every resident being tribal.

My practical recommendation is to expose missing-status and feed-provenance fields alongside facility counts, and prioritize independent verification of emergency destinations. I do not recommend discarding NULL-status facilities or treating signal-backed facilities as operationally verified. Such a filter could remove real services exactly where data is sparse.

## Reproducibility and scope

I use the supplied Overture 2026-08-19.0 extracts, census-tract polygons and strata tables. A place-to-tract assignment uses ST_Intersects; region and GEOID identify a row. Boundary points can participate in more than one tract, so spatially assigned counts must not be equated with unique raw-record counts. Urban means pct_urban>=0.5; rural means pct_urban<0.5. Emergency categories are fire_department, ambulance_and_ems_services, police_department, hospital and emergency_room. The discovery covers all five supplied regions, including Eastern Washington; it is not a claim that every discovery tract is scored on the leaderboard.

I added three spatial-aggregation regression tests covering mixed NULL statuses, all-NULL statuses and fully observed statuses. The first two failed on the original code and all three pass after correction. The corrected discovery script prints the stratum table, correlations, emergency-status count and raw feed cohorts from local package files. No removed reference layers, paid API or LLM inference is used in this computation. I used a coding assistant to draft and test the correction.

Please consider this correction with my already-submitted writeup for Best Bias Discovery and Best Documentation.
