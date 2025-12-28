"""
Broker Factory
Creates broker instances based on configuration
"""

import logging
from typing import Dict, Any

from app.brokers.base_broker import BaseBroker
from app.core.config import settings

logger = logging.getLogger(__name__)


class BrokerFactory:
    """Factory for creating broker instances"""
    
    _brokers: Dict[str, type] = {}
    
    @classmethod
    def register_broker(cls, name: str, broker_class: type):
        """
        Register a broker implementation
        
        Args:
            name: Broker identifier
            broker_class: Broker class
        """
        cls._brokers[name] = broker_class
        logger.info(f"Registered broker: {name}")
    
    @classmethod
    def create_broker(cls, broker_name: str, config: Dict[str, Any] = None) -> BaseBroker:
        """
        Create a broker instance
        
        Args:
            broker_name: Broker identifier ("angelone", "openalgo", etc.)
            config: Optional broker-specific configuration
            
        Returns:
            Broker instance
            
        Raises:
            ValueError: If broker not found
        """
        if broker_name not in cls._brokers:
            raise ValueError(
                f"Unknown broker: {broker_name}. "
                f"Available brokers: {list(cls._brokers.keys())}"
            )
        
        broker_class = cls._brokers[broker_name]
        
        # Use provided config or load from settings
        if config is None:
            config = cls._get_broker_config(broker_name)
        
        logger.info(f"Creating broker instance: {broker_name}")
        return broker_class(config)
    
    @classmethod
    def _get_broker_config(cls, broker_name: str) -> Dict[str, Any]:
        """
        Get broker configuration from settings
        
        Args:
            broker_name: Broker identifier
            
        Returns:
            Broker configuration
        """
        if broker_name == "angelone":
            return {
                "api_key": settings.ANGELONE_API_KEY,
                "client_id": settings.ANGELONE_CLIENT_ID,
                "password": settings.ANGELONE_PASSWORD,
                "totp_secret": settings.ANGELONE_TOTP_SECRET,
                "ws_url": settings.ANGELONE_WS_URL,
                "rest_url": settings.ANGELONE_REST_URL,
            }
        elif broker_name == "openalgo":
            return {
                "base_url": settings.OPENALGO_BASE_URL,
                "api_key": settings.OPENALGO_API_KEY,
            }
        else:
            return {}
    
    @classmethod
    def get_primary_broker(cls) -> BaseBroker:
        """
        Get the primary broker instance
        
        Returns:
            Primary broker instance
        """
        broker_name = settings.PRIMARY_BROKER
        return cls.create_broker(broker_name)
    
    @classmethod
    def list_brokers(cls) -> list:
        """
        List all registered brokers
        
        Returns:
            List of broker names
        """
        return list(cls._brokers.keys())


# Auto-register brokers when they're imported
def _register_brokers():
    """Register all available brokers"""
    try:
        from app.brokers.angelone.angelone_broker import AngelOneBroker
        BrokerFactory.register_broker("angelone", AngelOneBroker)
    except ImportError:
        logger.warning("Angel One broker not available")
    
    try:
        from app.websocket.adapters.openalgo_adapter import OpenAlgoBroker
        BrokerFactory.register_broker("openalgo", OpenAlgoBroker)
    except ImportError:
        logger.warning("OpenAlgo broker not available")


# Register brokers on module import
_register_brokers()
