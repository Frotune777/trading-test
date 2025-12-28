"""
Integration tests for Monitoring API Endpoints
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestMonitoringEndpoints:
    """Test suite for monitoring API endpoints"""
    
    def test_get_latency_stats(self):
        """Test GET /monitoring/latency/stats"""
        response = client.get("/api/v1/monitoring/latency/stats?hours=24")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "count" in data
        assert "avg" in data
        assert "p50" in data
        assert "p95" in data
        assert "p99" in data
    
    def test_get_traffic_stats(self):
        """Test GET /monitoring/traffic"""
        response = client.get("/api/v1/monitoring/traffic?hours=24")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_requests" in data
        assert "error_rate" in data
        assert "avg_response_time_ms" in data
    
    def test_get_endpoint_stats(self):
        """Test GET /monitoring/traffic/endpoints"""
        response = client.get("/api/v1/monitoring/traffic/endpoints?hours=24")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "endpoints" in data
        assert isinstance(data["endpoints"], list)
    
    def test_get_error_stats(self):
        """Test GET /monitoring/errors"""
        response = client.get("/api/v1/monitoring/errors?hours=24")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "total_errors" in data
        assert "error_types" in data
        assert "by_severity" in data
    
    def test_get_system_health(self):
        """Test GET /monitoring/health"""
        response = client.get("/api/v1/monitoring/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "components" in data
    
    def test_latency_stats_with_filters(self):
        """Test latency stats with metric_type filter"""
        response = client.get(
            "/api/v1/monitoring/latency/stats?metric_type=api_call&hours=1"
        )
        
        assert response.status_code == 200
    
    def test_invalid_hours_parameter(self):
        """Test that invalid hours parameter is rejected"""
        response = client.get("/api/v1/monitoring/traffic?hours=200")
        
        # Should fail validation (max 168 hours)
        assert response.status_code == 422
