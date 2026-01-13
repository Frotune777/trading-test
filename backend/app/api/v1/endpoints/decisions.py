"""
Decision Ledger API Endpoints
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Dict, Any

from app.core.database import get_db, get_db_sync
from app.services.decision_service import DecisionService
from app.api.v1.endpoints.auth import get_current_user


router = APIRouter()


# Request/Response Models
class CausalFactor(BaseModel):
    cause: str = Field(..., description="Description of the cause")
    effect: str = Field(..., description="Effect on the decision")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in this causal link")
    magnitude: Optional[float] = Field(None, description="Magnitude of effect")
    type: Optional[str] = Field("INDICATOR", description="Type of cause")
    value: Optional[str] = Field(None, description="Actual value that triggered")
    contribution: Optional[float] = Field(0, description="Contribution to conviction")


class RecordDecisionRequest(BaseModel):
    strategy_id: int
    symbol: str
    mode: str = Field("DRY_RUN", description="DRY_RUN, LIVE, or BACKTEST")
    
    inputs: Dict[str, Any] = Field(..., description="Input data")
    output: Dict[str, Any] = Field(..., description="Decision output")
    weights: Dict[str, float] = Field(..., description="Pillar weights")
    risk_checks: Dict[str, str] = Field(..., description="Risk check results")
    causal_graph: List[CausalFactor]
    
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


class UpdateExecutionRequest(BaseModel):
    execution_price: float
    execution_status: str = Field(..., description="FILLED, REJECTED, CANCELLED")


class UpdateOutcomeRequest(BaseModel):
    actual_pnl: float
    exit_price: float
    was_correct: Optional[bool] = None


# Endpoints
@router.post("/record")
async def record_decision(
    request: RecordDecisionRequest,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db_sync)
):
    """
    Record a trading decision with full causal explainability
    
    Creates an immutable record of:
    - Inputs (price, indicators, regime, ML prediction)
    - Pillar weights (Q/U/A/D)
    - Risk check results
    - Causal graph with confidence levels
    - Final output and conviction
    
    Returns decision_id for tracking
    """
    decision_service = DecisionService(db)
    
    # Convert causal factors to dict
    causal_graph = [factor.dict() for factor in request.causal_graph]
    
    decision = decision_service.record_decision(
        strategy_id=request.strategy_id,
        symbol=request.symbol,
        user_id=current_user,
        inputs=request.inputs,
        output=request.output,
        weights=request.weights,
        risk_checks=request.risk_checks,
        causal_graph=causal_graph,
        mode=request.mode,
        notes=request.notes,
        tags=request.tags,
    )
    
    return decision


@router.get("/decision/{decision_id}")
async def get_decision(
    decision_id: str,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db_sync)
):
    """Get a single decision by ID"""
    decision_service = DecisionService(db)
    decision = await decision_service.get_decision(decision_id)
    
    if not decision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Decision {decision_id} not found"
        )
    
    return decision


@router.get("/symbol/{symbol}")
async def get_decisions_by_symbol(
    symbol: str,
    mode: Optional[str] = None,
    limit: int = 50,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db_sync)
):
    """Get decision history for a symbol"""
    decision_service = DecisionService(db)
    decisions = await decision_service.get_decisions_by_symbol(
        symbol=symbol,
        user_id=current_user,
        limit=limit,
        mode=mode
    )
    
    return {
        'symbol': symbol,
        'count': len(decisions),
        'decisions': decisions
    }


@router.get("/strategy/{strategy_id}")
async def get_decisions_by_strategy(
    strategy_id: int,
    limit: int = 50,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db_sync)
):
    """Get decisions made by a specific strategy"""
    decision_service = DecisionService(db)
    decisions = await decision_service.get_decisions_by_strategy(
        strategy_id=strategy_id,
        user_id=current_user,
        limit=limit
    )
    
    return {
        'strategy_id': strategy_id,
        'count': len(decisions),
        'decisions': decisions
    }


@router.get("/timeline/{symbol}")
async def get_decision_timeline(
    symbol: str,
    days: int = 30,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db_sync)
):
    """
    Get decision timeline for visualization
    Shows evolution of decisions over time for a symbol
    """
    decision_service = DecisionService(db)
    timeline = await decision_service.get_decision_timeline(
        symbol=symbol,
        user_id=current_user,
        days=days
    )
    
    return {
        'symbol': symbol,
        'days': days,
        'timeline': timeline
    }


@router.put("/decision/{decision_id}/execution")
async def update_execution(
    decision_id: str,
    request: UpdateExecutionRequest,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db_sync)
):
    """Update decision with execution results"""
    decision_service = DecisionService(db)
    success = await decision_service.update_execution(
        decision_id=decision_id,
        execution_price=request.execution_price,
        execution_status=request.execution_status
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Decision {decision_id} not found"
        )
    
    return {'success': True, 'message': 'Execution updated'}


@router.put("/decision/{decision_id}/outcome")
async def update_outcome(
    decision_id: str,
    request: UpdateOutcomeRequest,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db_sync)
):
    """Update decision with final outcome"""
    decision_service = DecisionService(db)
    success = await decision_service.update_outcome(
        decision_id=decision_id,
        actual_pnl=request.actual_pnl,
        exit_price=request.exit_price,
        was_correct=request.was_correct
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Decision {decision_id} not found"
        )
    
    return {'success': True, 'message': 'Outcome updated'}


@router.get("/decision/{decision_id}/causal-analysis")
async def analyze_causal_accuracy(
    decision_id: str,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db_sync)
):
    """
    Analyze which causal factors were actually important
    Requires decision to have outcome data
    """
    decision_service = DecisionService(db)
    analysis = await decision_service.analyze_causal_accuracy(decision_id)
    
    if 'error' in analysis:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=analysis['error']
        )
    
    return analysis
