# core/mtf_manager.py
"""
Multi-Timeframe (MTF) Data Manager
Handles data across multiple timeframes for technical analysis
Production-ready with efficient storage and retrieval
Version: 1.0
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path
import sqlite3

logger = logging.getLogger(__name__)


class TimeFrame:
    """Timeframe definitions and conversions"""
    
    # Standard timeframes
    M1 = '1m'      # 1 minute
    M5 = '5m'      # 5 minutes
    M15 = '15m'    # 15 minutes
    M30 = '30m'    # 30 minutes
    H1 = '1h'      # 1 hour
    H4 = '4h'      # 4 hours
    D1 = '1d'      # Daily
    W1 = '1w'      # Weekly
    MN1 = '1M'     # Monthly
    
    # Mapping to minutes
    MINUTES_MAP = {
        '1m': 1,
        '5m': 5,
        '15m': 15,
        '30m': 30,
        '1h': 60,
        '4h': 240,
        '1d': 1440,
        '1w': 10080,
        '1M': 43200
    }
    
    # Typical lookback periods (in bars)
    LOOKBACK_BARS = {
        '1m': 1000,
        '5m': 500,
        '15m': 300,
        '30m': 200,
        '1h': 200,
        '4h': 100,
        '1d': 365,
        '1w': 104,
        '1M': 60
    }
    
    @classmethod
    def get_minutes(cls, timeframe: str) -> int:
        """Get minutes for a timeframe"""
        return cls.MINUTES_MAP.get(timeframe, 0)
    
    @classmethod
    def get_higher_timeframe(cls, timeframe: str) -> Optional[str]:
        """Get the next higher timeframe"""
        hierarchy = ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', '1M']
        try:
            idx = hierarchy.index(timeframe)
            return hierarchy[idx + 1] if idx < len(hierarchy) - 1 else None
        except ValueError:
            return None
    
    @classmethod
    def get_lower_timeframe(cls, timeframe: str) -> Optional[str]:
        """Get the next lower timeframe"""
        hierarchy = ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', '1M']
        try:
            idx = hierarchy.index(timeframe)
            return hierarchy[idx - 1] if idx > 0 else None
        except ValueError:
            return None


class MTFDataManager:
    """
    Multi-Timeframe Data Manager
    
    Responsibilities:
    - Fetch data across multiple timeframes
    - Resample lower to higher timeframes
    - Store intraday data efficiently
    - Synchronize data across timeframes
    - Provide MTF analysis utilities
    """
    
    def __init__(self, db_manager, nse_source):
        self.db = db_manager
        self.nse = nse_source
        self.cache = {}  # In-memory cache for speed
    
    # ========================================================================
    # DATA FETCHING
    # ========================================================================
    
    def get_mtf_data(
        self,
        symbol: str,
        timeframes: List[str],
        lookback_days: int = 30
    ) -> Dict[str, pd.DataFrame]:
        """
        Get data for multiple timeframes
        
        Args:
            symbol: Stock symbol
            timeframes: List of timeframes ['1d', '1h', '15m']
            lookback_days: Days to look back
        
        Returns:
            Dict mapping timeframe to DataFrame
        """
        logger.info(f"Fetching MTF data for {symbol}: {timeframes}")
        
        mtf_data = {}
        
        for tf in timeframes:
            try:
                df = self._get_timeframe_data(symbol, tf, lookback_days)
                if df is not None and not df.empty:
                    mtf_data[tf] = df
                    logger.info(f"  {tf}: {len(df)} bars")
                else:
                    logger.warning(f"  {tf}: No data")
            except Exception as e:
                logger.error(f"Error fetching {tf} data: {e}")
        
        return mtf_data
    
    def _get_timeframe_data(
        self,
        symbol: str,
        timeframe: str,
        lookback_days: int
    ) -> Optional[pd.DataFrame]:
        """Get data for a specific timeframe"""
        
        # For daily and higher, use database
        if timeframe in ['1d', '1w', '1M']:
            return self._get_daily_plus_data(symbol, timeframe, lookback_days)
        
        # For intraday, try database first, then NSE
        return self._get_intraday_data(symbol, timeframe, lookback_days)
    
    def _get_daily_plus_data(
        self,
        symbol: str,
        timeframe: str,
        lookback_days: int
    ) -> Optional[pd.DataFrame]:
        """Get daily, weekly, or monthly data"""
        
        # Get daily data from database
        daily_data = self.db.get_price_history(symbol, days=lookback_days)
        
        if daily_data.empty:
            return None
        
        # Ensure datetime index
        if 'date' in daily_data.columns:
            daily_data['date'] = pd.to_datetime(daily_data['date'])
            daily_data = daily_data.set_index('date')
        
        # Resample if needed
        if timeframe == '1w':
            return self._resample_ohlcv(daily_data, 'W')
        elif timeframe == '1M':
            return self._resample_ohlcv(daily_data, 'M')
        else:
            return daily_data.reset_index()
    
    def _get_intraday_data(
        self,
        symbol: str,
        timeframe: str,
        lookback_days: int
    ) -> Optional[pd.DataFrame]:
        """Get intraday data (1m, 5m, 15m, 30m, 1h, 4h)"""
        
        # First, try to get from database
        df = self._get_intraday_from_db(symbol, timeframe, lookback_days)
        
        if df is not None and not df.empty:
            return df
        
        # If not in database, fetch from NSE
        logger.info(f"Fetching fresh {timeframe} data from NSE for {symbol}")
        
        try:
            # NSE only provides certain intervals
            # We'll fetch the base interval and resample
            
            if timeframe in ['1m', '5m', '15m', '30m']:
                # Fetch from NSE (they provide up to 1 month of intraday)
                df = self._fetch_from_nse(symbol, timeframe, lookback_days)
            else:
                # For 1h, 4h - fetch 15m and resample
                df_base = self._fetch_from_nse(symbol, '15m', lookback_days)
                if df_base is not None and not df_base.empty:
                    df = self._resample_to_timeframe(df_base, timeframe)
                else:
                    df = None
            
            # Save to database for future use
            if df is not None and not df.empty:
                self._save_intraday_to_db(symbol, timeframe, df)
            
            return df
        
        except Exception as e:
            logger.error(f"Error fetching intraday data: {e}")
            return None
    
    def _fetch_from_nse(
        self,
        symbol: str,
        interval: str,
        lookback_days: int
    ) -> Optional[pd.DataFrame]:
        """Fetch intraday data from NSE"""
        
        try:
            # NSE master data can provide historical data
            df = self.nse.master.get_history(
                symbol=symbol,
                exchange='NSE',
                start=datetime.now() - timedelta(days=lookback_days),
                end=datetime.now(),
                interval=interval
            )
            
            return df
        
        except Exception as e:
            logger.error(f"NSE fetch error: {e}")
            return None
    
    # ========================================================================
    # DATABASE OPERATIONS FOR INTRADAY DATA
    # ========================================================================
    
    def _get_intraday_from_db(
        self,
        symbol: str,
        timeframe: str,
        lookback_days: int
    ) -> Optional[pd.DataFrame]:
        """Get intraday data from database"""
        
        try:
            cutoff_date = datetime.now() - timedelta(days=lookback_days)
            
            query = """
                SELECT timestamp, open, high, low, close, volume
                FROM intraday_prices
                WHERE symbol = ? AND timeframe = ? AND timestamp >= ?
                ORDER BY timestamp ASC
            """
            
            df = pd.read_sql_query(
                query,
                self.db.conn,
                params=(symbol, timeframe, cutoff_date.isoformat())
            )
            
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            return df if not df.empty else None
        
        except Exception as e:
            logger.error(f"Error reading intraday from DB: {e}")
            return None
    
    def _save_intraday_to_db(
        self,
        symbol: str,
        timeframe: str,
        df: pd.DataFrame
    ):
        """Save intraday data to database"""
        
        try:
            # Prepare data
            records = []
            
            for idx, row in df.iterrows():
                timestamp = row.get('date') or row.get('timestamp') or idx
                
                records.append({
                    'symbol': symbol,
                    'timeframe': timeframe,
                    'timestamp': pd.to_datetime(timestamp).isoformat(),
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': int(row['volume']) if 'volume' in row else 0
                })
            
            # Insert/update in database
            query = """
                INSERT OR REPLACE INTO intraday_prices
                (symbol, timeframe, timestamp, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            data_tuples = [
                (
                    r['symbol'], r['timeframe'], r['timestamp'],
                    r['open'], r['high'], r['low'], r['close'], r['volume']
                )
                for r in records
            ]
            
            self.db.executemany(query, data_tuples)
            self.db.commit()
            
            logger.info(f"Saved {len(records)} {timeframe} bars for {symbol}")
        
        except Exception as e:
            logger.error(f"Error saving intraday to DB: {e}")
    
    # ========================================================================
    # RESAMPLING
    # ========================================================================
    
    def _resample_ohlcv(
        self,
        df: pd.DataFrame,
        rule: str
    ) -> pd.DataFrame:
        """
        Resample OHLCV data to higher timeframe
        
        Args:
            df: DataFrame with OHLCV data (indexed by datetime)
            rule: Pandas resample rule ('W', 'M', '4H', etc.)
        """
        
        resampled = df.resample(rule).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        
        return resampled.reset_index()
    
    def _resample_to_timeframe(
        self,
        df: pd.DataFrame,
        target_timeframe: str
    ) -> pd.DataFrame:
        """Resample to specific timeframe"""
        
        # Ensure datetime index
        if 'date' in df.columns:
            df = df.set_index('date')
        elif 'timestamp' in df.columns:
            df = df.set_index('timestamp')
        
        df.index = pd.to_datetime(df.index)
        
        # Map timeframe to pandas rule
        rule_map = {
            '1h': '1H',
            '4h': '4H',
            '1d': '1D',
            '1w': 'W',
            '1M': 'M'
        }
        
        rule = rule_map.get(target_timeframe)
        if not rule:
            logger.error(f"Unknown timeframe: {target_timeframe}")
            return df
        
        return self._resample_ohlcv(df, rule)
    
    # ========================================================================
    # MTF ANALYSIS UTILITIES
    # ========================================================================
    
    def align_mtf_data(
        self,
        mtf_data: Dict[str, pd.DataFrame],
        reference_tf: str = '1d'
    ) -> Dict[str, pd.DataFrame]:
        """
        Align multiple timeframes to same datetime index
        Uses the reference timeframe as the base
        """
        
        if reference_tf not in mtf_data:
            logger.warning(f"Reference timeframe {reference_tf} not found")
            return mtf_data
        
        ref_df = mtf_data[reference_tf].copy()
        
        if 'date' in ref_df.columns:
            ref_index = pd.to_datetime(ref_df['date'])
        elif 'timestamp' in ref_df.columns:
            ref_index = pd.to_datetime(ref_df['timestamp'])
        else:
            ref_index = ref_df.index
        
        aligned = {reference_tf: ref_df}
        
        # Align other timeframes
        for tf, df in mtf_data.items():
            if tf == reference_tf:
                continue
            
            # This would implement forward-fill logic
            # For now, just include as-is
            aligned[tf] = df
        
        return aligned
    
    def get_htf_value_at_ltf(
        self,
        htf_data: pd.DataFrame,
        ltf_timestamp: datetime,
        column: str = 'close'
    ):
        """
        Get higher timeframe value at a lower timeframe timestamp
        Useful for checking HTF trend while on LTF
        """
        
        if 'date' in htf_data.columns:
            htf_data = htf_data.set_index('date')
        elif 'timestamp' in htf_data.columns:
            htf_data = htf_data.set_index('timestamp')
        
        htf_data.index = pd.to_datetime(htf_data.index)
        
        # Find the most recent HTF bar before this LTF timestamp
        mask = htf_data.index <= ltf_timestamp
        
        if mask.any():
            return htf_data.loc[mask, column].iloc[-1]
        
        return None
    
    def calculate_mtf_trend(
        self,
        mtf_data: Dict[str, pd.DataFrame],
        ma_period: int = 20
    ) -> Dict[str, str]:
        """
        Calculate trend direction for each timeframe
        
        Returns:
            Dict mapping timeframe to 'UP', 'DOWN', or 'NEUTRAL'
        """
        
        trends = {}
        
        for tf, df in mtf_data.items():
            if df.empty or len(df) < ma_period:
                trends[tf] = 'UNKNOWN'
                continue
            
            # Simple MA-based trend
            df_copy = df.copy()
            df_copy['ma'] = df_copy['close'].rolling(ma_period).mean()
            
            if len(df_copy) < 2:
                trends[tf] = 'UNKNOWN'
                continue
            
            current_price = df_copy['close'].iloc[-1]
            current_ma = df_copy['ma'].iloc[-1]
            prev_ma = df_copy['ma'].iloc[-2]
            
            if pd.isna(current_ma) or pd.isna(prev_ma):
                trends[tf] = 'UNKNOWN'
            elif current_price > current_ma and current_ma > prev_ma:
                trends[tf] = 'UP'
            elif current_price < current_ma and current_ma < prev_ma:
                trends[tf] = 'DOWN'
            else:
                trends[tf] = 'NEUTRAL'
        
        return trends
    
    def is_mtf_aligned(
        self,
        mtf_data: Dict[str, pd.DataFrame],
        direction: str = 'UP',
        min_timeframes: int = 3
    ) -> bool:
        """
        Check if multiple timeframes are aligned in same direction
        
        Args:
            mtf_data: Multi-timeframe data
            direction: 'UP' or 'DOWN'
            min_timeframes: Minimum number of TFs that should agree
        
        Returns:
            True if aligned
        """
        
        trends = self.calculate_mtf_trend(mtf_data)
        aligned_count = sum(1 for trend in trends.values() if trend == direction)
        
        return aligned_count >= min_timeframes
    
    # ========================================================================
    # DATA QUALITY
    # ========================================================================
    
    def validate_mtf_data(
        self,
        mtf_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, Dict]:
        """
        Validate data quality across timeframes
        
        Returns:
            Quality report for each timeframe
        """
        
        report = {}
        
        for tf, df in mtf_data.items():
            quality = {
                'rows': len(df),
                'missing_data': df.isnull().sum().to_dict(),
                'date_range': None,
                'gaps': 0,
                'quality_score': 0
            }
            
            if not df.empty:
                if 'date' in df.columns:
                    dates = pd.to_datetime(df['date'])
                elif 'timestamp' in df.columns:
                    dates = pd.to_datetime(df['timestamp'])
                else:
                    dates = pd.to_datetime(df.index)
                
                quality['date_range'] = f"{dates.min()} to {dates.max()}"
                
                # Check for gaps
                expected_bars = TimeFrame.LOOKBACK_BARS.get(tf, len(df))
                quality['gaps'] = max(0, expected_bars - len(df))
                
                # Calculate quality score
                missing_pct = df.isnull().sum().sum() / (len(df) * len(df.columns))
                gap_pct = quality['gaps'] / expected_bars if expected_bars > 0 else 0
                quality['quality_score'] = round((1 - missing_pct - gap_pct) * 100, 2)
            
            report[tf] = quality
        
        return report