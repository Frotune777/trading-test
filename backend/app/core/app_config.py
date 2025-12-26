"""
Configuration Loader
Loads and manages application configuration from YAML files.
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class BrokerConfig(BaseModel):
    """Broker configuration model"""
    enabled: bool = True
    priority: int = 1
    rate_limit_per_second: int = 10
    timeout_seconds: int = 30
    max_retries: int = 3
    symbol_format: str = "SYMBOL"


class ConnectionPoolConfig(BaseModel):
    """Connection pool configuration"""
    max_connections: int = 100
    max_keepalive_connections: int = 20
    keepalive_expiry_seconds: int = 30


class CircuitBreakerConfig(BaseModel):
    """Circuit breaker configuration"""
    failure_threshold: int = 3
    recovery_timeout_seconds: int = 60
    half_open_max_calls: int = 5


class CacheConfig(BaseModel):
    """Cache configuration"""
    ltp_ttl_seconds: int = 5
    symbol_token_ttl_seconds: int = 86400
    instrument_token_ttl_seconds: int = 86400


class MarketHoursConfig(BaseModel):
    """Market hours configuration"""
    pre_market_start: str = "09:00"
    market_open: str = "09:15"
    market_close: str = "15:30"
    post_market_end: str = "16:00"


class AppConfig:
    """
    Application Configuration Manager
    
    Loads configuration from YAML files with environment variable override.
    
    Usage:
        config = AppConfig()
        zerodha_config = config.get_broker_config("zerodha")
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            # Default to backend/config/brokers.yaml
            config_path = Path(__file__).parent.parent.parent / "config" / "brokers.yaml"
        
        self.config_path = config_path
        self.config_data: Dict[str, Any] = {}
        self.broker_configs: Dict[str, BrokerConfig] = {}
        
        self._load_config()
        logger.info(f"Configuration loaded from {config_path}")
    
    def _load_config(self):
        """Load configuration from YAML file"""
        try:
            if not self.config_path.exists():
                logger.warning(f"Config file not found: {self.config_path}, using defaults")
                self.config_data = self._get_default_config()
                return
            
            with open(self.config_path, 'r') as f:
                self.config_data = yaml.safe_load(f)
            
            # Parse broker configs
            if 'brokers' in self.config_data:
                for broker_name, broker_data in self.config_data['brokers'].items():
                    self.broker_configs[broker_name] = BrokerConfig(**broker_data)
            
            logger.info(f"Loaded configuration for {len(self.broker_configs)} brokers")
            
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            self.config_data = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'brokers': {},
            'connection_pool': {
                'max_connections': 100,
                'max_keepalive_connections': 20,
                'keepalive_expiry_seconds': 30
            },
            'circuit_breaker': {
                'failure_threshold': 3,
                'recovery_timeout_seconds': 60,
                'half_open_max_calls': 5
            },
            'cache': {
                'ltp_ttl_seconds': 5,
                'symbol_token_ttl_seconds': 86400,
                'instrument_token_ttl_seconds': 86400
            },
            'market_hours': {
                'pre_market_start': '09:00',
                'market_open': '09:15',
                'market_close': '15:30',
                'post_market_end': '16:00'
            }
        }
    
    def get_broker_config(self, broker_name: str) -> Optional[BrokerConfig]:
        """Get configuration for specific broker"""
        return self.broker_configs.get(broker_name)
    
    def get_connection_pool_config(self) -> ConnectionPoolConfig:
        """Get connection pool configuration"""
        data = self.config_data.get('connection_pool', {})
        return ConnectionPoolConfig(**data)
    
    def get_circuit_breaker_config(self) -> CircuitBreakerConfig:
        """Get circuit breaker configuration"""
        data = self.config_data.get('circuit_breaker', {})
        return CircuitBreakerConfig(**data)
    
    def get_cache_config(self) -> CacheConfig:
        """Get cache configuration"""
        data = self.config_data.get('cache', {})
        return CacheConfig(**data)
    
    def get_market_hours_config(self) -> MarketHoursConfig:
        """Get market hours configuration"""
        data = self.config_data.get('market_hours', {})
        return MarketHoursConfig(**data)
    
    def is_broker_enabled(self, broker_name: str) -> bool:
        """Check if broker is enabled"""
        config = self.get_broker_config(broker_name)
        return config.enabled if config else False
    
    def get_enabled_brokers(self) -> list[str]:
        """Get list of enabled broker names"""
        return [
            name for name, config in self.broker_configs.items()
            if config.enabled
        ]


# Global configuration instance
app_config = AppConfig()
