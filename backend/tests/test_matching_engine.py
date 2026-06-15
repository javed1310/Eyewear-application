import pytest
from datetime import datetime, timezone
from decimal import Decimal

from app.models.enums import LensType
from app.models.order import Order
from app.models.prescription import Prescription
from app.models.lens_spec import LensSpec
from app.models.inventory import InventoryItem
from app.models.sla_rule import SLARule
from app.services.matching_engine import (
    find_inventory_item,
    get_sla_rule,
    process_inventory_check,
    MatchingError
)

class MockResult:
    def __init__(self, data):
        self.data = data
    def scalars(self):
        return self
    def all(self):
        return self.data

class MockSession:
    def __init__(self, items=None, rules=None):
        self.items = items or []
        self.rules = rules or []
        self.executed_queries = []

    async def execute(self, query):
        self.executed_queries.append(query)
        # Very simple mock matching: if the query string contains "inventory_items", return items
        query_str = str(query)
        if "inventory_items" in query_str:
            return MockResult(self.items)
        if "sla_rules" in query_str:
            return MockResult(self.rules)
        return MockResult([])

@pytest.fixture
def prescription():
    return Prescription(
        od_sph=Decimal("-2.00"), od_cyl=Decimal("-0.50"), od_axis=90, od_pd=Decimal("32.0"),
        os_sph=Decimal("-1.50"), os_cyl=Decimal("-0.75"), os_axis=180, os_pd=Decimal("31.5")
    )

@pytest.fixture
def lens_spec():
    return LensSpec(
        lens_type=LensType.SINGLE_VISION,
        lens_index=Decimal("1.61"),
        coatings=["AR", "Blue-light"]
    )

@pytest.fixture
def order(prescription, lens_spec):
    return Order(
        id=1,
        prescription=prescription,
        lens_spec=lens_spec,
        external_procurement=False
    )

@pytest.fixture
def inventory_item():
    return InventoryItem(
        id=1,
        lens_type=LensType.SINGLE_VISION,
        lens_index=Decimal("1.61"),
        coatings=["AR", "Blue-light"],
        power_min=Decimal("-6.00"),
        power_max=Decimal("+2.00"),
        qty_on_hand=10
    )

@pytest.fixture
def sla_rule():
    return SLARule(
        lens_type=LensType.SINGLE_VISION,
        lens_index=Decimal("1.61"),
        coatings=["AR", "Blue-light"],
        in_house_sla_hours=48,
        external_sla_hours=120
    )

@pytest.mark.asyncio
async def test_find_inventory_item_match(lens_spec, prescription, inventory_item):
    db = MockSession(items=[inventory_item])
    # The max power needed is -2.50. The inventory item covers -6.00 to +2.00.
    match = await find_inventory_item(db, lens_spec, prescription)
    assert match is not None
    assert match.id == 1

@pytest.mark.asyncio
async def test_find_inventory_item_no_coatings_match(lens_spec, prescription, inventory_item):
    # Change coatings so it doesn't match
    inventory_item.coatings = ["AR"]
    db = MockSession(items=[inventory_item])
    match = await find_inventory_item(db, lens_spec, prescription)
    assert match is None

@pytest.mark.asyncio
async def test_process_inventory_check_in_house(order, inventory_item, sla_rule):
    db = MockSession(items=[inventory_item], rules=[sla_rule])
    
    is_in_house, target_date = await process_inventory_check(db, order)
    
    assert is_in_house is True
    assert order.external_procurement is False
    assert inventory_item.qty_on_hand == 9  # Stock deducted
    # SLA should be 48 hours from now
    now = datetime.now(timezone.utc)
    diff = target_date - now
    # Check within a small margin of error (seconds)
    assert 47 < (diff.total_seconds() / 3600) <= 48

@pytest.mark.asyncio
async def test_process_inventory_check_external(order, sla_rule):
    db = MockSession(items=[], rules=[sla_rule])  # No inventory
    
    is_in_house, target_date = await process_inventory_check(db, order)
    
    assert is_in_house is False
    assert order.external_procurement is True
    # SLA should be 120 hours from now
    now = datetime.now(timezone.utc)
    diff = target_date - now
    assert 119 < (diff.total_seconds() / 3600) <= 120

@pytest.mark.asyncio
async def test_process_inventory_missing_data(order):
    order.lens_spec = None
    db = MockSession()
    
    with pytest.raises(MatchingError):
        await process_inventory_check(db, order)
