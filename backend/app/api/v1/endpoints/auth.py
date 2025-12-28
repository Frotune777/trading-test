"""
User Authentication API Endpoints
Handles user registration, login, and API key management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.services.user_auth_service import UserAuthService
from app.database.models_user import User

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()

# Pydantic models
class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[EmailStr] = None

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str]
    is_active: bool
    is_superuser: bool
    order_mode: str
    created_at: datetime
    last_login: Optional[datetime]
    
    class Config:
        from_attributes = True

class APIKeyResponse(BaseModel):
    api_key: str
    message: str

class OrderModeUpdate(BaseModel):
    mode: str  # 'auto' or 'semi_auto'

# Dependency to get current user from API key
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current user from Bearer token (API key)"""
    api_key = credentials.credentials
    auth_service = UserAuthService(db)
    
    user = auth_service.get_user_by_api_key(api_key)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return user

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user.
    
    - **username**: Unique username (required)
    - **password**: Password (will be hashed with Argon2)
    - **email**: Optional email address
    """
    auth_service = UserAuthService(db)
    
    try:
        user = auth_service.create_user(
            username=user_data.username,
            password=user_data.password,
            email=user_data.email
        )
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login", response_model=UserResponse)
async def login_user(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Authenticate a user with username and password.
    
    Returns user information if authentication successful.
    """
    auth_service = UserAuthService(db)
    
    user = auth_service.authenticate_user(
        username=login_data.username,
        password=login_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    return user

@router.post("/api-key/generate", response_model=APIKeyResponse)
async def generate_api_key(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a new API key for the current user.
    
    **Warning**: This will invalidate the previous API key!
    Save the new key immediately - it will not be shown again.
    """
    auth_service = UserAuthService(db)
    
    api_key = auth_service.generate_api_key(current_user.id)
    
    return {
        "api_key": api_key,
        "message": "New API key generated. Save it now - it will not be shown again!"
    }

@router.delete("/api-key/revoke", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Revoke the current user's API key.
    
    After revocation, a new key must be generated to access the API.
    """
    auth_service = UserAuthService(db)
    
    success = auth_service.revoke_api_key(current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke API key"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user information.
    
    Requires valid API key in Authorization header.
    """
    return current_user

@router.put("/order-mode", response_model=UserResponse)
async def update_order_mode(
    mode_update: OrderModeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update order execution mode.
    
    - **auto**: Orders execute immediately
    - **semi_auto**: Orders require manual approval (Action Center)
    """
    auth_service = UserAuthService(db)
    
    try:
        auth_service.update_order_mode(current_user.id, mode_update.mode)
        db.refresh(current_user)
        return current_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
