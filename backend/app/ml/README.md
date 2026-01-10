# ML Module - Machine Learning Pipeline

## Overview

Complete ML pipeline for stock prediction integrated with QUAD trading platform. Supports XGBoost, Random Forest, LSTM models with SHAP explainability and MLflow tracking.

## Features

- **Multiple Algorithms**: XGBoost, Random Forest, LSTM
- **Ensemble Methods**: Voting and Stacking ensembles
- **Feature Engineering**: 100+ technical features
- **Hyperparameter Tuning**: Optuna Bayesian optimization
- **Explainability**: SHAP-based feature importance
- **Experiment Tracking**: MLflow integration
- **Background Training**: Celery async tasks
- **RESTful API**: FastAPI endpoints

## Quick Start

### 1. Train a Model

```python
from app.ml import MLPipeline, FeatureEngineer

# Load OHLCV data
df = load_ohlcv_data("SBIN", "1d")

# Engineer features
engineer = FeatureEngineer(df)
features = engineer.build_all()

# Create pipeline
pipeline = MLPipeline("SBIN", "1d")
target = pipeline.create_target(df, classification='3class')

# Prepare data
X_train, X_val, X_test, y_train, y_val, y_test = pipeline.prepare_data(features, target)

# Train
pipeline.train_model(X_train, y_train, X_val, y_val, model_type='xgboost')

# Evaluate
metrics = pipeline.evaluate(X_test, y_test)
print(f"Accuracy: {metrics['accuracy']:.2%}")

# Predict
predictions, probabilities = pipeline.predict(new_features)
```

### 2. Use API Endpoints

```bash
# Train model (async)
curl -X POST http://localhost:8000/api/v1/ml/train \
  -H "Content-Type: application/json" \
  -d '{"symbol": "SBIN", "model_type": "xgboost"}'

# Get prediction
curl -X POST http://localhost:8000/api/v1/ml/predict \
  -H "Content-Type: application/json" \
  -d '{"symbol": "SBIN"}'

# List models
curl http://localhost:8000/api/v1/ml/models?symbol=SBIN

# Get SHAP explanation
curl -X POST http://localhost:8000/api/v1/ml/explain \
  -H "Content-Type: application/json" \
  -d '{"symbol": "SBIN", "top_n": 10}'
```

## Architecture

```
app/ml/
├── pipeline.py              # Core ML pipeline
├── tasks.py                 # Celery background tasks
├── models/
│   ├── ensemble.py         # Ensemble methods
│   └── lstm.py             # LSTM classifier
├── features/
│   └── engineering.py      # Feature engineering
├── tuning/
│   └── hyperparameter.py   # Optuna tuning
├── explainability/
│   └── shap_explainer.py   # SHAP integration
└── tracking/
    └── mlflow_manager.py   # MLflow tracking
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/ml/train` | Start model training |
| GET | `/api/v1/ml/train/{task_id}` | Check training status |
| POST | `/api/v1/ml/predict` | Get predictions |
| GET | `/api/v1/ml/models` | List all models |
| GET | `/api/v1/ml/models/{id}` | Get model details |
| POST | `/api/v1/ml/models/{id}/promote` | Promote to champion |
| POST | `/api/v1/ml/explain` | SHAP explanations |
| GET | `/api/v1/ml/experiments` | List experiments |

## Database Tables

- **ml_models**: Model registry with versioning
- **ml_predictions**: Prediction history
- **ml_experiments**: MLflow experiments
- **ml_features**: Feature cache

## Configuration

Set environment variables:

```bash
REDIS_URL=redis://redis:6379/0
MLFLOW_TRACKING_URI=http://mlflow:5000
```

## Testing

```bash
# Run unit tests
pytest tests/unit/ml/ -v

# Run integration tests
pytest tests/integration/ml/ -v

# Run with coverage
pytest tests/ml/ --cov=app/ml --cov-report=html
```

## Dependencies

- scikit-learn
- xgboost
- pytorch
- optuna
- shap
- mlflow
- celery
- pandas
- numpy

## License

Proprietary - QUAD Trading Platform
