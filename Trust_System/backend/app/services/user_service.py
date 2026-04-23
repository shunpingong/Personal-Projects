from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.models.user import User
from app.schemas.user import UserCreate, UserUpdate


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    normalized_email = email.lower()
    result = await db.execute(select(User).where(User.email == normalized_email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> User | None:
    return await db.get(User, user_id)


async def get_user_or_404(db: AsyncSession, user_id: UUID) -> User:
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


async def list_users(
    db: AsyncSession,
    *,
    limit: int = 50,
    offset: int = 0,
) -> list[User]:
    result = await db.execute(
        select(User).order_by(User.created_at.desc()).offset(offset).limit(limit)
    )
    return result.scalars().all()


async def create_user(db: AsyncSession, payload: UserCreate) -> User:
    if await get_user_by_email(db, payload.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    user = User(
        email=payload.email.lower(),
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        is_active=payload.is_active,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update_user(db: AsyncSession, user_id: UUID, payload: UserUpdate) -> User:
    user = await get_user_or_404(db, user_id)
    update_data = payload.model_dump(exclude_unset=True, exclude_none=True)

    if "email" in update_data:
        normalized_email = update_data["email"].lower()
        existing_user = await get_user_by_email(db, normalized_email)
        if existing_user is not None and existing_user.id != user.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists",
            )
        user.email = normalized_email

    if "full_name" in update_data:
        user.full_name = update_data["full_name"]
    if "password" in update_data:
        user.hashed_password = hash_password(update_data["password"])
    if "role" in update_data:
        user.role = update_data["role"]
    if "is_active" in update_data:
        user.is_active = update_data["is_active"]

    await db.commit()
    await db.refresh(user)
    return user


async def delete_user(db: AsyncSession, user_id: UUID) -> None:
    user = await get_user_or_404(db, user_id)
    await db.delete(user)
    await db.commit()
