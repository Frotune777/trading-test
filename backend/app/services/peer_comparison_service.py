"""
Peer Comparison Service
Compares QUAD scores across sector peers
"""
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from app.database.models_quad import QUADDecision
from app.api.v1.endpoints.stocks import get_stock_profile # Revisit this if circular import

# We need a way to get sector. For now, we might need to rely on what's available or hardcode/fetch.
# The stocks endpoint uses yfinance. We should probably cache sector info in DB.
# For this implementation, I'll assume we can query other QUAD decisions and group by sector if we had it.
# Since we don't have sector in QUADDecision, we can't easily group. 
# Plan B: Use a hardcoded map or fetch from yfinance on the fly (slow) or use the 'meta_data' field if it has sector.

logger = logging.getLogger(__name__)

class PeerComparisonService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_peer_comparison(self, symbol: str) -> Dict[str, Any]:
        """
        Get peer comparison for a symbol.
        In a real app, we'd query by sector. 
        For now, we'll return a ranking against all tracked symbols as a proxy.
        """
        try:
            # 1. Get latest decision for the requested symbol
            stmt = select(QUADDecision).where(
                QUADDecision.symbol == symbol.upper()
            ).order_by(QUADDecision.timestamp.desc()).limit(1)
            
            result = await self.db.execute(stmt)
            target_decision = result.scalar_one_or_none()
            
            if not target_decision:
                return {"error": f"No analysis found for {symbol}"}

            # 2. Get latest decisions for ALL symbols (as a simple peer group for now)
            # In production, we'd filter by checking each symbol's sector
            
            # Subquery to get max timestamp per symbol
            subq = select(
                QUADDecision.symbol,
                func.max(QUADDecision.timestamp).label('max_ts')
            ).group_by(QUADDecision.symbol).subquery()
            
            # Join to get full records
            stmt_all = select(QUADDecision).join(
                subq,
                and_(
                    QUADDecision.symbol == subq.c.symbol,
                    QUADDecision.timestamp == subq.c.max_ts
                )
            )
            
            all_results = await self.db.execute(stmt_all)
            all_decisions = all_results.scalars().all()
            
            # 3. Rank them and calculate stats
            if not all_decisions:
                return {
                    "symbol": symbol,
                    "rank": 0,
                    "total_peers": 0,
                    "avg_sector_conviction": 0,
                    "sector": "NIFTY",
                    "peers": []
                }

            # Sort by conviction desc
            ranked = sorted(all_decisions, key=lambda x: x.conviction, reverse=True)
            
            # Calculate average
            avg_conviction = sum(d.conviction for d in all_decisions) / len(all_decisions)
            
            peers = []
            target_rank = 0
            
            for i, d in enumerate(ranked):
                is_self = d.symbol == symbol.upper()
                if is_self:
                    target_rank = i + 1
                
                # Add top 10 for display
                if i < 10:
                    peers.append({
                        "symbol": d.symbol,
                        "conviction": d.conviction,
                        "rank": i + 1,
                        "signal": d.signal,
                        "is_self": is_self
                    })
            
            # If target not in top 10, check if we need to add it or handle it
            # The frontend logic seems to assume list of peers. 
            # If we want to strictly follow "Top 5 + Target + Nearby", we'd do more logic.
            # For now, top 10 is fine. If target is > 10, it won't show in list but rank is correct.
            
            # Ensure target is in the list for alpha calc if missing
            target_in_list = any(p['symbol'] == symbol.upper() for p in peers)
            if not target_in_list and target_decision:
                 peers.append({
                        "symbol": target_decision.symbol,
                        "conviction": target_decision.conviction,
                        "rank": target_rank,
                        "signal": target_decision.signal,
                        "is_self": True
                    })
            
            return {
                "symbol": symbol,
                "rank": target_rank,
                "total_peers": len(ranked),
                "avg_sector_conviction": avg_conviction,
                "sector": "NIFTY 50", # Placeholder
                "peers": peers
            }
            
        except Exception as e:
            logger.error(f"Error getting peer comparison: {e}")
            return {"peers": [], "error": str(e)}
