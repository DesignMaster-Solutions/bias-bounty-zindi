"""Exercise the actual spatial aggregation with unknown statuses in its denominator."""
import sys
import tempfile
import unittest
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import discovery


class ClosureDenominatorTest(unittest.TestCase):
    def check_statuses(self, statuses, expected):
        with tempfile.TemporaryDirectory() as directory:
            con = duckdb.connect()
            con.sql('LOAD spatial')
            con.sql("CREATE TABLE tracts AS SELECT '04001000100' GEOID, ST_GeomFromText('POLYGON((0 0,0 2,2 2,2 0,0 0))') geometry")
            con.sql(f"COPY tracts TO '{directory}/fixture-census-tracts.parquet' (FORMAT PARQUET)")
            con.sql('CREATE TABLE states (operating_status VARCHAR)')
            con.executemany('INSERT INTO states VALUES (?)', [(s,) for s in statuses])
            con.sql(f"""COPY (SELECT row_number() over () id,
              struct_pack("primary" := 'fire_department') categories,
              0.8 confidence, operating_status,
              [struct_pack(dataset := 'meta')] sources,
              ST_Point(1,1) geometry FROM states)
              TO '{directory}/fixture-overture-pois.parquet' (FORMAT PARQUET)""")
            original = discovery.D
            try:
                discovery.D = directory
                row = discovery.quality(con, 'fixture').iloc[0]
                self.assertEqual(row.n_places, len(statuses))
                self.assertAlmostEqual(row.closed_share, expected)
            finally:
                discovery.D = original
                con.close()

    def test_unknown_status_is_in_all_places_denominator(self):
        self.check_statuses(['permanently_closed', 'open', None, None], 0.25)

    def test_all_unknown_has_zero_recorded_closures(self):
        self.check_statuses([None, None], 0.0)

    def test_fully_observed_denominator_unchanged(self):
        self.check_statuses(['permanently_closed', 'open'], 0.5)


if __name__ == '__main__':
    unittest.main()
