"""
Strategy Manager Service
Orchestrates the lifecycle and execution of all active strategies.

Responsibilities:
1. Poll active strategies from the database.
2. Fetch required market data (via BrokerGateway - simplified here).
3. Execute strategy logic (Python DSL or Webhook processing).
4. Generate TradeDecision objects.
5. Send decisions to the ExecutionGate (Rule 2).
"""

import logging
import asyncio
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.database.models_strategy import Strategy, StrategySymbolMapping
from app.database.models_decision import DecisionLedger
from app.services.execution_gate import ExecutionGate

logger = logging.getLogger(__name__)

class StrategyManager:
    """
    Manages active strategies and their execution cycles.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.gate = ExecutionGate(db)
        
    async def get_active_strategies(self) -> List[Strategy]:
        """Fetch all strategies marked as active."""
        try:
            stmt = select(Strategy).where(Strategy.is_active == True)
            result = await self.db.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error fetching active strategies: {e}")
            return []

    async def run_strategy_cycle(self):
        """
        Main polling loop (to be called by scheduler).
        Iterates through active strategies and processes them.
        """
        if not settings.EXECUTION_ENABLED:
            logger.info("Execution disabled via kill-switch. Strategy Manager skipping cycle.")
            return

        strategies = await self.get_active_strategies()
        logger.info(f"Processing {len(strategies)} active strategies...")
        
        for strategy in strategies:
            try:
                await self.process_strategy(strategy)
            except Exception as e:
                logger.error(f"Error processing strategy {strategy.name}: {e}")

    async def process_strategy(self, strategy: Strategy):
        """
        Process a single strategy.
        1. Fetch symbol mappings.
        2. (Simplified) Generate decision based on strategy logic.
        3. Submit to ExecutionGate.
        """
        # 1. Fetch symbols
        stmt = select(StrategySymbolMapping).where(StrategySymbolMapping.strategy_id == strategy.id)
        result = await self.db.execute(stmt)
        mappings = result.scalars().all()
        
        if not mappings:
            logger.warning(f"Strategy {strategy.name} has no symbols mapped.")
            return

        for mapping in mappings:
            # Placeholder: In real implementation, this would call the Python DSL runner or check Webhook cache
            # For now, we simulate a decision generation step
            decision = await self.generate_mock_decision(strategy, mapping)
            
            if decision:
                # 4. Submit to Execution Gate (Rule 2)
                await self.gate.intercept_decision(decision)

    async def generate_mock_decision(self, strategy: Strategy, mapping: StrategySymbolMapping) -> Optional[DecisionLedger]:
        """
        Generate a standardized TradeDecision.
        NOTE: In real system, this comes from the StrategyExecutor.
        """
        # This is just a placeholder to verify the flow. 
        # Real logic involves data fetching + signal generation.
        return None  # No decision by default to prevent spam during dev
