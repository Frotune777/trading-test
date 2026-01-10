"""
Model Explainability with SHAP

Provides interpretable explanations for model predictions using SHAP values.
Supports XGBoost (TreeExplainer) for tree-based models.

Ported from trader_start/libs/model_explainer.py
Author: Trading System ML Team
Created: 2026-01-09
"""

import shap
import numpy as np
import pandas as pd
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class ModelExplainer:
    """
    SHAP-based model explainer for interpretable predictions.
    
    Supports:
    - TreeExplainer for XGBoost, Random Forest
    - Feature importance analysis
    - Individual prediction explanations
    
    Example:
        >>> explainer = ModelExplainer(xgb_model, model_type='tree')
        >>> shap_values = explainer.explain_prediction(X_test)
        >>> importance = explainer.get_feature_importance(X_test, feature_names)
    """
    
    def __init__(self, 
                 model: object,
                 model_type: str = 'tree',
                 background_data: Optional[np.ndarray] = None):
        """
        Initialize model explainer.
        
        Args:
            model: Trained model to explain
            model_type: Type of model ('tree' for XGBoost/RF)
            background_data: Background dataset (optional)
        """
        self.model = model
        self.model_type = model_type
        
        # Create appropriate explainer
        if model_type == 'tree':
            self.explainer = shap.TreeExplainer(model)
            logger.info("Initialized TreeExplainer for tree-based model")
        else:
            raise ValueError(f"Unsupported model_type: {model_type}")
    
    def explain_prediction(self, X: np.ndarray) -> np.ndarray:
        """
        Calculate SHAP values for predictions.
        
        Args:
            X: Input features (n_samples, n_features)
        
        Returns:
            SHAP values array
        """
        shap_values = self.explainer.shap_values(X)
        logger.info(f"Calculated SHAP values for {len(X)} samples")
        return shap_values
    
    def get_feature_importance(self, 
                               X: np.ndarray,
                               feature_names: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Get SHAP-based feature importance.
        
        Args:
            X: Input features
            feature_names: Names of features (optional)
        
        Returns:
            DataFrame with feature importance scores
        """
        shap_values = self.explain_prediction(X)
        
        # Handle different SHAP value formats
        if isinstance(shap_values, list):
            importance = np.mean([np.abs(sv).mean(axis=0) for sv in shap_values], axis=0)
        elif shap_values.ndim == 3:
            importance = np.abs(shap_values).mean(axis=(0, 2))
        else:
            importance = np.abs(shap_values).mean(axis=0)
        
        importance = np.asarray(importance).flatten()
        
        if feature_names is None:
            feature_names = [f'feature_{i}' for i in range(len(importance))]
        
        importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance': importance
        }).sort_values('importance', ascending=False)
        
        return importance_df
    
    def get_top_features(self,
                        X_sample: np.ndarray,
                        feature_names: Optional[List[str]] = None,
                        class_idx: int = 0,
                        top_n: int = 10) -> pd.DataFrame:
        """
        Get top N features contributing to a prediction.
        
        Args:
            X_sample: Single sample features
            feature_names: Names of features
            class_idx: Class index for multiclass
            top_n: Number of top features to return
        
        Returns:
            DataFrame with top features and their SHAP values
        """
        if X_sample.ndim == 1:
            X_sample = X_sample.reshape(1, -1)
        
        shap_values = self.explain_prediction(X_sample)
        
        # Handle multiclass
        if isinstance(shap_values, list):
            shap_vals = shap_values[class_idx][0]
        else:
            shap_vals = shap_values[0]
        
        if feature_names is None:
            feature_names = [f'feature_{i}' for i in range(len(shap_vals))]
        
        abs_shap = np.abs(shap_vals)
        top_indices = np.argsort(abs_shap)[-top_n:][::-1]
        
        top_features = pd.DataFrame({
            'feature': [feature_names[i] for i in top_indices],
            'shap_value': shap_vals[top_indices],
            'feature_value': X_sample[0, top_indices],
            'abs_shap_value': abs_shap[top_indices]
        })
        
        return top_features


def explain_prediction(model: object,
                      X_sample: np.ndarray,
                      feature_names: List[str],
                      class_names: Optional[List[str]] = None) -> Dict:
    """
    Comprehensive explanation for a single prediction.
    
    Args:
        model: Trained model
        X_sample: Single sample to explain
        feature_names: Names of features
        class_names: Names of classes (optional)
    
    Returns:
        Dictionary with explanation details
    """
    explainer = ModelExplainer(model, model_type='tree')
    
    # Get prediction
    if hasattr(model, 'predict_proba'):
        prediction_proba = model.predict_proba(X_sample.reshape(1, -1))[0]
        prediction_class = np.argmax(prediction_proba)
    else:
        prediction_class = model.predict(X_sample.reshape(1, -1))[0]
        prediction_proba = None
    
    # Get top features
    top_features = explainer.get_top_features(
        X_sample, 
        feature_names, 
        class_idx=prediction_class,
        top_n=10
    )
    
    explanation = {
        'prediction_class': int(prediction_class),
        'prediction_proba': prediction_proba.tolist() if prediction_proba is not None else None,
        'class_name': class_names[prediction_class] if class_names else f'Class {prediction_class}',
        'top_features': top_features.to_dict('records')
    }
    
    return explanation
