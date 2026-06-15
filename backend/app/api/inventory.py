"""
OptiFlow — Inventory API Router
Handles inventory stock checks and SLA assignment.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.order import Order
from app.models.enums import OrderStatus
from app.services.matching_engine import process_inventory_check, MatchingError
from app.services.state_machine import transition_order
from app.api.websockets import broadcast_order_update
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/inventory", tags=["Inventory"])

class InventoryCheckResponse(BaseModel):
    is_in_house: bool
    sla_target_at: datetime
    message: str

@router.get("/")
async def get_inventory(db: AsyncSession = Depends(get_db)):
    """Returns the current inventory levels."""
    from app.models.inventory import InventoryItem
    result = await db.execute(select(InventoryItem))
    items = result.scalars().all()
    
    return [
        {
            "id": item.id,
            "lens_type": item.lens_type,
            "lens_index": float(item.lens_index),
            "promised_sla_hours": 24, # In-house SLA
            "quantity": item.qty_on_hand,
            "minimum_threshold": item.reorder_threshold
        }
        for item in items
    ]

@router.post("/check-order/{order_id}", response_model=InventoryCheckResponse)
async def check_order_inventory(
    order_id: int, db: AsyncSession = Depends(get_db)
):
    """
    Triggers the inventory matching engine for a specific order.
    Transitions the order from PRESCRIPTION_VALIDATION to INVENTORY_CHECK,
    evaluates stock, assigns SLA, and transitions to LAB_PRODUCTION.
    """
    # 1. Fetch order with relations
    result = await db.execute(
        select(Order)
        .options(
            selectinload(Order.prescription),
            selectinload(Order.lens_spec)
        )
        .where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # 2. Check if we're in the right state
    if order.status != OrderStatus.PRESCRIPTION_VALIDATION:
        raise HTTPException(
            status_code=400, 
            detail=f"Order must be in {OrderStatus.PRESCRIPTION_VALIDATION} to check inventory, but is in {order.status}"
        )

    # 3. Transition to INVENTORY_CHECK
    await transition_order(
        db=db,
        order=order,
        to_stage=OrderStatus.INVENTORY_CHECK,
        actor="system_inventory_engine"
    )
    
    # 4. Run matching logic
    try:
        is_in_house, sla_target = await process_inventory_check(db, order)
    except MatchingError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    # 5. Transition to LAB_PRODUCTION
    await transition_order(
        db=db,
        order=order,
        to_stage=OrderStatus.LAB_PRODUCTION,
        actor="system_inventory_engine"
    )
    
    await db.commit()
    
    # Broadcast transition event
    await broadcast_order_update(
        order_id, "status_changed", 
        {"status": OrderStatus.LAB_PRODUCTION, "risk_level": order.risk_level}
    )
    
    msg = "In-house matching successful. Proceeding to lab." if is_in_house else "Stock unavailable. Flagged for external procurement."
    
    return InventoryCheckResponse(
        is_in_house=is_in_house,
        sla_target_at=sla_target,
        message=msg
    )
