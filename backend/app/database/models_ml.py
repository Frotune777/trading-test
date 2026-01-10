"""
Database models for ML module.

Stores ML models, predictions, experiments, and feature cache.
"""

from sqlalchemy import Column, Integer, String, Boolean, Numeric, DateTime, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.core.database import Base


class MLModel(Base):
    """
    ML Models Registry.
    
    Stores trained models with versioning and metrics.
    """
    __tablename__ = "ml_models"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    version = Column(String(50), nullable=False)
    model_type = Column(String(50), nullable=False)  # xgboost, random_forest, lstm
    symbol = Column(String(20), nullable=True, index=True)
    interval = Column(String(10), nullable=True)  # 1d, 1h, etc.
    
    # Model storage
    model_path = Column(Text, nullable=False)  # Path to joblib/torch file
    scaler_path = Column(Text, nullable=True)  # Path to scaler file
    
    # Metadata
    metrics = Column(JSONB, nullable=True)  # {accuracy, precision, recall, f1, roc_auc}
    parameters = Column(JSONB, nullable=True)  # Model hyperparameters
    feature_names = Column(JSONB, nullable=True)  # List of feature names
    target_classes = Column(JSONB, nullable=True)  # Class labels
    
    # Status
    is_active = Column(Boolean, default=False, index=True)
    is_champion = Column(Boolean, default=False)  # Champion model for symbol
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(100), nullable=True)
    
    __table_args__ = (
        Index('idx_ml_models_active', 'is_active', 'model_type'),
        Index('idx_ml_models_symbol', 'symbol', 'model_type'),
    )
    
    def __repr__(self):
        return f"<MLModel(name={self.name}, version={self.version}, type={self.model_type})>"


class MLPrediction(Base):
    """
    ML Predictions History.
    
    Stores predictions made by models for tracking and verification.
    """
    __tablename__ = "ml_predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey('ml_models.id'), nullable=False, index=True)
    
    # Prediction details
    symbol = Column(String(20), nullable=False, index=True)
    prediction = Column(String(20), nullable=False)  # UP, DOWN, NEUTRAL (or class index)
    confidence = Column(Numeric(5, 4), nullable=True)  # 0.0000 to 1.0000
    probabilities = Column(JSONB, nullable=True)  # {0: 0.2, 1: 0.3, 2: 0.5}
    
    # Features used
    features_snapshot = Column(JSONB, nullable=True)  # Snapshot of features used
    
    # Verification
    actual_outcome = Column(String(20), nullable=True)  # Filled after verification
    is_correct = Column(Boolean, nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    predicted_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    __table_args__ = (
        Index('idx_ml_predictions_symbol_time', 'symbol', 'predicted_at'),
        Index('idx_ml_predictions_model', 'model_id', 'predicted_at'),
    )
    
    def __repr__(self):
        return f"<MLPrediction(symbol={self.symbol}, prediction={self.prediction}, confidence={self.confidence})>"


class MLExperiment(Base):
    """
    ML Experiments (MLflow integration).
    
    Tracks ML experiments for model development.
    """
    __tablename__ = "ml_experiments"
    
    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Metadata
    tags = Column(JSONB, nullable=True)
    artifact_location = Column(Text, nullable=True)
    
    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String(100), nullable=True)
    
    def __repr__(self):
        return f"<MLExperiment(name={self.name}, id={self.experiment_id})>"


class MLFeatureCache(Base):
    """
    ML Features Cache.
    
    Caches engineered features to avoid recomputation.
    """
    __tablename__ = "ml_features"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    interval = Column(String(10), nullable=False)  # 1d, 1h, etc.
    
    # Features
    features = Column(JSONB, nullable=False)  # Engineered features as JSON
    feature_count = Column(Integer, nullable=True)
    
    # Metadata
    data_start_date = Column(DateTime(timezone=True), nullable=True)
    data_end_date = Column(DateTime(timezone=True), nullable=True)
    rows_count = Column(Integer, nullable=True)
    
    # Cache control
    calculated_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    __table_args__ = (
        Index('idx_ml_features_symbol_interval', 'symbol', 'interval'),
    )
    
    def __repr__(self):
        return f"<MLFeatureCache(symbol={self.symbol}, interval={self.interval}, features={self.feature_count})>"
