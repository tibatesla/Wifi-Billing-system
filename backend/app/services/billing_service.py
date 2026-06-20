import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import Subscription, Plan, Customer

async def create_or_extend_subscription(
    db: AsyncSession, 
    customer_id: uuid.UUID, 
    plan_id: uuid.UUID, 
    router_id: uuid.UUID
) -> Subscription:
    """
    Creates a new subscription or extends an existing active one.
    """
    now = datetime.now(timezone.utc)
    
    # Fetch the plan to get validity hours
    stmt_plan = select(Plan).where(Plan.id == plan_id)
    plan = (await db.execute(stmt_plan)).scalar_one_or_none()
    
    if not plan:
        raise ValueError("Invalid Plan ID")

    # Checks for exxsting active subscribtion
    stmt_sub = select(Subscription).where(
        Subscription.customer_id == customer_id,
        Subscription.status == 'ACTIVE'
    )
    existing_sub = (await db.execute(stmt_sub)).scalar_one_or_none()

    if existing_sub:
        # Extend the current expiration date
        # If expired slightly, start from 'now', otherwise add to existing expiry
        base_time = existing_sub.expires_at if existing_sub.expires_at > now else now
        existing_sub.expires_at = base_time + timedelta(hours=plan.validity_hours)
        existing_sub.plan_id = plan_id # Update plan if they bought a different speed
        return existing_sub
    else:
        # Create a brand new subscription
        new_sub = Subscription(
            customer_id=customer_id,
            plan_id=plan_id,
            router_id=router_id,
            starts_at=now,
            expires_at=now + timedelta(hours=plan.validity_hours),
            status='ACTIVE'
        )
        db.add(new_sub)
        return new_sub