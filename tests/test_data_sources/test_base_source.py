import unittest
from data_sources.base_source import DataSource

class Dummy(DataSource):
    def __init__(self): super().__init__("Dummy")
    def get_company_info(self, symbol): return {"symbol": symbol}
    def get_price_data(self, symbol): return {"price": 1}
    def get_historical_prices(self, symbol, period="1y", interval="1d"): return {"history": []}
    def test_connection(self): return True

class TestBaseSource(unittest.TestCase):
    def test_error_handling(self):
        ds = Dummy()
        try:
            ds.handle_error(Exception("boom"), context="test")
        except Exception as e:
            self.fail(f"handle_error should not re-raise: {e}")
