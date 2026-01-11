"""
Create quad_risk_metrics table and calculate metrics using direct SQL
"""
import asyncio
import asyncpg
import numpy as np
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def setup_and_calculate():
    """Create table and calculate risk metrics"""
    
    conn = await asyncpg.connect(
        host='localhost',
        port=5438,
        user='postgres',
        password='postgres',
        database='quad_trading'
    )
    
    try:
        # Read and execute SQL to create table
        with open('/home/fortune/Desktop/Python_Projects/quad_trading/trading-test/backend/scripts/create_quad_risk_metrics.sql', 'r') as f:
            sql = f.read()
        
        await conn.execute(sql)
        logger.info("✅ quad_risk_metrics table created")
        
        # Now calculate metrics for each company
        companies = await conn.fetch("SELECT symbol FROM companies ORDER BY symbol")
        logger.info(f"\nCalculating risk metrics for {len(companies)} companies...")
        
        calculated = 0
        for company in companies:
            symbol = company['symbol']
            
            # Get last 252 trading days
            rows = await conn.fetch("""
                SELECT close FROM historical_ohlc
                WHERE symbol = $1 AND interval = '1d'
                ORDER BY timestamp DESC
                LIMIT 252
            """, symbol)
            
            if len(rows) < 30:
                logger.warning(f"  {symbol}: Insufficient data ({len(rows)} days)")
                continue
            
            # Calculate metrics
            prices = np.array([float(row['close']) for row in reversed(rows)])
            returns = np.diff(prices) / prices[:-1] * 100
            
            volatility = float(np.std(returns))
            var_95 = float(np.percentile(returns, 5))
            var_99 = float(np.percentile(returns, 1))
            beta = 1.0
            mean_return = float(np.mean(returns))
            risk_free_rate = 6.0 / 252
            sharpe = (mean_return - risk_free_rate) / volatility if volatility > 0 else 0.0
            
            # Insert
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
            """, symbol, var_95, var_99, beta, volatility, sharpe,
                len(returns), datetime.utcnow())
            
            logger.info(f"  ✅ {symbol}: VaR95={var_95:.2f}%, Vol={volatility:.2f}%, Sharpe={sharpe:.2f}")
            calculated += 1
        
        logger.info(f"\n{'='*60}")
        logger.info(f"✅ Risk metrics calculated for {calculated} companies")
        logger.info(f"{'='*60}")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(setup_and_calculate())
