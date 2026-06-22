from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.db.session import get_db
from app.db.models import Transaction
from app.api.deps import get_current_admin_user
from app.services.mikrotik_service import get_router_health_stats

router = APIRouter()

@router.get("/dashboard/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db), 
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Returns high-level metrics. Tenant ID is securely extracted from the JWT.
    """
    tenant_id = current_user.get("tenant_id")

    revenue_stmt = select(func.sum(Transaction.amount)).where(
        Transaction.tenant_id == UUID(tenant_id),
        Transaction.status == "COMPLETED"
    )
    revenue = await db.scalar(revenue_stmt) or 0.0

    sales_stmt = select(func.count(Transaction.id)).where(
        Transaction.tenant_id == UUID(tenant_id),
        Transaction.status == "COMPLETED"
    )
    sales = await db.scalar(sales_stmt) or 0

    router_stats = await get_router_health_stats(tenant_id)
    active_users = router_stats.get("active_hotspot_users", 0) if "error" not in router_stats else 0

    return {
        "total_revenue_kes": float(revenue),
        "total_sales": sales,
        "active_users": active_users
    }

@router.get("/transactions")
async def get_recent_transactions(
    db: AsyncSession = Depends(get_db), 
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Returns the latest 10 transactions.
    """
    tenant_id = current_user.get("tenant_id")

    stmt = select(Transaction).where(
        Transaction.tenant_id == UUID(tenant_id)
    ).order_by(desc(Transaction.created_at)).limit(10)
    
    result = await db.execute(stmt)
    txs = result.scalars().all()

    return {
        "transactions": [
            {
                "id": str(tx.id),
                "amount": float(tx.amount),
                "status": tx.status,
                "checkout_request_id": tx.checkout_request_id
            } for tx in txs
        ]
    }