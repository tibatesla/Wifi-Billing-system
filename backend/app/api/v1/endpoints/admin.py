from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

# Database dependencies & Models
from app.db.session import get_db
from app.db.models import Transaction, Plan, Tenant

router = APIRouter()

# 1. DASHBOARD STATISTICS
@router.get("/dashboard/stats/{tenant_id}")
async def get_dashboard_stats(tenant_id: str, db: AsyncSession = Depends(get_db)):
    """
    Fetches high-level metrics: Total Revenue and Total Successful Transactions.
    """
    # Query 1: Calculate Total Revenue (Only sum COMPLETED transactions)
    revenue_stmt = select(func.sum(Transaction.amount)).where(
        Transaction.tenant_id == tenant_id,
        Transaction.status == "COMPLETED"
    )
    revenue_result = await db.execute(revenue_stmt)
    total_revenue = revenue_result.scalar() or 0.0

    # Query 2: Count Total Successful Connections
    sales_stmt = select(func.count(Transaction.id)).where(
        Transaction.tenant_id == tenant_id,
        Transaction.status == "COMPLETED"
    )
    sales_result = await db.execute(sales_stmt)
    total_sales = sales_result.scalar() or 0

    return {
        "total_revenue_kes": total_revenue,
        "total_sales": total_sales,
        "active_users": total_sales # We will refine this later to only count unexpired plans
    }


# 2. TRANSACTION HISTORY
@router.get("/transactions/{tenant_id}")
async def get_all_transactions(tenant_id: str, db: AsyncSession = Depends(get_db)):
    """
    Fetches the raw history of all M-Pesa attempts (Completed, Pending, and Failed)
    ordered by the newest first.
    """
    stmt = select(Transaction).where(
        Transaction.tenant_id == tenant_id
    ).order_by(desc(Transaction.created_at)) # Assuming you have a created_at timestamp column
    
    result = await db.execute(stmt)
    transactions = result.scalars().all()

    # Convert to a list of dictionaries for React to consume easily
    tx_list = []
    for tx in transactions:
        tx_list.append({
            "id": str(tx.id),
            "amount": tx.amount,
            "status": tx.status,
            "checkout_request_id": tx.checkout_request_id,
            # If you added phone_number to your Transaction model, include it here:
            # "phone_number": tx.phone_number 
        })

    return {"transactions": tx_list}