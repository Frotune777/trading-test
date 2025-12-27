"""
Authentication Module

DEVELOPMENT ONLY - Mock Authentication
This module provides a mock authentication system for development purposes.

⚠️ SECURITY WARNING ⚠️
This implementation allows unauthenticated access to all endpoints.
MUST be replaced with real authentication before production deployment.

TODO for Production:
- Implement JWT token validation
- Add OAuth2 integration  
- Implement user session management
- Add role-based access control (RBAC)
- Integrate with user database
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

# Mock security scheme (not enforced in development)
security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> str:
    """
    Mock authentication dependency for development.
    
    Returns a default user ID without any validation.
    
    In production, this should:
    1. Validate JWT token from Authorization header
    2. Verify token signature and expiration
    3. Extract user ID from token claims
    4. Check user exists and is active
    5. Return authenticated user object
    
    Returns:
        str: User ID (always "dev_user" in development)
    
    Raises:
        HTTPException: In production, should raise 401 for invalid/missing tokens
    """
    # DEVELOPMENT: Return mock user without validation
    return "dev_user"
    
    # PRODUCTION CODE (commented out):
    # if not credentials:
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Missing authentication token",
    #         headers={"WWW-Authenticate": "Bearer"},
    #     )
    # 
    # try:
    #     # Validate JWT token
    #     payload = jwt.decode(
    #         credentials.credentials,
    #         settings.SECRET_KEY,
    #         algorithms=[settings.ALGORITHM]
    #     )
    #     user_id: str = payload.get("sub")
    #     if user_id is None:
    #         raise HTTPException(
    #             status_code=status.HTTP_401_UNAUTHORIZED,
    #             detail="Invalid authentication token"
    #         )
    #     return user_id
    # except JWTError:
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Could not validate credentials",
    #         headers={"WWW-Authenticate": "Bearer"},
    #     )


def get_current_active_user(current_user: str = Depends(get_current_user)) -> str:
    """
    Verify user is active (mock implementation).
    
    In production, should check user status in database.
    """
    # DEVELOPMENT: Always return user as active
    return current_user
    
    # PRODUCTION CODE (commented out):
    # user = db.query(User).filter(User.id == current_user).first()
    # if not user or not user.is_active:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Inactive user"
    #     )
    # return user
