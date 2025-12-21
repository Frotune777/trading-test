# tests/_helpers/fake_dataframes.py
import pandas as pd

def sample_price_history(symbol="TCS", rows=5):
    dates = pd.date_range("2025-01-01", periods=rows, freq="D")
    return pd.DataFrame(
        {"date": dates, "open": 100, "high": 110, "low": 95, "close": 105, "volume": 12345}
    )

def sample_intraday(symbol="TCS", rows=10, interval="5m"):
    idx = pd.date_range("2025-01-01 09:15", periods=rows, freq=interval)
    return pd.DataFrame(
        {"datetime": idx, "open": 100, "high": 101, "low": 99, "close": 100.5, "volume": 5000}
    )
