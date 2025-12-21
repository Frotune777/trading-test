import joblib
import pandas as pd
from typing import Dict, Any
import os

class PredictorService:
    """
    Handles model loading and inference for direction and volatility.
    """
    def __init__(self):
        self.models_path = "ml/models/saved_models/"
        self.direction_model = self._load_model("direction_model.joblib")
        self.volatility_model = self._load_model("volatility_model.joblib")

    def _load_model(self, filename: str):
        path = os.path.join(self.models_path, filename)
        if os.path.exists(path):
            return joblib.load(path)
        return None # Return None if not trained yet

    def predict(self, feature_row: pd.DataFrame) -> Dict[str, Any]:
        """Generate all predictions for a given feature set"""
        prediction = {
            "direction": "UNKNOWN",
            "confidence": 0.0,
            "target_price": 0.0,
            "volatility": 0.0
        }
        
        if self.direction_model:
            # ensemble or xgboost prediction
            pred_class = self.direction_model.predict(feature_row)[0]
            probs = self.direction_model.predict_proba(feature_row)[0]
            prediction["direction"] = "UP" if pred_class == 1 else "DOWN"
            prediction["confidence"] = float(max(probs))
            
        return prediction
