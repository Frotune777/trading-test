"""
Unit tests for Angel One Authentication Module
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import pytz

from app.brokers.angelone.angelone_auth import AngelOneAuth

IST = pytz.timezone('Asia/Kolkata')


class TestAngelOneAuth:
    """Test suite for AngelOneAuth"""
    
    @pytest.fixture
    def auth(self):
        """Create AngelOneAuth instance for testing"""
        return AngelOneAuth(
            api_key="test_api_key",
            client_id="test_client_id",
            password="test_password",
            totp_secret="JBSWY3DPEHPK3PXP",  # Test TOTP secret
            base_url="https://apiconnect.angelbroking.com"
        )
    
    def test_generate_totp(self, auth):
        """Test TOTP generation"""
        totp_code = auth.generate_totp()
        
        assert totp_code is not None
        assert len(totp_code) == 6
        assert totp_code.isdigit()
    
    @patch('requests.post')
    def test_login_success(self, mock_post, auth):
        """Test successful login"""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": True,
            "data": {
                "jwtToken": "test_jwt_token"
            }
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        result = auth.login()
        
        assert result is True
        assert auth.jwt_token == "test_jwt_token"
        
        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "loginByPassword" in call_args[0][0]
    
    @patch('requests.post')
    def test_login_failure(self, mock_post, auth):
        """Test failed login"""
        # Mock failed response
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": False,
            "message": "Invalid credentials"
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        result = auth.login()
        
        assert result is False
        assert auth.jwt_token is None
    
    @patch('requests.post')
    def test_login_exception(self, mock_post, auth):
        """Test login with exception"""
        mock_post.side_effect = Exception("Network error")
        
        result = auth.login()
        
        assert result is False
        assert auth.jwt_token is None
    
    @patch('requests.post')
    def test_generate_tokens_success(self, mock_post, auth):
        """Test successful token generation"""
        # Set JWT token first
        auth.jwt_token = "test_jwt_token"
        
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": True,
            "data": {
                "jwtToken": "test_access_token",
                "refreshToken": "test_refresh_token",
                "feedToken": "test_feed_token"
            }
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        result = auth.generate_tokens()
        
        assert result is True
        assert auth.access_token == "test_access_token"
        assert auth.refresh_token == "test_refresh_token"
        assert auth.feed_token == "test_feed_token"
        assert auth.token_expiry is not None
    
    @patch('requests.post')
    def test_generate_tokens_no_jwt(self, mock_post, auth):
        """Test token generation without JWT token"""
        result = auth.generate_tokens()
        
        assert result is False
        mock_post.assert_not_called()
    
    @patch('requests.post')
    def test_generate_tokens_failure(self, mock_post, auth):
        """Test failed token generation"""
        auth.jwt_token = "test_jwt_token"
        
        # Mock failed response
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": False,
            "message": "Token generation failed"
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        result = auth.generate_tokens()
        
        assert result is False
        assert auth.access_token is None
    
    def test_is_token_valid_no_token(self, auth):
        """Test token validation with no token"""
        assert auth.is_token_valid() is False
    
    def test_is_token_valid_expired(self, auth):
        """Test token validation with expired token"""
        auth.access_token = "test_token"
        auth.token_expiry = datetime.now(IST) - timedelta(hours=1)
        
        assert auth.is_token_valid() is False
    
    def test_is_token_valid_active(self, auth):
        """Test token validation with active token"""
        auth.access_token = "test_token"
        auth.token_expiry = datetime.now(IST) + timedelta(hours=1)
        
        assert auth.is_token_valid() is True
    
    @patch.object(AngelOneAuth, 'login')
    @patch.object(AngelOneAuth, 'generate_tokens')
    def test_refresh_access_token(self, mock_generate, mock_login, auth):
        """Test access token refresh"""
        mock_login.return_value = True
        mock_generate.return_value = True
        
        result = auth.refresh_access_token()
        
        assert result is True
        mock_login.assert_called_once()
        mock_generate.assert_called_once()
    
    def test_get_headers(self, auth):
        """Test header generation"""
        auth.access_token = "test_access_token"
        
        headers = auth.get_headers()
        
        assert headers["X-PrivateKey"] == "test_api_key"
        assert headers["Authorization"] == "Bearer test_access_token"
        assert headers["Content-Type"] == "application/json"
    
    @pytest.mark.asyncio
    async def test_ensure_authenticated_valid_token(self, auth):
        """Test ensure_authenticated with valid token"""
        auth.access_token = "test_token"
        auth.token_expiry = datetime.now(IST) + timedelta(hours=1)
        
        result = await auth.ensure_authenticated()
        
        assert result is True
    
    @pytest.mark.asyncio
    @patch.object(AngelOneAuth, 'login')
    @patch.object(AngelOneAuth, 'generate_tokens')
    async def test_ensure_authenticated_expired_token(self, mock_generate, mock_login, auth):
        """Test ensure_authenticated with expired token"""
        mock_login.return_value = True
        mock_generate.return_value = True
        
        result = await auth.ensure_authenticated()
        
        assert result is True
        mock_login.assert_called_once()
        mock_generate.assert_called_once()
    
    @pytest.mark.asyncio
    @patch.object(AngelOneAuth, 'login')
    async def test_ensure_authenticated_failure(self, mock_login, auth):
        """Test ensure_authenticated with authentication failure"""
        mock_login.return_value = False
        
        result = await auth.ensure_authenticated()
        
        assert result is False
