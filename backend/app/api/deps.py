from app.core.config import settings

def get_current_tenant() -> str:
    """
    Overrides multi-tenant logic. 
    Forces every API call to map to the single local instance.
    """
    return settings.LOCAL_TENANT_ID
