from fastapi import APIRouter

router = APIRouter()

@router.get("/stocks")
async def list_stocks():
    try:
        from ...data_sources.nse_master_data import NSEMasterData
        master = NSEMasterData()
        # Ensure master data is loaded
        if master.master_df is None or master.master_df.empty:
            master.download_symbol_master()
            
        if master.master_df is not None and not master.master_df.empty:
            # Return list of symbols
            # Assuming 'SYMBOL' or 'Symbol' column exists
            col = 'SYMBOL' if 'SYMBOL' in master.master_df.columns else 'Symbol'
            if col in master.master_df.columns:
                symbols = master.master_df[col].tolist()
                return {"count": len(symbols), "symbols": symbols}
        
        return {"count": 0, "symbols": [], "message": "No stocks found"}
    except Exception as e:
        return {"error": str(e), "message": "Failed to fetch stock list"}

@router.get("/indices")
async def get_indices():
    """Fetch live data for major market indices"""
    import yfinance as yf
    
    indices = [
        {"name": "NIFTY 50", "ticker": "^NSEI"},
        {"name": "SENSEX", "ticker": "^BSESN"},
        {"name": "NIFTY BANK", "ticker": "^NSEBANK"},
        {"name": "NIFTY IT", "ticker": "^CNXIT"}
    ]
    
    results = []
    
    for idx in indices:
        try:
            ticker = yf.Ticker(idx["ticker"])
            data = ticker.history(period="1d")
            
            if not data.empty:
                current_price = data['Close'].iloc[-1]
                prev_close = data['Open'].iloc[0] # Using Open as approximation for prev close if prev day not fetched, or better:
                # To get change, we really need prev close.
                # Let's try to get info['previousClose'] or calculate from 2 days history
                
                info = ticker.info
                # yfinance info is often faster for current price/change
                if info and 'regularMarketPrice' in info:
                    price = info.get('regularMarketPrice')
                    previous_close = info.get('previousClose')
                    
                    # Fix for some yf versions returning None
                    if price is None: price = current_price
                    if previous_close is None: previous_close = data['Open'].iloc[0] # Fallback
                    
                    change = price - previous_close
                    change_percent = (change / previous_close) * 100
                    
                    results.append({
                        "name": idx["name"],
                        "value": f"{price:,.2f}",
                        "change": f"{change_percent:+.2f}%",
                        "up": change >= 0
                    })
                else:
                    # Fallback to history calculation
                    price = current_price
                    # Get 5d history to ensure we have previous close
                    hist = ticker.history(period="5d")
                    if len(hist) >= 2:
                        prev = hist['Close'].iloc[-2]
                        change = price - prev
                        change_percent = (change / prev) * 100
                    else:
                        prev = price
                        change = 0.0
                        change_percent = 0.0
                        
                    results.append({
                        "name": idx["name"],
                        "value": f"{price:,.2f}",
                        "change": f"{change_percent:+.2f}%",
                        "up": change >= 0
                    })
            else:
                results.append({
                    "name": idx["name"],
                    "value": "N/A",
                    "change": "0.0%",
                    "up": True
                })
        except Exception as e:
             results.append({
                "name": idx["name"],
                "value": "Error",
                "change": "0.0%",
                "up": True
            })
            
    return results
