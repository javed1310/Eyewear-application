"""
OptiFlow — Order Lifecycle State Machine
Enforces strict server-side transition validation. No client can move an order
to an arbitrary status. Every transition is validated, audited, and — for QC
loopbacks — triggers SLA recalculation.

This is a pure function/class module, testable independently of the API layer.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import OrderStatus, RiskLevel
from app.models.order import Order
from app.models.stage_transition import StageTransition
from app.core.config import settings


# ── Allowed state transitions ──
ALLOWED_TRANSITIONS: dict[str, list[str]] = {
    OrderStatus.ORDER_INTAKE:            [OrderStatus.PRESCRIPTION_VALIDATION],
    OrderStatus.PRESCRIPTION_VALIDATION: [OrderStatus.INVENTORY_CHECK],
    OrderStatus.INVENTORY_CHECK:         [OrderStatus.LAB_PRODUCTION],
    OrderStatus.LAB_PRODUCTION:          [OrderStatus.QUALITY_CONTROL],
    OrderStatus.QUALITY_CONTROL:         [OrderStatus.READY_FOR_DISPATCH, OrderStatus.LAB_PRODUCTION],  # loopback
    OrderStatus.READY_FOR_DISPATCH:      [OrderStatus.OUT_FOR_DELIVERY],
    OrderStatus.OUT_FOR_DELIVERY:        [OrderStatus.DELIVERED],
    OrderStatus.DELIVERED:               [],
}

# ── Stage display names for human-readable output ──
STAGE_DISPLAY_NAMES: dict[str, str] = {
    OrderStatus.ORDER_INTAKE:            "Order Intake",
    OrderStatus.PRESCRIPTION_VALIDATION: "Prescription Validation",
    OrderStatus.INVENTORY_CHECK:         "Inventory Check",
    OrderStatus.LAB_PRODUCTION:          "Lab / Production",
    OrderStatus.QUALITY_CONTROL:         "Quality Control",
    OrderStatus.READY_FOR_DISPATCH:      "Ready for Dispatch",
    OrderStatus.OUT_FOR_DELIVERY:        "Out for Delivery",
    OrderStatus.DELIVERED:               "Delivered",
}


class InvalidTransitionError(Exception):
    """Raised when an order status transition is not allowed."""

    def __init__(self, current_status: str, target_status: str):
        self.current_status = current_status
        self.target_status = target_status
        super().__init__(
            f"Invalid transition: '{current_status}' -> '{target_status}'. "
            f"Allowed: {ALLOWED_TRANSITIONS.get(current_status, [])}"
        )


class DelayReasonRequiredError(Exception):
    """Raised when a status change requires a delay reason but none was provided."""

    def __init__(self):
        super().__init__(
            "A delay reason is required when the order has exceeded "
            "the dwell time threshold in the current stage."
        )


def get_allowed_transitions(current_status: str) -> list[str]:
    """Return the list of valid next statuses from the current status."""
    return ALLOWED_TRANSITIONS.get(current_status, [])


def is_valid_transition(current_status: str, target_status: str) -> bool:
    """Check whether a transition from current to target is allowed."""
    return target_status in ALLOWED_TRANSITIONS.get(current_status, [])


def dwell_exceeds_threshold(order: Order) -> bool:
    """
    Check if the order has been in its current stage longer than
    the configurable dwell threshold.
    """
    if not order.current_stage_entered_at:
        return False

    now = datetime.now(timezone.utc)
    entered = order.current_stage_entered_at
    if entered.tzinfo is None:
        entered = entered.replace(tzinfo=timezone.utc)

    elapsed = now - entered
    threshold = timedelta(hours=settings.DWELL_THRESHOLD_HOURS)
    return elapsed > threshold


async def transition_order(
    db: AsyncSession,
    order: Order,
    to_stage: str,
    actor: str,
    delay_reason: Optional[str] = None,
    qc_fail_reason: Optional[str] = None,
) -> StageTransition:
    """
    Transition an order to a new stage with full validation and audit logging.

    Args:
        db: Database session
        order: The order to transition
        to_stage: Target status
        actor: Who performed the action (user name or 'system')
        delay_reason: Required when dwell threshold exceeded
        qc_fail_reason: Structured failure reason for QC fail loopback

    Returns:
        The created StageTransition audit record

    Raises:
        InvalidTransitionError: If the transition is not allowed
        DelayReasonRequiredError: If delay reason is required but missing
    """
    from_stage = order.status

    # 1. Validate the transition
    if not is_valid_transition(from_stage, to_stage):
        raise InvalidTransitionError(from_stage, to_stage)

    # 2. Detect QC loopback
    is_loopback = (
        from_stage == OrderStatus.QUALITY_CONTROL
        and to_stage == OrderStatus.LAB_PRODUCTION
    )

    # 3. Handle loopback-specific logic
    if is_loopback:
        order.loopback_count += 1
        # Use QC fail reason as delay reason if not explicitly provided
        if not delay_reason and qc_fail_reason:
            delay_reason = f"QC Failed: {qc_fail_reason}"

        # Recalculate SLA: extend by rework buffer
        _recalc_sla(order)

    # 4. Check dwell threshold — require delay reason if exceeded
    if dwell_exceeds_threshold(order) and not delay_reason and not is_loopback:
        raise DelayReasonRequiredError()

    # 5. Write immutable audit log
    transition = StageTransition(
        order_id=order.id,
        from_stage=from_stage,
        to_stage=to_stage,
        changed_by=actor,
        delay_reason=delay_reason,
        is_loopback=is_loopback,
    )
    db.add(transition)

    # 6. Update order state
    order.status = to_stage
    order.current_stage_entered_at = datetime.now(timezone.utc)

    # 7. Force At Risk if loopback count >= 2
    if order.loopback_count >= 2:
        order.risk_level = RiskLevel.AT_RISK

    return transition


def _recalc_sla(order: Order) -> None:
    """
    Recalculate SLA target after a QC loopback.
    New target = current time + rework buffer (configurable, default 24h).
    """
    now = datetime.now(timezone.utc)
    rework_buffer = timedelta(hours=settings.REWORK_BUFFER_HOURS)

    if order.sla_target_at:
        # Extend from current target or now, whichever is later
        base = max(order.sla_target_at, now)
        order.sla_target_at = base + rework_buffer
    else:
        order.sla_target_at = now + rework_buffer
