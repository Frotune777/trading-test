from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.schemas.pkscreener import ScanRequest, ScanStatus, PKScreenerResultSchema, CustomListCreate, CustomListSchema
from app.database.models_screener import CustomStockList, PKScreenerResult
from app.workers.pkscreener_tasks import run_pkscreener_scan
from app.core.auth import get_current_user # Assuming auth logic exists
from celery.result import AsyncResult

router = APIRouter(prefix="/screener", tags=["screener"])

# --- Scanning Endpoints ---

@router.post("/scan", response_model=ScanStatus)
async def trigger_scan(
    request: ScanRequest, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Trigger a PKScreener scan index-wide or on a custom stock list.
    """
    stock_list = None
    if request.custom_list_id:
        db_list = db.query(CustomStockList).filter(CustomStockList.id == request.custom_list_id).first()
        if not db_list:
            raise HTTPException(status_code=404, detail="Custom stock list not found")
        stock_list = db_list.stocks
        
    task = run_pkscreener_scan.delay(
        index=request.index,
        strategy=request.strategy,
        params=request.params,
        stock_list=stock_list
    )
    
    return {
        "task_id": task.id,
        "state": task.state,
        "progress": 0,
        "message": "Scan task submitted to queue."
    }

@router.get("/status/{task_id}", response_model=ScanStatus)
async def get_scan_status(task_id: str):
    """
    Query the status of a background scan task.
    """
    res = AsyncResult(task_id)
    state = res.state
    progress = 0
    message = None
    results_ready = False
    
    if state == 'PROGRESS':
        progress = res.info.get('progress', 0)
        message = res.info.get('message', '')
    elif state == 'SUCCESS':
        progress = 100
        message = 'Scan completed.'
        results_ready = True
    elif state == 'FAILURE':
        message = str(res.info)
        
    return {
        "task_id": task_id,
        "state": state,
        "progress": progress,
        "message": message,
        "results_ready": results_ready
    }

# --- Results Endpoints ---

@router.get("/results/latest", response_model=List[PKScreenerResultSchema])
async def get_latest_results(limit: int = 10, db: Session = Depends(get_db)):
    """
    Fetch the most recent scan findings from the database.
    """
    results = db.query(PKScreenerResult).order_by(PKScreenerResult.scan_time.desc()).limit(limit).all()
    return results

@router.get("/results/{scan_id}", response_model=PKScreenerResultSchema)
async def get_result_by_id(scan_id: str, db: Session = Depends(get_db)):
    """
    Get results for a specific scan operation.
    """
    result = db.query(PKScreenerResult).filter(PKScreenerResult.scan_id == scan_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Results not found for this scan ID")
    return result

# --- Custom List Endpoints ---

@router.post("/lists", response_model=CustomListSchema)
async def create_custom_list(
    payload: CustomListCreate, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Save a custom stock list for persistent screening.
    """
    db_list = CustomStockList(
        name=payload.name,
        stocks=payload.stocks,
        description=payload.description
    )
    db.add(db_list)
    db.commit()
    db.refresh(db_list)
    return db_list

@router.get("/lists", response_model=List[CustomListSchema])
async def list_custom_lists(db: Session = Depends(get_db)):
    """
    Retrieve all saved custom stock lists.
    """
    return db.query(CustomStockList).all()

@router.delete("/lists/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_custom_list(
    list_id: int, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Delete a custom stock list.
    """
    db_list = db.query(CustomStockList).filter(CustomStockList.id == list_id).first()
    if not db_list:
        raise HTTPException(status_code=404, detail="List not found")
    db.delete(db_list)
    db.commit()
    return None
