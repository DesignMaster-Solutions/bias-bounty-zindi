"""Per-tract features from the challenge package (Overture + ACS + strata only; no reference layers)."""
import sys, os, duckdb

D = os.path.join(os.path.dirname(__file__), "..", "data")
HIFLD_SCHOOL = "('elementary_school','middle_school','high_school','school','private_school','public_school')"


def region_features(con, r):
    p = lambda name: f"'{D}/{r}-{name}.parquet'"
    con.sql(f"create or replace temp table t as select GEOID, geometry g from {p('census-tracts')}")
    poi = con.sql(f"""
      select t.GEOID, count(*) n_places,
        count(*) filter (where categories.primary='fire_department') n_fire,
        count(*) filter (where categories.primary='ambulance_and_ems_services') n_ems,
        count(*) filter (where categories.primary in {HIFLD_SCHOOL}) n_school
      from {p('overture-pois')} q join t on ST_Intersects(t.g, q.geometry) group by 1""").df()
    out = poi
    roads = f"{D}/{r}-overture-roads.parquet"
    if os.path.exists(roads):
        rd = con.sql(f"""
          with seg as (select t.GEOID, q.class,
              ST_Length(ST_Transform(ST_Intersection(t.g, q.geometry), 'EPSG:4326','EPSG:5070', always_xy:=true))/1000 km
            from '{roads}' q join t on ST_Intersects(t.g, q.geometry))
          select GEOID, sum(km) filter (where class in ('motorway','trunk','primary','secondary')) km_highway,
            sum(km) km_roads from seg group by 1""").df()
        out = out.merge(rd, on="GEOID", how="outer")
    bld = f"{D}/{r}-overture-buildings.parquet"
    if os.path.exists(bld):
        b = con.sql(f"""select t.GEOID, count(*) n_buildings from '{bld}' q
          join t on ST_Intersects(t.g, ST_Centroid(q.geometry)) group by 1""").df()
        out = out.merge(b, on="GEOID", how="outer")
    return out


if __name__ == "__main__":
    con = duckdb.connect()
    con.sql("INSTALL spatial; LOAD spatial;")
    for r in sys.argv[1:]:
        df = region_features(con, r)
        df.to_parquet(f"{D}/{r}-features.parquet")
        print(r, len(df), df.describe().T[["mean", "50%"]].to_string())
