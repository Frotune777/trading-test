import unittest
from unittest.mock import patch
from data_sources.nse_complete import NSEComplete

class TestNSECompleteIntegration(unittest.TestCase):
    @patch("data_sources.nse_complete.nse_utils.NseUtils.price_info", return_value={"last_price": 123})
    @patch("data_sources.nse_complete.nse_utils.NseUtils.equity_bhav_copy")
    def test_get_complete_data(self, mock_bhav, mock_price):
        import pandas as pd
        mock_bhav.return_value = pd.DataFrame({"symbol": ["TCS"], "close": [123]})
        nse = NSEComplete()
        data = nse.get_complete_data("TCS")
        self.assertIn("price_data", data)
        self.assertIn("history", data)
