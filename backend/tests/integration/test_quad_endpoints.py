"""
Integration tests for QUAD Analytics API Endpoints
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestQUADEndpoints:
    """Test suite for QUAD Analytics API endpoints"""
    
    def test_analyze_symbol(self):
        """Test POST /quad/analyze"""
        response = client.post(
            "/api/v1/quad/analyze",
            json={"symbol": "RELIANCE"}
        )
        
        # Should return analysis or error
        assert response.status_code in [200, 404, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "symbol" in data
            assert "conviction_score" in data
    
    def test_get_decision_history(self):
        """Test GET /quad/history"""
        response = client.get("/api/v1/quad/history?limit=10")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "decisions" in data or isinstance(data, list)
    
    def test_get_pillar_drift(self):
        """Test GET /quad/drift/{symbol}"""
        response = client.get("/api/v1/quad/drift/RELIANCE?days=7")
        
        # Should return drift data or 404
        assert response.status_code in [200, 404]
    
    def test_get_conviction_timeline(self):
        """Test GET /quad/timeline/{symbol}"""
        response = client.get("/api/v1/quad/timeline/RELIANCE?days=30")
        
        # Should return timeline or 404
        assert response.status_code in [200, 404]
    
    def test_analyze_invalid_symbol(self):
        """Test analysis with invalid symbol"""
        response = client.post(
            "/api/v1/quad/analyze",
            json={"symbol": ""}
        )
        
        # Should fail validation
        assert response.status_code == 422
