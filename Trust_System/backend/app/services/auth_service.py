from __future__ import annotations

from fastapi import HTTPException, status
from jose import JWTError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.enums import UserRole
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.db.models.user import User
from app.schemas.auth import TokenPair, TokenPayload, UserLogin, UserRegister
from app.schemas.user import UserCreate
from app.services import user_service


async def register_user(db: AsyncSession, payload: UserRegister) -> User:
    user_create = UserCreate(
        email=payload.email,
        full_name=payload.full_name,
        password=payload.password,
        role=UserRole.user,
        is_active=True,
    )
    return await user_service.create_user(db, user_create)


async def authenticate_user(db: AsyncSession, payload: UserLogin) -> User:
    user = await user_service.get_user_by_email(db, payload.email)
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    return user


def build_token_pair(user: User) -> TokenPair:
    return TokenPair(
        access_token=create_access_token(subject=str(user.id)),
        refresh_token=create_refresh_token(subject=str(user.id)),
        token_type="bearer",
        access_token_expires_in=settings.access_token_expire_minutes * 60,
        refresh_token_expires_in=settings.refresh_token_expire_days * 24 * 60 * 60,
    )


async def login_user(db: AsyncSession, payload: UserLogin) -> TokenPair:
    user = await authenticate_user(db, payload)
    return build_token_pair(user)


async def refresh_tokens(db: AsyncSession, refresh_token: str) -> TokenPair:
    try:
        token_payload = TokenPayload.model_validate(
            decode_token(refresh_token, expected_type="refresh")
        )
    except (JWTError, ValidationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = await user_service.get_user_by_id(db, token_payload.sub)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found for refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    return build_token_pair(user)
