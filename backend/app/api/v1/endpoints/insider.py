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
    try:
        df = nse.get_insider_trading(from_date=from_date, to_date=to_date)
        if df is None or df.empty:
            return {"data": []}
            
        # Rename columns for frontend
        df_renamed = df.rename(columns={
            'acquirerName': 'person',
            'secType': 'typeOfSecurity',
            'tdpAdvisers': 'acquisitionMode',
            'acqFromDate': 'date',
            'valueInRs': 'value'
        })
        return {"data": df_renamed.to_dict(orient="records")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/bulk-deals")
async def get_bulk_deals(
    from_date: Optional[str] = None, 
    to_date: Optional[str] = None
):
    try:
        df = nse.get_bulk_deals(from_date=from_date, to_date=to_date)
        if df is None or df.empty:
            return {"data": []}
            
        # Rename columns for frontend
        df_renamed = df.rename(columns={
            'transactionType': 'dealType',
            'quantityTraded': 'quantity',
            'tradePrice': 'price'
        })
        return {"data": df_renamed.to_dict(orient="records")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/block-deals")
async def get_block_deals(
    from_date: Optional[str] = None, 
    to_date: Optional[str] = None
):
    try:
        df = nse.get_block_deals(from_date=from_date, to_date=to_date)
        if df is None or df.empty:
            return {"data": []}
            
        # Rename columns for frontend
        df_renamed = df.rename(columns={
            'transactionType': 'dealType',
            'quantityTraded': 'quantity',
            'tradePrice': 'price'
        })
        return {"data": df_renamed.to_dict(orient="records")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/short-selling")
async def get_short_selling(
    from_date: Optional[str] = None, 
    to_date: Optional[str] = None
):
    try:
        df = nse.get_short_selling(from_date=from_date, to_date=to_date)
        if df is None or df.empty:
            return {"data": []}
            
        # Rename columns for frontend
        df_renamed = df.rename(columns={
            'short_qty': 'quantity',
            'short_percent': 'percent'
        })
        return {"data": df_renamed.to_dict(orient="records")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@router.get("/sentinel/{symbol}")
async def get_sentinel_signals(symbol: str):
    """
    Get high-conviction Sentinel signals for a specific symbol.
    Uses SnapshotBuilder and SentimentPillar logic internally.
    """
    try:
        from ....reasoning.snapshot_builder import SnapshotBuilder
        from ....reasoning.pillars.sentiment_pillar import SentimentPillar
        from ....core.market_snapshot import SessionContext
        from datetime import datetime
        
        builder = SnapshotBuilder()
        pillar = SentimentPillar()
        
        # Build snapshot for sentiment analysis
        snapshot = builder.build_snapshot(symbol.upper())
        
        # Simple neutral context for baseline
        context = SessionContext(
            timestamp=datetime.now(),
            market_regime="NEUTRAL",
            vix_level=15.0
        )
        
        # Run analysis (returns score, bias, metrics)
        score, bias, metrics = pillar.analyze(snapshot, context)
        
        return {
            "symbol": symbol.upper(),
            "sentinel_score": score,
            "bias": bias,
            "signals": metrics.get("Sentinel Signals", "None").split(", "),
            "metrics": {
                "insider_buys": metrics.get("Insider Buys"),
                "net_insider_value": metrics.get("Net Insider Value"),
                "bulk_deal_qty": snapshot.bulk_deal_net_qty,
                "block_deal_qty": snapshot.block_deal_net_qty,
                "short_selling_pct": snapshot.short_selling_pct
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
