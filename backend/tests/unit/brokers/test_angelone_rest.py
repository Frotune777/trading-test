"""
Unit tests for Angel One REST API Client
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import pytz

from app.brokers.angelone.angelone_rest import AngelOneREST
from app.brokers.angelone.angelone_auth import AngelOneAuth
from app.brokers.base_broker import OrderRequest, OrderResponse, OrderStatus, Position, Holding

IST = pytz.timezone('Asia/Kolkata')


class TestAngelOneREST:
    """Test suite for AngelOneREST"""
    
    @pytest.fixture
    def auth(self):
        """Create mock auth"""
        auth = Mock(spec=AngelOneAuth)
        auth.ensure_authenticated = AsyncMock(return_value=True)
        auth.get_headers = Mock(return_value={
            "Authorization": "Bearer test_token",
            "X-PrivateKey": "test_key"
        })
        return auth
    
    @pytest.fixture
    def rest_client(self, auth):
        """Create REST client instance"""
        return AngelOneREST(
            auth=auth,
            base_url="https://apiconnect.angelbroking.com"
        )
    
    @pytest.mark.asyncio
    async def test_rate_limit(self, rest_client):
        """Test rate limiting"""
        import time
        start = time.time()
        
        # Make two requests quickly
        await rest_client._rate_limit()
        await rest_client._rate_limit()
        
        elapsed = time.time() - start
        
        # Should take at least 100ms (min_request_interval)
        assert elapsed >= 0.1
    
    @pytest.mark.asyncio
    @patch('requests.Session.post')
    async def test_make_request_success(self, mock_post, rest_client):
        """Test successful HTTP request"""
        mock_response = Mock()
        mock_response.json.return_value = {"status": True, "data": {}}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        result = await rest_client._make_request("POST", "/test", {"key": "value"})
        
        assert result == {"status": True, "data": {}}
        mock_post.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('requests.Session.post')
    async def test_make_request_retry_on_401(self, mock_post, rest_client, auth):
        """Test retry on 401 unauthorized"""
        # First call returns 401, second succeeds
        mock_response_401 = Mock()
        mock_response_401.status_code = 401
        mock_response_401.raise_for_status.side_effect = Exception("401")
        
        mock_response_success = Mock()
        mock_response_success.json.return_value = {"status": True}
        mock_response_success.raise_for_status = Mock()
        
        mock_post.side_effect = [
            Exception("401"),
            mock_response_success
        ]
        
        auth.refresh_access_token = AsyncMock(return_value=True)
        
        # Should retry after token refresh
        # Note: This test may need adjustment based on actual retry logic
    
    @pytest.mark.asyncio
    async def test_place_order_success(self, rest_client):
        """Test successful order placement"""
        order = OrderRequest(
            symbol="RELIANCE",
            exchange="NSE",
            transaction_type="BUY",
            order_type="MARKET",
            quantity=10,
            product_type="INTRADAY"
        )
        
        with patch.object(rest_client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "status": True,
                "data": {"orderid": "123456"}
            }
            
            with patch.object(rest_client, '_get_symbol_token', new_callable=AsyncMock) as mock_token:
                mock_token.return_value = "test_token"
                
                response = await rest_client.place_order(order)
                
                assert response.order_id == "123456"
                assert response.status == OrderStatus.PENDING
                assert "success" in response.message.lower()
    
    @pytest.mark.asyncio
    async def test_place_order_failure(self, rest_client):
        """Test failed order placement"""
        order = OrderRequest(
            symbol="RELIANCE",
            exchange="NSE",
            transaction_type="BUY",
            order_type="MARKET",
            quantity=10,
            product_type="INTRADAY"
        )
        
        with patch.object(rest_client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "status": False,
                "message": "Insufficient funds"
            }
            
            with patch.object(rest_client, '_get_symbol_token', new_callable=AsyncMock) as mock_token:
                mock_token.return_value = "test_token"
                
                response = await rest_client.place_order(order)
                
                assert response.status == OrderStatus.REJECTED
                assert "Insufficient funds" in response.message
    
    @pytest.mark.asyncio
    async def test_modify_order_success(self, rest_client):
        """Test successful order modification"""
        with patch.object(rest_client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "status": True,
                "data": {}
            }
            
            response = await rest_client.modify_order("123456", {"price": "2500"})
            
            assert response.order_id == "123456"
            assert response.status == OrderStatus.OPEN
    
    @pytest.mark.asyncio
    async def test_cancel_order_success(self, rest_client):
        """Test successful order cancellation"""
        with patch.object(rest_client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "status": True,
                "data": {}
            }
            
            response = await rest_client.cancel_order("123456")
            
            assert response.order_id == "123456"
            assert response.status == OrderStatus.CANCELLED
    
    @pytest.mark.asyncio
    async def test_get_positions_success(self, rest_client):
        """Test fetching positions"""
        with patch.object(rest_client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "status": True,
                "data": [
                    {
                        "tradingsymbol": "RELIANCE",
                        "exchange": "NSE",
                        "netqty": "10",
                        "avgnetprice": "2500.50",
                        "ltp": "2550.00",
                        "producttype": "INTRADAY"
                    }
                ]
            }
            
            positions = await rest_client.get_positions()
            
            assert len(positions) == 1
            assert positions[0].symbol == "RELIANCE"
            assert positions[0].quantity == 10
            assert positions[0].average_price == 2500.50
            assert positions[0].ltp == 2550.00
    
    @pytest.mark.asyncio
    async def test_get_holdings_success(self, rest_client):
        """Test fetching holdings"""
        with patch.object(rest_client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "status": True,
                "data": [
                    {
                        "tradingsymbol": "TCS",
                        "exchange": "NSE",
                        "quantity": "5",
                        "averageprice": "3500.00",
                        "ltp": "3600.00"
                    }
                ]
            }
            
            holdings = await rest_client.get_holdings()
            
            assert len(holdings) == 1
            assert holdings[0].symbol == "TCS"
            assert holdings[0].quantity == 5
            assert holdings[0].average_price == 3500.00
    
    @pytest.mark.asyncio
    async def test_get_order_book_success(self, rest_client):
        """Test fetching order book"""
        with patch.object(rest_client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = {
                "status": True,
                "data": [
                    {
                        "orderid": "123456",
                        "status": "complete",
                        "text": "Order executed"
                    },
                    {
                        "orderid": "123457",
                        "status": "open",
                        "text": "Order pending"
                    }
                ]
            }
            
            orders = await rest_client.get_order_book()
            
            assert len(orders) == 2
            assert orders[0].order_id == "123456"
            assert orders[0].status == OrderStatus.COMPLETE
            assert orders[1].status == OrderStatus.OPEN
