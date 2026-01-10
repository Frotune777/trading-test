from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class ScanRequest(BaseModel):
    index: str = Field(..., description="Index code (e.g., '12' for Nifty 50)")
    strategy: str = Field(..., description="Strategy code (e.g., '9' for Volume Shockers)")
    params: Optional[Dict[str, Any]] = Field(default=None, description="Optional overrides for PKScreener settings")
    custom_list_id: Optional[int] = Field(default=None, description="ID of a saved custom stock list to scan")

class ScanStatus(BaseModel):
    task_id: str
    state: str # PENDING, STARTED, PROGRESS, SUCCESS, FAILURE
    progress: float
    message: Optional[str] = None
    results_ready: bool = False

class PKScreenerResultSchema(BaseModel):
    id: int
    scan_id: str
    index_name: str
    strategy_name: str
    results: List[Dict[str, Any]]
    scan_time: datetime

    class Config:
        orm_mode = True

class CustomListCreate(BaseModel):
    name: str
    stocks: List[str]
    description: Optional[str] = None

class CustomListSchema(BaseModel):
    id: int
    name: str
    stocks: List[str]
    description: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True
