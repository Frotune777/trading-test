"""
Pillar-Specific Input Bundles

These dataclasses define isolated input data for each pillar.
NO SHARED STATE across pillars.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import pandas as pd


@dataclass
class PriceStructureInput:
    """
    Input bundle for PILLAR 1: Price & Market Structure
    """
    symbol: str
    timestamp: datetime
    
    # Raw price data (from price_history table)
    ohlcv_daily: pd.DataFrame  # Last 252 days
    ohlcv_intraday: Optional[pd.DataFrame] = None  # Last 5 days, 5-min bars
    
    # Market depth (from market_depth table)
    bid_levels: List[Tuple[float, int]] = None  # [(price, qty), ...]
    ask_levels: List[Tuple[float, int]] = None
    
    # Auction data (if available)
    opening_auction_volume: Optional[int] = None
    closing_auction_volume: Optional[int] = None
    
    # Circuit limits
    upper_circuit: float = 0.0
    lower_circuit: float = 0.0


@dataclass
class InstitutionalFlowInput:
    """
    Input bundle for PILLAR 2: Institutional Flow
    """
    symbol: str
    timestamp: datetime
    
    # FII/DII data (from fii_dii_activity table)
    fii_net_30d: pd.DataFrame  # Last 30 days of FII flow
    dii_net_30d: pd.DataFrame
    
    # Bulk/Block deals (from bulk_deals, block_deals tables)
    bulk_deals_30d: pd.DataFrame
    block_deals_30d: pd.DataFrame
    
    # Insider trading (from insider_trading table)
    insider_trades_90d: pd.DataFrame
    
    # Shareholding pattern (from shareholding table)
    shareholding_latest: Dict[str, float] = None  # {promoter, fii, dii, public}
    shareholding_prev_quarter: Dict[str, float] = None


@dataclass
class DerivativesInput:
    """
    Input bundle for PILLAR 3: Derivatives & Positioning
    """
    symbol: str
    timestamp: datetime
    
    # Option chain (from option_chain table)
    option_chain_current: pd.DataFrame  # Current expiry
    option_chain_next: pd.DataFrame     # Next expiry
    
    # Futures data (from futures_data table)
    futures_current: pd.DataFrame
    
    # Aggregates (from option_chain_summary table)
    pcr_oi: float = 0.0
    pcr_volume: float = 0.0
    max_pain: float = 0.0
    iv_percentile: float = 0.0
    
    # Spot price for basis calculation
    spot_price: float = 0.0


@dataclass
class RegimeInput:
    """
    Input bundle for PILLAR 4: Risk & Regime Context
    """
    symbol: str
    timestamp: datetime
    
    # Index data (from index_history table)
    nifty_50_daily: pd.DataFrame  # Last 252 days
    sector_index_daily: pd.DataFrame
    
    # Market breadth (from market_breadth table)
    market_breadth_30d: pd.DataFrame
    
    # VIX data
    vix_daily: pd.DataFrame  # Last 252 days
    
    # Symbol's own price history for correlation
    symbol_daily: pd.DataFrame  # Last 252 days
    
    # Peer group for sector correlation
    peer_symbols: List[str] = None
    peer_prices: Dict[str, pd.DataFrame] = None


@dataclass
class FundamentalInput:
    """
    Input bundle for PILLAR 5: Fundamental / Thematic Context
    """
    symbol: str
    timestamp: datetime
    
    # Quarterly results (from quarterly_results table)
    quarterly_results: pd.DataFrame  # Last 8 quarters
    
    # Annual results (from annual_results table)
    annual_results: pd.DataFrame  # Last 5 years
    
    # Balance sheet (from balance_sheet table)
    balance_sheet: pd.DataFrame
    
    # Cash flow (from cash_flow table)
    cash_flow: pd.DataFrame
    
    # Financial ratios (from financial_ratios table)
    financial_ratios: pd.DataFrame
    
    # Peer comparison (from peers table)
    peer_metrics: pd.DataFrame
    
    # Sector performance
    sector_name: str = ""
    sector_pe: float = 0.0
    sector_pb: float = 0.0


@dataclass
class ExecutionInput:
    """
    Input bundle for PILLAR 6: Execution & Feasibility
    """
    symbol: str
    timestamp: datetime
    
    # Market depth (from market_depth table)
    depth_snapshots_1h: pd.DataFrame  # Last 1 hour of depth snapshots
    
    # Intraday volume profile (from intraday_prices table)
    volume_profile_5d: pd.DataFrame
    
    # Recent trades for slippage estimation
    recent_trades: pd.DataFrame  # Last 100 trades
    
    # Current state
    current_price: float = 0.0
    current_spread_bps: float = 0.0
    current_volume: int = 0
    avg_daily_volume_20d: int = 0
    
    # Exchange metadata
    lot_size: int = 1
    tick_size: float = 0.05
    is_trading_hours: bool = False
    time_to_close_minutes: int = 0
