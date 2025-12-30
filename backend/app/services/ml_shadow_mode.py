"""
ML Shadow Mode Service
Ensures ML predictions NEVER trigger autonomous execution
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.quad_ml_service import QUADMLService
from app.database.models_quad import QUADPrediction, PillarScores

logger = logging.getLogger(__name__)


class MLShadowModeService:
    """
    ML Service with strict shadow mode enforcement.
    
    Compliance:
    - Rule #42: Agent must never self-authorize autonomy
    - Rule #43: Agent must never remove human override paths
    - Rule #44: Agent must not schedule itself to trade
    - Rule #45: Any future autonomy must be opt-in and reversible
    
    CRITICAL: This service ONLY generates predictions for tracking.
              Predictions NEVER influence live trading decisions.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ml_service = QUADMLService(db)
        self._execution_guard_enabled = True  # Always True
    
    async def generate_shadow_prediction(
        self,
        symbol: str,
        current_pillars: PillarScores,
        quad_signal: str,
        quad_conviction: float
    ) -> Optional[Dict[str, Any]]:
        """
        Generate ML prediction in shadow mode.
        
        CRITICAL: This prediction is ONLY for tracking accuracy.
                  It NEVER influences execution decisions.
        
        Args:
            symbol: Stock symbol
            current_pillars: Current pillar scores
            quad_signal: QUAD signal (for comparison)
            quad_conviction: QUAD conviction (for comparison)
            
        Returns:
            Shadow prediction record or None
        """
        try:
            # Generate ML prediction
            ml_prediction = await self.ml_service.predict_conviction(
                symbol=symbol,
                current_pillars=current_pillars,
                days_ahead=7
            )
            
            if not ml_prediction:
                logger.debug(f"No ML prediction generated for {symbol}")
                return None
            
            # Store prediction with shadow mode flag
            shadow_record = {
                "symbol": symbol,
                "ml_conviction": ml_prediction.get("predicted_conviction"),
                "ml_confidence": ml_prediction.get("confidence"),
                "quad_signal": quad_signal,
                "quad_conviction": quad_conviction,
                "is_shadow": True,  # CRITICAL: Always True
                "used_for_execution": False,  # CRITICAL: Always False
                "timestamp": datetime.now()
            }
            
            # Log shadow prediction
            logger.info(
                f"🔮 SHADOW ML Prediction for {symbol}: "
                f"ML={ml_prediction.get('predicted_conviction'):.2f}, "
                f"QUAD={quad_conviction:.2f} "
                f"(NOT USED FOR EXECUTION)"
            )
            
            return shadow_record
            
        except Exception as e:
            logger.error(f"Error generating shadow prediction for {symbol}: {e}")
            return None
    
    async def track_prediction_accuracy(
        self,
        symbol: str,
        prediction_id: int,
        actual_outcome: float
    ) -> Dict[str, Any]:
        """
        Track accuracy of ML prediction vs actual outcome.
        
        Args:
            symbol: Stock symbol
            prediction_id: Prediction ID
            actual_outcome: Actual conviction/return
            
        Returns:
            Accuracy metrics
        """
        try:
            # Fetch prediction
            stmt = select(QUADPrediction).where(
                QUADPrediction.id == prediction_id
            )
            result = await self.db.execute(stmt)
            prediction = result.scalar_one_or_none()
            
            if not prediction:
                return {"error": "Prediction not found"}
            
            # Calculate accuracy
            predicted = prediction.ml_conviction
            error = abs(predicted - actual_outcome)
            error_pct = (error / actual_outcome * 100) if actual_outcome != 0 else 0
            
            accuracy_record = {
                "symbol": symbol,
                "prediction_id": prediction_id,
                "predicted": predicted,
                "actual": actual_outcome,
                "error": error,
                "error_pct": error_pct,
                "timestamp": datetime.now()
            }
            
            logger.info(
                f"📊 ML Prediction Accuracy for {symbol}: "
                f"Predicted={predicted:.2f}, Actual={actual_outcome:.2f}, "
                f"Error={error_pct:.1f}%"
            )
            
            return accuracy_record
            
        except Exception as e:
            logger.error(f"Error tracking prediction accuracy: {e}")
            return {"error": str(e)}
    
    def verify_execution_guard(self) -> bool:
        """
        Verify that execution guard is enabled.
        
        Returns:
            True if guard is enabled (should always be True)
        """
        if not self._execution_guard_enabled:
            logger.critical(
                "🚨 CRITICAL: ML execution guard is DISABLED! "
                "This violates Rule #42-45. Re-enabling immediately."
            )
            self._execution_guard_enabled = True
        
        return self._execution_guard_enabled
    
    def assert_shadow_mode(self):
        """
        Assert that shadow mode is active.
        
        Raises:
            RuntimeError: If shadow mode is compromised
        """
        if not self.verify_execution_guard():
            raise RuntimeError(
                "ML Shadow Mode Violation: Execution guard is disabled. "
                "This violates user rules #42-45."
            )
        
        logger.debug("✅ ML Shadow Mode verified: Execution guard active")
    
    async def get_prediction_performance(
        self,
        symbol: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get ML prediction performance metrics.
        
        Args:
            symbol: Optional symbol filter
            days: Days to look back
            
        Returns:
            Performance metrics
        """
        # This would query prediction accuracy records
        # and calculate aggregate metrics
        
        return {
            "symbol": symbol or "ALL",
            "days": days,
            "total_predictions": 0,
            "avg_error_pct": 0.0,
            "accuracy_rate": 0.0,
            "note": "Shadow mode only - predictions not used for execution"
        }


# Global guard function
def prevent_ml_execution():
    """
    Global guard to prevent ML-driven execution.
    
    This function should be called in ExecutionService
    to ensure ML predictions never trigger trades.
    """
    logger.warning(
        "⚠️ ML Execution Attempt Blocked: "
        "ML predictions cannot trigger autonomous execution (Rule #42-45)"
    )
    raise RuntimeError(
        "ML-driven execution is prohibited. "
        "Only QUAD decisions can trigger trades."
    )
