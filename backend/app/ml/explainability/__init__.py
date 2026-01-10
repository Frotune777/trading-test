"""
Explainability Package

Contains model explainability utilities using SHAP.
"""

from .shap_explainer import ModelExplainer, explain_prediction

__all__ = ["ModelExplainer", "explain_prediction"]
