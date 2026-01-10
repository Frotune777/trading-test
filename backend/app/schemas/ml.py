"""
Pydantic schemas for ML API endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum


class ModelType(str, Enum):
    """Supported model types."""
    XGBOOST = "xgboost"
    RANDOM_FOREST = "random_forest"
    LSTM = "lstm"


class PredictionClass(str, Enum):
    """Prediction classes."""
    UP = "UP"
    DOWN = "DOWN"
    NEUTRAL = "NEUTRAL"


# Training Schemas
class TrainRequest(BaseModel):
    """Request to train a new model."""
    symbol: str = Field(..., description="Stock symbol (e.g., SBIN)")
    model_type: ModelType = Field(..., description="Type of model to train")
    interval: str = Field(default="1d", description="Data interval (1d, 1h, etc.)")
    classification: str = Field(default="3class", description="Classification type (2class, 3class, 5class)")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Model hyperparameters")
    
    class Config:
        schema_extra = {
            "example": {
                "symbol": "SBIN",
                "model_type": "xgboost",
                "interval": "1d",
                "classification": "3class",
                "parameters": {"n_estimators": 200, "max_depth": 6}
            }
        }


class TrainResponse(BaseModel):
    """Response from training request."""
    task_id: str = Field(..., description="Celery task ID")
    status: str = Field(..., description="Task status")
    message: str = Field(..., description="Status message")


class TrainStatusResponse(BaseModel):
    """Training task status."""
    task_id: str
    state: str  # PENDING, STARTED, SUCCESS, FAILURE
    progress: Optional[int] = Field(default=None, description="Progress percentage (0-100)")
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# Prediction Schemas
class PredictRequest(BaseModel):
    """Request for prediction."""
    symbol: str = Field(..., description="Stock symbol")
    model_type: Optional[ModelType] = Field(default=None, description="Specific model type (uses champion if not specified)")
    model_id: Optional[int] = Field(default=None, description="Specific model ID")
    
    class Config:
        schema_extra = {
            "example": {
                "symbol": "SBIN",
                "model_type": "xgboost"
            }
        }


class PredictResponse(BaseModel):
    """Prediction response."""
    symbol: str
    prediction: str  # UP, DOWN, NEUTRAL
    confidence: float = Field(..., ge=0.0, le=1.0)
    probabilities: Dict[str, float]
    model_id: int
    model_name: str
    predicted_at: datetime
    features_used: Optional[List[str]] = None


# Model Schemas
class ModelListResponse(BaseModel):
    """Model list item."""
    id: int
    name: str
    version: str
    model_type: str
    symbol: Optional[str]
    interval: Optional[str]
    metrics: Optional[Dict[str, float]]
    is_active: bool
    is_champion: bool
    created_at: datetime


class ModelDetailResponse(BaseModel):
    """Detailed model information."""
    id: int
    name: str
    version: str
    model_type: str
    symbol: Optional[str]
    interval: Optional[str]
    metrics: Optional[Dict[str, float]]
    parameters: Optional[Dict[str, Any]]
    feature_names: Optional[List[str]]
    target_classes: Optional[List[str]]
    is_active: bool
    is_champion: bool
    created_at: datetime
    updated_at: Optional[datetime]


# Explainability Schemas
class ExplainRequest(BaseModel):
    """Request for SHAP explanation."""
    symbol: str
    model_id: Optional[int] = None
    sample_data: Optional[Dict[str, Any]] = Field(default=None, description="Optional sample data to explain")
    top_n: int = Field(default=10, description="Number of top features to return")


class FeatureImportance(BaseModel):
    """Feature importance item."""
    feature: str
    importance: float
    shap_value: Optional[float] = None


class ExplainResponse(BaseModel):
    """SHAP explanation response."""
    model_id: int
    symbol: str
    top_features: List[FeatureImportance]
    prediction: Optional[str] = None
    confidence: Optional[float] = None


# Experiment Schemas
class ExperimentResponse(BaseModel):
    """MLflow experiment."""
    id: int
    experiment_id: str
    name: str
    description: Optional[str]
    created_at: datetime


class ExperimentRunResponse(BaseModel):
    """MLflow experiment run."""
    run_id: str
    experiment_id: str
    metrics: Dict[str, float]
    parameters: Dict[str, Any]
    status: str
    start_time: datetime
    end_time: Optional[datetime]
