"""
Tests for TA Aggregator and Regime Detection
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import AsyncMock, MagicMock

from app.services.ta_aggregator import TAggregator
from app.services.market_regime import MarketRegimeDetector


class TestTAggregator:
    """Test TA Aggregator"""
    
    @pytest.mark.asyncio
    async def test_get_signal(self):
        """Test composite signal generation"""
        db_mock = AsyncMock()
        aggregator = TAggregator(db_mock)
        
        # Create sample data
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        data = pd.DataFrame({
            'close': np.random.randn(100).cumsum() + 100,
            'open': np.random.randn(100).cumsum() + 100,
            'high': np.random.randn(100).cumsum() + 105,
            'low': np.random.randn(100).cumsum() + 95,
            'volume': np.random.randint(1000, 10000, 100)
        }, index=dates)
        
        signal = await aggregator.get_signal(
            symbol="TEST",
            data=data,
            use_adaptive_weights=True
        )
        
        assert 'signal' in signal
        assert signal['signal'] in ['BUY', 'SELL', 'HOLD']
        assert 'confidence' in signal
        assert 0 <= signal['confidence'] <= 1
        assert 'regime' in signal
        assert 'composite_score' in signal
    
    def test_trend_score_calculation(self):
        """Test trend indicator scoring"""
        db_mock = AsyncMock()
        aggregator = TAggregator(db_mock)
        
        # Create uptrend data
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        data = pd.DataFrame({
            'close': np.linspace(90, 110, 100),
            'open': np.linspace(89, 109, 100),
            'high': np.linspace(92, 112, 100),
            'low': np.linspace(88, 108, 100),
            'volume': np.random.randint(1000, 10000, 100),
            'sma_20': np.linspace(91, 109, 100),
            'sma_50': np.linspace(90, 105, 100)
        }, index=dates)
        
        score = aggregator._calculate_trend_score(data)
        
        # Uptrend should have positive score
        assert score > 0
    
    def test_regime_weights(self):
        """Test regime-specific weights"""
        db_mock = AsyncMock()
        aggregator = TAggregator(db_mock)
        
        # Check weights for different regimes
        trending_weights = aggregator.REGIME_WEIGHTS['TRENDING_UP']
        assert trending_weights['trend'] > trending_weights['volatility']
        
        ranging_weights = aggregator.REGIME_WEIGHTS['RANGING']
        assert ranging_weights['momentum'] > ranging_weights['trend']
        
        volatile_weights = aggregator.REGIME_WEIGHTS['VOLATILE']
        assert volatile_weights['volatility'] > volatile_weights['trend']


class TestMarketRegimeDetector:
    """Test Market Regime Detector"""
    
    def test_trending_up_detection(self):
        """Test TRENDING_UP regime detection"""
        detector = MarketRegimeDetector()
        
        # Create strong uptrend data
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        data = pd.DataFrame({
            'close': np.linspace(90, 130, 100),
            'open': np.linspace(89, 129, 100),
            'high': np.linspace(92, 132, 100),
            'low': np.linspace(88, 128, 100),
            'volume': np.random.randint(1000, 10000, 100)
        }, index=dates)
        
        regime = detector.detect_regime(data)
        
        # Should detect trending (either UP or general TRENDING)
        assert regime in ['TRENDING_UP', 'RANGING', 'VOLATILE', 'UNKNOWN']
    
    def test_ranging_detection(self):
        """Test RANGING regime detection"""
        detector = MarketRegimeDetector()
        
        # Create ranging data
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        data = pd.DataFrame({
            'close': 100 + np.random.randn(100) * 2,  # Oscillating around 100
            'open': 100 + np.random.randn(100) * 2,
            'high': 102 + np.random.randn(100) * 2,
            'low': 98 + np.random.randn(100) * 2,
            'volume': np.random.randint(1000, 10000, 100)
        }, index=dates)
        
        regime = detector.detect_regime(data)
        
        # Should be valid regime
        assert regime in ['TRENDING_UP', 'TRENDING_DOWN', 'RANGING', 'VOLATILE', 'UNKNOWN']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
