"""
Broker Registry - Auto-discovery and Management
Dynamically loads and manages broker adapters using plugin system.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from app.brokers.base_adapter import BrokerAdapter, BrokerType

logger = logging.getLogger(__name__)


class BrokerMetadata:
    """Broker plugin metadata"""
    
    def __init__(self, data: dict):
        self.broker_name = data.get("broker_name")
        self.display_name = data.get("display_name")
        self.version = data.get("version")
        self.enabled = data.get("enabled", True)
        self.supports = data.get("supports", {})
        self.credentials = data.get("credentials", [])
        self.rate_limits = data.get("rate_limits", {})
        self.symbol_format = data.get("symbol_format")
        self.exchange_support = data.get("exchange_support", [])


class BrokerRegistry:
    """
    Broker Registry with Plugin System
    
    Features:
        - Auto-discovery of brokers from plugin.json files
        - Dynamic broker loading
        - Metadata management
        - Enable/disable brokers
    
    Usage:
        registry = BrokerRegistry()
        registry.discover_brokers()
        broker = registry.get_broker(BrokerType.ZERODHA)
    """
    
    def __init__(self):
        self.metadata: Dict[BrokerType, BrokerMetadata] = {}
        self.adapters: Dict[BrokerType, BrokerAdapter] = {}
        logger.info("BrokerRegistry initialized")
    
    def discover_brokers(self) -> List[BrokerType]:
        """
        Auto-discover brokers from plugin.json files.
        
        Returns:
            List of discovered broker types
        """
        broker_dir = Path(__file__).parent
        discovered = []
        
        # Look for *_plugin.json files
        for plugin_file in broker_dir.glob("*_plugin.json"):
            try:
                with open(plugin_file, 'r') as f:
                    data = json.load(f)
                
                broker_name = data.get("broker_name")
                if not broker_name:
                    logger.warning(f"No broker_name in {plugin_file.name}, skipping")
                    continue
                
                # Convert to BrokerType
                try:
                    broker_type = BrokerType(broker_name)
                except ValueError:
                    logger.warning(f"Unknown broker type: {broker_name}, skipping")
                    continue
                
                # Store metadata
                metadata = BrokerMetadata(data)
                self.metadata[broker_type] = metadata
                discovered.append(broker_type)
                
                logger.info(
                    f"Discovered broker: {metadata.display_name} "
                    f"(v{metadata.version}, enabled={metadata.enabled})"
                )
                
            except Exception as e:
                logger.error(f"Error loading plugin {plugin_file.name}: {e}")
        
        logger.info(f"Discovered {len(discovered)} brokers: {[b.value for b in discovered]}")
        return discovered
    
    def register_adapter(self, adapter: BrokerAdapter):
        """
        Register a broker adapter instance.
        
        Args:
            adapter: BrokerAdapter instance
        """
        self.adapters[adapter.broker_type] = adapter
        logger.info(f"Registered adapter: {adapter.broker_name}")
    
    def get_broker(self, broker_type: BrokerType) -> Optional[BrokerAdapter]:
        """
        Get broker adapter by type.
        
        Args:
            broker_type: Broker type enum
            
        Returns:
            BrokerAdapter instance or None
        """
        return self.adapters.get(broker_type)
    
    def get_metadata(self, broker_type: BrokerType) -> Optional[BrokerMetadata]:
        """
        Get broker metadata.
        
        Args:
            broker_type: Broker type enum
            
        Returns:
            BrokerMetadata or None
        """
        return self.metadata.get(broker_type)
    
    def get_enabled_brokers(self) -> List[BrokerType]:
        """
        Get list of enabled brokers.
        
        Returns:
            List of enabled broker types
        """
        return [
            broker_type
            for broker_type, metadata in self.metadata.items()
            if metadata.enabled
        ]
    
    def get_available_brokers(self) -> List[BrokerType]:
        """
        Get list of brokers with registered adapters.
        
        Returns:
            List of available broker types
        """
        return list(self.adapters.keys())
    
    def is_broker_enabled(self, broker_type: BrokerType) -> bool:
        """Check if broker is enabled"""
        metadata = self.metadata.get(broker_type)
        return metadata.enabled if metadata else False
    
    def supports_feature(self, broker_type: BrokerType, feature: str) -> bool:
        """
        Check if broker supports a feature.
        
        Args:
            broker_type: Broker type
            feature: Feature name (e.g., "streaming", "options")
            
        Returns:
            True if supported, False otherwise
        """
        metadata = self.metadata.get(broker_type)
        if not metadata:
            return False
        return metadata.supports.get(feature, False)
    
    def get_broker_info(self) -> List[Dict]:
        """
        Get information about all discovered brokers.
        
        Returns:
            List of broker info dictionaries
        """
        info = []
        for broker_type, metadata in self.metadata.items():
            info.append({
                "broker_type": broker_type.value,
                "display_name": metadata.display_name,
                "version": metadata.version,
                "enabled": metadata.enabled,
                "registered": broker_type in self.adapters,
                "supports": metadata.supports,
                "symbol_format": metadata.symbol_format,
                "exchanges": metadata.exchange_support
            })
        return info


# Global singleton instance
broker_registry = BrokerRegistry()
