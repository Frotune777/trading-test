"""
Check why only 1 of 4 IT peers has complete data
"""
import asyncio
import asyncpg

async def check_peer_data():
    conn = await asyncpg.connect(
        host='localhost',
        port=5438,
        user='postgres',
        password='postgres',
        database='quad_trading'
    )
    
    try:
        # Get all IT sector companies
        companies = await conn.fetch("""
            SELECT symbol, name FROM companies 
            WHERE sector = 'Information Technology'
            ORDER BY symbol
        """)
        
        print(f"IT Sector Companies: {len(companies)}")
        print("="*60)
        
        for comp in companies:
            symbol = comp['symbol']
            print(f"\n{symbol}: {comp['name']}")
            
            # Check OHLC data
            ohlc_count = await conn.fetchval("""
                SELECT COUNT(*) FROM historical_ohlc
                WHERE symbol = $1 AND interval = '1d'
            """, symbol)
            print(f"  OHLC records: {ohlc_count}")
            
            # Check risk metrics
            risk = await conn.fetchrow("""
                SELECT volatility_252d, beta_252d, calculated_at
                FROM quad_risk_metrics
                WHERE symbol = $1
            """, symbol)
            
            if risk:
                print(f"  Risk metrics: ✅")
                print(f"    Volatility: {risk['volatility_252d']}")
                print(f"    Beta: {risk['beta_252d']}")
                print(f"    Calculated: {risk['calculated_at']}")
            else:
                print(f"  Risk metrics: ❌ MISSING")
            
            # Check 30-day return calculation
            if ohlc_count >= 30:
                rows = await conn.fetch("""
                    SELECT close FROM historical_ohlc
                    WHERE symbol = $1 AND interval = '1d'
                    ORDER BY timestamp DESC
                    LIMIT 30
                """, symbol)
                
                if len(rows) == 30:
                    start_price = float(rows[-1]['close'])
                    end_price = float(rows[0]['close'])
                    return_30d = ((end_price - start_price) / start_price) * 100
                    print(f"  30-day return: {return_30d:.2f}%")
                else:
                    print(f"  30-day return: ❌ Insufficient data")
            else:
                print(f"  30-day return: ❌ No OHLC data")
            
            # Check market cap
            mc = await conn.fetchval("""
                SELECT market_cap FROM companies WHERE symbol = $1
            """, symbol)
            print(f"  Market cap: {mc}")
            
            # Determine completeness
            has_complete_data = (
                ohlc_count >= 30 and
                risk is not None and
                mc is not None
            )
            print(f"  Complete data: {'✅ YES' if has_complete_data else '❌ NO'}")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check_peer_data())
