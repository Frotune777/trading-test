import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
import pandas as pd
import logging
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
    
    async def fetch_price_data(self, symbol: str, interval: str = "1d", retries: int = 3) -> pd.DataFrame:
        """Helper to fetch price data as a task with retries"""
        for attempt in range(retries):
            try:
                # Current implementation of get_history is sync
                df = await asyncio.to_thread(
                    self.nse_master.get_history,
                    symbol=symbol,
                    exchange="NSE",
                    interval=interval
                )
                if df is not None and not df.empty:
                    return df
            except Exception as e:
                logger.warning(f"Attempt {attempt+1}/{retries} failed for {symbol} ({interval}): {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(1) # Wait before retry
                else:
                    logger.error(f"Final attempt failed for {symbol} ({interval})")
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
            # Wrap existing df in a future
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
            
        # 5. Sentinel Data (Insider/Bulk/Block)
        tasks.append(asyncio.to_thread(self._fetch_sentinel_data, symbol))

        # Execute all tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results with index-based safety
        price_df = results[0] if not isinstance(results[0], Exception) else pd.DataFrame()
        weekly_df = results[1] if not isinstance(results[1], Exception) else pd.DataFrame()
        quote_data = results[2] if not isinstance(results[2], Exception) else {}
        oc_df = results[3] if not isinstance(results[3], Exception) else pd.DataFrame()
        sentinel_data = results[4] if not isinstance(results[4], Exception) else {}

        if price_df is None or price_df.empty:
            raise ValueError(f"No price data available for {symbol} from NSE sources.")
        
        # Calculate technical indicators using TA-Lib
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
        
        # Basic indicators
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
                sma_20_weekly = float(ta_weekly.df.iloc[-1].get('sma_20', ltp))
            except Exception as e:
                logger.warning(f"Failed to calculate Weekly SMA for {symbol}: {e}")

        # Depth Data Processing
        bid_price = None
        ask_price = None
        bid_qty = None
        ask_qty = None
        spread_pct = None
        
        if quote_data and 'tradeData' in quote_data:
            ob = quote_data.get('tradeData', {}).get('marketDeptOrderBook', {})
            bids = ob.get('bid', [])
            asks = ob.get('ask', [])
            
            if bids:
                bid_price = float(bids[0].get('price', 0)) or None
                bid_qty = int(bids[0].get('quantity', 0)) or None
            if asks:
                ask_price = float(asks[0].get('price', 0)) or None
                ask_qty = int(asks[0].get('quantity', 0)) or None
            
            if bid_price and ask_price and bid_price > 0:
                spread_pct = (ask_price - bid_price) / bid_price * 100.0

        # Derivatives Data Processing
        oi_change = None
        if option_data:
            oi_change = option_data.get('oi_change')
        elif not oc_df.empty:
            ce_oi_chg = oc_df['CALLS_Chng_in_OI'].sum() if 'CALLS_Chng_in_OI' in oc_df else 0
            pe_oi_chg = oc_df['PUTS_Chng_in_OI'].sum() if 'PUTS_Chng_in_OI' in oc_df else 0
            oi_change = (pe_oi_chg + ce_oi_chg)

        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"Built async snapshot for {symbol} in {duration:.2f}s")

        return LiveDecisionSnapshot(
            symbol=symbol,
            timestamp=datetime.now(),
            ltp=ltp,
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
            **sentinel_data
        )

    def _fetch_sentinel_data(self, symbol: str) -> dict:
        """
        Original logic kept but wrapped for use in run_in_executor.
        """
        sentinel = {
            "insider_net_value": 0.0,
            "insider_buy_count": 0,
            "bulk_deal_net_qty": 0,
            "block_deal_net_qty": 0,
            "short_selling_pct": None
        }
        
        try:
            # 1. Insider Trades
            insider_df = self.nse_derivatives.nse_utils.get_insider_trading()
            if insider_df is not None and not insider_df.empty:
                if 'symbol' in insider_df.columns:
                    symbol_trades = insider_df[insider_df['symbol'].str.strip() == symbol]
                elif 'Symbol' in insider_df.columns:
                    symbol_trades = insider_df[insider_df['Symbol'].str.strip() == symbol]
                else:
                    symbol_trades = pd.DataFrame()

                if not symbol_trades.empty:
                    for _, trade in symbol_trades.iterrows():
                        val = float(trade.get('secVal', trade.get('valueInRs', 0)))
                        mode = str(trade.get('acqMode', '')).upper()
                        t_type = str(trade.get('tdpTransactionType', '')).upper()
                        if any(x in mode or x in t_type for x in ["ACQUISITION", "BUY", "PURCHASE"]):
                            sentinel["insider_net_value"] += val
                            sentinel["insider_buy_count"] += 1
                        elif any(x in mode or x in t_type for x in ["DISPOSAL", "SELL", "SALE"]):
                            sentinel["insider_net_value"] -= val
            
            # 2. Bulk Deals
            bulk_df = self.nse_derivatives.nse_utils.get_bulk_deals()
            if bulk_df is not None and not bulk_df.empty:
                bulk_df.columns = [c.strip().replace('ï»¿"', '').replace('"', '') for c in bulk_df.columns]
                if 'Symbol' in bulk_df.columns:
                    symbol_bulk = bulk_df[bulk_df['Symbol'].str.strip() == symbol]
                    if not symbol_bulk.empty:
                        for _, deal in symbol_bulk.iterrows():
                            qty_str = str(deal.get('Quantity Traded', '0')).replace(',', '')
                            qty = int(qty_str) if qty_str.isdigit() else 0
                            d_type = str(deal.get('Buy / Sell', '')).strip().upper()
                            if d_type == "BUY":
                                sentinel["bulk_deal_net_qty"] += qty
                            else:
                                sentinel["bulk_deal_net_qty"] -= qty
                                
            # 3. Block Deals
            block_df = self.nse_derivatives.nse_utils.get_block_deals()
            if block_df is not None and not block_df.empty:
                block_df.columns = [c.strip().replace('ï»¿"', '').replace('"', '') for c in block_df.columns]
                if 'Symbol' in block_df.columns:
                    symbol_block = block_df[block_df['Symbol'].str.strip() == symbol]
                    if not symbol_block.empty:
                        for _, deal in symbol_block.iterrows():
                            qty_str = str(deal.get('Quantity Traded', '0')).replace(',', '')
                            qty = int(qty_str) if qty_str.isdigit() else 0
                            d_type = str(deal.get('Buy / Sell', '')).strip().upper()
                            if d_type == "BUY":
                                sentinel["block_deal_net_qty"] += qty
                            else:
                                sentinel["block_deal_net_qty"] -= qty
                                
            # 4. Short Selling
            short_df = self.nse_derivatives.nse_utils.get_short_selling()
            if short_df is not None and not short_df.empty:
                short_df.columns = [c.strip().replace('ï»¿"', '').replace('"', '') for c in short_df.columns]
                if 'Symbol' in short_df.columns:
                    symbol_short = short_df[short_df['Symbol'].str.strip() == symbol]
                    if not symbol_short.empty:
                        sentinel["short_selling_pct"] = float(str(symbol_short.iloc[-1].get('Percentage of Short Quantity', 0)).replace(',', ''))
        except Exception as e:
            logger.warning(f"Error fetching sentinel data for {symbol}: {e}")
            
        return sentinel
    
    async def build_session_context(
        self,
        nifty_df: Optional[pd.DataFrame] = None
    ) -> SessionContext:
        """
        Build SessionContext from market-wide data. ASYNC.
        """
        if nifty_df is None or nifty_df.empty:
            nifty_df = await self.fetch_price_data("NIFTY 50", "1d")
        
        # Determine market regime
        regime = "NEUTRAL"
        if nifty_df is not None and not nifty_df.empty:
            market_regime_analyzer = MarketRegime(nifty_df)
            regime_data = market_regime_analyzer.determine_regime()
            regime = regime_data.get('direction', 'NEUTRAL')
        
        # VIX fetch
        vix_level = 15.0
        vix_percentile = 50.0
        try:
            vix_df = await self.fetch_price_data("INDIA VIX", "1d")
            if not vix_df.empty:
                vix_level = float(vix_df.iloc[-1]['Close'])
                vix_percentile = (vix_df['Close'].rank(pct=True).iloc[-1]) * 100.0
        except Exception as e:
            logger.warning(f"Failed to fetch VIX: {e}")
        
        return SessionContext(
            timestamp=datetime.now(),
            market_regime=regime,
            vix_level=vix_level,
            vix_percentile=vix_percentile
        )
