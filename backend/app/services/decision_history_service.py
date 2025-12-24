# app/services/decision_history_service.py

"""
QUAD v1.1 - Decision History Service

Purpose: Manage storage and retrieval of historical TradeIntent decisions.
Provides read-only access to decision history for observability and drift analysis.

CRITICAL CONSTRAINTS:
- Read-only access (no decision mutation)
- No execution logic (pure storage)
- Thread-safe operations
"""

import logging
import uuid
from typing import List, Optional
from datetime import datetime, timedelta
from ..core.decision_history import DecisionHistory, DecisionHistoryEntry
from ..core.trade_intent import TradeIntent
from ..database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


class DecisionHistoryService:
    """
    Service for managing decision history storage and retrieval.
    
    Schema Version: 1.1.0
    """
    
    def __init__(self, db_path: str = "stock_data.db"):
        """
        Initialize decision history service.
        
        Args:
            db_path: Path to SQLite database
        """
        self.db = DatabaseManager(db_path)
        self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        """Create decision_history table if it doesn't exist."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS decision_history (
            decision_id TEXT PRIMARY KEY,
            symbol TEXT NOT NULL,
            analysis_timestamp TEXT NOT NULL,
            directional_bias TEXT NOT NULL,
            conviction_score REAL NOT NULL,
            calibration_version TEXT,
            pillar_count_active INTEGER NOT NULL,
            pillar_count_placeholder INTEGER NOT NULL,
            pillar_count_failed INTEGER NOT NULL,
            engine_version TEXT NOT NULL,
            contract_version TEXT NOT NULL,
            created_at TEXT NOT NULL,
            is_superseded INTEGER DEFAULT 0,
            pillar_scores TEXT,  -- JSON
            pillar_biases TEXT   -- JSON
        );
        
        CREATE INDEX IF NOT EXISTS idx_decision_history_symbol 
        ON decision_history(symbol, analysis_timestamp DESC);
        
        CREATE INDEX IF NOT EXISTS idx_decision_history_created 
        ON decision_history(created_at DESC);
        """
        
        try:
            self.db.conn.executescript(create_table_sql)
            self.db.conn.commit()
            logger.info("✅ Decision history table verified")
        except Exception as e:
            logger.error(f"Failed to create decision_history table: {e}")
            raise
    
    def save_decision(self, trade_intent: TradeIntent) -> str:
        """
        Save a TradeIntent to decision history.
        
        Args:
            trade_intent: TradeIntent to save
        
        Returns:
            decision_id: Unique identifier for this decision
        """
        import json
        
        # Generate decision ID
        decision_id = f"dec_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{trade_intent.symbol}_{uuid.uuid4().hex[:8]}"
        
        # Create history entry
        entry = DecisionHistoryEntry.from_trade_intent(trade_intent, decision_id)
        
        # Serialize pillar data
        pillar_scores_json = json.dumps(entry.pillar_scores) if entry.pillar_scores else None
        pillar_biases_json = json.dumps(entry.pillar_biases) if entry.pillar_biases else None
        
        # Insert into database
        insert_sql = """
        INSERT INTO decision_history (
            decision_id, symbol, analysis_timestamp, directional_bias, conviction_score,
            calibration_version, pillar_count_active, pillar_count_placeholder, pillar_count_failed,
            engine_version, contract_version, created_at, is_superseded,
            pillar_scores, pillar_biases
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        try:
            self.db.conn.execute(insert_sql, (
                entry.decision_id,
                entry.symbol,
                entry.analysis_timestamp.isoformat(),
                entry.directional_bias.value,
                entry.conviction_score,
                entry.calibration_version,
                entry.pillar_count_active,
                entry.pillar_count_placeholder,
                entry.pillar_count_failed,
                entry.engine_version,
                entry.contract_version,
                entry.created_at.isoformat() if entry.created_at else datetime.now().isoformat(),
                1 if entry.is_superseded else 0,
                pillar_scores_json,
                pillar_biases_json
            ))
            self.db.conn.commit()
            logger.info(f"✅ Saved decision {decision_id} for {trade_intent.symbol}")
        except Exception as e:
            logger.error(f"Failed to save decision {decision_id}: {e}")
            raise
        
        return decision_id
    
    def get_history(
        self,
        symbol: str,
        limit: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> DecisionHistory:
        """
        Retrieve decision history for a symbol.
        
        Args:
            symbol: Symbol to retrieve history for
            limit: Maximum number of entries to return (None = all)
            start_date: Filter by start date (inclusive)
            end_date: Filter by end date (inclusive)
        
        Returns:
            DecisionHistory object
        """
        import json
        from ..core.trade_intent import DirectionalBias
        
        # Build query
        query = "SELECT * FROM decision_history WHERE symbol = ?"
        params = [symbol]
        
        if start_date:
            query += " AND analysis_timestamp >= ?"
            params.append(start_date.isoformat())
        
        if end_date:
            query += " AND analysis_timestamp <= ?"
            params.append(end_date.isoformat())
        
        query += " ORDER BY analysis_timestamp DESC"
        
        if limit:
            query += f" LIMIT {limit}"
        
        try:
            cursor = self.db.conn.execute(query, params)
            rows = cursor.fetchall()
        except Exception as e:
            logger.error(f"Failed to retrieve history for {symbol}: {e}")
            return DecisionHistory(symbol=symbol, entries=[])
        
        # Convert rows to DecisionHistoryEntry objects
        entries = []
        for row in rows:
            pillar_scores = json.loads(row[13]) if row[13] else None
            pillar_biases = json.loads(row[14]) if row[14] else None
            
            entry = DecisionHistoryEntry(
                decision_id=row[0],
                symbol=row[1],
                analysis_timestamp=datetime.fromisoformat(row[2]),
                directional_bias=DirectionalBias(row[3]),
                conviction_score=row[4],
                calibration_version=row[5],
                pillar_count_active=row[6],
                pillar_count_placeholder=row[7],
                pillar_count_failed=row[8],
                engine_version=row[9],
                contract_version=row[10],
                created_at=datetime.fromisoformat(row[11]) if row[11] else None,
                is_superseded=bool(row[12]),
                pillar_scores=pillar_scores,
                pillar_biases=pillar_biases
            )
            entries.append(entry)
        
        history = DecisionHistory(symbol=symbol, entries=entries)
        logger.info(f"Retrieved {len(entries)} decisions for {symbol}")
        
        return history
    
    def get_recent_decisions(self, symbol: str, limit: int = 10) -> List[DecisionHistoryEntry]:
        """
        Get N most recent decisions for a symbol.
        
        Args:
            symbol: Symbol to retrieve decisions for
            limit: Number of decisions to return
        
        Returns:
            List of DecisionHistoryEntry
        """
        history = self.get_history(symbol, limit=limit)
        return history.get_recent(limit)
    
    def get_decisions_by_date_range(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[DecisionHistoryEntry]:
        """
        Get decisions within a date range.
        
        Args:
            symbol: Symbol to retrieve decisions for
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
        
        Returns:
            List of DecisionHistoryEntry
        """
        history = self.get_history(symbol, start_date=start_date, end_date=end_date)
        return history.entries
    
    def get_latest_decision(self, symbol: str) -> Optional[DecisionHistoryEntry]:
        """
        Get the most recent decision for a symbol.
        
        Args:
            symbol: Symbol to retrieve decision for
        
        Returns:
            DecisionHistoryEntry or None if no history exists
        """
        recent = self.get_recent_decisions(symbol, limit=1)
        return recent[0] if recent else None
    
    def mark_superseded(self, decision_id: str):
        """
        Mark a decision as superseded by a newer analysis.
        
        Args:
            decision_id: ID of decision to mark as superseded
        """
        update_sql = "UPDATE decision_history SET is_superseded = 1 WHERE decision_id = ?"
        
        try:
            self.db.conn.execute(update_sql, (decision_id,))
            self.db.conn.commit()
            logger.info(f"Marked decision {decision_id} as superseded")
        except Exception as e:
            logger.error(f"Failed to mark decision {decision_id} as superseded: {e}")
            raise
    
    def get_statistics(self, symbol: str, days: int = 30) -> dict:
        """
        Get statistics for a symbol's decision history.
        
        Args:
            symbol: Symbol to analyze
            days: Number of days to look back
        
        Returns:
            Dictionary with statistics
        """
        start_date = datetime.now() - timedelta(days=days)
        history = self.get_history(symbol, start_date=start_date)
        
        if not history.entries:
            return {
                "symbol": symbol,
                "total_decisions": 0,
                "days_analyzed": days,
                "average_conviction": 0.0,
                "bias_distribution": {},
                "conviction_range": (0.0, 0.0)
            }
        
        return {
            "symbol": symbol,
            "total_decisions": history.total_decisions,
            "days_analyzed": days,
            "average_conviction": history.get_average_conviction(),
            "bias_distribution": history.get_bias_distribution(),
            "conviction_range": history.get_conviction_range(),
            "earliest_decision": history.earliest_decision.isoformat() if history.earliest_decision else None,
            "latest_decision": history.latest_decision.isoformat() if history.latest_decision else None
        }


# Singleton instance
_decision_history_service_instance = None


def get_decision_history_service() -> DecisionHistoryService:
    """Get or create DecisionHistoryService singleton instance."""
    global _decision_history_service_instance
    if _decision_history_service_instance is None:
        _decision_history_service_instance = DecisionHistoryService()
    return _decision_history_service_instance
