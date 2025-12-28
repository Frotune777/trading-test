from typing import List, Dict, Any, Optional
import asyncio
import pandas as pd
import yfinance as yf
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.database import get_db
from fastapi import APIRouter, HTTPException, Depends, Query
from app.data_sources.nse_utils import NseUtils

router = APIRouter()
nse = NseUtils()

@router.get("/status")
@router.get("/breadth")
async def get_market_breadth():
    """
    Get market advance/decline ratio.
    """
    try:
        df = await asyncio.to_thread(nse.get_advance_decline)
        if df is None or df.empty:
            return {"data": [], "advances": 0, "declines": 0, "unchanged": 0}
            
        # Get NIFTY 50 as the default summary
        nifty_50 = df[df['Index'] == 'NIFTY 50']
        if not nifty_50.empty:
            summary = nifty_50.iloc[0].to_dict()
            # Preserve the list in 'data' and add top-level keys for the widget
            return {
                "data": df.to_dict(orient="records"),
                "index": "NIFTY 50",
                "advances": int(summary.get('Advances', 0)),
                "declines": int(summary.get('Declines', 0)),
                "unchanged": int(summary.get('Unchanged', 0))
            }
            
        return {"data": df.to_dict(orient="records"), "advances": 0, "declines": 0, "unchanged": 0}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/activity/volume")
async def get_market_activity_volume():
    """
    Get most active stocks by volume.
    """
    try:
        df = await asyncio.to_thread(nse.most_active_equity_stocks_by_volume)
        if df is None or df.empty:
            return {"data": []}
        return {"data": df.to_dict(orient="records")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/activity/value")
async def get_market_activity_value():
    """
    Get most active stocks by value.
    """
    try:
        df = await asyncio.to_thread(nse.most_active_equity_stocks_by_value)
        if df is None or df.empty:
            return {"data": []}
        return {"data": df.to_dict(orient="records")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/indices")
async def get_indices():
    """
    Fetch live data for major market indices using yfinance.
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
            ticker = yf.Ticker(idx["ticker"])
            # Fast fetch using info if possible, else 1d history
            # Note: yfinance .info can be slow, history is often more reliable
            data = ticker.history(period="5d")
            
            if not data.empty:
                current_price = data['Close'].iloc[-1]
                
                # Calculate change
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
    Calculate Market Mood Index (MMI) based on multiple factors.
    Inspired by Tickertape MMI.
    """
    try:
        # 1. Broad Market Breadth
        breadth_data = await get_market_breadth()
        advances = breadth_data.get("advances", 0)
        declines = breadth_data.get("declines", 0)
        
        breadth_score = 50
        if (advances + declines) > 0:
            breadth_score = (advances / (advances + declines)) * 100
            
        # 2. Market Regime (NIFTY 50)
        ticker = yf.Ticker("^NSEI")
        hist = await asyncio.to_thread(ticker.history, period="6mo")
        
        regime_score = 50
        if not hist.empty:
            # Simple trend score: current price vs 50 DMA
            hist['SMA50'] = hist['Close'].rolling(window=50).mean()
            current_close = hist['Close'].iloc[-1]
            sma50 = hist['SMA50'].iloc[-1]
            
            if pd.notna(sma50):
                # Distance from SMA50 normalized to 0-100
                diff_pct = (current_close - sma50) / sma50 * 100
                # Map -5% to +5% range to 0 to 100
                regime_score = max(0, min(100, 50 + (diff_pct * 10)))
        
        # Weighted Average
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
    """
    try:
        # Normalize symbol
        symbol = symbol.upper()
        
        result = await db.execute(
            text("""
                SELECT date, open, high, low, close, volume
                FROM price_history
                WHERE symbol = :symbol
                ORDER BY date DESC
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
            
        data = []
        for row in reversed(rows): # Return in chronological order
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
    
    Returns:
    - profile: List of bins with price, volume, buy/sell volume
    - poc: Point of Control (highest volume price)
    - vah: Value Area High
    - val: Value Area Low
    - total_volume: sum of volume across all bins
    """
    try:
        from app.services.technical_analysis import TechnicalAnalysisService
        import pandas as pd
        
        # 1. Normalize symbol
        symbol = symbol.upper()
        
        # 2. Fetch historical data
        result = await db.execute(
            text("""
                SELECT date, open, high, low, close, volume
                FROM price_history
                WHERE symbol = :symbol
                ORDER BY date DESC
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
            
        # 3. Convert to DataFrame (reverse for chronological order if needed, 
        # but TA service handles the whole df anyway)
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
        
        # 4. Calculate volume profile
        ta_service = TechnicalAnalysisService(df)
        profile_data = ta_service.calculate_volume_profile(bins=bins)
        
        return profile_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating volume profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))
