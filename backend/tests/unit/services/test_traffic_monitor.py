"""
Unit tests for Traffic Monitor Service
"""

import pytest
from datetime import datetime, timedelta
import pytz

from app.services.traffic_monitor_service import TrafficMonitor
from app.database.models_monitoring import APITraffic, ErrorLog

IST = pytz.timezone('Asia/Kolkata')


class TestTrafficMonitor:
    """Test suite for TrafficMonitor"""
    
    @pytest.mark.asyncio
    async def test_record_request(self, db_session):
        """Test recording an API request"""
        monitor = TrafficMonitor(db_session)
        
        await monitor.record_request(
            endpoint="/api/v1/health",
            method="GET",
            status_code=200,
            response_time_ms=45.5,
            user_id=1,
            ip_address="127.0.0.1",
            user_agent="Mozilla/5.0"
        )
        
        # Verify
        traffic = db_session.query(APITraffic).all()
        assert len(traffic) == 1
        assert traffic[0].endpoint == "/api/v1/health"
        assert traffic[0].method == "GET"
        assert traffic[0].status_code == 200
        assert traffic[0].response_time_ms == 45.5
    
    @pytest.mark.asyncio
    async def test_record_error(self, db_session):
        """Test recording an error"""
        monitor = TrafficMonitor(db_session)
        
        await monitor.record_error(
            error_type="ValidationError",
            error_message="Invalid input",
            endpoint="/api/v1/orders",
            user_id=1,
            severity="ERROR"
        )
        
        # Verify
        errors = db_session.query(ErrorLog).all()
        assert len(errors) == 1
        assert errors[0].error_type == "ValidationError"
        assert errors[0].severity == "ERROR"
    
    def test_get_traffic_stats(self, db_session):
        """Test traffic statistics calculation"""
        monitor = TrafficMonitor(db_session)
        
        import asyncio
        
        # Record multiple requests
        for i in range(10):
            status = 500 if i < 2 else 200  # 2 errors
            asyncio.run(monitor.record_request(
                endpoint="/api/v1/test",
                method="GET",
                status_code=status,
                response_time_ms=50 + i * 10
            ))
        
        # Get stats
        stats = monitor.get_traffic_stats(hours=24)
        
        assert stats["total_requests"] == 10
        assert stats["error_requests"] == 2
        assert stats["error_rate"] == 20.0
    
    def test_get_endpoint_stats(self, db_session):
        """Test per-endpoint statistics"""
        monitor = TrafficMonitor(db_session)
        
        import asyncio
        
        # Record requests to different endpoints
        endpoints = ["/api/v1/health", "/api/v1/orders", "/api/v1/health"]
        for endpoint in endpoints:
            asyncio.run(monitor.record_request(
                endpoint=endpoint,
                method="GET",
                status_code=200,
                response_time_ms=50
            ))
        
        # Get endpoint stats
        stats = monitor.get_endpoint_stats(hours=24)
        
        # /api/v1/health should have 2 requests
        health_stats = [s for s in stats if s["endpoint"] == "/api/v1/health"]
        assert len(health_stats) == 1
        assert health_stats[0]["count"] == 2
    
    def test_get_error_stats(self, db_session):
        """Test error statistics"""
        monitor = TrafficMonitor(db_session)
        
        import asyncio
        
        # Record different types of errors
        error_types = ["ValidationError", "DatabaseError", "ValidationError"]
        for error_type in error_types:
            asyncio.run(monitor.record_error(
                error_type=error_type,
                error_message="Test error",
                severity="ERROR"
            ))
        
        # Get error stats
        stats = monitor.get_error_stats(hours=24)
        
        assert stats["total_errors"] == 3
        assert len(stats["error_types"]) == 2  # 2 unique types
        assert stats["by_severity"]["ERROR"] == 3
    
    def test_get_user_activity(self, db_session):
        """Test user activity tracking"""
        monitor = TrafficMonitor(db_session)
        
        import asyncio
        
        # Record requests from different users
        for user_id in [1, 2, 1, 1]:
            asyncio.run(monitor.record_request(
                endpoint="/api/v1/test",
                method="GET",
                status_code=200,
                response_time_ms=50,
                user_id=user_id
            ))
        
        # Get user activity
        activity = monitor.get_user_activity(hours=24, limit=10)
        
        # User 1 should have 3 requests
        user1_activity = [a for a in activity if a["user_id"] == 1]
        assert len(user1_activity) == 1
        assert user1_activity[0]["request_count"] == 3
