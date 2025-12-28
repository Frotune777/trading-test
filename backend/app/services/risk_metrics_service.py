"""
Risk Metrics Service

Calculates risk metrics including:
- Value at Risk (VaR) using historical simulation
- Beta vs market (NIFTY 50)
- Sharpe Ratio (risk-adjusted returns)
- Volatility (annualized standard deviation)
"""

import logging
import numpy as np
from typing import List, Optional, Dict, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.database.models_quad import RiskMetrics
from app.database.models_historical import PriceHistory

logger = logging.getLogger(__name__)

# Constants
RISK_FREE_RATE = 0.065  # 6.5% - India 10Y bond yield
TRADING_DAYS_PER_YEAR = 252


class RiskMetricsService:
    """Service for calculating and storing risk metrics"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        
    async def calculate_var(
        self,
        symbol: str,
        days: int = 30,
        confidence: float = 0.95
    ) -> Optional[float]:
        """
        Calculate Value at Risk using historical simulation
        
        VaR represents the maximum expected loss over a given time period
        at a specified confidence level.
        
        Args:
            symbol: Stock symbol
            days: Historical window (30, 60, 90)
            confidence: Confidence level (0.95 or 0.99)
            
        Returns:
            VaR as percentage (negative value indicates loss)
            e.g., -2.5 means 95% confident daily loss won't exceed 2.5%
        """
        try:
            # Fetch historical prices
            returns = await self._get_daily_returns(symbol, days)
            
            if len(returns) < 10:
                logger.warning(f"Insufficient data for VaR calculation: {symbol} ({len(returns)} days)")
                return None
            
            # Sort returns from worst to best
            sorted_returns = np.sort(returns)
            
            # Find the return at the confidence level
            # For 95% confidence, we want the 5th percentile (worst 5% of days)
            index = int((1 - confidence) * len(sorted_returns))
            var = sorted_returns[index] * 100  # Convert to percentage
            
            logger.info(f"VaR for {symbol} ({days}d, {confidence*100}%): {var:.2f}%")
            return float(var)
            
        except Exception as e:
            logger.error(f"Error calculating VaR for {symbol}: {e}", exc_info=True)
            return None
    
    async def calculate_beta(
        self,
        symbol: str,
        market_symbol: str = "NIFTY",
        days: int = 252
    ) -> Optional[float]:
        """
        Calculate Beta - measure of stock's volatility relative to market
        
        Beta = Covariance(stock, market) / Variance(market)
        
        Interpretation:
        - Beta > 1: More volatile than market
        - Beta = 1: Moves with market
        - Beta < 1: Less volatile than market
        - Beta < 0: Inverse correlation
        
        Args:
            symbol: Stock symbol
            market_symbol: Market index (default: NIFTY)
            days: Historical window (typically 252 for 1 year)
            
        Returns:
            Beta value
        """
        try:
            # Get stock and market returns
            stock_returns = await self._get_daily_returns(symbol, days)
            market_returns = await self._get_daily_returns(market_symbol, days)
            
            if len(stock_returns) < 30 or len(market_returns) < 30:
                logger.warning(f"Insufficient data for Beta calculation: {symbol}")
                return None
            
            # Align the arrays (use minimum length)
            min_len = min(len(stock_returns), len(market_returns))
            stock_returns = stock_returns[:min_len]
            market_returns = market_returns[:min_len]
            
            # Calculate covariance and variance
            covariance = np.cov(stock_returns, market_returns)[0][1]
            market_variance = np.var(market_returns)
            
            if market_variance == 0:
                logger.warning(f"Market variance is zero for Beta calculation")
                return None
            
            beta = covariance / market_variance
            
            logger.info(f"Beta for {symbol} ({days}d): {beta:.2f}")
            return float(beta)
            
        except Exception as e:
            logger.error(f"Error calculating Beta for {symbol}: {e}", exc_info=True)
            return None
    
    async def calculate_sharpe_ratio(
        self,
        symbol: str,
        days: int = 252,
        risk_free_rate: float = RISK_FREE_RATE
    ) -> Optional[float]:
        """
        Calculate Sharpe Ratio - risk-adjusted return
        
        Sharpe = (Mean Return - Risk Free Rate) / Std Dev of Returns
        
        Interpretation:
        - Sharpe > 2.0: Excellent
        - Sharpe 1.0-2.0: Good
        - Sharpe 0.5-1.0: Acceptable
        - Sharpe < 0.5: Poor
        
        Args:
            symbol: Stock symbol
            days: Historical window
            risk_free_rate: Annual risk-free rate (default: 6.5%)
            
        Returns:
            Sharpe ratio (annualized)
        """
        try:
            returns = await self._get_daily_returns(symbol, days)
            
            if len(returns) < 30:
                logger.warning(f"Insufficient data for Sharpe calculation: {symbol}")
                return None
            
            # Annualize the returns
            mean_return = np.mean(returns) * TRADING_DAYS_PER_YEAR
            std_dev = np.std(returns) * np.sqrt(TRADING_DAYS_PER_YEAR)
            
            if std_dev == 0:
                logger.warning(f"Standard deviation is zero for Sharpe calculation")
                return None
            
            sharpe = (mean_return - risk_free_rate) / std_dev
            
            logger.info(f"Sharpe Ratio for {symbol} ({days}d): {sharpe:.2f}")
            return float(sharpe)
            
        except Exception as e:
            logger.error(f"Error calculating Sharpe for {symbol}: {e}", exc_info=True)
            return None
    
    async def calculate_volatility(
        self,
        symbol: str,
        days: int = 30
    ) -> Optional[float]:
        """
        Calculate annualized volatility (standard deviation of returns)
        
        Args:
            symbol: Stock symbol
            days: Historical window
            
        Returns:
            Annualized volatility as percentage
        """
        try:
            returns = await self._get_daily_returns(symbol, days)
            
            if len(returns) < 10:
                logger.warning(f"Insufficient data for volatility calculation: {symbol}")
                return None
            
            # Annualize the standard deviation
            volatility = np.std(returns) * np.sqrt(TRADING_DAYS_PER_YEAR) * 100
            
            logger.info(f"Volatility for {symbol} ({days}d): {volatility:.2f}%")
            return float(volatility)
            
        except Exception as e:
            logger.error(f"Error calculating volatility for {symbol}: {e}", exc_info=True)
            return None
    
    async def calculate_all_metrics(self, symbol: str) -> Optional[RiskMetrics]:
        """
        Calculate all risk metrics for a symbol and store in database
        
        Args:
            symbol: Stock symbol
            
        Returns:
            RiskMetrics object with all calculated values
        """
        logger.info(f"Calculating all risk metrics for {symbol}")
        
        try:
            # Calculate VaR for different windows and confidence levels
            var_95_30d = await self.calculate_var(symbol, 30, 0.95)
            var_99_30d = await self.calculate_var(symbol, 30, 0.99)
            var_95_60d = await self.calculate_var(symbol, 60, 0.95)
            var_99_60d = await self.calculate_var(symbol, 60, 0.99)
            var_95_90d = await self.calculate_var(symbol, 90, 0.95)
            var_99_90d = await self.calculate_var(symbol, 90, 0.99)
            
            # Calculate Beta for different windows
            beta_30d = await self.calculate_beta(symbol, days=30)
            beta_60d = await self.calculate_beta(symbol, days=60)
            beta_252d = await self.calculate_beta(symbol, days=252)
            
            # Calculate Sharpe Ratio
            sharpe_30d = await self.calculate_sharpe_ratio(symbol, days=30)
            sharpe_60d = await self.calculate_sharpe_ratio(symbol, days=60)
            sharpe_252d = await self.calculate_sharpe_ratio(symbol, days=252)
            
            # Calculate Volatility
            volatility_30d = await self.calculate_volatility(symbol, days=30)
            volatility_60d = await self.calculate_volatility(symbol, days=60)
            volatility_252d = await self.calculate_volatility(symbol, days=252)
            
            # Get data points used
            returns = await self._get_daily_returns(symbol, 252)
            data_points = len(returns)
            
            # Create RiskMetrics object
            risk_metrics = RiskMetrics(
                symbol=symbol,
                calculated_at=datetime.utcnow(),
                var_95_30d=var_95_30d,
                var_99_30d=var_99_30d,
                var_95_60d=var_95_60d,
                var_99_60d=var_99_60d,
                var_95_90d=var_95_90d,
                var_99_90d=var_99_90d,
                beta_30d=beta_30d,
                beta_60d=beta_60d,
                beta_252d=beta_252d,
                sharpe_30d=sharpe_30d,
                sharpe_60d=sharpe_60d,
                sharpe_252d=sharpe_252d,
                volatility_30d=volatility_30d,
                volatility_60d=volatility_60d,
                volatility_252d=volatility_252d,
                data_points_used=data_points
            )
            
            # Save to database
            self.db.add(risk_metrics)
            await self.db.commit()
            await self.db.refresh(risk_metrics)
            
            logger.info(f"✅ Risk metrics calculated and saved for {symbol}")
            return risk_metrics
            
        except Exception as e:
            logger.error(f"Error calculating all metrics for {symbol}: {e}", exc_info=True)
            await self.db.rollback()
            return None
    
    async def get_latest_metrics(self, symbol: str) -> Optional[RiskMetrics]:
        """
        Get the most recent risk metrics for a symbol
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Latest RiskMetrics or None
        """
        try:
            result = await self.db.execute(
                select(RiskMetrics)
                .where(RiskMetrics.symbol == symbol)
                .order_by(RiskMetrics.calculated_at.desc())
                .limit(1)
            )
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error fetching risk metrics for {symbol}: {e}")
            return None
    
    async def _get_daily_returns(self, symbol: str, days: int) -> np.ndarray:
        """
        Fetch historical prices and calculate daily returns
        
        Args:
            symbol: Stock symbol
            days: Number of days to fetch
            
        Returns:
            Array of daily returns (percentage change)
        """
        try:
            # Fetch price history
            cutoff_date = datetime.utcnow() - timedelta(days=days + 10)  # Extra buffer
            
            result = await self.db.execute(
                select(PriceHistory)
                .where(
                    and_(
                        PriceHistory.symbol == symbol,
                        PriceHistory.date >= cutoff_date
                    )
                )
                .order_by(PriceHistory.date.asc())
            )
            
            prices = result.scalars().all()
            
            if len(prices) < 2:
                logger.warning(f"No price history found for {symbol}")
                return np.array([])
            
            # Calculate daily returns
            close_prices = np.array([float(p.close) for p in prices])
            returns = np.diff(close_prices) / close_prices[:-1]
            
            # Return only the requested number of days
            return returns[-days:] if len(returns) > days else returns
            
        except Exception as e:
            logger.error(f"Error fetching returns for {symbol}: {e}", exc_info=True)
            return np.array([])
    
    @staticmethod
    def get_var_interpretation(var: float, confidence: float) -> Dict[str, str]:
        """Get human-readable interpretation of VaR"""
        risk_level = "LOW" if var > -2 else "MODERATE" if var > -4 else "HIGH"
        
        return {
            "value": f"{var:.2f}%",
            "confidence": f"{confidence*100:.0f}%",
            "interpretation": f"{confidence*100:.0f}% confident daily loss won't exceed {abs(var):.2f}%",
            "risk_level": risk_level
        }
    
    @staticmethod
    def get_beta_interpretation(beta: float) -> Dict[str, str]:
        """Get human-readable interpretation of Beta"""
        if beta > 1.2:
            label = "High Volatility"
            desc = f"Stock moves {(beta-1)*100:.0f}% more than market"
        elif beta > 0.8:
            label = "Market Aligned"
            desc = "Stock moves with market"
        elif beta > 0:
            label = "Low Volatility"
            desc = f"Stock moves {(1-beta)*100:.0f}% less than market"
        else:
            label = "Inverse Correlation"
            desc = "Stock moves opposite to market"
        
        return {
            "value": f"{beta:.2f}",
            "label": label,
            "description": desc
        }
    
    @staticmethod
    def get_sharpe_interpretation(sharpe: float) -> Dict[str, str]:
        """Get human-readable interpretation of Sharpe Ratio"""
        if sharpe > 2.0:
            rating = "Excellent"
        elif sharpe > 1.0:
            rating = "Good"
        elif sharpe > 0.5:
            rating = "Acceptable"
        else:
            rating = "Poor"
        
        return {
            "value": f"{sharpe:.2f}",
            "rating": rating,
            "description": f"Risk-adjusted return is {rating.lower()}"
        }
