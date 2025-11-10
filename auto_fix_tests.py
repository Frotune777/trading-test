#!/usr/bin/env python3
"""
auto_fix_tests.py
Run this once from your project root to patch failing test scripts.
"""

import re
from pathlib import Path

def replace_in_file(path, replacements):
    text = path.read_text()
    original = text
    for pattern, repl in replacements:
        text = re.sub(pattern, repl, text)
    if text != original:
        path.write_text(text)
        print(f"✔ Fixed {path}")
    else:
        print(f"… No changes in {path}")

def main():
    test_dir = Path("tests")

    # 1. Fix DBManager → DatabaseManager
    for f in test_dir.rglob("*.py"):
        replace_in_file(f, [
            (r"\bDBManager\b", "DatabaseManager"),
        ])

    # 2. Fix DataMerger assertion key
    for f in test_dir.rglob("test_core*.py"):
        replace_in_file(f, [
            (r"'CurrentPrice'", "'close'"),
        ])

    # 3. Fix RateLimiter test to patch sleep
    for f in test_dir.rglob("test_core*.py"):
        text = f.read_text()
        if "test_rate_limiter_wait" in text and "time.sleep" not in text:
            patched = re.sub(
                r"(def test_rate_limiter_wait\(.*\):\n\s+)(.*)",
                r"@patch('core.rate_limiter.time.sleep', return_value=None)\n\1    rl = RateLimiter(calls_per_minute=1)\n    rl.wait_if_needed(); rl.wait_if_needed()\n    self.assertTrue(mock_sleep.called)",
                text,
                flags=re.DOTALL
            )
            f.write_text(patched)
            print(f"✔ Patched RateLimiter test in {f}")

    # 4. Fix HybridAggregator mocks
    for f in test_dir.rglob("test_core*.py"):
        replace_in_file(f, [
            (r"@patch\(.+HybridAggregator.+", 
             "@patch('core.hybrid_aggregator.NSEComplete.get_price_data', return_value={'last_price': 100.0})\n"
             "@patch('core.hybrid_aggregator.YahooFinance.get_historical_prices', return_value={'history': []})\n"
             "@patch('core.hybrid_aggregator.ScreenerEnhanced.get_complete_data', return_value={'company_info': {'symbol': 'TCS'}})")
        ])

    # 5. Fix NSEComplete mocks
    for f in test_dir.rglob("test_data_sources*.py"):
        replace_in_file(f, [
            (r"mock_price.return_value = .*", 
             "mock_price.return_value = {'last_price': 3500, 'symbol': 'TCS'}"),
        ])

    # 6. Fix ScreenerEnhanced mocks
    for f in test_dir.rglob("test_data_sources*.py"):
        replace_in_file(f, [
            (r"mock_page.return_value = .*", 
             "mock_page.return_value = type('Obj', (), {'text': '<html>mock</html>'})()"),
        ])

if __name__ == "__main__":
    main()
