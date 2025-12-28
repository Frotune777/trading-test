"""
Unit tests for Risk Engine
Tests risk limit validation, kill switch, and pre-trade checks
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from app.core.risk_engine import RiskEngine
from app.database.models_user import User


class TestRiskEngine:
    """Test suite for RiskEngine"""
    
    def test_risk_engine_initialization(self, db_session):
        """Test RiskEngine initializes correctly"""
        risk_engine = RiskEngine(db_session)
        assert risk_engine is not None
        assert risk_engine.db == db_session
    
    def test_max_daily_loss_limit_enforced(self, db_session):
        """Test that max daily loss limit is enforced"""
        risk_engine = RiskEngine(db_session)
        
        # Mock current P&L at -9000 (close to -10000 limit)
        with patch.object(risk_engine, 'get_daily_pnl', return_value=-9000):
            # Try to place order that would exceed limit
            result = risk_engine.validate_trade({
                "symbol": "RELIANCE",
                "action": "BUY",
                "quantity": 10,
                "price": 2500,
                "potential_loss": 1500  # Would bring total to -10500
            })
            
            assert result["allowed"] is False
            assert "daily loss limit" in result["reason"].lower()
    
    def test_max_position_quantity_enforced(self, db_session):
        """Test that max position quantity is enforced"""
        risk_engine = RiskEngine(db_session)
        
        # Mock current position at 90 shares
        with patch.object(risk_engine, 'get_position_quantity', return_value=90):
            # Try to buy 20 more (would exceed 100 limit)
            result = risk_engine.validate_trade({
                "symbol": "RELIANCE",
                "action": "BUY",
                "quantity": 20
            })
            
            assert result["allowed"] is False
            assert "position limit" in result["reason"].lower()
    
    def test_kill_switch_blocks_all_trades(self, db_session):
        """Test that kill switch blocks all trades"""
        risk_engine = RiskEngine(db_session)
        
        # Activate kill switch
        risk_engine.activate_kill_switch("Emergency stop")
        
        # Try to place any trade
        result = risk_engine.validate_trade({
            "symbol": "RELIANCE",
            "action": "BUY",
            "quantity": 1
        })
        
        assert result["allowed"] is False
        assert "kill switch" in result["reason"].lower()
    
    def test_kill_switch_can_be_deactivated(self, db_session):
        """Test that kill switch can be deactivated"""
        risk_engine = RiskEngine(db_session)
        
        # Activate then deactivate
        risk_engine.activate_kill_switch("Test")
        risk_engine.deactivate_kill_switch()
        
        # Trade should be allowed (assuming other checks pass)
        with patch.object(risk_engine, 'get_daily_pnl', return_value=0):
            with patch.object(risk_engine, 'get_position_quantity', return_value=0):
                result = risk_engine.validate_trade({
                    "symbol": "RELIANCE",
                    "action": "BUY",
                    "quantity": 1,
                    "price": 2500
                })
                
                assert result["allowed"] is True
    
    def test_max_trades_per_day_enforced(self, db_session):
        """Test that max trades per day is enforced"""
        risk_engine = RiskEngine(db_session)
        
        # Mock trade count at limit
        with patch.object(risk_engine, 'get_daily_trade_count', return_value=50):
            result = risk_engine.validate_trade({
                "symbol": "RELIANCE",
                "action": "BUY",
                "quantity": 1
            })
            
            assert result["allowed"] is False
            assert "trade limit" in result["reason"].lower()
    
    def test_max_account_exposure_enforced(self, db_session):
        """Test that max account exposure is enforced"""
        risk_engine = RiskEngine(db_session)
        
        # Mock current exposure at 90% of account value
        with patch.object(risk_engine, 'get_account_exposure', return_value=0.90):
            # Try to add more exposure
            result = risk_engine.validate_trade({
                "symbol": "RELIANCE",
                "action": "BUY",
                "quantity": 100,
                "price": 2500,
                "account_value": 1000000
            })
            
            assert result["allowed"] is False
            assert "exposure limit" in result["reason"].lower()
    
    def test_valid_trade_passes_all_checks(self, db_session):
        """Test that valid trade passes all risk checks"""
        risk_engine = RiskEngine(db_session)
        
        # Mock all checks passing
        with patch.object(risk_engine, 'get_daily_pnl', return_value=0):
            with patch.object(risk_engine, 'get_position_quantity', return_value=0):
                with patch.object(risk_engine, 'get_daily_trade_count', return_value=0):
                    with patch.object(risk_engine, 'get_account_exposure', return_value=0.10):
                        result = risk_engine.validate_trade({
                            "symbol": "RELIANCE",
                            "action": "BUY",
                            "quantity": 10,
                            "price": 2500
                        })
                        
                        assert result["allowed"] is True
                        assert "reason" not in result
    
    def test_risk_limits_are_configurable(self, db_session):
        """Test that risk limits can be configured"""
        risk_engine = RiskEngine(db_session)
        
        # Update risk limits
        new_limits = {
            "max_daily_loss": 5000,
            "max_position_quantity": 50,
            "max_trades_per_day": 25
        }
        risk_engine.update_risk_limits(new_limits)
        
        assert risk_engine.risk_limits["max_daily_loss"] == 5000
        assert risk_engine.risk_limits["max_position_quantity"] == 50
        assert risk_engine.risk_limits["max_trades_per_day"] == 25
    
    def test_risk_validation_logs_all_checks(self, db_session):
        """Test that risk validation logs all checks"""
        risk_engine = RiskEngine(db_session)
        
        with patch.object(risk_engine, 'log_risk_check') as mock_log:
            risk_engine.validate_trade({
                "symbol": "RELIANCE",
                "action": "BUY",
                "quantity": 10
            })
            
            # Verify logging was called
            assert mock_log.called
