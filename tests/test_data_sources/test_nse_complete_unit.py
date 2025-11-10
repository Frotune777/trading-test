import unittest
from unittest.mock import patch
from data_sources.nse_complete import NSEComplete

class TestNSECompleteUnit(unittest.TestCase):
    def setUp(self):
        self.nse = NSEComplete()

    @patch("data_sources.nse_complete.nse_utils.NseUtils.price_info")
    def test_get_price_data(self, mock_price):
        mock_price.return_value = {"last_price": 3500, "symbol": "TCS"}
        data = self.nse.get_price_data("TCS")
        self.assertIn("last_price", data)

    @patch("data_sources.nse_complete.nse_utils.NseUtils.get_option_chain")
    def test_get_option_chain(self, mock_chain):
        import pandas as pd
        mock_chain.return_value = pd.DataFrame({"strikePrice": [20000]})
        df = self.nse.get_option_chain("NIFTY", indices=True)
        self.assertFalse(df.empty)

    @patch("data_sources.nse_complete.nse_master_data.NSEMasterData.search")
    def test_search_symbol(self, mock_search):
        mock_search.return_value = [{"symbol": "TCS"}]
        res = self.nse.search("TCS", exchange="NSE")
        self.assertEqual(res[0]["symbol"], "TCS")
