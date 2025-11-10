import unittest
from unittest.mock import patch
from database.updater import DataUpdater

class TestDataUpdater(unittest.TestCase):
    @patch("database.updater.core.hybrid_aggregator.HybridAggregator.get_complete_analysis", return_value={
        "company_info": {"symbol": "TCS"},
        "price_history": None,
        "quarterly": None,
        "annual": None,
        "shareholding": None,
        "peers": None,
        "snapshot": {"symbol": "TCS"}
    })
    def test_update_stock(self, mock_analysis):
        updater = DataUpdater(db_path=":memory:")
        result = updater.update_stock("TCS", force=True)
        self.assertEqual(result.get("status"), "success")
