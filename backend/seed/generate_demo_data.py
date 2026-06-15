"""
OptiFlow — Demo Data Generator
Populates the database with initial inventory, SLA rules, and a few sample orders.
"""

import asyncio
import uuid
from decimal import Decimal
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import async_session_factory, engine, init_db
from app.models.enums import LensType, OrderStatus, SourceChannel, RiskLevel
from app.models.inventory import InventoryItem
from app.models.sla_rule import SLARule
from app.models.customer import Customer
from app.models.order import Order
from app.models.prescription import Prescription
from app.models.lens_spec import LensSpec
from app.models.frame import Frame


async def seed_data():
    print("Initializing database tables...")
    await init_db()

    async with async_session_factory() as db:
        print("Seeding SLA Rules...")
        rules = [
            SLARule(lens_type=LensType.SINGLE_VISION, lens_index=Decimal("1.56"), in_house_sla_hours=24, external_sla_hours=72),
            SLARule(lens_type=LensType.SINGLE_VISION, lens_index=Decimal("1.61"), in_house_sla_hours=48, external_sla_hours=96),
            SLARule(lens_type=LensType.PROGRESSIVE, lens_index=Decimal("1.67"), in_house_sla_hours=72, external_sla_hours=144),
        ]
        db.add_all(rules)

        print("Seeding Inventory...")
        inventory = [
            # High volume SV blanks
            InventoryItem(
                lens_type=LensType.SINGLE_VISION, lens_index=Decimal("1.61"), coatings=["AR"],
                power_min=Decimal("-4.00"), power_max=Decimal("+2.00"), qty_on_hand=50
            ),
            # Progressive blanks
            InventoryItem(
                lens_type=LensType.PROGRESSIVE, lens_index=Decimal("1.67"), coatings=["AR", "Blue-light"],
                power_min=Decimal("-6.00"), power_max=Decimal("-2.00"), qty_on_hand=15
            )
        ]
        db.add_all(inventory)

        print("Seeding Customers & Orders...")
        customer1 = Customer(name="Alice Smith", email="alice@example.com", phone="555-0100")
        db.add(customer1)
        await db.flush()

        order1 = Order(
            order_number=f"ORD-{str(uuid.uuid4().hex)[:8].upper()}",
            customer_id=customer1.id,
            store_location="Downtown Flagship",
            source_channel=SourceChannel.IN_STORE,
            status=OrderStatus.PRESCRIPTION_VALIDATION,
            risk_level=RiskLevel.ON_TRACK
        )
        db.add(order1)
        await db.flush()

        rx1 = Prescription(
            order_id=order1.id,
            od_sph=Decimal("-1.50"), od_cyl=Decimal("-0.50"), od_axis=90, od_pd=Decimal("32.0"),
            os_sph=Decimal("-1.25"), os_cyl=Decimal("-0.75"), os_axis=180, os_pd=Decimal("31.5")
        )
        spec1 = LensSpec(
            order_id=order1.id, lens_type=LensType.SINGLE_VISION, lens_index=Decimal("1.61"), coatings=["AR"]
        )
        frame1 = Frame(order_id=order1.id, sku="FR-AV-001", model_name="Classic Aviator", color="Gold")
        db.add_all([rx1, spec1, frame1])

        await db.commit()
        print("Seed complete! Demo data loaded.")

if __name__ == "__main__":
    asyncio.run(seed_data())
