"""
Model Promotion Pipeline
Automated deployment of best-performing models (shadow mode only)
"""

import logging
import pickle
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, r2_score
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class ModelPromoter:
    """
    Automated model promotion pipeline.
    
    Features:
    - Evaluate model performance
    - Compare against baseline
    - Automated promotion based on criteria
    - A/B testing support
    - Rollback mechanism
    
    CRITICAL: All models remain in shadow mode (Rule #42-45)
    """
    
    def __init__(self, db: AsyncSession, model_dir: str = "models/quad"):
        self.db = db
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
    
    async def evaluate_model(
        self,
        model: Any,
        X_val: np.ndarray,
        y_val: np.ndarray,
        task_type: str = 'classification'
    ) -> Dict[str, float]:
        """
        Evaluate model performance.
        
        Args:
            model: Trained model
            X_val: Validation features
            y_val: Validation labels/targets
            task_type: 'classification' or 'regression'
            
        Returns:
            Performance metrics
        """
        try:
            y_pred = model.predict(X_val)
            
            if task_type == 'classification':
                metrics = {
                    'accuracy': accuracy_score(y_val, y_pred),
                    'precision': precision_score(y_val, y_pred, average='weighted', zero_division=0),
                    'recall': recall_score(y_val, y_pred, average='weighted', zero_division=0),
                    'f1': f1_score(y_val, y_pred, average='weighted', zero_division=0)
                }
            else:  # regression
                from sklearn.metrics import mean_absolute_error, mean_squared_error
                metrics = {
                    'r2': r2_score(y_val, y_pred),
                    'mae': mean_absolute_error(y_val, y_pred),
                    'rmse': np.sqrt(mean_squared_error(y_val, y_pred))
                }
            
            logger.info(f"📊 Model evaluation: {metrics}")
            return metrics
            
        except Exception as e:
            logger.error(f"Error evaluating model: {e}")
            return {}
    
    async def promote_model(
        self,
        model: Any,
        model_name: str,
        metrics: Dict[str, float],
        min_accuracy: float = 0.70,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Promote model to production (shadow mode).
        
        Args:
            model: Trained model
            model_name: Model identifier
            metrics: Performance metrics
            min_accuracy: Minimum accuracy threshold
            force: Force promotion regardless of metrics
            
        Returns:
            Promotion result
        """
        try:
            # Check promotion criteria
            accuracy = metrics.get('accuracy', metrics.get('r2', 0))
            
            if not force and accuracy < min_accuracy:
                logger.warning(
                    f"❌ Model {model_name} does not meet promotion criteria: "
                    f"accuracy={accuracy:.4f} < {min_accuracy}"
                )
                return {
                    'promoted': False,
                    'reason': 'Below accuracy threshold',
                    'accuracy': accuracy,
                    'threshold': min_accuracy
                }
            
            # Save model
            model_path = self.model_dir / f"{model_name}_production.pkl"
            with open(model_path, 'wb') as f:
                pickle.dump(model, f)
            
            # Save metadata
            metadata = {
                'model_name': model_name,
                'metrics': metrics,
                'promoted_at': datetime.now().isoformat(),
                'model_path': str(model_path),
                'shadow_mode': True  # CRITICAL: Always True
            }
            
            metadata_path = self.model_dir / f"{model_name}_metadata.json"
            import json
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"✅ Model {model_name} promoted to shadow mode production")
            
            return {
                'promoted': True,
                'model_path': str(model_path),
                'metrics': metrics,
                'shadow_mode': True,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error promoting model: {e}")
            return {'promoted': False, 'error': str(e)}
    
    async def rollback_model(self, model_name: str) -> Dict[str, Any]:
        """
        Rollback to previous model version.
        
        Args:
            model_name: Model identifier
            
        Returns:
            Rollback result
        """
        try:
            # Check for backup
            backup_path = self.model_dir / f"{model_name}_backup.pkl"
            
            if not backup_path.exists():
                return {
                    'success': False,
                    'reason': 'No backup found'
                }
            
            # Restore backup
            production_path = self.model_dir / f"{model_name}_production.pkl"
            import shutil
            shutil.copy(backup_path, production_path)
            
            logger.info(f"✅ Rolled back model {model_name} to previous version")
            
            return {
                'success': True,
                'model_name': model_name,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error rolling back model: {e}")
            return {'success': False, 'error': str(e)}
    
    async def compare_models(
        self,
        model_a: Any,
        model_b: Any,
        X_val: np.ndarray,
        y_val: np.ndarray,
        task_type: str = 'classification'
    ) -> Dict[str, Any]:
        """
        Compare two models (for A/B testing).
        
        Args:
            model_a: First model
            model_b: Second model
            X_val: Validation features
            y_val: Validation labels
            task_type: Task type
            
        Returns:
            Comparison results
        """
        try:
            metrics_a = await self.evaluate_model(model_a, X_val, y_val, task_type)
            metrics_b = await self.evaluate_model(model_b, X_val, y_val, task_type)
            
            # Determine winner
            key_metric = 'accuracy' if task_type == 'classification' else 'r2'
            winner = 'model_a' if metrics_a.get(key_metric, 0) > metrics_b.get(key_metric, 0) else 'model_b'
            
            return {
                'model_a_metrics': metrics_a,
                'model_b_metrics': metrics_b,
                'winner': winner,
                'improvement': abs(metrics_a.get(key_metric, 0) - metrics_b.get(key_metric, 0)),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error comparing models: {e}")
            return {'error': str(e)}
    
    def load_production_model(self, model_name: str) -> Optional[Any]:
        """
        Load current production model.
        
        Args:
            model_name: Model identifier
            
        Returns:
            Loaded model or None
        """
        try:
            model_path = self.model_dir / f"{model_name}_production.pkl"
            
            if not model_path.exists():
                logger.warning(f"Production model {model_name} not found")
                return None
            
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            
            logger.info(f"✅ Loaded production model: {model_name}")
            return model
            
        except Exception as e:
            logger.error(f"Error loading production model: {e}")
            return None
