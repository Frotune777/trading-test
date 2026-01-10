"""
Hyperparameter Tuning with Optuna

Automated hyperparameter optimization for XGBoost and LSTM models.
Uses Bayesian optimization to find optimal hyperparameters.

Ported from trader_start/libs/hyperparameter_tuner.py
Author: Trading System ML Team
Created: 2026-01-09
"""

import optuna
import numpy as np
from typing import Dict, Optional
import logging
from sklearn.model_selection import cross_val_score
import joblib
from pathlib import Path

logger = logging.getLogger(__name__)

# Suppress Optuna logs
optuna.logging.set_verbosity(optuna.logging.WARNING)


class XGBoostTuner:
    """
    Hyperparameter tuner for XGBoost models using Optuna.
    
    Example:
        >>> tuner = XGBoostTuner(X_train, y_train, X_val, y_val)
        >>> best_params = tuner.optimize(n_trials=100)
        >>> print(best_params)
    """
    
    def __init__(self,
                 X_train: np.ndarray,
                 y_train: np.ndarray,
                 X_val: Optional[np.ndarray] = None,
                 y_val: Optional[np.ndarray] = None,
                 metric: str = 'accuracy'):
        """Initialize XGBoost tuner."""
        self.X_train = X_train
        self.y_train = y_train
        self.X_val = X_val
        self.y_val = y_val
        self.metric = metric
        self.best_params = None
        self.best_score = None
        
        logger.info(f"Initialized XGBoostTuner with {len(X_train)} training samples")
    
    def objective(self, trial: optuna.Trial) -> float:
        """Optuna objective function for XGBoost."""
        from xgboost import XGBClassifier
        from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
        
        # Suggest hyperparameters
        params = {
            'n_estimators': trial.suggest_int('n_estimators', 50, 500),
            'max_depth': trial.suggest_int('max_depth', 3, 10),
            'learning_rate': trial.suggest_float('learning_rate', 0.001, 0.3, log=True),
            'subsample': trial.suggest_float('subsample', 0.6, 1.0),
            'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
            'min_child_weight': trial.suggest_int('min_child_weight', 1, 10),
            'gamma': trial.suggest_float('gamma', 0.0, 5.0),
            'reg_alpha': trial.suggest_float('reg_alpha', 0.0, 1.0),
            'reg_lambda': trial.suggest_float('reg_lambda', 0.0, 1.0),
            'random_state': 42,
            'n_jobs': -1
        }
        
        # Train model
        model = XGBClassifier(**params)
        model.fit(self.X_train, self.y_train)
        
        # Evaluate
        if self.X_val is not None and self.y_val is not None:
            y_pred = model.predict(self.X_val)
            
            if self.metric == 'accuracy':
                score = accuracy_score(self.y_val, y_pred)
            elif self.metric == 'f1':
                score = f1_score(self.y_val, y_pred, average='weighted')
            elif self.metric == 'roc_auc':
                y_pred_proba = model.predict_proba(self.X_val)
                score = roc_auc_score(self.y_val, y_pred_proba, multi_class='ovr', average='weighted')
            else:
                score = accuracy_score(self.y_val, y_pred)
        else:
            # Use cross-validation
            scores = cross_val_score(model, self.X_train, self.y_train, cv=3, scoring=self.metric)
            score = scores.mean()
        
        return score
    
    def optimize(self,
                n_trials: int = 100,
                timeout: Optional[int] = None,
                show_progress: bool = True) -> Dict:
        """Run hyperparameter optimization."""
        logger.info(f"Starting optimization with {n_trials} trials...")
        
        # Create study
        study = optuna.create_study(
            direction='maximize',
            sampler=optuna.samplers.TPESampler(seed=42)
        )
        
        # Optimize
        study.optimize(
            self.objective,
            n_trials=n_trials,
            timeout=timeout,
            show_progress_bar=show_progress
        )
        
        # Store results
        self.best_params = study.best_params
        self.best_score = study.best_value
        
        logger.info(f"Optimization complete!")
        logger.info(f"Best {self.metric}: {self.best_score:.4f}")
        logger.info(f"Best parameters: {self.best_params}")
        
        return self.best_params
    
    def save_results(self, path: str):
        """Save optimization results."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        results = {
            'best_params': self.best_params,
            'best_score': self.best_score,
            'metric': self.metric
        }
        
        joblib.dump(results, path)
        logger.info(f"Saved optimization results to {path}")


def tune_xgboost(X_train: np.ndarray,
                y_train: np.ndarray,
                X_val: Optional[np.ndarray] = None,
                y_val: Optional[np.ndarray] = None,
                n_trials: int = 100,
                metric: str = 'accuracy',
                save_path: Optional[str] = None) -> Dict:
    """
    Convenience function to tune XGBoost hyperparameters.
    
    Args:
        X_train: Training features
        y_train: Training labels
        X_val: Validation features (optional)
        y_val: Validation labels (optional)
        n_trials: Number of optimization trials
        metric: Optimization metric
        save_path: Path to save results (optional)
    
    Returns:
        Best hyperparameters
    """
    tuner = XGBoostTuner(X_train, y_train, X_val, y_val, metric=metric)
    best_params = tuner.optimize(n_trials=n_trials)
    
    if save_path:
        tuner.save_results(save_path)
    
    return best_params
