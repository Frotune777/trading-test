from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.database.models_quad import RiskMetrics
import logging

logger = logging.getLogger(__name__)

class RiskService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_historical_var(self, symbol: str, days: int = 30, confidence: float = 0.95) -> Optional[float]:
        """
        Calculate Historical Value at Risk (VaR)
        
        Args:
            symbol: Stock symbol
            days: Lookback period for historical simulation
            confidence: Confidence level (e.g., 0.95, 0.99)
            
        Returns:
            VaR as a positive percentage (e.g., 2.5 means 2.5% potential loss)
        """
        try:
            # Fetch historical price data
            result = await self.db.execute(
                text("""
                    SELECT close 
                    FROM price_history 
                    WHERE symbol = :symbol 
                    ORDER BY date DESC 
                    LIMIT :limit
                """),
                {"symbol": symbol.upper(), "limit": days + 1}
            )
            rows = result.fetchall()
            
            if len(rows) < days:
                logger.warning(f"Insufficient data for VaR calculation for {symbol}. Need {days}, got {len(rows)}")
                return None
                
            prices = [float(r[0]) for r in rows][::-1] # Chronological order
            
            # Calculate daily returns
            returns = []
            for i in range(1, len(prices)):
                ret = (prices[i] - prices[i-1]) / prices[i-1]
                returns.append(ret)
                
            if not returns:
                return None
                
            # Historical Simulation
            sorted_returns = sorted(returns)
            index = int((1 - confidence) * len(sorted_returns))
            var_value = sorted_returns[index]
            
            # Return as positive percentage (absolute risk)
            return abs(var_value) * 100
            
        except Exception as e:
            logger.error(f"Error calculating VaR for {symbol}: {e}")
            return None

    async def update_risk_metrics(self, symbol: str) -> Optional[RiskMetrics]:
        """
        Calculate and store all risk metrics for a symbol
        """
        try:
            # Calculate VaR
            var_95_30d = await self.calculate_historical_var(symbol, 30, 0.95)
            var_99_30d = await self.calculate_historical_var(symbol, 30, 0.99)
            var_95_60d = await self.calculate_historical_var(symbol, 60, 0.95)
            var_99_60d = await self.calculate_historical_var(symbol, 60, 0.99)
            
            # Calculate Volatility (Standard Deviation of returns * sqrt(252))
            # Implementation placeholder for now, reusing VaR fetch logic would be cleaner but keeping distinct for clarity
            volatility = 0.0 # TODO: Implement properly
            
            # Store/Update in DB
            metric = RiskMetrics(
                symbol=symbol.upper(),
                calculated_at=datetime.utcnow(),
                var_95_30d=var_95_30d,
                var_99_30d=var_99_30d,
                var_95_60d=var_95_60d,
                var_99_60d=var_99_60d,
                volatility=volatility
                # beta and sharpe to be added in subsequent tasks
            )
            
            self.db.add(metric)
            await self.db.commit()
            await self.db.refresh(metric)
            
            logger.info(f"Updated risk metrics for {symbol}")
            return metric
            
        except Exception as e:
            logger.error(f"Failed to update risk metrics for {symbol}: {e}")
            await self.db.rollback()
            return None
