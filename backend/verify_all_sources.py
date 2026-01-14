from app.data_sources.nse_utils import NseUtils
import pandas as pd
import time

def audit_nse_utils():
    nse = NseUtils()
    print("Initializing NSE Session...")
    nse._establish_session() 
    print(f"Session Cookies: {len(nse.session.cookies)}")

    results = []

    def log_result(name, status, details=""):
        print(f"[{status}] {name}: {details}")
        results.append({"Method": name, "Status": status, "Details": details})

    # 1. Equity Info using NextApi (Known Working)
    try:
        data = nse.equity_info("TCS")
        if data and 'priceInfo' in data:
            log_result("equity_info", "PASS", f"Price: {data['priceInfo'].get('lastPrice')}")
        else:
            log_result("equity_info", "FAIL", "No data or missing 'priceInfo'")
    except Exception as e:
        log_result("equity_info", "ERROR", str(e))

    # 2. Historical/Periodic (Known Working via Chart API)
    try:
        df = nse.get_historical_data("TCS")
        if not df.empty:
            log_result("get_historical_data", "PASS", f"Rows: {len(df)}")
        else:
            log_result("get_historical_data", "FAIL", "Empty DataFrame")
    except Exception as e:
        log_result("get_historical_data", "ERROR", str(e))

    # 3. Option Chain (Known Failing)
    try:
        df = nse.get_option_chain("TCS")
        if not df.empty:
            log_result("get_option_chain", "PASS", f"Rows: {len(df)}")
        else:
            log_result("get_option_chain", "FAIL", "Empty DataFrame (Likely API issue)")
    except Exception as e:
        log_result("get_option_chain", "ERROR", str(e))
        
    # 4. Market Status / Gainers / Losers
    methods_to_test = [
        ("get_gainers_losers", [], {}), # Returns tuple (gainers, losers)
        ("get_index_pe_ratio", [], {}),
        ("get_index_pb_ratio", [], {}),
        ("get_index_div_yield", [], {}),
        ("get_advance_decline", [], {}),
        ("most_active_equity_stocks_by_volume", [], {}),
        ("most_active_equity_stocks_by_value", [], {}),
        ("most_active_index_calls", [], {}),
        ("most_active_index_puts", [], {}),
        ("most_active_stock_calls", [], {}),
        ("most_active_stock_puts", [], {}),
        ("most_active_contracts_by_oi", [], {}),
        ("most_active_contracts_by_volume", [], {}),
        ("most_active_futures_contracts_by_volume", [], {}),
        ("most_active_options_contracts_by_volume", [], {}),
        ("get_etf_list", [], {}),
        ("get_bulk_deals", [], {}),
        ("get_block_deals", [], {}),
        ("get_short_selling", [], {}),
        ("get_upcoming_results_calendar", [], {}),
    ]

    for name, args, kwargs in methods_to_test:
        try:
            method = getattr(nse, name)
            res = method(*args, **kwargs)
            if res is None:
                 log_result(name, "FAIL", "Returned None")
            elif isinstance(res, tuple):
                 empty = True
                 for item in res:
                     if isinstance(item, (dict, list)) and len(item) > 0:
                         empty = False
                 if empty:
                     log_result(name, "FAIL", "Returned tuple of empty items")
                 else:
                     log_result(name, "PASS", "Data found")
            elif isinstance(res, pd.DataFrame):
                if res.empty:
                    log_result(name, "FAIL", "Empty DataFrame")
                else:
                    log_result(name, "PASS", f"DataFrame rows: {len(res)}")
            else:
                 log_result(name, "PASS", f"Type: {type(res)}")
        except Exception as e:
            log_result(name, "ERROR", str(e))
        time.sleep(1) # Polite delay

    print("\n--- AUDIT REPORT ---")
    df_res = pd.DataFrame(results)
    print(df_res)
    
    # Save to file for easy reading by AI
    df_res.to_csv("audit_results.csv", index=False)

if __name__ == "__main__":
    audit_nse_utils()
