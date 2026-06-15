"""
OptiFlow — Inventory Item Model
Lens blanks in stock, keyed by lens type + index + coatings + power range.
"""

from sqlalchemy import (
    Column, Integer, String, Numeric, DateTime, Enum as SAEnum
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.enums import LensType


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, index=True)

    lens_type = Column(SAEnum(LensType), nullable=False, index=True)
    lens_index = Column(Numeric(3, 2), nullable=False, index=True)
    coatings = Column(ARRAY(String), default=[])

    # Power range this blank covers
    power_min = Column(Numeric(5, 2), nullable=False)  # e.g., -6.00
    power_max = Column(Numeric(5, 2), nullable=False)  # e.g., -2.00

    # Stock levels
    qty_on_hand = Column(Integer, nullable=False, default=0)
    reorder_threshold = Column(Integer, nullable=False, default=5)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return (
            f"<InventoryItem(id={self.id}, {self.lens_type}/{self.lens_index}, "
            f"qty={self.qty_on_hand})>"
        )
