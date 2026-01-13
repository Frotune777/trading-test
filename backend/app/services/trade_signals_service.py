"""
Trade Signals Service

Calculates actionable trade parameters:
- Support and Resistance (S/R) zones
- Stop-Loss (SL) and Take-Profit (TP) levels
- Entry/Exit recommendations
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select

from app.database.models_historical import PriceHistory
from app.database.models_quad import QUADDecision, PillarScores
from app.services.risk_metrics_service import RiskMetricsService

logger = logging.getLogger(__name__)

class TradeSignalsService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.risk_service = RiskMetricsService(db)

    async def get_trade_setup(self, symbol: str, current_price: Optional[float] = None) -> Dict[str, Any]:
        """
        Generate a complete trade setup for a symbol
        """
        logger.info(f"Generating trade setup for {symbol}")
        
        # 1. Fetch historical data for indicators
        df = await self._get_price_history(symbol, limit=100)
        if df.empty or len(df) < 20:
            logger.warning(f"Insufficient data for trade setup: {symbol}")
            return {"error": "Insufficient data"}

        if current_price is None:
            current_price = float(df.iloc[-1]['close'])

        # 2. Calculate Pivot Points (Standard & Fibonacci)
        pivots = self._calculate_pivots(df)
        
        # 3. Calculate Volatility-based Stop Loss (ATR)
        # Using 14-period ATR
        high_prices = df['high'].astype(float).values
        low_prices = df['low'].astype(float).values
        close_prices = df['close'].astype(float).values
        
        import talib
        atr = talib.ATR(high_prices, low_prices, close_prices, timeperiod=14)[-1]
        
        # 4. Get VaR for risk-based adjustment
        risk_metrics = await self.risk_service.get_latest_metrics(symbol)
        var_loss = 0.02 # Default 2%
        if risk_metrics and risk_metrics.var_95_30d:
            var_loss = abs(float(risk_metrics.var_95_30d)) / 100

        # 5. Generate BUY/SELL logic based on price relative to pivot
        # (This is simplified, usually we take the signal from QUAD)
        pivot_point = pivots['standard']['pivot']
        
        # Define levels
        support_zones = [
            {"label": "S1", "level": pivots['fibonacci']['s1'], "strength": "Moderate"},
            {"label": "S2", "level": pivots['fibonacci']['s2'], "strength": "Strong"},
            {"label": "S3", "level": pivots['fibonacci']['s3'], "strength": "Very Strong"},
        ]
        
        resistance_zones = [
            {"label": "R1", "level": pivots['fibonacci']['r1'], "strength": "Moderate"},
            {"label": "R2", "level": pivots['fibonacci']['r2'], "strength": "Strong"},
            {"label": "R3", "level": pivots['fibonacci']['r3'], "strength": "Very Strong"},
        ]

        # Calculate SL and TP targets
        # Assuming we want a general long setup for demonstration if price > pivot
        # In a real scenario, this would be guided by the QUAD signal
        
        sl_atr = current_price - (atr * 1.5)
        sl_var = current_price * (1 - var_loss)
        stop_loss = max(sl_atr, sl_var) # Conservative SL
        
        risk = current_price - stop_loss
        take_profit_1 = current_price + (risk * 1.5)
        take_profit_2 = current_price + (risk * 3.0)

        # 6. Position Sizing
        # Kelly Criterion: K% = W - [(1-W)/R]
        # Assuming win rate W=0.6 and R=1.5
        win_rate = 0.6
        rr_ratio = 1.5
        kelly_pct = win_rate - ((1 - win_rate) / rr_ratio)
        
        account_size = 1000000 # Default 10L
        risk_per_trade_pct = 0.01 # Default 1%
        
        # Risk-based sizing: Position = (Account * Risk%) / (Entry - StopLoss)
        if risk > 0:
            shares = (account_size * risk_per_trade_pct) / risk
        else:
            shares = 0

        # 7. Fetch latest QUAD Decision for Reasoning
        stmt = select(QUADDecision).where(
            QUADDecision.symbol == symbol
        ).order_by(QUADDecision.timestamp.desc()).limit(1)
        
        decision_result = await self.db.execute(stmt)
        latest_decision = decision_result.scalar_one_or_none()
        
        analysis_data = None
        if latest_decision:
            analysis_data = {
                "signal": latest_decision.signal,
                "conviction": latest_decision.conviction,
                "reasoning_summary": latest_decision.reasoning_summary,
                "pillars": {
                    "trend": latest_decision.trend_score,
                    "momentum": latest_decision.momentum_score,
                    "volatility": latest_decision.volatility_score,
                    "liquidity": latest_decision.liquidity_score,
                    "sentiment": latest_decision.sentiment_score,
                    "regime": latest_decision.regime_score
                }
            }

        return {
            "symbol": symbol,
            "current_price": current_price,
            "analysis": analysis_data,
            "pivots": pivots,
            "zones": {
                "support": support_zones,
                "resistance": resistance_zones
            },
            "parameters": {
                "stop_loss": round(stop_loss, 2),
                "take_profit_1": round(take_profit_1, 2),
                "take_profit_2": round(take_profit_2, 2),
                "risk_reward_ratio": rr_ratio,
                "atr": round(float(atr), 2),
                "var_risk": round(var_loss * 100, 2)
            },
            "position_sizing": {
                "account_size": account_size,
                "risk_per_trade_pct": risk_per_trade_pct * 100,
                "recommended_shares": int(shares),
                "kelly_allocation_pct": round(kelly_pct * 100, 2),
                "capital_required": round(shares * current_price, 2)
            }
        }

    async def _get_price_history(self, symbol: str, limit: int = 100) -> pd.DataFrame:
        """Fetch price history from PostgreSQL"""
        result = await self.db.execute(
            text("""
                SELECT open, high, low, close, volume, timestamp as date
                FROM historical_ohlc
                WHERE symbol = :symbol
                AND interval = '1d'
                ORDER BY timestamp DESC
                LIMIT :limit
            """),
            {"symbol": symbol, "limit": limit}
        )
        rows = result.fetchall()
        if not rows:
            return pd.DataFrame()
        
        # Reverse to chronological order for indicators
        df = pd.DataFrame(rows, columns=['open', 'high', 'low', 'close', 'volume', 'date'])
        return df.iloc[::-1].reset_index(drop=True)

    def _calculate_pivots(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate Pivot Points based on the previous candle (daily)
        """
        # In our price_history, the latest row is the current day 
        # (or last closed day if after hours)
        # For daily pivots, we use the High, Low, Close of the PREVIOUS day.
        
        prev_day = df.iloc[-2] if len(df) >= 2 else df.iloc[-1]
        H = float(prev_day['high'])
        L = float(prev_day['low'])
        C = float(prev_day['close'])
        
        # Standard Pivot
        P = (H + L + C) / 3
        S1 = (2 * P) - H
        S2 = P - (H - L)
        R1 = (2 * P) - L
        R2 = P + (H - L)
        
        # Fibonacci Pivot
        range_val = H - L
        fib_r1 = P + (0.382 * range_val)
        fib_r2 = P + (0.618 * range_val)
        fib_r3 = P + (1.000 * range_val)
        fib_s1 = P - (0.382 * range_val)
        fib_s2 = P - (0.618 * range_val)
        fib_s3 = P - (1.000 * range_val)
        
        return {
            "standard": {
                "pivot": round(P, 2),
                "s1": round(S1, 2),
                "s2": round(S2, 2),
                "r1": round(R1, 2),
                "r2": round(R2, 2)
            },
            "fibonacci": {
                "pivot": round(P, 2),
                "s1": round(fib_s1, 2),
                "s2": round(fib_s2, 2),
                "s3": round(fib_s3, 2),
                "r1": round(fib_r1, 2),
                "r2": round(fib_r2, 2),
                "r3": round(fib_r3, 2)
            }
        }
