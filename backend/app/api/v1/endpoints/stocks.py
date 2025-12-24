from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
import pandas as pd
from ....database.db_manager import DatabaseManager

router = APIRouter()

def get_db():
    return DatabaseManager()

@router.get("/{symbol}")
async def get_stock_profile(symbol: str):
    """
    Get company profile and latest snapshot.
    """
    import yfinance as yf
    
    # Try with .NS suffix for NSE stocks
    ticker_symbol = symbol.upper()
    if not ticker_symbol.endswith('.NS'):
        ticker_symbol = f"{ticker_symbol}.NS"
    
    try:
        stock = yf.Ticker(ticker_symbol)
        info = stock.info
        
        # Build profile
        profile = {
            "symbol": symbol.upper(),
            "name": info.get("longName", symbol.upper()),
            "sector": info.get("sector", ""),
            "industry": info.get("industry", ""),
            "isin": info.get("isin", "")
        }
        
        # Build snapshot
        snapshot = {
            "last_price": info.get("currentPrice", info.get("regularMarketPrice", 0)),
            "change": info.get("regularMarketChange", 0),
            "change_percent": info.get("regularMarketChangePercent", 0),
            "volume": info.get("volume", 0),
            "high_52w": info.get("fiftyTwoWeekHigh", 0),
            "low_52w": info.get("fiftyTwoWeekLow", 0),
            "market_cap": info.get("marketCap", 0),
            "pe_ratio": info.get("trailingPE", 0),
            "pb_ratio": info.get("priceToBook", 0),
            "book_value": info.get("bookValue", 0),
            "eps": info.get("trailingEps", 0),
            "roe": info.get("returnOnEquity", 0) * 100 if info.get("returnOnEquity") else 0,
            "roce": 0,  # Not available in yfinance
            "dividend_yield": info.get("dividendYield", 0) * 100 if info.get("dividendYield") else 0,
            "face_value": 0  # Not available in yfinance
        }
        
        return {
            "profile": profile,
            "snapshot": snapshot,
            "symbol": symbol.upper()
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Stock not found: {str(e)}")

@router.get("/{symbol}/history")
async def get_stock_history(
    symbol: str, 
    days: int = Query(365, ge=1, le=2000),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Get historical price data (OHLCV).
    """
    import yfinance as yf
    from datetime import datetime, timedelta
    
    # Try with .NS suffix for NSE stocks
    ticker_symbol = symbol.upper()
    if not ticker_symbol.endswith('.NS'):
        ticker_symbol = f"{ticker_symbol}.NS"
    
    try:
        stock = yf.Ticker(ticker_symbol)
        
        # Calculate date range
        if start_date and end_date:
            df = stock.history(start=start_date, end=end_date)
        else:
            end = datetime.now()
            start = end - timedelta(days=days)
            df = stock.history(start=start, end=end)
        
        if df.empty:
            return {"data": [], "symbol": symbol.upper(), "count": 0}
        
        # Reset index and format
        df = df.reset_index()
        df.columns = [col.lower() for col in df.columns]
        
        # Remove timezone if present
        df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None)
        df['date'] = df['date'].dt.strftime('%Y-%m-%d')
        
        # Convert to list of dicts for JSON response
        data = df[['date', 'open', 'high', 'low', 'close', 'volume']].to_dict(orient='records')
        
        return {
            "symbol": symbol.upper(),
            "count": len(data),
            "data": data
        }
    except Exception as e:
        return {"data": [], "symbol": symbol.upper(), "count": 0}

@router.get("/{symbol}/financials")
async def get_stock_financials(symbol: str, limit: int = 12):
    """
    Get quarterly and annual results.
    """
    db = get_db()
    
    quarterly = db.get_quarterly_results(symbol.upper(), limit=limit)
    annual = db.get_annual_results(symbol.upper(), limit=limit)
    
    return {
        "symbol": symbol.upper(),
        "quarterly": quarterly.to_dict(orient='records') if not quarterly.empty else [],
        "annual": annual.to_dict(orient='records') if not annual.empty else []
    }
