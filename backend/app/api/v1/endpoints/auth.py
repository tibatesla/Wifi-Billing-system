import secrets
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

# Local Application Imports
from app.db.session import get_db
from app.db.models import User, Transaction, Customer
from app.core.security import verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from app.services.mikrotik_service import suspend_customer_on_router

# Initialize the router exactly once
router = APIRouter()


# --- SCHEMAS ---

class DeviceTransferRequest(BaseModel):
    phone_number: str
    transfer_pin: str
    new_mac_address: str


# --- ROUTES ---

@router.post("/login")
async def login_access_token(
    db: AsyncSession = Depends(get_db), 
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    OAuth2 compatible token login, getting an access token for future requests.
    Note: OAuth2PasswordRequestForm expects data as form-urlencoded, not JSON.
    """
    # 1. Find the admin user by email
    stmt = select(User).where(User.email == form_data.username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    # 2. Verify existence and password
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # 3. Create JWT with user identity and tenant context
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    token_payload = {
        "sub": str(user.id),
        "tenant_id": str(user.tenant_id) if user.tenant_id else None,
        "role": user.role
    }
    
    access_token = create_access_token(
        data=token_payload, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user_info": {
            "email": user.email,
            "role": user.role
        }
    }


@router.post("/transfer")
async def transfer_device_session(
    payload: DeviceTransferRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Allows a customer to move their active Wi-Fi session to a new device (MAC address)
    by providing their phone number and their active 6-digit Transfer PIN.
    """
    
    # 1. Look up the Transaction by the provided PIN
    stmt = select(Transaction).where(
        Transaction.transfer_pin == payload.transfer_pin.upper(),
        Transaction.status == "COMPLETED"
    )
    result = await db.execute(stmt)
    transaction = result.scalar_one_or_none()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid Transfer PIN or transaction not found."
        )

    # 2. Kick the old device off the network
    # This forcibly removes the active session on the MikroTik. 
    try:
        await suspend_customer_on_router(
            tenant_id=str(transaction.tenant_id), 
            phone=payload.phone_number
        )
    except Exception as e:
        print(f"Failed to kick old session during transfer: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not communicate with the router to release the old session."
        )

    # 3. Update the Transaction & Rotate the PIN to protec t replay attacks
    new_pin = secrets.token_hex(3).upper()
    
    transaction.authorized_mac = payload.new_mac_address
    transaction.is_transferred = True
    transaction.transfer_pin = new_pin  # Invalidate the old one

    await db.commit()

    return {
        "message": "Session successfully transferred.",
        "new_transfer_pin": new_pin,
        "instructions": "Please log in on this device using your phone number."
    }