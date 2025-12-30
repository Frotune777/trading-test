"""
Tests for ML Auto-Tuner and Model Promotion
"""

import pytest
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

from app.services.ml_autotuner import MLAutoTuner
from app.services.model_promoter import ModelPromoter


class TestMLAutoTuner:
    """Test ML Auto-Tuner"""
    
    @pytest.mark.asyncio
    async def test_optimize_classifier(self):
        """Test classifier optimization"""
        db_mock = AsyncMock()
        tuner = MLAutoTuner(db_mock)
        
        # Create sample data
        X_train = np.random.randn(100, 5)
        y_train = np.random.randint(0, 2, 100)
        
        result = await tuner.optimize_classifier(
            X_train, y_train,
            model_type='random_forest',
            n_trials=5,  # Small number for testing
            cv_folds=3
        )
        
        assert 'best_params' in result
        assert 'best_score' in result
        assert result['model_type'] == 'random_forest'
        assert result['n_trials'] == 5
    
    @pytest.mark.asyncio
    async def test_optimize_regressor(self):
        """Test regressor optimization"""
        db_mock = AsyncMock()
        tuner = MLAutoTuner(db_mock)
        
        # Create sample data
        X_train = np.random.randn(100, 5)
        y_train = np.random.randn(100)
        
        result = await tuner.optimize_regressor(
            X_train, y_train,
            model_type='random_forest',
            n_trials=5,
            cv_folds=3
        )
        
        assert 'best_params' in result
        assert 'best_score' in result
        assert result['model_type'] == 'random_forest'
    
    def test_parameter_search_space(self):
        """Test hyperparameter search space"""
        db_mock = AsyncMock()
        tuner = MLAutoTuner(db_mock)
        
        # Mock trial
        trial_mock = MagicMock()
        trial_mock.suggest_int = MagicMock(return_value=100)
        trial_mock.suggest_categorical = MagicMock(return_value='sqrt')
        
        params = tuner._get_classifier_params(trial_mock, 'random_forest')
        
        assert 'n_estimators' in params
        assert 'max_depth' in params
        assert 'max_features' in params


class TestModelPromoter:
    """Test Model Promotion Pipeline"""
    
    @pytest.mark.asyncio
    async def test_evaluate_classifier(self):
        """Test classifier evaluation"""
        db_mock = AsyncMock()
        promoter = ModelPromoter(db_mock)
        
        # Train simple model
        X_train = np.random.randn(100, 5)
        y_train = np.random.randint(0, 2, 100)
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X_train, y_train)
        
        # Evaluate
        X_val = np.random.randn(50, 5)
        y_val = np.random.randint(0, 2, 50)
        
        metrics = await promoter.evaluate_model(
            model, X_val, y_val,
            task_type='classification'
        )
        
        assert 'accuracy' in metrics
        assert 'precision' in metrics
        assert 'recall' in metrics
        assert 'f1' in metrics
        assert 0 <= metrics['accuracy'] <= 1
    
    @pytest.mark.asyncio
    async def test_evaluate_regressor(self):
        """Test regressor evaluation"""
        db_mock = AsyncMock()
        promoter = ModelPromoter(db_mock)
        
        # Train simple model
        X_train = np.random.randn(100, 5)
        y_train = np.random.randn(100)
        model = RandomForestRegressor(n_estimators=10, random_state=42)
        model.fit(X_train, y_train)
        
        # Evaluate
        X_val = np.random.randn(50, 5)
        y_val = np.random.randn(50)
        
        metrics = await promoter.evaluate_model(
            model, X_val, y_val,
            task_type='regression'
        )
        
        assert 'r2' in metrics
        assert 'mae' in metrics
        assert 'rmse' in metrics
    
    @pytest.mark.asyncio
    async def test_promote_model_success(self):
        """Test successful model promotion"""
        db_mock = AsyncMock()
        promoter = ModelPromoter(db_mock)
        
        # Create model
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        X = np.random.randn(100, 5)
        y = np.random.randint(0, 2, 100)
        model.fit(X, y)
        
        # Promote with high accuracy
        metrics = {'accuracy': 0.85}
        result = await promoter.promote_model(
            model,
            model_name='test_model',
            metrics=metrics,
            min_accuracy=0.70
        )
        
        assert result['promoted'] == True
        assert result['shadow_mode'] == True  # CRITICAL
        assert 'model_path' in result
    
    @pytest.mark.asyncio
    async def test_promote_model_failure(self):
        """Test failed model promotion (below threshold)"""
        db_mock = AsyncMock()
        promoter = ModelPromoter(db_mock)
        
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        
        # Promote with low accuracy
        metrics = {'accuracy': 0.60}
        result = await promoter.promote_model(
            model,
            model_name='test_model',
            metrics=metrics,
            min_accuracy=0.70,
            force=False
        )
        
        assert result['promoted'] == False
        assert 'reason' in result
    
    @pytest.mark.asyncio
    async def test_compare_models(self):
        """Test A/B model comparison"""
        db_mock = AsyncMock()
        promoter = ModelPromoter(db_mock)
        
        # Create two models
        model_a = RandomForestClassifier(n_estimators=10, random_state=42)
        model_b = RandomForestClassifier(n_estimators=20, random_state=42)
        
        X_train = np.random.randn(100, 5)
        y_train = np.random.randint(0, 2, 100)
        model_a.fit(X_train, y_train)
        model_b.fit(X_train, y_train)
        
        X_val = np.random.randn(50, 5)
        y_val = np.random.randint(0, 2, 50)
        
        comparison = await promoter.compare_models(
            model_a, model_b,
            X_val, y_val,
            task_type='classification'
        )
        
        assert 'model_a_metrics' in comparison
        assert 'model_b_metrics' in comparison
        assert 'winner' in comparison
        assert comparison['winner'] in ['model_a', 'model_b']


class TestShadowModeCompliance:
    """Test shadow mode compliance"""
    
    @pytest.mark.asyncio
    async def test_promoted_model_shadow_mode(self):
        """Verify all promoted models have shadow_mode=True"""
        db_mock = AsyncMock()
        promoter = ModelPromoter(db_mock)
        
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        X = np.random.randn(100, 5)
        y = np.random.randint(0, 2, 100)
        model.fit(X, y)
        
        metrics = {'accuracy': 0.85}
        result = await promoter.promote_model(
            model,
            model_name='shadow_test',
            metrics=metrics,
            force=True
        )
        
        # CRITICAL: Must be in shadow mode
        assert result.get('shadow_mode') == True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
