"""
OptiFlow — Order & Prescription Schemas
Pydantic schemas for API request validation and response serialization.
Includes strict server-side validation for manual Rx entry (ranges & increments).
"""

from datetime import datetime, date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, ValidationInfo
from decimal import Decimal

from app.models.enums import (
    OrderStatus, PrescriptionSource, LensType,
    RiskLevel, SourceChannel
)


# ── Prescription Validation Helpers ──

def validate_diopters(v: Decimal, min_val: float, max_val: float, field_name: str) -> Decimal:
    """Validates SPH and CYL values: bounds and 0.25 increments."""
    val = float(v)
    if val < min_val or val > max_val:
        raise ValueError(f"{field_name} must be between {min_val} and {max_val}")
    
    # Check 0.25 increment
    # We multiply by 4; if it's a multiple of 0.25, the result should be an integer
    if not (val * 4).is_integer():
        raise ValueError(f"{field_name} must be in increments of 0.25")
        
    return v

def validate_axis(v: int) -> int:
    """Validates AXIS: 0 to 180 integer."""
    if v < 0 or v > 180:
        raise ValueError("AXIS must be an integer between 0 and 180")
    return v

def validate_pd(v: Decimal) -> Decimal:
    """Validates monocular PD: typically between 20.0 and 40.0 mm."""
    val = float(v)
    if val < 20.0 or val > 45.0:
        raise ValueError("PD must be between 20.0 and 45.0 mm per eye")
    return v


# ── Schemas ──

class PrescriptionBase(BaseModel):
    od_sph: Decimal
    od_cyl: Decimal
    od_axis: int
    od_pd: Decimal
    
    os_sph: Decimal
    os_cyl: Decimal
    os_axis: int
    os_pd: Decimal
    
    prescribed_by: Optional[str] = None
    prescription_date: Optional[date] = None

    @field_validator('od_sph', 'os_sph')
    @classmethod
    def validate_sph(cls, v: Decimal, info: ValidationInfo) -> Decimal:
        return validate_diopters(v, -20.0, 20.0, info.field_name.upper())

    @field_validator('od_cyl', 'os_cyl')
    @classmethod
    def validate_cyl(cls, v: Decimal, info: ValidationInfo) -> Decimal:
        return validate_diopters(v, -10.0, 10.0, info.field_name.upper())

    @field_validator('od_axis', 'os_axis')
    @classmethod
    def val_axis(cls, v: int) -> int:
        return validate_axis(v)

    @field_validator('od_pd', 'os_pd')
    @classmethod
    def val_pd(cls, v: Decimal) -> Decimal:
        return validate_pd(v)

class PrescriptionCreate(PrescriptionBase):
    pass

class PrescriptionResponse(PrescriptionBase):
    id: int
    source: PrescriptionSource
    raw_file_url: Optional[str]
    confidence: Optional[Dict[str, Any]]
    ai_cross_check: Optional[Dict[str, Any]]
    needs_review: bool

    class Config:
        from_attributes = True

class LensSpecBase(BaseModel):
    lens_type: LensType
    lens_index: Decimal
    coatings: List[str] = []
    tint: Optional[str] = None

class LensSpecCreate(LensSpecBase):
    pass

class LensSpecResponse(LensSpecBase):
    id: int

    class Config:
        from_attributes = True

class FrameBase(BaseModel):
    sku: Optional[str] = None
    model_name: Optional[str] = None
    dimensions: Optional[str] = None
    color: Optional[str] = None
    brand: Optional[str] = None

class FrameCreate(FrameBase):
    pass

class FrameResponse(FrameBase):
    id: int

    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    customer_id: int
    store_location: str
    source_channel: SourceChannel = SourceChannel.IN_STORE
    
    prescription: PrescriptionCreate
    lens_spec: LensSpecCreate
    frame: FrameCreate

class StageTransitionResponse(BaseModel):
    id: int
    from_stage: str
    to_stage: str
    changed_by: str
    changed_at: datetime
    delay_reason: Optional[str]
    is_loopback: bool

    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: int
    order_number: str
    customer_id: int
    store_location: str
    source_channel: SourceChannel
    status: OrderStatus
    loopback_count: int
    sla_target_at: Optional[datetime]
    current_stage_entered_at: Optional[datetime]
    external_procurement: bool
    risk_level: RiskLevel
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class OrderDetailResponse(OrderResponse):
    prescription: Optional[PrescriptionResponse]
    lens_spec: Optional[LensSpecResponse]
    frame: Optional[FrameResponse]
    stage_transitions: List[StageTransitionResponse] = []

    class Config:
        from_attributes = True

class StatusTransitionRequest(BaseModel):
    to_stage: OrderStatus
    actor: str
    delay_reason: Optional[str] = None
    qc_fail_reason: Optional[str] = None
