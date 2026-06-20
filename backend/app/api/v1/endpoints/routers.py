# app/api/v1/endpoints/routers.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.db.session import get_db
from app.db.models import Router
from app.api.dependencies.auth import get_current_tenant, RoleChecker

router = APIRouter()

# Define allowed roles for certain actions
allow_admin_only = RoleChecker(["TENANT_ADMIN", "SUPER_ADMIN"])
allow_all_staff = RoleChecker(["TENANT_ADMIN", "RESELLER", "SUPER_ADMIN"])

@router.get("/")
async def list_routers(
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    user_access = Depends(allow_all_staff)
):
    """
    Any staff member can view the routers, but ONLY the routers belonging to their specific tenant_id.
    """
    stmt = select(Router).where(Router.tenant_id == tenant_id)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.delete("/{router_id}")
async def delete_router(
    router_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    user_access = Depends(allow_admin_only) # REJECTS RESELLERS
):
    """
    Only Admins can delete routers. The query strictly includes tenant_id 
    to prevent an admin from deleting another ISP's router by guessing the UUID.
    """
    stmt = select(Router).where(Router.id == router_id, Router.tenant_id == tenant_id)
    result = await db.execute(stmt)
    router_obj = result.scalar_one_or_none()
    
    if not router_obj:
        raise HTTPException(status_code=404, detail="Router not found")
        
    await db.delete(router_obj)
    await db.commit()
    return {"message": "Router deleted successfully"}