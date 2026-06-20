from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.core.config import settings

# Create the async database engine with a connection pool
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,          # Set to True only for debugging raw SQL queries
    pool_size=20,        # Maximum number of permanent connections
    max_overflow=10,     # How many extra connections to allow during traffic spikes
    pool_recycle=1800    # Reconnect after 30 minutes to prevent dropped connections
)

# This Create a highly reusable session factory
async_session_maker = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False, 
    autoflush=False
)

# Dependency to inject the database session into FastAPI routes
async def get_db():
    """Yields a database session and safely closes it after the request."""
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()