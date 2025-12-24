from fastapi import APIRouter, HTTPException, Query
from ....data_sources.nse_master_data import NSEMasterData
from ....services.technical_analysis import TechnicalAnalysisService
import pandas as pd
from datetime import datetime, timedelta
import asyncio
import logging

logger = logging.getLogger(__name__)

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
    Async parallel fetching for performance.
    """
    try:
        symbol = symbol.upper()
        end = datetime.now()
        start_d = end - timedelta(days=365)
        start_w = end - timedelta(days=365 * 2) # 2 years for weekly MA
        
        # Parallel fetch daily and weekly
        tasks = [
            asyncio.to_thread(master.get_history, symbol=symbol, exchange="NSE", start=start_d, end=end, interval="1d"),
            asyncio.to_thread(master.get_history, symbol=symbol, exchange="NSE", start=start_w, end=end, interval="1w")
        ]
        results = await asyncio.gather(*tasks)
        df_hist = results[0]
        df_weekly = results[1]
        
        # Require minimum 50 days of data (instead of 200)
        if df_hist is None or df_hist.empty:
            raise HTTPException(
                status_code=404, 
                detail=f"No historical data available for {symbol}. Symbol may be invalid or newly listed."
            )
        
        if len(df_hist) < 50:
            raise HTTPException(
                status_code=404,
                detail=f"Insufficient historical data for {symbol}. Only {len(df_hist)} days available, need at least 50 days for technical analysis."
            )
            
        # Analysis Service
        tas = TechnicalAnalysisService(df_hist)
        df_indicators = tas.calculate_all()
        stats = tas.calculate_stats()
        
        # Weekly Confirmation
        sma_20_weekly = None
        if df_weekly is not None and not df_weekly.empty:
            tas_w = TechnicalAnalysisService(df_weekly)
            tas_w.add_trend_indicators()
            sma_20_weekly = float(tas_w.df.iloc[-1].get('sma_20', 0))

        # Get only the latest records
        tail_df = df_indicators.tail(100).copy()
        
        # Handle nan/inf for JSON
        tail_df = tail_df.fillna(0)
        
        # Add weekly marker to the latest record
        if not tail_df.empty:
            # We inject it into the dataframe records so it shows in the table
            tail_df['sma_20_weekly'] = sma_20_weekly

        if tail_df.index.name in ['Date', 'Timestamp'] or 'datetime' in str(tail_df.index.dtype):
             tail_df = tail_df.reset_index()
        
        date_col = next((c for c in tail_df.columns if c.lower() in ['date', 'timestamp']), None)
        if date_col:
            tail_df[date_col] = tail_df[date_col].astype(str)
            
        # Also include it in stats for quick access
        stats['sma_20_weekly'] = sma_20_weekly

        return {
            "symbol": symbol,
            "stats": stats,
            "indicators": tail_df.to_dict(orient="records")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in technicals endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))
