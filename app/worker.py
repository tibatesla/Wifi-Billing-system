import asyncio
from datetime import datetime, timezone
from celery import Celery
from celery.schedules import crontab
from sqlalchemy import select

from app.core.config import settings
from app.db.session import async_session_maker
from app.db.models import Subscription

# Initialize Celery pointing to local Redis
celery_app = Celery(
    "wifi_billing_worker",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

# Configure the Scheduler to run every 1 minute
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
    
    async with async_session_maker() as db:
        stmt = select(Subscription).where(
            Subscription.status == 'ACTIVE',
            Subscription.expires_at <= now
        )
        result = await db.execute(stmt)
        expired_subs = result.scalars().all()
        
        for sub in expired_subs:
            print(f"Disconnecting customer {sub.customer_id} on router {sub.router_id}")
            # Here we would call mikrotik_service.suspend_customer()
            sub.status = 'EXPIRED'
            
        if expired_subs:
            await db.commit()
            print(f"Successfully expired {len(expired_subs)} accounts.")
        else:
            print("No expired accounts found this minute.")

@celery_app.task
def process_expirations():
    asyncio.run(_async_process_expirations())
