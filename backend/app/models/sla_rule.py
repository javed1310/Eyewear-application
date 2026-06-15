"""
OptiFlow — SLA Rule Model
Defines turnaround time rules per lens type + index + coating combination.
"""

from sqlalchemy import Column, Integer, String, Numeric, Enum as SAEnum
from sqlalchemy.dialects.postgresql import ARRAY

from app.core.database import Base
from app.models.enums import LensType


class SLARule(Base):
    __tablename__ = "sla_rules"

    id = Column(Integer, primary_key=True, index=True)

    lens_type = Column(SAEnum(LensType), nullable=False)
    lens_index = Column(Numeric(3, 2), nullable=False)
    coatings = Column(ARRAY(String), default=[])

    # SLA hours based on availability
    in_house_sla_hours = Column(Integer, nullable=False, default=48)
    external_sla_hours = Column(Integer, nullable=False, default=120)

    def __repr__(self):
        return (
            f"<SLARule(id={self.id}, {self.lens_type}/{self.lens_index}, "
            f"in_house={self.in_house_sla_hours}h, external={self.external_sla_hours}h)>"
        )
