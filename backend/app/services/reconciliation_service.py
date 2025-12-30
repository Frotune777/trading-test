import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select
import asyncio

from app.database.models_position import (
    PositionSnapshot,
    PositionDiscrepancy,
    ReconciliationRun
)
from app.database.models_monitoring import TradePerformance
from app.services.broker_gateway import broker_gateway
from app.brokers.base_adapter import BrokerType, Position
from app.services.alert_service import AlertService
from app.core.database import SessionLocal # Import for singleton usage

logger = logging.getLogger(__name__)


class PositionReconciliationService:
    """
    Position Reconciliation Service
    
    Features:
        - Periodic reconciliation (every 5 min)
        - Discrepancy detection (Broker vs TradePerformance)
        - Auto-correction (optional)
        - Reconciliation reports
        - Alerts on mismatch
    
    Compliance:
        - Rule #38: UI reflects backend truth
        - Rule #33-37: All operations logged
    """
    
    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db
        self.alert_service = AlertService()
        self.auto_correct_enabled = False  # Safety: disabled by default
        self.reconciliation_interval = timedelta(minutes=5)
        self.max_auto_correct_quantity = 100  # Max quantity for auto-correction
    
    async def run_reconciliation(self, user_id: Optional[int] = None) -> ReconciliationRun:
        """
        Alias for reconcile_positions to match scheduler expectations.
        Automatically manages its own database session if not provided.
        """
        if self.db:
            return await self.reconcile_positions(user_id=user_id)
        
        async with SessionLocal() as db:
            self.db = db
            try:
                result = await self.reconcile_positions(user_id=user_id)
                # Note: reconcile_positions calls commit
                return result
            finally:
                self.db = None # Reset for next call
    
    async def reconcile_positions(
        self,
        broker_filter: Optional[BrokerType] = None,
        user_id: Optional[int] = None
    ) -> ReconciliationRun:
        """
        Reconcile positions with broker(s).
        
        Args:
            broker_filter: Specific broker to reconcile (None = all brokers)
            user_id: Specific user to reconcile (if applicable)
            
        Returns:
            ReconciliationRun record
        """
        start_time = datetime.now()
        
        # Determine brokers to check
        if broker_filter:
            brokers_to_check = [broker_filter]
        else:
            brokers_to_check = list(broker_gateway.brokers.keys())
        
        # Create reconciliation run record
        run = ReconciliationRun(
            run_time=start_time,
            brokers_checked=[b.value for b in brokers_to_check],
            status="RUNNING"
        )
        self.db.add(run)
        await self.db.commit()
        await self.db.refresh(run)
        
        logger.info(f"Starting reconciliation run {run.id} for {len(brokers_to_check)} brokers")
        
        try:
            total_positions = 0
            discrepancies_found = 0
            auto_corrections = 0
            
            # 1. Fetch live positions from all brokers
            broker_positions_map = {}
            for broker_type in brokers_to_check:
                positions = await self._get_broker_positions(broker_type)
                if positions is not None:
                    broker_positions_map[broker_type] = positions
                else:
                    logger.warning(f"Failed to fetch positions from {broker_type.value}")
            
            # 2. Fetch local open positions (TradePerformance with status='OPEN')
            stmt = select(TradePerformance).where(TradePerformance.status == "OPEN")
            if user_id:
                stmt = stmt.where(TradePerformance.user_id == user_id)
            
            result = await self.db.execute(stmt)
            local_trades = result.scalars().all()
            
            # Map local trades by symbol:exchange for easy comparison
            local_positions: Dict[str, Dict[str, Any]] = {}
            for trade in local_trades:
                key = f"{trade.symbol}:NSE"  # Default exchange if not specified
                if key not in local_positions:
                    local_positions[key] = {"quantity": 0, "avg_price": 0.0, "trades": []}
                
                total_qty = local_positions[key]["quantity"] + trade.quantity
                if total_qty > 0:
                    local_positions[key]["avg_price"] = (
                        (local_positions[key]["avg_price"] * local_positions[key]["quantity"]) +
                        (trade.entry_price * trade.quantity)
                    ) / total_qty
                
                local_positions[key]["quantity"] = total_qty
                local_positions[key]["trades"].append(trade)

            # 3. Compare broker vs local
            for broker_type, positions in broker_positions_map.items():
                broker_name = broker_type.value
                
                for pos in positions:
                    total_positions += 1
                    key = f"{pos.symbol}:{pos.exchange}"
                    
                    # Save Snapshot
                    snapshot = PositionSnapshot(
                        broker=broker_name,
                        symbol=pos.symbol,
                        exchange=pos.exchange,
                        quantity=pos.quantity,
                        average_price=float(pos.average_price),
                        pnl=float(pos.pnl) if pos.pnl else None,
                        product_type=pos.product if hasattr(pos, 'product') else None,
                        snapshot_time=start_time
                    )
                    self.db.add(snapshot)
                    
                    # Check against local
                    local_pos = local_positions.get(key)
                    if not local_pos:
                        # Rogue trade / manual trade at broker
                        await self._record_discrepancy(
                            run.id, pos.symbol, pos.exchange, broker_name,
                            0, pos.quantity, float(pos.average_price), 0.0
                        )
                        discrepancies_found += 1
                    else:
                        qty_diff = pos.quantity - local_pos["quantity"]
                        price_diff_percent = abs(float(pos.average_price) - local_pos["avg_price"]) / (local_pos["avg_price"] or 1.0)
                        
                        if qty_diff != 0 or price_diff_percent > 0.001:
                            await self._record_discrepancy(
                                run.id, pos.symbol, pos.exchange, broker_name,
                                local_pos["quantity"], pos.quantity, 
                                float(pos.average_price), local_pos["avg_price"]
                            )
                            discrepancies_found += 1
                        
                        # Mark as processed
                        local_pos["processed"] = True
            
            # Check for local positions missing from broker
            for key, data in local_positions.items():
                if not data.get("processed") and data["quantity"] != 0:
                    symbol, exchange = key.split(':')
                    await self._record_discrepancy(
                        run.id, symbol, exchange, "ANY",
                        data["quantity"], 0, 0.0, data["avg_price"]
                    )
                    discrepancies_found += 1
            
            # Update run record
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            run.total_positions = total_positions
            run.discrepancies_found = discrepancies_found
            run.auto_corrections = auto_corrections
            run.status = "COMPLETED"
            run.duration_ms = duration_ms
            run.completed_at = datetime.now()
            
            await self.db.commit()
            
            if discrepancies_found > 0:
                await self.alert_service.emit(
                    alert_type="POSITION_DRIFT",
                    message=f"Detected {discrepancies_found} position discrepancies during reconciliation run {run.id}.",
                    level="WARNING",
                    metadata={"run_id": run.id, "discrepancies": discrepancies_found}
                )
            
            logger.info(
                f"Reconciliation run {run.id} completed: "
                f"{total_positions} positions, {discrepancies_found} discrepancies in {duration_ms}ms"
            )
            
            return run
            
        except Exception as e:
            logger.error(f"Reconciliation run {run.id} failed: {e}", exc_info=True)
            run.status = "FAILED"
            run.error_message = str(e)
            run.completed_at = datetime.now()
            await self.db.commit()
            raise
    
    async def _get_broker_positions(
        self,
        broker_type: BrokerType
    ) -> Optional[List[Position]]:
        """Get positions from broker"""
        try:
            if broker_type not in broker_gateway.brokers:
                return None
            
            broker = broker_gateway.brokers[broker_type]
            positions = await broker.get_positions()
            
            return positions if positions is not None else []
            
        except Exception as e:
            logger.error(f"Error getting positions from {broker_type.value}: {e}")
            return None
    
    async def _record_discrepancy(
        self, run_id, symbol, exchange, broker, 
        local_qty, broker_qty, broker_avg, local_avg
    ):
        """Helper to create discrepancy record."""
        discrepancy = PositionDiscrepancy(
            symbol=symbol,
            exchange=exchange,
            broker=broker,
            local_quantity=local_qty,
            broker_quantity=broker_qty,
            difference=broker_qty - local_qty,
            local_avg_price=local_avg,
            broker_avg_price=broker_avg,
            detected_at=datetime.now(timezone.utc)
        )
        self.db.add(discrepancy)
        logger.warning(f"DRIFT: {symbol} (Local: {local_qty}, Broker: {broker_qty})")

    async def get_recent_discrepancies(
        self,
        hours: int = 24,
        resolved: Optional[bool] = None
    ) -> List[PositionDiscrepancy]:
        """Get recent discrepancies"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        stmt = select(PositionDiscrepancy).where(
            PositionDiscrepancy.detected_at >= cutoff_time
        )
        
        if resolved is not None:
            stmt = stmt.where(PositionDiscrepancy.resolved == resolved)
        
        result = await self.db.execute(stmt.order_by(PositionDiscrepancy.detected_at.desc()))
        return result.scalars().all()
    
    async def get_reconciliation_runs(
        self,
        limit: int = 10
    ) -> List[ReconciliationRun]:
        """Get recent reconciliation runs"""
        stmt = select(ReconciliationRun).order_by(
            ReconciliationRun.run_time.desc()
        ).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def generate_reconciliation_report(
        self,
        run_id: int
    ) -> Optional[Dict[str, Any]]:
        """Generate detailed reconciliation report"""
        stmt = select(ReconciliationRun).where(ReconciliationRun.id == run_id)
        result = await self.db.execute(stmt)
        run = result.scalar_one_or_none()
        
        if not run:
            return None
        
        # Get discrepancies from this run (detected between run_time and completed_at)
        completed_at = run.completed_at or datetime.now()
        stmt_disc = select(PositionDiscrepancy).where(
            and_(
                PositionDiscrepancy.detected_at >= run.run_time,
                PositionDiscrepancy.detected_at <= completed_at
            )
        )
        result_disc = await self.db.execute(stmt_disc)
        discrepancies = result_disc.scalars().all()
        
        # Get snapshots from this run
        stmt_snap = select(PositionSnapshot).where(
            PositionSnapshot.snapshot_time == run.run_time
        )
        result_snap = await self.db.execute(stmt_snap)
        snapshots = result_snap.scalars().all()
        
        return {
            "run_id": run.id,
            "run_time": run.run_time,
            "status": run.status,
            "duration_ms": run.duration_ms,
            "summary": {
                "brokers_checked": run.brokers_checked,
                "total_positions": run.total_positions,
                "discrepancies_found": run.discrepancies_found,
                "auto_corrections": run.auto_corrections,
                "unresolved_discrepancies": len([d for d in discrepancies if not d.resolved])
            },
            "discrepancies": discrepancies,
            "snapshots": snapshots
        }


# Global singleton instance for scheduler and other non-request usages
reconciliation_service = PositionReconciliationService()
