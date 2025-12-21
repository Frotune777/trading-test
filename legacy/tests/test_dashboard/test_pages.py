import unittest
from unittest.mock import patch
from dashboard.pages.analytics import render_price_trend_chart
import pandas as pd

class TestPages(unittest.TestCase):
    @patch("dashboard.pages.analytics.plotly")
    def test_render_price_trend_chart(self, _):
        df = pd.DataFrame({"date": pd.date_range("2025-01-01", periods=5), "close": [1,2,3,4,5], "volume": [10]*5})
        render_price_trend_chart(df, "TCS")
