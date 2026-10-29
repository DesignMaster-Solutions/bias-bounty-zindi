"""Heuristic coverage-gap estimate per tract (no labels, no reference layers; see METHODOLOGY.md)."""
import os, sys
import numpy as np, pandas as pd

D = os.path.join(os.path.dirname(__file__), "..", "data")
REGIONS = ["eastern-ok", "eastern-wa", "maricopa-az", "northern-ca", "south-central-tx"]
# knobs (calibrated only as global constants, never per tract)
K = dict(estab_per_person=0.03, building=0.03, transport=0.15, fire_missing=0.6, fire_present=0.05,
         people_per_school=2500)


def estimate(r, k=K):
    sub = pd.read_csv(f"{D}/SampleSubmission_zindi.csv", dtype={"GEOID": str})
    sub = sub[sub.region == r][["GEOID", "region"]]
    fp = f"{D}/{r}-features.parquet"
    # shortcut: region without features yet falls back to the POI-only table (no schools/roads)
    f = pd.read_parquet(fp) if os.path.exists(fp) else pd.read_parquet(f"{D}/poi-quality.parquet").query("region == @r")[
        ["GEOID", "n_places", "n_fire"]].assign(n_school=1, km_highway=1)
    s = pd.read_parquet(f"{D}/{r}-strata-tract-table.parquet", columns=["GEOID", "pop_total"])
    df = sub.merge(f, on="GEOID", how="left").merge(s, on="GEOID", how="left").fillna(0)
    pop = df.pop_total.clip(lower=1)
    cbp = (1 - df.n_places / (k["estab_per_person"] * pop)).clip(0, 1)
    fire = np.where(df.n_fire > 0, k["fire_present"], k["fire_missing"])
    school = (1 - df.n_school / np.maximum(1, pop / k["people_per_school"])).clip(0, 1)
    df["poi_gap"] = (cbp + (fire + school) / 2) / 2
    df["building_gap"] = k["building"]
    df["transport_gap"] = np.where(df.get("km_highway", 0) > 0, k["transport"], np.nan)
    df["coverage_gap_score"] = df[["transport_gap", "building_gap", "poi_gap"]].mean(axis=1)
    return df


if __name__ == "__main__":
    regs = REGIONS
    out = pd.concat([estimate(r) for r in regs])
    print(out.groupby("region").coverage_gap_score.describe())
    full = pd.read_csv(f"{D}/SampleSubmission_zindi.csv", dtype={"GEOID": str})[["GEOID"]]
    full = full.merge(out[["GEOID", "coverage_gap_score"]], on="GEOID", how="left")
    print("missing:", full.coverage_gap_score.isna().sum())
    if len(sys.argv) > 1:
        full.fillna(full.coverage_gap_score.mean()).to_csv(sys.argv[1], index=False)
