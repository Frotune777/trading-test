from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
import logging

from app.database.models_position import (
    DiscrepancyResponse,
    ReconciliationRunResponse,
    ReconciliationReportResponse,
    PositionSnapshotResponse
)
from app.services.reconciliation_service import PositionReconciliationService
from app.brokers.base_adapter import BrokerType
from app.core.database import get_db
from app.core.auth import get_current_user

router = APIRouter(prefix="/reconciliation", tags=["Position Reconciliation"])
logger = logging.getLogger(__name__)


@router.post("/run", response_model=ReconciliationRunResponse)
async def trigger_reconciliation(
    broker: Optional[str] = Query(None, description="Specific broker to reconcile (None = all)"),
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Trigger position reconciliation manually.
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
        return run
        
    except Exception as e:
        logger.error(f"Error triggering reconciliation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/runs", response_model=List[ReconciliationRunResponse])
async def list_reconciliation_runs(
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """List recent reconciliation runs."""
    service = PositionReconciliationService(db)
    runs = await service.get_reconciliation_runs(limit)
    return runs


@router.get("/discrepancies", response_model=List[DiscrepancyResponse])
async def list_discrepancies(
    hours: int = Query(24, ge=1, le=168, description="Look back period in hours"),
    resolved: Optional[bool] = Query(None, description="Filter by resolved status"),
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """List position discrepancies."""
    service = PositionReconciliationService(db)
    discrepancies = await service.get_recent_discrepancies(hours, resolved)
    return discrepancies


@router.get("/report/{run_id}", response_model=Dict[str, Any])
async def get_reconciliation_report(
    run_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Get detailed reconciliation report."""
    service = PositionReconciliationService(db)
    report = await service.generate_reconciliation_report(run_id)
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reconciliation run {run_id} not found"
        )
    return report

@router.post("/discrepancies/{discrepancy_id}/resolve", response_model=DiscrepancyResponse)
async def resolve_discrepancy(
    discrepancy_id: int,
    resolution_action: str,
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """Manually resolve a discrepancy."""
    from app.database.models_position import PositionDiscrepancy
    from datetime import datetime
    from sqlalchemy import select
    
    stmt = select(PositionDiscrepancy).where(PositionDiscrepancy.id == discrepancy_id)
    result = await db.execute(stmt)
    discrepancy = result.scalar_one_or_none()
    
    if not discrepancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Discrepancy {discrepancy_id} not found"
        )
    
    discrepancy.resolved = True
    discrepancy.resolved_at = datetime.now()
    discrepancy.resolution_action = resolution_action
    discrepancy.resolution_method = "MANUAL"
    
    await db.commit()
    await db.refresh(discrepancy)
    
    return discrepancy
