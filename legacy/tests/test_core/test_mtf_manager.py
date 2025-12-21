import unittest
import pandas as pd
from core.mtf_manager import MTFDataManager, TimeFrame

class FakeDB: pass
class FakeNSE:
    def get_intraday_data(self, symbol, interval="5m"):
        idx = pd.date_range("2025-01-01 09:15", periods=10, freq="5T")
        return pd.DataFrame({"datetime": idx, "open": 1, "high": 2, "low": 0.5, "close": 1.5, "volume": 100})

class TestMTFManager(unittest.TestCase):
    def test_timeframe_conversions(self):
        self.assertEqual(TimeFrame.get_minutes("5m"), 5)
        self.assertEqual(TimeFrame.get_higher_timeframe("5m"), "15m")

    def test_get_mtf_data(self):
        mtf = MTFDataManager(db_manager=FakeDB(), nse_source=FakeNSE())
        data = mtf.get_mtf_data("TCS", timeframes=["5m", "1d"], lookback_days=1)
        self.assertIn("5m", data)
        self.assertIn("1d", data)
