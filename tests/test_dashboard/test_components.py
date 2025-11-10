import unittest
import pandas as pd
from dashboard.components.tables import render_quarterly_results

class TestComponents(unittest.TestCase):
    def test_render_quarterly_results(self):
        df = pd.DataFrame({"Quarter": ["Q1 FY25"], "Sales": [10000]})
        # Should not raise
        render_quarterly_results(df)
