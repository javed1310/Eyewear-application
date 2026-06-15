"""
OptiFlow — Order Model
The central entity in the system. Represents an eyewear manufacturing job ticket
that flows through the 8-stage lifecycle state machine.
"""

from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, ForeignKey,
    Enum as SAEnum, Numeric
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.enums import OrderStatus, SourceChannel, RiskLevel


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(50), unique=True, nullable=False, index=True)

    # Customer linkage
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)

    # Order metadata
    store_location = Column(String(255), nullable=False, index=True)
    source_channel = Column(SAEnum(SourceChannel), default=SourceChannel.IN_STORE)

    # Lifecycle state
    status = Column(
        SAEnum(OrderStatus),
        nullable=False,
        default=OrderStatus.ORDER_INTAKE,
        index=True
    )

    # QC loopback tracking
    original_order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    loopback_count = Column(Integer, default=0)

    # SLA tracking
    sla_target_at = Column(DateTime(timezone=True), nullable=True)
    current_stage_entered_at = Column(DateTime(timezone=True), server_default=func.now())
    external_procurement = Column(Boolean, default=False)

    # Risk level (updated by TAT sweep)
    risk_level = Column(SAEnum(RiskLevel), default=RiskLevel.ON_TRACK)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    customer = relationship("Customer", back_populates="orders")
    prescription = relationship("Prescription", back_populates="order", uselist=False)
    lens_spec = relationship("LensSpec", back_populates="order", uselist=False)
    frame = relationship("Frame", back_populates="order", uselist=False)
    stage_transitions = relationship(
        "StageTransition", back_populates="order",
        order_by="StageTransition.changed_at"
    )
    tat_snapshots = relationship("TATRiskSnapshot", back_populates="order")
    alert_logs = relationship("AlertLog", back_populates="order")

    def __repr__(self):
        return f"<Order(id={self.id}, number='{self.order_number}', status='{self.status}')>"
