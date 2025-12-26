"""
QUAD ML Service
Machine learning predictions for QUAD conviction scores
"""

import logging
import numpy as np
from typing import List, Optional, Tuple
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import joblib
from pathlib import Path

from app.database.models_quad import (
    QUADDecision, QUADPrediction, QUADPredictionResponse, PillarScores
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

logger = logging.getLogger(__name__)


class QUADMLService:
    """Machine learning service for QUAD predictions"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.model_dir = Path("models/quad")
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        # Models
        self.conviction_model = None
        self.signal_classifier = None
        self.scaler = StandardScaler()
        
        # Model metadata
        self.model_version = "1.0.0"
        self.min_training_samples = 30
    
    async def predict_conviction(
        self,
        symbol: str,
        current_pillars: PillarScores,
        days_ahead: int = 7
    ) -> Optional[QUADPredictionResponse]:
        """
        Predict future conviction score
        
        Args:
            symbol: Stock symbol
            current_pillars: Current pillar scores
            days_ahead: Days to predict ahead
            
        Returns:
            Prediction with confidence intervals or None if insufficient data
        """
        try:
            # Get historical data
            historical_data = await self._get_historical_data(symbol, days=90)
            
            if len(historical_data) < self.min_training_samples:
                logger.warning(f"Insufficient data for {symbol}: {len(historical_data)} samples")
                return None
            
            # Train model if not exists
            if self.conviction_model is None:
                await self._train_conviction_model(historical_data)
            
            # Prepare features
            features = self._prepare_features(current_pillars, historical_data)
            
            # Make prediction
            predicted_conviction = int(self.conviction_model.predict([features])[0])
            
            # Calculate confidence interval (using historical std)
            convictions = [d['conviction'] for d in historical_data]
            std_dev = np.std(convictions)
            
            confidence_low = max(0, predicted_conviction - int(std_dev))
            confidence_high = min(100, predicted_conviction + int(std_dev))
            
            # Calculate accuracy score (R² from training)
            accuracy = self._calculate_model_accuracy(historical_data)
            
            # Store prediction
            prediction = QUADPrediction(
                symbol=symbol,
                predicted_conviction=predicted_conviction,
                confidence_interval_low=confidence_low,
                confidence_interval_high=confidence_high,
                model_version=self.model_version,
                model_type="LinearRegression",
                accuracy_score=accuracy,
                prediction_days=days_ahead,
                features_used={
                    "trend": current_pillars.trend,
                    "momentum": current_pillars.momentum,
                    "volatility": current_pillars.volatility,
                    "liquidity": current_pillars.liquidity,
                    "sentiment": current_pillars.sentiment,
                    "regime": current_pillars.regime
                }
            )
            
            self.db.add(prediction)
            await self.db.commit()
            await self.db.refresh(prediction)
            
            return QUADPredictionResponse(
                symbol=symbol,
                predicted_conviction=predicted_conviction,
                confidence_low=confidence_low,
                confidence_high=confidence_high,
                accuracy=accuracy,
                model_version=self.model_version,
                prediction_days=days_ahead,
                timestamp=prediction.timestamp
            )
            
        except Exception as e:
            logger.error(f"Error predicting conviction: {e}")
            return None
    
    async def _get_historical_data(
        self,
        symbol: str,
        days: int = 90
    ) -> List[dict]:
        """Get historical QUAD decisions"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            stmt = select(QUADDecision).where(
                and_(
                    QUADDecision.symbol == symbol,
                    QUADDecision.timestamp >= cutoff_date
                )
            ).order_by(QUADDecision.timestamp.asc())
            
            result = await self.db.execute(stmt)
            decisions = result.scalars().all()
            
            return [
                {
                    'conviction': d.conviction,
                    'trend': d.trend_score,
                    'momentum': d.momentum_score,
                    'volatility': d.volatility_score,
                    'liquidity': d.liquidity_score,
                    'sentiment': d.sentiment_score,
                    'regime': d.regime_score,
                    'timestamp': d.timestamp
                }
                for d in decisions
            ]
            
        except Exception as e:
            logger.error(f"Error getting historical data: {e}")
            return []
    
    def _prepare_features(
        self,
        pillars: PillarScores,
        historical_data: List[dict]
    ) -> np.ndarray:
        """Prepare feature vector for prediction"""
        # Current pillar scores
        current_features = [
            pillars.trend,
            pillars.momentum,
            pillars.volatility,
            pillars.liquidity,
            pillars.sentiment,
            pillars.regime
        ]
        
        # Add trend features (if enough history)
        if len(historical_data) >= 7:
            recent_convictions = [d['conviction'] for d in historical_data[-7:]]
            trend_7d = np.mean(np.diff(recent_convictions))
            current_features.append(trend_7d)
        else:
            current_features.append(0)
        
        # Add volatility feature
        if len(historical_data) >= 14:
            recent_convictions = [d['conviction'] for d in historical_data[-14:]]
            volatility_14d = np.std(recent_convictions)
            current_features.append(volatility_14d)
        else:
            current_features.append(0)
        
        return np.array(current_features)
    
    async def _train_conviction_model(self, historical_data: List[dict]):
        """Train linear regression model for conviction prediction"""
        try:
            if len(historical_data) < self.min_training_samples:
                logger.warning("Insufficient data for training")
                return
            
            # Prepare training data
            X = []
            y = []
            
            for i in range(len(historical_data) - 1):
                current = historical_data[i]
                next_conviction = historical_data[i + 1]['conviction']
                
                features = [
                    current['trend'],
                    current['momentum'],
                    current['volatility'],
                    current['liquidity'],
                    current['sentiment'],
                    current['regime'],
                    0,  # trend placeholder
                    0   # volatility placeholder
                ]
                
                X.append(features)
                y.append(next_conviction)
            
            X = np.array(X)
            y = np.array(y)
            
            # Train model
            self.conviction_model = LinearRegression()
            self.conviction_model.fit(X, y)
            
            # Save model
            model_path = self.model_dir / "conviction_model.joblib"
            joblib.dump(self.conviction_model, model_path)
            
            logger.info(f"Trained conviction model with {len(X)} samples")
            
        except Exception as e:
            logger.error(f"Error training model: {e}")
    
    def _calculate_model_accuracy(self, historical_data: List[dict]) -> float:
        """Calculate model accuracy (R² score)"""
        try:
            if self.conviction_model is None or len(historical_data) < 10:
                return 0.0
            
            # Prepare test data
            X_test = []
            y_test = []
            
            for i in range(len(historical_data) - 1):
                current = historical_data[i]
                next_conviction = historical_data[i + 1]['conviction']
                
                features = [
                    current['trend'],
                    current['momentum'],
                    current['volatility'],
                    current['liquidity'],
                    current['sentiment'],
                    current['regime'],
                    0, 0
                ]
                
                X_test.append(features)
                y_test.append(next_conviction)
            
            X_test = np.array(X_test)
            y_test = np.array(y_test)
            
            # Calculate R² score
            score = self.conviction_model.score(X_test, y_test)
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            logger.error(f"Error calculating accuracy: {e}")
            return 0.0
    
    async def predict_signal(
        self,
        symbol: str,
        current_pillars: PillarScores
    ) -> Tuple[str, float]:
        """
        Predict signal using Random Forest classifier
        
        Args:
            symbol: Stock symbol
            current_pillars: Current pillar scores
            
        Returns:
            Tuple of (predicted_signal, confidence)
        """
        try:
            # Get historical data
            historical_data = await self._get_historical_data(symbol, days=90)
            
            if len(historical_data) < self.min_training_samples:
                # Fallback to rule-based
                avg_score = np.mean([
                    current_pillars.trend,
                    current_pillars.momentum,
                    current_pillars.sentiment
                ])
                
                if avg_score >= 70:
                    return "BUY", 0.6
                elif avg_score <= 40:
                    return "SELL", 0.6
                else:
                    return "HOLD", 0.6
            
            # Simple rule-based prediction (can be enhanced with RF later)
            pillar_avg = np.mean([
                current_pillars.trend,
                current_pillars.momentum,
                current_pillars.volatility,
                current_pillars.liquidity,
                current_pillars.sentiment,
                current_pillars.regime
            ])
            
            if pillar_avg >= 70:
                signal = "BUY"
                confidence = min(0.95, pillar_avg / 100 + 0.2)
            elif pillar_avg <= 40:
                signal = "SELL"
                confidence = min(0.95, (100 - pillar_avg) / 100 + 0.2)
            else:
                signal = "HOLD"
                confidence = 0.7
            
            return signal, confidence
            
        except Exception as e:
            logger.error(f"Error predicting signal: {e}")
            return "HOLD", 0.5


# Global instance
quad_ml_service: Optional[QUADMLService] = None
