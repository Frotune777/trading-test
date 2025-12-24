from fastapi import APIRouter, HTTPException
from ....data_sources.nse_utils import NseUtils
import pandas as pd
import yfinance as yf
from typing import List, Dict, Any
import asyncio

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
