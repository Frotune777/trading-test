"""
Data Quality Service
Validates OHLC data integrity and detects anomalies.
Complies with Rules #5-6 (never fabricate, fail closed on bad data).
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import pandas as pd
from enum import Enum

logger = logging.getLogger(__name__)


class QualityIssue(Enum):
    """Types of data quality issues"""
    MISSING_CANDLES = "missing_candles"
    INVALID_OHLC = "invalid_ohlc"
    DUPLICATE_TIMESTAMP = "duplicate_timestamp"
    ZERO_VOLUME = "zero_volume"
    PRICE_DISCONTINUITY = "price_discontinuity"
    NEGATIVE_VALUES = "negative_values"


class DataQualityService:
    """
    Validates historical OHLC data quality.
    
    Compliance:
        - Rule #5: Never fabricate prices/ticks/candles
        - Rule #6: Fail closed if data is missing or invalid
    """
    
    def __init__(self):
        self.MAX_PRICE_JUMP_PCT = 10.0  # Flag >10% jumps
        self.MIN_QUALITY_SCORE = 0.80  # Minimum acceptable quality
    
    def validate_ohlc_dataframe(
        self, 
        df: pd.DataFrame, 
        symbol: str,
        interval: str
    ) -> Dict[str, Any]:
        """
        Comprehensive validation of OHLC DataFrame.
        
        Args:
            df: DataFrame with columns [timestamp, open, high, low, close, volume]
            symbol: Stock symbol for logging
            interval: Time interval (1m, 5m, 1d, etc.)
            
        Returns:
            Dict with validation results and quality score
        """
        if df is None or df.empty:
            return {
                "valid": False,
                "quality_score": 0.0,
                "issues": [{"type": QualityIssue.MISSING_CANDLES.value, "message": "DataFrame is empty"}],
                "symbol": symbol
            }
        
        issues = []
        
        # 1. Check required columns
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            return {
                "valid": False,
                "quality_score": 0.0,
                "issues": [{
                    "type": "missing_columns",
                    "message": f"Missing required columns: {missing_cols}"
                }],
                "symbol": symbol
            }
        
        # 2. Validate OHLC relationships
        ohlc_issues = self._validate_ohlc_relationships(df)
        issues.extend(ohlc_issues)
        
        # 3. Check for negative values
        negative_issues = self._check_negative_values(df)
        issues.extend(negative_issues)
        
        # 4. Check for duplicate timestamps
        duplicate_issues = self._check_duplicates(df)
        issues.extend(duplicate_issues)
        
        # 5. Check for missing candles (gaps)
        gap_issues = self._check_missing_candles(df, interval)
        issues.extend(gap_issues)
        
        # 6. Check for zero volume candles
        zero_vol_issues = self._check_zero_volume(df)
        issues.extend(zero_vol_issues)
        
        # 7. Check for price discontinuities
        discontinuity_issues = self._check_price_discontinuity(df)
        issues.extend(discontinuity_issues)
        
        # Calculate quality score
        total_candles = len(df)
        issue_count = len(issues)
        quality_score = max(0.0, 1.0 - (issue_count / max(total_candles, 1)))
        
        is_valid = quality_score >= self.MIN_QUALITY_SCORE
        
        result = {
            "valid": is_valid,
            "quality_score": round(quality_score, 2),
            "total_candles": total_candles,
            "issue_count": issue_count,
            "issues": issues[:10],  # Return first 10 issues
            "symbol": symbol,
            "interval": interval,
            "validated_at": datetime.utcnow().isoformat()
        }
        
        if not is_valid:
            logger.warning(
                f"Data quality FAILED for {symbol}: score={quality_score:.2f}, "
                f"issues={issue_count}/{total_candles}"
            )
        
        return result
    
    def _validate_ohlc_relationships(self, df: pd.DataFrame) -> List[Dict]:
        """Validate that High >= Low, High >= Open/Close, Low <= Open/Close"""
        issues = []
        
        # High must be >= Low
        invalid_hl = df[df['high'] < df['low']]
        if not invalid_hl.empty:
            for idx in invalid_hl.index[:5]:  # Report first 5
                issues.append({
                    "type": QualityIssue.INVALID_OHLC.value,
                    "message": f"High < Low at index {idx}",
                    "index": int(idx),
                    "high": float(df.loc[idx, 'high']),
                    "low": float(df.loc[idx, 'low'])
                })
        
        # High must be >= Open and Close
        invalid_ho = df[df['high'] < df['open']]
        if not invalid_ho.empty:
            for idx in invalid_ho.index[:5]:
                issues.append({
                    "type": QualityIssue.INVALID_OHLC.value,
                    "message": f"High < Open at index {idx}",
                    "index": int(idx)
                })
        
        invalid_hc = df[df['high'] < df['close']]
        if not invalid_hc.empty:
            for idx in invalid_hc.index[:5]:
                issues.append({
                    "type": QualityIssue.INVALID_OHLC.value,
                    "message": f"High < Close at index {idx}",
                    "index": int(idx)
                })
        
        # Low must be <= Open and Close
        invalid_lo = df[df['low'] > df['open']]
        if not invalid_lo.empty:
            for idx in invalid_lo.index[:5]:
                issues.append({
                    "type": QualityIssue.INVALID_OHLC.value,
                    "message": f"Low > Open at index {idx}",
                    "index": int(idx)
                })
        
        invalid_lc = df[df['low'] > df['close']]
        if not invalid_lc.empty:
            for idx in invalid_lc.index[:5]:
                issues.append({
                    "type": QualityIssue.INVALID_OHLC.value,
                    "message": f"Low > Close at index {idx}",
                    "index": int(idx)
                })
        
        return issues
    
    def _check_negative_values(self, df: pd.DataFrame) -> List[Dict]:
        """Check for negative prices or volume"""
        issues = []
        
        for col in ['open', 'high', 'low', 'close', 'volume']:
            negative = df[df[col] < 0]
            if not negative.empty:
                for idx in negative.index[:5]:
                    issues.append({
                        "type": QualityIssue.NEGATIVE_VALUES.value,
                        "message": f"Negative {col} at index {idx}",
                        "index": int(idx),
                        "column": col,
                        "value": float(df.loc[idx, col])
                    })
        
        return issues
    
    def _check_duplicates(self, df: pd.DataFrame) -> List[Dict]:
        """Check for duplicate timestamps"""
        issues = []
        
        if 'timestamp' in df.columns:
            duplicates = df[df.duplicated(subset=['timestamp'], keep=False)]
            if not duplicates.empty:
                unique_dups = duplicates['timestamp'].unique()[:5]
                for ts in unique_dups:
                    issues.append({
                        "type": QualityIssue.DUPLICATE_TIMESTAMP.value,
                        "message": f"Duplicate timestamp: {ts}",
                        "timestamp": str(ts)
                    })
        
        return issues
    
    def _check_missing_candles(self, df: pd.DataFrame, interval: str) -> List[Dict]:
        """
        Detect gaps in time series.
        
        Note: This is a simplified check. Production would need market hours awareness.
        """
        issues = []
        
        if 'timestamp' not in df.columns or len(df) < 2:
            return issues
        
        # Convert interval to timedelta
        interval_map = {
            '1m': timedelta(minutes=1),
            '5m': timedelta(minutes=5),
            '15m': timedelta(minutes=15),
            '30m': timedelta(minutes=30),
            '1h': timedelta(hours=1),
            '1d': timedelta(days=1)
        }
        
        expected_delta = interval_map.get(interval)
        if not expected_delta:
            return issues  # Unknown interval, skip check
        
        # Sort by timestamp
        df_sorted = df.sort_values('timestamp')
        timestamps = pd.to_datetime(df_sorted['timestamp'])
        
        # Check gaps (allowing 2x expected delta for market hours)
        max_gap = expected_delta * 2
        
        for i in range(1, len(timestamps)):
            gap = timestamps.iloc[i] - timestamps.iloc[i-1]
            if gap > max_gap:
                issues.append({
                    "type": QualityIssue.MISSING_CANDLES.value,
                    "message": f"Gap detected: {gap} between candles",
                    "gap_duration": str(gap),
                    "from_timestamp": str(timestamps.iloc[i-1]),
                    "to_timestamp": str(timestamps.iloc[i])
                })
                
                if len(issues) >= 5:  # Limit gap reports
                    break
        
        return issues
    
    def _check_zero_volume(self, df: pd.DataFrame) -> List[Dict]:
        """Check for zero volume candles"""
        issues = []
        
        zero_vol = df[df['volume'] == 0]
        if not zero_vol.empty:
            count = len(zero_vol)
            issues.append({
                "type": QualityIssue.ZERO_VOLUME.value,
                "message": f"{count} candles with zero volume",
                "count": count,
                "percentage": round(count / len(df) * 100, 2)
            })
        
        return issues
    
    def _check_price_discontinuity(self, df: pd.DataFrame) -> List[Dict]:
        """Check for abnormal price jumps (>10% without news)"""
        issues = []
        
        if len(df) < 2:
            return issues
        
        df_sorted = df.sort_index()
        
        # Calculate close-to-close percentage change
        df_sorted['pct_change'] = df_sorted['close'].pct_change() * 100
        
        # Flag jumps > 10%
        large_jumps = df_sorted[abs(df_sorted['pct_change']) > self.MAX_PRICE_JUMP_PCT]
        
        for idx in large_jumps.index[:5]:
            issues.append({
                "type": QualityIssue.PRICE_DISCONTINUITY.value,
                "message": f"Large price jump: {large_jumps.loc[idx, 'pct_change']:.2f}%",
                "index": int(idx),
                "pct_change": round(float(large_jumps.loc[idx, 'pct_change']), 2),
                "close": float(df_sorted.loc[idx, 'close'])
            })
        
        return issues


# Global instance
data_quality_service = DataQualityService()
