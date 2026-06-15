import pytest
from datetime import datetime, timedelta, timezone

from app.models.enums import OrderStatus, RiskLevel
from app.models.order import Order
from app.services.state_machine import (
    transition_order,
    is_valid_transition,
    InvalidTransitionError,
    DelayReasonRequiredError,
    dwell_exceeds_threshold
)
from app.core.config import settings

class MockSession:
    def __init__(self):
        self.added = []
    def add(self, obj):
        self.added.append(obj)

@pytest.fixture
def order():
    now = datetime.now(timezone.utc)
    return Order(
        id=1,
        order_number="ORD-TEST",
        status=OrderStatus.ORDER_INTAKE,
        current_stage_entered_at=now,
        loopback_count=0,
        risk_level=RiskLevel.ON_TRACK
    )

def test_is_valid_transition():
    assert is_valid_transition(OrderStatus.ORDER_INTAKE, OrderStatus.PRESCRIPTION_VALIDATION) is True
    assert is_valid_transition(OrderStatus.ORDER_INTAKE, OrderStatus.LAB_PRODUCTION) is False
    assert is_valid_transition(OrderStatus.QUALITY_CONTROL, OrderStatus.READY_FOR_DISPATCH) is True
    assert is_valid_transition(OrderStatus.QUALITY_CONTROL, OrderStatus.LAB_PRODUCTION) is True  # loopback

@pytest.mark.asyncio
async def test_valid_transition(order):
    db = MockSession()
    transition = await transition_order(
        db=db,
        order=order,
        to_stage=OrderStatus.PRESCRIPTION_VALIDATION,
        actor="system"
    )
    assert order.status == OrderStatus.PRESCRIPTION_VALIDATION
    assert transition.from_stage == OrderStatus.ORDER_INTAKE
    assert transition.to_stage == OrderStatus.PRESCRIPTION_VALIDATION
    assert len(db.added) == 1

@pytest.mark.asyncio
async def test_invalid_transition(order):
    db = MockSession()
    with pytest.raises(InvalidTransitionError):
        await transition_order(
            db=db,
            order=order,
            to_stage=OrderStatus.LAB_PRODUCTION,
            actor="system"
        )

@pytest.mark.asyncio
async def test_qc_loopback(order):
    db = MockSession()
    order.status = OrderStatus.QUALITY_CONTROL
    order.sla_target_at = datetime.now(timezone.utc) + timedelta(hours=12)

    transition = await transition_order(
        db=db,
        order=order,
        to_stage=OrderStatus.LAB_PRODUCTION,
        actor="qc_user",
        qc_fail_reason="Lens scratched"
    )
    
    assert order.status == OrderStatus.LAB_PRODUCTION
    assert order.loopback_count == 1
    assert transition.is_loopback is True
    assert "Lens scratched" in transition.delay_reason
    assert order.risk_level == RiskLevel.ON_TRACK  # < 2 loopbacks

@pytest.mark.asyncio
async def test_qc_loopback_escalates_risk(order):
    db = MockSession()
    order.status = OrderStatus.QUALITY_CONTROL
    order.loopback_count = 1

    await transition_order(
        db=db,
        order=order,
        to_stage=OrderStatus.LAB_PRODUCTION,
        actor="qc_user",
        qc_fail_reason="Wrong axis again"
    )
    
    assert order.loopback_count == 2
    assert order.risk_level == RiskLevel.AT_RISK  # >= 2 loopbacks escalates risk

@pytest.mark.asyncio
async def test_dwell_threshold_requires_reason(order):
    db = MockSession()
    # Mock entered_at to 5 hours ago (threshold is 4)
    order.current_stage_entered_at = datetime.now(timezone.utc) - timedelta(hours=5)
    
    # Should fail without delay reason
    with pytest.raises(DelayReasonRequiredError):
        await transition_order(
            db=db,
            order=order,
            to_stage=OrderStatus.PRESCRIPTION_VALIDATION,
            actor="system"
        )
    
    # Should succeed with delay reason
    transition = await transition_order(
        db=db,
        order=order,
        to_stage=OrderStatus.PRESCRIPTION_VALIDATION,
        actor="system",
        delay_reason="Waiting on customer confirmation"
    )
    assert transition.delay_reason == "Waiting on customer confirmation"
