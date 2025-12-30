"""
Risk Management Service
Calculates risk metrics, enforces limits, manages kill switch
"""
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
import json
from app.core.redis import redis_client

from app.database.models_risk import RiskLimit, RiskMetric, KillSwitchLog, AlertLog
from app.database.models_position import Position


class RiskService:
    def __init__(self, db: Session):
        self.db = db
    
    async def get_or_create_limits(self, user_id: str) -> RiskLimit:
        """Get user's risk limits or create defaults"""
        limits = self.db.query(RiskLimit).filter(
            RiskLimit.user_id == user_id
        ).first()
        
        if not limits:
            limits = RiskLimit(user_id=user_id)
            self.db.add(limits)
            self.db.commit()
            self.db.refresh(limits)
        
        return limits
    
    async def update_limits(
        self, 
        user_id: str, 
        limits_data: Dict
    ) -> RiskLimit:
        """Update risk limits"""
        limits = await self.get_or_create_limits(user_id)
        
        for key, value in limits_data.items():
            if hasattr(limits, key):
                setattr(limits, key, value)
        
        self.db.commit()
        self.db.refresh(limits)
        return limits
    
    async def calculate_current_metrics(self, user_id: str) -> Dict:
        """Calculate current risk metrics"""
        # Get all active positions
        positions = self.db.query(Position).filter(
            and_(
                Position.user_id == user_id,
                Position.status == 'OPEN'
            )
        ).all()
        
        # Calculate P&L
        total_pnl = sum(float(p.unrealized_pnl or 0) + float(p.realized_pnl or 0) for p in positions)
        unrealized_pnl = sum(float(p.unrealized_pnl or 0) for p in positions)
        realized_pnl = sum(float(p.realized_pnl or 0) for p in positions)
        
        # Calculate daily P&L
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        daily_positions = [p for p in positions if p.entry_time >= today_start]
        daily_pnl = sum(float(p.unrealized_pnl or 0) + float(p.realized_pnl or 0) for p in daily_positions)
        
        # Calculate weekly P&L
        week_start = datetime.now() - timedelta(days=7)
        weekly_positions = [p for p in positions if p.entry_time >= week_start]
        weekly_pnl = sum(float(p.unrealized_pnl or 0) + float(p.realized_pnl or 0) for p in weekly_positions)
        
        # Calculate exposure and portfolio value
        total_exposure = sum(float(p.quantity) * float(p.current_price or p.entry_price) for p in positions)
        portfolio_value = sum(float(p.quantity) * float(p.current_price or p.entry_price) for p in positions)
        
        # Calculate concentration
        concentration_by_symbol = {}
        if portfolio_value > 0:
            for p in positions:
                position_value = float(p.quantity) * float(p.current_price or p.entry_price)
                concentration_by_symbol[p.symbol] = (position_value / portfolio_value) * 100
        
        return {
            'total_pnl': total_pnl,
            'daily_pnl': daily_pnl,
            'weekly_pnl': weekly_pnl,
            'unrealized_pnl': unrealized_pnl,
            'realized_pnl': realized_pnl,
            'position_count': len(positions),
            'total_exposure': total_exposure,
            'portfolio_value': portfolio_value,
            'concentration_by_symbol': concentration_by_symbol,
        }
    
    async def get_dashboard(self, user_id: str) -> Dict:
        """Get complete risk dashboard data"""
        limits = await self.get_or_create_limits(user_id)
        metrics = await self.calculate_current_metrics(user_id)
        
        # Calculate limit utilization
        position_limit_utilization = (metrics['position_count'] / limits.max_positions) * 100 if limits.max_positions > 0 else 0
        
        daily_loss_limit_utilization = 0
        if limits.max_daily_loss > 0 and metrics['daily_pnl'] < 0:
            daily_loss_limit_utilization = (abs(metrics['daily_pnl']) / float(limits.max_daily_loss)) * 100
        
        weekly_loss_limit_utilization = 0
        if limits.max_weekly_loss > 0 and metrics['weekly_pnl'] < 0:
            weekly_loss_limit_utilization = (abs(metrics['weekly_pnl']) / float(limits.max_weekly_loss)) * 100
        
        return {
            **metrics,
            'limits': {
                'max_positions': limits.max_positions,
                'max_daily_loss': float(limits.max_daily_loss),
                'max_weekly_loss': float(limits.max_weekly_loss),
                'max_single_stock_pct': limits.max_single_stock_pct,
            },
            'utilization': {
                'position_limit': position_limit_utilization,
                'daily_loss_limit': daily_loss_limit_utilization,
                'weekly_loss_limit': weekly_loss_limit_utilization,
            },
            'kill_switch': {
                'enabled': limits.kill_switch_enabled,
                'reason': limits.kill_switch_reason,
                'activated_at': limits.kill_switch_activated_at.isoformat() if limits.kill_switch_activated_at else None,
            },
            'alerts': await self._get_active_alerts(user_id),
        }
    
    async def activate_kill_switch(
        self, 
        user_id: str, 
        reason: str, 
        activated_by: str
    ) -> Dict:
        """Activate kill switch"""
        limits = await self.get_or_create_limits(user_id)
        metrics = await self.calculate_current_metrics(user_id)
        
        # Update limits
        limits.kill_switch_enabled = True
        limits.kill_switch_reason = reason
        limits.kill_switch_activated_at = datetime.now()
        limits.kill_switch_activated_by = activated_by
        
        # Log activation
        log = KillSwitchLog(
            user_id=user_id,
            activated_by=activated_by,
            reason=reason,
            active_positions=metrics['position_count'],
            total_pnl=Decimal(str(metrics['total_pnl'])),
            portfolio_value=Decimal(str(metrics['portfolio_value'])),
        )
        
        self.db.add(log)
        self.db.commit()
        
        # Create critical alert
        await self.create_alert(
            user_id=user_id,
            alert_type='CRITICAL',
            category='RISK',
            title='Kill Switch Activated',
            message=f'All trading disabled. Reason: {reason}',
        )
        
        return {
            'success': True,
            'activated_at': limits.kill_switch_activated_at.isoformat(),
            'reason': reason,
        }
    
    async def deactivate_kill_switch(
        self, 
        user_id: str, 
        reason: str, 
        deactivated_by: str
    ) -> Dict:
        """Deactivate kill switch"""
        limits = await self.get_or_create_limits(user_id)
        
        # Find active log
        log = self.db.query(KillSwitchLog).filter(
            and_(
                KillSwitchLog.user_id == user_id,
                KillSwitchLog.deactivated_at.is_(None)
            )
        ).order_by(KillSwitchLog.activated_at.desc()).first()
        
        if log:
            log.deactivated_at = datetime.now()
            log.deactivated_by = deactivated_by
            log.deactivation_reason = reason
        
        # Update limits
        limits.kill_switch_enabled = False
        limits.kill_switch_reason = None
        
        self.db.commit()
        
        # Create info alert
        await self.create_alert(
            user_id=user_id,
            alert_type='INFO',
            category='RISK',
            title='Kill Switch Deactivated',
            message=f'Trading re-enabled. Reason: {reason}',
        )
        
        return {
            'success': True,
            'deactivated_at': datetime.now().isoformat(),
        }
    
    async def create_alert(
        self,
        user_id: str,
        alert_type: str,
        category: str,
        title: str,
        message: str,
        related_symbol: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> AlertLog:
        """Create a new alert"""
        alert = AlertLog(
            user_id=user_id,
            alert_type=alert_type,
            category=category,
            title=title,
            message=message,
            related_symbol=related_symbol,
            metadata=metadata or {},
        )
        
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        
        # Broadcast via Redis
        if redis_client:
            try:
                alert_data = {
                    'id': alert.id,
                    'type': alert.alert_type,
                    'category': alert.category,
                    'title': alert.title,
                    'message': alert.message,
                    'timestamp': alert.timestamp.isoformat(),
                    'symbol': alert.related_symbol,
                }
                await redis_client.publish(f"alerts:{user_id}", json.dumps(alert_data))
            except Exception as e:
                # Log error but don't fail the request
                print(f"Failed to publish alert to Redis: {e}")

        return alert
    
    async def _get_active_alerts(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get recent unacknowledged alerts"""
        alerts = self.db.query(AlertLog).filter(
            and_(
                AlertLog.user_id == user_id,
                AlertLog.acknowledged == False
            )
        ).order_by(AlertLog.timestamp.desc()).limit(limit).all()
        
        return [
            {
                'id': a.id,
                'type': a.alert_type,
                'category': a.category,
                'title': a.title,
                'message': a.message,
                'timestamp': a.timestamp.isoformat(),
                'symbol': a.related_symbol,
            }
            for a in alerts
        ]
    
    async def acknowledge_alert(self, alert_id: int, user_id: str) -> bool:
        """Mark alert as acknowledged"""
        alert = self.db.query(AlertLog).filter(
            and_(
                AlertLog.id == alert_id,
                AlertLog.user_id == user_id
            )
        ).first()
        
        if alert:
            alert.acknowledged = True
            alert.acknowledged_at = datetime.now()
            alert.acknowledged_by = user_id
            self.db.commit()
            return True
        
        return False
    
    async def check_limits(self, user_id: str) -> List[Dict]:
        """Check if any limits are breached"""
        limits = await self.get_or_create_limits(user_id)
        metrics = await self.calculate_current_metrics(user_id)
        breaches = []
        
        # Check position limit
        if metrics['position_count'] >= limits.max_positions:
            breaches.append({
                'type': 'POSITION_LIMIT',
                'severity': 'CRITICAL' if metrics['position_count'] > limits.max_positions else 'WARNING',
                'message': f"Position limit reached: {metrics['position_count']}/{limits.max_positions}",
            })
        
        # Check daily loss limit
        if metrics['daily_pnl'] < 0 and abs(metrics['daily_pnl']) >= float(limits.max_daily_loss):
            breaches.append({
                'type': 'DAILY_LOSS_LIMIT',
                'severity': 'CRITICAL',
                'message': f"Daily loss limit breached: {metrics['daily_pnl']:.2f}",
            })
        
        # Check weekly loss limit
        if metrics['weekly_pnl'] < 0 and abs(metrics['weekly_pnl']) >= float(limits.max_weekly_loss):
            breaches.append({
                'type': 'WEEKLY_LOSS_LIMIT',
                'severity': 'CRITICAL',
                'message': f"Weekly loss limit breached: {metrics['weekly_pnl']:.2f}",
            })
        
        # Check concentration
        for symbol, pct in metrics['concentration_by_symbol'].items():
            if pct > limits.max_single_stock_pct:
                breaches.append({
                    'type': 'CONCENTRATION_LIMIT',
                    'severity': 'WARNING',
                    'message': f"{symbol} concentration too high: {pct:.1f}%",
                    'symbol': symbol,
                })
        
        return breaches