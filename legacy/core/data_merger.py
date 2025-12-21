"""
Data merging and validation utilities
"""

from typing import Dict, Any, List
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class DataMerger:
    """Intelligent data merging with conflict resolution."""
    
    @staticmethod
    def merge_price_data(sources: List[Dict[str, Any]], 
                        priority: List[str]) -> Dict[str, Any]:
        """Merge price data from multiple sources."""
        merged = {}
        field_sources = {}
        
        for source_name in priority:
            for source in sources:
                if source_name in source and source[source_name]:
                    data = source[source_name]
                    
                    for field, value in data.items():
                        if field not in merged or merged[field] is None:
                            if value is not None:
                                merged[field] = value
                                field_sources[field] = source_name
        
        merged['_field_sources'] = field_sources
        return merged
    
    @staticmethod
    def validate_price_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean price data."""
        issues = []
        
        # Check price is positive
        if 'last_price' in data and data['last_price']:
            if data['last_price'] <= 0:
                issues.append(f"Invalid price: {data['last_price']}")
                data['last_price'] = None
        
        # Check high/low relationship
        if data.get('high') and data.get('low'):
            if data['high'] < data['low']:
                issues.append(f"High < Low")
                data['high'], data['low'] = data['low'], data['high']
        
        if issues:
            data['_validation_issues'] = issues
            logger.warning(f"Validation issues: {issues}")
        
        return data


class DataQualityChecker:
    """Check data quality and completeness."""
    
    @staticmethod
    def assess_quality(data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall data quality."""
        scores = {}
        issues = []
        
        # Completeness
        expected_fields = [
            'symbol', 'company_name', 'last_price', 'sector',
            'industry', 'market_cap', 'pe_ratio', 'volume'
        ]
        
        filled = sum(1 for field in expected_fields if data.get(field))
        scores['completeness'] = (filled / len(expected_fields)) * 100
        
        if scores['completeness'] < 50:
            issues.append("Low data completeness")
        
        # Overall score
        scores['score'] = scores['completeness']
        
        return {
            **scores,
            'issues': issues,
            'grade': DataQualityChecker._get_grade(scores['score'])
        }
    
    @staticmethod
    def _get_grade(score: float) -> str:
        """Convert score to letter grade."""
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'