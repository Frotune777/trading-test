from typing import Dict, List, Optional, Any
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class DataMerger:
    """
    Utility for merging data from multiple sources based on priority.
    """
    
    @staticmethod
    def merge_price_data(sources: List[Dict[str, Any]], priority: List[str] = None) -> Optional[Dict[str, Any]]:
        """
        Merge price data from multiple sources.
        
        Args:
            sources: List of price data dictionaries (order matters if priority not provided)
            priority: List of source names in order of preference
            
        Returns:
            Merged price data dictionary
        """
        if not sources:
            return None
            
        # If no priority logic needed, just take the first valid one
        # In a real implementation, we'd check timestamps, data quality, etc.
        
        # Simple strategy: Return the first non-empty source
        for source in sources:
            if source and isinstance(source, dict) and source.get('last_price'):
                return source
                
        return None

class DataQualityChecker:
    """
    Utility for checking data quality.
    """
    
    @staticmethod
    def check_price_data(data: Dict[str, Any]) -> bool:
        """
        Check if price data looks valid.
        """
        if not data:
            return False
            
        required_fields = ['last_price']
        return all(field in data for field in required_fields)
