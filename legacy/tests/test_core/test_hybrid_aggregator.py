import unittest
from unittest.mock import patch
from core.hybrid_aggregator import HybridAggregator

class TestHybridAggregator(unittest.TestCase):
    @patch("core.hybrid_aggregator.data_sources.nse_complete.NSEComplete.get_price_data")
    @patch("core.hybrid_aggregator.data_sources.screener_enhanced.ScreenerEnhanced.get_complete_data")
    @patch("core.hybrid_aggregator.data_sources.yahoo_finance.YahooFinance.get_historical_prices")
    def test_get_stock_data(self, mock_yf_hist, mock_screener, mock_nse_price):
        mock_yf_hist.return_value = {"history": []}
        mock_screener.return_value = {"company_info": {"name": "TCS"}}
        mock_nse_price.return_value = {"last_price": 3500}

        agg = HybridAggregator(use_cache=False)
        data = agg.get_stock_data("TCS")
        self.assertIn("price_data", data)
        self.assertIn("company_info", data)

    def test_batch_fetch(self):
        agg = HybridAggregator(use_cache=False)
        with patch.object(agg, "get_stock_data", return_value={"price_data": {"last_price": 1}}):
            results = agg.batch_fetch(["INFY", "TCS"], max_workers=2)
        self.assertEqual(len(results), 2)
        self.assertTrue(all("price_data" in v for v in results.values()))
