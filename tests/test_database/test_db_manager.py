import unittest
import tempfile
import os
import pandas as pd
from database.db_manager import DatabaseManager

class TestDatabaseManager(unittest.TestCase):
    def setUp(self):
        self.db_path = tempfile.mktemp(suffix=".db")
        self.db = DatabaseManager(db_path=self.db_path)

    def tearDown(self):
        self.db.close()
        if os.path.exists(self.db_path): os.remove(self.db_path)

    def test_add_and_get_company(self):
        self.db.add_company("TCS", "Tata Consultancy Services")
        company = self.db.get_company("TCS")
        self.assertEqual(company["symbol"], "TCS")

    def test_price_history_roundtrip(self):
        df = pd.DataFrame({"date": ["2025-01-01"], "open": [100], "high": [110], "low": [95], "close": [105], "volume": [1000]})
        self.db.save_price_history("TCS", df)
        out = self.db.get_price_history("TCS")
        self.assertFalse(out.empty)
