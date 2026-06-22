import asyncio
import routeros_api
from uuid import UUID

from sqlalchemy import select
# Ensure you import your async session factory, not the FastAPI dependency
from app.db.session import async_session_maker 
from app.db.models import Router, Plan

#  SYNCHRONOUS CORE OPERATION

def _connect_to_router(host: str, username: str, password: str, port: int):
    """Establishes the synchronous socket connection to the router."""
    use_ssl = True if port == 8729 else False
    
    connection = routeros_api.RouterOsApiPool(
        host=host,
        username=username,
        password=password,
        port=port,
        use_ssl=use_ssl,
        plaintext_login=True 
    )
    return connection

def _sync_activate_hotspot_user(host, user, pwd, port, phone, profile_name, validity_hours):
    """Idempotently creates/updates a user and delegates expiration to the router."""
    connection = _connect_to_router(host, user, pwd, port)
    api = connection.get_api()
    
    try:
        hotspot_users = api.get_resource('/ip/hotspot/user')
        active_users = api.get_resource('/ip/hotspot/active')
        
        uptime_limit = f"{validity_hours}h"
        existing_user = hotspot_users.get(name=phone)
        
        if existing_user:
            user_id = existing_user[0]['id']
            hotspot_users.set(
                id=user_id, 
                disabled='no', 
                profile=profile_name, 
                **{'limit-uptime': uptime_limit}
            )
            # Reset counters so they get their full purchased time
            hotspot_users.set(id=user_id, **{'bytes-in': '0', 'bytes-out': '0', 'uptime': '0s'})
        else:
            hotspot_users.add(
                server='all',
                name=phone, 
                password=phone, 
                profile=profile_name, 
                **{'limit-uptime': uptime_limit}
            )

        # Kick the active session to force re-authentication with new speeds
        active_sessions = active_users.get(user=phone)
        for session in active_sessions:
            active_users.remove(id=session['id'])

    except Exception as e:
        print(f"RouterOS API Error (Activation): {str(e)}")
        raise RuntimeError(f"RouterOS API Failure: {str(e)}")
    finally:
        connection.disconnect()

def _sync_suspend_hotspot_user(host, user, pwd, port, phone):
    """Manually disables a user (Used for admin bans or device PIN transfers)."""
    connection = _connect_to_router(host, user, pwd, port)
    api = connection.get_api()
    
    try:
        hotspot_users = api.get_resource('/ip/hotspot/user')
        existing_user = hotspot_users.get(name=phone)
        
        if existing_user:
            hotspot_users.set(id=existing_user[0]['id'], disabled='yes')
            
        active_sessions = api.get_resource('/ip/hotspot/active')
        active_user = active_sessions.get(user=phone)
        
        for session in active_user:
            active_sessions.remove(id=session['id'])
            
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
        resources = api.get_resource('/system/resource').get()[0]
        active_users = api.get_resource('/ip/hotspot/active').get()
        
        return {
            "cpu_load": resources.get('cpu-load', '0') + "%",
            "uptime": resources.get('uptime', '0s'),
            "free_memory": int(resources.get('free-memory', 0)),
            "active_hotspot_users": len(active_users)
        }
    finally:
        connection.disconnect()


#   ASYNCHRONOUS FASTAPI WRAPPERS 

async def activate_customer_on_router(tenant_id: str, phone: str, plan_id: str):
    """
    Called by M-Pesa background task. 
    Manages its own DB session to prevent DetachedInstanceErrors.
    """
    async with async_session_maker() as db:
        router_stmt = select(Router).where(Router.tenant_id == UUID(tenant_id), Router.status == 'ONLINE')
        router = (await db.execute(router_stmt)).scalar_one_or_none()

        plan_stmt = select(Plan).where(Plan.id == UUID(plan_id))
        plan = (await db.execute(plan_stmt)).scalar_one_or_none()

        if not router or not plan:
            print(f"❌ Provisioning failed: Missing Router or Plan for Tenant {tenant_id}")
            return

    print(f" Provisioning {phone} on MikroTik ({router.ip_address})...")
    
    await asyncio.to_thread(
        _sync_activate_hotspot_user,
        host=router.ip_address,
        user=router.api_username,
        pwd=router.api_password,
        port=router.api_port,
        phone=phone,
        profile_name=plan.mikrotik_profile_name,
        validity_hours=plan.validity_hours
    )

async def suspend_customer_on_router(tenant_id: str, phone: str):
    """
    Utility wrapper for admin bans or kicking a MAC address during a PIN transfer.
    """
    async with async_session_maker() as db:
        router_stmt = select(Router).where(Router.tenant_id == UUID(tenant_id), Router.status == 'ONLINE')
        router = (await db.execute(router_stmt)).scalar_one_or_none()
        
        if not router:
            return

    await asyncio.to_thread(
        _sync_suspend_hotspot_user,
        host=router.ip_address,
        user=router.api_username,
        pwd=router.api_password,
        port=router.api_port,
        phone=phone
    )

async def get_router_health_stats(tenant_id: str):
    """
    Wrapper for your React Admin Dashboard polling.
    """
    async with async_session_maker() as db:
        router_stmt = select(Router).where(Router.tenant_id == UUID(tenant_id), Router.status == 'ONLINE')
        router = (await db.execute(router_stmt)).scalar_one_or_none()
        
        if not router:
            return {"error": "Router offline or missing"}

    return await asyncio.to_thread(
        _sync_get_router_health,
        host=router.ip_address,
        user=router.api_username,
        pwd=router.api_password,
        port=router.api_port
    )