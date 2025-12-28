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
    
    def __init__(self, db_manager=None):
        from app.database.db_manager import DatabaseManager
        self.db_manager = db_manager or DatabaseManager()
    
    def calculate_for_symbol(self, symbol: str, min_periods: int = 50) -> Dict[str, Any]:
        """
        Calculate technical indicators for a single symbol
        """
        try:
            # Fetch price history using DatabaseManager (PostgreSQL)
            query = """
                SELECT date, open, high, low, close, volume
                FROM price_history
                WHERE symbol = ?
                ORDER BY date ASC
            """
            df = pd.DataFrame(self.db_manager.query_dict(query, (symbol,)))
            
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
        Store calculated indicators in technical_indicators table (PostgreSQL via DatabaseManager)
        """
        records_stored = 0
        params_list = []
        
        for idx, row in df.iterrows():
            try:
                # Skip rows with NaN date
                if pd.isna(row.get('date')):
                    continue
                
                # Prepare date
                date_val = row['date']
                if isinstance(date_val, pd.Timestamp):
                    date_obj = date_val.date()
                else:
                    date_obj = pd.to_datetime(date_val).date()
                
                # Helper to get value or None
                def get_val(key):
                    val = row.get(key)
                    return None if pd.isna(val) else float(val)
                
                # Insert parameters mapping to actual schema
                params_list.append((
                    symbol, date_obj,
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
                logger.debug(f"Error preparing indicator row for {symbol}: {e}")
                continue
        
        if params_list:
            # PostgreSQL compatible INSERT with ON CONFLICT
            query = '''
                INSERT INTO technical_indicators
                (symbol, date, sma_20, sma_50, sma_200, ema_12, ema_26,
                 rsi_14, macd, macd_signal, 
                 bollinger_upper, bollinger_middle, bollinger_lower,
                 atr_14, adx_14)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (symbol, date) DO UPDATE SET
                    sma_20 = EXCLUDED.sma_20,
                    sma_50 = EXCLUDED.sma_50,
                    sma_200 = EXCLUDED.sma_200,
                    ema_12 = EXCLUDED.ema_12,
                    ema_26 = EXCLUDED.ema_26,
                    rsi_14 = EXCLUDED.rsi_14,
                    macd = EXCLUDED.macd,
                    macd_signal = EXCLUDED.macd_signal,
                    bollinger_upper = EXCLUDED.bollinger_upper,
                    bollinger_middle = EXCLUDED.bollinger_middle,
                    bollinger_lower = EXCLUDED.bollinger_lower,
                    atr_14 = EXCLUDED.atr_14,
                    adx_14 = EXCLUDED.adx_14
            '''
            self.db_manager.executemany(query, params_list)
        
        return records_stored
    
    def calculate_for_all_symbols(self) -> Dict[str, Any]:
        """
        Calculate indicators for all symbols in price_history
        """
        # Get all symbols using DatabaseManager (PostgreSQL)
        query = 'SELECT DISTINCT symbol FROM price_history'
        symbols_raw = self.db_manager.query_dict(query)
        symbols = [row['symbol'] for row in symbols_raw]
        
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
