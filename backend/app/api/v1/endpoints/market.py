from typing import List, Dict, Any, Optional
import asyncio
import pandas as pd
import yfinance as yf
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db
from fastapi import APIRouter, HTTPException, Depends, Query
from app.data_sources.nse_utils import NseUtils
from app.core.openalgo_client import openalgo

router = APIRouter()
nse = NseUtils()

@router.get("/status")
@router.get("/breadth")
async def get_market_breadth():
    """
    Get market advance/decline ratio using Real-Time OpenAlgo data for NIFTY 50.
    """
    try:
        # 1. Fetch NIFTY 50 components (Using a known list for now, or fetch from index definition)
        # Ideally, we should fetch index constituents from OpenAlgo, but if not available, we use a static list
        # We check a sample of major stocks to simulate breadth if full index scanning is too heavy.
        
        nifty_50_symbols = [
            "RELIANCE", "TCS", "HDFCBANK", "ICICIBANK", "INFY", "SBIN", "BHARTIARTL", "ITC", "L&T", "KOTAKBANK",
            "AXISBANK", "HCLTECH", "ADANIENT", "ASIANPAINT", "TITAN", "MARUTI", "SUNPHARMA", "BAJFINANCE", "ULTRACEMCO", "TATASTEEL"
        ] # Top 20 weighted stocks as proxy for speed
        
        # Fetch Real-Time Quotes from OpenAlgo
        advances = 0
        declines = 0
        unchanged = 0
        data = []
        
        for sym in nifty_50_symbols:
            quote_result = await openalgo.get_quote(sym)
            if quote_result and quote_result.get("data"):
                quote = quote_result["data"]
                # OpenAlgo Quote Data: {'ltp': 1452.8, 'prev_close': 1483.2, ...}
                ltp = float(quote.get('ltp', 0))
                prev = float(quote.get('prev_close', 0))
                
                change = ltp - prev
                p_change = (change / prev * 100) if prev > 0 else 0
                
                status = "Unchanged"
                if change > 0:
                    status = "Advance"
                    advances += 1
                elif change < 0:
                    status = "Decline"
                    declines += 1
                else:
                    unchanged += 1
                    
                data.append({
                    "symbol": sym,
                    "lastPrice": ltp,
                    "change": change,
                    "pChange": p_change,
                    "status": status,
                    "feed_status": quote_result.get("feed_health", "UNKNOWN")
                })
        
        # Calculate broader market summary
        return {
            "data": data,
            "index": "NIFTY 50 (Top 20 Proxy)",
            "advances": advances,
            "declines": declines,
            "unchanged": unchanged
        }

    except Exception as e:
        # Fallback to NseUtils if OpenAlgo fails
        try:
            df = await asyncio.to_thread(nse.get_advance_decline)
            if df is None or df.empty:
               return {"data": [], "advances": 0, "declines": 0, "unchanged": 0}
            
            nifty_50 = df[df['Index'] == 'NIFTY 50']
            if not nifty_50.empty:
                summary = nifty_50.iloc[0].to_dict()
                return {
                    "data": df.to_dict(orient="records"),
                    "index": "NIFTY 50",
                    "advances": int(summary.get('Advances', 0)),
                    "declines": int(summary.get('Declines', 0)),
                    "unchanged": int(summary.get('Unchanged', 0))
                }
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/activity/volume")
async def get_market_activity_volume(db: AsyncSession = Depends(get_db)):
    """
    Get most active stocks by volume.
    Priority 1: Historical DB (Yesterday's volume for now, as real-time scanning entire market is expensive via generic API)
    Priority 2: NseUtils (Scraping)
    """
    try:
        # Query internal DB for highest volume yesterday
        result = await db.execute(text("""
            SELECT symbol, close, volume, timestamp
            FROM historical_ohlc
            WHERE interval = '1d' 
            AND timestamp = (SELECT MAX(timestamp) FROM historical_ohlc)
            ORDER BY volume DESC
            LIMIT 10
        """))
        rows = result.fetchall()
        
        if rows:
            data = []
            for row in rows:
                data.append({
                    "symbol": row[0],
                    "ltp": float(row[1]),
                    "volume": int(row[2]),
                    "value": float(row[1]) * int(row[2]) # Approx value
                })
            return {"data": data}
            
        # Fallback to NSE Utils
        df = await asyncio.to_thread(nse.most_active_equity_stocks_by_volume)
        if df is None or df.empty:
            return {"data": []}
        return {"data": df.to_dict(orient="records")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/activity/value")
async def get_market_activity_value(db: AsyncSession = Depends(get_db)):
    """
    Get most active stocks by value.
    """
    try:
        # Query internal DB
        result = await db.execute(text("""
            SELECT symbol, close, volume, (close * volume) as turnover
            FROM historical_ohlc
            WHERE interval = '1d' 
            AND timestamp = (SELECT MAX(timestamp) FROM historical_ohlc)
            ORDER BY turnover DESC
            LIMIT 10
        """))
        rows = result.fetchall()
        
        if rows:
            data = []
            for row in rows:
                data.append({
                    "symbol": row[0],
                    "ltp": float(row[1]),
                    "volume": int(row[2]),
                    "value": float(row[3])
                })
            return {"data": data}

        # Fallback
        df = await asyncio.to_thread(nse.most_active_equity_stocks_by_value)
        if df is None or df.empty:
            return {"data": []}
        return {"data": df.to_dict(orient="records")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/indices")
async def get_indices():
    """
    Fetch live data for major market indices.
    Priority: OpenAlgo (if index support added), otherwise yfinance (as requested).
    """
    indices = [
        {"name": "NIFTY 50", "ticker": "^NSEI"},
        {"name": "SENSEX", "ticker": "^BSESN"},
        {"name": "NIFTY BANK", "ticker": "^NSEBANK"},
        {"name": "NIFTY IT", "ticker": "^CNXIT"},
        {"name": "NIFTY SMALLCAP 100", "ticker": "^CNXSC"},
        {"name": "NIFTY MIDCAP 100", "ticker": "^CNXMID"}
    ]
    
    results = []
    
    for idx in indices:
        try:
            # TRY OPENALGO FIRST (Hybrid approach: use better data if available)
            # symbol mapping might be needed. assuming standard format.
            # quote = await openalgo.get_quote(idx["name"]) ...
            
            # As per user request, we stick to yfinance for indices to ensure stability 
            # until OpenAlgo index symbols are verified.
            
            ticker = yf.Ticker(idx["ticker"])
            data = ticker.history(period="5d")
            
            if not data.empty:
                current_price = data['Close'].iloc[-1]
                
                if len(data) >= 2:
                    prev_close = data['Close'].iloc[-2]
                    change = current_price - prev_close
                    change_percent = (change / prev_close) * 100
                else:
                    prev_close = current_price
                    change = 0.0
                    change_percent = 0.0
                
                results.append({
                    "name": idx["name"],
                    "value": float(current_price),
                    "change": float(change),
                    "change_percent": float(change_percent),
                    "is_up": bool(change >= 0)
                })
            else:
                results.append({
                    "name": idx["name"],
                    "value": None,
                    "error": "No data"
                })
        except Exception as e:
            results.append({
                "name": idx["name"],
                "value": None,
                "error": str(e)
            })
            
    return {"data": results}

@router.get("/mood")
async def get_market_mood():
    """
    Calculate Market Mood Index (MMI).
    Hybrid: Uses OpenAlgo breadth and yfinance historical trend.
    """
    try:
        # 1. Broad Market Breadth (Uses OpenAlgo now)
        breadth_data = await get_market_breadth()
        advances = breadth_data.get("advances", 0)
        declines = breadth_data.get("declines", 0)
        
        breadth_score = 50
        if (advances + declines) > 0:
            breadth_score = (advances / (advances + declines)) * 100
            
        # 2. Market Regime (NIFTY 50) - Uses yfinance for history
        ticker = yf.Ticker("^NSEI")
        hist = await asyncio.to_thread(ticker.history, period="6mo")
        
        regime_score = 50
        if not hist.empty:
            hist['SMA50'] = hist['Close'].rolling(window=50).mean()
            current_close = hist['Close'].iloc[-1]
            sma50 = hist['SMA50'].iloc[-1]
            
            if pd.notna(sma50):
                diff_pct = (current_close - sma50) / sma50 * 100
                regime_score = max(0, min(100, 50 + (diff_pct * 10)))
        
        final_score = (breadth_score * 0.4) + (regime_score * 0.6)
        
        status = "Neutral"
        if final_score >= 80: status = "Extreme Greed"
        elif final_score >= 65: status = "Greed"
        elif final_score <= 20: status = "Extreme Fear"
        elif final_score <= 35: status = "Fear"
        
        return {
            "score": round(final_score, 1),
            "status": status,
            "current_val": status,
            "previous_val": "Neutral",
            "previous_status": "Neutral"
        }
    except Exception as e:
        return {
            "score": 50.0,
            "status": "Neutral",
            "current_val": "Neutral",
            "previous_val": "Neutral",
            "previous_status": "Neutral",
            "error": str(e)
        }

@router.get("/history/{symbol}")
async def get_symbol_history(
    symbol: str,
    days: int = Query(30, ge=5, le=365),
    db: AsyncSession = Depends(get_db)
):
    """
    Get historical OHLCV data for a symbol from internal database.
    (Populated via Backfill/OpenAlgo History)
    """
    try:
        symbol = symbol.upper()
        
        result = await db.execute(
            text("""
                SELECT timestamp as date, open, high, low, close, volume
                FROM historical_ohlc
                WHERE symbol = :symbol
                AND interval = '1d'
                AND exchange = 'NSE'
                ORDER BY timestamp DESC
                LIMIT :limit
            """),
            {"symbol": symbol, "limit": days}
        )
        
        rows = result.fetchall()
        
        if not rows:
            # Fallback: Try fetching from OpenAlgo Ticker API directly if DB is empty
            # data = await openalgo.get_ticker(symbol, interval="1d")
            # For now, we return 404 to encourage backfill use
            raise HTTPException(
                status_code=404,
                detail=f"No historical data found for {symbol}"
            )
            
        data = []
        for row in reversed(rows):
            data.append({
                "time": row[0].strftime("%Y-%m-%d"),
                "open": float(row[1]),
                "high": float(row[2]),
                "low": float(row[3]),
                "close": float(row[4]),
                "volume": int(row[5])
            })
            
        return {"symbol": symbol, "data": data}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/volume-profile/{symbol}", response_model=Dict[str, Any])
async def get_volume_profile(
    symbol: str,
    days: int = Query(30, ge=5, le=365),
    bins: int = Query(40, ge=10, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Get Volume Profile (Volume by Price) for a symbol.
    """
    try:
        from app.services.technical_analysis import TechnicalAnalysisService
        import pandas as pd
        
        symbol = symbol.upper()
        
        result = await db.execute(
            text("""
                SELECT timestamp as date, open, high, low, close, volume
                FROM historical_ohlc
                WHERE symbol = :symbol
                AND interval = '1d'
                AND exchange = 'NSE'
                ORDER BY timestamp DESC
                LIMIT :limit
            """),
            {"symbol": symbol, "limit": days}
        )
        
        rows = result.fetchall()
        
        if not rows:
            raise HTTPException(
                status_code=404,
                detail=f"No historical data found for {symbol}"
            )
            
        df_rows = []
        for row in reversed(rows):
            df_rows.append({
                "open": float(row[1]),
                "high": float(row[2]),
                "low": float(row[3]),
                "close": float(row[4]),
                "volume": int(row[5])
            })
            
        df = pd.DataFrame(df_rows)
        
        ta_service = TechnicalAnalysisService(df)
        profile_data = ta_service.calculate_volume_profile(bins=bins)
        
        return profile_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
