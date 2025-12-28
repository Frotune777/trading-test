"""
Angel One Authentication Module
Handles login, token generation, and TOTP 2FA
"""

import logging
import pyotp
import requests
from typing import Dict, Optional
from datetime import datetime, timedelta
import pytz

logger = logging.getLogger(__name__)
IST = pytz.timezone('Asia/Kolkata')


class AngelOneAuth:
    """Angel One authentication handler"""
    
    def __init__(self, api_key: str, client_id: str, password: str, totp_secret: str, base_url: str):
        """
        Initialize Angel One authentication
        
        Args:
            api_key: Angel One API key
            client_id: Client ID
            password: Password
            totp_secret: TOTP secret for 2FA
            base_url: Angel One REST API base URL
        """
        self.api_key = api_key
        self.client_id = client_id
        self.password = password
        self.totp_secret = totp_secret
        self.base_url = base_url
        
        # Tokens
        self.jwt_token: Optional[str] = None
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.feed_token: Optional[str] = None
        
        # Token expiry
        self.token_expiry: Optional[datetime] = None
    
    def generate_totp(self) -> str:
        """
        Generate TOTP code for 2FA
        
        Returns:
            6-digit TOTP code
        """
        totp = pyotp.TOTP(self.totp_secret)
        return totp.now()
    
    def login(self) -> bool:
        """
        Login to Angel One and get JWT token
        
        Returns:
            True if login successful
        """
        try:
            url = f"{self.base_url}/rest/auth/angelbroking/user/v1/loginByPassword"
            
            totp_code = self.generate_totp()
            
            payload = {
                "clientcode": self.client_id,
                "password": self.password,
                "totp": totp_code
            }
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-UserType": "USER",
                "X-SourceID": "WEB",
                "X-ClientLocalIP": "127.0.0.1",
                "X-ClientPublicIP": "127.0.0.1",
                "X-MACAddress": "00:00:00:00:00:00",
                "X-PrivateKey": self.api_key
            }
            
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("status") and data.get("data"):
                self.jwt_token = data["data"].get("jwtToken")
                logger.info("Login successful, JWT token obtained")
                return True
            else:
                logger.error(f"Login failed: {data.get('message')}")
                return False
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False
    
    def generate_tokens(self) -> bool:
        """
        Generate access token, refresh token, and feed token
        
        Returns:
            True if token generation successful
        """
        try:
            if not self.jwt_token:
                logger.error("No JWT token available, login first")
                return False
            
            url = f"{self.base_url}/rest/auth/angelbroking/jwt/v1/generateTokens"
            
            payload = {
                "refreshToken": self.jwt_token
            }
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-UserType": "USER",
                "X-SourceID": "WEB",
                "X-ClientLocalIP": "127.0.0.1",
                "X-ClientPublicIP": "127.0.0.1",
                "X-MACAddress": "00:00:00:00:00:00",
                "X-PrivateKey": self.api_key,
                "Authorization": f"Bearer {self.jwt_token}"
            }
            
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("status") and data.get("data"):
                self.access_token = data["data"].get("jwtToken")
                self.refresh_token = data["data"].get("refreshToken")
                self.feed_token = data["data"].get("feedToken")
                
                # Set token expiry (typically 24 hours)
                self.token_expiry = datetime.now(IST) + timedelta(hours=24)
                
                logger.info("Tokens generated successfully")
                return True
            else:
                logger.error(f"Token generation failed: {data.get('message')}")
                return False
                
        except Exception as e:
            logger.error(f"Token generation error: {e}")
            return False
    
    def is_token_valid(self) -> bool:
        """
        Check if access token is valid
        
        Returns:
            True if token is valid
        """
        if not self.access_token or not self.token_expiry:
            return False
        
        # Check if token expired
        if datetime.now(IST) >= self.token_expiry:
            return False
        
        return True
    
    def refresh_access_token(self) -> bool:
        """
        Refresh access token using refresh token
        
        Returns:
            True if refresh successful
        """
        # For Angel One, we need to re-login
        # They don't support traditional refresh token flow
        logger.info("Refreshing tokens by re-login")
        return self.login() and self.generate_tokens()
    
    def get_headers(self) -> Dict[str, str]:
        """
        Get authenticated request headers
        
        Returns:
            Headers dict with authorization
        """
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-UserType": "USER",
            "X-SourceID": "WEB",
            "X-ClientLocalIP": "127.0.0.1",
            "X-ClientPublicIP": "127.0.0.1",
            "X-MACAddress": "00:00:00:00:00:00",
            "X-PrivateKey": self.api_key,
            "Authorization": f"Bearer {self.access_token}"
        }
    
    async def ensure_authenticated(self) -> bool:
        """
        Ensure we have valid authentication
        
        Returns:
            True if authenticated
        """
        if self.is_token_valid():
            return True
        
        # Need to authenticate
        if self.login() and self.generate_tokens():
            return True
        
        return False
