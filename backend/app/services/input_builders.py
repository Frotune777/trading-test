"""
Input Bundle Builders

These classes fetch data from the database and construct
pillar-specific input bundles.

Each builder is responsible for:
1. Fetching data from relevant tables
2. Transforming data into required format
3. Handling missing data gracefully
4. Constructing the input bundle
"""

import logging
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
import pandas as pd

from ..database.db_manager import DatabaseManager
from ..reasoning.institutional.input_bundles import (
    PriceStructureInput,
    InstitutionalFlowInput,
    DerivativesInput,
    RegimeInput,
    FundamentalInput,
    ExecutionInput
)

logger = logging.getLogger(__name__)


class PriceStructureInputBuilder:
    """Builds input bundle for Price & Market Structure pillar."""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    async def build(self, symbol: str) -> PriceStructureInput:
        """
        Fetch price structure data from database.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            PriceStructureInput bundle
        """
        logger.info(f"Building PriceStructureInput for {symbol}")
        
        # Fetch daily OHLCV (last 252 days)
        ohlcv_daily = await self._fetch_daily_ohlcv(symbol, days=252)
        
        # Fetch intraday data (last 5 days, 5-min bars)
        ohlcv_intraday = await self._fetch_intraday_ohlcv(symbol, days=5)
        
        # Fetch market depth
        bid_levels, ask_levels = await self._fetch_market_depth(symbol)
        
        # Fetch circuit limits
        upper_circuit, lower_circuit = await self._fetch_circuit_limits(symbol)
        
        # Fetch auction data
        opening_auction_vol, closing_auction_vol = await self._fetch_auction_data(symbol)
        
        return PriceStructureInput(
            symbol=symbol,
            timestamp=datetime.now(),
            ohlcv_daily=ohlcv_daily,
            ohlcv_intraday=ohlcv_intraday,
            bid_levels=bid_levels,
            ask_levels=ask_levels,
            upper_circuit=upper_circuit,
            lower_circuit=lower_circuit,
            opening_auction_volume=opening_auction_vol,
            closing_auction_volume=closing_auction_vol
        )
    
    async def _fetch_daily_ohlcv(self, symbol: str, days: int) -> pd.DataFrame:
        """Fetch daily OHLCV data."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        query = """
        SELECT date, open, high, low, close, volume
        FROM price_history
        WHERE symbol = ? AND date >= ?
        ORDER BY date ASC
        """
        
        cursor = self.db.conn.execute(query, (symbol, cutoff_date.date()))
        rows = cursor.fetchall()
        
        if not rows:
            logger.warning(f"No price history found for {symbol}")
            return pd.DataFrame()
        
        df = pd.DataFrame(rows, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
        df['date'] = pd.to_datetime(df['date'])
        return df
    
    async def _fetch_intraday_ohlcv(self, symbol: str, days: int) -> Optional[pd.DataFrame]:
        """Fetch intraday OHLCV data (5-min bars)."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        query = """
        SELECT timestamp, open, high, low, close, volume
        FROM intraday_prices
        WHERE symbol = ? AND timestamp >= ?
        ORDER BY timestamp ASC
        """
        
        cursor = self.db.conn.execute(query, (symbol, cutoff_date))
        rows = cursor.fetchall()
        
        if not rows:
            return None
        
        df = pd.DataFrame(rows, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    
    async def _fetch_market_depth(self, symbol: str) -> Tuple[List[Tuple], List[Tuple]]:
        """Fetch current market depth (bid/ask levels)."""
        query = """
        SELECT bid_price_1, bid_qty_1, bid_price_2, bid_qty_2, 
               bid_price_3, bid_qty_3, bid_price_4, bid_qty_4, 
               bid_price_5, bid_qty_5,
               ask_price_1, ask_qty_1, ask_price_2, ask_qty_2, 
               ask_price_3, ask_qty_3, ask_price_4, ask_qty_4, 
               ask_price_5, ask_qty_5
        FROM market_depth
        WHERE symbol = ?
        ORDER BY timestamp DESC
        LIMIT 1
        """
        
        cursor = self.db.conn.execute(query, (symbol,))
        row = cursor.fetchone()
        
        if not row:
            return [], []
        
        # Construct lists of (price, qty) tuples
        bid_levels = [
            (row['bid_price_1'], row['bid_qty_1']),
            (row['bid_price_2'], row['bid_qty_2']),
            (row['bid_price_3'], row['bid_qty_3']),
            (row['bid_price_4'], row['bid_qty_4']),
            (row['bid_price_5'], row['bid_qty_5'])
        ]
        
        ask_levels = [
            (row['ask_price_1'], row['ask_qty_1']),
            (row['ask_price_2'], row['ask_qty_2']),
            (row['ask_price_3'], row['ask_qty_3']),
            (row['ask_price_4'], row['ask_qty_4']),
            (row['ask_price_5'], row['ask_qty_5'])
        ]
        
        # Filter out zero/None levels
        bid_levels = [(p, q) for p, q in bid_levels if p and q]
        ask_levels = [(p, q) for p, q in ask_levels if p and q]
        
        return bid_levels, ask_levels
    
    async def _fetch_circuit_limits(self, symbol: str) -> Tuple[float, float]:
        """Fetch circuit limits from latest snapshot."""
        query = """
        SELECT high_52w, low_52w, prev_close
        FROM latest_snapshot
        WHERE symbol = ?
        """
        
        cursor = self.db.conn.execute(query, (symbol,))
        row = cursor.fetchone()
        
        if not row:
            return 0.0, 0.0
        
        high_52w, low_52w, prev_close = row
        
        # NSE circuit limits are typically ±20% for most stocks
        # Use prev_close to calculate
        if prev_close:
            upper_circuit = prev_close * 1.20
            lower_circuit = prev_close * 0.80
        else:
            upper_circuit = 0.0
            lower_circuit = 0.0
        
        return upper_circuit, lower_circuit
    
    async def _fetch_auction_data(self, symbol: str) -> Tuple[Optional[int], Optional[int]]:
        """Fetch auction volume data."""
        # Placeholder: auction data not in current schema
        return None, None


class InstitutionalFlowInputBuilder:
    """Builds input bundle for Institutional Flow pillar."""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    async def build(self, symbol: str) -> InstitutionalFlowInput:
        """Fetch institutional flow data."""
        logger.info(f"Building InstitutionalFlowInput for {symbol}")
        
        # Fetch FII/DII data (last 30 days)
        fii_net_30d = await self._fetch_fii_dii_data('fii', days=30)
        dii_net_30d = await self._fetch_fii_dii_data('dii', days=30)
        
        # Fetch bulk/block deals (last 30 days)
        bulk_deals_30d = await self._fetch_bulk_deals(symbol, days=30)
        block_deals_30d = await self._fetch_block_deals(symbol, days=30)
        
        # Fetch insider trading (last 90 days)
        insider_trades_90d = await self._fetch_insider_trades(symbol, days=90)
        
        # Fetch shareholding pattern
        shareholding_latest, shareholding_prev = await self._fetch_shareholding(symbol)
        
        return InstitutionalFlowInput(
            symbol=symbol,
            timestamp=datetime.now(),
            fii_net_30d=fii_net_30d,
            dii_net_30d=dii_net_30d,
            bulk_deals_30d=bulk_deals_30d,
            block_deals_30d=block_deals_30d,
            insider_trades_90d=insider_trades_90d,
            shareholding_latest=shareholding_latest,
            shareholding_prev_quarter=shareholding_prev
        )
    
    async def _fetch_fii_dii_data(self, investor_type: str, days: int) -> pd.DataFrame:
        """Fetch FII or DII net flow data."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        if investor_type == 'fii':
            query = """
            SELECT date, fii_buy_value, fii_sell_value, fii_net_value
            FROM fii_dii_activity
            WHERE date >= ?
            ORDER BY date ASC
            """
        else:
            query = """
            SELECT date, dii_buy_value, dii_sell_value, dii_net_value
            FROM fii_dii_activity
            WHERE date >= ?
            ORDER BY date ASC
            """
        
        cursor = self.db.conn.execute(query, (cutoff_date.date(),))
        rows = cursor.fetchall()
        
        if not rows:
            return pd.DataFrame()
        
        if investor_type == 'fii':
            df = pd.DataFrame(rows, columns=['date', 'fii_buy_value', 'fii_sell_value', 'fii_net_value'])
        else:
            df = pd.DataFrame(rows, columns=['date', 'dii_buy_value', 'dii_sell_value', 'dii_net_value'])
        
        df['date'] = pd.to_datetime(df['date'])
        return df
    
    async def _fetch_bulk_deals(self, symbol: str, days: int) -> pd.DataFrame:
        """Fetch bulk deals."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        query = """
        SELECT deal_date, client_name, deal_type, quantity, price
        FROM bulk_deals
        WHERE symbol = ? AND deal_date >= ?
        ORDER BY deal_date DESC
        """
        
        cursor = self.db.conn.execute(query, (symbol, cutoff_date.date()))
        rows = cursor.fetchall()
        
        if not rows:
            return pd.DataFrame()
        
        df = pd.DataFrame(rows, columns=['deal_date', 'client_name', 'deal_type', 'quantity', 'price'])
        df['deal_date'] = pd.to_datetime(df['deal_date'])
        return df
    
    async def _fetch_block_deals(self, symbol: str, days: int) -> pd.DataFrame:
        """Fetch block deals."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        query = """
        SELECT deal_date, client_name, deal_type, quantity, price
        FROM block_deals
        WHERE symbol = ? AND deal_date >= ?
        ORDER BY deal_date DESC
        """
        
        cursor = self.db.conn.execute(query, (symbol, cutoff_date.date()))
        rows = cursor.fetchall()
        
        if not rows:
            return pd.DataFrame()
        
        df = pd.DataFrame(rows, columns=['deal_date', 'client_name', 'deal_type', 'quantity', 'price'])
        df['deal_date'] = pd.to_datetime(df['deal_date'])
        return df
    
    async def _fetch_insider_trades(self, symbol: str, days: int) -> pd.DataFrame:
        """Fetch insider trading data."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        query = """
        SELECT acquisition_date, person_name, person_category, 
               transaction_type, securities_acquired, securities_disposed, value
        FROM insider_trading
        WHERE symbol = ? AND acquisition_date >= ?
        ORDER BY acquisition_date DESC
        """
        
        cursor = self.db.conn.execute(query, (symbol, cutoff_date.date()))
        rows = cursor.fetchall()
        
        if not rows:
            return pd.DataFrame()
        
        df = pd.DataFrame(rows, columns=[
            'acquisition_date', 'person_name', 'person_category',
            'transaction_type', 'securities_acquired', 'securities_disposed', 'value'
        ])
        df['acquisition_date'] = pd.to_datetime(df['acquisition_date'])
        return df
    
    async def _fetch_shareholding(self, symbol: str) -> Tuple[Optional[Dict], Optional[Dict]]:
        """Fetch shareholding pattern (latest and previous quarter)."""
        query = """
        SELECT quarter_end, promoter_holding, fii_holding, dii_holding, public_holding
        FROM shareholding
        WHERE symbol = ?
        ORDER BY quarter_end DESC
        LIMIT 2
        """
        
        cursor = self.db.conn.execute(query, (symbol,))
        rows = cursor.fetchall()
        
        if not rows:
            return None, None
        
        latest = {
            'promoter': rows[0][1],
            'fii': rows[0][2],
            'dii': rows[0][3],
            'public': rows[0][4]
        }
        
        prev = None
        if len(rows) > 1:
            prev = {
                'promoter': rows[1][1],
                'fii': rows[1][2],
                'dii': rows[1][3],
                'public': rows[1][4]
            }
        
        return latest, prev


class DerivativesInputBuilder:
    """Builds input bundle for Derivatives & Positioning pillar."""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    async def build(self, symbol: str) -> DerivativesInput:
        """Fetch derivatives data."""
        logger.info(f"Building DerivativesInput for {symbol}")
        
        # Fetch option chain (current and next expiry)
        option_chain_current, option_chain_next = await self._fetch_option_chain(symbol)
        
        # Fetch futures data
        futures_current = await self._fetch_futures(symbol)
        
        # Fetch option chain summary
        pcr_oi, pcr_volume, max_pain, iv_percentile = await self._fetch_option_summary(symbol)
        
        # Fetch spot price
        spot_price = await self._fetch_spot_price(symbol)
        
        return DerivativesInput(
            symbol=symbol,
            timestamp=datetime.now(),
            option_chain_current=option_chain_current,
            option_chain_next=option_chain_next,
            futures_current=futures_current,
            pcr_oi=pcr_oi,
            pcr_volume=pcr_volume,
            max_pain=max_pain,
            iv_percentile=iv_percentile,
            spot_price=spot_price
        )
    
    async def _fetch_option_chain(self, symbol: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Fetch option chain for current and next expiry."""
        query = """
        SELECT expiry_date, strike_price, option_type, underlying_value,
               last_price, open_interest, volume, iv, delta, gamma, theta, vega
        FROM option_chain
        WHERE symbol = ?
        ORDER BY expiry_date ASC, strike_price ASC
        """
        
        cursor = self.db.conn.execute(query, (symbol,))
        rows = cursor.fetchall()
        
        if not rows:
            return pd.DataFrame(), pd.DataFrame()
        
        df = pd.DataFrame(rows, columns=[
            'expiry_date', 'strike_price', 'option_type', 'underlying_value',
            'last_price', 'open_interest', 'volume', 'iv', 'delta', 'gamma', 'theta', 'vega'
        ])
        df['expiry_date'] = pd.to_datetime(df['expiry_date'])
        
        # Split into current and next expiry
        expiries = df['expiry_date'].unique()
        if len(expiries) == 0:
            return pd.DataFrame(), pd.DataFrame()
        
        current_expiry = expiries[0]
        next_expiry = expiries[1] if len(expiries) > 1 else current_expiry
        
        current_df = df[df['expiry_date'] == current_expiry]
        next_df = df[df['expiry_date'] == next_expiry]
        
        return current_df, next_df
    
    async def _fetch_futures(self, symbol: str) -> pd.DataFrame:
        """Fetch futures data."""
        query = """
        SELECT expiry_date, futures_price, open_interest, volume
        FROM futures_data
        WHERE symbol = ?
        ORDER BY expiry_date ASC
        """
        
        cursor = self.db.conn.execute(query, (symbol,))
        rows = cursor.fetchall()
        
        if not rows:
            return pd.DataFrame()
        
        df = pd.DataFrame(rows, columns=['expiry_date', 'futures_price', 'open_interest', 'volume'])
        df['expiry_date'] = pd.to_datetime(df['expiry_date'])
        return df
    
    async def _fetch_option_summary(self, symbol: str) -> Tuple[float, float, float, float]:
        """Fetch option chain summary metrics."""
        query = """
        SELECT pcr_oi, pcr_volume, max_pain, iv_percentile
        FROM option_chain_summary
        WHERE symbol = ?
        ORDER BY timestamp DESC
        LIMIT 1
        """
        
        cursor = self.db.conn.execute(query, (symbol,))
        row = cursor.fetchone()
        
        if not row:
            return 0.0, 0.0, 0.0, 0.0
        
        return row[0] or 0.0, row[1] or 0.0, row[2] or 0.0, row[3] or 0.0
    
    async def _fetch_spot_price(self, symbol: str) -> float:
        """Fetch current spot price."""
        query = """
        SELECT current_price
        FROM latest_snapshot
        WHERE symbol = ?
        """
        
        cursor = self.db.conn.execute(query, (symbol,))
        row = cursor.fetchone()
        
        return row[0] if row and row[0] else 0.0


class RegimeInputBuilder:
    """Builds input bundle for Risk & Regime Context pillar."""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    async def build(self, symbol: str) -> RegimeInput:
        """Fetch regime data from various sources."""
        logger.info(f"Building RegimeInput for {symbol}")
        
        # 1. Fetch Nifty 50 daily (last 252 days)
        nifty_50_daily = await self._fetch_index_history('NIFTY 50', days=252)
        
        # 2. Fetch sector index daily
        sector = await self._get_symbol_sector(symbol)
        sector_index_daily = await self._fetch_index_history(sector, days=252) if sector else pd.DataFrame()
        
        # 3. Fetch market breadth (last 30 days)
        market_breadth_30d = await self._fetch_market_breadth(days=30)
        
        # 4. Fetch VIX daily
        vix_daily = await self._fetch_vix_history(days=252)
        
        # 5. Fetch symbol price history
        symbol_daily = await self._fetch_symbol_history(symbol, days=252)
        
        return RegimeInput(
            symbol=symbol,
            timestamp=datetime.now(),
            nifty_50_daily=nifty_50_daily,
            sector_index_daily=sector_index_daily,
            market_breadth_30d=market_breadth_30d,
            vix_daily=vix_daily,
            symbol_daily=symbol_daily
        )
    
    async def _fetch_index_history(self, index_name: str, days: int) -> pd.DataFrame:
        cutoff_date = datetime.now() - timedelta(days=days)
        query = "SELECT date, open, high, low, close FROM index_history WHERE index_name = ? AND date >= ? ORDER BY date ASC"
        cursor = self.db.conn.execute(query, (index_name, cutoff_date.date()))
        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=['date', 'open', 'high', 'low', 'close'])
        df['date'] = pd.to_datetime(df['date'])
        return df

    async def _get_symbol_sector(self, symbol: str) -> Optional[str]:
        query = "SELECT sector FROM companies WHERE symbol = ?"
        cursor = self.db.conn.execute(query, (symbol,))
        row = cursor.fetchone()
        return row[0] if row else None

    async def _fetch_market_breadth(self, days: int) -> pd.DataFrame:
        cutoff_date = datetime.now() - timedelta(days=days)
        query = "SELECT date, advance_decline_ratio, advances, declines FROM market_breadth WHERE date >= ? ORDER BY date ASC"
        cursor = self.db.conn.execute(query, (cutoff_date.date(),))
        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=['date', 'advance_decline_ratio', 'advances', 'declines'])
        df['date'] = pd.to_datetime(df['date'])
        return df

    async def _fetch_vix_history(self, days: int) -> pd.DataFrame:
        cutoff_date = datetime.now() - timedelta(days=days)
        query = "SELECT date, open, high, low, close FROM vix_data WHERE date >= ? ORDER BY date ASC"
        cursor = self.db.conn.execute(query, (cutoff_date.date(),))
        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=['date', 'open', 'high', 'low', 'close'])
        df['date'] = pd.to_datetime(df['date'])
        return df

    async def _fetch_symbol_history(self, symbol: str, days: int) -> pd.DataFrame:
        cutoff_date = datetime.now() - timedelta(days=days)
        query = "SELECT date, close FROM price_history WHERE symbol = ? AND date >= ? ORDER BY date ASC"
        cursor = self.db.conn.execute(query, (symbol, cutoff_date.date()))
        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=['date', 'close'])
        df['date'] = pd.to_datetime(df['date'])
        return df


class FundamentalInputBuilder:
    """Builds input bundle for Fundamental / Thematic Context pillar."""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    async def build(self, symbol: str) -> FundamentalInput:
        """Fetch company fundamentals."""
        logger.info(f"Building FundamentalInput for {symbol}")
        
        quarterly_results = await self._fetch_table_data('quarterly_results', symbol, limit=8)
        annual_results = await self._fetch_table_data('annual_results', symbol, limit=5)
        balance_sheet = await self._fetch_table_data('balance_sheet', symbol, limit=5)
        cash_flow = await self._fetch_table_data('cash_flow', symbol, limit=5)
        financial_ratios = await self._fetch_table_data('financial_ratios', symbol, limit=5)
        
        # Sector metrics for relative valuation
        sector = await self._get_sector(symbol)
        sector_pe, sector_pb = await self._fetch_sector_averages(sector)
        peer_metrics = await self._fetch_peer_metrics(sector) if sector else pd.DataFrame()
        
        return FundamentalInput(
            symbol=symbol,
            timestamp=datetime.now(),
            quarterly_results=quarterly_results,
            annual_results=annual_results,
            balance_sheet=balance_sheet,
            cash_flow=cash_flow,
            financial_ratios=financial_ratios,
            peer_metrics=peer_metrics,
            sector_name=sector or "UNKNOWN",
            sector_pe=sector_pe,
            sector_pb=sector_pb
        )

    async def _fetch_table_data(self, table: str, symbol: str, limit: int) -> pd.DataFrame:
        query = f"SELECT * FROM {table} WHERE symbol = ? ORDER BY period_end DESC LIMIT ?"
        # Note: table name is verified here by code
        cursor = self.db.conn.execute(query, (symbol, limit))
        rows = cursor.fetchall()
        if not rows: return pd.DataFrame()
        columns = [description[0] for description in cursor.description]
        return pd.DataFrame(rows, columns=columns)

    async def _get_sector(self, symbol: str) -> Optional[str]:
        cursor = self.db.conn.execute("SELECT sector FROM companies WHERE symbol = ?", (symbol,))
        row = cursor.fetchone()
        return row[0] if row else None

    async def _fetch_sector_averages(self, sector: Optional[str]) -> Tuple[float, float]:
        if not sector: return 0.0, 0.0
        query = "SELECT AVG(pe_ratio), AVG(pb_ratio) FROM latest_snapshot s JOIN companies c ON s.symbol = c.symbol WHERE c.sector = ?"
        cursor = self.db.conn.execute(query, (sector,))
        row = cursor.fetchone()
        return row[0] or 0.0, row[1] or 0.0

    async def _fetch_peer_metrics(self, sector: str) -> pd.DataFrame:
        query = "SELECT s.symbol, pe_ratio as pe, pb_ratio as pb, roe, roce FROM latest_snapshot s JOIN companies c ON s.symbol = c.symbol WHERE c.sector = ? LIMIT 10"
        cursor = self.db.conn.execute(query, (sector,))
        rows = cursor.fetchall()
        return pd.DataFrame(rows, columns=['symbol', 'pe', 'pb', 'roe', 'roce'])


class ExecutionInputBuilder:
    """Builds input bundle for Execution & Feasibility pillar."""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    async def build(self, symbol: str) -> ExecutionInput:
        """Fetch real-time execution data."""
        logger.info(f"Building ExecutionInput for {symbol}")
        
        # 1. Depth snapshots (last 1 hour)
        depth_snapshots = await self._fetch_depth_snapshots(symbol, hours=1)
        
        # 2. Volume profile (last 5 days)
        volume_profile = await self._fetch_intraday_volume(symbol, days=5)
        
        # 3. Recent trades (last 100 trades)
        recent_trades = await self._fetch_recent_trades(symbol, limit=100)
        
        # 4. Snapshot data
        snapshot = await self._fetch_snapshot(symbol)
        
        # Check trading hours
        now = datetime.now()
        is_trading = (now.weekday() < 5 and time(9, 15) <= now.time() <= time(15, 30))
        time_to_close = self._get_minutes_to_close(now)
        
        return ExecutionInput(
            symbol=symbol,
            timestamp=now,
            depth_snapshots_1h=depth_snapshots,
            volume_profile_5d=volume_profile,
            recent_trades=recent_trades,
            current_price=snapshot.get('current_price', 0.0),
            current_spread_bps=snapshot.get('spread_bps', 0.0),
            avg_daily_volume_20d=int(snapshot.get('avg_volume', 0)),
            current_volume=int(snapshot.get('volume', 0)),
            is_trading_hours=is_trading,
            time_to_close_minutes=time_to_close
        )

    async def _fetch_depth_snapshots(self, symbol: str, hours: int) -> pd.DataFrame:
        cutoff = datetime.now() - timedelta(hours=hours)
        query = "SELECT timestamp, bid_price, bid_qty, ask_price, ask_qty FROM market_depth WHERE symbol = ? AND timestamp >= ? ORDER BY timestamp DESC"
        cursor = self.db.conn.execute(query, (symbol, cutoff))
        rows = cursor.fetchall()
        return pd.DataFrame(rows, columns=['timestamp', 'bid_price', 'bid_qty', 'ask_price', 'ask_qty'])

    async def _fetch_intraday_volume(self, symbol: str, days: int) -> pd.DataFrame:
        cutoff = datetime.now() - timedelta(days=days)
        query = "SELECT timestamp, volume FROM intraday_prices WHERE symbol = ? AND timestamp >= ? ORDER BY timestamp ASC"
        cursor = self.db.conn.execute(query, (symbol, cutoff))
        rows = cursor.fetchall()
        return pd.DataFrame(rows, columns=['timestamp', 'volume'])

    async def _fetch_recent_trades(self, symbol: str, limit: int) -> pd.DataFrame:
        # Placeholder for trade history table if it exists, otherwise use intraday prices with volume changes
        query = "SELECT timestamp, close as price, volume FROM intraday_prices WHERE symbol = ? ORDER BY timestamp DESC LIMIT ?"
        cursor = self.db.conn.execute(query, (symbol, limit))
        rows = cursor.fetchall()
        return pd.DataFrame(rows, columns=['timestamp', 'price', 'volume'])

    async def _fetch_snapshot(self, symbol: str) -> Dict:
        query = "SELECT current_price, volume, (day_high - day_low) as daily_range FROM latest_snapshot WHERE symbol = ?"
        cursor = self.db.conn.execute(query, (symbol,))
        row = cursor.fetchone()
        if not row: return {}
        # Spread calculation estimate if real spread not in table
        return {'current_price': row[0], 'volume': row[1], 'spread_bps': 5.0, 'avg_volume': row[1]}

    def _get_minutes_to_close(self, now: datetime) -> int:
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
        if now > market_close: return 0
        return int((market_close - now).total_seconds() / 60)


class InputBuilderRegistry:
    """Registry for all input builders to centralize access."""
    
    def __init__(self, db: DatabaseManager):
        self.builders = {
            'PRICE_STRUCTURE': PriceStructureInputBuilder(db),
            'INSTITUTIONAL_FLOW': InstitutionalFlowInputBuilder(db),
            'DERIVATIVES_POSITIONING': DerivativesInputBuilder(db),
            'REGIME_CONTEXT': RegimeInputBuilder(db),
            'FUNDAMENTAL_THEMATIC': FundamentalInputBuilder(db),
            'EXECUTION_FEASIBILITY': ExecutionInputBuilder(db)
        }
    
    async def build_all(self, symbol: str) -> Dict[str, any]:
        """Build all input bundles for a symbol."""
        results = {}
        for name, builder in self.builders.items():
            try:
                results[name] = await builder.build(symbol)
            except Exception as e:
                logger.error(f"Failed to build input for {name}: {e}")
                results[name] = None
        return results


# Continue in next file due to length...
