import unittest
from database.schema import SCHEMA_DEFINITIONS  # assuming a dict or similar

class TestSchema(unittest.TestCase):
    def test_schema_has_core_tables(self):
        core_tables = ["companies", "price_history", "snapshots"]
        for t in core_tables:
            self.assertIn(t, SCHEMA_DEFINITIONS)
