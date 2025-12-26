"""
Strategy Service
Business logic for strategy management and webhook automation.
"""

import logging
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, time
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.database.models_strategy import (
    Strategy,
    StrategySymbolMapping,
    StrategyCreate,
    StrategyUpdate,
    SymbolMappingCreate,
    TradingMode,
    Platform
)

logger = logging.getLogger(__name__)


class StrategyService:
    """
    Strategy Management Service
    
    Handles CRUD operations for strategies and symbol mappings.
    Validates trading hours, modes, and webhook configurations.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_strategy(
        self,
        user_id: str,
        data: StrategyCreate
    ) -> Strategy:
        """
        Create a new strategy.
        
        Args:
            user_id: User ID from session
            data: Strategy creation data
            
        Returns:
            Created strategy
            
        Raises:
            ValueError: If validation fails
        """
        # Validate strategy name
        if not self._validate_strategy_name(data.name):
            raise ValueError("Invalid strategy name. Use only letters, numbers, spaces, hyphens, and underscores (3-50 chars)")
        
        # Check if name already exists
        existing = self.db.query(Strategy).filter(Strategy.name == data.name).first()
        if existing:
            raise ValueError(f"Strategy with name '{data.name}' already exists")
        
        # Validate times for intraday
        if data.is_intraday:
            if not all([data.start_time, data.end_time, data.squareoff_time]):
                raise ValueError("Intraday strategies require start_time, end_time, and squareoff_time")
            
            if not self._validate_strategy_times(data.start_time, data.end_time, data.squareoff_time):
                raise ValueError("Invalid time configuration. Check market hours and time sequence")
        
        # Generate webhook ID
        webhook_id = str(uuid.uuid4())
        
        # Parse times
        start_time = self._parse_time(data.start_time) if data.start_time else None
        end_time = self._parse_time(data.end_time) if data.end_time else None
        squareoff_time = self._parse_time(data.squareoff_time) if data.squareoff_time else None
        
        # Create strategy
        strategy = Strategy(
            name=data.name,
            webhook_id=webhook_id,
            user_id=user_id,
            platform=data.platform,
            is_intraday=data.is_intraday,
            trading_mode=data.trading_mode,
            start_time=start_time,
            end_time=end_time,
            squareoff_time=squareoff_time,
            description=data.description
        )
        
        self.db.add(strategy)
        self.db.commit()
        self.db.refresh(strategy)
        
        logger.info(f"Created strategy: {strategy.name} (ID: {strategy.id}, webhook: {webhook_id})")
        
        return strategy
    
    async def get_strategy(self, strategy_id: int, user_id: str) -> Optional[Strategy]:
        """Get strategy by ID (with user ownership check)"""
        return self.db.query(Strategy).filter(
            and_(Strategy.id == strategy_id, Strategy.user_id == user_id)
        ).first()
    
    async def get_strategy_by_webhook(self, webhook_id: str) -> Optional[Strategy]:
        """Get strategy by webhook ID (no user check - for webhook endpoint)"""
        return self.db.query(Strategy).filter(Strategy.webhook_id == webhook_id).first()
    
    async def get_user_strategies(self, user_id: str) -> List[Strategy]:
        """Get all strategies for a user"""
        return self.db.query(Strategy).filter(Strategy.user_id == user_id).order_by(Strategy.created_at.desc()).all()
    
    async def update_strategy(
        self,
        strategy_id: int,
        user_id: str,
        data: StrategyUpdate
    ) -> Optional[Strategy]:
        """
        Update strategy.
        
        Args:
            strategy_id: Strategy ID
            user_id: User ID (for ownership check)
            data: Update data
            
        Returns:
            Updated strategy or None if not found
        """
        strategy = await self.get_strategy(strategy_id, user_id)
        if not strategy:
            return None
        
        # Update fields
        if data.name is not None:
            if not self._validate_strategy_name(data.name):
                raise ValueError("Invalid strategy name")
            strategy.name = data.name
        
        if data.is_active is not None:
            strategy.is_active = data.is_active
        
        if data.is_intraday is not None:
            strategy.is_intraday = data.is_intraday
        
        if data.trading_mode is not None:
            strategy.trading_mode = data.trading_mode
        
        if data.start_time is not None:
            strategy.start_time = self._parse_time(data.start_time)
        
        if data.end_time is not None:
            strategy.end_time = self._parse_time(data.end_time)
        
        if data.squareoff_time is not None:
            strategy.squareoff_time = self._parse_time(data.squareoff_time)
        
        if data.description is not None:
            strategy.description = data.description
        
        # Validate times if intraday
        if strategy.is_intraday:
            if not all([strategy.start_time, strategy.end_time, strategy.squareoff_time]):
                raise ValueError("Intraday strategies require all time fields")
        
        self.db.commit()
        self.db.refresh(strategy)
        
        logger.info(f"Updated strategy: {strategy.name} (ID: {strategy.id})")
        
        return strategy
    
    async def toggle_strategy(self, strategy_id: int, user_id: str) -> Optional[Strategy]:
        """Toggle strategy active status"""
        strategy = await self.get_strategy(strategy_id, user_id)
        if not strategy:
            return None
        
        strategy.is_active = not strategy.is_active
        self.db.commit()
        self.db.refresh(strategy)
        
        logger.info(f"Toggled strategy {strategy.name}: active={strategy.is_active}")
        
        return strategy
    
    async def delete_strategy(self, strategy_id: int, user_id: str) -> bool:
        """Delete strategy (cascade deletes symbol mappings)"""
        strategy = await self.get_strategy(strategy_id, user_id)
        if not strategy:
            return False
        
        self.db.delete(strategy)
        self.db.commit()
        
        logger.info(f"Deleted strategy: {strategy.name} (ID: {strategy_id})")
        
        return True
    
    # Symbol Mapping Methods
    
    async def add_symbol_mapping(
        self,
        strategy_id: int,
        user_id: str,
        data: SymbolMappingCreate
    ) -> Optional[StrategySymbolMapping]:
        """Add symbol mapping to strategy"""
        strategy = await self.get_strategy(strategy_id, user_id)
        if not strategy:
            return None
        
        # Validate exchange
        if data.exchange not in ['NSE', 'BSE', 'NFO', 'CDS', 'BFO', 'BCD', 'MCX', 'NCDEX']:
            raise ValueError(f"Invalid exchange: {data.exchange}")
        
        # Validate quantity
        if data.quantity <= 0:
            raise ValueError("Quantity must be greater than 0")
        
        # Create mapping
        mapping = StrategySymbolMapping(
            strategy_id=strategy_id,
            symbol=data.symbol,
            exchange=data.exchange,
            quantity=data.quantity,
            product_type=data.product_type,
            broker=data.broker
        )
        
        self.db.add(mapping)
        self.db.commit()
        self.db.refresh(mapping)
        
        logger.info(f"Added symbol {data.symbol} to strategy {strategy.name}")
        
        return mapping
    
    async def get_symbol_mappings(self, strategy_id: int) -> List[StrategySymbolMapping]:
        """Get all symbol mappings for a strategy"""
        return self.db.query(StrategySymbolMapping).filter(
            StrategySymbolMapping.strategy_id == strategy_id
        ).all()
    
    async def delete_symbol_mapping(
        self,
        mapping_id: int,
        user_id: str
    ) -> bool:
        """Delete symbol mapping (with ownership check)"""
        mapping = self.db.query(StrategySymbolMapping).filter(
            StrategySymbolMapping.id == mapping_id
        ).first()
        
        if not mapping:
            return False
        
        # Check ownership via strategy
        strategy = await self.get_strategy(mapping.strategy_id, user_id)
        if not strategy:
            return False
        
        self.db.delete(mapping)
        self.db.commit()
        
        logger.info(f"Deleted symbol mapping {mapping.symbol} from strategy {strategy.name}")
        
        return True
    
    # Validation Methods
    
    def _validate_strategy_name(self, name: str) -> bool:
        """Validate strategy name format"""
        if not name or len(name) < 3 or len(name) > 50:
            return False
        
        # Allow letters, numbers, spaces, hyphens, underscores
        import re
        return bool(re.match(r'^[A-Za-z0-9\s\-_]+$', name))
    
    def _validate_strategy_times(
        self,
        start_time: str,
        end_time: str,
        squareoff_time: str
    ) -> bool:
        """Validate strategy time configuration"""
        try:
            start = datetime.strptime(start_time, '%H:%M').time()
            end = datetime.strptime(end_time, '%H:%M').time()
            squareoff = datetime.strptime(squareoff_time, '%H:%M').time()
            
            # Market hours (9:15 AM to 3:30 PM IST)
            market_open = time(9, 15)
            market_close = time(15, 30)
            
            # Validate times
            if start < market_open:
                return False
            if end > market_close:
                return False
            if squareoff > market_close:
                return False
            if start >= end:
                return False
            if squareoff < end:
                return False
            
            return True
            
        except ValueError:
            return False
    
    def _parse_time(self, time_str: str) -> time:
        """Parse time string to time object"""
        return datetime.strptime(time_str, '%H:%M').time()


# Helper functions for API

def get_webhook_url(webhook_id: str, base_url: str = "http://localhost:8000") -> str:
    """Generate webhook URL for strategy"""
    return f"{base_url}/api/v1/webhook/{webhook_id}"
