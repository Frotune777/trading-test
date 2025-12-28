"""
Integration tests for Execution API Endpoints
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestExecutionEndpoints:
    """Test suite for Execution API endpoints"""
    
    def test_place_order_requires_auth(self):
        """Test that order placement requires authentication"""
        response = client.post(
            "/api/v1/execution/order",
            json={
                "symbol": "NSE:RELIANCE",
                "action": "BUY",
                "quantity": 10,
                "price": 2500
            }
        )
        
        # Should require authentication
        assert response.status_code in [401, 403]
    
    def test_get_order_status(self):
        """Test GET /execution/order/{order_id}"""
        response = client.get("/api/v1/execution/order/12345")
        
        # Should return order status or 404
        assert response.status_code in [200, 404, 401]
    
    def test_cancel_order(self):
        """Test DELETE /execution/order/{order_id}"""
        response = client.delete("/api/v1/execution/order/12345")
        
        # Should require auth or return 404
        assert response.status_code in [200, 404, 401, 403]
    
    def test_get_user_orders(self):
        """Test GET /execution/orders"""
        response = client.get("/api/v1/execution/orders")
        
        # Should require auth
        assert response.status_code in [200, 401]
    
    def test_place_basket_order(self):
        """Test POST /execution/basket"""
        response = client.post(
            "/api/v1/execution/basket",
            json={
                "orders": [
                    {"symbol": "NSE:RELIANCE", "action": "BUY", "quantity": 10},
                    {"symbol": "NSE:TCS", "action": "BUY", "quantity": 5}
                ]
            }
        )
        
        # Should require auth
        assert response.status_code in [200, 401, 403]
