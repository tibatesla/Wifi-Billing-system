import asyncio
from sqlalchemy import text
from app.db.session import async_session_maker

async def patch_database():
    print("🔧 Patching database schema for Device Transfer features...")
    
    async with async_session_maker() as db:
        try:
            # Safely add all the missing columns for the transfer feature
            await db.execute(text("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS transfer_pin VARCHAR;"))
            await db.execute(text("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS authorized_mac VARCHAR;"))
            await db.execute(text("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS is_transferred BOOLEAN DEFAULT FALSE;"))
            
            # Commit the schema changes
            await db.commit()
            
            print("✅ Successfully updated the transactions table with all new columns!")
        except Exception as e:
            print(f"⚠️ Error: {e}")

if __name__ == "__main__":
    asyncio.run(patch_database())