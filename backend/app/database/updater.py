"""
Data Updater - Fetches data from sources and stores in database
Handles both NSE market data and Screener fundamentals
"""

from typing import List, Dict, Optional
import logging
from datetime import datetime
import time
import re
import pandas as pd

from .db_manager import DatabaseManager
from ..services.data_aggregator import HybridAggregator
from ..services.data_aggregator import HybridAggregator
from ..data_sources.nse_derivatives import NSEDerivatives
from ..data_sources.nse_utils import NseUtils
from ..services.technical_analysis import TechnicalAnalysisService

logger = logging.getLogger(__name__)


class DataUpdater:
    """Update database with fresh data from all sources."""
    
    def __init__(self, db_path: str = 'stock_data.db'):
        self.db = DatabaseManager(db_path)
        self.aggregator = HybridAggregator()
        self.derivatives = NSEDerivatives()
        self.nse_utils = NseUtils()
    
    def update_stock(self, symbol: str, force: bool = False) -> Dict[str, any]:
        """
        Update all data for a symbol.
        """
        start_time = time.time()
        
        logger.info(f"{'='*60}")
        logger.info(f"Updating {symbol}")
        logger.info(f"{'='*60}")
        
        # Check if update is needed
        if not force and not self.db.needs_update(symbol, hours=24):
            last_update = self.db.get_last_update(symbol)
            logger.info(f"⏭️  {symbol} was updated recently ({last_update}). Use force=True to update anyway.")
            return {
                'symbol': symbol,
                'skipped': True,
                'last_update': last_update,
                'message': 'Recently updated'
            }
        
        results = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'updates': {},
            'errors': []
        }
        
        try:
            # Get complete data from all sources
            logger.info(f"📥 Fetching complete data for {symbol}...")
            data = self.aggregator.get_complete_analysis(symbol)
            
            if not data:
                logger.error(f"❌ No data received for {symbol}")
                results['errors'].append('No data received from sources')
                return results
            
            # 1. Update company info
            try:
                self._update_company_info(symbol, data)
                results['updates']['company_info'] = 'success'
            except Exception as e:
                logger.error(f"Error updating company info: {e}")
                results['updates']['company_info'] = 'error'
                results['errors'].append(f"Company info: {str(e)}")
            
            # 2. Update latest snapshot
            try:
                self._update_snapshot(symbol, data)
                results['updates']['snapshot'] = 'success'
            except Exception as e:
                logger.error(f"Error updating snapshot: {e}")
                results['updates']['snapshot'] = 'error'
                results['errors'].append(f"Snapshot: {str(e)}")
            
            # 3. Update price history
            try:
                count = self._update_price_history(symbol, data)
                results['updates']['price_history'] = f'success ({count} records)'
            except Exception as e:
                logger.error(f"Error updating price history: {e}")
                results['updates']['price_history'] = 'error'
                results['errors'].append(f"Price history: {str(e)}")
            
            # 4. Update quarterly results
            try:
                self._update_quarterly_results(symbol, data)
                results['updates']['quarterly'] = 'success'
            except Exception as e:
                logger.error(f"Error updating quarterly results: {e}")
                results['updates']['quarterly'] = 'error'
                results['errors'].append(f"Quarterly: {str(e)}")
            
            # 5. Update annual results
            try:
                self._update_annual_results(symbol, data)
                results['updates']['annual'] = 'success'
            except Exception as e:
                logger.error(f"Error updating annual results: {e}")
                results['updates']['annual'] = 'error'
                results['errors'].append(f"Annual: {str(e)}")
            
            # 6. Update shareholding
            try:
                self._update_shareholding(symbol, data)
                results['updates']['shareholding'] = 'success'
            except Exception as e:
                logger.error(f"Error updating shareholding: {e}")
                results['updates']['shareholding'] = 'error'
                results['errors'].append(f"Shareholding: {str(e)}")

            # 7. Update balance sheet
            try:
                self._update_balance_sheet(symbol, data)
                results['updates']['balance_sheet'] = 'success'
            except Exception as e:
                logger.error(f"Error updating balance sheet: {e}")
                results['updates']['balance_sheet'] = 'error'
                results['errors'].append(f"Balance sheet: {str(e)}")

            # 8. Update cash flow
            try:
                self._update_cash_flow(symbol, data)
                results['updates']['cash_flow'] = 'success'
            except Exception as e:
                logger.error(f"Error updating cash flow: {e}")
                results['updates']['cash_flow'] = 'error'
                results['errors'].append(f"Cash flow: {str(e)}")

            # 9. Update ratios
            try:
                self._update_ratios(symbol, data)
                results['updates']['ratios'] = 'success'
            except Exception as e:
                logger.error(f"Error updating ratios: {e}")
                results['updates']['ratios'] = 'error'
                results['errors'].append(f"Ratios: {str(e)}")
            
            # 7. Update peers
            try:
                count = self._update_peers(symbol, data)
                results['updates']['peers'] = f'success ({count} peers)'
            except Exception as e:
                logger.error(f"Error updating peers: {e}")
                results['updates']['peers'] = 'error'
                results['errors'].append(f"Peers: {str(e)}")
            
            # 8. Update corporate actions (Bulk update preferred)
            # SKIPPING per-stock corp action fetch as it is inefficient. Will implement bulk update method.
            
            # 9. Update Derivatives (Option Chain)
            try:
                self._update_derivatives(symbol)
                results['updates']['derivatives'] = 'success'
            except Exception as e:
                # Not all stocks have F&O
                logger.debug(f"Derivatives update skipped/failed: {e}")
                results['updates']['derivatives'] = 'skipped'
                
            # 10. Calculate and Save Technicals
            try:
                self._update_technicals(symbol)
                results['updates']['technicals'] = 'success'
            except Exception as e:
                logger.error(f"Error updating technicals: {e}")
                results['updates']['technicals'] = 'error'
            
            # Calculate execution time
            execution_time = time.time() - start_time
            results['execution_time'] = execution_time
            results['success'] = True
            
            # Log successful update
            self.db.log_update(
                symbol=symbol,
                table_name='complete_update',
                status='success',
                message=f"Updated {len([v for v in results['updates'].values() if 'success' in v])} sections",
                execution_time=execution_time
            )
            
            logger.info(f"✅ Update complete for {symbol} in {execution_time:.2f}s")
            
        except Exception as e:
            logger.error(f"💥 Critical error updating {symbol}: {e}")
            results['errors'].append(f"Critical: {str(e)}")
            results['success'] = False
            
            # Log failed update
            self.db.log_update(
                symbol=symbol,
                table_name='complete_update',
                status='error',
                message=str(e),
                execution_time=time.time() - start_time
            )
        
        return results
    
    def _update_company_info(self, symbol: str, data: Dict):
        """Update company master table."""
        company_info = data.get('company_info', {})
        if not company_info:
            return
            
        self.db.add_company(
            symbol=symbol,
            company_name=company_info.get('symbol') or company_info.get('company_name'),
            sector=company_info.get('sector'),
            industry=company_info.get('industry'),
            isin=company_info.get('isin')
        )
        logger.info(f"  ✅ Company info updated")
    
    def _update_snapshot(self, symbol: str, data: Dict):
        """Update latest snapshot."""
        snapshot = {}
        
        # Price data (standardized keys from UnifiedDataService via HybridAggregator)
        price = data.get('price', {})
        if price:
            snapshot['current_price'] = price.get('last_price')
            snapshot['prev_close'] = price.get('prev_close')
            snapshot['open'] = price.get('open')
            snapshot['day_high'] = price.get('high')
            snapshot['day_low'] = price.get('low')
            snapshot['change'] = price.get('change')
            snapshot['change_percent'] = price.get('change_percent')
            snapshot['volume'] = price.get('volume')
            snapshot['upper_circuit'] = price.get('upper_circuit')
            snapshot['lower_circuit'] = price.get('lower_circuit')
        
        # Key metrics
        metrics = data.get('key_metrics', {})
        if metrics:
            snapshot['market_cap'] = metrics.get('market_cap')
            snapshot['pe_ratio'] = metrics.get('pe_ratio')
            snapshot['roe'] = metrics.get('roe')
            snapshot['roce'] = metrics.get('roce')
            snapshot['dividend_yield'] = metrics.get('dividend_yield')
            snapshot['book_value'] = metrics.get('book_value')
            snapshot['face_value'] = metrics.get('face_value')
            snapshot['high_52w'] = metrics.get('high_52w')
            snapshot['low_52w'] = metrics.get('low_52w')
            snapshot['eps'] = metrics.get('eps')
        
        # Fallback for 52 week data
        week_52 = data.get('52week_high_low', {})
        if week_52:
            snapshot['high_52w'] = snapshot.get('high_52w') or week_52.get('high_52w')
            snapshot['low_52w'] = snapshot.get('low_52w') or week_52.get('low_52w')
        
        self.db.update_snapshot(symbol, snapshot)
        logger.info(f"  ✅ Snapshot updated")
    
    def _update_price_history(self, symbol: str, data: Dict) -> int:
        """Update historical prices."""
        historical = data.get('historical_daily')
        if historical is None or historical.empty:
            logger.warning(f"  ⚠️  No historical data available")
            return 0
        
        self.db.save_price_history(symbol, historical)
        logger.info(f"  ✅ Price history updated ({len(historical)} records)")
        return len(historical)
    
    def _update_quarterly_results(self, symbol: str, data: Dict):
        """Update quarterly results."""
        quarterly = data.get('quarterly_results')
        if quarterly is None or quarterly.empty:
            return
        self.db.save_quarterly_results(symbol, quarterly)
        logger.info(f"  ✅ Quarterly results updated")
    
    def _update_annual_results(self, symbol: str, data: Dict):
        """Update annual results."""
        annual = data.get('profit_loss')
        if annual is None or annual.empty:
            return
        self.db.save_annual_results(symbol, annual)
        logger.info(f"  ✅ Annual results updated")
    
    def _update_shareholding(self, symbol: str, data: Dict):
        """Update shareholding pattern."""
        shareholding = data.get('shareholding')
        if shareholding is None or shareholding.empty:
            return
        self.db.save_shareholding(symbol, shareholding)
        logger.info(f"  ✅ Shareholding pattern updated")
    
    def _update_balance_sheet(self, symbol: str, data: Dict):
        """Update balance sheet."""
        bs = data.get('balance_sheet')
        if bs is None or bs.empty:
            return
        self.db.save_balance_sheet(symbol, bs)
        logger.info(f"  ✅ Balance sheet updated")

    def _update_cash_flow(self, symbol: str, data: Dict):
        """Update cash flow."""
        cf = data.get('cash_flow')
        if cf is None or cf.empty:
            return
        self.db.save_cash_flow(symbol, cf)
        logger.info(f"  ✅ Cash flow updated")

    def _update_ratios(self, symbol: str, data: Dict):
        """Update financial ratios."""
        ratios = data.get('ratios')
        if ratios is None or ratios.empty:
            return
        self.db.save_financial_ratios(symbol, ratios)
        logger.info(f"  ✅ Financial ratios updated")
    
    def _update_peers(self, symbol: str, data: Dict) -> int:
        """Update peer comparison."""
        peers = data.get('peer_comparison')
        if peers is None or peers.empty:
            return 0
        self.db.save_peers(symbol, peers)
        logger.info(f"  ✅ Peer comparison updated ({len(peers)} peers)")
        return len(peers)
    
    def _update_corporate_actions(self, symbol: str, data: Dict):
        """Deprecated: Use update_all_corporate_actions instead."""
        pass
        
    def _update_derivatives(self, symbol: str):
        """Update option chain data."""
        # Use Unified/NseUtils directly
        df = self.aggregator.unified.get_options_data(symbol)
        if df is not None and not df.empty:
            self.db.save_option_chain(df)
            logger.info("  ✅ Option chain updated")
            
    def _update_technicals(self, symbol: str):
        """Calculate and save technical indicators."""
        # 1. Fetch history from DB (we just saved it)
        df = self.db.get_price_history(symbol, days=365) # Need enough data for 200 SMA
        if df.empty or len(df) < 50: 
            return # Not enough data
        
        # 2. Use TechnicalAnalysisService
        try:
            ta = TechnicalAnalysisService(df)
            df_indicators = ta.calculate_all()
            
            # 3. Save
            records = []
            for _, row in df_indicators.iterrows():
                # Skip rows with NaNs in critical indicators (warming up)
                if pd.isna(row.get('sma_200')) and pd.isna(row.get('rsi')): 
                    continue 

                records.append({
                    'date': row['date'].strftime('%Y-%m-%d') if hasattr(row['date'], 'strftime') else row['date'],
                    'sma_20': row.get('sma_20'),
                    'sma_50': row.get('sma_50'),
                    'sma_200': row.get('sma_200'),
                    'rsi': row.get('rsi'),
                    'macd': row.get('macd'),
                    'macd_signal': row.get('macd_signal'),
                    'adx': row.get('adx')
                })
            
            if records:
                self.db.save_technical_indicators(symbol, records)
                logger.info(f"  ✅ Technicals updated ({len(records)} records)")
        except Exception as e:
            logger.error(f"  ❌ Error calculating technicals: {e}")

    def update_all_corporate_actions(self):
        """Bulk update corporate actions for all stocks."""
        logger.info("🌍 Updating Corporate Actions...")
        try:
            df = self.nse_utils.get_corporate_action()
            if df is not None:
                self.db.save_corporate_actions(df)
                logger.info("✅ Bulk Corporate Actions updated")
            else:
                logger.warning("No corporate actions found")
        except Exception as e:
            logger.error(f"Error bulk updating corporate actions: {e}")

    def update_multiple(self, symbols: List[str], force: bool = False, delay: float = 2.0):
        """Update multiple stocks."""
        for symbol in symbols:
            self.update_stock(symbol, force=force)
            time.sleep(delay)

    def update_market_data(self) -> Dict[str, any]:
        """
        Update market-wide data (FII/DII, Market Breadth).
        """
        results = {
            'timestamp': datetime.now().isoformat(),
            'updates': {},
            'errors': []
        }
        
        logger.info("🌍 Updating Market Data...")
        
        # 1. Update FII/DII Activity
        try:
            fii_data = self.derivatives.get_fii_dii_activity()
            if fii_data:
                self.db.save_fii_dii_activity(fii_data)
                results['updates']['fii_dii'] = 'success'
                logger.info("  ✅ FII/DII Activity updated")
            else:
                results['updates']['fii_dii'] = 'no_data'
        except Exception as e:
            logger.error(f"Error updating FII/DII: {e}")
            results['updates']['fii_dii'] = 'error'
            results['errors'].append(f"FII/DII: {str(e)}")

        # 2. Update Market Breadth
        try:
            breadth = self.derivatives.get_market_breadth()
            if breadth:
                self.db.save_market_breadth(breadth)
                results['updates']['market_breadth'] = 'success'
                logger.info("  ✅ Market Breadth updated")
            else:
                results['updates']['market_breadth'] = 'no_data'
        except Exception as e:
            logger.error(f"Error updating Market Breadth: {e}")
            results['updates']['market_breadth'] = 'error'
            results['errors'].append(f"Market Breadth: {str(e)}")
            
        return results

    def _extract_number(self, value) -> Optional[float]:
        """Extract numeric value from string."""
        if not value: return None
        if isinstance(value, (int, float)): return float(value)
        cleaned = re.sub(r'[₹,\s%]', '', str(value))
        try: return float(cleaned)
        except: return None