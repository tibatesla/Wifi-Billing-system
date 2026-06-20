import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Wi-Fi Billing System (Standalone)"
    SECRET_KEY: str = "change-this-super-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    DATABASE_URL: str = "postgresql+asyncpg://postgres:wifi1234@localhost:5432/wifi_db"
    
    # SINGLE TENANT LOCK this locks the system from being  a saas to single product this i converted from saas tp product this harcoded 111 simplify the
    LOCAL_TENANT_ID: str = "11111111-1111-1111-1111-111111111111"

settings = Settings()