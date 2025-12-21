from fastapi import APIRouter, HTTPException, Query
from ....data_sources.nse_utils import NseUtils
from typing import Optional
from datetime import datetime, timedelta

router = APIRouter()
nse = NseUtils()

def get_default_dates():
    """Returns (30 days ago, today) formatted as dd-mm-yyyy"""
    end = datetime.now()
    start = end - timedelta(days=30)
    return start.strftime("%d-%m-%Y"), end.strftime("%d-%m-%Y")

@router.get("/trades")
async def get_insider_trades(
    from_date: Optional[str] = None, 
    to_date: Optional[str] = None
):
    """
    Get SAI (Substantial Acquisition of Shares) & Insider Trading data.
    Format: dd-mm-yyyy
    """
    try:
        df = nse.get_insider_trading(from_date=from_date, to_date=to_date)
        if df is None or df.empty:
            return {"data": []}
        return {"data": df.to_dict(orient="records")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/bulk-deals")
async def get_bulk_deals(
    from_date: Optional[str] = None, 
    to_date: Optional[str] = None
):
    """
    Get Bulk Deals.
    """
    try:
        df = nse.get_bulk_deals(from_date=from_date, to_date=to_date)
        if df is None or df.empty:
            return {"data": []}
        return {"data": df.to_dict(orient="records")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/block-deals")
async def get_block_deals(
    from_date: Optional[str] = None, 
    to_date: Optional[str] = None
):
    """
    Get Block Deals.
    """
    try:
        df = nse.get_block_deals(from_date=from_date, to_date=to_date)
        if df is None or df.empty:
            return {"data": []}
        return {"data": df.to_dict(orient="records")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/short-selling")
async def get_short_selling(
    from_date: Optional[str] = None, 
    to_date: Optional[str] = None
):
    """
    Get Short Selling data.
    """
    try:
        df = nse.get_short_selling(from_date=from_date, to_date=to_date)
        if df is None or df.empty:
            return {"data": []}
        return {"data": df.to_dict(orient="records")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
