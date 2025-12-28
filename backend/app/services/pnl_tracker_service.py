"""
P&L Tracker Service
Real-time P&L calculation and historical tracking
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pytz
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.database.models_monitoring import PnLSnapshot, TradePerformance

logger = logging.getLogger(__name__)
IST = pytz.timezone('Asia/Kolkata')


class PnLTracker:
    """Track and calculate P&L metrics"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_snapshot(
        self,
        user_id: int,
        realized_pnl: float,
        unrealized_pnl: float,
        positions_count: int,
        trades_count: int
    ):
        """Create a P&L snapshot"""
        try:
            snapshot = PnLSnapshot(
                user_id=user_id,
                realized_pnl=realized_pnl,
                unrealized_pnl=unrealized_pnl,
                total_pnl=realized_pnl + unrealized_pnl,
                day_pnl=self._calculate_day_pnl(user_id),
                positions_count=positions_count,
                trades_count=trades_count,
                timestamp=datetime.now(IST)
            )
            
            self.db.add(snapshot)
            self.db.commit()
            
            return snapshot
            
        except Exception as e:
            logger.error(f"Failed to create P&L snapshot: {e}")
            self.db.rollback()
            return None
    
    def _calculate_day_pnl(self, user_id: int) -> float:
        """Calculate P&L for current day"""
        today_start = datetime.now(IST).replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Get first snapshot of the day
        first_snapshot = self.db.query(PnLSnapshot).filter(
            and_(
                PnLSnapshot.user_id == user_id,
                PnLSnapshot.timestamp >= today_start
            )
        ).order_by(PnLSnapshot.timestamp.asc()).first()
        
        # Get latest snapshot
        latest_snapshot = self.db.query(PnLSnapshot).filter(
            PnLSnapshot.user_id == user_id
        ).order_by(PnLSnapshot.timestamp.desc()).first()
        
        if not first_snapshot or not latest_snapshot:
            return 0.0
        
        return latest_snapshot.total_pnl - first_snapshot.total_pnl
    
    def get_latest_snapshot(self, user_id: int) -> Optional[PnLSnapshot]:
        """Get latest P&L snapshot for user"""
        return self.db.query(PnLSnapshot).filter(
            PnLSnapshot.user_id == user_id
        ).order_by(PnLSnapshot.timestamp.desc()).first()
    
    def get_snapshot_history(
        self,
        user_id: int,
        hours: int = 24,
        limit: int = 100
    ) -> List[PnLSnapshot]:
        """Get P&L snapshot history"""
        since = datetime.now(IST) - timedelta(hours=hours)
        
        return self.db.query(PnLSnapshot).filter(
            and_(
                PnLSnapshot.user_id == user_id,
                PnLSnapshot.timestamp >= since
            )
        ).order_by(PnLSnapshot.timestamp.desc()).limit(limit).all()
    
    async def record_trade(
        self,
        user_id: int,
        symbol: str,
        entry_price: float,
        quantity: int,
        trade_type: str,
        strategy_name: Optional[str] = None
    ) -> TradePerformance:
        """Record a new trade (entry)"""
        try:
            trade = TradePerformance(
                user_id=user_id,
                symbol=symbol,
                strategy_name=strategy_name,
                entry_time=datetime.now(IST),
                entry_price=entry_price,
                quantity=quantity,
                trade_type=trade_type,
                status='OPEN'
            )
            
            self.db.add(trade)
            self.db.commit()
            
            return trade
            
        except Exception as e:
            logger.error(f"Failed to record trade: {e}")
            self.db.rollback()
            return None
    
    async def close_trade(
        self,
        trade_id: int,
        exit_price: float
    ):
        """Close a trade and calculate P&L"""
        try:
            trade = self.db.query(TradePerformance).filter(
                TradePerformance.id == trade_id
            ).first()
            
            if not trade:
                logger.error(f"Trade {trade_id} not found")
                return None
            
            # Calculate P&L
            if trade.trade_type == 'LONG':
                pnl = (exit_price - trade.entry_price) * trade.quantity
            else:  # SHORT
                pnl = (trade.entry_price - exit_price) * trade.quantity
            
            pnl_percent = (pnl / (trade.entry_price * trade.quantity)) * 100
            
            # Calculate holding time
            exit_time = datetime.now(IST)
            holding_time = (exit_time - trade.entry_time).total_seconds() / 60
            
            # Update trade
            trade.exit_time = exit_time
            trade.exit_price = exit_price
            trade.pnl = pnl
            trade.pnl_percent = pnl_percent
            trade.holding_time_minutes = int(holding_time)
            trade.status = 'CLOSED'
            
            self.db.commit()
            
            return trade
            
        except Exception as e:
            logger.error(f"Failed to close trade: {e}")
            self.db.rollback()
            return None
    
    def get_trade_performance(
        self,
        user_id: int,
        days: int = 30,
        strategy_name: Optional[str] = None
    ) -> Dict:
        """Get trade performance metrics"""
        since = datetime.now(IST) - timedelta(days=days)
        
        query = self.db.query(TradePerformance).filter(
            and_(
                TradePerformance.user_id == user_id,
                TradePerformance.entry_time >= since,
                TradePerformance.status == 'CLOSED'
            )
        )
        
        if strategy_name:
            query = query.filter(TradePerformance.strategy_name == strategy_name)
        
        trades = query.all()
        
        if not trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0,
                "avg_pnl": 0,
                "total_pnl": 0,
                "avg_holding_time_minutes": 0
            }
        
        winning_trades = [t for t in trades if t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl <= 0]
        
        return {
            "total_trades": len(trades),
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": (len(winning_trades) / len(trades)) * 100,
            "avg_pnl": sum(t.pnl for t in trades) / len(trades),
            "total_pnl": sum(t.pnl for t in trades),
            "avg_holding_time_minutes": sum(t.holding_time_minutes or 0 for t in trades) / len(trades),
            "best_trade": max(trades, key=lambda t: t.pnl).pnl,
            "worst_trade": min(trades, key=lambda t: t.pnl).pnl
        }
    
    def get_strategy_performance(self, user_id: int, days: int = 30) -> List[Dict]:
        """Get per-strategy performance"""
        since = datetime.now(IST) - timedelta(days=days)
        
        results = self.db.query(
            TradePerformance.strategy_name,
            func.count(TradePerformance.id).label('trade_count'),
            func.sum(TradePerformance.pnl).label('total_pnl'),
            func.avg(TradePerformance.pnl).label('avg_pnl')
        ).filter(
            and_(
                TradePerformance.user_id == user_id,
                TradePerformance.entry_time >= since,
                TradePerformance.status == 'CLOSED',
                TradePerformance.strategy_name.isnot(None)
            )
        ).group_by(
            TradePerformance.strategy_name
        ).all()
        
        return [
            {
                "strategy_name": row.strategy_name,
                "trade_count": row.trade_count,
                "total_pnl": round(row.total_pnl, 2),
                "avg_pnl": round(row.avg_pnl, 2)
            }
            for row in results
        ]
