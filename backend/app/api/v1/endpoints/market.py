from fastapi import APIRouter, HTTPException
from ....data_sources.nse_utils import NseUtils
import pandas as pd
import yfinance as yf
from typing import List, Dict, Any

router = APIRouter()
nse = NseUtils()

@router.get("/breadth")
async def get_market_breadth():
    """
    Get market advance/decline ratio.
    """
    try:
        df = nse.get_advance_decline()
        if df is None or df.empty:
            return {"data": []}
        return {"data": df.to_dict(orient="records")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/activity/volume")
async def get_market_activity_volume():
    """
    Get most active stocks by volume.
    """
    try:
        df = nse.most_active_equity_stocks_by_volume()
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
        df = nse.most_active_equity_stocks_by_value()
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
