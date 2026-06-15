"""
OptiFlow — Lens Specification Model
Defines the lens configuration for an order (type, index, coatings, tint).
"""

from sqlalchemy import (
    Column, Integer, String, ForeignKey, Enum as SAEnum, Numeric
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.enums import LensType


class LensSpec(Base):
    __tablename__ = "lens_specs"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, unique=True, index=True)

    lens_type = Column(SAEnum(LensType), nullable=False)
    lens_index = Column(Numeric(3, 2), nullable=False)  # 1.56, 1.61, 1.67, 1.74
    coatings = Column(ARRAY(String), default=[])  # ['AR', 'Blue-light', 'Photochromic']
    tint = Column(String(100), nullable=True)

    # Relationships
    order = relationship("Order", back_populates="lens_spec")

    def __repr__(self):
        return f"<LensSpec(id={self.id}, type='{self.lens_type}', index={self.lens_index})>"
