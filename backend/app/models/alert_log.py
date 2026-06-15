"""
OptiFlow — Alert Log Model
Records every notification sent (email/whatsapp) for breach/risk alerts.
"""

from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.enums import AlertChannel, RiskLevel


class AlertLog(Base):
    __tablename__ = "alert_logs"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)

    channel = Column(SAEnum(AlertChannel), nullable=False)
    risk_level = Column(SAEnum(RiskLevel), nullable=False)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    delivery_status = Column(String(50), default="pending")  # pending, sent, failed

    # Relationships
    order = relationship("Order", back_populates="alert_logs")

    def __repr__(self):
        return (
            f"<AlertLog(order={self.order_id}, channel='{self.channel}', "
            f"risk='{self.risk_level}', status='{self.delivery_status}')>"
        )
