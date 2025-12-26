"""
Unit Tests for Symbol Transformer
"""

import pytest
from app.services.symbol_transformer import SymbolTransformer, symbol_transformer
from app.brokers.base_adapter import BrokerType


class TestSymbolTransformer:
    """Test SymbolTransformer functionality"""
    
    @pytest.fixture
    def transformer(self):
        """Create fresh transformer for each test"""
        return SymbolTransformer()
    
    def test_zerodha_format(self, transformer):
        """Test Zerodha symbol format (just symbol name)"""
        result = transformer.to_broker_format("RELIANCE", "NSE", BrokerType.ZERODHA)
        assert result == "RELIANCE"
    
    def test_angelone_format(self, transformer):
        """Test Angel One symbol format (SYMBOL-EQ)"""
        result = transformer.to_broker_format("RELIANCE", "NSE", BrokerType.ANGELONE)
        assert result == "RELIANCE-EQ"
    
    def test_fyers_format(self, transformer):
        """Test Fyers symbol format (EXCHANGE:SYMBOL-EQ)"""
        result = transformer.to_broker_format("RELIANCE", "NSE", BrokerType.FYERS)
        assert result == "NSE:RELIANCE-EQ"
    
    def test_dhan_format(self, transformer):
        """Test Dhan symbol format (returns symbol as-is, needs security_id lookup)"""
        result = transformer.to_broker_format("RELIANCE", "NSE", BrokerType.DHAN)
        assert result == "RELIANCE"
    
    def test_from_zerodha_format(self, transformer):
        """Test reverse transformation from Zerodha"""
        result = transformer.from_broker_format("RELIANCE", "NSE", BrokerType.ZERODHA)
        assert result == "RELIANCE"
    
    def test_from_angelone_format(self, transformer):
        """Test reverse transformation from Angel One"""
        result = transformer.from_broker_format("RELIANCE-EQ", "NSE", BrokerType.ANGELONE)
        assert result == "RELIANCE"
    
    def test_from_fyers_format(self, transformer):
        """Test reverse transformation from Fyers"""
        result = transformer.from_broker_format("NSE:RELIANCE-EQ", "NSE", BrokerType.FYERS)
        assert result == "RELIANCE"
    
    def test_get_standard_format(self, transformer):
        """Test standard format generation"""
        result = transformer.get_standard_format("RELIANCE", "NSE")
        assert result == "NSE:RELIANCE"
    
    def test_caching(self, transformer):
        """Test symbol transformation caching"""
        # First call
        result1 = transformer.to_broker_format("RELIANCE", "NSE", BrokerType.FYERS)
        
        # Second call should use cache
        result2 = transformer.to_broker_format("RELIANCE", "NSE", BrokerType.FYERS)
        
        assert result1 == result2
        assert "fyers:NSE:RELIANCE" in transformer._symbol_cache
    
    def test_clear_cache(self, transformer):
        """Test cache clearing"""
        transformer.to_broker_format("RELIANCE", "NSE", BrokerType.FYERS)
        assert len(transformer._symbol_cache) > 0
        
        transformer.clear_cache()
        assert len(transformer._symbol_cache) == 0
    
    def test_global_instance(self):
        """Test global symbol_transformer instance"""
        assert symbol_transformer is not None
        assert isinstance(symbol_transformer, SymbolTransformer)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
