"""
User Authentication Service
Handles user registration, login, and API key management with Argon2 and Fernet.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database.models_user import User, UserSession
from app.core.security import hash_password, verify_password, encrypt_token, decrypt_token
from app.core.security.auth_cache import (
    cache_verified_api_key,
    get_cached_user_id,
    is_cached_invalid,
    cache_invalid_api_key,
    invalidate_user_cache
)

logger = logging.getLogger(__name__)

class UserAuthService:
    """Service for user authentication operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_user(
        self,
        username: str,
        password: str,
        email: Optional[str] = None,
        is_superuser: bool = False
    ) -> User:
        """
        Create a new user with Argon2 password hashing.
        
        Args:
            username: Unique username
            password: Plain text password (will be hashed)
            email: Optional email address
            is_superuser: Whether user has admin privileges
            
        Returns:
            User: Created user object
            
        Raises:
            ValueError: If username already exists
        """
        # Check if username exists
        existing_user = self.db.execute(
            select(User).where(User.username == username)
        ).scalar_one_or_none()
        
        if existing_user:
            raise ValueError(f"Username '{username}' already exists")
        
        # Hash password with Argon2
        password_hash = hash_password(password)
        
        # Create user
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            is_superuser=is_superuser,
            is_active=True
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        logger.info(f"Created user: {username} (id={user.id})")
        return user
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate a user with username and password.
        
        Args:
            username: Username
            password: Plain text password
            
        Returns:
            User: User object if authentication successful, None otherwise
        """
        # Get user
        user = self.db.execute(
            select(User).where(User.username == username)
        ).scalar_one_or_none()
        
        if not user:
            logger.warning(f"Authentication failed: user '{username}' not found")
            return None
        
        if not user.is_active:
            logger.warning(f"Authentication failed: user '{username}' is inactive")
            return None
        
        # Verify password
        if not verify_password(password, user.password_hash):
            logger.warning(f"Authentication failed: incorrect password for user '{username}'")
            return None
        
        # Update last login
        user.last_login = datetime.utcnow()
        self.db.commit()
        
        logger.info(f"User authenticated: {username}")
        return user
    
    def generate_api_key(self, user_id: int) -> str:
        """
        Generate a new API key for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            str: Generated API key (plain text, only shown once)
            
        Raises:
            ValueError: If user not found
        """
        import secrets
        
        # Get user
        user = self.db.get(User, user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Generate random API key
        api_key = secrets.token_urlsafe(32)
        
        # Hash for verification
        api_key_hash = hash_password(api_key)
        
        # Encrypt for retrieval
        api_key_encrypted = encrypt_token(api_key)
        
        # Store both
        user.api_key_hash = api_key_hash
        user.api_key_encrypted = api_key_encrypted
        self.db.commit()
        
        # Invalidate cache
        invalidate_user_cache(str(user_id))
        
        logger.info(f"Generated new API key for user {user_id}")
        return api_key
    
    def verify_api_key(self, api_key: str) -> Optional[int]:
        """
        Verify an API key and return the user ID.
        
        Args:
            api_key: API key to verify
            
        Returns:
            int: User ID if valid, None otherwise
        """
        # Check invalid cache first (fast rejection)
        if is_cached_invalid(api_key):
            logger.debug("API key rejected from invalid cache")
            return None
        
        # Check valid cache
        cached_user_id = get_cached_user_id(api_key)
        if cached_user_id:
            return int(cached_user_id)
        
        # Query all users with API keys
        users = self.db.execute(
            select(User).where(User.api_key_hash.isnot(None))
        ).scalars().all()
        
        # Try to verify against each hash
        for user in users:
            if verify_password(api_key, user.api_key_hash):
                # Valid key found - cache it
                cache_verified_api_key(api_key, str(user.id))
                logger.debug(f"API key verified for user {user.id}")
                return user.id
        
        # Invalid key - cache it
        cache_invalid_api_key(api_key)
        logger.debug("Invalid API key cached")
        return None
    
    def get_user_by_api_key(self, api_key: str) -> Optional[User]:
        """
        Get user by API key.
        
        Args:
            api_key: API key
            
        Returns:
            User: User object if valid, None otherwise
        """
        user_id = self.verify_api_key(api_key)
        if not user_id:
            return None
        
        return self.db.get(User, user_id)
    
    def update_order_mode(self, user_id: int, mode: str) -> bool:
        """
        Update user's order execution mode.
        
        Args:
            user_id: User ID
            mode: 'auto' or 'semi_auto'
            
        Returns:
            bool: True if successful
        """
        if mode not in ['auto', 'semi_auto']:
            raise ValueError(f"Invalid order mode: {mode}")
        
        user = self.db.get(User, user_id)
        if not user:
            return False
        
        user.order_mode = mode
        self.db.commit()
        
        # Invalidate cache
        invalidate_user_cache(str(user_id))
        
        logger.info(f"Updated order mode to '{mode}' for user {user_id}")
        return True
    
    def revoke_api_key(self, user_id: int) -> bool:
        """
        Revoke a user's API key.
        
        Args:
            user_id: User ID
            
        Returns:
            bool: True if successful
        """
        user = self.db.get(User, user_id)
        if not user:
            return False
        
        user.api_key_hash = None
        user.api_key_encrypted = None
        self.db.commit()
        
        # Invalidate cache
        invalidate_user_cache(str(user_id))
        
        logger.info(f"Revoked API key for user {user_id}")
        return True
