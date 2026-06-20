import uuid
from fastapi import APIRouter, Request, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Database dependencies & Models
from app.db.session import get_db
from app.db.models import Tenant, Plan, Transaction

# Domain Services
from app.services.mpesa_service import DarajaService
from app.services.mikrotik_service import activate_customer_on_router

# The JSON structure the backend expects from React
from pydantic import BaseModel

class STKPushRequest(BaseModel):
    phone_number: str
    plan_id: str
    tenant_id: str

router = APIRouter()

# 1. BACKGROUND TASK WORKER (INTERNAL)
async def process_successful_payment(
    phone: str, 
    amount: float, 
    receipt: str, 
    checkout_request_id: str,
    tenant_id: str
):
    """
    Decoupled background worker. Executes concurrently *after* FastAPI replies '200 OK'.
    """
    try:
        # Connect to MikroTik and immediately provision the customer
        await activate_customer_on_router(tenant_id=tenant_id, phone=phone)
        print(f"Background task complete: Verified {receipt} for {phone} under Tenant {tenant_id}")
    except Exception as e:
        print(f"Critical background processing error for checkout {checkout_request_id}: {str(e)}")


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

    # Instantiate Daraja Service
    mpesa_engine = DarajaService(
        consumer_key=tenant.daraja_consumer_key,
        consumer_secret=tenant.daraja_consumer_secret,
        shortcode=tenant.daraja_shortcode or "174379", 
        passkey="bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919" 
    )
    
    # EXACT NGROK URL - Properly indented
    callback_endpoint = f"https://winfred-uncaned-jerri.ngrok-free.dev/api/v1/mpesa/callback/{tenant_id}"    
    
    # Send request to Safaricom API
    result = await mpesa_engine.initiate_stk_push(
        phone_number=phone,
        amount=int(plan.price),
        callback_url=callback_endpoint,
        account_reference=phone,
        transaction_desc=f"WiFi {plan.name}"
    )
    
    if not result["success"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["error"])
        
    # Save a PENDING record into your transactions table
    new_tx = Transaction(
        tenant_id=tenant.id,
        amount=plan.price,
        checkout_request_id=result["checkout_request_id"],
        status="PENDING"
    )
    db.add(new_tx)
    await db.commit()
    
    return {"message": "STK Push sent to phone", "checkout_id": result["checkout_request_id"]}


# 3. INBOUND: WEBHOOK CALLBACK (FROM SAFARICOM)
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
    
    if result_code == 0:
        meta = stk_callback.get("CallbackMetadata", {}).get("Item", [])
        phone = next((i["Value"] for i in meta if i["Name"] == "PhoneNumber"), None)
        amount = next((i["Value"] for i in meta if i["Name"] == "Amount"), None)
        receipt = next((i["Value"] for i in meta if i["Name"] == "MpesaReceiptNumber"), None)
        
        # UPDATE THE DATABASE SO REACT STOPS POLLING
        stmt = select(Transaction).where(Transaction.checkout_request_id == checkout_request_id)
        result = await db.execute(stmt)
        transaction = result.scalar_one_or_none()
        
        if transaction:
            transaction.status = "COMPLETED"
            await db.commit()
            print(f"✅ Payment {receipt} recorded as COMPLETED in database.")

        # Hand off the MikroTik connection to the background worker
        background_tasks.add_task(
            process_successful_payment, 
            str(phone), float(amount), str(receipt), str(checkout_request_id), tenant_id
        )
    else:
        stmt = select(Transaction).where(Transaction.checkout_request_id == checkout_request_id)
        result = await db.execute(stmt)
        transaction = result.scalar_one_or_none()
        
        if transaction:
            transaction.status = "FAILED"
            await db.commit()
        print(f"❌ M-Pesa transaction {checkout_request_id} failed with code {result_code}")
        
    return {"ResultCode": 0, "ResultDesc": "Callback Processed Successfully"}


# 4. INBOUND: STATUS POLLING (FROM CLIENT)
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

    return {"status": transaction.status}