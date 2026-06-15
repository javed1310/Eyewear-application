"""
OptiFlow — SQLAlchemy Enum Types
Shared enumerations used across multiple models.
"""

import enum


class OrderStatus(str, enum.Enum):
    """Order lifecycle stages — matches the canonical state machine."""
    ORDER_INTAKE = "order_intake"
    PRESCRIPTION_VALIDATION = "prescription_validation"
    INVENTORY_CHECK = "inventory_check"
    LAB_PRODUCTION = "lab_production"
    QUALITY_CONTROL = "quality_control"
    READY_FOR_DISPATCH = "ready_for_dispatch"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"


class PrescriptionSource(str, enum.Enum):
    """How the prescription was entered."""
    MANUAL = "manual"
    UPLOAD = "upload"
    BOTH = "both"


class LensType(str, enum.Enum):
    """Types of corrective lenses."""
    SINGLE_VISION = "single_vision"
    BIFOCAL = "bifocal"
    PROGRESSIVE = "progressive"


class RiskLevel(str, enum.Enum):
    """TAT risk assessment levels."""
    ON_TRACK = "on_track"
    AT_RISK = "at_risk"
    BREACHED = "breached"


class AlertChannel(str, enum.Enum):
    """Notification delivery channels."""
    EMAIL = "email"
    WHATSAPP = "whatsapp"


class UserRole(str, enum.Enum):
    """Staff roles for access control."""
    OPS = "ops"
    LAB = "lab"
    QC = "qc"
    INVENTORY = "inventory"
    ADMIN = "admin"


class SourceChannel(str, enum.Enum):
    """How the order was placed."""
    ONLINE = "online"
    IN_STORE = "in_store"
    PHONE = "phone"
