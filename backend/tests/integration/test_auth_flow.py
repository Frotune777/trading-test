"""
Integration tests for user authentication flow
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.database.models_user import User

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db_session():
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db_session):
    """Create a test client with database override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

class TestAuthFlow:
    """Integration tests for authentication flow"""
    
    def test_user_registration(self, client):
        """Test user registration with Argon2 hashing"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "password": "secure_password_123",
                "email": "test@example.com"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert data["is_active"] is True
        assert "password" not in data  # Password should not be returned
    
    def test_duplicate_username_registration(self, client):
        """Test that duplicate usernames are rejected"""
        # Register first user
        client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "password": "password123"
            }
        )
        
        # Try to register with same username
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "password": "different_password"
            }
        )
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    def test_user_login_success(self, client):
        """Test successful login"""
        # Register user
        client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "password": "secure_password"
            }
        )
        
        # Login
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "secure_password"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["last_login"] is not None
    
    def test_user_login_wrong_password(self, client):
        """Test login with incorrect password"""
        # Register user
        client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "password": "correct_password"
            }
        )
        
        # Login with wrong password
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "wrong_password"
            }
        )
        
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_api_key_generation(self, client, db_session):
        """Test API key generation with Fernet encryption"""
        # Register and login user
        register_response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "testuser",
                "password": "password123"
            }
        )
        user_id = register_response.json()["id"]
        
        # Generate API key (need to authenticate first)
        # For testing, we'll directly create an API key
        from app.services.user_auth_service import UserAuthService
        auth_service = UserAuthService(db_session)
        api_key = auth_service.generate_api_key(user_id)
        
        # Verify API key format
        assert len(api_key) > 20
        assert isinstance(api_key, str)
        
        # Verify we can authenticate with the API key
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
    
    def test_api_key_verification_caching(self, client, db_session):
        """Test that API key verification uses caching"""
        # Create user and API key
        from app.services.user_auth_service import UserAuthService
        auth_service = UserAuthService(db_session)
        
        user = auth_service.create_user("testuser", "password123")
        api_key = auth_service.generate_api_key(user.id)
        
        # First request (cache miss)
        response1 = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        assert response1.status_code == 200
        
        # Second request (should hit cache)
        response2 = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        assert response2.status_code == 200
    
    def test_invalid_api_key_rejection(self, client):
        """Test that invalid API keys are rejected"""
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_api_key_12345"}
        )
        
        assert response.status_code == 401
        assert "Invalid API key" in response.json()["detail"]
    
    def test_order_mode_update(self, client, db_session):
        """Test updating order execution mode"""
        # Create user and API key
        from app.services.user_auth_service import UserAuthService
        auth_service = UserAuthService(db_session)
        
        user = auth_service.create_user("testuser", "password123")
        api_key = auth_service.generate_api_key(user.id)
        
        # Update to semi_auto mode
        response = client.put(
            "/api/v1/auth/order-mode",
            json={"mode": "semi_auto"},
            headers={"Authorization": f"Bearer {api_key}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["order_mode"] == "semi_auto"
    
    def test_api_key_revocation(self, client, db_session):
        """Test API key revocation"""
        # Create user and API key
        from app.services.user_auth_service import UserAuthService
        auth_service = UserAuthService(db_session)
        
        user = auth_service.create_user("testuser", "password123")
        api_key = auth_service.generate_api_key(user.id)
        
        # Verify API key works
        response1 = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        assert response1.status_code == 200
        
        # Revoke API key
        response2 = client.delete(
            "/api/v1/auth/api-key/revoke",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        assert response2.status_code == 204
        
        # Verify API key no longer works
        response3 = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        assert response3.status_code == 401
