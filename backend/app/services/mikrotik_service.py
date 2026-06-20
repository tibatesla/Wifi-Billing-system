import asyncio
import routeros_api
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.db.models import Router

# SYNCHRONOUS CORE OPERATIONS

def _connect_to_router(host: str, username: str, password: str, port: int = 8728):
    """Establishes the synchronous socket connection to the router."""
    # NIn production, switch plaintext_login to False and use API-SSL (port 8729)
    connection = routeros_api.RouterOsApiPool(
        host=host,
        username=username,
        password=password,
        port=port,
        plaintext_login=True 
    )
    return connection

def _sync_activate_hotspot_user(host, user, pwd, port, customer_phone, plan_profile):
    """Creates or un-suspends a hotspot user and assigns their bandwidth profile."""
    connection = _connect_to_router(host, user, pwd, port)
    api = connection.get_api()
    
    try:
        hotspot_users = api.get_resource('/ip/hotspot/user')
        
        # Check if user already exists (Idempotency)
        existing_user = hotspot_users.get(name=customer_phone)
        
        if existing_user:
            # User exists: Un-disable them and update their profile/speed limit
            user_id = existing_user[0]['id']
            hotspot_users.set(id=user_id, disabled='no', profile=plan_profile)
        else:
            # New User: Create them. We use phone number for both name and password
            hotspot_users.add(
                server='all', 
                name=customer_phone, 
                password=customer_phone, 
                profile=plan_profile
            )
        return True
    except Exception as e:
        print(f"RouterOS API Error (Activation): {str(e)}")
        raise
    finally:
        connection.disconnect()

def _sync_suspend_hotspot_user(host, user, pwd, port, customer_phone):
    """Disables the hotspot user and forcibly drops their active internet session."""
    connection = _connect_to_router(host, user, pwd, port)
    api = connection.get_api()
    
    try:
        # 1. Disable the account so they cannot log back in
        hotspot_users = api.get_resource('/ip/hotspot/user')
        existing_user = hotspot_users.get(name=customer_phone)
        
        if existing_user:
            hotspot_users.set(id=existing_user[0]['id'], disabled='yes')
            
        # 2. Kick them off immediately (Kill active session)
        active_sessions = api.get_resource('/ip/hotspot/active')
        active_user = active_sessions.get(user=customer_phone)
        
        for session in active_user:
            active_sessions.remove(id=session['id'])
            
        return True
    except Exception as e:
        print(f"RouterOS API Error (Suspension): {str(e)}")
        raise
    finally:
        connection.disconnect()

def _sync_get_router_health(host, user, pwd, port):
    """Fetches CPU load, uptime, and active user count for the Admin Dashboard."""
    connection = _connect_to_router(host, user, pwd, port)
    api = connection.get_api()
    
    try:
        # Get system resources
        resources = api.get_resource('/system/resource').get()[0]
        # Get active user count
        active_users = api.get_resource('/ip/hotspot/active').get()
        
        return {
            "cpu_load": resources.get('cpu-load', '0') + "%",
            "uptime": resources.get('uptime', '0s'),
            "free_memory": int(resources.get('free-memory', 0)),
            "active_hotspot_users": len(active_users)
        }
    finally:
        connection.disconnect()


# ASYNCHRONOUS FASTAPI WRAPPERS

async def get_router_credentials(db: AsyncSession, tenant_id: str):
    """Helper to fetch the active router for a tenant."""
    # For a multi-router setup, you would pass router_id. 
    # Assuming 1 primary router per tenant for this logic:
    stmt = select(Router).where(Router.tenant_id == uuid.UUID(tenant_id), Router.status == 'ONLINE')
    result = await db.execute(stmt)
    router = result.scalars().first()
    
    if not router:
        raise ValueError(f"No online router found for tenant {tenant_id}")
        
    return router

async def activate_customer_on_router(tenant_id: str, phone: str, plan_profile: str, db: AsyncSession):
    """
    Called by the M-Pesa background task after a successful payment.
    Non-blocking wrapper around the RouterOS activation sequence.
    """
    router = await get_router_credentials(db, tenant_id)
    
    await asyncio.to_thread(
        _sync_activate_hotspot_user,
        host=router.ip_address,
        user=router.api_username,
        pwd=router.api_password,
        port=router.api_port,
        customer_phone=phone,
        plan_profile=plan_profile
    )

async def suspend_customer_on_router(tenant_id: str, phone: str, db: AsyncSession):
    """
    Called by the billing expiration scheduler.
    Non-blocking wrapper around the RouterOS suspension sequence.
    """
    router = await get_router_credentials(db, tenant_id)
    
    await asyncio.to_thread(
        _sync_suspend_hotspot_user,
        host=router.ip_address,
        user=router.api_username,
        pwd=router.api_password,
        port=router.api_port,
        customer_phone=phone# this will be the customer registered number
    )