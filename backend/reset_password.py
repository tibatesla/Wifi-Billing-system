import asyncio
from sqlalchemy import select
from app.db.session import async_session_maker
from app.db.models import User
from app.core.security import get_password_hash

async def reset_admin_password():
    async with async_session_maker() as db:
        # 1. Fetch and display all existing emails so you remember what you typed
        result = await db.execute(select(User))
        users = result.scalars().all()

        if not users:
            print("❌ No admin accounts exist yet. Run create_superuser.py first.")
            return

        print("🔍 Found the following Admin accounts in the database:")
        for u in users:
            print(f"   -> {u.email}")

        # 2. Prompt for the reset
        target_email = input("\nType the email you want to reset: ").strip()
        new_password = input("Enter your NEW password: ").strip()

        # 3. Find the user and update the hash
        stmt = select(User).where(User.email == target_email)
        user = (await db.execute(stmt)).scalar_one_or_none()

        if user:
            user.password_hash = get_password_hash(new_password)
            await db.commit()
            print(f"\n✅ Success! Password for {target_email} has been securely updated.")
        else:
            print(f"\n❌ Error: Could not find an account with the email {target_email}.")

if __name__ == "__main__":
    asyncio.run(reset_admin_password())
