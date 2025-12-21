from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from ....database.db_manager import DatabaseManager

router = APIRouter()

def get_db():
    return DatabaseManager()

@router.get("/{symbol}")
async def get_stock_profile(symbol: str):
    """
    Get company profile and latest snapshot.
    """
    db = get_db()
    company = db.get_company(symbol.upper())
    if not company:
        raise HTTPException(status_code=404, detail="Stock not found")
        
    snapshot = db.get_snapshot(symbol.upper())
    
    return {
        "profile": company,
        "snapshot": snapshot,
        "symbol": symbol.upper()
    }

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
    db = get_db()
    df = db.get_price_history(symbol.upper(), days=days, start_date=start_date, end_date=end_date)
    
    if df.empty:
        return {"data": [], "symbol": symbol.upper(), "count": 0}
        
    # Convert to list of dicts for JSON response
    # Ensure date is string
    data = df.to_dict(orient='records')
    return {
        "symbol": symbol.upper(),
        "count": len(data),
        "data": data
    }

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
