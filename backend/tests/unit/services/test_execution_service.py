"""
Unit tests for Execution Service
Tests order placement, execution gate, and broker integration
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from app.services.execution_service import ExecutionService
from app.database.models_user import User


class TestExecutionService:
    """Test suite for Execution Service"""
    
    def test_execution_service_initialization(self, db_session):
        """Test Execution service initializes correctly"""
        exec_service = ExecutionService(db_session)
        assert exec_service is not None
        assert exec_service.db == db_session
    
    def test_auto_mode_executes_immediately(self, db_session, test_order_data):
        """Test that auto mode executes orders immediately"""
        exec_service = ExecutionService(db_session)
        
        # Create user in auto mode
        user = User(username="testuser", order_mode="auto")
        db_session.add(user)
        db_session.commit()
        
        with patch.object(exec_service, 'submit_to_broker') as mock_broker:
            mock_broker.return_value = {"order_id": "12345", "status": "PENDING"}
            
            result = exec_service.place_order(user.id, test_order_data)
            
            assert result["execute_immediately"] is True
            assert mock_broker.called
    
    def test_semi_auto_mode_queues_for_approval(self, db_session, test_order_data):
        """Test that semi_auto mode queues orders for approval"""
        exec_service = ExecutionService(db_session)
        
        # Create user in semi_auto mode
        user = User(username="testuser", order_mode="semi_auto")
        db_session.add(user)
        db_session.commit()
        
        with patch.object(exec_service, 'submit_to_broker') as mock_broker:
            result = exec_service.place_order(user.id, test_order_data)
            
            assert result["execute_immediately"] is False
            assert "pending_order_id" in result
            assert not mock_broker.called
    
    def test_risk_validation_before_execution(self, db_session, test_order_data):
        """Test that risk validation occurs before execution"""
        exec_service = ExecutionService(db_session)
        
        user = User(username="testuser", order_mode="auto")
        db_session.add(user)
        db_session.commit()
        
        with patch.object(exec_service.risk_engine, 'validate_trade') as mock_risk:
            mock_risk.return_value = {"allowed": False, "reason": "Risk limit exceeded"}
            
            result = exec_service.place_order(user.id, test_order_data)
            
            assert result["allowed"] is False
            assert "reason" in result
    
    def test_broker_submission_success(self, db_session, test_order_data):
        """Test successful broker submission"""
        exec_service = ExecutionService(db_session)
        
        with patch('app.services.broker_service.submit_order') as mock_submit:
            mock_submit.return_value = {
                "success": True,
                "order_id": "BROKER123",
                "status": "PENDING"
            }
            
            result = exec_service.submit_to_broker(test_order_data)
            
            assert result["success"] is True
            assert result["order_id"] == "BROKER123"
    
    def test_broker_submission_failure_handling(self, db_session, test_order_data):
        """Test broker submission failure handling"""
        exec_service = ExecutionService(db_session)
        
        with patch('app.services.broker_service.submit_order') as mock_submit:
            mock_submit.side_effect = Exception("Broker connection failed")
            
            result = exec_service.submit_to_broker(test_order_data)
            
            assert result["success"] is False
            assert "error" in result
    
    def test_order_status_tracking(self, db_session):
        """Test order status tracking"""
        exec_service = ExecutionService(db_session)
        
        order_id = "BROKER123"
        
        with patch('app.services.broker_service.get_order_status') as mock_status:
            mock_status.return_value = {"status": "COMPLETE", "filled_qty": 10}
            
            status = exec_service.get_order_status(order_id)
            
            assert status["status"] == "COMPLETE"
            assert status["filled_qty"] == 10
    
    def test_execution_audit_logging(self, db_session, test_order_data):
        """Test that all executions are logged"""
        exec_service = ExecutionService(db_session)
        
        user = User(username="testuser", order_mode="auto")
        db_session.add(user)
        db_session.commit()
        
        with patch.object(exec_service, 'log_execution') as mock_log:
            with patch.object(exec_service, 'submit_to_broker'):
                exec_service.place_order(user.id, test_order_data)
                
                assert mock_log.called
    
    def test_basket_order_execution(self, db_session):
        """Test basket order execution"""
        exec_service = ExecutionService(db_session)
        
        basket_order = {
            "orders": [
                {"symbol": "RELIANCE", "action": "BUY", "quantity": 10},
                {"symbol": "TCS", "action": "BUY", "quantity": 5}
            ]
        }
        
        user = User(username="testuser", order_mode="auto")
        db_session.add(user)
        db_session.commit()
        
        with patch.object(exec_service, 'submit_to_broker') as mock_broker:
            mock_broker.return_value = {"success": True, "order_id": "BASKET123"}
            
            result = exec_service.place_basket_order(user.id, basket_order)
            
            assert result["success"] is True
            assert mock_broker.call_count == 2  # Two orders in basket
    
    def test_order_modification(self, db_session):
        """Test order modification"""
        exec_service = ExecutionService(db_session)
        
        order_id = "BROKER123"
        modifications = {"quantity": 15, "price": 2550}
        
        with patch('app.services.broker_service.modify_order') as mock_modify:
            mock_modify.return_value = {"success": True, "order_id": order_id}
            
            result = exec_service.modify_order(order_id, modifications)
            
            assert result["success"] is True
    
    def test_order_cancellation(self, db_session):
        """Test order cancellation"""
        exec_service = ExecutionService(db_session)
        
        order_id = "BROKER123"
        
        with patch('app.services.broker_service.cancel_order') as mock_cancel:
            mock_cancel.return_value = {"success": True, "status": "CANCELLED"}
            
            result = exec_service.cancel_order(order_id)
            
            assert result["success"] is True
            assert result["status"] == "CANCELLED"
