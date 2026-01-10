"""
ML Module Package

Machine learning pipeline for stock prediction integrated with QUAD platform.
Supports XGBoost, Random Forest, LSTM, ensemble methods, and SHAP explainability.

Author: Trading System ML Team
Created: 2026-01-09
"""

__version__ = "1.0.0"

from .pipeline import MLPipeline
from .models.ensemble import VotingEnsemble, StackingEnsemble
from .models.lstm import LSTMClassifier, LSTMTrainer
from .features.engineering import FeatureEngineer
from .tuning.hyperparameter import XGBoostTuner, tune_xgboost
from .explainability.shap_explainer import ModelExplainer, explain_prediction
from .tracking.mlflow_manager import MLflowManager

__all__ = [
    "MLPipeline",
    "VotingEnsemble",
    "StackingEnsemble",
    "LSTMClassifier",
    "LSTMTrainer",
    "FeatureEngineer",
    "XGBoostTuner",
    "tune_xgboost",
    "ModelExplainer",
    "explain_prediction",
    "MLflowManager",
]
