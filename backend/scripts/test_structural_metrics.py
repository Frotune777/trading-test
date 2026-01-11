"""
Test the _get_structural_metrics logic directly
"""
import asyncio
import asyncpg
from datetime import datetime, timedelta

async def test_structural_metrics():
    conn = await asyncpg.connect(
        host='localhost',
        port=5438,
        user='postgres',
        password='postgres',
        database='quad_trading'
    )
    
    try:
        symbol = "WIPRO"
        print(f"Testing structural metrics for {symbol}")
        print("="*60)
        
        # Test 30-day return calculation (mimicking the service logic)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        print(f"\n30 days ago: {thirty_days_ago}")
        
        rows = await conn.fetch("""
            SELECT close, timestamp FROM historical_ohlc
            WHERE symbol = $1 AND timestamp >= $2 AND interval = '1d'
            ORDER BY timestamp ASC
        """, symbol, thirty_days_ago)
        
        print(f"OHLC records found: {len(rows)}")
        if rows:
            print(f"First record: {rows[0]['timestamp']} - {rows[0]['close']}")
            print(f"Last record: {rows[-1]['timestamp']} - {rows[-1]['close']}")
            
            if len(rows) >= 2:
                return_30d = ((float(rows[-1]['close']) - float(rows[0]['close'])) / float(rows[0]['close'])) * 100
                print(f"30-day return: {return_30d:.2f}%")
        
        # Test risk metrics
        risk = await conn.fetchrow("""
            SELECT volatility_252d, volatility_60d, volatility_30d,
                   beta_252d, beta_60d, beta_30d
            FROM quad_risk_metrics
            WHERE symbol = $1
        """, symbol)
        
        if risk:
            print(f"\nRisk metrics found:")
            print(f"  volatility_252d: {risk['volatility_252d']}")
            print(f"  volatility_60d: {risk['volatility_60d']}")
            print(f"  volatility_30d: {risk['volatility_30d']}")
            print(f"  beta_252d: {risk['beta_252d']}")
            
            # Test fallback logic
            volatility = risk['volatility_252d'] or risk['volatility_60d'] or risk['volatility_30d']
            beta = risk['beta_252d'] or risk['beta_60d'] or risk['beta_30d']
            print(f"\nSelected volatility: {volatility}")
            print(f"Selected beta: {beta}")
        else:
            print("\n❌ No risk metrics found")
        
        # Test market cap
        mc = await conn.fetchval("""
            SELECT market_cap FROM companies WHERE symbol = $1
        """, symbol)
        print(f"\nMarket cap: {mc}")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(test_structural_metrics())
