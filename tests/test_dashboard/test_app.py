import unittest
from unittest.mock import patch
from dashboard import app

class TestDashboardApp(unittest.TestCase):
    @patch("dashboard.app.get_nse")
    def test_validate_nse_symbol(self, mock_get_nse):
        class FakeNSE:
            def search_symbol(self, symbol, exchange="NSE"): return {"symbol": symbol}
        mock_get_nse.return_value = FakeNSE()
        self.assertTrue(app.validate_nse_symbol("TCS"))
