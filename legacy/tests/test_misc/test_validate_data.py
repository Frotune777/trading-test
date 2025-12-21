import unittest
import pandas as pd
from validate_data import DataValidator

class TestValidateData(unittest.TestCase):
    def test_validate_ohlcv(self):
        dv = DataValidator()
        df = pd.DataFrame({"date": pd.date_range("2025-01-01", periods=5),
                           "open": [1]*5, "high": [2]*5, "low": [0.5]*5, "close": [1.5]*5, "volume": [100]*5})
        dv._validate_ohlcv_data("prices.csv", df)  # Should not raise
