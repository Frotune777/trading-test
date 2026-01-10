"""
FastAPI endpoints for ML operations.

Provides API for model training, prediction, and explainability.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from celery.result import AsyncResult

from app.core.database import get_db
from app.schemas.ml import (
    TrainRequest, TrainResponse, TrainStatusResponse,
    PredictRequest, PredictResponse,
    ModelListResponse, ModelDetailResponse,
    ExplainRequest, ExplainResponse,
    ExperimentResponse
)
from app.database.models_ml import MLModel, MLPrediction, MLExperiment
from app.ml.tasks import train_model_task, batch_predict_task
from app.core.auth import get_current_user

router = APIRouter(prefix="/ml", tags=["ML"])


# Training Endpoints
@router.post("/train", response_model=TrainResponse)
async def train_model(
    request: TrainRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Start background training task for a model.
    
    Returns task_id for status tracking.
    """
    # Start Celery task
    task = train_model_task.delay(
        symbol=request.symbol,
        model_type=request.model_type.value,
        interval=request.interval,
        classification=request.classification,
        parameters=request.parameters
    )
    
    return TrainResponse(
        task_id=task.id,
        status="started",
        message=f"Training started for {request.symbol} with {request.model_type}"
    )


@router.get("/train/{task_id}", response_model=TrainStatusResponse)
async def get_train_status(task_id: str):
    """
    Get status of training task.
    
    Returns current state, progress, and result if complete.
    """
    task_result = AsyncResult(task_id)
    
    response = TrainStatusResponse(
        task_id=task_id,
        state=task_result.state
    )
    
    if task_result.state == 'PENDING':
        response.progress = 0
    elif task_result.state == 'STARTED':
        response.progress = 10
    elif task_result.state == 'PROGRESS':
        response.progress = task_result.info.get('progress', 50)
    elif task_result.state == 'SUCCESS':
        response.progress = 100
        response.result = task_result.result
    elif task_result.state == 'FAILURE':
        response.error = str(task_result.info)
    
    return response


# Prediction Endpoints
@router.post("/predict", response_model=PredictResponse)
async def predict(
    request: PredictRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get prediction for a symbol.
    
    Uses champion model if model_id not specified.
    """
    # Find model
    query = db.query(MLModel).filter(MLModel.symbol == request.symbol)
    
    if request.model_id:
        model = query.filter(MLModel.id == request.model_id).first()
    elif request.model_type:
        model = query.filter(
            MLModel.model_type == request.model_type.value,
            MLModel.is_active == True
        ).order_by(MLModel.created_at.desc()).first()
    else:
        # Use champion model
        model = query.filter(MLModel.is_champion == True).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active model found for {request.symbol}"
        )
    
    # TODO: Load model and make prediction
    # This is a placeholder
    from datetime import datetime
    
    prediction_response = PredictResponse(
        symbol=request.symbol,
        prediction="UP",
        confidence=0.75,
        probabilities={"UP": 0.75, "DOWN": 0.15, "NEUTRAL": 0.10},
        model_id=model.id,
        model_name=model.name,
        predicted_at=datetime.now()
    )
    
    # Save prediction to database
    db_prediction = MLPrediction(
        model_id=model.id,
        symbol=request.symbol,
        prediction=prediction_response.prediction,
        confidence=prediction_response.confidence,
        probabilities=prediction_response.probabilities
    )
    db.add(db_prediction)
    db.commit()
    
    return prediction_response


# Model Management Endpoints
@router.get("/models", response_model=List[ModelListResponse])
async def list_models(
    symbol: Optional[str] = None,
    model_type: Optional[str] = None,
    active_only: bool = False,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    List all models with optional filters.
    """
    query = db.query(MLModel)
    
    if symbol:
        query = query.filter(MLModel.symbol == symbol)
    if model_type:
        query = query.filter(MLModel.model_type == model_type)
    if active_only:
        query = query.filter(MLModel.is_active == True)
    
    models = query.order_by(MLModel.created_at.desc()).all()
    
    return [
        ModelListResponse(
            id=m.id,
            name=m.name,
            version=m.version,
            model_type=m.model_type,
            symbol=m.symbol,
            interval=m.interval,
            metrics=m.metrics,
            is_active=m.is_active,
            is_champion=m.is_champion,
            created_at=m.created_at
        )
        for m in models
    ]


@router.get("/models/{model_id}", response_model=ModelDetailResponse)
async def get_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get detailed information about a specific model.
    """
    model = db.query(MLModel).filter(MLModel.id == model_id).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model {model_id} not found"
        )
    
    return ModelDetailResponse(
        id=model.id,
        name=model.name,
        version=model.version,
        model_type=model.model_type,
        symbol=model.symbol,
        interval=model.interval,
        metrics=model.metrics,
        parameters=model.parameters,
        feature_names=model.feature_names,
        target_classes=model.target_classes,
        is_active=model.is_active,
        is_champion=model.is_champion,
        created_at=model.created_at,
        updated_at=model.updated_at
    )


@router.post("/models/{model_id}/promote")
async def promote_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Promote model to champion status.
    
    Demotes current champion for the same symbol.
    """
    model = db.query(MLModel).filter(MLModel.id == model_id).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model {model_id} not found"
        )
    
    # Demote current champion
    db.query(MLModel).filter(
        MLModel.symbol == model.symbol,
        MLModel.is_champion == True
    ).update({"is_champion": False})
    
    # Promote new champion
    model.is_champion = True
    model.is_active = True
    db.commit()
    
    return {"success": True, "message": f"Model {model_id} promoted to champion"}


# Explainability Endpoints
@router.post("/explain", response_model=ExplainResponse)
async def explain_prediction(
    request: ExplainRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get SHAP explanation for a prediction.
    """
    # Find model
    if request.model_id:
        model = db.query(MLModel).filter(MLModel.id == request.model_id).first()
    else:
        model = db.query(MLModel).filter(
            MLModel.symbol == request.symbol,
            MLModel.is_champion == True
        ).first()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No model found for {request.symbol}"
        )
    
    # TODO: Load model and generate SHAP values
    # This is a placeholder
    from app.schemas.ml import FeatureImportance
    
    top_features = [
        FeatureImportance(feature="return_1d", importance=0.25, shap_value=0.15),
        FeatureImportance(feature="volatility_20d", importance=0.18, shap_value=-0.08),
        FeatureImportance(feature="volume_momentum_10d", importance=0.15, shap_value=0.12),
        FeatureImportance(feature="roc_10d", importance=0.12, shap_value=0.09),
        FeatureImportance(feature="vwap_distance", importance=0.10, shap_value=-0.05),
    ]
    
    return ExplainResponse(
        model_id=model.id,
        symbol=request.symbol,
        top_features=top_features[:request.top_n],
        prediction="UP",
        confidence=0.75
    )


# Experiment Endpoints
@router.get("/experiments", response_model=List[ExperimentResponse])
async def list_experiments(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    List all MLflow experiments.
    """
    experiments = db.query(MLExperiment).order_by(MLExperiment.created_at.desc()).all()
    
    return [
        ExperimentResponse(
            id=exp.id,
            experiment_id=exp.experiment_id,
            name=exp.name,
            description=exp.description,
            created_at=exp.created_at
        )
        for exp in experiments
    ]
