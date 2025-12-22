from fastapi import APIRouter, HTTPException, Query
from ....data_sources.nse_utils import NseUtils
import pandas as pd
from typing import Dict, Any, Optional

router = APIRouter()
nse = NseUtils()

@router.get("/option-chain/{symbol}")
async def get_option_chain(symbol: str, indices: bool = False):
    """
    Get full option chain for a symbol, nested for the frontend.
    """
    try:
        is_index = indices or symbol.upper() in ['NIFTY', 'BANKNIFTY', 'FINNIFTY', 'NIFTYNXT50']
        df = nse.get_option_chain(symbol.upper(), indices=is_index)
        
        if df is None or df.empty:
            return {"symbol": symbol, "records": {"data": [], "expiryDates": [], "strikePrices": [], "underlyingValue": 0}}
            
        underlying_value = float(df.iloc[0].get('underlyingValue', 0))
        expiry_dates = sorted(list(df['expiryDate'].unique()))
        strike_prices = sorted(list(df['strikePrice'].unique()))
        
        # Group by strike
        grouped_data = []
        for strike in strike_prices:
            strike_df = df[df['strikePrice'] == strike]
            ce_data = strike_df[strike_df['instrumentType'] == 'CE'].to_dict(orient='records')
            pe_data = strike_df[strike_df['instrumentType'] == 'PE'].to_dict(orient='records')
            
            node = {
                "strikePrice": strike,
                "expiryDate": ce_data[0]['expiryDate'] if ce_data else (pe_data[0]['expiryDate'] if pe_data else ""),
                "CE": ce_data[0] if ce_data else None,
                "PE": pe_data[0] if pe_data else None
            }
            grouped_data.append(node)

        return {
            "symbol": symbol.upper(),
            "records": {
                "expiryDates": expiry_dates,
                "data": grouped_data,
                "strikePrices": strike_prices,
                "underlyingValue": underlying_value
            }
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
