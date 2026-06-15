"""
OptiFlow — TAT Risk Snapshot Model
Point-in-time risk assessment for an order, computed by the background TAT sweep.
"""

from sqlalchemy import (
    Column, Integer, DateTime, ForeignKey, Enum as SAEnum, Numeric
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.enums import RiskLevel


class TATRiskSnapshot(Base):
    __tablename__ = "tat_risk_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)

    computed_at = Column(DateTime(timezone=True), server_default=func.now())
    elapsed_in_stage_min = Column(Numeric(10, 2), nullable=True)
    predicted_completion_at = Column(DateTime(timezone=True), nullable=True)
    sla_target_at = Column(DateTime(timezone=True), nullable=True)

    risk_level = Column(SAEnum(RiskLevel), nullable=False, default=RiskLevel.ON_TRACK)

    # Human-readable contributing factors
    # Format: ["Progressive 1.67 + Photochromic typically adds 48h in Lab",
    #          "This order has been in Lab for 52h, SLA allows 40h"]
    contributing_factors = Column(JSONB, nullable=True)

    # Relationships
    order = relationship("Order", back_populates="tat_snapshots")

    def __repr__(self):
        return f"<TATRiskSnapshot(order={self.order_id}, risk='{self.risk_level}')>"
