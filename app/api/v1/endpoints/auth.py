from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.api import deps
from app.core import security
from app.core.config import settings
from app.db.session import get_db
from app.repositories.user_repository import user_repo
from app.schemas.user import Token, User, UserCreate

logger = logging.getLogger("app")
router = APIRouter()

@router.post("/login", response_model=Token)
async def login(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    logger.info(f"Login attempt: {form_data.username}")
    user = await user_repo.get_by_email(db, email=form_data.username)
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

@router.post("/register", response_model=User)
async def register(
    *,
    db: AsyncSession = Depends(get_db),
    user_in: UserCreate
) -> Any:
    logger.info(f"Registering user: {user_in.email}")
    try:
        user = await user_repo.get_by_email(db, email=user_in.email)
        if user:
            raise HTTPException(
                status_code=400,
                detail="The user with this email already exists in the system.",
            )
        
        from app.models.user import User as UserModel
        new_user = UserModel(
            email=user_in.email,
            hashed_password=security.get_password_hash(user_in.password),
            full_name=user_in.full_name,
            is_active=True
        )
        created_user = await user_repo.create(db, obj_in=new_user)
        logger.info(f"User created: {created_user.id}")
        return created_user
    except Exception as e:
        logger.error(f"Error in register endpoint: {e}", exc_info=True)
        raise
