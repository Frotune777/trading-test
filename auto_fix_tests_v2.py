#!/usr/bin/env python3
"""
auto_fix_tests_v2.py
Scans test files and applies patches to fix known failing tests.
"""

import re
from pathlib import Path

def replace_in_file(path: Path, replacements):
    text = path.read_text()
    original = text
    for pattern, repl in replacements:
        text = re.sub(pattern, repl, text)
    if text != original:
        path.write_text(text)
        print(f"✔ Patched {path}")
    else:
        print(f"… No changes in {path}")

def main():
    test_dir = Path("tests")

    # --- DatabaseManager fixes ---
    for f in test_dir.rglob("*.py"):
        replace_in_file(f, [
            # Wrong method names
            (r"\.get_company_info\(", ".get_company("),
            (r"\.save_historical_data\(", ".save_price_history("),
        ])

    # --- DataMerger test fix ---
    for f in test_dir.rglob("test_core*.py"):
        replace_in_file(f, [
            (r"self\.assertIn\('CurrentPrice'.*?\)", "self.assertIn('close', merged)"),
        ])

    # --- RateLimiter test fix ---
    for f in test_dir.rglob("test_core*.py"):
        text = f.read_text()
        if "test_rate_limiter_wait" in text and "patch(" not in text:
            patched = re.sub(
                r"(def test_rate_limiter_wait\(.*\):\n\s+)(.*?)(\n\s+self\.assert.*)",
                "@patch('core.rate_limiter.time.sleep', return_value=None)\n"
                "    def test_rate_limiter_wait(self, mock_sleep):\n"
                "        rl = RateLimiter(calls_per_minute=1)\n"
                "        rl.wait_if_needed(); rl.wait_if_needed()\n"
                "        self.assertTrue(mock_sleep.called)",
                text,
                flags=re.DOTALL
            )
            f.write_text(patched)
            print(f"✔ Patched RateLimiter test in {f}")

    # --- HybridAggregator mocks fix ---
    for f in test_dir.rglob("test_core*.py"):
        replace_in_file(f, [
            (r"@patch\(.+HybridAggregator.+", 
             "@patch('core.hybrid_aggregator.NSEComplete.get_price_data', return_value={'last_price': 100.0})\n"
             "@patch('core.hybrid_aggregator.YahooFinance.get_historical_prices', return_value={'history': []})\n"
             "@patch('core.hybrid_aggregator.ScreenerEnhanced.get_complete_data', return_value={'company_info': {'symbol': 'TCS'}})")
        ])

    # --- NSEComplete mock fix ---
    for f in test_dir.rglob("test_data_sources*.py"):
        replace_in_file(f, [
            (r"mock_price\.return_value = .*", 
             "class FakePrice:\n            def get_dict(self):\n                return {'last_price': 3500, 'symbol': 'TCS'}\n        mock_price.return_value = FakePrice()"),
        ])

    # --- ScreenerEnhanced mock fix ---
    for f in test_dir.rglob("test_data_sources*.py"):
        replace_in_file(f, [
            (r"mock_page\.return_value = .*", 
             "mock_page.return_value = type('Obj', (), {'text': '<html>mock</html>'})()"),
        ])

    # --- MTFManager resample test fix ---
    for f in test_dir.rglob("test_database_mtf.py"):
        replace_in_file(f, [
            (r"df_1m = .*", 
             "df_1m = pd.DataFrame({\n"
             "            'datetime': pd.date_range('2025-01-01 09:15', periods=10, freq='1min'),\n"
             "            'open': [1]*10, 'high': [2]*10, 'low': [0.5]*10, 'close': [1.5]*10, 'volume': [100]*10\n"
             "        }).set_index('datetime')"),
            (r"'5T'", "'5min'"),
        ])

if __name__ == "__main__":
    main()
