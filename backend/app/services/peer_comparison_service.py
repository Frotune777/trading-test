"""
Peer Comparison Service
Compares QUAD scores across sector peers with structural similarity ranking
"""
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from datetime import datetime, timedelta
from app.database.models_quad import Company, RiskMetrics
from app.database.models_historical import HistoricalOHLC

logger = logging.getLogger(__name__)

class PeerComparisonService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_peer_comparison(self, symbol: str, min_peers_required: int = 1) -> Dict[str, Any]:
        """
        Get peer comparison for a symbol.
        
        Rules:
        1. Sector matching is a HARD GATE - only same sector peers
        2. Structural similarity determines ranking (fixed metrics)
        3. Correlation is annotation only, never influences inclusion/rank
        4. If required metrics missing -> NO_PEERS
        
        Returns top 5 peers ranked by structural similarity
        """
        try:
            # 1. Get target company with sector
            stmt = select(Company).where(Company.symbol == symbol.upper())
            result = await self.db.execute(stmt)
            target_company = result.scalar_one_or_none()
            
            if not target_company:
                return {
                    "symbol": symbol,
                    "error": "NO_PEERS",
                    "reason": "Company not found in database",
                    "peers": []
                }
            
            if not target_company.sector:
                return {
                    "symbol": symbol,
                    "error": "NO_PEERS",
                    "reason": "Sector information missing for target company",
                    "peers": []
                }
            
            # 2. Find peers in same sector (HARD GATE)
            stmt = select(Company).where(
                Company.sector == target_company.sector,
                Company.symbol != symbol.upper()
            )
            result = await self.db.execute(stmt)
            peer_companies = result.scalars().all()
            
            if not peer_companies:
                return {
                    "symbol": symbol,
                    "sector": target_company.sector,
                    "error": "NO_PEERS",
                    "reason": f"No peers found in sector: {target_company.sector}",
                    "peers": []
                }
            
            # 3. Calculate structural similarity metrics for each peer
            target_metrics = await self._get_structural_metrics(symbol.upper())
            
            if not target_metrics or not target_metrics.get("complete"):
                return {
                    "symbol": symbol,
                    "sector": target_company.sector,
                    "error": "NO_PEERS",
                    "reason": "Required structural metrics missing for target symbol",
                    "peers": []
                }
            
            peers_data = []
            for peer in peer_companies:
                peer_metrics = await self._get_structural_metrics(peer.symbol)
                
                if not peer_metrics or not peer_metrics.get("complete"):
                    continue  # Skip peers with incomplete data
                
                # Calculate similarity score (lower is more similar)
                similarity_score = self._calculate_similarity(target_metrics, peer_metrics)
                
                peers_data.append({
                    "symbol": peer.symbol,
                    "name": peer.name,
                    "similarity_score": float(similarity_score),
                    "market_cap": float(peer.market_cap) if peer.market_cap else 0.0,
                    "return_30d": float(peer_metrics["return_30d"]),
                    "volatility": float(peer_metrics["volatility"]),
                    "beta": float(peer_metrics["beta"]),
                    "price_correlation": None  # Placeholder for future implementation
                })
            
            if not peers_data:
                return {
                    "symbol": symbol,
                    "sector": target_company.sector,
                    "error": "NO_PEERS",
                    "reason": "No peers with complete structural metrics",
                    "peers": []
                }
            
            # 4. Rank by structural similarity (ascending - lower score = more similar)
            peers_data.sort(key=lambda x: x["similarity_score"])
            
            # Check min_peers_required guardrail
            if len(peers_data) < min_peers_required:
                return {
                    "symbol": symbol,
                    "sector": target_company.sector,
                    "error": "NO_PEERS",
                    "reason": f"Only {len(peers_data)} peers found, minimum {min_peers_required} required",
                    "peers": []
                }
            
            # Build response with all floats
            return {
                "symbol": symbol,
                "name": target_company.name,
                "sector": target_company.sector,
                "total_peers_in_sector": len(peer_companies),
                "peers_with_complete_data": len(peers_data),
                "target_metrics": {
                    "market_cap": float(target_company.market_cap) if target_company.market_cap else 0.0,
                    "return_30d": float(target_metrics["return_30d"]),
                    "volatility": float(target_metrics["volatility"]),
                    "beta": float(target_metrics["beta"])
                },
                "peers": peers_data[:5]  # Top 5 most similar
            }
            
        except Exception as e:
            logger.error(f"Error getting peer comparison: {e}", exc_info=True)
            return {
                "symbol": symbol,
                "error": "NO_PEERS",
                "reason": f"Service error: {str(e)}",
                "peers": []
            }

    async def _get_structural_metrics(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get structural metrics for a symbol.
        Returns None if required metrics are missing.
        
        Required metrics:
        - 30-day return (from historical_ohlc)
        - Volatility (from risk_metrics)
        - Beta (from risk_metrics)
        - Market cap (from companies)
        """
        try:
            # Get last 30 trading days of data (not calendar days)
            # This works even if data is old
            stmt = select(HistoricalOHLC).where(
                HistoricalOHLC.symbol == symbol,
                HistoricalOHLC.interval == '1d'
            ).order_by(HistoricalOHLC.timestamp.desc()).limit(30)
            result = await self.db.execute(stmt)
            ohlc_data = result.scalars().all()
            
            if len(ohlc_data) < 2:
                return {"complete": False}
            
            # Reverse to get chronological order (oldest first)
            ohlc_data = list(reversed(ohlc_data))
            return_30d = ((ohlc_data[-1].close - ohlc_data[0].close) / ohlc_data[0].close) * 100
            
            # Get risk metrics
            stmt = select(RiskMetrics).where(
                RiskMetrics.symbol == symbol
            ).order_by(RiskMetrics.calculated_at.desc()).limit(1)
            result = await self.db.execute(stmt)
            risk = result.scalar_one_or_none()
            
            # Use 252d (1 year) metrics as primary, fallback to 60d, then 30d
            volatility = risk.volatility_252d or risk.volatility_60d or risk.volatility_30d
            beta = risk.beta_252d or risk.beta_60d or risk.beta_30d
            
            if volatility is None or beta is None:
                return {"complete": False}
            
            # Get market cap
            stmt = select(Company).where(Company.symbol == symbol)
            result = await self.db.execute(stmt)
            company = result.scalar_one_or_none()
            
            if not company or company.market_cap is None:
                return {"complete": False}
            
            return {
                "complete": True,
                "return_30d": float(round(return_30d, 2)),
                "volatility": float(volatility),
                "beta": float(beta),
                "market_cap": float(company.market_cap)
            }
            
        except Exception as e:
            logger.error(f"Error getting structural metrics for {symbol}: {e}")
            return {"complete": False}

    def _calculate_similarity(self, target: Dict, peer: Dict) -> float:
        """
        Calculate structural similarity score.
        Lower score = more similar.
        
        Uses normalized Euclidean distance across:
        - Market cap (log scale)
        - 30-day return
        - Volatility
        - Beta
        """
        import math
        
        # Convert Decimal to float for calculations
        target_mc = float(target["market_cap"])
        peer_mc = float(peer["market_cap"])
        target_return = float(target["return_30d"])
        peer_return = float(peer["return_30d"])
        target_vol = float(target["volatility"])
        peer_vol = float(peer["volatility"])
        target_beta = float(target["beta"])
        peer_beta = float(peer["beta"])
        
        # Normalize market cap using log scale
        target_mc_log = math.log10(max(target_mc, 1))
        peer_mc_log = math.log10(max(peer_mc, 1))
        mc_diff = abs(target_mc_log - peer_mc_log)
        
        # Normalize returns (already in %)
        return_diff = abs(target_return - peer_return) / 100.0
        
        # Normalize volatility
        vol_diff = abs(target_vol - peer_vol) / 100.0
        
        # Normalize beta
        beta_diff = abs(target_beta - peer_beta)
        
        # Weighted Euclidean distance
        # Rebalanced weights to reduce market cap dominance:
        # market_cap=0.2 (down from 0.3), return=0.25, volatility=0.3, beta=0.25
        mc_component = 0.2 * mc_diff ** 2
        return_component = 0.25 * return_diff ** 2
        vol_component = 0.3 * vol_diff ** 2
        beta_component = 0.25 * beta_diff ** 2
        
        similarity = math.sqrt(
            mc_component + return_component + vol_component + beta_component
        )
        
        # Log detailed breakdown
        logger.debug(
            f"Similarity calculation for {peer.get('symbol', 'unknown')}:\n"
            f"  Market Cap diff: {mc_diff:.4f} (contribution: {math.sqrt(mc_component):.4f})\n"
            f"  Return diff: {return_diff:.4f} (contribution: {math.sqrt(return_component):.4f})\n"
            f"  Volatility diff: {vol_diff:.4f} (contribution: {math.sqrt(vol_component):.4f})\n"
            f"  Beta diff: {beta_diff:.4f} (contribution: {math.sqrt(beta_component):.4f})\n"
            f"  Total similarity: {similarity:.4f}"
        )
        
        return float(round(similarity, 4))
