"""
Calculate and populate risk metrics for all companies with OHLC data
Calculates: VaR, Beta, Volatility, Sharpe Ratio
"""
import asyncio
import asyncpg
import numpy as np
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def calculate_risk_metrics():
    """Calculate risk metrics for all companies"""
    
    conn = await asyncpg.connect(
        host='localhost',
        port=5438,
        user='postgres',
        password='postgres',
        database='quad_trading'
    )
    
    try:
        # Get all companies
        companies = await conn.fetch("SELECT symbol FROM companies ORDER BY symbol")
        logger.info(f"Calculating risk metrics for {len(companies)} companies")
        
        for company in companies:
            symbol = company['symbol']
            logger.info(f"\nProcessing {symbol}...")
            
            try:
                # Get last 252 trading days (1 year) of data
                rows = await conn.fetch("""
                    SELECT close, timestamp
                    FROM historical_ohlc
                    WHERE symbol = $1 AND interval = '1d'
                    ORDER BY timestamp DESC
                    LIMIT 252
                """, symbol)
                
                if len(rows) < 30:
                    logger.warning(f"  Insufficient data for {symbol} ({len(rows)} days)")
                    continue
                
                # Calculate returns
                prices = np.array([float(row['close']) for row in reversed(rows)])
                returns = np.diff(prices) / prices[:-1] * 100  # Percentage returns
                
                # Calculate metrics
                volatility = float(np.std(returns))
                mean_return = float(np.mean(returns))
                
                # VaR (Value at Risk) - 95% and 99% confidence
                var_95 = float(np.percentile(returns, 5))
                var_99 = float(np.percentile(returns, 1))
                
                # Beta (simplified - using market proxy as 1.0 for now)
                # In production, would calculate against actual market index
                beta = 1.0
                
                # Sharpe Ratio (simplified - assuming risk-free rate of 6%)
                risk_free_rate = 6.0 / 252  # Daily risk-free rate
                sharpe = (mean_return - risk_free_rate) / volatility if volatility > 0 else 0.0
                
                # Insert into quad_risk_metrics table
                await conn.execute("""
                    INSERT INTO quad_risk_metrics (
                        symbol, var_95_30d, var_99_30d, var_95_60d, var_99_60d,
                        var_95_90d, var_99_90d, beta_30d, beta_60d, beta_252d,
                        volatility_30d, volatility_60d, volatility_252d,
                        sharpe_30d, sharpe_60d, sharpe_252d,
                        data_points_used, calculated_at
                    ) VALUES (
                        $1, $2, $3, $2, $3, $2, $3,
                        $4, $4, $4,
                        $5, $5, $5,
                        $6, $6, $6,
                        $7, $8
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        var_95_30d = EXCLUDED.var_95_30d,
                        var_99_30d = EXCLUDED.var_99_30d,
                        beta_252d = EXCLUDED.beta_252d,
                        volatility_252d = EXCLUDED.volatility_252d,
                        sharpe_252d = EXCLUDED.sharpe_252d,
                        calculated_at = EXCLUDED.calculated_at
                """, symbol, var_95, var_99, beta, volatility, sharpe,
                    len(returns), datetime.utcnow())
                
                logger.info(f"  ✅ {symbol}: VaR95={var_95:.2f}%, Vol={volatility:.2f}%, Sharpe={sharpe:.2f}")
                
            except Exception as e:
                logger.error(f"  ❌ Error calculating metrics for {symbol}: {e}")
                continue
        
        # Verify results
        count = await conn.fetchval("SELECT COUNT(*) FROM quad_risk_metrics")
        logger.info(f"\n{'='*60}")
        logger.info(f"Risk metrics calculated for {count} companies")
        logger.info(f"{'='*60}")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(calculate_risk_metrics())
