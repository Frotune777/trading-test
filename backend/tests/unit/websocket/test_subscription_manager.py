"""
Unit tests for WebSocket Subscription Manager
"""

import pytest
from unittest.mock import Mock

from app.websocket.subscription_manager import SubscriptionManager


class TestSubscriptionManager:
    """Test suite for SubscriptionManager"""
    
    def test_add_subscription(self):
        """Test adding a subscription"""
        manager = SubscriptionManager()
        client = Mock()
        
        manager.add_subscription("NSE:RELIANCE", "ltp", client)
        
        # Verify subscription was added
        subscribers = manager.get_subscribers("NSE:RELIANCE", "ltp")
        assert client in subscribers
    
    def test_remove_subscription(self):
        """Test removing a subscription"""
        manager = SubscriptionManager()
        client = Mock()
        
        # Add then remove
        manager.add_subscription("NSE:RELIANCE", "ltp", client)
        manager.remove_subscription("NSE:RELIANCE", client)
        
        # Verify subscription was removed
        subscribers = manager.get_subscribers("NSE:RELIANCE", "ltp")
        assert client not in subscribers
    
    def test_remove_all_subscriptions(self):
        """Test removing all subscriptions for a client"""
        manager = SubscriptionManager()
        client = Mock()
        
        # Add multiple subscriptions
        manager.add_subscription("NSE:RELIANCE", "ltp", client)
        manager.add_subscription("NSE:TCS", "ltp", client)
        
        # Remove all
        manager.remove_all_subscriptions(client)
        
        # Verify all removed
        assert len(manager.get_subscribers("NSE:RELIANCE", "ltp")) == 0
        assert len(manager.get_subscribers("NSE:TCS", "ltp")) == 0
    
    def test_get_subscribers_o1_lookup(self):
        """Test O(1) subscriber lookup"""
        manager = SubscriptionManager()
        client1 = Mock()
        client2 = Mock()
        
        # Add subscriptions
        manager.add_subscription("NSE:RELIANCE", "ltp", client1)
        manager.add_subscription("NSE:RELIANCE", "ltp", client2)
        manager.add_subscription("NSE:TCS", "ltp", client1)
        
        # Get subscribers for RELIANCE
        subscribers = manager.get_subscribers("NSE:RELIANCE", "ltp")
        assert len(subscribers) == 2
        assert client1 in subscribers
        assert client2 in subscribers
    
    def test_get_subscription_count(self):
        """Test subscription count"""
        manager = SubscriptionManager()
        client1 = Mock()
        client2 = Mock()
        
        # Add subscriptions
        manager.add_subscription("NSE:RELIANCE", "ltp", client1)
        manager.add_subscription("NSE:RELIANCE", "quote", client2)
        
        # Get count
        count = manager.get_subscription_count("NSE:RELIANCE")
        assert count == 2
    
    def test_get_all_subscribed_symbols(self):
        """Test getting all subscribed symbols"""
        manager = SubscriptionManager()
        client = Mock()
        
        # Add subscriptions
        manager.add_subscription("NSE:RELIANCE", "ltp", client)
        manager.add_subscription("NSE:TCS", "ltp", client)
        
        # Get all symbols
        symbols = manager.get_all_subscribed_symbols()
        assert "NSE:RELIANCE" in symbols
        assert "NSE:TCS" in symbols
    
    def test_get_client_subscriptions(self):
        """Test getting subscriptions for a specific client"""
        manager = SubscriptionManager()
        client = Mock()
        
        # Add subscriptions
        manager.add_subscription("NSE:RELIANCE", "ltp", client)
        manager.add_subscription("NSE:TCS", "quote", client)
        
        # Get client subscriptions
        subs = manager.get_client_subscriptions(client)
        assert len(subs) == 2
        assert ("NSE:RELIANCE", "ltp") in subs
        assert ("NSE:TCS", "quote") in subs
    
    def test_get_stats(self):
        """Test subscription statistics"""
        manager = SubscriptionManager()
        client1 = Mock()
        client2 = Mock()
        
        # Add subscriptions
        manager.add_subscription("NSE:RELIANCE", "ltp", client1)
        manager.add_subscription("NSE:RELIANCE", "ltp", client2)
        manager.add_subscription("NSE:TCS", "ltp", client1)
        
        # Get stats
        stats = manager.get_stats()
        
        assert stats["total_symbols"] == 2
        assert stats["total_clients"] == 2
        assert stats["total_subscriptions"] == 3
        assert stats["symbols"]["NSE:RELIANCE"] == 2
        assert stats["symbols"]["NSE:TCS"] == 1
