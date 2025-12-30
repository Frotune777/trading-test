import pytest
from datetime import datetime
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import FastAPI
from app.main import app
from app.brokers.base_adapter import BrokerType

@pytest.mark.asyncio
async def test_run_reconciliation_api():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        with patch("app.api.v1.endpoints.reconciliation.PositionReconciliationService") as mock_service_class:
            mock_service = AsyncMock()
            mock_run = MagicMock()
            mock_run.id = 1
            mock_run.status = "COMPLETED"
            mock_run.run_time = datetime.now()
            mock_run.error_message = None
            mock_service.reconcile_positions.return_value = mock_run
            mock_service_class.return_value = mock_service
            
            # Mock get_current_user
            with patch("app.api.v1.endpoints.reconciliation.get_current_user") as mock_user:
                mock_user.return_value = AsyncMock(id=1)
                
                response = await ac.post("/api/v1/reconciliation/run?broker=angelone")
                assert response.status_code == 200
                assert response.json()["id"] == 1

@pytest.mark.asyncio
async def test_get_reconciliation_runs_api():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        with patch("app.api.v1.endpoints.reconciliation.PositionReconciliationService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_reconciliation_runs.return_value = []
            mock_service_class.return_value = mock_service
            
            with patch("app.api.v1.endpoints.reconciliation.get_current_user") as mock_user:
                mock_user.return_value = AsyncMock(id=1)
                
                response = await ac.get("/api/v1/reconciliation/runs")
                assert response.status_code == 200
                assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_get_discrepancies_api():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        with patch("app.api.v1.endpoints.reconciliation.PositionReconciliationService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.get_recent_discrepancies.return_value = []
            mock_service_class.return_value = mock_service
            
            with patch("app.api.v1.endpoints.reconciliation.get_current_user") as mock_user:
                mock_user.return_value = AsyncMock(id=1)
                
                response = await ac.get("/api/v1/reconciliation/discrepancies")
                assert response.status_code == 200
                assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_get_report_api():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        with patch("app.api.v1.endpoints.reconciliation.PositionReconciliationService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.generate_reconciliation_report.return_value = {"run_id": 1, "status": "COMPLETED"}
            mock_service_class.return_value = mock_service
            
            with patch("app.api.v1.endpoints.reconciliation.get_current_user") as mock_user:
                mock_user.return_value = AsyncMock(id=1)
                
                response = await ac.get("/api/v1/reconciliation/report/1")
                assert response.status_code == 200
                assert response.json()["run_id"] == 1

@pytest.mark.asyncio
async def test_get_report_not_found_api():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        with patch("app.api.v1.endpoints.reconciliation.PositionReconciliationService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.generate_reconciliation_report.return_value = None
            mock_service_class.return_value = mock_service
            
            with patch("app.api.v1.endpoints.reconciliation.get_current_user") as mock_user:
                mock_user.return_value = AsyncMock(id=1)
                
                response = await ac.get("/api/v1/reconciliation/report/999")
                assert response.status_code == 404
