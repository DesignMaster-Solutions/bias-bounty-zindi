"""Quantify the place-trust discovery against strata the scorecard does not combine.
Run after src/discovery.py (needs data/poi-quality.parquet)."""
import os, duckdb
D = os.path.join(os.path.dirname(__file__), "..", "data")
con = duckdb.connect()
R = ["eastern-ok", "eastern-wa", "maricopa-az", "northern-ca", "south-central-tx"]
strata = " union all ".join(
    f"select '{r}' region, GEOID, pop_total, pct_urban, tribal_any, aiannh_name, svi_overall from '{D}/{r}-strata-tract-table.parquet'" for r in R)
con.sql(f"create view s as {strata}")
con.sql(f"""create view j as select s.*, q.n_places, q.closed_share, q.mean_conf, q.lowconf_share, q.meta_only_share, q.n_fire, q.fire_conf
  from s join '{D}/poi-quality.parquet' q using (GEOID, region) where q.n_places >= 20""")
print("== by tribal x urban (tracts with >= 20 places) ==")
print(con.sql("""select case when tribal_any then 'tribal' else 'non-tribal' end trib,
   case when pct_urban >= 0.5 then 'urban' else 'rural' end ur, count(*) tracts, sum(pop_total)::int pop,
   round(100*sum(closed_share*n_places)/sum(n_places),2) pct_closed, round(avg(mean_conf),3) conf,
   round(100*sum(meta_only_share*n_places)/sum(n_places),1) pct_meta_only,
   round(100*avg((closed_share=0)::int),1) pct_tracts_zero_closed
 from j group by 1,2 order by 1,2""").df().to_string(index=False))
print("== by SVI quartile ==")
print(con.sql("""select ntile(4) over (order by svi_overall) q, * from j where svi_overall is not null""").df()
  .groupby("q").apply(lambda g: (g.closed_share*g.n_places).sum()/g.n_places.sum()*100).round(2).to_string())
print("== named tribal areas: places, closed, confidence ==")
print(con.sql("""select region, aiannh_name, count(*) tracts, sum(n_places) places,
   round(100*sum(closed_share*n_places)/sum(n_places),2) pct_closed, round(avg(mean_conf),3) conf,
   round(100*sum(meta_only_share*n_places)/sum(n_places),1) pct_meta_only
 from j where tribal_any and aiannh_name is not null group by 1,2 having count(*)>=3 order by places desc limit 15""").df().to_string(index=False))
