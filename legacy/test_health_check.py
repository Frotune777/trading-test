#!/usr/bin/env python3
"""
Quick health check for Fortune Trading platform
Run: python test_health_check.py
"""

import sys
from pathlib import Path
import traceback

# Color codes for terminal
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def test_result(passed: bool, test_name: str, details: str = ""):
    """Print colored test result"""
    if passed:
        print(f"{GREEN}✓{RESET} {test_name}")
        if details:
            print(f"  {BLUE}→{RESET} {details}")
    else:
        print(f"{RED}✗{RESET} {test_name}")
        if details:
            print(f"  {YELLOW}→{RESET} {details}")
    return passed

def test_imports():
    """Test 1: Check if core modules can be imported"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}TEST 1: Import Tests{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    results = {}
    
    # Test core imports
    try:
        import pandas
        results['pandas'] = test_result(True, "pandas", f"v{pandas.__version__}")
    except Exception as e:
        results['pandas'] = test_result(False, "pandas", str(e))
    
    try:
        import numpy
        results['numpy'] = test_result(True, "numpy", f"v{numpy.__version__}")
    except Exception as e:
        results['numpy'] = test_result(False, "numpy", str(e))
    
    try:
        import streamlit
        results['streamlit'] = test_result(True, "streamlit", f"v{streamlit.__version__}")
    except Exception as e:
        results['streamlit'] = test_result(False, "streamlit", str(e))
    
    # Test project imports
    try:
        from core.cache_manager import CacheManager
        results['core.cache_manager'] = test_result(True, "core.cache_manager")
    except Exception as e:
        results['core.cache_manager'] = test_result(False, "core.cache_manager", str(e))
    
    try:
        from database.db_manager import DatabaseManager
        results['database.db_manager'] = test_result(True, "database.db_manager")
    except Exception as e:
        results['database.db_manager'] = test_result(False, "database.db_manager", str(e))
    
    try:
        from data_sources.nse_complete import NSEComplete
        results['data_sources.nse_complete'] = test_result(True, "data_sources.nse_complete")
    except Exception as e:
        results['data_sources.nse_complete'] = test_result(False, "data_sources.nse_complete", str(e))
    
    try:
        from core.hybrid_aggregator import HybridAggregator
        results['core.hybrid_aggregator'] = test_result(True, "core.hybrid_aggregator")
    except Exception as e:
        results['core.hybrid_aggregator'] = test_result(False, "core.hybrid_aggregator", str(e))
    
    return results

def test_data_sources():
    """Test 2: Check if data sources are accessible"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}TEST 2: Data Source Connectivity{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    results = {}
    
    # Test NSE
    try:
        from data_sources.nse_complete import NSEComplete
        nse = NSEComplete()
        test_result(True, "NSE instance created")
        
        # Test connection
        is_connected = nse.test_connection()
        results['nse_connection'] = test_result(
            is_connected, 
            "NSE connection test",
            "Connected" if is_connected else "Failed"
        )
        
        # Test a simple query
        try:
            holidays = nse.trading_holidays(list_only=True)
            results['nse_query'] = test_result(
                holidays is not None,
                "NSE query test (trading holidays)",
                f"{len(holidays) if holidays else 0} holidays found"
            )
        except Exception as e:
            results['nse_query'] = test_result(False, "NSE query test", str(e))
            
    except Exception as e:
        results['nse_init'] = test_result(False, "NSE initialization", str(e))
        traceback.print_exc()
    
    # Test Yahoo Finance
    try:
        from data_sources.yahoo_finance import YahooFinance
        yahoo = YahooFinance()
        results['yahoo_init'] = test_result(True, "Yahoo Finance initialized")
        
        # Quick test
        try:
            data = yahoo.get_price_data("RELIANCE")
            results['yahoo_query'] = test_result(
                data is not None and 'current_price' in data,
                "Yahoo Finance query test",
                f"Price: ₹{data.get('current_price', 'N/A')}" if data else "Failed"
            )
        except Exception as e:
            results['yahoo_query'] = test_result(False, "Yahoo Finance query", str(e))
            
    except Exception as e:
        results['yahoo_init'] = test_result(False, "Yahoo Finance initialization", str(e))
    
    # Test Screener
    try:
        from data_sources.screener_enhanced import ScreenerEnhanced
        screener = ScreenerEnhanced()
        results['screener_init'] = test_result(True, "Screener initialized")
        
        print(f"  {YELLOW}⚠{RESET}  Screener query test skipped (slow, requires web scraping)")
        
    except Exception as e:
        results['screener_init'] = test_result(False, "Screener initialization", str(e))
    
    return results

def test_database():
    """Test 3: Database operations"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}TEST 3: Database Operations{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    results = {}
    
    try:
        from database.db_manager import DatabaseManager
        
        # Use test database
        db = DatabaseManager(db_path='test_health.db')
        results['db_init'] = test_result(True, "Database initialized")
        
        # Test add company
        try:
            db.add_company(
                symbol="TEST",
                company_name="Test Company",
                sector="Technology"
            )
            results['db_write'] = test_result(True, "Database write (add company)")
        except Exception as e:
            results['db_write'] = test_result(False, "Database write", str(e))
        
        # Test read
        try:
            company = db.get_company("TEST")
            results['db_read'] = test_result(
                company is not None,
                "Database read (get company)",
                f"Found: {company.get('company_name', 'N/A')}" if company else "Not found"
            )
        except Exception as e:
            results['db_read'] = test_result(False, "Database read", str(e))
        
        # Test stats
        try:
            stats = db.get_database_stats()
            results['db_stats'] = test_result(
                stats is not None,
                "Database stats",
                f"{stats.get('total_companies', 0)} companies"
            )
        except Exception as e:
            results['db_stats'] = test_result(False, "Database stats", str(e))
        
        db.close()
        
        # Clean up test database
        test_db_path = Path('test_health.db')
        if test_db_path.exists():
            test_db_path.unlink()
            print(f"  {BLUE}→{RESET} Test database cleaned up")
            
    except Exception as e:
        results['db_init'] = test_result(False, "Database initialization", str(e))
        traceback.print_exc()
    
    return results

def test_core_functionality():
    """Test 4: Core functionality"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}TEST 4: Core Functionality{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    results = {}
    
    # Test Cache Manager
    try:
        from core.cache_manager import CacheManager
        cache = CacheManager(cache_dir='.test_cache')
        
        cache.set('test_key', {'value': 123}, ttl=60)
        cached_value = cache.get('test_key')
        
        results['cache'] = test_result(
            cached_value is not None and cached_value.get('value') == 123,
            "Cache Manager",
            "Set/Get working"
        )
        
        # Cleanup
        cache.clear()
        import shutil
        shutil.rmtree('.test_cache', ignore_errors=True)
        
    except Exception as e:
        results['cache'] = test_result(False, "Cache Manager", str(e))
    
    # Test Hybrid Aggregator
    try:
        from core.hybrid_aggregator import HybridAggregator
        aggregator = HybridAggregator(use_cache=False)
        results['aggregator_init'] = test_result(True, "Hybrid Aggregator initialized")
        
        print(f"  {YELLOW}⚠{RESET}  Full aggregation test skipped (slow)")
        
    except Exception as e:
        results['aggregator_init'] = test_result(False, "Hybrid Aggregator", str(e))
    
    # Test MTF Manager
    try:
        from core.mtf_manager import MTFDataManager, TimeFrame
        
        # Test TimeFrame utilities
        minutes = TimeFrame.get_minutes('1h')
        results['timeframe'] = test_result(
            minutes == 60,
            "TimeFrame utilities",
            f"1h = {minutes} minutes"
        )
        
    except Exception as e:
        results['timeframe'] = test_result(False, "TimeFrame utilities", str(e))
    
    return results

def test_dashboard():
    """Test 5: Dashboard components"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}TEST 5: Dashboard Components{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    results = {}
    
    # Check which app file exists
    app_files = {
        'app.py': Path('dashboard/app.py'),
        'app_v3.py': Path('dashboard/app_v3.py')
    }
    
    for name, path in app_files.items():
        results[name] = test_result(
            path.exists(),
            f"Dashboard {name}",
            "Found" if path.exists() else "Missing"
        )
    
    # Test dashboard utilities
    try:
        from dashboard.utils.formatters import safe_format_currency, safe_format_percent
        
        currency = safe_format_currency(1234.56)
        percent = safe_format_percent(12.34)
        
        results['formatters'] = test_result(
            '1,234' in currency and '12.34' in percent,
            "Dashboard formatters",
            f"{currency}, {percent}"
        )
    except Exception as e:
        results['formatters'] = test_result(False, "Dashboard formatters", str(e))
    
    # Test page imports
    try:
        from dashboard.pages import analytics, data_manager, research
        results['pages'] = test_result(True, "Dashboard pages import")
    except Exception as e:
        results['pages'] = test_result(False, "Dashboard pages import", str(e))
    
    return results

def print_summary(all_results):
    """Print overall summary"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}SUMMARY{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    total_tests = sum(len(results) for results in all_results.values())
    passed_tests = sum(
        sum(1 for result in results.values() if result)
        for results in all_results.values()
    )
    
    percentage = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {GREEN}{passed_tests}{RESET}")
    print(f"Failed: {RED}{total_tests - passed_tests}{RESET}")
    print(f"Success Rate: {GREEN if percentage > 80 else YELLOW if percentage > 50 else RED}{percentage:.1f}%{RESET}")
    
    if percentage == 100:
        print(f"\n{GREEN}🎉 ALL TESTS PASSED!{RESET}")
    elif percentage > 80:
        print(f"\n{YELLOW}⚠️  MOSTLY WORKING - Some issues to fix{RESET}")
    else:
        print(f"\n{RED}❌ CRITICAL ISSUES - Needs attention{RESET}")
    
    return percentage

def main():
    """Run all tests"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}FORTUNE TRADING - HEALTH CHECK{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    
    all_results = {}
    
    try:
        all_results['imports'] = test_imports()
        all_results['data_sources'] = test_data_sources()
        all_results['database'] = test_database()
        all_results['core'] = test_core_functionality()
        all_results['dashboard'] = test_dashboard()
        
        percentage = print_summary(all_results)
        
        # Exit code
        sys.exit(0 if percentage > 80 else 1)
        
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}⚠️  Tests interrupted by user{RESET}")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n{RED}❌ FATAL ERROR:{RESET}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()