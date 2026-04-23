from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import UserRole
from app.db.models.user import User
from app.db.session import get_db_session
from app.modules.auth.dependencies import get_current_user, require_roles
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services import user_service


router = APIRouter(prefix="/users", tags=["users"])
DbSession = Annotated[AsyncSession, Depends(get_db_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]
AdminOrModeratorUser = Annotated[
    User,
    Depends(require_roles(UserRole.admin, UserRole.moderator)),
]
AdminUser = Annotated[User, Depends(require_roles(UserRole.admin))]


@router.get("/", response_model=list[UserRead])
async def list_users(
    db: DbSession,
    _: AdminOrModeratorUser,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[UserRead]:
    return await user_service.list_users(db, limit=limit, offset=offset)


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
) -> UserRead:
    if current_user.role not in {UserRole.admin, UserRole.moderator}:
        if current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )

    return await user_service.get_user_or_404(db, user_id)


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    db: DbSession,
    _: AdminUser,
) -> UserRead:
    return await user_service.create_user(db, payload)


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: UUID,
    payload: UserUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> UserRead:
    if current_user.role == UserRole.admin:
        return await user_service.update_user(db, user_id, payload)

    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )

    if payload.role is not None or payload.is_active is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can modify role or active state",
        )

    return await user_service.update_user(db, user_id, payload)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    db: DbSession,
    _: AdminUser,
) -> Response:
    await user_service.delete_user(db, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
