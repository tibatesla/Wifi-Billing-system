import os
import uuid
import secrets
from fastapi import APIRouter, Request, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Database dependencies & Models
from app.db.session import get_db
from app.db.models import Tenant, Plan, Transaction

# Domain Services
from app.services.mpesa_service import DarajaService
from app.services.mikrotik_service import activate_customer_on_router

from pydantic import BaseModel

class STKPushRequest(BaseModel):
    phone_number: str
    plan_id: str
    tenant_id: str

router = APIRouter()

# 1. BACKGROUND TASK WORKER (INTERNAL)
async def process_successful_payment(
    tenant_id: str,
    phone: str, 
    plan_id: str
):
    """
    Decoupled background worker. Executes concurrently *after* FastAPI replies '200 OK'.
    """
    try:
        # We now pass plan_id so the Mikrotik service knows WHICH speed profile to assign
        await activate_customer_on_router(tenant_id=tenant_id, phone=phone, plan_id=plan_id)
        print(f" Background task complete: Provisioned {phone} on Tenant {tenant_id}")
    except Exception as e:
        print(f"❌ Critical background processing error: {str(e)}")


# 2. OUTBOUND: INITIATE PAYMENT (FROM CLIENT)
@router.post("/stk-push")
async def trigger_payment_request(
    payload: STKPushRequest, 
    db: AsyncSession = Depends(get_db)
):
    """
    Called by your Captive Portal when a user hits 'Pay via M-Pesa'.
    """
    phone = payload.phone_number
    plan_id = payload.plan_id
    tenant_id = payload.tenant_id

    # Fetch tenant-specific Daraja credentials
    tenant_stmt = select(Tenant).where(Tenant.id == uuid.UUID(tenant_id))
    tenant_result = await db.execute(tenant_stmt)
    tenant = tenant_result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant ISP not found")

    # Fetch the plan details
    plan_stmt = select(Plan).where(Plan.id == uuid.UUID(plan_id))
    plan_result = await db.execute(plan_stmt)
    plan = plan_result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Selected Internet Plan not found")

    # Instantiate Daraja Service (Use env vars for global configs)
    mpesa_engine = DarajaService(
        consumer_key=tenant.daraja_consumer_key,
        consumer_secret=tenant.daraja_consumer_secret,
        shortcode=tenant.daraja_shortcode or os.getenv("DARAJA_DEFAULT_SHORTCODE", "174379"), 
        passkey=os.getenv("DARAJA_PASSKEY") 
    )
    
    # Dynamically build webhook URL. Use env var in production, default to ngrok locally.
    webhook_domain = os.getenv("WEBHOOK_DOMAIN", "https://winfred-uncaned-jerri.ngrok-free.dev")
    callback_endpoint = f"{webhook_domain}/api/v1/mpesa/callback/{tenant_id}"    
    
    # Send request to Safaricom API
    result = await mpesa_engine.initiate_stk_push(
        phone_number=phone,
        amount=int(plan.price),
        callback_url=callback_endpoint,
        account_reference=phone,
        transaction_desc=f"WiFi {plan.name}"
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get("error", "STK Push Failed"))
        
    # Save a PENDING record WITH the plan_id
    new_tx = Transaction(
        tenant_id=tenant.id,
        plan_id=plan.id,
        amount=plan.price,
        checkout_request_id=result["checkout_request_id"],
        status="PENDING"
    )
    db.add(new_tx)
    await db.commit()
    
    return {"message": "STK Push sent to phone", "checkout_id": result["checkout_request_id"]}


# 3. INBOUND: WEBHOOK CALLBACK FROM SAFARICOM
@router.post("/callback/{tenant_id}")
async def stk_push_callback(
    tenant_id: str,
    request: Request, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Safaricom calls this endpoint asynchronously when the user completes or cancels PIN entry.
    """
    payload = await request.json()
    stk_callback = payload.get("Body", {}).get("stkCallback", {})
    result_code = stk_callback.get("ResultCode")
    checkout_request_id = stk_callback.get("CheckoutRequestID")
    
    stmt = select(Transaction).where(Transaction.checkout_request_id == checkout_request_id)
    result = await db.execute(stmt)
    transaction = result.scalar_one_or_none()

    if not transaction:
        print(f" Orphaned Webhook: Checkout {checkout_request_id} not found.")
        return {"ResultCode": 0, "ResultDesc": "Acknowledged but missing locally"}

    if result_code == 0:
        meta = stk_callback.get("CallbackMetadata", {}).get("Item", [])
        phone = next((i["Value"] for i in meta if i["Name"] == "PhoneNumber"), None)
        receipt = next((i["Value"] for i in meta if i["Name"] == "MpesaReceiptNumber"), None)
        
        # 1. Update State
        transaction.status = "COMPLETED"
        transaction.mpesa_receipt = receipt
        
        # 2. Generate the Zero-Cost Transfer PIN (6-digit alphanumeric string)
        transfer_pin = secrets.token_hex(3).upper() 
        transaction.transfer_pin = transfer_pin

        await db.commit()
        print(f" Payment {receipt} recorded. PIN generated: {transfer_pin}")

        # 3. Hand off to the MikroTik background worker
        background_tasks.add_task(
            process_successful_payment, 
            tenant_id=tenant_id,
            phone=str(phone),
            plan_id=str(transaction.plan_id)
        )
    else:
        transaction.status = "FAILED"
        await db.commit()
        print(f"❌ M-Pesa transaction {checkout_request_id} failed with code {result_code}")
        
    return {"ResultCode": 0, "ResultDesc": "Callback Processed Successfully"}


# 4. INBOUND: STATUS POLLING FROM CLIENT
@router.get("/status/{checkout_request_id}")
async def check_transaction_status(
    checkout_request_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Called by the React frontend polling engine every 3 seconds.
    """
    stmt = select(Transaction).where(Transaction.checkout_request_id == checkout_request_id)
    result = await db.execute(stmt)
    transaction = result.scalar_one_or_none()

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Transaction not found in the system."
        )

    return {
        "status": transaction.status,
        "receipt": transaction.mpesa_receipt,
        "transfer_pin": transaction.transfer_pin
    }