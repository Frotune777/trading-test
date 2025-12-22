import logging
import pandas as pd
from datetime import datetime
from .unified_data_service import UnifiedDataService
from ..database.db_manager import DatabaseManager
from ..data_sources.nse_utils import NseUtils

logger = logging.getLogger(__name__)

class DataSyncService:
    """
    Orchestrates the fetching and saving of data to the database.
    Ensures the system is populated for the frontend.
    """
    
    def __init__(self, db_path: str = 'stock_data.db'):
        self.uds = UnifiedDataService()
        self.db = DatabaseManager(db_path)
        self.nse_utils = NseUtils()

    def sync_stock(self, symbol: str):
        """Perform a full sync for a single stock."""
        logger.info(f"🚀 Starting full sync for {symbol}")
        try:
            # 1. Comprehensive Data (UDS)
            data = self.uds.get_comprehensive_data(symbol)
            
            # Save Company Master
            info = data.get('company_info', {})
            self.db.add_company(
                symbol=symbol,
                company_name=info.get('company_name'),
                sector=info.get('sector'),
                industry=info.get('industry'),
                isin=info.get('isin')
            )
            
            # Save Snapshot
            snapshot_data = data.get('price_data', {})
            # Merge with key metrics for a complete snapshot
            snapshot_data.update(data.get('key_metrics', {}))
            self.db.update_snapshot(symbol, snapshot_data)
            
            # Save Financials
            financials = data.get('financials', {})
            if financials.get('quarterly'):
                self.db.save_quarterly_results(symbol, pd.DataFrame(financials['quarterly']))
            if financials.get('annual'):
                self.db.save_annual_results(symbol, pd.DataFrame(financials['annual']))
            if financials.get('balance_sheet'):
                self.db.save_balance_sheet(symbol, pd.DataFrame(financials['balance_sheet']))
            if financials.get('cash_flow'):
                self.db.save_cash_flow(symbol, pd.DataFrame(financials['cash_flow']))
            if financials.get('shareholding'):
                self.db.save_shareholding(symbol, pd.DataFrame(financials['shareholding']))
            if financials.get('peers'):
                self.db.save_peers(symbol, pd.DataFrame(financials['peers']))
                
            # 2. Derivatives (Option Chain)
            # Use nse_utils directly for fresh data
            is_index = symbol.upper() in ['NIFTY', 'BANKNIFTY', 'FINNIFTY']
            option_chain_df = self.nse_utils.get_option_chain(symbol, indices=is_index)
            if option_chain_df is not None and not option_chain_df.empty:
                self.db.save_option_chain(option_chain_df)
                
            # 3. Futures
            futures_df = self.nse_utils.futures_data(symbol, indices=is_index)
            if futures_df is not None and not futures_df.empty:
                self.db.save_futures_data(futures_df)

            logger.info(f"✅ Full sync completed for {symbol}")
            return True
        except Exception as e:
            logger.error(f"❌ Error syncing {symbol}: {e}")
            return False

    def sync_institutional_deals(self):
        """Sync market-wide institutional activities."""
        logger.info("📡 Syncing Institutional Deals...")
        try:
            # Bulk Deals
            bulk = self.nse_utils.get_bulk_deals()
            self.db.save_bulk_deals(bulk)
            
            # Block Deals
            block = self.nse_utils.get_block_deals()
            self.db.save_block_deals(block)
            
            # Insider Trading
            insider = self.nse_utils.get_insider_trading()
            self.db.save_insider_trading(insider)
            
            logger.info("✅ Institutional sync completed")
            return True
        except Exception as e:
            logger.error(f"❌ Error syncing institutional: {e}")
            return False
