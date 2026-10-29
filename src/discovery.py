"""Bias discovery: how trustworthy are the Overture places that make a tract look 'covered'?

Per tract: share of places flagged permanently_closed, mean confidence, share backed by a single
upstream dataset, and the same for fire_department entries. Then compare across strata cuts the
automated scorecard does not use (e.g. tribal x rural, high SVI x high heat)."""
import os, sys, duckdb, pandas as pd

D = os.path.join(os.path.dirname(__file__), "..", "data")
REGIONS = ["eastern-ok", "eastern-wa", "maricopa-az", "northern-ca", "south-central-tx"]


def quality(con, r):
    return con.sql(f"""
      with t as (select GEOID, geometry g from '{D}/{r}-census-tracts.parquet'),
      q as (select id, categories.primary cat, confidence, operating_status st, len(sources) nsrc,
                   list_transform(sources, lambda s: s.dataset) ds, geometry from '{D}/{r}-overture-pois.parquet')
      select t.GEOID, '{r}' region, count(*) n_places,
        avg((st='permanently_closed')::int) closed_share,
        avg(confidence) mean_conf,
        avg((confidence < 0.5)::int) lowconf_share,
        avg((list_unique(ds)=1)::int) single_source_share,
        avg((list_contains(ds,'meta') and list_unique(ds)=1)::int) meta_only_share,
        count(*) filter (where cat='fire_department') n_fire,
        avg(confidence) filter (where cat='fire_department') fire_conf
      from q join t on ST_Intersects(t.g, q.geometry) group by 1""").df()


if __name__ == "__main__":
    con = duckdb.connect(); con.sql("LOAD spatial")
    df = pd.concat([quality(con, r) for r in (sys.argv[1:] or REGIONS)])
    df.to_parquet(f"{D}/poi-quality.parquet")
    print(df.groupby("region")[["closed_share", "mean_conf", "lowconf_share", "single_source_share", "meta_only_share"]].mean())
