# app/services/execution_service.py

import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.database.db_manager import DatabaseManager
from app.services.reasoning_service import ReasoningService
from app.services.alert_service import AlertService
from app.services.risk_manager import RiskManager
from app.core.openalgo_bridge import openalgo_bridge

logger = logging.getLogger(__name__)

class ExecutionService:
    """
    Service responsible for routing orders to execution venues (OpenAlgo)
    while enforcing safety gates and audit trials.
    """
    def __init__(self, db_path: str = "stock_data.db"):
        self.db = DatabaseManager(db_path)
        self.reasoning = ReasoningService()
        self.alerts = AlertService(db_path)
        self.risk_manager = RiskManager()

    async def execute_order(
        self, 
        symbol: str, 
        order_payload: Dict[str, Any], 
        snapshot: Any, 
        db: AsyncSession,
        user_id: int,
        decision: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for order execution.
        Unifies DRY_RUN and LIVE logic by delegating to OpenAlgo Smart Orders.
        
        Args:
            symbol: Target symbol
            order_payload: Dict containing action, quantity, type, etc.
            snapshot: LiveDecisionSnapshot used for the decision
            decision: TradeDecision object (required for LIVE)
        """
        from app.core.redis import redis_client
        
        # 0. Provenance Check
        if settings.EXECUTION_MODE == "LIVE" and not decision:
             return {"status": "FAILED", "error": "MISSING_TRADE_DECISION", "decision": None}

        # 0.1 Account-Level Risk check (Using new RiskManager)
        from app.brokers.base_adapter import Order
        mock_order = Order(
            symbol=symbol,
            exchange=order_payload.get("exchange", "NSE"),
            quantity=order_payload.get("quantity", 0),
            transaction_type=order_payload.get("action", "BUY"),
            order_type=order_payload.get("order_type", "MARKET")
        )
        
        risk_result = await self.risk_manager.validate_order(
            order=mock_order,
            db=db,
            user_id=user_id
        )
        
        if not risk_result["allowed"]:
            block_reason = ", ".join(risk_result["blocked_reasons"])
            self._log_execution(symbol, order_payload, snapshot.ltp, "BLOCKED", block_reason, decision)
            
            await self.alerts.emit(
                alert_type="ACCOUNT_RISK_BLOCKED",
                message=f"Trade blocked by Risk Governor for {symbol}: {block_reason}",
                level="CRITICAL",
                symbol=symbol
            )
            return {"status": "BLOCKED", "block_reason": block_reason, "source": "RISK_GOVERNOR"}

        # 1. Final Safety Gate Check
        gate_decision = await self.reasoning.can_execute_trade(symbol, snapshot)
        
        # Re-fetch exact Redis LTP for drift check
        current_ltp = snapshot.ltp
        try:
            cached = await redis_client.get(f"market:ltp:NSE:{symbol}")
            if cached:
                current_ltp = float(json.loads(cached).get("ltp", snapshot.ltp))
        except: pass

        # DRIFT & EXPIRY CHECKS (only if we have a decision)
        if decision:
            # 1. Expiry Check
            if datetime.now() > decision.valid_till:
                self._log_execution(symbol, order_payload, current_ltp, "BLOCKED", "DECISION_EXPIRED", decision)
                await self.alerts.emit(
                    alert_type="DECISION_EXPIRED",
                    message=f"Trade aborted: Decision {decision.decision_id[:8]} expired for {symbol}",
                    level="WARNING",
                    symbol=symbol,
                    metadata={"decision_id": decision.decision_id}
                )
                return {"status": "BLOCKED", "block_reason": "DECISION_EXPIRED", "decision": gate_decision}

            # 2. Price Drift Check (Default: 10 bps for stocks)
            drift_bps = abs(current_ltp - decision.decision_ltp) / decision.decision_ltp * 10000
            
            # Use 5bps for indices, 10bps for stocks (simple heuristic)
            threshold = 5.0 if "INDEX" in symbol else 10.0
            if drift_bps > threshold:
                self._log_execution(symbol, order_payload, current_ltp, "BLOCKED", "EXCESSIVE_DRIFT", decision, drift_bps=drift_bps)
                await self.alerts.emit(
                    alert_type="EXCESSIVE_DRIFT",
                    message=f"Trade aborted: Drift {drift_bps:.1f} bps > {threshold} bps for {symbol}",
                    level="CRITICAL",
                    symbol=symbol,
                    metadata={"drift_bps": drift_bps, "threshold": threshold, "decision_price": decision.decision_ltp, "execution_price": current_ltp}
                )
                return {"status": "BLOCKED", "block_reason": "EXCESSIVE_DRIFT", "drift_bps": drift_bps, "decision": gate_decision}

        if not gate_decision["is_execution_ready"]:
            # EXECUTION BLOCKED
            self._log_execution(symbol, order_payload, current_ltp, "BLOCKED", gate_decision["block_reason"], decision)
            await self.alerts.emit(
                alert_type="EXECUTION_GATE_BLOCKED",
                message=f"Trade blocked for {symbol}: {gate_decision['block_reason']}",
                level="WARNING",
                symbol=symbol
            )
            logger.warning(f"EXECUTION_BLOCKED: {symbol} Reason: {gate_decision['block_reason']}")
            return {
                "status": "BLOCKED",
                "block_reason": gate_decision["block_reason"],
                "decision": gate_decision
            }

        # 2. EXECUTION HANDOFF
        # Use simple try/catch for the API interaction
        try:
            action = order_payload.get("action", "BUY").upper()
            quantity = int(order_payload.get("quantity", 1))
            product = order_payload.get("product", "MIS")
            exchange = order_payload.get("exchange", "NSE")
            strategy = "QUAD_STRAT"

            # 2.1 Calculate Target Position for Smart Netting
            current_qty = await openalgo_bridge.get_open_position(symbol, exchange, product, strategy)
            
            target_position_size = 0
            if action == "BUY":
                target_position_size = current_qty + quantity
            elif action == "SELL":
                target_position_size = current_qty - quantity
            
            # 2.2 Construct Smart Order Payload
            smart_payload = {
                "symbol": symbol,
                "exchange": exchange,
                "action": action,
                "quantity": quantity, # Transaction quantity
                "position_size": target_position_size, # Net target
                "product": product,
                "order_type": order_payload.get("order_type", "MARKET"),
                "price": order_payload.get("price", 0),
                "strategy": strategy,
                "apikey": settings.OPENALGO_API_KEY
            }

            # 2.3 Call OpenAlgo Bridge
            # Note: This handles both LIVE (Broker) and ANALYZE (Sandbox) modes transparently.
            logger.info(f"Placing Smart Order for {symbol}: {action} {quantity} (Target: {target_position_size})")
            response = await openalgo_bridge.place_smart_order(smart_payload)
            
            if response.get("status") == "success":
                order_id = response.get("orderid", f"OA_{int(datetime.now().timestamp())}")
                
                # Determine final status for our DB
                # If OpenAlgo is in Analyze Mode, it's a Simulated Exec.
                # If OpenAlgo is Live, it's Live.
                # ExecutionService relies on ReasoningService's detected mode for labelling.
                oa_mode = gate_decision.get("openalgo_mode", "UNKNOWN")
                final_status = "LIVE" if oa_mode == "LIVE" else "DRY_RUN"
                
                self._log_execution(symbol, order_payload, current_ltp, final_status, None, decision, order_id=order_id)
                
                await self.alerts.emit(
                    alert_type=f"{final_status}_EXECUTION_SUCCESS",
                    message=f"{final_status} {action} executed for {symbol} (Target: {target_position_size})",
                    level="INFO",
                    symbol=symbol,
                    metadata={"order_id": order_id, "mode": final_status}
                )
                
                return {
                    "status": "SUCCESS",
                    "mode": final_status,
                    "order_id": order_id,
                    "price": current_ltp,
                    "decision": gate_decision
                }
            else:
                # API Failure
                error_msg = response.get("message", "Unknown OpenAlgo Error")
                self._log_execution(symbol, order_payload, current_ltp, "FAILED", f"API_ERROR: {error_msg}", decision)
                logger.error(f"OpenAlgo Order Failed: {error_msg}")
                return {"status": "FAILED", "error": error_msg, "decision": gate_decision}
                
        except Exception as e:
            logger.error(f"Execution Exception: {e}", exc_info=True)
            self._log_execution(symbol, order_payload, current_ltp, "FAILED", f"EXCEPTION: {str(e)}", decision)
            return {"status": "FAILED", "error": str(e), "decision": decision}

    def _log_execution(self, symbol, payload, price, status, reason, decision, drift_bps=0.0, order_id=None):
        """Helper to save execution record to DB."""
        try:
            record = {
                "symbol": symbol,
                "order_type": payload.get("action"),
                "quantity": payload.get("quantity"),
                "price": price,
                "execution_mode": settings.EXECUTION_MODE, # Logging logic reflects App settings
                "execution_status": status,
                "execution_block_reason": reason,
                "decision_id": decision.decision_id if decision else None,
                "drift_bps": drift_bps,
                "order_id": order_id
            }
            self.db.save_execution(record)
        except Exception as e:
            logger.error(f"Failed to save execution log: {e}")
