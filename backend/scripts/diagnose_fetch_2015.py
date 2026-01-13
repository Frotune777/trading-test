import asyncio
from nselib import capital_market
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_nselib_year(symbol, year):
    logger.info(f"Testing nselib for {symbol} in {year}...")
    try:
        data = capital_market.price_volume_and_deliverable_position_data(
            symbol=symbol, 
            from_date=f'01-01-{year}', 
            to_date=f'31-12-{year}'
        )
        if data is None or data.empty:
             logger.warning(f"  ❌ nselib returned empty/None for {symbol} in {year}")
        else:
             logger.info(f"  ✅ nselib fetched {len(data)} records for {symbol} in {year}")
             print(data.head(1))
    except Exception as e:
        logger.error(f"  ❌ nselib error for {symbol} in {year}: {e}")

if __name__ == "__main__":
    test_nselib_year("BPCL", 2015)
    test_nselib_year("BPCL", 2016)
    test_nselib_year("BPCL", 2023)
