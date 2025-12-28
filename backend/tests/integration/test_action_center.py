"""
Integration tests for Action Center and ExecutionGate
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.database.models_user import User
from app.database.models_action_center import PendingOrder
from app.services.user_auth_service import UserAuthService
from app.services.action_center_service import ActionCenterService

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

@pytest.fixture
def test_user_with_api_key(db_session):
    """Create a test user with API key"""
    auth_service = UserAuthService(db_session)
    user = auth_service.create_user("testuser", "password123")
    api_key = auth_service.generate_api_key(user.id)
    return {"user": user, "api_key": api_key}

class TestActionCenter:
    """Integration tests for Action Center"""
    
    def test_create_pending_order(self, db_session, test_user_with_api_key):
        """Test creating a pending order"""
        action_center = ActionCenterService(db_session)
        user = test_user_with_api_key["user"]
        
        order_data = {
            "symbol": "NSE:RELIANCE",
            "exchange": "NSE",
            "action": "BUY",
            "quantity": 10,
            "price": 2500.00,
            "pricetype": "LIMIT",
            "product": "MIS"
        }
        
        pending_order = action_center.create_pending_order(
            user_id=user.id,
            api_type="placeorder",
            order_data=order_data,
            strategy_name="QUAD_V1"
        )
        
        assert pending_order.id is not None
        assert pending_order.status == "pending"
        assert pending_order.user_id == user.id
        assert pending_order.api_type == "placeorder"
    
    def test_get_pending_orders(self, client, test_user_with_api_key, db_session):
        """Test retrieving pending orders via API"""
        api_key = test_user_with_api_key["api_key"]
        user = test_user_with_api_key["user"]
        
        # Create a pending order
        action_center = ActionCenterService(db_session)
        action_center.create_pending_order(
            user_id=user.id,
            api_type="placeorder",
            order_data={"symbol": "NSE:RELIANCE", "action": "BUY", "quantity": 10}
        )
        
        # Get pending orders
        response = client.get(
            "/api/v1/action-center/orders",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "pending"
        assert data[0]["api_type"] == "placeorder"
    
    def test_approve_order(self, client, test_user_with_api_key, db_session):
        """Test approving a pending order"""
        api_key = test_user_with_api_key["api_key"]
        user = test_user_with_api_key["user"]
        
        # Create a pending order
        action_center = ActionCenterService(db_session)
        pending_order = action_center.create_pending_order(
            user_id=user.id,
            api_type="placeorder",
            order_data={"symbol": "NSE:RELIANCE", "action": "BUY", "quantity": 10}
        )
        
        # Approve order
        response = client.post(
            f"/api/v1/action-center/orders/{pending_order.id}/approve",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "approved" in data["message"].lower()
        assert data["order_id"] == pending_order.id
    
    def test_reject_order(self, client, test_user_with_api_key, db_session):
        """Test rejecting a pending order"""
        api_key = test_user_with_api_key["api_key"]
        user = test_user_with_api_key["user"]
        
        # Create a pending order
        action_center = ActionCenterService(db_session)
        pending_order = action_center.create_pending_order(
            user_id=user.id,
            api_type="placeorder",
            order_data={"symbol": "NSE:RELIANCE", "action": "BUY", "quantity": 10}
        )
        
        # Reject order
        response = client.post(
            f"/api/v1/action-center/orders/{pending_order.id}/reject",
            json={"reason": "Risk limits exceeded"},
            headers={"Authorization": f"Bearer {api_key}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "rejected" in data["message"].lower()
        assert data["order_id"] == pending_order.id
        
        # Verify order is rejected in database
        db_session.refresh(pending_order)
        assert pending_order.status == "rejected"
        assert pending_order.rejected_reason == "Risk limits exceeded"
    
    def test_bulk_approve(self, client, test_user_with_api_key, db_session):
        """Test bulk approval of multiple orders"""
        api_key = test_user_with_api_key["api_key"]
        user = test_user_with_api_key["user"]
        
        # Create multiple pending orders
        action_center = ActionCenterService(db_session)
        order_ids = []
        for i in range(3):
            pending_order = action_center.create_pending_order(
                user_id=user.id,
                api_type="placeorder",
                order_data={"symbol": f"NSE:STOCK{i}", "action": "BUY", "quantity": 10}
            )
            order_ids.append(pending_order.id)
        
        # Bulk approve
        response = client.post(
            "/api/v1/action-center/bulk-approve",
            json={"order_ids": order_ids},
            headers={"Authorization": f"Bearer {api_key}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert data["successful"] == 3
        assert data["failed"] == 0
    
    def test_get_statistics(self, client, test_user_with_api_key, db_session):
        """Test getting approval statistics"""
        api_key = test_user_with_api_key["api_key"]
        user = test_user_with_api_key["user"]
        
        # Create orders with different statuses
        action_center = ActionCenterService(db_session)
        
        # Create pending order
        action_center.create_pending_order(
            user_id=user.id,
            api_type="placeorder",
            order_data={"symbol": "NSE:STOCK1", "action": "BUY", "quantity": 10}
        )
        
        # Create and approve order
        order2 = action_center.create_pending_order(
            user_id=user.id,
            api_type="placeorder",
            order_data={"symbol": "NSE:STOCK2", "action": "BUY", "quantity": 10}
        )
        action_center.approve_order(order2.id, "testuser")
        
        # Create and reject order
        order3 = action_center.create_pending_order(
            user_id=user.id,
            api_type="placeorder",
            order_data={"symbol": "NSE:STOCK3", "action": "BUY", "quantity": 10}
        )
        action_center.reject_order(order3.id, "testuser", "Test rejection")
        
        # Get statistics
        response = client.get(
            "/api/v1/action-center/statistics",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert data["pending"] == 1
        assert data["approved"] >= 1  # Could be approved or executed
        assert data["rejected"] == 1
    
    def test_cannot_approve_other_users_order(self, client, db_session):
        """Test that users cannot approve orders from other users"""
        # Create two users
        auth_service = UserAuthService(db_session)
        user1 = auth_service.create_user("user1", "password123")
        api_key1 = auth_service.generate_api_key(user1.id)
        
        user2 = auth_service.create_user("user2", "password123")
        api_key2 = auth_service.generate_api_key(user2.id)
        
        # User1 creates an order
        action_center = ActionCenterService(db_session)
        pending_order = action_center.create_pending_order(
            user_id=user1.id,
            api_type="placeorder",
            order_data={"symbol": "NSE:RELIANCE", "action": "BUY", "quantity": 10}
        )
        
        # User2 tries to approve user1's order
        response = client.post(
            f"/api/v1/action-center/orders/{pending_order.id}/approve",
            headers={"Authorization": f"Bearer {api_key2}"}
        )
        
        assert response.status_code == 403
        assert "permission" in response.json()["detail"].lower()
    
    def test_order_parsing_placeorder(self, db_session, test_user_with_api_key):
        """Test order parsing for placeorder type"""
        action_center = ActionCenterService(db_session)
        user = test_user_with_api_key["user"]
        
        order_data = {
            "symbol": "NSE:RELIANCE",
            "exchange": "NSE",
            "action": "BUY",
            "quantity": 10,
            "price": 2500.00,
            "pricetype": "LIMIT",
            "product": "MIS",
            "strategy": "QUAD_V1"
        }
        
        pending_order = action_center.create_pending_order(
            user_id=user.id,
            api_type="placeorder",
            order_data=order_data
        )
        
        parsed = action_center.parse_order_details(pending_order)
        
        assert parsed["symbol"] == "NSE:RELIANCE"
        assert parsed["action"] == "BUY"
        assert parsed["quantity"] == "10"
        assert parsed["price"] == "2500.0"
        assert parsed["strategy"] == "QUAD_V1"
    
    def test_order_parsing_basketorder(self, db_session, test_user_with_api_key):
        """Test order parsing for basketorder type"""
        action_center = ActionCenterService(db_session)
        user = test_user_with_api_key["user"]
        
        order_data = {
            "orders": [
                {"symbol": "NSE:RELIANCE", "exchange": "NSE", "action": "BUY", "quantity": 10},
                {"symbol": "NSE:TCS", "exchange": "NSE", "action": "BUY", "quantity": 5}
            ],
            "strategy": "BASKET_STRATEGY"
        }
        
        pending_order = action_center.create_pending_order(
            user_id=user.id,
            api_type="basketorder",
            order_data=order_data
        )
        
        parsed = action_center.parse_order_details(pending_order)
        
        assert "Basket (2 orders)" in parsed["symbol"]
        assert parsed["quantity"] == "15"  # Sum of quantities
        assert parsed["strategy"] == "BASKET_STRATEGY"
