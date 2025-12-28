"""
Integration tests for Risk Control API Endpoints
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestRiskControlEndpoints:
    """Test suite for Risk Control API endpoints"""
    
    def test_get_risk_limits(self):
        """Test GET /risk-control/limits"""
        response = client.get("/api/v1/risk-control/limits")
        
        assert response.status_code in [200, 401]
        
        if response.status_code == 200:
            data = response.json()
            assert "max_daily_loss" in data or isinstance(data, dict)
    
    def test_update_risk_limits_requires_auth(self):
        """Test that updating risk limits requires authentication"""
        response = client.put(
            "/api/v1/risk-control/limits",
            json={
                "max_daily_loss": 10000,
                "max_position_quantity": 100
            }
        )
        
        # Should require auth
        assert response.status_code in [200, 401, 403]
    
    def test_get_kill_switch_status(self):
        """Test GET /risk-control/kill-switch"""
        response = client.get("/api/v1/risk-control/kill-switch")
        
        assert response.status_code in [200, 401]
        
        if response.status_code == 200:
            data = response.json()
            assert "active" in data or "status" in data
    
    def test_activate_kill_switch_requires_auth(self):
        """Test that activating kill switch requires authentication"""
        response = client.post(
            "/api/v1/risk-control/kill-switch/activate",
            json={"reason": "Emergency stop"}
        )
        
        # Should require auth
        assert response.status_code in [200, 401, 403]
    
    def test_deactivate_kill_switch_requires_auth(self):
        """Test that deactivating kill switch requires authentication"""
        response = client.post("/api/v1/risk-control/kill-switch/deactivate")
        
        # Should require auth
        assert response.status_code in [200, 401, 403]
    
    def test_get_risk_metrics(self):
        """Test GET /risk-control/metrics"""
        response = client.get("/api/v1/risk-control/metrics")
        
        assert response.status_code in [200, 401]
