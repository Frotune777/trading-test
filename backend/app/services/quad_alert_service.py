"""
QUAD Alert Service
Monitors QUAD signals and triggers alerts based on thresholds
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update

from app.database.models_quad import (
    QUADAlert, QUADDecision, QUADAlertCreate, QUADAlertResponse,
    AlertType, PillarScores
)
from app.services.monitoring_service import monitoring_service, AlertLevel

logger = logging.getLogger(__name__)


class QUADAlertService:
    """Service for QUAD alert monitoring and notifications"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_alert(
        self,
        alert_data: QUADAlertCreate,
        user_id: Optional[str] = None
    ) -> QUADAlertResponse:
        """
        Create a new QUAD alert
        
        Args:
            alert_data: Alert configuration
            user_id: User ID (optional)
            
        Returns:
            Created alert
        """
        try:
            alert = QUADAlert(
                symbol=alert_data.symbol,
                user_id=user_id,
                alert_type=alert_data.alert_type.value,
                threshold=alert_data.threshold,
                pillar_name=alert_data.pillar_name,
                channels=alert_data.channels,
                active=True
            )
            
            self.db.add(alert)
            await self.db.commit()
            await self.db.refresh(alert)
            
            logger.info(f"Created QUAD alert for {alert_data.symbol}: {alert_data.alert_type.value}")
            
            return QUADAlertResponse(
                id=alert.id,
                symbol=alert.symbol,
                alert_type=alert.alert_type,
                threshold=alert.threshold,
                pillar_name=alert.pillar_name,
                active=alert.active,
                triggered_at=alert.triggered_at,
                message=alert.message,
                channels=alert.channels or [],
                created_at=alert.created_at
            )
            
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
            await self.db.rollback()
            raise
    
    async def check_alerts(
        self,
        symbol: str,
        conviction: int,
        signal: str,
        pillars: PillarScores,
        previous_conviction: Optional[int] = None,
        previous_signal: Optional[str] = None,
        previous_pillars: Optional[PillarScores] = None
    ):
        """
        Check if any alerts should be triggered
        
        Args:
            symbol: Stock symbol
            conviction: Current conviction score
            signal: Current signal
            pillars: Current pillar scores
            previous_conviction: Previous conviction (for comparison)
            previous_signal: Previous signal (for change detection)
            previous_pillars: Previous pillars (for drift detection)
        """
        try:
            # Get active alerts for this symbol
            stmt = select(QUADAlert).where(
                and_(
                    QUADAlert.symbol == symbol,
                    QUADAlert.active == True
                )
            )
            
            result = await self.db.execute(stmt)
            alerts = result.scalars().all()
            
            for alert in alerts:
                triggered = False
                message = ""
                
                # Check conviction thresholds
                if alert.alert_type == AlertType.CONVICTION_ABOVE.value:
                    if conviction >= alert.threshold:
                        triggered = True
                        message = f"{symbol} conviction {conviction} crossed above threshold {alert.threshold}"
                
                elif alert.alert_type == AlertType.CONVICTION_BELOW.value:
                    if conviction <= alert.threshold:
                        triggered = True
                        message = f"{symbol} conviction {conviction} dropped below threshold {alert.threshold}"
                
                # Check pillar drift
                elif alert.alert_type == AlertType.PILLAR_DRIFT.value and previous_pillars:
                    pillar_name = alert.pillar_name
                    if pillar_name:
                        current_score = getattr(pillars, pillar_name, None)
                        previous_score = getattr(previous_pillars, pillar_name, None)
                        
                        if current_score is not None and previous_score is not None:
                            drift = abs(current_score - previous_score)
                            if drift >= alert.threshold:
                                triggered = True
                                message = f"{symbol} {pillar_name} pillar drifted by {drift} points"
                
                # Check signal change
                elif alert.alert_type == AlertType.SIGNAL_CHANGE.value and previous_signal:
                    if signal != previous_signal:
                        triggered = True
                        message = f"{symbol} signal changed from {previous_signal} to {signal}"
                
                # Trigger alert if conditions met
                if triggered:
                    await self._trigger_alert(alert, conviction, message)
            
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
    
    async def _trigger_alert(
        self,
        alert: QUADAlert,
        conviction_value: int,
        message: str
    ):
        """
        Trigger an alert and send notifications
        
        Args:
            alert: Alert configuration
            conviction_value: Current conviction value
            message: Alert message
        """
        try:
            # Update alert record
            alert.triggered_at = datetime.utcnow()
            alert.conviction_value = conviction_value
            alert.message = message
            
            await self.db.commit()
            
            # Send notifications via monitoring service
            if monitoring_service:
                await monitoring_service.send_alert(
                    title=f"QUAD Alert: {alert.symbol}",
                    message=message,
                    level=AlertLevel.WARNING,
                    channels=alert.channels or ['websocket']
                )
            
            logger.info(f"Triggered alert: {message}")
            
        except Exception as e:
            logger.error(f"Error triggering alert: {e}")
    
    async def list_alerts(
        self,
        symbol: Optional[str] = None,
        active_only: bool = True,
        user_id: Optional[str] = None
    ) -> List[QUADAlertResponse]:
        """
        List alerts
        
        Args:
            symbol: Filter by symbol (optional)
            active_only: Only return active alerts
            user_id: Filter by user ID (optional)
            
        Returns:
            List of alerts
        """
        try:
            conditions = []
            
            if symbol:
                conditions.append(QUADAlert.symbol == symbol)
            if active_only:
                conditions.append(QUADAlert.active == True)
            if user_id:
                conditions.append(QUADAlert.user_id == user_id)
            
            stmt = select(QUADAlert)
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            stmt = stmt.order_by(QUADAlert.created_at.desc())
            
            result = await self.db.execute(stmt)
            alerts = result.scalars().all()
            
            return [
                QUADAlertResponse(
                    id=a.id,
                    symbol=a.symbol,
                    alert_type=a.alert_type,
                    threshold=a.threshold,
                    pillar_name=a.pillar_name,
                    active=a.active,
                    triggered_at=a.triggered_at,
                    message=a.message,
                    channels=a.channels or [],
                    created_at=a.created_at
                )
                for a in alerts
            ]
            
        except Exception as e:
            logger.error(f"Error listing alerts: {e}")
            raise
    
    async def delete_alert(self, alert_id: int) -> bool:
        """
        Delete an alert
        
        Args:
            alert_id: Alert ID
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            stmt = select(QUADAlert).where(QUADAlert.id == alert_id)
            result = await self.db.execute(stmt)
            alert = result.scalar_one_or_none()
            
            if not alert:
                return False
            
            await self.db.delete(alert)
            await self.db.commit()
            
            logger.info(f"Deleted alert {alert_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting alert: {e}")
            await self.db.rollback()
            raise
    
    async def acknowledge_alert(self, alert_id: int) -> bool:
        """
        Acknowledge an alert
        
        Args:
            alert_id: Alert ID
            
        Returns:
            True if acknowledged, False otherwise
        """
        try:
            stmt = update(QUADAlert).where(
                QUADAlert.id == alert_id
            ).values(
                acknowledged=True,
                acknowledged_at=datetime.utcnow()
            )
            
            result = await self.db.execute(stmt)
            await self.db.commit()
            
            return result.rowcount > 0
            
        except Exception as e:
            logger.error(f"Error acknowledging alert: {e}")
            await self.db.rollback()
            raise


# Global instance
quad_alert_service: Optional[QUADAlertService] = None
