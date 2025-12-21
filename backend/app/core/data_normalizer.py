"""
Data Normalizer
Normalizes data from different sources to standard schema
"""

from typing import Dict, Any, Optional, Type
import logging
from datetime import datetime
import pandas as pd

from .schema import StandardSchema
from .field_mappers import REVERSE_MAPPERS, YahooFinanceMapper, NSEMapper, ScreenerMapper

logger = logging.getLogger(__name__)


class DataNormalizer:
    """Normalizes data from different sources to standard schema"""
    
    def __init__(self):
        self.mappers = {
            'yahoo': YahooFinanceMapper,
            'nse': NSEMapper,
            'screener': ScreenerMapper,
        }
    
    def normalize_price_data(self, data: Dict[str, Any], source: str) -> Dict[str, Any]:
        """
        Normalize price data from any source to standard schema
        
        Args:
            data: Raw data from source
            source: Source name ('yahoo', 'nse', 'screener')
            
        Returns:
            Normalized data with standard field names
        """
        if source not in self.mappers:
            logger.warning(f"Unknown source: {source}, returning data as-is")
            return data
        
        mapper = self.mappers[source]
        normalized = {}
        
        # Map price fields
        for source_field, standard_field in mapper.PRICE_MAP.items():
            if source_field in data:
                value = data[source_field]
                target_type = StandardSchema.PRICE_FIELDS.get(standard_field)
                normalized[standard_field] = self._convert_type(value, target_type)
        
        # Add symbol if present
        if 'symbol' in data:
            normalized['symbol'] = str(data['symbol'])
        
        return normalized
    
    def normalize_company_data(self, data: Dict[str, Any], source: str) -> Dict[str, Any]:
        """Normalize company info data"""
        if source not in self.mappers:
            return data
        
        mapper = self.mappers[source]
        normalized = {}
        
        for source_field, standard_field in mapper.COMPANY_MAP.items():
            if source_field in data:
                value = data[source_field]
                target_type = StandardSchema.COMPANY_FIELDS.get(standard_field)
                normalized[standard_field] = self._convert_type(value, target_type)
        
        return normalized
    
    def normalize_fundamental_data(self, data: Dict[str, Any], source: str) -> Dict[str, Any]:
        """Normalize fundamental data"""
        if source not in self.mappers:
            return data
        
        mapper = self.mappers[source]
        normalized = {}
        
        for source_field, standard_field in mapper.FUNDAMENTAL_MAP.items():
            if source_field in data:
                value = data[source_field]
                target_type = StandardSchema.FUNDAMENTAL_FIELDS.get(standard_field)
                normalized[standard_field] = self._convert_type(value, target_type)
        
        return normalized
    
    def normalize_complete_data(self, data: Dict[str, Any], source: str) -> Dict[str, Any]:
        """
        Normalize all data types from a source
        Combines price, company, and fundamental data
        """
        normalized = {}
        
        # Merge all normalized data
        normalized.update(self.normalize_price_data(data, source))
        normalized.update(self.normalize_company_data(data, source))
        normalized.update(self.normalize_fundamental_data(data, source))
        
        return normalized
    
    def _convert_type(self, value: Any, target_type: Optional[Type]) -> Any:
        """
        Safe type conversion with validation
        
        Args:
            value: Value to convert
            target_type: Target Python type
            
        Returns:
            Converted value or None if conversion fails
        """
        if value is None or value == '' or (isinstance(value, float) and pd.isna(value)):
            return None
        
        if target_type is None:
            return value
        
        try:
            if target_type == float:
                # Handle percentage strings
                if isinstance(value, str):
                    value = value.replace('%', '').replace(',', '').strip()
                return float(value)
            
            elif target_type == int:
                if isinstance(value, str):
                    value = value.replace(',', '').strip()
                return int(float(value))  # Convert via float to handle decimals
            
            elif target_type == str:
                return str(value).strip()
            
            elif target_type == datetime:
                if isinstance(value, datetime):
                    return value
                return pd.to_datetime(value)
            
            else:
                return value
                
        except (ValueError, TypeError, AttributeError) as e:
            logger.debug(f"Type conversion failed for value '{value}' to {target_type}: {e}")
            return None
    
    def merge_normalized_data(self, *data_dicts: Dict[str, Any], priority_order: Optional[list] = None) -> Dict[str, Any]:
        """
        Merge multiple normalized data dictionaries
        Later sources override earlier ones (or use priority_order)
        
        Args:
            *data_dicts: Variable number of normalized data dictionaries
            priority_order: Optional list of indices indicating priority (higher = more important)
            
        Returns:
            Merged dictionary
        """
        merged = {}
        
        if priority_order:
            # Sort by priority (lowest first so higher priorities override)
            sorted_data = sorted(
                enumerate(data_dicts),
                key=lambda x: priority_order.index(x[0]) if x[0] in priority_order else -1
            )
            for _, data in sorted_data:
                merged.update({k: v for k, v in data.items() if v is not None})
        else:
            # Simple merge, later overrides earlier
            for data in data_dicts:
                merged.update({k: v for k, v in data.items() if v is not None})
        
        return merged
