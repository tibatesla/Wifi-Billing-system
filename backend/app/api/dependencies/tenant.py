# security
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api.dependencies.auth import get_current_user
from app.db.models import User

async def get_current_tenant_id(
    current_user: User = Depends(get_current_user)
) -> str:
    """
    Extracts the tenant_id from the authenticated user.
    Ensures that all subsequent DB queries are scoped to this tenant.
    """
    if not current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not belong to a valid tenant context."
        )
    return current_user.tenant_id