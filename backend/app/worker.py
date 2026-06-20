import asyncio
from datetime import datetime, timezone
from celery import Celery
from celery.schedules import crontab
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.db.models import Subscription, Customer

# Initialize Celery pointing to local Redis
celery_app = Celery(
    "wifi_billing_worker",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

celery_app.conf.beat_schedule = {
    'sweep-expired-subscriptions': {
        'task': 'app.worker.process_expirations',
        'schedule': crontab(minute='*'), 
    }
}
celery_app.conf.timezone = 'Africa/Nairobi'

async def _async_process_expirations():
    print("Sweeping database for expired subscriptions...")
    now = datetime.now(timezone.utc)
    
    # Create a fresh engine inside the async loop with NullPool
    # This prevents the "attached to a different loop" RuntimeError
    engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
    local_session = async_sessionmaker(engine, expire_on_commit=False)
    
    try:
        async with local_session() as db:
            stmt = select(Subscription).options(
                selectinload(Subscription.customer).selectinload(Customer.tenant)
            ).where(
                Subscription.status == 'ACTIVE',
                Subscription.expires_at <= now
            )
            result = await db.execute(stmt)
            expired_subs = result.scalars().all()
            
            for sub in expired_subs:
                print(f"Disconnecting customer {sub.customer.phone_number} on router {sub.router_id}")
                sub.status = 'EXPIRED'
                
            if expired_subs:
                await db.commit()
                print(f"Successfully expired {len(expired_subs)} accounts.")
            else:
                print("No expired accounts found this minute.")
    finally:
        # Safely tear down the connections linked to this specific event loop
        await engine.dispose()

@celery_app.task
def process_expirations():
    asyncio.run(_async_process_expirations())