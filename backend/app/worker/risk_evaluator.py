"""
OptiFlow — Background Risk Evaluator
Periodically scans active orders and updates their risk levels using the ML TAT Predictor.
"""

import asyncio
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.database import async_session_factory
from app.models.order import Order
from app.models.enums import OrderStatus, RiskLevel
from app.services.tat_predictor import update_order_risk
from app.services.notifications import notification_service
from app.api.websockets import broadcast_order_update

async def evaluate_active_orders():
    """
    Scans all orders that are not in terminal states, runs the ML risk prediction,
    and updates the database/frontend if the risk level changed.
    """
    terminal_states = [OrderStatus.READY_FOR_DISPATCH, OrderStatus.OUT_FOR_DELIVERY, OrderStatus.DELIVERED]
    
    async with async_session_factory() as db:
        result = await db.execute(
            select(Order)
            .options(selectinload(Order.lens_spec))
            .where(Order.status.not_in(terminal_states))
        )
        orders = result.scalars().all()
        
        updates_made = 0
        for order in orders:
            if not order.lens_spec:
                continue
                
            old_risk = order.risk_level
            risk_changed = update_order_risk(order, order.lens_spec)
            
            if risk_changed:
                updates_made += 1
                await broadcast_order_update(
                    order.id, "status_changed", 
                    {"status": order.status, "risk_level": order.risk_level}
                )
                
                # Write alert log to DB
                from app.models.alert_log import AlertLog
                from app.models.enums import AlertChannel
                alert = AlertLog(
                    order_id=order.id,
                    channel=AlertChannel.EMAIL,
                    risk_level=order.risk_level,
                    delivery_status="sent"
                )
                db.add(alert)
                
                # Trigger notifications
                if order.risk_level == RiskLevel.BREACHED and old_risk != RiskLevel.BREACHED:
                    await notification_service.alert_breach(order)
                elif order.risk_level == RiskLevel.AT_RISK and old_risk != RiskLevel.AT_RISK:
                    await notification_service.alert_at_risk(order)
                
        if updates_made > 0:
            await db.commit()
            print(f"[RiskEvaluator] Evaluated {len(orders)} orders. Updated risk for {updates_made} orders.")

async def start_risk_evaluator_loop(interval_seconds: int = 300):
    """Runs the evaluator every N seconds."""
    print(f"[RiskEvaluator] Started. Running every {interval_seconds} seconds.")
    while True:
        try:
            await evaluate_active_orders()
        except Exception as e:
            print(f"[RiskEvaluator] Error evaluating orders: {e}")
        await asyncio.sleep(interval_seconds)
