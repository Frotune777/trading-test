"""
ML Auto-Tuner
Automated hyperparameter optimization using Optuna
"""

import logging
import optuna
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import numpy as np
import pandas as pd
from sklearn.model_selection import cross_val_score, TimeSeriesSplit
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, mean_squared_error, r2_score
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Suppress Optuna logs
optuna.logging.set_verbosity(optuna.logging.WARNING)


class MLAutoTuner:
    """
    Automated ML hyperparameter tuning using Optuna.
    
    Features:
    - Bayesian optimization for hyperparameter search
    - Cross-validation for robust evaluation
    - Support for multiple model types
    - Automated best model selection
    
    Compliance:
    - All models remain in shadow mode (Rule #42-45)
    - No autonomous execution
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.study: Optional[optuna.Study] = None
    
    async def optimize_classifier(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        model_type: str = 'random_forest',
        n_trials: int = 50,
        cv_folds: int = 5
    ) -> Dict[str, Any]:
        """
        Optimize classification model hyperparameters.
        
        Args:
            X_train: Training features
            y_train: Training labels
            model_type: Model type (random_forest, xgboost, lightgbm)
            n_trials: Number of optimization trials
            cv_folds: Cross-validation folds
            
        Returns:
            Best parameters and metrics
        """
        try:
            logger.info(f"🔍 Starting hyperparameter optimization for {model_type}")
            
            # Create objective function
            def objective(trial: optuna.Trial) -> float:
                params = self._get_classifier_params(trial, model_type)
                
                # Create model
                if model_type == 'random_forest':
                    model = RandomForestClassifier(**params, random_state=42)
                else:
                    logger.warning(f"Model type {model_type} not implemented, using RandomForest")
                    model = RandomForestClassifier(**params, random_state=42)
                
                # Cross-validation
                cv = TimeSeriesSplit(n_splits=cv_folds)
                scores = cross_val_score(model, X_train, y_train, cv=cv, scoring='accuracy')
                
                return scores.mean()
            
            # Create study
            self.study = optuna.create_study(
                direction='maximize',
                study_name=f'{model_type}_optimization'
            )
            
            # Optimize
            self.study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
            
            # Get best results
            best_params = self.study.best_params
            best_score = self.study.best_value
            
            logger.info(f"✅ Optimization complete: Best accuracy = {best_score:.4f}")
            
            return {
                'model_type': model_type,
                'best_params': best_params,
                'best_score': best_score,
                'n_trials': n_trials,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error during optimization: {e}")
            return {'error': str(e)}
    
    async def optimize_regressor(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        model_type: str = 'random_forest',
        n_trials: int = 50,
        cv_folds: int = 5
    ) -> Dict[str, Any]:
        """
        Optimize regression model hyperparameters.
        
        Args:
            X_train: Training features
            y_train: Training targets
            model_type: Model type
            n_trials: Number of trials
            cv_folds: CV folds
            
        Returns:
            Best parameters and metrics
        """
        try:
            logger.info(f"🔍 Starting hyperparameter optimization for {model_type} (regression)")
            
            def objective(trial: optuna.Trial) -> float:
                params = self._get_regressor_params(trial, model_type)
                
                if model_type == 'random_forest':
                    model = RandomForestRegressor(**params, random_state=42)
                else:
                    model = RandomForestRegressor(**params, random_state=42)
                
                # Cross-validation
                cv = TimeSeriesSplit(n_splits=cv_folds)
                scores = cross_val_score(model, X_train, y_train, cv=cv, scoring='r2')
                
                return scores.mean()
            
            # Create and run study
            self.study = optuna.create_study(
                direction='maximize',
                study_name=f'{model_type}_regression_optimization'
            )
            
            self.study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
            
            best_params = self.study.best_params
            best_score = self.study.best_value
            
            logger.info(f"✅ Optimization complete: Best R² = {best_score:.4f}")
            
            return {
                'model_type': model_type,
                'best_params': best_params,
                'best_score': best_score,
                'n_trials': n_trials,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error during optimization: {e}")
            return {'error': str(e)}
    
    def _get_classifier_params(self, trial: optuna.Trial, model_type: str) -> Dict[str, Any]:
        """Get hyperparameter search space for classifier."""
        if model_type == 'random_forest':
            return {
                'n_estimators': trial.suggest_int('n_estimators', 50, 300),
                'max_depth': trial.suggest_int('max_depth', 3, 15),
                'min_samples_split': trial.suggest_int('min_samples_split', 2, 20),
                'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 10),
                'max_features': trial.suggest_categorical('max_features', ['sqrt', 'log2']),
            }
        else:
            return {}
    
    def _get_regressor_params(self, trial: optuna.Trial, model_type: str) -> Dict[str, Any]:
        """Get hyperparameter search space for regressor."""
        if model_type == 'random_forest':
            return {
                'n_estimators': trial.suggest_int('n_estimators', 50, 300),
                'max_depth': trial.suggest_int('max_depth', 3, 15),
                'min_samples_split': trial.suggest_int('min_samples_split', 2, 20),
                'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 10),
                'max_features': trial.suggest_categorical('max_features', ['sqrt', 'log2', None]),
            }
        else:
            return {}
    
    def get_optimization_history(self) -> Optional[pd.DataFrame]:
        """Get optimization history as DataFrame."""
        if self.study is None:
            return None
        
        return self.study.trials_dataframe()
    
    def plot_optimization_history(self) -> Optional[Any]:
        """Plot optimization history (for notebook use)."""
        if self.study is None:
            return None
        
        try:
            from optuna.visualization import plot_optimization_history
            return plot_optimization_history(self.study)
        except ImportError:
            logger.warning("Plotly not installed, cannot plot optimization history")
            return None
