"""
Unit tests for P&L Tracker Service
"""

import pytest
from datetime import datetime, timedelta
import pytz

from app.services.pnl_tracker_service import PnLTracker
from app.database.models_monitoring import PnLSnapshot, TradePerformance

IST = pytz.timezone('Asia/Kolkata')


class TestPnLTracker:
    """Test suite for PnLTracker"""
    
    @pytest.mark.asyncio
    async def test_create_snapshot(self, db_session):
        """Test creating a P&L snapshot"""
        tracker = PnLTracker(db_session)
        
        snapshot = await tracker.create_snapshot(
            user_id=1,
            realized_pnl=1000.0,
            unrealized_pnl=500.0,
            positions_count=3,
            trades_count=10
        )
        
        assert snapshot is not None
        assert snapshot.user_id == 1
        assert snapshot.realized_pnl == 1000.0
        assert snapshot.unrealized_pnl == 500.0
        assert snapshot.total_pnl == 1500.0
        assert snapshot.positions_count == 3
    
    def test_get_latest_snapshot(self, db_session):
        """Test retrieving latest snapshot"""
        tracker = PnLTracker(db_session)
        
        # Create multiple snapshots
        import asyncio
        asyncio.run(tracker.create_snapshot(1, 100, 50, 1, 1))
        asyncio.run(tracker.create_snapshot(1, 200, 75, 2, 2))
        
        # Get latest
        latest = tracker.get_latest_snapshot(1)
        
        assert latest is not None
        assert latest.realized_pnl == 200
        assert latest.unrealized_pnl == 75
    
    @pytest.mark.asyncio
    async def test_record_trade(self, db_session):
        """Test recording a new trade"""
        tracker = PnLTracker(db_session)
        
        trade = await tracker.record_trade(
            user_id=1,
            symbol="NSE:RELIANCE",
            entry_price=2500.0,
            quantity=10,
            trade_type="LONG",
            strategy_name="QUAD_Strategy"
        )
        
        assert trade is not None
        assert trade.symbol == "NSE:RELIANCE"
        assert trade.entry_price == 2500.0
        assert trade.quantity == 10
        assert trade.status == "OPEN"
    
    @pytest.mark.asyncio
    async def test_close_trade_long(self, db_session):
        """Test closing a LONG trade"""
        tracker = PnLTracker(db_session)
        
        # Open trade
        trade = await tracker.record_trade(
            user_id=1,
            symbol="NSE:RELIANCE",
            entry_price=2500.0,
            quantity=10,
            trade_type="LONG"
        )
        
        # Close trade
        closed_trade = await tracker.close_trade(trade.id, exit_price=2550.0)
        
        assert closed_trade is not None
        assert closed_trade.status == "CLOSED"
        assert closed_trade.exit_price == 2550.0
        assert closed_trade.pnl == 500.0  # (2550 - 2500) * 10
        assert closed_trade.pnl_percent == 2.0  # 500 / 25000 * 100
    
    @pytest.mark.asyncio
    async def test_close_trade_short(self, db_session):
        """Test closing a SHORT trade"""
        tracker = PnLTracker(db_session)
        
        # Open short trade
        trade = await tracker.record_trade(
            user_id=1,
            symbol="NSE:RELIANCE",
            entry_price=2500.0,
            quantity=10,
            trade_type="SHORT"
        )
        
        # Close trade (price went down, profit)
        closed_trade = await tracker.close_trade(trade.id, exit_price=2450.0)
        
        assert closed_trade.pnl == 500.0  # (2500 - 2450) * 10
    
    def test_get_trade_performance(self, db_session):
        """Test trade performance metrics"""
        tracker = PnLTracker(db_session)
        
        import asyncio
        
        # Create and close multiple trades
        for i in range(5):
            trade = asyncio.run(tracker.record_trade(
                user_id=1,
                symbol="NSE:RELIANCE",
                entry_price=2500.0,
                quantity=10,
                trade_type="LONG"
            ))
            
            # Close with profit or loss
            exit_price = 2550.0 if i % 2 == 0 else 2450.0
            asyncio.run(tracker.close_trade(trade.id, exit_price))
        
        # Get performance
        performance = tracker.get_trade_performance(user_id=1, days=30)
        
        assert performance["total_trades"] == 5
        assert performance["winning_trades"] == 3  # 0, 2, 4
        assert performance["losing_trades"] == 2   # 1, 3
        assert performance["win_rate"] == 60.0
    
    def test_get_strategy_performance(self, db_session):
        """Test per-strategy performance"""
        tracker = PnLTracker(db_session)
        
        import asyncio
        
        # Create trades for different strategies
        strategies = ["Strategy_A", "Strategy_B"]
        for strategy in strategies:
            for _ in range(3):
                trade = asyncio.run(tracker.record_trade(
                    user_id=1,
                    symbol="NSE:RELIANCE",
                    entry_price=2500.0,
                    quantity=10,
                    trade_type="LONG",
                    strategy_name=strategy
                ))
                asyncio.run(tracker.close_trade(trade.id, 2550.0))
        
        # Get strategy performance
        strategies = tracker.get_strategy_performance(user_id=1, days=30)
        
        assert len(strategies) == 2
        assert all(s["trade_count"] == 3 for s in strategies)
        assert all(s["total_pnl"] == 1500.0 for s in strategies)  # 500 * 3
