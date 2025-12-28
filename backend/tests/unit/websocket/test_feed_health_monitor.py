"""
Unit tests for Feed Health Monitor
"""

import pytest
import asyncio
from datetime import datetime, timedelta
import pytz

from app.websocket.feed_health_monitor import FeedHealthMonitor, FeedStatus

IST = pytz.timezone('Asia/Kolkata')


class TestFeedHealthMonitor:
    """Test suite for FeedHealthMonitor"""
    
    def test_initialization(self):
        """Test monitor initialization"""
        monitor = FeedHealthMonitor(stale_threshold_seconds=5)
        assert monitor.stale_threshold == timedelta(seconds=5)
        assert monitor.global_status == FeedStatus.DISCONNECTED
    
    def test_record_message(self):
        """Test recording a message"""
        monitor = FeedHealthMonitor()
        
        monitor.record_message("NSE:RELIANCE")
        
        # Verify message was recorded
        assert "NSE:RELIANCE" in monitor.last_message_time
        assert monitor.feed_status["NSE:RELIANCE"] == FeedStatus.HEALTHY
        assert monitor.message_count["NSE:RELIANCE"] == 1
    
    def test_get_feed_status(self):
        """Test getting feed status"""
        monitor = FeedHealthMonitor()
        
        # Initially disconnected
        assert monitor.get_feed_status("NSE:RELIANCE") == FeedStatus.DISCONNECTED
        
        # After message, healthy
        monitor.record_message("NSE:RELIANCE")
        assert monitor.get_feed_status("NSE:RELIANCE") == FeedStatus.HEALTHY
    
    def test_get_time_since_last_message(self):
        """Test time since last message calculation"""
        monitor = FeedHealthMonitor()
        
        # No message yet
        assert monitor.get_time_since_last_message("NSE:RELIANCE") is None
        
        # After message
        monitor.record_message("NSE:RELIANCE")
        time_since = monitor.get_time_since_last_message("NSE:RELIANCE")
        
        assert time_since is not None
        assert time_since.total_seconds() < 1  # Very recent
    
    def test_is_feed_healthy(self):
        """Test feed health check"""
        monitor = FeedHealthMonitor()
        
        # Initially not healthy
        assert not monitor.is_feed_healthy("NSE:RELIANCE")
        
        # After message, healthy
        monitor.record_message("NSE:RELIANCE")
        assert monitor.is_feed_healthy("NSE:RELIANCE")
    
    def test_get_stats(self):
        """Test statistics generation"""
        monitor = FeedHealthMonitor()
        
        # Record messages for multiple symbols
        monitor.record_message("NSE:RELIANCE")
        monitor.record_message("NSE:TCS")
        monitor.record_message("NSE:RELIANCE")  # Second message
        
        stats = monitor.get_stats()
        
        assert stats["monitored_symbols"] == 2
        assert "NSE:RELIANCE" in stats["symbols"]
        assert "NSE:TCS" in stats["symbols"]
        assert stats["symbols"]["NSE:RELIANCE"]["message_count"] == 2
        assert stats["symbols"]["NSE:TCS"]["message_count"] == 1
    
    @pytest.mark.asyncio
    async def test_stale_feed_detection(self):
        """Test that stale feeds are detected"""
        monitor = FeedHealthMonitor(stale_threshold_seconds=1)
        
        # Record message
        monitor.record_message("NSE:RELIANCE")
        
        # Wait for feed to become stale
        await asyncio.sleep(1.5)
        
        # Manually trigger health check
        await monitor._check_feed_health()
        
        # Feed should now be stale
        assert monitor.get_feed_status("NSE:RELIANCE") == FeedStatus.STALE
    
    @pytest.mark.asyncio
    async def test_feed_recovery(self):
        """Test that feeds can recover from stale state"""
        monitor = FeedHealthMonitor(stale_threshold_seconds=1)
        
        # Record message
        monitor.record_message("NSE:RELIANCE")
        
        # Wait for stale
        await asyncio.sleep(1.5)
        await monitor._check_feed_health()
        assert monitor.get_feed_status("NSE:RELIANCE") == FeedStatus.STALE
        
        # New message should recover
        monitor.record_message("NSE:RELIANCE")
        assert monitor.get_feed_status("NSE:RELIANCE") == FeedStatus.HEALTHY
    
    def test_get_global_status(self):
        """Test global status calculation"""
        monitor = FeedHealthMonitor()
        
        # Initially disconnected
        assert monitor.get_global_status() == FeedStatus.DISCONNECTED
        
        # All healthy
        monitor.record_message("NSE:RELIANCE")
        monitor.record_message("NSE:TCS")
        assert monitor.get_global_status() == FeedStatus.HEALTHY
        
        # One stale = degraded
        monitor.feed_status["NSE:RELIANCE"] = FeedStatus.STALE
        assert monitor.get_global_status() == FeedStatus.DEGRADED
