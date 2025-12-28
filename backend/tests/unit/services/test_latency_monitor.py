"""
Unit tests for Latency Monitor Service
"""

import pytest
import time
from datetime import datetime, timedelta
import pytz

from app.services.latency_monitor_service import LatencyMonitor, track_latency
from app.database.models_monitoring import LatencyMetric

IST = pytz.timezone('Asia/Kolkata')


class TestLatencyMonitor:
    """Test suite for LatencyMonitor"""
    
    def test_record_latency(self, db_session):
        """Test recording a latency metric"""
        monitor = LatencyMonitor(db_session)
        
        # Record metric
        monitor.record(
            metric_type="api_call",
            operation="GET /api/v1/health",
            latency_ms=150.5,
            user_id=1
        )
        
        # Verify
        metrics = db_session.query(LatencyMetric).all()
        assert len(metrics) == 1
        assert metrics[0].metric_type == "api_call"
        assert metrics[0].operation == "GET /api/v1/health"
        assert metrics[0].latency_ms == 150.5
        assert metrics[0].user_id == 1
    
    def test_get_metrics(self, db_session):
        """Test retrieving metrics"""
        monitor = LatencyMonitor(db_session)
        
        # Record multiple metrics
        for i in range(5):
            monitor.record(
                metric_type="api_call",
                operation=f"operation_{i}",
                latency_ms=100 + i * 10
            )
        
        # Get all metrics
        metrics = monitor.get_metrics()
        assert len(metrics) == 5
        
        # Filter by operation
        metrics = monitor.get_metrics(operation="operation_2")
        assert len(metrics) == 1
        assert metrics[0].latency_ms == 120
    
    def test_get_stats(self, db_session):
        """Test latency statistics calculation"""
        monitor = LatencyMonitor(db_session)
        
        # Record metrics with known values
        latencies = [100, 150, 200, 250, 300]
        for lat in latencies:
            monitor.record(
                metric_type="api_call",
                operation="test_op",
                latency_ms=lat
            )
        
        # Get stats
        stats = monitor.get_stats(operation="test_op")
        
        assert stats["count"] == 5
        assert stats["avg"] == 200  # (100+150+200+250+300)/5
        assert stats["min"] == 100
        assert stats["max"] == 300
        assert stats["p50"] == 200  # Median
    
    def test_track_latency_context_manager(self, db_session):
        """Test latency tracking context manager"""
        
        async def test_operation():
            async with track_latency("test", "sleep_operation", db_session):
                time.sleep(0.1)  # 100ms
        
        # Run operation
        import asyncio
        asyncio.run(test_operation())
        
        # Verify metric was recorded
        metrics = db_session.query(LatencyMetric).filter(
            LatencyMetric.operation == "sleep_operation"
        ).all()
        
        assert len(metrics) == 1
        assert metrics[0].latency_ms >= 100  # At least 100ms
    
    def test_high_latency_warning(self, db_session, caplog):
        """Test that high latency triggers warning"""
        monitor = LatencyMonitor(db_session)
        
        # Record high latency
        monitor.record(
            metric_type="api_call",
            operation="slow_operation",
            latency_ms=1500  # > 1000ms threshold
        )
        
        # Check warning was logged
        assert "High latency detected" in caplog.text
