"""
OptiFlow — Prescription (Rx) Model
Stores per-eye optical prescription values. Supports manual entry, AI upload parsing,
and cross-check mode. Confidence scores and AI cross-check data stored as JSONB.
"""

from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, ForeignKey,
    Enum as SAEnum, Numeric, Date
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.enums import PrescriptionSource


class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, unique=True, index=True)

    # Right Eye (OD)
    od_sph = Column(Numeric(5, 2), nullable=False)  # e.g., -2.25
    od_cyl = Column(Numeric(5, 2), nullable=False)   # e.g., -0.75
    od_axis = Column(Integer, nullable=False)          # 0-180
    od_pd = Column(Numeric(4, 1), nullable=False)     # e.g., 31.5

    # Left Eye (OS)
    os_sph = Column(Numeric(5, 2), nullable=False)
    os_cyl = Column(Numeric(5, 2), nullable=False)
    os_axis = Column(Integer, nullable=False)
    os_pd = Column(Numeric(4, 1), nullable=False)

    # Prescription metadata
    prescribed_by = Column(String(255), nullable=True)
    prescription_date = Column(Date, nullable=True)

    # Source & AI data
    source = Column(SAEnum(PrescriptionSource), nullable=False, default=PrescriptionSource.MANUAL)
    raw_file_url = Column(String(1024), nullable=True)  # Path to uploaded image/PDF

    # AI confidence scores (populated for upload/both sources)
    # Format: {"OD": 0.92, "OS": 0.88, "overall": 0.90, "fields": {"od_sph": 0.95, ...}}
    confidence = Column(JSONB, nullable=True)

    # AI cross-check data (populated when source='both' and discrepancies found)
    # Format: [{"field": "od_cyl", "manual": -0.75, "ai": -1.25, "ai_confidence": 0.91}]
    ai_cross_check = Column(JSONB, nullable=True)

    # Review flag — set when confidence is low or cross-check finds discrepancies
    needs_review = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    order = relationship("Order", back_populates="prescription")

    def __repr__(self):
        return f"<Prescription(id={self.id}, order_id={self.order_id}, source='{self.source}')>"
