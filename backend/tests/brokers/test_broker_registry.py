"""
Unit Tests for Broker Registry
"""

import pytest
import json
from pathlib import Path
from app.brokers.broker_registry import BrokerRegistry, BrokerMetadata
from app.brokers.base_adapter import BrokerType
from app.brokers.zerodha_adapter import ZerodhaAdapter


class TestBrokerRegistry:
    """Test BrokerRegistry functionality"""
    
    @pytest.fixture
    def registry(self):
        """Create fresh registry for each test"""
        return BrokerRegistry()
    
    def test_initialization(self, registry):
        """Test registry initialization"""
        assert registry is not None
        assert isinstance(registry.metadata, dict)
        assert isinstance(registry.adapters, dict)
    
    def test_discover_brokers(self, registry):
        """Test broker discovery from plugin files"""
        discovered = registry.discover_brokers()
        
        # Should discover at least Zerodha, Angel One, Fyers, Dhan
        assert len(discovered) >= 4
        assert BrokerType.ZERODHA in discovered
        assert BrokerType.ANGELONE in discovered
        assert BrokerType.FYERS in discovered
        assert BrokerType.DHAN in discovered
    
    def test_broker_metadata(self, registry):
        """Test broker metadata loading"""
        registry.discover_brokers()
        
        zerodha_meta = registry.get_metadata(BrokerType.ZERODHA)
        assert zerodha_meta is not None
        assert zerodha_meta.broker_name == "zerodha"
        assert zerodha_meta.display_name == "Zerodha (Kite Connect)"
        assert zerodha_meta.enabled == True
    
    def test_register_adapter(self, registry):
        """Test adapter registration"""
        # Create mock adapter
        from tests.services.test_broker_gateway import MockBrokerAdapter
        adapter = MockBrokerAdapter(BrokerType.ZERODHA)
        
        registry.register_adapter(adapter)
        
        assert BrokerType.ZERODHA in registry.adapters
        assert registry.get_broker(BrokerType.ZERODHA) == adapter
    
    def test_get_enabled_brokers(self, registry):
        """Test getting enabled brokers"""
        registry.discover_brokers()
        
        enabled = registry.get_enabled_brokers()
        
        # All brokers should be enabled by default
        assert len(enabled) >= 4
        assert BrokerType.ZERODHA in enabled
    
    def test_is_broker_enabled(self, registry):
        """Test checking if broker is enabled"""
        registry.discover_brokers()
        
        assert registry.is_broker_enabled(BrokerType.ZERODHA) == True
    
    def test_supports_feature(self, registry):
        """Test feature support checking"""
        registry.discover_brokers()
        
        # Zerodha should support LTP
        assert registry.supports_feature(BrokerType.ZERODHA, "ltp") == True
        
        # Zerodha should support historical data
        assert registry.supports_feature(BrokerType.ZERODHA, "historical_data") == True
    
    def test_get_broker_info(self, registry):
        """Test getting broker information"""
        registry.discover_brokers()
        
        info = registry.get_broker_info()
        
        assert len(info) >= 4
        assert all("broker_type" in item for item in info)
        assert all("display_name" in item for item in info)
        assert all("enabled" in item for item in info)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
