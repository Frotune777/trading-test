"""
Data Updater - Fetches data from sources and stores in database
Handles both NSE market data and Screener fundamentals
"""

from typing import List, Dict, Optional
import logging
from datetime import datetime
import time
import re

from .db_manager import DatabaseManager
from core.hybrid_aggregator import HybridAggregator

logger = logging.getLogger(__name__)


class DataUpdater:
    """Update database with fresh data from all sources."""
    
    def __init__(self, db_path: str = 'stock_data.db'):
        self.db = DatabaseManager(db_path)
        self.aggregator = HybridAggregator()
    
    def update_stock(self, symbol: str, force: bool = False) -> Dict[str, any]:
        """
        Update all data for a symbol.
        
        Args:
            symbol: Stock symbol
            force: Force update even if recent data exists
        
        Returns:
            Dictionary with status of each data type and statistics
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
            
            # 7. Update peers
            try:
                count = self._update_peers(symbol, data)
                results['updates']['peers'] = f'success ({count} peers)'
            except Exception as e:
                logger.error(f"Error updating peers: {e}")
                results['updates']['peers'] = 'error'
                results['errors'].append(f"Peers: {str(e)}")
            
            # 8. Update corporate actions (if available)
            try:
                self._update_corporate_actions(symbol, data)
                results['updates']['corporate_actions'] = 'success'
            except Exception as e:
                logger.debug(f"Corporate actions not available: {e}")
                results['updates']['corporate_actions'] = 'skipped'
            
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
        # Combine data from multiple sources
        snapshot = {}
        
        # Price data
        price = data.get('price', {})
        if price:
            snapshot['current_price'] = price.get('last_price')
            snapshot['change'] = price.get('change')
            snapshot['change_percent'] = price.get('change_percent')
            snapshot['volume'] = price.get('volume')
        
        # Key metrics from Screener
        metrics = data.get('key_metrics', {})
        if metrics:
            snapshot['market_cap'] = metrics.get('Market Cap')
            snapshot['pe_ratio'] = self._extract_number(metrics.get('Stock P/E'))
            snapshot['roe'] = self._extract_number(metrics.get('ROE'))
            snapshot['roce'] = self._extract_number(metrics.get('ROCE'))
            snapshot['dividend_yield'] = self._extract_number(metrics.get('Dividend Yield'))
            snapshot['book_value'] = self._extract_number(metrics.get('Book Value'))
            snapshot['face_value'] = self._extract_number(metrics.get('Face Value'))
            
            # Parse high/low if available
            high_low = metrics.get('High / Low', '')
            if high_low and '/' in high_low:
                parts = high_low.replace('₹', '').split('/')
                if len(parts) == 2:
                    snapshot['high_52w'] = self._extract_number(parts[0])
                    snapshot['low_52w'] = self._extract_number(parts[1])
        
        # 52 week data from NSE
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
            logger.warning(f"  ⚠️  No quarterly data available")
            return
        
        self.db.save_quarterly_results(symbol, quarterly)
        logger.info(f"  ✅ Quarterly results updated")
    
    def _update_annual_results(self, symbol: str, data: Dict):
        """Update annual results."""
        annual = data.get('profit_loss')
        
        if annual is None or annual.empty:
            logger.warning(f"  ⚠️  No annual results available")
            return
        
        self.db.save_annual_results(symbol, annual)
        logger.info(f"  ✅ Annual results updated")
    
    def _update_shareholding(self, symbol: str, data: Dict):
        """Update shareholding pattern."""
        shareholding = data.get('shareholding')
        
        if shareholding is None or shareholding.empty:
            logger.warning(f"  ⚠️  No shareholding data available")
            return
        
        self.db.save_shareholding(symbol, shareholding)
        logger.info(f"  ✅ Shareholding pattern updated")
    
    def _update_peers(self, symbol: str, data: Dict) -> int:
        """Update peer comparison."""
        peers = data.get('peer_comparison')
        
        if peers is None or peers.empty:
            logger.warning(f"  ⚠️  No peer data available")
            return 0
        
        self.db.save_peers(symbol, peers)
        count = len(peers)
        logger.info(f"  ✅ Peer comparison updated ({count} peers)")
        return count
    
    def _update_corporate_actions(self, symbol: str, data: Dict):
        """Update corporate actions."""
        actions = data.get('corporate_actions')
        
        if actions is None or actions.empty:
            logger.debug(f"  ⏭️  No corporate actions")
            return
        
        # Corporate actions handling can be added here
        logger.debug(f"  ℹ️  Corporate actions available but not stored yet")
    
    def update_multiple(
        self,
        symbols: List[str],
        force: bool = False,
        delay: float = 2.0
    ) -> Dict[str, Dict]:
        """
        Update multiple stocks with rate limiting.
        
        Args:
            symbols: List of stock symbols
            force: Force update even if recent
            delay: Delay between stocks (seconds) for rate limiting
        
        Returns:
            Dictionary mapping symbol to update results
        """
        results = {}
        total = len(symbols)
        
        print(f"\n{'='*80}")
        print(f"📊 BATCH UPDATE: {total} stocks")
        print(f"{'='*80}\n")
        
        for i, symbol in enumerate(symbols, 1):
            print(f"\n[{i}/{total}] Processing {symbol}...")
            
            try:
                result = self.update_stock(symbol, force=force)
                results[symbol] = result
                
                # Print summary
                if result.get('success'):
                    updates = result.get('updates', {})
                    success_count = len([v for v in updates.values() if 'success' in v])
                    print(f"  ✅ Success: {success_count} sections updated")
                elif result.get('skipped'):
                    print(f"  ⏭️  Skipped: {result.get('message')}")
                else:
                    print(f"  ❌ Failed: {len(result.get('errors', []))} errors")
                
            except Exception as e:
                logger.error(f"Error updating {symbol}: {e}")
                results[symbol] = {
                    'symbol': symbol,
                    'success': False,
                    'errors': [str(e)]
                }
            
            # Rate limiting
            if i < total:
                time.sleep(delay)
        
        # Print final summary
        self._print_batch_summary(results)
        
        return results
    
    def _print_batch_summary(self, results: Dict[str, Dict]):
        """Print summary of batch update."""
        print(f"\n{'='*80}")
        print("📊 BATCH UPDATE SUMMARY")
        print(f"{'='*80}\n")
        
        total = len(results)
        successful = len([r for r in results.values() if r.get('success')])
        skipped = len([r for r in results.values() if r.get('skipped')])
        failed = total - successful - skipped
        
        print(f"Total Stocks:    {total}")
        print(f"✅ Successful:   {successful}")
        print(f"⏭️  Skipped:      {skipped}")
        print(f"❌ Failed:       {failed}")
        
        if failed > 0:
            print(f"\n❌ Failed stocks:")
            for symbol, result in results.items():
                if not result.get('success') and not result.get('skipped'):
                    errors = result.get('errors', ['Unknown error'])
                    print(f"  • {symbol}: {errors[0]}")
        
        print(f"\n{'='*80}\n")
    
    def update_stale_stocks(self, hours: int = 24, max_stocks: int = None) -> Dict[str, Dict]:
        """
        Update stocks that haven't been updated recently.
        
        Args:
            hours: Consider stocks stale if not updated in this many hours
            max_stocks: Maximum number of stocks to update (None = all)
        
        Returns:
            Update results dictionary
        """
        # Get all companies
        companies = self.db.get_all_companies()
        
        # Filter stale stocks
        stale_symbols = []
        for company in companies:
            symbol = company['symbol']
            if self.db.needs_update(symbol, hours=hours):
                stale_symbols.append(symbol)
                if max_stocks and len(stale_symbols) >= max_stocks:
                    break
        
        if not stale_symbols:
            print(f"✅ All stocks are up to date (within {hours} hours)")
            return {}
        
        print(f"Found {len(stale_symbols)} stale stocks (not updated in {hours}h)")
        
        return self.update_multiple(stale_symbols, force=True)
    
    def update_sector(self, sector: str, force: bool = False) -> Dict[str, Dict]:
        """Update all stocks in a sector."""
        companies = self.db.get_all_companies(sector=sector)
        symbols = [c['symbol'] for c in companies]
        
        print(f"Updating {len(symbols)} stocks in {sector} sector")
        
        return self.update_multiple(symbols, force=force)
    
    def _extract_number(self, value) -> Optional[float]:
        """Extract numeric value from string."""
        if not value:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        
        # Remove currency symbols, commas, spaces, percentage
        cleaned = re.sub(r'[₹,\s%]', '', str(value))
        try:
            return float(cleaned)
        except:
            return None
    
    def get_update_status(self) -> Dict:
        """Get current update status of database."""
        stats = self.db.get_database_stats()
        summary = self.db.get_update_summary()
        
        return {
            'database_stats': stats,
            'update_summary': summary.to_dict('records') if not summary.empty else [],
            'total_companies': self.db.get_row_count('companies'),
            'needs_update_24h': len([
                c for c in self.db.get_all_companies()
                if self.db.needs_update(c['symbol'], hours=24)
            ])
        }