"""
Tests for Feature Engineering (Sentiment & Feature Store)
"""

import pytest
from unittest.mock import AsyncMock

from app.services.feature_engineering import SentimentAnalyzer, FeatureStore


class TestSentimentAnalyzer:
    """Test Sentiment Analyzer"""
    
    @pytest.mark.asyncio
    async def test_get_sentiment(self):
        """Test sentiment retrieval"""
        analyzer = SentimentAnalyzer()
        
        sentiment = await analyzer.get_sentiment(
            symbol="RELIANCE",
            sources=['news', 'twitter'],
            lookback_days=7
        )
        
        assert 'symbol' in sentiment
        assert sentiment['symbol'] == "RELIANCE"
        assert 'score' in sentiment
        assert -1 <= sentiment['score'] <= 1
        assert 'confidence' in sentiment
        assert 0 <= sentiment['confidence'] <= 1
        assert 'sources' in sentiment
    
    @pytest.mark.asyncio
    async def test_analyze_text_sentiment(self):
        """Test text sentiment analysis"""
        analyzer = SentimentAnalyzer()
        
        # Positive text
        positive_result = await analyzer.analyze_text_sentiment(
            "This stock is very bullish and positive"
        )
        assert positive_result['score'] > 0
        
        # Negative text
        negative_result = await analyzer.analyze_text_sentiment(
            "This stock is bearish and negative"
        )
        assert negative_result['score'] < 0


class TestFeatureStore:
    """Test Feature Store"""
    
    @pytest.mark.asyncio
    async def test_store_and_retrieve_features(self):
        """Test feature storage and retrieval"""
        store = FeatureStore()
        
        # Store features
        features = {
            'sma_20': 2500.0,
            'rsi': 65.0,
            'sentiment': 0.65
        }
        
        success = await store.store_features(
            symbol="RELIANCE",
            features=features,
            feature_set='test_set',
            version='v1'
        )
        
        assert success == True
        
        # Retrieve features
        retrieved = await store.get_features(
            symbol="RELIANCE",
            feature_set='test_set',
            version='v1'
        )
        
        assert retrieved is not None
        assert retrieved['sma_20'] == 2500.0
        assert retrieved['rsi'] == 65.0
        assert retrieved['sentiment'] == 0.65
    
    @pytest.mark.asyncio
    async def test_feature_not_found(self):
        """Test retrieval of non-existent features"""
        store = FeatureStore()
        
        retrieved = await store.get_features(
            symbol="NONEXISTENT",
            feature_set='test_set',
            version='v1'
        )
        
        assert retrieved is None
    
    @pytest.mark.asyncio
    async def test_register_feature_set(self):
        """Test feature set registration"""
        store = FeatureStore()
        
        success = await store.register_feature_set(
            feature_set='quad_features',
            features=['sma_20', 'rsi', 'macd', 'sentiment'],
            description='QUAD trading features'
        )
        
        assert success == True
        
        # Get metadata
        metadata = await store.get_feature_metadata('quad_features')
        assert metadata is not None
        assert len(metadata['features']) == 4
        assert 'sma_20' in metadata['features']
    
    @pytest.mark.asyncio
    async def test_list_feature_sets(self):
        """Test listing feature sets"""
        store = FeatureStore()
        
        # Register multiple sets
        await store.register_feature_set('set1', ['f1', 'f2'], 'Set 1')
        await store.register_feature_set('set2', ['f3', 'f4'], 'Set 2')
        
        feature_sets = await store.list_feature_sets()
        
        assert 'set1' in feature_sets
        assert 'set2' in feature_sets


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
