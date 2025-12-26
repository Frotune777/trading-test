"""
Unit Tests for BrokerGateway Service
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from app.services.broker_gateway import BrokerGateway, broker_gateway
from app.brokers.base_adapter import (
    BrokerAdapter,
    BrokerType,
    HealthStatus,
    BrokerHealth,
    Order,
    Position
)


class MockBrokerAdapter(BrokerAdapter):
    """Mock broker adapter for testing"""
    
    def __init__(self, broker_type: BrokerType, ltp_value: float = 1234.50):
        super().__init__(broker_type)
        self.ltp_value = ltp_value
        self._connected = True
    
    @property
    def broker_name(self) -> str:
        return f"Mock {self.broker_type.value}"
    
    async def connect(self) -> bool:
        self._connected = True
        return True
    
    async def disconnect(self) -> bool:
        self._connected = False
        return True
    
    async def get_ltp(self, symbol: str, exchange: str = "NSE") -> float:
        return self.ltp_value
    
    async def get_historical_data(self, symbol, interval, from_date, to_date, exchange="NSE"):
        return None
    
    async def get_positions(self):
        return []
    
    async def place_order(self, order: Order):
        return {"order_id": "TEST123", "status": "PLACED"}
    
    async def get_order_status(self, order_id: str):
        return {"order_id": order_id, "status": "COMPLETE"}
    
    async def get_health_status(self) -> BrokerHealth:
        return BrokerHealth(
            broker_name=self.broker_name,
            status=HealthStatus.HEALTHY,
            error_rate=0.0,
            message="OK"
        )


@pytest.fixture
def gateway():
    """Create a fresh BrokerGateway instance for each test"""
    return BrokerGateway()


@pytest.fixture
def mock_zerodha():
    """Create mock Zerodha adapter"""
    return MockBrokerAdapter(BrokerType.ZERODHA, ltp_value=1234.50)


@pytest.fixture
def mock_angelone():
    """Create mock Angel One adapter"""
    return MockBrokerAdapter(BrokerType.ANGELONE, ltp_value=1234.45)


@pytest.fixture
def mock_fyers():
    """Create mock Fyers adapter"""
    return MockBrokerAdapter(BrokerType.FYERS, ltp_value=1234.55)


class TestBrokerGateway:
    """Test BrokerGateway functionality"""
    
    def test_register_broker(self, gateway, mock_zerodha):
        """Test broker registration"""
        gateway.register_broker(mock_zerodha, is_primary=True)
        
        assert BrokerType.ZERODHA in gateway.brokers
        assert gateway.primary_broker == BrokerType.ZERODHA
    
    def test_register_multiple_brokers(self, gateway, mock_zerodha, mock_angelone):
        """Test registering multiple brokers"""
        gateway.register_broker(mock_zerodha, is_primary=True)
        gateway.register_broker(mock_angelone)
        
        assert len(gateway.brokers) == 2
        assert gateway.primary_broker == BrokerType.ZERODHA
    
    @pytest.mark.asyncio
    async def test_connect_all(self, gateway, mock_zerodha, mock_angelone):
        """Test connecting to all brokers"""
        gateway.register_broker(mock_zerodha)
        gateway.register_broker(mock_angelone)
        
        results = await gateway.connect_all()
        
        assert results[BrokerType.ZERODHA] == True
        assert results[BrokerType.ANGELONE] == True
    
    @pytest.mark.asyncio
    async def test_get_ltp_single_broker(self, gateway, mock_zerodha):
        """Test getting LTP from single broker"""
        gateway.register_broker(mock_zerodha, is_primary=True)
        
        ltp = await gateway.get_ltp("RELIANCE", "NSE")
        
        assert ltp == 1234.50
    
    @pytest.mark.asyncio
    async def test_get_ltp_from_all_brokers(self, gateway, mock_zerodha, mock_angelone, mock_fyers):
        """Test getting LTP from all brokers"""
        gateway.register_broker(mock_zerodha)
        gateway.register_broker(mock_angelone)
        gateway.register_broker(mock_fyers)
        
        ltp_map = await gateway.get_ltp_from_all_brokers("RELIANCE", "NSE")
        
        assert len(ltp_map) == 3
        assert ltp_map[BrokerType.ZERODHA] == 1234.50
        assert ltp_map[BrokerType.ANGELONE] == 1234.45
        assert ltp_map[BrokerType.FYERS] == 1234.55
    
    @pytest.mark.asyncio
    async def test_aggregate_ltp_consensus(self, gateway, mock_zerodha, mock_angelone, mock_fyers):
        """Test LTP aggregation and consensus calculation"""
        gateway.register_broker(mock_zerodha)
        gateway.register_broker(mock_angelone)
        gateway.register_broker(mock_fyers)
        
        result = await gateway.aggregate_ltp_from_brokers("RELIANCE", "NSE")
        
        # Median of [1234.50, 1234.45, 1234.55] = 1234.50
        assert result["consensus_ltp"] == 1234.50
        assert result["confidence"] == 1.0  # All 3 brokers responded
        assert len(result["broker_ltps"]) == 3
    
    @pytest.mark.asyncio
    async def test_aggregate_ltp_outlier_detection(self, gateway):
        """Test outlier detection in LTP aggregation"""
        # Create brokers with one outlier
        broker1 = MockBrokerAdapter(BrokerType.ZERODHA, ltp_value=1234.50)
        broker2 = MockBrokerAdapter(BrokerType.ANGELONE, ltp_value=1234.45)
        broker3 = MockBrokerAdapter(BrokerType.FYERS, ltp_value=1250.00)  # Outlier
        
        gateway.register_broker(broker1)
        gateway.register_broker(broker2)
        gateway.register_broker(broker3)
        
        result = await gateway.aggregate_ltp_from_brokers("RELIANCE", "NSE")
        
        # Should detect Fyers as outlier (>0.5% deviation)
        assert len(result["outliers"]) == 1
        assert result["outliers"][0]["broker"] == "fyers"
    
    @pytest.mark.asyncio
    async def test_failover_get_ltp(self, gateway):
        """Test failover when primary broker fails"""
        # Create failing primary broker
        failing_broker = MockBrokerAdapter(BrokerType.ZERODHA, ltp_value=None)
        failing_broker.get_ltp = AsyncMock(return_value=None)
        
        # Create working backup broker
        backup_broker = MockBrokerAdapter(BrokerType.ANGELONE, ltp_value=1234.50)
        
        gateway.register_broker(failing_broker, is_primary=True)
        gateway.register_broker(backup_broker)
        
        ltp = await gateway.get_ltp("RELIANCE", "NSE")
        
        # Should get LTP from backup broker
        assert ltp == 1234.50
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_activation(self, gateway):
        """Test circuit breaker activates after threshold failures"""
        failing_broker = MockBrokerAdapter(BrokerType.ZERODHA)
        failing_broker.get_ltp = AsyncMock(return_value=None)
        
        gateway.register_broker(failing_broker, is_primary=True)
        
        # Trigger failures to activate circuit breaker
        for _ in range(3):
            await gateway.get_ltp("RELIANCE", "NSE")
        
        assert gateway._circuit_breaker_active == True
        assert gateway._failure_counts[BrokerType.ZERODHA] >= 3
    
    @pytest.mark.asyncio
    async def test_reset_circuit_breaker(self, gateway, mock_zerodha):
        """Test circuit breaker reset"""
        gateway.register_broker(mock_zerodha)
        gateway._circuit_breaker_active = True
        gateway._failure_counts[BrokerType.ZERODHA] = 5
        
        await gateway.reset_circuit_breaker()
        
        assert gateway._circuit_breaker_active == False
        assert gateway._failure_counts[BrokerType.ZERODHA] == 0
    
    @pytest.mark.asyncio
    async def test_get_all_broker_health(self, gateway, mock_zerodha, mock_angelone):
        """Test getting health status from all brokers"""
        gateway.register_broker(mock_zerodha)
        gateway.register_broker(mock_angelone)
        
        health_map = await gateway.get_all_broker_health()
        
        assert len(health_map) == 2
        assert health_map[BrokerType.ZERODHA].status == HealthStatus.HEALTHY
        assert health_map[BrokerType.ANGELONE].status == HealthStatus.HEALTHY


@pytest.mark.asyncio
async def test_global_instance():
    """Test global broker_gateway instance"""
    assert broker_gateway is not None
    assert isinstance(broker_gateway, BrokerGateway)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
