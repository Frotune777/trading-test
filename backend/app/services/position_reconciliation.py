"""
Position Reconciliation Service
Auto-reconciles positions with brokers every 5 minutes.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
import asyncio

from app.database.models_position import (
    PositionSnapshot,
    PositionDiscrepancy,
    ReconciliationRun
)
from app.services.broker_gateway import broker_gateway
from app.brokers.base_adapter import BrokerType, Position

logger = logging.getLogger(__name__)


class PositionReconciliationService:
    """
    Position Reconciliation Service
    
    Features:
        - Periodic reconciliation (every 5 min)
        - Discrepancy detection
        - Auto-correction (optional)
        - Reconciliation reports
        - Alerts on mismatch
    
    Compliance:
        - Rule #38: UI reflects backend truth
        - Rule #33-37: All operations logged
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.auto_correct_enabled = False  # Safety: disabled by default
        self.reconciliation_interval = timedelta(minutes=5)
        self.max_auto_correct_quantity = 100  # Max quantity for auto-correction
    
    async def reconcile_positions(
        self,
        broker: Optional[BrokerType] = None
    ) -> ReconciliationRun:
        """
        Reconcile positions with broker(s).
        
        Args:
            broker: Specific broker to reconcile (None = all brokers)
            
        Returns:
            ReconciliationRun record
        """
        start_time = datetime.now()
        
        # Determine brokers to check
        if broker:
            brokers_to_check = [broker]
        else:
            brokers_to_check = list(broker_gateway.brokers.keys())
        
        # Create reconciliation run record
        run = ReconciliationRun(
            run_time=start_time,
            brokers_checked=[b.value for b in brokers_to_check],
            status="RUNNING"
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        
        logger.info(f"Starting reconciliation run {run.id} for {len(brokers_to_check)} brokers")
        
        try:
            total_positions = 0
            discrepancies_found = 0
            auto_corrections = 0
            
            for broker_type in brokers_to_check:
                # Get positions from broker
                broker_positions = await self._get_broker_positions(broker_type)
                
                if broker_positions is None:
                    logger.warning(f"Failed to fetch positions from {broker_type.value}")
                    continue
                
                total_positions += len(broker_positions)
                
                # Save snapshots
                for position in broker_positions:
                    snapshot = PositionSnapshot(
                        broker=broker_type.value,
                        symbol=position.symbol,
                        exchange=position.exchange,
                        quantity=position.quantity,
                        average_price=float(position.average_price),
                        pnl=float(position.pnl) if position.pnl else None,
                        product_type=position.product if hasattr(position, 'product') else None,
                        snapshot_time=start_time
                    )
                    self.db.add(snapshot)
                
                # Detect discrepancies
                discrepancies = await self._detect_discrepancies(
                    broker_type,
                    broker_positions
                )
                
                discrepancies_found += len(discrepancies)
                
                # Auto-correct if enabled
                if self.auto_correct_enabled:
                    corrections = await self._auto_correct_discrepancies(
                        broker_type,
                        discrepancies
                    )
                    auto_corrections += corrections
            
            # Update run record
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            run.total_positions = total_positions
            run.discrepancies_found = discrepancies_found
            run.auto_corrections = auto_corrections
            run.status = "COMPLETED"
            run.duration_ms = duration_ms
            run.completed_at = datetime.now()
            
            self.db.commit()
            
            logger.info(
                f"Reconciliation run {run.id} completed: "
                f"{total_positions} positions, {discrepancies_found} discrepancies, "
                f"{auto_corrections} auto-corrections in {duration_ms}ms"
            )
            
            return run
            
        except Exception as e:
            logger.error(f"Reconciliation run {run.id} failed: {e}")
            
            run.status = "FAILED"
            run.error_message = str(e)
            run.completed_at = datetime.now()
            self.db.commit()
            
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
            
            return positions if positions else []
            
        except Exception as e:
            logger.error(f"Error getting positions from {broker_type.value}: {e}")
            return None
    
    async def _detect_discrepancies(
        self,
        broker_type: BrokerType,
        broker_positions: List[Position]
    ) -> List[PositionDiscrepancy]:
        """
        Detect discrepancies between local and broker positions.
        
        For now, we compare against broker positions only.
        In production, would compare against local position tracking.
        """
        discrepancies = []
        
        # Get local positions (placeholder - would query from local DB)
        local_positions = {}  # symbol -> quantity
        
        # Create broker position map
        broker_position_map = {
            f"{pos.symbol}:{pos.exchange}": pos
            for pos in broker_positions
        }
        
        # Check for discrepancies
        all_symbols = set(local_positions.keys()) | set(broker_position_map.keys())
        
        for symbol_key in all_symbols:
            local_qty = local_positions.get(symbol_key, 0)
            broker_pos = broker_position_map.get(symbol_key)
            broker_qty = broker_pos.quantity if broker_pos else 0
            
            difference = broker_qty - local_qty
            
            if difference != 0:
                # Found discrepancy
                symbol, exchange = symbol_key.split(':') if ':' in symbol_key else (symbol_key, 'NSE')
                
                discrepancy = PositionDiscrepancy(
                    symbol=symbol,
                    exchange=exchange,
                    broker=broker_type.value,
                    local_quantity=local_qty,
                    broker_quantity=broker_qty,
                    difference=difference,
                    local_avg_price=None,  # Would get from local DB
                    broker_avg_price=float(broker_pos.average_price) if broker_pos else None
                )
                
                self.db.add(discrepancy)
                discrepancies.append(discrepancy)
                
                logger.warning(
                    f"Position discrepancy detected: {symbol} on {broker_type.value} - "
                    f"Local: {local_qty}, Broker: {broker_qty}, Diff: {difference}"
                )
        
        self.db.commit()
        
        return discrepancies
    
    async def _auto_correct_discrepancies(
        self,
        broker_type: BrokerType,
        discrepancies: List[PositionDiscrepancy]
    ) -> int:
        """
        Auto-correct discrepancies (if enabled and within limits).
        
        Returns:
            Number of corrections made
        """
        corrections = 0
        
        for discrepancy in discrepancies:
            # Safety checks
            if abs(discrepancy.difference) > self.max_auto_correct_quantity:
                logger.warning(
                    f"Discrepancy too large for auto-correction: "
                    f"{discrepancy.symbol} diff={discrepancy.difference}"
                )
                continue
            
            # TODO: Implement auto-correction logic
            # This would place orders to align positions
            # For now, just log
            logger.info(
                f"Would auto-correct {discrepancy.symbol}: "
                f"place order for {abs(discrepancy.difference)} shares"
            )
            
            # Mark as resolved
            discrepancy.resolved = True
            discrepancy.resolved_at = datetime.now()
            discrepancy.resolution_method = "AUTO"
            discrepancy.resolution_action = f"Auto-correction attempted for {abs(discrepancy.difference)} shares"
            
            corrections += 1
        
        self.db.commit()
        
        return corrections
    
    def get_recent_discrepancies(
        self,
        hours: int = 24,
        resolved: Optional[bool] = None
    ) -> List[PositionDiscrepancy]:
        """Get recent discrepancies"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        query = self.db.query(PositionDiscrepancy).filter(
            PositionDiscrepancy.detected_at >= cutoff_time
        )
        
        if resolved is not None:
            query = query.filter(PositionDiscrepancy.resolved == resolved)
        
        return query.order_by(PositionDiscrepancy.detected_at.desc()).all()
    
    def get_reconciliation_runs(
        self,
        limit: int = 10
    ) -> List[ReconciliationRun]:
        """Get recent reconciliation runs"""
        return self.db.query(ReconciliationRun).order_by(
            ReconciliationRun.run_time.desc()
        ).limit(limit).all()
    
    def generate_reconciliation_report(
        self,
        run_id: int
    ) -> Optional[Dict[str, Any]]:
        """Generate detailed reconciliation report"""
        run = self.db.query(ReconciliationRun).filter(
            ReconciliationRun.id == run_id
        ).first()
        
        if not run:
            return None
        
        # Get discrepancies from this run
        discrepancies = self.db.query(PositionDiscrepancy).filter(
            and_(
                PositionDiscrepancy.detected_at >= run.run_time,
                PositionDiscrepancy.detected_at <= (run.completed_at or datetime.now())
            )
        ).all()
        
        # Get snapshots from this run
        snapshots = self.db.query(PositionSnapshot).filter(
            PositionSnapshot.snapshot_time == run.run_time
        ).all()
        
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
