import unittest
from unittest.mock import patch
from data_sources.yahoo_finance import YahooFinance

class FakeTicker:
    def info(self): return {"symbol": "TCS"}
    def history(self, period="1y", interval="1d"):
        import pandas as pd
        return pd.DataFrame({"Close": [100]})

class TestYahooFinance(unittest.TestCase):
    @patch("data_sources.yahoo_finance.yfinance.Ticker", return_value=FakeTicker())
    def test_get_company_info(self, _):
        yf = YahooFinance()
        info = yf.get_company("TCS")
        self.assertIn("symbol", info)

    @patch("data_sources.yahoo_finance.yfinance.Ticker", return_value=FakeTicker())
    def test_get_historical_prices(self, _):
        yf = YahooFinance()
        hist = yf.get_historical_prices("TCS")
        self.assertIn("history", hist)
