import unittest
from unittest.mock import patch
from data_sources.screener_enhanced import ScreenerEnhanced

class TestScreenerEnhanced(unittest.TestCase):
    @patch("data_sources.screener_enhanced.ScreenerEnhanced._get_company_page")
    def test_get_complete_data(self, mock_page):
        mock_page.return_value = type("Obj", (), {"text": "<html>mock</html>"})
        sc = ScreenerEnhanced()
        with patch.object(sc, "_extract_company_info", return_value={"name": "TCS"}), \
             patch.object(sc, "_extract_key_metrics", return_value={"PE": "30"}):
            data = sc.get_complete_data("TCS")
        self.assertIn("company_info", data)
        self.assertIn("key_metrics", data)
