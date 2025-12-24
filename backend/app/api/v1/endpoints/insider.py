from fastapi import APIRouter, HTTPException, Query
from ....data_sources.nse_utils import NseUtils
from typing import Optional
from datetime import datetime, timedelta
import pandas as pd

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
            
        # Map actual NSE API fields to frontend expected fields
        column_mapping = {
            'acqName': 'person',
            'acqMode': 'acquisitionMode',
            'secVal': 'value',
            'tdpTransactionType': 'transactionType'  # Buy/Sell indicator
        }
        
        # Rename only the columns that exist in the dataframe
        existing_mappings = {k: v for k, v in column_mapping.items() if k in df.columns}
        df_renamed = df.rename(columns=existing_mappings)
        
        # Add typeOfSecurity if it exists, otherwise use a default
        if 'typeOfSecurity' not in df_renamed.columns:
            df_renamed['typeOfSecurity'] = 'Equity Shares'
        
        # Calculate signal strength and direction
        def calculate_signal(row):
            try:
                # Handle various value formats (including '-', 'Nil', empty, etc.)
                value_str = str(row.get('value', '0'))
                if value_str in ['-', 'Nil', '', 'None', 'nan']:
                    value = 0.0
                else:
                    value = float(value_str)
            except (ValueError, TypeError):
                value = 0.0
                
            transaction_type = str(row.get('transactionType', '')).lower()
            acq_mode = str(row.get('acquisitionMode', '')).lower()
            
            # Determine direction
            is_buy = 'buy' in transaction_type or 'purchase' in acq_mode
            is_sell = 'sell' in transaction_type or 'sale' in acq_mode
            
            direction = 'BUY' if is_buy else ('SELL' if is_sell else 'NEUTRAL')
            
            # Calculate strength based on value (in lakhs)
            value_lakhs = value / 100000
            if value_lakhs > 100:  # > 1 Cr
                strength = 'STRONG'
            elif value_lakhs > 10:  # > 10 Lakhs
                strength = 'MODERATE'
            elif value_lakhs > 1:  # > 1 Lakh
                strength = 'WEAK'
            else:
                strength = 'MINIMAL'
            
            return direction, strength
        
        # Apply signal calculation
        df_renamed[['signal_direction', 'signal_strength']] = df_renamed.apply(
            lambda row: pd.Series(calculate_signal(row)), axis=1
        )
            
        # Select columns to return
        columns_to_keep = []
        for col in ['symbol', 'person', 'personCategory', 'typeOfSecurity', 'acquisitionMode', 'date', 'value', 'signal_direction', 'signal_strength']:
            if col in df_renamed.columns:
                columns_to_keep.append(col)
        
        if columns_to_keep:
            df_final = df_renamed[columns_to_keep]
        else:
            df_final = df_renamed
        
        return {"data": df_final.to_dict(orient="records")}
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in insider trades: {e}", exc_info=True)
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
    Lightweight version that doesn't require full price data.
    """
    try:
        from ....reasoning.snapshot_builder import SnapshotBuilder
        import pandas as pd
        
        builder = SnapshotBuilder()
        symbol = symbol.upper()
        
        # Fetch only sentinel data (insider, bulk, block, short selling)
        # This doesn't require price data
        sentinel_data = builder._fetch_sentinel_data(symbol)
        
        # Calculate conviction score based on insider activity
        insider_value = sentinel_data.get("insider_net_value", 0)
        insider_buys = sentinel_data.get("insider_buy_count", 0)
        bulk_qty = sentinel_data.get("bulk_deal_net_qty", 0)
        block_qty = sentinel_data.get("block_deal_net_qty", 0)
        short_pct = sentinel_data.get("short_selling_pct", 0) or 0
        
        # Simple scoring logic
        score = 50.0  # Neutral baseline
        
        # Insider buying is most important
        if insider_value > 0:
            score += min(30, insider_value / 10000000)  # Up to +30 for large buys
        elif insider_value < 0:
            score -= min(30, abs(insider_value) / 10000000)  # Down to -30 for large sells
            
        # Bulk/Block deals
        if bulk_qty > 0 or block_qty > 0:
            score += 10
        elif bulk_qty < 0 or block_qty < 0:
            score -= 10
            
        # Short selling
        if short_pct > 5:
            score -= 10  # High shorting is bearish
        
        # Clamp score to 0-100
        score = max(0, min(100, score))
        
        # Determine bias
        if score >= 70:
            bias = "BULLISH"
        elif score <= 30:
            bias = "BEARISH"
        else:
            bias = "NEUTRAL"
            
        # Generate signals
        signals = []
        if insider_buys > 3:
            signals.append("Promoter Buyback Cluster")
        elif insider_buys > 0:
            signals.append("Insider Buying")
        elif insider_buys < 0:
            signals.append("Insider Selling")
            
        if bulk_qty > 0:
            signals.append("Bulk Accumulation")
        if block_qty > 0:
            signals.append("Block Deals")
        if short_pct > 5:
            signals.append("High Short Interest")
            
        if not signals:
            signals = ["None"]
        
        return {
            "symbol": symbol,
            "sentinel_score": round(score, 1),
            "bias": bias,
            "signals": signals,
            "metrics": {
                "insider_buys": insider_buys,
                "net_insider_value": f"{insider_value / 10000000:.2f}" if insider_value else "0",  # In crores
                "bulk_deal_qty": bulk_qty,
                "block_deal_qty": block_qty,
                "short_selling_pct": short_pct
            }
        }
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in sentinel endpoint for {symbol}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
