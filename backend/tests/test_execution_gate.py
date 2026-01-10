import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from app.services.execution_gate import ExecutionGate
from app.database.models_decision import DecisionLedger
from app.database.models_action_center import PendingOrder, OrderApprovalLog
from app.database.models_strategy import Strategy  # Import Strategy to ensure table creation
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from unittest.mock import patch
from app.core.config import settings

# Setup Async DB for these tests
TEST_ASYNC_DB_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def async_db_engine():
    engine = create_async_engine(TEST_ASYNC_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture
async def async_db_session(async_db_engine):
    async_session = sessionmaker(
        async_db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session

@pytest.mark.asyncio
async def test_execution_gate_intercept_success(async_db_session):
    """
    Rule 2 Verification: Verify that a valid decision is intercepted and NOT executed immediately.
    """
    gate = ExecutionGate(async_db_session)
    db_session = async_db_session
    
    with patch.object(settings, 'EXECUTION_ENABLED', True):
        # 1A. Create Context (Strategy)
        strategy = Strategy(
            id=1, name="TestStrategy", webhook_id="wh-1", user_id="user123", platform="PYTHON"
        )
        db_session.add(strategy)
        await db_session.commit()

        # 1B. Create a mock DecisionLedger entry
        decision = DecisionLedger(
            decision_id="test-dec-001",
            user_id="user123",
            strategy_id=1,
            symbol="RELIANCE",
            mode="LIVE",
            final_decision="BUY",
            conviction=85,
            inputs={"price": 2500},
            weights={"Q": 0.25},
            risk_checks={"status": "PASS"},
            causal_graph=[],
            output_details={"symbol": "RELIANCE", "quantity": 10, "action": "BUY"},
            validity_window_mins=15,
            strategy_name_snapshot="TestStrategy"
        )
        db_session.add(decision)
        await db_session.commit()
        
        # 2. Intercept
        pending_order = await gate.intercept_decision(decision)
        
        # 3. Assertions
        assert pending_order is not None
        assert pending_order.status == "pending"
        assert pending_order.decision_id == "test-dec-001"
        assert pending_order.api_type == "smartorder"
        
        # Verify persistence
        stmt = select(PendingOrder).where(PendingOrder.id == pending_order.id)
        result = await db_session.execute(stmt)
        saved_order = result.scalar_one()
        assert saved_order.status == "pending"

@pytest.mark.asyncio
async def test_execution_gate_ignore_hold(async_db_session):
    """
    Verify that HOLD decisions are ignored.
    """
    gate = ExecutionGate(async_db_session)
    db_session = async_db_session
    
    with patch.object(settings, 'EXECUTION_ENABLED', True):
        decision = DecisionLedger(
            decision_id="test-dec-hold",
            user_id="user123",
            strategy_id=1,
            symbol="TCS",
            mode="LIVE",
            final_decision="HOLD",
            conviction=50,
            inputs={},
            weights={},
            risk_checks={},
            causal_graph=[],
            validity_window_mins=15
        )
        db_session.add(decision)
        await db_session.commit()
        
        pending_order = await gate.intercept_decision(decision)
        assert pending_order is None

@pytest.mark.asyncio
async def test_execution_gate_authorization(async_db_session):
    """
    Rule 2 Verification: Verify manual authorization updates status.
    """
    gate = ExecutionGate(async_db_session)
    db_session = async_db_session
    
    with patch.object(settings, 'EXECUTION_ENABLED', True):
        # Setup pending order
        order = PendingOrder(
            user_id=1,
            api_type="smartorder",
            order_data={},
            status="pending",
            created_at_ist=datetime.now(),
            decision_id="test-dec-auth"
        )
        db_session.add(order)
        await db_session.commit()
        
        # Authorize
        success = await gate.authorize_execution(order.id, "admin_user")
        
        assert success is True
        
        # Verify DB update
        await db_session.refresh(order)
        assert order.status == "approved"
        assert order.approved_by == "admin_user"
        assert order.approved_at_ist is not None
        
        # Verify Audit Log (Rule 34)
        stmt = select(OrderApprovalLog).where(OrderApprovalLog.pending_order_id == order.id)
        result = await db_session.execute(stmt)
        log = result.scalar_one()
        assert log.action == "approved"
        assert log.performed_by == "admin_user"

@pytest.mark.asyncio
async def test_execution_gate_rejection(async_db_session):
    """
    Verify rejection flow.
    """
    gate = ExecutionGate(async_db_session)
    db_session = async_db_session
    
    order = PendingOrder(
        user_id=1,
        api_type="smartorder",
        order_data={},
        status="pending",
        created_at_ist=datetime.now(),
        decision_id="test-dec-reject"
    )
    db_session.add(order)
    await db_session.commit()
    
    success = await gate.reject_execution(order.id, "admin_user", "Too risky")
    
    assert success is True
    
    await db_session.refresh(order)
    assert order.status == "rejected"
    assert order.rejected_reason == "Too risky"
    
    # Verify Log
    stmt = select(OrderApprovalLog).where(OrderApprovalLog.pending_order_id == order.id)
    result = await db_session.execute(stmt)
    log = result.scalar_one()
    assert log.action == "rejected"
    assert log.reason == "Too risky"

@pytest.mark.asyncio
async def test_execution_gate_validity_expiry(async_db_session):
    """
    Rule 14 Verification: Verify authorization fails if validity window passed.
    """
    gate = ExecutionGate(async_db_session)
    db_session = async_db_session
    
    with patch.object(settings, 'EXECUTION_ENABLED', True):
        # Create expired decision (created 20 mins ago, validity 15 mins)
        created_at = datetime.now() - timedelta(minutes=20)
        decision = DecisionLedger(
            decision_id="test-dec-expired",
            user_id="user123",
            strategy_id=1,
            symbol="INFY",
            mode="LIVE",
            final_decision="BUY",
            conviction=80,
            inputs={},
            weights={},
            risk_checks={},
            causal_graph=[],
            validity_window_mins=15
        )
        # Hack to simulate old timestamp
        decision.timestamp = created_at
        
        db_session.add(decision)
        await db_session.commit()
        
        order = PendingOrder(
            user_id=1,
            api_type="smartorder",
            order_data={},
            status="pending",
            created_at_ist=created_at, # Order created 20 mins ago
            decision_id="test-dec-expired"
        )
        db_session.add(order)
        await db_session.commit()
        
        # Attempt to authorize
        success = await gate.authorize_execution(order.id, "admin_user")
        
        assert success is False
        
        await db_session.refresh(order)
        assert order.status == "rejected" # Auto-rejected due to expiry

@pytest.mark.asyncio
async def test_execution_gate_kill_switch(async_db_session):
    """
    Rule 20 Verification: Verify kill switch blocks execution even if manually authorized.
    """
    gate = ExecutionGate(async_db_session)
    db_session = async_db_session
    
    # Ensure disabled
    with patch.object(settings, 'EXECUTION_ENABLED', False):
        # 1. Interception Check
        decision = DecisionLedger(
            decision_id="test-dec-kill",
            user_id="user123",
            strategy_id=1,
            symbol="WIPRO",
            mode="LIVE",
            final_decision="BUY",
            conviction=85,
            inputs={},
            weights={},
            risk_checks={},
            causal_graph=[],
            output_details={},
            validity_window_mins=15
        )
        db_session.add(decision)
        await db_session.commit()
        
        pending = await gate.intercept_decision(decision)
        assert pending is None # Should be blocked
        
        # 2. Authorization Check
        order = PendingOrder(
            user_id=1,
            api_type="smartorder",
            order_data={},
            status="pending",
            created_at_ist=datetime.now(),
            decision_id="test-dec-auth-kill"
        )
        db_session.add(order)
        await db_session.commit()
        
        success = await gate.authorize_execution(order.id, "admin_user")
        assert success is False # Should be blocked
