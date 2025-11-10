import unittest
from unittest.mock import patch
from unified_exporter import UnifiedExporter
import pandas as pd

class TestUnifiedExporter(unittest.TestCase):
    @patch("unified_exporter.core.hybrid_aggregator.HybridAggregator.get_complete_analysis", return_value={
        "price_history": pd.DataFrame({"date": ["2025-01-01"], "close": [100]}),
        "company_info": {"symbol": "TCS"},
        "quarterly": pd.DataFrame(),
        "annual": pd.DataFrame(),
        "shareholding": pd.DataFrame(),
        "peers": pd.DataFrame(),
        "snapshot": {"symbol": "TCS"}
    })
    def test_export_to_excel(self, _):
        exporter = UnifiedExporter(output_dir="._tmp_export")
        exporter.export_to_excel("TCS", filename="._tmp_export.xlsx")
