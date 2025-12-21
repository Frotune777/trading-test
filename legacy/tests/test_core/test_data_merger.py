import unittest
from core.data_merger import DataMerger, DataQualityChecker

class TestDataMerger(unittest.TestCase):
    def test_merge_price_data_priority(self):
        sources = [
            {"source": "NSE", "close": 101, "volume": 1000},
            {"source": "YF", "close": 99, "volume": 900},
        ]
        merged = DataMerger.merge_price_data(sources, priority=["NSE", "YF"])
        self.assertEqual(merged["close"], 101)

    def test_validate_price_data(self):
        data = {"close": 101, "open": 100, "high": 105, "low": 99, "volume": 1000}
        validated = DataMerger.validate_price_data(data)
        self.assertEqual(validated["close"], 101)

class TestDataQualityChecker(unittest.TestCase):
    def test_assess_quality(self):
        dq = DataQualityChecker.assess_quality({"completeness": 0.9, "consistency": 0.95})
        self.assertIn("grade", dq)
        self.assertIn(dq["grade"], ["A", "B", "C", "D", "E"])
