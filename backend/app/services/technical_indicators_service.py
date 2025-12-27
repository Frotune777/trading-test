"""
Technical Indicators Calculation Service
Calculates and stores technical indicators using TA-Lib for all symbols in price_history
"""

import sqlite3
import pandas as pd
import logging
from datetime import datetime
from typing import List, Dict, Any
from app.services.technical_analysis import TechnicalAnalysisService

logger = logging.getLogger(__name__)


class TechnicalIndicatorsService:
    """
    Service to calculate and store technical indicators for all symbols
    Uses TA-Lib via TechnicalAnalysisService
    """
    
    def __init__(self, db_path: str = 'stock_data.db'):
        self.db_path = db_path
    
    def calculate_for_symbol(self, symbol: str, min_periods: int = 50) -> Dict[str, Any]:
        """
        Calculate technical indicators for a single symbol
        
        Args:
            symbol: Stock symbol
            min_periods: Minimum number of data points required
            
        Returns:
            Dict with calculation results
        """
        try:
            # Fetch price history
            conn = sqlite3.connect(self.db_path)
            query = f"""
                SELECT date, open, high, low, close, volume
                FROM price_history
                WHERE symbol = '{symbol}'
                ORDER BY date ASC
            """
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            if df.empty or len(df) < min_periods:
                logger.warning(f"Insufficient data for {symbol}: {len(df)} records (need {min_periods})")
                return {
                    'symbol': symbol,
                    'status': 'insufficient_data',
                    'records': len(df),
                    'indicators_calculated': 0
                }
            
            # Calculate indicators using TA-Lib
            logger.info(f"Calculating indicators for {symbol} ({len(df)} records)")
            ta_service = TechnicalAnalysisService(df)
            df_with_indicators = ta_service.calculate_all()
            
            # Store in database
            indicators_stored = self._store_indicators(symbol, df_with_indicators)
            
            logger.info(f"✅ Calculated and stored {indicators_stored} indicator records for {symbol}")
            
            return {
                'symbol': symbol,
                'status': 'success',
                'records': len(df),
                'indicators_calculated': indicators_stored
            }
            
        except Exception as e:
            logger.error(f"Error calculating indicators for {symbol}: {e}")
            return {
                'symbol': symbol,
                'status': 'error',
                'error': str(e)
            }
    
    def _store_indicators(self, symbol: str, df: pd.DataFrame) -> int:
        """
        Store calculated indicators in technical_indicators table
        Matches actual database schema
        
        Returns:
            Number of records stored
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        records_stored = 0
        
        for idx, row in df.iterrows():
            try:
                # Skip rows with NaN date
                if pd.isna(row.get('date')):
                    continue
                
                # Prepare date
                date_val = row['date']
                if isinstance(date_val, pd.Timestamp):
                    date_str = date_val.strftime('%Y-%m-%d')
                else:
                    date_str = str(date_val)
                
                # Helper to get value or None
                def get_val(key):
                    val = row.get(key)
                    return None if pd.isna(val) else float(val)
                
                # Insert matching actual schema:
                # sma_20, sma_50, sma_200, ema_12, ema_26, rsi_14, macd, macd_signal,
                # bollinger_upper, bollinger_middle, bollinger_lower, atr_14, adx_14
                cursor.execute('''
                    INSERT OR REPLACE INTO technical_indicators
                    (symbol, date, sma_20, sma_50, sma_200, ema_12, ema_26,
                     rsi_14, macd, macd_signal, 
                     bollinger_upper, bollinger_middle, bollinger_lower,
                     atr_14, adx_14)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    symbol, date_str,
                    get_val('sma_20'),
                    get_val('sma_50'),
                    get_val('sma_200'),
                    get_val('ema_9'),  # Map to ema_12
                    get_val('ema_21'),  # Map to ema_26
                    get_val('rsi'),  # Map to rsi_14
                    get_val('macd'),
                    get_val('macd_signal'),
                    get_val('bb_upper'),  # Map to bollinger_upper
                    get_val('bb_middle'),  # Map to bollinger_middle
                    get_val('bb_lower'),  # Map to bollinger_lower
                    get_val('atr'),  # Map to atr_14
                    get_val('adx')  # Map to adx_14
                ))
                records_stored += 1
                
            except Exception as e:
                logger.debug(f"Error storing indicator row for {symbol}: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        return records_stored
    
    def calculate_for_all_symbols(self) -> Dict[str, Any]:
        """
        Calculate indicators for all symbols in price_history
        
        Returns:
            Summary of calculation results
        """
        # Get all symbols
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT symbol FROM price_history')
        symbols = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        logger.info(f"Calculating indicators for {len(symbols)} symbols")
        
        results = {
            'total_symbols': len(symbols),
            'successful': 0,
            'failed': 0,
            'insufficient_data': 0,
            'details': []
        }
        
        for symbol in symbols:
            result = self.calculate_for_symbol(symbol)
            results['details'].append(result)
            
            if result['status'] == 'success':
                results['successful'] += 1
            elif result['status'] == 'insufficient_data':
                results['insufficient_data'] += 1
            else:
                results['failed'] += 1
        
        logger.info(f"✅ Indicator calculation complete: {results['successful']}/{results['total_symbols']} successful")
        
        return results


# Standalone script for testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    service = TechnicalIndicatorsService()
    results = service.calculate_for_all_symbols()
    
    print("\n=== TECHNICAL INDICATORS CALCULATION RESULTS ===")
    print(f"Total symbols: {results['total_symbols']}")
    print(f"Successful: {results['successful']}")
    print(f"Insufficient data: {results['insufficient_data']}")
    print(f"Failed: {results['failed']}")
    
    print("\nDetails:")
    for detail in results['details']:
        status_icon = "✅" if detail['status'] == 'success' else "⚠️" if detail['status'] == 'insufficient_data' else "❌"
        print(f"  {status_icon} {detail['symbol']}: {detail.get('indicators_calculated', 0)} indicators")
