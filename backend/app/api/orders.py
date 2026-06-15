"""
OptiFlow — Orders API Router
Handles CRUD and state transitions for orders.
"""

import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.order import Order
from app.models.prescription import Prescription
from app.models.lens_spec import LensSpec
from app.models.frame import Frame
from app.models.enums import OrderStatus, RiskLevel
from app.schemas.order import (
    OrderCreate, OrderResponse, OrderDetailResponse,
    StatusTransitionRequest, StageTransitionResponse
)
from app.services.state_machine import (
    transition_order, InvalidTransitionError, DelayReasonRequiredError
)
from app.api.websockets import broadcast_order_update

router = APIRouter(prefix="/orders", tags=["Orders"])

def generate_order_number() -> str:
    """Generate a unique order number (e.g. ORD-12345678)"""
    return f"ORD-{str(uuid.uuid4().hex)[:8].upper()}"

@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(order_in: OrderCreate, db: AsyncSession = Depends(get_db)):
    """Create a new order with prescription, lens spec, and frame."""
    
    from app.models.customer import Customer

    # Ensure customer exists (auto-create a mock customer for the demo)
    cust_result = await db.execute(select(Customer).where(Customer.id == order_in.customer_id))
    customer = cust_result.scalar_one_or_none()
    if not customer:
        customer = Customer(
            id=order_in.customer_id,
            name="Demo Customer",
            email="demo@optiflow.demo",
            phone="+1234567890"
        )
        db.add(customer)
        await db.flush()

    # Create the core order
    order = Order(
        order_number=generate_order_number(),
        customer_id=order_in.customer_id,
        store_location=order_in.store_location,
        source_channel=order_in.source_channel,
        status=OrderStatus.ORDER_INTAKE,
        risk_level=RiskLevel.ON_TRACK
    )
    db.add(order)
    await db.flush()  # To get order.id

    # Create associated entities
    prescription = Prescription(
        order_id=order.id,
        **order_in.prescription.dict(exclude_unset=True)
    )
    db.add(prescription)

    lens_spec = LensSpec(
        order_id=order.id,
        **order_in.lens_spec.dict(exclude_unset=True)
    )
    db.add(lens_spec)

    frame = Frame(
        order_id=order.id,
        **order_in.frame.dict(exclude_unset=True)
    )
    db.add(frame)

    await db.commit()
    await db.refresh(order)
    
    # ── AI Inventory Matching & SLA Assignment ──
    # PRD requirement: "Once customer order is placed the system needs to tell if the power is in house or not"
    try:
        from app.services.matching_engine import process_inventory_check
        await process_inventory_check(db, order)
        await db.commit()
        await db.refresh(order)
    except Exception as e:
        print(f"[WARNING] Auto-matching failed: {e}")
    
    # Broadcast creation event
    await broadcast_order_update(order.id, "created", {"status": order.status})
    
    return order

@router.get("/", response_model=List[OrderResponse])
async def list_orders(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    lens_type: str = None,
    store_location: str = None,
    db: AsyncSession = Depends(get_db)
):
    """List all orders with optional filters."""
    from sqlalchemy import and_

    query = select(Order).options(selectinload(Order.lens_spec))

    filters = []
    if status:
        filters.append(Order.status == status)
    if store_location:
        filters.append(Order.store_location.ilike(f"%{store_location}%"))

    if filters:
        query = query.where(and_(*filters))

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    orders = result.scalars().all()

    # Post-filter by lens_type (requires joined data)
    if lens_type:
        orders = [o for o in orders if o.lens_spec and o.lens_spec.lens_type == lens_type]

    return orders

@router.get("/{order_id}", response_model=OrderDetailResponse)
async def get_order(order_id: int, db: AsyncSession = Depends(get_db)):
    """Get full details for a specific order."""
    result = await db.execute(
        select(Order)
        .options(
            selectinload(Order.prescription),
            selectinload(Order.lens_spec),
            selectinload(Order.frame),
            selectinload(Order.stage_transitions)
        )
        .where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@router.post("/{order_id}/transition", response_model=StageTransitionResponse)
async def transition_order_status(
    order_id: int, req: StatusTransitionRequest, db: AsyncSession = Depends(get_db)
):
    """
    Transition an order to a new status.
    Enforces the state machine rules and records an audit log.
    """
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    try:
        transition = await transition_order(
            db=db,
            order=order,
            to_stage=req.to_stage,
            actor=req.actor,
            delay_reason=req.delay_reason,
            qc_fail_reason=req.qc_fail_reason
        )
        await db.commit()
        await db.refresh(transition)
        
        # Broadcast transition event
        await broadcast_order_update(
            order_id, "status_changed", 
            {"status": req.to_stage, "risk_level": order.risk_level}
        )
        
        return transition
    except InvalidTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DelayReasonRequiredError as e:
        raise HTTPException(status_code=400, detail=str(e))
