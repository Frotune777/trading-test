import asyncio
from nselib import capital_market
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_nselib(symbol):
    logger.info(f"Testing nselib for {symbol}...")
    try:
        data = capital_market.price_volume_and_deliverable_position_data(
            symbol=symbol, 
            from_date='01-01-2024', 
            to_date='10-01-2024'
        )
        if data is None or data.empty:
             logger.warning(f"  ❌ nselib returned empty/None for {symbol}")
        else:
             logger.info(f"  ✅ nselib fetched {len(data)} records for {symbol}")
             print(data.head(1))
    except Exception as e:
        logger.error(f"  ❌ nselib error for {symbol}: {e}")

def test_yfinance(symbol):
    logger.info(f"Testing yfinance for {symbol}...")
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(start="2024-01-01", end="2024-01-10")
        if data is None or data.empty:
             logger.warning(f"  ❌ yfinance returned empty/None for {symbol}")
        else:
             logger.info(f"  ✅ yfinance fetched {len(data)} records for {symbol}")
             print(data.head(1))
    except Exception as e:
        logger.error(f"  ❌ yfinance error for {symbol}: {e}")

if __name__ == "__main__":
    logger.info("--- DIAGNOSTIC START ---")
    
    # Test 1: Plain Symbol
    test_nselib("BPCL")
    test_yfinance("BPCL.NS")

    # Test 2: With EQ suffix
    test_nselib("BPCL-EQ") # nselib might not like this
    
    # Test 3: Infosys (known good?)
    test_nselib("INFY")
    
    logger.info("--- DIAGNOSTIC END ---")
