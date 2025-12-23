"""
Snapshot Builder - Converts existing data sources to LiveDecisionSnapshot
"""

from datetime import datetime
from typing import Optional
import pandas as pd
from ..core.market_snapshot import LiveDecisionSnapshot, SessionContext
from ..services.technical_analysis import TechnicalAnalysisService
from ..services.market_regime import MarketRegime
from ..data_sources.nse_master_data import NSEMasterData

class SnapshotBuilder:
    """
    Builds LiveDecisionSnapshot and SessionContext from existing data sources.
    Acts as an adapter between old data services and new reasoning engine.
    """
    
    def __init__(self):
        self.nse_master = NSEMasterData()
        # Initialize derivatives source for real-time data
        from ..data_sources.nse_derivatives import NSEDerivatives
        self.nse_derivatives = NSEDerivatives()
    
    def build_snapshot(
        self, 
        symbol: str,
        price_df: Optional[pd.DataFrame] = None,
        option_data: Optional[dict] = None
    ) -> LiveDecisionSnapshot:
        """
        Build a LiveDecisionSnapshot for a symbol.
        
        Args:
            symbol: Stock symbol
            price_df: Historical OHLCV DataFrame (optional, will fetch if None)
            option_data: Option chain data dict (optional)
            
        Returns:
            LiveDecisionSnapshot with all available data
        """
        # Fetch price data if not provided
        if price_df is None or price_df.empty:
            # Fetch last 100 days for indicator calculation
            price_df = self.nse_master.get_history(
                symbol=symbol,
                exchange="NSE",
                interval="1d"
            )
        
        if price_df is None or price_df.empty:
            raise ValueError(f"No price data available for {symbol}")
        
        # Calculate technical indicators
        ta = TechnicalAnalysisService(price_df)
        ta.add_trend_indicators()
        ta.add_momentum_indicators()
        ta.add_volatility_indicators()  # NEW: ATR and Bollinger Bands
        df = ta.df
        
        # Get latest values
        current = df.iloc[-1]
        
        # Extract price state
        ltp = float(current['close'])
        open_price = float(current['open'])
        high = float(current['high'])
        low = float(current['low'])
        volume = int(current['volume'])
        
        # Previous close (from second-to-last row)
        prev_close = float(df.iloc[-2]['close']) if len(df) > 1 else ltp
        
        # Calculate VWAP (simple approximation)
        vwap = (high + low + ltp) / 3.0
        
        # Extract technical indicators (Trend/Momentum)
        sma_50 = float(current.get('sma_50', ltp))
        sma_200 = float(current.get('sma_200', ltp))
        rsi = float(current.get('rsi', 50.0))
        macd = float(current.get('macd', 0.0))
        macd_signal = float(current.get('macd_signal', 0.0))
        macd_hist = float(current.get('macd_hist', 0.0))
        
        # Extract volatility indicators
        atr = float(current.get('atr', 0.0))
        atr_pct = (atr / ltp * 100.0) if ltp > 0 and atr > 0 else 0.0
        
        bb_upper = current.get('bb_upper')
        bb_middle = current.get('bb_middle')
        bb_lower = current.get('bb_lower')
        bb_width = None
        if bb_upper is not None and bb_lower is not None and bb_middle is not None and bb_middle > 0:
            bb_width = ((bb_upper - bb_lower) / bb_middle * 100.0)
        
        # Extract liquidity indicators
        adosc = current.get('adosc')
        
        # REAL-TIME LIQUIDITY & DEPTH
        bid_price = None
        ask_price = None
        bid_qty = None
        ask_qty = None
        spread_pct = None
        
        try:
            # Try fetching real-time equity info for depth
            quote_data = self.nse_derivatives.nse_utils.equity_info(symbol)
            if quote_data and 'tradeData' in quote_data:
                # Parse L2 depth if available
                ob = quote_data.get('tradeData', {}).get('marketDeptOrderBook', {})
                bids = ob.get('bid', [])
                asks = ob.get('ask', [])
                
                if bids and len(bids) > 0:
                    bid_price = float(bids[0]['price']) if 'price' in bids[0] else None
                    bid_qty = int(bids[0]['quantity']) if 'quantity' in bids[0] else None
                    
                if asks and len(asks) > 0:
                    ask_price = float(asks[0]['price']) if 'price' in asks[0] else None
                    ask_qty = int(asks[0]['quantity']) if 'quantity' in asks[0] else None
                
                if bid_price is not None and ask_price is not None and bid_price > 0:
                    spread_pct = (ask_price - bid_price) / bid_price * 100.0
                    
        except Exception as e:
            # Log but don't fail, just leave as None
            pass

        # Weekly SMA
        sma_20_weekly = None
        try:
            weekly_df = self.nse_master.get_history(
                symbol=symbol,
                exchange="NSE",
                interval="1w"
            )
            if weekly_df is not None and not weekly_df.empty:
                ta_weekly = TechnicalAnalysisService(weekly_df)
                ta_weekly.add_trend_indicators()
                sma_20_weekly = float(ta_weekly.df.iloc[-1].get('sma_20', ltp))
        except Exception as e:
            pass
        
        # Extract derivatives data if available
        delta = None
        gamma = None
        theta = None
        vega = None
        oi_change = None
        
        if option_data:
            # Extract from explicitly provided option data
            delta = option_data.get('delta')
            gamma = option_data.get('gamma')
            theta = option_data.get('theta')
            vega = option_data.get('vega')
            oi_change = option_data.get('oi_change')
        else:
            # Try fetching real-time Option Chain for Sentiment
            try:
                # We want aggregate OI change to gauge sentiment
                oc_df = self.nse_derivatives.get_option_chain(symbol)
                if not oc_df.empty:
                    # Sum up Change in OI for Calls vs Puts near ATM?
                    # For simple version: Sum of all ChangeInOI (Positive = accumulation)
                    # Note: Calls OI Change - Puts OI Change could be a metric, but let's stick to total activity
                    # Or better: PCR of OI Change?
                    
                    # SentimentPillar logic looks at "snapshot.oi_change".
                    # Let's aggregate total OI Change for Puts - Total OI Change for Calls?
                    # Or just the raw net OI change of the active contract?
                    
                    # Simplification: Sum of all OI Change
                    ce_oi_chg = oc_df['CALLS_Chng_in_OI'].sum() if 'CALLS_Chng_in_OI' in oc_df else 0
                    pe_oi_chg = oc_df['PUTS_Chng_in_OI'].sum() if 'PUTS_Chng_in_OI' in oc_df else 0
                    
                    # Net OI Change: (PE OI Chg) - (CE OI Chg) ? 
                    # Actually standard interpretation:
                    # High PE OI Chg = Bullish (Support building)
                    # High CE OI Chg = Bearish (Resistance building)
                    # Let's map this to a single number "oi_change" that SentimentPillar expects.
                    # SentimentPillar: "Positive OI change suggests new positions"
                    
                    # Let's store total absolute OI change as activity proxy, 
                    # OR specific net flow.
                    
                    # For now, let's just pass the total OI of the near ATM strikes or just total
                    oi_change = (pe_oi_chg + ce_oi_chg) # Net market activity
                    
                    # Also try to get Greeks if possible (requires Black-Scholes, usually not in raw chain)
                    # We leave Greeks as None for now unless calculated elsewhere
            except Exception as e:
                pass
        
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
            # Real-time L2 fields
            bid_price=bid_price,
            ask_price=ask_price,
            bid_qty=bid_qty,
            ask_qty=ask_qty,
            spread_pct=spread_pct,
            # Derivatives fields
            delta=delta,
            gamma=gamma,
            theta=theta,
            vega=vega,
            oi_change=oi_change,
            # Sentinel Data Implementation
            **self._fetch_sentinel_data(symbol)
        )
    
    def _fetch_sentinel_data(self, symbol: str) -> dict:
        """
        Fetch and aggregate insider/institutional data for the symbol.
        Last 30 days.
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
                # Normalize symbol column (case-insensitive, strip whitespace)
                if 'symbol' in insider_df.columns:
                    symbol_trades = insider_df[insider_df['symbol'].str.strip() == symbol]
                elif 'Symbol' in insider_df.columns:
                    symbol_trades = insider_df[insider_df['Symbol'].str.strip() == symbol]
                else:
                    symbol_trades = pd.DataFrame()

                if not symbol_trades.empty:
                    for _, trade in symbol_trades.iterrows():
                        # secVal is the value column in this API version
                        val = float(trade.get('secVal', trade.get('valueInRs', 0)))
                        
                        # Check acqMode and tdpTransactionType
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
                # Clean column names (strip whitespace and special chars)
                bulk_df.columns = [c.strip().replace('ï»¿"', '').replace('"', '') for c in bulk_df.columns]
                
                if 'Symbol' in bulk_df.columns:
                    symbol_bulk = bulk_df[bulk_df['Symbol'].str.strip() == symbol]
                    if not symbol_bulk.empty:
                        for _, deal in symbol_bulk.iterrows():
                            # Quantity Traded, Buy / Sell
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
                        # Percentage of Short Quantity
                        sentinel["short_selling_pct"] = float(str(symbol_short.iloc[-1].get('Percentage of Short Quantity', 0)).replace(',', ''))
                    
        except Exception as e:
            # Log but continue
            pass
            
        return sentinel
    
    def build_session_context(
        self,
        nifty_df: Optional[pd.DataFrame] = None
    ) -> SessionContext:
        """
        Build SessionContext from market-wide data.
        
        Args:
            nifty_df: NIFTY 50 historical data (optional, will fetch if None)
            
        Returns:
            SessionContext with market regime and VIX
        """
        # Fetch NIFTY data if not provided
        if nifty_df is None or nifty_df.empty:
            nifty_df = self.nse_master.get_history(
                symbol="NIFTY 50",
                exchange="NSE",
                interval="1d"
            )
        
        # Determine market regime
        regime = "NEUTRAL"
        if nifty_df is not None and not nifty_df.empty:
            market_regime_analyzer = MarketRegime(nifty_df)
            regime_data = market_regime_analyzer.determine_regime()
            regime = regime_data.get('direction', 'NEUTRAL')
        
        # Get VIX
        vix_level = 15.0  # Default fallback
        vix_percentile = 50.0
        
        try:
            vix_df = self.nse_master.get_history(
                symbol="INDIA VIX",
                exchange="NSE",
                interval="1d"
            )
            if vix_df is not None and not vix_df.empty:
                vix_level = float(vix_df.iloc[-1]['Close'])
                # Calculate percentile (approximate using last 100 days)
                vix_percentile = (vix_df['Close'].rank(pct=True).iloc[-1]) * 100.0
        except Exception as e:
            logger.warning(f"Failed to fetch real VIX: {e}")
        
        return SessionContext(
            timestamp=datetime.now(),
            market_regime=regime,
            vix_level=vix_level,
            vix_percentile=vix_percentile
        )
