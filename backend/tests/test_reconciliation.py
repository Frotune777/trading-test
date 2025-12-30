import pytest
import logging
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.reconciliation_service import PositionReconciliationService
from app.brokers.base_adapter import BrokerType, Position
from app.database.models_monitoring import TradePerformance
from app.database.models_position import ReconciliationRun, PositionSnapshot, PositionDiscrepancy

@pytest.fixture
async def mock_db():
    db = AsyncMock(spec=AsyncSession)
    # Mock scalars().all() for local trades
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = []
    db.execute.return_value = mock_result
    return db

@pytest.mark.asyncio
async def test_reconcile_positions_no_drift(mock_db):
    # Setup
    service = PositionReconciliationService(mock_db)
    
    # Mock broker positions
    mock_pos = Position(
        symbol="RELIANCE",
        exchange="NSE",
        quantity=100,
        average_price=2500.0,
        pnl=100.0,
        product="MIS"
    )
    
    with patch("app.services.reconciliation_service.broker_gateway") as mock_gateway:
        mock_gateway.brokers = {BrokerType.ANGELONE: AsyncMock()}
        mock_gateway.brokers[BrokerType.ANGELONE].get_positions.return_value = [mock_pos]
        
        # Mock local trades to match
        mock_trade = TradePerformance(
            symbol="RELIANCE",
            quantity=100,
            entry_price=2500.0,
            status="OPEN",
            user_id=1
        )
        mock_result = MagicMock()
        mock_result.scalars().all.return_value = [mock_trade]
        mock_db.execute.return_value = mock_result
        
        # Run
        run = await service.reconcile_positions(user_id=1)
        
        # Assert
        assert run.status == "COMPLETED"
        assert run.discrepancies_found == 0
        assert run.total_positions == 1

@pytest.mark.asyncio
async def test_reconcile_positions_with_drift(mock_db):
    # Setup
    service = PositionReconciliationService(mock_db)
    
    # Mock broker positions (100 shares)
    mock_pos = Position(
        symbol="RELIANCE",
        exchange="NSE",
        quantity=100,
        average_price=2500.0,
        pnl=100.0,
        product="MIS"
    )
    
    with patch("app.services.reconciliation_service.broker_gateway") as mock_gateway:
        mock_gateway.brokers = {BrokerType.ANGELONE: AsyncMock()}
        mock_gateway.brokers[BrokerType.ANGELONE].get_positions.return_value = [mock_pos]
        
        # Mock local trades (50 shares - DISCREPANCY)
        mock_trade = TradePerformance(
            symbol="RELIANCE",
            quantity=50,
            entry_price=2500.0,
            status="OPEN",
            user_id=1
        )
        mock_result = MagicMock()
        mock_result.scalars().all.return_value = [mock_trade]
        mock_db.execute.return_value = mock_result
        
        # Run
        run = await service.reconcile_positions(user_id=1)
        
        # Assert
        assert run.status == "COMPLETED"
        assert run.discrepancies_found == 1
        assert run.total_positions == 1

@pytest.mark.asyncio
async def test_reconcile_positions_rogue_trade(mock_db):
    # Setup
    service = PositionReconciliationService(mock_db)
    
    # Mock broker positions (RELIANCE)
    mock_pos = Position(
        symbol="RELIANCE",
        exchange="NSE",
        quantity=100,
        average_price=2500.0,
        pnl=100.0,
        product="MIS"
    )
    
    with patch("app.services.reconciliation_service.broker_gateway") as mock_gateway:
        mock_gateway.brokers = {BrokerType.ANGELONE: AsyncMock()}
        mock_gateway.brokers[BrokerType.ANGELONE].get_positions.return_value = [mock_pos]
        
        # Mock local trades (Empty - Rogue trade detected)
        mock_result = MagicMock()
        mock_result.scalars().all.return_value = []
        mock_db.execute.return_value = mock_result
        
        # Run
        run = await service.reconcile_positions(user_id=1)
        
        # Assert
        assert run.status == "COMPLETED"
        assert run.discrepancies_found == 1

@pytest.mark.asyncio
async def test_reconcile_positions_local_only(mock_db):
    """Test when a position is in TradePerformance but NOT at the broker."""
    service = PositionReconciliationService(mock_db)
    
    with patch("app.services.reconciliation_service.broker_gateway") as mock_gateway:
        mock_gateway.brokers = {BrokerType.ANGELONE: AsyncMock()}
        mock_gateway.brokers[BrokerType.ANGELONE].get_positions.return_value = []
        
        # Local trade exists
        mock_trade = TradePerformance(
            symbol="HDFC", quantity=10, entry_price=1500.0, status="OPEN", user_id=1
        )
        mock_result = MagicMock()
        mock_result.scalars().all.return_value = [mock_trade]
        mock_db.execute.return_value = mock_result
        
        run = await service.reconcile_positions(user_id=1)
        assert run.discrepancies_found == 1

@pytest.mark.asyncio
async def test_reconcile_positions_broker_filter(mock_db):
    """Test reconciliation with a specific broker filter."""
    service = PositionReconciliationService(mock_db)
    
    with patch("app.services.reconciliation_service.broker_gateway") as mock_gateway:
        mock_gateway.brokers = {BrokerType.ANGELONE: AsyncMock(), BrokerType.ZERODHA: AsyncMock()}
        mock_gateway.brokers[BrokerType.ANGELONE].get_positions.return_value = []
        
        run = await service.reconcile_positions(broker_filter=BrokerType.ANGELONE)
        assert run.brokers_checked == [BrokerType.ANGELONE.value]
        
        # Test broker not in gateway (hits line 214)
        mock_gateway.brokers = {BrokerType.ANGELONE: AsyncMock()}
        run = await service.reconcile_positions(broker_filter=BrokerType.ZERODHA)
        assert run.status == "COMPLETED"

@pytest.mark.asyncio
async def test_reconcile_positions_broker_failure(mock_db):
    """Test when broker gateway fails to return positions (Exception in _get_broker_positions)."""
    service = PositionReconciliationService(mock_db)
    
    with patch("app.services.reconciliation_service.broker_gateway") as mock_gateway:
        mock_gateway.brokers = {BrokerType.ANGELONE: AsyncMock()}
        # Make _get_broker_positions return None via exception to hit line 91
        mock_gateway.brokers[BrokerType.ANGELONE].get_positions.side_effect = Exception("API Down")
        
        run = await service.reconcile_positions()
        assert run.status == "COMPLETED"

@pytest.mark.asyncio
async def test_reconcile_positions_exception(mock_db):
    """Test top-level exception handling during processing."""
    service = PositionReconciliationService(mock_db)
    
    with patch("app.services.reconciliation_service.broker_gateway") as mock_gateway:
        mock_gateway.brokers = {BrokerType.ANGELONE: AsyncMock()}
        mock_gateway.brokers[BrokerType.ANGELONE].get_positions.return_value = []
        
        # Fail during local trades fetch (line 98)
        mock_db.execute.side_effect = Exception("Query Failed")
        
        with pytest.raises(Exception):
            await service.reconcile_positions()

@pytest.mark.asyncio
async def test_aux_methods(mock_db):
    """Test helper methods: get_recent_discrepancies, get_reconciliation_runs, generate_reconciliation_report."""
    service = PositionReconciliationService(mock_db)
    
    # Mocking for get_reconciliation_runs
    mock_run = ReconciliationRun(id=1, run_time=datetime.now())
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = [mock_run]
    mock_db.execute.return_value = mock_result
    
    runs = await service.get_reconciliation_runs()
    assert len(runs) == 1
    
    # Mocking for get_recent_discrepancies
    mock_disc = PositionDiscrepancy(id=1, symbol="SBI", detected_at=datetime.now(timezone.utc))
    mock_result.scalars().all.return_value = [mock_disc]
    
    discs = await service.get_recent_discrepancies(resolved=True)
    assert len(discs) == 1
    
    # Mocking for generate_reconciliation_report
    mock_run.completed_at = datetime.now()
    mock_result_run = MagicMock()
    mock_result_run.scalar_one_or_none.return_value = mock_run
    
    mock_result_disc = MagicMock()
    mock_result_disc.scalars().all.return_value = [mock_disc]
    
    mock_result_snap = MagicMock()
    mock_result_snap.scalars().all.return_value = []
    
    mock_db.execute.side_effect = [
        mock_result_run,
        mock_result_disc,
        mock_result_snap
    ]
    
    report = await service.generate_reconciliation_report(run_id=1)
    assert report["run_id"] == 1
    assert len(report["discrepancies"]) == 1

@pytest.mark.asyncio
async def test_generate_report_not_found(mock_db):
    service = PositionReconciliationService(mock_db)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    
    report = await service.generate_reconciliation_report(run_id=999)
    assert report is None
@pytest.mark.asyncio
async def test_run_reconciliation(mock_db):
    """Test the run_reconciliation alias/wrapper."""
    from app.services.reconciliation_service import reconciliation_service
    
    # 1. Test with existing db
    reconciliation_service.db = mock_db
    with patch.object(reconciliation_service, "reconcile_positions", new_callable=AsyncMock) as mock_recon:
        await reconciliation_service.run_reconciliation(user_id=1)
        mock_recon.assert_called_once_with(user_id=1)
    
    # 2. Test without db (using SessionLocal)
    reconciliation_service.db = None
    mock_session = AsyncMock()
    with patch("app.services.reconciliation_service.SessionLocal", return_value=MagicMock(__aenter__=AsyncMock(return_value=mock_session), __aexit__=AsyncMock())):
        with patch.object(reconciliation_service, "reconcile_positions", new_callable=AsyncMock) as mock_recon:
            await reconciliation_service.run_reconciliation(user_id=2)
            mock_recon.assert_called_once_with(user_id=2)
            assert reconciliation_service.db is None # Reset in finally
