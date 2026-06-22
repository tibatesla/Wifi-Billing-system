from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from pydantic import BaseModel

from app.db.session import get_db
from app.db.models import Tenant, Router, Plan
from app.api.deps import get_current_admin_user

router = APIRouter()

# --- Pydantic Schemas ---
class MpesaKeysUpdate(BaseModel):
    shortcode: str
    consumer_key: str
    consumer_secret: str

class RouterCreate(BaseModel):
    name: str
    ip_address: str
    api_username: str
    api_password: str
    api_port: int = 8728

class PlanCreate(BaseModel):
    name: str
    price: float
    speed_limit: str
    validity_hours: int
    mikrotik_profile_name: str

# --- Routes ---

@router.put("/tenant/{tenant_id}/mpesa")
async def update_mpesa_credentials(
    tenant_id: str,
    payload: MpesaKeysUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    if current_user.get("tenant_id") != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied.")
        
    stmt = select(Tenant).where(Tenant.id == UUID(tenant_id))
    tenant = (await db.execute(stmt)).scalar_one_or_none()
    
    tenant.daraja_shortcode = payload.shortcode
    tenant.daraja_consumer_key = payload.consumer_key
    tenant.daraja_consumer_secret = payload.consumer_secret
    
    await db.commit()
    return {"message": "M-Pesa credentials updated successfully."}


@router.post("/router")
async def add_router(
    payload: RouterCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    new_router = Router(
        tenant_id=UUID(current_user.get("tenant_id")),
        name=payload.name,
        ip_address=payload.ip_address,
        api_username=payload.api_username,
        api_password=payload.api_password,
        api_port=payload.api_port,
        status="ONLINE"
    )
    db.add(new_router)
    await db.commit()
    return {"message": f"Router {payload.name} added securely."}


@router.post("/plan")
async def add_plan(
    payload: PlanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    new_plan = Plan(
        tenant_id=UUID(current_user.get("tenant_id")),
        name=payload.name,
        price=payload.price,
        speed_limit=payload.speed_limit,
        validity_hours=payload.validity_hours,
        mikrotik_profile_name=payload.mikrotik_profile_name
    )
    db.add(new_plan)
    await db.commit()
    return {"message": f"Plan '{payload.name}' created successfully."}


# --- NEW PUBLIC ROUTE FOR CAPTIVE PORTAL ---
@router.get("/tenant/{tenant_id}/plans")
async def get_tenant_plans(tenant_id: str, db: AsyncSession = Depends(get_db)):
    """
    Public route for the Captive Portal to fetch available internet packages.
    No JWT authentication is required for this route so customers can see it.
    """
    stmt = select(Plan).where(Plan.tenant_id == UUID(tenant_id))
    result = await db.execute(stmt)
    plans = result.scalars().all()
    
    return {
        "plans": [
            {
                "id": str(plan.id),
                "name": plan.name,
                "price": float(plan.price),
                "speed_limit": plan.speed_limit,
                "validity_hours": plan.validity_hours,
                "mikrotik_profile_name": plan.mikrotik_profile_name
            } for plan in plans
        ]
    }