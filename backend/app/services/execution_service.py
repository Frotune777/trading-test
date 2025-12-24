# app/services/execution_service.py

import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime
import httpx
from app.core.config import settings
from app.database.db_manager import DatabaseManager
from app.services.reasoning_service import ReasoningService
from app.services.alert_service import AlertService
from app.core.risk_engine import RiskEngine

logger = logging.getLogger(__name__)

class ExecutionService:
    """
    Service responsible for routing orders to execution venues
    while enforcing safety gates and audit trials.
    """
    def __init__(self, db_path: str = "stock_data.db"):
        self.db = DatabaseManager(db_path)
        self.reasoning = ReasoningService()
        self.alerts = AlertService(db_path)
        self.risk = RiskEngine(db_path)

    async def execute_order(self, symbol: str, order_payload: Dict[str, Any], snapshot: Any, decision: Optional[Any] = None) -> Dict[str, Any]:
        """
        Main entry point for order execution.
        
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

        # 0.1 Account-Level Risk check
        is_safe, block_reason = await self.risk.check_risk(
            symbol, 
            order_payload.get("quantity", 0), 
            snapshot.ltp
        )
        if not is_safe:
            execution_record = {
                "symbol": symbol,
                "order_type": order_payload.get("action"),
                "quantity": order_payload.get("quantity"),
                "price": snapshot.ltp,
                "execution_mode": settings.EXECUTION_MODE,
                "execution_status": "BLOCKED",
                "execution_block_reason": block_reason,
                "decision_id": decision.decision_id if decision else None,
            }
            self.db.save_execution(execution_record)
            
            await self.alerts.emit(
                alert_type="ACCOUNT_RISK_BLOCKED",
                message=f"Trade blocked by Risk Engine for {symbol}: {block_reason}",
                level="CRITICAL",
                symbol=symbol
            )
            return {"status": "BLOCKED", "block_reason": block_reason, "source": "RISK_ENGINE"}

        # 1. Final Safety Gate Check
        gate_decision = await self.reasoning.can_execute_trade(symbol, snapshot)
        
        # Re-fetch exact Redis LTP for drift check
        current_ltp = snapshot.ltp
        try:
            cached = await redis_client.get(f"market:ltp:NSE:{symbol}")
            if cached:
                current_ltp = json.loads(cached).get("ltp", snapshot.ltp)
        except: pass

        execution_record = {
            "symbol": symbol,
            "order_type": order_payload.get("action"), # BUY/SELL
            "quantity": order_payload.get("quantity"),
            "price": current_ltp,
            "execution_mode": gate_decision["execution_mode"],
            "feed_state": gate_decision["feed_state"],
            "ltp_source": gate_decision["ltp_source"],
            "ltp_age_ms": gate_decision["ltp_age_ms"],
            "raw_payload": order_payload,
            "decision_id": decision.decision_id if decision else None,
        }

        # DRIFT & EXPIRY CHECKS (only if we have a decision)
        if decision:
            # 1. Expiry Check
            if datetime.now() > decision.valid_till:
                execution_record["execution_status"] = "BLOCKED"
                execution_record["execution_block_reason"] = "DECISION_EXPIRED"
                self.db.save_execution(execution_record)
                
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
            execution_record["drift_bps"] = drift_bps
            
            # Use 5bps for indices, 10bps for stocks (simple heuristic)
            threshold = 5.0 if "INDEX" in symbol else 10.0
            if drift_bps > threshold:
                execution_record["execution_status"] = "BLOCKED"
                execution_record["execution_block_reason"] = "EXCESSIVE_DRIFT"
                self.db.save_execution(execution_record)
                
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
            execution_record["execution_status"] = "BLOCKED"
            execution_record["execution_block_reason"] = gate_decision["block_reason"]
            self.db.save_execution(execution_record)
            
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

        # 2. Branch: DRY_RUN vs LIVE
        if decision and gate_decision["execution_mode"] == "LIVE":
            # LIVE GUARDRAILS
            from app.core.guardrails import LiveGuardrails
            is_allowed, reason = await LiveGuardrails.validate_execution(symbol, order_payload, decision, self.db)
            if not is_allowed:
                execution_record["execution_status"] = "BLOCKED"
                execution_record["execution_block_reason"] = reason
                self.db.save_execution(execution_record)
                
                await self.alerts.emit(
                    alert_type="LIVE_GUARDRAIL_VIOLATION",
                    message=f"LIVE Trade blocked for {symbol}: {reason}",
                    level="CRITICAL",
                    symbol=symbol
                )
                
                logger.warning(f"LIVE_GUARDRAIL_BLOCKED: {symbol} Reason: {reason}")
                return {"status": "BLOCKED", "block_reason": reason, "decision": gate_decision}

        if gate_decision["execution_mode"] == "DRY_RUN":
             # SIMULATED EXECUTION
            execution_record["execution_status"] = "DRY_RUN"
            execution_record["execution_block_reason"] = "DRY_RUN_MODE"
            execution_record["order_id"] = f"DRY_{int(datetime.now().timestamp())}"
            self.db.save_execution(execution_record)
            
            await self.alerts.emit(
                alert_type="DRY_RUN_SUCCESS",
                message=f"Simulated {order_payload.get('action')} executed for {symbol} at {snapshot.ltp}",
                level="INFO",
                symbol=symbol
            )
            
            return {
                "status": "DRY_RUN_EXECUTION",
                "order_id": execution_record["order_id"],
                "price": snapshot.ltp,
                "decision": gate_decision
            }
        
        elif gate_decision["execution_mode"] == "LIVE":
            # LIVE EXECUTION
            try:
                # Place order via OpenAlgo API
                order_id = await self._place_openalgo_order(symbol, order_payload)
                
                execution_record["execution_status"] = "LIVE"
                execution_record["order_id"] = order_id
                self.db.save_execution(execution_record)
                
                await self.alerts.emit(
                    alert_type="LIVE_EXECUTION_SUCCESS",
                    message=f"LIVE {order_payload.get('action')} executed for {symbol} at {snapshot.ltp} (Order: {order_id})",
                    level="INFO",
                    symbol=symbol,
                    metadata={"order_id": order_id}
                )
                
                logger.info(f"LIVE_EXECUTION_SUCCESS: {symbol} OrderID: {order_id}")
                
                return {
                    "status": "LIVE_SUCCESS",
                    "order_id": order_id,
                    "price": snapshot.ltp,
                    "decision": gate_decision
                }
            except Exception as e:
                logger.error(f"LIVE_EXECUTION_FAILED: {symbol} Error: {e}")
                execution_record["execution_status"] = "FAILED"
                execution_record["execution_block_reason"] = f"LIVE_ERROR: {str(e)}"
                self.db.save_execution(execution_record)
                
                return {
                    "status": "FAILED",
                    "error": str(e),
                    "decision": decision
                }
        
        return {"status": "UNKNOWN_MODE", "decision": decision}

    async def _place_openalgo_order(self, symbol: str, payload: Dict[str, Any]) -> str:
        """Internal helper to call OpenAlgo REST API."""
        url = f"{settings.OPENALGO_API_URL}/order"
        headers = {"api-key": settings.OPENALGO_API_KEY}
        
        # Standardize payload for OpenAlgo (assumed based on common patterns)
        # symbol, action, quantity, order_type, product, price, etc.
        data = {
            "symbol": symbol,
            "action": payload.get("action", "BUY"),
            "quantity": payload.get("quantity", 1),
            "order_type": payload.get("order_type", "MARKET"),
            "product": payload.get("product", "MIS"),
            "smart_order": True
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=data, headers=headers, timeout=5.0)
                response.raise_for_status()
                res_data = response.json()
                
                if res_data.get("status") == "error":
                    raise Exception(res_data.get("message", "OpenAlgo refused order"))
                    
                return res_data.get("order_id", f"ORD_{int(datetime.now().timestamp())}")
            except httpx.HTTPError as e:
                 logger.error(f"OpenAlgo API Connection Error: {e}")
                 raise Exception(f"API_CONNECTION_ERROR: {str(e)}")
