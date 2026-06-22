import asyncio
from app.db.session import async_session_maker
from app.db.models import Tenant, User
from app.core.security import get_password_hash  # Assumes you have a hashing function using PassLib

async def create_first_admin():
    print("🚀 Initializing Setup Sequence...")
    
    # Use input() to securely grab credentials from the terminal
    admin_email = input("Enter admin email: ").strip()
    admin_password = input("Enter strong admin password: ").strip()
    isp_name = input("Enter your ISP / Business Name: ").strip()

    if not admin_email or not admin_password or not isp_name:
        print("❌ Error: All fields are required. Aborting.")
        return

    async with async_session_maker() as db:
        # 1. Create the base Tenant (Your ISP)
        new_tenant = Tenant(
            name=isp_name,
            # You can add default Daraja keys here later via the UI
        )
        db.add(new_tenant)
        await db.flush()  # Flushes to DB to generate the new_tenant.id UUID

        # 2. Hash the password
        hashed_password = get_password_hash(admin_password)

        # 3. Create the Admin User linked to the Tenant
        new_admin = User(
            tenant_id=new_tenant.id,
            email=admin_email,
            password_hash=hashed_password,
            role="SUPERADMIN"
        )
        db.add(new_admin)
        
        # 4. Commit everything as a single transaction
        await db.commit()

        print("\n✅ Success! Database seeded.")
        print("========================================")
        print(f"ISP Tenant ID : {new_tenant.id}")
        print(f"Admin Email   : {admin_email}")
        print("========================================")
        print("Copy your Tenant ID. You will need it to configure your Router and Plans.")

if __name__ == "__main__":
    # Execute the async script
    asyncio.run(create_first_admin())
