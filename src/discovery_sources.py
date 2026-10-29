"""Discovery: whether a place is known to be open depends on which upstream dataset feeds it.
Per tract: share of places with operating_status NULL (never verified), share backed by
Overture-signals (the only feed that confirms 'open'), share with a BrightQuery record (the feed
that carries almost every 'permanently_closed' flag). Writes data/poi-sources.parquet."""
import os, duckdb
D = os.path.join(os.path.dirname(__file__), "..", "data")
R = ["eastern-ok", "eastern-wa", "maricopa-az", "northern-ca", "south-central-tx"]
EMERG = "('fire_department','ambulance_and_ems_services','police_department','hospital','emergency_room')"
con = duckdb.connect(); con.sql("LOAD spatial")
parts = []
for r in R:
    parts.append(con.sql(f"""
      with t as (select GEOID, geometry g from '{D}/{r}-census-tracts.parquet'),
      p as (select categories.primary cat, operating_status st, confidence,
                   list_transform(sources, lambda s: s.dataset) ds, geometry from '{D}/{r}-overture-pois.parquet')
      select t.GEOID, '{r}' region, count(*) n_places,
        avg((st is null)::int) unknown_share,
        avg(list_contains(ds,'Overture-signals')::int) signals_share,
        avg(list_contains(ds,'BrightQuery')::int) bq_share,
        avg((st='permanently_closed')::int) closed_share,
        count(*) filter (where cat in {EMERG}) n_emerg,
        avg((st is null)::int) filter (where cat in {EMERG}) emerg_unknown_share
      from p join t on ST_Intersects(t.g, p.geometry) group by 1, 2""").df())
import pandas as pd
df = pd.concat(parts); df.to_parquet(f"{D}/poi-sources.parquet", index=False)
strata = " union all ".join(f"select '{r}' region, GEOID, pop_total, pct_urban, tribal_any, aiannh_name, svi_overall from '{D}/{r}-strata-tract-table.parquet'" for r in R)
con.sql(f"create view s as {strata}")
con.register("q", df)
con.sql("create view j as select s.*, q.* exclude (GEOID, region) from s join q using (GEOID, region) where n_places >= 20")
w = lambda c: f"round(100*sum({c}*n_places)/sum(n_places),1)"
print("== feed mix and verification by tribal x urban (tracts >= 20 places) ==")
print(con.sql(f"""select case when tribal_any then 'tribal' else 'non-tribal' end trib, case when pct_urban>=0.5 then 'urban' else 'rural' end ur,
  count(*) tracts, sum(pop_total)::int pop, {w('unknown_share')} pct_unknown, {w('signals_share')} pct_signals, {w('bq_share')} pct_bq,
  {w('closed_share')} pct_closed, sum(n_emerg) emerg, round(100*sum(emerg_unknown_share*n_emerg)/sum(n_emerg),1) pct_emerg_unknown
  from j group by 1,2 order by 1,2""").df().to_string(index=False))
print("== by region x urban ==")
print(con.sql(f"""select region, case when pct_urban>=0.5 then 'urban' else 'rural' end ur, count(*) tracts, {w('unknown_share')} pct_unknown, {w('closed_share')} pct_closed,
  round(100*sum(emerg_unknown_share*n_emerg)/sum(n_emerg),1) pct_emerg_unknown from j group by 1,2 order by 1,2""").df().to_string(index=False))
print("== correlation of closed_share with bq_share across tracts ==")
print(con.sql("select round(corr(closed_share, bq_share),3) r_bq, round(corr(closed_share, pct_urban),3) r_urban from j").df().to_string(index=False))
print("== worst tracts: most places never verified (>= 50 places) ==")
print(con.sql("""select region, GEOID, aiannh_name, pop_total::int pop, round(pct_urban,2) urb, n_places, round(100*unknown_share,1) pct_unknown,
  n_emerg, round(100*emerg_unknown_share,0) pct_emerg_unknown from j where n_places>=50 order by unknown_share desc limit 12""").df().to_string(index=False))
