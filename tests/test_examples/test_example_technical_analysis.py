import unittest
from examples.example_technical_analysis import calculate_rsi
import pandas as pd

class TestExamplesTA(unittest.TestCase):
    def test_calculate_rsi(self):
        df = pd.DataFrame({"Close": [i for i in range(1, 30)]})
        rsi = calculate_rsi(df, period=14)
        self.assertIn("RSI", rsi.columns)
