"""
OptiFlow — Frame Model
Physical frame details for an order.
"""

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class Frame(Base):
    __tablename__ = "frames"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, unique=True, index=True)

    sku = Column(String(100), nullable=True)
    model_name = Column(String(255), nullable=True)
    dimensions = Column(String(100), nullable=True)  # e.g., "52-18-140"
    color = Column(String(100), nullable=True)
    brand = Column(String(255), nullable=True)

    # Relationships
    order = relationship("Order", back_populates="frame")

    def __repr__(self):
        return f"<Frame(id={self.id}, sku='{self.sku}', model='{self.model_name}')>"
