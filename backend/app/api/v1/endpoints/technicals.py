from fastapi import APIRouter, HTTPException, Query
from ....data_sources.nse_master_data import NSEMasterData
from ....services.technical_analysis import TechnicalAnalysisService
import pandas as pd
from datetime import datetime, timedelta

router = APIRouter()
master = NSEMasterData()

@router.get("/intraday/{symbol}")
async def get_intraday_data(
    symbol: str, 
    interval: str = Query('5m', regex='^(1m|3m|5m|10m|15m|30m|1h)$'),
    days: int = 5
):
    """
    Get intraday OHLCV data for charts.
    """
    try:
        end = datetime.now()
        start = end - timedelta(days=days)
        
        df = master.get_history(
            symbol=symbol.upper(),
            exchange="NSE",
            start=start,
            end=end,
            interval=interval
        )
        
        if df is None or df.empty:
            return {"symbol": symbol, "data": []}
            
        # Ensure timestamp is string for JSON
        if df.index.name in ['Date', 'Timestamp'] or 'datetime' in str(df.index.dtype):
             df = df.reset_index()
             
        # Identify the date/timestamp column
        date_col = next((c for c in df.columns if c.lower() in ['date', 'timestamp']), None)
        if date_col:
            df[date_col] = df[date_col].astype(str)
             
        return {
            "symbol": symbol.upper(),
            "interval": interval,
            "data": df.to_dict(orient="records")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/indicators/{symbol}")
async def get_technical_indicators(symbol: str):
    """
    Get 50+ Technical Indicators + Statistical Analysis.
    """
    try:
        # Fetch 1 year of daily data for robust indicator calculation
        end = datetime.now()
        start = end - timedelta(days=365)
        
        df_hist = master.get_history(
            symbol=symbol.upper(),
            exchange="NSE",
            start=start,
            end=end,
            interval="1d"
        )
        
        if df_hist is None or df_hist.empty:
            raise HTTPException(status_code=404, detail="Not enough historical data")
            
        # Analysis Service
        tas = TechnicalAnalysisService(df_hist)
        
        # Calculate All Indicators
        df_indicators = tas.calculate_all()
        stats = tas.calculate_stats()
        
        # Get only the latest row for "Current" status, 
        # but maybe we want the last 30 days for charting indicators?
        # For now, let's return the last 100 records to keep payload reasonable
        tail_df = df_indicators.tail(100)
        
        # Handle nan/inf for JSON
        tail_df = tail_df.fillna(0)
        
        if tail_df.index.name in ['Date', 'Timestamp'] or 'datetime' in str(tail_df.index.dtype):
             tail_df = tail_df.reset_index()
        
        date_col = next((c for c in tail_df.columns if c.lower() in ['date', 'timestamp']), None)
        if date_col:
            tail_df[date_col] = tail_df[date_col].astype(str)

        return {
            "symbol": symbol.upper(),
            "stats": stats,
            "indicators": tail_df.to_dict(orient="records")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
