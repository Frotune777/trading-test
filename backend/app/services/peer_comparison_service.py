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

    async def get_peer_comparison(self, symbol: str) -> Dict[str, Any]:
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
                    "similarity_score": similarity_score,
                    "market_cap": float(peer.market_cap) if peer.market_cap else 0.0,
                    "return_30d": peer_metrics.get("return_30d", 0.0),
                    "volatility": peer_metrics.get("volatility", 0.0),
                    "beta": peer_metrics.get("beta", 1.0),
                    # Correlation is annotation only
                    "price_correlation": None  # Can be calculated separately if needed
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
            
            # Return top 5 peers
            top_peers = peers_data[:5]
            
            return {
                "symbol": symbol,
                "name": target_company.name,
                "sector": target_company.sector,
                "total_peers_in_sector": len(peer_companies),
                "peers_with_complete_data": len(peers_data),
                "target_metrics": {
                    "market_cap": float(target_company.market_cap) if target_company.market_cap else 0.0,
                    "return_30d": target_metrics.get("return_30d", 0.0),
                    "volatility": target_metrics.get("volatility", 0.0),
                    "beta": target_metrics.get("beta", 1.0)
                },
                "peers": top_peers
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
            # Get 30-day return from historical data
            thirty_days_ago = datetime.now() - timedelta(days=30)
            stmt = select(HistoricalOHLC).where(
                HistoricalOHLC.symbol == symbol,
                HistoricalOHLC.timestamp >= thirty_days_ago
            ).order_by(HistoricalOHLC.timestamp.asc())
            result = await self.db.execute(stmt)
            ohlc_data = result.scalars().all()
            
            if len(ohlc_data) < 2:
                return {"complete": False}
            
            return_30d = ((ohlc_data[-1].close - ohlc_data[0].close) / ohlc_data[0].close) * 100
            
            # Get risk metrics
            stmt = select(RiskMetrics).where(
                RiskMetrics.symbol == symbol
            ).order_by(RiskMetrics.calculated_at.desc()).limit(1)
            result = await self.db.execute(stmt)
            risk = result.scalar_one_or_none()
            
            if not risk or risk.volatility_30d is None or risk.beta_30d is None:
                return {"complete": False}
            
            # Get market cap
            stmt = select(Company).where(Company.symbol == symbol)
            result = await self.db.execute(stmt)
            company = result.scalar_one_or_none()
            
            if not company or company.market_cap is None:
                return {"complete": False}
            
            return {
                "complete": True,
                "return_30d": round(return_30d, 2),
                "volatility": round(float(risk.volatility_30d), 2),
                "beta": round(float(risk.beta_30d), 2),
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
        # Weights: market_cap=0.3, return=0.2, volatility=0.25, beta=0.25
        similarity = math.sqrt(
            (0.3 * mc_diff ** 2) +
            (0.2 * return_diff ** 2) +
            (0.25 * vol_diff ** 2) +
            (0.25 * beta_diff ** 2)
        )
        
        return round(similarity, 4)
