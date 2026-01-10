"""
MLflow Tracking Module

Manages MLflow experiment tracking and model registry.

Ported from trader_start/libs/mlflow_utils.py
Author: Trading System ML Team
Created: 2026-01-09
"""

import mlflow
import mlflow.sklearn
import mlflow.pytorch
import mlflow.xgboost
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MLflowManager:
    """
    Manages MLflow experiment tracking and logging.
    
    Example:
        >>> manager = MLflowManager(experiment_name="stock_prediction")
        >>> with manager.start_run(run_name="xgboost_run"):
        ...     manager.log_params({"n_estimators": 100})
        ...     manager.log_metrics({"accuracy": 0.85})
        ...     manager.log_model(model, "model", model_type="xgboost")
    """
    
    def __init__(self, experiment_name: str = "quad_ml_experiments", tracking_uri: str = None):
        """
        Initialize MLflow manager.
        
        Args:
            experiment_name: Name of the experiment to log to
            tracking_uri: MLflow tracking URI (default: http://mlflow:5000)
        """
        if tracking_uri is None:
            # Default to MLflow server in Docker
            tracking_uri = "http://mlflow:5000"
            
        mlflow.set_tracking_uri(tracking_uri)
        mlflow.set_experiment(experiment_name)
        self.experiment = mlflow.get_experiment_by_name(experiment_name)
        self.run_id = None
        
        logger.info(f"Initialized MLflowManager: experiment={experiment_name}, uri={tracking_uri}")
        
    def start_run(self, run_name: str = None, nested: bool = False):
        """Start a new MLflow run."""
        if run_name is None:
            run_name = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
        run = mlflow.start_run(run_name=run_name, nested=nested)
        self.run_id = run.info.run_id
        logger.info(f"Started MLflow run: {run_name} (ID: {self.run_id})")
        return run
        
    def end_run(self):
        """End the current MLflow run."""
        if mlflow.active_run():
            mlflow.end_run()
            logger.info(f"Ended MLflow run: {self.run_id}")
            self.run_id = None
            
    def log_params(self, params: dict):
        """Log a dictionary of parameters."""
        mlflow.log_params(params)
        logger.debug(f"Logged {len(params)} parameters")
        
    def log_metrics(self, metrics: dict, step: int = None):
        """Log a dictionary of metrics."""
        mlflow.log_metrics(metrics, step=step)
        logger.debug(f"Logged {len(metrics)} metrics")
        
    def log_model(self, model, artifact_path: str, model_type: str = "sklearn"):
        """
        Log a model to MLflow.
        
        Args:
            model: Model object to log
            artifact_path: Path within the run's artifact directory
            model_type: Type of model ('sklearn', 'xgboost', 'pytorch')
        """
        if model_type == "sklearn":
            mlflow.sklearn.log_model(model, artifact_path)
        elif model_type == "xgboost":
            mlflow.xgboost.log_model(model, artifact_path)
        elif model_type == "pytorch":
            mlflow.pytorch.log_model(model, artifact_path)
        else:
            logger.warning(f"Unknown model type '{model_type}', skipping log_model")
            return
            
        logger.info(f"Logged {model_type} model to {artifact_path}")
            
    def log_artifact(self, local_path: str, artifact_path: str = None):
        """Log a local file or directory as an artifact."""
        import os
        if os.path.exists(local_path):
            mlflow.log_artifact(local_path, artifact_path)
            logger.info(f"Logged artifact: {local_path}")
        else:
            logger.warning(f"Artifact not found at {local_path}")
            
    def register_model(self, model_name: str, model_uri: str = None):
        """Register the current run's model to the Model Registry."""
        if model_uri is None and self.run_id:
            model_uri = f"runs:/{self.run_id}/model"
            
        if model_uri:
            mlflow.register_model(model_uri, model_name)
            logger.info(f"Registered model: {model_name}")
            
    def get_best_run(self, metric_name: str = "accuracy", ascending: bool = False):
        """Get the best run from the experiment based on a metric."""
        runs = mlflow.search_runs(experiment_ids=[self.experiment.experiment_id])
        if runs.empty:
            return None
            
        runs = runs.sort_values(f"metrics.{metric_name}", ascending=ascending)
        return runs.iloc[0]
