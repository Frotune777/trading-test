"""
Unit tests for User Auth Service
Tests password hashing, API key encryption, and session management
"""

import pytest
from datetime import datetime, timedelta
import pytz

from app.services.user_auth_service import UserAuthService
from app.database.models_user import User

IST = pytz.timezone('Asia/Kolkata')


class TestUserAuthService:
    """Test suite for UserAuthService"""
    
    def test_hash_password(self, db_session):
        """Test password hashing with Argon2"""
        service = UserAuthService(db_session)
        
        password = "SecurePassword123!"
        hashed = service.hash_password(password)
        
        # Verify Argon2 hash format
        assert hashed.startswith("$argon2id$")
        assert hashed != password
    
    def test_verify_password_correct(self, db_session):
        """Test password verification with correct password"""
        service = UserAuthService(db_session)
        
        password = "SecurePassword123!"
        hashed = service.hash_password(password)
        
        # Verify correct password
        assert service.verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self, db_session):
        """Test password verification with incorrect password"""
        service = UserAuthService(db_session)
        
        password = "SecurePassword123!"
        hashed = service.hash_password(password)
        
        # Verify incorrect password
        assert service.verify_password("WrongPassword", hashed) is False
    
    def test_encrypt_api_key(self, db_session):
        """Test API key encryption with Fernet"""
        service = UserAuthService(db_session)
        
        api_key = "test_api_key_12345"
        encrypted = service.encrypt_api_key(api_key)
        
        # Verify encryption
        assert encrypted != api_key
        assert len(encrypted) > len(api_key)
    
    def test_decrypt_api_key(self, db_session):
        """Test API key decryption"""
        service = UserAuthService(db_session)
        
        api_key = "test_api_key_12345"
        encrypted = service.encrypt_api_key(api_key)
        decrypted = service.decrypt_api_key(encrypted)
        
        # Verify decryption
        assert decrypted == api_key
    
    def test_generate_api_key(self, db_session):
        """Test API key generation"""
        service = UserAuthService(db_session)
        
        api_key = service.generate_api_key()
        
        # Verify format (32 hex characters)
        assert len(api_key) == 64  # 32 bytes = 64 hex chars
        assert all(c in '0123456789abcdef' for c in api_key)
    
    def test_verify_api_key_valid(self, db_session):
        """Test API key verification with valid key"""
        service = UserAuthService(db_session)
        
        # Create user with API key
        user = User(
            username="testuser",
            password_hash=service.hash_password("password"),
            api_key=service.encrypt_api_key("test_key_123")
        )
        db_session.add(user)
        db_session.commit()
        
        # Verify API key
        verified_user = service.verify_api_key("test_key_123")
        assert verified_user is not None
        assert verified_user.username == "testuser"
    
    def test_verify_api_key_invalid(self, db_session):
        """Test API key verification with invalid key"""
        service = UserAuthService(db_session)
        
        # Verify non-existent key
        verified_user = service.verify_api_key("invalid_key")
        assert verified_user is None
    
    def test_api_key_caching(self, db_session):
        """Test that API key verification uses cache"""
        service = UserAuthService(db_session)
        
        # Create user
        user = User(
            username="testuser",
            password_hash=service.hash_password("password"),
            api_key=service.encrypt_api_key("test_key_123")
        )
        db_session.add(user)
        db_session.commit()
        
        # First verification (cache miss)
        user1 = service.verify_api_key("test_key_123")
        
        # Second verification (cache hit)
        user2 = service.verify_api_key("test_key_123")
        
        # Both should return same user
        assert user1.id == user2.id
    
    def test_create_session(self, db_session):
        """Test session creation"""
        service = UserAuthService(db_session)
        
        # Create user
        user = User(
            username="testuser",
            password_hash=service.hash_password("password")
        )
        db_session.add(user)
        db_session.commit()
        
        # Create session
        session = service.create_session(user.id)
        
        assert session is not None
        assert session.user_id == user.id
        assert session.is_active is True
    
    def test_verify_session_valid(self, db_session):
        """Test session verification with valid session"""
        service = UserAuthService(db_session)
        
        # Create user and session
        user = User(
            username="testuser",
            password_hash=service.hash_password("password")
        )
        db_session.add(user)
        db_session.commit()
        
        session = service.create_session(user.id)
        
        # Verify session
        verified_session = service.verify_session(session.session_token)
        assert verified_session is not None
        assert verified_session.user_id == user.id
    
    def test_verify_session_expired(self, db_session):
        """Test that expired sessions are rejected"""
        service = UserAuthService(db_session)
        
        # Create user and session
        user = User(
            username="testuser",
            password_hash=service.hash_password("password")
        )
        db_session.add(user)
        db_session.commit()
        
        session = service.create_session(user.id)
        
        # Manually expire session
        session.expires_at = datetime.now(IST) - timedelta(hours=1)
        db_session.commit()
        
        # Verify session (should fail)
        verified_session = service.verify_session(session.session_token)
        assert verified_session is None
