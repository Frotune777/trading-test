import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
import pandas as pd
import logging
import json
import time
from app.core.redis import redis_client
from app.core.config import settings
from ..core.market_snapshot import LiveDecisionSnapshot, SessionContext
from ..services.technical_analysis import TechnicalAnalysisService
from ..services.market_regime import MarketRegime
from ..data_sources.nse_master_data import NSEMasterData

logger = logging.getLogger(__name__)

class SnapshotBuilder:
    """
    Builds LiveDecisionSnapshot and SessionContext from existing data sources.
    Acts as an adapter between old data services and new reasoning engine.
    Refactored to be ASYNC for performance.
    """
    
    def __init__(self):
        self.nse_master = NSEMasterData()
        # Initialize derivatives source for real-time data
        from ..data_sources.nse_derivatives import NSEDerivatives
        self.nse_derivatives = NSEDerivatives()
        from ..services.unified_data_service import UnifiedDataService
        self.unified = UnifiedDataService()
        from ..services.historical_data_service import historical_data_service
        self.historical = historical_data_service
    
    async def fetch_price_data(self, symbol: str, interval: str = "1d", limit: int = 250) -> pd.DataFrame:
        """Fetch price data from UnifiedDataService (PostgreSQL first)"""
        try:
            return await self.unified.get_historical_data(symbol=symbol, interval=interval, limit=limit)
        except Exception as e:
            logger.error(f"Error fetching price data for {symbol} ({interval}): {e}")
            return pd.DataFrame()

    async def fetch_equity_info(self, symbol: str) -> Dict[str, Any]:
        """Helper to fetch equity quote/depth as a task"""
        try:
            return await asyncio.to_thread(self.nse_derivatives.nse_utils.equity_info, symbol)
        except Exception as e:
            logger.error(f"Error fetching equity info for {symbol}: {e}")
            return {}

    async def fetch_option_chain(self, symbol: str) -> pd.DataFrame:
        """Helper to fetch option chain as a task"""
        try:
            return await asyncio.to_thread(self.nse_derivatives.get_option_chain, symbol)
        except Exception as e:
            logger.error(f"Error fetching option chain for {symbol}: {e}")
            return pd.DataFrame()

    async def build_snapshot(
        self, 
        symbol: str,
        price_df: Optional[pd.DataFrame] = None,
        option_data: Optional[dict] = None
    ) -> LiveDecisionSnapshot:
        """
        Build a LiveDecisionSnapshot for a symbol using ASYNC parallel tasks.
        """
        start_time = datetime.now()
        
        # Define tasks for parallel execution
        tasks = []
        
        # 1. Daily Price Data (only if not provided)
        if price_df is None or price_df.empty:
            tasks.append(self.fetch_price_data(symbol, "1d"))
        else:
            f = asyncio.Future()
            f.set_result(price_df)
            tasks.append(f)
            
        # 2. Weekly Price Data (for Weekly SMA)
        tasks.append(self.fetch_price_data(symbol, "1w"))
        
        # 3. Equity Info (for real-time depth/spread)
        tasks.append(self.fetch_equity_info(symbol))
        
        # 4. Option Chain (for sentiment)
        if not option_data:
            tasks.append(self.fetch_option_chain(symbol))
        else:
            f = asyncio.Future()
            f.set_result(pd.DataFrame())
            tasks.append(f)
            
        # 5. Sentinel Data (Insider/Bulk/Block Deals from PostgreSQL)
        tasks.append(self._fetch_async_sentinel(symbol))

        # Execute all tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        price_df = results[0] if not isinstance(results[0], Exception) else pd.DataFrame()
        weekly_df = results[1] if not isinstance(results[1], Exception) else pd.DataFrame()
        quote_data = results[2] if not isinstance(results[2], Exception) else {}
        oc_df = results[3] if not isinstance(results[3], Exception) else pd.DataFrame()
        sentinel_data = results[4] if not isinstance(results[4], Exception) else {}

        if price_df is None or price_df.empty:
            raise ValueError(f"No price data available for {symbol}. Ensure migration/ingestion is complete.")
        
        # Calculate technical indicators
        ta = TechnicalAnalysisService(price_df)
        ta.calculate_all()
        df = ta.df
        
        # Get latest values from daily data
        current = df.iloc[-1]
        ltp = float(current['close'])
        open_price = float(current['open'])
        high = float(current['high'])
        low = float(current['low'])
        volume = int(current['volume'])
        prev_close = float(df.iloc[-2]['close']) if len(df) > 1 else ltp
        vwap = (high + low + ltp) / 3.0
        
        # Indicators
        sma_50 = float(current.get('sma_50', ltp))
        sma_200 = float(current.get('sma_200', ltp))
        rsi = float(current.get('rsi', 50.0))
        macd = float(current.get('macd', 0.0))
        macd_signal = float(current.get('macd_signal', 0.0))
        macd_hist = float(current.get('macd_hist', 0.0))
        atr = float(current.get('atr', 0.0))
        atr_pct = (atr / ltp * 100.0) if ltp > 0 and atr > 0 else 0.0
        
        bb_upper = current.get('bb_upper')
        bb_middle = current.get('bb_middle')
        bb_lower = current.get('bb_lower')
        bb_width = ((bb_upper - bb_lower) / bb_middle * 100.0) if bb_middle and bb_middle > 0 else None
        adosc = current.get('adosc')

        # Weekly SMA calculation
        sma_20_weekly = None
        if not weekly_df.empty:
            try:
                ta_weekly = TechnicalAnalysisService(weekly_df)
                ta_weekly.add_trend_indicators()
                sma_20_weekly = float(ta_weekly.df.iloc[-1]['sma_20'])
            except:
                pass 

        # Depth Data Processing
        bid_price = None; ask_price = None; bid_qty = None; ask_qty = None; spread_pct = None
        if quote_data and 'tradeData' in quote_data:
            ob = quote_data.get('tradeData', {}).get('marketDeptOrderBook', {})
            bids = ob.get('bid', []); asks = ob.get('ask', [])
            if bids:
                bid_price = float(bids[0].get('price', 0)) or None
                bid_qty = int(bids[0].get('quantity', 0)) or None
            if asks:
                ask_price = float(asks[0].get('price', 0)) or None
                ask_qty = int(asks[0].get('quantity', 0)) or None
            if bid_price and ask_price and bid_price > 0:
                spread_pct = (ask_price - bid_price) / bid_price * 100.0

        # Derivatives Data
        oi_change = None
        if option_data:
            oi_change = option_data.get('oi_change')
        elif not oc_df.empty:
            ce_oi_chg = oc_df['CALLS_Chng_in_OI'].sum() if 'CALLS_Chng_in_OI' in oc_df else 0
            pe_oi_chg = oc_df['PUTS_Chng_in_OI'].sum() if 'PUTS_Chng_in_OI' in oc_df else 0
            oi_change = (pe_oi_chg + ce_oi_chg)

        # REDIS Freshness LTP
        final_ltp = ltp; ltp_source = "snapshot"; ltp_age_ms = None
        try:
            exchange = "NSE"
            redis_key = f"market:ltp:{exchange}:{symbol}"
            cached_tick_raw = await redis_client.get(redis_key)
            if cached_tick_raw:
                cached_tick = json.loads(cached_tick_raw)
                received_at = cached_tick.get("received_at", 0)
                age_ms = int((time.time() - received_at) * 1000)
                if age_ms < (settings.REDIS_TICK_TTL * 1000):
                    final_ltp = float(cached_tick.get("ltp", ltp))
                    ltp_source = "redis_ws"
                    ltp_age_ms = age_ms
        except:
            pass

        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"Built async snapshot for {symbol} in {duration:.2f}s using PostgreSQL")

        return LiveDecisionSnapshot(
            symbol=symbol,
            timestamp=datetime.now(),
            ltp=final_ltp,
            vwap=vwap,
            open=open_price,
            high=high,
            low=low,
            prev_close=prev_close,
            volume=volume,
            sma_50=sma_50,
            sma_200=sma_200,
            sma_20_weekly=sma_20_weekly,
            rsi=rsi,
            macd=macd,
            macd_signal=macd_signal,
            macd_hist=macd_hist,
            atr=atr,
            atr_pct=atr_pct,
            bb_width=bb_width,
            bb_upper=float(bb_upper) if bb_upper is not None else None,
            bb_middle=float(bb_middle) if bb_middle is not None else None,
            bb_lower=float(bb_lower) if bb_lower is not None else None,
            adosc=float(adosc) if adosc is not None else None,
            bid_price=bid_price,
            ask_price=ask_price,
            bid_qty=bid_qty,
            ask_qty=ask_qty,
            spread_pct=spread_pct,
            oi_change=oi_change,
            ltp_source=ltp_source,
            ltp_age_ms=ltp_age_ms,
            **sentinel_data
        )

    async def _fetch_async_sentinel(self, symbol: str) -> dict:
        """Fetch Sentinel data (Insider/Bulk/Block) from PostgreSQL via UnifiedDataService."""
        sentinel = {
            "insider_net_value": 0.0,
            "insider_buy_count": 0,
            "bulk_deal_net_qty": 0,
            "block_deal_net_qty": 0,
            "short_selling_pct": None
        }
        try:
            # Fetch from PostgreSQL
            insider_trades = await self.unified.get_insider_trading(symbol=symbol, limit=50)
            for trade in insider_trades:
                val = float(trade.get('value', 0))
                t_type = str(trade.get('transaction_type', '')).upper()
                if "BUY" in t_type or "PURCHASE" in t_type or "ACQUISITION" in t_type:
                    sentinel["insider_net_value"] += val
                    sentinel["insider_buy_count"] += 1
                elif "SELL" in t_type or "SALE" in t_type or "DISPOSAL" in t_type:
                    sentinel["insider_net_value"] -= val
            
            bulk = await self.historical.get_market_bulk_deals(symbol=symbol, limit=20)
            if not bulk.empty:
                for _, deal in bulk.iterrows():
                    qty = float(deal.get('quantity', 0))
                    side = str(deal.get('buy_sell', '')).upper()
                    if side == "BUY":
                        sentinel["bulk_deal_net_qty"] += qty
                    else:
                        sentinel["bulk_deal_net_qty"] -= qty
        except Exception as e:
            logger.warning(f"Error fetching async sentinel for {symbol}: {e}")
            
        return sentinel
    
    async def build_session_context(self, nifty_df: Optional[pd.DataFrame] = None) -> SessionContext:
        """Build SessionContext using UnifiedDataService."""
        if nifty_df is None or nifty_df.empty:
            nifty_df = await self.fetch_price_data("NIFTY 50", "1d")
        
        regime = "NEUTRAL"
        if nifty_df is not None and not nifty_df.empty:
            market_regime_analyzer = MarketRegime(nifty_df)
            regime_data = market_regime_analyzer.determine_regime()
            regime = regime_data.get('direction', 'NEUTRAL')
        
        vix_level = 15.0; vix_percentile = 50.0
        try:
            vix_df = await self.fetch_price_data("INDIA VIX", "1d")
            if not vix_df.empty:
                vix_level = float(vix_df.iloc[-1]['close'])
                vix_percentile = (vix_df['close'].rank(pct=True).iloc[-1]) * 100.0
        except Exception as e:
            logger.warning(f"Failed to fetch VIX: {e}")
        
        return SessionContext(
            timestamp=datetime.now(),
            market_regime=regime,
            vix_level=vix_level,
            vix_percentile=vix_percentile
        )
