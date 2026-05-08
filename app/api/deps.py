from typing import Generator, Optional, List, Callable
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select
import logging

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User, Role
from app.repositories.user_repository import user_repo
from app.schemas.user import TokenPayload

logger = logging.getLogger("app")

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (JWTError, Exception) as e:
        logger.error(f"JWT Validation Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    
    # Eagerly load roles and permissions to avoid lazy-loading issues in async
    query = (
        select(User)
        .where(User.id == token_data.sub)
        .options(selectinload(User.roles).selectinload(Role.permissions))
    )
    
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def PermissionChecker(required_permissions: List[str]):
    """
    Dependency factory to check if the current user has specific permissions.
    """
    async def checker(user: User = Depends(get_current_active_user)) -> User:
        if user.is_superuser:
            return user
            
        user_permissions = {perm.name for role in user.roles for perm in role.permissions}
        
        for required in required_permissions:
            if required not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permission: {required}"
                )
        return user
    return checker
