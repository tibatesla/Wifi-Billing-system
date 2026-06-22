from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt.exceptions import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

# Application Imports
from app.core.config import settings
from app.db.session import get_db
from app.core.security import SECRET_KEY, ALGORITHM 

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_tenant() -> str:
    """
    Fallback multi-tenant logic. 
    Can be used for local testing or public webhook routes where JWT is not present.
    """
    return settings.LOCAL_TENANT_ID

async def get_current_admin_user(
    token: str = Depends(oauth2_scheme), 
    db: AsyncSession = Depends(get_db)
):
    """
    Dependency to validate the JWT using the modern PyJWT library.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token expired",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # 
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        tenant_id: str = payload.get("tenant_id")
        
        if not user_id or not tenant_id:
            raise credentials_exception
            
    except InvalidTokenError:
        # Catching the specific PyJWT exception
        raise credentials_exception

    return payload