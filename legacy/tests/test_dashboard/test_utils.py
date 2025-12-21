import unittest
from dashboard.utils.formatters import safe_format_currency, format_time_ago
from datetime import datetime, timedelta

class TestUtils(unittest.TestCase):
    def test_currency(self):
        s = safe_format_currency(1234.567, decimals=2)
        self.assertIn("₹", s)

    def test_time_ago(self):
        s = format_time_ago(datetime.utcnow() - timedelta(hours=2))
        self.assertTrue("ago" in s.lower())
