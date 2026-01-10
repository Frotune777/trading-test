from app.workers.celery_app import celery_app
from app.services.pkscreener_service import pkscreener_service
from app.database.models_screener import PKScreenerResult
from app.core.database import SessionLocal
import pandas as pd
import json
import asyncio

@celery_app.task(bind=True)
def run_pkscreener_scan(self, index: str, strategy: str, params: dict = None, stock_list: list = None):
    """
    Celery task to run PKScreener scan in the background.
    """
    self.update_state(state='PROGRESS', meta={'progress': 10, 'message': 'Initializing PKScreener...'})
    
    # 1. Update config if params provided
    if params:
        self.update_state(state='PROGRESS', meta={'progress': 20, 'message': 'Updating PKScreener configuration...'})
        pkscreener_service.update_config(params)
        
    # 2. Execute Scan
    self.update_state(state='PROGRESS', meta={'progress': 40, 'message': f'Scanning {index} for strategy {strategy}...'})
    
    # run_scan is async, so we use asyncio to run it in a sync Celery task
    loop = asyncio.get_event_loop()
    df = loop.run_until_complete(pkscreener_service.run_scan(
        index_option=index,
        scan_sub_option=strategy,
        stock_list=stock_list
    ))
    
    self.update_state(state='PROGRESS', meta={'progress': 80, 'message': 'Parsing results...'})
    
    # 3. Save Results to DB
    if not df.empty:
        # Convert DF to record list for JSON storage
        results_json = df.to_dict(orient='records')
        
        db = SessionLocal()
        try:
            db_result = PKScreenerResult(
                scan_id=self.request.id,
                index_name=index,
                strategy_name=strategy,
                results=results_json
            )
            db.add(db_result)
            db.commit()
            self.update_state(state='SUCCESS', meta={'progress': 100, 'message': 'Scan completed successfully.'})
            return {"results_count": len(results_json), "scan_id": self.request.id}
        except Exception as e:
            db.rollback()
            print(f"Error saving scan results: {e}")
            self.update_state(state='FAILURE', meta={'progress': 100, 'message': f'Failed to save results: {str(e)}'})
        finally:
            db.close()
    else:
        self.update_state(state='SUCCESS', meta={'progress': 100, 'message': 'Scan completed. No results found.'})
        return {"results_count": 0, "scan_id": self.request.id}

@celery_app.task
def cleanup_screener_reports():
    """
    Scheduled task to delete old CSV/XLSX reports from the results directory.
    """
    import os
    import time
    from pathlib import Path
    
    results_dir = Path("/home/fortune/Desktop/Python_Projects/quad_trading/trading-test/backend/results")
    if not results_dir.exists():
        return
        
    now = time.time()
    deleted_count = 0
    
    # Delete files older than 24 hours
    for filename in os.listdir(results_dir):
        file_path = results_dir / filename
        if os.path.isfile(file_path):
            if os.stat(file_path).st_mtime < now - (24 * 3600):
                os.remove(file_path)
                deleted_count += 1
                
    return {"deleted_count": deleted_count}
