import unittest
from unittest.mock import patch
from examples.example_basic_usage import example_single_stock

class TestExamplesBasic(unittest.TestCase):
    @patch("core.hybrid_aggregator.HybridAggregator.get_stock_data", return_value={"price_data": {"last_price": 1}})
    def test_example_single_stock(self, _):
        # Should run without exceptions
        example_single_stock()
