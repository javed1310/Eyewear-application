"""
OptiFlow — Stage Transition (Audit Log) Model
Immutable record of every order status change. Includes loopback markers
and delay reasons for full auditability.
"""

from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, ForeignKey, Text
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class StageTransition(Base):
    __tablename__ = "stage_transitions"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)

    from_stage = Column(String(50), nullable=False)
    to_stage = Column(String(50), nullable=False)
    changed_by = Column(String(255), nullable=False)  # User name or system identifier
    changed_at = Column(DateTime(timezone=True), server_default=func.now())

    # Optional context
    delay_reason = Column(Text, nullable=True)
    is_loopback = Column(Boolean, default=False)

    # Relationships
    order = relationship("Order", back_populates="stage_transitions")

    def __repr__(self):
        lb = " [LOOPBACK]" if self.is_loopback else ""
        return (
            f"<StageTransition(order={self.order_id}, "
            f"{self.from_stage} -> {self.to_stage}{lb})>"
        )
