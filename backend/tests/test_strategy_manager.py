import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from app.services.strategy_manager import StrategyManager
from app.database.models_strategy import Strategy, StrategySymbolMapping
from app.database.models_decision import DecisionLedger
from app.database.models_action_center import PendingOrder
from app.core.config import settings

# Setup Async DB for these tests
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.database import Base

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
async def test_strat_manager_fetch_active(async_db_session):
    manager = StrategyManager(async_db_session)
    
    # Create strategies
    s1 = Strategy(name="S1", webhook_id="w1", user_id="u1", platform="PYTHON", is_active=True)
    s2 = Strategy(name="S2", webhook_id="w2", user_id="u1", platform="TRADINGVIEW", is_active=False)
    async_db_session.add_all([s1, s2])
    await async_db_session.commit()
    
    active = await manager.get_active_strategies()
    assert len(active) == 1
    assert active[0].name == "S1"

@pytest.mark.asyncio
async def test_strat_manager_execution_cycle(async_db_session):
    manager = StrategyManager(async_db_session)
    
    # 1. Setup Data
    s1 = Strategy(id=1, name="TrendStrategy", webhook_id="w3", user_id="u1", platform="PYTHON", is_active=True)
    async_db_session.add(s1)
    
    m1 = StrategySymbolMapping(strategy_id=1, symbol="RELIANCE", exchange="NSE", quantity=10, product_type="CN")
    async_db_session.add(m1)
    
    await async_db_session.commit()

    # 2. Mock decision generation to return a valid decision
    mock_decision = DecisionLedger(
        decision_id="mock-dec-1", user_id="u1", strategy_id=1, symbol="RELIANCE",
        mode="LIVE", final_decision="BUY", conviction=90, inputs={}, weights={}, risk_checks={}, causal_graph=[],
        validity_window_mins=15, strategy_name_snapshot="TrendStrategy"
    )
    
    # We patch generate_mock_decision on the INSTANCE or Class
    # Since Manager is instantiated inside test, we can patch the method on the instance or use patch.object on class
    
    with patch.object(StrategyManager, 'generate_mock_decision', new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_decision
        
        # Enable Execution
        with patch.object(settings, 'EXECUTION_ENABLED', True):
            await manager.run_strategy_cycle()
            
            # Verify it tried to fetch symbols and generate decision
            assert mock_gen.call_count == 1
            
            # Verify interception happened (check DB for PendingOrder)
            # Since manager.gate is real, it writes to DB
            from sqlalchemy import select
            stmt = select(PendingOrder).where(PendingOrder.decision_id == "mock-dec-1")
            result = await async_db_session.execute(stmt)
            order = result.scalar_one_or_none()
            
            assert order is not None
            assert order.status == "pending"

@pytest.mark.asyncio
async def test_strat_manager_kill_switch_respect(async_db_session):
    manager = StrategyManager(async_db_session)
    
    with patch.object(settings, 'EXECUTION_ENABLED', False):
         # It should return immediately
         with patch.object(manager, 'get_active_strategies') as mock_get:
             await manager.run_strategy_cycle()
             mock_get.assert_not_called()
