"""
OptiFlow — Alerts API Router
Serves in-app alert notifications for SLA breaches and risk escalations.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.models.alert_log import AlertLog
from app.models.order import Order

router = APIRouter(prefix="/alerts", tags=["Alerts"])


class AlertResponse(BaseModel):
    id: int
    order_id: int
    order_number: Optional[str] = None
    channel: str
    risk_level: str
    sent_at: datetime
    delivery_status: str

    class Config:
        from_attributes = True


@router.get("/", response_model=List[AlertResponse])
async def list_alerts(
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db)
):
    """Returns recent alerts, most recent first."""
    result = await db.execute(
        select(AlertLog)
        .options(selectinload(AlertLog.order))
        .order_by(AlertLog.sent_at.desc())
        .limit(limit)
    )
    alerts = result.scalars().all()

    return [
        AlertResponse(
            id=a.id,
            order_id=a.order_id,
            order_number=a.order.order_number if a.order else None,
            channel=a.channel,
            risk_level=a.risk_level,
            sent_at=a.sent_at,
            delivery_status=a.delivery_status
        )
        for a in alerts
    ]
