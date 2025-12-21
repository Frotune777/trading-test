# tests/_helpers/mock_responses.py
import datetime
import pandas as pd

def mock_nse_price_info(symbol="TCS"):
    return {
        "symbol": symbol, "last_price": 3520.5, "open": 3500.0, "high": 3550.0, "low": 3480.0,
        "volume": 1203456, "change": 0.6, "percent_change": 0.17
    }

def mock_nse_option_chain(symbol="NIFTY", indices=True):
    return pd.DataFrame({
        "strikePrice": [20000, 20100, 20200],
        "CE_OI": [100000, 85000, 90000],
        "PE_OI": [95000, 100500, 110000],
        "expiryDate": ["2025-11-27"] * 3
    })

def mock_yf_history(days=30):
    today = pd.Timestamp.today().normalize()
    dates = pd.date_range(end=today, periods=days, freq="D")
    return pd.DataFrame({"Date": dates, "Open": 100, "High": 105, "Low": 95, "Close": 102, "Volume": 100000})

def mock_screener_company_page(symbol="TCS"):
    return {
        "company_info": {"name": "Tata Consultancy Services", "symbol": symbol, "sector": "IT"},
        "key_metrics": {"ROE": "35%", "ROCE": "45%", "PE": "30", "Dividend Yield": "1.2%"},
        "quarterly": pd.DataFrame({"Quarter": ["Q1 FY25"], "Sales": [10000], "Profit": [2500]}),
        "ratios": pd.DataFrame({"Metric": ["ROE", "ROCE"], "Value": ["35", "45"]})
    }
