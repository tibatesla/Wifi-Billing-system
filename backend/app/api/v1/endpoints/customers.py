
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.api.dependencies.tenant import get_current_tenant_id
from app.db.models import Customer

router = APIRouter()

@router.post("/customers/")
async def create_local_customer(
    customer_data: dict, # Replace with your Pydantic schema
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(deps.get_current_tenant) #THE LOCK that forces the system to use the hardcode code on the config file
):
    # This  willexplicitly attach the locked tenant_id to the incoming data
    new_customer = Customer(
        tenant_id=tenant_id,
        phone_number=customer_data['phone_number'],
        mac_address=customer_data.get('mac_address'),
        status="ACTIVE"
    )
    
    db.add(new_customer)
    await db.commit()
    await db.refresh(new_customer)
    return new_customer