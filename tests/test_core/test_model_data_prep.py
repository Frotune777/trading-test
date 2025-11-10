import unittest
import pandas as pd
from core.model_data_prep import ModelDataPrep

class FakeNSE:
    def get_historical_prices(self, symbol, period="1y", interval="1d"):
        dates = pd.date_range("2024-01-01", periods=30, freq="D")
        return pd.DataFrame({"date": dates, "close": 100})

class FakeDB:
    def get_quarterly_results(self, symbol, limit=12): return pd.DataFrame()
    def get_annual_results(self, symbol, limit=10): return pd.DataFrame()
    def get_shareholding(self, symbol, limit=8): return pd.DataFrame()

class TestModelDataPrep(unittest.TestCase):
    def setUp(self):
        self.mdp = ModelDataPrep(nse=FakeNSE(), db=FakeDB())

    def test_prepare_price_prediction_data(self):
        data = self.mdp.prepare_price_prediction_data("TCS", lookback_days=30)
        self.assertIn("price_history", data)
        self.assertIn("quality", data)
