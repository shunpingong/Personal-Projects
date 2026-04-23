from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.db.session import get_db_session
from app.modules.auth.dependencies import get_current_user
from app.schemas.auth import TokenPair, TokenRefreshRequest, UserLogin, UserRegister
from app.schemas.user import UserRead
from app.services import auth_service


router = APIRouter(prefix="/auth", tags=["auth"])
DbSession = Annotated[AsyncSession, Depends(get_db_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(payload: UserRegister, db: DbSession) -> UserRead:
    return await auth_service.register_user(db, payload)


@router.post("/login", response_model=TokenPair)
async def login_user(payload: UserLogin, db: DbSession) -> TokenPair:
    return await auth_service.login_user(db, payload)


@router.post("/refresh", response_model=TokenPair)
async def refresh_tokens(
    payload: TokenRefreshRequest,
    db: DbSession,
) -> TokenPair:
    return await auth_service.refresh_tokens(db, payload.refresh_token)


@router.get("/me", response_model=UserRead)
async def get_authenticated_user(current_user: CurrentUser) -> UserRead:
    return current_user
