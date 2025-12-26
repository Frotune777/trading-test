"""
Position Reconciliation API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.database.models_position import (
    DiscrepancyResponse,
    ReconciliationRunResponse,
    ReconciliationReportResponse,
    PositionSnapshotResponse
)
from app.services.position_reconciliation import PositionReconciliationService
from app.brokers.base_adapter import BrokerType
from app.core.database import get_db
from app.core.auth import get_current_user

router = APIRouter(prefix="/reconciliation", tags=["Position Reconciliation"])
logger = logging.getLogger(__name__)


@router.post("/run", response_model=ReconciliationRunResponse)
async def trigger_reconciliation(
    broker: Optional[str] = Query(None, description="Specific broker to reconcile (None = all)"),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Trigger position reconciliation manually.
    
    - **broker**: Optional specific broker (zerodha, angelone, etc.)
    
    Reconciles positions with broker(s) and detects discrepancies.
    """
    try:
        service = PositionReconciliationService(db)
        
        broker_type = None
        if broker:
            try:
                broker_type = BrokerType(broker)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid broker: {broker}"
                )
        
        run = await service.reconcile_positions(broker_type)
        
        return ReconciliationRunResponse(
            id=run.id,
            run_time=run.run_time,
            brokers_checked=run.brokers_checked,
            total_positions=run.total_positions,
            discrepancies_found=run.discrepancies_found,
            auto_corrections=run.auto_corrections,
            status=run.status,
            error_message=run.error_message,
            duration_ms=run.duration_ms,
            completed_at=run.completed_at
        )
        
    except Exception as e:
        logger.error(f"Error triggering reconciliation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/runs", response_model=List[ReconciliationRunResponse])
async def list_reconciliation_runs(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """List recent reconciliation runs."""
    service = PositionReconciliationService(db)
    runs = service.get_reconciliation_runs(limit)
    
    return [
        ReconciliationRunResponse(
            id=run.id,
            run_time=run.run_time,
            brokers_checked=run.brokers_checked,
            total_positions=run.total_positions,
            discrepancies_found=run.discrepancies_found,
            auto_corrections=run.auto_corrections,
            status=run.status,
            error_message=run.error_message,
            duration_ms=run.duration_ms,
            completed_at=run.completed_at
        )
        for run in runs
    ]


@router.get("/discrepancies", response_model=List[DiscrepancyResponse])
async def list_discrepancies(
    hours: int = Query(24, ge=1, le=168, description="Look back period in hours"),
    resolved: Optional[bool] = Query(None, description="Filter by resolved status"),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    List position discrepancies.
    
    - **hours**: Look back period (default 24 hours)
    - **resolved**: Filter by resolved status (None = all)
    """
    service = PositionReconciliationService(db)
    discrepancies = service.get_recent_discrepancies(hours, resolved)
    
    return [
        DiscrepancyResponse(
            id=d.id,
            symbol=d.symbol,
            exchange=d.exchange,
            broker=d.broker,
            local_quantity=d.local_quantity,
            broker_quantity=d.broker_quantity,
            difference=d.difference,
            local_avg_price=float(d.local_avg_price) if d.local_avg_price else None,
            broker_avg_price=float(d.broker_avg_price) if d.broker_avg_price else None,
            detected_at=d.detected_at,
            resolved=d.resolved,
            resolved_at=d.resolved_at,
            resolution_action=d.resolution_action,
            resolution_method=d.resolution_method
        )
        for d in discrepancies
    ]


@router.get("/report/{run_id}")
async def get_reconciliation_report(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Get detailed reconciliation report for a specific run.
    
    Includes:
    - Run summary
    - All discrepancies found
    - Position snapshots
    """
    service = PositionReconciliationService(db)
    report = service.generate_reconciliation_report(run_id)
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reconciliation run {run_id} not found"
        )
    
    # Convert to response models
    return {
        "run_id": report["run_id"],
        "run_time": report["run_time"],
        "status": report["status"],
        "duration_ms": report["duration_ms"],
        "summary": report["summary"],
        "discrepancies": [
            DiscrepancyResponse(
                id=d.id,
                symbol=d.symbol,
                exchange=d.exchange,
                broker=d.broker,
                local_quantity=d.local_quantity,
                broker_quantity=d.broker_quantity,
                difference=d.difference,
                local_avg_price=float(d.local_avg_price) if d.local_avg_price else None,
                broker_avg_price=float(d.broker_avg_price) if d.broker_avg_price else None,
                detected_at=d.detected_at,
                resolved=d.resolved,
                resolved_at=d.resolved_at,
                resolution_action=d.resolution_action,
                resolution_method=d.resolution_method
            )
            for d in report["discrepancies"]
        ],
        "snapshots": [
            PositionSnapshotResponse(
                id=s.id,
                broker=s.broker,
                symbol=s.symbol,
                exchange=s.exchange,
                quantity=s.quantity,
                average_price=float(s.average_price) if s.average_price else 0.0,
                current_price=float(s.current_price) if s.current_price else None,
                pnl=float(s.pnl) if s.pnl else None,
                product_type=s.product_type,
                snapshot_time=s.snapshot_time
            )
            for s in report["snapshots"]
        ]
    }


@router.post("/discrepancies/{discrepancy_id}/resolve", response_model=DiscrepancyResponse)
async def resolve_discrepancy(
    discrepancy_id: int,
    resolution_action: str,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Manually resolve a discrepancy.
    
    - **resolution_action**: Description of how it was resolved
    """
    from app.database.models_position import PositionDiscrepancy
    from datetime import datetime
    
    discrepancy = db.query(PositionDiscrepancy).filter(
        PositionDiscrepancy.id == discrepancy_id
    ).first()
    
    if not discrepancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Discrepancy {discrepancy_id} not found"
        )
    
    discrepancy.resolved = True
    discrepancy.resolved_at = datetime.now()
    discrepancy.resolution_action = resolution_action
    discrepancy.resolution_method = "MANUAL"
    
    db.commit()
    db.refresh(discrepancy)
    
    return DiscrepancyResponse(
        id=discrepancy.id,
        symbol=discrepancy.symbol,
        exchange=discrepancy.exchange,
        broker=discrepancy.broker,
        local_quantity=discrepancy.local_quantity,
        broker_quantity=discrepancy.broker_quantity,
        difference=discrepancy.difference,
        local_avg_price=float(discrepancy.local_avg_price) if discrepancy.local_avg_price else None,
        broker_avg_price=float(discrepancy.broker_avg_price) if discrepancy.broker_avg_price else None,
        detected_at=discrepancy.detected_at,
        resolved=discrepancy.resolved,
        resolved_at=discrepancy.resolved_at,
        resolution_action=discrepancy.resolution_action,
        resolution_method=discrepancy.resolution_method
    )
