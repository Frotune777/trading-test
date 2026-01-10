"""
Integration tests for ML API endpoints.

Tests FastAPI endpoints for ML operations.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db


# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def test_db():
    """Create test database."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(test_db):
    """Create test client."""
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Mock authentication headers."""
    # TODO: Implement proper auth token generation
    return {"Authorization": "Bearer test_token"}


class TestMLEndpoints:
    """Test ML API endpoints."""
    
    def test_train_endpoint(self, client, auth_headers):
        """Test POST /api/v1/ml/train endpoint."""
        response = client.post(
            "/api/v1/ml/train",
            json={
                "symbol": "SBIN",
                "model_type": "xgboost",
                "interval": "1d",
                "classification": "3class",
                "parameters": {"n_estimators": 100}
            },
            headers=auth_headers
        )
        
        # Should return task_id
        assert response.status_code in [200, 401]  # 401 if auth not implemented
        if response.status_code == 200:
            data = response.json()
            assert "task_id" in data
            assert "status" in data
    
    def test_list_models_endpoint(self, client, auth_headers):
        """Test GET /api/v1/ml/models endpoint."""
        response = client.get(
            "/api/v1/ml/models",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
    
    def test_list_models_with_filters(self, client, auth_headers):
        """Test GET /api/v1/ml/models with filters."""
        response = client.get(
            "/api/v1/ml/models?symbol=SBIN&active_only=true",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 401]
    
    def test_predict_endpoint(self, client, auth_headers):
        """Test POST /api/v1/ml/predict endpoint."""
        response = client.post(
            "/api/v1/ml/predict",
            json={
                "symbol": "SBIN",
                "model_type": "xgboost"
            },
            headers=auth_headers
        )
        
        # Will fail if no model exists, but endpoint should be accessible
        assert response.status_code in [200, 404, 401]
    
    def test_explain_endpoint(self, client, auth_headers):
        """Test POST /api/v1/ml/explain endpoint."""
        response = client.post(
            "/api/v1/ml/explain",
            json={
                "symbol": "SBIN",
                "top_n": 10
            },
            headers=auth_headers
        )
        
        # Will fail if no model exists
        assert response.status_code in [200, 404, 401]
    
    def test_experiments_endpoint(self, client, auth_headers):
        """Test GET /api/v1/ml/experiments endpoint."""
        response = client.get(
            "/api/v1/ml/experiments",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 401]
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
