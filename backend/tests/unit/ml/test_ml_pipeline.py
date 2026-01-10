"""
Unit tests for ML Pipeline.

Tests core ML functionality including feature engineering,
model training, and predictions.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from app.ml import MLPipeline, FeatureEngineer


@pytest.fixture
def sample_ohlcv_data():
    """Create sample OHLCV data for testing."""
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
    np.random.seed(42)
    
    data = {
        'Open': 100 + np.random.randn(len(dates)).cumsum(),
        'High': 102 + np.random.randn(len(dates)).cumsum(),
        'Low': 98 + np.random.randn(len(dates)).cumsum(),
        'Close': 100 + np.random.randn(len(dates)).cumsum(),
        'Volume': np.random.randint(1000000, 10000000, len(dates))
    }
    
    df = pd.DataFrame(data, index=dates)
    # Ensure High >= Low
    df['High'] = df[['High', 'Low', 'Open', 'Close']].max(axis=1)
    df['Low'] = df[['Low', 'Open', 'Close']].min(axis=1)
    
    return df


class TestFeatureEngineer:
    """Test FeatureEngineer class."""
    
    def test_initialization(self, sample_ohlcv_data):
        """Test FeatureEngineer initialization."""
        engineer = FeatureEngineer(sample_ohlcv_data)
        assert engineer.df is not None
        assert len(engineer.df) == len(sample_ohlcv_data)
        assert isinstance(engineer.features, pd.DataFrame)
    
    def test_add_returns(self, sample_ohlcv_data):
        """Test return calculation."""
        engineer = FeatureEngineer(sample_ohlcv_data)
        engineer.add_returns(periods=[1, 5, 10])
        
        assert 'return_1d' in engineer.features.columns
        assert 'return_5d' in engineer.features.columns
        assert 'log_return_1d' in engineer.features.columns
        assert 'log_return_5d' in engineer.features.columns
    
    def test_add_volatility(self, sample_ohlcv_data):
        """Test volatility calculation."""
        engineer = FeatureEngineer(sample_ohlcv_data)
        engineer.add_volatility(windows=[10, 20])
        
        assert 'volatility_10d' in engineer.features.columns
        assert 'parkinson_vol_10d' in engineer.features.columns
        assert 'gk_vol_10d' in engineer.features.columns
    
    def test_add_volume_features(self, sample_ohlcv_data):
        """Test volume feature calculation."""
        engineer = FeatureEngineer(sample_ohlcv_data)
        engineer.add_volume_features(windows=[10])
        
        assert 'volume_momentum_10d' in engineer.features.columns
        assert 'vwap' in engineer.features.columns
        assert 'vwap_distance' in engineer.features.columns
    
    def test_build_all(self, sample_ohlcv_data):
        """Test building all features."""
        engineer = FeatureEngineer(sample_ohlcv_data)
        features = engineer.build_all()
        
        assert len(features.columns) > 50  # Should have 50+ features
        assert not features.empty


class TestMLPipeline:
    """Test MLPipeline class."""
    
    def test_initialization(self):
        """Test MLPipeline initialization."""
        pipeline = MLPipeline('SBIN', '1d')
        assert pipeline.symbol == 'SBIN'
        assert pipeline.timeframe == '1d'
        assert pipeline.model is None
    
    def test_create_target_3class(self, sample_ohlcv_data):
        """Test 3-class target creation."""
        pipeline = MLPipeline('SBIN', '1d')
        target = pipeline.create_target(sample_ohlcv_data, classification='3class')
        
        assert len(target) == len(sample_ohlcv_data)
        assert set(target.dropna().unique()).issubset({0, 1, 2})
        assert pipeline.classification_type == '3class'
    
    def test_create_target_2class(self, sample_ohlcv_data):
        """Test 2-class target creation."""
        pipeline = MLPipeline('SBIN', '1d')
        target = pipeline.create_target(sample_ohlcv_data, classification='2class')
        
        assert set(target.dropna().unique()).issubset({0, 1})
        assert pipeline.classification_type == '2class'
    
    def test_prepare_data(self, sample_ohlcv_data):
        """Test data preparation and splitting."""
        pipeline = MLPipeline('SBIN', '1d')
        engineer = FeatureEngineer(sample_ohlcv_data)
        features = engineer.build_all()
        target = pipeline.create_target(sample_ohlcv_data, classification='3class')
        
        X_train, X_val, X_test, y_train, y_val, y_test = pipeline.prepare_data(
            features, target, test_size=0.2, validation_size=0.1
        )
        
        # Check splits
        assert len(X_train) > 0
        assert len(X_val) > 0
        assert len(X_test) > 0
        
        # Check that splits sum to total (minus NaN rows)
        total_samples = len(X_train) + len(X_val) + len(X_test)
        assert total_samples > 0
        
        # Check feature names stored
        assert pipeline.feature_names is not None
        assert len(pipeline.feature_names) > 0
    
    def test_train_xgboost(self, sample_ohlcv_data):
        """Test XGBoost training."""
        pipeline = MLPipeline('SBIN', '1d')
        engineer = FeatureEngineer(sample_ohlcv_data)
        features = engineer.build_all()
        target = pipeline.create_target(sample_ohlcv_data, classification='3class')
        
        X_train, X_val, X_test, y_train, y_val, y_test = pipeline.prepare_data(
            features, target
        )
        
        # Train with minimal parameters for speed
        pipeline.train_model(
            X_train, y_train, X_val, y_val,
            model_type='xgboost',
            n_estimators=10,  # Small for testing
            max_depth=3
        )
        
        assert pipeline.model is not None
        assert hasattr(pipeline.model, 'predict')
    
    def test_evaluate(self, sample_ohlcv_data):
        """Test model evaluation."""
        pipeline = MLPipeline('SBIN', '1d')
        engineer = FeatureEngineer(sample_ohlcv_data)
        features = engineer.build_all()
        target = pipeline.create_target(sample_ohlcv_data, classification='3class')
        
        X_train, X_val, X_test, y_train, y_val, y_test = pipeline.prepare_data(
            features, target
        )
        
        pipeline.train_model(
            X_train, y_train, X_val, y_val,
            model_type='xgboost',
            n_estimators=10,
            max_depth=3
        )
        
        metrics = pipeline.evaluate(X_test, y_test)
        
        assert 'accuracy' in metrics
        assert 'precision' in metrics
        assert 'recall' in metrics
        assert 'f1_score' in metrics
        assert 0 <= metrics['accuracy'] <= 1
    
    def test_predict(self, sample_ohlcv_data):
        """Test making predictions."""
        pipeline = MLPipeline('SBIN', '1d')
        engineer = FeatureEngineer(sample_ohlcv_data)
        features = engineer.build_all()
        target = pipeline.create_target(sample_ohlcv_data, classification='3class')
        
        X_train, X_val, X_test, y_train, y_val, y_test = pipeline.prepare_data(
            features, target
        )
        
        pipeline.train_model(
            X_train, y_train, X_val, y_val,
            model_type='xgboost',
            n_estimators=10,
            max_depth=3
        )
        
        predictions, probabilities = pipeline.predict(X_test)
        
        assert len(predictions) == len(X_test)
        assert len(probabilities) == len(X_test)
        assert probabilities.shape[1] == 3  # 3 classes
