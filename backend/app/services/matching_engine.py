"""
OptiFlow — Inventory Matching & SLA Assignment Engine
Determines if an order can be fulfilled in-house or requires external procurement,
and assigns the corresponding SLA target timeframe.
"""

from typing import Tuple, Optional
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.enums import LensType
from app.models.order import Order
from app.models.inventory import InventoryItem
from app.models.sla_rule import SLARule
from app.models.prescription import Prescription
from app.models.lens_spec import LensSpec
from app.core.config import settings

class MatchingError(Exception):
    pass

async def find_inventory_item(
    db: AsyncSession,
    lens_spec: LensSpec,
    prescription: Prescription
) -> Optional[InventoryItem]:
    """
    Finds a matching lens blank in stock for the given spec and prescription.
    Checks if the required power falls within the blank's power range.
    For simplicity, we check if BOTH eyes fit within a single blank's range,
    or we'd technically need two blanks. In this system, we track blanks as pairs
    or individual items depending on the `qty_on_hand` (1 qty = 1 pair for MVP).
    """
    # Calculate the max power needed (spherical equivalent or max absolute power)
    # simplified: just checking if max(abs(sph + cyl)) fits in the blank range
    
    # Calculate required powers
    od_power = prescription.od_sph + prescription.od_cyl
    os_power = prescription.os_sph + prescription.os_cyl
    
    # Range check values
    min_needed = min(od_power, os_power)
    max_needed = max(od_power, os_power)

    # Query inventory for a matching spec that covers the power range
    query = select(InventoryItem).where(
        InventoryItem.lens_type == lens_spec.lens_type,
        InventoryItem.lens_index == lens_spec.lens_index,
        InventoryItem.power_min <= min_needed,
        InventoryItem.power_max >= max_needed,
        InventoryItem.qty_on_hand > 0
    )
    
    # In Postgres, checking array equality can be strict. 
    # For MVP, we fetch candidates and check coatings in Python to avoid complex array logic
    result = await db.execute(query)
    candidates = result.scalars().all()
    
    required_coatings = set(lens_spec.coatings)
    for candidate in candidates:
        if set(candidate.coatings) == required_coatings:
            return candidate
            
    return None

async def get_sla_rule(
    db: AsyncSession,
    lens_spec: LensSpec
) -> SLARule:
    """Finds the applicable SLA rule for the given lens specification."""
    query = select(SLARule).where(
        SLARule.lens_type == lens_spec.lens_type,
        SLARule.lens_index == lens_spec.lens_index
    )
    result = await db.execute(query)
    candidates = result.scalars().all()
    
    required_coatings = set(lens_spec.coatings)
    for candidate in candidates:
        if set(candidate.coatings) == required_coatings:
            return candidate
            
    # Default rule if not specifically defined
    return SLARule(
        lens_type=lens_spec.lens_type,
        lens_index=lens_spec.lens_index,
        in_house_sla_hours=48,
        external_sla_hours=120
    )

async def process_inventory_check(
    db: AsyncSession,
    order: Order
) -> Tuple[bool, datetime]:
    """
    Evaluates inventory, deducts stock if available, and assigns the SLA target.
    
    Returns:
        Tuple[is_in_house: bool, sla_target_at: datetime]
    """
    if not order.prescription or not order.lens_spec:
        raise MatchingError("Order is missing prescription or lens specification")

    # 1. Match inventory
    inventory_item = await find_inventory_item(db, order.lens_spec, order.prescription)
    
    is_in_house = inventory_item is not None
    
    # 2. Get SLA rule
    sla_rule = await get_sla_rule(db, order.lens_spec)
    
    # 3. Calculate target
    sla_hours = sla_rule.in_house_sla_hours if is_in_house else sla_rule.external_sla_hours
    target_date = datetime.now(timezone.utc) + timedelta(hours=sla_hours)
    
    # 4. Update order & inventory
    order.external_procurement = not is_in_house
    order.sla_target_at = target_date
    
    if is_in_house:
        inventory_item.qty_on_hand -= 1  # Deduct stock (MVP: 1 unit = 1 pair)
        
    return is_in_house, target_date
