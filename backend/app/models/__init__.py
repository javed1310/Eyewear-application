"""
OptiFlow — Models Package
Imports all models so they are registered with SQLAlchemy Base.metadata
and available for Alembic autogeneration.
"""

from app.models.enums import (
    OrderStatus, PrescriptionSource, LensType,
    RiskLevel, AlertChannel, UserRole, SourceChannel
)
from app.models.customer import Customer
from app.models.user import User
from app.models.order import Order
from app.models.prescription import Prescription
from app.models.lens_spec import LensSpec
from app.models.frame import Frame
from app.models.inventory import InventoryItem
from app.models.sla_rule import SLARule
from app.models.stage_transition import StageTransition
from app.models.tat_snapshot import TATRiskSnapshot
from app.models.alert_log import AlertLog

__all__ = [
    "OrderStatus", "PrescriptionSource", "LensType",
    "RiskLevel", "AlertChannel", "UserRole", "SourceChannel",
    "Customer", "User", "Order", "Prescription", "LensSpec",
    "Frame", "InventoryItem", "SLARule", "StageTransition",
    "TATRiskSnapshot", "AlertLog",
]
