from fastapi import APIRouter, HTTPException, Query
from ....data_sources.nse_utils import NseUtils
import pandas as pd
from typing import Dict, Any, Optional

router = APIRouter()
nse = NseUtils()

@router.get("/option-chain/{symbol}")
async def get_option_chain(symbol: str, indices: bool = False):
    """
    Get full option chain for a symbol.
    """
    try:
        # Indices check: NIFTY, BANKNIFTY, FINNIFTY need indices=True
        is_index = indices or symbol.upper() in ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'NIFTYNXT50']
        
        df = nse.get_option_chain(symbol.upper(), indices=is_index)
        
        if df is None or df.empty:
            return {"symbol": symbol, "data": []}
            
        # Reset index to make 'identifier' a column if needed, or just to_dict
        # nse_utils returns dataframe with index set to 'identifier' usually
        df_reset = df.reset_index()
        
        return {
            "symbol": symbol.upper(),
            "count": len(df_reset),
            "data": df_reset.to_dict(orient="records")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/futures/{symbol}")
async def get_futures_data(symbol: str, indices: bool = False):
    """
    Get futures metadata and prices.
    """
    try:
        is_index = indices or symbol.upper() in ['NIFTY', 'BANKNIFTY', 'FINNIFTY']
        df = nse.futures_data(symbol.upper(), indices=is_index)
        
        if df is None or df.empty:
            return {"symbol": symbol, "data": []}
            
        df_reset = df.reset_index()
        return {
            "symbol": symbol.upper(),
            "data": df_reset.to_dict(orient="records")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pcr/{symbol}")
async def get_pcr_ratio(symbol: str, indices: bool = False):
    """
    Calculate Put-Call Ratio (PCR) from Option Chain.
    """
    try:
        is_index = indices or symbol.upper() in ['NIFTY', 'BANKNIFTY', 'FINNIFTY']
        df = nse.get_option_chain(symbol.upper(), indices=is_index)
        
        if df is None or df.empty:
             raise HTTPException(status_code=404, detail="No option chain data found for PCR calculation")
        
        # Filter for valid OI data
        total_pe_oi = df[df['instrumentType'] == 'PE']['openInterest'].sum()
        total_ce_oi = df[df['instrumentType'] == 'CE']['openInterest'].sum()
        
        pcr = total_pe_oi / total_ce_oi if total_ce_oi > 0 else 0
        
        return {
            "symbol": symbol.upper(),
            "pcr": round(pcr, 4),
            "total_ce_oi": float(total_ce_oi),
            "total_pe_oi": float(total_pe_oi)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
