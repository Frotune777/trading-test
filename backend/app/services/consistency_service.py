# app/services/consistency_service.py

import logging
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.database.db_manager import DatabaseManager
from app.services.alert_service import AlertService

logger = logging.getLogger(__name__)

class DataConsistencyCheck:
    """
    Checks for gaps and inconsistencies in price data.
    """
    def __init__(self, db_path: str = "stock_data.db"):
        self.db = DatabaseManager(db_path)
        self.alerts = AlertService(db_path)

    async def detect_ohlc_gaps(self, symbol: str, timeframe: str = "1m", days: int = 1) -> List[Dict]:
        """
        Identifies missing timestamps in intraday data.
        """
        query = """
            SELECT timestamp FROM intraday_prices 
            WHERE symbol = ? AND timeframe = ? 
            AND timestamp >= date('now', ?)
            ORDER BY timestamp ASC
        """
        res = self.db.query_dict(query, (symbol, timeframe, f"-{days} days"))
        if not res:
            return []

        timestamps = [datetime.fromisoformat(r['timestamp']) for r in res]
        gaps = []
        
        # Define expected interval
        interval = timedelta(minutes=1) if timeframe == "1m" else timedelta(minutes=5)
        
        for i in range(1, len(timestamps)):
            diff = timestamps[i] - timestamps[i-1]
            if diff > interval:
                # Gap detected
                gap_info = {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "start": timestamps[i-1].isoformat(),
                    "end": timestamps[i].isoformat(),
                    "duration_mins": diff.total_seconds() / 60
                }
                gaps.append(gap_info)
                
                await self.alerts.emit(
                    alert_type="DATA_GAP_DETECTED",
                    message=f"Detected {gap_info['duration_mins']:.0f} min gap in {symbol} ({timeframe})",
                    level="WARNING",
                    symbol=symbol,
                    metadata=gap_info
                )
        
        return gaps

    async def validate_data_integrity(self, symbol: str) -> bool:
        """
        Cross-checks latest_snapshot against intraday_prices.
        """
        snapshot = self.db.get_snapshot(symbol)
        if not snapshot:
            return True
        
        # Get latest intraday price
        query = "SELECT close FROM intraday_prices WHERE symbol = ? ORDER BY timestamp DESC LIMIT 1"
        res = self.db.query_dict(query, (symbol,))
        
        if res:
            latest_intraday = res[0]['close']
            latest_snapshot = snapshot['current_price']
            
            # Allow for small drift (e.g. 0.1%)
            diff_pct = abs(latest_intraday - latest_snapshot) / latest_snapshot
            if diff_pct > 0.005: # 0.5% Threshold
                await self.alerts.emit(
                    alert_type="DATA_INCONSISTENCY",
                    message=f"Price mismatch for {symbol}: Snapshot {latest_snapshot} vs Intraday {latest_intraday}",
                    level="CRITICAL",
                    symbol=symbol,
                    metadata={"snapshot": latest_snapshot, "intraday": latest_intraday, "diff_pct": diff_pct}
                )
                return False
                
        return True
