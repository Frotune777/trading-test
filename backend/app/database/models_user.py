"""
User Authentication Models
SQLAlchemy models for user management with Argon2 and Fernet security.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Index
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    """
    User model with Argon2 password hashing and Fernet API key encryption.
    
    Security features:
    - password_hash: Argon2id hash with pepper
    - api_key_hash: Argon2id hash for verification
    - api_key_encrypted: Fernet encrypted for retrieval
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    
    # Argon2 password hash
    password_hash = Column(Text, nullable=False)
    
    # API Key storage (dual: hash for verification, encrypted for retrieval)
    api_key_hash = Column(Text, nullable=True)  # Argon2 hash
    api_key_encrypted = Column(Text, nullable=True)  # Fernet encrypted
    
    # User status
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
    # Order execution mode
    order_mode = Column(String(20), default='auto', nullable=False)  # 'auto' or 'semi_auto'
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Performance indexes
    __table_args__ = (
        Index('idx_users_username', 'username'),
        Index('idx_users_email', 'email'),
        Index('idx_users_is_active', 'is_active'),
        Index('idx_users_order_mode', 'order_mode'),
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', is_active={self.is_active})>"


class UserSession(Base):
    """
    User session tracking for security audit.
    """
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    session_token_hash = Column(Text, nullable=False)  # SHA256 hash
    
    # Session metadata
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    user_agent = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Session status
    is_active = Column(Boolean, default=True, nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    
    # Performance indexes
    __table_args__ = (
        Index('idx_sessions_user_id', 'user_id'),
        Index('idx_sessions_is_active', 'is_active'),
        Index('idx_sessions_expires_at', 'expires_at'),
    )
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, is_active={self.is_active})>"
