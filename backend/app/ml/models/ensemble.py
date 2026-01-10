"""
Ensemble Models for Stock Prediction

Combines multiple models (XGBoost, LSTM, Random Forest) for improved predictions.
Implements voting ensemble and stacking ensemble methods.

Ported from trader_start/libs/ensemble_models.py
Author: Trading System ML Team
Created: 2026-01-09
"""

import numpy as np
import pandas as pd
from typing import List, Tuple, Dict, Optional
import logging
import joblib
from pathlib import Path

logger = logging.getLogger(__name__)


class VotingEnsemble:
    """
    Soft voting ensemble for combining multiple models.
    
    Averages probability predictions from multiple models with optional weights.
    
    Example:
        >>> models = [
        ...     ('xgboost', xgb_model),
        ...     ('lstm', lstm_model),
        ...     ('rf', rf_model)
        ... ]
        >>> ensemble = VotingEnsemble(models, weights=[0.3, 0.5, 0.2])
        >>> predictions = ensemble.predict(X_test)
    """
    
    def __init__(self, 
                 models: List[Tuple[str, object]],
                 weights: Optional[List[float]] = None):
        """
        Initialize voting ensemble.
        
        Args:
            models: List of (name, model) tuples
            weights: Optional weights for each model (must sum to 1.0)
        """
        self.models = models
        
        # Set equal weights if not provided
        if weights is None:
            weights = [1.0 / len(models)] * len(models)
        
        # Validate weights
        if len(weights) != len(models):
            raise ValueError(f"Number of weights ({len(weights)}) must match number of models ({len(models)})")
        
        if not np.isclose(sum(weights), 1.0):
            logger.warning(f"Weights sum to {sum(weights)}, normalizing to 1.0")
            weights = [w / sum(weights) for w in weights]
        
        self.weights = weights
        
        logger.info(f"Initialized VotingEnsemble with {len(models)} models")
        for (name, _), weight in zip(models, weights):
            logger.info(f"  {name}: {weight:.2%}")
    
    def predict_proba(self, X: np.ndarray, X_seq: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Predict class probabilities using weighted voting.
        
        Args:
            X: Features for tree-based models (n_samples, n_features)
            X_seq: Sequences for LSTM models (n_samples, seq_len, n_features)
        
        Returns:
            Weighted average probabilities (n_samples, n_classes)
        """
        all_probas = []
        
        for (name, model), weight in zip(self.models, self.weights):
            # Check if model needs sequences (LSTM) or flat features
            if 'lstm' in name.lower() or 'gru' in name.lower():
                if X_seq is None:
                    raise ValueError(f"Model {name} requires sequences (X_seq)")
                
                # LSTM prediction
                import torch
                model.eval()
                with torch.no_grad():
                    X_tensor = torch.FloatTensor(X_seq)
                    proba = model.predict_proba(X_tensor).numpy()
            else:
                # Tree-based model prediction
                proba = model.predict_proba(X)
            
            # Weight the probabilities
            all_probas.append(proba * weight)
        
        # Average weighted probabilities
        ensemble_proba = np.sum(all_probas, axis=0)
        
        return ensemble_proba
    
    def predict(self, X: np.ndarray, X_seq: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Predict class labels.
        
        Args:
            X: Features for tree-based models
            X_seq: Sequences for LSTM models
        
        Returns:
            Predicted class labels
        """
        probas = self.predict_proba(X, X_seq)
        predictions = np.argmax(probas, axis=1)
        return predictions
    
    def evaluate(self, X: np.ndarray, y: np.ndarray, 
                X_seq: Optional[np.ndarray] = None) -> Dict:
        """
        Evaluate ensemble performance.
        
        Args:
            X: Test features
            y: True labels
            X_seq: Test sequences (optional)
        
        Returns:
            Dictionary with metrics
        """
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
        
        predictions = self.predict(X, X_seq)
        probas = self.predict_proba(X, X_seq)
        
        metrics = {
            'accuracy': accuracy_score(y, predictions),
            'precision': precision_score(y, predictions, average='weighted', zero_division=0),
            'recall': recall_score(y, predictions, average='weighted', zero_division=0),
            'f1': f1_score(y, predictions, average='weighted', zero_division=0)
        }
        
        logger.info(f"Ensemble Accuracy: {metrics['accuracy']:.4f}")
        
        return metrics
    
    def save(self, path: str):
        """Save ensemble configuration."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        config = {
            'model_names': [name for name, _ in self.models],
            'weights': self.weights
        }
        
        joblib.dump(config, path)
        logger.info(f"Saved ensemble config to {path}")
    
    @classmethod
    def load(cls, path: str, models: List[Tuple[str, object]]):
        """Load ensemble configuration."""
        config = joblib.load(path)
        
        # Match models by name
        model_dict = {name: model for name, model in models}
        ordered_models = [(name, model_dict[name]) for name in config['model_names']]
        
        return cls(ordered_models, config['weights'])


class StackingEnsemble:
    """
    Stacking ensemble with meta-learner.
    
    Uses predictions from base models as features for a meta-model.
    
    Example:
        >>> base_models = [('xgb', xgb_model), ('lstm', lstm_model), ('rf', rf_model)]
        >>> from sklearn.linear_model import LogisticRegression
        >>> meta_model = LogisticRegression()
        >>> stacker = StackingEnsemble(base_models, meta_model)
        >>> stacker.fit(X_train, y_train, X_train_seq)
        >>> predictions = stacker.predict(X_test, X_test_seq)
    """
    
    def __init__(self,
                 base_models: List[Tuple[str, object]],
                 meta_model: object):
        """
        Initialize stacking ensemble.
        
        Args:
            base_models: List of (name, model) tuples for base models
            meta_model: Meta-learner model (e.g., Logistic Regression)
        """
        self.base_models = base_models
        self.meta_model = meta_model
        self.is_fitted = False
        
        logger.info(f"Initialized StackingEnsemble with {len(base_models)} base models")
    
    def _get_base_predictions(self, X: np.ndarray, 
                             X_seq: Optional[np.ndarray] = None,
                             return_proba: bool = True) -> np.ndarray:
        """
        Get predictions from all base models.
        
        Args:
            X: Features for tree-based models
            X_seq: Sequences for LSTM models
            return_proba: Whether to return probabilities or class labels
        
        Returns:
            Stacked predictions (n_samples, n_models * n_classes) if proba
            or (n_samples, n_models) if class labels
        """
        all_preds = []
        
        for name, model in self.base_models:
            if 'lstm' in name.lower() or 'gru' in name.lower():
                if X_seq is None:
                    raise ValueError(f"Model {name} requires sequences")
                
                # LSTM prediction
                import torch
                model.eval()
                with torch.no_grad():
                    X_tensor = torch.FloatTensor(X_seq)
                    if return_proba:
                        pred = model.predict_proba(X_tensor).numpy()
                    else:
                        pred = torch.argmax(model(X_tensor), dim=1).numpy()
            else:
                # Tree-based model
                if return_proba:
                    pred = model.predict_proba(X)
                else:
                    pred = model.predict(X)
            
            all_preds.append(pred)
        
        # Stack predictions
        if return_proba:
            # Flatten probabilities: (n_samples, n_models, n_classes) -> (n_samples, n_models * n_classes)
            stacked = np.hstack(all_preds)
        else:
            # Stack class predictions: (n_samples, n_models)
            stacked = np.column_stack(all_preds)
        
        return stacked
    
    def fit(self, X: np.ndarray, y: np.ndarray,
           X_seq: Optional[np.ndarray] = None):
        """
        Fit meta-model on base model predictions.
        
        Args:
            X: Training features
            y: Training labels
            X_seq: Training sequences (optional)
        """
        logger.info("Fitting stacking ensemble...")
        
        # Get base model predictions
        base_preds = self._get_base_predictions(X, X_seq, return_proba=True)
        
        # Fit meta-model
        self.meta_model.fit(base_preds, y)
        self.is_fitted = True
        
        logger.info("Stacking ensemble fitted successfully")
    
    def predict_proba(self, X: np.ndarray, 
                     X_seq: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Predict probabilities using stacking.
        
        Args:
            X: Test features
            X_seq: Test sequences (optional)
        
        Returns:
            Predicted probabilities
        """
        if not self.is_fitted:
            raise ValueError("Ensemble must be fitted before prediction")
        
        # Get base model predictions
        base_preds = self._get_base_predictions(X, X_seq, return_proba=True)
        
        # Meta-model prediction
        probas = self.meta_model.predict_proba(base_preds)
        
        return probas
    
    def predict(self, X: np.ndarray, 
               X_seq: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Predict class labels.
        
        Args:
            X: Test features
            X_seq: Test sequences (optional)
        
        Returns:
            Predicted class labels
        """
        probas = self.predict_proba(X, X_seq)
        predictions = np.argmax(probas, axis=1)
        return predictions
    
    def evaluate(self, X: np.ndarray, y: np.ndarray,
                X_seq: Optional[np.ndarray] = None) -> Dict:
        """
        Evaluate stacking ensemble.
        
        Args:
            X: Test features
            y: True labels
            X_seq: Test sequences (optional)
        
        Returns:
            Dictionary with metrics
        """
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
        
        predictions = self.predict(X, X_seq)
        
        metrics = {
            'accuracy': accuracy_score(y, predictions),
            'precision': precision_score(y, predictions, average='weighted', zero_division=0),
            'recall': recall_score(y, predictions, average='weighted', zero_division=0),
            'f1': f1_score(y, predictions, average='weighted', zero_division=0)
        }
        
        logger.info(f"Stacking Accuracy: {metrics['accuracy']:.4f}")
        
        return metrics


def optimize_ensemble_weights(models: List[Tuple[str, object]],
                              X_val: np.ndarray,
                              y_val: np.ndarray,
                              X_val_seq: Optional[np.ndarray] = None,
                              n_trials: int = 100) -> List[float]:
    """
    Optimize ensemble weights using random search.
    
    Args:
        models: List of (name, model) tuples
        X_val: Validation features
        y_val: Validation labels
        X_val_seq: Validation sequences (optional)
        n_trials: Number of optimization trials
    
    Returns:
        Optimized weights
    """
    from sklearn.metrics import accuracy_score
    
    logger.info(f"Optimizing ensemble weights with {n_trials} trials...")
    
    best_accuracy = 0
    best_weights = [1.0 / len(models)] * len(models)
    
    # Simple random search
    for _ in range(n_trials):
        # Random weights from Dirichlet distribution
        weights = np.random.dirichlet(np.ones(len(models)))
        
        # Create ensemble
        ensemble = VotingEnsemble(models, weights.tolist())
        
        # Evaluate
        predictions = ensemble.predict(X_val, X_val_seq)
        accuracy = accuracy_score(y_val, predictions)
        
        if accuracy > best_accuracy:
            best_accuracy = accuracy
            best_weights = weights.tolist()
    
    logger.info(f"Best accuracy: {best_accuracy:.4f}")
    logger.info(f"Best weights: {best_weights}")
    
    return best_weights
